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
try:
    import pytest
except ImportError:  # pragma: no cover
    # fail here to get a better message than file-not-found below.
    raise ImportError(
        'Please install pytest -- in the music21 directory run "pip install ".[dev]"'
    )

# noinspection PyPackageRequirements
try:
    import nbval
except ImportError:  # pragma: no cover
    raise ImportError(
        'Please install nbval -- in the music21 directory run "pip install ".[dev]"'
    )

from music21 import environment
from music21 import common

if pytest is None or nbval is None:  # pragma: no cover
    # this will never run, but it's important to use pytest and nbval variables
    # or some modern code linters will remove the import pytest, import nbval lines.
    raise ImportError('Please install pytest and nbval')

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
    sanitize_fn = str(
        common.getRootFilePath()
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
