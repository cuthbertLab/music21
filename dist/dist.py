# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         dist.py
# Purpose:      Distribution and uploading script
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2021 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Builds various kinds of music21 distribution files and uploads them to PyPI and GoogleCode.

To do a release,

1. update the VERSION in _version.py and the single test cases in base.py.
2. run `corpus.corpora.CoreCorpus().cacheMetadata()`.
    for a major change run corpus.corpora.CoreCorpus().rebuildMetadataCache()
    (40 min on MacPro) -- either of these MAY change a lot of tests in corpus, metadata, etc.
    so don't skip the next step!
3. run test/warningMultiprocessTest.py for lowest and highest Py version -- fix all warnings!
4. run test/testLint.py and fix any lint errors (covered now by CI)
5. commit and then check test/testSingleCoreAll.py or wait for results on Github Actions
     (normally not necessary, because it's slower and mostly duplicates multiprocessTest,
     but should be done before making a release).
6. IMPORTANT: run python documentation/testDocumentation.py and afterwards fix errors [*]

[*] you will need pytest and nbval installed (along with ipython and jupyter), you cannot check
to see if fixed tests work while it is running.
This takes a while and runs single core, so allocate time.  Start working on
the announcement while it's running.

7. run documentation/make.py clean  (skip on minor version changes)
8. run documentation/make.py linkcheck  [*]
9. run documentation/make.py   [*]

[*] you will need sphinx, IPython (pip or easy_install), markdown, and pandoc (.dmg) installed

10. ssh to athena.dialup.mit.edu (yes, dialup!), cd music21/doc and rm -rf *  (skip on minor version changes)

11. run documentation/upload.py or upload via ssh.
   -- you will need an MIT username and password + a dual authentication passcode

12. zip up documentation/build/html and get ready to upload/delete it.
    Rename to music21.v.7.1.0-docs.zip (skip for Alpha/Beta)

12b. If any new file extensions have been added, be sure to add them to MANIFEST.in

13. And finally this file. (from the command line; not as python -m... OS 11+ needs sudo)

14. COMMIT to Github at this point w/ commit comment of the new version,
    then don't change anything until the next step is done.
    (.gitignore will avoid uploading the large files created here...)

15. Create a new release on GitHub and upload the TWO files created here and docs.
    Use tag v7.0.1 (etc.).
    Don't forget the "v" in the release tag.
    Drag in this order: .tar.gz, documentation, no-corpus.tar.gz

    Finish this before doing the next step, even though it looks like it could be done in parallel.

16. Upload the new file to PyPI with "twine upload music21-6.0.5a2.tar.gz" [*]

    [*] Requires twine to be installed

    You will need a file called ~/.pypirc with

        [distutils]
        index-servers =
            pypi

        [pypi]
        username:your_username
        password:your_password

17. Delete the two .tar.gz files in dist...

18. For starting a new major release create a GitHub branch for the old one.

19. Immediately increment the number in _version.py and run tests on it here
    to prepare for next release.

20. Announce on the blog, to the list, and twitter.

