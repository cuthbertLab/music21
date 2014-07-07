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

In the future, most of the functions in this module should be moved to a separate, import-only
module, so that functions for writing music21-to-MEI will fit nicely.
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
from music21 import clef
from music21 import beam
from music21 import meter
from music21 import key
from music21 import instrument
from music21 import interval
from music21 import bar

# six
from music21.ext import six
from six.moves import range, xrange


# Module-Level Constants
#------------------------------------------------------------------------------
_XMLID = '{http://www.w3.org/XML/1998/namespace}id'
_MEINS = '{http://www.music-encoding.org/ns/mei}'
# when these tags aren't processed, we won't worry about them (at least for now)
_IGNORE_UNPROCESSED = ('{}sb'.format(_MEINS),  # system break
                       '{}lb'.format(_MEINS),  # line break
                      )


# Exceptions
#------------------------------------------------------------------------------
class MeiValidityError(exceptions21.Music21Exception):
    "When there is an otherwise-unspecified validity error that prevents parsing."
    pass

class MeiValueError(exceptions21.Music21Exception):
    "When an attribute has an invalid value."
    pass

class MeiAttributeError(exceptions21.Music21Exception):
    "When a tag has an invalid attribute."
    pass

class MeiTagError(exceptions21.Music21Exception):
    "When there's an invalid tag."
    pass

# Text Strings for Error Conditions
#------------------------------------------------------------------------------
_WRONG_ROOT_TAG = 'Root tag is should be <mei>, not <{}>.'
_MULTIPLE_ROOT_TAGS = 'Found multiple <mei> tags.'
_UNKNOWN_TAG = 'Found unexpected tag while parsing MEI: <{}>.'
_UNEXPECTED_ATTR_VALUE = 'Unexpected value for "{}" attribute: {}'
_SEEMINGLY_NO_PARTS = 'There appear to be no <staffDef> tags in this score.'
_MISSING_VOICE_ID = 'Found a <layer> without @n attribute and no override.'


# Module-level Functions
#------------------------------------------------------------------------------
def convertFromString(dataStr):
    '''
    Convert a string from MEI markup to music21 objects.

    :parameter str dataStr: A string with MEI markup.
    :returns: A :class:`Stream` subclass, depending on the markup in the ``dataStr``.
    :rtype: :class:`music21.stream.Stream`
    '''
    documentRoot = ETree.fromstring(dataStr)
    if isinstance(documentRoot, ETree.ElementTree):
        documentRoot = documentRoot.getroot()

    if '{http://www.music-encoding.org/ns/mei}mei' != documentRoot.tag:
        raise MeiTagError(_WRONG_ROOT_TAG.format(documentRoot.tag))

    # Get a tuple of all the @n attributes for the <staff> tags in this score. Each <staff> tag
    # corresponds to what will be a music21 Part. The specificer, the better. What I want to do is
    # get all the <staffDef> tags that are in the <score>, no matter where they appear. This is just
    # to fetch everything that will affect the maximum number of parts that might happen at a time.
    allPartNs = allPartsPresent(documentRoot.findall('.//{mei}music//{mei}score//{mei}staffDef'.format(mei=_MEINS)))

    # holds the music21.stream.Part that we're building
    parsed = {n: stream.Part() for n in allPartNs}
    # holds things that should go in the following Measure
    inNextMeasure = {n: stream.Part() for n in allPartNs}

    # set the Instrument for each staff
    for eachN in allPartNs:
        queryStr = './/{mei}music//{mei}staffDef[@n="{n}"]'.format(mei=_MEINS, n=eachN)
        for info in staffDefFromElement(documentRoot.findall(queryStr)[0]):  # TODO: decide whether we need more than the first
            parsed[eachN].append(info)

    # it's possible there's a <scoreDef> before any of the <section> tags
    for eachDef in documentRoot.findall('*//{mei}score//{mei}scoreDef'.format(mei=_MEINS)):
        # TODO: this only puts the *first* <scoreDef> in the right spot
        if '{http://www.music-encoding.org/ns/mei}scoreDef' == eachDef.tag:
            scoreDefResults = scoreDefFromElement(eachDef)
            # spread all-part elements across all the parts
            for allPartObject in scoreDefResults['all-part objects']:
                for n in allPartNs:
                    inNextMeasure[n].append(allPartObject)
        else:
            # this should never happen
            print('!! found a {} in a place we only expected <scoreDef>s!!'.format(eachObject.tag))
            raise RuntimeError('bananas!')

    backupMeasureNum = 0
    for eachSection in documentRoot.findall('.//{mei}music//{mei}score//*[{mei}measure]'.format(mei=_MEINS)):
        # TODO: sections aren't divided or treated specially, yet
        for eachObject in eachSection:
            if '{http://www.music-encoding.org/ns/mei}measure' == eachObject.tag:
                # TODO: MEI's "rptboth" barlines require handling at the multi-measure level
                backupMeasureNum += 1
                # process all the stuff in the <measure>
                measureResult = measureFromElement(eachObject, backupMeasureNum, allPartNs)
                # process and append each part's stuff to the staff
                for eachN in allPartNs:
                    # TODO: what if an @n doesn't exist in this <measure>?
                    # insert objects specified in the immediately-preceding <scoreDef>
                    for eachThing in inNextMeasure[eachN]:
                        measureResult[eachN].insert(0, eachThing)
                    inNextMeasure[eachN] = []
                    # add this Measure to the Part
                    parsed[eachN].append(measureResult[eachN])
            elif '{http://www.music-encoding.org/ns/mei}scoreDef' == eachObject.tag:
                scoreDefResults = scoreDefFromElement(eachObject)
                # spread all-part elements across all the parts
                for allPartObject in scoreDefResults['all-part objects']:
                    for n in allPartNs:
                        inNextMeasure[n].append(allPartObject)
            elif eachObject.tag not in _IGNORE_UNPROCESSED:
                print('!! unprocessed {} in {}'.format(eachObject.tag, eachSection.tag))

    # TODO: check if there's anything left in "inNextMeasure"

    # convert the dict to a list
    # We must iterate here over "allPartNs," which preserves the part-order found in the MEI
    # document, whereas iterating over the keys in "parsed" would not preserve the order.
    parsed = [parsed[n] for n in allPartNs]

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


