"""
   NOTE: Deprecated 5/27/2010
"""

import nipype.interfaces.freesurfer as fs
import numpy as N
import fsroidict
import string
import os

def ProjectName():
    """This is where you specify your project name, which will be the name of
    the directory in roi/analyses/ where your data will be stored.
 
    Returns: string
    """
 
    #--------------------------------------------------------------------------#
    projname = 'development'
    #--------------------------------------------------------------------------#
    
   
    return projname


def Groups():
    """Here is where you set whether you want to run statistics for both groups
    or are looking at only one of your groups.  The return value should correspond 
    with the code in the Subjects function below (i.e. it should be either 'all,' 
    'patients,' or 'controls.'

    Returns: string
    """

    #--------------------------------------------------------------------------#
    grouptype = 'all'
    #--------------------------------------------------------------------------#

    return grouptype


def Analysis():
    """A way to hardcode a list of dictionaries specifying analysis
    parameters (analysis paradigm and mask paradigm, contrast, sign, and thresh).
    You can leave out the masksign parameter and it will be set to 'pos.'
    Note: must be a list of dictionaries, even if specifying only one analysis.
    Leave out the mask parameters if you don't want to mask the ROI.
 
    Returns: list of dictionaries
    """

    #--------------------------------------------------------------------------#
    analysis = [{'par':'novelfaces','maskpar':'social','maskcon':'AFvNF',
                 'maskthresh':0,'masksign':'pos'},
                {'par':'social','maskpar':'novelfaces','maskcon':'AvF',
                 'maskthresh':1.3,'masksign':'pos'},
		        {'par':'social'}]
    #--------------------------------------------------------------------------#
    
    return analysis


def SegVols(retval='dict'):
    """A dictionary of the automatic segmentation volumes
    (those that reside in the $SUBJ/mri/ directory with segmentation
    names keyed in the fsroidict.py module).

    Returns: dictionary or string
    """

    #--------------------------------------------------------------------------#
    segvols = {'aseg':'aseg',
               'parc1':'aparc',
               'parc2':'aparc.a2009s'}
	      # 'label_seg':'label_seg'}
    #--------------------------------------------------------------------------#
    
    space = RoiSpace('orig')
    tempsegvols = {}
    for key in segvols:
        if space[key] == 'surface':
	    for hemi in ['lh','rh']:
	        tempsegvols[key+'.'+hemi] = hemi+'.'+segvols[key]
        else:
	    tempsegvols[key] = segvols[key]
    segvols = tempsegvols

    space = RoiSpace()
    for segkey in segvols.keys():
         if segkey == 'aseg' or segkey == 'label_seg':
             segvols[segkey] = segvols[segkey] + '.mgz'
         elif space[segkey] == 'volume':
             segvols[segkey] = segvols[segkey] + '+aseg.mgz'
         elif space[segkey] == 'surface':
             segvols[segkey] = segvols[segkey]

    if retval == 'dict':   
        return segvols
    else:
        return segvols[retval]


def Regions(seg='aseg'):
    """A group of lists with the numerical ids (found in FreesurferColorLUT.txt)
    for the ROIs we are investigating.  

    Returns: list 
    """

 
    #--------------------------------------------------------------------------#
    regions = {
    # Subcoritcal ROIs (for use with aseg.mgz)
    'aseg' : [17,18,53,54],
    
    # Desikan-Killiany cortical ROIs (for use with aparc+aseg.mgz)
    'parc1.lh' : [1014,1022],
    'parc1.rh' : [2014,2022],
    
    # Destrieux cortical ROIs (for use with aparc.a2005/9s+aseg.mgz)
    'parc2' : [11106,12106],

    'label_seg' : []} #Labels('fullids')}
    #--------------------------------------------------------------------------#

    for key in regions:
        if isinstance(regions[key],int):
            regions[key] = [regions[key]]
    
    retlist = regions[seg]
    retlist.sort()
    if RoiSpace(seg) == 'surface':
        retlist = [int(i-(N.floor(i/100)*100)) for i in retlist]
    return retlist


