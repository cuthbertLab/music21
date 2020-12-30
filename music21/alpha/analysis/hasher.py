# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         alpha/analysis/hasher.py
# Purpose:      Hash musical notation
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest

import collections
import difflib

from music21 import note, chord, key
from music21 import interval
from music21 import stream


class Hasher:
    '''
    This is a modular hashing object that can hash notes, chords, and rests, and some of their
    properties. Steps to using and calling the hasher:

    1) Initialize a hasher object

    2) Set the properties that you want to hash. There are 4 main groups of properties/settings::

        a) self.validTypes should be some combination of notes, chords, rests

        b) general hashing settings include self.includeReference. if
           self.includeReference is True, a reference to to original note/rest/chord is created
           and kept track of during the hashing process.

        c) note properties are things like pitch, duration, offset, and some slightly fancier
           properties

        d) self.stateVars is a dictionary of things you might want to hash that require some memory
           e.g. current key signature, interval from the last note

    3) call the hashStream() function on the stream you want to hash.

    This is what the Hasher object does the in background once hashStream() is called:

    1) It runs self.setupValidTypesAndStateVars() and sets up properties from (a) and (d) from
    above based on your settings

    2) It runs self.preprocessStream() and based on settings from (d)

    3) It determines which objects in the passed-in stream should be hashed

    4) It runs self.setupTupleList() and sets up self.tupleList, self.hashingFunctions
    and self.tupleClass, all related to each other. self.tupleList is a list of all the
    properties that are hashed. self.hashingFunctions is a dictionary of which hashing function
    should be used for each property (there are multiple ways of hashing a note's pitch, for
    example, by MIDI number, or by a string representation). self.tupleClass is a NamedTuple
    that is constructed ad hoc based on which properties are to be hashed.

    5) For all the elements from the stream that are to be hashed, the hasher hashes every one of
    its properties that are to be hashed using the hashing function listed in
    self.hashingFunctions. It creates a single NamedTuple called a NoteHash for each element
    from the stream. However, if self.includeReference is set to True, a NoteHashWithReference
    tuple is created instead.
    '''

    def __init__(self):
        '''
        The Hasher object is initialized with defaults of what objects should be hashed, and
        what properties of those objects should be hashed.
        '''

        # --- begin general types of things to hash ---
        self.validTypes = [note.Note, note.Rest, chord.Chord]
        # --- end general types of things to hash ---

        # --- begin general hashing settings ---
        self.includeReference = False
        # --- end general hashing settings ---

        # --- begin note properties to hash ---
        self.hashPitch = True
        # hashMIDI = True => 58 instead of 'C--'
        self.hashMIDI = True
        # hashNoteNameOctave = False => 'C4' instead of 'C'
        self.hashNoteNameOctave = False
        self.hashOctave = False
        self.hashDuration = True
        self.roundDurationAndOffset = True
        self.hashOffset = True
        # self.roundOffset = True
        self.granularity = 32
        self.hashIntervalFromLastNote = False
        self.hashIsAccidental = False
        self.hashIsTied = False
        # --- end note properties to hash ---

        # --- begin chord properties to hash ---  #
        # chords can hashed as chords or by their note constituents
        self.hashChordsAsNotes = True
        self.hashChordsAsChords = False
        self.hashNormalOrderString = False
        self.hashPrimeFormString = False
        # --- end chord properties to hash ---  #

        self.tupleList = []
        self.tupleClass = None
        # stateVars are variables that are kept track of through multiple hashes
        # e.g. interval from the previous note, key signature
        self.stateVars = {}
        self.hashingFunctions = {}

    def setupValidTypesAndStateVars(self):
        '''
        Sets up the self.stateVars dictionary depending on how the flags for
        self.hashIntervalFromLastNote and self.hashIsAccidental are set.

        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.hashIntervalFromLastNote = True
        >>> h.setupValidTypesAndStateVars()
        >>> h.stateVars
        {'IntervalFromLastNote': None}

        >>> h2 = alpha.analysis.hasher.Hasher()
        >>> h2.hashIsAccidental = True
        >>> h2.setupValidTypesAndStateVars()
        >>> h2.stateVars
        {'KeySignature': None}

        >>> key.KeySignature in h2.validTypes
        True
        '''
        if self.hashIntervalFromLastNote:
            self.stateVars['IntervalFromLastNote'] = None

        if self.hashIsAccidental:
            self.validTypes.append(key.KeySignature)
            self.stateVars['KeySignature'] = None

        # -- Begin Individual Hashing Functions of Properties---
    def _hashDuration(self, e, thisChord=None):
        '''
        returns the duration of a chord object passed in, otherwise the duration of a note
        object passed in.

        >>> h = alpha.analysis.hasher.Hasher()
        >>> n = note.Note('A-', quarterLength=2.5)
        >>> h._hashDuration(n)
        2.5

        >>> d = duration.Duration(2.0)
        >>> c = chord.Chord('A-4 C#5 E5', duration=d)
        >>> h._hashDuration(n, thisChord=c)
        2.0
        '''
        if thisChord:
            return thisChord.duration.quarterLength
        return e.duration.quarterLength

    def _hashRoundedDuration(self, e, thisChord=None):
        '''
        TODO: Check if this is working
        '''
        if thisChord:
            return self._getApproxDurOrOffset(float(thisChord.duration.quarterLength))
        e.duration.quarterLength = self._getApproxDurOrOffset(float(e.duration.quarterLength))
        return e.duration.quarterLength

    def _hashMIDIPitchName(self, e, thisChord=None):
        '''
        returns midi pitch value (21-108) of a note
        returns 0 if rest
        returns 1 if not hashing individual notes of a chord

        >>> n = note.Note(72)
        >>> c = chord.Chord('A-4 C#5 E5')
        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.hashChordsAsChords = True
        >>> h._hashMIDIPitchName(n, thisChord=c)
        1
        >>> h.hashChordsAsChords = False
        >>> h._hashMIDIPitchName(n, thisChord=c)
        72
        >>> r = note.Rest()
        >>> h._hashMIDIPitchName(r, thisChord=c)
        0

        '''
        if thisChord and self.hashChordsAsChords:
            return 1
        elif isinstance(e, note.Rest):
            return 0
        return e.pitch.midi

    def _hashPitchName(self, e, thisChord=None):
        '''
        returns string representation of a note e.g. 'F##4'
        returns 'r' if rest
        returns 'z' if not hashing individual notes of a chord (i.e. hashing chords as chords)

        >>> n = note.Note(72)
        >>> c = chord.Chord('A-4 C#5 E5')
        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.hashChordsAsChords = True
        >>> h._hashPitchName(n, thisChord=c)
        'z'
        >>> h.hashChordsAsChords = False
        >>> h._hashPitchName(n, thisChord=c)
        'C5'
        >>> r = note.Rest()
        >>> h._hashPitchName(r, thisChord=c)
        'r'
        '''
        if thisChord and self.hashChordsAsChords:
            return 'z'
        elif isinstance(e, note.Rest):
            return 'r'
        return str(e.pitch)

    def _hashPitchNameNoOctave(self, e, thisChord=None):
        '''
        returns string representation of a note without the octave e.g. 'F##'
        returns 'r' if rest
        returns 'z' if not hashing individual notes of a chord

        >>> n = note.Note(72)
        >>> c = chord.Chord('A-4 C#5 E5')
        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.hashChordsAsChords = True
        >>> h._hashPitchNameNoOctave(n, thisChord=c)
        'z'
        >>> h.hashChordsAsChords = False
        >>> h._hashPitchNameNoOctave(n, thisChord=c)
        'C'
        >>> r = note.Rest()
        >>> h._hashPitchNameNoOctave(r, thisChord=c)
        'r'
        '''
        if thisChord and self.hashChordsAsChords:
            return 'z'
        elif isinstance(e, note.Rest):
            return 'r'
        return str(e.pitch)[:-1]

    def _hashOctave(self, e, thisChord=None):
        '''
        returns octave number of a note
        returns -1 if rest or not hashing individual notes of a chord

        >>> n = note.Note(72)
        >>> c = chord.Chord('A-4 C#5 E5')
        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.hashChordsAsChords = True
        >>> h._hashOctave(c, thisChord=c)
        -1
        >>> h.hashChordsAsChords = False
        >>> h._hashOctave(n, thisChord=c)
        5
        >>> r = note.Rest()
        >>> h._hashOctave(r, thisChord=c)
        -1
        '''
        if isinstance(e, chord.Chord) and self.hashChordsAsChords:
            return -1
        elif isinstance(e, note.Rest):
            return -1
        return e.octave

    def _hashIsAccidental(self, e, thisChord=None):
        # TODO: figure out how to tell if note is accidental based on key sig
        pass

    def _hashRoundedOffset(self, e, thisChord=None):
        '''
        returns offset rounded to the nearest subdivided beat
        subdivided beat is indicated with self.granularity
        by default, the granularity is set to 32, or 32nd notes
        '''
        if thisChord:
            return self._getApproxDurOrOffset(thisChord.offset)
        e.offset = self._getApproxDurOrOffset(e.offset)
        return e.offset

    def _hashOffset(self, e, thisChord=None):
        '''
        returns unrounded floating point representation of a note's offset
        '''
        if thisChord:
            return thisChord.offset
        return e.offset

    def _hashIntervalFromLastNote(self, e, thisChord=None):
        '''
        returns the interval between last note and current note, if extant
        known issues with first note of every measure in transposed pieces
        returns 0 if things don't work
        '''
        try:
            if (isinstance(e, note.Note)
                    and e.previous('Note') is not None):
                previousNote = e.previous('Note')
                if previousNote is None:
                    return 0
                intFromLastNote = interval.Interval(noteStart=previousNote,
                                                    noteEnd=e).intervalClass
                return interval.convertGeneric(interval.Interval(intFromLastNote).intervalClass)
        except TypeError:
            return 0

    def _hashPrimeFormString(self, e, thisChord=None):
        '''
        returns prime form of a chord as a string e.g. '<037>'
        returns '<>' otherwise
        '''
        if thisChord:
            return thisChord.primeFormString
        return '<>'

    def _hashChordNormalOrderString(self, e, thisChord=None):
        '''
        returns normal order of a chord as a string e.g. '<047>'
        returns '<>' otherwise
        '''
        if thisChord:
            return thisChord.formatVectorString(thisChord.normalOrder)
        return '<>'

    # --- End Individual Hashing Functions

    def setupTupleList(self):
        '''
        Sets up self.hashingFunctions, a dictionary of which properties of self.validTypes should
        be hashed and which hashing functions should be used for those properties. Creates a
        tupleList of all the properties that are hashed and uses that to create a named tuple
        NoteHash with those properties. This is how we can generate a malleable named tuple
        NoteHash that is different depending upon which properties a particular instance of
        Hasher object hashes.
        '''
        tupleList = []

        if self.hashPitch:
            tupleList.append('Pitch')
            if self.hashMIDI:
                self.hashingFunctions['Pitch'] = self._hashMIDIPitchName
            elif not self.hashMIDI and not self.hashNoteNameOctave:
                self.hashingFunctions['Pitch'] = self._hashPitchName
            elif not self.hashMIDI and self.hashNoteNameOctave:
                self.hashingFunctions['Pitch'] = self._hashPitchNameNoOctave

            if self.hashIsAccidental:
                tupleList.append('IsAccidental')
                self.hashingFunctions['IsAccidental'] = self._hashIsAccidental

        if self.hashOctave:
            tupleList.append('Octave')
            self.hashingFunctions['Octave'] = self._hashOctave

        if self.hashChordsAsNotes:
            pass
        elif self.hashChordsAsChords:
            if self.hashNormalOrderString:
                tupleList.append('NormalOrderString')
                self.hashingFunctions['NormalOrderString'] = self._hashChordNormalOrderString
            if self.hashPrimeFormString:
                tupleList.append('PrimeFormString')
                self.hashingFunctions['PrimeFormString'] = self._hashPrimeFormString

        if self.hashDuration:
            tupleList.append('Duration')
            if self.roundDurationAndOffset:
                self.hashingFunctions['Duration'] = self._hashRoundedDuration
            else:
                self.hashingFunctions['Duration'] = self._hashDuration

        if self.hashOffset:
            tupleList.append('Offset')
            if self.roundDurationAndOffset:
                self.hashingFunctions['Offset'] = self._hashRoundedOffset
            else:
                self.hashingFunctions['Offset'] = self._hashOffset

        if self.hashIntervalFromLastNote:
            tupleList.append('IntervalFromLastNote')
            self.hashingFunctions['IntervalFromLastNote'] = self._hashIntervalFromLastNote

        self.tupleList = tupleList
        self.tupleClass = collections.namedtuple('NoteHash', tupleList)

    def hashMeasures(self, s):
        '''
        lightweight hasher. only hashes number of notes, first and last pitch
        '''

    def hashStream(self, s):
        '''
        This method is the meat of the program. It goes through all the elements that are left
        to be hashed and individually hashes them by looking up which hashing functions ought
        to be used on each element and passing off the element to the method
        self.addSingleNoteHashToFinalHash, which creates the appropriate hash for that element
        and adds it to self.finalHash
        '''
        finalHash = []
        self.setupValidTypesAndStateVars()
        ss = s.recurse()
        tupValidTypes = tuple(self.validTypes)
        finalEltsToBeHashed = [elt for elt in ss if isinstance(elt, tupValidTypes)]
        self.setupTupleList()

        # TODO: see if can break for loop up into separate functions
        for elt in finalEltsToBeHashed:

            if self.hashIsAccidental and isinstance(elt, key.KeySignature):
                self.stateVars['currKeySig'] = elt
            elif isinstance(elt, chord.Chord):
                if self.hashChordsAsNotes:
                    for n in elt:
                        singleNoteHash = [self.hashingFunctions[hashProperty](n, thisChord=elt)
                                            for hashProperty in self.tupleList]

                        self.addHashToFinalHash(singleNoteHash, finalHash, n)
                elif self.hashChordsAsChords:
                    singleNoteHash = [self.hashingFunctions[hashProperty](None, thisChord=elt)
                                        for hashProperty in self.tupleList]
                    self.addHashToFinalHash(singleNoteHash, finalHash, elt)
            else:
                singleNoteHash = [self.hashingFunctions[hashProperty](elt)
                                    for hashProperty in self.tupleList]
                self.addHashToFinalHash(singleNoteHash, finalHash, elt)
        # TODO: don't finalHash back and forth, return it in the smaller functions
        return finalHash

    def addHashToFinalHash(self, singleNoteHash, finalHash, reference):
        tupleHash = (self.tupleClass._make(singleNoteHash))
        if self.includeReference:
            self.addNoteHashWithReferenceToFinalHash(finalHash, tupleHash, reference)
        else:
            self.addNoteHashToFinalHash(finalHash, tupleHash)

    def addNoteHashWithReferenceToFinalHash(self, finalHash, tupleHash, reference):
        '''
        creates a NoteHashWithReference object from tupleHash and with the reference pass in
        and adds the NoteHashWithReference object to the end of finalHash

        >>> from collections import namedtuple
        >>> n = note.Note('C4')
        >>> NoteHash = namedtuple('NoteHash', ['Pitch', 'Duration'])
        >>> nh = NoteHash(n.pitch, n.duration)
        >>> finalHash = []
        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.addNoteHashWithReferenceToFinalHash(finalHash, nh, n)
        >>> finalHash
        [NoteHashWithReference(Pitch=C4, Duration=<music21.duration.Duration 1.0>)]

        >>> finalHash[0].reference.id == n.id
        True
        '''
        nhwr = NoteHashWithReference(tupleHash)
        nhwr.reference = reference
        finalHash.append(nhwr)

    def addNoteHashToFinalHash(self, finalHash, tupleHash):
        '''
        creates a NoteHash object from tupleHash and adds the NoteHash
        object to the end of finalHash

        >>> from collections import namedtuple
        >>> n = note.Note('C4')
        >>> NoteHash = namedtuple('NoteHash', ['Pitch', 'Duration'])
        >>> nh = NoteHash(n.pitch, n.duration)
        >>> finalHash = []
        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.addNoteHashToFinalHash(finalHash, nh)
        >>> finalHash
        [(<music21.pitch.Pitch C4>, <music21.duration.Duration 1.0>)]
        '''
        nh = NoteHash(tupleHash)
        finalHash.append(nh)

