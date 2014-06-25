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

from music21 import pitch
from music21 import note
from music21 import duration
from music21 import articulations
from music21 import chord
from music21 import clef
from music21 import stream

# Importing from __main__.py
import music21.mei.__main__ as main
from music21.mei.__main__ import _XMLID



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

    def testMakeDuration(self):
        '''makeDuration(): just a couple of things'''
        self.assertEqual(2.0, main.makeDuration(2.0, 0).quarterLength)
        self.assertEqual(3.0, main.makeDuration(2.0, 1).quarterLength)
        self.assertEqual(3.5, main.makeDuration(2, 2).quarterLength) # "base" as int---should work
        self.assertEqual(3.999998092651367, main.makeDuration(2.0, 20).quarterLength)

    def testAllPartsPresent1(self):
        '''allPartsPresent(): one <staffDef>, no repeats'''
        inputValue = [mock.MagicMock(spec_set=ETree.Element('staffDef'))]
        inputValue[0].get = mock.MagicMock(return_value='1')
        expected = ['1']
        actual = main.allPartsPresent(inputValue)
        self.assertSequenceEqual(expected, actual)

    def testAllPartsPresent2(self):
        '''allPartsPresent(): four <staffDef>s'''
        inputValue = [mock.MagicMock(spec_set=ETree.Element('staffDef')) for _ in xrange(4)]
        for i in xrange(4):
            inputValue[i].get = mock.MagicMock(return_value=str(i + 1))
        expected = list('1234')
        actual = main.allPartsPresent(inputValue)
        self.assertSequenceEqual(expected, actual)

    def testAllPartsPresent3(self):
        '''allPartsPresent(): four unique <staffDef>s, several repeats'''
        inputValue = [mock.MagicMock(spec_set=ETree.Element('staffDef')) for _ in xrange(12)]
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
            self.assertEqual(main._SEEMINGLY_NO_PARTS, mvErr.message)


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
            self.assertEqual(expected, mvErr.message)

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
        mockTrans.return_value = 5
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
        self.assertEqual(expected, actual)

    @mock.patch('music21.mei.__main__._attrTranslator')
    def testArticulation3(self, mockTrans):
        '''_articulationFromAttr(): proper handling of "ten-stacc"'''
        attr = 'ten-stacc'
        expected = (articulations.Tenuto, articulations.Staccato)
        actual = main._articulationFromAttr(attr)
        self.assertEqual(0, mockTrans.call_count)
        self.assertEqual(expected, actual)

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
            self.assertEqual(expected, mvErr.message)

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



