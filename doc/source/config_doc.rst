.. _config_doc:

This is a skeleton config file for the PyROI package.  It consists of 
several sections where you first specify the elements of your ROI
analysis and then give information about your first-level design
and directory structure so the program knows what to look for and 
where to find it.

Each section is accompanied by a brief note about the expected variable
name and format.  See the documentation at http://web.mit.edu/mwaskom/pyroi 
for a fuller explanation the various components of this file.



Project Name
------------

projname : string -- project name



Subjects
--------

subjects : dictionary

           keys   : string -- group name
           values : list of strings -- subject ids



Paradigms
---------

paradigms : dictionary

            keys   : string -- full paradigm name
            values : string -- two-letter code for paradigm name



First Level Design
------------------

level1program : string
                    "SPM" or "FSL" (optional -- default: "SPM")

hrfcomponents : integer
                    number of components associated with each task regressor in your model

betastoextract : list of integers, or "all"
                    which components to extract parameter estimates for

conditions : dictionary

                 keys   : string -- full paradigm name
                 values : list of strings -- task condition names

sessions : dictionary (optional: if absent, assumes one session)

                 keys   : string -- full paradigm name
                 values : integer -- number of sessions (runs) for that paradigm


Contrasts
---------

contrasts : dictionary
           
            keys   : string -- full paradigm name
            values : dictionary
                     
                     keys   : string -- contrast name (in shorthand)
                     values : integer -- number of the corresponding contrast image


First Level Datapaths
---------------------

basepath : string
           absolute path to the top of your project tree; the roi directory will be stroed here

All paths below are should be relative to the basepath (but can be absolute)

betapath       : string
                 path to the results of your model estimation 

contrastpath   : string
                 path to the results of your contrast estimation     
                
timecoursepath : string
                 path to a timecourse image

meanfuncpath   : string
                 path to a mean functional image

regmatpath     : string
                 path to a registration matrix mapping functional space to native anatomical space

fssubjectsdir  : string
                 path to your Freesurfer Subject's Directory



Extraction Parameters
---------------------

extractions : dictionary
              
              Fields:
               Required:
                "par"     : paradigm to extract from
                "extract" : type of image to extract (beta, contrast, or timecourse)
               Optional:
                "maskpar"    : paradigm mask image will come from 
                "maskcon"    : contrast to mask image with before extraction
                "maskthresh" : threshold to apply to the mask (in -log10(p))
                "masksign"   : constrain mask to "pos" or "neg" (optional -- default "abs")


Atlases
-------

Required Entries
^^^^^^^^^^^^^^^^

Note: source is required for all atlas types

- freesurfer: manifold, fname, regions

- fsl: probthresh, regions

- sigsurf: hemi, file, thresh, minsize

- mask: sourcedir, sourcefiles

- label: hemi, sourcelevel, sourcedir, sourcefiles

- sphere: coordsys, radius, centers


Entry Formats
^^^^^^^^^^^^^^

- source: "freesurfer", "fsl", "mask", "label", or "sphere"

- regions: list of integers

- manifold: "volume" or "surface"

- fname: string

- hemi: "lh" or "rh"

- file: string

- thresh: tuple ("sig" or "fdr"; "pos", "neg", or "abs"; float)

- probthresh: integer

- sourcelevel: "subject" or "group"

- sourcedir: string

- sourcefiles: "all" or list of strings 

- coordsys: "mni", "tal", or "vox"

- radius: integer

- centers: dictionary with a string keys and tuples of integers as values 


