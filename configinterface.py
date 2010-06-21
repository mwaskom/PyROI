"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu
"""

import os
import re
import imp
import warnings
from glob import glob
import nipype.interfaces.freesurfer as fs
import exceptions as ex

__module__ = "configinterface"

# Look for a file indicating the setup module and import that module if found
if os.path.isfile(".roisetupfile"):
    
    fid = open(".roisetupfile","r")
    module = fid.read()
    fid.close()
    
    # Get rid of any extraneous whitespace
    m = re.search("\w+", module)
    if m:
        module = m.group()
    
    # Trim the file extension if it exists
    if module.endswith(".py"):
        module = pmodule[:-3]
    
    # Import the module
    file, name, desc = imp.find_module(module)
    try:
        setup = imp.load_module("setup", file, name, desc)
    finally:
        file.close()
    is_setup = True
    
    # Clean up
    del fid, m, module, file, name, desc
else:
    is_setup = False


def projectname():
    """Return the project name string.

    Returns
    -------
    str
    """
 
    return setup.projname


def analysis():
    """Return the analysis list.  
    
    If the variable type of analysis is a dictionary, it wraps it in a list.
   
    Returns
    -------
    list of dicts

    """

    analysis = setup.analysis

    if isinstance(analysis, dict):
        analysis = [analysis]

    return analysis


def atlases(atlasname=None):
    """Return the atlas specifications.
    
    This function deals with the ROI atlas defintions. If the scope is 
    empty when called, it will return the full atlas dictionary, where each
    entry specifies an atlas. If called with an atlas key as the argument,
    it will return the attribute dictionary for that atlas. The function 
    performs a fair amount of checking and addition of obvious but neccessary
    fields (via calls to private subfunctions), so always get atlas dictionaries
    from this function, not directly from the setup module.

    Parameters
    ----------
    atlasname : str, optional
        The atlas name, or None to return the full dictionary.

    Returns
    -------
    dict

    """
    atlases = setup.atlases
    
    for atlas in atlases:
        atlases[atlas]["atlasname"] = atlas
        for k, v in atlases[atlas].items():
            if not k.islower():
                atlases[atlas][k.lower()] = v
                del atlases[atlas][k]
        if "source" not in atlases[atlas]:
            raise ex.SetupError("Source missing from %s atlas dictionary" % atlas)
        atlases[atlas]["source"] = atlases[atlas]["source"].lower()
        if atlases[atlas]["source"] == "freesurfer":
            atlases[atlas] = __prep_freesurfer_atlas(atlases[atlas])
        elif atlases[atlas]["source"] == "fsl":
            atlases[atlas] = __prep_fsl_atlas(atlases[atlas])
        elif atlases[atlas]["source"] == "label":
            atlases[atlas] = __prep_label_atlas(atlases[atlas])
        elif atlases[atlas]["source"] == "mask":
            atlases[atlas] = __prep_mask_atlas(atlases[atlas])

    if atlasname is None:
        return atlases
    else:
        return atlases[atlasname]

def __check_fields(atlasfields, atlasdict):
    """Check whether any fields are missing or unexpected in an atlas dictionary."""
    extra = [k for k in atlasdict if k not in atlasfields]
    missing = [f for f in atlasfields if f not in atlasdict]
    atlasname = atlasdict["atlasname"]
    if extra:
        raise ex.SetupError("Unexpected field(s) %s found in %s dictionary"\
                            % (extra, atlasname))
    if missing:
        raise ex.SetupError("Field(s) %s missing from %s dictionary"\
                            % (missing, atlasname))

def __prep_freesurfer_atlas(atlasdict):
    """Prepare a Freesurfer atlas dictionary."""
    atlasfields = ["atlasname", "source", "fname", "manifold", "regions"]
    __check_fields(atlasfields, atlasdict)

    atlasdict["manifold"] = atlasdict["manifold"].lower()
    if atlasdict["manifold"] not in ["surface", "volume"]:
        raise ex.SetupError("Manifold setting '%s' for %s atlas not understood"\
                            % (atlasdict["manifold"], atlasdict["atlasname"]))

    if not os.path.isdir(fssubjdir()):
        raise ex.SetupError("Using Freesurfer atlas with illegitimite "
                            "subjects directory path")

    if not isinstance(atlasdict["regions"], list):
        atlasdict["regions"] = [atlasdict["regions"]]

    return atlasdict                                

def __prep_fsl_atlas(atlasdict):
    """Prepare a HarvardOxford atlas dictionary."""
    atlasfields = ["atlasname", "source", "probthresh", "regions"]
    __check_fields(atlasfields, atlasdict)

    atlasdict["manifold"] = "volume"

    if atlasdict["probthresh"] not in [25, 50]:
        raise ex.SetupError("HarvardOxford atlas probthresh setting must be either 25 or 50.")

    if not isinstance(atlasdict["regions"], list):
        atlasdict["regions"] = [atlasdict["regions"]]

    return atlasdict                                

def __prep_label_atlas(atlasdict):
    """Prepare a label atlas dictionary"""
    atlasfields = ["atlasname", "source", "hemi", "sourcedir", "sourcefiles"]
    __check_fields(atlasfields, atlasdict)
    
    if not os.path.isdir(fssubjdir()):
        raise ex.SetupError("Using label atlas with illegitimite "
                            "Freesurfer Subjects Directory path")

    if not os.path.isabs(atlasdict["sourcedir"]):
        atlasdict["sourcedir"] = os.path.join(setup.basepath, atlasdict["sourcedir"])

    atlasdict["manifold"] = "surface"

    if atlasdict["sourcefiles"] == "all" or ["all"]:
        atlasdict["sourcefiles"] = glob(os.path.join(atlasdict["sourcedir"], "*.label"))
    
    lfiles = atlasdict["sourcefiles"]
    if not isinstance(lfiles, list):
        lfiles = [lfiles]
    lnames = []
    for i, lfile in enumerate(lfiles):
        path, lfile = os.path.split(lfile)
        if lfile.endswith(".label"):
            lfile, ext = os.path.splitext(lfile)
        lfiles[i] = os.path.join(atlasdict["sourcedir"], lfile + ".label")
        lnames.append(lfile)
        if not os.path.isfile(lfiles[i]):
            warnings.warn("%s does not exist." % lfiles[i])
    atlasdict["sourcefiles"] = lfiles
    atlasdict["sourcenames"] = lnames
    return atlasdict

def __prep_mask_atlas(atlasdict):
    """Prepare a mask atlas dictionary"""
    atlasfields = ["atlasname", "source", "sourcedir", "sourcefiles"]
    __check_fields(atlasfields, atlasdict)

    if not os.path.isabs(atlasdict["sourcedir"]):
        atlasdict["sourcedir"] = os.path.join(setup.basepath, atlasdict["sourcedir"])

    atlasdict["manifold"] = "volume"
    
    if atlasdict["sourcefiles"] == "all" or ["all"]:
        atlasdict["sourcefiles"] = glob(os.path.join(atlasdict["sourcedir"],
                                        "*[.img|.nii|.nii.gz|.mgh|.mgz]"))

    lfiles = atlasdict["sourcefiles"]
    if not isinstance(lfiles, list):
        lfiles = [lfiles]

    notimgs = [f for f in lfiles if not f.endswith((".img",".nii",".nii.gz",".mgh",".mgz"))]
    if notimgs:
        spl = lambda fpath: os.path.splitext(os.path.split(fpath)[1])[0]
        repimgs = []
        for img in notimgs:
            imglob = glob(os.path.join(atlasdict["sourcedir"],
                                       img + "*[.img|.nii|.nii.gz|.mgh|.mgz]"))
            if len(imglob) == 1:
                lfiles[lfiles.index(img)] = imglob[0]
                repimgs.append(spl(imglob[0]))
        if not len(notimgs) == len(repimgs):
            raise ex.SetupError(
                "File type of mask(s) %s could not be determined or is not supported"\
                 % [img for img in notimgs if img not in repimgs])

    lnames = []
    for i, lfile in enumerate(lfiles):
        path, lfile = os.path.split(lfile)
        lfiles[i] = os.path.join(atlasdict["sourcedir"], lfile)
        lfile, ext = os.path.splitext(lfile)
        lnames.append(lfile)
        if not os.path.isfile(lfiles[i]):
            warnings.warn("%s does not exist." % lfiles[i])
    atlasdict["sourcefiles"] = lfiles
    atlasdict["sourcenames"] = lnames
    return atlasdict

def fssubjdir():
    """Set and return the path to the Freesurfer Subjects directory.

    Returns
    -------
    str
    
    """
    
    dirpath = setup.subjdir

    subjdir = fs.FSInfo.subjectsdir(os.path.abspath(dirpath))

    return subjdir


def paradigms(parname=None, case="upper"):
    """Return paradigm information.
    
    This function has two uses. If called with an empty scope, it will
    return a list of the paradigms inolved in the project. If called with 
    the full name of a paradigm as the first argument, it will return the 
    two-letter code for that paradigm. You may specify whether the paradigm
    code should be returned in upper or lower case using the second argument
    (upper case is default).

    Parameters
    ----------
    parname : string
        full paradigm name (if None, returns the full list of paradigms)
    case : string
        "upper" or "lower" -- Def: upper

    Returns
    -------
    list of full paradigm names or string 
    
    """

    pardict = setup.paradigms

 
    if parname is None:
        return pardict.keys()
    else:
        if case == "lower":
            return pardict[parname].lower()
        elif case == "upper":
            return pardict[parname].upper()
        else:
            raise Exception("Case argument \"%s\" to " % case +\
	                        "config.Paradigms not understood.") 


def betas(par=None, retval=None):
    """Return information about task regressors.
    
    This function deals with both condition and file names for the 
    first-level regressors.  It takes the name of a paradigm and the 
    type of list to return as parameters.  If asked for "names," it 
    will return the list of condition names.  If asked for "images," 
    it will return the list of image file names associated with task
    betas for that paradigm. If par is None, it will return the full
    conditions dictionary.

    If the hrfconditions variable is set higher than 1, it will add
    n names to the condition list in the format cond-n.  You can also
    control which of the multiple components will be returned (and thus
    involved in the analysis) with the betastoextract variable. Note 
    that this functionality is included for forward compatability, but 
    that it has not yet actually been tested.

    Parameters
    ----------
    par : str
        paradigm
    retval : str
        "images" or "names"

    Returns
    -------
    list or dict
    
    """    

    # Get the elements from the setup function 
    hrfcomponents = setup.hrfcomponents
    betastoextract = setup.betastoextract
    conditions = setup.conditions

    # Return the conditions dictionary and hrfcomponents if scope is empty
    if par is None:
        return conditions, hrfcomponents

    # Check that the paradigm is in the conditions dictionary
    # Exit with a more informative error if it is not
    try:
        dump = conditions[par]
    except KeyError:
        raise Exception("Paradigm \"%s\" not found in conditions dictionary"\
                        % par)

    # Wrap betastoextract in a list if it"s just an int
    if isinstance(betastoextract, int):
        betastoextract = [betastoextract]

    # Initialize filename and multi-component condition name lists
    condimages = []
    mcompnames = []

    # If extracting all beta components, make that list
    if betastoextract == "all" or betastoextract == ["all"]:
        betastoextract = range(1, hrfcomponents + 1)

    # Insert additional component image/names
    for i in range(1,len(conditions[par])+1):
        for j in range(0,hrfcomponents):
            if j+1 in betastoextract:
                # Add the component number to condition names
                mcompnames.append("%s-%02d" % (conditions[par][i-1], j+1))
                num = i + ((i-1)*(hrfcomponents-1)) + j
                # Add the image filename to the image list
                condimages.append("beta_%04d.img" % num)
    
    # Figure out what the function is being asked about and return it
    if retval == "images":
        return condimages
    elif retval == "names" and (hrfcomponents == 1 or betastoextract == [1]):
        return conditions[par]
    elif retval == "names" and hrfcomponents > 1:
        return mcompnames
    else:
        raise Exception("Beta return type \"%s\" not understood" % retval)


def contrasts(par=None, type="con-img", format=".nii"):
    """Return information about contrasts.
    
    This function controls the contrast images used in the analysis.
    It takes the paradigm, image type, and image format as parameters 
    and returns a dictionary mapping contrast shorthand names to image
    file names.

    Parameters
    ----------
    par : str
        Paradigm
    type : str
        "sig", "T-map", or "con-img" -- def: con-img
    format : str
        File extension -- def: .nii

    Returns
    -------
    dictionary

    """

    # Get the specified dict from setup
    contrastdict = setup.contrasts

    # Return the full dict if called with an empty scope
    if par is None:
        return contrastdict

    # Get the dictionary for the paradigm we"re looking at
    contrasts = contrastdict[par]

    # Initialize the dictionaries for file names
    contrasts_sig = {}
    contrasts_tstat = {}
    contrasts_con = {}

    if not format.startswith("."): 
        format = "." + format

    # Iterate through the contrasts and populate the filename dictionaries
    for con in contrasts:
        contrasts_sig[con] = "spmSig_%04d%s" % (contrasts[con], format)
        contrasts_tstat[con] = "spmT_%04d%s" % (contrasts[con], format)
        contrasts_con[con] = "con_%04d%s" % (contrasts[con], format)

    # Figure out what type of image the function is being asked about and return
    if type == "sig":
        return contrasts_sig
    elif type == "T-map":
        return contrasts_tstat
    elif type == "con-img":
        return contrasts_con
    else:
        raise Exception("Image type '%s' " %type +\
	                "not understood: use 'T-map', 'sig', or 'con-img'")

def meanfunc(paradigm, subject):
    """Return the path to a mean functional image.

    Note: this function simply globs nifti files from the path and takes the
    first one.  Standard NiPype behavior is to create a first level directory
    called "realign" for each paradigm/subject and store mean images there. 
    There may be issues if a NiPype is set up unusually or if it is not used
    for first level analysis

    Parameters
    ----------
    par : paradigm
    subj : subject

    Returns
    -------
    string
    
    """

    funcpath = pathspec("meanfunc", paradigm, subject)
    meanfuncimg = glob(funcpath)
    # XXX Add excpetion if this globs more than one file
    meanfuncimg = meanfuncimg[0]
    return meanfuncimg

def pathspec(imgtype, paradigm=None, subject=None, contrast=None):
    """Return the path to directories containing various first-level components.

    This function allows the ROI procesing pypeline to be free of any
    specific first-level directory structure. A variable path is specified
    in the setup function where the directory for paradigm, subject, and
    contrast is is signified by $variable for beta and contrast files
    separately.  This function expects those strings to be keyed by "betapath"
    and "contrastpath", respectively.

    In theory, this function should work for both SPM and FsFast first-level
    structures.  At the time of the writing of this docstring, however, the
    ROI pypeline does not yet handle the FsFast first level beta images
    themselves properly.

    Parameters
    -----------
    imgtype : timecourse, beta, meanfunc, or contrast
    paradigm : paradigm name, however it is specified in the actual path
    subject : subject name, however it is specified in the actual path
    contrast: : contrast name, however it is specified in the actual path

    Returns
    -------
    string of path to image directory

    """
    basepath = setup.basepath
    betapath = setup.betapath
    meanfuncpath = setup.meanfuncpath
    contrastpath = setup.contrastpath
    timecoursepath = setup.timecoursepath
    
    vardict = {"$paradigm" : paradigm,
               "$contrast" : contrast,
               "$subject" : subject}

    imgdict = {"beta": betapath,
               "meanfunc": meanfuncpath,
               "contrast": contrastpath,
               "timecourse": timecoursepath}
    
    varpath = os.path.join(basepath, imgdict[imgtype])

    for var in vardict:
        if var in varpath:
            varpath = varpath.replace(var,vardict[var])

    return varpath

def subjects(group = None, subject = None):
    """Return a list of subjects or subject group membership.
    
    This function controls the subjects and groups involved in the 
    analysis.  It takes either a group or a subject as a parameter.
    If called with an empty scope, it returns a list of all subjects.
    If called with the name of a group, it returns a list of the subjects
    in that group. If called with group = "groups", it returns a list of 
    the group names.  If called with the name of a subject, it will return
    the name of the group that subject is a member of.

    Parameters
    ----------
    group : group name or "groups"
    subject : subject name

    Returns
    -------
    list

    """

    subjects = setup.subjects

    for grp in subjects:
        subjects[grp].sort()
	
    if subject:
        for grp in subjects:
           if subject in subjects[grp]:
              return grp

    if group is None:
        all = []
        for grp in subjects:
	        all = all + subjects[grp]
        return all
    elif group in subjects:
        return subjects[group]
    elif group == "groups":
        return subjects.keys()
    else:
        raise Exception("Group '%s' not found." % group)


def overwrite(filetype=None):
    """Control file overwriting.
    
    Query whether a given filetype should be overwritten if it is found
    to exist at runtime.

    If this filetype is None, the function will return the dictionary

    Parameters
    ----------
    string specifying file type

    Returns
    -------
    boolean where True means "overwrite"
    
    """

    overwrite = setup.overwrite

    if filetype is None:
        return overwrite
    else:
        return overwrite[filetype]
