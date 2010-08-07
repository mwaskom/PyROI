.. _harvard_oxford_atlas:

Harvard Oxford Atlas
====================

.. _definition:

Atlas Definition
----------------

The :class:`HarvardOxfordAtlas` class provides access to cortical and subcortical 
regions from the Harvard-Oxford probabilistic atlas at either a 25% or 50% probability
threshold.  The atlas is in MNI152 space with 2mm isotropic voxels.

.. _dictionary:

Config Dictionary
-----------------

The Harvard Oxford config dictionary has the following fields:

* probthresh

* regions

The ``probthresh`` should be either ``25`` or ``50``.  The ``regions`` should 
be a list of integer values corresponding to the regions you wish to extract 
from.  See below for a table of ids and names.  Note that values are extracted 
separately for each hemisphere of a given region, even though the region is only 
specified once in the config file.


.. _notes:

Atlas Notes
-----------

The Harvard Oxford atlas was created from a set of manually-segmented T1
images.  See the `FSL website <http://www.fmrib.ox.ac.uk/fsl/data/atlas-descriptions.html#ho>`_
for full information about the creation of the atlas.
   
.. _id_table:

Segmentation ID Table
---------------------

The atlas regions can be queried interactively with the :func:`find_id` function
or by using the table below.  

.. include:: harvard_oxford_id_table.rst

.. _license:

License
-------

The :class:`HarvardOxfordAtlas` class uses two image files that were orignally 
distributed with FSL 4.1 and slightly modified for compatability with PyROI.
Below are the terms of the FSL licsense, which apply both to these files as
included in the distribution and the use of them within PyROI::


    FMRIB Software Library, Release 4.1 (c) 2008, The University of Oxford
    (the "Software")

    The Software remains the property of the University of Oxford ("the
    University").

    The Software is distributed "AS IS" under this Licence solely for
    non-commercial use in the hope that it will be useful, but in order
    that the University as a charitable foundation protects its assets for
    the benefit of its educational and research purposes, the University
    makes clear that no condition is made or to be implied, nor is any
    warranty given or to be implied, as to the accuracy of the Software,
    or that it will be suitable for any particular purpose or for use
    under any specific conditions. Furthermore, the University disclaims
    all responsibility for the use which is made of the Software. It
    further disclaims any liability for the outcomes arising from using
    the Software.

    The Licensee agrees to indemnify the University and hold the
    University harmless from and against any and all claims, damages and
    liabilities asserted by third parties (including claims for
    negligence) which arise directly or indirectly from the use of the
    Software or the sale of any products based on the Software.

    No part of the Software may be reproduced, modified, transmitted or
    transferred in any form or by any means, electronic or mechanical,
    without the express permission of the University. The permission of
    the University is not required if the said reproduction, modification,
    transmission or transference is done without financial return, the
    conditions of this Licence are imposed upon the receiver of the
    product, and all original and amended source code is included in any
    transmitted product. You may be held legally responsible for any
    copyright infringement that is caused or encouraged by your failure to
    abide by these terms and conditions.

    You are not permitted under this Licence to use this Software
    commercially. Use for which any financial return is received shall be
    defined as commercial use, and includes (1) integration of all or part
    of the source code or the Software into a product for sale or license
    by or on behalf of Licensee to third parties or (2) use of the
    Software or any derivative of it for research with the final aim of
    developing software products for sale or license to a third party or
    (3) use of the Software or any derivative of it for research with the
    final aim of developing non-software products for sale or license to a
    third party, or (4) use of the Software to provide any service to an
    external organisation for which payment is received. If you are
    interested in using the Software commercially, please contact Isis
    Innovation Limited ("Isis"), the technology transfer company of the
    University, to negotiate a licence. Contact details are:
    innovation@isis.ox.ac.uk quoting reference BS/3497.

