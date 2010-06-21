import os
import re
import sys
import shutil
import subprocess
from glob import glob

import configinterface as cfg
import analysis as an
import treeutils as tree
import exceptions as ex
import utils

import numpy as np
import scipy.stats as stats
import nibabel as nib
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.base import Bunch

__all__ = ["Atlas", "FreesurferAtlas", "FSRegister", "LabelAtlas",
           "MaskAtlas", "HarvardOxfordAtlas", "init_atlas"]

__module__ = "atlases"

class Atlas(Bunch):
    """Base atlas class."""
    
    def __init__(self, atlasdict, **kwargs):

        if not cfg.is_setup:
            raise ex.SetupError

        self.roidir = os.path.join(cfg.setup.basepath,"roi")
        self.subjdir = cfg.setup.subjdir

        self.atlasdict = atlasdict
        self.atlasname = atlasdict["atlasname"]

        if "regions" in atlasdict.keys():
            self.regions = atlasdict["regions"]
        else:
            self.regions = range(1, len(atlasdict["sourcefiles"]) + 1)

        self.manifold = atlasdict["manifold"]

        self._init_paradigm = False
        self._init_subject = False
        self._init_analysis = False

        self.__dict__.update(**kwargs)
        if "debug" not in self.__dict__:
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
            raise ex.InitError("Subject")

        self.analysis = analysis
        if analysis.mask:
            self.mask = True
            mask = an.SigImage(analysis)
            mask.init_subject(self.subject)
            if self.manifold == "surface":
                mask.sigimg = mask.sigsurf
            else:
                mask.sigimg = mask.sigvol
            self.analysis.maskimg = mask.sigimg
            self.analysis.maskthresh = analysis.maskthresh
            self.analysis.masksign = analysis.masksign
        else:
            self.mask = False
        source = an.init_stat_object(analysis)
        source.init_subject(self.subject)
        if self.manifold == "surface":
            self.analysis.source = source.extractsurf
        else:
            self.analysis.source = source.extractvol


        analysisdir = os.path.join(self.roidir, "analysis", 
                                   cfg.projectname(), 
                                   utils.get_analysis_name(analysis.dict))
        if self.manifold == "surface":
            self.analysis.dir = os.path.join(analysisdir, self.atlasname, "%s")
        else:
            self.analysis.dir = os.path.join(analysisdir, self.atlasname)

        self.funcstats = os.path.join(self.analysis.dir, "stats", 
                                      "%s.stats" % self.subject)
        self.functxt = os.path.join(self.analysis.dir, "extracttxt",
                                    "%s.txt" % self.subject)
        self.funcvol = os.path.join(self.analysis.dir, "extractvol",
                                    "%s.nii" % self.subject)

        if not self.debug:
            files = [self.atlas, self.analysis.source]
            if self.mask: files.append(self.analysis.maskimg)
            for file in files:
                if self.manifold == "surface":
                    for hemi in self.iterhemi:
                        if not os.path.isfile(file % hemi):
                            raise ex.PreprocessError(file % hemi)
                else:
                    if not os.path.isfile(file):
                        raise ex.PreprocessError(file)

        self._init_analysis = True         

    # Operation methods
    def copy_atlas(self):
        """Copy original atlas file to pyroi atlas tree"""
        if self.manifold == "volume":
            shutil.copy(self.origatlas, self.atlas)  
        else:
            shutil.copy(self.origatlas % self.hemi,
                        self.atlas % self.hemi)

    def sourcenames_to_dict(self):
        """Turn a list of labels into a look-up dictionary"""
        self.lut = {}
        for i, name in enumerate(self.sourcenames):
            self.lut[i+1] = name

    def write_lut(self):
        """Write a look up table to the roi atlas directory"""
        if self.debug:
            lutfile = open("/dev/null", "w")
        else:
            lutfile = open(self.lutfile, "w")
        for id in self.lut:
            lutfile.write("%d\t%s\t\t\t" % (id, self.lut[id]))
            for color in np.random.randint(0, 256, 3):
                lutfile.write("%d\t" % color)
            lutfile.write("0\n")

        lutfile.close()

    def _nipype_run(self, interface):
        """Run a program using its nipype interface"""
        if self.debug:
            return interface.cmdline, None
        else:
            res = interface.run()
            return interface.cmdline, res

    def _manual_run(self, cmd):
        """Run a freesurfer program that lacks a nipype interface"""
        cmdline = cmd[0]
        for i, component in enumerate(cmd):
            if i != 0:
                cmdline = "%s %s" % (cmdline, component)
        if self.debug:
            return cmdline, None
        else:
            res = subprocess.call(cmd)
            return cmdline, res

    def display(self):
        """Display the atlas"""
        if not self._init_subject:
            raise ex.InitError("Subject")

        if self.manifold == "surface":
            self.__surf_display()
        else:
            self.__vol_display()
    
    def __surf_display(self):
        """Display a surface atlas using tksurfer"""
        if "hemi" not in self.__dict__:
            hemi = "lh"
        else:
            hemi = self.hemi

        cmd = ["tksurfer"]

        cmd.append(self.subject)
        cmd.append(hemi)
        cmd.append("inflated")
        cmd.append("-gray")
        cmd.append("-annot %s" % self.atlas % hemi)

        subprocess.call(cmd) 

    def __vol_display(self):
        """Display a volume atlas using Freeview"""
        cmd = ["freeview"]
        cmd.append("-v")
        if self.atlasdict["source"] == "freesurfer":
            anat = os.path.join(self.subjdir, self.subject, "mri", "orig.mgz")
        else:
            anat = os.path.join(os.getenv("FSL_DIR"), "data", "standard",
                                "avg152T1.nii.gz")
        cmd.append("%s:%s" % (anat, "colormap=grayscale"))
        cmd.append("%s:colormap=lut:lut=%s" % (self.atlas, self.lutfile))

        if self.debug:
            print cmd
        else:
            subprocess.call(cmd)

    # Processing methods
    
    def make_annotation(self):
        """Create an annotation from a list of labels"""
        cmd = ["mris_label2annot"]

        cmd.append("--s %s" % self.subject)
        cmd.append("--hemi %s" % self.hemi)
        cmd.append("--ctab %s" % self.lutfile)
        cmd.append("--a %s" % self.atlasname)
        for label in self.sourcefiles:
            filepath = os.path.join(self.sourcedir, "%s.label" % label)
            cmd.append("--l %s" % filepath)

        cmdline, res = self._manual_run(cmd)

        if not self.debug: 
            self.copy_atlas()
        
        return cmdline, res
    
    def stats(self):
        """Generate a summary of voxel/vertex counts for all regions in an atlas."""
        if not self._init_subject:
            raise ex.InitError("Subject")
        
        if self.manifold == "volume":
            cmdline, res = self.__vol_stats()
            return cmdline, res
        else:
            results = map(self.__surf_stats, self.iterhemi)
            return ([res for i, res in enumerate(results) if not i%2],
                    [res for i, res in enumerate(results) if i%2])

    def __surf_stats(self, hemi):
        """Generate stats for a surface atlas"""
        segstats = fs.SegStats()

        segstats.inputs.annot = [self.subject, hemi, self.fname[:-6]]
        segstats.inputs.invol = self.atlas % hemi
        segstats.inputs.segid = self.lut.keys()
        segstats.inputs.sumfile = self.statsfile % hemi

        cmdline, res = self._nipype_run(segstats)
        return cmdline, res
    
    def __vol_stats(self, hemi):
        """Generate stats for a volume atlas"""
        segstats = fs.SegStats()

        segstats.inputs.annot = self.atlas
        segstats.inputs.invol = self.atlas
        segstats.inputs.segid = self.lut.keys()
        segstats.inputs.sumfile = self.statsfile

        cmdline, res = self._nipype_run(segstats)
        return cmdline, res

    def extract(self):
        """Extract average functional data from select regions in an atlas."""
        if not self._init_analysis:
            raise ex.InitError("analysis")

        if self.manifold == "volume":
            cmdline, res = self.__vol_extract()
            return cmdline, res
        else:
            results = map(self.__surf_extract, self.iterhemi)
            return ([res for i, res in enumerate(results) if not i%2],
                    [res for i, res in enumerate(results) if i%2])

    def __surf_extract(self, hemi):
        """Internal function to extract from a surface"""
        funcex = fs.SegStats()
        
        funcex.inputs.annot = [self.subject, hemi, self.fname[3:-6]]
        funcex.inputs.invol = self.analysis.source % hemi
        funcex.inputs.segid = self.regions
        if self.mask:
            funcex.inputs.maskvol = self.analysis.maskimg % hemi
            funcex.inputs.maskthresh = self.analysis.maskthresh
            funcex.inputs.masksign = self.analysis.masksign
        funcex.inputs.sumfile = self.funcstats % hemi
        funcex.inputs.avgwftxt = self.functxt % hemi
        funcex.inputs.avgwfvol = self.funcvol % hemi

        cmdline, res = self._nipype_run(funcex)
        return cmdline, res

    def __vol_extract(self):
        """Internal function to extract from a volume"""
        funcex = fs.SegStats()

        funcex.inputs.segvol = self.atlas
        funcex.inputs.invol = self.analysis.source
        funcex.inputs.segid = self.regions
        if self.mask:
            funcex.inputs.maskvol = self.analysis.maskimg
            funcex.inputs.maskthresh = self.analysis.maskthresh
            funcex.inputs.masksign = self.analysis.masksign
        funcex.inputs.sumfile = self.funcstats
        funcex.inputs.avgwftxt = self.functxt
        funcex.inputs.avgwfvol = self.funcvol

        cmdline, res = self._nipype_run(funcex)
        return cmdline, res

    def group_stats(self, subjects=None, paradigm=None):
        """Get atlas statistics for a group of subjects"""
        if subjects is None:
            subjects = cfg.subjects()
        if paradigm is not None:
            self.init_paradigm(paradigm)
        for subj in subjects:
            self.init_subject(subj)
            cmdline, res = self.stats()
            if self.debug:
                print "\n%s\n\n" % cmdline
            else:
                print "\n%s\n\n%s\n%s" % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

    def group_extract(self, analysis, subjects=None):
        """Extract functional data for a group of subjects."""
        if subjects is None:
            subjects = cfg.subjects()
        for subj in subjects:
            self.init_paradigm(analysis.paradigm)
            self.init_subject(subj)
            self.init_analysis(analysis)
            cmdline, res = self.extract()
            if self.debug:
                print "\n%s\n\n" % cmdline
            else:
                print "\n%s\n\n%s\n%s" % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)


