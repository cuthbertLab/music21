# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         smt2010.py
# Purpose:      Demonstrations for the SMT 2010 poster session
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-10, 2014 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------


import unittest
from music21 import corpus, converter, note, chord, stream, environment, graph, interval, meter

_MOD = 'demo/smt2010.py'
environLocal = environment.Environment(_MOD)



def ex01(show=True, *arguments, **keywords):
    '''
    This example extracts first a part, then a measure from a complete score. 
    Next, pitches are isolated from this score as pitch classes. 
    Finally, consecutive pitches from this measure are extracted, made into a chord, 
    and shown to be a dominant seventh chord. 
    '''

    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parse('opus133.xml') # load a MusicXML file

    v2Part = sStream.parts[1].getElementsByClass('Measure') 
    # get all measures from the second violin
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
    '''
    This example searches the second violin part for adjacent non-redundant 
    pitch classes that form dominant seventh chords.
    '''

    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parse('opus133.xml') # load a MusicXML file

    v2Part = sStream.parts[1].getElementsByClass('Measure') 
        # get all measures from the second violin
    
    # First, collect all non-redundant adjacent pitch classes, and 
    # store these pitch classes in a list. 
    pitches = []
    for i in range(len(v2Part.pitches)):
        pn = v2Part.pitches[i].name
        if i > 0 and pitches[-1] == pn:
            continue
        else: 
            pitches.append(pn)
    
    # Second, compare all adjacent four-note groups of pitch classes and 
    # determine which are dominant sevenths; store this in a list and display the results. 
    found = stream.Stream()
    for i in range(len(pitches)-3):
        testChord = chord.Chord(pitches[i:i+4])
        if testChord.isDominantSeventh():
            found.append(testChord)
    if show:
        found.show()
    
   

def ex03(show=True, *arguments, **keywords):
    
    # This examples graphs the usage of pitch classes in the first and second violin parts. 
    
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parse('opus133.xml') # load a MusicXML file

    # Create a graph of pitch class for the first and second part
    for part in [sStream[0], sStream[1]]:
        g = graph.PlotHistogramPitchClass(part, title=part.partName)
        if show:
            g.process()

    



def ex04(show=True, *arguments, **keywords):
    '''
    This example, by graphing pitch class over note offset, 
    shows the usage of pitch classes in the violoncello part 
    over the duration of the composition. While the display is coarse, 
    it is clear that the part gets less chromatic towards the end of the work.
    '''
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parse('opus133.xml') # load a MusicXML file

    # note: measure numbers are not being shown correctly
    # need to investigate
    part = sStream.parts[3]


    g = graph.PlotScatterPitchClassOffset(part.flat, title=part.partName)
    if show:
        g.process()





#-------------------------------------------------------------------------------

def ex01Alt(show=True, *arguments, **keywords):
    # measure here is a good test of dynamics positioning:
    if 'op133' in keywords.keys():
        sStream = keywords['op133']
    else:
        sStream = corpus.parse('opus133.xml') # load a MusicXML file
    v2Part = sStream.parts[1].getElementsByClass('Measure') 
        # get all measures from the second violin

    if show:
        v2Part[45].show() # render the 48th measure as notation



def findHighestNotes(show=True, *arguments, **keywords):
    import copy
    
    score = corpus.parse('bach/bwv366.xml')
    ts = score.flat.getElementsByClass(meter.TimeSignature)[0]
    # use default partitioning
    #ts.beatSequence.partition(3)
    
    found = stream.Stream()
    for part in score.getElementsByClass(stream.Part):
        found.append(part.flat.getElementsByClass('Clef')[0])
        highestNoteNum = 0
        for m in part.getElementsByClass('Measure'):
            for n in m.notes:
                if n.pitch.midi > highestNoteNum:
                    highestNoteNum = n.pitch.midi
                    highestNote = copy.deepcopy(n) # optional
    
                    # These two lines will keep the look of the original
                    # note values but make each note 1 4/4 measure long:
    
                    highestNote.duration.linked = False
                    highestNote.quarterLength = 4.0
                    highestNote.lyric = '%s: M. %s: beat %s' % (
                        part.partName[0], m.number, ts.getBeat(n.offset))
        found.append(highestNote)

    if show:
        found.show('musicxml')


