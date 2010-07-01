# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4

"""
This is a skeleton config file for the PyROI package.

"""


    

projname = ""


analysis = [{"par": "", "extract": ""},
            {"par": "", "extract": "", "maskpar": "",
             "maskcon": "", "maskthresh": 0,"masksign": ""}]


atlases = {"": 
               {"source": "freesurfer",
               "manifold": "volume",
               "fname": ".mgz",
               "regions": [ ]},
           "": 
               {"source": "freesurfer",
                "manifold": "surface",
                "fname": ".annot",
                "regions": [ ]},
           "":
               {"source": "label",
                "manifold": "surface",
                "hemi": "",
                "sourcedir": "",
                "sourcefiles": ["", ""]}
   


subjdir = ""


paradigms = {"": "",
             "": ""}


hrfcomponents = 1

betastoextract = []

conditions = {"":   ["",""],
              "":   ["",""]}


contrasts = {"" :  {"": ,
                    "": },
             "" :  {"": }}


basepath = ""

betapath = ""   

contrastpath = ""


timecoursepath = ""

meanfuncpath = ""



subjects  =  {"": 

                 [ ],

              "":

                 [ ]}

#==========================================================================#    
#==========================================================================#    
