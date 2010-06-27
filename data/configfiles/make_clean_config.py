import os

fullfid = open(os.path.join(os.path.split(__file__)[0],
                            "full_configbase.py"), "r")
cleanfid = open(os.path.join(os.path.split(__file__)[0],
                             "clean_configbase.py"), "w")
                             
write = True
lastflip = None

def flip(value):
    if value:
        return False
    else:
        return True

for num, line in enumerate(fullfid):
    
    if not line.startswith("#--"):
        if line.startswith("\"\"\"") and num > 8:
            write = flip(write)
            lastflip = num

        if write and not lastflip == num:
            cleanfid.write(line)

fullfid.close()
cleanfid.close()

