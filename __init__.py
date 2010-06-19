"""Package for functional neuroimaging region of interest analysis in Python"""

from core import *
import core.configinterface as cfg

#If module is told to run, turn around and run _pyroi.py script
if __name__ == "__main__":
    print "Run works properly"
    """
    cmd = ["_pyroi.py"]
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            cmd.append(arg)
    P = subprocess.call(cmd)
    """
