"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu
"""

import nipype.interfaces.freesurfer as fs
import numpy as N
import fsroidict
import string
import os

def SetUp(setupkey=None):
    
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
       below in this SetUp functino.
       
       All of the mask parameters are optional. If left unset, analysis will 
       be specified as "nomask" and statistics will be extracted from the full
       ROI.  NB: Mask thresh is in -log10(P).

       Format
       ------
       list of dictionaries, with each dictionary in the list specifying
           a separate analysis

       Parameters
       ----------
       par : full name of analysis paradigm
       maskpar : full name of functional mask paradigm 
       maskcon : abbreviated name of functional mask contrast 
       maskthresh : threshold for functional mask (in -log10(P))
       masksign : pos, neg, or abs

       Variable Name
       -------------
       analysis
    """
    
    analysis = [{'par':'novelfaces','maskpar':'social','maskcon':'AFvNF',
                 'maskthresh':0,'masksign':'pos'},
                {'par':'social','maskpar':'novelfaces','maskcon':'AvF',
                 'maskthresh':1.3,'masksign':'pos'},
	            {'par':'social'}]

    #------------------------------<Atlases>-----------------------------------#
    """

    """
       atlases



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
       while shorthand names should be a lower-case two-letter code that will 
       identify the paradigm in your database.

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
       The hrf components variable specifies how many different beta images
       are associated with each task condition. The condition variable links
       paradigm names (as specified above) to a list of short names (ideally
       4 or 5 letters) for the task conditions in that paradigm.

       Format
       ------
       integer
       dictionary where each key is a string and each value is a list of strings

       Variable Name
       -------------
       hrfcomponents
       conditions
    """

    hrfcomponents = 1
    
    conditions = {'novelfaces' :  ['fmzn','fmlr','novl'],
                  'novelobjects': ['fmzn','fmlr','novl'],
                  'surreal' :     ['valid','inval'],
                  'masked':       ['mkfr','mknl','fear','neut'],
                  'social':       ['aface','nface','pscen','escen','nscen']},

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
       run from) to directories containing first-level beta and contrast images.
       You may include $paradigm, $subject, and $contrast wildcards in the path
       strings, which will be replaced appropriately as the program runs. Note
       that you may leave the contrastpath variable as an empty string if you
       will not be using first level masks.

       Format
       ------
       string
       string

       Variable Name
       -------------
       betapath
       contrastpath
    """

    betapath = 'surface/l1output/$paradgim/$subject/model',    

    contrastpath = 'surface/l1output/$paradigm/$subject/contrasts',
    
    #----------------------------<Subjects>------------------------------------#
    """
       Specify the subjects to use in your analyses.  The format is a dictionary
       where keys are the names of your groups and values are lists of your
       subjects, specified by how they are stored in your filesystem (Freesurfer
       ID, etc.). Please maintain this structure even if you have only one group;
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
       
    """
    overwrite = {'task_betas' = True,
                 'registration_matrices' = True,
                 'resampled_volumes' = True,
                 'full_atlas_stats' = True,
                 'label_atlases' = True,
                 'spm_Sig_images' = True,
                 'functional_extracts' = True}


    #==========================================================================#    
    #==========================================================================#    
    
    # Set up the setup dictionary
    setup = {'projname' : projname, 'analysis' : analysis, 'atlases' : atlases,
             'subjdir' : subjdir, 'subjects' : subjects, 'paradigms' : paradigms,
             'contrastpath' : contrastpath, 'betapath' : betapath, 'contrasts' :
             contrasts, 'conditions' : conditions, 'hrfcomponents' : hrfcomponents}
    
    # XXX Change to variable based setup probably obviates the below, but
    # we should find a way to catch the exception from assigning the setup
    # dictionary with a variable that accidentally got deleted above

    # Full list of keys we expect
    fullkeylist = ['projname','analysis','atlases','subjdir','subjects',
                   'contrastpath','betapath','contrasts','conditions',
                   'hrfcomponents','paradigms']
    
    # Get the list of keys in the actual SetUp dictionary
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
            errstr = 'You are missing SetUp key(s) \'%s,\' and have unrecognized key(s) \'%s.\'' \
                     % (missingstr, extrastr)
        elif missing and not extra:
            errstr = 'You are missing SetUp key(s) \'%s.\'' % missingstr
        elif extra and not missing:
            errstr = 'You have unrecognized SetUp key(s) \'%s.\'' % extrastr
        else:
            errstr = 'Something is wrong in your SetUp, but we cannot figure out what.'
        raise Exception(errstr)
    
    # Return SetUp information
    if setupkey is None: return setup
    else: return setup[setupkey]

