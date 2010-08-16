"""
The config interface module provides an interface to custom config modules.

If a file called ``.roisetupfile`` exists in the working directory when
PyROI is imported, it will attempt to import the file named within as the
config setup module.  If successful, that module will be imported as 
``setup`` within this module.  If not, it will have to be manually 
imported through the ``import_setup()`` fucntion.

See the docstrings for individual functions in this module for 
information on how to use them.
"""

import os
import re
import imp
from warnings import warn
from copy import copy, deepcopy
from glob import glob
import scipy.io as scio
import nipype.interfaces.freesurfer as fs
from exceptions import *

__module__ = "configinterface"

# Look for a file indicating the setup module and import that module if found
if os.path.isfile(".roiconfigfile"):
    
    module = open(".roiconfigfile","r").read()
    
    # Get rid of any extraneous whitespace
    module = module.strip()

    # Trim the file extension if it exists
    if module.endswith(".py"):
        module = os.path.splitext(module)[0]

    # Import the module
    try:
        if not module: raise ImportError
        f, name, desc = imp.find_module(module)
        setup = imp.load_module("setup", f, name, desc)
        is_setup = True
        print "\nConfig file `%s` successfully imported" % name
        f.close()
        del f, name, desc
    except ImportError, err:
        print ("\nFound .roiconfigfile, but config module import failed with the message:"
               "\n'%s'"
               "\nYou will need to use the `import_setup()' function." % err)
        is_setup = False
    
    # Clean up
    del module
else:
    is_setup = False

def projectname():
    """Return the project name string.

    Returns
    -------
    str
    """
 
    return setup.projname

def analysis(dictnumber=None):
    """Return the analysis list or an analysis dict.  
    
    Parameter
    ---------
    dictnumber : int, optional
        If included, the function returns the dictionary at this index.
        Otherwise, it returns the full list.  Note that indexing for this
        function is 1-based, unlike normal python sequences.        

    Returns
    -------
    list of dicts or dict

    """

    analyses = setup.analysis
    analyses = [anal for anal in analyses if anal["par"]]


    if isinstance(analyses, dict):
        analyses = [analyses]

    if dictnumber is None:
        return analyses
    else:
        if dictnumber not in range(1, len(analyses) + 1):
            print ("\nAnalysis %d is out of range." 
                   "\nRemember that the analysis list index is 1-based."
                   % dictnumber)
            return
        else:
            return analyses[dictnumber - 1]

def atlases(atlasname=None):
    """Return the atlas specifications.
    
    This function performs a fair amount of checking and addition of obvious but 
    neccessary fields (via calls to private subfunctions), so always get atlas 
    dictionaries from this function, not directly from the setup module.

    Parameters
    ----------
    atlasname : str, optional
        The atlas name, or None to return the full dictionary, which is default.

    Returns
    -------
    dict

    """
    atlasdicts = deepcopy(setup.atlases)

    # Remove null atlas name if people kept cfg base atlases
    if "" in atlasdicts:
       del atlasdicts[""]
    for name, dictionary in atlasdicts.items():
        dictionary["atlasname"] = name
        for k, v in dictionary.items():
            if not k.islower():
                dictionary[k.lower()] = v
                del dictionary[k]
        if "source" not in dictionary:
            raise SetupError("Source missing from %s atlas dictionary" % name)
        dictionary["source"] = dictionary["source"].lower()
        switch = dict(freesurfer = _prep_freesurfer_atlas,
                      fsl        = _prep_fsl_atlas,
                      label      = _prep_label_atlas,
                      sigsurf    = _prep_sigsurf_atlas,
                      mask       = _prep_mask_atlas,
                      sphere     = _prep_sphere_atlas)

        try:
            dictionary = switch[dictionary["source"]](dictionary)
        except KeyError:
            raise SetupError("Source setting '%s' for %s atlas not understood"
                                % (dictionary["source"], name))

    if atlasname is None:
        return atlasdicts
    else:
        return atlasdicts[atlasname]

def _check_fields(atlasfields, atlasdict):
    """Check whether any fields are missing or unexpected in an atlas dictionary."""
    extra = [k for k in atlasdict if k not in atlasfields]
    missing = [f for f in atlasfields if f not in atlasdict]
    atlasname = atlasdict["atlasname"]
    if extra:
        raise SetupError("Unexpected field(s) %s found in %s dictionary"
                            % (extra, atlasname))
    if missing:
        raise SetupError("Field(s) %s missing from %s dictionary"
                            % (missing, atlasname))

