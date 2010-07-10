.. _extracting_data:

Extracting Data
===============


Importing the config file
-------------------------

Code examples for the remainder of the documentation will assume that you 
imported PyROI like this::

    >>> import pyroi as roi

PyROI will look for a file called ``.roiconfigfile`` in your working directory,
and, if it finds it, attempt to import the config module defined within.  This
file is automatically generated when you produce a config file skeleton with the
``write_config_base()`` function, but you rename your file, etc., you will have 
to update the ``.roiconfigfile`` accordingly.  If this file does not exist or 
if the import fails, you will have to manually import a config file with the
``import_config()`` function::

    >>> roi.import_config("my_config_file.py")

Note that this allows import by filename, so you can give a path to a config
file that is not in the working directory.

Either method imports your config file into the ``setup`` module of the
config interface module, which is loaded as ``roi.cfg`` automatically
when you start pyroi.  You can always check whether a config file has
been imported with the ``is_setup`` attribute of the config interface 
module::

    >>> roi.cfg.is_setup
    False

    >>> roi.import_config("my_config_file.py")
    >>> roi.cfg.is_setup
    True

To see which file actually provided the configuration information, check
the ``__file__`` attribute of the internal ``roi.cfg.setup`` module::

    >>> roi.cfg.setup.__file__
    'my_config_file.py'


Using the config file
---------------------

For standard processing streams in PyROI, you will not need to interact
directly with the information from the config file.  If you do wish to
access the data, however, you should do so through the ``roi.cfg``
module.  See the `config interface`_  reference for full information
about the functions afforded by that module.


An introduction to extraction
-----------------------------

Here's the standard workflow for a single subject extraction:

- Create an atlas object

- Initialize that object for a subject

- Create the atlas image

- Initialize the atlas for an analysis

- Prepare the source images

- Extract the data

In code, this is what that looks like::

    >>> atlas = roi.init_atlas("atlas_name")
    >>> atlas.init_subject("subj_id")
    >>> res = atlas.make_atlas()
    >>> atlas.init_analysis(1)
    >>> atlas.prepare_source_images()
    >>> res = atlas.extract()

The extraction method  will produce three files.  One will be a text 
file summarizing the regions from which data was extracted and the size
of those regions.  If a functional mask was included in the analysis 
parameters, the size of the regions will be reported after masking.  
The second will be a text summary of the average statistical value for 
each ROI in each frame of the input image.  The third will be a binary
"volume" file with the same data as the previous file as "voxel" values
-- one voxel for each ROI in each frame.

As convenient as this is, it still would be a hassle to type it out for
each subject in your project.  You could get the subject list from the 
``roi.cfg.subjects()`` function, and write a for loop to iterate over
the list, but there is a better way: all public processing methods on
atlases classes in PyROI have a "group" counterpart that does the same 
thing, but for a group of subjects::

    >>> atlas = roi.init_atlas("atlas_name")
    >>> res = atlas.group_make_atlas()
    >>> res = atlas.group_prepare_source_images(1)
    >>> res = atlas.group_extract(1)

This will create the same three summary files as before, but for each
subject in the group.  Having shown you the ease with which you can extract
data for a group, let's now go over each step in a bit more detail.


Initializing an atlas
---------------------

The first step is always to initialize an atlas object.  There are five
different atlas classes, one for each type of atlase: FreesurferAtlas(),
HarvardOxfordAtlas(), MaskAtlas(), LabelAtlas(), and SphereAtlas().  The
``init_atlas()`` function provides a common interface to these classes.  It can
be called with either the name of an atlas or a dictionary of atlas
parameters.  For instance, doing this::

    >>> atlasdict = roi.cfg.atlases("atlas_name")
    >>> atlas = roi.init_atlas(atlasdict)

Will do the same thing as the first line in the above snippets of code.  

Something that wasn't discussed above is that native space atlases
(currently this means just Freesurfer atlases) must be initialized with 
a paradigm -- corresponding to the main analysis paradigm -- before they
can be initialized with a subject.  However, *another* thing that wasn't
d
iscussed is that both paradigm initialization and subject initialization
can be acheived through the ``init_atlas()`` method::

    >>> atlas = roi.init_atlas("atlas_name", "subj_id", "par_name")

Note that, because of the order of arguments, if you want to initialize a
paradigm but not a subject (so you can use group processing methods),
you'll need to use a keyword argument::

    >>> atlas = roi.init_atlas("atlas_name", paradigm="par_name")

Otherwise, you can just use the ``init_paradigm()`` method::

    >>> atlas = roi.init_atlas("atlas_name")
    >>> atlas.init_paradigm("par_name")


Making the atlases
------------------

For all classes but the HarvardOxfordAtlas class, some preprocessing needs
to be done to create the final atlas image before data can be extracted.
This all occurs when you call the ``make_atlas()`` method on the atlas
object, but here I will discuss what is happening behind the scenes for
each class.  Note that the native-space atlases (Freesurfer and Label
atlases) need to be initialized with a subject before the atlas is made,
while the standard space atlases (Mask and Sphere atlases) do not.

Freesurfer atlases
^^^^^^^^^^^^^^^^^^

For Freesurfer surface atlases, nothing needs to be done to create the
atlas image; data will be extracted from the aparc.annot or
aparc.a2009s.annot.  

For volume atlases, the atlas images are sampled from anatomical space
(where voxels are 1mm isotropic) to native functional space (where voxel
size depends on the scan parameters).  Before this resampling happens, the
mean functional scan for the analysis paradigm is registered to the T1
image using Freesurfer's bbregister program.  

