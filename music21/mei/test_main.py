# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         mei/test_main.py
# Purpose:      Tests for mei/__main__.py
#
# Authors:      Christopher Antila
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------
'''
Tests for :mod:`music21.mei.__main__`.
'''
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods
# pylint: disable=no-self-use

from music21.ext import six

import unittest
if six.PY2:
    import mock
else:
    from unittest import mock  # pylint: disable=no-name-in-module

# To have working MagicMock objects, we can't use cElementTree even though it would be faster.
# The C implementation provides some methods/attributes dynamically (notably "tag"), so MagicMock
# won't know to mock them, and raises an exception instead.
from xml.etree import ElementTree as ETree

from fractions import Fraction
from collections import defaultdict

from music21 import pitch
from music21 import note
from music21 import duration
from music21 import articulations
from music21 import clef
from music21 import stream
from music21 import instrument
from music21 import key
from music21 import meter
from music21 import interval
from music21 import bar
from music21 import tie
from music21 import spanner

# six
from six.moves import xrange  # pylint: disable=redefined-builtin
from six.moves import range  # pylint: disable=redefined-builtin

# Importing from __main__.py
import music21.mei.__main__ as main
from music21.mei.__main__ import _XMLID
from music21.mei.__main__ import _MEINS


class TestThings(unittest.TestCase):
    '''Tests for utility functions.'''

    def testSafePitch1(self):
        '''safePitch(): when ``name`` is a valid pitch name'''
        name = 'D#6'
        expected = pitch.Pitch('D#6')
        actual = main.safePitch(name)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testSafePitch2(self):
        '''safePitch(): when ``name`` is not a valid pitch name'''
        name = ''
        expected = pitch.Pitch()
        actual = main.safePitch(name)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testSafePitch3(self):
        '''safePitch(): when ``name`` is not given, but there are various kwargs'''
        expected = pitch.Pitch('D#6')
        actual = main.safePitch(name='D', accidental='#', octave='6')
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testSafePitch4(self):
        '''safePitch(): when 2nd argument is None'''
        expected = pitch.Pitch('D6')
        actual = main.safePitch(name='D', accidental=None, octave='6')
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testMakeDuration(self):
        '''makeDuration(): just a couple of things'''
        self.assertEqual(2.0, main.makeDuration(2.0, 0).quarterLength)
        self.assertEqual(3.0, main.makeDuration(2.0, 1).quarterLength)
        self.assertEqual(3.5, main.makeDuration(2, 2).quarterLength) # "base" as int---should work
        self.assertEqual(Fraction(4, 1), main.makeDuration(2.0, 20).quarterLength)
        self.assertEqual(Fraction(1, 3), main.makeDuration(0.33333333333333333333, 0).quarterLength)
        self.assertEqual(Fraction(1, 3), main.makeDuration(Fraction(1, 3), 0).quarterLength)

    def testAllPartsPresent1(self):
        '''allPartsPresent(): one <staffDef>, no repeats'''
        inputValue = [mock.MagicMock()]
        inputValue[0].get = mock.MagicMock(return_value='1')
        expected = ['1']
        actual = main.allPartsPresent(inputValue)
        self.assertSequenceEqual(expected, actual)

    def testAllPartsPresent2(self):
        '''allPartsPresent(): four <staffDef>s'''
        inputValue = [mock.MagicMock() for _ in xrange(4)]
        for i in xrange(4):
            inputValue[i].get = mock.MagicMock(return_value=str(i + 1))
        expected = list('1234')
        actual = main.allPartsPresent(inputValue)
        self.assertSequenceEqual(expected, actual)

    def testAllPartsPresent3(self):
        '''allPartsPresent(): four unique <staffDef>s, several repeats'''
        inputValue = [mock.MagicMock() for _ in xrange(12)]
        for i in xrange(12):
            inputValue[i].get = mock.MagicMock(return_value=str((i % 4) + 1))
        expected = list('1234')
        actual = main.allPartsPresent(inputValue)
        self.assertSequenceEqual(expected, actual)

    def testAllPartsPresent4(self):
        '''allPartsPresent(): error: no <staffDef>s'''
        inputValue = []
        self.assertRaises(main.MeiValidityError, main.allPartsPresent, inputValue)
        try:
            main.allPartsPresent(inputValue)
        except main.MeiValidityError as mvErr:
            self.assertEqual(main._SEEMINGLY_NO_PARTS, mvErr.args[0])

    def testTimeSigFromAttrs(self):
        '''_timeSigFromAttrs(): that it works (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'meter.count': '3', 'meter.unit': '8'})
        expectedRatioString = '3/8'
        actual = main._timeSigFromAttrs(elem)
        self.assertEqual(expectedRatioString, actual.ratioString)

    def testKeySigFromAttrs1(self):
        '''_keySigFromAttrs(): using @key.pname, @key.accid, and @key.mode (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'key.pname': 'B', 'key.accid': 'f',
                                                      'key.mode': 'minor'})
        expectedTPNWC = 'b-'
        actual = main._keySigFromAttrs(elem)
        self.assertIsInstance(actual, key.Key)
        self.assertEqual(expectedTPNWC, actual.tonicPitchNameWithCase)

    def testKeySigFromAttrs2(self):
        '''_keySigFromAttrs(): using @key.sig, and @key.mode (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'key.sig': '6s', 'key.mode': 'minor'})
        expectedSharps = 6
        expectedMode = 'minor'
        actual = main._keySigFromAttrs(elem)
        self.assertIsInstance(actual, key.KeySignature)
        self.assertEqual(expectedSharps, actual.sharps)
        self.assertEqual(expectedMode, actual.mode)

    def testTranspositionFromAttrs1(self):
        '''_transpositionFromAttrs(): descending transposition (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'trans.semi': '-3', 'trans.diat': '-2'})
        expectedName = 'm-3'
        actual = main._transpositionFromAttrs(elem)
        self.assertIsInstance(actual, interval.Interval)
        self.assertEqual(expectedName, actual.directedName)

    def testTranspositionFromAttrs2(self):
        '''_transpositionFromAttrs(): ascending transposition (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'trans.semi': '7', 'trans.diat': '4'})
        expectedName = 'P5'
        actual = main._transpositionFromAttrs(elem)
        self.assertIsInstance(actual, interval.Interval)
        self.assertEqual(expectedName, actual.directedName)

    def testTranspositionFromAttrs3(self):
        '''_transpositionFromAttrs(): large ascending interval (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'trans.semi': '19', 'trans.diat': '11'})
        expectedName = 'P12'
        actual = main._transpositionFromAttrs(elem)
        self.assertIsInstance(actual, interval.Interval)
        self.assertEqual(expectedName, actual.directedName)

    def testTranspositionFromAttrs4(self):
        '''_transpositionFromAttrs(): alternate octave spec (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'trans.semi': '12', 'trans.diat': '0'})
        expectedName = 'P8'
        actual = main._transpositionFromAttrs(elem)
        self.assertIsInstance(actual, interval.Interval)
        self.assertEqual(expectedName, actual.directedName)

    def testTranspositionFromAttrs5(self):
        '''_transpositionFromAttrs(): alternate large descending interval (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'trans.semi': '-19', 'trans.diat': '-4'})
        expectedName = 'P-12'
        actual = main._transpositionFromAttrs(elem)
        self.assertIsInstance(actual, interval.Interval)
        self.assertEqual(expectedName, actual.directedName)

    def testTranspositionFromAttrs6(self):
        '''_transpositionFromAttrs(): alternate ascending sixteenth interval (integration test)'''
        elem = ETree.Element('{mei}staffDef', attrib={'trans.semi': '26', 'trans.diat': '1'})
        expectedName = 'M16'
        actual = main._transpositionFromAttrs(elem)
        self.assertIsInstance(actual, interval.Interval)
        self.assertEqual(expectedName, actual.directedName)

    def testRemoveOctothorpe1(self):
        '''removeOctothorpe(): when there's an octothorpe'''
        xmlid = '#14ccdc11-8090-49f4-b094-5935f534131a'
        expected = '14ccdc11-8090-49f4-b094-5935f534131a'
        actual = main.removeOctothorpe(xmlid)
        self.assertEqual(expected, actual)

    def testRemoveOctothorpe2(self):
        '''removeOctothorpe(): when there's not an octothorpe'''
        xmlid = 'b05c3007-bc49-4bc2-a970-bb5700cb634d'
        expected = 'b05c3007-bc49-4bc2-a970-bb5700cb634d'
        actual = main.removeOctothorpe(xmlid)
        self.assertEqual(expected, actual)

    @mock.patch('music21.mei.__main__._makeArticList')
    def testArticFromElement(self, mockMakeList):
        '''articFromElement(): very straight-forward test'''
        elem = ETree.Element('artic', attrib={'artic': 'yes'})
        mockMakeList.return_value = 5
        actual = main.articFromElement(elem)
        self.assertEqual(5, actual)
        mockMakeList.assert_called_once_with('yes')

    @mock.patch('music21.mei.__main__._accidentalFromAttr')
    def testAccidFromElement(self, mockAccid):
        '''accidFromElement(): very straight-forward test'''
        elem = ETree.Element('accid', attrib={'accid': 'yes'})
        mockAccid.return_value = 5
        actual = main.accidFromElement(elem)
        self.assertEqual(5, actual)
        mockAccid.assert_called_once_with('yes')

    def testGetVoiceId1(self):
        '''getVoiceId(): usual case'''
        theVoice = stream.Voice()
        theVoice.id = 42
        fromThese = [None, theVoice, stream.Stream(), stream.Part(), 900]
        expected = 42
        actual = main.getVoiceId(fromThese)
        self.assertEqual(expected, actual)

    def testGetVoiceId2(self):
        '''getVoiceId(): no Voice objects causes RuntimeError'''
        fromThese = [None, stream.Stream(), stream.Part(), 900]
        self.assertRaises(RuntimeError, main.getVoiceId, fromThese)

    def testGetVoiceId3(self):
        '''getVoiceId(): three Voice objects causes RuntimeError'''
        firstVoice = stream.Voice()
        firstVoice.id = 42
        otherVoice = stream.Voice()
        otherVoice.id = 24
        fromThese = [None, firstVoice, stream.Stream(), stream.Part(), otherVoice, 900]
        self.assertRaises(RuntimeError, main.getVoiceId, fromThese)


