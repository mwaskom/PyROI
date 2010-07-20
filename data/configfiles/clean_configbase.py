# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4

"""
This is a skeleton config file for the PyROI package.  It consists of 
several sections where you first specify the elements of your ROI
analysis and then give information about your first-level design
and directory structure so the program knows what to look for and 
where to find it.

Although the idea behind PyROI is that it gives you the flexibity
and power of Python without requiring any programming ability, some
familiarity with the basic Python data types will be useful when you
set up this config file, to avoid annoying -- and potentiall confusing
-- syntax errors when the module is imported.  Each section has notes
on the format for the variable settings required.  The `Python tutorial
<http://docs.python.org/tutorial/index.html>`_ is an excellent place
to learn about the language, but the material required to use this 
file efficiently is somewhat spread out in it.  Take a few minutes
to familiarize yourself with the definitions for the following data
types, which will save a few headaches in the long run:

- dictionaries

- lists

- strings

- integers and floats

If you feel like you understand the format each of these types
requires, you should be all set.  Just make sure to pay close 
attention to things like the order of quotation marks, commas,
and the difference between square brackets -- ``[ ]``, braces -- 
``{ }``, and parentheses -- ``( )``.  Using an editor that
highlights syntax to prepare this file is *strongly* encouraged,
as it can help you catch a lot of mistakes.

All of the commentary in this file is also availbile on the online
documentation in a format you might find easier to read.  Now, 
without further preamble, onto your project.

"""


    

projname = ""


analysis = [{"par": "", "extract": ""},
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
                "thresh": ("",0.),
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
   


paradigms = {"": "",
             "": ""}


level1program = ""

hrfcomponents = 1

betastoextract = []

conditions = {"":   ["",""],
              "":   ["",""]}


contrasts = {"" :  {"": 1,
                    "": 2},
             "" :  {"": 1}}


basepath = ""

betapath = ""   

contrastpath = ""


regmatpath = ""

timecoursepath = ""

meanfuncpath = ""



subjects  =  {"": 

                 [ ],

              "":

                 [ ]}

#==========================================================================#    
#==========================================================================#    
