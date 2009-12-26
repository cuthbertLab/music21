import music21
from music21 import humdrum
from music21.note import Note
from music21.meter import TimeSignature
from music21.stream import Measure
from copy import deepcopy

def bergEx01():
    # berg, violin concerto, measure 64-65, p12
    # triplets should be sextuplets

    humdata = '''
**kern
*M2/4
=1
24r
24g#
24f#
24e
24c#
24f
24r
24dn
24e-
24gn
24e-
24dn
=2
24e-
24f#
24gn
24b-
24an
24gn
24gn
24f#
24an
24cn
24a-
24en
=3
*-
'''

    score = humdrum.parseData(humdata).stream[0]
    score.show()
   
    ts = score.getElementsByClass(TimeSignature)[0]
   
    for thisNote in score.flat.getNotes():
        thisNote.duration.tuplets[0].setRatio(12, 8)

    for thisMeasure in score.getElementsByClass(Measure):
        thisMeasure.insertAtIndex(0, deepcopy(ts))
        thisMeasure.makeBeams()

    score.show()

if __name__ == '__main__':
    bergEx01()