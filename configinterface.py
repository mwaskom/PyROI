# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu
"""

import nipype.interfaces.freesurfer as fs
import pyroilut as lut
import numpy as N
import string
import os

def setup(setupkey=None):
    
    #----------------------------<Project Name>--------------------------------#
    """
       Specify the name your analysis will be associated with. All analysis
       results will be printed to roi/analyses/$projname.

       Format
       ------
       string

       Variable Name
       -------------
       projname
    """

    projname = 'development'

    #-------------------------<Analysis Parameters>----------------------------#
    """
       Specify the parameters for an arbitrary number of analyses. Task-related
       betas from the main analysis paradigm will be extraced from each ROI. 
       You may also specify a functional mask defined by a first-level paradigm
       which will be applied before extraction. The mask will restrict extraction
       to those voxels/vertices that are active in the mask contrast above the 
       mask threshold, with the direction specified by mask sign. If analysis
       is being done in the volume, mask paradigms must be in the same space 
       as the analysis paradigm.  This should not matter on the surface.

       See the "parameters" section below for the key names to use.  Values
       should be set according to the paradigm and contrast names you specify
       below in this setup functino.
       
       All of the mask parameters are optional. If left unset, analysis will 
       be specified as "nomask" and statistics will be extracted from the full
       ROI.  NB: Mask thresh is in -log10(P).

       Format
       ------
       list of dictionaries, with each dictionary in the list specifying
           a separate analysis

       Parameters
       ----------
       par : full name of main analysis paradigm
       extract: betas, contrasts, or timecourse
       maskpar : full name of functional mask paradigm 
       maskcon : abbreviated name of functional mask contrast 
       maskthresh : threshold for functional mask (in -log10(P))
       masksign : pos, neg, or abs

       Variable Name
       -------------
       analysis
    """
    
    analysis = [{'par': 'social', 'extract': 'betas'},
                {'par': 'novelfaces', 'extract': 'betas', 'maskpar': 'social',
                 'maskcon': 'AFvNF', 'maskthresh': 0,'masksign': 'pos'},
                {'par': 'social', 'extract': 'betas', 'maskpar': 'novelfaces', 
                 'maskcon': 'AvF', 'maskthresh': 1.3, 'masksign': 'pos'}]

    #------------------------------<Atlases>-----------------------------------#
    """
       Specify the atlases that will define your ROIs, and which ROIs from
       those atlases you will investigate. The format is of a dictionary
       where each key is a shorthand name for an atlas and the value is
       a dictionary of attributes for that atlas.

       For all atlases, you must specify the source and space. 
       
       Source can be 'freesurfer', for freesurfer segmentations/parcellations
       in native space; 'talairach', for a modified version of the talairach
       daemon used by the WFU Pick Atlas that is provided with this software;
       'mask', for an atlas composed of an arbitrary number of non-overlap-
       ping binary image files in the same space, or 'label', for an atlas
       composed of an arbitrary number of non-overlapping Freesurfer labels
       in fsaverage space. Space is either 'volume' or 'surface'; if the atlas
       is surface-based, you should also provide the hemisphere in the atlas
       dictionary with the 'hemi' key.

       If source is 'freesurfer', just provide the filename (this requires your
       Freesurfer subject directory to be set below). If source is 'talairach',
       give the path to the image file. For both of these sources, also specify
       a list of the numerical IDs to investigate from that atlas. For label or
       mask sources, you will need to provide two pieces of information: the 
       path to the directory where your masks/labels are stored and a list of
       the names for the masks/labels in that atlas. ROI names will be derived
       from these file names.

       Format
       ------
       dictionary with internal dictionaries for each atlas

       Parameters
       ----------
       All
       - source : freesurfer, talairach, label, mask
       - space : volume or surface
       Surfaces
       - hemi : hemisphere
       Freesurfer or Talairach Daemon source
       - fname : file name of atlas
       - regions : list of numerical ids to regions under investigation
       Label or Mask source
       - sourcedir : directory with source images
       - sourcefiles : list label or mask image file names 

       Variable Name
       -------------
       atlases
    """
    
    atlases = {'aseg': 
                   {'source': 'freesurfer',
                   'fname': 'aseg.mgz',
                   'space': 'volume',
                   'regions': [17,18,52,53]},
               'rhdesikan': 
                   {'source': 'freesurfer',
                    'fname': 'rh.aparc.annot',
                    'space': ' surface',
                    'hemi': 'rh',
                    'regions': [20,21,22,23]},
               'social_bg':
                   {'source': 'label',
                    'space': 'surface',
                    'hemi': 'rh',
                    'sourcedir': 'data/Oliver_Label_Files',
                    'sourcefiles': ['BG.STS',
                                    'BG.supoccipital.STS'
                                    'BG.supparietal.STS']}}
       

    #--------------------<Freesurfer Subject Directory>------------------------#
    """
       Specify the path to your Freesurfer Subjects directory. If you are not
       using any Freesurfer-based atlases, just specify an arbitry path.  
       Do not delete the variable, as it will cause the program to crash.

       Format
       ------
       string

       Variable Name
       -------------
       subjdir
    """
    
    subjdir = '/g2/gablab/sad/PY_STUDY_DIR/Block/data'

    #-----------------------------<Paradigms>----------------------------------#
    """
       Specify the full and shorthand names for the paradigms involved in you
       analyses. The format is a dictionary where keys are full names and
       values are short names. Full names should correspond to the name 
       associated with the paradigm in your file directory (case-sensitive),
       while shorthand names should be a two-letter code that will identify 
       the paradigm in your database.

       Format
       ------
       dictionary

       Variable Name
       -------------
       paradigms
    """
    
    paradigms = {'novelfaces':   'nf',
                 'novelobjects': 'no',
                 'social':       'sc',
                 'surreal':      'sr',
                 'masked':       'mk'}

    #--------------------------<First Level Design>----------------------------#
    """
       Specify the task-related elements of your first-level design matrix.
       The hrfcomponents variable specifies how many different beta images
       are associated with each task condition. The betastoextract variable 
       specifies which regressors to extract if multiple regressors are
       associated with each task condition.  It can be 'all' or a list of 
       integers corresponding to the components. The conditions variable links
       paradigm names (as specified above) to a list of short names (ideally
       4 or 5 letters) for the task conditions in that paradigm. The order of
       condition names in these lists should correspond to the order in your
       beta images.

       Note that although the hrfcomponents variable is added for forward
       compatability, the ROI pypeline has not been tested on any data
       with multiple HRF comopnents for each task condition.

       Format
       ------
       integer
       'all' or list of integers
       dictionary where each key is a string and each value is a list of strings

       Variable Name
       -------------
       hrfcomponents
       betastoextract
       conditions
    """

    hrfcomponents = 1

    betastoextract = 'all'
    
    conditions = {'novelfaces':   ['fmzn','fmlr','novl'],
                  'novelobjects': ['fmzn','fmlr','novl'],
                  'surreal':      ['valid','inval'],
                  'masked':       ['mkfr','mknl','fear','neut'],
                  'social':       ['aface','nface','pscen','escen','nscen']}

    #------------------------------<Contrasts>---------------------------------#
    """
       Specify the contrasts for each paradigm involved in your analysis. The 
       format is a dictionary where the keys are full paradigm names (as they
       are specified above) and values are dictionaries mapping an abbreviation
       for the contrast (typically in FsFast style) to the number of con image
       for that contrast.

       Note that if you are not going to be using any functional masks, you can
       leave this as an empty dictionary.

       Format
       ------
       dictionary where each key is a string and each value is a dictionary
          inner dictionary: each key is a string and each value is an integer

       Variable Name
       -------------
       contrasts
    """

    contrasts = {'novelfaces' :  {'NFvFF':     1,
                                  'AvF':       2},
                 'novelobjects': {'NOvFO':     1,
                                  'AvF':       2},
                 'surreal':      {'IvV':       1,
                                  'AvF':       2},
                 'social':       {'AFvNF':     1,
                                  'ESvNS':     2,
                                  'NFvNS':     3,
                                  'AFvES':     4,
                                  'AFESvNFNS': 5,
                                  'NFAFvNSES': 6,
                                  'AFNSvNFES': 7,
                                  'AvF':       8,
                                  'AFvNS':     9,
                                  'PSvNS':    10},
                 'masked':       {'FvN':       1,
                                  'MFvMN':     2,
                                  'AvF':       3}}

    #------------------------<First Level Datapaths>---------------------------#
    """
       Specify the paths (relative to the directory where the analysis will be
       run from) to directories containing timecourses, mean functionals, first-
       level betas, and contrast images.  You may include $paradigm, $subject,
       and $contrast wildcards in the path strings, which will be replaced 
       appropriately as the program runs. Note that you may leave the 
       contrastpath variable as an empty string if you will not be using first-
       level masks or extracting contrast effect sizes.

       NOTE: For now, PyROI just looks for a single .nii image in the terminal
       directory of the meanfunc path.  This is the standard setup for the out-
       put of NiPype first-level workflows, but if you are working with a diff-
       erent first-level analysis, you may need to create this path/file yourself.

       Format
       ------
       dictionary or string
       string
       string
       string

       Variable Name
       -------------
       meanfuncpath
       betapath
       contrastpath
    """

    timecourse = 'surface/l1output/$paradigm/$subject/timecourse'

    meanfuncpath = 'surface/l1output/$paradigm/$subject/realign'

    betapath = 'surface/l1output/$paradigm/$subject/model'    
    
    contrastpath = 'surface/l1output/$paradigm/$subject/contrasts'

    #----------------------------<Subjects>------------------------------------#
    """
       Specify the subjects to use in your analyses.  The format is a dictionary
       where keys are the names of your groups and values are lists of your
       subjects, specified by how they are stored in your filesystem (Freesurfer
       ID, etc.). Be sure to maintain this structure even if you have only one group;
       simply use the name of your experiment, or other, as the single key to the
       dictionary in that case.

       Format
       ------
       dictionary with strings as each key and a list of strings as each value

       Variable Name
       -------------
       subjects
    """    

    subjects  =  {'control': 

                     ['SAD_017','SAD_018','SAD_019','SAD_020','SAD_021',
                      'SAD_022','SAD_023','SAD_024','SAD_025','SAD_027', 
                      'SAD_028','SAD_029','SAD_030','SAD_031','SAD_032',         
                      'SAD_033','SAD_034','SAD_035','SAD_036','SAD_037',
                      'SAD_038','SAD_039','SAD_040','SAD_041','SAD_043',
                      'SAD_044','SAD_045','SAD_046','SAD_047','SAD_048',
                      'SAD_049','SAD_050'],

                  'patient':

                     ['SAD_P03','SAD_P04','SAD_P05','SAD_P06','SAD_P07',
                      'SAD_P08','SAD_P09','SAD_P10','SAD_P11','SAD_P12',
                      'SAD_P13','SAD_P14','SAD_P15','SAD_P16','SAD_P17',
                      'SAD_P18','SAD_P19','SAD_P20','SAD_P21','SAD_P22',
                      'SAD_P23','SAD_P24','SAD_P25','SAD_P26','SAD_P27',
                      'SAD_P28','SAD_P29','SAD_P30','SAD_P31','SAD_P32',
	                  'SAD_P33','SAD_P34','SAD_P35','SAD_P36','SAD_P37',
	                  'SAD_P38','SAD_P39','SAD_P40','SAD_P41']}

    #----------------------------<Overwrite>-----------------------------------#
    """
       Specify which files the program should overwrite as it is run multiple
       times.  This only pertains to files that are created by PyROI; it will
       never overwrite externally created data.  The format is of a dictionary 
       where keys are descriptions of classes of files produced by the pypeline
       and values are booleans (True or False), where True means that the file 
       will be overwritten.  
       
       NB: in Python, True and False are case-sensitive when serving as booleans.

       Format
       ------
       a dictionary where each key is a string and each value is a boolean
       
       Variable Name
       -------------
       overwrite
    """
    overwrite = {'task_betas' : True,
                 'registration' : True,
                 'resampled_volumes' : True,
                 'freesurfer_annots' : True,
                 'full_atlas_stats' : True,
                 'label_atlases' : True,
                 'spm_sig_images' : True,
                 'functional_extracts' : True}


    #==========================================================================#    
    #==========================================================================#    
    
    # Set up the setup dictionary
    setup = {'projname' : projname, 'analysis' : analysis, 'atlases' : atlases,
             'subjdir' : subjdir, 'subjects' : subjects, 'paradigms' : paradigms,
             'contrastpath' : contrastpath, 'betapath' : betapath, 'contrasts' :
             contrasts, 'conditions' : conditions, 'hrfcomponents' : hrfcomponents,
             'overwrite' : overwrite, 'betastoextract' : betastoextract,
             'meanfuncpath' : meanfuncpath, 'timecourse': timecourse}
    
    # XXX Change to variable based setup probably obviates the below, but
    # we should find a way to catch the exception from assigning the setup
    # dictionary with a variable that accidentally got deleted above
    """
    # Full list of keys we expect
    fullkeylist = ['projname','analysis','atlases','subjdir','subjects',
                   'contrastpath','betapath','contrasts','conditions',
                   'hrfcomponents','paradigms','overwrite']
    
    # Get the list of keys in the actual setup dictionary
    actkeylist = setup.keys()
    fullkeylist.sort()
    actkeylist.sort()
    
    # Figure out if anything is missing or unexpected
    missing = [i for i in fullkeylist if i not in actkeylist]
    extra = [i for i in actkeylist if i not in fullkeylist]

    # Figure out how to report what is missing or unexpected
    for i, key in enumerate(missing):
        if i == 0:
            missingstr = '%s' % key
        elif i == len(missing):
            missingstr = '%s, and %s' % (missingstr, key)
        else:
            missingstr = '%s, %s' % (missingstr, key)
    for i, key in enumerate(extra):
        if i == 0:
            extrastr = '%s' % key
        elif i == len(extra):
            extrastr = '%s, and %s' % (extrastr, key)
        else:
            extrastr = '%s, %s' % (extrastr, key)
    
    # If something is missing or unexpected, error out with some information about it
    if fullkeylist != actkeylist:
        if missing and extra:
            errstr = 'You are missing setup key(s) \'%s,\' and have '+\
                     'unrecognized key(s) \'%s.\'' % (missingstr, extrastr)
        elif missing and not extra:
            errstr = 'You are missing setup key(s) \'%s.\'' % missingstr
        elif extra and not missing:
            errstr = 'You have unrecognized setup key(s) \'%s.\'' % extrastr
        else:
            errstr = 'Something is wrong in setup, but we cannot figure out what.'
        raise Exception(errstr)
    """ 
    # Return setup information
    if setupkey is None: return setup
    else: return setup[setupkey]

def projectname():
    """This function will return the project name string

    Parameters
    ----------
    none

    Returns
    -------
    string
    """
 
    projname = setup('projname')

    return projname


def analysis():
    """This function will return the analysis list.  If the variable type
    of analysis is a dictionary, it wraps it in a list.
   
    Parameters
    ----------
    none

    Returns
    -------
    list of dictionaries

    """

    analysis = setup('analysis')

    if isinstance(analysis, dict):
        analysis = [analysis]

    return analysis


def atlases(atlas=None):
    """This function deals with the ROI atlas defintions. If the scope is 
    empty when called, it will return the full atlas dictionary, where each
    entry specifies an atlas. If called with an atlas key as the argument,
    it will return the attribute dictionary for that atlas.  

    Eventually, the function will do a fair amount of checking/modification
    to catch a lot of typcial user errors. Please report all of the errors 
    you run into to mwaskom@mit.edu to aid this process.

    Parameters
    ----------
    atlas : either atlas key name or None

    Returns
    -------
    dictionary

    """
    
    atlases = setup('atlases')
    
    for key in atlases.keys():
        atlases[key]['atlasname'] = key

    if atlas is None:
        return atlases
    else:
        return atlases[atlas]


def fssubjdir():
    """This function returns the path to the Freesurfer Subjects directory.

    Parameters
    ----------
    None

    Returns
    -------
    string
    
    """
    
    dirpath = setup('subjdir')

    subjdir = fs.FSInfo.subjectsdir(os.path.abspath(dirpath))

    return subjdir


def paradigms(parname=None, case='upper'):
    """This function has two uses. If called with an empty scope, it will
    return a list of the paradigms inolved in the project. If called with 
    the full name of a paradigm as the first argument, it will return the 
    two-letter code for that paradigm. You may specify whether the paradigm
    code should be returned in upper or lower case using the second argument
    (upper case is default).

    Parameters
    ----------
    parname : full paradigm name (if None, returns the full list of paradigms)
    case : upper or lower -- Def: upper

    Returns
    -------
    list of full paradigm names or string 
    
    """

    pardict = setup('paradigms')

 
    if parname is None:
        return pardict.keys()
    else:
        if case == 'lower':
            return pardict[parname].lower()
        elif case == 'upper':
            return pardict[parname].upper()
        else:
            raise Exception('Case argument \'%s\' to ' % case +\
	                        'config.Paradigms not understood.') 


def betas(par=None, retval=None):
    """This function deals with both condition and file names for the 
    first-level betas.  It takes the name of a paradigm and the type 
    of list to return as parameters.  If asked for "names," it will
    return the list of condition names.  If asked for "images," it 
    will return the list of image file names associated with task
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
    par : paradigm
    retval : images or names

    Returns :
    list of condition names or image files names
    
    """    

    # Get the elements from the setup function 
    hrfcomponents = setup('hrfcomponents')
    betastoextract = setup('betastoextract')
    conditions = setup('conditions')

    # Return the conditions dictionary and hrfcomponents if scope is empty
    if par is None:
        return conditions, hrfcomponents

    # Check that the paradigm is in the conditions dictionary
    # Exit with a more informative error if it is not
    try:
        dump = conditions[par]
    except KeyError:
        raise Exception('Paradigm \'%s\' not found in conditions dictionary'\
                        % par)

    # Wrap betastoextract in a list if it's just an int
    if isinstance(betastoextract, int):
        betastoextract = [betastoextract]

    # Initialize filename and multi-component condition name lists
    condimages = []
    mcompnames = []

    # If extracting all beta components, make that list
    if betastoextract == 'all' or betastoextract == ['all']:
        betastoextract = range(1, hrfcomponents + 1)

    # Insert additional component image/names
    for i in range(1,len(conditions[par])+1):
        for j in range(0,hrfcomponents):
            if j+1 in betastoextract:
                pad = None
                if j < 10:
                    pad = '0'
                # Add the component number to condition names    
                mcompnames.append(conditions[par][i-1] + '-' + pad + str(j+1))
                num = i + ((i-1)*(hrfcomponents-1)) + j
                # Add the image filename to the image list
                if num < 10:
                    condimages.append('beta_000%s.img' %str(num))
                elif num < 100:
                    condimages.append('beta_00%s.img' %str(num))
                elif num < 1000:
                    condimages.append('beta_0%s.img' %str(num))
                else:
                    condimages.append('beta_%s.img' %str(num))
    
    
    # Figure out what the function is being asked about and return it
    if retval == 'images':
        return condimages
    elif retval == 'names' and (hrfcomponents == 1 or betastoextract == [1]):
        return conditions[par]
    elif retval == 'names' and hrfcomponents > 1:
        return mcompnames
    else:
        raise Exception('Beta return type \'%s\' not understood' % retval)


def contrasts(par=None, type='con-img', format='.nii'):
    """This function controls the contrast images used in the analysis.
    It takes the paradigm, image type, and image format as parameters 
    and returns a dictionary mapping contrast shorthand names to image
    file names.

    Parameters
    ----------
    par : paradigm
    type : sig, T-map, or con-img -- def: con-img
    format : file extension -- def: .nii

    Returns
    -------
    dictionary

    """

    # Get the specified dict from setup
    contrastdict = setup('contrasts')

    # Return the full dict if called with an empty scope
    if par is None:
        return contrastdict

    # Get the dictionary for the paradigm we're looking at
    contrasts = contrastdict[par]

    # Initialize the dictionaries for file names
    contrasts_sig = {}
    contrasts_tstat = {}
    contrasts_con = {}

    # Iterate through the contrasts and populate the filename dictionaries
    for con in contrasts:
        if contrasts[con] < 10:
           pad = '0'
        else:
            pad = ''
        contrasts_sig[con] = 'spmSig_00%s%d%s' % (pad, contrasts[con], format)
        contrasts_tstat[con] = 'spmT_00%s%d%s' % (pad, contrasts[con], format)
        contrasts_con[con] = 'con_00%s%d%s' % (pad, contrasts[con], format)

    # Figure out what type of image the function is being asked about and return
    if type == 'sig':
        return contrasts_sig
    elif type == 'T-map':
        return contrasts_tstat
    elif type == 'con-img':
        return contrasts_con
    else:
        raise Exception('Image type \'%s\' ' %type +\
	                'not understood: use \'T-map\', \'sig\', or \'con-img\'')


def pathspec(imgtype, paradigm=None, subject=None, contrast=None):
    """Return a path to a beta or contrast image directory

    This function allows the ROI procesing pypeline to be free of any
    specific first-level directory structure. A variable path is specified
    in the setup function where the directory for paradigm, subject, and
    contrast is is signified by $variable for beta and contrast files
    separately.  This function expects those strings to be keyed by 'betapath'
    and 'contrastpath', respectively.

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
    betapath = setup('betapath')
    meanfuncpath = setup('meanfuncpath')
    contrastpath = setup('contrastpath')
    timecoursepath = setup('timecourse')
    
    vardict = {'$paradigm' : paradigm,
               '$contrast' : contrast,
               '$subject' : subject}

    imgdict = {'betas': betapath,
               'meanfunc': meanfuncpath,
               'contrasts': contrastpath,
               'timecourse': timecoursepath}
    
    varpath = imgdict[imgtype]

    for var in vardict.keys():
        if var in varpath:
            varpath = varpath.replace(var,vardict[var])

    return varpath

