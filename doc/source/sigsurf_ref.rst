.. sigsurf_atlases::

SigSurf Atlases
===============

.. _definition:

Atlas Definition
----------------
The :class:`SigSurf` class is used to turn a second-level significance map on a 
standard-space surface manifold into an atlas where regions are defined based on
the extent of activation above a given threshold.  Optionally, a false-discovery
rate correction can be applied to the activation map before clustering.  The 
regions are resampled back to each subject's native surface via Freesurfer's
spherical transform before data is extracted.

.. _dictionary:

Config Dictionary
-----------------
The sigsurf atlas dictionary has the following fields:

* hemi
* file
* thresh
* minsize

The ``hemi`` should be either ``rh`` or ``lh``.  Unlike the :class:`FreesurferAtlas`
surface atlases, each hemisphere for sigsurf atlases must be processed separately.
The ``file`` should be the path to the significance map you want to use.  This can
be absolute or relative to the basepath defined elsewhere in your config file.  The
``thresh`` argument is a three-tuple: the threshold type -- ``"fdr"`` or ``"sig"`` -- 
the threshold sign -- ``"pos"``, ``"neg"``, or ``"abs"`` -- and the threshold to use.
If you are using a significance threshold, this should be in -log10p (i.e. a sig of 2 
is equivalent to a p value of 0.01), whereas if you are using FDR, this should be a
standard decimal.  The ``minsize`` should be an integer that corresponds to the minimum
number of vertices an activation blob must have to be considered a region of interest
in your atlas.  This will depend somewhat on your hypothesis and threshold, but 50-100
should be sufficient to exclude noise activations.

.. _notes:

Atlas Notes
-----------

The regions will be named by which aparc region contains the most significant vertex.
If the peak vertex of multiple clusters are in the same region, the name will be
appended with an integer (i.e. ``precentral``, ``precentral-2``, etc.).  The
:meth:`display` method will probably come in particularly handy for sigsurf atlases
to get an idea of where you regions actually are.  The cluster summary file that
is produced when the clusters are created on the fsaverage surface is saved to
$basedir/roi/atlases/sigsurf/$projectname/$atlasname/$atlasname.sum.  This file 
contains information about the size, location, and activation of the clusters
that will constitute your atlas.

When applied to the standard ``sig.mgh`` maps produced by mri_glmfit, the cluster
thresholding inference will be done on a vertex-activation-wise level.  If you 
would rather choose regions based on a cluster-size inference, you can use the
mri_surfcluster program to create a map where the value at each vertex is the 
cluster-wise significance level of the cluster that vertex belongs to, and then
use that map as the input for your sigsurf atlas, thresholded however you would like.
Freesurfer 5 includes a built-in database for applying cluster-level significance
that will obviate this step in the future.