class FreesurferAtlas(Atlas):
    """Atlas class for a Freesurfer atlas"""
    def __init__(self, atlasdict, **kwargs):
               
        Atlas.__init__(self, atlasdict, **kwargs)
        tree.make_fs_atlas_tree()
        
        if self.manifold == "surface":
            self.iterhemi = ["lh","rh"]
        self.fname = atlasdict["fname"]

        #self.lut = lut.freesurfer(self.fname)
        self.lutfile = os.path.join(os.getenv("FREESURFER_HOME"),
                                    "FreeSurferColorLUT.txt")
        self.basedir = os.path.join(self.roidir, "atlases", "freesurfer")

    # Initialization methods
    def init_subject(self, subject):
       """Initialize the atlas for a subject"""
       if self.manifold == "volume" and not self._init_paradigm:
           raise ex.InitError("Paradigm")
       self.subject = subject
       if self.manifold == "surface":
           fname = "%s." + self.fname
           atlasname = "%s." + self.atlasname
           pardir = ""
           origdir = "label"
       else:
           pardir = self.paradigm
           fname = self.fname
           atlasname = self.atlasname
           origdir = "mri"
           self.meanfuncimg = cfg.meanfunc(self.paradigm, subject)
           self.regmat = os.path.join(self.roidir, "reg", self.paradigm,
                                      subject, "func2orig.dat")

       if self.manifold != "reg":
           self.statsfile = os.path.join(self.basedir, self.manifold, pardir,
                                         subject, self.atlasname,
                                         "%s.stats" % self.atlasname)
           self.origatlas = os.path.join(self.subjdir, subject, 
                                         origdir, fname)
           self.atlas = os.path.join(self.basedir, self.manifold, pardir, subject,
                                     self.atlasname, atlasname)
       
           self._init_subject = True

    # Processing methods
    def resample(self):
        """Resample a freesurfer volume atlas into functional space"""
        if not self._init_paradigm:
            raise ex.InitError("paradigm")
        elif not self._init_subject:
            raise ex.InitError("subject")

        transform = fs.ApplyVolTransform()

        transform.inputs.targfile = self.origatlas
        transform.inputs.sourcefile = self.meanfuncimg
        transform.inputs.tkreg = self.regmat
        transform.inputs.inverse = True
        transform.inputs.interp = "nearest"
        transform.inputs.outfile = self.atlas

        cmdline, res = self._nipype_run(transform)
        return cmdline, res


