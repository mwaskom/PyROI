.. _extracting_data:

===============
Extracting Data
===============

Importing the Config File
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
config interface module, which is imported as ``roi.cfg`` automatically
when you import pyroi.  You can always check whether a config file has
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

Using the Config File
---------------------

Although you can access all of the config setup attributes through ``roi.cfg.setup``, 
it is best to use the functions in ``roi.cfg`` to interact with the information.  See
the :ref:`configinterface` module reference for full information, but generally you will
just interact with the ``analysis()`` and ``atlases()`` functions.

To access a specific analysis dictionary, call the ``roi.cfg.analysis()`` function with
the dictionary index in the analysis list as an argument (remember that Python is 0-based)::

    >>> analysis = roi.cfg.analysis(0)
    >>> analysis
    {'par': 'social', 'extract': 'beta'}

You would then pass this dictionary to an atlas object (see below).  To get the whole
list of analyses to then iterate over, just call the function with an empty scope::

    >>> analyses = roi.cfg.analysis()
    >>> analysis
    [{'par': 'social', 'extract': 'beta'},
     {'par': 'novelfaces', 'extract': contrast'}]



