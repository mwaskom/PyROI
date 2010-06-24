import os
import re
import sys
import shutil
import subprocess
from glob import glob

import numpy as np
import scipy.stats as stats
import nibabel as nib
import nipype.interfaces.freesurfer as fs

import configinterface as cfg
import analysis as anal
import treeutils as tree
import exceptions as ex
import core
from core import RoiBase, RoiResult

__all__ = ["Atlas", "FreesurferAtlas", "FSRegister", "LabelAtlas",
           "MaskAtlas", "HarvardOxfordAtlas", "init_atlas"]

__module__ = "atlases"

class Atlas(RoiBase):
    """Base atlas class.
    
    See the docstrings of atlas subclasses for usage and examples.
    Subclasses currently offered:
    - FreesurferAtlas
    - HarvardOxfordAtlas
    - LabelAtlas
    - MaskAtlas

    """    
    def __init__(self, atlasdict, **kwargs):

        if not cfg.is_setup:
            raise ex.SetupError

        if isinstance(atlasdict, str):
            atlasdict = cfg.atlases(atlasdict)

        self.roidir = os.path.join(cfg.setup.basepath,"roi")
        self.subjdir = cfg.setup.subjdir

        self.atlasdict = atlasdict
        self.atlasname = atlasdict["atlasname"]
        self.source = atlasdict["source"]
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

        if isinstance(analysis, dict):
            analysis = anal.Analysis(analysis)

        self.analysis = analysis
        if analysis.mask:
            self.mask = True
            mask = anal.SigImage(analysis)
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
        source = anal.init_stat_object(analysis)
        source.init_subject(self.subject)
        if self.manifold == "surface":
            self.analysis.source = source.extractsurf
        else:
            self.analysis.source = source.extractvol


        analysisdir = os.path.join(self.roidir, "analysis", 
                                   cfg.projectname(), 
                                   core.get_analysis_name(analysis.dict))
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
        """Copy original atlas file to pyroi atlas tree."""
        if self.manifold == "volume":
            shutil.copy(self.origatlas, self.atlas)  
        else:
            shutil.copy(self.origatlas % self.hemi,
                        self.atlas % self.hemi)

    def sourcenames_to_lutdict(self):                        
        """Turn the list of sourcenames into a lookup dict."""
        self.lutdict = {}
        for i, name in enumerate(self.sourcenames):
            self.lutdict[i+1] = name

    def write_lut(self):
        """Write a look up table to the roi atlas directory"""
        lutfile = open(self.lutfile, "w")
        for id, name in self.lutdict.items():
            lutfile.write("%d\t%s\t\t\t" % (id, name))
            for color in np.random.randint(0, 256, 3):
                lutfile.write("%d\t" % color)
            lutfile.write("0\n")

        lutfile.close()
        if self.debug: os.remove(self.lutfile)

    def display(self):
        """Display the atlas."""
        if not self._init_subject and self.source in ["freesurfer", "label"]:
            raise ex.InitError("Subject")

        if self.manifold == "surface":
            self.__surf_display()
        else:
            self.__vol_display()
    
    def __surf_display(self):
        """Display a surface atlas using tksurfer."""
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

        if self.deubg:
            print cmd
        else:
            subprocess.call(cmd) 

    def __vol_display(self):
        """Display a volume atlas using Freeview."""
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
        """Create an annotation from a list of labels."""
        if not self._init_subject:
            raise ex.InitError("Subject")
        cmd = ["mris_label2annot"]

        cmd.append("--s %s" % self.subject)
        cmd.append("--hemi %s" % self.hemi)
        cmd.append("--ctab %s" % self.lutfile)
        cmd.append("--a %s" % self.atlasname)
        for label in self.sourcenames:
            cmd.append("--l %s" % os.path.join(self.atlasdir, "%s.label" % label))

        res = self._manual_run(cmd)

        if not self.debug: 
            try:
                self.copy_atlas()
                res("Copying %s to atlas directory" % self.atlasname)
            except IOError:
                res("IOError: Atlas copy failed")

        return res
    
    def stats(self):
        """Generate a summary of voxel/vertex counts for all regions in an atlas."""
        if not self._init_subject:
            raise ex.InitError("Subject")
        
        if self.manifold == "volume":
            return self.__vol_stats()
        else:
            results = RoiResult()
            for hemi in self.iterhemi:
                res = self.__surf_stats(hemi)
                results(res) 
            return results

    def __surf_stats(self, hemi):
        """Generate stats for a surface atlas."""
        segstats = fs.SegStats()

        segstats.inputs.annot = [self.subject, hemi, self.fname[:-6]]
        segstats.inputs.invol = self.atlas % hemi
        segstats.inputs.segid = self.all_regions
        segstats.inputs.sumfile = self.statsfile % hemi

        return self._nipype_run(segstats)
    
    def __vol_stats(self):
        """Generate stats for a volume atlas."""
        segstats = fs.SegStats()

        segstats.inputs.annot = self.atlas
        segstats.inputs.invol = self.atlas
        segstats.inputs.segid = self.all_regions
        segstats.inputs.sumfile = self.statsfile

        return self._nipype_run(segstats)

    def extract(self):
        """Extract average functional data from select regions in an atlas."""
        if not self._init_analysis:
            raise ex.InitError("analysis")

        if self.manifold == "volume":
            return self.__vol_extract()
        else:
            results = RoiResult()
            for hemi in self.iterhemi:
                res = self.__surf_extract(hemi)
                results(res)
            return results

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

        return self._nipype_run(funcex)
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

        return self._nipype_run(funcex)

    def group_stats(self, subjects=None, paradigm=None):
        """Get atlas statistics for a group of subjects"""
        if subjects is None:
            subjects = cfg.subjects()
        if paradigm is not None:
            self.init_paradigm(paradigm)
        for subj in subjects:
            self.init_subject(subj)
            print self.stats()

    def group_extract(self, analysis, subjects=None):
        """Extract functional data for a group of subjects."""
        if subjects is None:
            subjects = cfg.subjects()
        for subj in subjects:
            self.init_paradigm(analysis.paradigm)
            self.init_subject(subj)
            self.init_analysis(analysis)
            print self.extract()