class FSRegister(FreesurferAtlas):
    """Freesurfer atlas for registration"""

    def __init__(self, **kwargs):

        tree.make_reg_tree()
        self.roidir = os.path.join(cfg.setup.basepath,"roi")
        subjdir = cfg.setup.subjdir
        
        self.manifold = "reg"
        self.fname = "orig.mgz"
        self.atlasname = "register"

        self.basedir = os.path.join(roidir, "atlases", "reg")
        self.subjdir = subjdir
        
        self.__dict__.update(**kwargs)
        if "debug" not in self.__dict__:
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

        cmdline, res = self._nipype_run(reg)
        return cmdline, res


class HarvardOxfordAtlas(Atlas):

    def __init__(self, atlasdict, **kwargs):

        Atlas.__init__(self, atlasdict, **kwargs)
     
        self.thresh = atlasdict["probthresh"]
        pckgdir = os.path.split(__file__)[0]
        filename = "HarvardOxford-%d.nii" % self.thresh
        self.lutfile = os.path.join(pckgdir, "data", "HarvardOxford", "HarvardOxford-LUT.txt")
        self.atlas = os.path.join(pckgdir, "data", "HarvardOxford",
                                  filename)


    def init_subject(self, subject):
       """Initialize the atlas for a subject"""
       self.subject = subject
   
       self._init_subject = True

