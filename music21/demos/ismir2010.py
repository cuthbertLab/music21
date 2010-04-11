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
from copy import deepcopy


import music21
from music21 import *
import music21.analysis.metrical

from music21.note import Note
from music21.meter import TimeSignature
from music21.stream import Measure



#-------------------------------------------------------------------------------
def newDots(show=True):

    # alternative chorales:
    # 26.6 : no pickup, eighth notes
    # bach/bwv30.6

    # load a Bach Chorale from the music21 corpus of supplied pieces 
    bwv281 = corpus.parseWork('bach/bwv281.xml')
    
    # get just the bass part using DOM-like method calls
    bass = bwv281.getElementById('Bass')
    
    # apply a Lerdahl/Jackendoff-style metrical analysis to the piece.
    music21.analysis.metrical.labelBeatDepth(bass)
    
    # display measure 0 (pickup) to measure 6 in the default viewer 
    # (here Finale Reader 2009)
    if (show is True):
        bass.getMeasureRange(0,6).show()


def altDots(show=True):
    '''This adds a syncopated bass line.
    '''
    bwv30_6 = corpus.parseWork('bach/bwv30.6.xml')
    bass = bwv30_6.getElementById('Bass')
    excerpt = bass.getMeasureRange(1,10)
    music21.analysis.metrical.labelBeatDepth(excerpt)
    excerpt.show()


    bwv11_6 = corpus.parseWork('bach/bwv11.6.xml')
    alto = bwv11_6.getElementById('Alto')
    excerpt = alto.getMeasureRange(13,20)
    music21.analysis.metrical.labelBeatDepth(excerpt)
    excerpt.show()

    # 13-20

def newDomSev(show=True):
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
          #  the measure containing the chord.
    
          chordMeasure = stream.Measure()
          chordMeasure.append(
            testChord.closedPosition())
          display.append(chordMeasure)
          display.append(thisMeasure)
    
    if (show is True):
        display.show()

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

    
    

    
#def  eventPitchCount(show=True):
#
#    from music21 import corpus
#    from music21.analysis import correlate
#    
#    s = corpus.parseWork('bach/bwv773')
#    na = correlate.NoteAnalysis(s.flat)
#    na.notePitchDurationCount()

def pitchQuarterLengthUsageWeightedScatter(show=True):
    
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


def pitchQuarterLengthUsage3D(show=True):
    
    from music21 import converter, graph
    from music21.musicxml import testFiles as xml
    from music21.humdrum import testFiles as kern

    mozartStream = music21.parse(
        xml.mozartTrioK581Excerpt)
    g = graph.Plot3DBarsPitchSpaceQuarterLength(
        mozartStream.flat.stripTies(), colors=['r'])
    g.process()
    
    chopinStream = music21.parse(kern.mazurka6)
    g = graph.Plot3DBarsPitchSpaceQuarterLength(
        chopinStream.flat.stripTies(), colors=['b']) 
    g.process()
    

#     na1 = correlate.NoteAnalysis(mozartStream.flat)  
#     na1.noteAttributeCount(barWidth=.15, 
#                            colors=['r']) 
#     
#     na2 = correlate.NoteAnalysis(chopinStream.flat)
#     na2.noteAttributeCount(barWidth=.15, 
#                            colors=['b']) 


def messiaen(show = True):
    messiaen = converter.parse('d:/docs/research/music21/ismir-2010/messiaen_valeurs_part2.xml')
    #messiaen = converter.parse('/Volumes/xdisc/_sync/_x/libMusicXML/messiaen/messiaen_valeurs_part2.xml')

    #messiaen.show()
    notes = messiaen.flat.stripTies()
    g = graph.PlotScatterWeightedPitchSpaceQuarterLength(notes, 
        title='Messiaen, Mode de Valeurs', xLog=False)
    
    if (show is True):
        g.process()



funcList = [messiaen, newDomSev, ] #pitchDensity, newDots, pitchDensity]

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def xtestBasic(self):
        '''Test non-showing functions

        removed b/c taking a long time
        '''
        for func in funcList:
            func(show=False)

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        for func in funcList:
            func(show=True)


if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(TestExternal)
    elif len(sys.argv) > 1:
        pass
        #newDots()
        #altDots()
        #pitchDensity()
        #pitchQuarterLengthUsage()
        #messiaen()
        pitchQuarterLengthUsage3D()
