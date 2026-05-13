import unittest

from music21 import meter
from music21 import note
from music21 import stream

class Test(unittest.TestCase):
    def test_beam_status_with_makeNotation_false(self):
        '''
        Test that there is a way to get no beams w/ makeNotation
        '''
        m = stream.Measure(number=1)
        m.insert(0, meter.TimeSignature('2/4'))
        m.repeatAppend(note.Note('C4', type='eighth'), 4)
        p = stream.Part([m], id='part')
        sc = stream.Score([p], id='score')
        o = sc.write('musicxml', makeNotation=False)
        with open(o, 'r', encoding='utf-8') as FH:
            data = FH.read()
        self.assertNotIn('<beam number', data)


# -------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
