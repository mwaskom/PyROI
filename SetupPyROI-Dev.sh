source /software/python/SetupNiPy26.sh
export FREESURFER_HOME='/software/Freesurfer/4.5.0/'
source $FREESURFER_HOME/SetUpFreeSurfer.sh
export PYTHONPATH=/repos/pyroi/PyROI-Dev:$PYTHONPATH
export PATH=/repos/PyROI-Dev:$PATH
eval $(/repos/pyroi/setdevprompt.py)