def _prep_freesurfer_atlas(atlasdict):
    """Prepare a Freesurfer atlas dictionary."""
    atlasfields = ["atlasname", "source", "fname", "manifold", "regions"]
    _check_fields(atlasfields, atlasdict)

    atlasdict["manifold"] = atlasdict["manifold"].lower()
    if atlasdict["manifold"] not in ["surface", "volume"]:
        raise SetupError("Manifold setting '%s' for %s atlas not understood"
                            % (atlasdict["manifold"], atlasdict["atlasname"]))

    if atlasdict["manifold"] == "surface" and not atlasdict["fname"].endswith(".annot"):
        atlasdict["fname"] = "%s.annot" % atlasdict["fname"]

    if not os.path.isdir(fssubjdir()):
        raise SetupError("Using Freesurfer atlas with illegitimite "
                            "subjects directory path")

    if not isinstance(atlasdict["regions"], list):
        atlasdict["regions"] = [atlasdict["regions"]]

    return atlasdict                                

def _prep_fsl_atlas(atlasdict):
    """Prepare a HarvardOxford atlas dictionary."""
    atlasfields = ["atlasname", "source", "probthresh", "regions"]
    _check_fields(atlasfields, atlasdict)

    atlasdict["manifold"] = "volume"

    if atlasdict["probthresh"] not in [25, 50]:
        raise SetupError("HarvardOxford atlas probthresh setting must "
                         "be either 25 or 50.")

    if not isinstance(atlasdict["regions"], list):
        atlasdict["regions"] = [atlasdict["regions"]]

    return atlasdict                                

def _prep_sigsurf_atlas(atlasdict):
    """Prepare a sigsurf atlas dictionary."""
    atlasfields = ["atlasname", "source", "hemi", "file", "thresh", "minsize"]
    _check_fields(atlasfields, atlasdict)

    atlasdict["manifold"] = "surface"

    if not os.path.isdir(fssubjdir()):
        raise SetupError("Using sigsurf atlas with illegitimite "
                            "Freesurfer Subjects Directory path")

    if not isinstance(atlasdict["thresh"], tuple):
        try:
            atlasdict["fdr"] = tuple((atlasdict["thresh"]))
        except TypeError:
            raise SetupError("The thresh entry for atlas %s is not a tuple."
                             % atlasdict["atlasname"])
    if not (len(atlasdict["thresh"]) == 2 or 
       not isinstance(atlasdict["thresh"][0], str) or
       not isinstance(atlasdict["thresh"][1], float)):
        raise SetupError("The thresh entry for atlas %s must be a two-tuple of the form "
                         "(str, float)" % atlasdict["atlasname"])

    if isinstance(atlasdict["minsize"], str):
        try:
            atlasdict["fdr"] = int(atlasdict["fdr"])
        except ValueError:
            raise SetupError("Minsize setting for %s atlas does not appear "
                             "to be a number" % atlasdict["atlasname"])

    if not os.path.isabs(atlasdict["file"]):
        atlasdict["file"] = os.path.join(setup.basepath, atlasdict["file"])
    if not os.path.isfile(atlasdict["file"]):
        raise SetupError("%s source image %s does not exist" 
                         % (atlasdict["atlasname"], atlasdict["file"]))

    return atlasdict                         

