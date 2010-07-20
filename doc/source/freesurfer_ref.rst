.. _freesurfer_atlases::

.. toctree::
    :maxdepth: 2

    definition
    dictionary
    notes
    seg_ref


Freesurfer Atlases
==================

.. _definition:

Atlas Definition
----------------
The :class:`FreesurferAtlas` is used primarily with the automatic subcortical 
segmentation and cortical parcellation of native-space T1 weighted anatomical
scans during the Freesurfer reconstruction process (recon-all).  In the near 
future, it will be possible to use this class with any atlas image that conforms
to the general characteristics of the recon-all products -- they are located in
the standard paths within the Freesufer subjects directory structure and written
such that the voxel/vertex values within of each ROI are integer ids.

.. _dictionary:

Config Dictionary
-----------------
The Freesurfer config dictionary has the following fields::

    manifold
    fname
    regions

The ``manifold`` should be either ``"volume"`` or ``surface``.  The ``fname``
should be the file name and extension of the source image as a string, e.g. 
``"aseg.mgz"`` or ``"aparc.annot"``.  The ``regions`` should be a list of 
integer values corresponding to the regions you wish to extract from.  
See the below for a table of ids and names.

.. _notes:

Atlas Notes
-----------

PyROI will look for the filename of a volume image in the 
$SUBJECTS_DIR/$subject/mri directory and a surface image in the 
$SUBJECTS_DIR/$subject/label directory.  

Currently, PyROI supports only the following files::

    aseg.mgz
    aparc.annot
    aparc.a2009s.annot

This means that you will not be able to use the Destrieux parcellation
(which defines both gyral and sulcul regions) if you processed your
T1s with a Freesurfer version older than 4.5.  See Mike Waskom for 
a standalone program that will automate the creation of the 2009
parcellation for older datasets.

If you are going to be sharing a dataset with other users of PyROI
(ie, you have the same basepath in your config files), it is advisable
that you name your freesufer atlases in a consistent fashion to avoid
duplicating the make-atlas processing The reccomended names are "aseg",
"aparc", and "destrieux" (for the aseg.mgz, aparc.annot, and aparc.a2009s.annot
files, respectively), but no specific naming system is required.

.. _seg_ref:

Segmentation ID Tables
----------------------

The tables below provide a reference for which ids to use for which strucutres.
Note that, although you will only specify a region once, data will be extracted
separately from each hemisphere.  You may be interested in the :func:`find_id`,
which will search for region ids that correpsonds to a given region name.

Note also that the values in these tables differ from those of the official 
Freesurfer look up table (at $FREESURFER_HOME/FreeSurferColorLUT.txt), so don't
use them if you're running Freesurfer programs directly.

.. include:: aseg_id_table.rst

.. include:: aparc_id_table.rst

.. include:: aparc_2009_id_table.rst

You may also be interested in `this PDF <http://web.mit.edu/mwaskom/www/
fsaverage_parcellations.pdf>`_ of the surface parcellations.

