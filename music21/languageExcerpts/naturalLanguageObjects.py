# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         naturalLanguageObjects.py
# Purpose:      Multi-lingual conversion of pitch, etc. objects
# Authors:      David Perez
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
r'''
Module docs...
'''

import unittest
from music21 import pitch

SUPPORTED_LANGUAGES = ["de","fr","it","du","es"]
SUPPORTED_ACCIDENTALS = ["----","---","--","-","","#","##","###","####"]
SUPPORTED_MICROTONES = ["A","B","C","D","E","F","G"]

def generateLanguageDictionary(languageString):
    
    #Helper method for toPitch
    
    #Generates a dictionary that allows the conversion of pitches from any language supported,
    #consistent with the standards set by pitch.py
    
    if languageString not in SUPPORTED_LANGUAGES:
        return {}
    
    dictionary = {}
    pitchStrings = []
    
    for microtone in SUPPORTED_MICROTONES:
        for accidental in SUPPORTED_ACCIDENTALS:
            pitchStrings.append(microtone + accidental)
    
    if languageString is "de":
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p._getGerman()] = pitchString
    elif languageString is "fr":
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p._getFrench()] = pitchString
    elif languageString is "it":
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p._getItalian()] = pitchString
    elif languageString is "du":
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p._getDutch()] = pitchString
    elif languageString is "es":
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p._getSpanish()] = pitchString
    
    return dictionary

def toPitch(pitchString, languageString):
    '''
    Converts a string to a :class:`music21.pitch.Pitch` object given a language.
    
    Supported languages are Dutch, French, German, Italian, and Spanish
    
    Defaults to C natural
    
    >>> languageExcerpts.naturalLanguageObjects.toPitch("Es", "de")
    <music21.pitch.Pitch E->
    
    >>> languageExcerpts.naturalLanguageObjects.toPitch("H", "de")
    <music21.pitch.Pitch B>
    >>> for i in ['As','A','Ais']:
    ...     print(languageExcerpts.naturalLanguageObjects.toPitch(i, "de"))
    A-
    A
    A#
    '''    
    
    defaultPitch = pitch.Pitch("C")
    
    langDict = generateLanguageDictionary(languageString)
    if pitchString not in langDict:
        return defaultPitch
    return pitch.Pitch(langDict[pitchString])

def toNote(pitchString, languageString):
    '''
    Converts a string to a :class:`music21.note.Note` object given a language
    
    Supported languages are Dutch, French, German, Italian, and Spanish
    
    Defaults to C Naturual
    
    >>> languageExcerpts.naturalLanguageObjects.toNote("Es", "de")
    <music21.note.Note E->
    
    >>> languageExcerpts.naturalLanguageObjects.toNote("H", "de")
    <music21.note.Note B>
    >>> for i in ['As','A','Ais']:
    ...     print(languageExcerpts.naturalLanguageObjects.toNote(i, "de"))
    <music21.note.Note A->
    <music21.note.Note A>
    <music21.note.Note A#>
    '''
    
    from music21 import note
    
    return note.Note(toPitch(pitchString, languageString))
    
def toChord(pitchArray, languageString):
    '''
    Converts a list of strings to a :class:`music21.chord.Chord` object given a language
    
    Supported languages are Dutch, French, German, Italian, and Spanish
    
    Unsupported strings default to pitch C Naturual
    
    >>> languageExcerpts.naturalLanguageObjects.toChord(["Es","E","Eis"], "de")
    <music21.chord.Chord E- E E#>
    '''
    
    from music21 import chord
    
    noteList = [toNote(pitchObj, languageString) for pitchObj in pitchArray]
    return chord.Chord(noteList)

def toDuration():
    
    '''
    TODO: Everything
    '''
    
    pass