def _prep_label_atlas(atlasdict):
    """Prepare a label atlas dictionary"""
    atlasfields = ["atlasname", "source", "hemi", "sourcelevel", "sourcedir", "sourcefiles"]
    _check_fields(atlasfields, atlasdict)
    
    if not os.path.isdir(fssubjdir()):
        raise SetupError("Using label atlas with illegitimite "
                         "Freesurfer Subjects Directory path")

    if not os.path.isabs(atlasdict["sourcedir"]):
        atlasdict["sourcedir"] = os.path.join(setup.basepath, atlasdict["sourcedir"])

    atlasdict["manifold"] = "surface"
    
    atlasdict["sourcelevel"] = atlasdict["sourcelevel"].lower()
    if not atlasdict["sourcelevel"] in ["subject", "group"]:
        raise SetupError("Sourcelevel for %s atlas must be 'subject' or 'group'" 
                         % atlasdict["atlasname"])

    usedall = False
    subj = subjects()[0]
    if atlasdict["sourcefiles"] == "all" or atlasdict["sourcefiles"] == ["all"]:
        usedall = True
        if atlasdict["sourcelevel"] == "group":
            atlasdict["sourcefiles"] = glob(os.path.join(
                                           atlasdict["sourcedir"], "*.label"))
        else:                                           
            dir = atlasdict["sourcedir"].replace("$subject", subj)
            atlasdict["sourcefiles"] = glob(os.path.join(dir, "*.label"))
        if not atlasdict["sourcefiles"]:
            raise SetupError("Using 'all' for %s atlas found no label images"
                                % atlasdict["atlasname"])

    if atlasdict["sourcelevel"] == "subject":
        nlabels = len(atlasdict["sourcefiles"])
        for subj in subjects():
            ll = glob(os.path.join(atlasdict["sourcedir"].replace("$subject", subj),
                                   "*.label"))
            if usedall and len(ll) != nlabels:
                raise SetupError("Not all subjects for atlas %s have the same "
                                 "number of labels in their sourcedirectory" 
                                 % atlasdict["atlasname"])

    lfiles = atlasdict["sourcefiles"]
    if not isinstance(lfiles, list):
        lfiles = [lfiles]
    lnames = []
    for i, lfile in enumerate(lfiles):
        path, lfile = os.path.split(lfile)
        if lfile.endswith(".label"):
            lfile, ext = os.path.splitext(lfile)
        hemi = atlasdict["hemi"]
        lfiles[i] = os.path.join(atlasdict["sourcedir"], lfile + ".label")
        lnames.append(lfile)
        if atlasdict["sourcelevel"] == "group" and not os.path.isfile(lfiles[i]):
            warn("%s does not exist." % lfiles[i])
    atlasdict["sourcefiles"] = lfiles
    atlasdict["sourcenames"] = lnames
    return atlasdict

def _prep_mask_atlas(atlasdict):
    """Prepare a mask atlas dictionary"""
    atlasfields = ["atlasname", "source", "sourcedir", "sourcefiles"]
    _check_fields(atlasfields, atlasdict)

    if not os.path.isabs(atlasdict["sourcedir"]):
        atlasdict["sourcedir"] = os.path.join(setup.basepath, atlasdict["sourcedir"])

    atlasdict["manifold"] = "volume"
    
    imgregexp = re.compile("[\w\.-]+\.(img)|(nii)|(nii\.gz)|(mgh)|(mgz)$")

    if atlasdict["sourcefiles"] == "all" or atlasdict["sourcefiles"] == ["all"]:
        refiles = []
        gfiles = glob(os.path.join(atlasdict["sourcedir"],"*"))
        for gfile in gfiles:
            if imgregexp.search(gfile):
                refiles.append(gfile)
        if refiles:
            atlasdict["sourcefiles"] = refiles
        else:
            raise SetupError("Using 'all' for %s atlas found no mask images" 
                                % atlasdict["atlasname"])

    lfiles = atlasdict["sourcefiles"]
    if not isinstance(lfiles, list):
        lfiles = [lfiles]

    notimgs = [f for f in lfiles if not imgregexp.search(f)]
    if notimgs:
        spl = lambda fpath: os.path.splitext(os.path.split(fpath)[1])[0]
        repimgs = []
        for img in notimgs:
            imglob = glob(os.path.join(atlasdict["sourcedir"], img + "*"))
            imreg = [f for f in imglob if imgregexp.search(f)]
            if len(imreg) == 1:
                lfiles[lfiles.index(img)] = imreg[0]
                repimgs.append(spl(imreg[0]))
        if not len(notimgs) == len(repimgs):
            raise SetupError(
                "File type of mask(s) %s could not be determined or is not supported"
                 % [f for f in notimgs if f not in repimgs])

    lnames = []
    for i, lfile in enumerate(lfiles):
        path, lfile = os.path.split(lfile)
        lfiles[i] = os.path.join(atlasdict["sourcedir"], lfile)
        lfile, ext = os.path.splitext(lfile)
        lnames.append(lfile)
        if not os.path.isfile(lfiles[i]):
            raise SetupError("%s does not exist." % lfiles[i])
    atlasdict["sourcefiles"] = lfiles
    atlasdict["sourcenames"] = lnames
    return atlasdict

def _prep_sphere_atlas(atlasdict):
    """Prepare the atlas dictionary for a sphere atlas."""
    atlasdict["manifold"] = "volume"

def fssubjdir():
    """Set and return the path to the Freesurfer Subjects directory.

    Returns
    -------
    str
    
    """
    try:
        path = fs.FSInfo.subjectsdir(setup.fssubjectsdir)
    except AttributeError:
        path = fs.FSInfo.subjectsdir(os.getenv("SUBJECTS_DIR"))
        if not path:
            raise Exception("Freesurfer subjects directory could not be determined "
                        "from environment variables.")
    os.environ["SUBJECTS_DIR"] = path
    return path

