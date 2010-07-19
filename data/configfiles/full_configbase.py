# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4

"""
This is a skeleton config file for the PyROI package.  It consists of 
several sections where you first specify the elements of your ROI
analysis and then give information about your first-level design
and directory structure so the program knows what to look for and 
where to find it.

Although the idea behind PyROI is that it gives you the flexibity
and power of Python without requiring any programming ability, some
familiarity with the basic Python data types will be useful when you
set up this config file, to avoid annoying -- and potentiall confusing
-- syntax errors when the module is imported.  Each section has notes
on the format for the variable settings required.  The `Python tutorial
<http://docs.python.org/tutorial/index.html>`_ is an excellent place
to learn about the language, but the material required to use this 
file efficiently is somewhat spread out in it.  Take a few minutes
to familiarize yourself with the definitions for the following data
types, which will save a few headaches in the long run:

- dictionaries

- lists

- strings

- integers and floats

If you feel like you understand the format each of these types
requires, you should be all set.  Just make sure to pay close 
attention to things like the order of quotation marks, commas,
and the difference between square brackets -- ``[ ]``, braces -- 
``{ }``, and parentheses -- ``( )``.  Using an editor that
highlights syntax to prepare this file is *strongly* encouraged,
as it can help you catch a lot of mistakes.

All of the commentary in this file is also availbile on the online
documentation in a format you might find easier to read.  Now, 
without further preamble, onto your project.

"""


    
#----------------------------<Project Name>--------------------------------#
"""
Give your project a name that will be associated with the analysis 
databases and any user-defined atlases you create.  The sense of a
*project* in PyROI is somewhat narrower than the traditional sense
of a research project: each config file should have a unique project
name, but multiple config files may be associated with the collection
of subjects and functional paradigms that constitute your research
project.

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
An *analysis* consists of the functional paradigm for which data will 
be extracted, which type of image the data will be extracted from, and,
optionally, the parameters for a functional mask that will be applied
to the image before extraction.  Here, you specify a list of these such
analyses that will be used in your project.  

Note that the "masking" considered part of an analysis is wholly 
separate from the definition ROIs, which is part of the concept of an 
*atlas,* and specified below.

All of the mask parameters are optional. If left unset, analysis will 
be specified as "nomask" and statistics will be extracted from the full
ROI. 

In your operation of the program, analyses will be referred to by their
index in the list (i.e. analysis 1, analysis 2, etc.), so you may want
to take some note of the order.  In the databases, the analyses are
referred to by a code in the form EE_mmCvC_stat, where `EE` is the code
for the paradigm that statistics are extracted from `mm` is the mask
paradigm, `CvC` is the mask contrast, and `stat` is the type of image
that is extracted.  See the paradigms_ section below to specify these
codes.

See the "Entries" notes for the key names to use and their meanings.  
Values should be set according to the paradigm and contrast names you
specify  in the appropriate sections below in this config file.

Format
------
A list of dictionaries

Entries
-------
- par : string -- full name of main analysis paradigm

- extract: "beta," "contrast," or "timecourse"

- maskpar : string -- the full name of the mask paradigm 

- maskcon : string -- the name of the mask contrast 

- maskthresh : float -- threshold for the mask in -log10(p)

- masksign : "pos", "neg", or "abs" -- how to threshold

Variable Name
-------------
``analysis``

"""

analysis = [{"par": "", "extract": ""},
            {"par": "", "extract": "", "maskpar": "",
             "maskcon": "", "maskthresh": 0,"masksign": ""}]

#------------------------------<Atlases>-----------------------------------#
"""
An *atlas* is the concept that lets you define the regions PyROI will
extract data from.  There currently five atlas types: Freesurfer atlases,
the Harvard-Oxford probabilistic atlas distributed with FSL, and atlases
composed of regions defined by the user in the form of Freesurfer surface
labels, binary mask volumes, or spheres.

See the atlas reference pages in the online documentation for a full
description of the various atlases you can use and how to set them up.

Format
------
A dictionary of dictionaries.  
The key in each inner dictionary is a string, and the value formats are given below.

Entry Formats
--------------
- source: "freesurfer", "fsl", "mask", "label", or "sphere"
- regions: list of integers
- manifold: "volume" or "surface"
- fname: string
- hemi: "lh" or "rh"
- file: string
- thresh: tuple ("sig" or "fdr", float)
- probthresh: integer
- sourcelevel: "subject" or "group"
- sourcedir: string
- sourcefiles: "all" or list of strings 
- coordsys: "mni", "tal", or "vox"
- radius: integer
- centers: dictionary with a string keys and tuples of integers as values 


Required Entries
----------------
Note: source is required for all atlas types
- freesurfer: manifold, fname, regions
- fsl: probthresh, regions
- sigsurf: hemi, file, thresh, minsize
- mask: sourcedir, sourcelabels
- label: hemi, sourcelebel, sourcedir, sourcelabels
- sphere: coordsys, radius, centers

Variable Name
-------------
``atlases``

"""

