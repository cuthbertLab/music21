# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.scoreFollower.py
# Purpose:      Detection of the position in the score in real time  
#
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import math
import matplotlib.pyplot

import os
import random
import sys
from time import time

from music21 import corpus
from music21 import converter
from music21 import environment
from music21 import scale, stream, note, pitch
from music21.audioSearch.base import *
from music21.audioSearch import recording
_MOD = 'audioSearch/transcriber.py'
environLocal = environment.Environment(_MOD)

class ScoreFollower(object):
    
    def __init__(self, scoreStream=None):
        self.scoreStream = scoreStream
        if scoreStream is not None:
            self.scoreNotesOnly = scoreStream.flat.notesAndRests
        else:
            self.scoreNotesOnly = None
        self.waveFile = environLocal.getRootTempDir() + os.path.sep + 'scoreFollowerTemp.wav'
        self.lastNotePostion = 0
        self.currentSample = 0
        self.totalFile = 0
        self.lastNotePosition = 0
        self.startSearchAtSlot = 0
        self.predictedNotePosition = 0
        self.countdown = 0
        self.END_OF_SCORE = False
        self.lengthFixed = False
        self.qle = None


    def runScoreFollower(self, show=True, plot=False, useMic=False,
                      seconds=15.0, useScale=scale.ChromaticScale('C4')):
        '''
        I'll think about it.
        '''          
          
        self.begins = True
        self.seconds_recording = seconds
        
        self.useMic = useMic
        self.useScale = useScale
        
        self.result = False
        while(self.result is False): 
            self.result = self.repeatTranscription()    
              
        if show == True:
            #transcribedScore.show()    
            pass    

        if plot == True:
            matplotlib.pyplot.plot(listplot)
            matplotlib.pyplot.show()
        environLocal.printDebug("* END")
        return self.result


    def repeatTranscription(self):  
        print "WE STAY AT:  *****",
        print self.lastNotePosition, len(self.scoreNotesOnly),
        print "en percent %d %%" % (self.lastNotePosition * 100 / len(self.scoreNotesOnly)),
        print " this search begins at: ", self.startSearchAtSlot,
        print "countdown %d" %self.countdown

        if self.useMic == True:
            freqFromAQList = getFrequenciesFromMicrophone(length=self.seconds_recording, storeWaveFilename=None)
        else:
            freqFromAQList, self.waveFile, self.currentSample = getFrequenciesFromPartialAudioFile(self.waveFile, length=self.seconds_recording, startSample=self.currentSample)
            if self.totalFile == 0:
                self.totalFile = self.waveFile.getnframes()
        
        time_start = time()
        #print "MOSTRES LLEGIDES:       ----  %d/%d = %d %%" % (self.totsamples, self.totalfile, self.totsamples * 100 / self.totalfile)
        detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, self.useScale)
        detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
        (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, self.useScale)
        (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
        scNotes = self.scoreStream[self.lastNotePosition:self.lastNotePosition + len(notesList)]
        transcribedScore, self.lengthFixed, self.qle = notesAndDurationsToStream(notesList, durationList, scNotes=scNotes, lengthFixed=self.lengthFixed, qle=self.qle) 
        totalLengthPeriod, self.lastNotePosition, prob, END_OF_SCORE = self.matchingNotes(self.scoreStream, transcribedScore, self.startSearchAtSlot, self.lastNotePosition)

        if END_OF_SCORE == True:
            exitType = "endOfScore"  #"endOfScore"
            return exitType


        # estimate position, or exit if we can't at all...
        exitType = self.updatePosition(prob, totalLengthPeriod, time_start)

        if self.useMic == False: # reading from the disc (only for TESTS)
            # skip ahead the processing time.
            freqFromAQList, junk, self.currentSample = getFrequenciesFromPartialAudioFile(self.waveFile, length=self.processing_time, startSample=self.currentSample)
           
        if self.lastNotePosition > len(self.scoreNotesOnly):
            print "finishedPerforming"
            exitType = "finishedPerforming"
        elif (self.useMic == False and self.currentSample >= self.totalFile):
            print "waveFileEOF"
            exitType = "waveFileEOF"
        
        print "El que retorna el repeater",exitType
        return exitType

    def updatePosition(self, prob, totalLengthPeriod, time_start):
        '''
        It updates the position in which the scoreFollower starts to search at, 
        and the predicted position in which the new fragment of the score should start.
        It updates these positions taking into account the value of the "countdown", and if is the
        beginning of the song or not.
        
        It returns the exitType, which determines whether the scoreFollower has to stop (and why) or not.
        
        
        See example of a bad prediction at the beginning of the song:
        
        >>> from music21 import *
        >>> from time import time
        >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
        >>> ScF = ScoreFollower(scoreStream=scNotes)        
        >>> ScF.begins = True
        >>> ScF.startSearchAtSlot = 15
        >>> ScF.countdown = 0
        >>> prob = 0.5 # bad prediction
        >>> totalLengthPeriod = 15
        >>> time_start = time()
        >>> exitType = ScF.updatePosition(prob, totalLengthPeriod, time_start)
        >>> print ScF.startSearchAtSlot
        0
        
        
        Different examples for different countdowns:
        
        Countdown = 0:
        The last matching was good, so it calculates the position in which it starts
        to search at, and the position in which the music should start.
        
        >>> ScF = ScoreFollower(scoreStream=scNotes)
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
        >>> print ScF.startSearchAtSlot
        38
        >>> ScF.predictedNotePosition >=38
        True
        
        Countdown = 1: 
        Now it doesn't change the slot in which it starts to search at.
        It also predicts the position in which the music should start.
        
        >>> ScF = ScoreFollower(scoreStream=scNotes)
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
        >>> print ScF.startSearchAtSlot
        15
        >>> ScF.predictedNotePosition > 15
        True
        
        
        Countdown = 2: 
        Now it starts searching at the beginning of the page of the screen.
        The note prediction is also the beginning of the page.
        

        >>> ScF = ScoreFollower(scoreStream=scNotes)
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
        >>> print ScF.startSearchAtSlot
        15
        >>> print ScF.predictedNotePosition
        39
        
        
        Countdown = 4: 
        Now it starts searching at the beginning of the page of the screen.
        The note prediction is also the beginning of the page.
        

        >>> ScF = ScoreFollower(scoreStream=scNotes)
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
        >>> print ScF.startSearchAtSlot
        0
        >>> print ScF.predictedNotePosition
        0

        Countdown = 5: 
        Now it stops the program         
        
        >>> ScF = ScoreFollower(scoreStream=scNotes)
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
        >>> print exitType
        countdownExceeded
        '''
        exitType = False
        
        if self.begins == False:
            if self.countdown == 0:
                # successfully matched last note; predict next position.
                self.startSearchAtSlot = self.lastNotePosition
                processing_time = time() - time_start
                self.predictedNotePosition = self.predictNextNotePosition(totalLengthPeriod, processing_time)
            elif self.countdown == 1:
                # do nothing to startSearch or predicted note position
                totalSeconds = 2 * (time() - time_start) + self.seconds_recording
                self.predictedNotePosition = self.predictNextNotePosition(totalLengthPeriod, totalSeconds)                
            elif self.countdown == 2:
                # another chance to match notes
                totalSeconds = 3 * (time() - time_start) + self.seconds_recording
                self.predictedNotePosition = self.predictNextNotePosition(totalLengthPeriod, totalSeconds)               
            elif self.countdown > 2 and self.countdown < 5:
                #print "SEARCHING IN ALL THE SCORE; MAYBE THE MUSICIAN HAS STARTED FROM THE BEGINNING"
                firstSlot = self.getFirstSlotOnScreen()
                self.lastNotePosition = firstSlot
                self.startSearchAtSlot = firstSlot
                self.predictedNotePosition = firstSlot
                self.lengthFixed = False
            else: # self.countdown >= 5:
                #print "Exit due to bad recognition or rests"
                environLocal.printDebug("COUNTDOWN = 5")
                exitType = 'countdownExceeded'
        else:  # at beginning
            if prob < 0.7: #to avoid rests at the beginning
                self.lastNotePosition = 0
                self.startSearchAtSlot = 0
                self.lengthFixed = False
                environLocal.printDebug("Silence or noise at the beginning")
            else:  # got some good notes at the beginning!
                self.begins = False
                print "GO!"
            if self.countdown >= 5:
                exitType = "5consecutiveCountdownsBeginning"               
        
        return exitType
         


    def getFirstSlotOnScreen(self):
        '''
        returns the index of the first element on the screen right now.
        
        Doesn't work.
        
        
        '''
        return 0

    def predictNextNotePosition(self, totalLengthPeriod, totalSeconds):     
        '''
        It predicts the position in which the first note of the following recording
        note should start, taking into account the processing time of the computer.
        It has two inputs: totalLengthPeriod, that is the number of pulses or beats in the 
        recorded audio, and totalSeconds, that is the length in seconds of the processing time.
        
        It returns a number with the position of the predicted note in the score.
        
        >>> from music21 import *
        >>> from time import time
        >>> scNotes = corpus.parse('luca/gloria').parts[0].flat.notes        
        >>> ScF = ScoreFollower(scoreStream=scNotes)  
        >>> ScF.scoreNotesOnly = ScF.scoreStream.flat.notesAndRests 
        >>> ScF.lastNotePosition = 14
        >>> ScF.seconds_recording = 10
        >>> totalLengthPeriod = 8
        >>> totalSeconds = 2
        >>> predictedStartPosition = ScF.predictNextNotePosition(totalLengthPeriod, totalSeconds)
        >>> print predictedStartPosition
        16
        '''   
        extraLength = totalLengthPeriod * totalSeconds / self.seconds_recording
        middleRhythm = 0
        slots = 0
        
        while middleRhythm < extraLength:
            middleRhythm = middleRhythm + self.scoreNotesOnly[self.lastNotePosition + slots].quarterLength
            slots = slots + 1                
        predictedStartingNotePosition = int(slots + self.lastNotePosition)
        return predictedStartingNotePosition
                


    def matchingNotes(self, scoreStream, transcribedScore, notePrediction, lastNotePosition): 
        '''
        
        '''
        # Analyzing streams
        tn_recording = int(len(transcribedScore.flat.notesAndRests))
        totScores = []
        beginningData = []
        lengthData = []
        END_OF_SCORE = False
        tn_window = int(math.ceil(tn_recording * 1.1)) # take 10% more of samples
        hop = int(math.ceil(tn_window / 4))
        if hop == 0:
            iterations = 1
        else:
            iterations = int((math.floor(len(scoreStream) / hop)) - math.ceil(tn_window / hop)) 
        
        for i in range(iterations):
            scNotes = scoreStream[i * hop + 1 :i * hop + tn_recording + 1 ] 
            name = "%d" % i
            beginningData.append(i * hop + 1)
            lengthData.append(tn_recording)
            scNotes.id = name
            totScores.append(scNotes)  
    
        listOfParts = search.approximateNoteSearch(transcribedScore.flat.notes, totScores)
            
        #decision process    
        if notePrediction > len(scoreStream) - tn_recording - hop - 1:
            notePrediction = len(scoreStream) - tn_recording - hop - 1
            END_OF_SCORE = True
            environLocal.printDebug("**********++++ LAST PART OF THE SCORE ++++***********")
        position, self.countdown = decisionProcess(listOfParts, notePrediction, beginningData, lastNotePosition, self.countdown)
        try:
            print "measure: " + listOfParts[position][0].measureNumber     
        except:
            pass
        
        totalLength = 0    
        number = int(listOfParts[position].id)
        
        if self.countdown != 0:
            probabilityHit = 0
        else:
            probabilityHit = listOfParts[position].matchProbability
            
        for i in range(len(totScores[number])):
            totalLength = totalLength + totScores[number][i].quarterLength
    
        if self.countdown == 0:   
            lastNotePosition = beginningData[number] + lengthData[number]
                   
        return totalLength, lastNotePosition, probabilityHit, END_OF_SCORE



class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        pass
    
    def xtestRunScoreFollower(self):
        #scoreNotes = ["d8", "b8", "a8", "g8", "d2", "b8", "a8", "g8", "e2", "c'8", "b8", "a8", "f#2", "d8", "e8", "d8", "c8", "a8", "b8", "r4", "d4", "b4", "a4", "g4", "d4", "b4", "a4", "g4", "e4", "c4", "b4", "a4", "d4", "e4", "d4", "c4", "a4", "g4", "b4", "d4", "g4", "a4", "b4", "c4", "b4", "a4", "b4", "a4", "d4", "b4", "d4", "g4", "a4", "b4", "c4", "b4", "d4", "c4", "a4", "g4"]
        #scoreNotes = ["f'#4", "e'", "d'", "c'#", "b", "a", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "g", "e", "d8", "f#", "a", "g", "f#", "d", "f#", "e", "d", "B", "d", "a", "g", "b", "a", "g", "f#", "d", "e", "c'#", "d'", "f'#", "a'", "a", "b", "g", "a", "f#", "d", "d'16", "e'", "d'8", "c'#", "d'16", "c'#", "d'", "d", "c#", "a", "e", "f#", "d", "d'", "c'#", "b", "c'#", "f'#", "a'", "b'", "g'", "f'#", "e'", "g'", "f'#", "e'", "d'", "c'#", "b", "a", "g", "f#", "e", "g", "f#", "e", "d", "e", "f#", "g", "a", "e", "a", "g", "f#", "b", "a", "g", "a", "g", "f#", "e", "d", "B", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "e", "b", "a", "b", "a", "g", "f#8", "f'#", "e'4", "d'", "f'#", "b'4", "a'", "b'", "c'#'", "d''8", "d'", "c'#4", "b", "d'"]
        #scNotes = converter.parse(" ".join(scoreNotes), "4/4")
        scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
        ScF = ScoreFollower(scoreStream=scNotes)
        ScF.runScoreFollower(show=True, plot=False, useMic=True, seconds=10.0)
    


if __name__ == '__main__':
    music21.mainTest(TestExternal)


#------------------------------------------------------------------------------
# eof
