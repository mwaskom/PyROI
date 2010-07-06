"""
Database module for PyROI package.
"""
import os
import shutil
from datetime import datetime

import numpy as np

import configinterface as cfg
from core import get_analysis_name
from exceptions import *

def build_database(atlas, analysis):
    """Good Python programmers write docstrings"""
    if not cfg.is_setup:
        raise SetupError

    # Allow for arg format flexibility
    if isinstance(atlas, str):
        atlas = roi.cfg.atlases(atlas)
    if isinstance(analysis, int):
        analysis = roi.cfg.analysis(analysis)

    # Get the name, current date, and database directory
    name = atlas["atlasname"] + "_" + get_analysis_name(analysis)
    newdate = str(datetime.now())[:-10].replace("-","").replace(":","").replace("-","-")
    dbdir = os.path.join(cfg.setup.basepath, "roi", "analysis",
                         cfg.projectname(), "databases")

    # Hist file has names and dates of writing of old databases
    histfile = os.path.join(dbdir, "." + cfg.projectname() + "_history")
    try:
        dbhist = np.genfromtxt(histfile, str)
        if name in dbhist:
            # Figure out the old date and then replace it with the new date
            nameidx = np.where(dbhist == name)
            dateidx = (nameidx[0], nameidx[1]+1)
            olddate = dbhist[dateidx]
            dbhist[dateidx] = newdate
            try:
                # Move the old database to database depository 
                shutil.move(os.path.join(dbdir, name + ".txt"),
                            os.path.join(dbdir, ".old", name + "_" + olddate + ".txt"))
            except IOError:
                # Or just pass if the old database no longer exists
                pass
        else:
            dbhist = np.vstack((dbhist, np.array((name, newdate),)))
        write_new_hist = False
    except IOError:
        # Catch the error where the history file doesn't exist
        write_new_hist = True







    if write_new_hist:
        # Write a new history file
        histfid = open(histfile, "w")
        histfid.write("%s\t%s" % (name, newdate))
        histfid.close()
    else:
        # Or save the updated history array
        np.savetxt(dbfile, dbhist, "%s", "\t")