class TalairachAtlas(Atlas):

        pass

class LabelAtlas(Atlas):
    """Atlas class for an atlas construced from surface labels"""
    def __init__(self, atlasdict, **kwargs):
        
        Atlas.__init__(self, atlasdict, **kwargs)
        
        tree.make_label_atlas_tree()
        self.iterhemi =[atlasdict["hemi"]]
        self.hemi = atlasdict["hemi"]
        self.fname = "%s." + "%s.annot" % self.atlasname

        self.sourcefiles = atlasdict["sourcefiles"]
        self.sourcenames = atlasdict["sourcenames"]
        self.sourcenames_to_dict()
        # XXX FIX: self.regions = self.lut.keys()

        self.basedir = os.path.join(self.roidir, "atlases", "label")

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        self.subject = subject
        self.atlasdir = os.path.join(self.basedir, subject,
                                 self.atlasname)
        self.lutfile = os.path.join(atlasdir, "%s.lut" % self.atlasname)
        self.atlas = os.path.join(self.atlasdir, self.fname)
        self.origatlas = os.path.join(self.subjdir, subject, "label", self.fname)
        
        self._init_subject = True

    # Processing methods
    def resample_labels(self):
       """Resample label files from fsaverage surface to native surfaces"""
       results = []
       for label in self.sourcefiles:

            cmd = ["mri_label2label"]

            cmd.append("--srcsubject fsaverage")
            cmd.append("--srclabel %s" % os.path.join(self.sourcedir,
                                                      "%s.label" % label))
            cmd.append("--trgsubject %s" % self.subject)
            cmd.append("--trglabel %s" % os.path.join(self.atlasdir,
                                                      "%s.label" % label))
            cmd.append("--hemi %s" % self.hemi)
            cmd.append("--regmethod surface")

            cmdline, res = self._manual_run(cmd)
            if self.debug:
                results.append(cmdline)
            else:
                for output in [cmdline, res.runtime.stdout, res.runtime.stderr]:
                    results.append(output)

       return results

    def group_preproc(self, subjects=None):
        """Run atlas preprocessing steps for a list of subjects"""
        if subjects is None:
            subjects = cfg.subjects()
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
                print "\n%s\n\n%s\n%s" % (cmdline, 
                                          res.runtime.stdout,
                                          res.runtime.stdout)

