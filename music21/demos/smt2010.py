#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         icmc2010.py
# Purpose:      icmc2010.py
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import unittest, doctest
from music21 import *



# TODO: possibly use more than one example, or more than one encoding
# TODO: remove extraneous print statements in examples?


def ex01(show=True, *arguments, **keywords):
    # This example extracts first a part, then a measure from a complete score. Next, pitches are isolated from this score as pitch classes. Finally, consecutive pitches from this measure are extracted, made into a chord, and shown to be a dominant seventh chord. 
    
    from music21 import corpus, chord

    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parseWork('opus133.xml') # load a MusicXML file

    v2Part = sStream[1].getElementsByClass('Measure') # get all measures from the second violin
    if show:
        v2Part[48].show() # render the 48th measure as notation
    
    # create a list of pitch classes in this measure
    pcGroup = [n.pitchClass for n in v2Part[48].pitches] 

    if show:
        print(pcGroup) # display the collected pitch classes as a list
    # extract from the third pitch until just before the end
    pnGroup = [n.nameWithOctave for n in v2Part[48].pitches[2:-1]] 
    qChord = chord.Chord(pnGroup) # create a chord from these pitches
    
    if show:
        qChord.show() # render this chord as notation
        print(qChord.isDominantSeventh()) # find if this chord is a dominant
    



def ex02(show=True, *arguments, **keywords):

    
    # This example searches the second violin part for adjacent non-redundant pitch classes that form dominant seventh chords.
    
    from music21 import corpus, chord, stream
    
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parseWork('opus133.xml') # load a MusicXML file

    v2Part = sStream[1].getElementsByClass('Measure') # get all measures from the first violin
    
    # First, collect all non-redundant adjacent pitch classes, and store these pitch classes in a list. 
    pitches = []
    for i in range(len(v2Part.pitches)):
        pn = v2Part.pitches[i].name
        if i > 0 and pitches[-1] == pn: continue
        else: pitches.append(pn)
    
    # Second, compare all adjacent four-note groups of pitch classes and determine which are dominant sevenths; store this in a list and display the results. 
    found = stream.Stream()
    for i in range(len(pitches)-3):
        testChord = chord.Chord(pitches[i:i+4])
        if testChord.isDominantSeventh():
            found.append(testChord)
    if show:
        found.show()
    
   

def ex03(show=True, *arguments, **keywords):
    
    # This examples graphs the usage of pitch classes in the first and second violin parts. 
    
    from music21 import corpus, graph
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parseWork('opus133.xml') # load a MusicXML file

    # Create a graph of pitch class for the first and second part
    for part in [sStream[0], sStream[1]]:
        g = graph.PlotHistogramPitchClass(part, title=part.getInstrument().partName)
        if show:
            g.process()

    



def ex04(show=True, *arguments, **keywords):
    
    # This example, by graphing pitch class over note offset, shows the usage of pitch classes in the violoncello part over the duration of the composition. While the display is coarse, it is clear that the part gets less chromatic towards the end of the work.
    
    from music21 import corpus
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parseWork('opus133.xml') # load a MusicXML file

    # note: measure numbers are not being shown correcntly
    # need to investigate
    part = sStream[3]


    g = graph.PlotScatterPitchClassOffset(part.flat,
                 title=part.getInstrument().partName)
    if show:
        g.process()





#-------------------------------------------------------------------------------

def ex01Alt(show=True, *arguments, **keywords):
    # measure here is a good test of dynamics positioning:
    from music21 import corpus, chord
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parseWork('opus133.xml') # load a MusicXML file
    v2Part = sStream[1].getElementsByClass('Measure') # get all measures from the second violin

    if show:
        v2Part[45].show() # render the 48th measure as notation



def findHighestNotes(show=True, *arguments, **keywords):
    import copy
    import music21
    from music21 import corpus, meter, stream
    
    score = corpus.parseWork('bach/bwv366.xml')
    ts = score.flat.getElementsByClass(meter.TimeSignature)[0]
    # use default partitioning
    #ts.beatSequence.partition(3)
    
    found = stream.Stream()
    for part in score.getElementsByClass(stream.Part):
        found.append(part.flat.getElementsByClass(music21.clef.Clef)[0])
        highestNoteNum = 0
        for m in part.getElementsByClass('Measure'):
            for n in m.notes:
                if n.midi > highestNoteNum:
                    highestNoteNum = n.midi
                    highestNote = copy.deepcopy(n) # optional
    
                    # These two lines will keep the look of the original
                    # note values but make each note 1 4/4 measure long:
    
                    highestNote.duration.components[0].unlink()
                    highestNote.quarterLength = 4
                    highestNote.lyric = '%s: M. %s: beat %s' % (
                        part.getInstrument().partName[0], m.number, ts.getBeat(n.offset))
        found.append(highestNote)

    if show:
        print (found.write('musicxml'))
    else:
        mx = found.musicxml


