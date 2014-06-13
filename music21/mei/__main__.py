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
from music21 import stream
from music21 import chord


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
    ETree.register_namespace('mei', 'http://www.music-encoding.org/ns/mei')
    documentRoot = ETree.fromstring(dataStr)
    if 'mei' != documentRoot.tag:
        raise MeiTagError('Root tag is should be <mei>, not <%s>.' % documentRoot.tag)
    # NOTE: this is obviously not proper document structure---there *should* be many levels of things before a <note>
    parsed = []
    foundTheRoot = False  # when the <mei> tag is discovered
    for eachTag in documentRoot.iter():
        if 'note' == eachTag.tag:
            parsed.append(noteFromElement(eachTag))
        elif 'rest' == eachTag.tag:
            parsed.append(restFromElement(eachTag))
        elif 'mei' == eachTag.tag:
            if not foundTheRoot:
                foundTheRoot = True
            else:
                raise MeiTagError('Found multiple <mei> tags')
        else:
            raise MeiTagError('what garbage is this?!: %s' % eachTag.tag)

    return stream.Score(parsed)


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
                    'tap': None, 'lhpizz': None, 'dot': None, 'stroke': None, 'rip': None,
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
    if 'marc-stacc' == attr:
        return (articulations.StrongAccent, articulations.Staccato)
    elif 'ten-stacc' == attr:
        return (articulations.Tenuto, articulations.Staccato)
    else:
        return (_attrTranslator(attr, 'artic', _ARTIC_ATTR_DICT),)


def _makeArticList(attr):
    '''
    Use :func:`_articulationFromAttr` to convert the actual value of an MEI "artic" attribute
    (including multiple items) into a list suitable for :attr:`GeneralNote.articulations`.
    '''
    post = []
    for eachArtic in attr.split(' '):
        post.extend(_articulationFromAttr(eachArtic))
    return post


# Converter Functions
#------------------------------------------------------------------------------
def noteFromElement(elem):
    '''
    <note> is a single pitched event.

    In MEI 2013: pg.382 (396 in PDF) (MEI.shared module)

    Attributes Implemented:
    =======================
    - accid, from att.accidental: (via _accidentalFromAttr())
    - pname, from att.pitch: [a--g]
    - oct, from att.octave: [0..9]
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]
    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - artic, a list from att.articulation: (via _articulationFromAttr())

    Attributes In Progress:
    =======================

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

    if elem.get('id') is not None:
        post.id = elem.get('id')

    if elem.get('artic') is not None:
        post.articulations = _makeArticList(elem.get('artic'))

    return post


def restFromElement(elem):
    '''
    <rest/> is a non-sounding event found in the source being transcribed

    In MEI 2013: pg.424 (438 in PDF) (MEI.shared module)

    Attributes Implemented:
    =======================
    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]

    Attributes In Progress:
    =======================

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.rest.log (att.event (att.timestamp.musical (@tstamp))
                            (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                            (att.staffident (@staff))
                            (att.layerident (@layer)))
                 (att.fermatapresent (@fermata))
                 (att.tupletpresent (@tuplet))
                 (att.rest.log.cmn (att.beamed (@beam)))
    att.rest.vis (att.altsym (@altsym))
                 (att.color (@color))
                 (att.enclosingchars (@enclose))
                 (att.relativesize (@size))
                 (att.rest.vis.cmn)
                 (att.rest.vis.mensural (@spaces))
                 (att.staffloc (@loc))
                 (att.staffloc.pitched (@ploc, @oloc))
                 (att.visualoffset (att.visualoffset.ho (@ho))
                                   (att.visualoffset.to (@to))
                                   (att.visualoffset.vo (@vo)))
                 (att.xy (@x, @y))
    att.rest.ges (att.duration.performed (@dur.ges))
                 (att.instrumentident (@instr))
                 (att.rest.ges.mensural (att.duration.ratio (@num, @numbase)))
    att.rest.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                 (att.alignment (@when)))

    May Contain:
    ============
    None.
    '''
    post = note.Rest(duration=makeDuration(_qlDurationFromAttr(elem.get('dur')),
                                           int(elem.get('dots', 0))))

    if elem.get('id') is not None:
        post.id = elem.get('id')

    return post


def chordFromElement(elem):
    '''
    <chord> is a simultaneous sounding of two or more notes in the same layer with the same duration.

    In MEI 2013: pg.280 (294 in PDF) (MEI.shared module)

    Attributes Implemented:
    =======================
    - <note> contained within
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]

    Attributes In Progress:
    =======================

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.facsimile (@facs)
    att.chord.log (att.event (att.timestamp.musical (@tstamp))
                             (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                             (att.staffident (@staff))
                             (att.layerident (@layer)))
                  (att.articulation (@artic))
                  (att.augmentdots (@dots))
                  (att.duration.musical (@dur))
                  (att.fermatapresent (@fermata))
                  (att.syltext (@syl))
                  (att.slurpresent (@slur))
                  (att.tiepresent (@tie))
                  (att.tupletpresent (@tuplet))
                  (att.chord.log.cmn (att.beamed (@beam))
                                     (att.lvpresent (@lv))
                                     (att.ornam (@ornam)))
    att.chord.vis (@cluster)
                  (att.altsym (@altsym))
                  (att.color (@color))
                  (att.relativesize (@size))
                  (att.stemmed (@stem.dir, @stem.len, @stem.pos, @stem.x, @stem.y)
                               (att.stemmed.cmn (@stem.mod, @stem.with)))
                  (att.visibility (@visible))
                  (att.visualoffset.ho (@ho))
                  (att.visualoffset.to (@to))
                  (att.xy (@x, @y))
                  (att.chord.vis.cmn (att.beamsecondary (@breaksec)))
    att.chord.ges (att.articulation.performed (@artic.ges))
                  (att.duration.performed (@dur.ges))
                  (att.instrumentident (@instr))
                  (att.chord.ges.cmn (att.graced (@grace, @grace.time)))
    att.chord.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                  (att.alignment (@when)))

    May Contain:
    ============
    MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied unclear
    MEI.shared: artic note
    '''
    # pitch and duration... these are what we can set in the constructor
    post = chord.Chord(notes=[noteFromElement(x) for x in elem.iterfind('note')])

    # for a Chord, setting "duration" with a Duration object in __init__() doesn't work
    post.duration = makeDuration(_qlDurationFromAttr(elem.get('dur')), int(elem.get('dots', 0)))

    if elem.get('id') is not None:
        post.id = elem.get('id')

    if elem.get('artic') is not None:
        post.articulations = _makeArticList(elem.get('artic'))

    return post


#------------------------------------------------------------------------------
_DOC_ORDER = [noteFromElement, restFromElement]

if __name__ == "__main__":
    import music21
    import test_main
    music21.mainTest(test_main.TestThings,
                     test_main.TestAttrTranslators,
                     test_main.TestNoteFromElement,
                     test_main.TestRestFromElement,
                     test_main.TestChordFromElement,
                     )

#------------------------------------------------------------------------------
# eof
