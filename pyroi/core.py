"""
Core classes and functions for the PyROI package.
"""
import os
import re
import sys
import shutil
import subprocess
from copy import deepcopy
from datetime import datetime
import numpy as np
import nipype.interfaces.base as pypebase
import configinterface as cfg

__all__ = ["RoiResult",
           "import_config", "write_config_base", "config_file_path", "find_id"]

__module__ = "core"

class RoiBase(object):
    """Base class for PyROI objects that defines run methods."""
    def __init__(self, **kwargs):

        self.__dict__.update(**kwargs)
        if "debug" not in self.__dict__:
            self.debug = False

    def _run(self, input):
        """Interface to _nipype_run and _manual_run methods.
        
        Parameters
        ----------
        input : list or nipype interface object
            If the input is a list, it gets passed to the _manual_run
            method to be executed with a subprocess system call.  If 
            an interface, it is passed to _nipype_run and executed by
            calling its run() method.

        Returns
        -------
        RoiResult object
        """

        if isinstance(input, pypebase.Interface):
            return self._nipype_run(input)
        elif isinstance(input, list):
            return self._manual_run(input)
        else:
            raise TypeError("Unexpected input %s" % type(input))
            

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
        """Run a command line program that lacks a nipype interface.
        
        Parameter
        ---------
        cmd : list
            List of command and argument strings

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
    """Result class to return PyROI processing command lines and results.
    
    An object of this class is returned any time a method runs an external
    binary for processing.  It has three main attributes: cmdline, stdout,
    and stderr.  Each is a list of strings, with the same index in each
    list corresponding to the command line that was called and any infor-
    mation from the stdout and stderr system pipes.  The class has a
    __str__ method that turns these lists into a readable string that will
    duplicate what you would have seen on your terminal.

    By calling or using the add() method on another RoiResult object,
    it will add that object's information to its internal result lists.  
    
    """
    def __init__(self, cmdline=None, res=None, log=False, continue_log=False, logdir=None):
        
        self.cmdline = []
        self.stdout = []
        self.stderr = []

        if log:
            self._setup_log(continue_log, logdir)
        else:
            self.log = False

        if cmdline is not None:
            self(cmdline, res)

    def __call__(self, cmdline, res=None):
        """Call the object with a cmdline and optionally a processing result.""" 
        if isinstance(cmdline, self.__class__):
            self.cmdline.extend(cmdline.cmdline)
            self.stdout.extend(cmdline.stdout)
            self.stderr.extend(cmdline.stderr)
            logentry = ""
            for i, entry in enumerate(cmdline.cmdline):
                logentry = "\n".join((logentry, cmdline.cmdline[i],
                                      cmdline.stdout[i], cmdline.stderr[i]))
        elif cmdline is None:
            self.cmdline.append("")
            self.stdout.append("")
            self.stderr.append("")
            logentry = ""
        else:
            self.cmdline.append(cmdline)
            logentry = cmdline
            if isinstance(res, list):
                self.stdout.append(res[0])
                self.stderr.append(res[1])
                logentry = "\n".join((logentry, res[0], res[1]))
            elif res is not None:
                self.stdout.append(res.runtime.stdout)
                self.stderr.append(res.runtime.stderr)
                logentry = "\n".join((logentry, res.runtime.stdout, res.runtime.stderr))
            else:
                self.stdout.append("")
                self.stderr.append("")

        logentry = logentry + "\n"
        if self.log:
            self._log_fid.write(logentry)

    def __str__(self):

        strrep = ""
        for i, cmditem in enumerate(self.cmdline):
            strrep = "\n".join([strrep, cmditem, self.stdout[i], self.stderr[i]])
        return strrep

    def add(self, cmdline, res=None):

        self(cmdline, res)

    def last(self):

        print "\n".join([self.cmdline[-1], self.stdout[-1], self.stderr[-1]])

    def _setup_log(self, continue_log, logdir):
        """Set up the logging."""
        self.log = True
        self.continue_log = continue_log

        if logdir is None:
            self.logdir = os.path.join(cfg.setup.basepath, "roi", "analysis",
                                       cfg.projectname(), "logfiles")
            self._loghistfile = os.path.join(self.logdir, ".logtimestamp")                   
            self._archive_log = True                                           
            self._oldlogdir = os.path.join(self.logdir, "archive")
        else:
            self.logdir = logdir
            self._archive_log = False
        self.log_file = os.path.join(self.logdir, "pyroi.log")

        if self._archive_log and os.path.isfile(self.log_file):
            try:
                oldtimestamp = open(self._loghistfile,"r").read()
            except IOError:
                oldtimestamp = "unknown"
            if not continue_log:
                shutil.move(self.log_file, 
                             os.path.join(self._oldlogdir, "pyroi_%s.log" % oldtimestamp))
        if not continue_log: 
            self._log_fid = open(self.log_file, "w")
            self._write_new_log_header()
        else:
            self._log_fid = open(self.log_file, "a")
            self._write_continue_log_header()

        newtimestamp = str(
            datetime.now())[:-10].replace("-","").replace(":","").replace(" ","-")
        if self._archive_log:
            histfid = open(self._loghistfile, "w")
            histfid.write(newtimestamp)
            histfid.close()
    
    def _write_new_log_header(self):
        pass

    def _write_continue_log_header(self):
        pass


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
        f.write(os.path.split(filename)[1])

    sourcepath = os.path.join(os.path.split(__file__)[0], "data", "configfiles")
    if clean:
        sourceprefix = "clean"
    else:
        sourceprefix = "full"
    sourcefile = os.path.join(sourcepath, "%s_configbase.py" % sourceprefix)

    shutil.copy(sourcefile, filename)
    
def config_file_path():
    """Return the file location of an imported config file or report that it doesn't exist.

    Returns
    -------
    Config file path if import was successful, or None if not
    """
    if hasattr(cfg, "setup"):
        return os.path.abspath(cfg.setup.__file__)
    else:
        print "Config file not imported."
        return None

def find_id(term, atlastype=None):
    """Search for IDs whose region name contains some term.
    
    This function can be used to search for ids to use with 
    the built-in macroanatomical atlases.  Because many of 
    the region names contain abbreviations, it is best to 
    use shortened search terms (e.g., `cingul` to seach for
    regions in the cingulate).  This search will hopefully 
    get smarter in the future.

    Parameters
    ----------
    term : str
        Term to search for (not case sensitive)
    atlastype : {"freesurfer" | "fsl"}, optional
        Atlas type to search regions of.  Searches all if absent.
    """

    seed = re.compile(term, re.I)
    freesurftbls = ["aseg.mgz", "aparc.annot", "aparc.a2009s.annot"]
    harvoxtbls = ["HarvardOxford"]
    if atlastype is None:
        tbls = freesurftbls + harvoxtbls
    elif atlastype.lower() == "freesurfer":
        tbls = freesurftbls
    elif atlastype.lower() == "fsl" or atlastype.lower() == "harvardoxford":
        tbls = freesurftbls
    dirstem = os.path.join(os.path.split(__file__)[0], "data")
    res = ""
    for lut in tbls:
        tabres = ""
        if lut in freesurftbls: 
            dir = os.path.sep.join((dirstem, "Freesurfer"))
        else:
            dir = os.path.sep.join((dirstem, "HarvardOxford"))
        tblarr = np.genfromtxt(os.path.join(dir, "%s_id_table.txt" % lut), str)
        for row in tblarr:
            if re.search(seed, row[1]):
                line = ": ".join((row[1], row[0]))
                tabres = "".join((tabres, "\n", line))
        if tabres:
            line = ""
            for i in range(len(lut)):
                line = "".join((line, "-"))
            res = "".join((res, "\n\n", lut, "\n", line, tabres))
    print res[1:]

#XXX Semi-privatize these    
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