def Labels(retval='fulldict'):
    """
    
    NOTE: this docstring is depracated, but it's Saturday and I'm lazy

    A list of names for rois that are the prefix to their .label files 
    (without the .label extension).  For use with labels created  from 
    functional data, or other non recon-all source.  If you do not intend
    To examine any label-based ROIs, this should be an empty list: []
    NOTE: labels should be bilateral (for now).

    Returns: list
    """
    
    #--------------------------------------------------------------------------#
    labels = {}
    """{'lh':
             {1:'lh_dummylabel_1'},
        'rh':
             {1:'rh.FFA'}}"""
    #--------------------------------------------------------------------------#

    if not labels: return None

    labels['adjrh'] = {}
    adj = len(labels['lh'].keys()) + 1
    for id in labels['rh'].keys():
        labels['adjrh'][id*adj] = labels['rh'][id]

    lhids = labels['lh'].keys()
    rhids = labels['adjrh'].keys()
    lhids.sort()
    rhids.sort()
    fullids = lhids + rhids

    fullnames = []
    for id in fullids:
        if id < adj: hemi = 'lh'
	else: hemi = 'adjrh'
        fullnames.append(labels[hemi][id])
       
    if len(labels['lh'].keys()) != len(labels['rh'].keys()):
        raise Exception('Number of label ROIs are not even across hemispheres')

    realnames = []
    for id in labels['lh'].keys():
        if 'dummy' not in labels['lh'][id]:
	    realnames.append(labels['lh'][id])
	else:
	    oppname = labels['rh'][id]
	    fakename = 'lh_' + oppname[3:len(oppname)]
	    realnames.append(fakename)
    for id in labels['rh'].keys():
        if 'dummy' not in labels['rh'][id]:
	    realnames.append(labels['rh'][id])
	else:
	    oppname = labels['lh'][id]
	    fakename = 'rh_' + oppname[3:len(oppname)]
	    realnames.append(fakename)

    if retval == 'fulldict': 
        return labels
    elif retval == 'lh' or retval == 'left':
        return labels['lh']
    elif retval == 'rh' or retval == 'right':
        return labels['adjrh']
    elif retval == 'origrh' or retval == 'origright':
        return labels['rh']
    elif retval == 'fullids':
        return fullids    
    elif retval == 'fullnames':
        return fullnames
    elif retval == 'realnames':
        return realnames
    elif retval == 'adjust':
        return adj
    elif retval == 'space':
        return RoiSpace()['label_seg']
    else:
        raise Exception('Label return value \'%s\' not understood' % retval)


def RoiSpace(retval='dict'):
    """Sets whether the ROIs will be analyzed in the volume or on the surface.
    Note: aseg ROIs must be analyzed in the volume.  Label ROIs should be
    analyzed in the space in which they were created.

    Returns: dict
    """
    
    #--------------------------------------------------------------------------#
    roispacedict = {'aseg':'volume',
                    'parc1':'surface',
                    'parc2':'volume',
		            'label_seg':'volume'}
    #--------------------------------------------------------------------------#

    if retval == 'orig':
        return roispacedict

    temproispacedict = {}
    for key in roispacedict:
        if roispacedict[key] == 'surface':
	    temproispacedict[key+'.lh'] = 'surface'
	    temproispacedict[key+'.rh'] = 'surface'
        else:
	    temproispacedict[key] = 'volume'

    roispacedict = temproispacedict

    if retval == 'dict':
        return roispacedict
    else:
        return roispacedict[retval]


def SubjDir():
    """Sets the Freesurfer subject directory.

    Returns: string
    """    

    #--------------------------------------------------------------------------#
    subjdir = fs.FSInfo.subjectsdir(os.path.abspath('data'))
    #--------------------------------------------------------------------------# 
    
    return subjdir    


def Paradigms(parname='all',case='upper'):
    """Contains two items: a list of paradigms used in this analysis (paradigms 
    should have the same scan parameters if they will be used in ROI analysis),
    and a dictionary to link paradigm names to two-letter shortcuts for datafiles.
    If called with an empty scope, returns the list; if called with a paradigm name,
    it will return the shortcut.

    Second argument sets the case of the abbreviation, if intended to be returned.
    By default returns upper case, which is convention for analysis paradigm.  Include
    'lower' to return lowercase, which is convention for mask paradigm.

    Returns: list or string
    """

    #--------------------------------------------------------------------------#
    parlist = ['novelfaces','novelobjects','social','masked','surreal']
    
    pardict = {'novelfaces':   'nf',
               'novelobjects': 'no',
               'social':       'sc',
               'surreal':      'sr',
               'masked':       'mk'}
    #--------------------------------------------------------------------------#


    if parname == 'all':
        return parlist
    else:
        if case == 'lower':
            return pardict[parname]
        elif case == 'upper':
            return string.swapcase(pardict[parname])
        else:
            raise exception('Case argument \'%s\' to '+\
	                        'config.Paradigms not understood.' % case)


def Betas(par,retval='names'):
    """Contains  lists defining the task condition names.  Can return those
    names or the file names of their associated beta images.  First argument 
    should be the paradig you want the betas for, second arugment should be 
    either 'images' or 'names' ('names' is default) depending on what you want 
    to return.  Names should be shortened to fit in the stats database, if possible.
    Also suggested is that all beta names for one paradigm have same length.

    Returns: list
    """    

    #--------------------------------------------------------------------------#
    components = 1
    
    if par == 'novelfaces':
        condnames = ['fmzn','fmlr','novl']
    elif par == 'novelobjects':
        condnames = ['fmzn','fmlr','novl']
    elif par == 'surreal':
        condnames = ['valid','inval']
    elif par == 'masked':
        condnames = ['mkfr','mknl','fear','neut']
    elif par == 'social':
        condnames = ['aface','nface','pscen','escen','nscen'] 
    else:
        raise Exception('Paradigm \'%s\' not found' % par)
    #--------------------------------------------------------------------------#


    condimages = []
    mcompnames = []

    for i in range(1,len(condnames)+1):
        for j in range(0,components):
            pad = None
            if j < 10:
	        pad = '0'
            mcompnames.append(condnames[i-1] + '-' + pad + str(j+1))
	    num = i + ((i-1)*(components-1)) + j
            if num < 10:
                condimages.append('beta_000%s.img' %str(num))
            elif num < 100:
                condimages.append('beta_00%s.img' %str(num))
            elif num < 1000:
                condimages.append('beta_0%s.img' %str(num))
            else:
                condimages.append('beta_%s.img' %str(num))

    if retval == 'images':
        return condimages
    elif retval == 'names' and components == 1:
        return condnames
    elif retval == 'names' and components > 1:
        return mcompnames
    else:
        raise Exception('Beta return type \'%s\' not understood' % retval)