#------------------------------------------------------------------------------
class TestAttrTranslators(unittest.TestCase):
    '''Tests for the one-to-one (string-to-simple-datatype) converter functions.'''

    def testAttrTranslator1(self):
        '''_attrTranslator(): the usual case works properly when "attr" is in "mapping"'''
        attr = 'two'
        name = 'numbers'
        mapping = {'one': 1, 'two': 2, 'three': 3}
        expected = 2
        actual = main._attrTranslator(attr, name, mapping)
        self.assertEqual(expected, actual)

    def testAttrTranslator2(self):
        '''_attrTranslator(): exception is raised properly when "attr" isn't found'''
        attr = 'four'
        name = 'numbers'
        mapping = {'one': 1, 'two': 2, 'three': 3}
        expected = 'Unexpected value for "numbers" attribute: four'
        self.assertRaises(main.MeiValueError, main._attrTranslator, attr, name, mapping)
        try:
            main._attrTranslator(attr, name, mapping)
        except main.MeiValueError as mvErr:
            self.assertEqual(expected, mvErr.args[0])

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testAccidental(self, mockTrans):
        '''_accidentalFromAttr(): ensure proper arguments to _attrTranslator'''
        attr = 's'
        main._accidentalFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'accid', main._ACCID_ATTR_DICT)

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testDuration(self, mockTrans):
        '''_qlDurationFromAttr(): ensure proper arguments to _attrTranslator'''
        attr = 's'
        main._qlDurationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'dur', main._DUR_ATTR_DICT)

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testArticulation1(self, mockTrans):
        '''_articulationFromAttr(): ensure proper arguments to _attrTranslator'''
        attr = 'marc'
        mockTrans.return_value = mock.MagicMock(name='asdf', return_value=5)
        expected = (5,)
        actual = main._articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', main._ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testArticulation2(self, mockTrans):
        '''_articulationFromAttr(): proper handling of "marc-stacc"'''
        attr = 'marc-stacc'
        expected = (articulations.StrongAccent, articulations.Staccato)
        actual = main._articulationFromAttr(attr)
        self.assertEqual(0, mockTrans.call_count)
        for i in xrange(len(expected)):
            self.assertTrue(isinstance(actual[i], expected[i]))

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testArticulation3(self, mockTrans):
        '''_articulationFromAttr(): proper handling of "ten-stacc"'''
        attr = 'ten-stacc'
        expected = (articulations.Tenuto, articulations.Staccato)
        actual = main._articulationFromAttr(attr)
        self.assertEqual(0, mockTrans.call_count)
        for i in xrange(len(expected)):
            self.assertTrue(isinstance(actual[i], expected[i]))

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testArticulation4(self, mockTrans):
        '''_articulationFromAttr(): proper handling of not-found'''
        attr = 'garbage'
        expected = 'error message'
        mockTrans.side_effect = main.MeiValueError(expected)
        self.assertRaises(main.MeiValueError, main._articulationFromAttr, attr)
        mockTrans.assert_called_once_with(attr, 'artic', main._ARTIC_ATTR_DICT)
        try:
            main._articulationFromAttr(attr)
        except main.MeiValueError as mvErr:
            self.assertEqual(expected, mvErr.args[0])

    @mock.patch('music21.mei.__main__._articulationFromAttr')
    def testArticList1(self, mockArtic):
        '''_makeArticList(): properly handles single-articulation lists'''
        attr = 'acc'
        mockArtic.return_value = ['accent']
        expected = ['accent']
        actual = main._makeArticList(attr)
        self.assertEqual(expected, actual)

    @mock.patch('music21.mei.__main__._articulationFromAttr')
    def testArticList2(self, mockArtic):
        '''_makeArticList(): properly handles multi-articulation lists'''
        attr = 'acc stacc marc'
        mockReturns = [['accent'], ['staccato'], ['marcato']]
        mockArtic.side_effect = lambda x: mockReturns.pop(0)
        expected = ['accent', 'staccato', 'marcato']
        actual = main._makeArticList(attr)
        self.assertEqual(expected, actual)

    @mock.patch('music21.mei.__main__._articulationFromAttr')
    def testArticList3(self, mockArtic):
        '''_makeArticList(): properly handles the compound articulations'''
        attr = 'acc marc-stacc marc'
        mockReturns = [['accent'], ['marcato', 'staccato'], ['marcato']]
        mockArtic.side_effect = lambda *x: mockReturns.pop(0)
        expected = ['accent', 'marcato', 'staccato', 'marcato']
        actual = main._makeArticList(attr)
        self.assertEqual(expected, actual)

    def testOctaveShift1(self):
        '''_getOctaveShift(): properly handles positive displacement'''
        dis = '15'
        disPlace = 'above'
        expected = 2
        actual = main._getOctaveShift(dis, disPlace)
        self.assertEqual(expected, actual)

    def testOctaveShift2(self):
        '''_getOctaveShift(): properly handles negative displacement'''
        dis = '22'
        disPlace = 'below'
        expected = -3
        actual = main._getOctaveShift(dis, disPlace)
        self.assertEqual(expected, actual)

    def testOctaveShift3(self):
        '''_getOctaveShift(): properly handles positive displacement with "None"'''
        dis = '8'
        disPlace = None
        expected = 1
        actual = main._getOctaveShift(dis, disPlace)
        self.assertEqual(expected, actual)

    def testOctaveShift4(self):
        '''_getOctaveShift(): properly positive two "None" args'''
        dis = None
        disPlace = None
        expected = 0
        actual = main._getOctaveShift(dis, disPlace)
        self.assertEqual(expected, actual)

    def testBarlineFromAttr1(self):
        '''_barlineFromAttr(): rptboth'''
        right = 'rptboth'
        expected = None
        actual = main._barlineFromAttr(right)
        self.assertEqual(type(expected), type(actual))

    def testBarlineFromAttr2(self):
        '''_barlineFromAttr(): rptend'''
        right = 'rptend'
        expected = bar.Repeat('end', times=2)
        actual = main._barlineFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.direction, expected.direction)
        self.assertEqual(expected.times, expected.times)

    def testBarlineFromAttr3(self):
        '''_barlineFromAttr(): rptstart'''
        right = 'rptstart'
        expected = bar.Repeat('start')
        actual = main._barlineFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.direction, expected.direction)
        self.assertEqual(expected.times, expected.times)

    def testBarlineFromAttr4(self):
        '''_barlineFromAttr(): end (--> final)'''
        right = 'end'
        expected = bar.Barline('final')
        actual = main._barlineFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.style, expected.style)

    def testTieFromAttr1(self):
        '''_tieFromAttr(): "i"'''
        right = ''
        expected = tie.Tie('start')
        actual = main._tieFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.type, expected.type)

    def testTieFromAttr2(self):
        '''_tieFromAttr(): "ti"'''
        right = ''
        expected = tie.Tie('continue')
        actual = main._tieFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.type, expected.type)

    def testTieFromAttr3(self):
        '''_tieFromAttr(): "m"'''
        right = ''
        expected = tie.Tie('continue')
        actual = main._tieFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.type, expected.type)

    def testTieFromAttr4(self):
        '''_tieFromAttr(): "t"'''
        right = ''
        expected = tie.Tie('stop')
        actual = main._tieFromAttr(right)
        self.assertEqual(type(expected), type(actual))
        self.assertEqual(expected.type, expected.type)


#------------------------------------------------------------------------------
class TestNoteFromElement(unittest.TestCase):
    '''Tests for noteFromElement()'''
    # NOTE: For this TestCase, in the unit tests, if you get...
    #       AttributeError: 'str' object has no attribute 'call_count'
    #       ... it means a test failure, because the str should have been a MagicMock but was
    #       replaced with a string by the unit under test.

    @mock.patch('music21.note.Note')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.safePitch')
    @mock.patch('music21.mei.__main__.makeDuration')
    def testUnit1(self, mockMakeDuration, mockSafePitch, mockProcEmbEl, mockNote):
        '''
        noteFromElement(): all the basic attributes (i.e., @pname, @accid, @oct, @dur, @dots)

        (mostly-unit test; mock out Note, _processEmbeddedElements(), safePitch(), and makeDuration())
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4',
                                             'dots': '1'})
        mockMakeDuration.return_value = 'makeDuration() return'
        mockSafePitch.return_value = 'safePitch() return'
        mockNewNote = mock.MagicMock()
        mockNote.return_value = mockNewNote
        mockProcEmbEl.return_value = []
        expected = mockNewNote

        actual = main.noteFromElement(elem, None)

        self.assertEqual(expected, mockNewNote, actual)
        mockSafePitch.assert_called_once_with('D', '#', '2')
        mockMakeDuration.assert_called_once_with(1.0, 1)
        mockNote.assert_called_once_with(mockSafePitch.return_value,
                                         duration=mockMakeDuration.return_value)
        self.assertEqual(0, mockNewNote.id.call_count)
        self.assertEqual(0, mockNewNote.articulations.extend.call_count)
        self.assertEqual(0, mockNewNote.tie.call_count)
        self.assertEqual(0, mockNewNote.duration.call_count)

    def testIntegration1a(self):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'pname', 'accid', 'oct', 'dur', 'dots'
        (corresponds to testUnit1() with no mocks)
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4',
                                             'dots': '1'})
        actual = main.noteFromElement(elem)
        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)

    def testIntegration1b(self):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'pname', 'accid', 'oct', 'dur', 'dots'
        (this has different arguments than testIntegration1a())
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'accid': 'n', 'oct': '2', 'dur': '4'})
        actual = main.noteFromElement(elem)
        self.assertEqual('D2', actual.nameWithOctave)
        self.assertEqual(1.0, actual.quarterLength)
        self.assertEqual(0, actual.duration.dots)

    @mock.patch('music21.note.Note')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.safePitch')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.pitch.Accidental')
    def testUnit2(self, mockAccid, mockMakeDuration, mockSafePitch, mockProcEmbEl, mockNote):
        '''
        noteFromElement(): adds <artic>, <accid>, and <dot> elements held within

        (mostly-unit test; mock out Note, _processEmbeddedElements(), safePitch(), and makeDuration())
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'oct': '2', 'dur': '4'})
        # accid: s, dots: 1, artic: stacc
        mockMakeDuration.return_value = 'makeDuration() return'
        mockSafePitch.return_value = 'safePitch() return'
        mockAccid.return_value = 'an accidental'
        mockNewNote = mock.MagicMock()
        mockNote.return_value = mockNewNote
        mockProcEmbEl.return_value = [1, '#', articulations.Staccato()]
        expected = mockNewNote
        expMockMakeDur = [mock.call(1.0, 0), mock.call(1.0, 1)]

        actual = main.noteFromElement(elem, None)

        self.assertEqual(expected, mockNewNote, actual)
        mockSafePitch.assert_called_once_with('D', None, '2')
        mockNewNote.pitch.accidental = mockAccid.return_value
        self.assertEqual(1, mockNewNote.articulations.append.call_count)
        self.assertIsInstance(mockNewNote.articulations.append.call_args_list[0][0][0],
                              articulations.Staccato)
        self.assertEqual(expMockMakeDur, mockMakeDuration.call_args_list)
        mockNote.assert_called_once_with(mockSafePitch.return_value,
                                         duration=mockMakeDuration.return_value)
        self.assertEqual(0, mockNewNote.id.call_count)
        self.assertEqual(0, mockNewNote.articulations.extend.call_count)
        self.assertEqual(0, mockNewNote.tie.call_count)
        self.assertEqual(mockMakeDuration.return_value, mockNewNote.duration)

    def testIntegration2(self):
        '''
        noteFromElement(): adds <artic>, <accid>, and <dot> elements held within
        (corresponds to testUnit2() with no mocks)
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'oct': '2', 'dur': '2'})
        elem.append(ETree.Element('{}dot'.format(_MEINS)))
        elem.append(ETree.Element('{}artic'.format(_MEINS), attrib={'artic': 'stacc'}))
        elem.append(ETree.Element('{}accid'.format(_MEINS), attrib={'accid': 's'}))

        actual = main.noteFromElement(elem)

        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(3.0, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)
        self.assertEqual(1, len(actual.articulations))
        self.assertIsInstance(actual.articulations[0], articulations.Staccato)

    @mock.patch('music21.note.Note')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.safePitch')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__._makeArticList')
    @mock.patch('music21.mei.__main__._tieFromAttr')
    @mock.patch('music21.mei.__main__.addSlurs')
    def testUnit3(self, mockSlur, mockTie, mockArticList, mockMakeDuration, mockSafePitch, mockProcEmbEl, mockNote):
        '''
        noteFromElement(): adds @xml:id, @artic, and @tie attributes, and the slurBundle

        (mostly-unit test; mock out Note, _processEmbeddedElements(), safePitch(), and makeDuration())
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4',
                                             'dots': '1', 'artic': 'stacc', _XMLID: '123',
                                             'tie': 'i1'})
        mockMakeDuration.return_value = 'makeDuration() return'
        mockSafePitch.return_value = 'safePitch() return'
        mockNewNote = mock.MagicMock()
        mockNote.return_value = mockNewNote
        mockProcEmbEl.return_value = []
        mockArticList.return_value = ['staccato!']
        mockTie.return_value = 'a tie!'
        expected = mockNewNote

        actual = main.noteFromElement(elem, 'slur bundle')

        self.assertEqual(expected, mockNewNote, actual)
        mockSafePitch.assert_called_once_with('D', '#', '2')
        mockMakeDuration.assert_called_once_with(1.0, 1)
        mockNote.assert_called_once_with(mockSafePitch.return_value,
                                         duration=mockMakeDuration.return_value)
        self.assertEqual('123', mockNewNote.id)
        mockNewNote.articulations.extend.assert_called_once_with(['staccato!'])
        self.assertEqual('a tie!', mockNewNote.tie)
        self.assertEqual(0, mockNewNote.duration.call_count)
        mockSlur.assert_called_once_with(elem, mockNewNote, 'slur bundle')

    def testIntegration3(self):
        '''
        noteFromElement(): adds @xml:id, @artic, and @tie attributes, and the slurBundle
        (corresponds to testUnit3() with no mocks)
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4',
                                             'dots': '1', _XMLID: 'asdf1234', 'artic': 'stacc',
                                             'tie': 'i1'})
        slurBundle = spanner.SpannerBundle()

        actual = main.noteFromElement(elem, slurBundle)

        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)
        self.assertEqual('asdf1234', actual.id)
        self.assertEqual(1, len(actual.articulations))
        self.assertIsInstance(actual.articulations[0], articulations.Staccato)
        self.assertEqual(tie.Tie('start'), actual.tie)

    @mock.patch('music21.note.Note')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.safePitch')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__.scaleToTuplet')
    def testUnit4(self, mockTuplet, mockMakeDuration, mockSafePitch, mockProcEmbEl, mockNote):
        '''
        noteFromElement(): adds @grace, and tuplet-related attributes

        (mostly-unit test)
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'oct': '2', 'dur': '4',
                                             'm21TupletNum': '5', 'm21TupletNumbase': '4',
                                             'm21TupletSearch': 'start'})
        mockSafePitch.return_value = 'safePitch() return'
        mockNewNote = mock.MagicMock()
        mockNote.return_value = mockNewNote
        mockProcEmbEl.return_value = []
        mockTuplet.return_value = 'made the tuplet'
        expected = mockTuplet.return_value

        actual = main.noteFromElement(elem, 'slur bundle')

        self.assertEqual(expected, actual)
        mockSafePitch.assert_called_once_with('D', None, '2')
        mockMakeDuration.assert_calleed_once_with(1.0, 0)
        mockNote.assert_called_once_with(mockSafePitch.return_value,
                                         duration=mockMakeDuration.return_value)
        mockTuplet.assert_called_once_with(mockNewNote, elem)

    def testIntegration4(self):
        '''
        noteFromElement(): adds @grace, @m21TupletNum
        (corresponds to testUnit4() with no mocks)
        '''
        elem = ETree.Element('note', attrib={'pname': 'D', 'oct': '2', 'dur': '4',
                                             'm21TupletNum': '5', 'm21TupletNumbase': '4',
                                             'm21TupletSearch': 'start'})
        slurBundle = spanner.SpannerBundle()

        actual = main.noteFromElement(elem, slurBundle)

        self.assertEqual('D2', actual.nameWithOctave)
        self.assertEqual(1.0, actual.quarterLength)
        self.assertEqual('quarter', actual.duration.type)
        self.assertEqual('5', actual.m21TupletNum)
        self.assertEqual('4', actual.m21TupletNumbase)
        self.assertEqual('start', actual.m21TupletSearch)

    # NOTE: consider adding to the testUnit4() and testIntegration4() rather than making a new test


