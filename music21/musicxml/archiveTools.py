# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         musicxml/archiveTools.py
# Purpose:      Tools for compressing and uncompressing MusicXML files
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2017 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for compressing and uncompressing musicxml files.
'''
import os
import zipfile

from music21 import common
from music21 import environment
_MOD = 'musicxml/archiveTools.py'
environLocal = environment.Environment(_MOD)

def compressXML(filename, deleteOriginal=False):
    '''
    Takes a filename, and if the filename corresponds to a musicXML file with
    an .xml extension, creates a corresponding compressed .mxl file in the same
    directory.

    If deleteOriginal is set to True, the original musicXML file is deleted
    from the system.
    '''
    if not filename.endswith('.xml') and not filename.endswith('.musicxml'):
        return  # not a musicXML file
    filename = common.pathTools.cleanpath(filename)
    environLocal.warn("Updating file: {0}".format(filename))
    filenameList = filename.split(os.path.sep)
    # find the archive name (name w/out filepath)
    archivedName = filenameList.pop()
    # new archive name
    filenameList.append(archivedName[0:len(archivedName) - 4] + ".mxl")
    newFilename = os.path.sep.join(filenameList)  # new filename
    # contents of container.xml file in META-INF folder
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container>
  <rootfiles>
    <rootfile full-path="{0}"/>
  </rootfiles>
</container>
    '''.format(archivedName)
    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(
            newFilename,
            'w',
            compression=zipfile.ZIP_DEFLATED,
            ) as myZip:
        myZip.write(filename, archivedName)
        myZip.writestr(
            'META-INF' + os.path.sep + 'container.xml',
            container,
            )
    # Delete uncompressed xml file from system
    if deleteOriginal:
        os.remove(filename)


def uncompressMXL(filename, deleteOriginal=False):
    '''
    Takes a filename, and if the filename corresponds to a compressed musicXML
    file with an .mxl extension, creates a corresponding uncompressed .xml file
    in the same directory.

    If deleteOriginal is set to True, the original compressed musicXML file is
    deleted from the system.
    '''
    if not filename.endswith(".mxl") and not filename.endswith('.musicxml'):
        return  # not a musicXML file
    filename = common.pathTools.cleanpath(filename)
    environLocal.warn("Updating file: {0}".format(filename))
    filenames = filename.split(os.path.sep)
    # find the archive name (name w/out filepath)
    archivedName = filenames.pop()

    unarchivedName = os.path.splitext(archivedName)[0] + '.xml'
    extractPath = os.path.sep.join(filenames)
    # Export container and original xml file to system as a compressed XML.
    with zipfile.ZipFile(filename, 'r', compression=zipfile.ZIP_DEFLATED) as myZip:
        try:
            myZip.extract(member=unarchivedName, path=extractPath)
        except KeyError:
            for storedName in myZip.namelist():
                myZip.extract(member=storedName, path=extractPath)
            
    # Delete uncompressed xml file from system
    if deleteOriginal:
        os.remove(filename)

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 1:
        for xmlName in sys.argv[1:]:
            if xmlName.endswith('.xml'):
                compressXML(xmlName)
            elif xmlName.endswith('.mxl'):
                uncompressMXL(xmlName)
