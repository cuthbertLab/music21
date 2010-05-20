import music21
from music21.common import *
from music21.humdrum import *
import music21.note
import music21.pitch
import music21.stream
from music21 import clef
from music21 import common
from music21 import corpus
from music21 import converter
from music21 import graph
from music21 import instrument
from music21 import lily
from music21 import meter
from music21 import stream
from music21 import note
from music21.analysis import correlate


def simple1():
    '''
    show correlations (if any) between notelength and pitch in several pieces coded in musicxml or humdrum and also including the trecento cadences.
    '''
    
    for work in ['opus18no1', 'opus59no3']:
        movementNumber = 3
        score = corpus.parseWork(work, movementNumber, extList=['xml'])
    
        for part in score:
            instrumentName = part.flat.getElementsByClass(
                instrument.Instrument)[0].bestName()
            title='%s, Movement %s, %s' % (work, movementNumber, instrumentName)

            #grapher = correlate.NoteAnalysis(part.flat.sorted)    
            #grapher.pitchToLengthScatter(title=title)
            g = graph.PlotScatterPitchSpaceQuarterLength(part.flat.sorted, 
                title=title)
            g.process()
#
#  longer version -- reuse for something less common than quarterLength to pitch
#            
#            iObj = part.getElementsByClass(instrument.Instrument)[0]
#            na = correlate.NoteAnalysis(part.flat.sorted)    
#            na.noteAttributeScatter('quarterLength', 'midi', 
#                                    xLabel='Duration', yLabel='Pitch',
#                                    title='%s, Movement %s, %s' % (work, movementNumber, iObj.bestName()),
#                                    yTicks=correlate.ticksPitchSpace(),
#                                    xTicks=correlate.ticksQuarterLength()
#                                    )

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
    
    import copy
    from music21.converter import parse
    from music21.stream import Stream, Measure
    
    
    #  semiFlat lets me get all Measures no matter where they reside in the tree structure
    measureStream = parse(testFiles.mazurka6).semiFlat[Measure]
    rhythmicHash = common.defHash(default = list, callDefault = True )

    for thisMeasure in measureStream:
        if not almostEquals(thisMeasure.duration.quarterLength, 3.0):
            continue
        notes = thisMeasure.flat.getNotes()
        rhythmicStream = Measure()
        
        offsetString = "" ## comma separated string of offsets 
        for thisNote in notes:
            rhythmNote = copy.deepcopy(thisNote)
            if rhythmNote.isNote:
                rhythmNote.pitch = defaultPitch
            elif rhythmNote.isChord:
                rhythmNote          = music21.note.Note()
                rhythmNote.pitch    = defaultPitch
                rhythmNote.duration = thisNote.duration
                            
            if not rhythmNote.isRest:
                offsetString += str(rhythmNote.offset) + ", "
            
            if thisNote.isChord:
                thisNote.pitch = defaultPitch
            rhythmicStream.append(rhythmNote)
            
        notes[0].lyric = str(thisMeasure.measureNumber)
        if len(rhythmicHash[offsetString]) == 0: # if it is our first encounter with the rhythm, add the rhythm alone in blue
            for thisNote in rhythmicStream:
                thisNote.color = "blue"
            rhythmicHash[offsetString].append(rhythmicStream)
        thisMeasure.getNotes()[0].editorial.comment.text = str(thisMeasure.measureNumber)
        rhythmicHash[offsetString].append(thisMeasure)

    allLily = lily.LilyString()
    allLily += meter.TimeSignature('3/4').lily + " "
    for thisRhythmProfile in sorted(rhythmicHash, key=lsort, reverse=True):
        for thisMeasure in rhythmicHash[thisRhythmProfile]:
            thisLily = " " + str(thisMeasure.bestClef().lily) + " " + str(thisMeasure.lily) + "\n"
            allLily += thisLily
    allLily.showPNG()

def simple4a():
    '''
    find at least 5 questions that are difficult to solve in Humdrum which are simple in music21; (one which just uses Python)
    '''

# 4a: in addition to the graphs as they are can we have a graph showing average
# dynamic for a given pitch, and a single number for the Correlation Coefficient
# between dynamic level and pitch -- the sort of super scientific. I imagine
# it'd be something like 0.55, so no, not a connection between pitch and dynamic.

    from music21 import corpus
    from music21.analysis import correlate

    # question 1: Above G4 do higher pitches tend to be louder?
    work = 'opus18no1'
    movementNumber = 3
    movement = corpus.getWork(work, movementNumber)
    s = converter.parse(movement)
    for part in s:
        # get the instrument object from the stream
        iObj = part.getElementsByClass(instrument.Instrument)[0]
        am = correlate.ActivityMatch(part.flat.sorted)
        titleStr = '%s, Movement %s, %s' % (work, movementNumber, iObj.bestName())
        am.pitchToDynamic(title=titleStr)