DO NOT RUN THIS ON A PC -- the Mac .tar.gz has an incorrect permission if you do.
'''
import hashlib
import os
import sys
import shutil
import tarfile

from music21 import base
from music21 import common

from music21 import environment
environLocal = environment.Environment('..dist.dist')

PY = sys.executable
environLocal.warn(f'using python executable at {PY}')

class Distributor:
    def __init__(self):
        # self.fpEgg = None
        # self.fpWin = None
        self.fpTar = None

        self.buildNoCorpus = True
        # self.fpEggNoCorpus = None
        self.fpTarNoCorpus = None

        self.version = base.VERSION_STR

        self._initPaths()

    def _initPaths(self):

        # must be in the dist dir
        directory = os.getcwd()
        parentDir = os.path.dirname(directory)
        parentContents = sorted(os.listdir(parentDir))
        # make sure we are in the proper directory
        if (not directory.endswith('dist')
                or 'music21' not in parentContents):
            raise Exception(f'not in the music21{os.sep}dist directory: {directory}')

        self.fpDistDir = directory
        self.fpPackageDir = parentDir  # dir with setup.py
        self.fpBuildDir = os.path.join(self.fpPackageDir, 'build')
        # self.fpEggInfo = os.path.join(self.fpPackageDir, 'music21.egg-info')

        sys.path.insert(0, parentDir)  # to get setup in as a possibility.

        for fp in [self.fpDistDir, self.fpPackageDir, self.fpBuildDir]:
            environLocal.warn(fp)


    def updatePaths(self):
        '''
        Process output of build scripts. Get most recently produced distributions.
        '''
        contents = sorted(os.listdir(self.fpDistDir))
        for fn in contents:
            fp = os.path.join(self.fpDistDir, fn)
            # if self.version in fn and fn.endswith('.egg'):
            #    self.fpEgg = fp
            # if self.version in fn and fn.endswith('.exe'):
            #     fpNew = fp.replace('.macosx-10.8-intel.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.8-x86_64.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.9-intel.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.9-x86_64.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.10-intel.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.10-x86_64.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.11-intel.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.11-x86_64.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.12-intel.exe', '.win32.exe')
            #     fpNew = fpNew.replace('.macosx-10.12-x86_64.exe', '.win32.exe')
            #     if fpNew != fp:
            #         os.rename(fp, fpNew)
            #     self.fpWin = fpNew

            print(fn)
            if self.version in fn and fn.endswith('.tar.gz'):
                self.fpTar = fp
            else:
                environLocal.warn(fn + ' does not end with .tar.gz')

        environLocal.warn('giving path for tar.gz')
        for fn in [self.fpTar]:
            if fn is None:
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
        # EGG = 'EGG'
        if fp and fp.endswith('.tar.gz'):
            mode = TAR
            modeExt = '.tar.gz'
        else:
            raise Exception('incorrect source file path')

        fpDir, fn = os.path.split(fp)

        # this has .tar.gz extension; this is the final completed package
        fnDst = fn.replace('music21', 'music21-noCorpus')
        fpDst = os.path.join(fpDir, fnDst)
        # remove file extensions
        fnDstDir = fnDst.replace(modeExt, '')
        fpDstDir = os.path.join(fpDir, fnDstDir)

        # get the name of the dir after decompression
        fpSrcDir = os.path.join(fpDir, fn.replace(modeExt, ''))

        # remove old dirs if it exists
        if os.path.exists(fpDst):
            shutil.rmtree(fpDst)

        if os.path.exists(fpDstDir):
            shutil.rmtree(fpDstDir)

        if mode == TAR:
            tf = tarfile.open(fp, "r:gz")
            # the path here is the dir into which to expand,
            # not the name of that dir
            tf.extractall(path=fpDir)
            os.system(f'mv {fpSrcDir} {fpDstDir}')
            tf.close()  # done after extraction

        # elif mode == EGG:
        #    os.system(f'mkdir {fpDstDir}')
        #    # need to create dst dir to unzip into
        #    tf = zipfile.ZipFile(fp, 'r')
        #    tf.extractall(path=fpDstDir)


        # remove files, updates manifest
        for fn in common.getCorpusContentDirs():
            fp = os.path.join(fpDstDir, 'music21', 'corpus', fn)
            shutil.rmtree(fp)

        fp = os.path.join(fpDstDir, 'music21', 'corpus', '_metadataCache')
        shutil.rmtree(fp)

        # adjust the sources Txt file
        # if mode == TAR:
        sourcesTxt = os.path.join(fpDstDir, 'music21.egg-info', 'SOURCES.txt')
        # else:
        #    raise Exception('invalid mode')

        # elif mode == EGG:
        #    sourcesTxt = os.path.join(fpDstDir, 'EGG-INFO', 'SOURCES.txt')

        # files will look like 'music21/corpus/haydn' in SOURCES.txt
        post = []
        f = open(sourcesTxt, 'r')
        corpusContentDirs = common.getCorpusContentDirs()
        for line in f:
            match = False
            if 'corpus' in line:
                for fn in corpusContentDirs:
                    # these are relative paths
                    fp = os.path.join('music21', 'corpus', fn)
                    if line.startswith(fp):
                        match = True
                        break
            if not match:
                post.append(line)
        f.close()
        f = open(sourcesTxt, 'w')
        f.writelines(post)
        f.close()

        if mode == TAR:
            # compress dst dir to dst file path name
            # need the -C flag to set relative dir
            # just name of dir
            cmd = f'tar -C {fpDir} -czf {fpDst} {fnDstDir}/'
            os.system(cmd)

        # remove directory that was compressed
        if os.path.exists(fpDstDir):
            shutil.rmtree(fpDstDir)

        return fpDst  # full path with extension



    def build(self):
        '''
        Build all distributions. Update and rename file paths if necessary;
        remove extract build products.
        '''
        # call setup.py
        # import setup  # -- for some reason does not work unless called from command line
        for buildType in ['sdist --formats=gztar']:
            environLocal.warn(f'making {buildType}')

            savePath = os.getcwd()
            os.chdir(self.fpPackageDir)
            os.system(f'{PY} setup.py {buildType}')
            os.chdir(savePath)

        self.updatePaths()

        environLocal.warn(f'removing {self.fpBuildDir} (except on windows...there do it yourself)')
        try:
            shutil.rmtree(self.fpBuildDir)
        except FileNotFoundError:
            environLocal.warn(
                'Directory was already cleaned up'
            )

        if self.buildNoCorpus is True:
            # create no corpus versions
            self.fpTarNoCorpus = self.removeCorpus(fp=self.fpTar)
            # self.fpEggNoCorpus = self.removeCorpus(fp=self.fpEgg)


    def md5ForFile(self, path, hexReturn=True):
        if hexReturn:
            return hashlib.md5(open(path, 'rb').read()).hexdigest()
        else:
            return hashlib.md5(open(path, 'rb').read()).digest()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    d = Distributor()
    d.buildNoCorpus = True
    d.build()
    d.updatePaths()
    # d.getMD5Path()
    # d.uploadPyPi()
