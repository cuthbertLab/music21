# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         dist.py
# Purpose:      Distribution and uploading script
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2022 Michael Scott Asato Cuthbert
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
5. commit and then check test/testSingleCoreAll.py or wait for results on GitHub Actions
     (normally not necessary, because it's slower and mostly duplicates multiprocessTest,
     but should be done before making a release).
6. IMPORTANT: run python documentation/testDocumentation.py and afterwards fix errors [*]

[*] you will need pytest, docutils, nbval installed (along with ipython and jupyter), you cannot check
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

13. Run "hatch build" -- requires hatch to be installed "brew install hatch"

14. Run this file -- it builds the no-corpus version of music21.
    DO NOT RUN THIS ON A PC -- the Mac .tar.gz might have an incorrect permission if you do.

15. COMMIT to GitHub at this point w/ commit comment of the new version,
    then don't change anything until the next step is done.
    (.gitignore will avoid uploading the large files created here...)

16. Tag the commit: git tag -a vX.Y.Z -m "music21 vX.Y.Z"
    Don't forget the "v" in the release tag.
    Sanity check that the correct commit was tagged: git log

17. Push tags: git push --tags  (or git push upstream --tags if not on main branch)

18. Create a new release on GitHub and upload the TWO non-wheel files created here and docs.
    Drag in this order: .tar.gz, documentation, no-corpus.tar.gz

    Finish this before doing the next step, even though it looks like it could be done in parallel.

19. Upload the new file to PyPI with "twine upload music21-7.3.5a2.tar.gz" [*]

    [*] Requires twine to be installed

    You will need a file called ~/.pypirc with

        [distutils]
        index-servers =
            pypi

        [pypi]
        username:your_username
        password:your_password

20. Delete the two .tar.gz files in dist...

21. For starting a new major release create a GitHub branch for the old one.

22. Immediately increment the number in _version.py and run tests on it here
    to prepare for next release.

23. Announce on the blog, to the list, and twitter.
'''
import os
import shutil
import tarfile

from music21._version import __version__ as version
from music21.common.pathTools import getRootFilePath, getCorpusContentDirs

def removeCorpus():
    '''
    Remove the corpus from a compressed file (.tar.gz) and
    create a new music21-noCorpus version.

    Return the completed file path of the newly created edition.

    NOTE: this function works only with Posix systems.
    '''
    fp = getRootFilePath() / 'dist' / ('music21-' + version + '.tar.gz')
    fpDir, fn = os.path.split(str(fp))

    # this has .tar.gz extension; this is the final completed package
    fnDst = fn.replace('music21', 'music21-noCorpus')
    fpDst = os.path.join(fpDir, fnDst)
    # remove file extensions
    fnDstDir = fnDst.replace('.tar.gz', '')
    fpDstDir = os.path.join(fpDir, fnDstDir)

    file = tarfile.open(fp)
    file.extractall(fpDir)
    file.close()

    os.rename(fpDstDir.replace('-noCorpus', ''), fpDstDir)

    # remove files, updates manifest
    for fn in getCorpusContentDirs():
        fp = os.path.join(fpDstDir, 'music21', 'corpus', fn)
        shutil.rmtree(fp)

    fp = os.path.join(fpDstDir, 'music21', 'corpus', '_metadataCache')
    shutil.rmtree(fp)

    # compress dst dir to dst file path name
    # need the -C flag to set relative dir
    # just name of dir
    cmd = f'tar -C {fpDir} -czf {fpDst} {fnDstDir}/'
    os.system(cmd)

    # # remove directory that was compressed
    if os.path.exists(fpDstDir):
        shutil.rmtree(fpDstDir)

    return fpDst  # full path with extension


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    removeCorpus()
