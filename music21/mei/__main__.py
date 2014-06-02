# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         mei/__main__.py
# Purpose:      Public methods for the MEI module
#
# Authors:      Christopher Antila
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------
'''
These are the public methods for the MEI module.

To convert a string with MEI markup into music21 objects, use :func:`convertFromString`.
'''

from music21.ext import six

import unittest
if six.PY2:
    import mock
else:
    from unittest import mock

# Determine which ElementTree implementation to use.
# We'll prefer the C-based versions if available, since they provide better performance.
try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree

# music21
from music21 import exceptions21
from music21 import note
from music21 import duration
from music21 import articulations
from music21 import pitch


#------------------------------------------------------------------------------
class MeiValueError(exceptions21.Music21Exception):
    "When an attribute has an invalid value."
    pass

class MeiAttributeError(exceptions21.Music21Exception):
    "When a tag has an invalid attribute."
    pass

class MeiTagError(exceptions21.Music21Exception):
    "When there's an invalid tag."
    pass


# Stuff
#------------------------------------------------------------------------------
def convertFromString(dataStr):
    '''
    Convert a string from MEI markup to music21 objects.

    :parameter str dataStr: A string with MEI markup.
    :returns: A :class:`Stream` subclass, depending on the markup in the ``dataStr``.
    :rtype: :class:`music21.stream.Stream`
    '''
    pass


def safePitch(name):
    '''
    Safely build a :class:`Pitch` from a string.

    When :meth:`Pitch.__init__` is given an empty string, it raises a :exc:`PitchException`. This
    function catches the :exc:`PitchException`, instead returning a :class:`Pitch` instance with
    the music21 default.

    .. note:: Every :exc:`PitchException` is caught---not just those arising from an empty string.
    '''
    try:
        return pitch.Pitch(name)
    except pitch.PitchException:
        return pitch.Pitch()


def makeDuration(base=0.0, dots=0):
    '''
    Given a "base" duration and a number of "dots," create a :class:`Duration` instance with the
    appropriate ``quarterLength`` value.

    **Examples**

    +------+------+-------------------+
    | base | dots | quarterLength     |
    +======+======+===================+
    | 2.0  | 1    | 3.0               |
    +------+------+-------------------+
    | 2.0  | 2    | 3.5               |
    +------+------+-------------------+
    | 1.0  | 1    | 1.5               |
    +------+------+-------------------+
    | 2.0  | 20   | 3.999998092651367 |
    +------+------+-------------------+
    >>>
    '''
    return duration.Duration(base + sum([float(base) / x for x in [2 ** i for i in xrange(1, dots + 1)]]),
                             dots=dots)


# Constants for One-to-One Translation
#------------------------------------------------------------------------------
# for _accidentalFromAttr()
# None is for when @accid is omitted
# TODO: figure out these equivalencies
_ACCID_ATTR_DICT = {'s': '#', 'f': '-', 'ss': '##', 'x': '##', 'ff': '--', 'xs': '###',
                    'ts': '###', 'tf': '---', 'n': '', 'nf': '-', 'ns': '#', 'su': '???',
                    'sd': '???', 'fu': '???', 'fd': '???', 'nu': '???', 'nd': '???', None: ''}

# for _qlDurationFromAttr()
# None is for when @dur is omitted
_DUR_ATTR_DICT = {'long': 16.0, 'breve': 8.0, '1': 4.0, '2': 2.0, '4': 1.0, '8': 0.5, '16': 0.25,
                  '32': 0.125, '64': 0.0625, '128': 0.03125, '256': 0.015625, '512': 0.0078125,
                  '1024': 0.00390625, '2048': 0.001953125, None: 0.0}

# for _articulationFromAttr()
# NOTE: 'marc-stacc' and 'ten-stacc' require multiple music21 events, so they are handled
#       separately in _articulationFromAttr().
_ARTIC_ATTR_DICT = {'acc': articulations.Accent, 'stacc': articulations.Staccato,
                    'ten': articulations.Tenuto, 'stacciss': articulations.Staccatissimo,
                    'marc': articulations.StrongAccent, 'spicc': articulations.Spiccato,
                    'doit': articulations.Doit, 'plop': articulations.Plop,
                    'fall': articulations.Falloff, 'dnbow': articulations.DownBow,
                    'upbow': articulations.UpBow, 'harm': articulations.Harmonic,
                    'snap': articulations.SnapPizzicato, 'stop': articulations.Stopped,
                    'open': articulations.OpenString,  # this may also mean "no mute?"
                    'dbltongue': articulations.DoubleTongue, 'toe': articulations.OrganToe,
                    'trpltongue': articulations.TripleTongue, 'heel': articulations.OrganHeel,
                    # NOTE: these aren't implemented in music21, so I'll make new ones
                    'tap': None, 'lhpizz': None, 'dot': None, 'stroke': None,  'rip': None,
                    'bend': None, 'flip': None, 'smear': None, 'fingernail': None,  # (u1D1B3)
                    'damp': None, 'dampall': None}