def allPartsPresent(allStaffDefs):
    '''
    Given an iterable of all <staffDef> :class:`Element` objects in an MEI file, deduplicate the @n
    attributes, yielding a list of all @n attributes in the <score>.

    :param allStaffDefs: All the <staffDef> elements in a <score>.
    :type allStaffDefs: iterable of :class:`~xml.etree.ElementTree.Element`
    :returns: All the unique @n values in the <score>.
    :rtype: tuple of str

    ``allStaffDefs`` should probably be the result of this XPath query:::
        documentRoot.findall('.//score//staffDef')

    But of course you must prefix it with the MEI namespace, so it's actually this:::
        documentRoot.findall('.//{http://www.music-encoding.org/ns/mei}score//{http://www.music-encoding.org/ns/mei}staffDef')  # pylint: disable=line-too-long

    If you don't do this, you may get misleading <staffDef> tags from, for example, the incipit.
    '''
    post = []
    for staffDef in allStaffDefs:
        if staffDef.get('n') not in post:
            post.append(staffDef.get('n'))
    if 0 == len(post):
        raise MeiValidityError(_SEEMINGLY_NO_PARTS)
    return tuple(post)


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

# for _barlineFromAttr()
# TODO: make new music21 Barline styles for 'dbldashed' and 'dbldotted'
_BAR_ATTR_DICT = {'dashed': 'dashed', 'dotted': 'dotted', 'dbl': 'double', 'end': 'final',
                  'invis': 'none', 'single': 'none'}


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
        raise MeiValueError('Unexpected value for "{}" attribute: {}'.format(name, attr))
    MeiValueError: Unexpected value for "dur" attribute: 9
    '''
    try:
        return mapping[attr]
    except KeyError:
        raise MeiValueError(_UNEXPECTED_ATTR_VALUE.format(name, attr))


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


def _getOctaveShift(dis, disPlace):
    '''
    Use :func:`_getOctaveShift` to calculate the :attr:`octaveShift` attribute for a
    :class:`~music21.clef.Clef` subclass. Any of the arguments may be ``None``.

    :param str dis: The "dis" attribute from the <clef> tag.
    :param str disPlace: The "dis.place" attribute from the <clef> tag.

    :returns: The octave displacement compared to the clef's normal position. This may be 0.
    :rtype: integer
    '''
    # NB: dis: 8, 15, or 22 (or "ottava" clefs)
    # NB: dis.place: "above" or "below" depending on whether the ottava clef is Xva or Xvb
    octavesDict = {None: 0, '8': 1, '15': 2, '22': 3}
    if 'below' == disPlace:
        return -1 * octavesDict[dis]
    else:
        return octavesDict[dis]


def _sharpsFromAttr(signature):
    '''
    Use :func:`_sharpsFromAttr` to convert MEI's ``data.KEYSIGNATURE`` datatype to an integer
    representing the number of sharps, for use with music21's :class:`~music21.key.KeySignature`.

    :param str signature: The @key.sig attribute.
    :returns: The number of sharps.
    :rtype: int

    >>> from music21.mei.__main__ import _sharpsFromAttr
    >>> _sharpsFromAttr('3s')
    3
    >>> _sharpsFromAttr('3f')
    -3
    >>> _sharpsFromAttr('0')
    0
    '''
    if signature.startswith('0'):
        return 0
    elif signature.endswith('s'):
        return int(signature[0])
    else:
        return -1 * int(signature[0])


def _timeSigFromAttrs(elem):
    # TODO: write tests
    '''
    From any tag with @meter.count and @meter.unit attributes, make a :class:`TimeSignature`.

    :param :class:`~xml.etree.ElementTree.Element` elem: An :class:`Element` with @meter.count and
        @meter.unit attributes.
    :returns: The corresponding time signature.
    :rtype: :class:`~music21.meter.TimeSignature`
    '''
    return meter.TimeSignature('{!s}/{!s}'.format(elem.get('meter.count'), elem.get('meter.unit')))


def _keySigFromAttrs(elem):
    # TODO: write tests
    '''
    From any tag with (at minimum) either @key.pname or @key.sig attributes, make a
    :class:`KeySignature` or :class:`Key`, as possible.

    :param :class:`~xml.etree.ElementTree.Element` elem: An :class:`Element` with either the
        @key.pname or @key.sig attribute.
    :returns: The key or key signature.
    :rtype: :class:`music21.key.Key` or :class:`~music21.key.KeySignature`
    '''
    if elem.get('key.pname') is not None:
        # @key.accid, @key.mode, @key.pname
        return key.Key(tonic=elem.get('key.pname') + _accidentalFromAttr(elem.get('key.accid')),
                       mode=elem.get('key.mode', ''))
    else:
        # @key.sig, @key.mode
        return key.KeySignature(sharps=_sharpsFromAttr(elem.get('key.sig')),
                                mode=elem.get('key.mode'))


def _transpositionFromAttrs(elem):
    # TODO: write tests
    '''
    From any tag with the @trans.diat (and optionally the @trans.semi) attributes, make an
    :class:`Interval` that represents the interval of transposition from written to concert pitch.

    :param :class:`~xml.etree.ElementTree.Element` elem: An :class:`Element` with the @trans.diat
        (and optionally @trans.semi) attributes.
    :returns: The interval of transposition from written to concert pitch.
    :rtype: :class:`music21.interval.Interval`
    '''
    # NB: MEI uses zero-based unison rather than 1-based unison, so for music21 we must make every
    #     diatonic interval one greater than it was. E.g., '@trans.diat="2"' in MEI means to
    #     "transpose up two diatonic steps," which music21 would rephrase as "transpose up by a
    #     diatonic third."
    iFGAC = interval.intervalFromGenericAndChromatic
    if elem.get('trans.diat') < 0:
        return iFGAC(interval.GenericInterval(int(elem.get('trans.semi'))),
                     interval.ChromaticInterval(int(elem.get('trans.diat')) - 1))
    else:
        return iFGAC(interval.GenericInterval(int(elem.get('trans.semi'))),
                     interval.ChromaticInterval(int(elem.get('trans.diat')) + 1))


def _barlineFromAttr(attr):
    # TODO: write tests
    '''
    Use :func:`_attrTranslator` to convert the value of a "left" or "right" attribute to a
    list of :class:`Barline` or :class:`Repeat`. Note this must be a list because an end-repeat and
    start-repeat at the same time must be two distinct objects in music21.

    :param str attr: The MEI @left or @right attribute to convert to a barline.
    :returns: The barline.
    :rtype: list of :class:`music21.bar.Barline` or :class:`~music21.bar.Repeat`
    '''
    # NB: the MEI Specification says @left is used only for legcay-format conversions, so we'll
    #     just assume it's a @right attribute. Not a huge deal if we get this wrong (I hope).
    if attr.startswith('rpt'):
        if 'rptboth' == attr:
            return None
        elif 'rptend' == attr:
            return bar.Repeat('end', times=2)
        else:
            return bar.Repeat('start')
    else:
        return bar.Barline(_attrTranslator(attr, 'right', _BAR_ATTR_DICT))


# Converter Functions
#------------------------------------------------------------------------------
def scoreDefFromElement(elem):
    # TODO: this whole function is untested
    '''
    <scoreDef> Container for score meta-information.

    In MEI 2013: pg.431 (445 in PDF) (MEI.shared module)

    This function returns objects related to the score overall, and those relevant only to
    specific parts, depending on the attributes and contents of the given :class:`Element`.

    Objects relevant only to a particular part are accessible in the returned dictionary using that
    part's @n attribute. The dictionary also has two special keys:
    * ``'whole-score objects'``, which are related to the entire score (e.g., page size), and
    * ``'all-part objects'``, which should appear in every part.

    Note that it is the caller's responsibility to determine the right actions if there are
    conflicting objects in the returned dictionary.

    :param elem: The ``<scoreDef>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: Objects from the ``<scoreDef>`` relevant on a per-part and whole-score basis.
    :rtype: dict of list of :class:`Music21Objects`

    Attributes Implemented:
    =======================

    Attributes In Progress:
    =======================
    (att.meterSigDefault.log (@meter.count, @meter.unit))
    (att.keySigDefault.log (@key.accid, @key.mode, @key.pname, @key.sig))

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.scoreDef.log (att.cleffing.log (@clef.shape, @clef.line, @clef.dis, @clef.dis.place))
                     (att.duration.default (@dur.default, @num.default, @numbase.default))
                     (att.keySigDefault.log (@key.sig.mixed))
                     (att.octavedefault (@octave.default))
                     (att.transposition (@trans.diat, @trans.semi))
                     (att.scoreDef.log.cmn (att.beaming.log (@beam.group, @beam.rests)))
                     (att.scoreDef.log.mensural (att.mensural.log (@mensur.dot, @mensur.sign,
                                                                   @mensur.slash, @proport.num,
                                                                   @proport.numbase)
                                                (att.mensural.shared (@modusmaior, @modusminor,
                                                                      @prolatio, @tempus))))
    att.scoreDef.vis (@ending.rend, @mnum.visible, @music.name, @music.size, @optimize,
                      @page.height, @page.width, @page.topmar, @page.botmar, @page.leftmar,
                      @page.rightmar, @page.panels, @page.scale, @spacing.packexp,
                      @spacing.packfact, @spacing.staff, @spacing.system, @system.leftmar,
                      @system.rightmar, @system.topmar, @vu.height)
                     (att.barplacement (@barplace, @taktplace))
                     (att.cleffing.vis (@clef.color, @clef.visible))
                     (att.distances (@dynam.dist, @harm.dist, @text.dist))
                     (att.keySigDefault.vis (@key.sig.show, @key.sig.showchange))
                     (att.lyricstyle (@lyric.align, @lyric.fam, @lyric.name, @lyric.size,
                                      @lyric.style, @lyric.weight))
                     (att.meterSigDefault.vis (@meter.rend, @meter.showchange, @meter.sym))
                     (att.multinummeasures (@multi.number))
                     (att.onelinestaff (@ontheline))
                     (att.textstyle (@text.fam, @text.name, @text.size, @text.style, @text.weight))
                     (att.scoreDef.vis.cmn (@grid.show)
                                           (att.beaming.vis (@beam.color, @beam.rend, @beam.slope))
                                           (att.pianopedals (@pedal.style))
                                           (att.rehearsal (@reh.enclose))
                                           (att.slurrend (@slur.rend))
                                           (att.tierend (@tie.rend)))
                     (att.scoreDef.vis.mensural (att.mensural.vis (@mensur.color, @mensur.form,
                                                                   @mensur.loc, @mensur.orient,
                                                                   @mensur.size)))
    att.scoreDef.ges (@tune.pname, @tune.Hz, @tune.temper)
                     (att.channelized (@midi.channel, @midi.duty, @midi.port, @midi.track))
                     (att.timebase (@ppq))
                     (att.miditempo (@midi.tempo))
                     (att.mmtempo (@mm, @mm.unit, @mm.dots))
    att.scoreDef.anl

    May Contain:
    ============
    MEI.cmn: meterSig meterSigGrp
    MEI.harmony: chordTable
    MEI.linkalign: timeline
    MEI.midi: instrGrp
    MEI.shared: keySig pgFoot pgFoot2 pgHead pgHead2 staffGrp
    MEI.usersymbols: symbolTable
    '''
    # make the dict
    allParts = 'all-part objects'
    wholeScore = 'whole-score objects'
    post = {allParts: [], wholeScore: []}

    # 1.) process whole-score objects
    # --> time signature
    if elem.get('meter.count') is not None:
        post[allParts].append(_timeSigFromAttrs(elem))

    # --> key signature
    if elem.get('key.pname') is not None or elem.get('key.sig') is not None:
        post[allParts].append(_keySigFromAttrs(elem))

    # 2.) process per-part objects
    # TODO: deal with per-part stuff

    return post


def staffDefFromElement(elem):
    '''
    <staffDef> Container for staff meta-information.

    In MEI 2013: pg.445 (459 in PDF) (MEI.shared module)

    :returns: A list with an :class:`Instrument` subclass with the staff's metadata, followed by
        other music21 objects specified by the ``<staffDef>``, like a :class:`Clef` or :class:`Key`.
    :rtype: list of :class:`music21.instrument.Instrument` then :class:`music21.base.Music21Object`

    Attributes Implemented:
    =======================

    Attributes Ignored:
    ===================
    - @key.sig.mixed (from att.keySigDefault.log)

    Attributes In Progress:
    =======================
    - @label (att.common) as Instrument.partName
    - @label.abbr (att.labels.addl) as Instrument.partAbbreviation
    - @n (att.common) as Instrument.partId
    - (att.keySigDefault.log (@key.accid, @key.mode, @key.pname, @key.sig))
    - (att.meterSigDefault.log (@meter.count, @meter.unit))
    - (att.cleffing.log (@clef.shape, @clef.line, @clef.dis, @clef.dis.place)) (via :func:`clefFromElement`)
    - @trans.diat and @trans.demi (att.transposition)

    Attributes not Implemented:
    ===========================
    att.common (@n, @xml:base)
               (att.id (@xml:id))
    att.declaring (@decls)
    att.staffDef.log (att.duration.default (@dur.default, @num.default, @numbase.default)) <-- need this!!!
                     (att.octavedefault (@octave.default)) <-- need this!!!
                     (att.staffDef.log.cmn (att.beaming.log (@beam.group, @beam.rests)))
                     (att.staffDef.log.mensural (att.mensural.log (@mensur.dot, @mensur.sign, @mensur.slash, @proport.num, @proport.numbase)
                                                (att.mensural.shared (@modusmaior, @modusminor, @prolatio, @tempus))))
    att.staffDef.vis (@grid.show, @layerscheme, @lines, @lines.color, @lines.visible, @spacing)
                     (att.cleffing.vis (@clef.color, @clef.visible))
                     (att.distances (@dynam.dist, @harm.dist, @text.dist))
                     (att.keySigDefault.vis (@key.sig.show, @key.sig.showchange))
                     (att.lyricstyle (@lyric.align, @lyric.fam, @lyric.name, @lyric.size, @lyric.style, @lyric.weight))
                     (att.meterSigDefault.vis (@meter.rend, @meter.showchange, @meter.sym))
                     (att.multinummeasures (@multi.number))
                     (att.onelinestaff (@ontheline))
                     (att.scalable (@scale))
                     (att.textstyle (@text.fam, @text.name, @text.size, @text.style, @text.weight))
                     (att.visibility (@visible))
                     (att.staffDef.vis.cmn (att.beaming.vis (@beam.color, @beam.rend, @beam.slope))
                                           (att.pianopedals (@pedal.style))
                                           (att.rehearsal (@reh.enclose))
                                           (att.slurrend (@slur.rend))
                                           (att.tierend (@tie.rend)))
                     (att.staffDef.vis.mensural (att.mensural.vis (@mensur.color, @mensur.form, @mensur.loc, @mensur.orient, @mensur.size)))
    att.staffDef.ges (att.instrumentident (@instr))
                     (att.timebase (@ppq))
                     (att.staffDef.ges.tablature (@tab.strings))
    att.staffDef.anl

    May Contain:
    ============
    MEI.cmn: meterSig meterSigGrp
    MEI.mensural: mensur proport
    MEI.midi: instrDef <-- need this!!!
    MEI.shared: clef clefGrp keySig label layerDef
    '''
    # mapping from tag name to our converter function
    tagToFunction = {}

    # <instrDef> contained within
    #for eachDef in elem.findall('%sinstrDef' % _MEINS):
        #print('?? partName: %s; partId: %s' % (post[0].partName == '', post[0].partId))  # DEBUG
        #instr = instrDefFromElement(eachDef)
        #if '' == post[0].partName and '' != instr.bestName():
            #post[0].partName = instr.bestName()
        #if post[0].partId is None and instr.partId is not None:
            #post[0].partId = instr.partId

    # first make the Instrument
    post = elem.findall('{}instrDef'.format(_MEINS))
    if len(post) > 0:
        post = [instrDefFromElement(post[0])]
    else:
        try:
            post = [instrument.fromString(elem.get('label'))]
        except (AttributeError, instrument.InstrumentException):
            post = [instrument.Instrument()]
    post[0].partName = elem.get('label')
    post[0].partAbbreviation = elem.get('label.abbr')
    post[0].partId = elem.get('n')





    # process other part-specific information
    # --> time signature
    if elem.get('meter.count') is not None:
        post.append(_timeSigFromAttrs(elem))

    # --> key signature
    if elem.get('key.pname') is not None or elem.get('key.sig') is not None:
        post.append(_keySigFromAttrs(elem))

    # --> clef
    # (att.cleffing.log (@clef.shape, @clef.line, @clef.dis, @clef.dis.place))
    if elem.get('clef.shape') is not None:
        post.append(clefFromElement(ETree.Element('clef', {'shape': elem.get('clef.shape'),
                                                           'line': elem.get('clef.line'),
                                                           'dis': elem.get('clef.dis'),
                                                           'dis.place': elem.get('clef.dis.place')})))

    # --> transposition
    # - A clarinet: trans.semi="-3" trans.diat="-2"... because C to A is two diatonic steps comprised of three semitones
    # - they're both integer values
    # - "diatonic transposition" requires both .semi and .diat
    if elem.get('trans.semi') is not None:
        post[0].transposition = _transpositionFromAttrs(elem)

    # iterate all immediate children
    for eachTag in elem.findall('*'):
        if eachTag.tag in tagToFunction:
            post.append(tagToFunction[eachTag.tag](eachTag))
        elif '%sinstrDef' % _MEINS != eachTag.tag:  # DEBUG
            print('!! unprocessed %s in %s' % (eachTag.tag, elem.tag))  # DEBUG

    return post


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

    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

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

    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

    return post


def mRestFromElement(elem):
    '''
    <mRest/> Complete measure rest in any meter.

    In MEI 2013: pg.375 (389 in PDF) (MEI.cmn module)

    This is a function wrapper for :func:`restFromElement`.
    '''
    return restFromElement(elem)


def chordFromElement(elem):
    '''
    <chord> is a simultaneous sounding of two or more notes in the same layer with the same duration.

    In MEI 2013: pg.280 (294 in PDF) (MEI.shared module)

    Attributes Implemented:
    =======================
    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - <note> contained within
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]
    - artic, a list from att.articulation: (via _articulationFromAttr())

    Attributes In Progress:
    =======================

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.chord.log (att.event (att.timestamp.musical (@tstamp))
                             (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                             (att.staffident (@staff))
                             (att.layerident (@layer)))
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
    MEI.shared: artic
    '''
    # pitch and duration... these are what we can set in the constructor
    post = chord.Chord(notes=[noteFromElement(x) for x in elem.iterfind('{}note'.format(_MEINS))])

    # for a Chord, setting "duration" with a Duration object in __init__() doesn't work
    post.duration = makeDuration(_qlDurationFromAttr(elem.get('dur')), int(elem.get('dots', 0)))

    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

    if elem.get('artic') is not None:
        post.articulations = _makeArticList(elem.get('artic'))

    return post


def clefFromElement(elem):
    '''
    <clef> Indication of the exact location of a particular note on the staff and, therefore,
    the other notes as well.

    In MEI 2013: pg.284 (298 in PDF) (MEI.shared module)

    Attributes Implemented:
    =======================
    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - shape, from att.clef.gesatt.clef.log
    - line, from att.clef.gesatt.clef.log
    - dis, from att.clef.gesatt.clef.log
    - dis.place, from att.clef.gesatt.clef.log

    Attributes Ignored:
    ===================
    - cautionary, from att.clef.gesatt.clef.log
        --> I don't know how this affects the music21 objects
    - octave, from att.clef.gesatt.clef.log
        --> this is more complicated than it's worth; who would write a G clef in octave 1?

    Attributes In Progress:
    =======================

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.event (att.timestamp.musical (@tstamp))
              (att.timestamp.performed (@tstamp.ges, @tstamp.real))
              (att.staffident (@staff))
              (att.layerident (@layer))
    att.facsimile (@facs)
    att.clef.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                 (att.alignment (@when)))
    att.clef.vis (att.altsym (@altsym))
                 (att.color (@color))

    May Contain:
    ============
    None.
    '''
    if 'perc' == elem.get('shape'):
        post = clef.PercussionClef()
    elif 'TAB' == elem.get('shape'):
        post = clef.TabClef()
    else:
        post = clef.clefFromString(elem.get('shape') + elem.get('line'),
                                   octaveShift=_getOctaveShift(elem.get('dis'),
                                                               elem.get('dis.place')))

    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

    return post


def instrDefFromElement(elem):
    # TODO: write tests
    '''
    <instrDef> (instrument definition)---MIDI instrument declaration.

    In MEI 2013: pg.344 (358 in PDF) (MEI.midi module)

    :returns: An :class:`Instrument`

    Attributes Implemented:
    =======================

    Attributes In Progress:
    =======================
    - @midi.instrname (att.midiinstrument)
    - @midi.instrnum (att.midiinstrument)

    Attributes Ignored:
    ===================
    - @xml:id

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.channelized (@midi.channel, @midi.duty, @midi.port, @midi.track)
    att.midiinstrument (@midi.pan, @midi.volume)

    May Contain:
    ============
    None.
    '''
    if elem.get('midi.instrnum') is not None:
        return instrument.instrumentFromMidiProgram(int(elem.get('midi.instrnum')))
    else:
        try:
            return instrument.fromString(elem.get('midi.instrname'))
        except (AttributeError, instrument.InstrumentException):
            post = instrument.Instrument()
            post.partName = elem.get('midi.instrname', '')
            return post


def beamFromElement(elem, overrideN=None):
    '''
    <beam> A container for a series of explicitly beamed events that begins and ends entirely
           within a measure.

    In MEI 2013: pg.264 (278 in PDF) (MEI.cmn module)

    :param elem: The ``<beam>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: An iterable of all the objects contained within the ``<beam>`` container.
    :rtype: tuple of :class:`~music21.base.Music21Object`

    Attributes Implemented:
    =======================
    - <clef> contained within
    - <chord> contained within
    - <note> contained within
    - <rest> contained within

    Attributes Ignored:
    ===================
    - @xml:id. Since this tag does not translate to a :class:`Music21Object`, we cannot set the ``id``.

    Attributes In Progress:
    =======================

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.beam.log (att.event (att.timestamp.musical (@tstamp))
                            (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                            (att.staffident (@staff))
                            (att.layerident (@layer)))
                 (att.beamedwith (@beam.with))
    att.beam.vis (att.color (@color))
                 (att.beamrend (@rend, @slope))
    att.beam.gesatt.beam.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                             (att.alignment (@when)))

    May Contain:
    ============
    MEI.cmn: bTrem beam beatRpt fTrem halfmRpt meterSig meterSigGrp tuplet
    MEI.critapp: app
    MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied unclear
    MEI.mensural: ligature mensur proport
    MEI.shared: barLine clefGrp custos keySig pad space
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement}
    post = []

    # iterate all immediate children
    for eachTag in elem.findall('*'):
        if eachTag.tag in tagToFunction:
            post.append(tagToFunction[eachTag.tag](eachTag))
        else:  # DEBUG
            print('!! unprocessed %s in %s' % (eachTag.tag, elem.tag))  # DEBUG

    # install the beams
    beamEnd = len(post) - 1  # object with this index in "post" should have the 'stop' Beam type
    if 0 != beamEnd:
        for i, thing in enumerate(post):
            # first determine beam type
            if 0 == i:
                beamType = 'start'
            elif beamEnd == i:
                beamType = 'stop'
            else:
                beamType = 'continue'

            # then set it (if possible)
            if hasattr(thing, 'beams'):
                thing.beams.fill(duration.convertQuarterLengthToType(thing.quarterLength), beamType)
            elif beamEnd == i:  # end the beam earlier if the last thing is a Rest (for example)
                post[i - 1].beams.setAll('partial', direction='right')

    return tuple(post)


