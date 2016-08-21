# -*- coding: utf-8 -*-
'''
Module to determine how often we would expect to have Francesco\'s cadences happen by chance
'''
from collections import defaultdict
#import random

from music21.alpha.trecento import cadencebook

#def getRandomIncipitNote(p):
#    probabilities = []


def getLandiniRandomStart(i):
    '''according to distribution of starting tenor notes of Landini cadences'''
    if i < 16: 
        return "A"
    if i < 35: 
        return "C"
    if i < 67: 
        return "D"
    if i < 69: 
        return "E"
    if i < 85: 
        return "F"
    return "G"

# def findsame(total = 1000):
#     '''find out how often the first note and second note should be the same 
#     according to chance, given Landini\'s distribution of pitches.
#     '''
#     same = 0
#     for i in range(0,total):
#         (n1, n2) = (random.randrange(138), random.randrange(138))
#         if getLetter(n1) == getLetter(n2):
#             same += 1
#     return same

# def multipleFindsame(total = 10000):
#     '''find out how often findsame percentage meets or exceeds Landini\'s same count
#     which is either 64 out of 138 (for A cadences) or 49 (for B cadences)
#     '''
#     mulFS = 0
#     for i in range(0, total):
#         same = findsame(138)
#         if same >= 64: 
#             mulFS += 1
#     return mulFS

def countCadencePercentages():
    ballatas = cadencebook.BallataSheet()
    totalPieces = 0.0
    firstNoteTotal = defaultdict(lambda:0)
    lastNoteTotal = defaultdict(lambda:0) 
    
    for thisWork in ballatas:
        incipit = thisWork.incipit
        cadenceB = thisWork.cadenceA #BClos or thisWork.cadenceBOuvert
        
#        if thisWork.composer != 'A. Zacara' and thisWork.composer != 'Zacharias':
#            continue
        if incipit is None or cadenceB is None:
            continue
        
        incipitTenor = incipit.tenor
        cadenceBTenor = cadenceB.tenor
            
        if incipitTenor is None or cadenceBTenor is None:
            continue
        
        firstNotes = incipitTenor.flat.getElementsByClass('Note')
        lastNotes  = cadenceBTenor.flat.getElementsByClass('Note')
            
        if len(firstNotes) == 0 or len(lastNotes) == 0:
            continue
        
        firstNote = firstNotes[0]
        lastNote = lastNotes[-1]
                    
        print(thisWork.title, firstNote.name, lastNote.name)
        totalPieces += 1.0  # for float division later
        firstNoteTotal[firstNote.name] += 1
        lastNoteTotal[lastNote.name] += 1
    
    print ("First note distribution:")
    
    for thisName in firstNoteTotal:
        print (thisName, firstNoteTotal[thisName]/totalPieces)

    print ("Last note distribution:")
    
    for thisName in lastNoteTotal:
        print (thisName, lastNoteTotal[thisName]/totalPieces) 
        
if __name__ == "__main__":
    countCadencePercentages()

#------------------------------------------------------------------------------
# eof

