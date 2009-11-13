import music21
from music21.common import *
from music21.humdrum import *
import music21.note
import music21.pitch
import music21.stream
from music21 import common
from music21 import corpus
from music21 import converter
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
        score = corpus.parseWork(work, movementNumber)
    
        for part in score:
            instrumentName = part.getElementsByClass(instrument.Instrument)[0].findName()
            grapher = correlate.NoteAnalysis(part.flat.sorted)    
            grapher.pitchToLengthScatter(title='%s, Movement %s, %s' % (work, movementNumber, instrumentName))

#
#  longer version -- reuse for something less common than quarterLength to pitch
#            
#            iObj = part.getElementsByClass(instrument.Instrument)[0]
#            na = correlate.NoteAnalysis(part.flat.sorted)    
#            na.noteAttributeScatter('quarterLength', 'midi', 
#                                    xLabel='Duration', yLabel='Pitch',
#                                    title='%s, Movement %s, %s' % (work, movementNumber, iObj.findName()),
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
            rhythmNote = thisNote.deepcopy()
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
        titleStr = '%s, Movement %s, %s' % (work, movementNumber, iObj.findName())
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
        print map

    print 'total crescendi: %s' % countCrescendo    
    print 'total diminuendi: %s' % countDiminuendo    

def simple4c():
    # question 178 Generate a set matrix for a given tone row. (python only)

    p = [8,1,7,9,0,2,3,5,4,11,6,10]

    i = [(12-x) % 12 for x in p]
    matrix = [[(x+t) % 12 for x in p] for t in i]

    for row in matrix:
        msg = []
        for pitch in row:
            msg.append(str(pitch).ljust(3))
        print ''.join(msg)


def simple4c_b():

    from music21 import serial

    p = [8,1,7,9,0,2,3,5,4,11,6,10]
    print serial.rowToMatrix(p)


def simple4d():
    # question 11: Assemble syllables into words for some vocal text.

    import webbrowser
    from music21 import converter
    from music21 import text
        
    for part in converter.parse('d:/web/eclipse/music21misc/musicxmlLib/Binchois.xml'):
        lyrics = text.assembleLyrics(part)
        if 'exultavit' in lyrics:
            print lyrics
            webbrowser.open('http://www.google.com/search?&q=' + lyrics)

    # open a web browswer to google, searching for the string


def simple4e():
    # 250.    Identify the longest note in a score
    from music21 import stream
    
    qLenMax = 0
    
    beethovenQuartet = corpus.parseWork('opus18no1', 4)
    
    for part in beethovenQuartet:
        pf = part.flat.getNotes()
        for n in pf:
            if n.quarterLength >= qLenMax:
                qLenMax = n.quarterLength
                n.color = 'red'
                display = pf.extractContext(n, before = 4.0, after = 6.0)
                
    print 'longest duration was: %s quarters long' % (qLenMax)
    lily.LilyString("{ \\time 2/4 " + display.bestClef().lily + " " + display.lily + "}").showPNG()


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
    print foundSets


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
    print 'repeated pitches for %s, movement %s: %s counts' % (work,
                     movementNumber, count)


def simple4h():
    # question 40: Count how many measures contain at least one trill.
    pass

    # question 60: Determine how frequently ascending melodic leaps are followed by descending steps
    # question 184: Identify all D major triads in a work
    # 251.    Identify the longest run of ascending intervals in some melody.
    # 252.    Identify the lowest note in a score


#-------------------------------------------------------------------------------



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
    from music21 import notationMod

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
                if isinstance(thisEditorial, notationMod.Fermata):
                    isCadence = True
            
            if isCadence is True and thisChord.inversion == 1:
                thisChord.lyric.append(str.chorale.name + ": " + str(thisChord.context.measureNumber) + "/" + str(thisChord.context.beat))
                returnStream.addNext(prev2Chord)
                returnStream.addNext(prevChord)
                returnStream.addNext(thisChord)

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
    simple1()
    