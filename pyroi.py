"""Library for fMRI region of interest analysis with NiPyPE interfaces"""
import os
import re
import sys
import shutil
import subprocess
from glob import glob

import pyroilut as lut
import configinterface as cfg

import numpy as np
import scipy.stats as stats
import nibabel as nib
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.base import Bunch

class Analysis(Bunch):
    """Analysis object."""
    def __init__(self, cfg, analysis):
        
        if not 'setup' in cfg.__dict__.keys():
            raise InitError('Config setup function')
        
        make_analysis_tree(cfg)
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
    
    def __init__(self, cfg, atlasdict, **kwargs):

        self.roidir = os.path.join(cfg.setup('basepath'),'roi') 
        self.subjdir = cfg.setup('subjdir')

        if not 'setup' in cfg.__dict__.keys():
            raise InitError('Config setup function')

        self.cfg = cfg
        self.atlasdict = atlasdict
        self.atlasname = atlasdict['atlasname']

        self._init_paradigm = False
        self._init_subject = False
        self._init_analysis = False

        self.__dict__.update(**kwargs)
        if 'debug' not in self.__dict__:
            self.debug = False

    def __call__(self, analysis):

        self.init_analysis(analysis)
    
    # Initialization methods
    def init_paradigm(self, paradigm):
        """Initialize the atlas with a paradigm"""
        self.paradigm = paradigm
        self._init_paradigm = True

    def init_analysis(self, analysis):
        """Initialize the atlas with an analysis."""
        if not self._init_subject:
            raise InitError('Subject')

        self.analysis = analysis
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
        else:
            self.mask = False

        
        sourcedict = \
        {'betas' : os.path.join(analysis.cfg.pathspec('betas', 
                                self.paradigm, self.subject),
                                '%stask_betas.mgz' % self.atlasprefix),
         'contrasts' : os.path.join(analysis.cfg.pathspec('contrasts', 
                                   self.paradigm, self.subject),
                                   '%sall_contrasts.mgz' % self.atlasprefix),
         'timecourse' : os.path.join(analysis.cfg.pathspec('timecourse', 
                                     self.paradigm, self.subject))}#XXX 

        self.analysis.source = sourcedict[analysis.extract]

        self.analysis.dir = os.path.join(self.basedir, 'analyses', 
                                        analysis.cfg.projectname(), 
                                        get_analysis_name(analysis.cfg, 
                                                          analysis.dict))

        self.funcstats = os.path.join(self.analysis.dir, 'stats', 
                                      '%s.stats' % self.subject)
        self.functxt = os.path.join(self.analysis.dir, 'extracttxt',
                                    '%s.txt' % self.subject)
        self.funcvol = os.path.join(self.analysis.dir, 'extractvol',
                                    '%s.nii' % self.subject)
        self._init_analysis = True         

    # Operation methods
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
        if not self._init_subject:
            raise InitError('subject')
        
        segstats = fs.SegStats()

        if self.manifold == 'volume':
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
        if not self._init_subject:
            raise InitError('subject')
        elif not self._init_analysis:
            raise InitError('analysis')

        funcex = fs.SegStats()

        if self.manifold == 'volume':
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


    def group_stats(self, subjects, paradigm=None):
        """Get atlas statistics for a group of subjects"""
        if paradigm is not None:
            self.init_paradigm(paradigm)
        for subj in subjects:
            self.init_subject(subj)
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
            self.init_paradigm(analysis.paradigm)
            self.init_subject(subj)
            self.init_analysis(analysis)
            cmdline, res = self.extract()
            if self.debug:
                print '\n%s\n\n' % cmdline
            else:
                print '\n%s\n\n%s\n%s' % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

class SurfaceAtlas(Bunch):
    """Additional base class that adds surface methods"""
    
    def write_lut(self):
        """Write a look up table to the roi atlas directory"""
        lutfile = open(self.lutfile, 'w')
        for id in self.lut.keys():
            lutfile.write('%d\t%s\t\t\t' % id, self.lut[id])
            for color in np.random.randint(0, 260, 3):
                lutfile.write('%d\t' % color)
            lutfile.write('0\n')

        lutfile.close()

    def labels_to_dict(self, labels):
        """Turn a list of labels into a look-up dictionary"""
        # Assuming the list of labels has been trimmed of hemisphere
        # prefix and .label extension

        self.lut = {}
        for i, label in enumerate(labels):
            self.lut[i+1] = label
    
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


