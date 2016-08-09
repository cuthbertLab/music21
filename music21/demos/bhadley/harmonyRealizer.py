# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         harmonyRealizer.py
#
# Purpose:      Demonstration of using music21 (especially fbRealizer, harmony, 
#               and romanText.clercqTemperley) to generate smooth voice-leading 
#               arrangements of a harmony line (roman Numerals and chord symbols)
#
# Authors:      Beth Hadley
#               fbRealizer: Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

#    TODO:
#    1.
#    current examples do not handle changes in key signature or time signature
#    each change requires a new fbLine to be created...which destroys the 
#    voice-Leading continuity between these changes
#    
#    2.
#    unify approach to harmony objects (chordsymbols vs. roman numerals)
#    
#    3.
#    accommodate pop-music specific harmonies (9th/11th/13th chords)

from music21 import clef
from music21 import harmony
from music21 import interval
from music21 import metadata
from music21 import note
from music21 import roman
from music21 import stream
from music21 import corpus
from music21.figuredBass import realizer, rules
from music21.romanText import clercqTemperley
import copy
import unittest

def generateContrapuntalBassLine(harmonyObject, fbRules):
    '''
    harmonyObject can be either harmony.ChordSymbol or roman.RomanNumeral
    TODO: unify approach to harmony and chordsymbols vs. roman numerals
    
    returns a bass line with correct voice-leading according to common practice
    rules defined by fbRules. Utilizes fbRealizer to generate correct voice-leading,
    but depends on the harmonyObject for pitches
    
    fbRealizer wasn't designed to deal with 9th/11th/13th chords
    TODO: accommodate 9th/11th/13th chords
    '''
    fbLine = realizer.FiguredBassLine()
    
    for o in harmonyObject:
        fbLine.addElement(o)

    allSols = fbLine.realize(fbRules)
    #print allSols.getNumSolutions()
    return allSols.generateRandomRealizations(1)

def generateSmoothBassLine(harmonyObjects):
    '''
    accepts a list of harmony.chordSymbol objects and returns that same list
    with a computer generated octave assigned to each bass note.
    The algorithm is under development, but currently works like this:
    
    1. assigns octave of 2 to the first bass note
    2. iterates through each of the following bass notes corresponding to the chordSymbol
        i. creates three generic intervals between the previous bass note 
        and the current bass note, all using the previous bass note's newly defined
        octave and one of three current bass note octaves:
            1. the last bass note's octave    2. the last bass note's octave + 1    3. the last bass note's octave - 1
        ii. evaluates the size of each of the three intervals above (using interval.generic.undirected)
        and finds the smallest size
        v. assigns the bass note octave that yields this smallest interval to the current bass note
            - if the newly found octave is determined to be greater than 3 or less than 1, the
        bass note octave is assigned to the last bass note's octave
        iv. updates the previous bass note, and the iteration continues
    3. returns list of chordSymbols, with computer generated octaves assigned
    '''
    s = stream.Score()
    s.append(clef.BassClef())
    harmonyObjects[0].bass().octave = 2
    lastBass = harmonyObjects[0].bass()
    s.append(note.Note(lastBass))
    for cs in harmonyObjects[1:]:
        cs.bass().octave = lastBass.octave
        sameOctave = interval.Interval(lastBass, copy.deepcopy(cs.bass()))
        cs.bass().octave += 1
        octavePlus = interval.Interval(lastBass, copy.deepcopy(cs.bass()))
        cs.bass().octave = cs.bass().octave - 2
        octaveMinus = interval.Interval(lastBass, copy.deepcopy(cs.bass()))
        l = [sameOctave, octavePlus, octaveMinus]
        minimum = sameOctave.generic.undirected
        ret = sameOctave
        for i in l:
            if i.generic.undirected < minimum:
                minimum = i.generic.undirected
                ret = i
        
        if ret.noteEnd.octave > 3 or ret.noteEnd.octave < 1:
            ret.noteEnd.octave = lastBass.octave
        cs.bass().octave = ret.noteEnd.octave
        lastBass = cs.bass()
        s.append(note.Note(cs.bass()))
    return harmonyObjects

def generateBaroqueRules():
    fbRules = rules.Rules()
    return fbRules

def generatePopSongRules():
    '''
    generation of rules for using fbRealizer to realize a lead sheet of chord symbols
    or roman numerals. Currently all attributes are default except for the special resolution
    rules which are turned off. Default value is left as a comment to the right of each line
    '''
    fbRules = rules.Rules()
    
    #Single Possibility rules
    fbRules.forbidIncompletePossibilities = True #True
    fbRules.upperPartsMaxSemitoneSeparation = 12    #12
    fbRules.forbidVoiceCrossing = True      #True
    
    #Consecutive Possibility rules
    fbRules.forbidParallelFifths = True #True
    fbRules.forbidParallelOctaves = True #True
    fbRules.forbidHiddenFifths = True #True
    fbRules.forbidHiddenOctaves = True #True
    fbRules.forbidVoiceOverlap = True #True
    fbRules.partMovementLimits = [] #[]

    #Special resolution rules
    fbRules.resolveDominantSeventhProperly = False #True
    fbRules.resolveDiminishedSeventhProperly = False #True
    fbRules.resolveAugmentedSixthProperly = False #True
    fbRules.doubledRootInDim7 = False #False
    fbRules.applySinglePossibRulesToResolution = False #False
    fbRules.applyConsecutivePossibRulesToResolution = False #False
    fbRules.restrictDoublingsInItalianA6Resolution = True #True
    
    fbRules._upperPartsRemainSame = False        #False
    
    fbRules.partMovementLimits.append((1,5))
    
    return fbRules

