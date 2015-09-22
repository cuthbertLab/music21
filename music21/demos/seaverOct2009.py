# -*- coding: utf-8 -*-

from music21 import stream, converter, corpus, instrument, graph, note, meter, humdrum
import music21.pitch
from collections import defaultdict

import copy
import unittest

def simple1():
    '''
    show correlations (if any) between notelength and pitch in several pieces coded in musicxml or humdrum and also including the trecento cadences.
    '''
    
    for work in ['opus18no1', 'opus59no3']:
        movementNumber = 3
        score = corpus.parse(work, movementNumber) #, extList=['xml'])
    
        for part in score:
            instrumentName = part.flat.getElementsByClass(
                instrument.Instrument)[0].bestName()
            title='%s, Movement %s, %s' % (work, movementNumber, instrumentName)

            g = graph.PlotScatterPitchSpaceQuarterLength(part.flat.sorted, 
                title=title)
            g.process()

def simple2():
    '''
    find unusual leaps in Trecento cadences
    '''
    pass

def simple3():
    '''
    reduce all measures of Chopin mazurkas to their rhythmic components and give the measure numbers (harder: render in notation) of all measures sorted by pattern.
    '''
    def lsort(keyname):
        return len(rhythmicHash[keyname])
    
    defaultPitch = music21.pitch.Pitch("C3")      
    
    #  semiFlat lets me get all Measures no matter where they reside in the tree structure
    measureStream = converter.parse(humdrum.testFiles.mazurka6).semiFlat.getElementsByClass('Measure')
    rhythmicHash = defaultdict(list) 
    
    for thisMeasure in measureStream:
        if thisMeasure.duration.quarterLength != 3.0:
            continue
        notes = thisMeasure.flat.notesAndRests  # n.b. won't work any more because of voices...
        if len(notes) == 0:
            continue
        rhythmicStream = stream.Measure()
        
        offsetString = "" ## comma separated string of offsets 
        for thisNote in notes:
            rhythmNote = copy.deepcopy(thisNote)
            if rhythmNote.isNote:
                rhythmNote.pitch = copy.deepcopy(defaultPitch)
            elif rhythmNote.isChord:
                rhythmNote          = note.Note()
                rhythmNote.pitch    = copy.deepcopy(defaultPitch)
                rhythmNote.duration = copy.deepcopy(thisNote.duration)
                            
            if not rhythmNote.isRest:
                offsetString += str(rhythmNote.offset) + ", "
            
            rhythmicStream.append(rhythmNote)
            
        #notes[0].lyric = str(thisMeasure.number)
        if len(rhythmicHash[offsetString]) == 0: # if it is our first encounter with the rhythm, add the rhythm alone in blue
            for thisNote in rhythmicStream:
                thisNote.color = "blue"
            rhythmicHash[offsetString].append(rhythmicStream)
        thisMeasure.flat.notesAndRests[0].editorial.comment.text = str(thisMeasure.number)
        rhythmicHash[offsetString].append(thisMeasure)

    s = stream.Part()
    s.insert(0, meter.TimeSignature('3/4'))
    
    for thisRhythmProfile in sorted(rhythmicHash, key=lsort, reverse=True):
        for thisMeasure in rhythmicHash[thisRhythmProfile]:
            thisMeasure.insert(0, thisMeasure.bestClef())
            s.append(thisMeasure)
    s.show('lily.png')

