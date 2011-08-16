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


def runscoreFollower(show=True, scoreStream=None, plot=True, useMic=False,
                  seconds=15.0, useScale=scale.ChromaticScale('C4')):
    '''
    I'll think about it.
    '''
    scoreNotesOnly = scoreStream.flat.notesAndRests
    WAVE_FILENAME = "xmas.wav"    
    lastNotePosition = 0
    totsamples = 0
    totalfile = 10
    notePrediction = 0
    wvfd = None
    result = stream.Part()
    seconds_recording = 10
    countdown = 0
    END_OF_SCORE = False
    begins = True
    lengthFixed = False
    qle = None
    while(lastNotePosition < len(scoreNotesOnly)) and (totsamples < totalfile) and (END_OF_SCORE == False):
        print "ANEM PER AQUI *****************", lastNotePosition, len(scoreNotesOnly), "en percent %d %%" % (lastNotePosition * 100 / len(scoreNotesOnly)), "new", notePrediction
        freqFromAQList, wvfd, totsamples, totalfile = getFrequenciesFromAudio(record=useMic, length=seconds_recording, waveFilename=WAVE_FILENAME, wholeFile=False, wv=wvfd, totsamples=totsamples)
        time_start = time()
        #print "MOSTRES LLEGIDES:       ----  %d/%d = %d º/o" % (totsamples, totalfile, totsamples * 100 / totalfile)
        detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale)
        detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
        (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, useScale)
        (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
        scNotes = scoreStream[lastNotePosition:lastNotePosition + len(notesList)]
        print "long", lastNotePosition, lastNotePosition + len(notesList)
        transcribedScore, lengthFixed, qle = notesAndDurationsToStream(notesList, durationList, scNotes=scNotes, lengthFixed=lengthFixed, qle=qle) 
        print "FORA", lengthFixed
        #transcribedScore.show('text')
        totalLengthPeriod, lastNotePosition, prob, END_OF_SCORE, result, countdown = matchingNotes(scoreStream, transcribedScore, notePrediction, lastNotePosition, result, countdown)
        if countdown >= 5:
            END_OF_SCORE = True # Exit due to bad recognition or rests
            print "Exit due to bad recognition or rests"
        
        # estimation of the position        
        processing_time = time() - time_start
        extraLength = totalLengthPeriod * processing_time / seconds        
        middleRhythm = 0
        slots = 0 # will be the number of slots of the score during the processing time        
        if END_OF_SCORE == False:
            while middleRhythm < extraLength:
                middleRhythm = middleRhythm + scoreNotesOnly[lastNotePosition + slots].quarterLength
                slots = slots + 1                
            if countdown == 0:
                notePrediction = int(slots + lastNotePosition)
            else:
                print "!!!!!!!!!COUNTDOWN!!!!!!", countdown
                if countdown == 2:
                    print "SEARCHING IN ALL THE SCORE; MAYBE THE MUSICIAN HAS STARTED FROM THE BEGINNING"
                    lastNotePosition = 0
                    notePrediction = 0
                    
            #new note?
            lengthForward = 0
            if prob < 0.7 and begins == True: #to avoid silence at the beginning
                lastNotePosition = 0
                notePrediction = 0
                lengthFixed = False
                print "Silence or noise at the beginning"
            else:
                begins = False
                print "GO!"
                seconds_recording = seconds # not needed

            if useMic == False: # reading from the disc (only for TESTS)
                fre, wv, totsamples, totalfile = getFrequenciesFromAudio(record=False, length=processing_time, waveFilename='xmas.wav', entireFile=False, wv=wvfd, totsamples=totsamples)
                print "MOSTRES LLEGIDES ABAIX:       ----  %d/%d = %d º/o" % (totsamples, totalfile, totsamples * 100 / totalfile)
            
    if show == True:
        #transcribedScore.show()    
        pass    
    result.show('text')
    result.show()
    if plot == True:
        matplotlib.pyplot.plot(listplot)
        matplotlib.pyplot.show()
    environLocal.printDebug("* END")
    return transcribedScore

if __name__ == '__main__':
    #scoreNotes = ["d8", "b8", "a8", "g8", "d2", "b8", "a8", "g8", "e2", "c'8", "b8", "a8", "f#2", "d8", "e8", "d8", "c8", "a8", "b8", "r4", "d4", "b4", "a4", "g4", "d4", "b4", "a4", "g4", "e4", "c4", "b4", "a4", "d4", "e4", "d4", "c4", "a4", "g4", "b4", "d4", "g4", "a4", "b4", "c4", "b4", "a4", "b4", "a4", "d4", "b4", "d4", "g4", "a4", "b4", "c4", "b4", "d4", "c4", "a4", "g4"]
    #scoreNotes = ["f'#4", "e'", "d'", "c'#", "b", "a", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "g", "e", "d8", "f#", "a", "g", "f#", "d", "f#", "e", "d", "B", "d", "a", "g", "b", "a", "g", "f#", "d", "e", "c'#", "d'", "f'#", "a'", "a", "b", "g", "a", "f#", "d", "d'16", "e'", "d'8", "c'#", "d'16", "c'#", "d'", "d", "c#", "a", "e", "f#", "d", "d'", "c'#", "b", "c'#", "f'#", "a'", "b'", "g'", "f'#", "e'", "g'", "f'#", "e'", "d'", "c'#", "b", "a", "g", "f#", "e", "g", "f#", "e", "d", "e", "f#", "g", "a", "e", "a", "g", "f#", "b", "a", "g", "a", "g", "f#", "e", "d", "B", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "e", "b", "a", "b", "a", "g", "f#8", "f'#", "e'4", "d'", "f'#", "b'4", "a'", "b'", "c'#'", "d''8", "d'", "c'#4", "b", "d'"]
    #scNotes = converter.parse(" ".join(scoreNotes), "4/4")
    scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
    runscoreFollower(show=True, scoreStream=scNotes, plot=True, useMic=True, seconds=10.0)

#------------------------------------------------------------------------------
# eof


