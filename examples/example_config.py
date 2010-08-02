


projname = "pyroi_tutorial"


subjects  =  {"contol": 

                 ["subj_1", "subj_2"],

              "patient":

                 ["subj_3", "subj_4"]}


paradigms = {"social": "sc",
             "novelfaces": "nf"}


level1program = "SPM"

hrfcomponents = 1

betastoextract = "all"


conditions = {"social":     {"aface": 1,
                             "nface": 2,
                             "pscen": 3,
                             "escen": 4,
                             "nscen": 5},
              "novelfaces": {"fmzn": (1, 9),
                             "fmlr": (2, 10),
                             "novl": (3, 11)}}


contrasts = {"social" :  {"AFvNF": 1,
                          "NFvNS": 2},
             "novelfaces" :  {"NvF": 1}}


basepath = "/mindhive/gablab/sad/PyROI_Example_Data/"

betapath = "native/l1output/$paradigm/$subject/model/"   

contrastpath = "native/l1output/$paradigm/$subject/contrast/"



meanfuncpath = "native/l1output/$paradigm/$subject/realign/mean*.nii"

regmatpath = "native/l1output/$paradigm/$subject/surfreg/mean*.dat"


timecoursepath = ""


analysis = [{"par": "social", "extract": "contrast"},
            {"par": "novelfaces", "extract": "beta", "maskpar": "social",
             "maskcon": "NFvNS", "maskthresh": 1.3,"masksign": "pos"}]



atlases = {"aseg": 
               {"source": "freesurfer",
                "manifold": "volume",
                "fname":    "aseg.mgz",
                "regions": [5, 6, 7]},


           "aparc": 
               {"source": "freesurfer",
                "manifold": "surface",
                "fname":    "aparc.annot",
                "regions": [1, 2, 7]},


           "clinreg":
               {"source": "sigsurf",
                "hemi": "lh",
                "file": "",
                "thresh": ("fdr",0.05),
                "minsize": 200},


           "localizer":
               {"source": "label",
                "hemi": "rh",
                "sourcelevel": "subject",
                "sourcedir": "data/$subject/label",
                "sourcefiles": ["rh.FFA.label",
                                "rh.TPJ.label"]},
                }