Registration can take quite a bit of time, however, so the default behavior
for the ``make_atlas()`` method is only to create a registration matrix if
it is not found.  This behavior can be controlled with the ``reg`` argument
of the method.  By default it is set to ``1``; setting it to ``2`` will
cause all registration matrices to be created, overwriting any that might
currently exist.  In contrast, setting it to ``0`` will cause the method to
never estimate the registration, and instead to skip any subjects for which
it does not find the matrix file.  

Note that the registration step is the only processing element that behaves
this way: all other processing steps will run regardless of whether the
file they create already exists.

Finally, although bbregister typically works very well, it is good practice
to check the registration and, optionally, adjust it.  This can be done with
the ``check_registration()`` method, which will open up a tkregister2 window.

Mask atlases
^^^^^^^^^^^^

Mask atlases are created from a list of binary mask images, so the first
step in creating a mask atlas is adjusting the voxel values so that the ROI
in each image has a different value, and then combining these image files
into a single atlas volume.

Label atlases
^^^^^^^^^^^^^

Label atlases are created from labels in fsaverage space.  First, these
labels are resampled back to the native surfaces via Freesurfer's spherical
transformation.  Then, the label files are combined into one annotation
file, which is used as the atlas.

Sphere atlases
^^^^^^^^^^^^^^

Sphere atlases are created from lists of coordinates.  If necessary,
coordinates in Talairach space are adjusted to MNI space with the Brett
transform.  Then, the spheres themselves are created and combined into  one
atlas volume through a process similar to the mask atlas processing stream.

Viewing the final atlas
^^^^^^^^^^^^^^^^^^^^^^^

Once an atlas has been created, it can be visually inspected by calling the
``display()`` method.  If it is a volume atlas, this will open up Freeview,
whereas surface atlases will be displayed in tksurfer.


Preparing source images
-----------------------

Once the atlas image has been created, initialize the atlas object with an
analysis.  Analyses are keyed by their index in the analysis list, although
note that these indices, unlike others in Python, are *not* zero-based.  In
other words, calling ``atlas.init_analysis(1)`` will initialize the atlas
object with the analysis defined by the first dictionary of analysis
parameters.  Any argument that takes an analysis index will also take an
analysis dictionary that is returned by the ``roi.cfg.analysis()``
function, if you find this confusing or just want to be safe.

For most analyses, the source images will need to be preprocessed before
they are ready for extraction.  If parameter or contrast effect sizes are
going to be extracted, the individual volumes containing those statistics
will be concatenated into a single volume with as many frames as there are
regressors/contrasts specified in your config file.  

If you are preparing images for extraction with a surface atlas, the 
statistical volumes will be sampled to the surface.  The same registration
issues as discussed in the Freesurfer atlas preprocessing section apply to
this step, and the behavior and ``reg`` argument options are also the same.

Finally, if a functional mask is part of the analysis, the T-statistic
images will be converted to -log10(p) images to confrom with the operation
of the Freesurfer binaries used to perform the extraction


Processing Results
------------------

In the code snippets above, you may have noticed that processing method
calls were assigned to a variable called ``res``.  All processing methods
return an instance of the RoiResult() class, which holds the command lines
used to call external binaries and any information that they returned
through the stdout or stderr pipes.  To see this information, simply print
the result object::

    >>> res = aseg.extract()
    >>> print res
    mri_segstats --i /g2/gablab/sad/PY_STUDY_DIR/Block/roi/levelone/beta/novelfaces/SAD_020/task_betas.mgz 
    --seg /g2/gablab/sad/PY_STUDY_DIR/Block/roi/atlases/freesurfer/volume/novelfaces/SAD_020/aseg/aseg.mgz 
    --id 17 --id 18 --id 53 --id 54 
    --sum /g2/gablab/sad/PY_STUDY_DIR/Block/roi/analysis/development/NF_nomask_beta/aseg/stats/SAD_020.stats 
    --avgwf /g2/gablab/sad/PY_STUDY_DIR/Block/roi/analysis/development/NF_nomask_beta/aseg/extracttxt/SAD_020.txt 
    --avgwfvol /g2/gablab/sad/PY_STUDY_DIR/Block/roi/analysis/development/NF_nomask_beta/aseg/extractvol/SAD_020.nii

    Loading /g2/gablab/sad/PY_STUDY_DIR/Block/roi/atlases/freesurfer/volume/novelfaces/SAD_020/aseg/aseg.mgz
    Loading /g2/gablab/sad/PY_STUDY_DIR/Block/roi/levelone/beta/novelfaces/SAD_020/task_betas.mgz
    Voxel Volume is 14.6228 mm^3
    Generating list of segmentation ids
    Found   4 segmentations
    Computing statistics for each segmentation
      0    17    316  4620.81
      1    18    132  1930.21
      2    53    328  4796.28
      3    54     95  1389.17

    Reporting on   4 segmentations
    Computing spatial average of each frame
      0  1  2  3
    Writing to /g2/gablab/sad/PY_STUDY_DIR/Block/roi/analysis/development/NF_nomask_beta/aseg/extracttxt/SAD_020.txt
    Writing to /g2/gablab/sad/PY_STUDY_DIR/Block/roi/analysis/development/NF_nomask_beta/aseg/extractvol/SAD_020.nii

If you call a result object on a different result object (or call it on a
function that returns one), it will add the information in the latter
object to its internal records.  In this way, result objects can be used in
a script to easily create a log object, which you can then write to a file
after you finish your processing::

    >>> result = roi.RoiResult()
    >>> res = atlas.make_atlas()
    >>> result(res)
    >>> res = atlas.extract()
    >>> result(res)
    >>> log = open("log_file.txt", "w")
    >>> log.write("%s" % str(result))
    >>> log.close()

You can also print the last group of command lines and system pipe
information by calling the ``res.latest()`` method.


