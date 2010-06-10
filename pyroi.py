"""Library for fMRI region of interest analysis with NiPyPE interfaces"""
import os
import re
import sys
import shutil
import subprocess
import numpy as np
import pyroilut as lut
import configinterface as cfg
import scipy.stats as stats
import nibabel as nib
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.base import Bunch
from glob import glob

class Analysis(Bunch):
    """Analysis object."""
    def __init__(self, cfg, analysis):
        
        self.dict = analysis
        self.cfg = cfg
        self.paradigm = analysis['par']
        self.extract = analysis['extract']
        self.name = get_analysis_name(cfg, analysis)
        if 'maskpar' in analysis.keys() and \
           analysis['maskpar'] != 'nomask':
            self.mask = True
            self.maskpar = analysis['maskpar']
            self.maskcon = analysis['maskcon']
            self.maskthresh = analysis['maskthresh']
            if 'masksign' in analysis.keys():
                self.masksign = analysis['masksign']
            else:
                self.masksign = 'abs'
        else:
            self.mask = False
 

class Atlas(Bunch):
    """Base atlas class."""
    
    def __call__(self, analysis):

        self.init_analysis(analysis)
    
    # Initialization methods
    def init_analysis(self, analysis):
        """Initialize the atlas with an analysis."""
        self.analysis = analysis
        self.__init_analysis = True 
        if analysis.mask:
            self.mask = True
            maskpath = analysis.cfg.pathspec('contrasts', analysis.maskpar,
                                             self.subject, analysis.maskcon)
            maskfile = '%s%s' % (self.atlasprefix, 
                        analysis.cfg.contrasts(analysis.maskpar, 
                                               'sig',)[analysis.maskcon])
            self.analysis.maskimg = os.path.join(maskpath, maskfile)
            self.analysis.maskthresh = analysis.maskthresh
            self.analysis.masksign = analysis.masksign

        
        sourcedict = \
        {'betas' : os.path.join(analysis.cfg.pathspec('beta', self.par, 
                                                      self.subject),
                                '%stask_betas.mgz' % self.atlasprefix),
         'contrast' : os.path.join(analysis.cfg.pathspec('contrast', self.par,
                                   self.subject),
                                   '%sall_contrasts.mgz' % self.atlasprefix),
         'timecourse' : os.path.join(analysis.cfg.pathspec('timecourse', self.par, 
                                     self.subject))} #XXX figure this out

        self.analysis.source = sourcedict[analysis.extract]

        self.analysis.dir = os.path.join(self.basedir, 'analyses', 
                                        analysis.cfg.projectname(), 
                                        get_analysis_name(analysis.cfg, 
                                                          analysis.dict))

        self.funcstats = os.path.join(self.analysis.dir, 'stats', 
                                      '%s.stats' % self.subject)
        self.functxt = os.path.join(self.analysis.dir, 'avgwftxt',
                                    '%s.avgwf' % self.subject)
        self.funcvol = os.path.join(self.analysis.dir, 'avgwfvol',
                                    '%s.nii' % self.subject)
         

    # Operation methos
    def copy_atlas(self):
        """Copy original atlas file to pyroi atlas tree"""
        shutil.copy(self.origatlas, self.atlas)  

    def nipype_run(self, interface):
        """Run a program using its nipype interface"""
        if self.debug:
            return interface.cmdline, None
        else:
            res = interface.run()
            return interface.cmdline, res

    def manual_run(self, cmd):
        """Run a freesurfer program that lacks a nipype interface"""
        cmdline = cmd[0]
        for i, component in enumerate(cmd):
            if i != 0:
                cmdline = '%s %s' % (cmdline, component)
        if self.debug:
            return cmdline, None
        else:
            res = subprocess.call(cmd)
            return cmdline, res
    # Processing methods
    def stats(self):
        """Generate a summary of voxel/vertex counts for all regions in an atlas."""
        segstats = fs.SegStats()

        if self.space == 'volume':
            segstats.inputs.segvol = self.atlas
        else:
            segstats.inputs.annot = self.atlas
        segstats.inputs.invol = self.atlas
        segstats.inputs.segid = self.lut.keys()
        segstats.inputs.sumfile = self.statsfile

        cmdline, res = self.nipype_run(segstats)
        return cmdline, res
     
    def extract(self):
        """Extract average functional data from select regions in an atlas."""
        funcex = fs.SegStats()

        if self.space == 'volume':
            funcex.inputs.segvol = self.atlas
        else:
            funcex.inputs.annot = self.atlas
        funcex.inputs.invol = self.analysis.source

        funcex.inputs.segid = self.regions
        
        if self.mask:
            funcex.inputs.maskvol = self.analysis.maskimg
            funcex.inputs.maskthresh = self.analysis.maskthresh
            funcex.inputs.masksign = self.analysis.masksign
        
        funcex.inputs.sumfile = self.funcstats
        funcex.inputs.avgwftxt = self.functxt
        funcex.inputs.avgwfvol = self.funcvol

        cmdline, res = self.nipype_run(funcex)
        return cmdline, res


    def group_stats(self, subjects, par=None):
        """Get atlas statistics for a group of subjects"""
        if par is None:
            par = ''
        for subj in subjects:
            self.init_subject(subj, par)
            cmdline, res = self.stats()
            if self.debug:
                print '\n%s\n\n' % cmdline
            else:
                print '\n%s\n\n%s\n%s' % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

    def group_extract(self, analysis, subjects):
        """Extract functional data for a group of subjects."""
        for subj in subjects:
            self.init_subject(subj, analysis.paradigm)
            self.init_analysis(analysis)
            cmdline, res = self.extract()
            if self.debug:
                print '\n%s\n\n' % cmdline
            else:
                print '\n%s\n\n%s\n%s' % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

