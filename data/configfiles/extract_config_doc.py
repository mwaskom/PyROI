#! /usr/bin/env python

"""
This script will extract the documentation from the full_configbase.py
module, write it as a reST document, and then append that document to the 
end of config_into.rst in the documentation directory.
"""

import os
import re
from shutil import copyfileobj
import pyroi

path = os.path.split(pyroi.__file__)[0]
docpath = os.path.join(path, "doc", "source")

confid = open(os.path.join(path, "data/configfiles/full_configbase.py"), "r")
docfid = open(os.path.join(docpath, "config_doc.rst"), "w")

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

final = open(os.path.join(docpath, "config_file.rst"), "w")
final.write(".. _config_file\n\n")
copyfileobj(open(os.path.join(docpath, "config_intro.rst"), "rb"), final)
copyfileobj(open(os.path.join(docpath, "config_doc.rst"), "rb"), final)
final.close()
