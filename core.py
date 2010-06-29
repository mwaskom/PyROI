import os
import sys
import shutil
import subprocess
from copy import deepcopy
import configinterface as cfg

__all__ = ["import_config", "write_config_base"]

__module__ = "core"

class RoiBase(object):
    """Base class for PyROI objects that defines run methods."""
    def _nipype_run(self, interface):
        """Run a program using its nipype interface.
        
        Parameter
        ---------
        interface : NiPype interface object
        
        Returns
        -------
        PyROI result object
        
        """
        result = RoiResult()
        if self.debug:
            result(interface.cmdline)
        else:
            res = interface.run()
            result(interface.cmdline, res)
        return result

    def _manual_run(self, cmd):
        """Run a freesurfer program that lacks a nipype interface.
        
        Parameter
        ---------
        interface : NiPype interface object
        
        Returns
        -------
        PyROI result object

        """
        result = RoiResult()
        cmdline = " ".join(cmd)
        if self.debug:
            result(cmdline)
        else:
            proc = subprocess.Popen(cmdline, 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    env=deepcopy(os.environ.data),
                                    shell=True)
            stdout, stderr = proc.communicate()
            result(cmdline, [stdout, stderr])
        return result

class RoiResult(object):
    """Result class to return PyROI processing command lines and results"""
    def __init__(self, cmdline=None, res=None):
        
        self.cmdline = []
        self.stdout = []
        self.stderr = []

    def __call__(self, cmdline, res=None):
        """Call the object with a cmdline and optionally a processing result.""" 
        if isinstance(cmdline, self.__class__):
            self.cmdline.extend(cmdline.cmdline)
            self.stdout.extend(cmdline.stdout)
            self.stderr.extend(cmdline.stderr)
        else:
            self.cmdline.append(cmdline)

            if isinstance(res, list):
                self.stdout.append(res[0])
                self.stderr.append(res[1])
            elif res is not None:
                self.stdout.append(res.runtime.stdout)
                self.stderr.append(res.runtime.stderr)
            else:
                self.stdout.append("")
                self.stderr.append("")

    def __str__(self):

        strrep = ""
        for i, cmditem in enumerate(self.cmdline):
            strrep = "\n".join([strrep, cmditem, self.stdout[i], self.stderr[i]])
        return strrep

    def add(self, cmdline, res=None):

        self(cmdline, res)

    def last(self):

        print "\n".join([self.cmdline[-1], self.stdout[-1], self.stderr[-1]])

def import_config(module_name):
    """Import a customized config setup module into the cfg module.

    Note that this allows import by filename (i.e. you can give a
    path to python module not in your working directory or on your
    Python path.

    You can check whether the file imported correctly with the
    ``is_setup`` attribute of the config interface module::

        >>> import pyroi as roi
        >>> roi.cfg.is_setup
        False

        >>> roi.import_config("/mindhive/gablab/myconfigfile.py")
        >>> roi.cfg.is_setup
        True

    You can also double-check which module is actually being
    used for configuration with the __file__ attribute of the
    setup module within the config interface::

    >>> roi.cfg.setup.__file__
    '/mindhive/gablab/myconfigfile.pyc'

    Parameters
    ----------
    module_name : str
        The filename of the custom config file.

    """
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    if os.path.split(module_name)[0]:
        sys.path.append(os.path.abspath(os.path.split(module_name)[0]))

    setupmodule = __import__(os.path.split(module_name)[1])

    cfg.setup = setupmodule
    cfg.is_setup = True

def write_config_base(filename, force=False, clean=False):
    """Write a config file skeleton.

    If a file with the filename you give exists, it will be overwritten.
    This function also attempts to write a file called ``.roiconfigfile``
    to the target directory, the contents of which are the name of your
    config file.  When you import PyROI, it will look for this file
    and attempt to import the config file specified within.  If this
    file exists in your target directory, however, this function will
    not overwrite it by default (it will however warn you about its
    existence).  Include the argument ``force = True`` to overwrite
    a .roiconfigfile file in the target directory.

    Parameters
    ----------
    filename : str
        What to call the file.  If a path is given, writes to that path.
        Otherwise, writes to the working directory.
    force : bool, optional
        If true, overwrites a .roiconfigfile file if it exists in the target
        directory.  False by default.
    clean : bool, optional
        If true, writes the config file skeleton without any documentation.
        False by default.
    
    """
    if not filename.endswith(".py"):
        filename = "%s.py" % filename
    targpath = os.path.abspath(os.path.split(filename)[0])
    if os.path.isfile(os.path.join(targpath, ".roiconfigfile")) and not force:
        print ("\nWarning: found '.roiconfigfile' in target directory."
               "\nYour config file will not automatically import."
               "\n(But someone else's might.)")
    else:
        f = open(os.path.join(targpath, ".roiconfigfile"), "w")
        w.write(os.path.split(filename)[1])

    sourcepath = os.path.join(os.path.split(__file__)[0], "data", "configfiles")
    if clean:
        sourceprefix = "clean"
    else:
        sourceprefix = "full"
    sourcefile = os.path.join(sourcepath, "%s_configbase.py" % sourceprefix)

    shutil.copy(sourcefile, filename)
    
def get_analysis_name_list(full=True):
    """Return a list of analysis names in PyROI format.

    Parameters
    ----------
    cfg : module
        Initialized config module.
    full : bool, optional
        If true, appends the extract value to the name.

    Returns
    -------
    list of strings
        List of analysis names.

    """
    analnames = []
    for anal in cfg.analysis():
        analnames.append(get_analysis_name(anal, full))
    return analnames
        
def get_analysis_name(analysis, full=True):
    """Get an analysis name in PyROI format.

    Parameters
    ----------
    analysis : dict
        Analysis dictionary.
    full : bool, optional
        If true, appends the extract value to the name.
 
    Returns
    -------
    str
       Properly fomatted analysis name.

    """
    analpar = cfg.paradigms(analysis["par"], "upper")
    extract = analysis["extract"]
    if "maskpar" in analysis.keys() and analysis["maskpar"] != "nomask":
        maskpar = cfg.paradigms(analysis["maskpar"], "lower")
        maskcon = analysis["maskcon"]
        maskthresh = str(analysis["maskthresh"])

        stem = "%s_%s-%s-%s" % (analpar, maskpar, maskcon, maskthresh)

    else:
        stem = "%s_nomask" % (analpar)

    if full:
        return "%s_%s" % (stem, extract)
    else:
        return stem


