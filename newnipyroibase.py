# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu

"""


# Here is where you import your configuration module
# This is the only thing you should have to edit in this script
#----------------------------#
from configbase import *
import configbase as config
#----------------------------#

import os
import re
import datetime
import fsroidict
import numpy as N
from glob import glob
from nipype.interfaces import freesurfer as fs
from nipype.interfaces import matlab as mlab
from nipype.interfaces import base


# Get the analysis parameters 
analysis = Analysis()


# Get our subject list
if ProjectName() == 'development':
    subjList = ['SAD_022','SAD_033']
else:
    subjList = Subjects()


# Set up some directory variables
fsSubjDir = SubjDir()
maindir = os.path.abspath('.')
l1output = os.path.join(maindir,'surface/l1output')
segvoldir = os.path.join(maindir,'roi/segvols')
analysisdir = os.path.join(maindir,'roi/analyses')
projectdir = os.path.join(analysisdir,ProjectName())
logdir = os.path.join(projectdir,'logfiles')


# Make roi directories, if they don't exist
try: os.mkdir(os.path.joinp(maindir,'roi'))
except: pass

roidirs = [segvoldir,analysisdir,projectdir,logdir]

for dir in roidirs:
    try: os.mkdir(dir)
    except: pass

# Find out what functional paradigms will be analyzed in this project
analysisPars = set()
for anparams in analysis:
    analysisPars.add(anparams['par'])

# Set some variables we'll use when we print to the terminal/log
thinline = '----------------------------------------------------------------------'
thickline = '======================================================================'

# Some little functions for controlling terminal and logfile output
def fullOut(message,line):
    print
    print line
    print message
    print line
    print
    lf.write('\n'+line+'\n'+message+'\n'+line+'\n\n')

def cmdOut(cmd,res):
    print cmd.cmdline
    print
    print res.runtime.stdout
    print res.runtime.stderr
    print
    lf.write(cmd.cmdline+'\n\n'+res.runtime.stdout+'\n'+res.runtime.stderr+'\n\n')

def shortOut(message):
    print message
    lf.write(message)

    

# Get a timestamp for the analysis
now = datetime.datetime.now()
now = str(now)
nowyear = now[0:4]
nowmonth = now[5:7]
nowday = now[8:10]
nowhour = now[11:13]
nowminute = now[14:16]
timeStamp = nowyear + nowmonth + nowday + '-' + nowhour + nowminute


# Open up the log file and print important information
logpath = (os.path.join(logdir,ProjectName() + '_' + timeStamp + '.log'))
            
lf = open(logpath,'w')

print 'NiPyRoi Analysis'
print now[0:16]
print os.getcwd()
print 'User: ' + os.getlogin()
print 'Project name: ' + ProjectName()
print 'Config module: ' + config.__file__
print 'Log file is ' + logpath
print

lf.write('NiPyRoi Analysis \n' + now[0:16] + '\n' + os.getcwd() + 
              '\nUser: ' + os.getlogin() + '\n' + 'Project name: ' + ProjectName() + '\n' 
              'Config module: ' + __file__ + '\nLog file is ' + logpath + '\n\n')
 


#-------------------------------------------------------------------------------#
# Resample the segmentation volumes into functional space
#-------------------------------------------------------------------------------#


# Register the functional to the original volume with bbregister, calling FLIRT
for par in analysisPars:
    fullOut('Creating segmentation volumes for '+par+' analysis',thickline)
    for subj in subjList:
        svsubjdir = os.path.join(segvoldir,par,subj)
        regdir = os.path.join(svsubjdir,'regmats')
        regmat = Paradigms(par,'lower') + '2orig_bbregister.dat'
        regmat = os.path.join(regdir,regmat)
        funcvol = glob(os.path.join(l1output,par,subj,'realign/*.nii'))
        funcvol = funcvol[0]
        try: os.mkdir(regdir)
        except: pass
        if not isfile(regmat):
            fullOut('Creating registration matrix for ' + subj,thinline)
            # Set the inputs

            register = fs.BBRegister()

            register.inputs.subject_id = subj
            register.inputs.sourcefile = funcvol
            register.inputs.init_fsl = True
            register.inputs.t2_contrast = True
            register.inputs.outregfile = regmat

            # Run bbregister
            res = register.run()
            cmdOut = (register,res)
        else:
            shortOut('Found ' + regmat)


        # Check to see if the segmentation volumes exist and make them if not
        volumedir = os.path.join(svsubjdir,'volumes')
        segvols = []
        segvoltypes = []
        segspace = RoiSpace()
        for voltype in SegVols().keys():
            if segspace[voltype] == 'volume':
                if Regions(voltype) and 'label' not in voltype:
                    segvols.append(SegVols()[voltype])
                    segvoltypes.append(voltype)

        try: os.mkdir(volumedir)
        except: pass

        for vol in segvols:

            resampledvol = os.path.join(volumedir,vol)
            if not isfile(resampledvol):
                fullOut('Resampling ' + vol + ' for ' + subj,thinline)
                # Set the inputs

                resample = fs.ApplyVolTransform()
            
                resample.inputs.targfile = os.path.join(fsSubjDir,subj,'mri',vol)
                resample.inputs.sourcefile = funcvol
                resample.inputs.outfile = resampledvol
                resample.inputs.tkreg = regmat
                resample.inputs.inverse = True
                resample.inputs.interp = 'nearest'           

                # Run mri_vol2vol
                res = resample.run()
                cmdOut(resample,res)
            else:
                shortOut('Found ' + resampledvol)
        
            # Print a summarry of the voxel counts in each ROI with mri_segstats 
            statsdir = os.path.join(svsubjdir,'stats')
            try: os.mkdir(statsdir)
            except: pass 
            segstatsfile = os.path.join(statsdir,vol + '.stats') 
            if not isfile(segstatsfile):
                fullOut('Running segmentation statistics \
                         on %s for %s' % (vol,subj),thinline)
                # Set the inputs

                segstats = fs.SegStats()

                segstats.inputs.segvol = resampledvol
                segstats.inputs.invol = resampledvol
                segids = fsroidict.Rois(vol).keys()
                segids.sort()
                if RoiSpace(vol) == 'surface':
                    segids = [int(i-(N.floor(i/100)*100)) for i in segids]
                segstats.inputs.segid = segids
                segstats.inputs.sumfile = segstatsfile
            
                # Run mri_segstats
                res = segstats.run()
                cmdOut(segstats,res)
            else:
                shortOut('Found '+ segstatsfile)

        """        
        # Make a segmentation volume from labels, if label ROIs exist
        if 'label_seg' in SegVols().keys():
            origvol = os.path.join(fsSubjDir,subj,'mri/orig.mgz')
            labeldir = os.path.join(fsSubjDir,subj,'label')
            for hemi in ['lh','rh']:
                hemivol = os.path.join(volumedir,hemi + '_labels.mgz')
                if not isfile(hemivol):
                    fullOut('Projecting '+hemi+' labels into the colume for '+subj,thinline)
      
                    # Set the inputs
  
                    projlabel = fs.Label2Vol()
                      
                    labels = []
                    labids = Labels(hemi).keys()
                    labids.sort()
                    for id in labids:
                        labels.append(labeldir+'/'+Labels(hemi)[id])
                        projlabel.inputs.label = labels
                    projlabel.inputs.templatevol = origvol
                    projlabel.inputs.identity = True
                    projlabel.inputs.proj = ['frac',0,1,.1]
                    projlabel.inputs.subjectid = subj
                    projlabel.inputs.hemi = hemi
                    projlabel.inputs.outvol = hemivol
                    projlabel.inputs.fillthresh = 0.5

                    # Run mri_label2vol
                    res = projlabel.run()
                    cmdOut(projlabel,res)
                else:
                    shortOut('Found ' + hemivol)

            # Adjust the segids of the right hemisphere volume
            adjrhvol = os.path.join(volumedir,'adj_rh_labels.mgz')
            if not isfile(adjrhvol):
                fullOut('Adjusting rh label IDs for ' + subj,thinline)
  
                # Set the inputs

                adjseg = fs.Concatenate()

                adjseg.inputs.invol = os.path.join(volumedir,'rh_labels.mgz')
                adjseg.inputs.outvol = adjrhvol
                adjseg.inputs.mul = Labels('adjust')
      
                # Run mri_concat
                res = adjseg.run()
                cmdOut(adjseg,res)
            else:
                shortOut('Found ' + adjrhvol)


            # Combine the left and right hemisphere label seg vols
            origlabelsegvol = os.path.join(volumedir,'orig_label_seg.mgz')
            lhvol = os.path.join(volumedir,'lh_labels.mgz')
            rhvol = os.path.join(volumedir,'adj_rh_labels.mgz')
            if not isfile(origlabelsegvol):
                fullOut('Merging label volumes for ' + subj)
  
                # Set the inputs

                mergevols = fs.Concatenate()

                mergevols.inputs.invol = [lhvol,rhvol]
                mergevols.inputs.outvol = origlabelsegvol
                mergevols.inputs.sum = True
 
                # Run mri_concat
                res = mergevols.run()
                cmdOut(mergevols,res)
            else:
                shortOut('Found ' + origlabelsegvol)

            # Resample the label seg volume into functional space
            labelsegvol = os.path.join(volumedir,'label_seg.mgz')
            if not isfile(labelsegvol):
                fullOut('Resampling label_seg for ' + subj)
                # Set the inputs

                resample = fs.ApplyVolTransform()
            
                resample.inputs.targfile = origlabelsegvol
                resample.inputs.sourcefile = funcvol
                resample.inputs.outfile = labelsegvol
                resample.inputs.tkreg = regmat
                resample.inputs.inverse = True
                resample.inputs.interp = 'nearest'           

                # Run mri_vol2vol
                res = resample.run()
                cmdOut(resample,res)
            else:
                shortOut('Found ' + labelsegvol)

            # Print a summary of the label seg volume
            labelstats = os.path.join(statsdir,'label_seg.mgz.stats')
            if not isfile(labelstats):
                fullOut('Running segmentation statistics on ' + labelsegvol + ' for ' + subj)
                # Set the inputs

                segstats = fs.SegStats()

                segstats.inputs.segvol = labelsegvol
                segstats.inputs.invol = labelsegvol
                segids = Labels('fullids')
                segids.sort()
                segstats.inputs.segid = segids
                segstats.inputs.sumfile = labelstats
            
                # Run mri_segstats
                res = segstats.run()
                cmdOut(segstats,res)
            else:
                shortOut('Found ' + labelstats)

        """
#-------------------------------------------------------------------------------#
# Concatenate the task beta volumes into one volume for analysis 
#-------------------------------------------------------------------------------#


for par in analysisPars:
    fullOut('Creating beta volumes for ' + par + ' analysis',thickline)
    for subj in subjList:
        modeldir = os.path.join(l1output,par,subj,'model')
        betavol = os.path.join(modeldir,'task_betas.mgz')
        if not isfile(betavol):
            fullOut('Concatenating task betas for ' + subj,thinline)
            # Set the inputs

            concat = fs.Concatenate()

            volumes = []
            for img in Betas(par,'images'):
                volumes.append(os.path.join(modeldir,img))
            concat.inputs.invol = volumes
            concat.inputs.outvol = betavol
            
            # Run mri_concat            
            res = concat.run()
            cmdOut(concat,res)
        else:
            shortOut('Found ' + betavol)


#-------------------------------------------------------------------------------#
# Convert the spmT maps to -log10(p) volumes for masking 
#-------------------------------------------------------------------------------#

conCell = '{'
for par in analysisPars:
    for subj in subjList:
        conDir = os.path.join(l1output,par,subj,'contrasts')
        tmaps = glob(os.path.join(conDir,'spmT*.img'))
        doCon = None
        for tmapimg in tmaps:
            l = len(tmapimg)
            imgnum = tmapimg[l-8:l-4]
            pmapimg = os.path.join(conDir,'spmP_' + imgnum + '.nii')
            if not isfile(pmapimg):
                doCon = True
            if doCon:
                conCell = conCell + '\'' + \
                conDir  + '\','
            else:
                shortOut('Found %s for %s' % (pmapimg,par))

            if conCell != '{':
                conCell = conCell[0:len(conCell)-1]
                conCell = conCell + '}'
                command = 'spm_t2sig(' + conCell + ')'
                shortOut(command)
                mlcmd = mlab.MatlabCommandLine()
                mlcmd.inputs.script_lines = command
                mlcmd.mfile = True
                res = mlcmd.run()
                shortOut(res.runtime.stdout)

#-------------------------------------------------------------------------------#
# Print some files that will be used when assembling the database 
#-------------------------------------------------------------------------------#

# Print a full subject list
shortOut('\nWriting subject list\n')
subjtxt = open(os.path.join(projectdir,'subjectlist.txt'),'w')
for subj in subjList:
    subjtxt.write(subj + '\t')
subjtxt.close()

# Print a list of the groups
shortOut('\nWriting group lists\n')
grptxt = open(os.path.join(projectdir,'grouplist.txt'),'w')
for group in Subjects('groups'):
    grptxt.write(group + '\t')
    grpfile = open(os.path.join(projectdir,group + 'list.txt'),'w')
    for subj in Subjects(group):
       grpfile.write(subj + '\t')
grpfile.close()
grptxt.close()

# Print out lists of our ROI names and ids 
roilistDir = os.path.join(projectdir,'roilists')
try: os.mkdir(roilistDir)
except: pass

shortOut('\nWriting ROI lists\n')

segvoltext = open(os.path.join(roilistDir,'segvols.txt'),'w')
segnametext = open(os.path.join(roilistDir,'segvolnames.txt'),'w')
vollist = SegVols().keys()
vollist.sort()
for voltype in vollist:
    if Regions(voltype):
        segvoltext.write(voltype + '\t')
        segnametext.write(SegVols(voltype) + '\t')

        roinames = open(os.path.join(roilistDir,voltype + '_roi_names.txt'),'w')
        roikeys = open(os.path.join(roilistDir,voltype + '_roi_ids.txt'),'w')
        roivalues = open(os.path.join(roilistDir,
                                      SegVols(voltype) + '_roi_ids.txt'),'w')
        if voltype == 'label_seg':
            for name in Labels('realnames'):
                roinames.write(name + '\t')
        for roiID in Regions(voltype):
            if voltype != 'label_seg':
                roinames.write(fsroidict.Rois(SegVols(voltype),
                               RoiSpace(voltype))[roiID] + '\t')
                roikeys.write(str(roiID) + '\t')
                roivalues.write(str(roiID) + '\t')
roinames.close()
segvoltext.close()
segnametext.close() 
roinames.close()
roikeys.close()
roivalues.close()


#-------------------------------------------------------------------------------#
# Run the functional ROI analysis 
#-------------------------------------------------------------------------------#


# Iterate through the list of analyses
for anparams in analysis:
    # Format the names for storage purposes
    if 'maskpar' in anparams.keys(): 
        maskstring = Paradigms(anparams['maskpar'],'lower')+'-'+\
                                        anparams['maskcon']+'-'+\
                                        str(anparams['maskthresh'])
    else:       
        maskstring = 'nomask'
    analname = Paradigms(anparams['par'],'upper') + '_' + maskstring
    fullOut('Running functional analysis for ' + analname,thickline)
    # Check to see if analysis exists, error out if yes, make directory if no
    try: os.mkdir(os.path.join(projectdir,analname)) 
    except: pass

    for vol in SegVols().keys():
        if Regions(vol):
            try: os.mkdir(os.path.join(projectdir,analname,vol))
            except: pass
        
        for txtdir in ['avgwf','segsum']:
            try: os.mkdir(os.path.join(projectdir,analname,vol,txtdir))
            except: pass

    
    # Print a list of the beta conditions
    shortOut('Writing task regressor list\n')
    betalist = open(os.path.join(projectdir,analname,'beta_list.txt'),'w')
    for cond in Betas(anparams['par']):
       betalist.write(cond + '\t')
    betalist.close()

    # Iterate through the subjects
    for subj in subjList:     
        fullOut('Running functional stats for ' + subj,thinline)
        # Iterate through the four segmentation volumes 
        for segkey in SegVols().keys():
            # Make sure we're looking at ROIs in this segmentation, skip if not
            doSeg = None
            if Regions(segkey):
                    doSeg = True
            analPar = anparams['par']
            firstleveldir = os.path.join(l1output,analPar,subj)
            svsubjdir = os.path.join(segvoldir,analPar,subj)
            if RoiSpace(segkey) == 'volume':
                funcvolfile = os.path.join(firstleveldir,'model/task_betas.mgz')
                segvolfile = os.path.join(svsubjdir,'volumes',SegVols(segkey))
            else:
                hemi = segkey[-2] + 'h'
                funcvolfile = os.path.join(firstleveldir,'model/'+hemi+'.task_betas.mgz')
                segval = SegVols(segkey)
                annotfile = [subj,hemi,segval[3:len(segval)]]
            avgwfdir = os.path.join(projectdir,analname,segkey,'avgwf')
            segsumdir = os.path.join(projectdir,analname,segkey,'segsum')


            if doSeg:
                # Set the input variables

                funcroi = fs.SegStats()

                if RoiSpace(segkey) == 'volume':
                    funcroi.inputs.segvol = segvolfile
                else:
                    funcroi.inputs.annot = annotfile
                ids = Regions(segkey)
                if RoiSpace(segkey) == 'surface':
                    ids = [int(i-(N.floor(i/100)*100)) for i in ids]
                funcroi.inputs.segid = ids
                funcroi.inputs.sumfile = os.path.join(segsumdir,subj + '.txt')
                funcroi.inputs.invol = funcvolfile
                if 'maskpar' in anparams.keys():
                    maskcon = anparams['maskcon']
                    maskpar = anparams['maskpar']
                    maskdict = Contrasts(maskpar,'P-map','.nii')
                    if RoiSpace(segkey) == 'volume':
                        funcroi.inputs.maskvol = os.path.join(l1output,maskpar,subj,'contrasts',
                                                              maskdict[maskcon])
                    else:
                        funcroi.inputs.maskvol = os.path.join(l1output,maskpar,subj,'contrasts',
                                                              hemi +'.'+ maskdict[maskcon]) 
                    funcroi.inputs.maskthresh = anparams['maskthresh']
                    if 'masksign' not in anparams.keys():
                        sign = 'pos'
                    else:
                        sign = anparams['masksign']
                    funcroi.inputs.masksign = sign
                funcroi.inputs.avgwftxt = os.path.join(avgwfdir,subj + '.txt')

                # Run mri_segstats
                res = funcroi.run()
                cmdOut(funcroi,res)

#-------------------------------------------------------------------------------#
# Assemble the database
#-------------------------------------------------------------------------------#

fullOut('Assembling analysis database',thickline)

# Make the database directory if it doesn't exist
shortOut('\nCreating database directory structure\n')
roidatadir = os.path.join(projectdir,'roidatabases')
outsumdir = os.path.join(roidatadir,'outliers')
winsdir = os.path.join(roidatadir,'winsor_databases')
trimdir = os.path.join(roidatadir,'trimmed_databases')
for dir in [roidatadir,outsumdir,winsdir,trimdir]:
    try: os.mkdir(dir)
    except: pass

# Initialize our main arrays
head = N.array(([],),str)
data = N.array(([],),float)

segList = SegVols().keys()
segList.sort()

# Iterate through each analysis
for anparams in analysis:
    # Set up the header
    betas = Betas(anparams['par'])
    if 'maskpar' in anparams.keys(): 
        maskstring = Paradigms(anparams['maskpar'],'lower')+'-'+\
                                        anparams['maskcon']+'-'+\
                                        str(anparams['maskthresh'])
    else:       
        maskstring = 'nomask'
    analname = Paradigms(anparams['par'],'upper') + '_' + maskstring
    for hemi in ['lh','rh']:
        suffices = ['voxels'] + betas
        for suffix in suffices:
            try: head = N.hstack((head,N.array(([analname+'_'+suffix+'_'+hemi],))))
            except ValueError: head = N.array(([analname+'_'+suffix+'_'+hemi],))
    # Set up the data array
    analdata = N.array(([],),float)
    for subj in subjList:
        subjdata = N.array(([],),float)
        for vol in segList:
            volDir = os.path.join(projectdir,analname,vol)
            voldata = N.genfromtxt(os.path.join(volDir,'avgwf',subj+'.txt'))
            if voldata.ndim == 1: voldata = N.array((voldata,))
            voldata = voldata.transpose()
            voxdata = N.genfromtxt(os.path.join(volDir,'segsum',subj+'.txt'),int)
            voxdata = N.array((voxdata[:,2],))
            voxdata = voxdata.transpose()
            voldata = N.hstack((voxdata,voldata))
            if RoiSpace(vol) == 'volume':
                [left,right] = N.vsplit(voldata,2)
                voldata = N.hstack((left,right))
                lefthemi = N.array(([],),float)
                if not subjdata.any(): subjdata = voldata
                else: subjdata = N.vstack((subjdata,voldata))
            elif lefthemi.any(): 
                righthemi = voldata
                voldata = N.hstack((lefthemi,righthemi))
                if not subjdata.any(): subjdata = voldata
                else: subjdata = N.vstack((subjdata,voldata))
                lefthemi = N.array(([],),float)
            else: 
                lefthemi = voldata
        if not analdata.any(): analdata = subjdata
        else: analdata = N.vstack((analdata,subjdata))
    if not data.any(): data = analdata
    else: data = N.hstack((data,analdata))

# Set up the subject and groups columns
datalen = data.shape[0]
numrows = datalen/len(subjList)
subs = N.array(([],),str)
groups = N.array(([],),str)
for subj in subjList:
    for row in range(numrows):
        if not subs[0]: subs = N.array(([subj],))
        else: subs = N.vstack((subs,N.array(([subj],))))
        if not groups[0]: groups = N.array(([Subjects(subject=subj)]))
        else: groups = N.vstack((groups,N.array([Subjects(subject=subj)])))

# Set up the ROI and space columns
rois = N.array(([],),str)
space = N.array(([],),str)
for subj in subjList:
    for vol in segList:
        volrois = N.array(([],),str)
        volids = N.array((Regions(vol),))
        volids = volids.transpose()
        for id in volids:
            id = id[0]
            name = fsroidict.Rois(SegVols(vol),RoiSpace(vol))[id]
            h = re.search('(([lr]h)|([lL]eft|[rR]ight))[-_\.]',name)
            h = h.group()
            name = name[len(h):len(name)]
            if not volrois[0]: volrois = N.array(([name],))
            else: volrois = N.vstack((volrois,N.array(([name]),)))
        if RoiSpace(vol) == 'volume':
            volrois = N.vsplit(volrois,2)[0]
        if not 'rh' in vol:
            if not rois[0]: rois = volrois
            else: rois = N.vstack((rois,volrois))
            volspace = RoiSpace(vol)
            for i in range(len(volrois)):
                if not space[0]: space = N.array(([volspace],))
                else: space = N.vstack((space,N.array(([volspace],))))

# Set the unmasked voxel count columns and header
vox = N.array(([],),int)
voxhead = N.array(([],),int)
volvox = N.array(([],),int)
for par in analysisPars:
    parvox = N.array(([],),int)
    for subj in subjList:
        subjvox = N.array(([],),int)
        for vol in segList:
            if RoiSpace(vol) == 'volume' or 'rh' not in vol:
                volvox = N.array(([],),int)
            else:
                leftvolvox = volvox
            fullstats = N.genfromtxt(os.path.join(segvoldir,par,subj,'stats',SegVols(vol)+'.stats'),int)
            if fullstats.ndim == 1: fullstats = N.array((fullstats,))
            for row in range(fullstats.shape[0]):
                if fullstats[row,1] in Regions(vol):
                    if not volvox.any(): volvox = N.array((fullstats[row,2],))
                    else: volvox = N.vstack((volvox,N.array((fullstats[row,2],))))
            if RoiSpace(vol) == 'volume' or 'rh' in vol:
                [left,right] = N.vsplit(volvox,2)
                volvox = N.hstack((left,right))
                if not subjvox.any(): subjvox = volvox
                else: subjvox = N.vstack((subjvox,volvox))
        if not parvox.any(): parvox = subjvox
        else: parvox = N.vstack((parvox,subjvox))
    if not vox.any(): vox = parvox
    else: vox = N.hstack((vox,parvox))
    try: voxhead = N.hstack((voxhead,N.array(([par+'base_voxels_lh',par+'base_voxels_rh'],))))
    except ValueError: voxhead = N.array(([par+'_lh',par+'_rh'],))
head = N.hstack((voxhead,head))
head = N.hstack((N.array((['Subject','Group','ROI','Space'],)),head))


database = N.hstack((subs,groups,rois,space,vox,data))
database = N.vstack((head,database))
shortOut('Saving analysis database\n')
dbfile = os.path.join(projectdir,'roidatabases',ProjectName()+'_roidata_'+timeStamp+'.txt')
N.savetxt(dbfile,database,fmt='%s',delimiter='\t')
shortOut('Your database printed to %s' % dbfile)
fullOut('Analysis done',thickline)