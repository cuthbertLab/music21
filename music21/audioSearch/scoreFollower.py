# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         audioSearch.scoreFollower.py
# Purpose:      Detection of the position in the score in real time
#
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------


from time import time
import math
import os
import unittest

from music21 import scale
from music21 import search

from music21 import environment
_MOD = 'audioSearch/transcriber.py'
environLocal = environment.Environment(_MOD)


class ScoreFollower(object):

    def __init__(self, scoreStream=None):
        self.scoreStream = scoreStream
        if scoreStream is not None:
            self.scoreNotesOnly = scoreStream.flat.notesAndRests
        else:
            self.scoreNotesOnly = None
        self.waveFile = environLocal.getRootTempDir() + \
            os.path.sep + \
            'scoreFollowerTemp.wav'
        self.lastNotePostion = 0
        self.currentSample = 0
        self.totalFile = 0
        self.lastNotePosition = 0
        self.startSearchAtSlot = 0
        self.predictedNotePosition = 0
        self.countdown = 0
        self.END_OF_SCORE = False
        self.qle = None
        self.firstNotePage = None
        self.lastNotePage = None
        self.firstSlot = 1
        self.silencePeriodCounter = 0
        self.notesCounter = 0
        self.begins = True

        self.useScale = None
        self.silencePeriod = None
        self.result = None
        self.useMic = None
        self.processing_time = None
        self.seconds_recording = None

    def runScoreFollower(
        self,
        plot=False,
        useMic=False,
        seconds=15.0,
        useScale=None,
        ):
        '''
        The main program. It runs the 'repeatTranscription' until the
        performance ends.

        If `useScale` is none, then it uses a scale.ChromaticScale
        '''
        if useScale is None:
            useScale = scale.ChromaticScale('C4')
        self.seconds_recording = seconds
        self.useMic = useMic
        self.useScale = useScale

        self.result = False
        while(self.result is False):
            self.result = self.repeatTranscription()

#        if plot is True:
#            try:
#                import matplotlib.pyplot # for find
#            except ImportError:
#                raise AudioSearchException("Cannot plot without matplotlib installed.")
#
#            matplotlib.pyplot.plot(listplot)
#            matplotlib.pyplot.show()
        environLocal.printDebug("* END")

    def repeatTranscription(self):
        '''
        First, it records from the microphone (or from a file if is used for
        test). Later, it processes the signal in order to detect the pitches.
        It converts them into music21 objects and compares them with the score.
        It finds the best matching position of the recorded signal with the
        score, and decides, depending on matching accuracy, the last note
        predicted and some other parameters, in which position the recorded
        signal is.

        It returns a value that is False if the song has not finished, or true
        if there has been a problem like some consecutive bad matchings or the
        score has finished.

        >>> from music21.audioSearch import scoreFollower
        >>> scoreNotes = " ".join(["c4", "d", "e", "f", "g", "a", "b", "c'", "c", "e",
        ...     "g", "c'", "a", "f", "d", "c#", "d#", "f#","c", "e", "g", "c'",
        ...     "a", "f", "d", "c#", "d#", "f#"])
        >>> scNotes = converter.parse("tinynotation: 4/4 " + scoreNotes, makeNotation=False)
        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.useMic = False
        >>> import os #_DOCS_HIDE
        >>> readPath = os.path.join(common.getSourceFilePath(), 'audioSearch', 'test_audio.wav') #_DOCS_HIDE
        >>> ScF.waveFile = readPath #_DOCS_HIDE
        >>> #_DOCS_SHOW ScF.waveFile = 'test_audio.wav'
        >>> ScF.seconds_recording = 10
        >>> ScF.useScale = scale.ChromaticScale('C4')
        >>> ScF.currentSample = 0
        >>> exitType = ScF.repeatTranscription()
        >>> print(exitType)
        False
        >>> print(ScF.lastNotePosition)
        10

        '''
        from music21 import audioSearch

