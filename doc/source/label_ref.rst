.. _label_atlases::

Label Atlases
=============

.. _definition:

Atlas Definition
----------------
The :class:`LabelAtlas` class is used for atlases in which regions are defined by
an arbitrary number of Freesurfer .label files on the cortical surface.  Typically,
these labels are created from within the TkSurfer visualization program, but it should
not matter how they are generated.  The labels may be in native space or defined on
the fsaverage subject.  Note that, for the latter, you may find the :class:`SigSurfAtlas`
class more convenient.  Additionally, although this class will work for labels created
from the automatic cortical parcellation (the aparc or aparc.a2009s), the 
:class:`FreesurferAtlas` class is designed to be used with those atlases.

.. _dictionary:

Config Dictionary
-----------------
The label atlas config dictionary has the following fields:

* hemi
* sourcelevel
* sourcedir
* sourcefiles

The ``hemi`` should be either ``rh`` or ``lh``.  Unlike the :class:`FreesurferAtlas`
surface atlases, each hemisphere for label atlases must be processed separately.  The 
``sourcelevel`` should be either ``group`` or ``subject``, depending on whether the
orignal labels were defined on the fsaverage surface or on each subject's surface.
The ``sourcedir`` should a string representing the path to the directory where the
source files are stored.  If you are using labels defined on each subject's surface,
this path should include a ``$subject`` wildcard, which can be replaced with a subject
id to give a path to the right directory.  Finally, the ``sourcefiles`` entry should be
either a list of file names (without the path) or ``all``.  If ``all`` is used, every
file ending in ``.label`` in the source directory will be used to create the atlas; files
with other extensions will be ignored.

.. _notes:

Atlas Notes
-----------

The :class:`LabelAtlas` class can be used to extract statistics from regions defined in
a variety of ways, including by functional activation or morphological aberration.  The
`TkSurfer <http://surfer.nmr.mgh.harvard.edu/fswiki/TkSurferGuide>`_ program (part of
Freesurfer) has some nice tools for the creation of labels from functional blobs;
if you load the curvature file and an annotation along with your activation map, you 
can use the anatomy to further constrain the region definition.

If the labels are defined on the fsaverage surface, they will be resampled back to 
each subject's native surface via Freesurfer's highly-accurate spherical transform.
It is not currently possible to define a label for the whole group on a subject
other than fsaverage (ie, on a custom average subject), but please `let the developers
know <pyroi-bugs@mit.edu>`_ if you desire this functionality and it can be incorporated.

