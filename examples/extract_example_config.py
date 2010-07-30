#! /usr/bin/env python

import os

code = open("example_config.py", "w")

lastline = ""
for line in open("example_config.rst", "r").read():
    if lastline.endswith("::"):
        code.write(line[4:])
    lastline = line

code.close()
