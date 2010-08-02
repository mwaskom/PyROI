.. _example_config:

Below are the example components of full config file.  This example is based
off a real analysis stream, although some elements have been modified for
demonstrative purposes.  The code for this file can also be obtained `here`.

We will call the project this config file is for the "pyroi_tutorial"::

    projname = "pyroi_tutorial"

This project has four subjects, two in a "control" group and two in a "patient"
group.  Here is how we'll set up our subjects' dictionary::

    subjects  =  {"contol": 

                     ["subj_1", "subj_2"],

                  "patient":

                     ["subj_3", "subj_4"]}

We had two functional paradigms in our study.  The first, we'll call a "social"
paradigm, because we looked at response to social and nonsocial stimuli. The
second is the "novelfaces" paradigm, where we looked at the differences in response
to novel or familiar faces.  We'll code these paradigms as "sc" and "nf, which
is how they will be referred to in our databases::

    paradigms = {"social": "sc",
                 "novelfaces": "nf"}

Now we will give information about our first level design.  We used SPM with
a canonical HFR, which has one component::

    level1program = "SPM"

    hrfcomponents = 1

    betastoextract = "all"

There were five task-conditions for the social paradigm, and three task
conditions for the novelfaces paradigm.  The novelfaces paradigm had two
runs, so we must specify the beta image numbers for each run::

    conditions = {"social":     {"aface": 1,
                                 "nface": 2,
                                 "pscen": 3,
                                 "escen": 4,
                                 "nscen": 5},
                  "novelfaces": {"fmzn": (1, 9),
                                 "fmlr": (2, 10),
                                 "novl": (3, 11)}}

For our ROI analysis, there are three contrasts of interest.  For the
social paradigm, we will call them "AFvNF" for angry versus neutral
faces, and "NFvNS" for neutral faces versus neutral scenes.  In the
novelfaces paradigm, we have "NvF", or novel versus familiar::

    contrasts = {"social" :  {"AFvNF": 1,
                              "NFvNS": 2},
                 "novelfaces" :  {"NvF": 1}}

Now we have to specify where the output of our first-level analysis lives::

    basepath = "/mindhive/gablab/sad/PyROI_Example_Data/"

    betapath = "native/l1output/$paradigm/$subject/model/"   

    contrastpath = "native/l1output/$paradigm/$subject/contrast/"

In other words, the full path to a subject/paradigm's contrast images is
``/mindhive/gablab/sad/PyROI_Example_Data/native/l1output/$paradigm/$subject/contrast/``.  

Our first-level processing stream included generating registering our
mean functionals to our structural images, so we'll give the paths to
those files::

    meanfuncpath = "native/l1output/$paradigm/$subject/realign/mean*.nii"

    regmatpath = "native/l1output/$paradigm/$subject/surfreg/mean*.dat"

We're not going to be looking at timecourses, so we can just leave this
as an empty string::

    timecoursepath = ""

Now we've reached the point where we'll be setting up what we want to do with
PyROI.  First, the "analysis" list, for what we'll be extracting and how.  We
want to look at the contrast effect size images from the social paradigm and
the parameter estimate images from the novelty paradigm.  For the novelty analysis,
we also want to apply a thresholded mask to the atlas before extraction, using the
faces vs. scenes contrast from the social paradigm, thresholded so that only positively
activated voxels with a significance above 1.3 (or, in other words, with a p-value 
less than 0.05) within the ROIs in our atlases will be extracted::

    analysis = [{"par": "social", "extract": "contrast"},
                {"par": "novelfaces", "extract": "beta", "maskpar": "social",
                 "maskcon": "NFvNS", "maskthresh": 1.3,"masksign": "pos"}]

Finally, we will be using four different atlas types to define our regions of
interest.

The first uses Freesurfer's automatic volume segmentation.  In our case, we'll
be looking at the hippocampus, amygdala, and nucleus accumbens::

    atlases = {"aseg": 
                   {"source": "freesurfer",
                    "manifold": "volume",
                    "fname":    "aseg.mgz",
                    "regions": [5, 6, 7]},

The second is a surface based atlas, using the "aparc", or Desikan-Kiliany
atlas, which defines gyral based macro-anatomical ROIs.  We'll extract from the 
posterior STS ("bankSTS"), caudal ACC ("caudalanteriorcingulate") and fusiorm
gyri::

               "aparc": 
                   {"source": "freesurfer",
                    "manifold": "surface",
                    "fname":    "aparc.annot",
                    "regions": [1, 2, 7]},

In our second-level analysis, we have a model where we regress data from a clinical
scale onto our imaging data.  Here we will take the significance map from that
analysis, FDR-correct it at 0.05, and then extract from any contiguous activation
blobs larger than 200 vertices::

               "clinreg":
                   {"source": "sigsurf",
                    "hemi": "lh",
                    "file": "",
                    "thresh": ("fdr",0.05),
                    "minsize": 200},

Finally, we used the faces vs scenes contrast as a functional localizer, and have
created surface labels on each individual subject's brain using tksurfer from two
blobs we think represent the fusiform face area and the temporoparietal junction.
These labels live in the "label" directory in the Freesurfer subjects directory
structure::

               "localizer":
                   {"source": "label",
                    "hemi": "rh",
                    "sourcelevel": "subject",
                    "sourcedir": "data/$subject/label",
                    "sourcefiles": ["rh.FFA.label",
                                    "rh.TPJ.label"]},
                    }

And, we're done!