def simple4b():
    from music21 import corpus
    from music21 import dynamics

    # question 8: Are dynamic swells (crescendo-diminuendos) more common than dips (diminuendos-crescendos)?
    # so we need to compute the average distance between < and > and see if it's higheror lower than > to <. And any dynamic marking in between resets the count.

    work = 'opus41no1'
    movementNumber = 2
    s = corpus.getWork(work, movementNumber)
    countCrescendo = 0
    countDiminuendo = 0
    for part in s:
        map = [] # create a l
        wedgeStream = part.flat.getElementsByClass(dynamics.Wedge)
        for wedge in wedgeStream:
            if wedge.type == 'crescendo':
                countCrescendo += 1
                map.append(('>', wedge.offset))
            elif wedge.type == 'diminuendo': 
                countDiminuendo += 1
                map.append(('<', wedge.offset))
        print(map)

    print('total crescendi: %s' % countCrescendo) 
    print('total diminuendi: %s' % countDiminuendo)

def simple4c():
    # question 178 Generate a set matrix for a given tone row. (python only)

    p = [8,1,7,9,0,2,3,5,4,11,6,10]

    i = [(12-x) % 12 for x in p]
    matrix = [[(x+t) % 12 for x in p] for t in i]

    for row in matrix:
        msg = []
        for pitch in row:
            msg.append(str(pitch).ljust(3))
        print (''.join(msg))


def simple4c_b():

    from music21 import serial

    p = [8,1,7,9,0,2,3,5,4,11,6,10]
    print(serial.rowToMatrix(p))


def simple4d():
    # question 11: Assemble syllables into words for some vocal text.

    import webbrowser
    from music21 import converter
    from music21 import text
        
    for part in music21.parse('d:/web/eclipse/music21misc/musicxmlLib/Binchois.xml'):
        lyrics = text.assembleLyrics(part)
        if 'exultavit' in lyrics:
            print(lyrics)
            webbrowser.open('http://www.google.com/search?&q=' + lyrics)

    # open a web browswer to google, searching for the string


def simple4e():
    # 250.    Identify the longest note in a score
    from music21 import stream
    
    qLenMax = 0
    beethovenQuartet = corpus.parseWork('opus18no1', 4)
    maxNote = None
    for part in beethovenQuartet:
#         lily.LilyString("{ \\time 2/4 " + str(part.bestClef().lily) + " " + str(part.lily) + "}").showPNG()

        # note: this probably is not re-joining tied notes
        pf = part.flat.getNotes()
        for n in pf:
            if n.quarterLength >= qLenMax:
                qLenMax = n.quarterLength
                maxNote = n
        maxNote.color = 'red'
        display = part.flat.extractContext(maxNote, before = 4.0, after = 6.0)
               
    print('longest duration was: %s quarters long' % (qLenMax))


    lily.LilyString("{ \\time 2/4 " + str(display.bestClef().lily) + " " + str(display.lily) + "}").showPNG()
    display.show()



def simple4f():
    # question 19: Calculate pitch-class sets for melodic passages segmented by rests.
    work = 'opus18no1'
    movementNumber = 3
    movement = corpus.getWork(work, movementNumber)
    s = converter.parse(movement)

    foundSets = []
    candidateSet = []
    for part in s:
        eventStream = part.flat.getNotes()
        for i in range(len(eventStream)):
            e = eventStream[i]
            if isinstance(e, music21.note.Rest) or i == len(eventStream)-1:
                if len(candidateSet) > 0:
                    candidateSet.sort()
                    # this removes redundancies for simplicity
                    if candidateSet not in foundSets:
                        foundSets.append(candidateSet)
                    candidateSet = []
            elif isinstance(e, music21.note.Note):      
                if e.pitchClass not in candidateSet:
                    candidateSet.append(e.pitchClass)
    foundSets.sort()
    print(foundSets)


def simple4g():
    # question 62: Determine how often a pitch is followed immediately by the same pitch
    work = 'opus18no1'
    movements = corpus.getWork(work)
    movementNumber = 3
    s = converter.parse(movements[movementNumber-1])
    count = 0
    for part in s:
        noteStream = part.flat.getElementsByClass(music21.note.Note)
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
    from music21 import converter
    from music21.humdrum import testFiles  
    from music21.analysis import correlate

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
    #correlated = correlate.NoteAnalysis(stream2)  
    #correlated.noteAttributeCount()
    g = graph.Plot3DBarsPitchSpaceQuarterLength(stream2)
    g.process()


