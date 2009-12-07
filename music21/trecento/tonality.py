'''
music21.trecento.tonality

A series of example scripts that show how music21 can be used to analyze the pitch
relations between the incipit tenor note and the tenor note at cadences.

Also demonstrates the PNG generating abilities of the software, etc.

'''

import music21
import unittest

from music21.note import Note
from music21 import interval
import cadencebook
from re import match
from music21 import lily
from music21.lily import lilyString
import capua
import polyphonicSnippet
from music21.common import defHash

ph = lambda h = {}: defHash(h, default = False)

def landiniTonality():
    ballataObj  = cadencebook.BallataSheet()
    myDict = ph({'A': ph(), 'B': ph(), 'C': ph(), 'D': ph(), 'E': ph(), 'F': ph(), 'G': ph()})
    for thisWork in ballataObj:
        incip = thisWork.incipitClass()
        cadA  = thisWork.cadenceAClass()
        cadB  = thisWork.cadenceB2Class()
        if thisWork.composer != "Landini":
            continue
        if (incip is None or incip.streams is None or len(incip.streams) < 2):
            continue
        if (cadA is None or cadA.streams is None or len(cadA.streams) < 2):
            continue
        if (cadB is None or cadB.streams is None or len(cadB.streams) < 2):
            cadB = thisWork.cadenceB1Class()
        if (cadB is None or cadB.streams is None or len(cadB.streams) < 2):
            print thisWork.title.encode('utf-8')
            continue
        try:           
            firstTenorNote = incip.streams[1].getNotes()[0]
            cadATenorNote  = cadA.streams[1].getNotes()[-1]
            cadBTenorNote  = cadB.streams[1].getNotes()[-1]
        except IndexError:
            continue
        
        if match(thisWork.title,'Ecco la primavera'): #ends with a rest in all parts
            cadATenorNote  = cadA.streams[1].getNotes()[-2]
            cadBTenorNote  = cadB.streams[1].getNotes()[-2]
        if firstTenorNote.isRest is True:
            continue
            
        if firstTenorNote.isNote is True and cadATenorNote.isNote is True:
            myDict[firstTenorNote.step][cadATenorNote.step] += 1
        print "%30s %4s %4s %4s" % (thisWork.title.encode('utf-8')[0:30], firstTenorNote.name.encode('utf-8'),
                                    cadATenorNote.name.encode('utf-8'), cadBTenorNote.name.encode('utf-8'))
        
    bigTotalSame = 0
    bigTotalDiff = 0
    for outKey in sorted(myDict.keys()):
        outKeyDiffTotal = 0
        for inKey in sorted(myDict[outKey].keys()):
            if outKey == inKey:
                print "**** ",
                bigTotalSame += myDict[outKey][inKey]
            else:
                print "     ",
                outKeyDiffTotal += myDict[outKey][inKey]
                bigTotalDiff    += myDict[outKey][inKey] 
            print "%4s %4s %4d" % (outKey, inKey, myDict[outKey][inKey])
        print "      %4s diff %4d" % (outKey, outKeyDiffTotal)
    print "Total Same %4d %3.1f" % (bigTotalSame, (bigTotalSame * 100.0)/(bigTotalSame + bigTotalDiff))
    print "Total Diff %4d %3.1f" % (bigTotalDiff, (bigTotalDiff * 100.0)/(bigTotalSame + bigTotalDiff))


