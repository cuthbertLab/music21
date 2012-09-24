# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         dist.py
# Purpose:      Distribution and uploading script
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''
Builds various kinds of music21 distribution files and uploads them to PyPI and GoogleCode.

To do a release, first run test/multiprocessTest.py then test/test.py (normally not necessary,
because it's slower and mostly duplicates multiprocessTest, but should be done before making
a release), then test/testDocumentation, test/testSerialization, and test/testStream.

If all tests pass, run `corpus.cacheMetadata('core')`, buildDoc/build, buildDoc/upload, and
finally this file.
'''


import os, sys, tarfile, zipfile

from music21 import base
from music21 import common

from music21 import environment
_MOD = 'dist.py'
environLocal = environment.Environment(_MOD)


'''
Build and upload music21 in three formats: egg, exe, and tar.

Simply call from the command line.
'''

PY = sys.executable
environLocal.warn("using python executable at %s" % PY)

class Distributor(object):
    def __init__(self):
        self.fpEgg = None
        self.fpWin = None
        self.fpTar = None

        self.buildNoCorpus = True
        self.fpEggNoCorpus = None
        self.fpTarNoCorpus = None

        self.version = base.VERSION_STR

        self._initPaths()

    def _initPaths(self):

        # must be in the dist dir
        directory = os.getcwd()
        parentDir = os.path.dirname(directory)
        parentContents = os.listdir(parentDir)
        # make sure we are in the the proper directory
        if (not directory.endswith("dist") or 
            'music21' not in parentContents):
            raise Exception("not in the music21%dist directory: %s" % (os.sep, directory))
    
        self.fpDistDir = directory
        self.fpPackageDir = parentDir # dir with setup.py
        self.fpBuildDir = os.path.join(self.fpPackageDir, 'build')
        self.fpEggInfo = os.path.join(self.fpPackageDir, 'music21.egg-info')

        sys.path.insert(0, parentDir)  # to get setup in as a possibility.

        for fp in [self.fpDistDir, self.fpPackageDir, self.fpBuildDir]:
            environLocal.warn(fp)


    def updatePaths(self):
        '''
        Process output of build scripts. Get most recently produced distributions.
        '''
        contents = os.listdir(self.fpDistDir)
        for fn in contents:
            fp = os.path.join(self.fpDistDir, fn)
            if self.version in fn and fn.endswith('.egg'):
                self.fpEgg = fp
            elif self.version in fn and fn.endswith('.exe'):
                fpNew = fp.replace('.macosx-10.6-intel.exe', '.exe')
                fpNew = fpNew.replace('.macosx-10.7-x86_64.exe', '.exe')
                fpNew = fpNew.replace('.macosx-10.8-x86_64.exe', '.exe')
                if fpNew != fp:
                    os.rename(fp, fpNew)
                self.fpWin = fpNew
            elif self.version in fn and fn.endswith('.tar.gz'):
                self.fpTar = fp

        environLocal.warn('giving paths for egg, exe, and tar.gz/zip, respectively:')
        for fn in [self.fpEgg, self.fpWin, self.fpTar]:
            if fn == None:
                environLocal.warn('missing fn path')
            else:
                environLocal.warn(fn)   
    
    def removeCorpus(self, fp):
        '''Remove the corpus from a compressed file (.tar.gz or .egg) and create a new music21-noCorpus version.

        Return the completed file path of the newly created edition.
    
        NOTE: this function works only with Posix systems. 
        '''
        TAR = 'TAR'
        EGG = 'EGG'
        if fp.endswith('.tar.gz'):
            mode = TAR
            modeExt = '.tar.gz'
        elif fp.endswith('.egg'):
            mode = EGG
            modeExt = '.egg'
        else:
            raise Exception('incorrect source file path')
    
        fpDir, fn = os.path.split(fp)
    
        # this has .tar.gz extension; this is the final completed package
        fnDst = fn.replace('music21', 'music21-noCorpus')
        fpDst = os.path.join(fpDir, fnDst)
        # remove file extnesions
        fnDstDir = fnDst.replace(modeExt, '')
        fpDstDir = os.path.join(fpDir, fnDstDir)
        
        # get the name of the dir after decompression
        fpSrcDir = os.path.join(fpDir, fn.replace(modeExt, ''))
            
        # remove old dir if ti exists
        if os.path.exists(fpDst):
            # can use shutil.rmtree
            os.system('rm -r %s' % fpDst)
        if os.path.exists(fpDstDir):
            # can use shutil.rmtree
            os.system('rm -r %s' % fpDstDir)
    
        if mode == TAR:
            tf = tarfile.open(fp, "r:gz")
            # the path here is the dir into which to expand, 
            # not the name of that dir
            tf.extractall(path=fpDir)
            os.system('mv %s %s' % (fpSrcDir, fpDstDir))
    
        elif mode == EGG:
            os.system('mkdir %s' % fpDstDir)
            # need to create dst dir to unzip into
            tf = zipfile.ZipFile(fp, 'r')
            tf.extractall(path=fpDstDir)
    
        tf.close() # done after extraction
    
        # remove files, updates manifest
        for fn in common.getCorpusContentDirs():
            fp = os.path.join(fpDstDir, 'music21', 'corpus', fn)
            os.system('rm -r %s' % fp)
    
        # adjust the sources Txt file
        if mode == TAR:
            sourcesTxt = os.path.join(fpDstDir, 'music21.egg-info', 'SOURCES.txt')
        elif mode == EGG:
            sourcesTxt = os.path.join(fpDstDir, 'EGG-INFO', 'SOURCES.txt')
    
        # files will look like 'music21/corpus/haydn' in SOURCES.txt
        post = []
        f = open(sourcesTxt, 'r')
        corpusContentDirs = common.getCorpusContentDirs()
        for l in f:
            match = False
            if 'corpus' in l:
                for fn in corpusContentDirs:
                    # these are relative paths
                    fp = os.path.join('music21', 'corpus', fn)
                    if l.startswith(fp):
                        match = True
                        break
            if not match: 
                post.append(l)
        f.close()
        f = open(sourcesTxt, 'w')
        f.writelines(post)
        f.close()
    
        if mode == TAR:
            # compress dst dir to dst file path name
            # need the -C flag to set relative dir
            # just name of dir
            cmd = 'tar -C %s -czf %s %s/' % (fpDir, fpDst, fnDstDir) 
            os.system(cmd)
        elif mode == EGG:
            # zip and name with egg: give dst, then source
            cmd = 'cd %s; zip -r %s %s' % (fpDir, fnDst, fnDstDir) 
            os.system(cmd)
    
        # remove directory that was compressed
        if os.path.exists(fpDstDir):
            # can use shutil.rmtree
            os.system('rm -r %s' % fpDstDir)

        return fpDst # full path with extension
    


    def build(self):
        '''Build all distributions. Update and rename file paths if necessary; remove extract build produts.
        '''
        # call setup.py
        #import setup -- for some reason doesnt work unless called from commandline
        for buildType in ['bdist_egg', 'bdist_wininst', 'sdist --formats=gztar']:    
                environLocal.warn('making %s' % buildType)

                #setup.writeManifestTemplate(self.fpPackageDir)
                #setup.runDisutils(type)
                savePath = os.getcwd()
                os.chdir(self.fpPackageDir)
                os.system('%s setup.py %s' % 
                            (PY, buildType))
                os.chdir(savePath)

#        os.system('cd %s; %s setup.py bdist_egg' % (self.fpPackageDir, PY))
#        os.system('cd %s; %s setup.py bdist_wininst' % 
#                    (self.fpPackageDir, PY))
#        os.system('cd %s; %s setup.py sdist' % 
#                    (self.fpPackageDir, PY))

        #os.system('cd %s; python setup.py sdist' % self.fpPackageDir)
        self.updatePaths()
        #exit()
        # remove build dir, egg-info dir
        environLocal.warn('removing %s (except on windows...do it yourself)' % self.fpEggInfo)
        os.system('rm -r %s' % self.fpEggInfo)
        environLocal.warn('removing %s (except on windows...do it yourself)' % self.fpBuildDir)
        os.system('rm -r %s' % self.fpBuildDir)

        if self.buildNoCorpus is True:
            # create no corpus versions
            self.fpTarNoCorpus = self.removeCorpus(fp=self.fpTar)
            self.fpEggNoCorpus = self.removeCorpus(fp=self.fpEgg)


    def uploadPyPi(self):
        '''
        Upload source package to PyPI
        '''
        environLocal.warn('putting bdist_egg on pypi -- looks redundant, but we have to do it again')
        savePath = os.getcwd()
        os.chdir(self.fpPackageDir)
        os.system('%s setup.py bdist_egg upload' % PY)
        os.chdir(savePath)

        #os.system('cd %s; %s setup.py bdist_egg upload' % 
        #        (self.fpPackageDir, PY))

    def uploadGoogleCodeOneFile(self, fp):
        '''Upload distributions to Google code. Requires googlecode_upload.py script from: 
        http://code.google.com/p/support/source/browse/trunk/scripts/googlecode_upload.py
        '''
        import googlecode_upload # placed in site-packages

        summary = self.version
        project = 'music21'
        user = 'cuthbert@gmail.com'

        if fp.endswith('.tar.gz'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
        elif fp.endswith('.exe'):
            labels = ['OpSys-Windows', 'Featured', 'Type-Installer']
        elif fp.endswith('.egg'):
            labels = ['OpSys-All', 'Featured', 'Type-Archive']
        
        print(['starting GoogleCode upload of:', fp])
        status, reason, unused_url = googlecode_upload.upload_find_auth(fp, 
                        project, summary, labels, user)
        print([status, reason])


    def uploadGoogleCode(self):
        '''
        Upload each file to googleCode.
        '''
#         for fp in [self.fpTar, self.fpEgg, self.fpWin, 
#             self.fpTarNoCorpus, self.fpEggNoCorpus]:
        if self.buildNoCorpus is True:
            fileList = [self.fpEggNoCorpus, self.fpTarNoCorpus, self.fpWin, 
                    self.fpEgg, self.fpTar]
        else:
            fileList = [self.fpWin, self.fpEgg, self.fpTar]
        
        for fp in fileList:
            self.uploadGoogleCodeOneFile(fp)





    


#-------------------------------------------------------------------------------
if __name__ == '__main__':
    d = Distributor()
    d.buildNoCorpus = False
    d.build()
    d.updatePaths()
    d.uploadGoogleCode(d.fpTar)
    #d.uploadPyPi()