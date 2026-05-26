# ------------------------------------------------------------------------------
# Name:         buildNoCorpus.py
# Purpose:      Build the no-corpus music21 distribution (.tar.gz)
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Build the "no-corpus" edition of music21: take a built `.tar.gz` and
strip out the corpus (which carries licenses such as
CC-SA or old copyrighted files are not fully public domain in the entire world
like music from 1935 but in Mexico and other life+100 countries)
to produce a `music21-noCorpus-*.tar.gz` suitable for Linux distros that
require a fully PD package.

Part of `RELEASING.md` at the repository root::

    uv run scripts/buildNoCorpus.py

This file and `removeCorpus()` were reorganized out of the old `dist/dist.py`.
'''
import os
import shutil
import tarfile

from music21 import __version__ as version
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

    with tarfile.open(fp) as file:
        file.extractall(fpDir, filter='data')  # note -- this requires 3.12+ but that's okay

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