class MaskAtlas(Atlas):
    """Mask atlas class"""
    def __init__(self, atlasdict, **kwargs):
        
        Atlas.__init__(self, atlasdict, **kwargs)
        tree.make_mask_atlas_tree()
        
        self.fname = "%s.mgz" % self.atlasname
        self.sourcefiles = atlasdict["sourcefiles"]
        self.sourcedir = atlasdict["sourcedir"]
        self.sourcevolumes = []
        for vol in atlasdict["sourcefiles"]:
            self.sourcevolumes.append(os.path.split(vol)[1])
        self.sourcenames_to_dict()

        self.basedir = os.path.join(self.roidir, "atlases", "mask")
        self.atlas = os.path.join(self.basdir, self.fname)
        self.lutfile = os.path.join(self.basedir, "%s.lut" % self.atlasname)

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        self.subject = subject
        
        self._init_subject = True

    # Processing methods
    def make_atlas(self):
        """Make the single atlas image and look-up-table from a group of masks"""
        self.tempdir = os.path.join(self.basedir, ".temp")
        if not os.path.isdir(self.tempdir): os.mkdir(self.tempdir)
        self.tempvols = []
        for segnum in range(1, len(self.sourcefiles) + 1):
            self.__adj_binary_segvol(segnum)
        
        self.__combine_segvols()

        shutil.rmtree(self.tempdir)

    def __adj_binary_segvol(self, segnum):
        """Adjust the segmentation value of a binary mask image"""
        adjust = fs.Concatenate()

        adjust.inputs.invol = self.sourcefiles[segnum - 1]
        output = os.path.join(self.tempdir, "adj-%s" % self.sourcevolumes[segnum-1])
        self.tempvols.append(output)
        adjust.inputs.outvol = output
        adjust.inputs.mul = segnum

        cmdline, res = self._nipype_run(adjust)
        if self.debug:
            print cmdline

    def __combine_segvols(self):
        """Combine adjusted segvols into one atlas"""
        combine = fs.Concatenate()

        combine.inputs.invol = self.tempvols
        combine.inputs.outvol = self.atlas
        combine.inputs.combine = True

        cmdline, res = self._nipype_run(combine)
        if self.debug:
            print cmdline

def init_atlas(atlasdict, **kwargs):
    """Initialize the proper atlas class with an atlas dictionary.
    
    Parameters
    ----------
    cfg: module
        Initialized config module.
    atlasdict : dict
        Atlas dictionary.

    Returns
    -------
    atlas object

    """
    if atlasdict["source"] == "freesurfer": 
        return FreesurferAtlas(atlasdict, **kwargs)
    elif atlasdict["source"] == "talairach": 
        return TalairachAtlas(atlasdict, **kwargs)
    elif atlasdict["source"] == "label": 
        return LabelAtlas(atlasdict, **kwargs) 
    elif atlasdict["source"] == "mask": 
        return MaskAtlas(atlasdict, **kwargs)