def mergeLeadSheetAndBassLine(leadsheet, bassLine):
    '''
    method to combine the lead sheet with just the melody line
    and chord symbols with the newly realized bassLine (i.e. from fbRealizer) which 
    consists of two parts, the treble line and bass line.
    '''
    s = stream.Score()
    
    s.insert(metadata.Metadata()) 
    s.metadata.title = leadsheet.metadata.title
    cs = leadsheet.flat.getElementsByClass(harmony.ChordSymbol)
    if cs[0].offset > 0:
        bassLine.parts[0].insertAndShift(0, note.Rest(quarterLength=cs[0].offset))
        bassLine.parts[1].insertAndShift(0, note.Rest(quarterLength=cs[0].offset))
    voicePart = leadsheet.parts[0]
    pianoTreble = bassLine.parts[0]
    pianoBass = bassLine.parts[1]
    s.insert(0, voicePart)
    s.insert(0, pianoTreble)
    s.insert(0, pianoBass)

    return s
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
           
class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def realizeclercqTemperleyEx(self, testfile):  
        '''
        Example realization  (using fbRealizer - romanNumerals flavor) of any clercqTemperley file.
        testfile must conform to the requirements of a class clercgTemperley file (must be a string)
        '''
        s = clercqTemperley.CTSong(testfile)
    
        testFile1 = s.toScore()
        testFile = harmony.realizeChordSymbolDurations(testFile1)
        smoothBassRN = generateSmoothBassLine(testFile.flat.getElementsByClass(roman.RomanNumeral))
    
        output = generateContrapuntalBassLine(smoothBassRN, generateBaroqueRules())
        output.insert(metadata.Metadata()) 
        output.metadata.title = s.title
        output.show()
    
    def testLeadsheetEx1(self):
        '''
        Example realization of a lead sheet, "Jeanie With The Light Brown Hair" from music21 corpus
        
        '''
        testFile1 = corpus.parse('leadSheet/fosterBrownHair.xml')
        testFile1.insert(metadata.Metadata()) 
        testFile1.metadata.title = 'Jeanie With The Light Brown Hair'
        testFile = harmony.realizeChordSymbolDurations(testFile1)
        smoothBassCS = generateSmoothBassLine(testFile.flat.getElementsByClass(harmony.ChordSymbol))
    
        output = generateContrapuntalBassLine(smoothBassCS, generatePopSongRules())
        mergeLeadSheetAndBassLine(testFile1, output).show()

    def testRealizeLeadsheet(self, music21Stream):
        '''
        Example realization (using fbRealizer - chordSymbols flavor) of any leadsheet 
        converted to a music21Stream
        
        '''
        testFile = harmony.realizeChordSymbolDurations(music21Stream)
        smoothBassCS = generateSmoothBassLine(testFile.flat.getElementsByClass(harmony.ChordSymbol))
        output = generateContrapuntalBassLine(smoothBassCS, generatePopSongRules())
        mergeLeadSheetAndBassLine(music21Stream, output).show()
    
            
if __name__ == "__main__":
    from music21 import base
    base.mainTest(Test, TestExternal)
    
    #from music21 import corpus
    #from music21.demos.bhadley import HarmonyRealizer
    #test = HarmonyRealizer.TestExternal()

    #test.leadsheetEx1()
    #sc = converter.parse('https://github.com/cuthbertLab/music21/raw/master/music21/corpus/leadSheet/fosterBrownHair.mxl') # Jeannie Light Brown Hair
    


    testfile1 = '''
% Dylan - Blowin' in the Wind
VP: I IV | V I |
In: I |
Vr: $VP I IV | I | $VP I IV | V | $VP I IV | I | IV V | I IV | IV V | [2/4] I | [4/4] IV V | I IV | IV V | I |
S: [D] $In $Vr $Vr $Vr
'''
    #test.realizeclercqTemperleyEx(testfile1)
    
    testfile2 = '''
% Brown-Eyed Girl
A: I | IV | I | V |
In: $A*2
Vr: $A*4 IV | V | I | vi | IV | V | I | V |
Ext: V | |
Ch: $A*2
Brk: I |*4 $A

S: [G] $In $Vr*2 $Ext $Ch $Brk $Vr $Ext $Ch $A
'''
    #test.realizeclercqTemperleyEx(testfile2)
    