def displayChopinRhythms():
    defaultPitch = music21.pitch.Pitch("C3")      
    
    #  semiFlat lets me get all Measures no matter where they reside in the tree structure
    measureStream = converter.parse(humdrum.testFiles.mazurka6).semiFlat.getElementsByClass('Measure')
    rhythmicHash = {} 

    def lsort(keyname):
        return len(rhythmicHash[keyname])

    for thisMeasure in measureStream:
        if thisMeasure.duration.quarterLength == 3.0:
            continue
        notes = thisMeasure.flat.notesAndRests  # n.b. won't work any more because of voices...
        if len(notes) == 0:
            continue  # should not happen...
        rhythmicStream = stream.Measure()
        
        offsetString = "" ## comma separated string of offsets 
        for thisNote in notes:
            rhythmNote = copy.deepcopy(thisNote)
            if rhythmNote.isNote:
                rhythmNote.pitch = copy.deepcopy(defaultPitch)
            elif rhythmNote.isChord:
                rhythmNote          = note.Note()
                rhythmNote.pitch    = copy.deepcopy(defaultPitch)
                rhythmNote.duration = copy.deepcopy(thisNote.duration)
                            
            if not rhythmNote.isRest:
                offsetString += str(rhythmNote.offset) + ", "
            
            rhythmicStream.append(rhythmNote)
            
        notes[0].lyric = str(thisMeasure.number)
        if len(rhythmicHash[offsetString]) == 0: # if it is our first encounter with the rhythm, add the rhythm alone in blue
            for thisNote in rhythmicStream:
                thisNote.color = "blue"
            rhythmicHash[offsetString].append(rhythmicStream)
        #thisMeasure.flat.notesAndRests[0].editorial.comment.text = str(thisMeasure.number)
        rhythmicHash[offsetString].append(thisMeasure)

    s = stream.Part()
    s.insert(0, meter.TimeSignature('3/4')) # this should be made more flexible.
    
    for thisRhythmProfile in sorted(rhythmicHash, key=lsort, reverse=True):
        for thisMeasure in rhythmicHash[thisRhythmProfile]:
            thisMeasure.insert(0, thisMeasure.bestClef())
            s.append(thisMeasure)
    s.show('lily.png')


def simple4a(show=True):
    '''
    find at least 5 questions that are difficult to solve in Humdrum which are simple in music21; (one which just uses Python)
    '''

# 4a: in addition to the graphs as they are can we have a graph showing average
# dynamic for a given pitch, and a single number for the Correlation Coefficient
# between dynamic level and pitch -- the sort of super scientific. I imagine
# it'd be something like 0.55, so no, not a connection between pitch and dynamic.

    # question 1: Above G4 do higher pitches tend to be louder?
    work = 'opus18no1'
    movementNumber = 3
    #movement = corpus.getWork(work, movementNumber)
    #s = converter.parse(movement)

    s = corpus.parse('opus18no1', movementNumber) #, extList=['xml'])

    #s[0].show()

    for movement in [0]:
        sPart = s.parts[movement]
        iObj = sPart.getElementsByClass(instrument.Instrument)[0]
        titleStr = '%s, Movement %s, %s' % (work, movementNumber, iObj.bestName())
    
        if not show:
            doneAction = None
        else:
            doneAction = 'write'

        p = graph.PlotScatterWeightedPitchSpaceDynamicSymbol(s.parts[0].flat,
             doneAction=doneAction, title=titleStr)
        p.process()



def simple4b(show=True):
    from music21 import dynamics

    # question 8: Are dynamic swells (crescendo-diminuendos) more common than dips (diminuendos-crescendos)?
    # so we need to compute the average distance between < and > and see if it's higheror lower than > to <. And any dynamic marking in between resets the count.

    work = 'opus41no1'
    movementNumber = 2
    s = corpus.parse(work, movementNumber) #, extList='xml')
    countCrescendo = 0
    countDiminuendo = 0
    for part in s.getElementsByClass(stream.Part):
        map = [] # create a l @ReservedAssignment
        wedgeStream = part.flat.getElementsByClass(dynamics.DynamicWedge)
        for wedge in wedgeStream:
            if wedge.type == 'crescendo':
                countCrescendo += 1
                map.append(('>', wedge.offset))
            elif wedge.type == 'diminuendo': 
                countDiminuendo += 1
                map.append(('<', wedge.offset))
        if show:
            print(map)

    if show:
        print('total crescendi: %s' % countCrescendo) 
        print('total diminuendi: %s' % countDiminuendo)


def simple4c(show=True):
    '''
    question 178: Generate a set matrix for a given tone row.
    '''
    from music21 import serial
    p = [8,1,7,9,0,2,3,5,4,11,6,10]

    if show == True:
        print(serial.rowToMatrix(p))


def simple4d():
    '''
    question 11: Assemble syllables into words for some vocal text.
    
    music21 extension: then Google the lyrics if they contain the word exultavit
    '''
    import webbrowser
    from music21 import text
        
    for part in converter.parse('d:/web/eclipse/music21misc/musicxmlLib/Binchois.xml'):
        lyrics = text.assembleLyrics(part)
        if 'exultavit' in lyrics:
            print(lyrics)
            webbrowser.open('http://www.google.com/search?&q=' + lyrics)

    # open a web browswer to google, searching for the string


