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
from exceptions import *
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

    - SphereAtlas [Not quite ready yet]

    """    
    def __init__(self, atlasdict, **kwargs):

        if not cfg.is_setup:
            raise SetupError

        self.roidir = os.path.join(cfg.setup.basepath,"roi")
        self.subjdir = cfg.setup.subjdir

        self.atlasdict = atlasdict
        self.atlasname = atlasdict["atlasname"]
        self.source = atlasdict["source"]
        self.manifold = atlasdict["manifold"]

        if "sourcefiles" in atlasdict:
            self.sourcefiles = atlasdict["sourcefiles"]
            self.sourcenames = atlasdict["sourcenames"]
            self.__sourcenames_to_lutdict()

        self._init_paradigm = False
        self._init_subject = False
        self._init_analysis = False

        self.__dict__.update(**kwargs)
        if "debug" not in self.__dict__:
            self.debug = False

    def __call__(self, analysis):
        """Calling the atlas object on an analysis will initialize it.

        Parameters
        ----------
        analysis : Analysis object or dict

        """
        if isinstance(analysis, dict):
            analysis = anal.Analysis(analysis)
        self.init_analysis(analysis)

    def __str__(self):
        """String representation."""



    # Initialization methods
    def init_paradigm(self, paradigm):
        """Initialize the atlas with a paradigm.
        
        Parameters
        ----------
        paradigm : str
            Full paradigm name
        
        """
        self.paradigm = paradigm
        self._init_paradigm = True


    def init_analysis(self, analysis):
        """Initialize the atlas with an analysis.
        
        Parameters
        ----------
        analysis : Analysis object or dict
        
        """
        if not self._init_subject:
            raise InitError("Subject")

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
        self._init_analysis = True         

    # Operation methods
    def __copy_atlas(self):
        """Copy original atlas file to pyroi atlas tree."""
        if self.manifold == "volume":
            shutil.copy(self.origatlas, self.atlas)  
        else:
            shutil.copy(self.origatlas % self.hemi,
                        self.atlas % self.hemi)

    def __sourcenames_to_lutdict(self):                        
        """Turn the list of sourcenames into a lookup dict."""
        self.lutdict = {}
        for i, name in enumerate(self.sourcenames):
            self.lutdict[i+1] = name

    # Display methods
    def display(self):
        """Display the atlas.
        
        This method will launch a viewing program that will display
        the atlas.  For native-space atlases, the atlas must be
        initialized with a subject.  Volume atlases are displayed
        with Freeview, while surface atlases are displayed on the
        inflated surface with tksurfer.

        Examples
        --------
        >>> atlas = roi.init_atlas("atlasname", "subj_id")
        >>> atlas.make_atlas()
        >>> atlas.display()

        """
        if not self._init_subject and self.source in ["freesurfer", "label"]:
            raise InitError("Subject")

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

        if self.debug:
            print " ".join(cmd)
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
            print " ".join(cmd)
        else:
            subprocess.call(cmd)

    def check_registration(self):
        """Open a tkregister2 session to check registration"""
        if not self._init_subject:
            raise InitError("Subject")
        
        cmd = ["tkregister2"]

        cmd.append("--mov %s" % cfg.meanfunc(self.paradigm, self.subject))
        cmd.append("--reg %s" % self.regmat)
        cmd.append("--surf")

        if self.debug:
            print " ".join(cmd)
        else:
            subprocess.call(cmd)
        

    # Processing methods
    def make_atlas(self, reg=False):
        """Run the neccessary preprocessing steps to make a mask or label atlas.
        
        For native-space atlases (Freesurfer and Label atlases), a subject
        must be initialized.  This is uneccesary for standard-space atlases.


        Parameters
        ----------
        reg : bool, optional
            If true, Freesurfer's bbregister program will be run to register
            the mean functional volume to the anatomical.  This is only rele-
            vant for Freesurfer atlases.  It is false by default because 
            registration can take a while.
        
        Returns
        -------
        RoiResult object
            
        """
        res = RoiResult()
        if self.source == "mask":
            res(self.__make_mask_atlas())
            res(self.__stats())
        elif self.source == "label":
            if not self._init_subject:
                raise InitError("Subject")
            res(self.__make_label_atlas())
            res(self.__stats())
        elif self.source == "freesurfer":
            if not self._init_subject:
                raise InitError("Subject")
            res(self.__make_freesurfer_atlas(reg))
            res(self.__stats())
        else:
            res("No make_atlas processing neccessary for %s atlases." 
                % self.source)
        return res

    def group_make_atlas(self, subjects=None):
        """Run atlas preprocessing steps for a list of subjects.
        
        Prerequisite
        ------------
        For native space atlases, the paradigm has to be initialized.  
        This is uneccesary for standard space atlases.

        Parameters
        ----------
        subjects : list, or str, optional
            List of subjects to preprocess. If a string, it runs the
            group defined by that name in the config file. Will run
            the full subject list from config if ommitted.
           
        Returns
        -------
        RoiResult object

        """
        if subjects is None:
            subjects = cfg.subjects()
        elif isinstance(subjects, str):
            subjects = cfg.subjects(subjects)
        result = RoiResult()
        for subject in subjects:
            self.init_subject(subject)
            res = self.make_atlas()
            print res
            result(res)
        return result

    def __make_mask_atlas(self):
        """Make the single atlas image and look-up-table from a group of masks."""
        self.tempdir = os.path.join(self.basedir, ".temp")
        if not os.path.isdir(self.tempdir): os.mkdir(self.tempdir)
        self.tempvols = []
        result = RoiResult(self.__write_lut())
        for segnum in range(1, len(self.sourcefiles) + 1):
            res = self.__adj_binary_segvol(segnum)
            result(res)

        res = self.__combine_segvols()
        result(res)
        shutil.rmtree(self.tempdir)

        return result

    def __adj_binary_segvol(self, segnum):
        """Adjust the segmentation value of a binary mask image."""
        adjust = fs.Concatenate()

        adjust.inputs.invol = self.sourcefiles[segnum - 1]
        output = os.path.join(self.tempdir, "adj-%s" 
                              % os.path.split(self.sourcefiles[segnum-1])[1])
        self.tempvols.append(output)
        adjust.inputs.outvol = output
        adjust.inputs.mul = segnum

        return self._nipype_run(adjust)

    def __combine_segvols(self):
        """Combine adjusted segvols into one atlas."""
        combine = fs.Concatenate()

        combine.inputs.invol = self.tempvols
        combine.inputs.outvol = self.atlas
        combine.inputs.combine = True

        return self._nipype_run(combine)

    def __make_label_atlas(self):
        """Turn a list of label files into a label annotation."""
        result = RoiResult(self.__write_lut())
        result(self.__resample_labels())
        result(self.__gen_annotation())
        return result

    def __resample_labels(self):
        """Resample label files from fsaverage surface to native surfaces."""
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

    def __gen_annotation(self):
        """Create an annotation from a list of labels."""
        if os.path.isfile(self.origatlas % self.hemi) and not self.debug:
            os.remove(self.origatlas)
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
                self.__copy_atlas()
                res("Copying %s to atlas directory" % self.atlasname)
            except IOError:
                res("IOError: Atlas copy failed")

        return res
    
    def __write_lut(self):
        """Write a look up table to the roi atlas directory."""
        lutfile = open(self.lutfile, "w")
        for id, name in self.lutdict.items():
            lutfile.write("%d\t%s\t\t\t" % (id, name))
            for color in np.random.randint(0, 256, 3):
                lutfile.write("%d\t" % color)
            lutfile.write("0\n")

        lutfile.close()
        if self.debug: os.remove(self.lutfile)
        return RoiResult("Writing %s" % self.lutfile)

    def __make_freesurfer_atlas(self, reg=False):
        """Run atlas preprocessing steps for a Freesurfer atlas."""
        if not os.path.isfile(self.regmat) and not reg:
            print ("\nRegistration matrix not found."
                   "\nCall method with the argument 'reg=True' to create.")
            return
        result = RoiResult()
        if self.manifold == "volume":
            if reg:
                reg = FSRegister()
                reg.init_paradigm(self.paradigm)
                reg.init_subject(self.subject)
                result(reg.register())
            result(self.__resample())
        return result

    def __resample(self):
        """Resample a freesurfer volume atlas into functional space."""

        transform = fs.ApplyVolTransform()

        transform.inputs.targfile = self.origatlas
        transform.inputs.sourcefile = self.meanfuncimg
        transform.inputs.tkreg = self.regmat
        transform.inputs.inverse = True
        transform.inputs.interp = "nearest"
        transform.inputs.outfile = self.atlas

        return self._nipype_run(transform)

    def __stats(self):
        """Generate a summary of voxel/vertex counts for all regions in an atlas."""
        if not self._init_subject:
            raise InitError("Subject")
        
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
        
        """Running this manually until NiPype interface is fixed
        segstats = fs.SegStats()

        segstats.inputs.annot = [self.subject, hemi, self.fname[3:-6]]
        segstats.inputs.invol = self.atlas % hemi
        segstats.inputs.segid = self.all_regions
        segstats.inputs.sumfile = self.statsfile % hemi

        return self._nipype_run(segstats)
        """
        cmd = ["mri_segstats"]

        cmd.append("--annot %s %s %s" % (self.subject, hemi, self.atlasname))
        cmd.append("--sum %s" % self.statsfile % hemi)
        ids = self.all_regions[hemi]
        ids.sort()
        for id in ids:
            cmd.append("--id %d" % id)

        return self._manual_run(cmd)

    def __vol_stats(self):
        """Generate stats for a volume atlas."""
        segstats = fs.SegStats()

        segstats.inputs.segvol = self.atlas
        segstats.inputs.invol = self.atlas
        ids = self.all_regions
        ids.sort()
        segstats.inputs.segid = ids
        segstats.inputs.sumfile = self.statsfile

        return self._nipype_run(segstats)

    def prepare_source_images(self, reg=False):
        """Prepare the functional and statistical images for extraction.
        
        An analysis must be initialized in the atlas

        Parameters
        ----------
        reg = bool, optional
            If True and analysis is on the surface, will use Freesurfer's
            bbregister program to register the mean functional to the
            anatomical so statisitcal images can be sampled onto the surface.
            It is False by default, because registration can take a long time.

        Returns
        -------
        RoiResult object

        """
        if not self._init_analysis:
            raise InitError("Analysis")
        if not reg:
            if self.manifold == "surface" and not os.path.isfile(self.regmat):
                print ("\nRegistration matrix not found."
                       "\nCall method with the argument 'reg=True' to create.")
                return

        res = RoiResult()
        if self.manifold == "surface" and reg:
            reg = FSRegister()
            reg.init_paradigm(self.analysis.paradigm)
            reg.init_subject(self.subject)
            res(reg.register())
            if self.mask and self.analysis.maskpar != self.analysis.paradigm:
                reg = FSRegister()
                reg.init_paradigm(self.analysis.maskpar)
                reg.init_subject(self.subject)
                res(reg.register())
        extractvols = anal.init_stat_object(self.analysis)
        extractvols.init_subject(self.subject)
        res(extractvols.concatenate())
        if self.manifold == "surface":
            res(extractvols.sample_to_surface())
        if self.mask:
            tstat = anal.TStatImage(self.analysis)
            tstat.init_subject(self.subject)
            res(tstat.convert_to_sig())
            if self.manifold == "surface":
                sig = anal.SigImage(self.analysis)
                sig.init_subject(self.subject)
                res(sig.sample_to_surface())

        return res

    def group_prepare_source_images(self, analysis, subjects=None, reg=False):
        """Prepare the source images for a group.

        Parameters
        ----------
        analysis : dict or Analysis object
        subjects : list, or str, optional
            List of subjects to preprocess. If a string, it runs the
            group defined by that name in the config file. Will run
            the full subject list from config if ommitted.
        reg : bool, optional
            Perform intramodal registration, if applicable.  False by default.

        Returns
        -------
        RoiResult object

        """
        if subjects is None:
            subjects = cfg.subjects()
        elif isinstance(subjects, str):
            subjects = cfg.subjects(subjects)
        result = RoiResult()
        for subject in subjects:
            self.init_subject(subject)
            self.init_analysis(analysis)
            res = self.prepare_source_images(reg)
            print res
            result(res)

        return result

    def extract(self):
        """Extract average functional data from select regions in an atlas.
        
        This prints a text file with the average statistic for each region
        to the $main_dir/roi/analysis/ directory structure.  It also saves
        a binary "volume" where each voxel represents a region in the atlas.
        See the database functions to collect this data for statistical anal-
        ysis.

        Returns
        -------
        RoiResult object.
        
        Note
        ----
        Currently, this just averages the voxelwise statistics over all voxels
        considered to be in each region, after applying a functional mask (if
        included in the analysis parameters).  If a mask is applied, it will
        also generate a count of how many voxels/vertices were included in the
        final ROI.

        """
        if not self._init_analysis:
            raise InitError("analysis")

        if self.manifold == "volume":
            return self.__vol_extract()
        else:
            results = RoiResult()
            for hemi in self.iterhemi:
                res = self.__surf_extract(hemi)
                results(res)
            return results

    def __surf_extract(self, hemi):
        """Internal function to extract from a surface."""
        funcex = fs.SegStats()
        
        funcex.inputs.annot = [self.subject, hemi, self.fname[:-6]]
        funcex.inputs.invol = self.analysis.source % hemi
        ids = self.regions[hemi]
        ids.sort()
        funcex.inputs.segid = ids
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
        """Internal function to extract from a volume."""
        funcex = fs.SegStats()

        funcex.inputs.segvol = self.atlas
        funcex.inputs.invol = self.analysis.source
        ids = self.regions
        ids.sort()
        funcex.inputs.segid = ids
        if self.mask:
            funcex.inputs.maskvol = self.analysis.maskimg
            funcex.inputs.maskthresh = self.analysis.maskthresh
            funcex.inputs.masksign = self.analysis.masksign
        funcex.inputs.sumfile = self.funcstats
        funcex.inputs.avgwftxt = self.functxt
        funcex.inputs.avgwfvol = self.funcvol

        return self._nipype_run(funcex)

    def group_extract(self, analysis, subjects=None):
        """Extract functional data for a group of subjects.
        
        See the docstring for the extract() method for more information.
        
        Parameters
        ----------
        analysis : Analysis object or dict
        subjects : list, or str, optional
            List of subjects to preprocess. If a string, it runs the
            group defined by that name in the config file. Will run
            the config setup module.
            
        """
        if subjects is None:
            subjects = cfg.subjects()
        elif isinstance(subjects, str):
            subjects = cfg.subjects(subjects)
        if isinstance(analysis, dict):
            analysis = anal.Analysis(analysis)
        for subj in subjects:
            self.init_paradigm(analysis.paradigm)
            self.init_subject(subj)
            self.init_analysis(analysis)
            print self.extract()

class FreesurferAtlas(Atlas):
    """Class for Freesurfer atlases.

    Parameters
    ----------
    atlas : str or dict
        The name of an atlas defined in your setup module, or a dictionary
        of atlas parameters.
    paradigm : str, optional
        The name of a paradigm to initialize the atlas for. 
    subject : str, optional
        The name of a subject to initialize the atlas for.  

    Examples
    --------
    
    Single Subject:
    
    >>> aseg = roi.FreesurferAtlas("aseg", "par_name", "subj_id")
    >>> res = aseg.make_atlas()
    >>> analysis = roi.cfg.analysis(0)
    >>> aseg(analysis)
    >>> aseg.prepare_source_images()
    >>> res = aseg.extract()

    Group:

    >>> aseg = roi.FreesurferAtlas("aseg", "par_name")
    >>> res = aseg.group_make_atlas()
    >>> analysis = roi.cfg.analysis(0)
    >>> res = aseg.group_prepare_source_images(analysis)
    >>> res = aseg.group_extract(analysis)

    Atlas Information
    -----------------
    The FreesurferAtlas class can be used for the Freesurfer aseg (automatic
    subcortical segmentation) or either flavour of aparc (automatic cortical
    parcellation).  In theory, any "Freesurfer style" atlas should work with
    this class.  Custom atlases are not yet officially implemented in the setup
    module, but it should be possible to hack together a working atlas object.

    If you want to extract from ROIs defined by Freesurfer labels (e.g, ROIs
    drawn around activation blobs), see the LabelAtlas class.
    
    Anatomical data must have been preprocessed in Freesurfer (with recon-all)
    to use this class.  When using cortical atlases, functional/statistical 
    volumes are automatically sampled onto the reconstructed cortical surface.

    References
    ----------
    Fischl, B., D.H. Salat, E. Busa, M. Albert, M. Dieterich, C. Haselgrove,
        A. van der Kouwe, R. Killiany, D. Kennedy, S. Klaveness, A. Montillo,
        N. Makris, B. Rosen, and A.M. Dale, (2002).  Whole Brain Segmentation:
        Automated Labeling of Neuroanatomical Structures in the Human Brain,  
        Neuron, 33:341-355.     
    Desikan, R.S., F. Segonne, B. Fischl, B.T. Quinn, B.C. Dickerson, D. 
        Blacker, R.L. Buckner, A.M. Dale, R.P. Maguire, B.T. Hyman, M.S. 
        Albert, and R.J. Killiany, (2006).  An automated labeling system 
        for subdividing the human cerebral cortex on MRI scans into gyral 
        based regions of interest,  NeuroImage, 31(3):968-80.  
    Destrieux C., B. Fischl, A. Dale, E. Halgren, (2010).  Automatic parcel-
        lation of human cortical gyri and sulci using standard anatomical 
        nomenclature. Neuroimage, 2010 [Epub ahead of print] 
        
    """
    def __init__(self, atlas, paradigm=None, subject=None, **kwargs):
               
        if isinstance(atlas, str):
            atlasdict = cfg.atlases(atlas)
        else:
            atlasdict = atlas

        Atlas.__init__(self, atlasdict, **kwargs)

        tree.make_fs_atlas_tree()
        
        if self.manifold == "surface":
            self.iterhemi = ["lh","rh"]
        self.fname = atlasdict["fname"]

        self.lutfile = os.path.join(os.getenv("FREESURFER_HOME"), 
                                    "FreeSurferColorLUT.txt")

        dictdict = {"aseg.mgz": "aseg-lut.txt",
                    "aparc.annot": "aparc-lut.txt",
                    "aparc.a2009s": "aparc-aparc.a2009s-lut.txt"}
        datadir = os.path.join(os.path.split(__file__)[0], "data", "Freesurfer")
        dictfile = os.path.join(datadir, dictdict[self.fname])
        lutarray = np.genfromtxt(dictfile, str)
        self.lutdict = {}
        for row in lutarray:
            self.lutdict[int(row[0])] = row[1]
        
        convtable = {1:(10,49), 2:(11,50), 2:(12,51), 3:(13,52), 
                     4:(17,53), 5:(18,54), 6:(26,58), 7:(28,60)}
        if self.fname == "aseg.mgz":
            self.regions = ([convtable[id][0] for id in self.atlasdict["regions"]] + 
                            [convtable[id][1] for id in self.atlasdict["regions"]])
            self.all_regions = self.lutdict.keys()
            self.regionnames = [self.lutdict[id] for id in self.regions]
        else:
            self.regions = {}
            self.all_regions = {}
            if self.fname == "aparc.annot":
                self.regions["lh"] = [1000 + id for id in self.atlasdict["regions"]]
                self.regions["rh"] = [2000 + id for id in self.atlasdict["regions"]]
                self.all_regions["lh"] = [1000 + id for id in self.lutdict.keys()]
                self.all_regions["rh"] = [2000 + id for id in self.lutdict.keys()]
            else:
                self.regions["lh"] = self.atlasdict["regions"]
                self.regions["rh"] = self.atlasdict["regions"]
                self.all_regions["lh"] = self.lutdict.keys()
                self.all_regions["rh"] = self.lutdict.keys()
            self.regionnames = (["lh-" + self.lutdict[id] for id in self.atlasdict["regions"]] +
                                ["rh-" + self.lutdict[id] for id in self.atlasdict["regions"]])
        self.regionnames.sort()                                


        self.basedir = os.path.join(self.roidir, "atlases", "freesurfer")

        if paradigm is not None: self.init_paradigm(paradigm)
        if subject is not None: self.init_subject(subject)

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        if not self._init_paradigm:
            raise InitError("Paradigm")
        self.subject = subject
        if self.manifold == "surface":
            pardir = ""
            fname = "%s." + self.fname
            atlasname = "%s." + self.atlasname
            origdir = "label"
            ext = "annot"
        else:
            pardir = self.paradigm
            fname = self.fname
            atlasname = self.atlasname
            origdir = "mri"
            ext = "mgz"

        self.meanfuncimg = cfg.pathspec("meanfunc", self.paradigm,
                                        self.subject)
        self.regmat = os.path.join(self.roidir, "reg", self.paradigm,
                                   subject, "func2orig.dat")

        if self.manifold != "reg":
            self.origatlas = os.path.join(self.subjdir, subject, origdir, fname)
            self.atlas = os.path.join(self.basedir, self.manifold, pardir, subject,
                                      self.atlasname, "%s.%s" % (atlasname, ext))
            self.statsfile = os.path.join(self.basedir, self.manifold, pardir,
                                          subject, self.atlasname,
                                          "%s.stats" % atlasname)

            self._init_subject = True

class FSRegister(FreesurferAtlas):
    """Extension of FreesurferAtlas for intramodal registration.
    
    This class is used internally by the make_atlas() and prepare_source_image()
    methods, so it is usually not neccesary for a user to interface with it.
    The register() method runs the Freesurfer program bbregister, which can
    internally find a linear transform matrix with either FSL FLIRT, the SPM
    coregister routine, or from header geometry.  It uses FLIRT by default.

    Examples
    --------
    >>> reg = roi.FSRegister("par_name", "subj_id")
    >>> reg.register()

    """
    def __init__(self, paradigm=None, subject=None, **kwargs):

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
        
        if paradigm is not None: self.init_paradigm(paradigm)
        if subject is not None: self.init_subject(subject)

    # Processing methods
    def register(self, method="fsl"):
        """Register functional space to Freesurfer original atlas space.
        
        Parameters
        ----------
        method : str, optional
            Specifiy the initial registration method.  Options are 'fsl',
            'spm', or 'header'.  Defaults to 'fsl'.

        Returns
        -------
        RoiResult object

        """
        reg = fs.BBRegister()

        reg.inputs.subject_id = self.subject
        reg.inputs.sourcefile = self.meanfuncimg
        reg.inputs.t2_contrast = True
        reg.inputs.outregfile = self.regmat       
        if method == "fsl":
            reg.inputs.init_fsl = True
        elif method == "spm":
            reg.inputs.init_spm = True
        elif method == "header":
            reg.inputs.init_header = True

        return self._nipype_run(reg)


class HarvardOxfordAtlas(Atlas):
    """Class for the HarvardOxford atlas included with FSL.   

    Parameters
    ----------
    atlas : str or dict
        The name of an atlas defined in your setup module, or a dictionary
        of atlas parameters.
    subject : str, optional
        The name of a subject to initialize the atlas for. 

    Examples
    --------

    Single Subject:
    
    >>> fslatlas = roi.HavardOxfordAtlas("fsl")
    >>> analysis = roi.cfg.analysis(0)
    >>> fslatlas(analysis)
    >>> res = fslatlas.prepare_source_images()
    >>> res = fslatlas.extract()
    
    Group:
    
    >>> fslatlas = roi.HarvardOxfordAtlas("fsl")
    >>> analysis = roi.cfg.analysis(0)
    >>> res = fslatlas.group_prepare_source_images(analysis)
    >>> res = fslatlas.group_extract()

    Atlas Information
    -----------------
    The HarvardOxford Atlas is a probabilistic standard-space atlas 
    drawn from data collected at the Harvard Center for Morphometric
    Analysis and Oxford's FMRIB.  Two versions are provided with PyROI,
    corresponding to thresholding the probabilistic atlas at 25% or 50%.
    See http://www.fmrib.ox.ac.uk/fsl/fslview/atlas-descriptions.html
    for more information.  The FSL volumes were modified slightly using
    scripts written by Russ Poldrack to give different segmentation 
    values for left and right hemisphere structures.

    """
    def __init__(self, atlas, subject=None, **kwargs):

        if isinstance(atlas, str):
            atlasdict = cfg.atlases(atlas)
        else:
            atlasdict = atlas

        Atlas.__init__(self, atlasdict, **kwargs)
     
        tree.make_fsl_atlas_tree()

        self.thresh = atlasdict["probthresh"]
        pckgdir = os.path.split(__file__)[0]
        filename = "HarvardOxford-%d.nii" % self.thresh
        self.atlas = os.path.join(pckgdir, "data", "HarvardOxford", filename)
        self.lutfile = os.path.join(os.path.split(__file__)[0], "data", 
                                 "HarvardOxford", "HarvardOxford-LUT.txt")
        self.regions = atlasdict["regions"]

        self.regionnames = [self.lutdict[id] for id in self.regions]
        self.regionnames.sort()                                

        if subject is not None: self.init_subject(subject)

    def init_subject(self, subject):
       """Initialize the atlas for a subject"""
       self.subject = subject
   
       self._init_subject = True


class LabelAtlas(Atlas):
    """Atlas class for an atlas construced from surface labels.

    Parameters
    ----------
    atlas : str or dict
        The name of an atlas defined in your setup module, or a dictionary
        of atlas parameters.
    subject : str, optional
        The name of a subject to initialize the atlas for.

    Examples
    --------

    Single subject:
    
    >>> labls = roi.LabelAtlas("social_labels", "subj_id")
    >>> labls.make_atlas()
    >>> analysis = roi.cfg.analysis(0)
    >>> labls.init_analysis(analysis)
    >>> labls.extract()

    Group:
    
    >>> labls = roi.LabelAtlas("social_labels")
    >>> labls.group_make_atlas()
    >>> analysis = roi.cfg.analysis(0)
    >>> labls.group_extract(analysis)

    Atlas Information
    -----------------
    The LabelAtlas class can construct and extract from an atlas 
    composed of any number of non-overlapping Freesurfer surface 
    label files defined on the fsaverage standard-space subject.  
    These labels will be resampled back to each subject's native
    surface space via a spherical transform.  This class should 
    not be used for labels derived from Freesurfer's automatic
    parcellations that are produced during the reconstruction
    process.  See the FreesurferAtlas class to extract data
    from those regions.

    """
    def __init__(self, atlas, subject, **kwargs):

        if isinstance(atlas, str):
            atlasdict = cfg.atlases(atlas)
        else:
            atlasdict = atlas
        
        Atlas.__init__(self, atlasdict, **kwargs)
        
        tree.make_label_atlas_tree()

        self.hemi = self.atlasdict["hemi"]
        self.iterhemi = [self.hemi]
        self.fname = "%s.annot" % self.atlasname

        self.basedir = os.path.join(self.roidir, "atlases", "label")
        
        self.lutfile = os.path.join(self.basedir, cfg.projectname(), 
                                    "lookup_tables",
                                    "%s.lut" % self.atlasname)
        self.regions = {}
        self.regions[self.hemi] = self.lutdict.keys()
        self.all_regions = {}
        self.all_regions[self.hemi] = self.regions
        self.regionnames = [self.lutdict[id] for id in self.regions["hemi"]]
        self.regionnames.sort()                                

        if subject is not None: self.init_subject(subject)

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        self.subject = subject
        self.atlasdir = os.path.join(self.basedir, cfg.projectname(),
                                     subject, self.atlasname)
        self.statsfile = os.path.join(self.atlasdir,
                                      "%s." + self.atlasname + ".stats")
        self.atlas = os.path.join(self.atlasdir, "%s." + self.fname)
        self.origatlas = os.path.join(self.subjdir, subject, 
                                      "label", "%s." + self.fname)
        
        self._init_subject = True


class MaskAtlas(Atlas):
    """Class for atlases constructed from binary volume masks.

    Parameters
    ----------
    atlas : str or dict
        The name of an atlas defined in your setup module, or a dictionary
        of atlas parameters.
    subject : str, optional
        The name of a subject to initialize the atlas for.

    Examples
    --------

    Single subject:
    
    >>> masks = roi.MaskAtlas("social_masks", "subj_id")
    >>> masks.make_atlas()
    >>> analysis = roi.cfg.analysis(0)
    >>> masks.init_analysis(analysis)
    >>> masks.extract()

    Group:
    
    >>> masks = roi.LabelAtlas("social_masks")
    >>> masks.group_make_atlas()
    >>> analysis = roi.cfg.analysis(0)
    >>> masks.group_extract(analysis)

    Atlas Information
    -----------------
    The MaskAtlas class can construct and extract from an atlas 
    defined by any number of non-overlapping binary mask images
    in standard volume space.  
    
    Note
    ----
    This has not yet been tested for masks in Analyze format, and
    it is quite likely that using Analyze masks will cause orienta-
    tion problems. If at all possible, use Nifti (both .nii single
    volumes and .img/.hdr pairs should work).

    """
    def __init__(self, atlasdict, **kwargs):

        if isinstance(atlasdict, str):
            atlasdict = cfg.atlases(atlasdict)
        
        Atlas.__init__(self, atlasdict, **kwargs)

        tree.make_mask_atlas_tree()
        
        self.fname = "%s.mgz" % self.atlasname

        self.basedir = os.path.join(self.roidir, "atlases",
                                    "mask", cfg.projectname())
        
        self.lutfile = os.path.join(self.basedir, "%s.lut" % self.atlasname)
        self.regions = self.lutdict.keys()
        self.all_regions = self.regions
        self.regionnames = [self.lutdict[id] for id in self.regions]
        self.regionnames.sort()                                
        
        self.atlas = os.path.join(self.basedir, self.fname)


        if subject is not None: self.init_subject(subject)

    # Initialization methods
    def init_subject(self, subject):
        """Initialize the atlas for a subject"""
        self.subject = subject
        
        self._init_subject = True


def init_atlas(atlasdict, subject=None, paradigm=None, **kwargs):
    """Initialize the proper atlas class with an atlas dictionary.
    
    Parameters
    ----------
    atlasdict : dict or str
        Atlas dictionary or atlas name, if internal config module is setup.
    subject : str, optional
        If included, the atlas will be initialized for this subject
    paradigm : str, optional
        If included, the atlas will be initialized for this paradigm.
        Note that this is only relevant for Freesurfer atlases.

    Returns
    -------
    Atlas object

    """
    if isinstance(atlasdict, str):
        atlasdict = cfg.atlases(atlasdict)
    if atlasdict["source"] == "freesurfer": 
        return FreesurferAtlas(atlasdict, paradigm, subject, **kwargs)
    elif atlasdict["source"] == "fsl": 
        return HarvardOxfordAtlas(atlasdict, subject, **kwargs)
    elif atlasdict["source"] == "label": 
        return LabelAtlas(atlasdict, subject, **kwargs) 
    elif atlasdict["source"] == "mask": 
        return MaskAtlas(atlasdict, subject, **kwargs)