def ProjectName():
    """This is where you specify your project name, which will be the name of
    the directory in roi/analyses/ where your data will be stored.
 
    Returns: string
    """
 
    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    
   
    return projname


def Groups():
    """Here is where you set whether you want to run statistics for both groups
    or are looking at only one of your groups.  The return value should correspond 
    with the code in the Subjects function below (i.e. it should be either 'all,' 
    'patients,' or 'controls.'

    Returns: string
    """

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    return grouptype


def Analysis():
    """A way to hardcode a list of dictionaries specifying analysis
    parameters (analysis paradigm and mask paradigm, contrast, sign, and thresh).
    You can leave out the masksign parameter and it will be set to 'pos.'
    Note: must be a list of dictionaries, even if specifying only one analysis.
    Leave out the mask parameters if you don't want to mask the ROI.
 
    Returns: list of dictionaries
    """

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    
    return analysis


def SegVols(retval='dict'):
    """A dictionary of the automatic segmentation volumes
    (those that reside in the $SUBJ/mri/ directory with segmentation
    names keyed in the fsroidict.py module).

    Returns: dictionary or string
    """

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    
    space = RoiSpace('orig')
    tempsegvols = {}
    for key in segvols:
        if space[key] == 'surface':
	    for hemi in ['lh','rh']:
	        tempsegvols[key+'.'+hemi] = hemi+'.'+segvols[key]
        else:
	    tempsegvols[key] = segvols[key]
    segvols = tempsegvols

    space = RoiSpace()
    for segkey in segvols.keys():
         if segkey == 'aseg' or segkey == 'label_seg':
             segvols[segkey] = segvols[segkey] + '.mgz'
         elif space[segkey] == 'volume':
             segvols[segkey] = segvols[segkey] + '+aseg.mgz'
         elif space[segkey] == 'surface':
             segvols[segkey] = segvols[segkey]

    if retval == 'dict':   
        return segvols
    else:
        return segvols[retval]


def Regions(seg='aseg'):
    """A group of lists with the numerical ids (found in FreesurferColorLUT.txt)
    for the ROIs we are investigating.  

    Returns: list 
    """

 
    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    for key in regions:
        if isinstance(regions[key],int):
            regions[key] = [regions[key]]
    
    retlist = regions[seg]
    retlist.sort()
    if RoiSpace(seg) == 'surface':
        retlist = [int(i-(N.floor(i/100)*100)) for i in retlist]
    return retlist


