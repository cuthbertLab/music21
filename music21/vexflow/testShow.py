# -*- coding: utf-8 -*-
from music21 import stream, note, clef

if __name__ == '__main__':
    p = stream.Part()
    p2 = stream.Part()
    m1 = stream.Measure()
    m2 = stream.Measure()
    m1.insert(0, note.Note("C5", type="whole"))
    m2.insert(0, note.Note("D3", type="whole"))
    m1.insert(0, clef.TrebleClef())
    m2.insert(0, clef.BassClef())
    p.insert(0, m1)
    p2.insert(0, m2)
    s = stream.Score()
    s.insert(0, p)
    s.insert(0, p2)
    s.show('vexflow')
