# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         graph/utilities.py
# Purpose:      Methods for finding external modules, manipulating colors, etc.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Methods for finding external modules, converting colors to Matplotlib colors, etc.
'''
import unittest
from collections import namedtuple

import webcolors

# TODO: Move _missingImport to environment or common so this is unnecessary.
from music21.base import _missingImport

from music21 import common
from music21 import exceptions21
from music21 import pitch

from music21 import environment
_MOD = 'graph.utilities'
environLocal = environment.Environment(_MOD)


ExtendedModules = namedtuple('ExtendedModules',
                             'matplotlib Axes3D collections patches plt networkx')


def getExtendedModules():
    '''
    this is done inside a function, so that the slow import of matplotlib is not done
    in ``from music21 import *`` unless it's actually needed.

    Returns a namedtuple: (matplotlib, Axes3D, collections, patches, plt, networkx)
    '''
    if 'matplotlib' in _missingImport:
        raise GraphException(
            'could not find matplotlib, graphing is not allowed')  # pragma: no cover
    import matplotlib  # @UnresolvedImport
    # backend can be configured from config file, matplotlibrc,
    # but an early test broke all processing
    # matplotlib.use('WXAgg')
    try:
        from mpl_toolkits.mplot3d import Axes3D  # @UnresolvedImport
    except ImportError:  # pragma: no cover
        Axes3D = None
        environLocal.warn(
            'mpl_toolkits.mplot3d.Axes3D could not be imported -- likely cause is an '
            + 'old version of six.py (< 1.9.0) on your system somewhere'
        )

    from matplotlib import collections  # @UnresolvedImport
    from matplotlib import patches  # @UnresolvedImport

    # from matplotlib.colors import colorConverter
    import matplotlib.pyplot as plt  # @UnresolvedImport

    try:
        import networkx
    except ImportError:  # pragma: no cover
        networkx = None  # use for testing

    return ExtendedModules(matplotlib, Axes3D, collections, patches, plt, networkx)

# ------------------------------------------------------------------------------


class GraphException(exceptions21.Music21Exception):
    pass


class PlotStreamException(exceptions21.Music21Exception):
    pass


def accidentalLabelToUnicode(label):
    '''
    Changes a label possibly containing a modifier such as "-" or "#" into
    a unicode string.

    >>> graph.utilities.accidentalLabelToUnicode('B-4')
    'B♭4'

    Since matplotlib's default fonts do not support double sharps or double flats,
    etc. these are converted as best we can...

    >>> graph.utilities.accidentalLabelToUnicode('B--4')
    'B♭♭4'
    '''
    if not isinstance(label, str):
        return label
    for modifier, unicodeAcc in pitch.unicodeFromModifier.items():
        if modifier != '' and modifier in label and modifier in ('-', '#'):
            # ideally eventually matplotlib will do the other accidentals...
            label = label.replace(modifier, unicodeAcc)
            break

    return label


def getColor(color):
    '''
    Convert any specification of a color to a hexadecimal color used by matplotlib.

    >>> graph.utilities.getColor('red')
    '#ff0000'
    >>> graph.utilities.getColor('r')
    '#ff0000'
    >>> graph.utilities.getColor('Steel Blue')
    '#4682b4'
    >>> graph.utilities.getColor('#f50')
    '#ff5500'
    >>> graph.utilities.getColor([0.5, 0.5, 0.5])
    '#808080'
    >>> graph.utilities.getColor(0.8)
    '#cccccc'
    >>> graph.utilities.getColor([0.8])
    '#cccccc'
    >>> graph.utilities.getColor([255, 255, 255])
    '#ffffff'

    Invalid colors raise GraphExceptions:

    >>> graph.utilities.getColor('l')
    Traceback (most recent call last):
    music21.graph.utilities.GraphException: invalid color abbreviation: l

    >>> graph.utilities.getColor('chalkywhitebutsortofgreenish')
    Traceback (most recent call last):
    music21.graph.utilities.GraphException: invalid color name: chalkywhitebutsortofgreenish

    >>> graph.utilities.getColor(True)
    Traceback (most recent call last):
    music21.graph.utilities.GraphException: invalid color specification: True
    '''
    # expand a single value to three
    if common.isNum(color):
        color = [color, color, color]
    if isinstance(color, str):
        if color[0] == '#':  # assume is hex
            # this will expand three-value codes, and check for badly
            # formed codes
            return webcolors.normalize_hex(color)
        color = color.lower().replace(' ', '')
        # check for one character matplotlib colors
        if len(color) == 1:
            colorMap = {'b': 'blue',
                        'g': 'green',
                        'r': 'red',
                        'c': 'cyan',
                        'm': 'magenta',
                        'y': 'yellow',
                        'k': 'black',
                        'w': 'white'}
            try:
                color = colorMap[color]
            except KeyError:
                raise GraphException(f'invalid color abbreviation: {color}')
        try:
            return webcolors.name_to_hex(color)
        except ValueError:  # no color match
            raise GraphException(f'invalid color name: {color}')

    elif common.isListLike(color):
        percent = False
        for sub in color:
            if sub < 1:
                percent = True
                break
        if percent:
            if len(color) == 1:
                color = [color[0], color[0], color[0]]
            # convert to 0 100% values as strings with % symbol
            colorStrList = [str(x * 100) + '%' for x in color]
            return webcolors.rgb_percent_to_hex(colorStrList)
        else:  # assume integers
            return webcolors.rgb_to_hex(tuple(color))
    raise GraphException(f'invalid color specification: {color}')


class Test(unittest.TestCase):
    def testColors(self):
        self.assertEqual(getColor([0.5, 0.5, 0.5]), '#808080')
        self.assertEqual(getColor(0.5), '#808080')
        self.assertEqual(getColor(255), '#ffffff')
        self.assertEqual(getColor('Steel Blue'), '#4682b4')


if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)  # TestExternal, 'noDocTest') #, runTest='testGetPlotsToMakeA')