def Labels(retval='fulldict'):
    """
    
    NOTE: this docstring is depracated, but it's Saturday and I'm lazy

    A list of names for rois that are the prefix to their .label files 
    (without the .label extension).  For use with labels created  from 
    functional data, or other non recon-all source.  If you do not intend
    To examine any label-based ROIs, this should be an empty list: []
    NOTE: labels should be bilateral (for now).

    Returns: list
    """
    
    #--------------------------------------------------------------------------#
    labels = {}
    """{'lh':
             {1:'lh_dummylabel_1'},
        'rh':
             {1:'rh.FFA'}}"""
    #--------------------------------------------------------------------------#

    if not labels: return None

    labels['adjrh'] = {}
    adj = len(labels['lh'].keys()) + 1
    for id in labels['rh'].keys():
        labels['adjrh'][id*adj] = labels['rh'][id]

    lhids = labels['lh'].keys()
    rhids = labels['adjrh'].keys()
    lhids.sort()
    rhids.sort()
    fullids = lhids + rhids

    fullnames = []
    for id in fullids:
        if id < adj: hemi = 'lh'
	else: hemi = 'adjrh'
        fullnames.append(labels[hemi][id])
       
    if len(labels['lh'].keys()) != len(labels['rh'].keys()):
        raise Exception('Number of label ROIs are not even across hemispheres')

    realnames = []
    for id in labels['lh'].keys():
        if 'dummy' not in labels['lh'][id]:
	    realnames.append(labels['lh'][id])
	else:
	    oppname = labels['rh'][id]
	    fakename = 'lh_' + oppname[3:len(oppname)]
	    realnames.append(fakename)
    for id in labels['rh'].keys():
        if 'dummy' not in labels['rh'][id]:
	    realnames.append(labels['rh'][id])
	else:
	    oppname = labels['lh'][id]
	    fakename = 'rh_' + oppname[3:len(oppname)]
	    realnames.append(fakename)

    if retval == 'fulldict': 
        return labels
    elif retval == 'lh' or retval == 'left':
        return labels['lh']
    elif retval == 'rh' or retval == 'right':
        return labels['adjrh']
    elif retval == 'origrh' or retval == 'origright':
        return labels['rh']
    elif retval == 'fullids':
        return fullids    
    elif retval == 'fullnames':
        return fullnames
    elif retval == 'realnames':
        return realnames
    elif retval == 'adjust':
        return adj
    elif retval == 'space':
        return RoiSpace()['label_seg']
    else:
        raise Exception('Label return value \'%s\' not understood' % retval)


def RoiSpace(retval='dict'):
    """Sets whether the ROIs will be analyzed in the volume or on the surface.
    Note: aseg ROIs must be analyzed in the volume.  Label ROIs should be
    analyzed in the space in which they were created.

    Returns: dict
    """
    
    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    if retval == 'orig':
        return roispacedict

    temproispacedict = {}
    for key in roispacedict:
        if roispacedict[key] == 'surface':
	    temproispacedict[key+'.lh'] = 'surface'
	    temproispacedict[key+'.rh'] = 'surface'
        else:
	    temproispacedict[key] = 'volume'

    roispacedict = temproispacedict

    if retval == 'dict':
        return roispacedict
    else:
        return roispacedict[retval]


def SubjDir():
    """Sets the Freesurfer subject directory.

    Returns: string
    """    

    #--------------------------------------------------------------------------#
    {'subjdir' : fs.FSInfo.subjectsdir(os.path.abspath('data'))}
    #--------------------------------------------------------------------------# 
    
    return subjdir    


def Paradigms(parname='all',case='upper'):
    """Contains two items: a list of paradigms used in this analysis (paradigms 
    should have the same scan parameters if they will be used in ROI analysis),
    and a dictionary to link paradigm names to two-letter shortcuts for datafiles.
    If called with an empty scope, returns the list; if called with a paradigm name,
    it will return the shortcut.

    Second argument sets the case of the abbreviation, if intended to be returned.
    By default returns upper case, which is convention for analysis paradigm.  Include
    'lower' to return lowercase, which is convention for mask paradigm.

    Returns: list or string
    """

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#


    if parname == 'all':
        return parlist
    else:
        if case == 'lower':
            return pardict[parname]
        elif case == 'upper':
            return string.swapcase(pardict[parname])
        else:
            raise exception('Case argument \'%s\' to '+\
	                        'config.Paradigms not understood.' % case)


