#! /usr/bin/env python

"""
This script will extract the documentation from the full_configbase.py
module, reformat it somewhat, and write it as a reST document in 
$PYROI/doc/source.

"""

import os
import re
from pyroi import __file__ as roifile

roipath = os.path.split(roifile)[0]

confid = open(os.path.join(
    roipath, "data", "configfiles", "full_configbase.py"), "r")
docfid = open(os.path.join(
    roipath, "doc", "source", "config_doc.rst"), "w")

write = False
space = False

def flip(value):
    if value: 
        return False
    else:
        return True

sectionhead = re.compile("(<)([\w\s]+)(>)")

def get_head(line):

    m = sectionhead.search(line)
    if m:
        head = m.groups()[1]
    else:
        return ""

    length = len(head)
    head = "\n\n%s\n" % head
    for i in range(length):
        head = "%s-" % head
    head = "%s\n\n" % head

    return head

for num, line in enumerate(confid):

    if re.match("-+\n", line):
        space = True
        newline = ""
        for i in range(len(line) - 1):
            newline = "%s^" % newline
        line = "%s\n" % newline
    elif re.match("[ \t\n]+", line):
        space = False
    if line.startswith("#-"):
        docfid.write(get_head(line))
    else:
        if line.startswith("\"\"\""):
            write = flip(write)
            lastflip = num
    if space:
        line = "%s\n" % line

    if write and not num == lastflip:
        docfid.write(line)

confid.close()
docfid.close()