def nonLandiniBallataTonality():
    ballataObj  = cadencebook.BallataSheet()
    myDict = ph({'A': ph(), 'B': ph(), 'C': ph(), 'D': ph(), 'E': ph(), 'F': ph(), 'G': ph()})
    for thisWork in ballataObj:
        incip = thisWork.incipitClass()
        cadA  = thisWork.cadenceAClass()
        cadB  = thisWork.cadenceB2Class()
        if thisWork.composer == "Landini":
            continue
        if thisWork.composer == ".":  ## no anonymous
            continue
        if (incip is None or incip.streams is None or len(incip.streams) < 2):
            continue
        if (cadA is None or cadA.streams is None or len(cadA.streams) < 2):
            continue
        if (cadB is None or cadB.streams is None or len(cadB.streams) < 2):
            cadB = thisWork.cadenceB1Class()
        if (cadB is None or cadB.streams is None or len(cadB.streams) < 2):
            print thisWork.title.encode('utf-8')
            continue            
        firstTenorNote = incip.streams[1].getNotes()[0]
        cadATenorNote  = cadA.streams[1].getNotes()[-1]
        cadBTenorNote  = cadB.streams[1].getNotes()[-1]
        if match(thisWork.title,'Ecco la primavera'): #ends with a rest in all parts
            cadATenorNote  = cadA.streams[1].getNotes()[-2]
            cadBTenorNote  = cadB.streams[1].getNotes()[-2]
        if firstTenorNote.isRest is True:
            continue
            
        if firstTenorNote.isNote is True and cadATenorNote.isNote is True:
            myDict[firstTenorNote.step][cadATenorNote.step] += 1
        print "%30s %4s %4s %4s" % (thisWork.title.encode('utf-8')[0:30], firstTenorNote.name.encode('utf-8'),
                                    cadATenorNote.name.encode('utf-8'), cadBTenorNote.name.encode('utf-8'))
        
    bigTotalSame = 0
    bigTotalDiff = 0
    for outKey in sorted(myDict.keys()):
        outKeyDiffTotal = 0
        for inKey in sorted(myDict[outKey].keys()):
            if outKey == inKey:
                print "**** ",
                bigTotalSame += myDict[outKey][inKey]
            else:
                print "     ",
                outKeyDiffTotal += myDict[outKey][inKey]
                bigTotalDiff    += myDict[outKey][inKey] 
            print "%4s %4s %4d" % (outKey, inKey, myDict[outKey][inKey])
        print "      %4s diff %4d" % (outKey, outKeyDiffTotal)
    print "Total Same %4d %3.1f" % (bigTotalSame, (bigTotalSame * 100.0)/(bigTotalSame + bigTotalDiff))
    print "Total Diff %4d %3.1f" % (bigTotalDiff, (bigTotalDiff * 100.0)/(bigTotalSame + bigTotalDiff))

