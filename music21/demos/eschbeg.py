# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         eschbeg.py
# Purpose:      Demonstration of using music21 to test Taruskin's 
#               EsCHBEG assertions
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------

'''
In his landmark, Oxford History of Western Music, vol. 4, Richard Taruskin
spends an unusually long time discussing Arnold Schoenberg's supposed
love for encoding his own name in his music.  But it is quite possible
that most of his examples would arise due to chance given a highly
chromatic pitch world.  This module investigates the probability
of the set A.SCHBEG (=A. Schoenberg; with S = Es = E-flat; H=B, B=B-flat)
arising given the different exceptions that Taruskin allows.
'''
from music21 import chord
import random

eschbeg = '30ET47'

def letterToNumber(letter):
    if letter == "E": number = 11
    elif letter == "T": number = 10
    else: number = int(letter)
    return number

def numberToLetter(number):
    if number == 11: 
        letter = "E"
    elif number == 10: 
        letter = "T"
    else: 
        letter = str(number)
    return letter


def setupTranspositions():
    _eschbegTransposed = []
    for i in range(0, 12):
        thisTransposition = ""
        for letter in eschbeg:
            number = letterToNumber(letter)
            newnum = (number + i) % 12
            newletter = numberToLetter(newnum)
            thisTransposition += newletter
        _eschbegTransposed.append(thisTransposition)
    return _eschbegTransposed

eschbegTransposed = setupTranspositions()

def generateToneRows(numberToGenerate = 1000, cardinality=12):
    '''
    generates a list of random 12-tone rows.

    >>> from music21.demos import eschbeg
    >>> #_DOCS_SHOW eschbeg.generateToneRows(4)
    ['T310762985E4', '9E036T472158', '5879E3T12064', '417T26E95038']

    generate random 3-note sets:

    >>> #_DOCS_SHOW eschbeg.generateToneRows(4, 3)
    ['840', 'T61', 'T10', '173']
    '''
    allNotes = "0123456789TE"
    firstRow = list(allNotes)
    returnRows = []
    for i in range(numberToGenerate):
        random.shuffle(firstRow)
        returnRows.append(''.join(firstRow[0:cardinality]))
    return returnRows

def generateRandomRows(numberToGenerate = 1000):
    '''
    generates random rows which might have the
    same note twice, but never twice in a row.

    >>> from music21.demos import eschbeg
    >>> #_DOCS_SHOW eschbeg.generateRandomRows(4)
    ['67051534121', '05874071696', 'E082T6569674', '4E8383E4E395']
    '''
    returnRows = []
    for i in range(numberToGenerate):
        myRow = []
        lastLetter = ""
        for j in range(12):
            newLetter = numberToLetter(random.randint(0,11))
            if newLetter != lastLetter:
                myRow.append(newLetter)
                lastLetter = newLetter
            else:
                j = j-1
        returnRows.append(''.join(myRow))
    return returnRows


def priorProbability(rowsToTest = 1000000, enforce12Tone = True):
    '''
    Returns the number of randomly generated
    tone rows (or random 12 pitch collections)
    that contain the AEsCHBEG set,
    followed by the number that contain a
    transposition of the AEsCHBEG set.
    
    Works out to about 12 per million for the former
    and 130 per million for the latter.
    
    if enforce12Tone is False then random rows
    which might include pitch duplication are
    used.  This lowers the number of matching rows
    to about 4 and 30 in 1 million, respectively.
    (however, it doesn't find cases where a pitch
    is repeated immediately)
    '''
    if enforce12Tone is True:
        allRows = generateToneRows(rowsToTest)
    else:
        allRows = generateRandomRows(rowsToTest)
    eschbegTotal = 0
    eschbegTransTotal = 0
    for myRow in allRows:
        if eschbeg in myRow:
            eschbegTotal += 1
        for i in range(1,12):
            if eschbegTransposed[i] in myRow:
                eschbegTransTotal += 1
    return (eschbegTotal, eschbegTransTotal)