#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testConvertPitches(self):
        #testing defaults in case of invalid language and invalid input    
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","hello").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","hello").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","").__repr__())
        
        #testing defaults in case of invalid language and valid input    
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("Eis","hello").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("Eis","").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("H","hello").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("H","").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("Sol","hello").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("Sol","").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("Re","hello").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("Re","").__repr__())
        
        #testing defaults in case of invalid input string and valid language    
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","de").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","de").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","fr").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","fr").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","es").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","es").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","du").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","du").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("hello","it").__repr__())
        self.assertEqual("<music21.pitch.Pitch C>", toPitch("","it").__repr__())
        
        #testing defaults in case of valid input string and valid language    
        self.assertEqual("<music21.pitch.Pitch C##>", toPitch("do doppio diesis","it").__repr__())
        self.assertEqual("<music21.pitch.Pitch F##>", toPitch("fa doble sostenido","es").__repr__())
        self.assertEqual("<music21.pitch.Pitch G--->", toPitch("sol triple bèmol","es").__repr__())
        self.assertEqual("<music21.pitch.Pitch D>", toPitch("re","it").__repr__())
        self.assertEqual("<music21.pitch.Pitch B-->", toPitch("Heses","de").__repr__())
        self.assertEqual("<music21.pitch.Pitch E##>", toPitch("Eisis","de").__repr__())
        self.assertEqual("<music21.pitch.Pitch D-->", toPitch("Deses","du").__repr__())
        self.assertEqual("<music21.pitch.Pitch B->", toPitch("Bes","du").__repr__())
        self.assertEqual("<music21.pitch.Pitch A####>", toPitch("la quadruple dièse","fr").__repr__())
        self.assertEqual("<music21.pitch.Pitch B--->", toPitch("si triple bémol","fr").__repr__())
        pass


    def testConvertNotes(self):
        #testing defaults in case of invalid language and invalid input    
        self.assertEqual("<music21.note.Note C>", toNote("hello","").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","hello").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("hello","hello").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","").__repr__())
        
        #testing defaults in case of invalid language and valid input    
        self.assertEqual("<music21.note.Note C>", toNote("Eis","hello").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("Eis","").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("H","hello").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("H","").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("Sol","hello").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("Sol","").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("Re","hello").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("Re","").__repr__())
        
        #testing defaults in case of invalid input string and valid language    
        self.assertEqual("<music21.note.Note C>", toNote("hello","de").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","de").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("hello","fr").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","fr").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("hello","es").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","es").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("hello","du").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","du").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("hello","it").__repr__())
        self.assertEqual("<music21.note.Note C>", toNote("","it").__repr__())
        
        #testing defaults in case of valid input string and valid language    
        self.assertEqual("<music21.note.Note C##>", toNote("do doppio diesis","it").__repr__())
        self.assertEqual("<music21.note.Note F##>", toNote("fa doble sostenido","es").__repr__())
        self.assertEqual("<music21.note.Note G--->", toNote("sol triple bèmol","es").__repr__())
        self.assertEqual("<music21.note.Note D>", toNote("re","it").__repr__())
        self.assertEqual("<music21.note.Note B-->", toNote("Heses","de").__repr__())
        self.assertEqual("<music21.note.Note E##>", toNote("Eisis","de").__repr__())
        self.assertEqual("<music21.note.Note D-->", toNote("Deses","du").__repr__())
        self.assertEqual("<music21.note.Note B->", toNote("Bes","du").__repr__())
        self.assertEqual("<music21.note.Note A####>", toNote("la quadruple dièse","fr").__repr__())
        self.assertEqual("<music21.note.Note B--->", toNote("si triple bémol","fr").__repr__())
        
    def testConvertChords(self):
        #testing defaults in case of invalid language and no input    
        self.assertEqual("<music21.chord.Chord >", toChord([],"").__repr__())
        self.assertEqual("<music21.chord.Chord >", toChord([],"hello").__repr__())
                
        #testing defaults in case of valid language and no input
        self.assertEqual("<music21.chord.Chord >", toChord([],"de").__repr__())
        self.assertEqual("<music21.chord.Chord >", toChord([],"fr").__repr__())
        self.assertEqual("<music21.chord.Chord >", toChord([],"es").__repr__())
        self.assertEqual("<music21.chord.Chord >", toChord([],"du").__repr__())
        self.assertEqual("<music21.chord.Chord >", toChord([],"it").__repr__())
        
        #testing defaults in case of invalid language and valid list    
        self.assertEqual("<music21.chord.Chord C>", toChord(["Eis"],"hello").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["Eis"],"").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["H"],"hello").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["H"],"").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["Sol"],"hello").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["Sol"],"").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["Re"],"hello").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["Re"],"").__repr__())
        
        #testing defaults in case of invalid input list and valid language    
        self.assertEqual("<music21.chord.Chord C>", toChord(["hello"],"de").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord([""],"de").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["hello"],"fr").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord([""],"fr").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["hello"],"es").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord([""],"es").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["hello"],"du").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord([""],"du").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord(["hello"],"it").__repr__())
        self.assertEqual("<music21.chord.Chord C>", toChord([""],"it").__repr__())
        
        #testing defaults in case of valid input list and valid language    
        self.assertEqual("<music21.chord.Chord C##>", toChord(["do doppio diesis"],"it").__repr__())
        self.assertEqual("<music21.chord.Chord F##>", toChord(["fa doble sostenido"],"es").__repr__())
        self.assertEqual("<music21.chord.Chord G--->", toChord(["sol triple bèmol"],"es").__repr__())
        self.assertEqual("<music21.chord.Chord D>", toChord(["re"],"it").__repr__())
        self.assertEqual("<music21.chord.Chord B-->", toChord(["Heses"],"de").__repr__())
        self.assertEqual("<music21.chord.Chord E##>", toChord(["Eisis"],"de").__repr__())
        self.assertEqual("<music21.chord.Chord D-->", toChord(["Deses"],"du").__repr__())
        self.assertEqual("<music21.chord.Chord B->", toChord(["Bes"],"du").__repr__())
        self.assertEqual("<music21.chord.Chord A####>", toChord(["la quadruple dièse"],"fr").__repr__())
        self.assertEqual("<music21.chord.Chord B--->", toChord(["si triple bémol"],"fr").__repr__())    
        
        self.assertEqual("<music21.chord.Chord C## D>", toChord(["do doppio diesis","re"],"it").__repr__())
        self.assertEqual("<music21.chord.Chord F## G--->", toChord(["fa doble sostenido","sol triple bèmol"],"es").__repr__())
        self.assertEqual("<music21.chord.Chord B-- E##>", toChord(["Heses","Eisis"],"de").__repr__())
        self.assertEqual("<music21.chord.Chord D-- B->", toChord(["Deses","Bes"],"du").__repr__())
        self.assertEqual("<music21.chord.Chord A#### B--->", toChord(["la quadruple dièse","si triple bémol"],"fr").__repr__())
        pass
#------------------------------------------------------------------------------
# define presented order in documentation


_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
