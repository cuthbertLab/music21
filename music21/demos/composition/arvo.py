# -*- coding: utf-8 -*-
'''
Demonstration tools of Arvo Pärt Tintinabulation compositions
'''
import copy

from music21 import bar
from music21 import clef
from music21 import converter
from music21 import instrument
from music21 import key
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import stream

def partPari(show=True):
    '''
    generate the score of Arvo Pärt's "Pari Intervallo" algorithmically
    using music21.scale.ConcreteScale() to simulate Tintinabulation.
    '''
    s = stream.Score()
    cminor = key.Key('c')
    #real Paert
    main = converter.parse('tinynotation: 4/4 E-1 C D E- F G F E- D C D E- G A- F G E- F G F E- '
                            + 'D F G c B- c G A- B- c B- A- B- G c e- d c d c B- A- G F E- F G c '
                            + 'E- F G E- D E- F E- D C E- G F E- C F E- D C E- D C D C~ C')

    # fake Paert
    #main = converter.parse("E-1 F G A- G F c d e- G A- F E- D d e- c B- A- c d A- G F G " 
    #                        + "F A- B- A- c d A- B- c B- A- G F G F E-~ E-", '4/4')
    main.transpose('P8', inPlace=True)
    main.insert(0, cminor)
    main.insert(0, instrument.Recorder())
    bass = copy.deepcopy(main.flat)
    for n in bass.notes:
        n.pitch.diatonicNoteNum = n.pitch.diatonicNoteNum - 9
        if (n.pitch.step == 'A' or n.pitch.step == 'B') and n.pitch.octave == 2:
            n.accidental = pitch.Accidental('natural')
        else:
            n.accidental = cminor.accidentalByStep(n.step)
        if n.offset == (2 - 1) * 4 or n.offset == (74 - 1) * 4:
            n.pitch = pitch.Pitch("C3") # exceptions to rule
        elif n.offset == (73 - 1) * 4:
            n.tie = None
            n.pitch = pitch.Pitch("C3")
    top = copy.deepcopy(main.flat)
    main.insert(0, clef.Treble8vbClef())
    middle = copy.deepcopy(main.flat)


    cMinorArpeg = scale.ConcreteScale(pitches=["C2", "E-2", "G2"])
    ##  dummy test on other data
    # myA = pitch.Pitch("A2")
    # myA.microtone = -15
    # cMinorArpeg = scale.ConcreteScale(pitches=["C2", "E`2", "F~2", myA])

    lastNote = top.notes[-1]
    top.remove(lastNote)
    for n in top:
        if 'Note' in n.classes:
            n.pitch = cMinorArpeg.next(n.pitch, stepSize=2)
            if n.offset != (73 - 1) * 4.0:  # m. 73 is different
                n.duration.quarterLength = 3.0
                top.insert(n.offset + 3, note.Rest())
            else:
                n.duration.quarterLength = 6.0
                n.tie = None
    r1 = note.Rest(type='half')
    top.insertAndShift(0, r1)
    top.getElementsByClass(key.Key)[0].setOffsetBySite(top, 0)
    lastNote = middle.notes[-1]
    middle.remove(lastNote)

    for n in middle:
        if 'Note' in n.classes:
            n.pitch = cMinorArpeg.next(n.pitch, direction=scale.DIRECTION_DESCENDING, stepSize=2)
            if n.offset != (73 - 1) *4.0:  # m. 73 is different
                n.duration.quarterLength = 3.0
                middle.insert(n.offset + 3, note.Rest())
            else:
                n.duration.quarterLength = 5.0
                n.tie = None
    r2 = note.Rest(quarterLength=3.0)
    middle.insertAndShift(0, r2)
    middle.getElementsByClass(key.Key)[0].setOffsetBySite(middle, 0)

    ttied = top.makeMeasures().makeTies()
    mtied = middle.makeMeasures().makeTies()
    bass.makeMeasures(inPlace=True)
    main.makeMeasures(inPlace=True)

    s.insert(0, ttied)
    s.insert(0, main)
    s.insert(0, mtied)
    s.insert(0, bass)

    for p in s.parts:
        p.getElementsByClass(stream.Measure)[-1].rightBarline = bar.Barline('final')

    if show:
        s.show()
        