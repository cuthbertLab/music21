# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         dist.py
# Purpose:      Distribution and uploading script
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Builds various kinds of music21 distribution files and uploads them to PyPI and GoogleCode.

To do a release,

1. update the VERSION in _version.py and the single test cases in base.py.
2. for a major change, run
    `corpus.corpora.CoreCorpus().cacheMetadata()`.
    every once in a while run corpus.corpora.CoreCorpus().rebuildMetadataCache()
    (40 min on MacPro) -- either of these MAY change a lot of tests in corpus, metadata, etc.
    so don't skip the next step!
3. run test/warningMultiprocessTest.py for lowest and highest version -- fix all warnings!
4. run test/testLint.py and fix any lint errors
5. commit and then check test/testSingleCoreAll.py results on Travis-CI
     (normally not necessary, because it's slower and mostly duplicates multiprocessTest,
     but should be done before making a release).
6. then python3 test/testDocumentation.py [*]

[*] you will need pytest and nbval installed (along with ipython and jupyter)

7. run documentation/make.py clean
8. run documentation/make.py   [*]

[*] you will need sphinx, IPython (pip or easy_install), markdown, and pandoc (.dmg) installed

9. run documentation/upload.py [not via eclipse] or upload via ssh.
   -- you will need an MIT username and password 
   -- for each new major version ssh in and delete old files before uploading.

10. And finally this file. (from the command line; not as python -m...)

11. COMMIT to Github at this point w/ commit comment of the new version,
    then don't change anything until the next step is done.
    (.gitignore SHOULD avoid uploading the large files created here...)

12. Create a new release on GitHub and upload the TWO files created here. Use tag v2.0.1 (etc.).
    Don't forget the "v" in the release tag.
    Drag in this order: .tar.gz, no-corpus.tar.gz

    Finish this before doing the next step, even though it looks like it could be done in parallel.

13. Upload the new file with "twine upload music21-5.0.3a1.tar.gz" [*]

    [*] Requires twine to be installed

    You will need a file called ~/.pypirc with

        [distutils]
        index-servers =
            pypi

        [pypi]
        username:yourusername
        password:yourpassword

15. Delete the two .tar.gz files in dist...

16. Immediately increment the number in _version.py and run tests on it here
    to prepare for next release.

17. Announce on the blog, to the list, and twitter.

