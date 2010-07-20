.. _errors:

Common Errors
=============

As you are using PyROI, you will probably run into some error messages.  When you 
cause an error, it will print a traceback to your IPython session with the code
that caused the error and some information about its type::

    >>> roi.init_atlas("foobar")
    ---------------------------------------------------------------------------
    KeyError                                  Traceback (most recent call last)

    /u2/mwaskom/<ipython console> in <module>()

    /u2/mwaskom/PyROI/pyroi/atlases.py in init_atlas(atlasdict, subject, paradigm, **kwargs)
       1571     """
       1572     if isinstance(atlasdict, str):
    -> 1573         atlasdict = cfg.atlases(atlasdict)
       1574     if atlasdict["source"] == "freesurfer":
       1575         return FreesurferAtlas(atlasdict, paradigm, subject, **kwargs)

    /u2/mwaskom/PyROI/pyroi/configinterface.pyc in atlases(atlasname)
        146         return atlasdicts
        147     else:
    --> 148         return atlasdicts[atlasname]
        149 
        150 def _check_fields(atlasfields, atlasdict):

    KeyError: 'foobar'

The first part you'll want to focus on is the last line, which names the error
(in this case, it's a ``KeyError``), and prints a message about the error that
varies somewhat in helpfulness.  Directly above the error definition is a pointer
to the offending line of code, which, depending on the error type, might be relevant
to you.  Below, we'll look at the three main types of errors that you might run into,
and how to handle them.


Syntax errors
-------------

When Python imports a file, the first thing it does is parse the code and turn it into
a set of commands.  If it runs into any illegal synatx, it will immediately raise a 
``SyntaxError`` and abort the import::  

    >>> import pyroi as roi
    ------------------------------------------------------------
       File "roidevelopment.py", line 52
         {"par": "novelfaces", "extract": "contrast"},
         ^
    SyntaxError: invalid syntax

Here, the first line of the error traceback tells us that the error is in the file 
``roidevelopment.py``, which is a config file the development team uses for testing.
The caret points to the part of the code that tripped the syntax error when the 
parser ran.  However, you might notice that nothing looks particularly off about
this line.  The annoying thing about syntax errors is that the error is usually 
raised a bit *after* the mistake.  Let's examine the sourcecode that caused the
error::

     51 analysis = [{"par": "novelfaces", "extract": "beta"} 
     52             {"par": "novelfaces", "extract": "contrast"}, 
     53             {"par": "surreal", "extract": "beta", 
     54              "maskpar": "social", "maskcon": "NFAFvNSES", 
     55              "maskthresh": 1.3, "masksign": "pos"}]

Do you see the problem?  In the line directly above the line we saw in the traceback,
we're missing a comma after the first analysis dictionary definition.  One of the most
common causes of syntax errors is forgetting commas between elements of a list or 
dictionary, or forgetting to properly close lists or dictionaries with a final ``]`` or
``}``.  Generally, the first thing you should do when you get a syntax error in your
config file is to look for these missing items directly above where the traceback points
you to an error.

A config file syntax error will be raised when the config file is imported.  If you're
using autoimport (because you have a ``.roiconfigfile`` in your working directory that
points PyROI to an existing config file), this will happen when you import pyroi.  Once
you've fixed to error, just retry the import.  If you're not using autoimport, the error
will be raised when you use the ``roi.import_config()`` function.  After fixing an error
raised then, simply recall the function.

Operator Errors
---------------

PyROI has three custom exception classes that raise errors when you use the program
incorrectly.  They are ``InitError``, ``SetupErrror``, and ``PreprocessError``.  

InitError
^^^^^^^^^

An ``InitError`` is raised when you try to use a method that requires an atlas to
be at a specific stage of initialization, for instance, calling the ``make_atlas()``
method on a native-space atlas without initializing the subject::

    >>> aseg = roi.init_atlas("aseg", paradigm="novelfaces")
    >>> res = aseg.make_atlas()
    ---------------------------------------------------------------------------
    InitError                                 Traceback (most recent call last)

    /u2/mwaskom/<ipython console> in <module>()

    /u2/mwaskom/PyROI/pyroi/atlases.pyc in make_atlas(self, reg, gen_new_atlas)
        429         elif self.source == "freesurfer":
        430             if not self._init_subject:
    --> 431                 raise InitError("Subject")
        432             res(self._make_freesurfer_atlas(reg))
        433             if self._atlas_exists: res(self._stats())

    InitError: Subject not initialized

This error is fixed by the ``init_subject()`` method::

    >>> aseg.init_subject("subj_1")
    >>> res = aseg.make_atlas()
    >>> ...

SetupError
^^^^^^^^^^

A ``SetupError`` is raised by the internal checking of config file structure.
It will usually be raised when you call methods that access the config file 
information.  Most commonly, this will be when you create an atlas object or
initialize an analysis for the atlas.  Setup errors will warn you about things
like missing atlas fields, using analysis paradigms that are not defined in your
paradigm/first-level design sections, etc.  The solution to a ``SetupError`` is
almost always to revisit you config file, possibly consulting the internal or
online documentation.

A ``SetupError`` is also raised when you use a method that tries to access the 
config file information when no config file has been imported.  Here, the solution
is to use the ``roi.import_config()`` function.

PreprocessError
^^^^^^^^^^^^^^^

Finally, a ``PreprocessError`` is raised when you get ahead of yourself and try
to perform some processing before the right images have been created::

    >>> res = aseg.extract()
    ---------------------------------------------------------------------------
    PreprocessError                           Traceback (most recent call last)

    /u2/mwaskom/<ipython console> in <module>()

    /u2/mwaskom/PyROI/pyroi/atlases.py in extract(self, analysis)
        872             raise InitError("Analysis")
        873         elif not self._atlas_exists():
    --> 874             raise PreprocessError("The atlas")
        875         elif not selg._source_exists():
        876             raise PreprocessError("The source")

    PreprocessError: The atlas does not exist

The solution here, obviously, is to back up and run the processing step that
will create the needed images.

Program Errors
--------------

Python (and some of the external modules that PyROI runs behind the scenes) provide many other
error types that you might run into.  When you get an error after running a function that
took some input, the first thing to check is that you're using the function correctly and
didn't make any mistakes in the input.  Using IPython's build in help can be useful here -- 
simply type a ``?`` after any object (variables, classes, functions, or class methods)
to view the docstring for that object::

    >>> aseg.extract?
    Type:           instancemethod
    Base Class:     <type 'instancemethod'>
    String Form:    <bound method FreesurferAtlas.extract of <pyroi.atlases.FreesurferAtlas object at 0x1d2c3d0>>
    Namespace:      Interactive
    File:           /u2/mwaskom/PyROI/pyroi/atlases.py
    Definition:     aseg.extract(self, analysis=None)
    Docstring:
        Extract average functional data from select regions in an atlas.
        
        This prints a text file with the average statistic for each region
        to the $main_dir/roi/analysis/ directory structure.  It also saves
        a binary "volume" where each voxel represents a region in the atlas.
        See the database functions to collect this data for statistical 
        analysis.
        
        Parameters
        ----------
        analysis : int, dict, or Analysis object, optional
            Analysis to extract from.  Runs init_analysis() internally.
        
        Returns
        -------
        RoiResult object.
        
        Note
        ----
        Currently, this just averages the voxelwise statistics over all voxels
        considered to be in each region, after applying a functional mask (if
        included in the analysis parameters).  If a mask is applied, it will
        also generate a count of how many voxels/vertices were included in the
        final ROI.

If you don't see any reason why your input should be causing an error, it's quite 
likely that it is not your fault, and should be `reported <mailto:pyroi-bugs@mit.edu>`_
to the developers.  Please include the full traceback, and a short description of what 
you were trying to do when the error was caused.  If you are at MIT, pointing the 
developers to your config file on the Mindhive filesystem may also be helpful.

