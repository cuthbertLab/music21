import note
from note import Note
from scale import *

def test():
    n1 = Note()
    
    CMajor = ConcreteMajorScale(n1)
    
    assert CMajor.name == "C major"
    assert CMajor.scaleList[6].step == "B"
    
    CScale = CMajor.getConcreteMajorScale()
    
    assert CScale[7].step == "C"
    assert CScale[7].octave == 5
    
    CScale2 = CMajor.getAbstractMajorScale()
    
    for note1 in CScale2:
        assert note1.octave == 0
        assert note1.duration.type == ""
    assert [note1.name for note1 in CScale] == ["C", "D", "E", "F", "G", "A", "B", "C"]
    
    seventh = CMajor.getScaleDegree(7)
    assert seventh.step == "B"
    
    dom = CMajor.getDominant()
    assert dom.step == "G"
    
    n2 = Note()
    n2.step = "A"
    
    aMinor = CMajor.getRelativeMinor()
    assert aMinor.name == "A minor", "Got a different name: " + aMinor.name
    
    notes = [note1.name for note1 in aMinor.scaleList]
    assert notes == ["A", "B", "C", "D", "E", "F", "G"]
    
    n3 = Note()
    n3.name = "B-"
    n3.octave = 5
    
    bFlatMinor = ConcreteMinorScale(n3)
    assert bFlatMinor.name == "B- minor", "Got a different name: " + bFlatMinor.name
    notes2 = [note1.name for note1 in bFlatMinor.scaleList]
    assert notes2 == ["B-", "C", "D-", "E-", "F", "G-", "A-"]
    assert bFlatMinor.scaleList[0] == n3
    assert bFlatMinor.scaleList[6].octave == 6
    
    harmonic = bFlatMinor.getConcreteHarmonicMinorScale()
    niceHarmonic = [note1.name for note1 in harmonic]
    assert niceHarmonic == ["B-", "C", "D-", "E-", "F", "G-", "A", "B-"]
    
    harmonic2 = bFlatMinor.getAbstractHarmonicMinorScale()
    assert [note1.name for note1 in harmonic2] == niceHarmonic
    for note1 in harmonic2:
        assert note1.octave == 0
        assert note1.duration.type == ""
    
    melodic = bFlatMinor.getConcreteMelodicMinorScale()
    niceMelodic = [note1.name for note1 in melodic]
    assert niceMelodic == ["B-", "C", "D-", "E-", "F", "G", "A", "B-", "A-", "G-", \
                           "F", "E-", "D-", "C", "B-"]
    
    melodic2 = bFlatMinor.getAbstractMelodicMinorScale()
    assert [note1.name for note1 in melodic2] == niceMelodic
    for note1 in melodic2:
        assert note1.octave == 0
        assert note1.duration.type == ""
    
    cNote = bFlatMinor.getScaleDegree(2)
    assert cNote.name == "C"
    fNote = bFlatMinor.getDominant()
    assert fNote.name == "F"
    
    bFlatMajor = bFlatMinor.getParallelMajor()
    assert bFlatMajor.name == "B- major"
    scale = [note1.name for note1 in bFlatMajor.getConcreteMajorScale()]
    assert scale == ["B-", "C", "D", "E-", "F", "G", "A", "B-"]
    
    dFlatMajor = bFlatMinor.getRelativeMajor()
    assert dFlatMajor.name == "D- major"
    assert dFlatMajor.getTonic().name == "D-"
    assert dFlatMajor.getDominant().name == "A-"

if (__name__ == "__main__"):
    test()
    