import os
import re

confid = open("full_configbase.py", "r")
docfid = open("config_doc.rst", "w")

write = False

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
        head = "%s^" % head
    head = "%s\n\n" % head

    return head

for num, line in enumerate(confid):

    if line.startswith("#-"):
        docfid.write(get_head(line))
    else:
        if line.startswith("\"\"\""):
            write = flip(write)
            lastflip = num

        if write and not num == lastflip:
            docfid.write(line)

confid.close()
docfid.close()