# One-to-One Translator Functions
#------------------------------------------------------------------------------
def _attrTranslator(attr, name, mapping):
    '''
    Helper function for other functions that need to translate the value of an attribute to another
    known value. :func:`_attrTranslator` tries to return the value of ``attr`` in ``mapping`` and,
    if ``attr`` isn't in ``mapping``, an exception is raised.

    :param str attr: The value of the attribute to look up in ``mapping``.
    :param str name: Name of the attribute, used when raising an exception (read below).
    :param mapping: A mapping type (nominally a dict) with relevant key-value pairs.

    :raises: :exc:`MeiValueError` when ``attr`` is not found in ``mapping``. The error message will
        be of this format: 'Unexpected value for "name" attribute: attr'.

    Examples:

    >>> from music21.mei.__main__ import _attrTranslator, _ACCID_ATTR_DICT, _DUR_ATTR_DICT
    >>> _attrTranslator('s', 'accid', _ACCID_ATTR_DICT)
    '#'
    >>> _attrTranslator('9', 'dur', _DUR_ATTR_DICT)
    Traceback (most recent call last):
      File "/usr/lib64/python2.7/doctest.py", line 1289, in __run
        compileflags, 1) in test.globs
      File "<doctest __main__._attrTranslator[2]>", line 1, in <module>
        _attrTranslator('9', 'dur', _DUR_ATTR_DICT)
      File "/home/crantila/Documents/DDMAL/programs/music21/music21/mei/__main__.py", line 131, in _attrTranslator
        raise MeiValueError('Unexpected value for "%s" attribute: %s' % (name, attr))
    MeiValueError: Unexpected value for "dur" attribute: 9
    '''
    try:
        return mapping[attr]
    except KeyError:
        raise MeiValueError('Unexpected value for "%s" attribute: %s' % (name, attr))


def _accidentalFromAttr(attr):
    '''
    Use :func:`_attrTranslator` to convert the value of an "accid" attribute to its music21 string.
    '''
    return _attrTranslator(attr, 'accid', _ACCID_ATTR_DICT)


def _qlDurationFromAttr(attr):
    '''
    Use :func:`_attrTranslator` to convert an MEI "dur" attribute to a music21 quarterLength.

    .. note:: This function only handles data.DURATION.cmn, not data.DURATION.mensural.
    '''
    return _attrTranslator(attr, 'dur', _DUR_ATTR_DICT)


def _articulationFromAttr(attr):
    '''
    Use :func:`_attrTranslator` to convert an MEI "artic" attribute to a
    :class:`music21.articulations.Articulation` subclass.

    :returns: A **tuple** of one or two :class:`Articulation` subclasses.

    .. note:: This function returns a singleton tuple *unless* ``attr`` is ``'marc-stacc'`` or
        ``'ten-stacc'``. These return ``(StrongAccent, Staccato)`` and ``(Tenuto, Staccato)``,
        respectively.
    '''
    try:
        post = (_attrTranslator(attr, 'artic', _ARTIC_ATTR_DICT),)
    except MeiValueError as valErr:
        if 'marc-stacc' == attr:
            post = (articulations.StrongAccent, articulations.Staccato)
        elif 'ten-stacc' == attr:
            post = (articulations.Tenuto, articulations.Staccato)
        else:
            raise valErr
    return post


def _makeArticList(attr):
    '''
    Use :func:`_articulationFromAttr` to convert the actual value of an MEI "artic" attribute
    (including multiple items) into a list suitable for :attr:`GeneralNote.articulations`.
    '''
    post = []
    for each_artic in attr.split(' '):
        post.extend(_articulationFromAttr(each_artic))
    return post


