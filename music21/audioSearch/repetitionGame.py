# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.repetitionGame.py
# Purpose:      Repetition game, human player vs human player
#               
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


from music21 import environment
from music21 import scale, stream, note, pitch
from music21.audioSearch.base import *
import time


def runGame():
    from music21.audioSearch import recording
    useScale = scale.ChromaticScale('C4')
    round = 0
    good = True
    gameNotes = []
    
    print "Welcome to the music21 game!"
    print "Rules:"
    print "Two players: the first one plays a note. \nThe second one has to play the first note and a new one."
    print "Continue doing the same until one fails."
    time.sleep(2)
    print "3, 2, 1 GO!"
    
    while(good == True):
        round = round + 1
        print "ROUND %d" % round
    #    print "NOTES UNTIL NOW: (this will not be shown in the final version)"
    #    for k in range(len(gameNotes)):
    #        print gameNotes[k].fullName
        
        seconds = 2 * round
        freqFromAQList = getFrequenciesFromMicrophone(length=seconds, storeWaveFilename=None)
        detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, useScale)
        detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
        (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, useScale)
        (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
        j = 0
        i = 0
        while i < len(notesList) and j < len(gameNotes) and good == True:
            if notesList[i].name == "rest":
                i = i + 1
            elif notesList[i].name == gameNotes[j].name:              
                i = i + 1
                j = j + 1
            else:
                print "WRONG NOTE! You played", notesList[i].fullName, "and should have been", gameNotes[j].fullName
                good = False
           
        if good == True and j != len(gameNotes):
            good = False
            print "YOU ARE VERY SLOW!!! PLAY FASTER NEXT TIME!"
            
        if good == False:
            print "YOU LOSE!! HAHAHAHA"
    
        else:
            while i < len(notesList) and notesList[i].name == "rest":
                i = i + 1
            if i < len(notesList):
                gameNotes.append(notesList[i])  #add a new note
                print "WELL DONE!"
            else:
                print "YOU HAVE NOT ADDED A NEW NOTE! REPEAT AGAIN NOW"
                round = round - 1
            

if __name__ == "__main__":
    runGame()
            
#------------------------------------------------------------------------------
# eof
