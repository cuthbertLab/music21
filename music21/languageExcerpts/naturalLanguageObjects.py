# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         naturalLanguageObjects.py
# Purpose:      Multi-lingual conversion of pitch, etc. objects
# Authors:      David Perez
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014, 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Multi-lingual conversion of pitch, etc. objects
'''

import unittest
from music21 import pitch

SUPPORTED_LANGUAGES = ['de', 'fr', 'it', 'es']
SUPPORTED_ACCIDENTALS = ['----', '---', '--', '-', '', '#', '##', '###', '####']
SUPPORTED_MICROTONES = ['A', 'B', 'C', 'D', 'E', 'F', 'G']


def generateLanguageDictionary(languageString):

    # Helper method for toPitch

    # Generates a dictionary that allows the conversion of pitches from any language supported,
    # consistent with the standards set by pitch.py

    if languageString not in SUPPORTED_LANGUAGES:
        return {}

    dictionary = {}
    pitchStrings = []

    for microtone in SUPPORTED_MICROTONES:
        for accidental in SUPPORTED_ACCIDENTALS:
            pitchStrings.append(microtone + accidental)

    if languageString == 'de':
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p.german] = pitchString
    elif languageString == 'fr':
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p.french] = pitchString
    elif languageString == 'it':
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p.italian] = pitchString
    elif languageString == 'es':
        for pitchString in pitchStrings:
            p = pitch.Pitch(pitchString)
            dictionary[p.spanish] = pitchString

    return dictionary


def toPitch(pitchString, languageString):
    '''
    Converts a string to a :class:`music21.pitch.Pitch` object given a language.

    Supported languages are French, German, Italian, and Spanish

    Defaults to C natural

    >>> languageExcerpts.naturalLanguageObjects.toPitch('Es', 'de')
    <music21.pitch.Pitch E->

    >>> languageExcerpts.naturalLanguageObjects.toPitch('H', 'de')
    <music21.pitch.Pitch B>
    >>> for i in ['As', 'A', 'Ais']:
    ...     print(languageExcerpts.naturalLanguageObjects.toPitch(i, 'de'))
    A-
    A
    A#
    '''
    langDict = generateLanguageDictionary(languageString)
    if pitchString not in langDict:
        return pitch.Pitch('C')

    return pitch.Pitch(langDict[pitchString])


def toNote(pitchString, languageString):
    '''
    Converts a string to a :class:`music21.note.Note` object given a language

    Supported languages are French, German, Italian, and Spanish

    Defaults to C Natural

    >>> languageExcerpts.naturalLanguageObjects.toNote('Es', 'de')
    <music21.note.Note E->

    >>> languageExcerpts.naturalLanguageObjects.toNote('H', 'de')
    <music21.note.Note B>
    >>> for i in ['As', 'A', 'Ais']:
    ...     print(languageExcerpts.naturalLanguageObjects.toNote(i, 'de'))
    <music21.note.Note A->
    <music21.note.Note A>
    <music21.note.Note A#>
    '''

    from music21 import note

    return note.Note(toPitch(pitchString, languageString))


def toChord(pitchArray, languageString):
    '''
    Converts a list of strings to a :class:`music21.chord.Chord` object given a language

    Supported languages are French, German, Italian, and Spanish

    Unsupported strings default to pitch C Natural

    >>> languageExcerpts.naturalLanguageObjects.toChord(['Es', 'E', 'Eis'], 'de')
    <music21.chord.Chord E- E E#>
    '''
    from music21 import chord

    noteList = [toNote(pitchObj, languageString) for pitchObj in pitchArray]
    return chord.Chord(noteList)

# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testConvertPitches(self):
        # testing defaults in case of invalid language and invalid input
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('hello', '')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('', 'hello')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('hello', 'hello')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('', '')))

        # testing defaults in case of invalid language and valid input
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('Eis', 'hello')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('Eis', '')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('H', 'hello')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('H', '')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('Sol', 'hello')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('Sol', '')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('Re', 'hello')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('Re', '')))

        # testing defaults in case of invalid input string and valid language
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('hello', 'de')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('', 'de')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('hello', 'fr')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('', 'fr')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('hello', 'es')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('', 'es')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('hello', 'it')))
        self.assertEqual('<music21.pitch.Pitch C>', repr(toPitch('', 'it')))

        # testing defaults in case of valid input string and valid language
        self.assertEqual('<music21.pitch.Pitch C##>', repr(toPitch('do doppio diesis',
                                                                   'it')))
        self.assertEqual('<music21.pitch.Pitch F##>', repr(toPitch('fa doble sostenido',
                                                                   'es')))
        self.assertEqual('<music21.pitch.Pitch G--->', repr(toPitch('sol triple bèmol',
                                                                    'es')))
        self.assertEqual('<music21.pitch.Pitch D>', repr(toPitch('re', 'it')))
        self.assertEqual('<music21.pitch.Pitch B-->', repr(toPitch('Heses', 'de')))
        self.assertEqual('<music21.pitch.Pitch E##>', repr(toPitch('Eisis', 'de')))
        self.assertEqual('<music21.pitch.Pitch A####>',
                         repr(toPitch('la quadruple dièse', 'fr')))
        self.assertEqual('<music21.pitch.Pitch B--->', repr(toPitch('si triple bémol', 'fr')))

    def testConvertNotes(self):
        # testing defaults in case of invalid language and invalid input
        self.assertEqual('<music21.note.Note C>', repr(toNote('hello', '')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('', 'hello')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('hello', 'hello')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('', '')))

        # testing defaults in case of invalid language and valid input
        self.assertEqual('<music21.note.Note C>', repr(toNote('Eis', 'hello')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('Eis', '')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('H', 'hello')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('H', '')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('Sol', 'hello')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('Sol', '')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('Re', 'hello')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('Re', '')))

        # testing defaults in case of invalid input string and valid language
        self.assertEqual('<music21.note.Note C>', repr(toNote('hello', 'de')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('', 'de')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('hello', 'fr')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('', 'fr')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('hello', 'es')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('', 'es')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('hello', 'it')))
        self.assertEqual('<music21.note.Note C>', repr(toNote('', 'it')))

        # testing defaults in case of valid input string and valid language
        self.assertEqual('<music21.note.Note C##>', repr(toNote('do doppio diesis', 'it')))
        self.assertEqual('<music21.note.Note F##>', repr(toNote('fa doble sostenido', 'es')))
        self.assertEqual('<music21.note.Note G--->', repr(toNote('sol triple bèmol', 'es')))
        self.assertEqual('<music21.note.Note D>', repr(toNote('re', 'it')))
        self.assertEqual('<music21.note.Note B-->', repr(toNote('Heses', 'de')))
        self.assertEqual('<music21.note.Note E##>', repr(toNote('Eisis', 'de')))
        self.assertEqual('<music21.note.Note A####>',
                            repr(toNote('la quadruple dièse', 'fr')))
        self.assertEqual('<music21.note.Note B--->', repr(toNote('si triple bémol', 'fr')))

    def testConvertChords(self):
        # testing defaults in case of invalid language and no input
        self.assertEqual((), toChord([], '').pitches)
        self.assertEqual((), toChord([], 'hello').pitches)

        # testing defaults in case of valid language and no input
        self.assertEqual((), toChord([], 'de').pitches)
        self.assertEqual((), toChord([], 'fr').pitches)
        self.assertEqual((), toChord([], 'es').pitches)
        self.assertEqual((), toChord([], 'it').pitches)

        # testing defaults in case of invalid language and valid list
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['Eis'], 'hello')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['Eis'], '')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['H'], 'hello')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['H'], '')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['Sol'], 'hello')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['Sol'], '')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['Re'], 'hello')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['Re'], '')))

        # testing defaults in case of invalid input list and valid language
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['hello'], 'de')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord([''], 'de')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['hello'], 'fr')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord([''], 'fr')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['hello'], 'es')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord([''], 'es')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord(['hello'], 'it')))
        self.assertEqual('<music21.chord.Chord C>', repr(toChord([''], 'it')))

        # testing defaults in case of valid input list and valid language
        self.assertEqual('<music21.chord.Chord C##>',
                         repr(toChord(['do doppio diesis'], 'it')))
        self.assertEqual('<music21.chord.Chord F##>',
                         repr(toChord(['fa doble sostenido'], 'es')))
        self.assertEqual('<music21.chord.Chord G--->',
                         repr(toChord(['sol triple bèmol'], 'es')))
        self.assertEqual('<music21.chord.Chord D>', repr(toChord(['re'], 'it')))
        self.assertEqual('<music21.chord.Chord B-->', repr(toChord(['Heses'], 'de')))
        self.assertEqual('<music21.chord.Chord E##>', repr(toChord(['Eisis'], 'de')))
        self.assertEqual('<music21.chord.Chord A####>',
                         repr(toChord(['la quadruple dièse'], 'fr')))
        self.assertEqual('<music21.chord.Chord B--->',
                         repr(toChord(['si triple bémol'], 'fr')))

        self.assertEqual('<music21.chord.Chord C## D>',
                         repr(toChord(['do doppio diesis', 're'], 'it')))
        self.assertEqual('<music21.chord.Chord F## G--->',
                         repr(toChord(['fa doble sostenido', 'sol triple bèmol'], 'es')))
        self.assertEqual('<music21.chord.Chord B-- E##>',
                         repr(toChord(['Heses', 'Eisis'], 'de')))
        self.assertEqual('<music21.chord.Chord A#### B--->',
                         repr(toChord(['la quadruple dièse', 'si triple bémol'], 'fr')))

# -----------------------------------------------------------------------------
# define presented order in documentation


_DOC_ORDER = []


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