#        print "WE STAY AT:",
#        print self.lastNotePosition, len(self.scoreNotesOnly),
#        print "en percent %d %%" % (self.lastNotePosition * 100 / len(self.scoreNotesOnly)),
#        print " this search begins at: ", self.startSearchAtSlot,
#        print "countdown %d" % self.countdown
#        print "Measure last note", self.scoreStream[self.lastNotePosition].measureNumber

        environLocal.printDebug("repeat transcription starting")

        if self.useMic is True:
            freqFromAQList = audioSearch.getFrequenciesFromMicrophone(
                length=self.seconds_recording,
                storeWaveFilename=None,
                )
        else:
            freqFromAQList, self.waveFile, self.currentSample = \
                audioSearch.getFrequenciesFromPartialAudioFile(
                    self.waveFile,
                    length=self.seconds_recording,
                    startSample=self.currentSample,
                    )
            if self.totalFile == 0:
                self.totalFile = self.waveFile.getnframes()

        environLocal.printDebug("got Frequencies from Microphone")

        time_start = time()
        detectedPitchesFreq = audioSearch.detectPitchFrequencies(
            freqFromAQList, self.useScale)
        detectedPitchesFreq = audioSearch.smoothFrequencies(
            detectedPitchesFreq)
        detectedPitchObjects, unused_listplot = \
            audioSearch.pitchFrequenciesToObjects(
                detectedPitchesFreq, self.useScale)
        notesList, durationList = audioSearch.joinConsecutiveIdenticalPitches(
            detectedPitchObjects)
        self.silencePeriodDetection(notesList)
        environLocal.printDebug("made it to here...")
        scNotes = self.scoreStream[self.lastNotePosition:self.lastNotePosition
            + len(notesList)]
        #print "1"
        transcribedScore, self.qle = audioSearch.notesAndDurationsToStream(
            notesList,
            durationList,
            scNotes=scNotes,
            qle=self.qle,
            )
        #print "2"
        totalLengthPeriod, self.lastNotePosition, prob, END_OF_SCORE = \
            self.matchingNotes(
                self.scoreStream,
                transcribedScore,
                self.startSearchAtSlot,
                self.lastNotePosition,
                )
        #print "3"
        self.processing_time = time() - time_start
        environLocal.printDebug("and even to here...")
        if END_OF_SCORE is True:
            exitType = "endOfScore"  # "endOfScore"
            return exitType

        # estimate position, or exit if we can't at all...
        exitType = self.updatePosition(prob, totalLengthPeriod, time_start)

        if self.useMic is False:  # reading from the disc (only for TESTS)
            # skip ahead the processing time.
            freqFromAQList, junk, self.currentSample = \
                audioSearch.getFrequenciesFromPartialAudioFile(
                    self.waveFile,
                    length=self.processing_time,
                    startSample=self.currentSample,
                    )

        if self.lastNotePosition > len(self.scoreNotesOnly):
            #print "finishedPerforming"
            exitType = "finishedPerforming"
        elif (self.useMic is False and self.currentSample >= self.totalFile):
            #print "waveFileEOF"
            exitType = "waveFileEOF"

        environLocal.printDebug("about to return -- exitType: %s " % exitType)
        return exitType


    def silencePeriodDetection(self, notesList):
        '''
        Detection of consecutive periods of silence.
        Useful if the musician has some consecutive measures of silence.

        >>> from music21.audioSearch import scoreFollower
        >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> notesList = []
        >>> notesList.append(note.Rest())
        >>> ScF.notesCounter = 3
        >>> ScF.silencePeriodCounter = 0
        >>> ScF.silencePeriodDetection(notesList)
        >>> ScF.notesCounter
        0
        >>> ScF.silencePeriodCounter
        1


        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> notesList = []
        >>> notesList.append(note.Rest())
        >>> notesList.append(note.Note())
        >>> ScF.notesCounter = 1
        >>> ScF.silencePeriodCounter = 3
        >>> ScF.silencePeriodDetection(notesList)
        >>> ScF.notesCounter
        2
        >>> ScF.silencePeriodCounter
        0
        '''
        onlyRests = True
        for i in notesList:
            if i.name != 'rest':
                onlyRests = False

        if onlyRests is True:
            self.silencePeriod = True
            self.notesCounter = 0
            self.silencePeriodCounter += 1
        else:
            self.silencePeriod = False
            self.notesCounter += 1
            self.silencePeriodCounter = 0

    def updatePosition(self, prob, totalLengthPeriod, time_start):
        '''
        It updates the position in which the scoreFollower starts to search at,
        and the predicted position in which the new fragment of the score
        should start.  It updates these positions taking into account the value
        of the "countdown", and if is the beginning of the song or not.

        It returns the exitType, which determines whether the scoreFollower has
        to stop (and why) or not.

        See example of a bad prediction at the beginning of the song:

        >>> from time import time
        >>> from music21.audioSearch import scoreFollower
        >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.begins = True
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.countdown = 0
        >>> prob = 0.5 # bad prediction
        >>> totalLengthPeriod = 15
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print(ScF.startSearchAtSlot)
        0

        Different examples for different countdowns:

        Countdown = 0:

        The last matching was good, so it calculates the position in which it
        starts to search at, and the position in which the music should start.

        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.scoreNotesOnly = scNotes.flat.notesAndRests
        >>> ScF.begins = False
        >>> ScF.countdown = 0
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.lastNotePosition = 38
        >>> ScF.predictedNotePosition = 19
        >>> ScF.seconds_recording = 10
        >>> prob = 0.8
        >>> totalLengthPeriod = 25
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print(ScF.startSearchAtSlot)
        38

        >>> ScF.predictedNotePosition >=38
        True

        Countdown = 1:

        Now it doesn't change the slot in which it starts to search at.
        It also predicts the position in which the music should start.

        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.begins = False
        >>> ScF.countdown = 1
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.lastNotePosition = 15
        >>> ScF.predictedNotePosition = 19
        >>> ScF.seconds_recording = 10
        >>> prob = 0.8
        >>> totalLengthPeriod = 25
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print(ScF.startSearchAtSlot)
        15

        >>> ScF.predictedNotePosition > 15
        True

        Countdown = 2:

        Now it starts searching at the beginning of the page of the screen.
        The note prediction is also the beginning of the page.

        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.begins = False
        >>> ScF.countdown = 2
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.lastNotePosition = 15
        >>> ScF.predictedNotePosition = 19
        >>> ScF.seconds_recording = 10
        >>> prob = 0.8
        >>> totalLengthPeriod = 25
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print(ScF.startSearchAtSlot)
        15

        >>> print(ScF.predictedNotePosition)
        39

        Countdown = 4:

        Now it starts searching at the beginning of the page of the screen.
        The note prediction is also the beginning of the page.

        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.begins = False
        >>> ScF.countdown = 4
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.lastNotePosition = 15
        >>> ScF.predictedNotePosition = 19
        >>> ScF.seconds_recording = 10
        >>> prob = 0.8
        >>> totalLengthPeriod = 25
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print(ScF.startSearchAtSlot)
        0

        >>> print(ScF.predictedNotePosition)
        0

        Countdown = 5:

        Now it stops the program.

        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.begins = False
        >>> ScF.countdown = 5
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.lastNotePosition = 15
        >>> ScF.predictedNotePosition = 19
        >>> ScF.seconds_recording = 10
        >>> prob = 0.8
        >>> totalLengthPeriod = 25
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print(exitType)
        countdownExceeded

        '''
        exitType = False

        if not self.begins:
            if self.countdown == 0:
                # successfully matched last note; predict next position.
                self.startSearchAtSlot = self.lastNotePosition
                processing_time = time() - time_start
                self.predictedNotePosition = self.predictNextNotePosition(
                    totalLengthPeriod, processing_time)
            elif self.countdown == 1:
                # do nothing to startSearch or predicted note position
                totalSeconds = 2 * (time() - time_start) + \
                    self.seconds_recording
                self.predictedNotePosition = self.predictNextNotePosition(
                    totalLengthPeriod, totalSeconds)
            elif self.countdown == 2:
                # another chance to match notes
                totalSeconds = 3 * (time() - time_start) + \
                    self.seconds_recording
                self.predictedNotePosition = self.predictNextNotePosition(
                    totalLengthPeriod, totalSeconds)
            elif self.countdown == 3:
                # searching at the beginning of the shown pages
                self.lastNotePosition = self.firstSlot
                self.startSearchAtSlot = self.firstSlot
                self.predictedNotePosition = self.firstSlot
            elif self.countdown == 4:
                # SEARCHING IN ALL THE SCORE;
                # MAYBE THE MUSICIAN HAS STARTED FROM THE BEGINNING
                self.lastNotePosition = 0
                self.startSearchAtSlot = 0
                self.predictedNotePosition = 0
            else:  # self.countdown >= 5:
                #print "Exit due to bad recognition or rests"
                environLocal.printDebug("COUNTDOWN = 5")
                exitType = 'countdownExceeded'
        else:  # at beginning
            if prob < 0.7:  # to avoid rests at the beginning
                self.lastNotePosition = 0
                self.startSearchAtSlot = 0
                environLocal.printDebug("Silence or noise at the beginning")
            else:  # got some good notes at the beginning!
                self.begins = False