def threeDimMozart():
    from music21 import converter
    from music21.musicxml import testFiles  
    from music21.analysis import correlate

    streamObject = converter.parse(testFiles.mozartTrioK581Excerpt)
#    stream2 = streamObject.stripTies() # adds one outlier that makes the graph difficult to read
#     correlated = correlate.NoteAnalysis(streamObject.flat)  
#     correlated.noteAttributeCount(colors=['b'], barWidth = 0.2)

    g = graph.Plot3DBarsPitchSpaceQuarterLength(streamObject.flat)
    g.process()



def threeDimBoth():
    from music21 import converter
    from music21.musicxml import testFiles as xmlTest
    from music21.humdrum import testFiles as kernTest  
    from music21.analysis import correlate

    mozartStream = converter.parse(xmlTest.mozartTrioK581Excerpt)
    g = graph.Plot3DBarsPitchSpaceQuarterLength(mozartStream.flat)
    g.process()

#     correlated1 = correlate.NoteAnalysis(mozartStream.flat)  
#     correlated1.noteAttributeCount()
    
    chopinStream = converter.parse(kernTest.mazurka6) 
    g = graph.Plot3DBarsPitchSpaceQuarterLength(chopinStream.flat)
    g.process()

#     correlated2 = correlate.NoteAnalysis(chopinStream.flat)  
#     correlated2.noteAttributeCount()


def januaryThankYou():
    names = ['opus132', 'opus133', 'opus18no3', 'opus18no4', 'opus18no5', 'opus74']
    names += ['opus59no1', 'opus59no2', 'opus59no3']

    for workName in names:
        beethovenScore = corpus.parseWork('beethoven/' + workName, 1)
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
                        for site in notes[i]._definedContexts.getSites():
                            if isinstance(site, stream.Measure):
                                measureNumber = site.measureNumber
                                display.append(site)
                        notes[i].lyric = workName + " " + str(thisPart.id) + " " + str(measureNumber)
                        m = stream.Measure()
                        m.append(notes[i])
                        m.append(notes[i+1])
                        m.append(notes[i+2])
                        m.append(notes[i+3])
                        m.insert(0, m.bestClef())
                        display.append(m)
            try:
                display.show()
            except:
                pass
    



'''
jdstewar@fas.harvard.edu wrote on Nov 21 [1999]:
> Dear Myke, 
> 
> In the meantime here are a few 
> questions I would pose for the program; some I imagine would be easy 
> and straighforward, some perhaps not so easy: 

Indeed, you've organized the questions in order from what I believe
will be the easiest to answer to what I believe will be the hardest.
The program doesn't have a good "Label Harmony" function (just because
of how complicated and ambiguous that can be) so anything involving a
single labeled chord can be difficult.  The first and second should be
extremely easy.  The third and fifth should be easy to construct in
such a way that it doesn't miss anything but it might give some
results that are "false positives".  #4 will be the hardest to
construct, since a half cadence is something that's not determined so
much by the cadence chord and the chords directly preceding but more
from a larger sense of tonal listening which is of course harder to
teach a computer to have.

warmly,
Myke Cuthbert
'''


class Chorales(object):
    '''
    move to top level module perhaps, because of such general use
    '''
    pass

    def all(self):
        pass
    
class Chorale(object):
    pass

class ReducedChorale(Chorale):
    pass

def js_q1():
    '''
    give all cadential arrivals on a first inversion chord, 6 or 65. 
    '''
    from music21 import expressions

    allChorales = Chorales().all()
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
                thisChord.lyric.append(str.chorale.name + ": " + str(thisChord.context.measureNumber) + "/" + str(thisChord.context.beat))
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
    allChorales = Chorales().all()
    returnStream = stream.Stream()
    for chorale in allChorales:
        reducedChorale = chorale.simplify()
        
    returnStream.show()

def js_q4():
    '''
    give all instances of half cadences in which the arrival is preceded 
    by VII6/V. 
    '''
    allChorales = Chorales().all()
    returnStream = stream.Stream()
    for chorale in allChorales:
        reducedChorale = chorale.simplify()
        
    returnStream.show()

def js_q5():
    '''
    give all cadences that represent modulations to the key of bVII. 
    '''
    allChorales = Chorales().all()
    returnStream = stream.Stream()
    for chorale in allChorales:
        reducedChorale = chorale.simplify()
        
    returnStream.show()

if (__name__ == "__main__"):
#    threeDimMozart()

    simple4d()
    #januaryThankYou()