class FreesurferAtlas(Atlas):
    """Atlas class for a Freesurfer atlas"""
    def __init__(self, atlasdict, **kwargs):
               
        Atlas.__init__(self, atlasdict, **kwargs)
        tree.make_fs_atlas_tree()
        
        if self.manifold == "surface":
            self.iterhemi = ["lh","rh"]
        self.fname = atlasdict["fname"]

        self.lutfile = os.path.join(os.getenv("FREESURFER_HOME"), 
                                    "FreeSurferColorLUT.txt")

        
        convtable = {1:(10,49), 2:(11,50), 2:(12,51), 3:(13,52), 
                     4:(17,53), 5:(18,54), 6:(26,58), 7:(28,60)}
        if self.fname == "aseg.mgz":
            self.regions = ([convtable[id][0] for id in self.atlasdict["regions"]] + 
                            [convtable[id][1] for id in self.atlasdict["regions"]])
        else:
            self.regions = self.atlasdict["regions"]

        dictdict = {"aseg.mgz": "aseg-lut.txt",
                    "aparc.annot": "aparc-lut.txt",
                    "aparc.a2009s": "aparc-aparc.a2009s-lut.txt"}
        datadir = os.path.join(os.path.split(__file__)[0], "data", "Freesurfer")
        dictfile = os.path.join(datadir, dictdict[self.fname])
        lutarray = np.genfromtxt(dictfile, str)
        self.lutdict = {}
        for row in lutarray:
            self.lutdict[int(row[0])] = row[1]

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
            if not os.path.isfile(self.regmat):
                raise ex.PreprocessError("%s does not exist." % self.regmat)

            self.statsfile = os.path.join(self.basedir, self.manifold, pardir,
                                          subject, self.atlasname,
                                          "%s.stats" % self.atlasname)
            self.origatlas = os.path.join(self.subjdir, subject, 
                                          origdir, fname)
            self.atlas = os.path.join(self.basedir, self.manifold, pardir, subject,
                                      self.atlasname, self.fname)
        
            self._init_subject = True

    # Processing methods
    def resample(self):
        """Resample a freesurfer volume atlas into functional space."""
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

        return self._nipype_run(transform)


class FSRegister(FreesurferAtlas):
    """Freesurfer atlas for registration"""

    def __init__(self, **kwargs):

        tree.make_reg_tree()
        self.roidir = os.path.join(cfg.setup.basepath, "roi")
        subjdir = cfg.setup.subjdir
        
        self.manifold = "reg"
        self.fname = "orig.mgz"
        self.atlasname = "register"

        self.basedir = os.path.join(self.roidir, "atlases", "reg")
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

        return self._nipype_run(reg)