#------------------------------------------------------------------------------
def noteFromElement(elem):
    '''
    <note> is a single pitched event.

    In MEI 2013: pg.382 (396 in PDF)

    Attributes Implemented:
    =======================
    - accid, from att.accidental: (via _accidentalFromAttr())
    - pname, from att.pitch: [a--g]
    - oct, from att.octave: [0..9]
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]

    Attributes In Progress:
    =======================
    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - artic, a list from att.articulation: (via _articulationFromAttr())

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.note.log (att.event (att.timestamp.musical (@tstamp))
                            (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                            (att.staffident (@staff))
                            (att.layerident (@layer)))
                 (att.fermatapresent (@fermata))
                 (att.syltext (@syl))
                 (att.slurpresent (@slur))
                 (att.tiepresent (@tie))
                 (att.tupletpresent (@tuplet))
                 (att.note.log.cmn (att.beamed (@beam))
                                   (att.lvpresent (@lv))
                                   (att.ornam (@ornam)))
                 (att.note.log.mensural (@lig))
    att.note.vis (@headshape)
                 (att.altsym (@altsym))
                 (att.color (@color))
                 (att.coloration (@colored))
                 (att.enclosingchars (@enclose))
                 (att.relativesize (@size))
                 (att.staffloc (@loc))
                 (att.stemmed (@stem.dir, @stem.len, @stem.pos, @stem.x, @stem.y)
                              (att.stemmed.cmn (@stem.mod, @stem.with)))
                 (att.visibility (@visible))
                 (att.visualoffset.ho (@ho))
                 (att.visualoffset.to (@to))
                 (att.xy (@x, @y))
                 (att.note.vis.cmn (att.beamsecondary (@breaksec)))
    att.note.ges (@oct.ges, @pname.ges, @pnum)
                 (att.accidental.performed (@accid.ges))
                 (att.articulation.performed (@artic.ges))
                 (att.duration.performed (@dur.ges))
                 (att.instrumentident (@instr))
                 (att.note.ges.cmn (@gliss)
                                   (att.graced (@grace, @grace.time)))
                 (att.note.ges.mensural (att.duration.ratio (@num, @numbase)))
                 (att.note.ges.tablature (@tab.fret, @tab.string))
    att.note.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                 (att.alignment (@when)))
                 (att.harmonicfunction (@deg))
                 (att.intervallicdesc (@intm)
                                      (att.intervalharmonic (@inth)))
                 (att.melodicfunction (@mfunc))
                 (att.pitchclass (@pclass))
                 (att.solfa (@psolfa))

    May Contain:
    ============
    MEI.critapp: app
    MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied unclear
    MEI.lyrics: verse
    MEI.shared: accid artic dot syl
    '''
    # pitch and duration... these are what we can set in the constructor
    post = note.Note(safePitch(''.join((elem.get('pname', ''),
                                        _accidentalFromAttr(elem.get('accid')),
                                        elem.get('oct', '')))),
                     duration=makeDuration(_qlDurationFromAttr(elem.get('dur')),
                                           int(elem.get('dots', 0))))

    ## add the xml:id
    #post.id = elem.get('id')

    ## add articulations as possible
    #if 'artic' in elem.attrib:
        #post.articulations = _makeArticList(elem.attrib['artic'])

    return post


#------------------------------------------------------------------------------
class TestThings(unittest.TestCase):

    def testSafePitch1(self):
        # safePitch(): when ``name`` is a valid pitch name
        name = 'D#6'
        expected = pitch.Pitch('D#6')
        actual = safePitch(name)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testSafePitch2(self):
        # safePitch(): when ``name`` is not a valid pitch name
        name = ''
        expected = pitch.Pitch()
        actual = safePitch(name)
        self.assertEqual(expected.name, actual.name)
        self.assertEqual(expected.accidental, actual.accidental)
        self.assertEqual(expected.octave, actual.octave)

    def testMakeDuration(self):
        # just a couple of things
        self.assertEqual(2.0, makeDuration(2.0, 0).quarterLength)
        self.assertEqual(3.0, makeDuration(2.0, 1).quarterLength)
        self.assertEqual(3.5, makeDuration(2, 2).quarterLength) # "base" as int---should work
        self.assertEqual(3.999998092651367, makeDuration(2.0, 20).quarterLength)



