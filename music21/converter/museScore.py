# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         converter/museScore.py
# Purpose:      music21 to MuseScore connection
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-23 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module contains tools for using MuseScore to do conversions
from music21.  It was formerly mostly in subConverters.
'''
from __future__ import annotations
import os
import pathlib
import typing as t
import unittest

from music21 import common
from music21 import defaults
from music21 import environment
from music21.exceptions21 import SubConverterException

environLocal = environment.Environment('converter.museScore')

if t.TYPE_CHECKING:
    pass

def runThroughMuseScore(
    fp,
    subformats=(),
    *,
    dpi: int | None = None,
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
    museScorePath = environLocal['musescoreDirectPNGPath']
    if not museScorePath:
        raise SubConverterException(
            'To create PNG files directly from MusicXML you need to download MuseScore and '
            + 'put a link to it in your .music21rc via Environment.')
    if not museScorePath.exists():
        raise SubConverterException(
            "Cannot find a path to the 'mscore' file at "
            + f'{museScorePath} -- download MuseScore')

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



def findNumberedPNGPath(inputFp: str | pathlib.Path) -> pathlib.Path:
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
    lastFp: pathlib.Path | None = None
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