atlases = {"": 
               {"source": "freesurfer",
               "manifold": "volume",
               "fname":    ".mgz",
               "regions": [ ]},
           "": 
               {"source": "freesurfer",
                "manifold": "surface",
                "fname":    ".annot",
                "regions": [ ]},
           "":
               {"source": "fsl",
                "probthresh":  ,
                "regions",   []},
           "":
               {"source": "sigsurf",
                "hemi": "",
                "file": ""
                "thresh": ("",)
                "minsize": },
           "":
               {"source": "label",
                "hemi": "",
                "sourcelevel": ""
                "sourcedir": "",
                "sourcefiles": ["", ""],
           "":
               {"source": "mask",
                "sourcedir":   "",
                "sourcefiles": ["", ""]}
           "":
               {"source": "sphere",
                "coordsys": "",
                "radius":   ,
                "centers":
                  {"" : ( , , ),
                   "" : ( , , )}
                }
   

#-----------------------------<Paradigms>----------------------------------#
"""
These are the full and shorthand names for the paradigms involved in 
your analyses. The format is a dictionary where keys are full names 
and values are short names. Full names should correspond to the name 
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
Specify the task-related elements of your first-level design matrix,
And the program that was used to analyze it (currently is supported, but
FSL should be soon. The hrfcomponents variable specifies how many different
beta images are associated with each task condition. The betastoextract 
variable specifies which regressors to extract if multiple regressors 
are associated with each task condition.  It can be "all" or a list of 
integers corresponding to the components. The conditions variable links
paradigm names (as specified above) to a list of short names (ideally
4 or 5 letters) for the task conditions in that paradigm. The order of
condition names in these lists should correspond to the order in your
beta images.

Formats
-------
- "SPM"

- integer

- "all" or list of integers

- dictionary where each key is a string and each value is a list of strings

Variable Names
--------------
- ``level1program``

- ``hrfcomponents``

- ``betastoextract``

- ``conditions``

"""

level1program = ""

hrfcomponents = 1

betastoextract = []

conditions = {"":   ["",""],
              "":   ["",""]}

#------------------------------<Contrasts>---------------------------------#
"""
Here you name the contrasts for each paradigm involved in your analysis.
The format is a dictionary where the keys are full paradigm names (as they
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

contrasts = {"" :  {"": 1,
                    "": 2},
             "" :  {"": 1}}

#------------------------<First Level Datapaths>---------------------------#
"""
Specify the absolute path to your main directory and relative paths
from that directory to those containing certain types of images.  You 
may include ``$paradigm``, ``$subject``, ``group``, and ``$contrast`` 
wildcards in the path strings, which will be replaced appropriately as the 
program runs.  After replacement,each variable should pick out a single 
directory in your file system.

A directory will be created within the basepath directory called ``roi``,
which is where all files created by PyROI will be stored.

The betapath variable gives the path to parameter estimates for regressors
from your first-level model.  The contrastpath variable gives the path to
contrast effect size estimates and T stastic images (currently, PyROI 
assumes these are in the same directory).  The timecourse path leads to
functional timecourses at your desired level of preprocessing, and the 
meanfunctionalpath should lead to a single-frame mean image created from
your timecouse.  Finally, the regmat path leads to a .dat registration file
created by the Freesurfer program bbregister.  This matrix should align a
subject's natve-space functional volume to the cortical surfaces.  If you
have not run bbregister on your subjects, simply leave this variable as 
something that evaluates to False (e.g., ``""``), and PyROI will perform
the registration.

See the note below on the special usage for the timecourse, regmat, and mean
functional variables.


Format
------
strings


Variable Names
--------------
``basepath``

``betapath``

``contrastpath``

``timecoursepath``

``meanfuncpath``

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

regmatpath = ""

timecoursepath = ""

meanfuncpath = ""


#----------------------------<Subjects>------------------------------------#
"""
Here you name the subjects in your project.  The format is a dictionary
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