def anonBallataTonality():
    '''
    Gives a list of all anonymous ballate with their incipit tenor note and cadence tenor notes
    keeps track of how often they are the same and how often they are different.
    
    And then generates a PNG of the incipit and first cadence of all the ones that are the same.
    '''

    
    ballataObj  = cadencebook.BallataSheet()
    myDict = ph({'A': ph(), 'B': ph(), 'C': ph(), 'D': ph(), 'E': ph(), 'F': ph(), 'G': ph()})

    allLily = lily.LilyString()
    for thisWork in ballataObj:
        incip = thisWork.incipitClass()
        cadA  = thisWork.cadenceAClass()
        cadB  = thisWork.cadenceB2Class()
        if thisWork.composer != ".":
            continue
        if (incip is None or incip.streams is None or len(incip.streams) < 2):
            continue
        if (cadA is None or cadA.streams is None or len(cadA.streams) < 2):
            continue
        if (cadB is None or cadB.streams is None or len(cadB.streams) < 2):
            cadB = thisWork.cadenceB1Class()
        if (cadB is None or cadB.streams is None or len(cadB.streams) < 2):
            print thisWork.title.encode('utf-8')
            continue            
        firstTenorNote = incip.streams[1].getNotes()[0]
        cadATenorNote  = cadA.streams[1].getNotes()[-1]
        cadBTenorNote  = cadB.streams[1].getNotes()[-1]
        if match(thisWork.title,'Ecco la primavera'): #ends with a rest in all parts
            cadATenorNote  = cadA.streams[1].getNotes()[-2]
            cadBTenorNote  = cadB.streams[1].getNotes()[-2]
        if firstTenorNote.isRest is True:
            continue
            
        if firstTenorNote.isNote is True and cadATenorNote.isNote is True:
            myDict[firstTenorNote.step][cadATenorNote.step] += 1
            if firstTenorNote.step == cadATenorNote.step:
                allLily += incip.lily
                allLily += cadA.lily
                
        print "%30s %4s %4s %4s" % (thisWork.title.encode('utf-8')[0:30], firstTenorNote.name.encode('utf-8'),
                                    cadATenorNote.name.encode('utf-8'), cadBTenorNote.name.encode('utf-8'))
        
    bigTotalSame = 0
    bigTotalDiff = 0
    for outKey in sorted(myDict.keys()):
        outKeyDiffTotal = 0
        for inKey in sorted(myDict[outKey].keys()):
            if outKey == inKey:
                print "**** ",
                bigTotalSame += myDict[outKey][inKey]
            else:
                print "     ",
                outKeyDiffTotal += myDict[outKey][inKey]
                bigTotalDiff    += myDict[outKey][inKey] 
            print "%4s %4s %4d" % (outKey, inKey, myDict[outKey][inKey])
        print "      %4s diff %4d" % (outKey, outKeyDiffTotal)
    print "Total Same %4d %3.1f" % (bigTotalSame, (bigTotalSame * 100.0)/(bigTotalSame + bigTotalDiff))
    print "Total Diff %4d %3.1f" % (bigTotalDiff, (bigTotalDiff * 100.0)/(bigTotalSame + bigTotalDiff))

    print "Generating Lilypond PNG of all pieces where the first note of the tenor is the same pitchclass as the last note of Cadence A"
    print "It might take a while, esp. on the first Lilypond run..."
    allLily.showPNG()

def sacredTonality():
    '''
    Gives a list of all sacred pieces by incipit tenor note and first cadence tenor note
    and then notices which are the same and which are different.
    
    And then just displays all of them...
    '''
    
    kyrieObj  = cadencebook.KyrieSheet()
    gloriaObj  = cadencebook.GloriaSheet()
    credoObj  = cadencebook.CredoSheet()
    sanctusObj  = cadencebook.SanctusSheet()
    agnusObj  = cadencebook.AgnusDeiSheet()
    myDict = ph({'A': ph(), 'B': ph(), 'C': ph(), 'D': ph(), 'E': ph(), 'F': ph(), 'G': ph()})
    allWork = [kyrieObj.makeWork(2),
               gloriaObj.makeWork(2),
               credoObj.makeWork(2),
               sanctusObj.makeWork(2),
               agnusObj.makeWork(2) ]

    allLily = lily.LilyString()
    for thisWork in allWork:    
        incip = thisWork.incipitClass()
        cadA  = thisWork.snippetBlocks[-1]

        if (incip is None or incip.streams is None or len(incip.streams) < 2):
            continue
        if (cadA is None or cadA.streams is None or len(cadA.streams) < 2):
            continue
        allLily += incip.lily
        allLily += cadA.lily

        firstTenorNote = incip.streams[1].getNotes()[0]
        cadATenorNote  = cadA.streams[1].getNotes()[-1]
        if firstTenorNote.isRest is True:
            continue
            
        if firstTenorNote.isNote is True and cadATenorNote.isNote is True:
            myDict[firstTenorNote.step][cadATenorNote.step] += 1
        print "%30s %4s %4s" % (thisWork.title.encode('utf-8')[0:30], firstTenorNote.name.encode('utf-8'),
                                    cadATenorNote.name.encode('utf-8'))
        
    bigTotalSame = 0
    bigTotalDiff = 0
    for outKey in sorted(myDict.keys()):
        outKeyDiffTotal = 0
        for inKey in sorted(myDict[outKey].keys()):
            if outKey == inKey:
                print "**** ",
                bigTotalSame += myDict[outKey][inKey]
            else:
                print "     ",
                outKeyDiffTotal += myDict[outKey][inKey]
                bigTotalDiff    += myDict[outKey][inKey] 
            print "%4s %4s %4d" % (outKey, inKey, myDict[outKey][inKey])
        print "      %4s diff %4d" % (outKey, outKeyDiffTotal)
    print "Total Same %4d %3.1f" % (bigTotalSame, (bigTotalSame * 100.0)/(bigTotalSame + bigTotalDiff))
    print "Total Diff %4d %3.1f" % (bigTotalDiff, (bigTotalDiff * 100.0)/(bigTotalSame + bigTotalDiff))

    allLily.showPNG()

