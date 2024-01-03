# -*- coding: utf-8 -*-
'''
Run tests of notebooks using nbval -- called from testDocumentation

Created on May 24, 2017

@author: cuthbert
'''
from __future__ import annotations

import pathlib  # for typing
import sys
import subprocess

# noinspection PyPackageRequirements
import pytest  # pylint: disable=unused-import
# noinspection PyPackageRequirements
import nbval  # pylint: disable=unused-import

from music21 import environment
from music21 import common

# pytest --nbval usersGuide_15_key.ipynb --nbval-sanitize-with ../../nbval-sanitize.cfg -q
skip = ['installJupyter.ipynb']

def getAllFiles() -> list[pathlib.Path]:
    sourcePath = common.getRootFilePath() / 'documentation' / 'source'
    goodFiles = []
    for innerDir in ('about', 'developerReference', 'installing', 'usersGuide'):
        fullDir = sourcePath / innerDir
        for f in sorted(fullDir.rglob('*.ipynb')):
            if f.name in skip:
                continue
            if 'checkpoint' in str(f):
                continue

            goodFiles.append(f)
    return goodFiles

def runAll():
    for f in getAllFiles():
        print('Running: ', str(f))
        try:
            retVal = runOne(f)
        except KeyboardInterrupt:
            break

        if retVal == 512:
            return None

def findAndRun(filename: str):
    allFiles = getAllFiles()
    for f in allFiles:
        if filename in str(f):
            runOne(f)

def runOne(nbFile):
    us = environment.UserSettings()
    museScore = us['musescoreDirectPNGPath']
    us['musescoreDirectPNGPath'] = '/skip' + str(museScore)

    # this config file changes 0x39f3a0 to 0xADDRESS.
    sanitize_fn = str(common.getRootFilePath()
                      / 'documentation'
                      / 'docbuild'
                      / 'nbval-sanitize.cfg'
                      )
    try:
        retVal = subprocess.run(
            ['pytest',
             '--disable-pytest-warnings',
             '--nbval', str(nbFile),
             '--nbval-sanitize-with', sanitize_fn,
             '-q'],
            check=False,
        )
    # except (Exception, KeyboardInterrupt):  # specifically looking at KeyboardInterrupt.
    #     raise
    finally:
        us['musescoreDirectPNGPath'] = museScore

    return retVal


if __name__ == '__main__':
    if len(sys.argv) > 1:
        runOne(sys.argv[1])
    else:
        runAll()