def first_level_program():
    """Return the program used for first-level analysis.
    
    If the config file does not have a level1program attribute, return "spm"
    for backwards compatability with original config files.

    Returns
    -------
    str : "SPM" or "FSL"
    """
    return firstlevel()["l1prog"]

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
    parname : string, optional
        full paradigm name (if None, returns the full list of paradigms)
    case : string
        "upper" or "lower" -- Def: upper

    Returns
    -------
    list of full paradigm names or string 
    
    """

    pardict = deepcopy(setup.paradigms)

    # Remove any null entries
    try:
        del pardict[""]
    except KeyError:
        pass
    if parname is None:
        return pardict.keys()
    else:
        if case == "lower":
            return pardict[parname].lower()
        elif case == "upper":
            return pardict[parname].upper()
        else:
            raise Exception("Case argument '%s' to "
                            "config.Paradigms not understood." % case) 


def betas(paradigm, retval="names", subject=None):
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
    pardigm : str
        paradigm
    retval : str, optional
        "images", "names", or "sessions"; default: "names"
    subject : str, optional
        subject name


    Returns
    -------
    list or int
    
    """    

    # Get the elements from the setup function 
    hrfcomponents = deepcopy(firstlevel(paradigm, subject)["hrfcomp"])
    betastoextract = deepcopy(firstlevel(paradigm, subject)["beta2ext"])
    names = deepcopy(firstlevel(paradigm, subject)["conditions"])
    sessions = deepcopy(firstlevel(paradigm, subject)["sessions"])

    # Initialize filename and multi-component condition name lists
    condimages = []
    mcompnames = []
    
    # Insert additional component image/names
    for i in range(1,len(names)+1):
        for j in range(hrfcomponents):
            if j+1 in betastoextract:
                # Add the component number to condition names
                mcompnames.append("%s-%02d" % (names[i-1], j+1))
                num = i + ((i-1)*(hrfcomponents-1)) + j
                # Add the image filename to the image list
                condimages.append("beta_%04d.img" % num)

    # Deal with multiple sessions
    if sessions[0] > 1:
        # Figure out how many images are task
        taskbetapersess = hrfcomponents * len(names)
        total = taskbetapersess
        # Add session suffix to names for session 1
        msnames = ["%s-s1" % n for n in names]
        nmcompnames = copy(mcompnames)
        mcompnames = ["%s-s1" % n for n in mcompnames]
        ncondimages = copy(condimages)
        avgnames = ["%s-avg"%n for n in names]
        avgmcnames = ["%s-avg"%n for n in nmcompnames]
        # Loop through addition sessions
        for i in range(1, sessions[0]):
            # Add the nuisance regressions to total
            nuisance = sessions[1][i]
            total += nuisance
            # Add this sessions
            msnames.extend(["%s-s%d"%(n, i+1) for n in names])
            l = 4 
            # Add future flexibility for nii.gz
            if condimages[0].endswith("nii.gz"):
                l = 7
            mcompnames.extend(
                ["%s%02d-s%s"%(n[:-2],int(n[-2:]),i+1) for n in nmcompnames])
            bump = lambda x: x + total 
            for img in ncondimages:
                condimages.append(
                    "%s%02d%s"%(img[:-(l+2)],bump(int(img[-(l+2):-l])),img[-l:]))
            total += taskbetapersess
        mcompnames.extend(avgmcnames)
        msnames.extend(avgnames)
        names = msnames

    # Figure out what the function is being asked about and return it
    if retval == "images":
        return condimages
    elif retval == "sessions":
        return sessions[0]
    elif retval != "names":
        raise Exception("Beta return type \"%s\" not understood" % retval)
    elif hrfcomponents == 1 or betastoextract == [1]:
        return names
    else:
        return mcompnames