#------------------------------------------------------------------------------
class TestNoteFromElement(unittest.TestCase):
    '''Tests for noteFromElement()'''
    # NOTE: in this function's integration tests, the Element.tag attribute doesn't actually matter

    @mock.patch('music21.note.Note')
    def testUnit1(self, mockNote):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'pname', 'accid', 'oct', 'dur', 'dots'
        (mostly-unit test; only mock out Note and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedElemOrder = [mock.call('pname', ''), mock.call('accid'), mock.call('oct', ''),
                             mock.call('dur'), mock.call('dots', 0)]
        expectedElemOrder.extend([mock.ANY for _ in xrange(2)])  # additional calls to elem.get(), not part of this test
        elemReturns = ['D', 's', '2', '4', '1']
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        mockNote.return_value = mock.MagicMock(spec_set=note.Note, name='note return')
        expected = mockNote.return_value
        actual = main.noteFromElement(elem)
        self.assertEqual(expected, actual)
        mockNote.assert_called_once_with(pitch.Pitch('D#2'), duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)

    def testIntegration1a(self):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'pname', 'accid', 'oct', 'dur', 'dots'
        (corresponds to testUnit1() with real Note and real ElementTree.Element)
        '''
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4', 'dots': '1'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.noteFromElement(elem)
        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)

    def testIntegration1b(self):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'pname', 'accid', 'oct', 'dur', 'dots'
        (this has different arguments than testIntegration2())
        '''
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 'n', 'oct': '2', 'dur': '4'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.noteFromElement(elem)
        self.assertEqual('D2', actual.nameWithOctave)
        self.assertEqual(1.0, actual.quarterLength)
        self.assertEqual(0, actual.duration.dots)

    @mock.patch('music21.note.Note')
    def testUnit2(self, mockNote):
        '''
        noteFromElement(): adds "id"
        (mostly-unit test; only mock out Note and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedElemOrder = [mock.ANY for _ in xrange(5)]  # not testing the calls from previous unit tests
        expectedElemOrder.extend([mock.call(_XMLID), mock.call(_XMLID)])
        expectedElemOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        expectedId = 42
        elemReturns = ['D', 's', '2', '4', '1',  # copied from testUnit1()---not important in this test
                       expectedId, expectedId]  # xml:id for this test
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        # NB: this can't use 'spec_set' because the "id" attribute is part of Music21Object, note Note
        mockNote.return_value = mock.MagicMock(spec=note.Note, name='note return')
        expected = mockNote.return_value
        actual = main.noteFromElement(elem)
        self.assertEqual(expected, actual)
        mockNote.assert_called_once_with(pitch.Pitch('D#2'), duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)
        self.assertEqual(expectedId, actual.id)

    def testIntegration2(self):
        '''
        noteFromElement(): adds "id"
        (corresponds to testUnit2() with real Note and real ElementTree.Element)
        '''
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4', 'dots': '1', _XMLID: 42}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.noteFromElement(elem)
        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)
        self.assertEqual(42, actual.id)

    @mock.patch('music21.note.Note')
    def testUnit3(self, mockNote):
        '''
        noteFromElement(): adds "artic"
        (mostly-unit test; only mock out Note and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedElemOrder = [mock.ANY for _ in xrange(6)]  # not testing the calls from previous unit tests
        expectedElemOrder.extend([mock.call('artic'), mock.call('artic')])
        elemArtic = 'stacc'
        elemReturns = ['D', 's', '2', '4', '1',  # copied from testUnit1()---not important in this test
                       None,  # the xml:id attribute
                       elemArtic, elemArtic]  # value of "artic", for this test
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        mockNote.return_value = mock.MagicMock(spec=note.Note, name='note return')
        expected = mockNote.return_value
        actual = main.noteFromElement(elem)
        self.assertEqual(expected, actual)
        mockNote.assert_called_once_with(pitch.Pitch('D#2'), duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)
        self.assertSequenceEqual([articulations.Staccato], actual.articulations)

    def testIntegration3(self):
        '''
        noteFromElement(): adds "artic"
        (corresponds to testUnit2() with real Note and real ElementTree.Element)
        '''
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4', 'dots': '1', 'artic': 'stacc'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.noteFromElement(elem)
        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)
        self.assertEqual([articulations.Staccato], actual.articulations)


#------------------------------------------------------------------------------
class TestRestFromElement(unittest.TestCase):
    '''Tests for restFromElement()'''
    # NOTE: in this function's integration tests, the Element.tag attribute doesn't actually matter

    @mock.patch('music21.note.Rest')
    def testUnit1(self, mockRest):
        '''
        restFromElement(): all the elements that go in Rest.__init__()...
                           'dur', 'dots'
        (mostly-unit test; only mock out Rest and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedElemOrder = [mock.call('dur'), mock.call('dots', 0)]
        expectedElemOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemReturns = ['4', '1']
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        mockRest.return_value = mock.MagicMock(spec_set=note.Rest, name='rest return')
        expected = mockRest.return_value
        actual = main.restFromElement(elem)
        self.assertEqual(expected, actual)
        mockRest.assert_called_once_with(duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)

    def testIntegration1a(self):
        '''
        restFromElement(): all the elements that go in Rest.__init__()...
                           'dur', 'dots'
        (corresponds to testUnit1() with real Rest and real ElementTree.Element)
        '''
        elem = ETree.Element('rest')
        attribDict = {'dur': '4', 'dots': '1'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.restFromElement(elem)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)

    def testIntegration1b(self):
        '''
        restFromElement(): all the elements that go in Rest.__init__()...
                           'dur', 'dots'
        (this has different arguments than testIntegration2())
        '''
        elem = ETree.Element('note')
        attribDict = {'dur': '4'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.restFromElement(elem)
        self.assertEqual(1.0, actual.quarterLength)
        self.assertEqual(0, actual.duration.dots)

    @mock.patch('music21.note.Rest')
    def testUnit2(self, mockRest):
        '''
        restFromElement(): adds the "id" attribute
        (mostly-unit test; only mock out Rest and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedElemOrder = [mock.ANY for _ in xrange(2)]  # not testing the calls from previous unit tests
        expectedElemOrder.extend([mock.call(_XMLID), mock.call(_XMLID)])
        expectedId = 42
        elemReturns = ['4', '1',  # copied from testUnit1()---not important in this test
                       expectedId, expectedId]  # xml:id for this test
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        # NB: this can't use 'spec_set' because the "id" attribute is part of Music21Object, note.Rest
        mockRest.return_value = mock.MagicMock(spec=note.Rest, name='rest return')
        expected = mockRest.return_value
        actual = main.restFromElement(elem)
        self.assertEqual(expected, actual)
        mockRest.assert_called_once_with(duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)
        self.assertEqual(expectedId, actual.id)

    def testIntegration2(self):
        '''
        restFromElement(): adds the "id" attribute
        (corresponds to testUnit2() with real Rest and real ElementTree.Element)
        '''
        elem = ETree.Element('rest')
        attribDict = {'dur': '4', 'dots': '1', _XMLID: 42}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = main.restFromElement(elem)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)
        self.assertEqual(42, actual.id)



#------------------------------------------------------------------------------
class TestChordFromElement(unittest.TestCase):
    '''Tests for chordFromElement()'''
    # NOTE: in this function's integration tests, the Element.tag attribute doesn't actually matter

    @staticmethod
    def makeNoteTags(pname, accid, octArg, dur, dots):
        '''Factory function for the Element objects that are a <note>.'''
        return ETree.Element('note', pname=pname, accid=accid, oct=octArg, dur=dur, dots=dots)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__.noteFromElement')
    def testUnit1(self, mockNoteFromElement, mockChord):
        '''
        chordFromElement(): all the elements that go in Chord.__init__()...
                            'dur', 'dots', and some note.Note objects.
        (mostly-unit test; only mock out Chord, noteFromElement, and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.call('dur'), mock.call('dots', 0)]
        expectedGetOrder.extend([mock.ANY for _ in xrange(2)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['4', '1']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        elem.iterfind = mock.MagicMock(return_value=['root', 'third', 'fifth'])
        mockChord.return_value = mock.MagicMock(spec=chord.Chord, name='chord return')
        mockNoteFromElement.side_effect = lambda x: x  # noteFromElement() returns its input
        expectedNotes = ['root', 'third', 'fifth']
        expected = mockChord.return_value

        actual = main.chordFromElement(elem)

        self.assertEqual(expected, actual)
        elem.iterfind.assert_called_once_with('note')
        mockChord.assert_called_once_with(notes=expectedNotes)
        self.assertEqual(mockChord.return_value.duration, duration.Duration(1.5))
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)

    def testIntegration1(self):
        '''
        chordFromElement(): all the elements that go in Chord.__init__()...
                            'dur', 'dots', and some note.Note objects.
        (corresponds to testUnit1() with real Note, Chord, and ElementTree.Element)
        '''
        chordElem = ETree.Element('chord')
        chordAttribs = {'dur': '4', 'dots': '1'}
        for key in chordAttribs:
            chordElem.set(key, chordAttribs[key])
        for eachPitch in [('C', 's', '2'), ('D', 'f', '2'), ('F', 'ss', '3')]:
            chordElem.append(TestChordFromElement.makeNoteTags(eachPitch[0], eachPitch[1], eachPitch[2], '4', '1'))
        expectedPitches = [pitch.Pitch(x) for x in ('C#2', 'D-2', 'F##3')]
        expectedQuarterLength = 1.5
        expectedDots = 1

        actual = main.chordFromElement(chordElem)

        self.assertEqual(expectedQuarterLength, actual.duration.quarterLength)
        self.assertEqual(expectedDots, actual.duration.dots)
        self.assertSequenceEqual(expectedPitches, actual.pitches)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__.noteFromElement')
    def testUnit2(self, mockNoteFromElement, mockChord):
        '''
        chordFromElement(): adds "id"
        (mostly-unit test; only mock out Chord, noteFromElement, and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.ANY for _ in xrange(2)]  # additional calls to elem.get(), not part of this test
        expectedGetOrder.extend([mock.call(_XMLID), mock.call(_XMLID)])
        expectedGetOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['4', '1', '42', '42']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        elem.iterfind = mock.MagicMock(return_value=['root', 'third', 'fifth'])
        mockChord.return_value = mock.MagicMock(spec=chord.Chord, name='chord return')
        mockNoteFromElement.side_effect = lambda x: x  # noteFromElement() returns its input
        expectedNotes = ['root', 'third', 'fifth']
        expected = mockChord.return_value

        actual = main.chordFromElement(elem)

        self.assertEqual(expected, actual)
        elem.iterfind.assert_called_once_with('note')
        mockChord.assert_called_once_with(notes=expectedNotes)
        self.assertEqual(duration.Duration(1.5), actual.duration)
        self.assertEqual('42', actual.id)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)

    def testIntegration2(self):
        '''
        chordFromElement(): adds "id"
        (corresponds to testUnit2() with real Note, Chord, and ElementTree.Element)
        '''
        chordElem = ETree.Element('chord')
        chordAttribs = {'dur': '4', 'dots': '1', _XMLID: 'bef1f18a'}
        for key in chordAttribs:
            chordElem.set(key, chordAttribs[key])
        for eachPitch in [('C', 's', '2'), ('D', 'f', '2'), ('F', 'ss', '3')]:
            chordElem.append(TestChordFromElement.makeNoteTags(eachPitch[0], eachPitch[1], eachPitch[2], '4', '1'))
        expectedPitches = [pitch.Pitch(x) for x in ('C#2', 'D-2', 'F##3')]
        expectedQuarterLength = 1.5
        expectedDots = 1

        actual = main.chordFromElement(chordElem)

        self.assertEqual(chordAttribs[_XMLID], actual.id)

    @mock.patch('music21.chord.Chord')
    @mock.patch('music21.mei.__main__.noteFromElement')
    def testUnit3(self, mockNoteFromElement, mockChord):
        '''
        chordFromElement(): adds "artic"
        (mostly-unit test; only mock out Chord, noteFromElement, and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.ANY for _ in xrange(3)]  # additional calls to elem.get(), not part of this test
        expectedGetOrder.extend([mock.call('artic'), mock.call('artic')])
        expectedGetOrder.extend([mock.ANY for _ in xrange(0)])  # additional calls to elem.get(), not part of this test
        elemArtic = 'stacc'
        elemGetReturns = ['4', '1', None, elemArtic, elemArtic]
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        elem.iterfind = mock.MagicMock(return_value=['root', 'third', 'fifth'])
        mockChord.return_value = mock.MagicMock(spec=chord.Chord, name='chord return')
        mockNoteFromElement.side_effect = lambda x: x  # noteFromElement() returns its input
        expectedNotes = ['root', 'third', 'fifth']
        expected = mockChord.return_value

        actual = main.chordFromElement(elem)

        self.assertEqual(expected, actual)
        elem.iterfind.assert_called_once_with('note')
        mockChord.assert_called_once_with(notes=expectedNotes)
        self.assertEqual(duration.Duration(1.5), actual.duration)
        self.assertEqual([articulations.Staccato], actual.articulations)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)

    def testIntegration3(self):
        '''
        chordFromElement(): adds "artic"
        (corresponds to testUnit2() with real Note, Chord, and ElementTree.Element)
        '''
        chordElem = ETree.Element('chord')
        chordAttribs = {'dur': '4', 'dots': '1', 'artic': 'stacc'}
        for key in chordAttribs:
            chordElem.set(key, chordAttribs[key])
        for eachPitch in [('C', 's', '2'), ('D', 'f', '2'), ('F', 'ss', '3')]:
            chordElem.append(TestChordFromElement.makeNoteTags(eachPitch[0], eachPitch[1], eachPitch[2], '4', '1'))
        expectedPitches = [pitch.Pitch(x) for x in ('C#2', 'D-2', 'F##3')]
        expectedQuarterLength = 1.5
        expectedDots = 1

        actual = main.chordFromElement(chordElem)

        self.assertEqual([articulations.Staccato], actual.articulations)



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
                           'clefshape', 'line', 'dis', and 'dis.place'
        (mostly-unit test; only mock out clef and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.call('clefshape'), mock.call('clefshape'), mock.call('clefshape'),
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
        clefFromElement(): same as testUnit1a() but with 'perc' "clefshape"
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.call('clefshape')]
        expectedGetOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['perc']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockPercClef.return_value = mock.MagicMock(name='PercussionClef()')
        expected = mockClefFromString.return_value

        actual = main.clefFromElement(elem)

        self.assertEqual(0, mockClefFromString.call_count)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)
        self.assertEqual(0, mockTabClef.call_count)
        self.assertEqual(1, mockPercClef.call_count)

    @mock.patch('music21.clef.clefFromString')
    @mock.patch('music21.clef.PercussionClef')
    @mock.patch('music21.clef.TabClef')
    def testUnit1c(self, mockTabClef, mockPercClef, mockClefFromString):
        '''
        clefFromElement(): same as testUnit1c() but with 'TAB' "clefshape"
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.call('clefshape'), mock.call('clefshape')]
        expectedGetOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['TAB', 'TAB']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockPercClef.return_value = mock.MagicMock(name='PercussionClef()')
        expected = mockClefFromString.return_value

        actual = main.clefFromElement(elem)

        self.assertEqual(0, mockClefFromString.call_count)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)
        self.assertEqual(1, mockTabClef.call_count)
        self.assertEqual(0, mockPercClef.call_count)

    def testIntegration1a(self):
        '''
        clefFromElement(): all the elements that go in clef.clefFromString()...
                           'clefshape', 'line', 'dis', and 'dis.place'
        (corresponds to testUnit1a, with real objects)
        '''
        clefElem = ETree.Element('clef')
        clefAttribs = {'clefshape': 'G', 'line': '2', 'dis': '8', 'dis.place': 'above'}
        for key in clefAttribs:
            clefElem.set(key, clefAttribs[key])
        expectedClass = clef.Treble8vaClef

        actual = main.clefFromElement(clefElem)

        self.assertEqual(expectedClass, actual.__class__)

    def testIntegration1b(self):
        '''
        PercussionClef

        (corresponds to testUnit1b, with real objects)
        '''
        clefElem = ETree.Element('clef')
        clefAttribs = {'clefshape': 'perc'}
        for key in clefAttribs:
            clefElem.set(key, clefAttribs[key])
        expectedClass = clef.PercussionClef

        actual = main.clefFromElement(clefElem)

        self.assertEqual(expectedClass, actual.__class__)

    def testIntegration1c(self):
        '''
        TabClef

        (corresponds to testUnit1c, with real objects)
        '''
        clefElem = ETree.Element('clef')
        clefAttribs = {'clefshape': 'TAB'}
        for key in clefAttribs:
            clefElem.set(key, clefAttribs[key])
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
        elem = mock.MagicMock(spec_set=ETree.Element('mock'))
        expectedGetOrder = [mock.call('clefshape'), mock.call(_XMLID), mock.call(_XMLID)]
        expectedGetOrder.extend([mock.ANY for _ in xrange(0)])  # additional calls to elem.get(), not part of this test
        elemGetReturns = ['perc', 'theXMLID', 'theXMLID']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) > 0 else None
        mockPercClef.return_value = mock.MagicMock(name='PercussionClef()')
        expected = mockClefFromString.return_value

        actual = main.clefFromElement(elem)

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
    def testUnit1(self, mockVoice, mockNoteFromElement):
        '''
        layerFromElement(): basic functionality (i.e., that the tag-name-to-converter-function
                            mapping works; that tags not in the mapping are ignored; and that a
                            Voice object is returned. And "xml:id" is set.
        (mostly-unit test; only mock noteFromElement and the ElementTree.Element)
        '''
        elem = mock.MagicMock(spec_set=ETree.Element('layer'))
        elemGetReturns = ['theXMLID', 'theXMLID']
        elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) else None
        expectedGetOrder = [mock.call(_XMLID), mock.call(_XMLID)]
        findallReturn = [mock.MagicMock(spec_set=ETree.Element('note'), name='note1'),
                         mock.MagicMock(spec_set=ETree.Element('imaginary'), name='imaginary'),
                         mock.MagicMock(spec_set=ETree.Element('note'), name='note2')]
        findallReturn[0].tag = 'note'
        findallReturn[1].tag = 'imaginary'
        findallReturn[2].tag = 'note'
        elem.findall = mock.MagicMock(return_value=findallReturn)
        expectedMNFEOrder = [mock.call(findallReturn[0]), mock.call(findallReturn[2])]  # "MNFE" is "mockNoteFromElement"
        mockNFEreturns = ['mockNoteFromElement return 1', 'mockNoteFromElement return 2']
        mockNoteFromElement.side_effect = lambda *x: mockNFEreturns.pop(0)
        mockVoice.return_value = mock.MagicMock(spec_set=stream.Stream(), name='Voice')
        expectedAppendCalls = [mock.call(mockNFEreturns[0]), mock.call(mockNFEreturns[1])]

        actual = main.layerFromElement(elem)

        elem.findall.assert_called_once_with('*')
        self.assertEqual(mockVoice.return_value, actual)
        self.assertSequenceEqual(expectedMNFEOrder, mockNoteFromElement.call_args_list)
        mockVoice.assert_called_once_with()
        self.assertSequenceEqual(expectedAppendCalls, mockVoice.return_value.append.call_args_list)
        self.assertEqual('theXMLID', actual.id)
        self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)

    def testIntegration1(self):
        '''
        layerFromElement(): basic functionality (i.e., that the tag-name-to-converter-function
                            mapping works; that tags not in the mapping are ignored; and that a
                            Voice object is returned. And "xml:id" is set.
        (corresponds to testUnit1() but without mock objects)
        '''
        inputXML = '''<layer id="asdf1234">
                          <note pname="F" oct="2" dur="4" />
                          <note pname="E" oct="2" accid="f" dur="4" />
                          <imaginary awesome="true" />
                      </layer>'''
        elem = ETree.fromstring(inputXML)

        actual = main.layerFromElement(elem)

        self.assertEqual(2, len(actual))
        self.assertEqual(0.0, actual[0].offset)
        self.assertEqual(1.0, actual[1].offset)
        self.assertEqual(1.0, actual[0].quarterLength)
        self.assertEqual(1.0, actual[1].quarterLength)
        self.assertEqual('F2', actual[0].nameWithOctave)
        self.assertEqual('E-2', actual[1].nameWithOctave)
        self.assertEqual('asdf1234', actual.id)



