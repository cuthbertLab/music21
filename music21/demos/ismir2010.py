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
import sys

import music21
from music21 import humdrum
from music21.note import Note
from music21.meter import TimeSignature
from music21.stream import Measure
from copy import deepcopy




#-------------------------------------------------------------------------------
# not being used

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



#-------------------------------------------------------------------------------



def melodicChordExpression(show=True):
    '''This method not only searches the entire second violin part of a complete string quarter for a seventh chord expressed melodically, but creates new notation to display the results with analytical markup. 
    '''
    #from music21 import *
    from music21 import corpus, stream, chord
    beethovenScore = corpus.parseWork(
                  'beethoven/opus133.xml') 
    # parts are given IDs by the MusicXML part name 
    violin2 = beethovenScore.getElementById(
                            '2nd Violin')
    # create an empty container for storing found notes
    display = stream.Stream() 
    
    # iterate over all measures
    for measure in violin2.measures:
        notes = measure.findConsecutiveNotes(
            skipUnisons=True, skipChords=True, 
            skipOctaves=True, skipRests=True, 
            noNone=True)
        pitches = [n.pitch for n in notes]
        # examine four-note gruops, where i is the first of four
        for i in range(len(pitches) - 3):
            # createa chord from four pitches
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
                # the first note with the pitch classes used in the measure
                measure.notes[0].lyric = chord.Chord(
                    measure.pitches).orderedPitchClassesString
                display.append(measure)
    # showing the complete Stream will produce output
    if show:
        display.show('musicxml')
    
    
    
def  pitchDensity(show=True):

    from music21 import corpus, graph
    
    beethovenScore = corpus.parseWork('opus133.xml')
    celloPart = beethovenScore.getElementById('Cello')
    
    #First, we take a "flat" view of the Stream, which removes nested containers such as Measures. Second, we combine tied notes into single notes with summed durations.
    
    notes = celloPart.flat.stripTies()
    g = graph.PlotScatterPitchClassOffset(notes, 
        title='Beethoven Opus 133, Cello', alpha=.2)
    g.process()

    
    

# Two graph improvements: I'd really like Figure 6 (the 3d graphs) to use the
# log(base2) of the quarter-length, because it's really hard to see the
# differences between eighth notes and dotted sixteenths, etc. I think it will


#     
# def eventPitchCount(show=True):
# 
#     from music21 import corpus
#     from music21.analysis import correlate
#     
#     s = corpus.parseWork('bach/bwv773')
#     na = correlate.NoteAnalysis(s.flat)
#     na.notePitchDurationCount()
# 



def pitchQuarterLengthUsage(show=True):
    
    from music21 import converter, graph
    from music21.musicxml import testFiles as xml
    from music21.humdrum import testFiles as kern
    
    mozartStream = converter.parse(xml.mozartTrioK581Excerpt)
    notes = mozartStream.flat.stripTies()
    g = graph.PlotScatterWeightedPitchSpaceQuarterLength(notes, 
        title='Mozart Trio K. 581 Excerpt')
    g.process()
    
    g = graph.PlotScatterWeightedPitchClassQuarterLength(notes, 
        title='Mozart Trio K. 581 Excerpt')
    g.process()
    
    
    chopinStream = converter.parse(kern.mazurka6) 
    notes = chopinStream.flat.stripTies()
    g = graph.PlotScatterWeightedPitchSpaceQuarterLength(notes,
        title='Chopin Mazurka 6 Excerpt')
    g.process()
    
    g = graph.PlotScatterWeightedPitchClassQuarterLength(notes,
        title='Chopin Mazurka 6 Excerpt')
    g.process()


#     na1 = correlate.NoteAnalysis(mozartStream.flat)  
#     na1.noteAttributeCount(barWidth=.15, 
#                            colors=['r']) 
#     
#     na2 = correlate.NoteAnalysis(chopinStream.flat)










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

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        pass
        #pitchDensity()
        #pitchQuarterLengthUsage()