def simple4e(show=True):
    # 250.    Identify the longest note in a score
    qLenMax = 0
    beethovenQuartet = corpus.parse('beethoven/opus18no1/movement4.xml')
    maxMeasure = 0
    for part in beethovenQuartet.parts:
        partStripped = part.stripTies()
        for n in partStripped.flat.notesAndRests:
            if n.quarterLength > qLenMax and n.isRest is False:
                qLenMax = n.quarterLength
                maxMeasure = n.measureNumber
    if show:
        beethovenQuartet.measures(maxMeasure - 2, maxMeasure + 2).show()



def simple4f(show=True):
    # question 19: Calculate pitch-class sets for melodic passages segmented by rests.
    work = 'opus18no1'
    movementNumber = 3
    s = corpus.parse(work, movementNumber) #, extList=['xml'])

    foundSets = []
    candidateSet = []
    for part in s.getElementsByClass(stream.Part):
        eventStream = part.flat.notesAndRests
        for i in range(len(eventStream)):
            e = eventStream[i]
            if isinstance(e, note.Rest) or i == len(eventStream)-1:
                if len(candidateSet) > 0:
                    candidateSet.sort()
                    # this removes redundancies for simplicity
                    if candidateSet not in foundSets:
                        foundSets.append(candidateSet)
                    candidateSet = []
            elif isinstance(e, note.Note):      
                if e.pitchClass not in candidateSet:
                    candidateSet.append(e.pitchClass)
    foundSets.sort()

    if show:
        print(foundSets)


def simple4g():
    # question 62: Determine how often a pitch is followed immediately by the same pitch
    work = 'opus18no1'
    movements = corpus.getWork(work)
    movementNumber = 3
    s = converter.parse(movements[movementNumber-1])
    count = 0
    for part in s:
        noteStream = part.flat.getElementsByClass(note.Note)
        for i in range(len(noteStream)-1):
            # assuming spelling does not count
            if noteStream[i].midi == noteStream[i+1].midi:
                count += 1
    print('repeated pitches for %s, movement %s: %s counts' % (work,
                     movementNumber, count))


def simple4h():
    # question 40: Count how many measures contain at least one trill. 
    pass

    # question 60: Determine how frequently ascending melodic leaps are followed by descending steps
    # question 184: Identify all D major triads in a work
    # 251.    Identify the longest run of ascending intervals in some melody.
    # 252.    Identify the lowest note in a score


def threeDimChopin():
    from music21.humdrum import testFiles  

    streamObject = converter.parse(testFiles.mazurka6)
#    n1 = music21.note.Note("C7")
#    n1.duration.quarterLength = 3
#    n1.tie = music21.note.Tie("start")
#    streamObject.append(n1)
#    
#    n2 = music21.note.Note("C7")
#    n2.duration.quarterLength = 3
#    n2.tie = music21.note.Tie("stop")
#    streamObject.append(n2)
    
    stream2 = streamObject.stripTies()
    g = graph.Plot3DBarsPitchSpaceQuarterLength(stream2)
    g.process()


def threeDimMozart():
    from music21.musicxml.testFiles import mozartTrioK581Excerpt  # @UnresolvedImport

    streamObject = converter.parse(mozartTrioK581Excerpt) # 
#    stream2 = streamObject.stripTies() # adds one outlier that makes the graph difficult to read

    g = graph.Plot3DBarsPitchSpaceQuarterLength(streamObject.flat)
    g.process()



def threeDimBoth():
    from music21.musicxml.testFiles import mozartTrioK581Excerpt # @UnresolvedImport
    from music21.humdrum import testFiles as kernTest  

    mozartStream = converter.parse(mozartTrioK581Excerpt)
    g = graph.Plot3DBarsPitchSpaceQuarterLength(mozartStream.flat)
    g.process()
    
    chopinStream = converter.parse(kernTest.mazurka6) 
    g = graph.Plot3DBarsPitchSpaceQuarterLength(chopinStream.flat)
    g.process()



def januaryThankYou():
    names = ['opus132', 'opus133', 'opus18no3', 'opus18no4', 'opus18no5', 'opus74']
    names += ['opus59no1', 'opus59no2', 'opus59no3']

    for workName in names:
        beethovenScore = corpus.parse('beethoven/' + workName, 1)
        for partNum in range(4):
            print(workName, str(partNum))
            thisPart = beethovenScore[partNum]
            display = stream.Stream()
            notes = thisPart.flat.findConsecutiveNotes(skipUnisons = True, skipChords = True,
                       skipOctaves = True, skipRests = True, noNone = True )
            for i in range(len(notes) - 4):
