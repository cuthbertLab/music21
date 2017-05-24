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
skip = ['usersGuide_90_musicxmlTest.ipynb']

def runAll():
    pass

def runOne(nbFile):
    us = environment.UserSettings()
    museScore = us['musescoreDirectPNGPath']
    us['musescoreDirectPNGPath'] = '/skip'
    try:
        _ = input('skip: ')
        os.system('pytest --nbval ' + nbFile + ' --sanitize-with '
                  + common.getSourceFilePath() + os.sep + 'documentation' + os.sep
                  + 'nbval-sanitize.cfg -q')
    except Exception:
        raise
    finally:
        us['musescoreDirectPNGPath'] = museScore
        
    '/Applications/MuseScore 2.app/Contents/MacOS/mscore'
        


if __name__ == '__main__':
    if len(sys.argv) > 1:
        runOne(sys.argv[1])
    else:
        runAll()