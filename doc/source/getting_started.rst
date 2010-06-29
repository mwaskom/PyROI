.. _getting_started:

===============
Getting Started
===============

Currently, PyROI is undergoing internal testing at MIT and is not
yet released for use elsewhere.  The following instructions pertain
to users of the MIT Mindhive cluster.  

To access PyROI, run the following code in a terminal or add it 
to your ``~/.bashrc`` file::

    source /repos/pyroi/SetupPyROI.sh

PyROI relies on quite a few dependencies both in the form of Python
packages and external binaries.  All required Python packages run in
the NiPype environment, which is setup automatically as part of the
``SetupPyROI.sh`` script execution.

Much of the underlying processing takes place with Freesurfer binaries.
Although Mindhive users should have Freesurfer set up automatically,
those running older versions may experience strange behavior.  PyROI
was developed and tested with Freesurfer 4.5, which can be set up with
these commands::

    export FREESURFER_HOME=/software/Freesurfer/current
    source $FREESURFER_HOME/SetUpFreeSurfer.sh

To test that everything worked properly, open up IPython::

    ipython
    
Although all of the examples in this documentation are in the style 
of the standard Python interpreter, the use of IPython is highly 
recommended.  Then type::

    >>> import pyroi as roi

If you get a new prompt with no error messages, you should be good to go.

