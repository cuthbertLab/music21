.. _examples:


Examples and Demonstrations
=============================


The following examples provide a few samples of some of the possibilities available when working with music21.



Counting, Searching, and Statistical Processing
------------------------------------------------

1. Load a MusicXML file and count the number of G#'s in it::

    from music21 import *
    aScore = corpus.parseWork("bach/bwv30.6")
    
    # the getPitches() method will get all Pitch objects from all contained
    # Streams and Stream subclasses recursively 

    pitches = aScore.getPitches()
    
    totalGSharps = 0
    for p in pitches:
        if p.name == 'G#':
            totalGSharps += 1
    
    print totalGSharps # returns 28


2. This example searches a Part for a particular chord formation, a dominant seventh, expressed melodically::


    from music21 import *

    op133 = corpus.parseWork('beethoven/opus133.xml') 
    violin2 = op133.getElementById('2nd Violin')
    
    # an empty container for later display
    display = stream.Stream() 
    
    for thisMeasure in violin2.measures:
    
        # get a list of consecutive notes, skipping unisons, octaves,
        # and rests (and putting nothing in their places)
        notes = thisMeasure.findConsecutiveNotes(
        skipUnisons = True, skipOctaves = True, 
        skipRests = True, noNone = True )
        
        pitches = stream.Stream(notes).pitches
        
        for i in range(len(pitches) - 3):
            # makes every set of 4 notes into a whole-note chord
            testChord = chord.Chord(pitches[i:i+4])           
            testChord.duration.type = "whole" 
            
            if testChord.isDominantSeventh():
                # A dominant-seventh chord was found in this measure.
                # We label the chord with the measure number
                # and the first note of the measure with the Forte Prime form
                
                testChord.lyric = "m. " + str(thisMeasure.measureNumber)
                
                primeForm = chord.Chord(thisMeasure.pitches).primeFormString
                firstNote = thisMeasure.notes[0]
                firstNote.lyric = primeForm
                
                # Thus we append the chord in closed position and  then 
                # the measure containing the chord.
                
                chordMeasure = stream.Measure()
                chordMeasure.append(testChord.closedPosition())
                display.append(chordMeasure)
                display.append(thisMeasure)
        
    display.show()


.. image:: images/examples-01.*
    :width: 600

