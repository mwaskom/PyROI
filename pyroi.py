"""Library for fMRI region of interest analysis with NiPyPE interfaces"""
import os
import sys
import shutil
import subprocess
import pyroilut as lut
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.base import Bunch
from glob import glob

class Analysis(Bunch):
    """Analysis object"""
    def __init__(self, cfg, analysis):
        
        self.dict = analysis
        self.cfg = cfg
        self.par = analysis['par']
        self.source = analysis['extract']
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
    """Base atlas class"""
    def __init__(self):

        pass
    
    def init_analysis(self, analysis):

        self.analysis = analysis
    
        if analysis.mask:
            self.mask = True
            maskpath = analysis.cfg.pathspec('contrast', analysis.maskpar,
                                             self.subj, analysis.maskcon)
            maskfile = '%s%s' % (self.atlasprefix, 
                        analysis.cfg.contrasts(analysis.maskpar, 
                                               'sig',)[analysis.maskcon])
            self.analysis.maskimg = os.path.join(maskpath, maskfile)
            self.analysis.maskthresh = analysis.maskthresh
            self.analysis.masksign = analysis.masksign

        
        sourcedict = \
        {'betas' : os.path.join(analysis.cfg.pathspec('beta', self.par, 
                                                      self.subj),
                                '%stask_betas.mgz' % self.atlasprefix),
         'contrast' : os.path.join(analysis.cfg.pathspec('contrast', self.par,
                                   self.subj),
                                   '%sall_contrasts.mgz' % self.atlasprefix),
         'timecourse' : os.path.join(cfg.pathspec('timecourse', self.par, 
                                     self.subj))} #XXX figure this out

        self.analysis.source = sourcedict[analysis.source]

        self.analysis.dir = os.path.join(self.basedir, 'analyses', 
                                        analysis.cfg.projectname(), 
                                        get_analysis_name(analysis.cfg, 
                                                          analysis.dict))

        self.funcstats = os.path.join(self.analysis.dir, 'stats', 
                                      '%s.stats' % self.subj)
        self.functxt = os.path.join(self.analysis.dir, 'avgwftxt',
                                    '%s.avgwf' % self.subj)
        self.funcvol = os.path.join(self.analysis.dir, 'avgwfvol',
                                    '%s.nii' % self.subj)
         

    def copy_atlas(self):

        shutil.copy(self.origatlas, self.atlas)  

    def nipype_run(self, interface):
     
        if self.debug:
            return interface.cmdline, None
        else:
            res = interface.run()
            return interface.cmdline, res

    def stats(self):

        segstats = fs.SegStats()

        if self.space == 'volume':
            segstats.inputs.segvol = self.atlas
            segstats.inputs.invol = self.atlas
        else:
            segstats.inputs.annot = [self.subj, self.hemi, self.atlasname]
        segstats.inputs.segid = self.lut.keys()
        segstats.inputs.sumfile = self.statsfile

        cmdline, res = self.nipype_run(segstats)
        return cmdline, res
     
    def extract(self):

        funcex = fs.SegStats()

        if self.space == 'volume':
            funcex.inputs.segvol = self.atlas
        else:
            funcex.inputs.annot = [self.subj, self.hemi, self.atlasname]
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

class FreesurferAtlas(Atlas):
    """Freesurfer atlas object"""
    def __init__(self, atlasdict, fsroidir, fssubjdir, **kwargs):
        
        self.atlasname = atlasdict['atlasname']
        self.fname = atlasdict['fname']
        self.space = atlasdict['space']
        self.regions = atlasdict['regions']
        if self.space == 'surface':
            self.hemi = atlasdict['hemi']

        self.lut = lut.freesurfer(self.fname)

        self.basedir = fsroidir
        self.subjdir = fssubjdir

        self.__dict__.update(**kwargs)
        if 'debug' not in self.__dict__:
            self.debug = False

    def init_subject(self, par, subj, meanfuncimg=None):
        
       self.subj = subj
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
       self.regmat = os.path.join(self.basedir, 'reg', par,
                                  subj, 'func2orig.dat')

       if self.space != 'reg':
           self.statsfile = os.path.join(self.basedir, self.space, self.pardir,
                                         self.subj, self.atlasname,
                                         '%s.stats' % self.atlasname)
           self.origatlas = os.path.join(self.subjdir, subj, 
                                         self.origdir, self.fname)
           self.atlas = os.path.join(self.basedir, self.space, self.pardir,
                                     self.subj, self.atlasname,
                                     '%s%s.%s' % (self.atlasprefix, 
                                                  self.atlasname, 
                                                  self.atlasext))
        
    def resample(self):

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
    """Freesurfer atlas object for registration"""

    def __init__(self, fsroidir, fssubjdir, **kwargs):
        self.basedir = fsroidir
        self.subjdir = fssubjdir
        self.space = 'reg'
        self.fname = 'orig.mgz'
        self.atlasname = 'register'

        self.__dict__.update(**kwargs)
        if 'debug' not in self.__dict__:
            self.debug = False

    def register(self):

        self.regmat = os.path.join(self.basedir, 'reg', self.par,
                                   self.subj, 'func2orig.dat')
        reg = fs.BBRegister()

        reg.inputs.subject_id = self.subj
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

    def __init__(self, atlasdict, roidir, subjdir):
        pass

class MaskAtlas(Atlas):

    def __init__(self, atlasdict, roidir):
        pass

class FirstLevelStats(Bunch):
    """Docstring goes here"""
    def __init__(self):
        
        pass

    def concatenate(self):

        pass

    def sample_to_surface(self):

        pass

def init_atlas(atlasdict, roidir, subjdir):
    """Docstring goes here"""
    atlasopts = {'freesurfer': FreesurferAtlas(atlasdict, roidir, subjdir),
                 'talairach': TalairachAtlas(atlasdict, roidir),
                 'label': LabelAtlas(atlasdict, roidir, subjdir),
                 'mask': MaskAtlas(atlasdict, roidir)}

    return atlasopts[atlasdict['source']] 

def get_analysis_name_list(cfg):
    """Return a list of analysis names in PyROI format

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
    """Get an analysis name in PyROI format

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
    """Return the path to a mean functional image

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

    funcpath = cfg.pathspec('meanfunc', par, subj)
    niftis = glob(os.path.join(basedir,funcpath,'*.nii'))
    meanfuncimg = niftis[0]
    return meanfuncimg

def make_analysis_tree(cfg, roidir):
    """Set up the analysis directory tree for a project

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


if __name__ == '__main__':
    """If module is told to run, turn around and run _pyroi.py script"""
    cmd = ['_pyroi.py']
    if len(sys.argv) > 0:
        for arg in range(1,len(sys.argv)):
            cmd.append(sys.argv[arg])
    P = subprocess.call(cmd)
