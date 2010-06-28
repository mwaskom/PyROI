.. _config_file:

===============
The Config File
===============

The config file is central to PyROI.  Before you can do just about anything
else, you have to set up your config file, which tells the program which
atlases you want to use, how to use them, and where to find the data to
use them on.

Getting a config base
---------------------

To get a config file skeleton, start the python interpreter and run the 
following commands::

>>> import pyroi as roi
>>> roi.write_config_base("your_config_file_name")

Replace "your_config_file_name" with the name you wish to use, of course.
If you just give a file name, it will write the file to your working 
directory.  If you give it as a path, it will write the file to the
directory specified on the path.  If there is a file with the name you
give in the target directory, it will be overwritten, so make sure to 
check for that first.

There are two other options that can be given as arguments.  The 
function will attempt to write a file called .roiconfigfile to the
target directory, the contents of which will tell PyROI the name of
your config file.  If this file exists when you run the ``write_config_base``
function, however, it will not be overwritten.  You can cause the file 
to be overwritten by adding the argument ``force = True`` to the function
call.

By default, the config file base contains a lot of commentary on what
the different parts of the config file do and the format they are
expected to be in.  If you want to write a clean config file without
all of these coments, add the argument ``clean = True`` to the function
call.  This is not recommended for beginners.

Config file content
-------------------

The following duplicates the internal config file documentation:

May/June 2010 update of ROI pypeline.  A work in progress.

Michael Waskom -- mwaskom@mit.edu


Project Name
------------

Specify the name your analysis will be associated with. All analysis
results will be printed to roi/analyses/$projname.

Format
^^^^^^

string


Variable Name
^^^^^^^^^^^^^

``projname``




Analysis Parameters
-------------------

Specify the parameters for an arbitrary number of analyses. Task-related
betas from the main analysis paradigm will be extraced from each ROI. 
You may also specify a functional mask defined by a first-level paradigm
which will be applied before extraction. The mask will restrict extraction
to those voxels/vertices that are active in the mask contrast above the 
mask threshold, with the direction specified by mask sign. If analysis is
being done in the volume, mask paradigms must be in the same space as the
analysis paradigm.  This should not matter on the surface.

See the "Entries" section below for the key names to use.  Values
should be set according to the paradigm and contrast names you specify
below in this setup functino.

All of the mask parameters are optional. If left unset, analysis will 
be specified as "nomask" and statistics will be extracted from the full
ROI.  NB: Mask thresh is in -log10(P).

Format: list of dictionaries, with each dictionary in the list specifying
a separate analysis

Entries
^^^^^^^

par : full name of main analysis paradigm

extract: betas, contrasts, or timecourse

maskpar : full name of functional mask paradigm 

maskcon : abbreviated name of functional mask contrast 

maskthresh : threshold for functional mask (in -log10(P))

masksign : pos, neg, or abs


Variable Name
^^^^^^^^^^^^^

``analysis``




Atlases
-------

Specify the atlases that will define your ROIs, and which ROIs from
those atlases you will investigate. The format is of a dictionary
where each key is a shorthand name for an atlas and the value is
a dictionary of attributes for that atlas.

For all atlases, you must specify the source and space. 

Source can be "freesurfer", for freesurfer segmentations/parcellations
in native space; "talairach", for a modified version of the talairach
daemon used by the WFU Pick Atlas that is provided with this software;
"mask", for an atlas composed of an arbitrary number of non-overlap-
ping binary image files in the same space, or "label", for an atlas
composed of an arbitrary number of non-overlapping Freesurfer labels
in fsaverage space. Space is either "volume" or "surface"; if the atlas
is surface-based, you should also provide the hemisphere in the atlas
dictionary with the "hemi" key.

If source is "freesurfer", just provide the filename (this requires your
Freesurfer subject directory to be set below). If source is "talairach",
give the path to the image file. For both of these sources, also specify
a list of the numerical IDs to investigate from that atlas. For label or
mask sources, you will need to provide two pieces of information: the 
path to the directory where your masks/labels are stored and a list of
the names for the masks/labels in that atlas. ROI names will be derived
from these file names.

Format
^^^^^^

dictionary with internal dictionaries for each atlas


Parameters
^^^^^^^^^^

All:

- source : freesurfer, talairach, label, mask

- manifold : volume or surface

Freesurfer or Talairach Daemon source:

- fname : file name of atlas

- regions : list of numerical ids to regions under investigation

Label Source:

- hemi : hemisphere

Label or Mask source:

- sourcedir : directory with source images

- sourcefiles : list label or mask image file names 


Variable Name
^^^^^^^^^^^^^

``atlases``




Freesurfer Subject Directory
----------------------------

Specify the path to your Freesurfer Subjects directory. If you are not
using any Freesurfer-based atlases, just specify an arbitry path.  
Do not delete the variable, as it will cause the program to crash.

Format
^^^^^^

string


Variable Name
^^^^^^^^^^^^^

``subjdir``




Paradigms
---------

Specify the full and shorthand names for the paradigms involved in you
analyses. The format is a dictionary where keys are full names and
values are short names. Full names should correspond to the name 
associated with the paradigm in your file directory (case-sensitive),
while shorthand names should be a two-letter code that will identify 
the paradigm in your database.

Format
^^^^^^

dictionary


Variable Name
^^^^^^^^^^^^^^

``paradigms``




First Level Design
------------------

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

Note that although the hrfcomponents variable is added for forward
compatability, the ROI pypeline has not been tested on any data
with multiple HRF comopnents for each task condition.

Formats
^^^^^^^

integer

"all" or list of integers

dictionary where each key is a string and each value is a list of strings


Variable Names
^^^^^^^^^^^^^^

``hrfcomponents``

``betastoextract``

``conditions``




Contrasts
---------

Specify the contrasts for each paradigm involved in your analysis. The 
format is a dictionary where the keys are full paradigm names (as they
are specified above) and values are dictionaries mapping an abbreviation
for the contrast (typically in FsFast style) to the number of con image
for that contrast.

Note that if you are not going to be using any functional masks, you can
leave this as an empty dictionary.

Format
^^^^^^

dictionary where each key is a string and each value is a dictionary

inner dictionary: each key is a string and each value is an integer


Variable Name
^^^^^^^^^^^^^

``contrasts``




First Level Datapaths
---------------------

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
^^^^^^

string


Variable Names
^^^^^^^^^^^^^^

``basepath``

``timecoursepath``

``meanfuncpath``

``betapath``

``contrastpath``




Subjects
--------

Specify the subjects to use in your analyses.  The format is a dictionary
where keys are the names of your groups and values are lists of your
subjects, specified by how they are stored in your filesystem (Freesurfer
ID, etc.). Maintain this format even if you have only one group; simply 
use the name of your experiment, or other, as the single key to the dict-
ionary in that case.

Format
^^^^^^

dictionary with strings as each key and a list of strings as each value


Variable Name
^^^^^^^^^^^^^

``subjects``


