from math import modf


from music21 import note
#from note import Note
#doesn't work with loop from note.py
from music21 import common
from music21 import lily as lilyModule
from music21 import clef
from music21 import chord
from music21.common import *
from music21 import meter
from music21 import measure

class NoteStream(object):    
    allowTreble8va = False
    debug = False

    def __init__(self, notes = None):
        '''NoteStream class is a series of note objects that sound consecutively. Takes
        a list of note objects as an argument.'''
        if notes is None:
            notes = []
        self.notesAndRests = notes
        self.totalNotes = len(notes)
        self.iterIndex  = 0
        self.__lilyout  = None
        self.__intervalList = []
        self.__intervalORList = [] # interval over rests
        self.clef = None  # a stream takes zero or one clefs
        self.timeSignature = None # a stream takes zero or one time signatures
        self.showTimeSignature = False # false if you are going to put more than one stream together
                                       # true if this is your whole score

        # creates noteTimeInfo, a list of lists containing [duration,
        # start time] for each note in notes.
        # Time is measured in quarter notes using each note's quarter length.
        self.noteTimeInfo = []
        self.getNoteTimeInfo()

    def __iter__(self):
        '''Resets the counter to 0 so that iteration is correct'''
        self.iterIndex = 0
        return self

    def next(self):
        '''Returns the current note and increments the iteration index.'''
        if self.iterIndex == self.totalNotes:
            raise StopIteration
        thisNote = self.notesAndRests[self.iterIndex]
        self.iterIndex += 1
        return thisNote

    def getNoteTimeInfo(self):
        self.noteTimeInfo = []
        time = 0 

        for note in self.notesAndRests:
            length = float(note.duration.quarterLength)
            self.noteTimeInfo.append({'length': length, 'start': time})
            time += length

    __overriddenDuration = 0.0
    def __getDuration(self):
        '''Returns the total duration of the stream in quarter lengths.'''
        if self.__overriddenDuration > 0:
            return self.__overriddenDuration

        self.__totalDuration = 0.0
        for thisNote in self.notesAndRests:
            self.__totalDuration += thisNote.duration.quarterLength
        return self.__totalDuration
    def __setDuration(self, value):
        '''Sets the total duration of the stream (overrides what would be
        calculated using each note's duration.quarterLength.'''
        ### Bad idea to override, but possible
        self.__overriddenDuration = value
    
    totalDuration = property(__getDuration, __setDuration) # read-only attribute

    def __get_lily(self):
        '''Returns the stream translated into Lilypond format.'''
        if self.__lilyout is not None:
            return self.__lilyout
        lilyout = lilyModule.LilyString(''' \override Staff.StaffSymbol #'color = #(x11-color 'LightSlateGray) ''')
        if self.showTimeSignature is not False and self.timeSignature is not None:
            lilyout += self.timeSignature.lily
    
        clef = self.clef or self.bestClef()
        lilyout += clef.lily
        for thisNote in self.notesAndRests:
            if hasattr(thisNote, "startTransparency") and thisNote.startTransparency == True:
                lilyout += lilyModule.TRANSPARENCY_START

            if thisNote.duration.tuplets:
                if thisNote.duration.tuplets[0].type == "start":
                    numerator = str(int(thisNote.duration.tuplets[0].tupletNormal[0]))
                    denominator = str(int(thisNote.duration.tuplets[0].tupletActual[0]))
                    lilyout += "\\times " + numerator + "/" + denominator + " {"
                        ### TODO-- should get the actual ratio not assume that the
                        ### type of top and bottom are the same
            lilyout += thisNote.lily
            lilyout += " "
            if thisNote.duration.tuplets:
                if thisNote.duration.tuplets[0].type == "stop":
                    lilyout = lilyout.rstrip()
                    lilyout += "} "

            if hasattr(thisNote, "stopTransparency") and thisNote.stopTransparency == True:
                lilyout += lilyModule.TRANSPARENCY_STOP
        self.__lilyout = lilyout
        return lilyout

    def __set_lily(self, value):
        '''Sets the Lilypond output for the stream. Overrides what is obtained
        from get_lily.'''
        self.__lilyout = value

    lily = property(__get_lily, __set_lily)

    def bestClef(self):
        '''Returns the clef that is the best fit for the stream.'''
        totalNotes = 0
        totalHeight = 0.0
        for thisNote in self.notesAndRests:
            if isinstance(thisNote, note.Note):
                totalNotes += 1
                totalHeight += thisNote.diatonicNoteNum
                if thisNote.diatonicNoteNum > 33: # a4
                    totalHeight += 3 # bonus
                elif thisNote.diatonicNoteNum < 24: # Bass F or lower
                    totalHeight += -3 # bonus
        if totalNotes == 0:
            averageHeight = 29
        else:
            averageHeight = totalHeight / totalNotes
        if self.debug is True:
            print "Average Clef Height: " + str(averageHeight) + " "

        # c4 = 32
        if (self.allowTreble8va == False):
            if averageHeight > 28:    # c4
                return clef.TrebleClef()
            else:
                return clef.BassClef()
        else:
            if averageHeight > 32:    # g4
                return clef.TrebleClef()
            elif averageHeight > 26:  # a3
                return clef.Treble8vbClef()
            else:
                return clef.BassClef()

    def getNoteAtTime(self, time1):
        '''Returns the note object that is sounding at the given time.
        Time is assumed to be measured in quarter notes.'''
        for i in range(len(self.noteTimeInfo)):
            if 'start' not in self.noteTimeInfo[i]:
                self.noteTimeInfo[i]['start'] = 0
            if almostEquals(self.noteTimeInfo[i]['start'], time1):
                return self.notesAndRests[i]
            elif self.noteTimeInfo[i]['start'] > time1:
                return self.notesAndRests[i-1]

        if self.totalDuration > time1:
            return self.notesAndRests[-1]
        else:
            raise Exception("Cannot get a note at %f, it is longer than the stream %d" % (self.totalDuration, time1))

    def notesFollowingNote(self, compareNote, totalToReturn = 1, allowRests = True):
        '''returns a list of totalToReturn (or fewer) notes following
        compareNote in stream'''
        returningNow = False
        returnMore = totalToReturn
        notesToReturn = []
        for thisNote in self.notesAndRests:
            if returningNow == True:
                if allowRests == True or \
                   thisNote.isRest == False:
                    notesToReturn.append(thisNote)
                    returnMore = returnMore - 1
            if returnMore == 0 and returningNow is True:
                returningNow = False
            if thisNote == compareNote:
                returningNow = True
        return notesToReturn

    def noteFollowingNote(self, compareNote, allowRests = True):
        '''returns the single note object following compareNote'''
        nextNotes = self.notesFollowingNote(compareNote, 1, allowRests)
        if len(nextNotes) > 0:
            return nextNotes[0]
        else:
            return None

    def getNoteStartEndTime(self, note):
        '''Returns [start time, end time] for the given note. Time is measured
        in quarter notes.'''
        index = self.notesAndRests.index(note)
        if 'start' not in self.noteTimeInfo[index]:
            self.noteTimeInfo[index]['start'] = 0
        if 'length' not in self.noteTimeInfo[index]:
            self.noteTimeInfo[index]['length'] = 0
        start = self.noteTimeInfo[index]['start']
        end = start + self.noteTimeInfo[index]['length']
        return [start, end]

    def applyTimeSignature(self, timeSignature = None,
                           startingQtrPosition = 0, startingMeasure = 1):
        '''applyTimeSignature(self, timeSignature = self.timeSignature, startingBeat,
        startingMeasure)

        applies the timeSignature to the notes so they are aware of their
        position in the measure.  alters stream object

        Does not yet handle ComplexNotes

        '''

        if (timeSignature is None):
            timeSignature = self.timeSignature
        if (timeSignature is None):
            raise StreamException("Can't applyTimeSignature without a TimeSignature object")

        measureLength = timeSignature.barDuration.quarterLength
        currentQtrPosition = startingQtrPosition
        currentMeasure = startingMeasure
        for i in range(len(self.notesAndRests)):
            thisNote = self.notesAndRests[i]
            self.noteTimeInfo[i]['quarterPosition'] = currentQtrPosition
            self.noteTimeInfo[i]['measure'] = currentMeasure
            self.noteTimeInfo[i]['beat'] = timeSignature.quarterPositionToBeat(currentQtrPosition)
            if self.debug is True:
                print "Note %d: measure %3d, beat %3.3f, quarter %3.3f" % \
                      (i, currentMeasure, timeSignature.quarterPositionToBeat(currentQtrPosition), currentQtrPosition)
            
            currentQtrPosition += thisNote.duration.quarterLength
            (percentOff, additionalMeasures) = modf(currentQtrPosition/measureLength)
            currentMeasure += additionalMeasures
            currentQtrPosition = percentOff * measureLength

    def sliceDurationsForMeasures(self, timeSignature = None):
        '''run this AFTER applyTimeSignature: looks at each note's timeInfo
        and splits its duration into different durations in order to make each duration
        fit in one measure only.  Needed for proper LilyPond output.
        '''
        if (timeSignature is None):
            timeSignature = self.timeSignature
        if (timeSignature is None):
            raise StreamException("Can't sliceDurationsForMeasures without a TimeSignature object")

        measureLength = timeSignature.barDuration.quarterLength
        for i in range(len(self.notesAndRests)):
            thisNote = self.notesAndRests[i]
            qtrPosition = self.noteTimeInfo[i]['quarterPosition']
            noteLength = thisNote.duration.quarterLength
            if (noteLength + qtrPosition > measureLength):
                #measure length has been exceeded
                exceededLength = noteLength + qtrPosition - measureLength
                if not hasattr(thisNote.duration, "components"):
                    raise StreamException("Cannot slice a simple Duration")
                if (len(thisNote.duration.components) == 0):
                    thisNote.duration.transferDurationToComponent0()
                
                firstCut = measureLength - qtrPosition
                thisNote.duration.sliceComponentAtPosition(firstCut)
                exceededLength = exceededLength - firstCut
                cutPosition = firstCut
                
                while greaterThan(exceededLength, measureLength):
                    cutPosition += measureLength
                    if thisNote.duration.quarterLength > cutPosition:
                        thisNote.duration.sliceComponentAtPosition(cutPosition)
                    exceededLength = exceededLength - measureLength
        
    
    def makeMeasures(self, timeSignature = None, startingQtrPosition = 0, startingMeasure = 1, fillMeasure = None):
        '''run this AFTER applyTimeSignature

        timeSignature: TimeSignature object.  Otherwise uses self.timeSignature or raises StreamException
        startingQtrPosition: place in the measure to begin (default zero)
        startingMeasure: First measure number to begin on (default 1)
        fillMeasure: if beginning midway through a measure, requires a music21.Measure object filled
                     up to that point.  Does nothing unless startingQtrPosition is not zero

        Does not yet handle ComplexNotes
        '''
        
        if (timeSignature is None):
            timeSignature = self.timeSignature
        if (timeSignature is None):
            raise StreamException("Can't applyTimeSignature without a TimeSignature object")
        
        currentMeasure = startingMeasure
        currentQtrPosition = startingQtrPosition
        isFirstMeasure = True  # not measure 1 but the
        if startingQtrPosition > 0:
            if fillMeasure is None:
                raise StreamException("Need a Measure object for fillMeasure if startingQtrPosition is > 0")
            else:
                currentMeasureObject = fillMeasure
        else:
            currentMeasureObject = measure.Measure()
            currentMeasureObject.timeSignature = timeSignature
            currentMeasureObject.number = currentMeasure

        returnMeasures = []
        returnMeasures.append(currentMeasureObject)
        lastNote = None

        for i in range(len(self.notesAndRests)):
            thisNote = self.notesAndRests[i]
            thisNoteMeasure = self.noteTimeInfo[i]['measure']
            while thisNoteMeasure > currentMeasure:
                currentMeasureObject.filled = True
                currentMeasure += 1
                currentMeasure = thisNoteMeasure
                currentMeasureObject = measure.Measure()
                currentMeasureObject.timeSignature = timeSignature
                currentMeasureObject.number = int(currentMeasure)
                returnMeasures.append(currentMeasureObject)
            currentMeasureObject.notesAndRests.append(thisNote)
            currentQtrPosition += thisNote.duration.quarterLength
            currentQtrPosition = currentQtrPosition % timeSignature.barDuration.quarterLength 
            lastNote = thisNote
        
        if almostEquals(currentQtrPosition, 0):
            currentMeasureObject.filled = True

        return returnMeasures


    def setNoteTimeInfo(self, cloneit = False):
        '''setNoteTimeInfo(self, cloneit): run this when you want to commit
        the stream information to the notes

        cloneit gives a copy of the stream timeInfo instead of the actual timeInfo
        '''

        for i in range(len(self.notesAndRests)):
            thisNote = self.notesAndRests[i]
            thisTimeInfo = self.noteTimeInfo[i]
            if (thisNote is None or thisTimeInfo is None):
                raise StreamException("setNoteTimeInfo cannot be run without setting timeInfo; best also to run applyTimeSignature also!")
            if (cloneit is True):
                thisNote.duration.timeInfo = copy.deepcopy(thisTimeInfo)
            else:
                thisNote.duration.timeInfo = thisTimeInfo
                
    def __getIntervalList(self):
        '''Returns an ordered list of the melodic intervals traversed when
        going directly from one note to the next (i.e. no rests in between).
        A None element indicates that one of the notes is a rest.'''
        if (self.__intervalList):
            return self.__intervalList
        else:
            self.generateIntervalLists()
            return self.__intervalList

    def __getIntervalORList(self):
        '''Returns an ordered list of the melodic intervals traversed when
        playing through the stream. If a rest is encountered, the interval will
        be to the next pitched note.'''
        if (self.__intervalORList):
            return self.__intervalORList
        else:
            try:
                self.generateIntervalLists()
            except:
                raise Exception("Could not generateIntervalLists")
            return self.__intervalORList

    def generateIntervalLists(self):
        '''Generates intervalList and intervalORList.'''
        iL = []
        iORL = []
        for i in range(0, self.totalNotes - 1):
            n1 = self.notesAndRests[i]
            n2 = self.notesAndRests[i+1]
            if n1 is None or n2 is None:
                raise StreamException("Some reason a NoneType is Here...")
            if n1.isRest == True or n2.isRest == True:
                iL.append(None)
                if n1.isRest == False:
                    n3 = self.noteFollowingNote(n2, allowRests = False)
                    if n3 is not None:
                        int1 = interval.notesToInterval(n1, n3)
                        n1.editorial.melodicIntervalOverRests = int1
                        iORL.append(int1)
            else:
                try:
                    int1 = interval.notesToInterval(n1, n2)
                except:
                    int1 = interval.notesToInterval(n1, n2)
                iL.append(int1)
                iORL.append(int1)
                n1.editorial.melodicInterval = int1
                n1.editorial.melodicIntervalOverRests = int1
        self.__intervalList = iL
        self.__intervalORList = iORL

    def __setIntervalList(self, value):
        '''Sets intervalList to value.'''
        self.__intervalList = value

    def __setIntervalORList(self, value):
        '''Sets intervalORList to value.'''
        self.__intervalORList = value

    intervalList = property(__getIntervalList, __setIntervalList)
    intervalOverRestsList = property(__getIntervalORList, __setIntervalORList)

