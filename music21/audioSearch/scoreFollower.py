# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.scoreFollower.py
# Purpose:      ...
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
        self.waveFile = 'xmas.wav'
        self.lastNotePostion = 0
        self.currentSample = 0
        self.totalFile = 0
        self.lastNotePosition = 0
        self.startSearchAtSlot = 0
        self.predictedNotePosition = 0
        self.result = stream.Part()
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
        self.countdown = 0
        self.useMic = useMic
        self.useScale = useScale
        
        result = False
        while(result is False): 
            result = self.repeatTranscription()
    
              
        if show == True:
            #transcribedScore.show()    
            pass    
        result.show('text')
        result.show()
        if plot == True:
            matplotlib.pyplot.plot(listplot)
            matplotlib.pyplot.show()
        environLocal.printDebug("* END")
        return result


    def repeatTranscription(self):  
        print "ANEM PER AQUI *****************", 
        print self.lastNotePosition, len(self.scoreNotesOnly), 
        print "en percent %d %%" % (self.lastNotePosition * 100 / len(self.scoreNotesOnly)), 
        print " this search begins at: ", self.startSearchAtSlot

        if self.useMic == True:
            freqFromAQList = getFrequenciesFromMicrophone(length=self.seconds_recording, storeWaveFilename=None)
        else:
            freqFromAQList, self.waveFile, self.currentSample = getFrequenciesFromPartialAudioFile(self.waveFile, length=self.seconds_recording, startSample = self.currentSample)
            if self.totalFile == 0:
                self.totalFile = self.waveFile.getnframes()
        
        time_start = time()
        #print "MOSTRES LLEGIDES:       ----  %d/%d = %d %%" % (self.totsamples, self.totalfile, self.totsamples * 100 / self.totalfile)
        detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, self.useScale)
        detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
        (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, self.useScale)
        (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
        scNotes = self.scoreStream[self.lastNotePosition:self.lastNotePosition + len(notesList)]
        print "long", self.lastNotePosition, self.lastNotePosition + len(notesList)
        transcribedScore, self.lengthFixed, self.qle = notesAndDurationsToStream(notesList, durationList, scNotes=scNotes, lengthFixed=self.lengthFixed, qle=self.qle) 
        print "FORA", self.lengthFixed
        #transcribedScore.show('text')
        totalLengthPeriod, self.lastNotePosition, prob, END_OF_SCORE, self.result, self.countdown = self.matchingNotes(self.scoreStream, transcribedScore, self.startSearchAtSlot, self.lastNotePosition, self.result, self.countdown)

        if END_OF_SCORE == True:
            exitType = self.result  #"endOfScore"
            return exitType


        # estimate position, or exit if we can't at all...
        exitType = self.updatePosition(prob, totalLengthPeriod, time_start)
        if exitType != False:
            print "exiting based on five countdowns"
            
            return self.result 
            #return exitType

        if self.useMic == False: # reading from the disc (only for TESTS)
            # skip ahead the processing time.
            freqFromAQList, junk, self.currentSample = getFrequenciesFromPartialAudioFile(self.waveFile, length=self.processing_time, startSample=self.currentSample)
            # print "MOSTRES LLEGIDES ABAIX:       ----  %d/%d = %d º/o" % (totsamples, totalfile, totsamples * 100 / totalfile)

        if self.lastNotePosition > len(self.scoreNotesOnly):
            print "finishedPerforming"
            exitType = self.result
        elif (self.useMic == False and self.currentSample >= self.totalFile):
            print "waveFileEOF"
            exitType = self.result # 
        else:
            exitType = False
        return exitType

    def updatePosition(self, prob, totalLengthPeriod, time_start):
        exitType = False
        
        if self.begins == False:
            if self.countdown == 0:
                # successfully matched last note; predict next position.
                self.startSearchAtSlot = self.lastNotePosition
                self.predictedNotePosition = self.predictNextNotePosition(totalLengthPeriod, time_start)
            elif self.countdown == 1:
                print "!!!!!!!!!COUNTDOWN!!!!!!", self.countdown
                self.predictedNotePosition = self.predictNextNotePosition(totalLengthPeriod, time_start)
    
                # do nothing to startSearch or predicted note position
            elif self.countdown >= 2 and self.countdown < 5:
                print "!!!!!!!!!COUNTDOWN!!!!!!", self.countdown
                print "SEARCHING IN ALL THE SCORE; MAYBE THE MUSICIAN HAS STARTED FROM THE BEGINNING"
                firstSlot = self.getFirstSlotOnScreen()
                self.lastNotePosition = firstSlot
                self.startSearchAtSlot = firstSlot
                self.predictedNotePosition = self.predictNextNotePosition(totalLengthPeriod, time_start)
                self.lengthFixed = False
            else: # self.countdown >= 5:
                print "Exit due to bad recognition or rests"
                exitType = 'countdownExceeded'
        else:  # at beginning
            if prob < 0.7: #to avoid silence at the beginning
                self.lastNotePosition = 0
                self.startSearchAtSlot = 0
                self.lengthFixed = False
                print "Silence or noise at the beginning"
            else:  # got some good notes at the beginning!
                self.begins = False
                print "GO!"
        
        return exitType
        


    def getFirstSlotOnScreen(self):
        '''
        returns the index of the first element on the screen right now.
        
        Doesn't work.
        
        
        '''
        return 0

    def predictNextNotePosition(self, totalLengthPeriod, time_start):
        processing_time = time() - time_start
        extraLength = totalLengthPeriod * processing_time / self.seconds_recording
        middleRhythm = 0
        slots = 0
        
        while middleRhythm < extraLength:
            middleRhythm = middleRhythm + self.scoreNotesOnly[self.lastNotePosition + slots].quarterLength
            slots = slots + 1                
        predictedStartingNotePosition = int(slots + self.lastNotePosition)
        return predictedStartingNotePosition
                


    def matchingNotes(self, scoreStream, transcribedScore, notePrediction, lastNotePosition, result, countdown):#i'll remove "result" soon
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
        print "number of iterations", iterations, hop, tn_window, len(scoreStream)
    
        #scNotes = copy.deepcopy(scoreStream)
        #scNotes = converter.parse(" ".join(scNotes), "4/4")
        #sN = copy.deepcopy(scNotes)
        #scNotes.elements = sN.elements[i * hop + 1 :i * hop + tn_recording + 1 ] #the [0] is the key 
        for i in range(iterations):
            scNotes = scoreStream[i * hop + 1 :i * hop + tn_recording + 1 ] 
            #scNotes = copy.deepcopy(scoreStream)
            #scNotes = converter.parse(" ".join(scNotes), "4/4")
            #scNotes.elements = scNotes.elements[i * hop + 1 :i * hop + tn_recording + 1 ] #the [0] is the key 
            name = "%d" % i
            #print "inici", i * hop + 1, i * hop + tn_recording + 1 
            beginningData.append(i * hop + 1)
            lengthData.append(tn_recording)
            scNotes.id = name
            totScores.append(scNotes)  
    
        listOfParts = search.approximateNoteSearch(transcribedScore.flat.notes, totScores)
    #    print "printo prob", len(totScores)  
    #    for i in l:
    #        print i.id, i.matchProbability#, totScores[i]
            
        #decision process    
        if notePrediction > len(scoreStream) - tn_recording - hop - 1:
            print "PETARIA", notePrediction, len(scoreStream) - tn_recording - hop - 1, len(scoreStream), tn_recording, hop
            notePrediction = len(scoreStream) - tn_recording - hop - 1
            END_OF_SCORE = True
            print "************++++ LAST PART OF THE SCORE ++++**************"
        position, countdown = decisionProcess(listOfParts, notePrediction, beginningData, lastNotePosition, countdown)
        try:
            print "measure: " + listOfParts[position][0].measureNumber     
        except:
            pass
        
        totalLength = 0    
        number = int(listOfParts[position].id)
        if result != None:
            result.append(listOfParts[number])
        
        if countdown != 0:
            probabilityHit = 0
        else:
            probabilityHit = listOfParts[position].matchProbability
        for i in range(len(totScores[number])):
            totalLength = totalLength + totScores[number][i].quarterLength
    
        if countdown == 0:   
            lastNotePosition = beginningData[number] + lengthData[number]
            
    #    if lastNotePosition < len(scoreStream) / 4:
    #        print "--------------------------1", lastNotePosition, len(scoreStream) / 4, len(scoreStream)
    #    elif lastNotePosition < len(scoreStream) / 2:
    #        print "--------------------------2", lastNotePosition, len(scoreStream) / 2, len(scoreStream)
    #    elif lastNotePosition < len(scoreStream) * 3 / 4:
    #        print "--------------------------2", lastNotePosition, len(scoreStream) * 3 / 4, len(scoreStream)
    #    else: 
    #        print "--------------------------2", lastNotePosition, len(scoreStream), len(scoreStream)
            
        return totalLength, lastNotePosition, probabilityHit, END_OF_SCORE, result, countdown #i'll remove "result" later,it's only to see if it works



if __name__ == '__main__':
    #scoreNotes = ["d8", "b8", "a8", "g8", "d2", "b8", "a8", "g8", "e2", "c'8", "b8", "a8", "f#2", "d8", "e8", "d8", "c8", "a8", "b8", "r4", "d4", "b4", "a4", "g4", "d4", "b4", "a4", "g4", "e4", "c4", "b4", "a4", "d4", "e4", "d4", "c4", "a4", "g4", "b4", "d4", "g4", "a4", "b4", "c4", "b4", "a4", "b4", "a4", "d4", "b4", "d4", "g4", "a4", "b4", "c4", "b4", "d4", "c4", "a4", "g4"]
    scoreNotes = ["f'#4", "e'", "d'", "c'#", "b", "a", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "g", "e", "d8", "f#", "a", "g", "f#", "d", "f#", "e", "d", "B", "d", "a", "g", "b", "a", "g", "f#", "d", "e", "c'#", "d'", "f'#", "a'", "a", "b", "g", "a", "f#", "d", "d'16", "e'", "d'8", "c'#", "d'16", "c'#", "d'", "d", "c#", "a", "e", "f#", "d", "d'", "c'#", "b", "c'#", "f'#", "a'", "b'", "g'", "f'#", "e'", "g'", "f'#", "e'", "d'", "c'#", "b", "a", "g", "f#", "e", "g", "f#", "e", "d", "e", "f#", "g", "a", "e", "a", "g", "f#", "b", "a", "g", "a", "g", "f#", "e", "d", "B", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "e", "b", "a", "b", "a", "g", "f#8", "f'#", "e'4", "d'", "f'#", "b'4", "a'", "b'", "c'#'", "d''8", "d'", "c'#4", "b", "d'"]
    scNotes = converter.parse(" ".join(scoreNotes), "4/4")
    #scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
    ScF = ScoreFollower(scoreStream=scNotes)
    ScF.runScoreFollower(show=True, plot=False, useMic=True, seconds=10.0)

#------------------------------------------------------------------------------
# eof