def Betas(par,retval='names'):
    """Contains  lists defining the task condition names.  Can return those
    names or the file names of their associated beta images.  First argument 
    should be the paradig you want the betas for, second arugment should be 
    either 'images' or 'names' ('names' is default) depending on what you want 
    to return.  Names should be shortened to fit in the stats database, if possible.
    Also suggested is that all beta names for one paradigm have same length.

    Returns: list
    """    

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#


    condimages = []
    mcompnames = []

    for i in range(1,len(condnames)+1):
        for j in range(0,components):
            pad = None
            if j < 10:
	        pad = '0'
            mcompnames.append(condnames[i-1] + '-' + pad + str(j+1))
	    num = i + ((i-1)*(components-1)) + j
            if num < 10:
                condimages.append('beta_000%s.img' %str(num))
            elif num < 100:
                condimages.append('beta_00%s.img' %str(num))
            elif num < 1000:
                condimages.append('beta_0%s.img' %str(num))
            else:
                condimages.append('beta_%s.img' %str(num))

    if retval == 'images':
        return condimages
    elif retval == 'names' and components == 1:
        return condnames
    elif retval == 'names' and components > 1:
        return mcompnames
    else:
        raise Exception('Beta return type \'%s\' not understood' % retval)


def Contrasts(par,type='P-map',format='.nii'):
    """A set of dictionaries that define the contrast image number
    for each paradigm in FsFast format.  Arguments: par = paradigm,
    type = 'T-map' or 'con-img' (default).  

    Returns: dictionary
    """



    contrasts_sig = {}
    contrasts_tstat = {}
    contrasts_con = {}
    for con in contrasts:
        if contrasts[con] < 10:
           pad = '0'
        else:
            pad = ''
	contrasts_sig[con] = 'spmP_00' + pad + str(contrasts[con]) + format
        contrasts_tstat[con] = 'spmT_00' + pad + str(contrasts[con]) + format 
        contrasts_con[con] = 'con_00' + pad + str(contrasts[con]) + format

    if type == 'P-map':
        return contrasts_sig
    elif type == 'T-map':
        return contrasts_sig
    elif type == 'con-img':
        return contrasts_con
    else:
        raise Exception('Image type \'%s\' \
	                not found: use \'T-map\', \'P-map\', or \'con-img\'' % type)


def Subjects(group='all',subject=None):
    """Group lists.  By default returns both patients and controls, but 
    can specify by passing either 'patients' or 'controls'
    
    Returns: list or dict
    """

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    for grp in subjects.keys():
        subjects[grp].sort()
	
    if subject:
        for grp in subjects.keys():
           if subject in subjects[grp]:
              return grp

    if group == 'all':
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

def PathSpec(imgtype, paradigm=None, subject=None, contrast=None):
    """Return a path to a beta or contrast image directory

    This function allows the ROI procesing pypeline to be free of any
    specific first-level directory structure. A variable path is specified
    in the SetUp function where the directory for paradigm, subject, and
    contrast is is signified by $variable for beta and contrast files
    separately.  This function expects those strings to be keyed by 'betapath'
    and 'contrastpath', respectively.

    In theory, this function should work for both SPM and FsFast first-level
    structures.  At the time of the writing of this docstring, however, the
    ROI pypeline does not yet handle the FsFast first level beta images
    themselves properly.

    Parameters
    -----------
    imgtype : beta or contrast
    paradigm : paradigm name, however it is specified in the actual path
    subject : subject name, however it is specified in the actual path
    contrast: : contrast name, however it is specified in the actual path

    Returns
    -------
    string of path to image directory

    """
    betapath = SetUp('betapath')
    contrastpath = SetUp('contrastpath')
    
    vardict = {'$paradigm' : paradigm,
               '$contrast' : contrast,
               '$subject' : subject}

    imgdict = {'beta' : betapath,
               'contrast' : contrastpath}
    
    varpath = imgdict[imgtype]

    for var in vardict.keys():
        if var in varpath:
            varpath = varpath.replace(var,vardict[var])

    return varpath
