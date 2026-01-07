# ------------------------------------------------------------------------------
# Name:         dist.py
# Purpose:      Distribution and uploading script
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2025 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Builds various kinds of music21 distribution files and uploads them to PyPI and GoogleCode.

To do a release,

1. update the VERSION in _version.py and the single test case in base.py.
2. run `corpus.corpora.CoreCorpus().cacheMetadata()`.
    for a major change that affects parsing run corpus.corpora.CoreCorpus().rebuildMetadataCache()
    (2 min on M4) -- either of these MAY change a
    lot of tests in corpus, metadata, etc. so don't skip the next step!
3. IMPORTANT: run python documentation/testDocumentation.py and afterwards fix errors [*]

[*] you will need pytest, docutils, nbval installed (along with ipython and jupyter),
you cannot check to see if fixed tests work while it is running.
This takes a while and runs single core, and then almost always needs code patches
so allocate time (2 min on M4).  Start working on the announcement while it's running.

4. run test/warningMultiprocessTest.py for lowest and highest Py version -- fix all warnings!
5. run `from music21.test import treeYield
    and then run `treeYield.find_all_non_hashable_m21objects()` and check that the set returned is
    empty.  Note -- it will print a bunch of module names, but only the final set matters.
    Then do the same for `treeYield.find_all_non_default_instantiation_m21objects()`.
6. commit and wait for results on GitHub Actions
     (normally not necessary, because it's slower and mostly duplicates multiprocessTest,
     but should be done before making a release).

7. run documentation/make.py clean  (skip on minor version changes) -- you may need to make a
     documentation/build directory first.
8. run documentation/make.py linkcheck  [*]
     some persistent errors that actually work are in the conf.py file under linkcheck_ignore
9. run documentation/make.py   [*]

[*] you will need sphinx, Jupyter (pip or easy_install), markdown, and pandoc (.dmg) installed

10. move music21 documentation/build/html to music21.org/music21docs/
    via Amazon S3 (contact MSAC for authentication if need be) (MSAC has a program:
    combine_sync/deploy.py that will do this automatically.

11. zip up documentation/build/html and get ready to upload/delete it (you can put on your
    desktop or wherever you like).
    Rename to music21-9.5.0-docs.zip (skip for Alpha/Beta)

12. From the music21 main folder (not subfolder) run "hatch build" --
    requires hatch to be installed "pip install hatch" -- brew version of hatch
    was giving Environment `default` is incompatible messages recently. (mysql? why relevant?)

    This builds the dist/music21-9.3.0.tar.gz and dist/music21-9.3.0-py3-none-any.whl
    files.  That used to be what *this* script did, but now hatch does it better!

13. Run this (dist.py) file: it builds the no-corpus version of music21.
    (need Python 3.12 or higher)
    DO NOT RUN THIS ON A PC or the Mac .tar.gz might have an incorrect permission if you do.

14. PR and Commit to GitHub at this point w/ commit comment of the new version,
    then don't change anything until the next step is done.  Merge to main/master
    (.gitignore will avoid uploading the large files created here.)

15. Switch back to master/main branch (or whatever main version we are releasing)

16. Tag the commit: git tag -a vX.Y.Z -m "music21 vX.Y.Z"
    Don't forget the "v" in the release tag.
    Sanity check that the correct commit was tagged: git log

17. Push tags: git push --tags

18. Create a new release on GitHub (using the tag just created) and upload the
    non-wheel files created here and docs.

    Drag in this order: .tar.gz, -docs.zip, no-corpus.tar.gz

    Finish this before doing the next step, even though it looks like it could be done in parallel.

19a. Upload the tar.gz file to PyPI with "twine upload music21-9.3.0.tar.gz" [*]

19b. Do the same for the whl file (but not for the no-corpus file) [*]

    [*] Requires twine to be installed and up-to-date (pip install --upgrade twine)

    You will need a file called ~/.pypirc with

        [distutils]
        index-servers =
            pypi

        [pypi]
        username:__token__
        password:pypi-API_TOKEN

    The "password" is the API token you've just created -- if you lose the file you
    will also lose the API token. and have to create it again.  This is all very
    poorly documented.  This is Not the "Unique identifier" that you see in the
    "API Tokens" tab on the "Your Account" page -- super confusing.

20. Delete the two .tar.gz files and .whl file in dist. (and the docs)

21. For starting a new major release create a GitHub branch to preserve the old one
    for patches, etc. esp. during beta releases.

22. Immediately increment the number in _version.py and run tests on it here
    to prepare for next release.

23. Announce on the blog and to the list.
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
    file.extractall(fpDir, filter='data')  # note -- this requires 3.12+ but that's okay
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