def Contrasts(par,type='P-map',format='.nii'):
    """A set of dictionaries that define the contrast image number
    for each paradigm in FsFast format.  Arguments: par = paradigm,
    type = 'T-map' or 'con-img' (default).  

    Returns: dictionary
    """

    contrasts = {}
    
    #--------------------------------------------------------------------------#
    if par == 'novelfaces':
        contrasts = {'NFvFF':     1,
                     'AvF':       2}
    elif par == 'novelobjects':
        contrasts = {'NOvFO':     1,
                     'AvF':       2}
    elif par == 'surreal':
        contrasts = {'IvV':       1,
                     'AvF':       2}
    elif par == 'social':
        contrasts = {'AFvNF':     1,
                     'ESvNS':     2,
                     'NFvNS':     3,
                     'AFvES':     4,
                     'AFESvNFNS': 5,
                     'NFAFvNSES': 6,
                     'AFNSvNFES': 7,
                     'AvF':       8,
                     'AFvNS':     9,
                     'PSvNS':    10}
    elif par == 'masked':
        contrasts = {'FvN':       1,
                     'MFvMN':     2,
                     'AvF':       3}
    #--------------------------------------------------------------------------#
    else:
        raise Exception('Paradigm \'%s\' not found' % par)


    contrasts_sig = {}
    contrasts_tstat = {}
    contrasts_con = {}
    for con in contrasts:
        if contrasts[con] < 10:
           pad = '0'
        else:
            pad = ''
	contrasts_sig[con] = 'spmP_00' + pad + str(contrasts[con]) + format
        contrasts_tstat[con] = 'spmT_00' + pad + str(contrasts[con]) + format 
        contrasts_con[con] = 'con_00' + pad + str(contrasts[con]) + format

    if type == 'P-map':
        return contrasts_sig
    elif type == 'T-map':
        return contrasts_sig
    elif type == 'con-img':
        return contrasts_con
    else:
        raise Exception('Image type \'%s\' \
	                not found: use \'T-map\', \'P-map\', or \'con-img\'' % type)


def Subjects(group='all',subject=None):
    """Group lists.  By default returns both patients and controls, but 
    can specify by passing either 'patients' or 'controls'
    
    Returns: list or dict
    """

    #--------------------------------------------------------------------------#
    subjects = {'control': 

                ['SAD_017','SAD_018','SAD_019','SAD_020','SAD_021',
                 'SAD_022','SAD_023','SAD_024','SAD_025','SAD_027',                     
                 'SAD_028','SAD_029','SAD_030','SAD_031','SAD_032',                     
                 'SAD_033','SAD_034','SAD_035','SAD_036','SAD_037',
                 'SAD_038','SAD_039','SAD_040','SAD_041','SAD_043',
                 'SAD_044','SAD_045','SAD_046','SAD_047','SAD_048',
                 'SAD_049','SAD_050'],

                'patient':

                ['SAD_P03','SAD_P04','SAD_P05','SAD_P06','SAD_P07',
                 'SAD_P08','SAD_P09','SAD_P10','SAD_P11','SAD_P12',
                 'SAD_P13','SAD_P14','SAD_P15','SAD_P16','SAD_P17',
                 'SAD_P18','SAD_P19','SAD_P20','SAD_P21','SAD_P22',
    	         'SAD_P23','SAD_P24','SAD_P25','SAD_P26','SAD_P27',
                 'SAD_P28','SAD_P29','SAD_P30','SAD_P31','SAD_P32',
	             'SAD_P33','SAD_P34','SAD_P35','SAD_P36','SAD_P37',
	             'SAD_P38','SAD_P39','SAD_P40','SAD_P41']}
    #--------------------------------------------------------------------------#

    for grp in subjects.keys():
        subjects[grp].sort()
	
    if subject:
        for grp in subjects.keys():
           if subject in subjects[grp]:
              return grp

    if group == 'all':
        all = []
	for grp in subjects.keys():
	    all = all + subjects[grp]
	return all
    elif group in subjects.keys():
        return subjects[group]
    elif group == 'groups':
        return subjects.keys()
    else:
        raise Exception('Group \'%s\' not found.' % group)

