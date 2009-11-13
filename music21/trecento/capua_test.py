
import music21
from stream import Stream
from note import Note
import capua

def colorCapuaFictaTest():
    (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
    (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
    n11.duration.type = "quarter"
    n11.name = "D"
    n12.duration.type = "quarter"
    n12.name = "E"
    n13.duration.type = "quarter"
    n13.name = "F"
    n14.duration.type = "quarter"
    n14.name = "G"

    n21.name = "C"
    n21.duration.type = "quarter"
    n22.name = "C"
    n22.duration.type = "quarter"
    n23.name = "B"
    n23.octave = 3
    n23.duration.type = "quarter"
    n24.name = "C"
    n24.duration.type = "quarter"

    stream1 = Stream()
    stream1.addNext([n11, n12, n13, n14])
    stream2 = Stream()
    stream2.addNext([n21, n22, n23, n24])


    ### Need twoStreamComparer to Work
    capua.evaluateWithoutFicta(stream1, stream2)
    assert n13.editorial.harmonicInterval.name == "d5", n13.editorial.harmonicInterval.name
    capua.evaluateCapuaTwoStreams(stream1, stream2)

    capua.colorCapuaFicta(stream1, stream2, "both")
    assert n13.editorial.harmonicInterval.name == "P5", n13.editorial.harmonicInterval.name

    assert n11.editorial.color == "yellow"
    assert n12.editorial.color == "yellow"
    assert n13.editorial.color == "green"
    assert n14.editorial.color == "yellow"

    assert n11.editorial.harmonicInterval.name == "M2"
    assert n21.editorial.harmonicInterval.name == "M2"

    assert n13.editorial.harmonicInterval.name == "P5"
    assert n13.editorial.misc["noFictaHarmony"] == "perfect cons"
    assert n13.editorial.misc["capua2FictaHarmony"] == "perfect cons"
    assert n13.editorial.misc["capua2FictaInterval"].name == "P5"
    assert n13.editorial.color == "green"
    assert stream1.lily.strip() == r'''\clef "treble" \color "yellow" d'4 \color "yellow" e'4 \ficta \color "green" fis'!4 \color "yellow" g'4'''

colorCapuaFictaTest()