def ex1_revised(show=True, *arguments, **keywords):
    if 'op133' in keywords.keys():
        beethovenScore = keywords['op133']
    else:
        beethovenScore = corpus.parse('opus133.xml') # load a MusicXML file

    violin2 = beethovenScore[1]      # most programming languages start counting from 0, 
    #  so part 0 = violin 1, part 1 = violin 2, etc.
    display = stream.Stream() # an empty container for filling with found notes
    for thisMeasure in violin2.getElementsByClass('Measure'):
        notes = thisMeasure.findConsecutiveNotes(skipUnisons=True, 
                                                 skipChords=True,
                                                 skipOctaves=True, 
                                                 skipRests=True, 
                                                 noNone=True )
        pitches = [n.pitch for n in notes]
        for i in range(len(pitches) - 3):
            testChord = chord.Chord(pitches[i:i+4])
            testChord.duration.type = "whole"
            if testChord.isDominantSeventh() is True:
                # since a chord was found in this measure, 
                # append the found pitches in closed position
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
        display.show('musicxml')
    
def findPotentialPassingTones(show=True):
    g = corpus.parse('gloria')
    gcn = g.parts['cantus'].measures(1,126).flat.notesAndRests

    gcn[0].lyric = ""
    gcn[-1].lyric = ""
    for i in range(1, len(gcn) - 1):
        prev = gcn[i-1]
        cur  = gcn[i]
        nextN = gcn[i+1]  
        
        cur.lyric = ""
        
        if ("Rest" in prev.classes or 
            "Rest" in cur.classes or 
            "Rest" in nextN.classes):
            continue
        
        int1 = interval.notesToInterval(prev, cur)
        if int1.isStep is False:
            continue
        
        int2 = interval.notesToInterval(cur, nextN)
        if int2.isStep is False:
            continue
            
        cma = cur.beatStrength 
        if (cma < 1 and 
            cma <= prev.beatStrength and
            cma <= nextN.beatStrength): 

            if int1.direction == int2.direction:
                cur.lyric = 'pt' # neighbor tone
            else:
                cur.lyric = 'nt' # passing tone
    if show:   
        g.parts['cantus'].show()


def demoJesse(show=True):
    luca = corpus.parse('luca/gloria')
    for n in luca.measures(2, 20).flat.notesAndRests:
        if n.isRest is False:
            n.lyric = n.pitch.german
    if show:   
        luca.show()

#-------------------------------------------------------------------------------
# new examples


def corpusMelodicIntervalSearch(show = True):
    # this version compares china to netherlands
    from music21.analysis import discrete

    mid = discrete.MelodicIntervalDiversity()
    groupEast = corpus.search('shanxi', field='locale')
    groupWest = corpus.search('niederlande', field='locale') 

    msg = []
    for name, group in [('shanxi', groupEast), ('niederlande', groupWest)]:
        intervalDict = {}
        workCount = 0
        intervalCount = 0
        seventhCount = 0
        for fp, n in group:
            workCount += 1
            s = converter.parse(fp, number=n)
            intervalDict = mid.countMelodicIntervals(s, found=intervalDict)
        
        for key in sorted(intervalDict.keys()):
            intervalCount += intervalDict[key][1] # second value is count
            if key in ['m7', 'M7']:
                seventhCount += intervalDict[key][1] 

        pcentSevenths = round(((seventhCount / float(intervalCount)) * 100), 4)
        msg.append(
            'locale: %s: found %s percent melodic sevenths, out of %s intervals in %s works' % (
                                                name, pcentSevenths, intervalCount, workCount))
#         for key in sorted(intervalDict.keys()):
#             print intervalDict[key]

    for sub in msg: 
        if show == True:
            print (sub)



        # ('anhui', corpus.search('anhui', field='locale')), # gets 3.5
        # ('Qinghai', corpus.search('Qinghai', field='locale')), # gets 2.5
        # ('Zhejiang', corpus.search('Zhejiang', field='locale')), # ; coastal
        # shanxi get 3.2
        # fujian gets 0.8

def corpusMelodicIntervalSearchBrief(show=False):
    # try for the most concise representation
    from music21 import analysis
    melodicIntervalDiversity = analysis.discrete.MelodicIntervalDiversity()
    message = []
    for region in ['shanxi', 'fujian']:
        intervalDict = {}
        workCount = 0
        intervalCount = 0
        seventhCount = 0
        for metadataEntry in corpus.search(region, field='locale'):
            workCount += 1
            score = corpus.parse(
                metadataEntry.sourcePath,
                number=metadataEntry.number,
                )
            intervalDict = melodicIntervalDiversity.countMelodicIntervals(
                score, found=intervalDict)
        for key in intervalDict.keys():
            intervalCount += intervalDict[key][1] # second value is count
            if key in ['m7', 'M7']:
                seventhCount += intervalDict[key][1]
        pcentSevenths = round((seventhCount / float(intervalCount) * 100), 4)
        message.append(
            'locale: %s: found %s percent melodic sevenths, out of %s intervals in %s works' % (
                        region, pcentSevenths, intervalCount, workCount))
    if show == True:
        for sub in message: 
            print (sub)