def sacredAllCadencesTonality():
    '''looks at all cadence tonalities compared to opening tenor note, not just final cadence'''
    kyrieObj  = cadencebook.KyrieSheet()
    gloriaObj  = cadencebook.GloriaSheet()
    credoObj  = cadencebook.CredoSheet()
    sanctusObj  = cadencebook.SanctusSheet()
    agnusObj  = cadencebook.AgnusDeiSheet()
    myDict = ph({'A': ph(), 'B': ph(), 'C': ph(), 'D': ph(), 'E': ph(), 'F': ph(), 'G': ph()})
    allWork = [ kyrieObj.makeWork(2),
               gloriaObj.makeWork(2),
               credoObj.makeWork(2),
               sanctusObj.makeWork(2),
               agnusObj.makeWork(2) ]

    allLily = lily.LilyString()
    for thisWork in allWork:    
        incip = thisWork.incipitClass()

        if (incip is None or incip.streams is None or len(incip.streams) < 2):
            continue

        for tS in incip.streams:
            capua.runRulesOnStream(tS)

        allLily += incip.lily
        firstTenorNote = incip.streams[1].getNotes()[0]
        if firstTenorNote.isRest is True:
                continue
            
        for i in range(1, len(thisWork.snippetBlocks)):
            thisCadence = thisWork.snippetBlocks[i]
            
            if (thisCadence is None or thisCadence.streams is None or len(thisCadence.streams) < 2):
                continue
            assert isinstance(thisCadence, polyphonicSnippet.PolyphonicSnippet)
            
            for tS in thisCadence.streams:
                capua.runRulesOnStream(tS)

            allLily += thisCadence.lily
            thisCadenceTenorNote  = thisCadence.streams[1].getNotes()[-1]
            
            if firstTenorNote.isNote is True and thisCadenceTenorNote.isNote is True:
                myDict[firstTenorNote.step][thisCadenceTenorNote.step] += 1
                print "%30s %4s %4s" % (thisWork.title.encode('utf-8')[0:30], firstTenorNote.name.encode('utf-8'),
                                        thisCadenceTenorNote.name.encode('utf-8'))
        
    bigTotalSame = 0
    bigTotalDiff = 0
    for outKey in sorted(myDict.keys()):
        outKeyDiffTotal = 0
        for inKey in sorted(myDict[outKey].keys()):
            if outKey == inKey:
                print "**** ",
                bigTotalSame += myDict[outKey][inKey]
            else:
                print "     ",
                outKeyDiffTotal += myDict[outKey][inKey]
                bigTotalDiff    += myDict[outKey][inKey] 
            print "%4s %4s %4d" % (outKey, inKey, myDict[outKey][inKey])
        print "      %4s diff %4d" % (outKey, outKeyDiffTotal)
    print "Total Same %4d %3.1f" % (bigTotalSame, (bigTotalSame * 100.0)/(bigTotalSame + bigTotalDiff))
    print "Total Diff %4d %3.1f" % (bigTotalDiff, (bigTotalDiff * 100.0)/(bigTotalSame + bigTotalDiff))

class TestExternal(unittest.TestCase):
    pass

    def testAll(self):
        landiniTonality()
        nonLandiniBallataTonality()
        anonBallataTonality()
        sacredTonality()
        sacredAllCadencesTonality()
        
if __name__ == "__main__":
    music21.mainTest(TestExternal)