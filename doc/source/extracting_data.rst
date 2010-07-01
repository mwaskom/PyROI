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

Using the Config File
---------------------

For standard processing streams in PyROI, you will not need to interact
directly with the information from the config file.  If you do wish to
access the data, however, you should do so through the ``roi.cfg``
module.  See the :ref:`config_interface`_  reference for full information
about the functions afforded by that module.

Extracting Data
---------------



