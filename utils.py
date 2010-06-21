import configinterface as cfg

__all__ = ["import_setup"]

__module__ = "utils"

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