def layerFromElement(elem, overrideN=None):
    '''
    <layer> An independent stream of events on a staff.

    In MEI 2013: pg.353 (367 in PDF) (MEI.shared module)

    .. note:: The :class:`Voice` object's :attr:`~music21.stream.Voice.id` attribute must be set
        properly in order to ensure continuity of voices between measures. If the ``elem`` does not
        have an @n attribute, you can set one with the ``overrideN`` parameter in this function. If
        you provide a value for ``overrideN``, it will be used instead of the ``elemn`` object's
        @n attribute.

        Because improperly-set :attr:`~music21.stream.Voice.id` attributes nearly guarantees errors
        in the imported :class:`Score`, either ``overrideN`` or @n must be specified.

    :param elem: The ``<layer>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param str overrideN: The value to be set as the ``id`` attribute in the outputted :class:`Voice`.
    :returns: A :class:`Voice` with the objects found in the provided :class:`Element`.
    :rtype: :class:`music21.stream.Voice`
    :raises: :exc:`MeiAttributeError` if neither ``overrideN`` nor @n are specified.

    Attributes Implemented:
    =======================
    - <clef> contained within
    - <chord> contained within
    - <note> contained within
    - <rest> contained within
    - <mRest> contained within
    - @n, from att.common

    Attributes Ignored:
    ===================
    - xml:id. Since the @xml:id atttribute must be unique within a document, setting @xml:id as the
        :class:`Voice` object's ``id`` attribute would make it seem as though every measure has an
        entirely different set of voices. Since voices are (in this case) connected between
        measures, we must ensure corresponding :class:`Voice` objects have corresponding ``id``
        attributes.

    Attributes In Progress:
    =======================
    - <beam> contained within

    Attributes not Implemented:
    ===========================
    att.common (@label, @xml:base)
    att.declaring (@decls)
    att.facsimile (@facs)
    att.layer.log (@def)
                  (att.meterconformance (@metcon))
    att.layer.vis (att.visibility (@visible))
    att.layer.gesatt.layer.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                               (att.alignment (@when)))

    May Contain:
    ============
    MEI.cmn: arpeg bTrem beamSpan beatRpt bend breath fTrem fermata gliss hairpin halfmRpt
             harpPedal mRpt mRpt2 mSpace meterSig meterSigGrp multiRest multiRpt octave pedal
             reh slur tie tuplet tupletSpan
    MEI.cmnOrnaments: mordent trill turn
    MEI.critapp: app
    MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied unclear
    MEI.harmony: harm
    MEI.lyrics: lyrics
    MEI.mensural: ligature mensur proport
    MEI.midi: midi
    MEI.neumes: ineume syllable uneume
    MEI.shared: accid annot artic barLine clefGrp custos dir dot dynam keySig pad pb phrase sb
                scoreDef space staffDef tempo
    MEI.text: div
    MEI.usersymbols: anchoredText curve line symbol
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement,
                     '{http://www.music-encoding.org/ns/mei}mRest': mRestFromElement,
                     '{http://www.music-encoding.org/ns/mei}beam': beamFromElement}
    post = stream.Voice()

    # iterate all immediate children
    for eachTag in elem.findall('*'):
        if eachTag.tag in tagToFunction:
            result = tagToFunction[eachTag.tag](eachTag)
            if not isinstance(result, (tuple, list)):
                post.append(result)
            else:
                for eachObject in result:
                    post.append(eachObject)
        else:  # DEBUG
            print('!! unprocessed %s in %s' % (eachTag.tag, elem.tag))  # DEBUG

    # try to set the Voice's "id" attribte
    if overrideN:
        post.id = overrideN
    elif elem.get('n') is not None:
        post.id = elem.get('n')
    else:
        raise MeiAttributeError(_MISSING_VOICE_ID)

    return post


def staffFromElement(elem):
    '''
    <staff> A group of equidistant horizontal lines on which notes are placed in order to
    represent pitch or a grouping element for individual 'strands' of notes, rests, etc. that may
    or may not actually be rendered on staff lines; that is, both diastematic and non-diastematic
    signs.

    In MEI 2013: pg.444 (458 in PDF) (MEI.shared module)

    :param elem: The ``<staff>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: The :class:`Voice` classes corresponding to the ``<layer>`` tags in ``elem``.
    :rtype: list of :class:`music21.stream.Voice`

    Attributes Implemented:
    =======================
    - <layer> contained within

    Attributes Ignored:
    ===================
    - xml:id. Because the function does not return a music21 object, we cannot use @xml:id.

    Attributes In Progress:
    =======================

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
    att.declaring (@decls)
    att.facsimile (@facs)
    att.staff.log (@def)
                  (att.meterconformance (@metcon))
    att.staff.vis (att.visibility (@visible))
    att.staff.gesatt.staff.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                               (att.alignment (@when)))

    May Contain:
    ============
    MEI.cmn: ossia
    MEI.critapp: app
    MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied unclear
    MEI.shared: annot pb sb scoreDef staffDef
    MEI.text: div
    MEI.usersymbols: anchoredText curve line symbol
    '''
    # mapping from tag name to our converter function
    layerTagName = '{http://www.music-encoding.org/ns/mei}layer'
    tagToFunction = {}
    post = []

    # track the @n values given to layerFromElement()
    currentNValue = '1'

    # iterate all immediate children
    for eachTag in elem.findall('*'):
        if layerTagName == eachTag.tag:
            thisLayer = layerFromElement(eachTag, currentNValue)
            # check for objects that must appear in the Measure, but are currently in the Voice
            for eachThing in thisLayer:
                if isinstance(eachThing, (clef.Clef,)):
                    post.append(eachThing)
                    thisLayer.remove(eachThing)
            post.append(thisLayer)
            currentNValue = str(int(currentNValue) + 1)  # inefficient, but we need a string
        elif eachTag.tag in tagToFunction:
            # NB: this won't be tested until there's something in tagToFunction
            post.append(tagToFunction[eachTag.tag](eachTag))
        else:  # DEBUG
            print('!! unprocessed %s in %s' % (eachTag.tag, elem.tag))  # DEBUG

    return post


def measureFromElement(elem, backupNum=None, expectedNs=None):
    # TODO: write tests
    '''
    <measure> Unit of musical time consisting of a fixed number of note-values of a given type, as
    determined by the prevailing meter, and delimited in musical notation by two bar lines.

    In MEI 2013: pg.365 (379 in PDF) (MEI.cmn module)

    :param elem: The ``<measure>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param int backupNum: A fallback value for the resulting :class:`Measure` objects' ``number``
        attribute. The default will be 0.
    :param expectedNs: A list of the expected @n attributes for the <staff> tags in this <measure>.
        If an expected <staff> isn't in the <measure>, it will be created with a full-measure rest.
        The default is ``None``.
    :type expectedNs: iterable of str
    :returns: A dictionary where keys are the @n attributes for <staff> tags found in this
        <measure>, and values are :class:`~music21.stream.Measure` objects that should be appended
        to the :class:`Part` instance with the value's @n attributes.
    :rtype: dict of :class:`music21.stream.Measure`

    Attributes Implemented:
    =======================

    Attributes Ignored:
    ===================
    - xml:id, since it would logically require every :class:`Measure` object's ``id`` attribute
        to be set identically, running contrary to the point of unique ``id`` fields.

    Attributes In Progress:
    =======================
    - <staff> contained within
    - @right (att.measure.log)
    - @left (att.measure.log)

    Attributes not Implemented:
    ===========================
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.declaring (@decls)
    att.facsimile (@facs)
    att.typed (@type, @subtype)
    att.pointing (@xlink:actuate, @xlink:role, @xlink:show, @target, @targettype, @xlink:title)
    att.measure.log (@left, @right)
                    (att.meterconformance.bar (@metcon, @control))
    att.measure.vis (att.barplacement (@barplace, @taktplace))
                    (att.measurement (@unit))
                    (att.width (@width))
    att.measure.ges (att.timestamp.performed (@tstamp.ges, @tstamp.real))
    att.measure.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                    (att.alignment (@when)))
                    (att.joined (@join))

    May Contain:
    ============
    MEI.cmn: arpeg beamSpan bend breath fermata gliss hairpin harpPedal octave ossia pedal reh slur
             tie tupletSpan
    MEI.cmnOrnaments: mordent trill turn
    MEI.critapp: app
    MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied
                   unclear
    MEI.harmony: harm
    MEI.lyrics: lyrics
    MEI.midi: midi
    MEI.shared: annot dir dynam pb phrase sb staffDef tempo
    MEI.text: div
    MEI.usersymbols: anchoredText curve line symbol
    '''
    post = {}

    backupNum = 0 if backupNum is None else backupNum
    expectedNs = [] if expectedNs is None else expectedNs

    # mapping from tag name to our converter function
    staffTagName = '{http://www.music-encoding.org/ns/mei}staff'
    tagToFunction = {}

    # track the bar's duration
    barDuration = None

    # iterate all immediate children
    for eachTag in elem.findall('*'):
        if staffTagName == eachTag.tag:
            post[eachTag.get('n')] = stream.Measure(staffFromElement(eachTag),
                                                    number=int(elem.get('n', backupNum)))
            if barDuration is None:
                barDuration = post[eachTag.get('n')].duration.quarterLength
        elif eachTag.tag in tagToFunction:
            # NB: this won't be tested until there's something in tagToFunction
            post.append(tagToFunction[eachTag.tag](eachTag))
        else:  # DEBUG
            print('!! unprocessed %s in %s' % (eachTag.tag, elem.tag))  # DEBUG

    # create rest-filled measures for expected parts that had no <staff> tag in this <measure>
    for eachN in expectedNs:
        if eachN not in post:
            restVoice = stream.Voice([note.Rest(quarterLength=barDuration)])
            restVoice.id = '1'
            post[eachN] = stream.Measure([restVoice], number=int(elem.get('n', backupNum)))

    # assign left and right barlines
    if elem.get('left') is not None:
        for eachMeasure in six.itervalues(post):
            if not isinstance(eachMeasure, stream.Measure):
                continue
            eachMeasure.leftBarline = _barlineFromAttr(elem.get('left'))
    if elem.get('right') is not None:
        for eachMeasure in six.itervalues(post):
            if not isinstance(eachMeasure, stream.Measure):
                continue
            eachMeasure.rightBarline = _barlineFromAttr(elem.get('right'))

    return post


#------------------------------------------------------------------------------
_DOC_ORDER = [noteFromElement, restFromElement]

if __name__ == "__main__":
    import music21
    from music21.mei import test_main
    music21.mainTest(test_main.TestThings,
                     test_main.TestAttrTranslators,
                     test_main.TestNoteFromElement,
                     test_main.TestRestFromElement,
                     test_main.TestChordFromElement,
                     test_main.TestClefFromElement,
                     test_main.TestLayerFromElement,
                     test_main.TestStaffFromElement,)

#------------------------------------------------------------------------------
# eof