def findEmbeddedChords(testSet = "0234589", cardinality = 3, skipInverse = False):
    '''
    finds the trichords (or chords of other cardinalities) in the Aschbeg set or 
    any other set.  This example shows that every possible trichord appears at least once
    in the ESCHBEG set and two other trichords (037 = major/minor triad; 048 = augmented triad)
    appear just as often.   
    
    >>> from music21.demos import eschbeg
    >>> print(eschbeg.findEmbeddedChords("0234589"))
    [012]: (234) (345) 
    [013]: (235) 
    [023]: (023) (245) 
    [014]: (458) (890) 
    [034]: (034) (589) 
    [015]: (348) (459) 
    [045]: (045) (489) 
    [016]: (238) (349) (892) 
    [056]: (389) (923) 
    [024]: (024) 
    [025]: (025) (358) 
    [035]: (035) (902) 
    [026]: (248) (359) 
    [046]: (802) 
    [027]: (249) 
    [057]: (924) 
    [036]: (258) (903) 
    [037]: (259) (580) (904) 
    [047]: (590) (803) 
    [048]: (048) (480) (804)
    
    
    This is the all trichord hexachord:

    >>> print(eschbeg.findEmbeddedChords("012478", skipInverse=True))
    [012]: (012) 
    [013]: (124) 
    [014]: (014) 
    [015]: (780) 
    [016]: (127) (781) 
    [024]: (024) 
    [025]: (247) 
    [026]: (248) 
    [027]: (027) 
    [036]: (147) 
    [037]: (148) 
    [048]: (048) (480) (804) 

    But it does not contain every inversion:
    
    >>> print(eschbeg.findEmbeddedChords("012478"))
    [012]: (012) 
    [013]: (124) 
    [023]: 
    [014]: (014) 
    [034]: (478) 
    [015]: (780) 
    [045]: (801) 
    [016]: (127) (781) 
    [056]: (278) (701) (812) 
    [024]: (024) 
    [025]: (247) 
    [035]: 
    [026]: (248) 
    [046]: (802) 
    [027]: (027) 
    [057]: (702) 
    [036]: (147) 
    [037]: (148) 
    [047]: (047) 
    [048]: (048) (480) (804) 
    
    
    '''
    eschbegSplit12 = [letterToNumber(x) for x in testSet]
    ret = "" 
    for myTrichord in chord.tables.FORTE[cardinality]:
        if myTrichord is None:
            continue
        myPitches = myTrichord[0]

        myPitchString = ''.join([str(p) for p in myPitches])
        ret += "\n[" + myPitchString + "]: "
        for i in range(12):
            notFound = False
            transPitches = [(p+i)%12 for p in myPitches]
            for p in transPitches:
                if p not in eschbegSplit12:
                    notFound = True
            if notFound is False:
                transPitchesString = ''.join([str(p) for p in transPitches])
                ret += "(" + transPitchesString + ") "

        if skipInverse is False:
            myInverse = []
            for myPitch in myPitches:
                myInverse.append(11 - myPitch)
            myInverseMin = min(myInverse)
            for i,p in enumerate(myInverse):
                myInverse[i] = p - myInverseMin
            myInverse = sorted(myInverse)
            myInverseString = ''.join([str(p) for p in myInverse])
            if myInverseString != myPitchString: # some are symmetric
                ret += "\n[" + myInverseString + "]: "
                for i in range(12):
                    notFound = False
                    transInverse = [(p+i)%12 for p in myInverse]
                    for p in transInverse:
                        if p not in eschbegSplit12:
                            notFound = True
                    if notFound is False:
                        transInverseString = ''.join([str(p) for p in transInverse])
                        ret += "(" + transInverseString + ") "
    return ret.lstrip()

def uniquenessOfEschbeg(cardinality = 7, searchCardinality = 3, skipInverse = False, showMatching=True):
    '''
    the Eschbeg heptachord contains all trichords and their inversions.  How many heptachords do
    that?
    
    Returns a list of heptachords that have all of them.
    
    First a baseline:
    
    >>> from music21 import *
    >>> len(chord.tables.FORTE[7])
    39
    
    There are 39 chords in that list, but #0 is blank, so that you can reference them by
    conventional Forte numbers.  Thus there are 38 in actuality.
    
    >>> allTrichordAndInversionHeptachords = demos.eschbeg.uniquenessOfEschbeg()
    >>> len(allTrichordAndInversionHeptachords)
    16

    So almost half of all heptachords have a complete set of trichords and inversions. How many
    have all trichords without inversion?
    
    >>> len(demos.eschbeg.uniquenessOfEschbeg(skipInverse = True))
    18
    
    So, not too many more.
    
    For fun, other questions:
    
    Is there an all-tetrachord heptachord?
    
    >>> len(demos.eschbeg.uniquenessOfEschbeg(searchCardinality = 4, skipInverse = True))
    0
    
    Nope.  What about octachord?
    
    >>> len(demos.eschbeg.uniquenessOfEschbeg(cardinality = 8, searchCardinality = 4, skipInverse = True))
    2
    
    Yep! what are they?
    
    >>> demos.eschbeg.uniquenessOfEschbeg(cardinality = 8, searchCardinality = 4, skipInverse = True)
    ['01234689', '01235679']

    Notice that they're the complement sets of the all-interval tetrachords 0146 and 0137!
    
    Is every octachord all-trichord?
    
    >>> numOctochords = len(chord.tables.FORTE[8]) - 1
    >>> numOctochords
    29
    >>> len(demos.eschbeg.uniquenessOfEschbeg(cardinality = 8, searchCardinality = 3, skipInverse = True))
    22
    
    Nope.  Seven are not.  We can see them by reversing showMatching
    
    >>> demos.eschbeg.uniquenessOfEschbeg(cardinality = 8, searchCardinality = 3, skipInverse = True, showMatching = False)
    ['01234567', '01235678', '01236789', '02345679', '01234679', '0123578T', '0134679T']

    These are the complement sets of 0123 0128 0167 0235 0136 0258 0369
    
    '''
    allHeptachords = chord.tables.FORTE[cardinality]
    allHeptachordList = []
    for i in range(1, len(allHeptachords)):
        thisHeptachord = allHeptachords[i][0]
        thisHeptachordString = ''.join([numberToLetter(p) for p in thisHeptachord])
        #print thisHeptachordString
        foundTrichords = findEmbeddedChords(thisHeptachordString, 
                                            cardinality = searchCardinality, 
                                            skipInverse = skipInverse)
        foundTrichordList = foundTrichords.split('\n')
        noneMissing = True
        for trichordInfo in foundTrichordList:
            if '(' not in trichordInfo:
                noneMissing = False
                break
        if noneMissing == showMatching: # default True
            allHeptachordList.append(thisHeptachordString)
        
    return allHeptachordList

if __name__ == "__main__":
    import music21
    music21.mainTest()

    #print findEmbeddedChords(cardinality = 5)
    #p, t = priorProbability(100000, enforce12Tone = False)
    #print p
    #print t

#------------------------------
#eof