class FreesurferAtlas(Atlas):
    """Atlas class for a Freesurfer atlas"""
    def __init__(self, atlasdict, roidir=None, subjdir=None, **kwargs):
       
        if roidir is None:
            self.roidir = os.path.join(os.path.abspath(os.curdir),'roi')
        if subjdir is None:
            subjdir = os.getenv('FREESURFER_HOME')
        
        self.atlasdict = atlasdict
        self.atlasname = atlasdict['atlasname']
        self.fname = atlasdict['fname']
        self.space = atlasdict['space']
        self.regions = atlasdict['regions']
        if self.space == 'surface':
            self.hemi = atlasdict['hemi']

        self.lut = lut.freesurfer(self.fname)

        self.basedir = os.path.join(self.roidir, 'atlases', 'freesurfer')
        self.subjdir = subjdir

        self._init_subject = False
        self.__init_analysis = True

        self.__dict__.update(**kwargs)
        if 'debug' not in self.__dict__:
            self.debug = False

    # Initialization methods
    def init_subject(self, subject, par=None, meanfuncimg=None):
       """Initialize the atlas for a subject and analysis paradigm"""
       self.subject = subject
       if par is None:
           self.par = ''
       else:
           self.par = par
       if self.space == 'surface':
           self.pardir = ''
           self.atlasprefix = self.hemi + '.'
           self.origdir = 'label'
           self.atlasext = 'annot'
       else:
           self.pardir = par
           self.atlasprefix = ''
           self.origdir = 'mri'
           self.atlasext = 'mgz'
       self.meanfuncimg = meanfuncimg
       self.regmat = os.path.join(self.roidir, 'reg', self.par,
                                  subject, 'func2orig.dat')

       if self.space != 'reg':
           self.statsfile = os.path.join(self.basedir, self.space, self.pardir,
                                         self.subject, self.atlasname,
                                         '%s.stats' % self.atlasname)
           self.origatlas = os.path.join(self.subjdir, subject, 
                                         self.origdir, self.fname)
           self.atlas = os.path.join(self.basedir, self.space, self.pardir,
                                     self.subject, self.atlasname,
                                     '%s%s.%s' % (self.atlasprefix, 
                                                  self.atlasname, 
                                                  self.atlasext))
       
           self._init_subject = True

    # Processing methods
    def resample(self):
        """Resample a freesurfer volume atlas into functional space"""
        transform = fs.ApplyVolTransform()

        transform.inputs.targfile = self.origatlas
        transform.inputs.sourcefile = self.meanfuncimg
        transform.inputs.tkreg = self.regmat
        transform.inputs.inverse = True
        transform.inputs.interp = 'nearest'
        transform.inputs.outfile = self.atlas

        cmdline, res = self.nipype_run(transform)
        return cmdline, res


class FSRegister(FreesurferAtlas):
    """Freesurfer atlas for registration"""

    def __init__(self, roidir=None, subjdir=None, **kwargs):

        if roidir is None:
            self.roidir = os.path.join(os.path.abspath(os.curdir),'roi')
        if subjdir is None:
            subjdir = os.getenv('FREESURFER_HOME')
        
        self.space = 'reg'
        self.fname = 'orig.mgz'
        self.atlasname = 'register'

        self.basedir = os.path.join(roidir, 'atlases', 'reg')
        self.subjdir = subjdir
        
        self.__dict__.update(**kwargs)
        if 'debug' not in self.__dict__:
            self.debug = False
            
    # Processing methods
    def register(self):
        """Register functional space to Freesurfer original atlas space"""
        reg = fs.BBRegister()

        reg.inputs.subject_id = self.subject
        reg.inputs.sourcefile = self.meanfuncimg
        reg.inputs.init_fsl = True
        reg.inputs.t2_contrast = True
        reg.inputs.outregfile = self.regmat       

        cmdline, res = self.nipype_run(reg)
        return cmdline, res