#------------------------------------------------------------------------------
class TestRestFromElement(unittest.TestCase):
    '''Tests for restFromElement()'''

    @mock.patch('music21.note.Rest')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__.scaleToTuplet')
    def testUnit1(self, mockTuplet, mockMakeDur, mockRest):
        '''
        restFromElement(): test @dur, @dots, @xml:id, and tuplet-related attributes
        '''
        elem = ETree.Element('rest', attrib={'dur': '4', 'dots': '1', _XMLID: 'the id',
                                             'm21TupletNum': '5', 'm21TupletNumbase': '4',
                                             'm21TupletType': 'start'})
        mockMakeDur.return_value = 'the duration'
        mockNewRest = mock.MagicMock('new rest')
        mockRest.return_value = mockNewRest
        mockTuplet.return_value = 'tupletized'
        expected = mockTuplet.return_value

        actual = main.restFromElement(elem)

        self.assertEqual(expected, actual)
        mockRest.assert_called_once_with(duration=mockMakeDur.return_value)
        mockMakeDur.assert_called_once_with(1.0, 1)
        mockTuplet.assert_called_once_with(mockRest.return_value, elem)
        self.assertEqual('the id', mockNewRest.id)

    def testIntegration1(self):
        '''
        restFromElement(): test @dur, @dots, @xml:id, and tuplet-related attributes

        (without mock objects)
        '''
        elem = ETree.Element('rest', attrib={'dur': '4', 'dots': '1', _XMLID: 'the id',
                                             'm21TupletNum': '5', 'm21TupletNumbase': '4',
                                             'm21TupletType': 'start'})

        actual = main.restFromElement(elem)

        self.assertEqual(Fraction(6, 5), actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)
        self.assertEqual('the id', actual.id)
        self.assertEqual('start', actual.duration.tuplets[0].type)


