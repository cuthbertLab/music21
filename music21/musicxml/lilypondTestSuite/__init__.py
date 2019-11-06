# -*- coding: utf-8 -*-
'''
The Lilypond MusicXML Test Suite comes from
https://github.com/cuthbertLab/musicxmlTestSuite
and is a fork of
http://lilypond.org/doc/v2.18/input/regression/musicxml/collated-files

The test suite is licensed under the MIT license
(https://opensource.org/licenses/mit-license.php)
and copyrighted by the Lilypond project.
'''
import os
import unittest

import warnings
from music21 import converter
from music21 import common


def allFiles():
    thisDir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
    allOut = []
    for f in thisDir.iterdir():
        if f.name.startswith('__'):
            continue
        allOut.append(f)
    return allOut


class Test(unittest.TestCase):
    '''
    Test Suite for the Test Suite (meta!)
    '''

    def testAll(self):
        for f in allFiles():
            converter.parse(f)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