class TalairachAtlas(Atlas):

    def __init__(self, atlasdict, roidir):
        
        pass

class LabelAtlas(Atlas):
    """Atlas class for an atlas construced from surface labels"""
    def __init__(self, atlasdict, roidir=None, subjdir=None, **kwargs):
        
        if roidir is None:
            self.roidir = os.path.join(os.path.abspath(os.curdir),'roi')
        if subjdir is None:
            subjdir = os.getenv('FREESURFER_HOME')
                 
        self.atlasdict = atlasdict
        self.atlasname = atlasdict['atlasname']
        self.manifold = 'surface'
        self.hemi = atlasdict['hemi']
        self.sourcefiles = atlasdict['sourcefiles']
        self.sourcedir = atlasdict['sourcedir']


        self.labels_to_dict(atlasdict['labels'])
        self.regions = self.lut.keys()

        self.basedir = os.path.join(roidir, 'atlases', 'label')
        self.subjdir = subjdir

        self.__dict__.update(**kwargs)

        self._init_subject = False
        self.__init_analysis = False

        if 'debug' not in self.__dict__:
            self.debug = False

    def labels_to_dict(self, labels):
        """Turn a list of labels into a look-up dictionary"""
        # Assuming the list of labels has been trimmed of hemisphere
        # prefix and .label extension

        self.lut = {}
        for i, label in enumerate(labels):
            self.lut[i+1] = label

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        self.subject = subject
        self.atlasdir = os.path.join(self.basedir, subject,
                                     self.atlasname)
        self.lutfile = os.path.join(self.atlasdir, '%s.lut' % self.atlasname)
        self.atlas = os.path.join(self.atlasdir, 
                                  '%s.%s.annot' % (self.hemi, self.atlasname))
        self.origatlas = os.path.join(self.subjdir, subject, 'label',
                                      '%s.%s.annot' % (self.hemi, self.atlasname))
        
        self._init_subject = True

    # Processing methods
    def resample_labels(self):
       """Resample label files from fsaverage surface to native surfaces"""
       results = []
       for label in self.sourcefiles:

            cmd = ['mri_label2label']

            cmd.append('--srcsubject fsaverage')
            cmd.append('--srclabel %s' % os.path.join(self.sourcedir,
                                                      '%s.label' % label))
            cmd.append('--trgsubject %s' % self.subject)
            cmd.append('--trglabel %s' % os.path.join(self.atlasdir,
                                                      '%s.label' % label))
            cmd.append('--hemi %s' % self.hemi)
            cmd.append('--regmethod surface')

            cmdline, res = self.manual_run(cmd)
            if self.debug:
                results.append(cmdline)
            else:
                for output in [cmdline, res.runtime.stdout, res.runtime.stderr]:
                    results.append(output)

       return results

    
    def write_lut(self):
        """Write a look up table to the roi atlas directory"""
        lutfile = open(self.lutfile, 'w')
        for id in self.lut.keys():
            lutfile.write('%d\t%s\t\t\t' % id, self.lut[id])
            for color in np.random.randint(0, 260, 3):
                lutfile.write('%d\t' % color)
            lutfile.write('0\n')

        lutfile.close()

    def make_annotation(self):
        """Create an annotation from a list of labels"""
        cmd = ['mris_label2annot']

        cmd.append('--s %s' % self.subject)
        cmd.append('--hemi %s' % self.hemi)
        cmd.append('--ctab %s' % self.lutfile)
        cmd.append('--a %s' % self.atlasname)
        for label in self.sourcefiles:
            filepath = os.path.join(self.sourcedir, '%s.label' % label)
            cmd.append('--l %s' % filepath)

        cmdline, res = self.manual_run(cmd)

        self.copy_atlas(self.origatlas, self.atlas)

        return cmdline, res

    def group_preproc(self, subjects):
        """Run atlas preprocessing steps for a list of subjects"""
        for subject in subjects:
            self.init_subject(subject)
            results = self.resample_labels()
            for item in results:
                print item
            self.write_lut()
            cmdline, res = self.make_annotation()
            if self.debug:
                print cmdline
            else:
                print '\n%s\n\n%s\n%s' % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

