'''
Created on May 24, 2017

@author: cuthbert
'''
from music21 import environment
from music21 import common

import sys
import pytest # @UnusedImport
import nbval # @UnusedImport
import os

# pytest --nbval usersGuide_15_key.ipynb --sanitize-with ../../nbval-sanitize.cfg -q
skip = ['usersGuide_90_musicxmlTest.ipynb', 'installJupyter.ipynb']

def runAll():
    sourcePath = common.getSourceFilePath() + os.sep + 'documentation' + os.sep + 'source'
    for innerDir in ('about', 'developerReference', 'installing', 'moduleReference',
                     'tutorials', 'usersGuide'):

        fullDir = sourcePath + os.sep + innerDir
        allFiles = os.listdir(fullDir)
        for f in allFiles:
            if not f.endswith('ipynb'):
                continue
            if f in skip:
                continue
            print(innerDir + os.sep + f)
            try:
                retVal = runOne(fullDir + os.sep + f)
            except KeyboardInterrupt:
                break

            if retVal == 512:
                return None

def runOne(nbFile):
    us = environment.UserSettings()
    museScore = us['musescoreDirectPNGPath']
    us['musescoreDirectPNGPath'] = '/skip'
    try:
        retVal = os.system('pytest --nbval ' + nbFile + ' --sanitize-with '
                  + common.getSourceFilePath() + os.sep + 'documentation' + os.sep
                  + 'nbval-sanitize.cfg -q')
    except (Exception, KeyboardInterrupt):
        raise
    finally:
        us['musescoreDirectPNGPath'] = museScore

    return retVal
    '/Applications/MuseScore 2.app/Contents/MacOS/mscore'



if __name__ == '__main__':
    if len(sys.argv) > 1:
        runOne(sys.argv[1])
    else:
        runAll()