def corpusFindMelodicSevenths(show = True):
    # find and display melodic sevenths
    import os
    from music21.analysis import discrete

    mid = discrete.MelodicIntervalDiversity()
    groupEast = corpus.search('shanxi', field='locale')
    groupWest = corpus.search('niederlande', field='locale') 

    found = []
    for unused_name, group in [('shanxi', groupEast), ('niederlande', groupWest)]:
        for fp, n in group:
            s = converter.parse(fp, number=n)
            intervalDict = mid.countMelodicIntervals(s)
        
            for key in sorted(intervalDict.keys()):
                if key in ['m7', 'M7']:
                    found.append([fp, n, s])
                   
    results = stream.Stream()
    for fp, num, s in found: 
        environLocal.printDebug(['working with found', fp, num])
        # this assumes these are all monophonic
        noteStream = s.flat.getElementsByClass('Note')
        for i, n in enumerate(noteStream):
            if i <= len(noteStream) - 2:
                nNext = noteStream[i+1]
            else:
                nNext = None

            if nNext is not None:
                #environLocal.printDebug(['creating interval from notes:', n, nNext, i])
                i = interval.notesToInterval(n, nNext)
                environLocal.printDebug(['got interval', i.name])
                if i.name in ['m7', 'M7']:
                    #n.addLyric(s.metadata.title)
                    junk, fn = os.path.split(fp)
                    n.addLyric('%s: %s' % (fn, num))

                    m = noteStream.extractContext(n, 1, 2, forceOutputClass=stream.Measure)
                    m.makeAccidentals()
                    m.timeSignature = m.bestTimeSignature()
                    results.append(m)
    if show == True:
        results.show()

def chordifyAnalysis():

    o = corpus.parse('josquin/milleRegrets')
    sSrc = o.mergeScores()
    #sSrc = corpus.parse('bwv1080', 1)

    sExcerpt = sSrc.measures(0,20)

    display = stream.Score()
    display.metadata = sSrc.metadata
    for p in sExcerpt.parts:
        display.insert(0, p)

    reduction = sExcerpt.chordify()
    for c in reduction.flat.getElementsByClass('Chord'):
        c.annotateIntervals()
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
    display.insert(0, reduction)
    display.show()


def chordifyAnalysisHandel():
    sExcerpt = corpus.parse('hwv56', '3-03')
    sExcerpt = sExcerpt.measures(0,10)
    display = stream.Score()
    for p in sExcerpt.parts: 
        display.insert(0, p)
    reduction = sExcerpt.chordify()
    for c in reduction.flat.getElementsByClass('Chord'):
        c.annotateIntervals()
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
    display.insert(0, reduction)
    display.show()



def chordifyAnalysisBrief():
    #sSrc = corpus.parse('josquin/milleRegrets').mergeScores()
    #sExcerpt = corpus.parse('bwv1080', 8).measures(10,12)

    # 128, 134
    #o = corpus.parse('josquin/milleRegrets')
    # remove number
    o = corpus.parse('josquin/laDeplorationDeLaMorteDeJohannesOckeghem')
    excerpt = o.mergeScores().measures(126, 134)

    reduction = excerpt.chordify()
    for c in reduction.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    excerpt.insert(0, reduction)
    excerpt.show()


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''
        smt2010: Test non-showing functions
        '''
        # beethoven examples are commented out for time
        # findPassingTones too
        #sStream = corpus.parse('opus133.xml') # load a MusicXML file
        # ex03, ex01, ex02, ex04, ex01Alt, findHighestNotes,ex1_revised
        #for func in [findPotentialPassingTones]:
        for func in [findHighestNotes, demoJesse, 
                     corpusMelodicIntervalSearchBrief, findPotentialPassingTones]:

            #func(show=False, op133=sStream)
            func(show=False)



if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        chordifyAnalysisBrief()
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()

        #corpusSearch()
        #corpusMelodicIntervalSearch()
        #chordifyAnalysis()
        #chordifyAnalysisHandel()
        #corpusFindMelodicSevenths()

        #ex04()

        #chordifyAnalysisHandel()
        #chordifyAnalysisBrief()
        #corpusMelodicIntervalSearchBrief()
        chordifyAnalysisBrief()

#------------------------------------------------------------------------------
# eof