class MaskAtlas(Atlas):

    def __init__(self, atlasdict, roidir):
        pass

class FirstLevelStats(Bunch):
    """Docstring goes here"""
    def __init__(self):
        
        pass

    # Operation methods
    def nipype_run(self, interface):
        """Run a program using its nipype interface"""
        if self.debug:
            return interface.cmdline, None
        else:
            res = interface.run()
            return interface.cmdline, res

    # Processing methods
    def concatenate(self):
        """Concatenate the first level images and write them to roi tree."""
        if not self._init_subject:
            raise InitError('Subject')
        
        concat = fs.Concatenate()

        concat.inputs.invol = self.betaimglist
        concat.inputs.outvol = self.taskbetas

        cmdline, res = self.nipype_run(concat)
        return cmdline, res

    def sample_to_surface(self):

        pass

    def group_concatenate(self, subjects):
        """Concatenate stat images for a group of subjects."""
        for subj in subjects:
            self.init_subject(subj)
            cmdline, res = self.concatenate()
            if self.debug:
                print '\n%s\n\n' % cmdline
            else:
                print '\n%s\n\n%s\n%s' % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

class BetaImage(FirstLevelStats):
    """Docstring goes here"""
    def __init__(self, analysis, **kwargs):

        self.cfg = analysis.cfg
        self.analysis = analysis

        self.betalist = self.cfg.betas(analysis.paradigm, 'images')

        self.roidir = os.path.join(self.cfg.setup('basepath'), 'roi')
        self.statsdir = os.path.join(self.roidir, 'levelone', 'sig')

        self._init_subject = False

        self.__dict__.update(**kwargs)

        if 'debug' not in self.__dict__:
            self.debug = False
    
    # Initialization methods
    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.betapath = cfg.pathspec('beta', self.analysis.paradigm,
                                        self.subject)
        self.betaimglist = []
        for img in self.betalist:
            self.betaimglist.append(os.path.join(self.betapath, img))

        self.roistatdir = os.path.join(self.roidir, 'levelone', 'beta',
                                       self.analysis.paradigm, subject)
        self.taskbetas = os.path.join(self.roistatdir, 'task_betas.mgz') 
        
        self._init_subject = True

class TStatImage(FirstLevelStats):
    """T Statistic class"""
    def __init__(self, analysis, **kwargs):
        
        self.cfg = analysis.cfg
        self.analysis = analysis
        self.timgdict = self.cfg.contrasts(analysis.maskpar, 'T-map', '.img')

        self.roidir = os.path.join(self.cfg.setup('basepath'), 'roi')
        self.statsdir = os.path.join(self.roidir, 'levelone', 'sig')

        self._init_subject = False

        self.__dict__.update(**kwargs)

        if 'debug' not in self.__dict__:
            self.debug = False

    # Operation methods
    def get_dof(self, timg):
        """Get the degrees of freedom from a NiBabel T image"""
        theader = timg.get_header()
        desc = str(theader['descrip'])
        m = re.search('(\[)([\d\.]+)(\])', desc)
        dof = float(m.groups()[1])

        return dof
    
    # Initialization methods
    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.conpath = cfg.pathspec('contrast', self.analysis.maskpar,
                                       subject, self.analysis.maskcon)
        self.timg = os.path.join(self.conpath, 
                                 self.timgdict[self.analysis.maskcon])
        self.sigpath = os.path.join(self.statsdir, self.analysis.maskpar,
                                   subject)
        self.sigimg = os.path.join(self.sigpath, 
                                   self.cfg.contrasts(self.analysis.maskpar,
                                                      'sig')[self.analysis.maskcon])

        self._init_subject = True                                               

    # Processing methods
    def convert_to_sig(self):
        """Read a T stat image in and write it to -log10(P)"""
        if not self._init_subject:
            raise InitError('Subject')
        
        timg = nib.load(self.timg)
        dof = self.get_dof(timg)
        origvol = timg.get_data()
        signvol = np.sign(origvol)
        pvol = stats.t.sf(origvol, dof)
        unsignedsigvol = -np.log10(pvol)
        sigvol = signvol * unsignedsigvol
        
        sigaffine = timg.get_affine()
        sigimg = nib.Nifti1Image(sigvol, sigaffine)

        nib.save(sigimg, self.sigimg)

    def group_convert_to_sig(self, subjects):
        """Convert a t statistic image to a sig image for a group of subjects"""  
        for subj in subjects:
            self.init_subject(subj)
            self.convert_to_sig()
            print 'Converting %s to %s' % (self.timg, self.sigimg)

        
