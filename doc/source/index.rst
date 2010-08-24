==========
PyROI Home
==========

PyROI is a Python package for functional neuroimaging region of interest
extraction and analysis.  It offers a highly efficient processing stream
and a wide range of flexibility in the way source images are parcellated.
Using PyROI, users can extract parameter and contrast effect sizes or 
timecourses from regions defined the following ways:

* `Freesurfer's <http://surfer.nmr.mgh.harvard.edu/>`_ automatic parcellation and segmentation of the cortical surface and subcortical structures in native space.

* The Harvard-Oxford Atlas from `FSL <http://www.fmrib.ox.ac.uk/fsl//>`_, a probabilistic macroanatomical atlas in standard space.

* Regions automatically created by clustering thresholded statistical maps on the average cortical surface or standard volume.

* Arbitrarily-defined ROIs in native or standard space either on the cortical surface or in the volume.

PyROI offers a unified interface to these various atlas types.  Currently, the program
is compatible with statistical images produced by SPM first-level analyses (FSL support
is forthcoming), although timecourse images processed with any analysis package should
work perfectly well.

.. toctree::
   :maxdepth: 2

   contents
   atlas_reference

* :ref:`genindex`

* :ref:`modindex`

* :ref:`search`

