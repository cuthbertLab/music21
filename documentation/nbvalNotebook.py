# -*- coding: utf-8 -*-
'''
Run tests of notebooks using nbval -- called from testDocumentation

Created on May 24, 2017

@author: cuthbert
'''
import sys
import pytest # @UnusedImport # pylint: disable=unused-import
import nbval # @UnusedImport # pylint: disable=unused-import
import os

from music21 import environment
from music21 import common

# pytest --nbval usersGuide_15_key.ipynb --sanitize-with ../../nbval-sanitize.cfg -q
skip = ['installJupyter.ipynb']

def runAll():
    sourcePath = common.getRootFilePath() + os.sep + 'documentation' + os.sep + 'source'
    for innerDir in ('about', 'developerReference', 'installing', 'usersGuide'):

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
                  + common.getRootFilePath() + os.sep + 'documentation' + os.sep
                  + 'docbuild' + os.sep
                  + 'nbval-sanitize.cfg -q')
    except (Exception, KeyboardInterrupt):
        raise
    finally:
        us['musescoreDirectPNGPath'] = museScore

    return retVal
    # '/Applications/MuseScore 2.app/Contents/MacOS/mscore'



if __name__ == '__main__':
    if len(sys.argv) > 1:
        runOne(sys.argv[1])
    else:
        runAll()
