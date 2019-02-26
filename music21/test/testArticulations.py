import unittest
import music21


class TestArticulations(unittest.TestCase):  # pragma: no cover
    def testArticulations(self):
        score = music21.converter.parse('tab_test.xml')
        guitar_part = score.parts[0]
        notes = guitar_part.recurse().notes
        self.assertEqual(int(notes[0].articulations[1].number), 7)
        self.assertEqual(int(notes[0].articulations[0].number), 6)
        self.assertEqual(int(notes[1].articulations[1].number), 4)
        self.assertEqual(int(notes[1].articulations[0].number), 4)
        self.assertEqual(int(notes[2].articulations[1].number), 0)
        self.assertEqual(int(notes[2].articulations[0].number), 1)
        self.assertEqual(int(notes[3].articulations[1].number), 3)
        self.assertEqual(int(notes[3].articulations[0].number), 2)



if __name__ == '__main__':
    music21.mainTest(TestArticulations)
