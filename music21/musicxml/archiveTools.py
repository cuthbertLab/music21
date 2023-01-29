# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         musicxml/archiveTools.py
# Purpose:      Tools for compressing and decompressing MusicXML files
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009, 2017-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Tools for compressing and decompressing musicxml files.
'''
from __future__ import annotations

import os
import pathlib
import zipfile

from music21 import common
from music21 import environment

environLocal = environment.Environment('musicxml.archiveTools')


# -----------------------------------------------------------------------------
# compression


def compressAllXMLFiles(*, deleteOriginal=False):
    '''
    Takes all filenames in corpus.paths and runs
    :meth:`music21.musicxml.archiveTools.compressXML` on each.  If the musicXML files are
    compressed, the originals are deleted from the system.
    '''
    from music21.corpus.corpora import CoreCorpus
    environLocal.warn('Compressing musicXML files...')

    # this gets all .xml, .musicxml, .mxl etc.
    for filename in CoreCorpus().getPaths(fileExtensions=('.xml',)):
        compressXML(filename, deleteOriginal=deleteOriginal)
    environLocal.warn(
        'Compression complete. '
        'Run the main test suite, fix bugs if necessary,'
        'and then commit modified directories in corpus.'
    )


def compressXML(filename: str | pathlib.Path,
                *,
                deleteOriginal=False,
                silent=False,
                strictMxlCheck=True) -> bool:
    '''
    Takes a filename, and if the filename corresponds to a musicXML file with
    an .musicxml or .xml extension, creates a corresponding compressed .mxl file in the same
    directory.

    If deleteOriginal is set to True, the original musicXML file is deleted
    from the system.

    If strictMxlCheck is False then any suffix will do.

    Returns bool if successful.
    '''
    filename = str(filename)
    if strictMxlCheck and not filename.endswith('.xml') and not filename.endswith('.musicxml'):
        return False  # not a musicXML file
    fp = common.pathTools.cleanpath(filename, returnPathlib=True)
    if not silent:  # pragma: no cover
        environLocal.warn(f'Updating file: {fp}')
    newFilename = str(fp.with_suffix('.mxl'))


    # contents of container.xml file in META-INF folder
    container = f'''<?xml version="1.0" encoding="UTF-8"?>
<container>
  <rootfiles>
    <rootfile full-path="{fp.name}"/>
  </rootfiles>
</container>
    '''
    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(
            newFilename,
            'w',
            compression=zipfile.ZIP_DEFLATED,
    ) as myZip:
        myZip.write(filename, fp.name)
        myZip.writestr(
            'META-INF' + os.path.sep + 'container.xml',
            container,
        )
    # Delete uncompressed xml file from system
    if deleteOriginal:
        fp.unlink()

    return True


def uncompressMXL(filename: str | pathlib.Path,
                  *,
                  deleteOriginal=False,
                  strictMxlCheck=True) -> bool:
    '''
    Takes a filename, and if the filename corresponds to a compressed musicXML
    file with an .mxl extension, creates a corresponding uncompressed .musicxml file
    in the same directory.

    If deleteOriginal is set to True, the original compressed musicXML file is
    deleted from the system.

    If strictMxlCheck is False then any type of file will attempt to be extracted.

    Returns bool if successful.
    '''
    filename = str(filename)
    if not filename.endswith('.mxl') and strictMxlCheck:
        return False  # not a compressed musicXML file

    fp: pathlib.Path = common.pathTools.cleanpath(filename, returnPathlib=True)
    environLocal.warn(f'Updating file: {fp}')
    extractPath = str(fp.parent)
    unarchivedName = fp.with_suffix('.musicxml').name
    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(filename, 'r', compression=zipfile.ZIP_DEFLATED) as myZip:
        try:
            myZip.extract(member=unarchivedName, path=extractPath)
        except KeyError:
            try:
                unarchivedName = unarchivedName.replace('.xml', '.musicxml')
                myZip.extract(member=unarchivedName, path=extractPath)
            except KeyError:
                found_one_file = False
                for storedName in myZip.namelist():
                    if 'META-INF' in storedName:
                        continue
                    myZip.extract(member=storedName, path=extractPath)
                    if not found_one_file:
                        # only rename one file...hope it is the right one.
                        extractPath_pathlib = pathlib.Path(extractPath)
                        wrongName = extractPath_pathlib / storedName
                        correctName = extractPath_pathlib / unarchivedName
                        wrongName.rename(correctName)
                        found_one_file = True

    # Delete uncompressed xml file from system
    if deleteOriginal:
        fp.unlink()
    return True


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 1:
        for xmlName in sys.argv[1:]:
            if xmlName.endswith('.xml'):
                compressXML(xmlName)
            elif xmlName.endswith('.musicxml'):
                compressXML(xmlName)
            elif xmlName.endswith('.mxl'):
                uncompressMXL(xmlName)
