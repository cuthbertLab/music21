# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         eschbeg.py
# Purpose:      Demonstration of using music21 to test Taruskin's 
#               EsCHBEG assertions
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
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
import music21
import random

eschbeg = '30ET47'

def letterToNumber(letter):
    if letter == "E": number = 11
    elif letter == "T": number = 10
    else: number = int(letter)
    return number

def numberToLetter(number):
    if number == 11: letter = "E"
    elif number == 10: letter = "T"
    else: letter = str(number)
    return letter


def setupTranspositions():
    eschbegTransposed = []
    for i in range(0, 12):
        thisTransposition = ""
        for letter in eschbeg:
            number = letterToNumber(letter)
            newnum = (number + i) % 12
            newletter = numberToLetter(newnum)
            thisTransposition += newletter
        eschbegTransposed.append(thisTransposition)
    return eschbegTransposed

eschbegTransposed = setupTranspositions()

def generateToneRows(numberToGenerate = 1000):
    '''
    generates a list of random 12-tone rows.
    '''
    firstRow = list("0123456789TE")
    returnRows = []
    for i in range(numberToGenerate):
        random.shuffle(firstRow)
        returnRows.append(''.join(firstRow))
    return returnRows

def generateRandomRows(numberToGenerate = 1000):
    '''
    generates random rows which might have the
    same note twice, but never twice in a row.
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
    that contain the Eschbeg set,
    followed by the number that contain a
    transposition of the Eschbeg set.
    
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
    any other set:
    
    >>> print findEmbeddedChords("0234589")
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
    '''
    eschbegSplit12 = [letterToNumber(x) for x in testSet]
    ret = "" 
    for myTrichord in music21.chordTables.FORTE[cardinality]:
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
    return ret

if __name__ == "__main__":
    music21.mainTest()

#print findEmbeddedChords(cardinality = 5)
#p, t = priorProbability(1000000, enforce12Tone = False)
#print p
#print t

#------------------------------
#eof