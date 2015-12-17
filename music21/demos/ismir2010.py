# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         ismir2010.py
# Purpose:      Examples for ISMIR 2010 paper
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-10 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------

import unittest

from music21 import corpus, converter, stream, chord, graph, meter, pitch
import music21.analysis.metrical



import os

#-------------------------------------------------------------------------------
def newDots(show=True):

    # alternative chorales:
    # 26.6 : no pickup, eighth notes
    # bach/bwv30.6

    # load a Bach Chorale from the music21 corpus of supplied pieces 
    bwv281 = corpus.parse('bach/bwv281.xml')
    
    # get just the bass part using DOM-like method calls
    bass = bwv281.getElementById('Bass')
    
    # apply a Lerdahl/Jackendoff-style metrical analysis to the piece.
    music21.analysis.metrical.labelBeatDepth(bass)
    
    # display measure 0 (pickup) to measure 6 in the default viewer 
    # (here Finale Reader 2009)
    if (show is True):
        bass.measures(0,6).show()


def altDots(show=True):
    '''This adds a syncopated bass line.
    '''
    bwv30_6 = corpus.parse('bach/bwv30.6.xml')
    bass = bwv30_6.getElementById('Bass')
    excerpt = bass.measures(1,10)
    music21.analysis.metrical.labelBeatDepth(excerpt)
    if (show is True):
        excerpt.show()


    bwv11_6 = corpus.parse('bach/bwv11.6.xml')
    alto = bwv11_6.getElementById('Alto')
    excerpt = alto.measures(13,20)
    music21.analysis.metrical.labelBeatDepth(excerpt)
    if (show is True):
        excerpt.show()

    # 13-20

def newDomSev(show=True):
    op133 = corpus.parse('beethoven/opus133.xml') 
    violin2 = op133.getElementById('2nd Violin')
    
    # an empty container for later display
    display = stream.Stream() 
    
    for thisMeasure in violin2.getElementsByClass('Measure'):
    
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
            
                testChord.lyric = "m. " + str(thisMeasure.number)
              
                primeForm = chord.Chord(thisMeasure.pitches).primeFormString
                firstNote = thisMeasure.notesAndRests[0]
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
    #from music21 import corpus, stream, chord
    beethovenScore = corpus.parseWork(
                  'beethoven/opus133.xml') 
    # parts are given IDs by the MusicXML part name 
    violin2 = beethovenScore.getElementById(
                            '2nd Violin')
    # create an empty container for storing found notes
    display = stream.Stream() 
    
    # iterate over all measures
    for measure in violin2.getElementsByClass('Measure'):
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
                    measure.number)
                # store the chord in a measure
                emptyMeasure = stream.Measure()
                emptyMeasure.append(
                   testChord.closedPosition())
                display.append(emptyMeasure)
                # append the source measure, tagging 
                # the first note with the pitch classes used in the measure
                measure.notesAndRests[0].lyric = chord.Chord(
                    measure.pitches).orderedPitchClassesString
                display.append(measure)
    # showing the complete Stream will produce output
    if show:
        display.show('musicxml')
    
    
    
def  pitchDensity(show=True):

    #from music21 import corpus, graph
    
    beethovenScore = corpus.parse('beethoven/opus133.xml')
    celloPart = beethovenScore.getElementById('Cello')
    
    #First, we take a "flat" view of the Stream, which removes nested containers such as Measures. Second, we combine tied notes into single notes with summed durations.
    
    notes = celloPart.flat.stripTies()
    g = graph.PlotScatterPitchClassOffset(notes, 
        title='Beethoven Opus 133, Cello', alpha=.2)
    g.process()

    
    


def pitchQuarterLengthUsageWeightedScatter(show=True):
    
    #from music21 import converter, graph
    from music21.musicxml import testFiles as xml
    from music21.humdrum import testFiles as kern
    
    mozartStream = converter.parse(xml.mozartTrioK581Excerpt) # @UndefinedVariable
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
    from music21.musicxml import testFiles as xml
    from music21.humdrum import testFiles as kern

    mozartStream = converter.parse(
        xml.mozartTrioK581Excerpt) # @UndefinedVariable
    g = graph.Plot3DBarsPitchSpaceQuarterLength(
        mozartStream.flat.stripTies(), colors=['r'])
    g.process()
    
    chopinStream = converter.parse(kern.mazurka6)
    g = graph.Plot3DBarsPitchSpaceQuarterLength(
        chopinStream.flat.stripTies(), colors=['b']) 
    g.process()
    




