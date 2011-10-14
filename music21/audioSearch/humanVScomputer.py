# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.repetitionGame.py
# Purpose:      Repetition game, human player vs computer
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
import random



def runGame():
    from music21.audioSearch import recording 
    useScale = scale.ChromaticScale('C4')
    round = 0
    good = True
    gameNotes = []
    
    print "Welcome to the music21 game!"
    print "Rules:"
    print "The computer generates a note (and it will play them in the future)."
    print "The player has to play all the notes from the beginning."
    time.sleep(2)
    print "3, 2, 1 GO!"
    nameNotes = ["A", "B", "C", "D", "E", "F", "G"]
    while(good == True):
        randomNumber = random.randint(0, 6)
        octaveNumber = 4 # I can put a random number here...
        fullNameNote = "%s%d" % (nameNotes[randomNumber], octaveNumber)
        gameNotes.append(note.Note(fullNameNote))   
        
        round = round + 1
        print "ROUND %d" % round
        print "NOTES UNTIL NOW: (this will not be shown in the final version)"
        for k in range(len(gameNotes)):
            print gameNotes[k].fullName
        
        seconds = 2 * round + 2
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
            print "GAME OVER! TOTAL ROUNDS: %d" % round

if __name__ == "__main__":
    runGame()
            
                            
#------------------------------------------------------------------------------
# eof