class Stream(NoteStream):
    pass

class ChordStream(NoteStream):
    
    def maxChordNotes(self):
        '''
        returns an int of the most notes present in any chord in the ChordStream
        '''
        pass
    
    def sortAscendingAllChords(self):
        '''
        runs chord.sortAscending for every chord
        '''
        pass 

    def splitIntoNoteStreams(self, fillWithRests = False, copyNotes = False):
        pass
    


class StreamException(Exception):
    pass

if (__name__ == "__main__"):
    (note1,note2,note3,note4) = (note.Note (), note.Note (), note.Note(), note.Note())
    note1.name = "C"; note2.name = "D"; note3.name = "E-"; note4.name = "F#"
    rest1 = note.Rest()
    rest1.duration.type = "eighth"
    note1.duration.type = "whole"; note2.duration.type = "half"
    note3.duration.type = "quarter"; note4.duration.type = "eighth"
    stream1 = Stream ([note1, note2, note3, rest1, note4])
    assert stream1.totalDuration == 8
    for tN in stream1:
        tN.duration.dots = 1
    a = stream1.lily.value
    assert common.basicallyEqual(a, r'''\override Staff.StaffSymbol #'color = #(x11-color 'LightSlateGray) \clef "treble" c'1. d'2. ees'4. r8. fis'8. ''')
    ts1 = meter.TimeSignature("2/4")
    stream1.applyTimeSignature(ts1)
    stream1.setNoteTimeInfo(True)
    print stream1.intervalOverRestsList
    noteFollowingRest = stream1.noteFollowingNote(rest1, True)
    assert noteFollowingRest.name == "F#", "noteFollowingNote is not working!"
    assert note3.editorial.melodicIntervalOverRests.niceName == "Augmented Second", "melodicIntervalOverRests aint workin either!"

    note11 = note.Note()
    note11.name = "C"
    note11.duration.type = "quarter"
    note12 = note.Note()
    note11.name = "D"
    note12.duration.type = "quarter"
    note13 = note.Note()
    note13.name = "E"
    note13.duration.type = "quarter"
    note13.duration.dots = 1
    note14 = note.Note()
    note14.name = "F"
    note14.duration.type = "eighth"
    stream2 = Stream ([note11, note12, note13, note14])
    assert stream2.totalDuration == 4
    stream2.applyTimeSignature(ts1)
