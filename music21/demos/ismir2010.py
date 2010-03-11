#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         ismir2010.py
# Purpose:      ismir2010.py
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

import music21
from music21 import humdrum
from music21.note import Note
from music21.meter import TimeSignature
from music21.stream import Measure
from copy import deepcopy

def bergEx01(show=True):
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
    if show:
        score.show()
   
    ts = score.getElementsByClass(TimeSignature)[0]
   
# TODO: what is the best way to do this now that 
# this raises a TupletException for being frozen?
#     for thisNote in score.flat.getNotes():
#         thisNote.duration.tuplets[0].setRatio(12, 8)

    for thisMeasure in score.getElementsByClass(Measure):
        thisMeasure.insertAtIndex(0, deepcopy(ts))
        thisMeasure.makeBeams()

    if show:
        score.show()




def melodicChordExpression(show=True):
    #from music21 import *
    from music21 import corpus, stream, chord
    beethovenScore = corpus.parseWork(
                  'beethoven/opus133.xml') 
    # parts are given IDs by the MusicXML part name 
    violin2 = beethovenScore.getElementById(
                            '2nd Violin')
    # create an empty container for storing found notes
    display = stream.Stream() 
    
    for measure in violin2.measures:
        notes = measure.findConsecutiveNotes(
            skipUnisons=True, skipChords=True, 
            skipOctaves=True, skipRests=True, 
            noNone=True)
        pitches = [n.pitch for n in notes]
        # examine four-note gruops 
        for i in range(len(pitches) - 3):
            testChord = chord.Chord(pitches[i:i+4])           
            # modify duration for final presentation
            testChord.duration.type = "whole" 
            if testChord.isDominantSeventh():
                # append the found pitches as chord
                testChord.lyric = "m. " + str(
                    measure.measureNumber)
                # store the chord in a measure
                emptyMeasure = stream.Measure()
                emptyMeasure.append(
                   testChord.closedPosition())
                display.append(emptyMeasure)
                # append the source measure, tagging 
                # the first note of the measure with a list
                # of all pitch classes used in the measure.
                measure.notes[0].lyric = chord.Chord(
                    measure.pitches).orderedPitchClassesString
                display.append(measure)
    # showing the complete Stream will produce output
    if show:
        display.show('musicxml')
    
    
    
def  pitchDensity(show=True):

    from music21 import corpus
    from music21.analysis import correlate
    
    beethovenScore = corpus.parseWork('opus133.xml')
    celloPart = beethovenScore.getElementById('Cello')
    
    # given a "flat" view of the stream, with nested information removed and all information at the same hierarchical level, combine tied notes into single notes with summed durations
    notes = celloPart.flat.stripTies()
    
    # NoteAnalysis objects permit graphing attributes of a Stream of notes
    na = correlate.NoteAnalysis(notes) 
    # calling noteAttributeScatter() with x and y values as named attributes returns a graph 
    if show:
        na.noteAttributeScatter('offset', 'pitchClass')
    
    

# Two graph improvements: I'd really like Figure 6 (the 3d graphs) to use the
# log(base2) of the quarter-length, because it's really hard to see the
# differences between eighth notes and dotted sixteenths, etc. I think it will
# make the graphs clearer.  Similarly, it'd be really great if Figure 4 at least
# used flats instead of sharps (it is the Grosse Fuge in B-flat, not A#!), but
# maybe it'd be good to plot Name against Offset that way we separate A#s from
# Bbs -- it would probably make the results even more convincing (though the
# graph would be bigger). 


    
def  eventPitchCount(show=True):

    from music21 import corpus
    from music21.analysis import correlate
    
    s = corpus.parseWork('bach/bwv773')
    na = correlate.NoteAnalysis(s.flat)
    na.notePitchDurationCount()


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def xtestBasic(self):
        '''Test non-showing functions

        removed b/c taking a long time
        '''
        for func in [bergEx01, melodicChordExpression, pitchDensity]:
            func(show=False)

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