def subjects(group = None, subject = None):
    """This function controls the subjects and groups involved in the 
    analysis.  It takes either a group or a subject as a parameter.
    If called with an empty scope, it returns a list of all subjects.
    If called with the name of a group, it returns a list of the subjects
    in that group. If called with group = 'groups', it returns a list of 
    the group names.  If called with the name of a subject, it will return
    the name of the group that subject is a member of.

    Parameters
    ----------
    group : group name or 'groups'
    subject : subject name

    Returns
    -------
    list

    """

    subjects = setup('subjects')

    for grp in subjects.keys():
        subjects[grp].sort()
	
    if subject:
        for grp in subjects.keys():
           if subject in subjects[grp]:
              return grp

    if group is None:
        all = []
        for grp in subjects.keys():
	        all = all + subjects[grp]
        return all
    elif group in subjects.keys():
        return subjects[group]
    elif group == 'groups':
        return subjects.keys()
    else:
        raise Exception('Group \'%s\' not found.' % group)


def overwrite(filetype=None):
    """Query whether a given filetype should be overwritten if it is found
    to exist at runtime.

    If this filetype is None, the function will return the dictionary

    Parameters
    ----------
    string specifying file type

    Returns
    -------
    boolean where True means "overwrite"
    
    """

    overwrite = setup('overwrite')

    if filetype is None:
        return overwrite
    else:
        return overwrite[filetype]