#------------------------------------------------------------------------------
class TestStaffFromElement(unittest.TestCase):
    '''Tests for staffFromElement()'''

    #@mock.patch('music21.mei.__main__.noteFromElement')
    #@mock.patch('music21.stream.Voice')
    #def testUnit1(self, mockVoice, mockNoteFromElement):
        #'''
        #layerFromElement(): basic functionality (i.e., that the tag-name-to-converter-function
                            #mapping works; that tags not in the mapping are ignored; and that a
                            #Voice object is returned. And "xml:id" is set.
        #(mostly-unit test; only mock noteFromElement and the ElementTree.Element)
        #'''
        #elem = mock.MagicMock(spec_set=ETree.Element('layer'))
        #elemGetReturns = ['theXMLID', 'theXMLID']
        #elem.get.side_effect = lambda *x: elemGetReturns.pop(0) if len(elemGetReturns) else None
        #expectedGetOrder = [mock.call(_XMLID), mock.call(_XMLID)]
        #findallReturn = [mock.MagicMock(spec_set=ETree.Element('note'), name='note1'),
                         #mock.MagicMock(spec_set=ETree.Element('imaginary'), name='imaginary'),
                         #mock.MagicMock(spec_set=ETree.Element('note'), name='note2')]
        #findallReturn[0].tag = 'note'
        #findallReturn[1].tag = 'imaginary'
        #findallReturn[2].tag = 'note'
        #elem.findall = mock.MagicMock(return_value=findallReturn)
        #expectedMNFEOrder = [mock.call(findallReturn[0]), mock.call(findallReturn[2])]  # "MNFE" is "mockNoteFromElement"
        #mockNFEreturns = ['mockNoteFromElement return 1', 'mockNoteFromElement return 2']
        #mockNoteFromElement.side_effect = lambda *x: mockNFEreturns.pop(0)
        #mockVoice.return_value = mock.MagicMock(spec_set=stream.Stream(), name='Voice')
        #expectedAppendCalls = [mock.call(mockNFEreturns[0]), mock.call(mockNFEreturns[1])]

        #actual = main.layerFromElement(elem)

        #elem.findall.assert_called_once_with('*')
        #self.assertEqual(mockVoice.return_value, actual)
        #self.assertSequenceEqual(expectedMNFEOrder, mockNoteFromElement.call_args_list)
        #mockVoice.assert_called_once_with()
        #self.assertSequenceEqual(expectedAppendCalls, mockVoice.return_value.append.call_args_list)
        #self.assertEqual('theXMLID', actual.id)
        #self.assertSequenceEqual(expectedGetOrder, elem.get.call_args_list)

    #def testIntegration1(self):
        #'''
        #layerFromElement(): basic functionality (i.e., that the tag-name-to-converter-function
                            #mapping works; that tags not in the mapping are ignored; and that a
                            #Voice object is returned. And "xml:id" is set.
        #(corresponds to testUnit1() but without mock objects)
        #'''
        #inputXML = '''<layer id="asdf1234">
                          #<note pname="F" oct="2" dur="4" />
                          #<note pname="E" oct="2" accid="f" dur="4" />
                          #<imaginary awesome="true" />
                      #</layer>'''
        #elem = ETree.fromstring(inputXML)

        #actual = main.layerFromElement(elem)

        #self.assertEqual(2, len(actual))
        #self.assertEqual(0.0, actual[0].offset)
        #self.assertEqual(1.0, actual[1].offset)
        #self.assertEqual(1.0, actual[0].quarterLength)
        #self.assertEqual(1.0, actual[1].quarterLength)
        #self.assertEqual('F2', actual[0].nameWithOctave)
        #self.assertEqual('E-2', actual[1].nameWithOctave)
        #self.assertEqual('asdf1234', actual.id)