#     def addSingleNoteHashToFinalHash(self, singleNoteHash, finalHash, reference=None):
#         # TODO: use the linter, reference DOESN'T have to be passed in
#         # what is reference? it's a hashable music21 elt, write documentation
#         tupleHash = (self.tupleClass._make(singleNoteHash))
#         if self.includeReference:
#             nhwr = NoteHashWithReference(tupleHash)
#             if reference.derivation.rootDerivation is not None:
#                 nhwr.reference = reference.derivation.rootDerivation
#             else:
#                 nhwr.reference = reference
#             finalHash.append(nhwr)
#         else:
#             nh = NoteHash(tupleHash)
#             finalHash.append(nh)

    # --- Begin Rounding Helper Functions ---

    def _getApproxDurOrOffset(self, durOrOffset):
        return round(durOrOffset * self.granularity) / self.granularity

    def _approximatelyEqual(self, a, b, sig_fig=4):
        '''
        use to look at whether beat lengths are close, within a certain range
        probably can use for other things that are approx. equal
        '''
        return a == b or int(a * 10 ** sig_fig) == int(b * 10 ** sig_fig)

    # --- End Rounding Helper Functions ---


class NoteHashWithReference:
    '''
    returns tuple with reference to original note or chord or rest

    >>> from collections import namedtuple
    >>> NoteHash = namedtuple('NoteHash', ['Pitch', 'Duration'])
    >>> nh = NoteHash(60, 4)
    >>> nhwr = alpha.analysis.hasher.NoteHashWithReference(nh)
    >>> nhwr.reference = note.Note('C4')
    >>> nhwr
    NoteHashWithReference(Pitch=60, Duration=4)

    >>> nhwr.Pitch
    60
    >>> nhwr.Duration
    4

    >>> nhwr.hashItemsKeys
    ('Pitch', 'Duration')

    >>> for val in nhwr:
    ...     print(val)
    60
    4

    >>> nhwr.reference
    <music21.note.Note C>
    '''

    def __init__(self, hashItemsNT):
        self.reference = None
        hashItemsDict = hashItemsNT._asdict()
        for x in hashItemsDict:
            setattr(self, x, hashItemsDict[x])
        self.hashItemsKeys = tuple(hashItemsDict.keys())

    def __iter__(self):
        for keyName in self.hashItemsKeys:
            yield(getattr(self, keyName))

    def __repr__(self):
        nhStrAll = 'NoteHashWithReference('

        vals = []
        for x in self.hashItemsKeys:
            nhStr = x
            nhStr += '='
            nhStr += str(getattr(self, x))
            vals.append(nhStr)
        nhStrAll += ', '.join(vals)
        nhStrAll += ')'
        return nhStrAll


