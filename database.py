"""
Database module for PyROI package.
"""
import os
import shutil
from datetime import datetime

import numpy as np

import atlases
import configinterface as cfg
from core import RoiBase, RoiResult, get_analysis_name
from exceptions import *

__module__ = "database"

def build_database(atlas, analysis, subjects=None):
    """Build a text database for an atlas/analysis extraction.

    The text database will be saved to $basedir/roi/analysis/$projectname/databases.
    This function is run automatically at the end of the group_extract() atlas method.

    Parameters
    ----------
    atlas : str, dict, or Atlas object
        Atlas name or dictionary of parameters or instance of Atlas subclass
    analysis : int or dict
        Analysis index or dictionary of parameters
    subjects : list or str, optional
        If None or missing, builds database for all subjects defined in config file.
        If a string, builds database for the subject group named by that string.  If
        a list, it builds the database for that list of subjects.
        
    Returns
    -------
    RoiResult object

    """
    if not cfg.is_setup:
        raise SetupError

    # Allow for arg format flexibility
    if isinstance(analysis, int):
        analysis = cfg.analysis(analysis)
    if subjects is None or isinstance(subjects, str):
        subjects = cfg.subjects(subjects)
    if not isinstance(atlas, RoiBase):
        atlas = atlases.init_atlas(atlas, paradigm = analysis["par"])

    # Get the name, current date, and database directory
    name = atlas.atlasname + "_" + get_analysis_name(analysis)
    newdate = str(
        datetime.now())[:-10].replace("-","").replace(":","").replace(" ","-")
    dbdir = os.path.join(cfg.setup.basepath, "roi", "analysis",
                         cfg.projectname(), "databases")
    dbfile = os.path.join(dbdir, name + ".txt")                         
    dbtmpfile = os.path.join(dbdir, ".tmp1-" + name + ".txt")
    rectmpfile = os.path.join(dbdir, ".tmp2-" + name + ".txt")
    
    # Hist file has names and dates of writing of old databases
    histfile = os.path.join(dbdir, "." + cfg.projectname() + "_history.npy")
    try:
        dbhist = np.load(histfile)
        if name in dbhist:
            # Figure out the old date and then replace it with the new date
            if dbhist.ndim > 1: 
                nameidx = np.where(dbhist == name)
                dateidx = (nameidx[0], nameidx[1]+1)
                olddate = dbhist[dateidx][0]
                dbhist[dateidx] = newdate
            else:
                olddate = dbhist[1][0]
                dbhist[1] = newdate

            archfile = os.path.join(dbdir, ".old", name + "_" + olddate + ".txt")
            try:
                # Move the old database to database depository 
                shutil.move(dbfile, archfile)
            except IOError:
                # Or just pass if the old database no longer exists
                pass
        else:
            dbhist = np.vstack((dbhist, np.array((name, newdate))))
    except IOError:
        # Catch the error where the history file doesn't exist
        dbhist = np.array((name, newdate))
    
    unitdict = {"surface": "vertices", "volume": "voxels"}
    units = unitdict[atlas.manifold]

    # Initialize the array components
    subj = np.array("subjects")
    rois = np.array("rois")
    size = np.array("base-%s" % units)
    mask = np.array("final-%s" % units)
    if analysis["extract"] == "beta":
        func = np.array(cfg.betas(analysis["par"], "names"))
    elif analysis["extract"] == "contrast":
        func = np.array(cfg.contrasts(analysis["par"], "names"))
    elif analysis["extract"] == "timecourse":
        raise NotImplementedError("Using build_database() function for timecourse extractions")

    if atlas.manifold == "volume":
        addrois = np.array([atlas.lutdict[id] for id in atlas.regions])
    elif len(atlas.iterhemi) == 1:
        addrois = np.array([atlas.lutdict[id] for id in atlas.regions[atlas.iterhemi[0]]])
    else:
        addrois = np.array([atlas.lutdict[id] for id in atlas.regions['lh']] + 
                           [atlas.lutdict[id] for id in atlas.regions['rh']])
    nrois = addrois.shape[0]
    addrois = addrois.reshape(nrois, 1)

    # Make sure surface rois start with hemi (fixes destrieux lut problem)
    splitrois = np.vsplit(addrois, len(atlas.iterhemi))
    if atlas.manifold == "surface" and len(atlas.iterhemi) == 2:
        for idx, hemi in enumerate(atlas.iterhemi):
            for i, row in enumerate(splitrois[idx]):
                roiname = row[0]
                if not roiname.startswith(hemi):
                    try:
                        surfrois = np.vstack((surfrois, np.array([hemi + "-" + roiname],)))
                    except NameError:
                        surfrois = np.array([hemi + "-" + roiname],)
        addrois = surfrois


    # Build the database
    for subject in subjects:
        atlas.init_subject(subject)
        atlas.init_analysis(analysis)
        # Volume atlases
        if atlas.manifold == "volume" or len(atlas.iterhemi) == 1:
            # Read the SegStats output files
            if atlas.manifold == "volume":
                addfunc = np.genfromtxt(atlas.functxt)
            else:
                addfunc = np.genfromtxt(atlas.functxt % atlas.hemi)
            addfunc = np.transpose(addfunc)
            addsubj = np.array([subject for i in range(nrois)]).reshape(nrois, 1)
            sizearr = np.genfromtxt(atlas.statsfile, int)
            maskarr = np.genfromtxt(atlas.funcstats, int)
            getsize = lambda id: sizearr[np.where(sizearr[:,1] == id), 2].flat[0]
            getmask = lambda id: maskarr[np.where(maskarr[:,1] == id), 2].flat[0]
            addsize = np.array([getsize(id) for id in atlas.regions]).reshape(nrois, 1)
            addmask = np.array([getmask(id) for id in atlas.regions]).reshape(nrois, 1)
            
            # Append this subject's rows
            subj = np.vstack((subj, addsubj))
            rois = np.vstack((rois, addrois))
            size = np.vstack((size, addsize))
            func = np.vstack((func, addfunc))
            mask = np.vstack((mask, addmask))
        else:
            # Bilateral surface atlases are handled differently
            splitrois = np.vsplit(addrois, len(atlas.iterhemi))
            for idx, hemi in enumerate(atlas.iterhemi):
                # Read the SegStats output files
                addfunc = np.genfromtxt(atlas.functxt % hemi)
                addfunc = np.transpose(addfunc)
                addsubj = np.array([subject for i in range(nrois/2)]).reshape(nrois/2, 1)
                sizearr = np.genfromtxt(atlas.statsfile % hemi, int)
                maskarr = np.genfromtxt(atlas.funcstats % hemi, int)
                getsize = lambda id: sizearr[np.where(sizearr[:,1] == id), 2].flat[0]
                getmask = lambda id: maskarr[np.where(maskarr[:,1] == id), 2].flat[0]
                addsize = np.array(
                    [getsize(id) for id in atlas.regions[hemi]]).reshape(nrois/2, 1)
                addmask = np.array(
                    [getmask(id) for id in atlas.regions[hemi]]).reshape(nrois/2, 1)

                # Append this subject's rows
                subj = np.vstack((subj, addsubj))
                rois = np.vstack((rois, splitrois[idx]))
                size = np.vstack((size, addsize))
                func = np.vstack((func, addfunc))
                mask = np.vstack((mask, addmask))

    # Possible hack to sort by ROI using a recarray
    fulldb = np.hstack((subj, rois, size, func, mask))
    head = fulldb[0,:]
    np.savetxt(dbtmpfile, fulldb, "%s", "\t")
    recdb = np.recfromtxt(dbtmpfile, names=True)
    sortdb = np.sort(recdb, order=["rois", "subjects"])
    np.savetxt(rectmpfile, sortdb, "%s", "\t")
    finalbody = np.genfromtxt(rectmpfile, str)
    final = np.vstack((head, finalbody))
    np.savetxt(dbfile, final, "%s", "\t")
    os.remove(dbtmpfile)
    os.remove(rectmpfile)

    # Write the updated history file
    np.save(histfile, dbhist)

    return RoiResult("Writing database to %s" % dbfile)