def messiaen(show = True):
    #messiaen = #converter.parse('d:/docs/research/music21/ismir-2010/messiaen_valeurs_part2.xml')
    #messiaen = converter.parse('/Volumes/xdisc/_sync/_x/libMusicXML/messiaen/messiaen_valeurs_part2.xml')
    mall = converter.parse('/Users/cuthbert/desktop/messiaen_valeurs_2012.xml')
    messiaenP = mall[1]
    #messiaen.show()
    notes = messiaenP.flat.stripTies()
    g = graph.PlotScatterWeightedPitchSpaceQuarterLength(notes, 
        title='Messiaen, Mode de Valeurs', xLog=False)
    
    if (show is True):
        g.process()



def schumann(show = True):
    streamObject = corpus.parse('schumann/opus41no1', 3)
    streamObject.plot('pitch')

    from music21.humdrum import testFiles as tf
    streamObject = converter.parse(tf.mazurka6)
    streamObject.plot('pitch')





















#------------------------------------------------------------------------------





# minor mode bach chorales
# >>> s = corpus.parse('bwv227.7')

# this has bad beaming
# move to relative major
# ends on major I


# >>> s = corpus.parse('bwv103.6')
# 4/4, good beaming, has pickup
# b minor, momves to D major, ends on major I
# 16 measures
# 4/4

# >>> s = corpus.parse('bwv18.5-lz')
# a minor, good amount of minor iv, ends on major 1
# 17 measures


def demoGettingWorks():
    

    # Can obtain works from an integrated corpus 
    unused_s1 = corpus.parse('bach/bwv103.6') # @UnusedVariable
    unused_s2 = corpus.parse('bach/bwv18.5-lz') # @UnusedVariable

    # Can parse data stored in MusicXML files locally or online:
    unused_s = converter.parse('http://www.musicxml.org/xml/elite.xml') # @UnusedVariable

    # Can parse data stored in MIDI files locally or online:
    unused_s = converter.parse('http://www.jsbchorales.net/down/midi/010306b_.mid') # @UnusedVariable



def demoBasic():

    # A score can be represented as a Stream of Parts and Metadata
    s1 = corpus.parse('bach/bwv103.6')

    # We can show() a Stream in a variety of forms
    #s1.show()
    #s1.show('midi') # has errors!
    #s1.show('text') # too long here

    # Can get the number of Elements as a length, and iterate over Elements
    len(s1)

    # Can grab polyphonic Measure range;

    # Can get sub-components through class or id filtering
    soprano = s1.getElementById('soprano')


    # Can employ the same show() method on any Stream or Stream subclass
    #soprano.show()
    #soprano.show('midi') # problem is here: offset is delayed

    # A Part might contain numerous Measure Streams
    len(soprano.getElementsByClass('Measure'))
    unused_mRange = soprano.measures(14,16) # @UnusedVariable
    #mRange.show()
    # mRange.sorted.show('text') # here we can see this



    sNew = soprano.measures(14,16).flat.notesAndRests.transpose('p-5')
    sNew.makeAccidentals(overrideStatus=True)
    ts1 = meter.TimeSignature('3/4')
    ts2 = meter.TimeSignature('5/8')
    sNew.insert(0, ts1)
    sNew.insert(3, ts2)

    #sNew.show()
    

    sNew.augmentOrDiminish(2, inPlace=True)  
    for n in sNew.notesAndRests:
        if n.pitch.name == 'G' and n.quarterLength == 2:
            n.addLyric('%s (2 QLs)' % n.name)
    sNew.show()

    # Any stream can be flattened to remove all hierarchical levels
    # All notes of a part can be gathered into a single Stream
#     sNotes = soprano.flat.notesAndRests
# 
#     # Can add notation elements or other objects by appending to a Stream
#     sNotes.insert(0, meter.TimeSignature('3/4'))
# 
#     # Can create a new, transformed Stream by looking for Fermatas and extending them
#     sExtended = stream.Stream()
#     sExtended.insert(0, meter.TimeSignature('6/4'))
#     for n in sNotes.notesAndRests:
#         #if isinstance(n.expressions[0], expressions.Fermata):
#         if len(n.expressions) > 0:
#             n.duration.quarterLength = 4
#             sExtended.append(n)
#         else:
#             sExtended.append(n)
#     #sExtended.show()
# 