class FreesurferAtlas(Atlas, SurfaceAtlas):
    """Atlas class for a Freesurfer atlas"""
    def __init__(self, cfg, atlasdict, **kwargs):
               
        Atlas.__init__(self, cfg, atlasdict, **kwargs)
        self.fname = atlasdict['fname']
        self.manifold = atlasdict['manifold']
        self.regions = atlasdict['regions']
        if self.manifold == 'surface':
            self.hemi = atlasdict['hemi']

        self.lut = lut.freesurfer(self.fname)

        self.basedir = os.path.join(self.roidir, 'atlases', 'freesurfer')


    # Initialization methods
    def init_subject(self, subject):
       """Initialize the atlas for a subject and analysis paradigm"""
       if not self._init_paradigm:
           raise InitError('Paradigm')
       self.subject = subject
       if self.manifold == 'surface':
           self.pardir = ''
           self.atlasprefix = self.hemi + '.'
           self.origdir = 'label'
           self.atlasext = 'annot'
       else:
           self.pardir = self.paradigm
           self.atlasprefix = ''
           self.origdir = 'mri'
           self.atlasext = 'mgz'
           self.meanfuncimg = self.cfg.meanfunc(self.paradigm, subject)
       self.regmat = os.path.join(self.roidir, 'reg', self.paradigm,
                                  subject, 'func2orig.dat')

       if self.manifold != 'reg':
           self.statsfile = os.path.join(self.basedir, self.manifold, self.pardir,
                                         self.subject, self.atlasname,
                                         '%s.stats' % self.atlasname)
           self.origatlas = os.path.join(self.subjdir, subject, 
                                         self.origdir, self.fname)
           self.atlas = os.path.join(self.basedir, self.manifold, self.pardir,
                                     self.subject, self.atlasname,
                                     '%s%s.%s' % (self.atlasprefix, 
                                                  self.atlasname, 
                                                  self.atlasext))
       
           self._init_subject = True

    # Processing methods
    def resample(self):
        """Resample a freesurfer volume atlas into functional space"""
        if not self._init_paradigm:
            raise InitError('paradigm')
        elif not self._init_subject:
            raise InitError('subject')

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

    def __init__(self, cfg, **kwargs):

        make_reg_tree(cfg)
        self.roidir = os.path.join(cfg.setup('basepath'),'roi')
        subjdir = cfg.setup('subjdir')
        
        self.manifold = 'reg'
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

class LabelAtlas(Atlas, SurfaceAtlas):
    """Atlas class for an atlas construced from surface labels"""
    def __init__(self, cfg, atlasdict, **kwargs):
        
        Atlas.__init__(self, cfg, atlasdict, **kwargs)
        
        self.manifold = 'surface'
        self.hemi = atlasdict['hemi']
        self.sourcefiles = atlasdict['sourcefiles']
        self.sourcedir = atlasdict['sourcedir']

        self.labels_to_dict(atlasdict['sourcefiles'])
        # FIX: self.regions = self.lut.keys()

        self.basedir = os.path.join(self.roidir, 'atlases', 'label')

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
    def concatenate(self):
        """Concatenate the first level images and write them to roi tree."""
        if not self._init_subject:
            raise InitError('Subject')
        
        concat = fs.Concatenate()

        concat.inputs.invol = self.extractlist
        concat.inputs.outvol = self.extractvol

        cmdline, res = self.nipype_run(concat)
        return cmdline, res

    def sample_to_surface(self):
        """Sample an extraction volume to the surface."""
        if not self._init_subject:
            raise InitError('Subject')

        surfs = {'lh': self.extractlhsurf,
                 'rh': self.extractrhsurf}

        cmdlines = []
        results = []

        for hemi in ['lh','rh']:
            cmd = ['mri_vol2surf']    
            cmd.append('--mov %s' % self.extractvol)
            cmd.append('--o %s' % surfs[hemi])
            cmd.append('--reg %s' % self.regmat)
            cmd.append('--hemi %s' % hemi)
            cmd.append('--noreshape')

            cmdline, res = self.manual_run(cmd)
            cmdlines.append(cmdline)
            results.append(res)

        return cmdlines, results

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

    def group_sample_to_surface(self, subjects):
        """Sample stat volumes to the surface for a group."""
        for subj in subjects:
            self.init_subject(subj)
            cmdlines, results = self.sample_to_surface()
            for i in range(1):
                if self.debug:
                    print '\n%s\n\n' % cmdlines[i]
                else:
                    print '\n%s\n\n%s\n%s' % (cmdlines[i], 
                                          results[i].runtime.stdout,
                                          results[i].runtime.stdout)

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
        self.extractlist = []
        for img in self.betalist:
            self.extractlist.append(os.path.join(self.betapath, img))

        self.roistatdir = os.path.join(self.roidir, 'levelone', 'beta',
                                       self.analysis.paradigm, subject)
        self.extractvol = os.path.join(self.roistatdir, 'task_betas.mgz')
        
        self.regmat = os.path.join(self.roidir, 'reg', self.analysis.paradigm,
                                   subject, 'func2orig.dat')
        self.extractlhsurf = os.path.join(self.roistatdir, 'lh.task_betas.mgz')
        self.extractrhsurf = os.path.join(self.roistatdir, 'rh.task_betas.mgz')
        
        self._init_subject = True


