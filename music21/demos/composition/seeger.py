# -*- coding: utf-8 -*-
'''
Dynamically generating the 4th movement of Ruth Crawford Seeger's String Quartet 1931
'''


from music21 import converter
from music21 import meter
from music21 import note
from music21 import stream


import copy

def lowerLines():
    restLengths = [0, 16, 12, 11, 10, 7, 6, 7, 6, 5, 4, 3, 8, 10, 12, 14, 16, 17, 18, 19, 20]
    correctTranspositions = [-1, 2, -3, -3, 1, 1, 6, 3, -2] # correct the first note of rotations 13-21
    fixLastNoteLengths = {11: 4.5, 12: 3, 13: 2.5, 14: 2, 15: 1.5, 20: 10.5}
    
    currentNote = 0
    rotationNumber = 1
    myRow = stream.Part()
    for phraseNumber in range(1,21):
        myRow.append(note.Rest(quarterLength=restLengths[phraseNumber]/2.0))
        if phraseNumber == 8: ## inconsistency in RCS's scheme
            currentNote += 2
        for addNote in range(21 - phraseNumber):
            if rotationNumber <= 10 or rotationNumber >= 20:
                #default
                appendNote = copy.deepcopy(rowNotes[currentNote % 10])
            else: # second set of rotations is up a step:
                appendNote = rowNotes[currentNote % 10].transpose(2)
#                if phraseNumber == 8 and addNote == 9: # mistaken transpositions by RCS
#                    appendNote = appendNote.transpose(-1)
#                    appendNote.lyrics.append(note.Lyric(text="*", number=3))
#
#                elif phraseNumber == 9 and addNote == 6:
#                    appendNote = appendNote.transpose(2)
#                    appendNote.lyrics.append(note.Lyric(text="*", number=3))

            if addNote == 0:
                if phraseNumber != 8:
                    appendNote.lyrics.append(note.Lyric(text="p" + str(phraseNumber), number=1))
                else:
                    appendNote.lyrics.append(note.Lyric(text="p8*", number=1))
            if (currentNote % 10 == (rotationNumber + 8) % 10) and (currentNote != 0):
                currentNote += 2
                rotationNumber += 1
            else:
                if (currentNote % 10 == (rotationNumber + 9) % 10):
                    appendNote.lyrics.append(note.Lyric(text="r" + str(rotationNumber), number=2))
                    if rotationNumber in range(13, 22):
                        appendNote.transpose(correctTranspositions[rotationNumber-13], inPlace = True)
                        appendNote.pitch.simplifyEnharmonic(inPlace = True)
                        appendNote.lyrics.append(note.Lyric(text="*", number=3))
                        
                currentNote += 1
            if addNote == 20-phraseNumber: # correct Last Notes
                #if phraseNumber == 12: # bug in Finale for accidental display?
                #    appendNote.pitch.accidental.displayStatus = True
                if phraseNumber in fixLastNoteLengths:
                    appendNote.quarterLength = fixLastNoteLengths[phraseNumber]
            myRow.append(appendNote)

    #retrograde
    totalNotes = len(myRow)
    for i in range(2, totalNotes+1): #skip last note
        el = myRow[totalNotes-i]
        if 'Note' in el.classes:
            elNote = el.transpose('A1')
            elNote.pitch.simplifyEnharmonic(inPlace = True)
            elNote.lyrics = []
            myRow.append(elNote)
        else:
            elRest = copy.deepcopy(el) # rests
            if i == 2:
                elRest.quarterLength=11.5
            myRow.append(elRest)
    
    myRow.insert(0, meter.TimeSignature('2/2'))

    myRow.show()

if __name__ == '__main__':
    row = converter.parse('tinynotation: 2/2 d8 e f e- f# a a- g d- c')
    rowNotes = row.notes
    lowerLines()
