Getting Started
===============

Currently, PyROI is undergoing internal testing at MIT and is not
yet released for use elsewhere.  The following instructions pertain
to users of the MIT Mindhive cluster:

To access PyROI, you need only to add the package directory to your
Python and system paths.  That can be accomplished by running the following
code in a terminal or your .bashrc::

$ export PYTHONPATH=/repos:$PYTHONPATH
$ export PATH=/repos:$PATH

PyROI relies on quite a few dependencies both in the form of Python
packages and external binaries.  All required Python packages run in
the NiPype environment, which can be accessed with the following code::

$ source /software/python/SetupNiPy26.sh

Much of the underlying processing takes place with Freesurfer binaries.
Although Mindhive users should have Freesurfer set up automatically,
those running older versions may experience strange behavior.  PyROI
was developed and tested with Freesurfer 4.5, which can be set up with
this code::

$ export FREESURFER_HOME=/software/Freesurfer/current
$ source $FREESURFER_HOME/SetUpFreeSurfer.sh

To test that everything worked properly, open up the Python interpreter
or iPython (use of the latter is highly recommended) and type::

>>> import pyroi as roi

If you get a new prompt with no error messages, you should be good to go.

