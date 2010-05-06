#-------------------------------------------------------------------------------
# Name:          dist.py
# Purpose:       Distribution and uploading script
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
#-------------------------------------------------------------------------------

import os, sys
from music21 import base

from music21 import environment
_MOD = 'dist.py'
environLocal = environment.Environment(_MOD)



class Distributor(object):
    def __init__(self):
        self.fpEgg = None
        self.fpWin = None
        self.fpTar = None
        self.version = base.VERSION_STR

        self._initPaths()

    def _initPaths(self):

        # must be in the dist dir
        dir = os.getcwd()
        parentDir = os.path.dirname(dir)
        parentContents = os.listdir(parentDir)
        # make sure we are in the the proper directory
        if (not dir.endswith("dist") or 
            'music21' not in parentContents):
            raise Exception("not in the music21%dist directory: %s" % (os.sep, dir))
    
        self.fpDistDir = dir
        self.fpPackageDir = parentDir # dir with setup.py
        self.fpBuildDir = os.path.join(self.fpPackageDir, 'build')
        self.fpEggInfo = os.path.join(self.fpPackageDir, 'music21.egg-info')

        for fp in [self.fpDistDir, self.fpPackageDir, self.fpBuildDir]:
            environLocal.warn(fp)


    def _updatePaths(self):
        '''Process output of build scripts. Get most recently produced distributions.
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
            else:
                environLocal.warn(fn)


    def build(self):
        '''Build all distributions. Update and rename file paths if necessary; remove extract build produts.
        '''
        # call setup.py
        os.system('cd %s; python setup.py bdist_egg' % self.fpPackageDir)
        os.system('cd %s; python setup.py bdist_wininst' % 
                    self.fpPackageDir)
        os.system('cd %s; python setup.py sdist' % 
                    self.fpPackageDir)

        #os.system('cd %s; python setup.py sdist' % self.fpPackageDir)
        self._updatePaths()

        # remove build dir, egg-info dir
        environLocal.warn('removing %s' % self.fpEggInfo)
        os.system('rm -r %s' % self.fpEggInfo)
        environLocal.warn('removing %s' % self.fpBuildDir)
        os.system('rm -r %s' % self.fpBuildDir)




    def _uploadPyPi(self):
        '''Upload source package to PyPI
        '''
        os.system('cd %s; python setup.py bdist_egg upload' % 
                self.fpPackageDir)

    def _uploadGoogleCode(self, fp):
        '''Upload distributions to Google code. Requires googlecode_upload.py script from: 
        http://code.google.com/p/support/source/browse/trunk/scripts/googlecode_upload.py
        '''
        import googlecode_upload # placed in site-packages

        summary = self.version
        project = 'music21'
        user = 'christopher.ariza'

        if fp.endswith('.tar.gz'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
        elif fp.endswith('.exe'):
            labels = ['OpSys-Windows', 'Featured', 'Type-Installer']
        elif fp.endswith('.egg'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
        
        print(['starting GoogleCode upload of:', fp])
        status, reason, url = googlecode_upload.upload_find_auth(fp, 
                        project, summary, labels, user)
        print([status, reason])


    def upload(self):
        '''Perform all uploads.
        '''
        self._uploadPyPi()
        for fp in [self.fpTar, self.fpEgg, self.fpWin]:
            self._uploadGoogleCode(fp)



#-------------------------------------------------------------------------------
if __name__ == '__main__':
    a = Distributor()
    a.build()
    a.upload()