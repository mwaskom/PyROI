import os
import shutil

import configinterface as cfg
import exceptions as ex
import core

__all__ = ["trim_analysis_tree", "make_analysis_tree", 
           "make_levelone_tree",
           "make_fs_atlas_tree", "make_reg_tree", "make_label_atlas_tree", "make_mask_atlas_tree"]

def trim_analysis_tree(analysis):
    """Remove a analysis tree and all of its contents.
    
    Parameters
    ----------
    analysis: dict
        Analysis dictionary.
    
    """
    projectdir = os.path.join(cfg.setup.basepath,
                               "roi", "analysis",
                               cfg.projectname())
    analysisname = core.get_analysis_name(analysis)
    analysisdir = os.path.join(projectdir, analysisname)

    shutil.rmtree(analysisdir)

def make_analysis_tree(analysis):
    """Set up the directory tree for an analysis.
    
    Parameters
    ----------
    analysis: dict
        Analysis dictionary.
    
    """
    roidir = os.path.join(cfg.setup.basepath, "roi")
    analysisdir = os.path.join(roidir, "analysis")

    projdir = os.path.join(analysisdir, cfg.projectname())
    logdir = os.path.join(projdir, "logfiles")
    dbdir = os.path.join(projdir, "databases")
    
    analdir = os.path.join(projdir, core.get_analysis_name(analysis))
    
    analdirs = [roidir, analysisdir, projdir, logdir, dbdir, analdir]

    for atlas in cfg.atlases().keys():
        atlasdir = os.path.join(analdir, atlas)
        analdirs.append(atlasdir)

        if cfg.atlases(atlas)["manifold"] == "surface":
            if cfg.atlases(atlas)["source"] == "freesurfer":
                hemis = ["lh","rh"]
            else:
                hemis = [cfg.atlases(atlas)["hemi"]]
            for hemi in hemis:
                hemidir = os.path.join(atlasdir, hemi)
                analdirs.append(hemidir)
                
                for res in ["extracttxt", "extractvol", "stats"]:
                    resdir = os.path.join(hemidir, res)
                    analdirs.append(resdir)
        else:
            for res in ["extracttxt", "extractvol", "stats"]:
                resdir = os.path.join(atlasdir, res)
                analdirs.append(resdir)

    print analdirs
    for direct in analdirs:
        if not os.path.isdir(direct):
            os.mkdir(direct)

def make_levelone_tree():
    """Setup the tree for level one data that will be extracted."""
    roidir = os.path.join(cfg.setup.basepath, "roi")
    l1dir = os.path.join(roidir, "levelone")

    l1dirs = [roidir, l1dir]

    for stat in ["beta", "contrast", "timecourse"]:
        statdir = os.path.join(l1dir, stat)
        l1dirs.append(statdir)

        for par in cfg.paradigms():
            pardir = os.path.join(statdir, par)
            l1dirs.append(pardir)

            for subj in cfg.subjects():
                subjdir = os.path.join(pardir, subj)
                l1dirs.append(subjdir)

    for direct in l1dirs:
        if not os.path.isdir(direct):
            os.mkdir(direct)

def make_fs_atlas_tree():
    """Setup the Freesurfer atlas tree."""
    roidir = os.path.join(cfg.setup.basepath, "roi")
    atlasdir = os.path.join(roidir, 'atlases')
    basedir = os.path.join(atlasdir, "freesurfer")

    fsdirs = [roidir, atlasdir, basedir]

    for mani in ["volume", "surface"]:
        manidir = os.path.join(basedir, mani)
        fsdirs.append(manidir)

        for par in cfg.paradigms():
            if mani == "volume":
                pardir = os.path.join(manidir, par)
                fsdirs.append(pardir)
            else:
                pardir = manidir

            for subj in cfg.subjects():
                subjdir = os.path.join(pardir, subj)
                fsdirs.append(subjdir)

                for atlas in cfg.atlases().keys():
                    if cfg.atlases(atlas)["source"] == "freesurfer":
                        atnamedir = os.path.join(subjdir, atlas)
                        fsdirs.append(atnamedir)
                    
    for direct in fsdirs:
        if not os.path.isdir(direct):
            os.mkdir(direct)

def make_reg_tree():
    """Setup the registration tree."""
    roidir = os.path.join(cfg.setup.basepath, "roi")
    basedir = os.path.join(roidir, "reg")
    regdirs = [roidir, basedir]

    for par in cfg.paradigms():
        pardir = os.path.join(basedir, par)
        regdirs.append(pardir)

        for subj in cfg.subjects():
            subjdir = os.path.join(pardir, subj)
            regdirs.append(subjdir)

    for direct in regdirs:
        if not os.path.isdir(direct):
            os.mkdir(direct)

def make_label_atlas_tree():
    """Set up the atlas tree for label atlases."""
    roidir = os.path.join(cfg.setup.basepath, "roi")
    atlasdir = os.path.join(roidir, "atlases")
    basedir = os.path.join(atlasdir, "label")
    projectdir = os.path.join(basedir, cfg.projectname())
    labeldirs = [roidir, atlasdir, basedir, projectdir]

    for subj in cfg.subjects():
        subjdir = os.path.join(projectdir, subj)
        labeldirs.append(subjdir)

        for atlas in cfg.atlases().keys():
            if cfg.atlases(atlas)["source"] == "label":
                atnamedir = os.path.join(subjdir, atlas)
                labeldirs.append(atnamedir)

    for direct in labeldirs:
        if not os.path.isdir(direct):
            os.mkdir(direct)

def make_mask_atlas_tree():
    """Set up the atlas tree for mask atlases"""
    roidir = os.path.join(cfg.setup.basepath, "roi")
    atlasdir = os.path.join(roidir, "atlases")
    basedir = os.path.join(atlasdir, "mask")
    projectdir = os.path.join(basedir, cfg.projectname())
    maskdirs = [roidir, atlasdir, basedir, projectdir]

    for atlas in cfg.atlases().keys():
        if cfg.atlases(atlas)["source"] == "mask":
            atnamedir = os.path.join(projectdir, atlas)
            maskdirs.append(atnamedir)

    for direct in maskdirs:
        if not os.path.isdir(direct):
            os.mkdir(direct)

