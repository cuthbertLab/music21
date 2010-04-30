#-----------------------------------------------------------------||||||||||||--
# Name:          dist.py
# Purpose:       Distribution and uploading script
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import os, sys
from music21 import base
import googlecode_upload # placed in site-packages

from music21 import environment
_MOD = 'dist.py'
environLocal = environment.Environment(_MOD)



class Distributor(object):
    def __init__(self):
        self.fpEgg = None
        self.fpWin = None
        self.fpTar = None
        self._initPaths()
        self.version = base.VERSION_STR

    def _initPaths(self):

        # must be in the dist dir
        self.dir = os.getcwd()
        self.parentDir = os.path.dirname(self.dir)
        parentContents = os.listdir(self.parentDir)
        # make sure we are in the the proper directory
        if (not self.dir.endswith("dist") or 
            'music21' not in parentContents):
            raise Exception("not in the music21%dist directory: %s" % (os.sep, self.dir))
    
        self.fpDistDir = self.dir
        

    def _updatePaths(self):
        '''get most recently produced distributions.
        '''
        contents = os.listdir(self.fpDistDir)
        for fn in contents:
            fp = os.path.join(self.fpDistDir, fn)
            if self.version in fn and fn.endswith('.egg'):
                self.fpEgg = fp
            elif self.version in fn and fn.endswith('.exe'):
                fpNew = fp.replace('.macosx-10.3-fat.exe', '.exe')
                os.rename(fp, fpNew)
                self.fpWin = fpNew
            elif self.version in fn and fn.endswith('.tar.gz'):
                self.fpTar = fp

        for fn in [self.fpEgg, self.fpWin, self.fpTar]:
            if fn == None:
                environLocal.warn('missing fn path')
            environLocal.warn(fn)


    def build(self):
        os.system('cd %s; python setup.py sdist' % fpPackageDir)
        self._updatePaths()


    def _uploadGoogleCode(self, fp):
        summary = self.version
        project = 'music21'
        user = 'christopher.ariza'

        if fp.endswith('.tar.gz'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
    
        print(['starting GoogleCode upload of:', fp])
        status, reason, url = googlecode_upload.upload_find_auth(fp, 
                        project, summary, labels, user)
        print([status, reason])

    def upload(self):    
        for fp in [self.fpTar]:
            self._uploadGoogleCode(fp)


if __name__ == '__main__':
    a = Distributor()
    a.build()
    a.upload()