def beethovenSearch():
    op133 = corpus.parse('beethoven/opus133.xml') 
    violin2 = op133.getElementById('2nd Violin')
    
    # an empty container for later display
    display = stream.Stream() 
    
    for m in violin2.getElementsByClass('Measure'):
        notes = m.findConsecutiveNotes(
                                       skipUnisons=True, skipOctaves=True, 
                                       skipRests=True, noNone=True )
     
        pitches = stream.Stream(notes).pitches  
        for i in range(len(pitches) - 3):
        # makes every set of 4 notes into a whole-note chord
            testChord = chord.Chord(pitches[i:i+4])       
            testChord.duration.type = "whole" 
        
            if testChord.isDominantSeventh():
                testChord.lyric = "m. " + str(m.number)
                m.notesAndRests[0].lyric = chord.Chord(m.pitches).primeFormString
                   
                chordMeasure = stream.Measure()
                chordMeasure.append(testChord.closedPosition())
                display.append(chordMeasure)
                display.append(m)    
    display.show()



def demoGraphMessiaen():
    # use Messiaen, ciconia, bach

    #fp = '/Volumes/xdisc/_sync/_x/libMusicXML/messiaen/messiaen_valeurs_part2.xml'
    fp = '/Users/cuthbert/desktop/messiaen_valeurs_2012.xml'
    dpi = 300
    part = 2

    pieceTitle = 'Messiaen, Mode de valeurs..., Part ' + str(part + 1)

    s = converter.parse(fp).parts[part].stripTies()

    s.plot('histogram', 'pitchspace', dpi=dpi, title='Pitch Space Usage, %s' % pieceTitle)

    s.plot('histogram', 'pitchclass', dpi=dpi, title='Pitch Class Usage, %s' % pieceTitle)


    s.plot('scatter', values=['pitchclass', 'offset'], dpi=dpi, title='Pitch Class By Measure, %s' % pieceTitle)

    s.plot('horizontalBar', values=['pitch', 'offset'], dpi=dpi, title='Pitch By Measure, %s' % pieceTitle)


    s.plot('scatterweighted', values=['pitch', 'quarterlength'], dpi=dpi, title='Pitch and Duration, %s' % pieceTitle, xLog=False)

    # s.getMeasuresRange(10,20)plot('PlotHorizontalBarPitchSpaceOffset')
    # s.plot('PlotScatterWeightedPitchSpaceQuarterLength')


def demoGraphMessiaenBrief():
    # use Messiaen, ciconia, bach
    fp = '/Volumes/xdisc/_sync/_x/libMusicXML/messiaen/messiaen_valeurs_part2.xml'
    dpi = 600

    #pieceTitle = 'Messiaen, Mode de valeurs..., Part 2'

    s = converter.parse(fp).stripTies()


    #s.plot('scatter', values=['pitchclass', 'offset'], dpi=dpi)

    s.plot('scatterweighted', title='', colorGrid=None, values=['pitch', 'quarterlength'], dpi=dpi, xLog=False)



def demoGraphBach():

    dpi = 300

    # loping off first measure to avoid pickup
    s1 = corpus.parse('bach/bwv103.6').measures(1,None)
    s2 = corpus.parse('bach/bwv18.5-lz').measures(1,None)

    s1.plot('key', dpi=dpi, title='Windowed Key Analysis, Bach, BWV 103.6', windowStep='pow2')
    s2.plot('key', dpi=dpi, title='Windowed Key Analysis, Bach, BWV 18.5', windowStep='pow2')



def demoGraphMozartChopin():
    from music21.musicxml import testFiles as xmlTest
    from music21.humdrum import testFiles as kernTest  

    dpi = 300

    mozartStream = converter.parse(xmlTest.mozartTrioK581Excerpt) # @UndefinedVariable
    g = graph.Plot3DBarsPitchSpaceQuarterLength(mozartStream.stripTies(), dpi=dpi, title='Mozart Trio K. 581, Excerpt', colors=['#CD4F39'], alpha=.8)
    g.process()
    
    chopinStream = converter.parse(kernTest.mazurka6) 
    g = graph.Plot3DBarsPitchSpaceQuarterLength(chopinStream.stripTies(), dpi=dpi, title='Chopin Mazurka 6, Excerpt', colors=['#6495ED'], alpha=.8)
    g.process()



