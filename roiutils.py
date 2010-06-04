import os
#import pyroilut as lut
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.base import Bunch

class FreesurferAtlas(Bunch):
    """
    """
    def __init__(self, atlasdict, fsroidir, fssubjdir, **kwargs):
        
        self.atlasname = atlasdict['atlasname']
        self.fname = atlasdict['fname']
        self.space = atlasdict['space']
        self.regions = atlasdict['regions']
        if self.space == 'surface':
            self.hemi = atlasdict['hemi']

 #       self.lut = lut.freesurfer(self.fname)

        self.basedir = fsroidir
        self.subjdir = fssubjdir

        self.__dict__.update(**kwargs)


    def init_subj(self, par, subj, meanfuncimg=None):
        
       self.par = par
       self.subj = subj
       self.regmat = os.path.join(self.basedir, 'reg', par,
                                  subj, 'func2orig.dat')

       if self.space == 'volume':
           self.meanfuncimg = meanfuncimg
           self.origatlas = os.path.join(self.subjdir, subj, 'mri', self.fname)


        
    def resample(self):

        transform = fs.ApplyVolTransform()

        transform.inputs.targfile = self.origatlas
        transform.inputs.sourcefile = self.meanfuncimg
        transform.inputs.tkreg = self.regmat
        transform.inputs.inverse = True
        transform.inputs.interp = 'nearest'
        transform.inputs.outfile = os.path.join(self.basedir, 'vol', self.par,
                                                self.subj, self.atlasname,
                                                '%s.mgz' % self.atlasname)

        print transform.cmdline


class FSRegister(FreesurferAtlas):
    """
    """

    def __init__(self, fsroidir, fssubjdir, **kwargs):

        self.basedir = fsroidir
        self.subjdir = fssubjdir

        self.__dict__.update(**kwargs)

    def init_subj(self, par, subj, meanfuncimg):

       self.par = par
       self.subj = subj
       self.regmat = os.path.join(self.basedir, 'reg', par,
                                  subj, 'func2orig.dat')
       self.meanfuncimg = meanfuncimg
    
    def register(self):

        self.regmat = os.path.join(self.basedir, 'reg', self.par,
                                   self.subj, 'func2orig.dat')
        reg = fs.BBRegister()

        reg.inputs.subject_id = self.subj
        reg.inputs.sourcefile = self.meanfuncimg
        reg.inputs.init_fsl = True
        reg.inputs.t2_contrast = True
        reg.inputs.outregfile = self.regmat       

        print reg.cmdline


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


def make_analysis_dirs(roidir, cfg): # projname, analysis, atlases, subjects):
    """Set up the analysis directory hierarchy for a project

    Parameters
    ----------
    roidir : path to roi directory
    projname : project name
    analysis : analysis dictionary
    atlases : list of atlas names
    subjects : list of subjects

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


def make_fs_atlas_dirs(roidir, cfg):

    fsdir = os.path.join(roidir, 'freesurfer')

    fsdirs = [fsdir]

    for dir in ['vol', 'surf', 'reg']:
        topdir = os.path.join(fsdir, topdir)
        fsdirs.append(topdir)


       