#    measures = stream2.makeMeasures(ts1)
#   for thisM in measures:
#      print "New Measure, number " + str(thisM.number)
#      if thisM.filled is True:
#           print "Filled up"
#        for thisN in thisM.notesAndRests:
#            print thisN.name
    
    note15 = note.Note()
    note15.name = "F#"
    note15.duration.type = "quarter"
    note16 = note.Note()
    note16.name = "G"
    note16.duration.type = "quarter"
    note16.duration.dots = 1
    
    stream3 = Stream ([note11, note12, note13, note15, note16])
    assert almostEquals(stream3.totalDuration, 6)
    stream3.applyTimeSignature(ts1)
    stream3.sliceDurationsForMeasures(ts1)
#    print stream3.lily

    nC = note.Note("C4"); nE = note.Note("E4"); nG = note.Note("G4")
    nC.duration.type  = "quarter"
    nE.duration.type  = "quarter"
    nG.duration.type  = "quarter"
    
    chord1 = chord.Chord([nC.pitch, nE.pitch, nG.pitch])
    stream4 = ChordStream([note15, chord1, note16])
#    assert stream4.maxChordNotes() == 3 
#    (stream4a, stream4b, stream4c) = stream4.splitIntoNoteStreams(fillWithRests = False)
#    assert stream4a.notesAndRests[0] is note15
#    assert stream4a.notesAndRests[1] is nC
#    assert stream4b.notesAndRests[1] is nE
