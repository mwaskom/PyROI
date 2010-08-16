# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4

"""
This is a skeleton config file for the PyROI package.  It consists of 
several sections where you first specify the elements of your ROI
analysis and then give information about your first-level design
and directory structure so the program knows what to look for and 
where to find it.

Each section is accompanied by a brief note about the expected variable
name and format.  See the documentation at http://web.mit.edu/mwaskom/pyroi 
for a fuller explanation the various components of this file.

"""

    

projname = ""


subjects  =  {"": 
                 [ ],
              "":
                 [ ]}


paradigms = {"": "",
             "": ""}


level1program = ""

hrfcomponents = 1

betastoextract = []

conditions = {"":   ["",""],
              "":   ["",""]}

sessions = {"":  1}


contrasts = {"" :  {"": 1,
                    "": 2},
             "" :  {"": 1}}


basepath = ""

betapath = ""   

contrastpath = ""

meanfuncpath = ""

regmatpath = ""

timecoursepath = ""


extractions = [{"par": "", "extract": ""},
               {"par": "", "extract": "", "maskpar": "",
                "maskcon": "", "maskthresh": 0,"masksign": ""}]


atlases = {"": 
               {"source": "freesurfer",
               "manifold": "volume",
               "fname":    ".mgz",
               "regions": [ ]},
           "": 
               {"source": "freesurfer",
                "manifold": "surface",
                "fname":    ".annot",
                "regions": [ ]},
           "":
               {"source": "fsl",
                "probthresh": 0,
                "regions":   [ ]},
           "":
               {"source": "sigsurf",
                "hemi": "",
                "file": "",
                "thresh": ("","",0.),
                "minsize": 0},
           "":
               {"source": "label",
                "hemi": "",
                "sourcelevel": "",
                "sourcedir": "",
                "sourcefiles": ["", ""]},
           "":
               {"source": "mask",
                "sourcedir":   "",
                "sourcefiles": ["", ""]},
           "":
               {"source": "sphere",
                "coordsys": "",
                "radius":   0.,
                "centers":
                  {"" : (0.,0.,0.),
                   "" : (0.,0.,0.)}
                }}
   

#==========================================================================#    
#==========================================================================#    
