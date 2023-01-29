from __future__ import annotations

from xml.etree.ElementTree import fromstring as El
import unittest

from music21 import clef
from music21 import meter
from music21.musicxml.xmlToM21 import MeasureParser
from music21 import note
from music21 import stream


class Test(unittest.TestCase):
    def testConversionClassMatch(self):
        # need to get music21.clef.X, not X, because
        # we are comparing the result to a translation outside
        # clef.py
        src = [
            [('G', 1, 0), clef.FrenchViolinClef],
            [('G', 2, 0), clef.TrebleClef],
            [('G', 2, -1), clef.Treble8vbClef],
            [('G', 2, 1), clef.Treble8vaClef],
            [('G', 3, 0), clef.GSopranoClef],
            [('C', 1, 0), clef.SopranoClef],
            [('C', 2, 0), clef.MezzoSopranoClef],
            [('C', 3, 0), clef.AltoClef],
            [('C', 4, 0), clef.TenorClef],
            [('C', 5, 0), clef.CBaritoneClef],
            [('F', 3, 0), clef.FBaritoneClef],
            [('F', 4, 0), clef.BassClef],
            [('F', 4, 1), clef.Bass8vaClef],
            [('F', 4, -1), clef.Bass8vbClef],
            [('F', 5, 0), clef.SubBassClef],
            [('TAB', 5, 0), clef.TabClef]
        ]

        MP = MeasureParser()

        for params, className in src:
            sign, line, octaveChange = params
            mxClef = El(r'<clef><sign>'
                        + sign + '</sign><line>'
                        + str(line) + '</line>'
                        + '<clef-octave-change>'
                        + str(octaveChange)
                        + '</clef-octave-change></clef>')
            c = MP.xmlToClef(mxClef)

            # environLocal.printDebug([type(c).__name__])

            self.assertEqual(c.sign, params[0])
            self.assertEqual(c.line, params[1])
            self.assertEqual(c.octaveChange, params[2])
            self.assertIsInstance(c, className,
                                  f'Failed Conversion of classes: {c} is not a {className}')

    def testContexts(self):
        n1 = note.Note('C')
        n1.offset = 10
        c1 = clef.AltoClef()
        c1.offset = 0
        s1 = stream.Stream([c1, n1])

        self.assertIs(s1.recurse().notes[0].getContextByClass(clef.Clef), c1)
        # equally good: getContextsByClass(Clef)[0]

        del s1

        n2 = note.Note('D')
        n2.duration.type = 'whole'
        n3 = note.Note('E')
        n3.duration.type = 'whole'
        ts1 = meter.TimeSignature('4/4')
        s2 = stream.Stream()
        s2.append(c1)
        s2.append(ts1)
        s2.append(n2)
        s2.append(n3)
        s2.makeMeasures()
        self.assertIs(n2.getContextByClass(clef.Clef), c1)

        del s2

        n4 = note.Note('F')
        n4.duration.type = 'half'
        n5 = note.Note('G')
        n5.duration.type = 'half'
        n6 = note.Note('A')
        n6.duration.type = 'whole'

        ts2 = meter.TimeSignature('4/4')
        bc1 = clef.BassClef()
        tc1 = clef.TrebleClef()

        s3 = stream.Stream()
        s3.append(bc1)
        s3.append(ts2)
        s3.append(n4)
        s3.append(tc1)
        s3.append(n5)
        s3.append(n6)
        s3.makeMeasures()

        self.assertIs(n4.getContextByClass(stream.Measure), n5.getContextByClass(stream.Measure))
        self.assertIs(n4.getContextByClass(clef.Clef), bc1)
        self.assertIs(n5.getContextByClass(clef.Clef), tc1)
        self.assertIs(n6.getContextByClass(clef.Clef), tc1)

    def testTabClefBeamDirections(self):
        m = stream.Measure()

        n1 = note.Note(64, quarterLength=0.25)
        n2 = note.Note(67, quarterLength=0.25)

        m.append(clef.TabClef())
        m.append(meter.TimeSignature('4/4'))
        m.append(n1)
        m.append(n2)
        m.makeBeams(inPlace=True)

        self.assertEqual(m.notes[0].stemDirection, 'down')


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
