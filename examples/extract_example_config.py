#! /usr/bin/env python

import os

code = open("example_config.py", "w")

for line in open("example_config.rst", "r"):
    if line.startswith("    "):
        code.write(line[4:])
    elif line.startswith("\n"):
        code.write(line)
code.close()

import example_config
    