class HarvardOxfordAtlas(Atlas):

    def __init__(self, atlasdict, **kwargs):

        Atlas.__init__(self, atlasdict, **kwargs)
     
        self.thresh = atlasdict["probthresh"]
        pckgdir = os.path.split(__file__)[0]
        filename = "HarvardOxford-%d.nii" % self.thresh
        self.atlas = os.path.join(pckgdir, "data", "HarvardOxford", filename)
        self.lutfile = os.path.join(os.path.split(__file__)[0], "data", 
                                 "HarvardOxford", "HarvardOxford-LUT.txt")


    def init_subject(self, subject):
       """Initialize the atlas for a subject"""
       self.subject = subject
   
       self._init_subject = True


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
        self.sourcenames_to_lutdict()

        self.basedir = os.path.join(self.roidir, "atlases", "label")
        
        self.lutfile = os.path.join(self.basedir, "%s.lut" % self.atlasname)
        self.regions = self.lutdict.keys()
        self.all_regions = self.regions

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        self.subject = subject
        self.atlasdir = os.path.join(self.basedir, cfg.projectname(), subject,
                                 self.atlasname)
        self.atlas = os.path.join(self.atlasdir, self.fname)
        self.origatlas = os.path.join(self.subjdir, subject, 
                                      "label", self.fname)
        
        self._init_subject = True

    # Processing methods
    def resample_labels(self):
        """Resample label files from fsaverage surface to native surfaces"""
        if not self._init_subject:
            raise ex.InitError("subject")
        res = RoiResult()
        for i, label in enumerate(self.sourcefiles):
         
            cmd = ["mri_label2label"]

            cmd.append("--srcsubject fsaverage")
            cmd.append("--srclabel %s"  % label)
            cmd.append("--trgsubject %s" % self.subject)
            cmd.append("--hemi %s" % self.hemi)
            cmd.append("--regmethod surface")
            cmd.append("--trglabel %s" 
                       % os.path.join(self.atlasdir,
                       "%s.label" % self.sourcenames[i]))

            result = self._manual_run(cmd)
            res(result)      

        return res

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
            print self.make_annotation()

class MaskAtlas(Atlas):
    """Mask atlas class"""
    def __init__(self, atlasdict, **kwargs):
        
        Atlas.__init__(self, atlasdict, **kwargs)
        tree.make_mask_atlas_tree()
        
        self.fname = "%s.mgz" % self.atlasname
        self.sourcefiles = atlasdict["sourcefiles"]
        self.sourcenames = atlasdict["sourcenames"]
        self.sourcenames_to_lutdict()

        self.basedir = os.path.join(self.roidir, "atlases", "mask")
        
        self.lutfile = os.path.join(self.basedir, "%s.lut" % self.atlasname)
        self.regions = self.lutdict.keys()
        self.all_regions = self.regions
        
        self.atlas = os.path.join(self.basedir, self.fname)

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
        result = RoiResult()
        for segnum in range(1, len(self.sourcefiles) + 1):
            res = self.__adj_binary_segvol(segnum)
            result(res)

        res = self.__combine_segvols()
        result(res)
        shutil.rmtree(self.tempdir)
        return result

    def __adj_binary_segvol(self, segnum):
        """Adjust the segmentation value of a binary mask image"""
        adjust = fs.Concatenate()

        adjust.inputs.invol = self.sourcefiles[segnum - 1]
        output = os.path.join(self.tempdir, "adj-%s" % self.sourcevolumes[segnum-1])
        self.tempvols.append(output)
        adjust.inputs.outvol = output
        adjust.inputs.mul = segnum

        return self._nipype_run(adjust)

    def __combine_segvols(self):
        """Combine adjusted segvols into one atlas"""
        combine = fs.Concatenate()

        combine.inputs.invol = self.tempvols
        combine.inputs.outvol = self.atlas
        combine.inputs.combine = True

        return self._nipype_run(combine)
        

def init_atlas(atlasdict, **kwargs):
    """Initialize the proper atlas class with an atlas dictionary.
    
    Parameters
    ----------
    atlasdict : dict or str
        Atlas dictionary or atlas name, if internal config module is setup.

    Returns
    -------
    atlas object

    """
    if isinstance(atlasdict, str):
        atlasdict = cfg.atlases(atlasdict)
    if atlasdict["source"] == "freesurfer": 
        return FreesurferAtlas(atlasdict, **kwargs)
    elif atlasdict["source"] == "talairach": 
        return TalairachAtlas(atlasdict, **kwargs)
    elif atlasdict["source"] == "label": 
        return LabelAtlas(atlasdict, **kwargs) 
    elif atlasdict["source"] == "mask": 
        return MaskAtlas(atlasdict, **kwargs)

