#! /usr/bin/env python

"""Initial testing framework: merely loop through the atlases/analyses from the
development config file on debug and run the various methods.  Should suffice for
now... """

import sys
import pyroi as roi

res = roi.RoiResult(log=True, logdir=".")
run = False
native=True
standard=True
if "--no-native" in sys.argv: native=False
if "--no-standard" in sys.argv: standard=False
if "--run" in sys.argv: run = True

if native:
    # Native space analyses

    roi.import_config("/u2/mwaskom/roidevelopment_native.py")

    path = roi.config_file_path()
    res("Config file: %s" % path)

    for anal in roi.cfg.analysis():
        for name in roi.cfg.atlases():
            atlas = roi.init_atlas(name, anal["par"], debug=not run)
            res(atlas.group_make_atlas())
            res(atlas.group_prepare_source_images(anal))
            res(atlas.group_extract(anal))

if standard:
    # Standard space analyses

    roi.import_config("/u2/mwaskom/roidevelopment_standard.py")

    path = roi.config_file_path()
    res("Config file: %s" % path)

    for anal in roi.cfg.analysis():
        for name in roi.cfg.atlases():
            atlas = roi.init_atlas(name, anal["par"], debug= not run)
            res(atlas.group_make_atlas())
            res(atlas.group_prepare_source_images(anal))
            res(atlas.group_extract(anal))
