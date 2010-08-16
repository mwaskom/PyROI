source /software/python/SetupNiPy26.sh
. fss 4.5.0
export PYTHONPATH=/repos/pyroi/PyROI-Dev:/u2/mwaskom/NiTime/:$PYTHONPATH
export PATH=/repos/pyroi/PyROI-Dev:/repos/pyroi/PyROI-Dev/bin:/u2/mwaskom/NiTime/:$PATH
eval $(/repos/pyroi/setdevprompt.py)
echo 'The PyROI development environment is now active'
