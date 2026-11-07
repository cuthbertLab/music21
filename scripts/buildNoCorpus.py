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
import tarfile

from music21 import __version__ as version
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