def firstlevel(par=None, subject=None):

    # Condition names
    conditions = deepcopy(setup.conditions)[par]

    # HRF Components
    hrfcomp = copy(setup.hrfcomponents)
    if not isinstance(hrfcomp, int):
        raise SetupError("hrfcomponents must be an integer")
    beta2ext = copy(setup.betastoextract)
    if not beta2ext:
        beta2ext = [1]
    elif not isinstance(beta2ext, list):
        beta2ext = [beta2ext]
    if beta2ext == ["all"]:
        beta2ext = range(1, hrfcomp + 1)

    spmfile = os.path.join(pathspec("beta", par, subject, subjects(subject=subject)), "SPM.mat")
    
    # Multiple sessions
    try:
        sessions = deepcopy(setup.sessions)
    except AttributeError:
        sessions = {}
    if par not in sessions:
        n_sessions = 1
    else:
        n_sessions = sessions[par]
    if n_sessions > 1:
        n_regressors = _get_n_regressor_per_sess(spmfile, n_sessions)
        n_regressors = [i * hrfcomp for i in n_regressors]
        nuisance_list = [i - len(conditions) for i in n_regressors]
    else:
        nuisance_list = []
    sessions = (n_sessions, nuisance_list)

    # First level program
    try:
        l1prog = copy(setup.level1program).lower()
        if l1prog not in ["spm"]:
            raise SetupError("First level program %s not understood "
                             "or not supported." % setup.level1program)
    except AttributeError:
        l1prog = "spm"
    
    return dict(hrfcomp=hrfcomp,
                beta2ext=beta2ext,
                conditions=conditions,
                sessions=sessions,
                l1prog=l1prog)
    
def _get_n_regressor_per_sess(matfilepath, n_sessions):
    """Return a list with the number of regressors for each session."""
    spmstruct = scio.loadmat(matfilepath, struct_as_record=False)["SPM"].flat[0]
    version = spmstruct.SPMid.flat[0]
    switch = dict(SPM8 = _parse_spm8_matfile,
                  SPM5 = _parse_spm5_matfile)
    try:
        return switch[version[:4]](spmstruct, n_sessions)
    except KeyError:
        raise NotImplementedError("Parsing %s .mat file" % version[:4])

def _parse_spm8_matfile(spmstruct, n_sessions):
    """Return a list of regressor count per session."""
    names = spmstruct.xX.flat[0].name[0]
    sessionlist = [0 for i in range(n_sessions+1)]
    session = 0
    pattern = names[0][0].replace("Sn(1) ", "")
    for name in names:
        if pattern in name[0]:
            session += 1
        sessionlist[session] += 1
    return sessionlist[1:]

def _parse_spm5_matfile(spm_struct, n_sessions):
    raise NotImplementedError("Parsing SPM5 .mat file (yet)")

def contrasts(type="con-img", format=".nii"):
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
        "sig", "T-map", "con-img", or "names" -- default: con-img
    format : str
        File extension -- default: .nii

    Returns
    -------
    dictionary

    """

    # Get the specified dict from setup
    contrastdict = deepcopy(setup.contrasts)

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

    # Get the list of names
    names = []
    connums = contrasts.values()
    connums.sort()
    for num in connums:
        names.append([k for k, v in contrasts.items() if v == num][0])

    # Figure out what type of image the function is being asked about and return
    if type == "sig":
        return contrasts_sig
    elif type == "T-map":
        return contrasts_tstat
    elif type == "con-img":
        return contrasts_con
    elif type == "names":
        return names
    else:
        raise Exception("Image type '%s' " % type +
                        "not understood: use 'T-map', 'sig', or 'con-img'")


def pathspec(imgtype, paradigm=None, subject=None, group=None, contrast=None):
    """Return the path to directories containing various first-level components.

    Parameters
    -----------
    imgtype : str
        "beta", "meanfunc", "regmat", "timecourse," or "contrast"
    paradigm : str
        full paradigm name
    subject : str 
        subject name
    contrast: str
        contrast name

    Returns
    -------
    str : path to image directory or to image

    """
    basepath = setup.basepath
    betapath = setup.betapath
    regpath = setup.regmatpath
    meanfuncpath = setup.meanfuncpath
    contrastpath = setup.contrastpath
    timecoursepath = setup.timecoursepath
    
    vardict = {"$paradigm" : paradigm,
               "$contrast" : contrast,
               "$subject" : subject,
               "$group" : group}

    imgdict = {"beta": betapath,
               "meanfunc": meanfuncpath,
               "regmat" : regpath,
               "contrast": contrastpath,
               "timecourse": timecoursepath}
   
    if not imgdict[imgtype]:
        return None
    varpath = os.path.join(basepath, imgdict[imgtype])

    for var in vardict:
        if var in varpath:
            if vardict[var]:
                varpath = varpath.replace(var,vardict[var])
            else:
                raise Exception("Wildcard '%s' found in path, but no argument "
                                "given for it." % var)

    if imgtype in ["beta", "contrast"]:
        return varpath
    else:
        imgs = glob(varpath)
        if len(imgs) > 1:
            raise SetupError("Found more than one %s image." % imgtype)
        else:
            try:
                return imgs[0]
            except IndexError:
                raise SetupError("Found no %s images." % imgtype)
                

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
