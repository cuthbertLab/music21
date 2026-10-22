# ------------------------------------------------------------------------------
# Name:         converter/museScore.py
# Purpose:      music21 to MuseScore connection
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module contains tools for using MuseScore to do conversions
from music21.  It was formerly mostly in subConverters.
'''
from __future__ import annotations
import os
import pathlib
import re
import typing as t
import unittest

from music21 import common
from music21 import defaults
from music21 import environment
from music21.exceptions21 import SubConverterException

environLocal = environment.Environment('converter.museScore')

if t.TYPE_CHECKING:
    from collections.abc import Iterable

reMuseScoreBefore3 = re.compile(r'MuseScore ?[12]\b', re.IGNORECASE)


def findMuseScore(searchDirs: Iterable[str|pathlib.Path]|None = None) -> pathlib.Path|None:
    '''
    Return the MuseScore program (version 3 or newer) that music21 can run to make
    images of notation, or None if there isn't one.  Looks in the usual places for
    this computer (Applications folders on Mac, Program Files on Windows, the PATH
    elsewhere) unless given `searchDirs`.  If several versions are installed,
    returns the newest.

    * New in v11.

    AI-assisted (Claude).
    '''
    platform = common.getPlatform()
    if platform == 'darwin':
        patterns: tuple[str, ...] = ('MuseScore*.app/Contents/MacOS/mscore',)
        defaultDirs: list[str|pathlib.Path] = ['/Applications',
                                               pathlib.Path.home() / 'Applications']
    elif platform == 'win':
        patterns = ('MuseScore*/bin/MuseScore*.exe',)
        defaultDirs = [os.environ[key]
                       for key in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432')
                       if os.environ.get(key)]
    else:
        # names do not give versions here, so check in order: a bare "mscore"
        # is MuseScore 2 on Debian but MuseScore 4 on Arch
        patterns = ('mscore4portable', 'mscore3', 'musescore3', 'mscore', 'musescore')
        defaultDirs = [d for d in os.environ.get('PATH', '').split(os.pathsep) if d]

    if searchDirs is None:
        searchDirs = defaultDirs
    searchPaths = [pathlib.Path(d) for d in searchDirs]
    for pattern in patterns:
        # keyed by the path inside its folder, e.g. "MuseScore 4.app/Contents/MacOS/mscore"
        found = {str(p.relative_to(d)): p for d in searchPaths for p in d.glob(pattern)}
        current = {name: p for name, p in found.items()
                   if not reMuseScoreBefore3.search(name)}
        if current:
            return current[max(current)]
    return None


def getMuseScorePath() -> pathlib.Path:
    '''
    Return the MuseScore program set as `musescoreDirectPNGPath`.  If that is
    missing or points nowhere, find MuseScore and save its location; if it is
    not installed, raise a SubConverterException that says where to get it.

    * New in v11.
    '''
    museScorePath = environLocal['musescoreDirectPNGPath']
    if museScorePath is not None and museScorePath.exists():
        return museScorePath
    found = findMuseScore()
    if found is None:
        raise SubConverterException(
            'To show notation, music21 needs MuseScore (free from https://musescore.org), '
            + 'even if you use other notation software.  Install it and then try again.')
    environment.set('musescoreDirectPNGPath', found)
    return found

def runThroughMuseScore(
    fp,
    subformats=(),
    *,
    dpi: int|None = None,
    trimEdges: bool = True,
    leaveMargin: int = 0,
    **keywords
) -> pathlib.Path:  # pragma: no cover
    '''
    Take the output of the conversion process and run it through MuseScore to convert it
    to a png.

    * dpi: specifies the dpi of the output file.  If None, then the default is used.
    * trimEdges: if True (default) the image is trimmed to the edges of the music.
    * leaveMargin: if trimEdges is True, then this number of pixels is left around the
      trimmed image.
    '''
    museScorePath = getMuseScorePath()

    if not subformats:
        subformatExtension = 'png'
    else:
        subformatExtension = subformats[0] or 'png'

    fpOut = fp.with_suffix('.' + subformatExtension)

    museScoreRun = [str(museScorePath), fp, '-o', str(fpOut)]
    if trimEdges:
        # -T 0 = trim to zero pixel margin
        museScoreRun.extend(['-T', str(leaveMargin)])

    if dpi is not None:
        museScoreRun.extend(['-r', str(dpi)])

    prior_qt = os.getenv('QT_QPA_PLATFORM')
    prior_xdg = os.getenv('XDG_RUNTIME_DIR')
    if common.runningInNotebook():
        if common.getPlatform() == 'nix':
            # provide defaults to support headless MuseScore in Google Colab
            # https://github.com/cuthbertLab/music21/issues/260
            if prior_qt is None:
                os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            if prior_xdg is None:
                os.environ['XDG_RUNTIME_DIR'] = str(environment.Environment().getRootTempDir())
        if dpi is None:
            museScoreRun.extend(['-r', str(defaults.jupyterImageDpi)])

    common.fileTools.runSubprocessCapturingStderr(museScoreRun)

    if common.runningInNotebook() and common.getPlatform() == 'nix':
        # Leave environment in original state
        if prior_qt is None:
            os.environ.pop('QT_QPA_PLATFORM')
        if prior_xdg is None:
            os.environ.pop('XDG_RUNTIME_DIR')

    if subformatExtension == 'png':
        return findNumberedPNGPath(fpOut)
    else:
        return fpOut
    # common.cropImageFromPath(fp)



def findNumberedPNGPath(inputFp: str|pathlib.Path) -> pathlib.Path:
    '''
    Find the first numbered file path corresponding to the provided unnumbered file path
    ending in ".png". Raises an exception if no file can be found.

    Renamed in v7.  Returns a pathlib.Path
    '''
    inputFp = str(inputFp)  # not pathlib.
    if not inputFp.endswith('.png'):
        raise ValueError(f'inputFp must end with ".png"; got {inputFp}')

    path_without_extension = inputFp[:-1 * len('.png')]

    for search_extension in ('1', '01', '001', '0001', '00001'):
        search_path = pathlib.Path(path_without_extension + '-' + search_extension + '.png')
        if search_path.exists():
            return search_path

    raise IOError(
        f'No png file for {inputFp} (such as {path_without_extension}-1.png) was found.  '
        + 'The conversion to png failed'
    )


def findLastPNGPath(inputFp: pathlib.Path) -> pathlib.Path:
    '''
    Find the last numbered file path corresponding to the provided NUMBERED file path
    ending in ".png". Raises an exception if no file can be found.

    For instance, if there was a file named abc-01.png it might find abc-22.png.
    '''
    inputFpStr = inputFp.name  # not pathlib.
    if not inputFpStr.endswith('.png'):
        raise ValueError(f'inputFp must end with ".png"; got {inputFp}')

    dash_location = inputFpStr.rfind('-')
    if dash_location == -1:
        raise SubConverterException(
            f'inputFp must end with "-0001.png" or similar; got {inputFp}'
        )
    base_name = inputFpStr[:dash_location]
    last_name = list(sorted(inputFp.parent.glob(f'{base_name}-*.png'),
                            key=lambda p: p.name))[-1]
    return last_name


def findPNGRange(
    firstFp: pathlib.Path,
    lastFp: pathlib.Path|None = None
) -> tuple[int, int]:
    '''
    Return a 2-tuple of the maximum PNG number and the number of digits used to
    specify the PNG (for MuseScore generated PNGs, for use in the widget)
    '''
    inputFpStr = firstFp.name  # not pathlib.
    if not inputFpStr.endswith('.png'):
        raise ValueError(f'firstFp must end with ".png"; got {firstFp}')

    if lastFp is None:
        lastFp = findLastPNGPath(firstFp)

    dash_location = inputFpStr.rfind('-')
    if dash_location == -1:
        raise ValueError(
            f'firstFp must end with "-0001.png" or similar; got {firstFp}'
        )
    suffix_len = 4  # len('.png')
    num_digits = len(inputFpStr) - dash_location - suffix_len - 1
    num_string = lastFp.name[dash_location + 1:dash_location + 1 + num_digits]
    # print(inputFpStr, dash_location, num_digits, lastFp, num_string)
    last_number = int(num_string)
    return (last_number, num_digits)


class Test(unittest.TestCase):
    def _fakeInstall(self, root: pathlib.Path, *programs: str) -> None:
        for program in programs:
            (root / program).parent.mkdir(parents=True, exist_ok=True)
            (root / program).touch()

    def testFindMuseScoreNewestOnMac(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            apps = pathlib.Path(tmp)
            self._fakeInstall(apps,
                              'MuseScore 3.app/Contents/MacOS/mscore',
                              'MuseScore 4.app/Contents/MacOS/mscore')
            oldApps = apps / 'old'
            self._fakeInstall(oldApps,
                              'MuseScore 2.app/Contents/MacOS/mscore',
                              'Dorico 5.app/Contents/MacOS/Dorico 5')
            with mock.patch('music21.common.getPlatform', return_value='darwin'):
                self.assertEqual(findMuseScore([apps]),
                                 apps / 'MuseScore 4.app' / 'Contents' / 'MacOS' / 'mscore')
                self.assertIsNone(findMuseScore([oldApps]))

    def testFindMuseScoreOnWindows(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            programFiles = pathlib.Path(tmp)
            self._fakeInstall(programFiles, 'MuseScore 4/bin/MuseScore4.exe')
            with mock.patch('music21.common.getPlatform', return_value='win'):
                self.assertEqual(findMuseScore([programFiles]),
                                 programFiles / 'MuseScore 4' / 'bin' / 'MuseScore4.exe')

    def testFindMuseScoreOnLinux(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            binDir = pathlib.Path(tmp)
            # Debian's "mscore" is MuseScore 2; "mscore3" says what it is
            self._fakeInstall(binDir, 'mscore', 'mscore3')
            with mock.patch('music21.common.getPlatform', return_value='nix'):
                self.assertEqual(findMuseScore([binDir]), binDir / 'mscore3')

    def testGetMuseScorePathSavesWhatItFinds(self):
        from unittest import mock
        found = pathlib.Path(__file__)  # any file that exists
        with (mock.patch('music21.converter.museScore.environLocal',
                         {'musescoreDirectPNGPath': pathlib.Path('/nowhere/mscore')}),
              mock.patch('music21.converter.museScore.findMuseScore', return_value=found),
              mock.patch('music21.environment.set') as setMock):
            self.assertEqual(getMuseScorePath(), found)
        setMock.assert_called_once_with('musescoreDirectPNGPath', found)

    def testGetMuseScorePathSaysWhereToGetIt(self):
        from unittest import mock
        with (mock.patch('music21.converter.museScore.environLocal',
                         {'musescoreDirectPNGPath': None}),
              mock.patch('music21.converter.museScore.findMuseScore', return_value=None)):
            with self.assertRaisesRegex(SubConverterException, 'https://musescore.org'):
                getMuseScorePath()

    def pngNumbering(self):
        '''
        Testing findNumberedPNGPath() with files of lengths
        that create .png files with -1, -01, -001, and -0001 in the fp
        '''
        env = environment.Environment()
        for ext_base in '1', '01', '001', '0001':
            png_ext = '-' + ext_base + '.png'

            tmp = env.getTempFile(suffix='.png', returnPathlib=False)
            tmpNumbered = tmp.replace('.png', png_ext)
            os.rename(tmp, tmpNumbered)
            pngFp1 = findNumberedPNGPath(tmp)
            self.assertEqual(str(pngFp1), tmpNumbered)
            os.remove(tmpNumbered)

        # Now with a very long path.
        tmp = env.getTempFile(suffix='.png', returnPathlib=False)
        tmpNumbered = tmp.replace('.png', '-0000001.png')
        os.rename(tmp, tmpNumbered)
        with self.assertRaises(IOError):
            findNumberedPNGPath(tmpNumbered)
        os.remove(tmpNumbered)
