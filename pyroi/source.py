"""
Classes that define an analysis object and several source image objects.

Generally, a user will not interact directly with the objects in this module,
but rather use them indirectly through the ``prepare_source_images()`` method
on atlas objects.

Classes
-------

Analysis         :  An object that defines analysis parameters

FirstLevelStats  :  Base source image object

BetaImage        :  Provides methods for preparing parameter estimate images

ContrastImage    :  Provides methods for preparing contrast effect size images

TimecourseImage  :  Provides methods for preparing timecourse images

TStatImage       :  Provides methods for preparing T statisic images

SigImage         :  Provides methods for preparing -log10(p) statistical images

Functions
---------

init_stat_object :  Provides a common interface to source image objects.

"""
import os
import re
import sys
import shutil
import subprocess
from glob import glob
from tempfile import mkdtemp

import numpy as np
import scipy.stats as stats
import nibabel as nib
import nipype.interfaces.freesurfer as fs

import configinterface as cfg
import treeutils as tree
from exceptions import *
import core
from core import RoiBase, RoiResult

__all__ = ["Analysis", "FirstLevelStats", 
           "BetaImage", "ContrastImage", "TStatImage", "SigImage", "Timecourse",
           "init_stat_object"]

__module__ = "source"

class Analysis(RoiBase):
    """Analysis object."""
    def __init__(self, analysis):
        """Initialize an analysis object.

        Parameter
        ---------
        analysis : int or dict
            Analysis index or dictionary from config module.
        
        """
        if not cfg.is_setup:
            raise SetupError

        if isinstance(analysis, int):
            analysis = cfg.analysis(analysis)
        
        tree.make_analysis_tree(analysis)
        self.dict = analysis
        self.paradigm = analysis["par"]
        self.extract = analysis["extract"]
        self.name = core.get_analysis_name(analysis)
        if "maskpar" in analysis.keys() and \
           analysis["maskpar"] != "nomask":
            self.mask = True
            self.maskpar = analysis["maskpar"]
            self.maskcon = analysis["maskcon"]
            self.maskthresh = analysis["maskthresh"]
            if "masksign" in analysis.keys():
                self.masksign = analysis["masksign"]
            else:
                self.masksign = "abs"
        else:
            self.mask = False


class FirstLevelStats(RoiBase):
    """Base First Level Stats class"""
    def __init__(self, analysis, **kwargs):
        
        if not cfg.is_setup:
            raise SetupError
        
        if isinstance(analysis, int) or isinstance(analysis, dict):
            analysis = Analysis(analysis)

        tree.make_levelone_tree()
        self.analysis = analysis
        
        self.roidir = os.path.join(cfg.setup.basepath, "roi")
        
        self._init_subject = False

        self.__dict__.update(**kwargs)

        if "debug" not in self.__dict__:
            self.debug = False
    
    # Processing methods
    def concatenate(self):
        """Concatenate the first level statistic images."""
        if not self._init_subject:
            raise InitError("Subject")
        
        result = RoiResult()
        if hasattr(self, "_n_sessions") and self._n_sessions > 1:
            result(self.make_avg_betas())
        
        cmd = ["mri_concat"]
        for f in self.extractlist:
            cmd.append("--i %s"%f)
        cmd.append("--o %s"self.extractvol)

        self._run(cmd)
        if hasattr(self, "_avgtempdir"):
            shutil.rmtree(self._avgtempdir)
        return result

    def make_avg_betas(self):
        """Create the average parameter estimate images."""
        self._avgtempdir = mkdtemp()
        result = RoiResult()
        for i, sourcelist in enumerate(self._avgsource):
            avgimg = os.path.join(self._avgtempdir,"avg-%d.mgz"%i)
            self.extractlist.append(avgimg)

            cmd = ["mri_concat"]
            for f in sourcelist:
                cmd.append("--i %s"%f)
            cmd.append("--mean")
            cmd.append("--o %s"%avgimg)

            result(self._run(cmd))
        return result

    def sample_to_surface(self):
        """Sample an extraction volume to the surface."""
        if not self._init_subject:
            raise InitError("Subject")
        if not os.path.isfile(self.regmat) and not self.debug:
            raise PreprocessError(self.regmat)

        res = RoiResult()

        for hemi in ["lh","rh"]:
            cmd = ["mri_vol2surf"]    
            cmd.append("--mov %s" % self.extractvol)
            cmd.append("--o %s" % self.extractsurf % hemi)
            cmd.append("--reg %s" % self.regmat)
            cmd.append("--hemi %s" % hemi)
            cmd.append("--projfrac 1")
            cmd.append("--noreshape")

            result = self._run(cmd)
            res(result)

        return res

    def group_concatenate(self, subjects=None):
        """Concatenate stat images for a group of subjects."""
        if subjects is None:
            subjects = cfg.subjects()
        elif isinstance(subjects, str):
            subjects = cfg.subjects(subjects)
        result = RoiResult()
        for subj in subjects:
            self.init_subject(subj)
            res = self.concatenate()
            print res
            result(res)
        return result

    def group_sample_to_surface(self, subjects=None):
        """Sample stat volumes to the surface for a group."""
        if subjects is None:
            subjects = cfg.subjects()
        elif isinstance(subjects, str):
            subjects = cfg.subjects(subjects)
        result = RoiResult()
        for subj in subjects:
            self.init_subject(subj)
            res = self.sample_to_surface()
            print res
            result(res)
        return result

