__all__ = ["import_setup"]

__module__ = "utils"

import configinterface as cfg

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

