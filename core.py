import os
import subprocess
from copy import deepcopy
import configinterface as cfg

__all__ = ["import_setup"]

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
    def __init__(self):
        
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

    def __repr__(self):

        strrep = ""
        for i, cmditem in enumerate(self.cmdline):
            strrep = "\n".join([strrep, cmditem, self.stdout[i], self.stderr[i]])
        return strrep

def import_setup(module_name):
    """Import a customized setup module into the cfg module.

    It tries to import `configmodule_name`, then just `module_name`.
    
    Parameters
    ----------
    module_name : str
        The name of the custom config file (sans .py extension).

    """
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    try:
        setupmodule = __import__("config%s" % module_name)
    except ImportError:
        setupmodule = __import__(module_name)

    cfg.setup = setupmodule
    cfg.is_setup = True

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