class ContrastImage(FirstLevelStats):
    """Contrast Image class."""
    def __init__(self, analysis, **kwargs):

        self.cfg = analysis.cfg
        self.analysis = analysis
        self.condict = self.cfg.contrasts(analysis.maskpar, 'con-img', '.img')

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
        self.extractlist = []
        for name, image in self.condict.items():
            self.conpath = cfg.pathspec('contrast', self.analysis.paradigm,
                                        self.subject, name)
            self.extractlist.append(os.path.join(self.conpath, image))

        self.roistatdir = os.path.join(self.roidir, 'levelone', 'contrasts',
                                       self.analysis.paradigm, subject)
        self.extractvol = os.path.join(self.roistatdir, 'all_contrasts.mgz') 
        
        self.regmat = os.path.join(self.roidir, 'reg', self.analysis.paradigm,
                                   subject, 'func2orig.dat')
        self.extractlhsurf = os.path.join(self.roistatdir, 'lh.all_contrasts.mgz')
        self.extractrhsurf = os.path.join(self.roistatdir, 'rh.all_contrasts.mgz')
        
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
        imagefname = self.cfg.contrasts(self.analysis.maskpar,
                                        'sig', '.nii')[analysis.maskcon]
        self.sigimg = os.path.join(self.sigpath, imagefname)

        self.regmat = os.path.join(self.roidir, 'reg', self.analysis.maskpar,
                                   subject, 'func2orig.dat')
        self.siglhsurf = os.path.join(self.roistatdir, 'lh.%s' % imagefname )
        self.sigrhsurf = os.path.join(self.roistatdir, 'rh.%s' % imagefname)

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


def init_atlas(cfg, atlasdict):
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
    if atlasdict['source'] == 'freesurfer': 
        return FreesurferAtlas(cfg, atlasdict)
    elif atlasdict['source'] == 'talairach': 
        return TalairachAtlas(cfg, atlasdict)
    elif atlasdict['source'] == 'label': 
        return LabelAtlas(cfg, atlasdict) 
    elif atlasdict['source'] == 'mask': 
        return MaskAtlas(cfg, atlasdict)


def init_stat_object(analysis):
    """Initalize the proper first level statistic class with an analysis object.
    
    Parameters
    ----------
    analysis : analysis object
    
    Returns
    -------
    First Level Statistics object
    
    """
    if analysis.extract == 'betas':
        return BetaImage(analysis)
    elif analysis.extract == 'contrasts':
        return ContrastImage(analysis)


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


def make_analysis_tree(cfg):
    """Set up the analysis directory tree for a project.

    Parameters
    ----------
    cfg : module
        Initialized config module

    """
    roidir = os.path.join(cfg.setup('basepath'), 'roi')

    if not os.path.isdir(roidir):
        os.mkdir(roidir)

    projdir = os.path.join(roidir, cfg.projectname())
    logdir = os.path.join(projdir, 'logfiles')
    dbdir = os.path.join(projdir, 'databases')

    analdirs = [projdir, logdir, dbdir]

    analnames = get_analysis_name_list(cfg)
    for name in analnames:
        analdir = os.path.join(projdir, name)
        analdirs.append(analdir)
        
        for atlas in cfg.atlases().keys():
            atlasdir = os.path.join(analdir, atlas)
            analdirs.append(atlasdir)

            for subj in cfg.subjects():
                subjdir = os.path.join(atlasdir, subj)
                analdirs.append(subjdir)

                for dir in ['extracttxt', 'extractvol', 'stats']:
                    resdir = os.path.join(subjdir, dir)
                    analdirs.append(resdir)

    for dir in analdirs:
        if not os.path.isdir(dir):
            os.mkdir(dir)

###XXX Can we do some recursive fancyness?

def make_fs_atlas_tree(cfg):
    """Setup the Freesurfer atlas tree
    
    Parameters
    ----------
    cfg : module
        Initialized config module
        
    """
    roidir = os.path.join(cfg.setup('basepath'), 'roi')
    basedir = os.path.join(roidir, 'freesurfer')

    fsdirs = [roidir, basedir]

    for mani in ['volume', 'surface']:
        manidir = os.path.join(basedir, mani)
        fsdirs.append(manidir)

        for par in cfg.paradigms():
            if mani == 'volume':
                pardir = os.path.join(manidir, par)
                fsdirs.append(pardir)

                for subj in cfg.subjects():
                    subjdir = os.path.join(pardir, subj)
                    fsdirs.append(subjdir)

                    for atlas in cfg.atlases():
                        atlasdir = os.path.join(subjdir, atlas)
                        fsdirs.append(atlasdir)

                        for hemi in ['lh, rh']:
                            hemidir = os.path.join(atlasdir, hemi)
                            fsdirs.append(hemidir)

    for dir in fsdirs:
        if not os.path.isdir(dir):
            os.mkdir(dir)

def make_reg_tree(cfg):

    roidir = os.path.join(cfg.setup('basepath'), 'roi')
    basedir = os.path.join(roidir, 'reg')
    regdirs = [roidir, basedir]


    for par in cfg.paradigms():
        pardir = os.path.join(basedir, par)
        regdirs.append(pardir)

        for subj in cfg.subjects():
            subjdir = os.path.join(pardir, subj)
            regdirs.append(subjdir)

    for dir in regdirs:
        if not os.path.isdir(dir):
            os.mkdir(dir)



#If module is told to run, turn around and run _pyroi.py script
if __name__ == '__main__':
    cmd = ['_pyroi.py']
    if len(sys.argv) > 0:
        for arg in sys.argv[1:]:
            cmd.append(arg)
    P = subprocess.call(cmd)