class InitError(Exception):

    def __init__(self, component):
        self.comp = component
    
    def __str__(self):
        return '%s not initialized' % self.comp


def init_atlas(atlasdict, roidir, subjdir= None):
    """Initialize the proper atlas class with an atlas dictionary.
    
    Parameters
    ----------
    atlasdict : atlas dictionary
    roidir : path to roi directory
    subjdir : path to Freesurfer subjects directory

    Returns
    -------
    atlas object

    """
    atlasopts = {'freesurfer': 
                     FreesurferAtlas(atlasdict, roidir, subjdir),
                 'talairach': 
                     TalairachAtlas(atlasdict, roidir),
                 'label': 
                     LabelAtlas(atlasdict, roidir, subjdir),
                 'mask': 
                     MaskAtlas(atlasdict, roidir)}

    return atlasopts[atlasdict['source']] 

def get_analysis_name_list(cfg):
    """Return a list of analysis names in PyROI format.

    Parameters
    ----------
    cfg : config module

    Returns
    -------
    list of analysis names

    """
    analnames = []
    for anal in cfg.analysis():
        analnames.append(get_analysis_name(cfg, anal))
    return analnames

        
def get_analysis_name(cfg, analysis):
    """Get an analysis name in PyROI format.

    Parameters
    ----------
    cfg : config module
    analysis : analysis dictionary
 
    Returns
    -------
    string

    """
    if 'maskpar' in analysis.keys() and analysis['maskpar'] != 'nomask':
        analpar = cfg.paradigms(analysis['par'], 'upper')
        maskpar = cfg.paradigms(analysis['maskpar'], 'lower')
        maskcon = analysis['maskcon']
        maskthresh = str(analysis['maskthresh'])

        return '%s_%s-%s-%s' % (analpar, maskpar, maskcon, maskthresh)

    else:
        analpar = cfg.paradigms(analysis['par'], 'upper')

        return '%s_nomask' % (analpar)

def meanfunc(cfg, par, subj, basedir = ''):
    """Return the path to a mean functional image.

    Note: this function simply globs nifti files from the path and takes the 
    first one.  Standard NiPype behavior is to create a first level directory
    called 'realign' for each paradigm/subject and store mean images there. 
    There may be issues if a NiPype is set up unusually or if it is not used
    for first level analysis

    Parameters
    ----------
    cfg : config module
    par : paradigm
    subj : subject

    Returns
    -------
    string
    
    """
    #XXX This whole function seems a bit misplaced, no? 
    funcpath = cfg.pathspec('meanfunc', par, subj)
    niftis = glob(os.path.join(basedir,funcpath,'*.nii'))
    meanfuncimg = niftis[0]
    return meanfuncimg

def make_analysis_tree(cfg, roidir):
    """Set up the analysis directory tree for a project.

    Parameters
    ----------
    cfg : config module
    roidir : path to roi directory

    """
    if not os.path.isdir(roidir):
        os.mkdir(roidir)

    projdir = os.path.join(roidir, cfg.projectname())
    logdir = os.path.join(projdir, 'logfiles')
    dbdir = os.path.join(projdir, 'databases')

    analdirs = [projdir, logdir, dbdir]

    analnames = get_analysis_names(cfg)
    for name in analnames:
        analdir = os.path.join(projdir, name)
        analdirs.append(analdir)
        
        for atlas in cfg.atlases().keys():
            atlasdir = os.path.join(analdir, atlas)
            analdirs.append(atlasdir)

            for subj in cfg.subjects():
                subjdir = os.path.join(atlasdir, subj)
                analdirs.append(subjdir)

                for dir in ['avgwftxt', 'avgwfvol', 'stats']:
                    resdir = os.path.join(subjdir, dir)
                    analdirs.append(resdir)

    for dir in analdirs:
        if not os.path.isdir(dir):
            os.mkdir(dir)


def make_fs_atlas_tree(roidir, cfg):

    fsdir = os.path.join(roidir, 'freesurfer')

    fsdirs = [fsdir]

    for dir in ['vol', 'surf', 'reg']:
        topdir = os.path.join(fsdir, topdir)
        fsdirs.append(topdir)


#If module is told to run, turn around and run _pyroi.py script
if __name__ == '__main__':
    cmd = ['_pyroi.py']
    if len(sys.argv) > 0:
        for arg in sys.argv[1:]:
            cmd.append(arg)
    P = subprocess.call(cmd)
