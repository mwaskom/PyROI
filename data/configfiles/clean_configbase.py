# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
   May/June 2010 update of ROI pypeline.  A work in progress.

   Michael Waskom -- mwaskom@mit.edu
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

betastoextract = ""

conditions = {"":   ["",""],
              "":   ["",""]}


contrasts = {"" :  {"": ,
                    "": },
             "" :  {"": }}


basepath = ""

timecoursepath = ""

meanfuncpath = ""

betapath = ""    

contrastpath = ""


subjects  =  {"": 

                 [ ],

              "":

                 [ ]}

overwrite = {"task_betas" : True,
             "registration" : True,
             "resampled_volumes" : True,
             "freesurfer_annots" : True,
             "full_atlas_stats" : True,
             "label_atlases" : True,
             "spm_sig_images" : True,
             "functional_extracts" : True}


#==========================================================================#    
#==========================================================================#    