def ex1_revised(show=True, *arguments, **keywords):
    if 'op133' in keywords.keys():
        beethovenScore = keywords['op133']
    else:
        beethovenScore = corpus.parseWork('opus133.xml') # load a MusicXML file

    violin2 = beethovenScore[1]      # most programming languages start counting from 0, 
    #  so part 0 = violin 1, part 1 = violin 2, etc.
    display = stream.Stream() # an empty container for filling with found notes
    for thisMeasure in violin2.getElementsByClass('Measure'):
        notes = thisMeasure.findConsecutiveNotes(skipUnisons = True, 
                      skipChords = True,
                       skipOctaves = True, skipRests = True, noNone = True )
        pitches = [n.pitch for n in notes]
        for i in range(len(pitches) - 3):
            testChord = chord.Chord(pitches[i:i+4])
            testChord.duration.type = "whole"
            if testChord.isDominantSeventh() is True:
                # since a chord was found in this measure, append the found pitches in closed position
                testChord.lyric = "m. " + str(thisMeasure.number)
                emptyMeasure = stream.Measure()
                emptyMeasure.append(testChord.closedPosition())
                display.append(emptyMeasure)
    
                # append the whole measure as well, tagging the first note of the measure with an
                # ordered list of all the pitch classes used in the measure.
                pcGroup = [p.pitchClass for p in thisMeasure.pitches]
                firstNote = thisMeasure.getElementsByClass(note.Note)[0]
                firstNote.lyric = str(sorted(set(pcGroup)))
                thisMeasure.setRightBarline("double")
                display.append(thisMeasure)
    
    if show:
        display.write('musicxml')
    
def findPotentialPassingTones(show = True):
    g = corpus.parseWork('gloria')
    gcn = g.parts['cantus'].measures(1,126).flat.notes

    gcn[0].lyric = ""
    gcn[-1].lyric = ""
    for i in range(1, len(gcn) - 1):
        prev = gcn[i-1]
        cur  = gcn[i]
        next = gcn[i+1]
        
        cur.lyric = ""
        
        if "Rest" in prev.classes or "Rest" in cur.classes \
            or "Rest" in next.classes:
            continue
        
        int1 = interval.notesToInterval(prev, cur)
        if int1.isStep is False:
            continue
        
        int2 = interval.notesToInterval(cur, next)
        if int2.isStep is False:
            continue
            
        cma = cur.beatStrength 
        if cma < 1 and \
            cma <= prev.beatStrength and \
            cma <= next.beatStrength: 

            if int1.direction == int2.direction:
                cur.lyric = 'pt' # neighbor tone
            else:
                cur.lyric = 'nt' # passing tone
    if show:   
        g.parts['cantus'].show()


def demoJesse(show=True):
    luca = corpus.parseWork('luca/gloria')
    for n in luca.measures(2, 20).flat.notes:
        if n.isRest is False:
            n.lyric = n.pitch.german
    if show:   
        luca.show()
    else:
        mx = luca.musicxml

#-------------------------------------------------------------------------------
# new examples


def corpusSearch():

    from music21 import corpus
    from music21.analysis import discrete

    parsedStream = {}

    sa = discrete.SadoianAmbitus()

    def getStream(fp, n):
        if fp not in parsedStream.keys():
            s = converter.parse(fp)
            parsedStream[fp] = s
        else:   
            s = parsedStream[fp]
        if n != None: # get from opus
            s = s.getScoreByNumber(n)
        return s

    # Shanbei: region in northwestern china
    # qitai: on the silk road
    post = corpus.search('qitai', 'locale')
    for fp, n in post:
        print fp, n
        s = getStream(fp, n)        
        print sa.getPitchRanges(s), s.flat.getElementsByClass('KeySignature')[0]

    print
    post = corpus.search('hequ', 'locale')
    for fp, n in post:
        print fp, n
        s = getStream(fp, n)        
        print sa.getPitchRanges(s), s.flat.getElementsByClass('KeySignature')[0]

    print
    post = corpus.search('suzhou', 'locale')
    for fp, n in post:
        print fp, n
        s = getStream(fp, n)        
        print sa.getPitchRanges(s), s.flat.getElementsByClass('KeySignature')[0]

    #s.show()




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''Test non-showing functions
        '''
        # beethoven examples are commented out for time
        # findPassingTones too
        #sStream = corpus.parseWork('opus133.xml') # load a MusicXML file
        # ex03, ex01, ex02, ex04, ex01Alt, findHighestNotes,ex1_revised
        #for func in [findPotentialPassingTones]:
        for func in [findHighestNotes, demoJesse]:

            pass
            #func(show=False, op133=sStream)
            func(show=False)



if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        corpusSearch()

