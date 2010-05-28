#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         upload.py
# Purpose:      music21 documentation upload utility
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009-10 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------



import getpass, os


def getDirBuildHtml():
    '''Return the html directory
    '''
    dir = os.getcwd()
    parentDir = os.path.dirname(dir)
    parentContents = os.listdir(parentDir)
    # make sure we are in the the proper directory
    if (not dir.endswith("buildDoc") or 
        'music21' not in parentContents):
        raise Exception("not in the music21%sbuildDoc directory: %s" % (os.sep, dir))
    dirBuild = os.path.join(parentDir, 'music21', 'doc')
    dirBuildHtml = os.path.join(dirBuild, 'html')
    return dirBuildHtml


# this needs to be on level higher then the level of the source
DST_MIT = 'athena.dialup.mit.edu:/afs/athena.mit.edu/org/m/music21/doc'

print('provide user:')
user = getpass.getpass()


src = getDirBuildHtml()


# -r flag makes this recurseive
cmdStr = 'scp -r %s %s@%s' % (src, user, DST_MIT)
print(cmdStr)

os.system(cmdStr)