class NoteHash(tuple):
    '''
    >>> note1 = note.Note('C4')
    >>> nh = alpha.analysis.hasher.NoteHash((1, 2))
    >>> nh
    (1, 2)
    >>> a, b = nh
    >>> a
    1
    >>> b
    2
    >>> nh.__class__
    <... 'music21.alpha.analysis.hasher.NoteHash'>
    '''
    def __new__(cls, tupEls):
        return super(NoteHash, cls).__new__(cls, tuple(tupEls))


class Test(unittest.TestCase):

    def _approximatelyEqual(self, a, b, sig_fig=2):
        '''
        use to look at whether beat lengths are close, within a certain range
        probably can use for other things that are approx. equal
        '''
        return (a == b or int(a * 10 ** sig_fig) == int(b * 10 ** sig_fig))

    def testBasicHash(self):
        '''
        test for hasher with basic settings: pitch, rounded duration, offset
        with notes, chord, and rest
        '''
        s1 = stream.Stream()
        note1 = note.Note('C4')
        note1.duration.type = 'half'
        note2 = note.Note('F#4')
        note3 = note.Note('B-2')
        cMinor = chord.Chord(['C4', 'G4', 'E-5'])
        cMinor.duration.type = 'half'
        r = note.Rest(quarterLength=1.5)
        s1.append(note1)
        s1.append(note2)
        s1.append(note3)
        s1.append(cMinor)
        s1.append(r)

        h = Hasher()

        hashes_plain_numbers = [(60, 2.0, 0.0), (66, 1.0, 2.0), (46, 1.0, 3.0), (60, 2.0, 4.0),
                                (67, 2.0, 4.0), (75, 2.0, 4.0), (0, 1.5, 6.0)]
        CNoteHash = collections.namedtuple('NoteHash', ['Pitch', 'Duration', 'Offset'])
        hashes_in_format = [CNoteHash(Pitch=x, Duration=y, Offset=z)
                            for (x, y, z) in hashes_plain_numbers]

        self.assertEqual(h.hashStream(s1), hashes_in_format)

    def testHashChordsAsChordsPrimeFormString(self):
        '''
        test to make sure that hashing works when trying to hash chord as chord
        '''
        s1 = stream.Stream()
        note1 = note.Note('C4')
        note1.duration.type = 'half'
        cMinor = chord.Chord(['C4', 'G4', 'E-5'])
        cMinor.duration.type = 'half'
        cMajor = chord.Chord(['C4', 'G4', 'E4'])
        cMajor.duration.type = 'whole'
        s1.append(note1)
        s1.append(cMinor)
        s1.append(cMajor)
        h = Hasher()
        h.hashChordsAsChords = True
        h.hashChordsAsNotes = False
        h.hashPrimeFormString = True
        CNoteHash = collections.namedtuple('NoteHash', ['Pitch', 'PrimeFormString',
                                                        'Duration', 'Offset'])
        hashes_plain_numbers = [(60, '<>', 2.0, 0.0), (1, '<037>', 2.0, 2.0),
                                (1, '<037>', 4.0, 4.0)]
        hashes_in_format = [CNoteHash(Pitch=x, PrimeFormString=y, Duration=z, Offset=a)
                            for (x, y, z, a) in hashes_plain_numbers]

        self.assertEqual(h.hashStream(s1), hashes_in_format)

    def testHashChordsAsChordsNormalOrder(self):
        s2 = stream.Stream()
        note1 = note.Note('C4')
        note1.duration.type = 'half'
        cMinor = chord.Chord(['C4', 'G4', 'E-5'])
        cMinor.duration.type = 'half'
        cMajor = chord.Chord(['C4', 'G4', 'E3'])
        cMajor.duration.type = 'whole'
        s2.append(note1)
        s2.append(cMinor)
        s2.append(cMajor)
        h = Hasher()
        h.hashChordsAsChords = True
        h.hashChordsAsNotes = False
        h.hashPrimeFormString = False
        h.hashNormalOrderString = True
        CNoteHash = collections.namedtuple('NoteHash', ['Pitch', 'NormalOrderString',
                                                        'Duration', 'Offset'])
        hashes_plain_numbers = [(60, '<>', 2.0, 0.0), (1, '<037>', 2.0, 2.0),
                                (1, '<047>', 4.0, 4.0)]
        hashes_in_format = [CNoteHash(Pitch=x, NormalOrderString=y, Duration=z, Offset=a)
                            for (x, y, z, a) in hashes_plain_numbers]
        self.assertEqual(h.hashStream(s2), hashes_in_format)

    def testHashUnroundedDuration(self):
        s3 = stream.Stream()
        note1 = note.Note('C4')
        note2 = note.Note('G4')
        cMinor = chord.Chord(['C4', 'G4'])
        note1.duration.quarterLength = 1.783
        note2.duration.quarterLength = 2 / 3
        cMinor.duration.type = 'half'
        s3.append(note1)
        s3.append(note2)
        s3.append(cMinor)
        h = Hasher()
        h.roundDurationAndOffset = False
        CNoteHash = collections.namedtuple('NoteHash', ['Pitch', 'Duration', 'Offset'])
        hashes_plain_numbers = [(60, 1.783, 0.0), (67, 2 / 3, 1.783), (60, 2.0, 1.783 + 2 / 3),
                                (67, 2.0, 1.783 + 2 / 3)]
        hashes_in_format = [CNoteHash(Pitch=x, Duration=z, Offset=a)
                            for (x, z, a) in hashes_plain_numbers]
        h3 = h.hashStream(s3)
        h3_floats = [h3[0][2], h3[1][2], h3[2][2], h3[3][2]]
        answers_floats = [hashes_in_format[0][2],
                          hashes_in_format[1][2],
                          hashes_in_format[2][2],
                          hashes_in_format[3][2]]
        assert all(self._approximatelyEqual(*values)
                   for values in zip(h3_floats, answers_floats))

    def testHashRoundedDuration(self):
        s3 = stream.Stream()
        note1 = note.Note('C4')
        note2 = note.Note('G4')
        cMinor = chord.Chord(['C4', 'G4'])
        note1.duration.quarterLength = 1.783
        note2.duration.quarterLength = 2 / 3
        cMinor.duration.type = 'half'
        s3.append(note1)
        s3.append(note2)
        s3.append(cMinor)
        h = Hasher()
        h.roundDurationAndOffset = True

        CNoteHash = collections.namedtuple('NoteHash', ['Pitch', 'Duration', 'Offset'])
        hashes_plain_numbers = [(60, 1.78125, 0.0), (67, 0.65625, 1.78125), (60, 2.0, 2.4375),
                                (67, 2.0, 2.4375)]
        hashes_in_format = [CNoteHash(Pitch=x, Duration=z, Offset=a)
                            for (x, z, a) in hashes_plain_numbers]
        h3 = h.hashStream(s3)
        self.assertEqual(h3, hashes_in_format)
        h.granularity = 8  # smallest length note is now 8th note
        new_hashes_in_format = [(60, 1.75, 0.0),
                                (67, 0.625, 1.75),
                                (60, 2.0, 2.5),
                                (67, 2.0, 2.5)]
        h4 = h.hashStream(s3)
        self.assertEqual(h4, new_hashes_in_format)

    def testReferences(self):
        s = stream.Stream()
        note1 = note.Note('C4')
        note2 = note.Note('G4')
        s.append([note1, note2])

        h = Hasher()
        h.includeReference = True
        hashes = h.hashStream(s)

        note1ref = hashes[0].reference
        note2ref = hashes[1].reference

        self.assertEqual(note1.id, note1ref.id)
        self.assertEqual(note2.id, note2ref.id)

    def testIntervals(self):
        s = stream.Stream()
        note1 = note.Note('E5')
        note2 = note.Note('D5')
        note3 = note.Note('A5')
        s.append([note1, note2, note3])
        h = Hasher()
        h.hashPitch = True
        h.hashDuration = False
        h.hashOffset = False
        h.hashIntervalFromLastNote = True
        unused_hashes = h.hashStream(s)


