"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu

"""

import os
import re
import sys
import shutil
import datetime
import numpy as N
import roiutils as roi
import pyroilut as lut
from glob import glob
from nipype.interfaces import freesurfer as fs
from nipype.interfaces import matlab as mlab
from nipype.interfaces import base

# If the script is not run with one argument, print the docstring and exit
if len(sys.argv) != 2:
    print __doc__
    sys.exit(0)
# Otherwise, get the config module to use from the command line
else:
    configmod = sys.argv[1]

# Import the config module, trying two different ways
try:
    cfg = __import__('config%s' % configmod)
    print '\nImporting config%s module\n' % configmod
except ImportError:
    cfg = __import('%s' % configmod)
    print '\nImporting %s module\n' % configmod

# Get the project name
projname = cfg.projectname()

# Get the analysis parameters 
analysis = cfg.analysis()

# Get our subject list
if projname == 'development':
    subjList = ['SAD_022','SAD_033']
else:
    subjList = cfg.subjects()

# Get our dictionary of atlases
atlases = cfg.atlases()

# Set up some directory variables
fssubjdir = cfg.subjDir()
maindir = os.path.abspath('.')
l1output = os.path.join(maindir,'surface','l1output')

roidir = os.path.join(miandir,'roi')

analysisdir = os.path.join(roidir,'analyses')
projectdir = os.path.join(analysisdir,cfg.projectName())
logdir = os.path.join(projectdir,'logfiles')
dbdir = os.path.join(projectdir,'databases')

atlasdir = os.path.join(maindir,'roi','atlases')
fsatlasdir = os.path.join(atlasdir,'freesurfer')
talatlasdir = os.path.join(atlasdir,'talairach')
maskatlasdir = os.path.join(atlasdir,'mask')
labelatlasdir = os.path.join(atlasdir,'label')

projmaskdir = os.path.join(maskatlasdir,projname)
projlabeldir = os.path.join(labelatlasdir,projname)

# Create the analysis directory structure
roi.make_analysis_dirs(roidir, cfg)

# Create the atlas directory structures
roi.make_fs_atlas_dirs(roidir, cfg)

# Make roi directories, if they don't exist
if not os.path.isdir(os.path.join(maindir,'roi')):
    os.mkdir((os.path.join(maindir,'roi'))

roidirs = [atlasdir,analysisdir,projectdir,logdir,fsatlasdir,
           talatlasdir,maskatlasdir,labelatlasdir,projmaskdir,
           projlabeldir]

for dir in roidirs:
    if not os.path.isdir(dir):
        os.mkdir(dir)

# Find out what functional paradigms will be analyzed in this project
analysisPars = set()
for anparams in analysis:
    analysisPars.add(anparams['par'])


# Set some variables we'll use when we print to the terminal/log
thinline = '----------------------------------------------------------------------'
thickline = '======================================================================'

# Some little functions for controlling terminal and logfile output
def fullout(message,line):
    print
    print line
    print message
    print line
    print
    lf.write('\n'+line+'\n'+message+'\n'+line+'\n\n')

def cmdout(cmdline, res):
    print cmdline
    print
    print res.runtime.stdout
    print res.runtime.stderr
    print
    lf.write(cmd.cmdline+'\n\n'+res.runtime.stdout+'\n'+res.runtime.stderr+'\n\n')

def shortout(message):
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
timeStamp = '%s%s%s-%s%s' % (nowyear, nowmonth, nowday, nowhour, nowminute)


# Open up the log file and print important information
logpath = (os.path.join(logdir,projname + '_' + timeStamp + '.log'))
            
lf = open(logpath,'w')

print 'NiPyRoi Analysis'
print now[0:16]
print os.getcwd()
print 'User: ' + os.getlogin()
print 'Project name: ' + projname
print 'Config module: ' + cfg.__file__
print 'Log file is ' + logpath
print

lf.write('NiPyRoi Analysis \n' + now[0:16] + '\n' + os.getcwd() + 
              '\nUser: ' + os.getlogin() + '\n' + 'Project name: ' + projname + '\n' 
              'Config module: ' + __file__ + '\nLog file is ' + logpath + '\n\n')
 


#===============================================================================#
# Set up the ROI atlases
#===============================================================================#

fullout('Preparing ROI atlases for extraction', thickline)

#-------------------------------------------------------------------------------#
# Registration
#-------------------------------------------------------------------------------#

doReg = any([i for i in atlases if 
                        atlases[i]['source'] == 'freesurfer' or 'label'])

# Register the mean functional for each analyzed paradigm to native Freesurfer
# space if any atlases are in the native volume or on the surface
if doReg:
    register = FSRegister(fsatlasdir, fssubjdir) 
    for par in analysisPars:
        fullout('Creating registration matrices for %s paradgim' % par,thinline)
        for subj in subjList:
            register.init_subj(par, subj)
            if not os.path.isfile(register.regmat) or cfg.overwrite('registration')
                cmdline, res = register.register()
                cmdout(cmdline, res)
            else:
                shortout('Found %s' % register.regmat)

#-------------------------------------------------------------------------------#
# Freesurfer Volume Resampling
#-------------------------------------------------------------------------------#

# Make a list of atlases to resample
fs_vols =  []
for atlas in atlases.keys():
    if atlases[atlas]['source'] == 'freesurfer' and \
       atlases[atlas]['space'] == 'volume':
        fs_vols.append(atlases[atlas])

for atlas in fs_vols:
    fullout('Resampling %s volumes into functional space' \
            % atlas['atlasname'], thickline)
    resample = roi.FreesurferAtlas(atlas, fsatlasdir, fssubjdir)
        for par in analysisPars:
            for subj in subjList:
                # Resample the Freesurfer segmentations into functional space
                resample.init_subj(par, subj, roi.meanfunc(cfg, par, subj)
                if not os.path.isfile(resample.atlas) or \
                       cfg.overwrite('resampled_volumes'):
                    cmdline, res = resample.resample()
                    cmdout(cmdline, res)
                else:
                    shortout('Found %s' % resample.atlas)

                # Generate full segmentation statistics
                if not os.path.isfile(resample.statsfile) or \
                       cfg.overwrite('atlas_stats'):
                    cmdline, res = resample.stats()
                    cmdout(cmdline, res)
                else
                    shortout('Found %s' % resample.statsfile)


#-------------------------------------------------------------------------------#
# Freesurfer Surface Copying
#-------------------------------------------------------------------------------#

fs_surfs = []
for atlas in atlases.keys()
    if atlases[atlas]['source'] == 'freesurfer' and \
       atlases[atlas]['space'] == 'surface':
        fs_surfs.append(atlases[atlas])


for atlas in fs_surfs:
    fullout('Preparing %s annotations' % atlas['atlasname'], thickline)
    annot = roi.FreesurferAtlas(atlas, fsatlasdir, fssubjdir)
        for par in analysisPars:
            for subj in subjList:
                # Copy the annot from the fs label dir to the roi atlas dir
                annot.init_subj(par, subj)
                if not os.path.isfile(annot.atlas) or \
                       cfg.overwrite('freesurfer_annots'):
                    annot.copy()
                # Generate full annotation statistics
                if not os.path.isfile(annot.statsfile) or \
                       cfg.overwrite('atlas_stats'):
                    cmdline, res = annot.stats()
                    cmdout(cmdline, res)
                else
                    shortout('Found %s' % annot.statsfile)


#===============================================================================#
# Prepare the first level data sources
#===============================================================================#


for par in analysisPars:
    fullout('Creating beta volumes for ' + par + ' analysis',thickline)
    for subj in subjList:
        modeldir = os.path.join(l1output,par,subj,'model')
        betavol = os.path.join(modeldir,'task_betas.mgz')
        if not isfile(betavol):
            fullout('Concatenating task betas for ' + subj,thinline)
            # Set the inputs

            concat = fs.Concatenate()

            volumes = []
            for img in Betas(par,'images'):
                volumes.append(os.path.join(modeldir,img))
            concat.inputs.invol = volumes
            concat.inputs.outvol = betavol
            
            # Run mri_concat            
            res = concat.run()
            cmdout(concat,res)
        else:
            shortout('Found ' + betavol)


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
                shortout('Found %s for %s' % (pmapimg,par))

            if conCell != '{':
                conCell = conCell[0:len(conCell)-1]
                conCell = conCell + '}'
                command = 'spm_t2sig(' + conCell + ')'
                shortout(command)
                mlcmd = mlab.MatlabCommandLine()
                mlcmd.inputs.script_lines = command
                mlcmd.mfile = True
                res = mlcmd.run()
                shortout(res.runtime.stdout)


#===============================================================================#
# Run the functional ROI extraction
#===============================================================================#

for atlasdict in atlases.values():
    atlas = roi.init_atlas(atlasdict)
    fullout('Extracting data with %s atlas' % atlas.atlasname, thickline)
    for anal in analysis:
        fullout('Extracting data for %s analysis' % roi.get_analysis_name(anal),
                thickline)
        anparams = roi.Analysis(anal)
        for subj in subjlist:
            fullout('Extracting data for %s' % subj, thinline)
            atlas.init_subj(analysis.par, subj)
            atlas.init_analysis(cfg, anparams)
            for datafile in [atlas.functxt, atlas.funcvol, atlas.funcstats]:
                if not os.path.isfile(datafile) or cfg.overwrite('extractions')
                    cmdline, res = atlas.extract()
                    cmdout(cmdline, res)
                else:
                    shortout('Found %s' % datafile)



#===============================================================================#
# Assemble the database
#===============================================================================#

fullout('Assembling analysis database',thickline)

# Make the database directory if it doesn't exist
shortout('\nCreating database directory structure\n')
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
            fullstats = N.genfromtxt(os.path.join(atlasdir,par,subj,
                                                  'stats',SegVols(vol)+'.stats'),int)
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
shortout('Saving analysis database\n')
dbfile = os.path.join(projectdir,'roidatabases','%s_roidata_%s.txt' % (projname,timeStamp))
N.savetxt(dbfile,database,fmt='%s',delimiter='\t')
shortout('Your database printed to %s' % dbfile)
fullout('Analysis done',thickline)
