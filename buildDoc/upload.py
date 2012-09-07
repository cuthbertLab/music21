#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         upload.py
# Purpose:      music21 documentation upload utility
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2009-2010 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------



import getpass, os


def getDirBuildHtml():
    '''Return the html directory
    '''
    cwdir = os.getcwd()
    parentDir = os.path.dirname(cwdir)
    parentContents = os.listdir(parentDir)
    # make sure we are in the the proper directory
    if (not cwdir.endswith("buildDoc") or 
        'music21' not in parentContents):
        raise Exception("not in the music21%sbuildDoc directory: %s" % (os.sep, cwdir))
    dirBuild = os.path.join(parentDir, 'music21', 'doc')
    dirBuildHtml = os.path.join(dirBuild, 'html')
    return dirBuildHtml


# this needs to be on level higher then the level of the source
DST_MIT = 'athena.dialup.mit.edu:/afs/athena.mit.edu/org/m/music21/doc'

print('provide user:')
user = getpass.getpass()


src = getDirBuildHtml()


# -r flag makes this recursive
cmdStr = 'scp -r %s %s@%s' % (src, user, DST_MIT)
print(cmdStr)

os.system(cmdStr)



