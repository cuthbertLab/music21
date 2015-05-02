# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testMidMeasureClef.py
# Purpose:      testing mid measure clefs
#
# Authors:      Frank Zalkow
#
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
_DOC_IGNORE_MODULE_OR_PACKAGE = True

import unittest

class Test(unittest.TestCase):
    """ Tests if there are two clefs"""

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import stream, note, clef, musicxml, converter, meter

        orig_stream = stream.Stream()
        orig_stream.append(meter.TimeSignature("4/4"))
        orig_stream.append(clef.TrebleClef())
        orig_stream.repeatAppend(note.Note("C4"), 2)
        orig_stream.append(clef.BassClef())
        orig_stream.repeatAppend(note.Note("C4"), 2)

        xml = musicxml.m21ToString.fromStream(orig_stream)

        new_stream = converter.parse(xml)
        assert len(new_stream.flat.getElementsByClass('Clef')) == 2



if __name__ == "__main__":
    import music21
    music21.mainTest(Test)