#------------------------------------------------------------------------------
class TestAttrTranslators(unittest.TestCase):

    def testAttrTranslator1(self):
        # _attrTranslator(): the usual case works properly when "attr" is in "mapping"
        attr = 'two'
        name = 'numbers'
        mapping = {'one': 1, 'two': 2, 'three': 3}
        expected = 2
        actual = _attrTranslator(attr, name, mapping)
        self.assertEqual(expected, actual)

    def testAttrTranslator2(self):
        # _attrTranslator(): exception is raised properly when "attr" isn't found
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
        # _accidentalFromAttr(): ensure proper arguments to _attrTranslator
        attr = 's'
        _accidentalFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'accid', _ACCID_ATTR_DICT)

    @mock.patch('__main__._attrTranslator')
    def testDuration(self, mockTrans):
        # _qlDurationFromAttr(): ensure proper arguments to _attrTranslator
        attr = 's'
        _qlDurationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'dur', _DUR_ATTR_DICT)

    @mock.patch('__main__._attrTranslator')
    def testArticulation1(self, mockTrans):
        # _articulationFromAttr(): ensure proper arguments to _attrTranslator
        attr = 'marc'
        mockTrans.return_value = 5
        expected = (5,)
        actual = _articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._attrTranslator')
    def testArticulation2(self, mockTrans):
        # _articulationFromAttr(): proper handling of 'marc-stacc'
        attr = 'marc-stacc'
        mockTrans.side_effect = MeiValueError()
        expected = (articulations.StrongAccent, articulations.Staccato)
        actual = _articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._attrTranslator')
    def testArticulation3(self, mockTrans):
        # _articulationFromAttr(): proper handling of 'ten-stacc'
        attr = 'ten-stacc'
        mockTrans.side_effect = MeiValueError()
        expected = (articulations.Tenuto, articulations.Staccato)
        actual = _articulationFromAttr(attr)
        mockTrans.assert_called_once_with(attr, 'artic', _ARTIC_ATTR_DICT)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._attrTranslator')
    def testArticulation4(self, mockTrans):
        # _articulationFromAttr(): proper handling of not-found
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
        # _makeArticList(): properly handles single-articulation lists
        attr = 'acc'
        mockArtic.return_value = ['accent']
        expected = ['accent']
        actual = _makeArticList(attr)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._articulationFromAttr')
    def testArticList2(self, mockArtic):
        # _makeArticList(): properly handles multi-articulation lists
        attr = 'acc stacc marc'
        mockReturns = [['accent'], ['staccato'], ['marcato']]
        mockArtic.side_effect = lambda x: mockReturns.pop(0)
        expected = ['accent', 'staccato', 'marcato']
        actual = _makeArticList(attr)
        self.assertEqual(expected, actual)

    @mock.patch('__main__._articulationFromAttr')
    def testArticList3(self, mockArtic):
        # _makeArticList(): properly handles the compound articulations
        attr = 'acc marc-stacc marc'
        mockReturns = [['accent'], ['marcato', 'staccato'], ['marcato']]
        mockArtic.side_effect = lambda *x: mockReturns.pop(0)
        expected = ['accent', 'marcato', 'staccato', 'marcato']
        actual = _makeArticList(attr)
        self.assertEqual(expected, actual)



#------------------------------------------------------------------------------
class TestNoteFromElement(unittest.TestCase):

    @mock.patch('music21.note.Note')
    def testUnit1(self, mockNote):
        # noteFromElement(): all the elements that go in Note.__init__()...
        #                    'id', 'pname', 'accid', 'oct', 'dur', 'dots'
        # (mostly-unit test; only mock out Note and the ElementTree.Element)
        elem = mock.MagicMock()
        expectedElemOrder = [mock.call('pname', ''), mock.call('accid'), mock.call('oct', ''),
                             mock.call('dur'), mock.call('dots', 0)]
        elemReturns = ['D', 's', '2', '4', '1']
        elem.get.side_effect = lambda *x: elemReturns.pop(0)
        mockNote.return_value = 'note return'
        expected = mockNote.return_value
        actual = noteFromElement(elem)
        self.assertEqual(expected, actual)
        mockNote.assert_called_once_with(pitch.Pitch('D#2'), duration=duration.Duration(1.5))
        self.assertSequenceEqual(expectedElemOrder, elem.get.call_args_list)

    def testIntegration1(self):
        # noteFromElement(): all the elements that go in Note.__init__()...
        #                    'id', 'pname', 'accid', 'oct', 'dur', 'dots'
        # (corresponds to testUnit1() with real Note and real ElementTree.Element)
        elem = ETree.Element('note')
        attribDict = {'pname': 'D', 'accid': 's', 'oct': '2', 'dur': '4', 'dots': '1'}
        for key in attribDict:
            elem.set(key, attribDict[key])
        actual = noteFromElement(elem)
        self.assertEqual('D#2', actual.nameWithOctave)
        self.assertEqual(1.5, actual.quarterLength)
        self.assertEqual(1, actual.duration.dots)



#------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [noteFromElement]

if __name__ == "__main__":
    import music21
    music21.mainTest(TestThings)
    music21.mainTest(TestAttrTranslators)
    music21.mainTest(TestNoteFromElement)

#------------------------------------------------------------------------------
# eof
