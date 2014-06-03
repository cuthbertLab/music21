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

from music21.ext import six

import unittest
if six.PY2:
    import mock
else:
    from unittest import mock  # pylint: disable=no-name-in-module

# Determine which ElementTree implementation to use.
# We'll prefer the C-based versions if available, since they provide better performance.
try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree



class TestThings(unittest.TestCase):
    'Tests for utility functions.'

    def testSafePitch1(self):
        'safePitch(): when ``name`` is a valid pitch name'
        name = 'D#6'
        expected = pitch.Pitch('D#6')
        actual = safePitch(name)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testSafePitch2(self):
        'safePitch(): when ``name`` is not a valid pitch name'
        name = ''
        expected = pitch.Pitch()
        actual = safePitch(name)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testMakeDuration(self):
        'makeDuration(): just a couple of things'
        self.assertEqual(2.0, makeDuration(2.0, 0).quarterLength)
        self.assertEqual(3.0, makeDuration(2.0, 1).quarterLength)
        self.assertEqual(3.5, makeDuration(2, 2).quarterLength) # "base" as int---should work
        self.assertEqual(3.999998092651367, makeDuration(2.0, 20).quarterLength)



#------------------------------------------------------------------------------
class TestAttrTranslators(unittest.TestCase):
    '''Tests for the one-to-one (string-to-simple-datatype) converter functions.'''

    def testAttrTranslator1(self):
        '''_attrTranslator(): the usual case works properly when "attr" is in "mapping"'''
        attr = 'two'
        name = 'numbers'
        mapping = {'one': 1, 'two': 2, 'three': 3}
        expected = 2
        actual = _attrTranslator(attr, name, mapping)
        self.assertEqual(expected, actual)

    def testAttrTranslator2(self):
        '''_attrTranslator(): exception is raised properly when "attr" isn't found'''
        attr = 'four'
        name = 'numbers'
        mapping = {'one': 1, 'two': 2, 'three': 3}
        expected = 'Unexpected value for "numbers" attribute: four'
        self.assertRaises(MeiValueError, _attrTranslator, attr, name, mapping)
        try:
            _attrTranslator(attr, name, mapping)
        except MeiValueError as mvErr:
            self.assertEqual(expected, mvErr.message)

    @mock.patch('__main__._attrTranslator')
    def testAccidental(self, mockTrans):
        '''_accidentalFromAttr(): ensure proper arguments to _attrTranslator'''
        attr = 's'
        _accidentalFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'accid', _ACCID_ATTR_DICT)

    @mock.patch('__main__._attrTranslator')
    def testDuration(self, mockTrans):
        '''_qlDurationFromAttr(): ensure proper arguments to _attrTranslator'''
        attr = 's'
        _qlDurationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'dur', _DUR_ATTR_DICT)

    @mock.patch('__main__._attrTranslator')
    def testArticulation1(self, mockTrans):
        '''_articulationFromAttr(): ensure proper arguments to _attrTranslator'''
        attr = 'marc'
        mockTrans.return_value = 5
        expected = (5,)
        actual = _articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._attrTranslator')
    def testArticulation2(self, mockTrans):
        '''_articulationFromAttr(): proper handling of "marc-stacc"'''
        attr = 'marc-stacc'
        mockTrans.side_effect = MeiValueError()
        expected = (articulations.StrongAccent, articulations.Staccato)
        actual = _articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._attrTranslator')
    def testArticulation3(self, mockTrans):
        '''_articulationFromAttr(): proper handling of "ten-stacc"'''
        attr = 'ten-stacc'
        mockTrans.side_effect = MeiValueError()
        expected = (articulations.Tenuto, articulations.Staccato)
        actual = _articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._attrTranslator')
    def testArticulation4(self, mockTrans):
        '''_articulationFromAttr(): proper handling of not-found'''
        attr = 'garbage'
        expected = 'error message'
        mockTrans.side_effect = MeiValueError(expected)
        self.assertRaises(MeiValueError, _articulationFromAttr, attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        try:
            _articulationFromAttr(attr)
        except MeiValueError as mvErr:
            self.assertEqual(expected, mvErr.message)

    @mock.patch('__main__._articulationFromAttr')
    def testArticList1(self, mockArtic):
        '''_makeArticList(): properly handles single-articulation lists'''
        attr = 'acc'
        mockArtic.return_value = ['accent']
        expected = ['accent']
        actual = _makeArticList(attr)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._articulationFromAttr')
    def testArticList2(self, mockArtic):
        '''_makeArticList(): properly handles multi-articulation lists'''
        attr = 'acc stacc marc'
        mockReturns = [['accent'], ['staccato'], ['marcato']]
        mockArtic.side_effect = lambda x: mockReturns.pop(0)
        expected = ['accent', 'staccato', 'marcato']
        actual = _makeArticList(attr)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._articulationFromAttr')
    def testArticList3(self, mockArtic):
        '''_makeArticList(): properly handles the compound articulations'''
        attr = 'acc marc-stacc marc'
        mockReturns = [['accent'], ['marcato', 'staccato'], ['marcato']]
        mockArtic.side_effect = lambda *x: mockReturns.pop(0)
        expected = ['accent', 'marcato', 'staccato', 'marcato']
        actual = _makeArticList(attr)
        self.assertEqual(expected, actual)



#------------------------------------------------------------------------------
class TestNoteFromElement(unittest.TestCase):
    '''Tests for noteFromElement()'''

    @mock.patch('music21.note.Note')
    def testUnit1(self, mockNote):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'id', 'pname', 'accid', 'oct', 'dur', 'dots'
        (mostly-unit test; only mock out Note and the ElementTree.Element)
        '''
        elem = mock.MagicMock()
        expectedElemOrder = [mock.call('pname', ''), mock.call('accid'), mock.call('oct', ''),
                             mock.call('dur'), mock.call('dots', 0)]
        expectedElemOrder.extend([mock.ANY for _ in xrange(1)])  # additional calls to elem.get(), not part of this test
        elemReturns = ['D', 's', '2', '4', '1']
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        mockNote.return_value = mock.MagicMock(spec_set=note.Note, name='note return')
        expected = mockNote.return_value
        actual = noteFromElement(elem)
        self.assertEqual(expected, actual)
        mockNote.assert_called_once_with(pitch.Pitch('D#2'), duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)

    def testIntegration1(self):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'id', 'pname', 'accid', 'oct', 'dur', 'dots'
        (corresponds to testUnit1() with real Note and real ElementTree.Element)
        '''
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4', 'dots': '1'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = noteFromElement(elem)
        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)

    def testIntegration2(self):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'id', 'pname', 'accid', 'oct', 'dur', 'dots'
        (this has different arguments than testIntegration2())
        '''
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 'n', 'oct': '2', 'dur': '4'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = noteFromElement(elem)
        self.assertEqual('D2', actual.nameWithOctave)
        self.assertEqual(1.0, actual.quarterLength)
        self.assertEqual(0, actual.duration.dots)

    @mock.patch('music21.note.Note')
    def testUnit2(self, mockNote):
        '''
        noteFromElement(): all the elements that go in Note.__init__()...
                           'id', 'pname', 'accid', 'oct', 'dur', 'dots'
        (mostly-unit test; only mock out Note and the ElementTree.Element)
        '''
        elem = mock.MagicMock()
        expectedElemOrder = [mock.ANY for _ in xrange(5)]  # not testing the calls from testUnit1()
        expectedElemOrder.extend([mock.call('id'), mock.call('id')])
        expectedId = 42
        elemReturns = ['D', 's', '2', '4', '1',  # copied from testUnit1()---not important in this test
                       expectedId, expectedId]  # xml:id for this test
        elem.get.side_effect = lambda *x: elemReturns.pop(0) if len(elemReturns) > 0 else None
        # NB: this can't use 'spec_set' because the "id" attribute is part of Music21Object, note Note
        mockNote.return_value = mock.MagicMock(spec=note.Note, name='note return')
        expected = mockNote.return_value
        actual = noteFromElement(elem)
        self.assertEqual(expected, actual)
        mockNote.assert_called_once_with(pitch.Pitch('D#2'), duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)
        self.assertEqual(expectedId, actual.id)