DO NOT RUN THIS ON A PC -- the Mac .tar.gz has an incorrect permission if you do.
'''
import hashlib
import os
import sys
import tarfile

from music21 import base
from music21 import common

from music21 import environment
environLocal = environment.Environment('..dist.dist')

PY = sys.executable
environLocal.warn("using python executable at %s" % PY)

class Distributor:
    def __init__(self):
        #self.fpEgg = None
        #self.fpWin = None
        self.fpTar = None

        self.buildNoCorpus = True
        #self.fpEggNoCorpus = None
        self.fpTarNoCorpus = None

        self.version = base.VERSION_STR

        self._initPaths()

    def _initPaths(self):

        # must be in the dist dir
        directory = os.getcwd()
        parentDir = os.path.dirname(directory)
        parentContents = os.listdir(parentDir)
        # make sure we are in the proper directory
        if (not directory.endswith("dist") or
            'music21' not in parentContents):
            raise Exception("not in the music21%dist directory: %s" % (os.sep, directory))

        self.fpDistDir = directory
        self.fpPackageDir = parentDir # dir with setup.py
        self.fpBuildDir = os.path.join(self.fpPackageDir, 'build')
        #self.fpEggInfo = os.path.join(self.fpPackageDir, 'music21.egg-info')

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
            #if self.version in fn and fn.endswith('.egg'):
            #    self.fpEgg = fp
#             if self.version in fn and fn.endswith('.exe'):
#                 fpNew = fp.replace('.macosx-10.8-intel.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.8-x86_64.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.9-intel.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.9-x86_64.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.10-intel.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.10-x86_64.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.11-intel.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.11-x86_64.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.12-intel.exe', '.win32.exe')
#                 fpNew = fpNew.replace('.macosx-10.12-x86_64.exe', '.win32.exe')
#                 if fpNew != fp:
#                     os.rename(fp, fpNew)
#                 self.fpWin = fpNew
            
            if self.version in fn and fn.endswith('.tar.gz'):
                self.fpTar = fp
            else:
                environLocal.warn(fn + ' does not end with .tar.gz')

        environLocal.warn('giving path for tar.gz')
        for fn in [self.fpTar]:
            if fn == None:
                environLocal.warn('missing fn path')
            else:
                environLocal.warn(fn)

    def removeCorpus(self, fp):
        '''
        Remove the corpus from a compressed file (.tar.gz) and
        create a new music21-noCorpus version.

        Return the completed file path of the newly created edition.

        NOTE: this function works only with Posix systems.
        '''
        TAR = 'TAR'
        #EGG = 'EGG'
        if fp.endswith('.tar.gz'):
            mode = TAR
            modeExt = '.tar.gz'
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

        # remove old dir if it exists
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

        #elif mode == EGG:
        #    os.system('mkdir %s' % fpDstDir)
        #    # need to create dst dir to unzip into
        #    tf = zipfile.ZipFile(fp, 'r')
        #    tf.extractall(path=fpDstDir)

        tf.close() # done after extraction

        # remove files, updates manifest
        for fn in common.getCorpusContentDirs():
            fp = os.path.join(fpDstDir, 'music21', 'corpus', fn)
            os.system('rm -r %s' % fp)

        fp = os.path.join(fpDstDir, 'music21', 'corpus', '_metadataCache')
        os.system('rm -r %s' % fp)


        # adjust the sources Txt file
        if mode == TAR:
            sourcesTxt = os.path.join(fpDstDir, 'music21.egg-info', 'SOURCES.txt')
        #elif mode == EGG:
        #    sourcesTxt = os.path.join(fpDstDir, 'EGG-INFO', 'SOURCES.txt')

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
        #elif mode == EGG:
        #    # zip and name with egg: give dst, then source
        #    cmd = 'cd %s; zip -r %s %s' % (fpDir, fnDst, fnDstDir)
        #    os.system(cmd)

        # remove directory that was compressed
        if os.path.exists(fpDstDir):
            # can use shutil.rmtree
            os.system('rm -r %s' % fpDstDir)

        return fpDst # full path with extension



    def build(self):
        '''
        Build all distributions. Update and rename file paths if necessary;
        remove extract build products.
        '''
        # call setup.py
        #import setup # -- for some reason does not work unless called from command line
        for buildType in [#'bdist_egg',
                          #'bdist_wininst',
                          'sdist --formats=gztar'
                          ]:
            environLocal.warn('making %s' % buildType)

            #setup.writeManifestTemplate(self.fpPackageDir)
            #setup.runDisutils(type)
            savePath = os.getcwd()
            os.chdir(self.fpPackageDir)
            os.system('%s setup.py %s' % (PY, buildType))
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
        #environLocal.warn('removing %s (except on windows...do it yourself)' % self.fpEggInfo)
        #os.system('rm -r %s' % self.fpEggInfo)
        environLocal.warn('removing %s (except on windows...do it yourself)' % self.fpBuildDir)
        os.system('rm -r %s' % self.fpBuildDir)

        if self.buildNoCorpus is True:
            # create no corpus versions
            self.fpTarNoCorpus = self.removeCorpus(fp=self.fpTar)
            #self.fpEggNoCorpus = self.removeCorpus(fp=self.fpEgg)


#     def uploadPyPi(self):
#         '''
#         Upload source package to PyPI -- currently source file is too big for PyPi...sigh...
#         '''
#         environLocal.warn(
#                'putting bdist_egg on pypi -- looks redundant, but we have to do it again')
#         savePath = os.getcwd()
#         os.chdir(self.fpPackageDir)
#         os.system('%s setup.py bdist_egg upload' % PY)
#         os.chdir(savePath)

        #os.system('cd %s; %s setup.py bdist_egg upload' %
        #        (self.fpPackageDir, PY))

    def md5ForFile(self, path, hexReturn=True):
        if hexReturn:
            return hashlib.md5(open(path, 'rb').read()).hexdigest()
        else:
            return hashlib.md5(open(path, 'rb').read()).digest()




#-------------------------------------------------------------------------------
if __name__ == '__main__':
    d = Distributor()
    d.buildNoCorpus = True
    d.build()
    d.updatePaths()
    #d.getMD5Path()
    #d.uploadPyPi()