#------------------------------------------------------------------------------
class TestChordFromElement(unittest.TestCase):
    '''Tests for chordFromElement()'''
    # NOTE: For this TestCase, in the unit tests, if you get...
    #       AttributeError: 'str' object has no attribute 'call_count'
    #       ... it means a test failure, because the str should have been a MagicMock but was
    #       replaced with a string by the unit under test.

    @staticmethod
    def makeNoteElems(pname, accid, octArg, dur, dots):
        '''Factory function for the Element objects that are a <note>.'''
        return ETree.Element('{}note'.format(_MEINS), pname=pname, accid=accid, oct=octArg, dur=dur, dots=dots)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__.noteFromElement')
    def testUnit1(self, mockNoteFromE, mockMakeDuration, mockProcEmbEl, mockChord):
        '''
        chordFromElement(): all the basic attributes (i.e., @pname, @accid, @oct, @dur, @dots)
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'dots': '1'})
        noteElements = [TestChordFromElement.makeNoteElems(x, None, '4', '8', None) for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        mockNoteFromE.return_value = 'a note'
        mockMakeDuration.return_value = 'makeDuration() return'
        mockNewChord = mock.MagicMock()
        mockChord.return_value = mockNewChord
        mockProcEmbEl.return_value = []
        expected = mockNewChord

        actual = main.chordFromElement(elem, None)

        self.assertEqual(expected, mockNewChord, actual)  # TODO: this calls __eq__() but I don't know if that actually returns something useful
        mockMakeDuration.assert_called_once_with(1.0, 1)
        mockChord.assert_called_once_with(notes=[mockNoteFromE.return_value for _ in range(3)])
        self.assertEqual(0, mockNewChord.id.call_count)
        self.assertEqual(0, mockNewChord.articulations.extend.call_count)
        self.assertEqual(0, mockNewChord.tie.call_count)
        self.assertEqual(mockMakeDuration.return_value, mockNewChord.duration)

    def testIntegration1a(self):
        '''
        chordFromElement(): all the basic attributes (i.e., @pname, @accid, @oct, @dur, @dots)

        (corresponds to testUnit1() with no mocks)
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'dots': '1'})
        noteElements = [TestChordFromElement.makeNoteElems(x, 'n', '4', '8', '0') for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        expectedName = 'Chord {C-natural in octave 4 | E-natural in octave 4 | G-natural in octave 4} Dotted Quarter'
        actual = main.chordFromElement(elem)
        self.assertEqual(expectedName, actual.fullName)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__.noteFromElement')
    def testUnit2(self, mockNoteFromE, mockMakeDuration, mockProcEmbEl, mockChord):
        '''
        chordFromElement(): adds an <artic> element held within
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'dots': '1'})
        noteElements = [TestChordFromElement.makeNoteElems(x, None, '4', '8', None) for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        elem.append(ETree.Element('{}artic'.format(_MEINS), artic='stacc'))
        mockNoteFromE.return_value = 'a note'
        mockMakeDuration.return_value = 'makeDuration() return'
        mockNewChord = mock.MagicMock()
        mockChord.return_value = mockNewChord
        mockProcEmbEl.return_value = [articulations.Staccato()]
        expected = mockNewChord

        actual = main.chordFromElement(elem, None)

        self.assertEqual(expected, mockNewChord, actual)
        mockMakeDuration.assert_called_once_with(1.0, 1)
        mockChord.assert_called_once_with(notes=[mockNoteFromE.return_value for _ in range(3)])
        self.assertEqual(1, mockNewChord.articulations.append.call_count)
        self.assertIsInstance(mockNewChord.articulations.append.call_args_list[0][0][0],
                              articulations.Staccato)
        self.assertEqual(0, mockNewChord.id.call_count)
        self.assertEqual(0, mockNewChord.articulations.extend.call_count)
        self.assertEqual(0, mockNewChord.tie.call_count)
        self.assertEqual(mockMakeDuration.return_value, mockNewChord.duration)

    def testIntegration2(self):
        '''
        noteFromElement(): adds <artic>, <accid>, and <dot> elements held within

        (corresponds to testUnit2() with no mocks)
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'dots': '1'})
        noteElements = [TestChordFromElement.makeNoteElems(x, 'n', '4', '8', '0') for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        elem.append(ETree.Element('{}artic'.format(_MEINS), artic='stacc'))
        expectedName = 'Chord {C-natural in octave 4 | E-natural in octave 4 | G-natural in octave 4} Dotted Quarter'
        actual = main.chordFromElement(elem)
        self.assertEqual(expectedName, actual.fullName)
        self.assertEqual(1, len(actual.articulations))
        self.assertIsInstance(actual.articulations[0], articulations.Staccato)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__.noteFromElement')
    @mock.patch('music21.mei.__main__._makeArticList')
    @mock.patch('music21.mei.__main__._tieFromAttr')
    @mock.patch('music21.mei.__main__.addSlurs')
    def testUnit3(self, mockSlur, mockTie, mockArticList, mockNoteFromE, mockMakeDuration, mockProcEmbEl, mockChord):
        '''
        chordFromElement(): adds @xml:id, @artic, and @tie attributes, and the slurBundle
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'dots': '1', 'artic': 'stacc',
                                              _XMLID: '123', 'tie': 'i1'})
        noteElements = [TestChordFromElement.makeNoteElems(x, None, '4', '8', None) for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        mockNoteFromE.return_value = 'a note'
        mockMakeDuration.return_value = 'makeDuration() return'
        mockNewChord = mock.MagicMock()
        mockChord.return_value = mockNewChord
        mockProcEmbEl.return_value = []
        mockArticList.return_value = ['staccato!']
        mockTie.return_value = 'a tie!'
        expected = mockNewChord

        actual = main.chordFromElement(elem, 'slur bundle')

        self.assertEqual(expected, mockNewChord, actual)
        mockMakeDuration.assert_called_once_with(1.0, 1)
        mockChord.assert_called_once_with(notes=[mockNoteFromE.return_value for _ in range(3)])
        self.assertEqual(mockMakeDuration.return_value, mockNewChord.duration)
        mockNewChord.articulations.extend.assert_called_once_with(['staccato!'])
        self.assertEqual('123', mockNewChord.id)
        self.assertEqual('a tie!', mockNewChord.tie)
        mockSlur.assert_called_once_with(elem, mockNewChord, 'slur bundle')

    def testIntegration3(self):
        '''
        noteFromElement(): adds @xml:id, @artic, and @tie attributes, and the slurBundle

        (corresponds to testUnit3() with no mocks)
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'dots': '1', 'artic': 'stacc',
                                              _XMLID: 'asdf1234', 'tie': 'i1'})
        noteElements = [TestChordFromElement.makeNoteElems(x, 'n', '4', '8', '0') for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        expectedName = 'Chord {C-natural in octave 4 | E-natural in octave 4 | G-natural in octave 4} Dotted Quarter'
        actual = main.chordFromElement(elem)
        self.assertEqual(expectedName, actual.fullName)
        self.assertEqual(1, len(actual.articulations))
        self.assertIsInstance(actual.articulations[0], articulations.Staccato)
        self.assertEqual('asdf1234', actual.id)
        self.assertEqual(tie.Tie('start'), actual.tie)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.makeDuration')
    @mock.patch('music21.mei.__main__.noteFromElement')
    @mock.patch('music21.mei.__main__.scaleToTuplet')
    def testUnit4(self, mockTuplet, mockNoteFromE, mockMakeDuration, mockProcEmbEl, mockChord):
        '''
        chordFromElement(): adds tuplet-related attributes
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'm21TupletNum': '5', 'm21TupletNumbase': '4',
                                              'm21TupletSearch': 'start'})
        noteElements = [TestChordFromElement.makeNoteElems(x, None, '4', '8', None) for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        mockNoteFromE.return_value = 'a note'
        mockMakeDuration.return_value = 'makeDuration() return'
        mockNewChord = mock.MagicMock()
        mockChord.return_value = mockNewChord
        mockProcEmbEl.return_value = []
        mockTuplet.return_value = 'tupletified'
        expected = mockTuplet.return_value

        actual = main.chordFromElement(elem, 'slur bundle')

        self.assertEqual(expected, actual)
        mockMakeDuration.assert_called_once_with(1.0, 0)
        mockChord.assert_called_once_with(notes=[mockNoteFromE.return_value for _ in range(3)])
        self.assertEqual(mockMakeDuration.return_value, mockNewChord.duration)
        mockTuplet.assert_called_once_with(mockNewChord, elem)

    def testIntegration4(self):
        '''
        noteFromElement(): adds tuplet-related attributes

        (corresponds to testUnit4() with no mocks)
        '''
        elem = ETree.Element('chord', attrib={'dur': '4', 'm21TupletNum': '5', 'm21TupletNumbase': '4',
                                              'm21TupletSearch': 'start'})
        noteElements = [TestChordFromElement.makeNoteElems(x, 'n', '4', '8', '0') for x in ('c', 'e', 'g')]
        for eachElement in noteElements:
            elem.append(eachElement)
        expectedName = 'Chord {C-natural in octave 4 | E-natural in octave 4 | G-natural in octave 4} Quarter'

        actual = main.chordFromElement(elem)

        self.assertEqual(expectedName, actual.fullName)
        self.assertEqual('5', actual.m21TupletNum)
        self.assertEqual('4', actual.m21TupletNumbase)
        self.assertEqual('start', actual.m21TupletSearch)


#------------------------------------------------------------------------------
class TestClefFromElement(unittest.TestCase):
    '''Tests for clefFromElement()'''
    # NOTE: in this function's integration tests, the Element.tag attribute doesn't actually matter

    @mock.patch('music21.clef.clefFromString')
    @mock.patch('music21.clef.PercussionClef')
    @mock.patch('music21.clef.TabClef')
    def testUnit1a(self, mockTabClef, mockPercClef, mockClefFromString):
        '''
        clefFromElement(): all the elements that go in clef.clefFromString()...
                           'shape', 'line', 'dis', and 'dis.place'
        (mostly-unit test; only mock out clef and the ElementTree.Element)
        '''
        elem = mock.MagicMock()
        expectedGetOrder = [mock.call('shape'), mock.call('shape'), mock.call('shape'),
                            mock.call('line'), mock.call('dis'), mock.call('dis.place')]
        expectedGetOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['theClefShape', 'theClefShape', 'theClefShape', '2', '8', 'above']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockClefFromString.return_value = mock.MagicMock(name='clefFromString()')
        expected = mockClefFromString.return_value

        actual = main.clefFromElement(elem)

        self.assertEqual(expected, actual)
        mockClefFromString.assert_called_once_with_('theClefShape2', 1)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)
        self.assertEqual(0, mockTabClef.call_count)
        self.assertEqual(0, mockPercClef.call_count)

    @mock.patch('music21.clef.clefFromString')
    @mock.patch('music21.clef.PercussionClef')
    @mock.patch('music21.clef.TabClef')
    def testUnit1b(self, mockTabClef, mockPercClef, mockClefFromString):
        '''
        clefFromElement(): same as testUnit1a() but with 'perc' "shape"
        '''
        elem = mock.MagicMock()
        expectedGetOrder = [mock.call('shape')]
        expectedGetOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['perc']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockPercClef.return_value = mock.MagicMock(name='PercussionClef()')
        expected = mockPercClef.return_value

        actual = main.clefFromElement(elem)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mockClefFromString.call_count)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)
        self.assertEqual(0, mockTabClef.call_count)
        self.assertEqual(1, mockPercClef.call_count)

    @mock.patch('music21.clef.clefFromString')
    @mock.patch('music21.clef.PercussionClef')
    @mock.patch('music21.clef.TabClef')
    def testUnit1c(self, mockTabClef, mockPercClef, mockClefFromString):
        '''
        clefFromElement(): same as testUnit1c() but with 'TAB' "shape"
        '''
        elem = mock.MagicMock()
        expectedGetOrder = [mock.call('shape'), mock.call('shape')]
        expectedGetOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['TAB', 'TAB']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockPercClef.return_value = mock.MagicMock(name='PercussionClef()')
        expected = mockTabClef.return_value

        actual = main.clefFromElement(elem)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mockClefFromString.call_count)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)
        self.assertEqual(1, mockTabClef.call_count)
        self.assertEqual(0, mockPercClef.call_count)

    def testIntegration1a(self):
        '''
        clefFromElement(): all the elements that go in clef.clefFromString()...
                           'shape', 'line', 'dis', and 'dis.place'
        (corresponds to testUnit1a, with real objects)
        '''
        clefElem = ETree.Element('clef')
        clefAttribs = {'shape': 'G', 'line': '2', 'dis': '8', 'dis.place': 'above'}
        for eachKey in clefAttribs:
            clefElem.set(eachKey, clefAttribs[eachKey])
        expectedClass = clef.Treble8vaClef

        actual = main.clefFromElement(clefElem)

        self.assertEqual(expectedClass, actual.__class__)

    def testIntegration1b(self):
        '''
        PercussionClef

        (corresponds to testUnit1b, with real objects)
        '''
        clefElem = ETree.Element('clef')
        clefAttribs = {'shape': 'perc'}
        for eachKey in clefAttribs:
            clefElem.set(eachKey, clefAttribs[eachKey])
        expectedClass = clef.PercussionClef

        actual = main.clefFromElement(clefElem)

        self.assertEqual(expectedClass, actual.__class__)

    def testIntegration1c(self):
        '''
        TabClef

        (corresponds to testUnit1c, with real objects)
        '''
        clefElem = ETree.Element('clef')
        clefAttribs = {'shape': 'TAB'}
        for eachKey in clefAttribs:
            clefElem.set(eachKey, clefAttribs[eachKey])
        expectedClass = clef.TabClef

        actual = main.clefFromElement(clefElem)

        self.assertEqual(expectedClass, actual.__class__)

    @mock.patch('music21.clef.clefFromString')
    @mock.patch('music21.clef.PercussionClef')
    @mock.patch('music21.clef.TabClef')
    def testUnit2(self, mockTabClef, mockPercClef, mockClefFromString):
        '''
        clefFromElement(): adds the "xml:id" attribute
        '''
        elem = mock.MagicMock()
        expectedGetOrder = [mock.call('shape'), mock.call(_XMLID), mock.call(_XMLID)]
        expectedGetOrder.extend([mock.ANY for _ in xrange(0)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['perc', 'theXMLID', 'theXMLID']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockPercClef.return_value = mock.MagicMock(name='PercussionClef()')
        expected = mockPercClef.return_value

        actual = main.clefFromElement(elem)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mockClefFromString.call_count)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)
        self.assertEqual(0, mockTabClef.call_count)
        self.assertEqual(1, mockPercClef.call_count)
        self.assertEqual('theXMLID', actual.id)



#------------------------------------------------------------------------------
class TestLayerFromElement(unittest.TestCase):
    '''Tests for layerFromElement()'''

    @mock.patch('music21.mei.__main__.noteFromElement')
    @mock.patch('music21.stream.Voice')
    def testUnit1a(self, mockVoice, mockNoteFromElement):
        '''
        layerFromElement(): basic functionality (i.e., that the tag-name-to-converter-function
                            mapping works; that tags not in the mapping are ignored; and that a
                            Voice object is returned. And "id" is set from the @n attribute.
        (mostly-unit test; only mock noteFromElement and the ElementTree.Element)
        '''
        theNAttribute = '@n value'
        elem = mock.MagicMock()
        elemGetReturns = [theNAttribute, theNAttribute]
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) else None
        expectedGetOrder = [mock.call('n'), mock.call('n')]
        iterfindReturn = [mock.MagicMock(name='note1'),
                          mock.MagicMock(name='imaginary'),
                          mock.MagicMock(name='note2')]
        iterfindReturn[0].tag = '{}note'.format(main._MEINS)
        iterfindReturn[1].tag = '{}imaginary'.format(main._MEINS)
        iterfindReturn[2].tag = '{}note'.format(main._MEINS)
        elem.iterfind = mock.MagicMock(return_value=iterfindReturn)
        # "MNFE" is "mockNoteFromElement"
        expectedMNFEOrder = [mock.call(iterfindReturn[0], None), mock.call(iterfindReturn[2], None)]
        mockNFEreturns = ['mockNoteFromElement return 1', 'mockNoteFromElement return 2']
        mockNoteFromElement.side_effect = lambda *x: mockNFEreturns.pop(0)
        mockVoice.return_value = mock.MagicMock(spec_set=stream.Stream(), name='Voice')
        expectedAppendCalls = [mock.call(mockNFEreturns[0]), mock.call(mockNFEreturns[1])]

        actual = main.layerFromElement(elem)

        elem.iterfind.assert_called_once_with('*')
        self.assertEqual(mockVoice.return_value, actual)
        self.assertSequenceEqual(expectedMNFEOrder, mockNoteFromElement.call_args_list)
        mockVoice.assert_called_once_with()
        self.assertSequenceEqual(expectedAppendCalls, mockVoice.return_value.append.call_args_list)
        self.assertEqual(theNAttribute, actual.id)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)

    @mock.patch('music21.mei.__main__.noteFromElement')
    @mock.patch('music21.stream.Voice')
    def testUnit1b(self, mockVoice, mockNoteFromElement):
        '''
        Same as testUnit1a() *but* with ``overrideN`` provided.
        '''
        elem = mock.MagicMock()
        iterfindReturn = [mock.MagicMock(name='note1'),
                          mock.MagicMock(name='imaginary'),
                          mock.MagicMock(name='note2')]
        iterfindReturn[0].tag = '{}note'.format(main._MEINS)
        iterfindReturn[1].tag = '{}imaginary'.format(main._MEINS)
        iterfindReturn[2].tag = '{}note'.format(main._MEINS)
        elem.iterfind = mock.MagicMock(return_value=iterfindReturn)
        # "MNFE" is "mockNoteFromElement"
        expectedMNFEOrder = [mock.call(iterfindReturn[0], None), mock.call(iterfindReturn[2], None)]
        mockNFEreturns = ['mockNoteFromElement return 1', 'mockNoteFromElement return 2']
        mockNoteFromElement.side_effect = lambda *x: mockNFEreturns.pop(0)
        mockVoice.return_value = mock.MagicMock(spec_set=stream.Stream(), name='Voice')
        expectedAppendCalls = [mock.call(mockNFEreturns[0]), mock.call(mockNFEreturns[1])]
        overrideN = 'my own @n'

        actual = main.layerFromElement(elem, overrideN)

        elem.iterfind.assert_called_once_with('*')
        self.assertEqual(mockVoice.return_value, actual)
        self.assertSequenceEqual(expectedMNFEOrder, mockNoteFromElement.call_args_list)
        mockVoice.assert_called_once_with()
        self.assertSequenceEqual(expectedAppendCalls, mockVoice.return_value.append.call_args_list)
        self.assertEqual(overrideN, actual.id)
        self.assertEqual(0, elem.get.call_count)

    @mock.patch('music21.mei.__main__.noteFromElement')
    @mock.patch('music21.stream.Voice')
    def testUnit1c(self, mockVoice, mockNoteFromElement):
        '''
        Same as testUnit1a() *but* without ``overrideN`` or @n.
        '''
        elem = mock.MagicMock()
        elem.get.return_value = None
        iterfindReturn = [mock.MagicMock(name='note1'),
                          mock.MagicMock(name='imaginary'),
                          mock.MagicMock(name='note2')]
        iterfindReturn[0].tag = '{}note'.format(main._MEINS)
        iterfindReturn[1].tag = '{}imaginary'.format(main._MEINS)
        iterfindReturn[2].tag = '{}note'.format(main._MEINS)
        elem.iterfind = mock.MagicMock(return_value=iterfindReturn)
        # NB: we call the layerFromElement() twice, so we need twice the return values here
        # "MNFE" is "mockNoteFromElement"
        mockNFEreturns = ['mockNoteFromElement return 1', 'mockNoteFromElement return 2',
                          'mockNoteFromElement return 1', 'mockNoteFromElement return 2']
        mockNoteFromElement.side_effect = lambda *x: mockNFEreturns.pop(0)
        mockVoice.return_value = mock.MagicMock(spec_set=stream.Stream(), name='Voice')

        self.assertRaises(main.MeiAttributeError, main.layerFromElement, elem)

        try:
            main.layerFromElement(elem)
        except main.MeiAttributeError as maError:
            self.assertEqual(main._MISSING_VOICE_ID, maError.args[0])


    def testIntegration1a(self):
        '''
        layerFromElement(): basic functionality (i.e., that the tag-name-to-converter-function
                            mapping works; that tags not in the mapping are ignored; and that a
                            Voice object is returned. And "xml:id" is set.
        (corresponds to testUnit1a() but without mock objects)
        '''
        inputXML = '''<layer n="so voice ID" xmlns="http://www.music-encoding.org/ns/mei">
                          <note pname="F" oct="2" dur="4" />
                          <note pname="E" oct="2" accid="f" dur="4" />
                          <imaginary awesome="true" />
                      </layer>'''
        elem = ETree.fromstring(inputXML)

        actual = main.layerFromElement(elem)

        self.assertEqual(2, len(actual))
        self.assertEqual('so voice ID', actual.id)
        self.assertEqual(0.0, actual[0].offset)
        self.assertEqual(1.0, actual[1].offset)
        self.assertEqual(1.0, actual[0].quarterLength)
        self.assertEqual(1.0, actual[1].quarterLength)
        self.assertEqual('F2', actual[0].nameWithOctave)
        self.assertEqual('E-2', actual[1].nameWithOctave)


    def testIntegration1b(self):
        '''
        (corresponds to testUnit1b() but without mock objects)
        '''
        inputXML = '''<layer xmlns="http://www.music-encoding.org/ns/mei">
                          <note pname="F" oct="2" dur="4" />
                          <note pname="E" oct="2" accid="f" dur="4" />
                          <imaginary awesome="true" />
                      </layer>'''
        elem = ETree.fromstring(inputXML)

        actual = main.layerFromElement(elem, 'so voice ID')

        self.assertEqual(2, len(actual))
        self.assertEqual('so voice ID', actual.id)
        self.assertEqual(0.0, actual[0].offset)
        self.assertEqual(1.0, actual[1].offset)
        self.assertEqual(1.0, actual[0].quarterLength)
        self.assertEqual(1.0, actual[1].quarterLength)
        self.assertEqual('F2', actual[0].nameWithOctave)
        self.assertEqual('E-2', actual[1].nameWithOctave)


    def testIntegration1c(self):
        '''
        (corresponds to testUnit1c() but without mock objects)
        '''
        inputXML = '''<layer xmlns="http://www.music-encoding.org/ns/mei">
                          <note pname="F" oct="2" dur="4" />
                          <note pname="E" oct="2" accid="f" dur="4" />
                          <imaginary awesome="true" />
                      </layer>'''
        elem = ETree.fromstring(inputXML)

        self.assertRaises(main.MeiAttributeError, main.layerFromElement, elem)

        try:
            main.layerFromElement(elem)
        except main.MeiAttributeError as maError:
            self.assertEqual(main._MISSING_VOICE_ID, maError.args[0])



#------------------------------------------------------------------------------
class TestStaffFromElement(unittest.TestCase):
    '''Tests for staffFromElement()'''

    @mock.patch('music21.mei.__main__.layerFromElement')
    def testUnit1(self, mockLayerFromElement):
        '''
        staffFromElement(): basic functionality (i.e., that layerFromElement() is called with the
                            right arguments, and with properly-incrementing "id" attributes
        (mostly-unit test; only mock noteFromElement and the ElementTree.Element)
        '''
        elem = mock.MagicMock()
        findallReturn = [mock.MagicMock(name='layer1'),
                         mock.MagicMock(name='layer2'),
                         mock.MagicMock(name='layer3')]
        findallReturn[0].tag = '{}layer'.format(main._MEINS)
        findallReturn[1].tag = '{}layer'.format(main._MEINS)
        findallReturn[2].tag = '{}layer'.format(main._MEINS)
        elem.iterfind = mock.MagicMock(return_value=findallReturn)
        # "MLFE" is "mockLayerFromElement"
        expectedMLFEOrder = [mock.call(findallReturn[i], str(i + 1), slurBundle=None)
                             for i in xrange(len(findallReturn))]
        mockLFEreturns = ['mockLayerFromElement return %i' for i in xrange(len(findallReturn))]
        mockLayerFromElement.side_effect = lambda x, y, slurBundle: mockLFEreturns.pop(0)
        expected = ['mockLayerFromElement return %i' for i in xrange(len(findallReturn))]

        actual = main.staffFromElement(elem)

        elem.iterfind.assert_called_once_with('*')
        self.assertEqual(expected, actual)
        self.assertSequenceEqual(expectedMLFEOrder, mockLayerFromElement.call_args_list)

    def testIntegration1(self):
        '''
        staffFromElement(): basic functionality (i.e., that layerFromElement() is called with the
                            right arguments, and with properly-incrementing "id" attributes
        (corresponds to testUnit1() but without mock objects)
        '''
        inputXML = '''<staff xmlns="http://www.music-encoding.org/ns/mei">
                          <layer>
                              <note pname="F" oct="2" dur="4" />
                          </layer>
                          <layer>
                              <note pname="A" oct="2" dur="4" />
                          </layer>
                          <layer>
                              <note pname="C" oct="2" dur="4" />
                          </layer>
                      </staff>'''
        elem = ETree.fromstring(inputXML)

        actual = main.staffFromElement(elem)

        self.assertEqual(3, len(actual))
        # common to each part
        for i in xrange(len(actual)):
            self.assertEqual(1, len(actual[i]))
            self.assertEqual(0.0, actual[i][0].offset)
            self.assertEqual(1.0, actual[i][0].quarterLength)
        # first part
        self.assertEqual('1', actual[0].id)
        self.assertEqual('F2', actual[0][0].nameWithOctave)
        # second part
        self.assertEqual('2', actual[1].id)
        self.assertEqual('A2', actual[1][0].nameWithOctave)
        # third part
        self.assertEqual('3', actual[2].id)
        self.assertEqual('C2', actual[2][0].nameWithOctave)



#------------------------------------------------------------------------------
class TestStaffDefFromElement(unittest.TestCase):
    '''Tests for staffDefFromElement()'''

    @mock.patch('music21.mei.__main__.instrDefFromElement')
    @mock.patch('music21.mei.__main__._timeSigFromAttrs')
    @mock.patch('music21.mei.__main__._keySigFromAttrs')
    @mock.patch('music21.mei.__main__.clefFromElement')
    @mock.patch('music21.mei.__main__._transpositionFromAttrs')
    def testUnit1(self, mockTrans, mockClef, mockKey, mockTime, mockInstr):
        '''
        staffDefFromElement(): proper handling of the following attributes (see function docstring
            for more information).

        @label, @label.abbr  @n, @key.accid, @key.mode, @key.pname, @key.sig, @meter.count,
        @meter.unit, @clef.shape, @clef.line, @clef.dis, @clef.dis.place, @trans.diat, @trans.demi
        '''
        # 1.) prepare
        elem = mock.MagicMock()
        elem.find = mock.MagicMock(name='{}instrDef', return_value='{}instrDef tag')
        elem.findall = mock.MagicMock(return_value=[])
        def elemGetSideEffect(which, default=None):
            "mock the behaviour of Element.get()"
            theDict = {'clef.shape': 'F', 'clef.line': '4', 'clef.dis': 'cd', 'clef.dis.place': 'cdp',
                       'label': 'the label', 'label.abbr': 'the l.', 'n': '1', 'meter.count': '1',
                       'key.pname': 'G', 'trans.semi': '123'}
            if which in theDict:
                return theDict[which]
            else:
                return default
        elem.get = mock.MagicMock(side_effect=elemGetSideEffect)
        expectedGetCalls = ['label', 'label.abbr', 'n', 'meter.count', 'key.pname',
                            'clef.shape', 'clef.shape', 'clef.line', 'clef.dis', 'clef.dis.place',
                            'trans.semi']
        expectedGetCalls = [mock.call(x) for x in expectedGetCalls]
        theMockInstrument = mock.MagicMock('mock instrument')
        mockInstr.return_value = theMockInstrument
        mockTime.return_value = 'mockTime return'
        mockKey.return_value = 'mockKey return'
        mockClef.return_value = 'mockClef return'
        mockTrans.return_value = 'mockTrans return'
        expected = [mockInstr.return_value, mockTime.return_value, mockKey.return_value,
                    mockClef.return_value]
        # attributes on theMockInstrument that should be set by staffDefFromElement()
        expectedAttrs = [('partName', 'the label'), ('partAbbreviation', 'the l.'), ('partId', '1'),
                         ('transposition', mockTrans.return_value)]

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertSequenceEqual(expected, actual)
        # ensure elem.get() was called with all the expected calls; it doesn't necessarily have to
        # be in a particular order
        if six.PY2:
            self.assertItemsEqual(expectedGetCalls, elem.get.mock_calls)
        else:
            self.assertCountEqual(expectedGetCalls, elem.get.mock_calls)
        mockInstr.assert_called_once_with('{}instrDef tag')
        mockTime.assert_called_once_with(elem)
        mockKey.assert_called_once_with(elem)
        # mockClef is more difficult because it's given an Element
        mockTrans.assert_called_once_with(elem)
        elem.findall.assert_called_once_with('*')
        # check that all attributes are set with their expected values
        for attrName, attrValue in expectedAttrs:
            self.assertEqual(getattr(theMockInstrument, attrName), attrValue)
        # now mockClef, which got an Element
        mockClef.assert_called_once_with(mock.ANY)  # confirm there was a single one-argument call
        mockClefArg = mockClef.call_args_list[0][0][0]
        self.assertEqual('clef', mockClefArg.tag)
        self.assertEqual('F', mockClefArg.get('shape'))
        self.assertEqual('4', mockClefArg.get('line'))
        self.assertEqual('cd', mockClefArg.get('dis'))
        self.assertEqual('cdp', mockClefArg.get('dis.place'))

    def testIntegration1a(self):
        '''
        staffDefFromElement(): corresponds to testUnit1() without mock objects
        '''
        # 1.) prepare
        inputXML = '''<staffDef xmlns="http://www.music-encoding.org/ns/mei" n="12" clef.line="2"
                                clef.shape="G" key.sig="0" key.mode="major" trans.semi="-3"
                                trans.diat="-2" meter.count="3" meter.unit="8">
                         <instrDef midi.channel="1" midi.instrnum="71" midi.instrname="Clarinet"/>
                      </staffDef>'''
        elem = ETree.fromstring(inputXML)

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertIsInstance(actual[0], instrument.Clarinet)
        self.assertIsInstance(actual[1], meter.TimeSignature)
        self.assertIsInstance(actual[2], key.KeySignature)
        self.assertIsInstance(actual[3], clef.TrebleClef)
        self.assertEqual('12', actual[0].partId)
        self.assertEqual('3/8', actual[1].ratioString)
        self.assertEqual('major', actual[2].mode)
        self.assertEqual(0, actual[2].sharps)

    def testIntegration1b(self):
        '''
        staffDefFromElement(): testIntegration1() with <clef> tag inside
        '''
        # 1.) prepare
        inputXML = '''<staffDef xmlns="http://www.music-encoding.org/ns/mei" n="12" key.sig="0"
                                key.mode="major" trans.semi="-3" trans.diat="-2" meter.count="3"
                                meter.unit="8">
                         <instrDef midi.channel="1" midi.instrnum="71" midi.instrname="Clarinet"/>
                         <clef shape="G" line="2"/>
                      </staffDef>'''
        elem = ETree.fromstring(inputXML)

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertIsInstance(actual[0], instrument.Clarinet)
        self.assertIsInstance(actual[1], meter.TimeSignature)
        self.assertIsInstance(actual[2], key.KeySignature)
        self.assertIsInstance(actual[3], clef.TrebleClef)
        self.assertEqual('12', actual[0].partId)
        self.assertEqual('3/8', actual[1].ratioString)
        self.assertEqual('major', actual[2].mode)
        self.assertEqual(0, actual[2].sharps)

    @mock.patch('music21.instrument.fromString')
    @mock.patch('music21.mei.__main__.instrDefFromElement')
    @mock.patch('music21.mei.__main__._timeSigFromAttrs')
    @mock.patch('music21.mei.__main__._keySigFromAttrs')
    @mock.patch('music21.mei.__main__.clefFromElement')
    @mock.patch('music21.mei.__main__._transpositionFromAttrs')
    def testUnit2(self, mockTrans, mockClef, mockKey, mockTime, mockInstr, mockFromString):
        '''
        staffDefFromElement(): same as testUnit1() *but* there's no <instrDef> so we have to use
            music21.instrument.fromString()
        '''
        # NB: differences from testUnit1() are marked with a "D1" comment at the end of the line
        # 1.) prepare
        elem = mock.MagicMock()
        elem.find = mock.MagicMock(name='{}instrDef', return_value=None)  # D1
        elem.findall = mock.MagicMock(return_value=[])
        def elemGetSideEffect(which, default=None):
            "mock the behaviour of Element.get()"
            theDict = {'clef.shape': 'F', 'clef.line': '4', 'clef.dis': 'cd', 'clef.dis.place': 'cdp',
                       'label': 'the label', 'label.abbr': 'the l.', 'n': '1', 'meter.count': '1',
                       'key.pname': 'G', 'trans.semi': '123'}
            if which in theDict:
                return theDict[which]
            else:
                return default
        elem.get = mock.MagicMock(side_effect=elemGetSideEffect)
        expectedGetCalls = ['label', 'label', 'label.abbr', 'n', 'meter.count', 'key.pname',  # D1
                            'clef.shape', 'clef.shape', 'clef.line', 'clef.dis', 'clef.dis.place',
                            'trans.semi']
        expectedGetCalls = [mock.call(x) for x in expectedGetCalls]
        theMockInstrument = mock.MagicMock('mock instrument')
        mockFromString.return_value = theMockInstrument  # D1
        mockTime.return_value = 'mockTime return'
        mockKey.return_value = 'mockKey return'
        mockClef.return_value = 'mockClef return'
        mockTrans.return_value = 'mockTrans return'
        expected = [mockFromString.return_value, mockTime.return_value, mockKey.return_value,  # D1
                    mockClef.return_value]
        # attributes on theMockInstrument that should be set by staffDefFromElement()
        expectedAttrs = [('partName', 'the label'), ('partAbbreviation', 'the l.'), ('partId', '1'),
                         ('transposition', mockTrans.return_value)]

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertSequenceEqual(expected, actual)
        # ensure elem.get() was called with all the expected calls; it doesn't necessarily have to
        # be in a particular order
        if six.PY2:
            self.assertItemsEqual(expectedGetCalls, elem.get.mock_calls)
        else:
            self.assertCountEqual(expectedGetCalls, elem.get.mock_calls)
        self.assertEqual(0, mockInstr.call_count)  # D1
        mockTime.assert_called_once_with(elem)
        mockKey.assert_called_once_with(elem)
        # mockClef is more difficult because it's given an Element
        mockTrans.assert_called_once_with(elem)
        elem.findall.assert_called_once_with('*')
        # check that all attributes are set with their expected values
        for attrName, attrValue in expectedAttrs:
            self.assertEqual(getattr(theMockInstrument, attrName), attrValue)
        # now mockClef, which got an Element
        mockClef.assert_called_once_with(mock.ANY)  # confirm there was a single one-argument call
        mockClefArg = mockClef.call_args_list[0][0][0]
        self.assertEqual('clef', mockClefArg.tag)
        self.assertEqual('F', mockClefArg.get('shape'))
        self.assertEqual('4', mockClefArg.get('line'))
        self.assertEqual('cd', mockClefArg.get('dis'))
        self.assertEqual('cdp', mockClefArg.get('dis.place'))

    def testIntegration2(self):
        '''
        staffDefFromElement(): corresponds to testUnit2() but without mock objects
        '''
        # 1.) prepare
        inputXML = '''<staffDef xmlns="http://www.music-encoding.org/ns/mei" n="12" clef.line="2"
                                clef.shape="G" key.sig="0" key.mode="major" trans.semi="-3"
                                trans.diat="-2" meter.count="3" meter.unit="8" label="clarinet">
                      </staffDef>'''
        elem = ETree.fromstring(inputXML)

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertIsInstance(actual[0], instrument.Clarinet)
        self.assertIsInstance(actual[1], meter.TimeSignature)
        self.assertIsInstance(actual[2], key.KeySignature)
        self.assertIsInstance(actual[3], clef.TrebleClef)
        self.assertEqual('12', actual[0].partId)
        self.assertEqual('3/8', actual[1].ratioString)
        self.assertEqual('major', actual[2].mode)
        self.assertEqual(0, actual[2].sharps)

    @mock.patch('music21.instrument.Instrument')
    @mock.patch('music21.instrument.fromString')
    @mock.patch('music21.mei.__main__.instrDefFromElement')
    @mock.patch('music21.mei.__main__._timeSigFromAttrs')
    @mock.patch('music21.mei.__main__._keySigFromAttrs')
    @mock.patch('music21.mei.__main__.clefFromElement')
    @mock.patch('music21.mei.__main__._transpositionFromAttrs')
    def testUnit3(self, mockTrans, mockClef, mockKey, mockTime, mockInstr, mockFromString, mockInstrInit):
        '''
        staffDefFromElement(): same as testUnit1() *but* there's no <instrDef> so we have to use
          music21.instrument.fromString() *and* that raises an InstrumentException.
        '''
        # NB: differences from testUnit1() are marked with a "D1" comment at the end of the line
        # NB: differences from testUnit2() are marked with a "D2" comment at the end of the line
        # 1.) prepare
        elem = mock.MagicMock()
        elem.find = mock.MagicMock(name='{}instrDef', return_value=None)  # D1
        elem.findall = mock.MagicMock(return_value=[])
        def elemGetSideEffect(which, default=None):
            "mock the behaviour of Element.get()"
            theDict = {'clef.shape': 'F', 'clef.line': '4', 'clef.dis': 'cd', 'clef.dis.place': 'cdp',
                       'label': 'the label', 'label.abbr': 'the l.', 'n': '1', 'meter.count': '1',
                       'key.pname': 'G', 'trans.semi': '123'}
            if which in theDict:
                return theDict[which]
            else:
                return default
        elem.get = mock.MagicMock(side_effect=elemGetSideEffect)
        expectedGetCalls = ['label', 'label', 'label.abbr', 'n', 'meter.count', 'key.pname',  # D1
                            'clef.shape', 'clef.shape', 'clef.line', 'clef.dis', 'clef.dis.place',
                            'trans.semi']
        expectedGetCalls = [mock.call(x) for x in expectedGetCalls]
        theMockInstrument = mock.MagicMock('mock instrument')
        mockFromString.side_effect = instrument.InstrumentException  # D2
        mockInstrInit.return_value = theMockInstrument  # D1 & D2
        mockTime.return_value = 'mockTime return'
        mockKey.return_value = 'mockKey return'
        mockClef.return_value = 'mockClef return'
        mockTrans.return_value = 'mockTrans return'
        expected = [mockInstrInit.return_value, mockTime.return_value, mockKey.return_value,  # D1 & D2
                    mockClef.return_value]
        # attributes on theMockInstrument that should be set by staffDefFromElement()
        expectedAttrs = [('partName', 'the label'), ('partAbbreviation', 'the l.'), ('partId', '1'),
                         ('transposition', mockTrans.return_value)]

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertSequenceEqual(expected, actual)
        # ensure elem.get() was called with all the expected calls; it doesn't necessarily have to
        # be in a particular order
        if six.PY2:
            self.assertItemsEqual(expectedGetCalls, elem.get.mock_calls)
        else:
            self.assertCountEqual(expectedGetCalls, elem.get.mock_calls)
        self.assertEqual(0, mockInstr.call_count)  # D1
        mockTime.assert_called_once_with(elem)
        mockKey.assert_called_once_with(elem)
        # mockClef is more difficult because it's given an Element
        mockTrans.assert_called_once_with(elem)
        elem.findall.assert_called_once_with('*')
        # check that all attributes are set with their expected values
        for attrName, attrValue in expectedAttrs:
            self.assertEqual(getattr(theMockInstrument, attrName), attrValue)
        # now mockClef, which got an Element
        mockClef.assert_called_once_with(mock.ANY)  # confirm there was a single one-argument call
        mockClefArg = mockClef.call_args_list[0][0][0]
        self.assertEqual('clef', mockClefArg.tag)
        self.assertEqual('F', mockClefArg.get('shape'))
        self.assertEqual('4', mockClefArg.get('line'))
        self.assertEqual('cd', mockClefArg.get('dis'))
        self.assertEqual('cdp', mockClefArg.get('dis.place'))

    def testIntegration3(self):
        '''
        staffDefFromElement(): corresponds to testUnit3() but without mock objects
        '''
        # 1.) prepare
        inputXML = '''<staffDef xmlns="http://www.music-encoding.org/ns/mei" n="12" clef.line="2"
                                clef.shape="G" key.sig="0" key.mode="major" trans.semi="-3"
                                trans.diat="-2" meter.count="3" meter.unit="8">
                      </staffDef>'''
        elem = ETree.fromstring(inputXML)

        # 2.) run
        actual = main.staffDefFromElement(elem)

        # 3.) check
        self.assertIsInstance(actual[0], instrument.Instrument)
        self.assertIsInstance(actual[1], meter.TimeSignature)
        self.assertIsInstance(actual[2], key.KeySignature)
        self.assertIsInstance(actual[3], clef.TrebleClef)
        self.assertEqual('12', actual[0].partId)
        self.assertEqual('3/8', actual[1].ratioString)
        self.assertEqual('major', actual[2].mode)
        self.assertEqual(0, actual[2].sharps)



#------------------------------------------------------------------------------
class TestScoreDefFromElement(unittest.TestCase):
    '''Tests for scoreDefFromElement()'''

    @mock.patch('music21.mei.__main__._timeSigFromAttrs')
    @mock.patch('music21.mei.__main__._keySigFromAttrs')
    def testUnit1(self, mockKey, mockTime):
        '''
        scoreDefFromElement(): proper handling of the following attributes (see function docstring
            for more information).

        @meter.count, @meter.unit, @key.accid, @key.mode, @key.pname, @key.sig
        '''
        # 1.) prepare
        elem = mock.MagicMock()
        def elemGetSideEffect(which, default=None):  # pylint: disable=missing-docstring
            theDict = {'meter.count': '7', 'key.pname': 'G'}
            if which in theDict:
                return theDict[which]
            else:
                return default
        elem.get = mock.MagicMock(side_effect=elemGetSideEffect)
        expectedGetCalls = ['meter.count', 'key.pname']
        expectedGetCalls = [mock.call(x) for x in expectedGetCalls]
        mockTime.return_value = 'mockTime return'
        mockKey.return_value = 'mockKey return'
        expected = {'all-part objects': [mockTime.return_value, mockKey.return_value],
                    'whole-score objects': []}

        # 2.) run
        actual = main.scoreDefFromElement(elem)

        # 3.) check
        self.assertEqual(expected, actual)
        # ensure elem.get() was called with all the expected calls; it doesn't necessarily have to
        # be in a particular order
        if six.PY2:
            self.assertItemsEqual(expectedGetCalls, elem.get.mock_calls)
        else:
            self.assertCountEqual(expectedGetCalls, elem.get.mock_calls)
        mockTime.assert_called_once_with(elem)
        mockKey.assert_called_once_with(elem)

    def testIntegration1(self):
        '''
        scoreDefFromElement(): corresponds to testUnit1() without mock objects
        '''
        # 1.) prepare
        inputXML = '''<staffDef xmlns="http://www.music-encoding.org/ns/mei"
                                key.sig="4s" key.mode="major" meter.count="3" meter.unit="8"/>'''
        elem = ETree.fromstring(inputXML)

        # 2.) run
        actual = main.scoreDefFromElement(elem)

        # 3.) check
        self.assertIsInstance(actual['all-part objects'][0], meter.TimeSignature)
        self.assertIsInstance(actual['all-part objects'][1], key.KeySignature)
        self.assertEqual('3/8', actual['all-part objects'][0].ratioString)
        self.assertEqual('major', actual['all-part objects'][1].mode)
        self.assertEqual(4, actual['all-part objects'][1].sharps)



#------------------------------------------------------------------------------
class TestEmbeddedElements(unittest.TestCase):
    '''Tests for _processesEmbeddedElements()'''

    def testUnit1(self):
        '''
        _processesEmbeddedElements(): that single m21 objects are handled properly
        '''
        mockTranslator = mock.MagicMock(return_value='translator return')
        elements = [ETree.Element('note') for _ in xrange(2)]
        mapping = {'note': mockTranslator}
        expected = ['translator return', 'translator return']
        expectedCalls = [mock.call(elements[0], None), mock.call(elements[1], None)]

        actual = main._processEmbeddedElements(elements, mapping)

        self.assertSequenceEqual(expected, actual)
        self.assertSequenceEqual(expectedCalls, mockTranslator.call_args_list)

    def testUnit2(self):
        '''
        _processesEmbeddedElements(): that iterables of m21 objects are handled properly
        '''
        mockTranslator = mock.MagicMock(return_value='translator return')
        mockBeamTranslator = mock.MagicMock(return_value=['embedded 1', 'embedded 2'])
        elements = [ETree.Element('note'), ETree.Element('beam')]
        mapping = {'note': mockTranslator, 'beam': mockBeamTranslator}
        expected = ['translator return', 'embedded 1', 'embedded 2']

        actual = main._processEmbeddedElements(elements, mapping)

        self.assertSequenceEqual(expected, actual)
        mockTranslator.assert_called_once_with(elements[0], None)
        mockBeamTranslator.assert_called_once_with(elements[1], None)

    @mock.patch('music21.mei.__main__.environLocal')
    def testUnit3(self, mockEnviron):
        '''
        _processesEmbeddedElements(): that un-translated elements are reported properly
        '''
        mockTranslator = mock.MagicMock(return_value='translator return')
        elements = [ETree.Element('note'), ETree.Element('bream')]
        mapping = {'note': mockTranslator}
        expected = ['translator return']

        actual = main._processEmbeddedElements(elements, mapping)

        self.assertSequenceEqual(expected, actual)
        mockTranslator.assert_called_once_with(elements[0], None)
        mockEnviron.printDebug.assert_called_once_with('found an unprocessed <bream> element')



#------------------------------------------------------------------------------
class TestAddSlurs(unittest.TestCase):
    '''Tests for addSlurs()'''

    def testUnit1(self):
        '''
        addSlurs(): element with @m21SlurStart is handled correctly
        '''
        theUUID = 'ae0b1570-451f-4ee9-a136-2094e26a797b'
        elem = ETree.Element('note', attrib={'m21SlurStart': theUUID,
                                             'm21SlurEnd': None,
                                             'slur': None})
        slurBundle = mock.MagicMock('slur bundle')
        mockNewSlur = mock.MagicMock('mock slur')
        mockNewSlur.addSpannedElements = mock.MagicMock()
        slurBundle.getByIdLocal = mock.MagicMock(return_value=[mockNewSlur])
        obj = mock.MagicMock('object')
        expected = True

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)
        slurBundle.getByIdLocal.assert_called_once_with(theUUID)
        mockNewSlur.addSpannedElements.assert_called_once_with(obj)

    def testIntegration1(self):
        '''
        addSlurs(): element with @m21SlurStart is handled correctly
        '''
        theUUID = 'ae0b1570-451f-4ee9-a136-2094e26a797b'
        elem = ETree.Element('note', attrib={'m21SlurStart': theUUID,
                                             'm21SlurEnd': None,
                                             'slur': None})
        slurBundle = spanner.SpannerBundle()
        theSlur = spanner.Slur()
        theSlur.idLocal = theUUID
        slurBundle.append(theSlur)
        obj = note.Note('E-7', quarterLength=2.0)
        expected = True

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)
        self.assertSequenceEqual([theSlur], slurBundle.list)
        self.assertSequenceEqual([obj], slurBundle.list[0].getSpannedElements())

    def testUnit2(self):
        '''
        addSlurs(): element with @m21SlurEnd is handled correctly
        '''
        theUUID = 'ae0b1570-451f-4ee9-a136-2094e26a797b'
        elem = ETree.Element('note', attrib={'m21SlurStart': None,
                                             'm21SlurEnd': theUUID,
                                             'slur': None})
        slurBundle = mock.MagicMock('slur bundle')
        mockNewSlur = mock.MagicMock('mock slur')
        mockNewSlur.addSpannedElements = mock.MagicMock()
        slurBundle.getByIdLocal = mock.MagicMock(return_value=[mockNewSlur])
        obj = mock.MagicMock('object')
        expected = True

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)
        slurBundle.getByIdLocal.assert_called_once_with(theUUID)
        mockNewSlur.addSpannedElements.assert_called_once_with(obj)

    # NB: skipping testIntegration2() ... if Integration1 and Unit2 work, this probably does too

    @mock.patch('music21.spanner.Slur')
    def testUnit3(self, mockSlur):
        '''
        addSlurs(): element with @slur is handled correctly (both an 'i' and 't' slur)
        '''
        elem = ETree.Element('note', attrib={'m21SlurStart': None,
                                             'm21SlurEnd': None,
                                             'slur': '1i 2t'})
        slurBundle = mock.MagicMock('slur bundle')
        slurBundle.append = mock.MagicMock('slurBundle.append')
        mockSlur.return_value = mock.MagicMock('mock slur')
        mockSlur.return_value.addSpannedElements = mock.MagicMock()
        mockNewSlur = mock.MagicMock('mock new slur')
        mockNewSlur.addSpannedElements = mock.MagicMock()
        slurBundle.getByIdLocal = mock.MagicMock(return_value=[mockNewSlur])
        obj = mock.MagicMock('object')
        expected = True

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)
        slurBundle.append.assert_called_once_with(mockSlur.return_value)
        mockSlur.return_value.addSpannedElements.assert_called_once_with(obj)
        mockSlur.return_value.idLocal = '1'
        slurBundle.getByIdLocal.assert_called_once_with('2')
        mockNewSlur.addSpannedElements.assert_called_once_with(obj)

    def testIntegration3(self):
        '''
        addSlurs(): element with @slur is handled correctly (both an 'i' and 't' slur)
        '''
        elem = ETree.Element('note', attrib={'m21SlurStart': None,
                                             'm21SlurEnd': None,
                                             'slur': '1i 2t'})
        slurBundle = spanner.SpannerBundle()
        theSlur = spanner.Slur()
        theSlur.idLocal = '2'
        slurBundle.append(theSlur)
        obj = note.Note('E-7', quarterLength=2.0)
        expected = True

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)
        self.assertSequenceEqual([theSlur, mock.ANY], slurBundle.list)
        self.assertIsInstance(slurBundle.list[1], spanner.Slur)
        self.assertSequenceEqual([obj], slurBundle.list[0].getSpannedElements())
        self.assertSequenceEqual([obj], slurBundle.list[1].getSpannedElements())

    def testUnit4(self):
        '''
        addSlurs(): nothing was added; all three slur-related attributes missing
        '''
        elem = ETree.Element('note', attrib={'m21SlurStart': None,
                                             'm21SlurEnd': None,
                                             'slur': None})
        slurBundle = mock.MagicMock('slur bundle')
        obj = mock.MagicMock('object')
        expected = False

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)

    def testUnit5(self):
        '''
        addSlurs(): nothing was added; @slur is present, but only "medial" indicators
        '''
        elem = ETree.Element('note', attrib={'m21SlurStart': None,
                                             'm21SlurEnd': None,
                                             'slur': '1m 2m'})
        slurBundle = mock.MagicMock('slur bundle')
        obj = mock.MagicMock('object')
        expected = False

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)

    def testUnit6(self):
        '''
        addSlurs(): nothing was added; when the Slur with id of @m21SlurStart can't be found

        NB: this tests that the inner function works---catching the IndexError
        '''
        elem = ETree.Element('note', attrib={'m21SlurStart': '07f5513a-436a-4247-8a5d-85c10c661920',
                                             'm21SlurEnd': None,
                                             'slur': None})
        slurBundle = mock.MagicMock('slur bundle')
        slurBundle.getByIdLocal = mock.MagicMock(side_effect=IndexError)
        obj = mock.MagicMock('object')
        expected = False

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)

    def testIntegration6(self):
        '''
        addSlurs(): nothing was added; when the Slur with id of @m21SlurStart can't be found

        NB: this tests that the inner function works---catching the IndexError
        '''
        elem = ETree.Element('note', attrib={'m21SlurStart': '07f5513a-436a-4247-8a5d-85c10c661920',
                                             'm21SlurEnd': None,
                                             'slur': None})
        slurBundle = spanner.SpannerBundle()
        obj = note.Note('E-7', quarterLength=2.0)
        expected = False

        actual = main.addSlurs(elem, obj, slurBundle)

        self.assertEqual(expected, actual)
        self.assertSequenceEqual([], slurBundle.list)



#------------------------------------------------------------------------------
class TestBeams(unittest.TestCase):
    '''Tests for beams in all their guises.'''

    def testBeamTogether1(self):
        '''
        beamTogether(): with three mock objects, that their "beams" attributes are set properly
        '''
        someThings = [mock.MagicMock() for _ in range(3)]
        for i in xrange(len(someThings)):
            someThings[i].beams = mock.MagicMock('thing {} beams'.format(i))
            someThings[i].beams.__len__.return_value = 0
            someThings[i].beams.fill = mock.MagicMock()
            someThings[i].beams.setAll = mock.MagicMock()
            someThings[i].duration.type = '16th'
        expectedTypes = ['start', 'continue', 'continue']  # first call with "continue"; corrected later in function

        main.beamTogether(someThings)

        for i in xrange(len(someThings)):
            someThings[i].beams.__len__.assert_called_once_with()
            someThings[i].beams.fill.assert_called_once_with('16th', expectedTypes[i])
        someThings[2].beams.setAll.assert_called_once_with('stop')

    def testBeamTogether2(self):
        '''
        beamTogether(): with four mock objects, the middle two of which already have "beams" set
        '''
        someThings = [mock.MagicMock() for _ in range(4)]
        for i in xrange(len(someThings)):
            someThings[i].beams = mock.MagicMock('thing {} beams'.format(i))
            someThings[i].beams.__len__.return_value = 0
            someThings[i].beams.fill = mock.MagicMock()
            someThings[i].beams.setAll = mock.MagicMock()
            someThings[i].duration.type = '16th'
        expectedTypes = ['start', None, None, 'continue']  # first call with "continue"; corrected later in function
        # modifications for test 2
        someThings[1].beams.__len__.return_value = 2
        someThings[2].beams.__len__.return_value = 2

        main.beamTogether(someThings)

        for i in [0, 3]:
            someThings[i].beams.__len__.assert_called_once_with()
            someThings[i].beams.fill.assert_called_once_with('16th', expectedTypes[i])
        someThings[3].beams.setAll.assert_called_once_with('stop')
        for i in [1, 2]:
            self.assertEqual(0, someThings[i].beams.fill.call_count)
            self.assertEqual(0, someThings[i].beams.setAll.call_count)

    def testBeamTogether3(self):
        '''
        beamTogether(): with four mock objects, one of which doesn't have a "beams" attribute
        '''
        someThings = [mock.MagicMock() for _ in range(4)]
        someThings[2] = 5  # this will cause failure if the function tries to set "beams"
        for i in [0, 1, 3]:
            someThings[i].beams = mock.MagicMock('thing {} beams'.format(i))
            someThings[i].beams.__len__.return_value = 0
            someThings[i].beams.fill = mock.MagicMock()
            someThings[i].beams.setAll = mock.MagicMock()
            someThings[i].duration.type = '16th'
        expectedTypes = ['start', 'continue', None, 'continue']  # first call with "continue"; corrected later in function

        main.beamTogether(someThings)

        for i in [0, 1, 3]:
            someThings[i].beams.__len__.assert_called_once_with()
            someThings[i].beams.fill.assert_called_once_with('16th', expectedTypes[i])
        someThings[3].beams.setAll.assert_called_once_with('stop')



#------------------------------------------------------------------------------
class TestPreprocessors(unittest.TestCase):
    '''Tests for the preprocessing helper functions for convertFromString().'''

    def testUnitTies1(self):
        '''
        _ppTies(): that three ties are specified correctly in the m21Attr
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}tie'.format(mei=_MEINS)
        iterfindReturn = []
        for i in xrange(3):
            iterfindReturn.append(ETree.Element('tie', attrib={'startid': 'start {}'.format(i),
                                                               'endid': 'end {}'.format(i)}))
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppTies(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        for i in xrange(3):
            self.assertEqual('i', m21Attr['start {}'.format(i)]['tie'])
            self.assertEqual('t', m21Attr['end {}'.format(i)]['tie'])

    @mock.patch('music21.mei.__main__.environLocal')
    def testUnitTies2(self, mockEnviron):
        '''
        _ppTies(): <tie> without @startid and @endid is properly announced as failing
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}tie'.format(mei=_MEINS)
        iterfindReturn = [ETree.Element('tie', attrib={'tstamp': '4.1', 'tstamp2': '4.2'})]
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppTies(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        self.assertEqual(0, len(m21Attr))
        mockEnviron.warn.assert_called_once_with('Importing <tie> without @startid and @endid is not yet supported.')

    @mock.patch('music21.spanner.Slur')
    def testUnitSlurs1(self, mockSlur):
        '''
        _ppSlurs(): that three slurs are specified correctly in the m21Attr, and put in the slurBundle
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}slur'.format(mei=_MEINS)
        iterfindReturn = []
        for i in xrange(3):
            iterfindReturn.append(ETree.Element('slur',
                                                attrib={'startid': 'start {}'.format(i),
                                                        'endid': 'end {}'.format(i)}))
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)
        mockSlur.side_effect = lambda: mock.MagicMock('a fake Slur')
        # the "slurBundle" only needs to support append(), so this can serve as our mock object
        slurBundle = []

        actual = main._ppSlurs(documentRoot, m21Attr, slurBundle)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check things in the slurBundle
        expectedIdLocal = []
        self.assertEqual(3, len(slurBundle))
        for eachSlur in slurBundle:
            self.assertIsInstance(eachSlur, mock.MagicMock)
            self.assertEqual(36, len(eachSlur.idLocal))
            expectedIdLocal.append(eachSlur.idLocal)
        # check all the right values were added to the m21Attr dict
        for i in xrange(3):
            self.assertTrue(m21Attr['start {}'.format(i)]['m21SlurStart'] in expectedIdLocal)
            self.assertTrue(m21Attr['end {}'.format(i)]['m21SlurEnd'] in expectedIdLocal)

    @mock.patch('music21.spanner.Slur')
    @mock.patch('music21.mei.__main__.environLocal')
    def testUnitSlurs2(self, mockEnviron, mockSlur):
        '''
        _ppSlurs(): <slur> without @startid and @endid is properly announced as failing
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}slur'.format(mei=_MEINS)
        iterfindReturn = [ETree.Element('slur', attrib={'tstamp': '4.1', 'tstamp2': '4.3'})]
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)
        mockSlur.side_effect = lambda: mock.MagicMock('a fake Slur')
        # the "slurBundle" only needs to support append(), so this can serve as our mock object
        slurBundle = []

        actual = main._ppSlurs(documentRoot, m21Attr, slurBundle)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check things in the slurBundle
        self.assertEqual(0, len(slurBundle))
        # check all the right values were added to the m21Attr dict
        self.assertEqual(0, len(m21Attr))
        mockEnviron.warn.assert_called_once_with('Importing <slur> without @startid and @endid is not yet supported.')

    def testUnitBeams1(self):
        '''
        _ppBeams(): that three beamed notes are specified correctly in the m21Attr

        with @plist
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}beamSpan'.format(mei=_MEINS)
        iterfindReturn = []
        for i in xrange(3):
            iterfindReturn.append(ETree.Element('beamSpan',
                                                attrib={'startid': 'start-{}'.format(i),
                                                        'endid': 'end-{}'.format(i),
                                                        'plist': '#start-{j} #mid-{j} #end-{j}'.format(j=i)}))
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppBeams(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        for i in xrange(3):
            self.assertEqual('start', m21Attr['start-{}'.format(i)]['m21Beam'])
            self.assertEqual('continue', m21Attr['mid-{}'.format(i)]['m21Beam'])
            self.assertEqual('stop', m21Attr['end-{}'.format(i)]['m21Beam'])

    def testUnitBeams2(self):
        '''
        _ppBeams(): that three beamed notes are specified correctly in the m21Attr

        without @plist
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}beamSpan'.format(mei=_MEINS)
        iterfindReturn = []
        for i in xrange(3):
            iterfindReturn.append(ETree.Element('beamSpan',
                                                attrib={'startid': '#start-{}'.format(i),
                                                        'endid': '#end-{}'.format(i)}))
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppBeams(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        for i in xrange(3):
            self.assertEqual('start', m21Attr['start-{}'.format(i)]['m21Beam'])
            self.assertEqual('stop', m21Attr['end-{}'.format(i)]['m21Beam'])

    @mock.patch('music21.mei.__main__.environLocal')
    def testUnitBeams3(self, mockEnviron):
        '''
        _ppBeams(): <beamSpan> without @startid and @endid is properly announced as failing
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}beamSpan'.format(mei=_MEINS)
        iterfindReturn = [ETree.Element('beamSpan', attrib={'tstamp': '12.4', 'tstamp2': '13.1'})]
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppBeams(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        self.assertEqual(0, len(m21Attr))
        mockEnviron.warn.assert_called_once_with('Importing <beamSpan> without @startid and @endid is not yet supported.')

    def testUnitTuplets1(self):
        '''
        _ppTuplets(): that three notes in a tuplet are specified correctly in the m21Attr

        with @plist
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}tupletSpan'.format(mei=_MEINS)
        theNum = 42
        theNumbase = 900
        iterfindReturn = []
        for i in xrange(3):
            iterfindReturn.append(ETree.Element('tupletSpan',
                                                attrib={'plist': '#start-{j} #mid-{j} #end-{j}'.format(j=i),
                                                        'num': theNum,
                                                        'numbase': theNumbase}))
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppTuplets(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        for i in xrange(3):
            self.assertEqual(theNum, m21Attr['start-{}'.format(i)]['m21TupletNum'])
            self.assertEqual(theNumbase, m21Attr['start-{}'.format(i)]['m21TupletNumbase'])
            self.assertEqual(theNum, m21Attr['mid-{}'.format(i)]['m21TupletNum'])
            self.assertEqual(theNumbase, m21Attr['mid-{}'.format(i)]['m21TupletNumbase'])
            self.assertEqual(theNum, m21Attr['end-{}'.format(i)]['m21TupletNum'])
            self.assertEqual(theNumbase, m21Attr['end-{}'.format(i)]['m21TupletNumbase'])

    @mock.patch('music21.mei.__main__.environLocal')
    def testUnitTuplets2(self, mockEnviron):
        '''
        _ppTuplets(): <tupletSpan> without (@startid and @endid) or @plist is properly announced as failing
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}tupletSpan'.format(mei=_MEINS)
        theNum = 42
        theNumbase = 900
        iterfindReturn = [ETree.Element('tupletSpan', attrib={'num': theNum, 'numbase': theNumbase})]
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppTuplets(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        self.assertEqual(0, len(m21Attr))
        mockEnviron.warn.assert_called_once_with('Importing <tupletSpan> without @startid and @endid or @plist is not yet supported.')

    def testUnitTuplets3(self):
        '''
        _ppTuplets(): that three notes in a tuplet are specified correctly in the m21Attr

        without @plist (this should set @m21TupletSearch attributes)
        '''
        # NB: I'm mocking out the documentRoot because setting up an element tree for a unit test
        #     is much more work than it's worth
        m21Attr = defaultdict(lambda: {})
        documentRoot = mock.MagicMock()
        expectedIterfind = './/{mei}music//{mei}score//{mei}tupletSpan'.format(mei=_MEINS)
        theNum = 42
        theNumbase = 900
        iterfindReturn = []
        for i in xrange(3):
            iterfindReturn.append(ETree.Element('tupletSpan',
                                                attrib={'startid': '#start-{j}'.format(j=i),
                                                        'endid': '#end-{j}'.format(j=i),
                                                        'num': theNum,
                                                        'numbase': theNumbase}))
        documentRoot.iterfind = mock.MagicMock(return_value=iterfindReturn)

        actual = main._ppTuplets(documentRoot, m21Attr)

        self.assertTrue(m21Attr is actual)
        documentRoot.iterfind.assert_called_once_with(expectedIterfind)
        # check all the right values were added to the m21Attr dict
        for i in (0, 2):
            self.assertEqual(theNum, m21Attr['start-{}'.format(i)]['m21TupletNum'])
            self.assertEqual(theNumbase, m21Attr['start-{}'.format(i)]['m21TupletNumbase'])
            self.assertEqual('start', m21Attr['start-{}'.format(i)]['m21TupletSearch'])
            self.assertEqual(theNum, m21Attr['end-{}'.format(i)]['m21TupletNum'])
            self.assertEqual(theNumbase, m21Attr['end-{}'.format(i)]['m21TupletNumbase'])
            self.assertEqual('end', m21Attr['end-{}'.format(i)]['m21TupletSearch'])



#------------------------------------------------------------------------------
class TestTuplets(unittest.TestCase):
    '''Tests for the tuplet-processing helper function, scaleToTuplet().'''

    def testTuplets1(self):
        '''
        scaleToTuplet(): with three objects, the "tuplet search" attributes are set properly.
        '''
        objs = [mock.MagicMock(spec=note.Note()) for _ in range(3)]
        elem = ETree.Element('tupletDef', attrib={'m21TupletNum': '12', 'm21TupletNumbase': '400',
                                                  'm21TupletSearch': 'the forest'})

        main.scaleToTuplet(objs, elem)

        for obj in objs:
            self.assertEqual('12', obj.m21TupletNum)
            self.assertEqual('400', obj.m21TupletNumbase)
            self.assertEqual('the forest', obj.m21TupletSearch)

    @mock.patch('music21.duration.Tuplet')
    def testTuplets2(self, mockTuplet):
        '''
        scaleToTuplet(): with three objects, their duration is scaled properly. (With @m21TupletType).
        '''
        objs = [mock.MagicMock(spec=note.Note()) for _ in range(3)]
        for obj in objs:
            obj.duration = mock.MagicMock()
            obj.duration.type = 'duration type'
            obj.duration.tuplets = [mock.MagicMock()]
        elem = ETree.Element('tupletDef', attrib={'m21TupletNum': '12', 'm21TupletNumbase': '400',
                                                  'm21TupletType': 'banana'})
        mockTuplet.return_value = 'a Tuplet'
        expectedCall = mock.call(numberNotesActual=12, durationActual='duration type',
                                 numberNotesNormal=400, durationNormal='duration type')

        main.scaleToTuplet(objs, elem)

        self.assertEqual(3, mockTuplet.call_count)
        for eachCall in mockTuplet.call_args_list:
            self.assertEqual(expectedCall, eachCall)
        for obj in objs:
            self.assertEqual('banana', obj.duration.tuplets[0].type)

    @mock.patch('music21.duration.Tuplet')
    def testTuplets3(self, mockTuplet):
        '''
        scaleToTuplet(): with three objects, their duration is scaled properly. (With @tuplet == 'i1').
        '''
        objs = [mock.MagicMock(spec=note.Note()) for _ in range(3)]
        for obj in objs:
            obj.duration = mock.MagicMock()
            obj.duration.type = 'duration type'
            obj.duration.tuplets = [mock.MagicMock()]
        elem = ETree.Element('tupletDef', attrib={'m21TupletNum': '12', 'm21TupletNumbase': '400',
                                                  'tuplet': 'i1'})
        mockTuplet.return_value = 'a Tuplet'
        expectedCall = mock.call(numberNotesActual=12, durationActual='duration type',
                                 numberNotesNormal=400, durationNormal='duration type')

        main.scaleToTuplet(objs, elem)

        self.assertEqual(3, mockTuplet.call_count)
        for eachCall in mockTuplet.call_args_list:
            self.assertEqual(expectedCall, eachCall)
        for obj in objs:
            self.assertEqual('start', obj.duration.tuplets[0].type)

    @mock.patch('music21.duration.Tuplet')
    def testTuplets4(self, mockTuplet):
        '''
        scaleToTuplet(): with one object, its duration is scaled properly. (With @tuplet == 't1').
        '''
        obj = mock.MagicMock(spec=note.Note())
        obj.duration = mock.MagicMock()
        obj.duration.type = 'duration type'
        obj.duration.tuplets = [mock.MagicMock()]
        elem = ETree.Element('tupletDef', attrib={'m21TupletNum': '12', 'm21TupletNumbase': '400',
                                                  'tuplet': 't1'})
        mockTuplet.return_value = 'a Tuplet'
        expectedCall = mock.call(numberNotesActual=12, durationActual='duration type',
                                 numberNotesNormal=400, durationNormal='duration type')

        main.scaleToTuplet(obj, elem)

        self.assertEqual(1, mockTuplet.call_count)
        self.assertEqual(expectedCall, mockTuplet.call_args_list[0])
        self.assertEqual('stop', obj.duration.tuplets[0].type)

    @mock.patch('music21.duration.Tuplet')
    def testTuplets5(self, mockTuplet):
        '''
        scaleToTuplet(): with three objects, their duration is scaled properly. (One of the objects
        isn't a Note/Chord/Rest).
        '''
        objs = [mock.MagicMock(spec=note.Note()) for _ in range(3)]
        for obj in objs:
            obj.duration = mock.MagicMock()
            obj.duration.type = 'duration type'
            obj.duration.tuplets = [mock.MagicMock()]
        objs[1] = mock.MagicMock(spec=clef.TrebleClef())
        elem = ETree.Element('tupletDef', attrib={'m21TupletNum': '12', 'm21TupletNumbase': '400',
                                                  'tuplet': 'i1'})
        mockTuplet.return_value = 'a Tuplet'
        expectedCall = mock.call(numberNotesActual=12, durationActual='duration type',
                                 numberNotesNormal=400, durationNormal='duration type')

        main.scaleToTuplet(objs, elem)

        self.assertEqual(2, mockTuplet.call_count)
        for eachCall in mockTuplet.call_args_list:
            self.assertEqual(expectedCall, eachCall)
        self.assertEqual('start', objs[0].duration.tuplets[0].type)
        self.assertEqual([], objs[1].duration.call_args_list)
        self.assertEqual('start', objs[2].duration.tuplets[0].type)

    def testTuplets6(self):
        '''
        tupletFromElement(): when either @num or @numbase isn't in the element, raise an
            MeiAttributeError.
        '''
        # missing @numbase
        elem = ETree.Element('tuplet', attrib={'num': '3'})
        self.assertRaises(main.MeiAttributeError, main.tupletFromElement, elem)
        try:
            main.tupletFromElement(elem)
        except main.MeiAttributeError as err:
            self.assertEqual(main._MISSING_TUPLET_DATA, err.args[0])
        # missing @num
        elem = ETree.Element('tuplet', attrib={'numbase': '2'})
        self.assertRaises(main.MeiAttributeError, main.tupletFromElement, elem)
        try:
            main.tupletFromElement(elem)
        except main.MeiAttributeError as err:
            self.assertEqual(main._MISSING_TUPLET_DATA, err.args[0])

    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.scaleToTuplet')
    @mock.patch('music21.mei.__main__.beamTogether')
    def testTuplets7(self, mockBeam, mockTuplet, mockEmbedded):  # pylint: disable=unused-argument
        '''
        tupletFromElement(): everything set properly in a triplet; no extraneous elements
        '''
        elem = ETree.Element('tuplet', attrib={'num': '3', 'numbase': '2'})
        mockNotes = [mock.MagicMock(spec=note.Note()) for _ in range(3)]
        for obj in mockNotes:
            obj.duration.tuplets = [mock.MagicMock(spec=duration.Tuplet())]
            obj.duration.tuplets[0].type = 'default'
        mockTuplet.return_value = mockNotes
        mockBeam.side_effect = lambda x: x

        actual = main.tupletFromElement(elem)

        self.assertSequenceEqual(mockNotes, actual)
        mockBeam.assert_called_once_with(mockNotes)
        self.assertEqual('start', mockNotes[0].duration.tuplets[0].type)
        self.assertEqual('default', mockNotes[1].duration.tuplets[0].type)
        self.assertEqual('stop', mockNotes[2].duration.tuplets[0].type)

    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.scaleToTuplet')
    @mock.patch('music21.mei.__main__.beamTogether')
    def testTuplets8(self, mockBeam, mockTuplet, mockEmbedded):  # pylint: disable=unused-argument
        '''
        tupletFromElement(): everything set properly in a triplet; extraneous elements interposed
        '''
        # NB: elements 0, 3, and 5 are the Notes; elements 1, 2, and 4 are not
        elem = ETree.Element('tuplet', attrib={'num': '3', 'numbase': '2'})
        mockNotes = [mock.MagicMock(spec=note.Note()) for _ in range(6)]
        for obj in mockNotes:
            obj.duration.tuplets = [mock.MagicMock(spec=duration.Tuplet())]
            obj.duration.tuplets[0].type = 'default'
        for i in (1, 2, 4):
            mockNotes[i] = mock.MagicMock(spec=clef.TrebleClef())
        mockTuplet.return_value = mockNotes
        mockBeam.side_effect = lambda x: x

        actual = main.tupletFromElement(elem)

        self.assertSequenceEqual(mockNotes, actual)
        mockBeam.assert_called_once_with(mockNotes)
        self.assertEqual('start', mockNotes[0].duration.tuplets[0].type)
        self.assertEqual('default', mockNotes[3].duration.tuplets[0].type)
        self.assertEqual('stop', mockNotes[5].duration.tuplets[0].type)

    @mock.patch('music21.mei.__main__._processEmbeddedElements')
    @mock.patch('music21.mei.__main__.scaleToTuplet')
    @mock.patch('music21.mei.__main__.beamTogether')
    def testTuplets9(self, mockBeam, mockTuplet, mockEmbedded):  # pylint: disable=unused-argument
        '''
        tupletFromElement(): everything set properly in a triplet; extraneous elements interposed,
            prepended, and appended
        '''
        # NB: elements 1, 4, and 6 are the Notes; elements 0, 2, 3, 5, and 7 are not
        elem = ETree.Element('tuplet', attrib={'num': '3', 'numbase': '2'})
        mockNotes = [mock.MagicMock(spec=note.Note()) for _ in range(8)]
        for obj in mockNotes:
            obj.duration.tuplets = [mock.MagicMock(spec=duration.Tuplet())]
            obj.duration.tuplets[0].type = 'default'
        for i in (0, 2, 3, 5, 7):
            mockNotes[i] = mock.MagicMock(spec=clef.TrebleClef())
        mockTuplet.return_value = mockNotes
        mockBeam.side_effect = lambda x: x

        actual = main.tupletFromElement(elem)

        self.assertSequenceEqual(mockNotes, actual)
        mockBeam.assert_called_once_with(mockNotes)
        self.assertEqual('start', mockNotes[1].duration.tuplets[0].type)
        self.assertEqual('default', mockNotes[4].duration.tuplets[0].type)
        self.assertEqual('stop', mockNotes[6].duration.tuplets[0].type)

    def testTuplets10(self):
        '''
        _postGuessTuplets(): integration test that a single-part Score with one triplet is guessed
        '''
        # setup the Voice with tuplets
        theVoice = stream.Voice()
        for _ in range(3):
            eachNote = note.Note('D-5', quarterLength=0.5)
            theVoice.append(eachNote)
        theVoice[0].m21TupletSearch = 'start'
        theVoice[0].m21TupletNum = '3'
        theVoice[0].m21TupletNumbase = '2'
        theVoice[2].m21TupletSearch = 'stop'
        theVoice[2].m21TupletNum = '3'
        theVoice[2].m21TupletNumbase = '2'
        # setup the Score->Part->Measure->Voice hierarchy
        theMeasure = stream.Measure([theVoice])
        thePart = stream.Part([theMeasure])
        theScore = stream.Score(givenElements=[thePart])
        # make the expected values
        expectedOffsets = [0.0, Fraction(1, 3), Fraction(2, 3)]

        actual = main._postGuessTuplets(theScore)

        # the checking stage is simple for this score
        for i in range(3):
            self.assertEqual(expectedOffsets[i], actual[0][0][0][i].offset)
            self.assertEqual(Fraction(1, 3), actual[0][0][0][i].duration.quarterLength)
