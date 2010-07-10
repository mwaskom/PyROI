"""Package for functional neuroimaging region of interest analysis in Python"""
from atlases import *
from database import build_database
from core import RoiResult, import_config, write_config_base
import source
import exceptions
import treeutils as tree
import configinterface as cfg

__version__ = 0.1