#                print "GO!"
            if self.countdown >= 5:
                exitType = "5consecutiveCountdownsBeginning"
        return exitType

    def getFirstSlotOnScreen(self):
        '''
        Returns the index of the first element on the screen right now.

        Doesn't work. (maybe it's not necessary)
        '''
        return 0

    def predictNextNotePosition(self, totalLengthPeriod, totalSeconds):
        '''
        It predicts the position in which the first note of the following
        recording note should start, taking into account the processing time of
        the computer.  It has two inputs: totalLengthPeriod, that is the number
        of pulses or beats in the recorded audio, and totalSeconds, that is the
        length in seconds of the processing time.

        It returns a number with the position of the predicted note in the
        score.

        >>> from time import time
        >>> from music21.audioSearch import scoreFollower
        >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
        >>> ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        >>> ScF.scoreNotesOnly = ScF.scoreStream.flat.notesAndRests
        >>> ScF.lastNotePosition = 14
        >>> ScF.seconds_recording = 10.0
        >>> totalLengthPeriod = 8
        >>> totalSeconds = 2.0
        >>> predictedStartPosition = ScF.predictNextNotePosition(
        ...     totalLengthPeriod, totalSeconds)
        >>> print(predictedStartPosition)
        18

        '''
        extraLength = totalLengthPeriod * totalSeconds / float(self.seconds_recording)
        middleRhythm = 0
        slots = 0

        while middleRhythm < extraLength:
            middleRhythm = middleRhythm + self.scoreNotesOnly[
                self.lastNotePosition + slots].quarterLength
            slots = slots + 1
        predictedStartingNotePosition = int(slots + self.lastNotePosition)
        return predictedStartingNotePosition

    def matchingNotes(
        self,
        scoreStream,
        transcribedScore,
        notePrediction,
        lastNotePosition,
        ):
        from music21 import audioSearch

        # Analyzing streams
        tn_recording = int(len(transcribedScore.flat.notesAndRests))
        totScores = []
        beginningData = []
        lengthData = []
        END_OF_SCORE = False
        # take 10% more of samples
        tn_window = int(math.ceil(tn_recording * 1.1))
        hop = int(math.ceil(tn_window / 4))
        if hop == 0:
            iterations = 1
        else:
            iterations = int((math.floor(len(scoreStream) / hop)) -
                math.ceil(tn_window / hop))

        for i in range(iterations):
            scNotes = scoreStream[i * hop + 1:i * hop + tn_recording + 1]
            name = "%d" % i
            beginningData.append(i * hop + 1)
            lengthData.append(tn_recording)
            scNotes.id = name
            totScores.append(scNotes)
        listOfParts = search.approximateNoteSearchWeighted(
            transcribedScore.flat.notesAndRests, totScores)

        #decision process
        if notePrediction > len(scoreStream) - tn_recording - hop - 1:
            notePrediction = len(scoreStream) - tn_recording - hop - 1
            END_OF_SCORE = True
            environLocal.printDebug("LAST PART OF THE SCORE")

        #lastCountdown = self.countdown
        position, self.countdown = audioSearch.decisionProcess(
            listOfParts,
            notePrediction,
            beginningData,
            lastNotePosition,
            self.countdown,
            self.firstNotePage,
            self.lastNotePage,
            )

        totalLength = 0
        number = int(listOfParts[position].id)

        if self.silencePeriod is True and self.silencePeriodCounter < 5:
            # print lastCountdown, self.countdown, lastNotePosition, beginningData[number], lengthData[number]
            environLocal.printDebug("All rest period")
            self.countdown -= 1

        if self.countdown != 0:
            probabilityHit = 0
        else:
            probabilityHit = listOfParts[position].matchProbability

        unused_listOfParts2 = search.approximateNoteSearch(transcribedScore.flat.notesAndRests, totScores)
        unused_listOfParts3 = search.approximateNoteSearchNoRhythm(transcribedScore.flat.notesAndRests, totScores)
        unused_listOfParts4 = search.approximateNoteSearchOnlyRhythm(transcribedScore.flat.notesAndRests, totScores)
#        print "PROBABILITIES:",
#        print "pitches and durations weighted (current)",listOfParts[position].matchProbability,
#        print "pitches and durations without weighting" , listOfParts2[position].matchProbability,
#        print "pitches", listOfParts3[position].matchProbability,
#        print "durations",listOfParts4[position].matchProbability

        for i in range(len(totScores[number])):
            totalLength = totalLength + totScores[number][i].quarterLength

        if self.countdown == 0 and self.silencePeriodCounter == 0:
            lastNotePosition = beginningData[number] + lengthData[number]

        return totalLength, lastNotePosition, probabilityHit, END_OF_SCORE


#------------------------------------------------------------------------------


class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        pass

    def xtestRunScoreFollower(self):
        from music21 import corpus
        scNotes = corpus.parse('luca/gloria').parts[0].flat.notesAndRests
        ScF = ScoreFollower(scoreStream=scNotes)
        ScF.runScoreFollower(plot=False, useMic=True, seconds=10.0)


#------------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(TestExternal)


#------------------------------------------------------------------------------
# eof
