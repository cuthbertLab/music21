# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.repetitionGame.py
# Purpose:      Repetition game, human player vs computer
#               
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

_DOC_IGNORE_MODULE_OR_PACKAGE = True

from music21 import scale, note
from music21 import audioSearch as base
#from music21.audioSearch import *
import time
import random



def runGame():
    useScale = scale.ChromaticScale('C4')
    roundNumber = 0
    good = True
    gameNotes = []
    
    print("Welcome to the music21 game!")
    print("Rules:")
    print("The computer generates a note (and it will play them in the future).")
    print("The player has to play all the notes from the beginning.")
    time.sleep(2)
    print("3, 2, 1 GO!")
    nameNotes = ["A", "B", "C", "D", "E", "F", "G"]
    while(good == True):
        randomNumber = random.randint(0, 6)
        octaveNumber = 4 # I can put a random number here...
        fullNameNote = "%s%d" % (nameNotes[randomNumber], octaveNumber)
        gameNotes.append(note.Note(fullNameNote))   
        
        roundNumber = roundNumber + 1
        print("ROUND %d" % roundNumber)
        print("NOTES UNTIL NOW: (this will not be shown in the final version)")
        for k in range(len(gameNotes)):
            print(gameNotes[k].fullName)
        
        seconds = 2 * roundNumber + 2
        freqFromAQList = base.getFrequenciesFromMicrophone(length=seconds, storeWaveFilename=None)
        detectedPitchesFreq = base.detectPitchFrequencies(freqFromAQList, useScale)
        detectedPitchesFreq = base.smoothFrequencies(detectedPitchesFreq)
        (detectedPitchObjects, unused_listplot) = base.pitchFrequenciesToObjects(detectedPitchesFreq, useScale)
        (notesList, unused_durationList) = base.joinConsecutiveIdenticalPitches(detectedPitchObjects)
        j = 0
        i = 0
        while i < len(notesList) and j < len(gameNotes) and good == True:
            if notesList[i].name == "rest":
                i = i + 1
            elif notesList[i].name == gameNotes[j].name:              
                i = i + 1
                j = j + 1
            else:
                print("WRONG NOTE! You played", notesList[i].fullName, "and should have been", gameNotes[j].fullName)
                good = False
           
        if good == True and j != len(gameNotes):
            good = False
            print("YOU ARE VERY SLOW!!! PLAY FASTER NEXT TIME!")
            
        if good == False:
            print("GAME OVER! TOTAL ROUNDS: %d" % roundNumber)

if __name__ == "__main__":
    runGame()
            
                            
#------------------------------------------------------------------------------
# eof
