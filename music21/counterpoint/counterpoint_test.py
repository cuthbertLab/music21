import music21
from music21 import note
from music21 import duration
from music21 import key
from music21 import scale
from music21.lily import LilyString
from music21 import noteStream

from note import Note
from noteStream import Stream
from counterpoint import *

import random

def counterpointTest():
    (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
    (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
    n11.duration.type = "quarter"
    n12.duration.type = "quarter"
    n13.duration.type = "quarter"
    n14.duration.type = "quarter"
    n21.duration.type = "quarter"
    n22.duration.type = "quarter"
    n23.duration.type = "quarter"
    n24.duration.type = "quarter"
    
    n12.step = "D"
    n13.step = "E"
    n14.step = "F"

    n21.step = "G"
    n22.step = "G"
    n23.step = "B"
    n24.step = "C"
    n24.octave = 5


    stream1 = Stream([n11, n12, n13, n14])
    stream2 = Stream([n21, n22, n23, n24])
    stream3 = Stream([n11, n13, n14])
    stream4 = Stream([n21, n23, n24])
    stream5 = Stream([n11, n23, n24, n21])

    counterpoint1 = Counterpoint(stream1, stream2)

    findPar5 = counterpoint1.findParallelFifths(stream1, stream2)
    
    assert findPar5 == 1
    assert n24.editorial.misc["Parallel Fifth"] == True
    assert n21.editorial.misc.has_key("Parallel Fifth") == False
    assert n22.editorial.misc.has_key("Parallel Fifth") == False
    assert n23.editorial.misc.has_key("Parallel Fifth") == False

    assert n14.editorial.misc["Parallel Fifth"] == True
    assert n11.editorial.misc.has_key("Parallel Fifth") == False
    assert n12.editorial.misc.has_key("Parallel Fifth") == False
    assert n13.editorial.misc.has_key("Parallel Fifth") == False

    par5 = counterpoint1.isParallelFifth(n11, n21, n12, n22)
    assert par5 == False

    par52 = counterpoint1.isParallelFifth(n13, n23, n14, n24)
    assert par52 == True

    validHarmony1 = counterpoint1.isValidHarmony(n11, n21)
    validHarmony2 = counterpoint1.isValidHarmony(n12, n22)

    assert validHarmony1 == True
    assert validHarmony2 == False

    validStep1 = counterpoint1.isValidStep(n11, n23)
    validStep2 = counterpoint1.isValidStep(n23, n11)
    validStep3 = counterpoint1.isValidStep(n23, n24)

    assert validStep1 == False
    assert validStep2 == False
    assert validStep3 == True

    allHarmony = counterpoint1.allValidHarmony(stream1, stream2)
    assert allHarmony == False

    allHarmony2 = counterpoint1.allValidHarmony(stream3, stream4)
    assert allHarmony2 == True

    melody1 = counterpoint1.isValidMelody(stream1)
    melody2 = counterpoint1.isValidMelody(stream5)

    assert melody1 == True
    assert melody2 == False

    numBadHarmony = counterpoint1.countBadHarmonies(stream1, stream2)
    numBadHarmony2 = counterpoint1.countBadHarmonies(stream3, stream4)

    assert numBadHarmony == 1
    assert numBadHarmony2 == 0

    numBadMelody = counterpoint1.countBadSteps(stream1)
    numBadMelody2 = counterpoint1.countBadSteps(stream5)

    assert numBadMelody == 0
    assert numBadMelody2 == 1

    (n31, n32, n33, n34) = (Note(), Note(), Note(), Note())
    n31.duration.type = "quarter"
    n32.duration.type = "quarter"
    n33.duration.type = "quarter"
    n34.duration.type = "quarter"

    n31.octave = 5
    n32.octave = 5
    n33.octave = 5
    n34.octave = 5

    n32.step = "D"
    n33.step = "E"
    n34.step = "F"

    stream6 = Stream([n31, n32, n33, n34])

    par8 = counterpoint1.findParallelOctaves(stream1, stream6)

    assert par8 == 3
    assert not n31.editorial.misc.has_key("Parallel Octave")
    assert n32.editorial.misc["Parallel Octave"] == True
    assert n33.editorial.misc["Parallel Octave"] == True
    assert n34.editorial.misc["Parallel Octave"] == True

    par82 = counterpoint1.findParallelOctaves(stream1, stream2)
    assert par82 == 0

    par83 = counterpoint1.isParallelOctave(n11, n31, n12, n32)
    par84 = counterpoint1.isParallelOctave(n11, n21, n12, n22)

    assert par83 == True
    assert par84 == False

    intervalList = ["m3", "M3", "P4", "P5", "m3"]
    consecutive = counterpoint1.thirdCounter(intervalList, 0)
    assert consecutive == 2

    list2 = ["m3", "M3", "m3", "m7"]
    consecutive2 = counterpoint1.thirdCounter(list2, 3)
    assert consecutive2 == 6

    list3 = ["m2", "m3"]
    consecutive3 = counterpoint1.thirdCounter(list3, 0)
    assert consecutive3 == 0

    (n41, n42, n43, n44, n45, n46, n47) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
    n41.duration.type = "quarter"
    n42.duration.type = "quarter"
    n43.duration.type = "quarter"
    n44.duration.type = "quarter"
    n45.duration.type = "quarter"
    n46.duration.type = "quarter"
    n47.duration.type = "quarter"

    (n51, n52, n53, n54, n55, n56, n57) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
    n51.duration.type = "quarter"
    n52.duration.type = "quarter"
    n53.duration.type = "quarter"
    n54.duration.type = "quarter"
    n55.duration.type = "quarter"
    n56.duration.type = "quarter"
    n57.duration.type = "quarter"

    n51.step = "E"
    n52.step = "E"
    n53.step = "E"
    n54.step = "E"
    n56.step = "E"
    n57.step = "E"

    stream7 = Stream([n41, n42, n43, n44, n45, n46, n47])
    stream8 = Stream([n51, n52, n53, n54, n55, n56, n57])

    too3 = counterpoint1.tooManyThirds(stream7, stream8, 4)
    too32 = counterpoint1.tooManyThirds(stream7, stream8, 3)

    assert too3 == False
    assert too32 == True

    (n61, n62, n63, n64, n65, n66, n67) = (Note(), Note(), Note(), Note(), Note(), Note(), Note())
    n61.duration.type = "quarter"
    n62.duration.type = "quarter"
    n63.duration.type = "quarter"
    n64.duration.type = "quarter"
    n65.duration.type = "quarter"
    n66.duration.type = "quarter"
    n67.duration.type = "quarter"

    n61.step = "E"
    n62.step = "E"
    n63.step = "E"
    n64.step = "E"
    n66.step = "E"
    n67.step = "E"

    n61.octave = 3
    n62.octave = 3
    n63.octave = 3
    n64.octave = 3
    n66.octave = 3
    n67.octave = 3

    stream9 = Stream([n61, n62, n63, n64, n65, n66, n67])

    too6 = counterpoint1.tooManySixths(stream7, stream9, 4)
    too62 = counterpoint1.tooManySixths(stream7, stream9, 3)

    assert too6 == False
    assert too62 == True

    (n71, n72, n81, n82) = (Note(), Note(), Note(), Note())
    n71.duration.type = "quarter"
    n72.duration.type = "quarter"
    n81.duration.type = "quarter"
    n82.duration.type = "quarter"
    
    n71.octave = 5
    n72.step = "D"
    n72.octave = 5
    n82.step = "G"
    hiding = counterpoint1.isHiddenFifth(n71, n81, n72, n82)
    hiding2 = counterpoint1.isHiddenFifth(n71, n82, n72, n81)

    assert hiding == True
    assert hiding2 == False

    (n73, n74, n75, n76) = (Note(), Note(), Note(), Note())
    n73.duration.type = "quarter"
    n74.duration.type = "quarter"
    n75.duration.type = "quarter"
    n76.duration.type = "quarter"
    
    n73.step = "D"
    n73.octave = 5
    n74.step = "A"
    n75.step = "D"
    n75.octave = 5
    n76.step = "E"
    n76.octave = 5

    (n83, n84, n85, n86) = (Note(), Note(), Note(), Note())
    n83.duration.type = "quarter"
    n84.duration.type = "quarter"
    n85.duration.type = "quarter"
    n86.duration.type = "quarter"
    
    n83.step = "G"
    n84.step = "F"
    n85.step = "G"
    n86.step = "A"

    stream10 = Stream([n71, n72, n73, n74, n75, n76])
    stream11 = Stream([n81, n82, n83, n84, n85, n86])

    parallel5 = counterpoint1.findParallelFifths(stream10, stream11)
    hidden5 = counterpoint1.findHiddenFifths(stream10, stream11)
    assert not n71.editorial.misc.has_key("Hidden Fifth")
    assert n72.editorial.misc["Hidden Fifth"] == True
    assert n75.editorial.misc["Hidden Fifth"] == True
    total5 = counterpoint1.findAllBadFifths(stream10, stream11)

    assert parallel5 == 2
    assert hidden5 == 2
    assert total5 == 4

    (n91, n92, n93, n94, n95, n96) = (Note(), Note(), Note(), Note(), Note(), Note())
    (n01, n02, n03, n04, n05, n06) = (Note(), Note(), Note(), Note(), Note(), Note())

    n91.duration.type = n92.duration.type = n93.duration.type = "quarter"
    n94.duration.type = n95.duration.type = n96.duration.type = "quarter"
    n01.duration.type = n02.duration.type = n03.duration.type = "quarter"
    n04.duration.type = n05.duration.type = n06.duration.type = "quarter"

    n91.step = "A"
    n92.step = "D"
    n92.octave = 5
    n93.step = "E"
    n93.octave = 5
    n94.octave = 5
    n95.step = "A"
    n96.step = "E"
    n96.octave = 5

    n02.step = "D"
    n03.step = "E"
    n06.step = "E"

    stream12 = Stream([n91, n92, n93, n94, n95, n96])
    stream13 = Stream([n01, n02, n03, n04, n05, n06])

    parallel8 = counterpoint1.findParallelOctaves(stream12, stream13)
    hidden8 = counterpoint1.findHiddenOctaves(stream12, stream13)
    total8 = counterpoint1.findAllBadOctaves(stream12, stream13)

    assert not n91.editorial.misc.has_key("Parallel Octave")
    assert not n91.editorial.misc.has_key("Hidden Octave")
    assert n92.editorial.misc["Hidden Octave"] == True
    assert not n92.editorial.misc.has_key("Parallel Octave")
    assert n93.editorial.misc["Parallel Octave"] == True
    assert not n93.editorial.misc.has_key("Hidden Octave")
    assert n94.editorial.misc["Parallel Octave"] == True
    assert n96.editorial.misc["Hidden Octave"] == True

    assert parallel8 == 2
    assert hidden8 == 2
    assert total8 == 4

    hidden8 = counterpoint1.isHiddenOctave(n91, n01, n92, n02)
    hidden82 = counterpoint1.isHiddenOctave(n92, n02, n93, n03)

    assert hidden8 == True
    assert hidden82 == False

    (n100, n101, n102, n103, n104, n105, n106, n107) = (Note(), Note(), Note(), Note(), Note(), Note(), Note(), Note())
    n100.duration.type = "quarter"
    n101.duration.type = "quarter"
    n102.duration.type = "quarter"
    n103.duration.type = "quarter"
    n104.duration.type = "quarter"
    n105.duration.type = "quarter"
    n106.duration.type = "quarter"
    n107.duration.type = "quarter"

    n100.name = "G"
    n101.name = "A"
    n102.name = "D"
    n103.name = "F"
    n104.name = "G"
    n105.name = "A"
    n106.name = "G"
    n107.name = "F"

    stream14 = Stream([n100, n101, n102, n103, n104, n105, n106, n107])
    aMinor = scale.ConcreteMinorScale(n101)
    stream15 = counterpoint1.raiseLeadingTone(stream14, aMinor)
    names15 = [note1.name for note1 in stream15.notes]
    assert names15 == ["G#", "A", "D", "F#", "G#", "A", "G", "F"]

   
def firstSpeciesTest():
    n101 = Note()
    n101.duration.type = "quarter"
    n101.name = "A"
    aMinor = scale.ConcreteMinorScale(n101)
    n101b = Note()
    n101b.duration.type = "quarter"
    n101b.name = "D"
    dMinor = scale.ConcreteMinorScale(n101b)
    
    counterpoint1 = Counterpoint()
    (n110, n111, n112, n113) = (Note(), Note(), Note(), Note())
    (n114, n115, n116, n117, n118) = (Note(), Note(), Note(), Note(), Note())
    (n119, n120, n121, n122, n123) = (Note(), Note(), Note(), Note(), Note())
    (n124, n125, n126, n127, n128) = (Note(), Note(), Note(), Note(), Note())

    n110.duration.type = "quarter"
    n111.duration.type = "quarter"
    n112.duration.type = "quarter"
    n113.duration.type = "quarter"
    n114.duration.type = "quarter"
    n115.duration.type = "quarter"
    n116.duration.type = "quarter"
    n117.duration.type = "quarter"
    n118.duration.type = "quarter"

    n110.name = "A"
    n110.octave = 3
    n111.name = "C"
    n111.octave = 4
    n112.name = "B"
    n112.octave = 3
    n113.name = "C"
    n113.octave = 4
    n114.name = "D"
    n115.name = "E"
    n116.name = "C"
    n116.octave = 4
    n117.name = "B"
    n117.octave = 3
    n118.name = "A"
    n118.octave = 3
    n119.name = "F"
    n120.name = "E"
    n121.name = "D"
    n122.name = "G"
    n123.name = "F"
    n124.name = "A"
    n125.name = "G"
    n126.name = "F"
    n127.name = "E"
    n128.name = "D"
#    n120 = n115.deepcopy()

    cantusFirmus1 = Stream([n110, n111, n112, n113, n114, n115, n116, n117, n118])
    cantusFirmus2 = Stream([n110, n115, n114, n119, n120, n113, n121, n116, n117, n118])
    cantusFirmus3 = Stream([n114, n119, n115, n121, n122, n123, n124, n125, n126, n127, n128])
    
    choices = [cantusFirmus1, cantusFirmus2, cantusFirmus3, cantusFirmus3, cantusFirmus3, cantusFirmus3]
    cantusFirmus = random.choice(choices)

    thisScale = aMinor
    if cantusFirmus is cantusFirmus3:
        thisScale = dMinor
        
    goodHarmony = False
    goodMelody = False

    while (goodHarmony == False or goodMelody == False):
        try:
            hopeThisWorks = counterpoint1.generateFirstSpecies(cantusFirmus, thisScale)
            print [note1.name + str(note1.octave) for note1 in hopeThisWorks.notes]

            hopeThisWorks2 = counterpoint1.raiseLeadingTone(hopeThisWorks, thisScale)
            print [note1.name + str(note1.octave) for note1 in hopeThisWorks2.notes]
    
            goodHarmony = counterpoint1.allValidHarmony(hopeThisWorks2, cantusFirmus)
            goodMelody = counterpoint1.isValidMelody(hopeThisWorks2)        

            lastInterval = interval.generateInterval(hopeThisWorks2.notes[-2], hopeThisWorks2.notes[-1])
            if lastInterval.generic.undirected != 2:
                goodMelody = False
                print "rejected because lastInterval was not a second"
         
            print [note1.name + str(note1.octave) for note1 in cantusFirmus.notes]
            if not goodHarmony: print "bad harmony"
            else: print "harmony good"
            if not goodMelody: print "bad melody"
            else: print "melody good"
        except CounterpointException:
            pass
    
    d1 = duration.Duration()
    d1.type = "whole"
    for tN in hopeThisWorks2.notes:
        tN.duration = d1
    for tN in cantusFirmus.notes:
        tN.duration = d1

    lilyOut = twoStreamLily(hopeThisWorks2, cantusFirmus)
    lilyOut.showPNGandPlayMIDI()
    
def twoStreamLily(st1, st2):
    lilyOut = LilyString()
    lilyOut += "<< \\time 4/4\n"
    lilyOut += "  \\new Staff { " 
    lilyOut += st1.lily + " } \n"    
    lilyOut += "  \\new Staff { " 
    lilyOut += st2.lily + " } \n"    
    lilyOut += ">> \n"
    return lilyOut
    
if (__name__ == "__main__"):
#    counterpointTest()
    firstSpeciesTest()