class TestExternal(unittest.TestCase):

    # def testBasicHash(self):
    #     # from pprint import pprint as pp
    #     from music21 import corpus
    #     s1 = corpus.parse('schoenberg', 6).parts[0]
    #     h = Hasher()
    #     # h.hashPitch = True
    #     # h.hashDuration = True
    #     # h.hashOffset = True
    #     # h.hashMIDI = False
    #     # h.hashChords = False
    #     # h.hashChordsAsNotes = False
    #     # h.validTypes = [note.Note, note.Rest]
    #     # h.hashMIDI = False  # otherwise, hash string 'C-- instead of 58'
    #     # h.hashOctave = False
    #     # h.hashDuration = True
    #     # h.roundDurationAndOffset = False
    #     # h.roundOffset = False
    #     # h.hashChordsAsNotes = False
    #     # h.hashChordsAsChords = True
    #     # h.hashOctave = True
    #     # h.hashPrimeiFormString = True
    #     h.hashIntervalFromLastNote = True
    #     # pp(h.hashStream(s1.recurse()))
    #     # hashes1 = h.hashStream(s1.recurse())
    #     s2 = corpus.parse('schoenberg', 2).parts[0]
    #     # hashes2 = h.hashStream(s2.recurse())
    #     s3 = corpus.parse('bwv66.6').parts[0]
    #     # print(type(s3.recurse()))
    #     hashes3 = h.hashStream(s3)
    #     # s4 = corpus.parse('bwv66.6').parts[0].transpose('M2')
    #     # s4 = s5.parts[0].transpose('M2')
    #     s4.show()
    #     # pp(s4.recurse())

    #     hashes4 = h.hashStream(s4)
    #     print(hashes3)
    #     print('    ')
    #     print(hashes4)

    #     pp(difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio())
    #     pp(difflib.SequenceMatcher(a=hashes1, b=hashes3).ratio())
    #     pp(difflib.SequenceMatcher(a=hashes2, b=hashes3).ratio())
    #     # pp(difflib.SequenceMatcher(a=hashes3, b=hashes4).ratio())
    # def testfolk(self):
    #     from music21 import corpus
    #     h = Hasher()

    #     s1 = corpus.parse('ryansMammoth/MyLoveIsInAmericaReel.abc').parts[0]
    #     s2 = corpus.parse('ryansMammoth/MyLoveIsFarAwayReel.abc').parts[0]

    #     s2.show()

    #     hashes1 = h.hashStream(s1)
    #     hashes2 = h.hashStream(s2)

    #     print(difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio())

    #     h.hashPitch = False

    #     hashes1 = h.hashStream(s1)
    #     hashes2 = h.hashStream(s2)

    #     print(difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio())

    def testBvSvS(self):
        from music21 import corpus
        h = Hasher()
        h.hashDuration = False
        h.hashOffset = False
        s1 = corpus.parse('schoenberg', 6).parts[0]
        s2 = corpus.parse('schoenberg', 2).parts[0]
        s3 = corpus.parse('bwv66.6').parts[0]
        hashes1 = h.hashStream(s1)
        hashes2 = h.hashStream(s2)
        hashes3 = h.hashStream(s3)

        print(difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio())
        print(difflib.SequenceMatcher(a=hashes1, b=hashes3).ratio())
        print(difflib.SequenceMatcher(a=hashes2, b=hashes3).ratio())
        s2.show()

        h.hashPitch = False
        h.hashDuration = True
        h.hashOffset = True

        hashes1 = h.hashStream(s1)
        hashes2 = h.hashStream(s2)
        hashes3 = h.hashStream(s3)

        print(difflib.SequenceMatcher(a=hashes1, b=hashes2).ratio())
        print(difflib.SequenceMatcher(a=hashes1, b=hashes3).ratio())
        print(difflib.SequenceMatcher(a=hashes2, b=hashes3).ratio())

    def testInterval(self):
        from music21 import corpus
        h = Hasher()
        s3 = corpus.parse('bwv66.6').parts[0]
        s4 = corpus.parse('bwv66.6').parts[0].transpose('M2')

        hashes3 = h.hashStream(s3)
        hashes4 = h.hashStream(s4)

        print(difflib.SequenceMatcher(a=hashes3, b=hashes4).ratio())

        h.hashIntervalFromLastNote = True
        h.hashPitch = False

        hashes3 = h.hashStream(s3)
        hashes4 = h.hashStream(s4)

        print(difflib.SequenceMatcher(a=hashes3, b=hashes4).ratio())


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