class BetaImage(FirstLevelStats):
    """Class for first-level parameter estimate images."""
    def __init__(self, analysis, **kwargs):

        FirstLevelStats.__init__(self, analysis, **kwargs)
        self.statsdir = os.path.join(self.roidir, "levelone", "beta")

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.subjgroup = cfg.subjects(subject=subject)
        self.betalist = cfg.betas(self.analysis.paradigm, "images", subject) 
        self._n_sessions = cfg.betas(self.analysis.paradigm, "sessions", subject)  
        self.betapath = cfg.pathspec("beta", self.analysis.paradigm,
                                        self.subject, self.subjgroup)
        # Build a list of file paths
        self.extractlist = []
        for img in self.betalist:
            self.extractlist.append(os.path.join(self.betapath, img))
        
        # Get a list of lists to average
        if self._n_sessions > 1:
            imgpersess = len(self.betalist)/self._n_sessions
            # Magic?
            chunk = lambda ulist, step:  map(
                lambda i: ulist[i:i+step],  xrange(0, len(ulist), step))
            chunkedimgs = chunk(self.extractlist, imgpersess)
            zippedimgs = zip(*chunkedimgs)
            self._avgsource = [list(tup) for tup in zippedimgs]

        self.roistatdir = os.path.join(self.roidir, "levelone", "beta",
                                       self.analysis.paradigm, subject)
        self.extractvol = os.path.join(self.roistatdir, "task_betas.mgz")
        self.extractsurf = os.path.join(self.roistatdir, "%s.task_betas.mgz")

        self._regtreepath = os.path.join(self.roidir, "reg", self.analysis.paradigm,
                                         subject, "func2orig.dat")
        cfgreg = cfg.pathspec("regmat", self.analysis.paradigm, self.subject,
                              self.subjgroup)
        if cfgreg:
            self.regmat = cfgreg
        else: 
            self.regmat = self._regtreepath

        
        self._init_subject = True


class ContrastImage(FirstLevelStats):
    """Class for first-level contrast effect-size images."""
    def __init__(self, analysis, **kwargs):

        FirstLevelStats.__init__(self, analysis, **kwargs)
        self.imgdict = cfg.contrasts(self.analysis.paradigm, "con-img", ".img")
        self.statsdir = os.path.join(self.roidir, "levelone", "contrast")

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.subjgroup = cfg.subjects(subject=subject)
        self.extractlist = []
        for name, image in self.imgdict.items():
            self.conpath = cfg.pathspec("contrast", self.analysis.paradigm,
                                        self.subject, self.subjgroup, name)
            self.extractlist.append(os.path.join(self.conpath, image))
            self.extractlist.sort()

        self.roistatdir = os.path.join(self.roidir, "levelone", "contrast",
                                       self.analysis.paradigm, subject)
        self.extractvol = os.path.join(self.roistatdir, "all_contrasts.mgz") 
        self.extractsurf = os.path.join(self.roistatdir, "%s.all_contrasts.mgz")
        self._regtreepath = os.path.join(self.roidir, "reg", self.analysis.paradigm,
                                         subject, "func2orig.dat")
        cfgreg = cfg.pathspec("regmat", self.analysis.paradigm, self.subject,
                              self.subjgroup)
        if cfgreg:
            self.regmat = cfgreg
        else: 
            self.regmat = self._regtreepath

        self._init_subject = True


