import os
#import pyroilut as lut
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.base import Bunch

class FreesurferAtlas(Bunch):

    def __init__(self, atlasdict, fsroidir, fssubjdir, **kwargs):
        
        self.atlasname = atlasdict['atlasname']
        self.fname = atlasdict['fname']
        self.space = atlasdict['space']
        self.regions = atlasdict['regions']
        if self.space == 'surface':
            self.hemi = atlasdict['hemi']

 #       self.lut = lut.freesurfer(self.fname)

        self.basedir = fsroidir
        self.subjdir = fssubjdir

        self.__dict__.update(**kwargs)

        
    def resample(self, par, subj, meanfuncimg):

        transform = fs.ApplyVolTransform()

        transform.inputs.targfile = os.path.join(self.subjdir,subj,self.fname)
        transform.inputs.sourcefile = meanfuncimg
        transform.inputs.tkreg = os.path.join(self.basedir,'reg',par,
                                              subj,'%s.dat' % self.atlasname)
        transform.inputs.inverse = True
        transform.inputs.interp = 'nearest'
        transform.inputs.outfile = os.path.join(self.basedir,'vol',par,
                                                subj,self.atlasname,
                                                '%s.mgz' % self.atlasname)

        print transform.cmdline