def demoBeethoven133():

    dpi = 300

    sStream = corpus.parse('opus133.xml') # load a MusicXML file
    part = sStream['cello'].stripTies()

    part.plot('scatter', values=['pitchclass', 'offset'],
                 title='Beethoven, Opus 133, Cello', dpi=dpi)



def demoCombineTransform():
    from music21 import interval

    s1 = corpus.parse('bach/bwv103.6')
    s2 = corpus.parse('bach/bwv18.5-lz')

    keyPitch1 = s1.analyze('key')[0]
    unused_gap1 = interval.Interval(keyPitch1, pitch.Pitch('C'))

    keyPitch2 = s2.analyze('key')[0]
    unused_gap2 = interval.Interval(keyPitch2, pitch.Pitch('C'))

    sCompare = stream.Stream()
    sCompare.insert(0, s1.parts['bass'])
    sCompare.insert(0, s2.parts['bass'])

    sCompare.show()

    # attach interval name to lyric
    # attach pitch class

def demoBachSearch():

    import random
    from music21 import key
    
    fpList = corpus.getBachChorales('.xml')
    random.shuffle(fpList)
    results = stream.Stream()

    for fp in fpList[:40]:
        fn = os.path.split(fp)[1]
        print (fn)
        s = converter.parse(fp)
        # get key, mode
        key, mode = s.analyze('key')[:2]
        if mode == 'minor':
            pFirst = []
            pLast = []

            for pStream in s.parts:
                # clear accidental display status
                pFirst.append(pStream.flat.getElementsByClass('Note')[0].pitch)
                pLast.append(pStream.flat.getElementsByClass('Note')[-1].pitch)

            cFirst = chord.Chord(pFirst)
            cFirst.quarterLength = 2
            cFirst.transpose(12, inPlace=True)
            cFirst.addLyric(fn)
            cFirst.addLyric('%s %s' % (key, mode))

            cLast = chord.Chord(pLast)
            cLast.quarterLength = 2
            cLast.transpose(12, inPlace=True)
            if cLast.isMajorTriad():
                cLast.addLyric('M')
            elif cLast.isMinorTriad():
                cLast.addLyric('m')
            else:
                cLast.addLyric('?')
        
            m = stream.Measure()
            m.keySignature = s.flat.getElementsByClass('KeySignature')[0]

            print ('got', m.keySignature)

            m.append(cFirst)
            m.append(cLast)
            results.append(m.makeAccidentals(inPlace=True))

    results.show()


def demoBachSearchBrief():    
    choraleList = corpus.getBachChorales()
    results = stream.Stream()
    for filePath in choraleList:
        fileName = os.path.split(filePath)[1]
        pieceName = fileName.replace('.xml', '')
        chorale = converter.parse(filePath)
        print (fileName)
        key = chorale.analyze('key')
        if key.mode == 'minor':
            lastChordPitches = []
            for part in chorale.parts:
                lastChordPitches.append(part.flat.pitches[-1])
            lastChord = chord.Chord(lastChordPitches)
            lastChord.duration.type = "whole"
            lastChord.transpose("P8", inPlace=True)
            if lastChord.isMinorTriad() is False and lastChord.isIncompleteMinorTriad() is False:
                continue
            lastChord.lyric = pieceName
            m = stream.Measure()
            m.keySignature = chorale.flat.getElementsByClass(
              'KeySignature')[0]
            m.append(lastChord)
            results.append(m.makeAccidentals(inPlace=True))
    results.show()

















#------------------------------------------------------------------------------
funcList = [newDots, altDots ] #pitchDensity, newDots, pitchDensity]

slow = [newDomSev, melodicChordExpression, pitchDensity]

dependent = [messiaen ]


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''ismir2010: Test non-showing functions

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
    pass
    #newDots()
    #altDots()
    #pitchDensity()
    #pitchQuarterLengthUsage()
    #messiaen()
    #pitchQuarterLengthUsage3D()


    #demoSearch()

    #demoBasic()
    #demoCombineTransform()

    #demoSearch()

    #demoGraphMessiaen()

    #demoGraphBach()



    #demoGraphMozartChopin()


    #demoBeethoven133()

    #beethovenSearch()

    #demoBachSearchBrief()

    #demoGraphMessiaenBrief()
    demoGraphMessiaen()

#------------------------------------------------------------------------------
# eof

