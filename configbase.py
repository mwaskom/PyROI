# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu
"""


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
       - manifold : volume or surface
       Volumes
       - space : native or MNI
       Freesurfer or Talairach Daemon source
       - fname : file name of atlas
       - regions : list of numerical ids to regions under investigation
       Label Source
       - hemi : hemisphere
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
                   'manifold': 'volume',
                   'regions': [17,18,52,53]},
               'aparc': 
                   {'source': 'freesurfer',
                    'fname': 'aparc.annot',
                    'manifold': ' surface',
                    'regions': [20,21,22,23]},
               'social_bg':
                   {'source': 'label',
                    'manifold': 'surface',
                    'hemi': 'rh',
                    'sourcedir': 'data/Oliver_Label_Files',
                    'sourcefiles': ['BG.STS',
                                    'BG.supoccipital.STS',
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
       Specify the absolute path to your main directory and relative paths from
       that directory to those containing timecourses, mean functionals, first-
       level betas, and contrast images.  You may include $paradigm, $subject,
       and $contrast wildcards in the path strings, which will be replaced 
       appropriately as the program runs. 

       NOTE: For now, PyROI just looks for a single .nii image in the terminal
       directory of the meanfunc path.  This is the standard setup for the out-
       put of NiPype first-level workflows, but if you are working with a diff-
       erent first-level analysis, you may need to create this path/file yourself.

       Format
       ------
       string
       string
       string
       string
       string

       Variable Name
       -------------
       basepath
       timecoursepath
       meanfuncpath
       betapath
       contrastpath
    """

    basepath = '/g2/gablab/sad/PY_STUDY_DIR/Block'

    timecoursepath = 'surface/l1output/$paradigm/$subject/timecourse'

    meanfuncpath = 'surface/l1output/$paradigm/$subject/realign'

    betapath = 'surface/l1output/$paradigm/$subject/model'    
    
    contrastpath = 'surface/l1output/$paradigm/$subject/contrasts'

    #----------------------------<Subjects>------------------------------------#
    """
       Specify the subjects to use in your analyses.  The format is a dictionary
       where keys are the names of your groups and values are lists of your
       subjects, specified by how they are stored in your filesystem (Freesurfer
       ID, etc.). Maintain this format even if you have only one group; simply 
       use the name of your experiment, or other, as the single key to the dict-
       ionary in that case.

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
    setup = \
    {'projname': projname, 'analysis': analysis, 'atlases': atlases,
     'subjdir': subjdir, 'subjects': subjects, 'paradigms': paradigms,
     'contrastpath': contrastpath, 'betapath': betapath, 'contrasts':
     contrasts, 'conditions': conditions, 'hrfcomponents': hrfcomponents,
     'overwrite': overwrite, 'betastoextract': betastoextract, 'basepath':
     basepath, 'meanfuncpath': meanfuncpath, 'timecoursepath': timecoursepath}
    
    # Return setup information
    if setupkey is None: return setup
    else: return setup[setupkey]

