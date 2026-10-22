# ------------------------------------------------------------------------------
# Name:         dist.py
# Purpose:      Distribution and uploading script
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2026 Michael Scott Asato Cuthbert
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
3. IMPORTANT: `uv run documentation/testDocumentation.py` and afterwards fix errors [*]

[*] `uv sync` installs pytest, docutils, nbval, ipython, and jupyter.
You cannot check to see if fixed tests work while it is running.
This takes a while and runs single core, and then almost always needs code patches
so allocate time (2 min on M4).  Start working on the announcement while it's running.
Cannot run 2 and 3 in parallel, since often metadata changes cause documentation changes.

* developerReference/musicxmlTest - 41b and 41c are currently failing and acceptable.
* usersGuide_22_graphing 3dbars sometimes returns 1, sometimes 2 Axes.  It should just do one...

4. `uv run music21/test/warningMultiprocessTest.py` for lowest and highest Py
    version -- fix all warnings!
5. run `from music21.test import treeYield
    and then run `treeYield.find_all_non_hashable_m21objects()` and check that the set returned is
    empty.  Note -- it will print a bunch of module names, but only the final `set()`
    being empty matters.
    (You can also check to see if
    `treeYield.find_all_non_default_instantiation_m21objects()` looks sane.
    If that one isn't empty it is not a bug, and v11 will make some M21 objects require
    arguments (such as VoiceLeadingQuartet)
6. commit and wait for results on GitHub Actions
     (normally not necessary, because it's slower and mostly duplicates multiprocessTest,
     but should be done before making a release).
7. `uv run documentation/make.py clean`  (skip on minor version changes) -- you may need to make a
     documentation/build directory first.
8. `uv run documentation/make.py linkcheck`  [*]
     some persistent errors that actually work are in the conf.py file under linkcheck_ignore
     note that since AI-Agent world, more and more links are being blocked from bot checking.
9. `uv run documentation/make.py`   [*]

[*] `uv sync` installs sphinx and Jupyter; you will also need markdown and pandoc (.dmg)

10. move music21 documentation/build/html to music21.org/music21docs/
    via Amazon S3 (contact MSAC for authentication if need be)
    Two ways to do this:
    * `uv run documentation/upload.py`
    * or MSAC has a program combine_sync/deploy.py that will do this automatically
      when he updates the site.

11. zip up documentation/build/html and get ready to upload/delete it (you can put on your
    desktop or wherever you like).
    Rename to music21-11.1.0-docs.zip (skip for Alpha/Beta)

12. From the music21 main folder (not subfolder) run "uvx hatch build".

    This builds the dist/music21-11.1.0.tar.gz and dist/music21-11.1.0-py3-none-any.whl
    files.  That used to be what *this* script did, but now hatch does it better!

13. Run this (dist.py) file with `uv run dist/dist.py`: it builds the no-corpus version of music21.

14. PR and Commit to GitHub at this point w/ commit comment of the new version,
    then don't change anything until the next step is done.  Merge to main/master
    (.gitignore will avoid uploading the large files created here.)

15. Switch back to master/main branch (or whatever main version we are releasing)

16. Tag the commit: git tag -a vX.Y.Z -m "music21 vX.Y.Z"
    Don't forget the "v" in the release tag.
    Sanity check that the correct commit was tagged: git log

17. Push that tag: git push origin vX.Y.Z

18. Create a new release on GitHub (using the tag just created) and upload the
    non-wheel files created here and docs.

    Drag in this order: .tar.gz (wait to finish), -docs.zip (wait), no-corpus.tar.gz

    Finish this before doing the next step, even though it looks like it could be done in parallel.

19a. Upload the tar.gz file to PyPI with "uvx twine upload music21-11.1.0.tar.gz" [*]

19b. Do the same for the whl file (but not for the no-corpus file) [*]

    [*] You will need a file called ~/.pypirc with

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
import tarfile

from music21._version import __version__ as version
from music21.common.pathTools import getRootFilePath, getCorpusContentDirs

def removeCorpus():
    '''
    Remove the corpus from a compressed file (.tar.gz) and
    create a new music21-noCorpus version.

    Return the completed file path of the newly created edition.
    '''
    distDir = getRootFilePath() / 'dist'
    srcName = 'music21-' + version
    dstName = 'music21-noCorpus-' + version
    fpDst = distDir / (dstName + '.tar.gz')
    corpusPrefixes = tuple(
        f'{srcName}/music21/corpus/{d}/'
        for d in [*getCorpusContentDirs(), '_metadataCache']
    )

    # iterating over tar "members" rather than files/filenames in order to preserve
    # the permissions etc. that the original hatch build set
    with (tarfile.open(distDir / (srcName + '.tar.gz')) as src,
          tarfile.open(fpDst, 'w:gz') as dst):
        for member in src:
            if member.name.startswith(corpusPrefixes):
                continue
            fileObj = src.extractfile(member) if member.isfile() else None
            member.name = dstName + member.name[len(srcName):]
            if 'path' in member.pax_headers:
                # long paths (over 100 characters) and non-ASCII names store a short name
                # in the tar and the longer name in this "path" header -- but it will be
                # inaccurate in the new tar (because of the added "noCorpus-" in the path).
                # Deleting this header will make the dst tar file regenerate it.
                del member.pax_headers['path']
            dst.addfile(member, fileObj)

    return fpDst


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    removeCorpus()