#                if (notes[i].name == 'E-' or notes[i].name == "D#") and notes[i+1].name == 'E' and notes[i+2].name == 'A':
                if notes[i].name == 'E-' and notes[i+1].name == 'E' and notes[i+2].name == 'A':
                    measureNumber = 0
                    for site in notes[i].sites.getSites():
                        if isinstance(site, stream.Measure):
                            measureNumber = site.number
                            display.append(site)
                    notes[i].lyric = workName + " " + str(thisPart.id) + " " + str(measureNumber)
                    m = stream.Measure()
                    m.append(notes[i])
                    m.append(notes[i+1])
                    m.append(notes[i+2])
                    m.append(notes[i+3])
                    m.insert(0, m.bestClef())
                    display.append(m)

            
            display.show()
    



#-------------------------------------------------------------------------------



# jdstewar@fas.harvard.edu wrote on Nov 21 [1999]:
# > Dear Myke, 
# > 
# > In the meantime here are a few 
# > questions I would pose for the program; some I imagine would be easy 
# > and straighforward, some perhaps not so easy: 
# 
# Indeed, you've organized the questions in order from what I believe
# will be the easiest to answer to what I believe will be the hardest.
# The program doesn't have a good "Label Harmony" function (just because
# of how complicated and ambiguous that can be) so anything involving a
# single labeled chord can be difficult.  The first and second should be
# extremely easy.  The third and fifth should be easy to construct in
# such a way that it doesn't miss anything but it might give some
# results that are "false positives".  #4 will be the hardest to
# construct, since a half cadence is something that's not determined so
# much by the cadence chord and the chords directly preceding but more
# from a larger sense of tonal listening which is of course harder to
# teach a computer to have.
# 
# warmly,
# Myke Cuthbert



def js_q1():
    '''
    give all cadential arrivals on a first inversion chord, 6 or 65. 
    '''
    from music21 import expressions

    allChorales = corpus.chorales.Iterator()
    returnStream = stream.Stream()
    
    prevChord = None
    saveChord = None
    for chorale in allChorales:
        reducedChorale = chorale.simplify()
        for thisChord in reducedChorale.chords:
            # move this into ReducedChorale...
            prev2Chord = prevChord
            prevChord = saveChord
            saveChord = thisChord
            
            isCadence = False
            for thisEditorial in thisChord.editorial:
                if isinstance(thisEditorial, expressions.Fermata):
                    isCadence = True
            
            if isCadence is True and thisChord.inversion == 1:
                thisChord.lyric.append(str.chorale.name + ": " + str(thisChord.context.number) + "/" + str(thisChord.context.beat))
                returnStream.append(prev2Chord)
                returnStream.append(prevChord)
                returnStream.append(thisChord)

    returnStream.show()

def js_q2():
    '''
    give all instances of bass lines with 7-6-7-5-all 8th notes. OR more 
    precisely four 8th notes starting on the beat: down a whole step, up a 
    whole step, down a M 3rd. 
    '''
    pass

def js_q3():
    '''
    find all I II42 V65 I progressions 
    '''
    allChorales = corpus.chorales.Iterator()
    returnStream = stream.Stream()
    for chorale in allChorales:
        unused_reducedChorale = chorale.simplify()
        
    returnStream.show()

def js_q4():
    '''
    give all instances of half cadences in which the arrival is preceded 
    by VII6/V. 
    '''
    allChorales = corpus.chorales.Iterator()
    returnStream = stream.Stream()
    for chorale in allChorales:
        unused_reducedChorale = chorale.simplify()
        
    returnStream.show()

def js_q5():
    '''
    give all cadences that represent modulations to the key of bVII. 
    '''
    allChorales = corpus.chorales.Iterator()
    returnStream = stream.Stream()
    for chorale in allChorales:
        unused_reducedChorale = chorale.simplify()
        
    returnStream.show()




#-------------------------------------------------------------------------------
tests = [simple4a, simple4b, simple4c, simple4e, simple4f]

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''Test showing functions
        '''
        #
        simple4e(show=True)
#        for func in tests:
#            func(show=True)

    def testSimple3(self):
        simple3()


class Test(unittest.TestCase):

    def runTest(self):
        pass

        
    def xtestBasic(self):
        '''seaverOct2009: Test non-showing functions
        '''
        for func in tests:
            func(show=False)


if __name__ == "__main__":
    simple3()
    #music21.mainTest(Test)
    #music21.mainTest(TestExternal)




#------------------------------------------------------------------------------
# eof

