# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4

"""
This is a skeleton config file for the PyROI package.

"""


    
#----------------------------<Project Name>--------------------------------#
"""
Specify the name your analysis will be associated with. All analysis
results will be printed to roi/analyses/$projname.  In addition, all
user-defined atlases (mask, label, and sphere atlases) will be
associated with this name.

Format
------
string

Variable Name
-------------
``projname``

"""

projname = ""

#-------------------------<Analysis Parameters>----------------------------#
"""
Specify the parameters for an arbitrary number of analyses. Task-related
betas from the main analysis paradigm will be extraced from each ROI. 
You may also specify a functional mask defined by a first-level paradigm
which will be applied before extraction. The mask will restrict extraction
to those voxels/vertices that are active in the mask contrast above the 
mask threshold, with the direction specified by mask sign. If analysis is
being done in the volume, mask paradigms must be in the same space as the
analysis paradigm.  

See the "Entries" section below for the key names to use and their meanings.
Values should be set according to the paradigm and contrast names you specify
in the appropriate sections below in this config file.

All of the mask parameters are optional. If left unset, analysis will 
be specified as "nomask" and statistics will be extracted from the full
ROI.  NB: Mask thresh is in -log10(P).

Format: list of dictionaries, with each dictionary in the
list specifying a separate analysis

Entries
-------
- par : full name of main analysis paradigm

- extract: betas, contrasts, or timecourse

- maskpar : full name of functional mask paradigm 

- maskcon : abbreviated name of functional mask contrast 

- maskthresh : threshold for functional mask in -log10(P)

- masksign : pos, neg, or abs

Variable Name
-------------
``analysis``

"""

analysis = [{"par": "", "extract": ""},
            {"par": "", "extract": "", "maskpar": "",
             "maskcon": "", "maskthresh": 0,"masksign": ""}]

#------------------------------<Atlases>-----------------------------------#
"""
Specify the atlases that will define your ROIs, and which ROIs from
those atlases you will investigate. The format is of a dictionary
where each key is a shorthand name for an atlas and the value is
a dictionary of attributes for that atlas.

Source can be "freesurfer", for freesurfer segmentations/parcellations
in native space; "fsl", for the Harvard Oxford probabilistic atlas from
FSL, "mask", for an atlas composed of an arbitrary number of non 
overlapping binary image files in the same space,"label", for an atlas
composed of an arbitrary number of non-overlapping Freesurfer surface
labels in fsaverage space, or "sphere", for an atlas composed of an
arbitrary number of spheres. 

Entries
-------
- source: ``freesurfer``, ``fsl``, ``mask``, ``label``, or ``sphere``
- regions: a list of integer ids for the regions you want to extract from
- manifold: ``volume`` or ``surface``
- hemi: ``lh`` or ``rh``
- coordsys: ``mni``, ``tal``, or ``vox``
- radius: an integer -- in mm if coordsys is mni or tal, or in vox
- centers: a dictionary mapping region name to a tuple of center coordinates
- sourcedir: the path to the directory where the source images are located
- sourcefiles: a list of the source file names, or ``all`` to use all image
or label files in the source directory



Required Entries
----------------
Note: source is required for all atlas types
- freesurfer: manifold, fname, regions
- fsl: probthresh, regions
- mask: sourcedir, sourcelabels
- label: sourcedir, sourcelabels
- sphere: coordsys, radius, centers

Variable Name
-------------
``atlases``

"""

atlases = {"": 
               {"source":  "freesurfer",
               "manifold": "volume",
               "fname":    ".mgz",
               "regions": [ ]},
           "": 
               {"source":   "freesurfer",
                "manifold": "surface",
                "fname":    ".annot",
                "regions": [ ]},
           "":
               {"source":    "label",
                "hemi": "",
                "sourcedir": "",
                "sourcefiles": ["", ""],
           "":
               {"source":   "sphere",
                "coordsys": "MNI",
                "radius":   "10",
                "centers":
                  {"one" : (34, 98, 9),
                   "two" : (45, 20, 4)}
                }
   

#--------------------<Freesurfer Subject Directory>------------------------#
"""
Specify the path to your Freesurfer Subjects directory. If your data has not
been processed in Freesurfer, leave this variable as an empty string.

Format
------
string

Variable Name
-------------
``subjdir``

"""

subjdir = ""

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
--------------
``paradigms``

"""

paradigms = {"": "",
             "": ""}

#--------------------------<First Level Design>----------------------------#
"""
Specify the task-related elements of your first-level design matrix.
The hrfcomponents variable specifies how many different beta images
are associated with each task condition. The betastoextract variable 
specifies which regressors to extract if multiple regressors are
associated with each task condition.  It can be "all" or a list of 
integers corresponding to the components. The conditions variable links
paradigm names (as specified above) to a list of short names (ideally
4 or 5 letters) for the task conditions in that paradigm. The order of
condition names in these lists should correspond to the order in your
beta images.

Formats
-------

- integer

- "all" or list of integers

- dictionary where each key is a string and each value is a list of strings

Variable Names
--------------
- ``hrfcomponents``

- ``betastoextract``

- ``conditions``

"""

hrfcomponents = 1

betastoextract = []

conditions = {"":   ["",""],
              "":   ["",""]}

#------------------------------<Contrasts>---------------------------------#
"""
Specify the contrasts for each paradigm involved in your analysis. The 
format is a dictionary where the keys are full paradigm names (as they
are specified above) and values are dictionaries mapping an abbreviation
for the contrast the number of con image number for that contrast.

This section is only relevant if you are using functional masks in your
analyses or extracting from contrast effect-size images.  Otherwise,
you can leave the dictionary empty.

Format
------
dictionary where each key is a string and each value is a dictionary
inner dictionary: each key is a string and each value is an integer

Variable Name
-------------
``contrasts``

"""

contrasts = {"" :  {"": ,
                    "": },
             "" :  {"": }}

#------------------------<First Level Datapaths>---------------------------#
"""
Specify the absolute path to your main directory and relative paths from
that directory to those containing timecourses, mean functionals, first-
level betas, and first-level contrast images (currently, PyROI assumes that
contrast-effect size and T statistic images are in the same directory for 
each paradigm/subject).  You may include ``$paradigm``, ``$subject``, and 
``$contrast`` wildcards in the path strings, which will be replaced
appropriately as the program runs. 


Format
------

strings


Variable Names
--------------
``basepath``

``timecoursepath``

``meanfuncpath``

``betapath``

``contrastpath``

"""

basepath = ""

betapath = ""   

contrastpath = ""

"""
For the timecoursepath and meanfuncpath variables, specify the path to
your images as above, but also include a file template with a wildcard
character (*) in the file name.  As there should only be one of each 
image type for each paradigm/subject, the wildcard should be choosen
to match only one file in the directory.
"""

timecoursepath = ""

meanfuncpath = ""


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
dictionary with a string as each key and a list of strings as each value

Variable Name
-------------
``subjects``

"""    

subjects  =  {"": 

                 [ ],

              "":

                 [ ]}

#==========================================================================#    
#==========================================================================#    