class TStatImage(FirstLevelStats):
    """Class for first-level T-statistics."""
    def __init__(self, analysis, **kwargs):
        
        FirstLevelStats.__init__(self, analysis, **kwargs)
        self.imgdict = cfg.contrasts(self.analysis.maskpar, "T-map", ".img")
        self.statsdir = os.path.join(self.roidir, "levelone", "contrast")

    # Operation methods
    def get_dof(self, timg):
        """Get the degrees of freedom from a NiBabel T image"""
        theader = timg.get_header()
        desc = str(theader["descrip"])
        m = re.search("(\[)([\d\.]+)(\])", desc)
        dof = float(m.groups()[1])

        return dof
    
    # Initialization methods
    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.subjgroup = cfg.subjects(subject=subject)
        conpath = cfg.pathspec("contrast", self.analysis.maskpar,
                                       subject, self.subjgroup, self.analysis.maskcon)
        self.timg = os.path.join(conpath, 
                                 self.imgdict[self.analysis.maskcon])
        self.extractvol = self.timg                                 
        self.sigpath = os.path.join(self.statsdir, self.analysis.maskpar,
                                   subject)
        imagefname = cfg.contrasts(self.analysis.maskpar,
                                        "sig", ".nii")[self.analysis.maskcon]
        self.sigimg = os.path.join(self.sigpath, imagefname)

        self._regtreepath = os.path.join(self.roidir, "reg", self.analysis.maskpar,
                                         subject, "func2orig.dat")
        cfgreg = cfg.pathspec("regmat", self.analysis.maskpar, self.subject,
                              self.subjgroup)
        if cfgreg:
            self.regmat = cfgreg
        else: 
            self.regmat = self._regtreepath
        self.roistatdir = os.path.join(self.roidir, "levelone", "contrast",
                                       self.analysis.paradigm, subject)
        self.sigsurf = os.path.join(self.roistatdir, "%s." + imagefname)
        self.extractsurf = self.sigsurf

        self._init_subject = True                                               

    # Processing methods
    def convert_to_sig(self):
        """Read a T stat image in and write it to -log10(P)"""
        if not self._init_subject:
            raise InitError("Subject")
        
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
        res = RoiResult()
        res("Writing to %s" % self.sigimg)
        return res

    def group_convert_to_sig(self, subjects=None):
        """Convert a t statistic image to a sig image for a group of subjects"""  
        if subjects is None:
            subjects = cfg.subjects()
        elif isinstance(subjects, str):
            subjects = cfg.subjects(subjects)
        result = RoiResult()
        for subj in subjects:
            self.init_subject(subj)
            res = self.convert_to_sig()
            result(res)
        return result

class SigImage(FirstLevelStats):
    """Sig image class"""
    def __init__(self, analysis, **kwargs):
        
        FirstLevelStats.__init__(self, analysis, **kwargs)
        self.imgdict = cfg.contrasts(self.analysis.maskpar, "sig", ".nii")
        self.statsdir = os.path.join(self.roidir, "levelone", "contrast")

    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.subjgroup = cfg.subjects(subject=subject)
        self.sigpath = os.path.join(self.statsdir, self.analysis.maskpar,
                                   subject)
        imagefname = cfg.contrasts(self.analysis.maskpar,
                                        "sig", ".nii")[self.analysis.maskcon]
        self.sigvol = os.path.join(self.sigpath, imagefname)    
        self.extractvol = self.sigvol
        self.sigsurf = os.path.join(self.sigpath, "%s." + imagefname)
        self.extractsurf = self.sigsurf
        self._regtreepath = os.path.join(self.roidir, "reg", self.analysis.maskpar,
                                         subject, "func2orig.dat")
        cfgreg = cfg.pathspec("regmat", self.analysis.maskpar, self.subject,
                              self.subjgroup)
        if cfgreg:
            self.regmat = cfgreg
        else: 
            self.regmat = self._regtreepath
        self.roistatdir = os.path.join(self.roidir, "levelone", "contrast",
                                       self.analysis.paradigm, subject)

        self._init_subject = True                                               

class Timecourse(FirstLevelStats):
    """Timecourse class"""
    def __init__(self, analysis, **kwargs):
        
        FirstLevelStats.__init__(self, analysis, **kwargs)
        self.statsdir = os.path.join(self.roidir, "levelone", "timecourse")
    
    def init_subject(self, subject):
        """Initialize the object for a subject"""
        self.subject = subject
        self.subjgroup = cfg.subjects(subject=subject)
        self.roistatdir = os.path.join(self.roidir, "levelone", "timecourse",
                                       self.analysis.paradigm, subject)
        self.extractvol = cfg.pathspec("timecourse", self.analysis.paradigm, 
                                       self.subject, self.subjgroup)
        self.extractsurf = os.path.join(self.roistatdir, "%s.timecourse.mgz")
        self._regtreepath = os.path.join(self.roidir, "reg", self.analysis.paradigm,
                                         subject, "func2orig.dat")
        cfgreg = cfg.pathspec("regmat", self.analysis.paradigm, self.subject,
                              self.subjgroup)
        if cfgreg:
            self.regmat = cfgreg
        else: 
            self.regmat = self._regtreepath
        self.roistatdir = os.path.join(self.roidir, "levelone", "contrast",
                                       self.analysis.paradigm, subject)

        self._init_subject = True                                               

def init_stat_object(analysis, **kwargs):
    """Initalize the proper first level statistic class with an analysis object.
    
    This initializes the proper object for extraction (corresponding to the main
    analysis paradigm and the image type specified by the 'extract' entry in the
    analysis dictionary).

    Parameters
    ----------
    analysis : int, dict, or Analysis object
        Either the analysis list index, an analysis dictionary, or an instance
        of the Analysis() class.
    
    Returns
    -------
    FirstLevelStats subclass object
    
    """
    if isinstance(analysis, int) or isinstance(analysis, dict):
        analysis = Analysis(analysis)
    if analysis.extract == "beta":
        return BetaImage(analysis, **kwargs)
    elif analysis.extract == "contrast":
        return ContrastImage(analysis, **kwargs)
    elif analysis.extract == "timecourse":
        return Timecourse(analysis, **kwargs)
    elif analysis.extract in ["tstat", "sig"]:
        raise NotImplementedError("%s cannot yet be extracted." % analysis.extract)
