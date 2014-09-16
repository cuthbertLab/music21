# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         mei/base.py
# Purpose:      Public methods for the MEI module
#
# Authors:      Christopher Antila
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
These are the public methods for the MEI module.

To convert a string with MEI markup into music21 objects, use :func:`convertFromString`.

In the future, most of the functions in this module should be moved to a separate, import-only
module, so that functions for writing music21-to-MEI will fit nicely.

**Simple "How-To"**

Use :class:`MeiToM21Converter` to convert a string to a set of music21 objects. In the future, the
:class:`M21ToMeiConverter` class will convert a set of music21 objects into a string with an MEI
document.

TODO: make this use an actual file
>> from music21 import *
>> meiString = convert_some_file_to_a_string()
>> conv = mei.MeiToM21Converter(meiString)
>> result = conv.run()
>> type(result)
<class 'music21.stream.Score'>

**Ignored Elements**

The following elements are not yet imported, though you might expect they would be:

* ``<sb>``: a system break, since this is not usually semantically significant
* ``<lb>``: a line break, since this is not usually semantically significant
* ``<pb>``: a page break, since this is not usually semantically significant

**Where Elements Are Processed**

Many elements are handled in a function called :func:`tagFromElement`, where "tag" is replaced by
the element's tag name (e.g., :func:`staffDefFromElement` for <staffDef> elements). These public
functions perform a transformation operation from a Python :class:`~xml.etree.ElementTree.Element`
object to its corresponding music21 element.

However, certain elements are processed primarily in another way, by private functions. Rather than
transforming an :class:`Element` object into a music21 object, these modify the MEI document tree
by adding instructions for the :func:`tagFromElement` functions. The elements processed by private
functions include:

* <slur>
* <tie>
* <beamSpan>
* <tupletSpan>

**Guidelines for Encoders**

While we aim for the best possible compatibility, the MEI specification is large. The following
guidelines will help you produce a file that this MEI-to-music21 module will import correctly and
in the most efficient way, but should not necessarily be considered recommendations when encoding
for any other context.

* Tuplets indicated only in a @tuplet attribute do not work.
* For elements that allow @startid, @endid, and @plist attributes, use all three. This is especially
  important for tuplets.
* For any tuplet, specify at least @num and @numbase. The module refuses to import a tuplet that
  does not have the @numbase attribute.
* Retain consistent @n values for the same voice, staff, and instrument throughout the score.
* Always indicate the duration of an <mRest> element.
'''

# Determine which ElementTree implementation to use.
# We'll prefer the C-based versions if available, since they provide better performance.
try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree

from uuid import uuid4
from collections import defaultdict

# music21
from music21 import exceptions21
from music21 import note
from music21 import duration
from music21 import articulations
from music21 import pitch
from music21 import stream
from music21 import chord
from music21 import clef
from music21 import meter
from music21 import key
from music21 import instrument
from music21 import interval
from music21 import bar
from music21 import spanner
from music21 import tie
from music21 import metadata

from music21 import environment
_MOD = 'mei.base'
environLocal = environment.Environment(_MOD)

# six
from music21.ext import six
from six.moves import xrange  # pylint: disable=redefined-builtin,import-error
from six.moves import range  # pylint: disable=redefined-builtin,import-error


# Module-Level Constants
#------------------------------------------------------------------------------
_XMLID = '{http://www.w3.org/XML/1998/namespace}id'
_MEINS = '{http://www.music-encoding.org/ns/mei}'
# when these tags aren't processed, we won't worry about them (at least for now)
_IGNORE_UNPROCESSED = ('{}sb'.format(_MEINS),  # system break
                       '{}lb'.format(_MEINS),  # line break
                       '{}pb'.format(_MEINS),  # page break
                       '{}slur'.format(_MEINS),  # slurs; handled in convertFromString()
                       '{}tie'.format(_MEINS),  # ties; handled in convertFromString()
                       '{}tupletSpan'.format(_MEINS),  # tuplets; handled in convertFromString()
                       '{}beamSpan'.format(_MEINS),  # beams; handled in convertFromString()
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
    "When an element has an invalid attribute."
    pass

class MeiElementError(exceptions21.Music21Exception):
    "When an element itself is invalid."
    pass

# Text Strings for Error Conditions
#------------------------------------------------------------------------------
_INVALID_XML_DOC = 'MEI document is not valid XML.'
_WRONG_ROOT_ELEMENT = 'Root element should be <mei>, not <{}>.'
_UNKNOWN_TAG = 'Found unexpected tag while parsing MEI: <{}>.'
_UNEXPECTED_ATTR_VALUE = 'Unexpected value for "{}" attribute: {}'
_SEEMINGLY_NO_PARTS = 'There appear to be no <staffDef> tags in this score.'
_MISSING_VOICE_ID = 'Found a <layer> without @n attribute and no override.'
_CANNOT_FIND_XMLID = 'Could not find the @{} so we could not create the {}.'
_MISSING_TUPLET_DATA = 'Both @num and @numbase attributes are required on <tuplet> tags.'
_UNIMPLEMENTED_IMPORT = 'Importing {} without {} is not yet supported.'


# Module-level Functions
#------------------------------------------------------------------------------
class MeiToM21Converter(object):
    '''
    A :class:`MeiToM21Converter` instance manages the conversion of an MEI document into music21
    objects.
    '''

    def __init__(self, theDocument):
        '''
        If ``theDocument`` does not have <mei> as the root element, the class raises an
        :class:`MeiElementError`. If ``theDocument`` is not a valid XML file, the class raises an
        :class:`MeiValidityError`.

        :param str theDocument: A string containing an MEI document.
        :raises: :exc:`MeiElementError` when the root element is not <mei>
        :raises: :exc:`MeiValidityError` when the MEI file is not valid XML.
        '''
        environLocal.printDebug('*** initializing MeiToM21Converter')

        try:
            self.documentRoot = ETree.fromstring(theDocument)
        except ETree.ParseError:
            raise MeiValidityError(_INVALID_XML_DOC)

        if isinstance(self.documentRoot, ETree.ElementTree):
            self.documentRoot = self.documentRoot.getroot()

        if '{http://www.music-encoding.org/ns/mei}mei' != self.documentRoot.tag:
            raise MeiElementError(_WRONG_ROOT_ELEMENT.format(self.documentRoot.tag))

    def run(self):
        '''
        Convert a string that is an MEI document into a music21 object.

        :return: The :class:`Score` corresponding to the MEI document.
        :rtype: :class:`music21.stream.Score`
        '''
        # TODO: this replaces convertFromString()
        return convertFromString(self.documentRoot)


# Module-level Functions
#------------------------------------------------------------------------------
def convertFromString(dataStr):
    '''
    Convert a string from MEI markup to music21 objects.

    :parameter str dataStr: A string with MEI markup.
    :returns: A :class:`Stream` subclass, depending on the markup in the ``dataStr``.
    :rtype: :class:`music21.stream.Stream`
    '''

    # TODO: this is temporary
    documentRoot = dataStr

    # This defaultdict stores extra, music21-specific attributes that we add to elements to help
    # importing. The key is an element's @xml:id, and the value is a regular dict with keys
    # corresponding to attributes we'll add and values corresponding to those attributes's values.
    m21Attr = defaultdict(lambda: {})

    slurBundle = spanner.SpannerBundle()

    _ppSlurs(documentRoot, m21Attr, slurBundle)
    _ppTies(documentRoot, m21Attr)
    _ppBeams(documentRoot, m21Attr)
    _ppTuplets(documentRoot, m21Attr)
    _ppConclude(documentRoot, m21Attr)

    environLocal.printDebug('*** preparing part and staff definitions')

    # Get a tuple of all the @n attributes for the <staff> tags in this score. Each <staff> tag
    # corresponds to what will be a music21 Part. The specificer, the better. What I want to do is
    # get all the <staffDef> tags that are in the <score>, no matter where they appear. This is just
    # to fetch everything that will affect the maximum number of parts that might happen at a time.
    # TODO: this doesn't always work. For some scores where a part uses more than one clef, more
    #       than one @n is picked up, so more than one staff appears---though all the notes are put
    #       in the highest relevant staff
    allPartNs = allPartsPresent(documentRoot.findall('.//{mei}music//{mei}score//{mei}staffDef'.format(mei=_MEINS)))

    # holds the music21.stream.Part that we're building
    parsed = {n: stream.Part() for n in allPartNs}
    # holds things that should go in the following Measure
    inNextMeasure = {n: stream.Part() for n in allPartNs}

    # set the initial Instrument for each staff
    for eachN in allPartNs:
        eachStaffDef = staffDefFromElement(documentRoot.find(
            './/{mei}music//{mei}staffDef[@n="{n}"]'.format(mei=_MEINS, n=eachN)))
        if eachStaffDef is not None:
            parsed[eachN].append(eachStaffDef)
        else:
            # TODO: try another strategy to get instrument information
            pass

    # process a <scoreDef> tag that happen before a <section> tag
    scoreDefResults = documentRoot.find('.//{mei}music//{mei}scoreDef'.format(mei=_MEINS))
    if scoreDefResults is not None:
        # scoreDefResults would be None if there is no <scoreDef> outside of a <section>, but...
        # TODO: we don't actually know whether this <scoreDef> happens before or between <section>
        scoreDefResults = scoreDefFromElement(scoreDefResults)
        for allPartObject in scoreDefResults['all-part objects']:
            for partN in allPartNs:
                inNextMeasure[partN].append(allPartObject)

    environLocal.printDebug('*** processing measures')

    backupMeasureNum = 0
    for eachSection in documentRoot.iterfind('.//{mei}music//{mei}score//*[{mei}measure]'.format(mei=_MEINS)):
        # TODO: sections aren't divided or treated specially, yet
        for eachObject in eachSection:
            if '{http://www.music-encoding.org/ns/mei}measure' == eachObject.tag:
                # TODO: MEI's "rptboth" barlines require handling at the multi-measure level
                # TODO: follow the use of @n described on pg.585 (599) of the MEI Guidelines
                backupMeasureNum += 1
                # process all the stuff in the <measure>
                measureResult = measureFromElement(eachObject, backupMeasureNum, allPartNs, slurBundle=slurBundle)
                # process and append each part's stuff to the staff
                for eachN in allPartNs:
                    # TODO: what if an @n doesn't exist in this <measure>?
                    # insert objects specified in the immediately-preceding <scoreDef>
                    for eachThing in inNextMeasure[eachN]:
                        measureResult[eachN].insert(0, eachThing)
                    inNextMeasure[eachN] = []
                    # if it's the first measure, pad for a possible anacrusis
                    # TODO: this may have to change when @n is better set
                    # TODO: this doesn't actually solve the "pick-up measure" problem
                    if 1 == backupMeasureNum:
                        measureResult[eachN].padAsAnacrusis()
                    # add this Measure to the Part
                    parsed[eachN].append(measureResult[eachN])
            elif '{http://www.music-encoding.org/ns/mei}scoreDef' == eachObject.tag:
                scoreDefResults = scoreDefFromElement(eachObject)
                # spread all-part elements across all the parts
                for allPartObject in scoreDefResults['all-part objects']:
                    for partN in allPartNs:
                        inNextMeasure[partN].append(allPartObject)
            elif '{http://www.music-encoding.org/ns/mei}staffDef' == eachObject.tag:
                whichPart = eachObject.get('n')
                # to process this here, we need @n. But if something refers to this <staffDef> with
                # the @xml:id, it may not have an @n
                if whichPart is not None:
                    staffDefResults = staffDefFromElement(eachObject)
                    for thisPartObject in staffDefResults:
                        parsed[whichPart].append(thisPartObject)
            elif eachObject.tag not in _IGNORE_UNPROCESSED:
                environLocal.printDebug('unprocessed {} in {}'.format(eachObject.tag, eachSection.tag))

    # TODO: check if there's anything left in "inNextMeasure"

    # Convert the dict to a Score
    # We must iterate here over "allPartNs," which preserves the part-order found in the MEI
    # document. Iterating the keys in "parsed" would not preserve the order.
    environLocal.printDebug('*** making the Score')
    parsed = [parsed[n] for n in allPartNs]
    post = stream.Score(parsed)

    # process tuplets indicated by the "m21TupletSearch" attribute (i.e., in the MEI file these are
    # encoded with a <tupletSpan> that has @startid and @endid but not @plist).
    post = _postGuessTuplets(post)

    # insert metadata
    post.metadata = makeMetadata(documentRoot)

    # put slurs in the Score
    post.append(slurBundle.list)

    return post


def safePitch(name, accidental=None, octave=''):
    '''
    Safely build a :class:`Pitch` from a string.

    When :meth:`Pitch.__init__` is given an empty string, it raises a :exc:`PitchException`. This
    function instead returns a default :class:`Pitch` instance.

    :param str name: Desired name of the :class:`Pitch`.
    :param str accidental: (Optional) Symbol for the accidental.
    :param octave: (Optional) Octave number.
    :type octave: str or int

    :returns: A :class:`Pitch` with the appropriate properties.
    :rtype: :class:`music21.pitch.Pitch`

    >>> from music21.mei.base import safePitch  # OMIT_FROM_DOCS
    >>> safePitch('D#6')
    <music21.pitch.Pitch D#6>
    >>> safePitch('D', '#', '6')
    <music21.pitch.Pitch D#6>
    '''
    if len(name) < 1:
        return pitch.Pitch()
    elif accidental is None:
        return pitch.Pitch(name + octave)
    else:
        return pitch.Pitch(name, accidental=accidental, octave=int(octave))


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
    # pylint: disable=line-too-long
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
        documentRoot.findall('.//{http://www.music-encoding.org/ns/mei}score//{http://www.music-encoding.org/ns/mei}staffDef')

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
                    'ts': '###', 'tf': '---', 'n': 'n', 'nf': '-', 'ns': '#', 'su': '???',
                    'sd': '???', 'fu': '???', 'fd': '???', 'nu': '???', 'nd': '???', None: None}

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
                    # TODO: these aren't implemented in music21, so I'll make new ones
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

    >>> from music21.mei.base import _attrTranslator, _ACCID_ATTR_DICT, _DUR_ATTR_DICT
    >>> _attrTranslator('s', 'accid', _ACCID_ATTR_DICT)
    '#'
    >>> _attrTranslator('9', 'dur', _DUR_ATTR_DICT)
    Traceback (most recent call last):
      File "/usr/lib64/python2.7/doctest.py", line 1289, in __run
        compileflags, 1) in test.globs
      File "<doctest base._attrTranslator[2]>", line 1, in <module>
        _attrTranslator('9', 'dur', _DUR_ATTR_DICT)
      File "/home/crantila/Documents/DDMAL/programs/music21/music21/mei/base.py", line 131, in _attrTranslator
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
        return (articulations.StrongAccent(), articulations.Staccato())
    elif 'ten-stacc' == attr:
        return (articulations.Tenuto(), articulations.Staccato())
    else:
        return (_attrTranslator(attr, 'artic', _ARTIC_ATTR_DICT)(),)


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

    >>> from music21.mei.base import _sharpsFromAttr
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


# "Preprocessing" and "Postprocessing" Functions for convertFromString()
#------------------------------------------------------------------------------
def _ppSlurs(documentRoot, m21Attr, slurBundle):
    '''
    Pre-processing helper for :func:`convertFromString` that handles slurs specified in <slur>
    elements.

    :param documentRoot: The root tag of the MEI document being imported.
    :type documentRoot: :class:`xml.etree.ElementTree.Element`
    :param m21Attr: A mapping of @xml:id attributes to mappings of attributes-to-values on the
        element with that @xml:id (read below for more information).
    :type m21Attr: defaultdict
    :param slurBundle: The :class:`SpannerBundle` that holds :class:`Slur` objects for the MEI
        document being imported.
    :type slurBundle: :class:`music21.spanner.SpannerBundle`
    :returns: The ``m21Attr`` mapping after specified transformations.
    :rtype: defaultdict

    **Example of ``m21Attr``**

    The ``m21Attr`` argument must be a defaultdict that returns an empty (regular) dict for
    non-existant keys. The defaultdict stores the @xml:id attribute of an element; the dict holds
    attribute names and their values that should be added to the element with the given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.

    **This Preprocessor**
    The slur preprocessor adds @m21SlurStart and @m21SlurEnd attributes. The value of these
    attributes is the ``idLocal`` of a :class:`Slur` in the ``slurBundle`` argument. This means, for
    example, that if you encounter an element like ``<note m21SlurStart="82f87cd7"/>``, the
    resulting :class:`music21.note.Note` should be set as the starting point of the slur with and
    ``idLocal`` of ``'82f87cd7'``.
    '''
    environLocal.printDebug('*** pre-processing slurs')
    # pre-processing for <slur> tags
    for eachSlur in documentRoot.iterfind('.//{mei}music//{mei}score//{mei}slur'.format(mei=_MEINS)):
        if eachSlur.get('startid') is not None and eachSlur.get('endid') is not None:
            thisIdLocal = str(uuid4())
            thisSlur = spanner.Slur()
            thisSlur.idLocal = thisIdLocal
            slurBundle.append(thisSlur)

            m21Attr[removeOctothorpe(eachSlur.get('startid'))]['m21SlurStart'] = thisIdLocal
            m21Attr[removeOctothorpe(eachSlur.get('endid'))]['m21SlurEnd'] = thisIdLocal
        else:
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<slur>', '@startid and @endid'))

    return m21Attr


def _ppTies(documentRoot, m21Attr):
    '''
    Pre-processing helper for :func:`convertFromString` that handles ties specified in <tie> elements.

    :param documentRoot: The root tag of the MEI document being imported.
    :type documentRoot: :class:`xml.etree.ElementTree.Element`
    :param m21Attr: A mapping of @xml:id attributes to mappings of attributes-to-values on the
        element with that @xml:id (read below for more information).
    :type m21Attr: defaultdict
    :returns: The ``m21Attr`` mapping after specified transformations.
    :rtype: defaultdict

    **Example of ``m21Attr``**

    The ``m21Attr`` argument must be a defaultdict that returns an empty (regular) dict for
    non-existant keys. The defaultdict stores the @xml:id attribute of an element; the dict holds
    attribute names and their values that should be added to the element with the given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.

    **This Preprocessor**
    The tie preprocessor adds @tie attributes. The value of these attributes conforms to the MEI
    Guidelines, so no special action is required.
    '''
    environLocal.printDebug('*** pre-processing ties')
    for eachTie in documentRoot.iterfind('.//{mei}music//{mei}score//{mei}tie'.format(mei=_MEINS)):
        if eachTie.get('startid') is not None and eachTie.get('endid') is not None:
            m21Attr[removeOctothorpe(eachTie.get('startid'))]['tie'] = 'i'
            m21Attr[removeOctothorpe(eachTie.get('endid'))]['tie'] = 't'
        else:
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<tie>', '@startid and @endid'))

    return m21Attr


def _ppBeams(documentRoot, m21Attr):
    '''
    Pre-processing helper for :func:`convertFromString` that handles beams specified in <beamSpan>
    elements.

    :param documentRoot: The root tag of the MEI document being imported.
    :type documentRoot: :class:`xml.etree.ElementTree.Element`
    :param m21Attr: A mapping of @xml:id attributes to mappings of attributes-to-values on the
        element with that @xml:id (read below for more information).
    :type m21Attr: defaultdict
    :returns: The ``m21Attr`` mapping after specified transformations.
    :rtype: defaultdict

    **Example of ``m21Attr``**

    The ``m21Attr`` argument must be a defaultdict that returns an empty (regular) dict for
    non-existant keys. The defaultdict stores the @xml:id attribute of an element; the dict holds
    attribute names and their values that should be added to the element with the given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.

    **This Preprocessor**
    The slur preprocessor adds the @m21Beam attribute. The value of this attribute is either
    ``'start'``, ``'continue'``, or ``'stop'``, indicating the music21 ``type`` of the primary
    beam attached to this element.
    '''
    environLocal.printDebug('*** pre-processing beams')
    # pre-processing for <beamSpan> elements
    for eachBeam in documentRoot.iterfind('.//{mei}music//{mei}score//{mei}beamSpan'.format(mei=_MEINS)):
        if eachBeam.get('startid') is None or eachBeam.get('endid') is None:
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<beamSpan>', '@startid and @endid'))
            continue

        m21Attr[removeOctothorpe(eachBeam.get('startid'))]['m21Beam'] = 'start'
        m21Attr[removeOctothorpe(eachBeam.get('endid'))]['m21Beam'] = 'stop'

        # iterate things in the @plist attribute
        for eachXmlid in eachBeam.get('plist', '').split(' '):
            eachXmlid = removeOctothorpe(eachXmlid)
            if 0 == len(eachXmlid):
                # this is either @plist not set or extra spaces around the contained xml:id values
                pass
            if 'm21Beam' not in m21Attr[eachXmlid]:
                # only set to 'continue' if it wasn't previously set to 'start' or 'stop'
                m21Attr[eachXmlid]['m21Beam'] = 'continue'

    return m21Attr


def _ppTuplets(documentRoot, m21Attr):
    '''
    Pre-processing helper for :func:`convertFromString` that handles tuplets specified in
    <tupletSpan> elements.

    :param documentRoot: The root tag of the MEI document being imported.
    :type documentRoot: :class:`xml.etree.ElementTree.Element`
    :param m21Attr: A mapping of @xml:id attributes to mappings of attributes-to-values on the
        element with that @xml:id (read below for more information).
    :type m21Attr: defaultdict
    :returns: The ``m21Attr`` mapping after specified transformations.
    :rtype: defaultdict

    **Example of ``m21Attr``**

    The ``m21Attr`` argument must be a defaultdict that returns an empty (regular) dict for
    non-existant keys. The defaultdict stores the @xml:id attribute of an element; the dict holds
    attribute names and their values that should be added to the element with the given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.

    **This Preprocessor**
    The slur preprocessor adds @m21TupletNum and @m21TupletNumbase attributes. The value of these
    attributes corresponds to the @num and @numbase attributes found on a <tuplet> element.

    This preprocessor also performs a significant amount of guesswork to try to handle <tupletSpan>
    elements that do not include a @plist attribute.
    '''
    environLocal.printDebug('*** pre-processing tuplets')
    # pre-processing <tupletSpan> tags
    for eachTuplet in documentRoot.iterfind('.//{mei}music//{mei}score//{mei}tupletSpan'.format(mei=_MEINS)):
        if ((eachTuplet.get('startid') is None or eachTuplet.get('endid') is None) and
            eachTuplet.get('plist') is None):
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<tupletSpan>', '@startid and @endid or @plist'))
        elif eachTuplet.get('plist') is not None:
            # Ideally (for us) <tupletSpan> elements will have a @plist that enumerates the
            # @xml:id of every affected element. In this case, tupletSpanFromElement() can use the
            # @plist to add our custom @m21TupletNum and @m21TupletNumbase attributes.
            # TODO: use @startid and @endid, if present, to set the duration.tuplets "type"
            for eachXmlid in eachTuplet.get('plist', '').split(' '):
                eachXmlid = removeOctothorpe(eachXmlid)
                if 0 < len(eachXmlid):
                    # protect against extra spaces around the contained xml:id values
                    m21Attr[eachXmlid]['m21TupletNum'] = eachTuplet.get('num')
                    m21Attr[eachXmlid]['m21TupletNumbase'] = eachTuplet.get('numbase')
        else:
            # For <tupletSpan> elements that don't give a @plist attribute, we have to do some
            # guesswork and hope we find all the related elements. Right here, we're only setting
            # the "flags" that this guesswork must be done later.
            startid = removeOctothorpe(eachTuplet.get('startid'))
            endid = removeOctothorpe(eachTuplet.get('endid'))

            m21Attr[startid]['m21TupletSearch'] = 'start'
            m21Attr[startid]['m21TupletNum'] = eachTuplet.get('num')
            m21Attr[startid]['m21TupletNumbase'] = eachTuplet.get('numbase')
            m21Attr[endid]['m21TupletSearch'] = 'end'
            m21Attr[endid]['m21TupletNum'] = eachTuplet.get('num')
            m21Attr[endid]['m21TupletNumbase'] = eachTuplet.get('numbase')

    return m21Attr


def _ppConclude(documentRoot, m21Attr):
    # TODO: test this function
    '''
    Pre-processing helper for :func:`convertFromString` that adds attributes from ``m21Attr`` to the
    appropriate elements in ``documentRoot``.

    :param documentRoot: The root tag of the MEI document being imported.
    :type documentRoot: :class:`xml.etree.ElementTree.Element`
    :param m21Attr: A mapping of @xml:id attributes to mappings of attributes-to-values on the
        element with that @xml:id (read below for more information).
    :type m21Attr: defaultdict
    :returns: The ``documentRoot`` element.
    :rtype: :class:`~xml.etree.ElementTree.Element`

    **Example of ``m21Attr``**

    The ``m21Attr`` argument must be a defaultdict that returns an empty (regular) dict for
    non-existant keys. The defaultdict stores the @xml:id attribute of an element; the dict holds
    attribute names and their values that should be added to the element with the given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.

    **This Preprocessor**
    The slur preprocessor adds all attributes from the ``m21Attr`` to the appropriate element in
    ``documentRoot``. In effect, it finds the element corresponding to each key in ``m21Attr``,
    then iterates the keys in its dict, *appending* the ``m21Attr``-specified value to any existing
    value.
    '''
    environLocal.printDebug('*** concluding pre-processing')
    # conclude pre-processing by adding music21-specific attributes to their respective elements
    for eachObject in documentRoot.iterfind('*//*'):
        # we have a defaultdict, so this "if" isn't strictly necessary; but without it, every single
        # element with an @xml:id creates a new, empty dict, which would consume a lot of memory
        if eachObject.get(_XMLID) in m21Attr:
            for eachAttr in m21Attr[eachObject.get(_XMLID)]:
                eachObject.set(eachAttr, eachObject.get(eachAttr, '') + m21Attr[eachObject.get(_XMLID)][eachAttr])

    return documentRoot


def _postGuessTuplets(post):
    # TODO: this tuplet-guessing still leaves the Measure at the wrong offset in the Part
    # TODO: finish tests for this function
    # TODO: make this work for nested tuplets
    # TODO: make this work for simultaneous tuplets in different voices in the same part
    '''
    A "postprocessing" function that takes an otherwise fully-imported score and completes the
    import process by guessing tuplets indicated with :attr:`m21TupletSearch` attributes.

    This is for the tuplets given in a <tupletSpan> with @startid and @endid but not @plist; we
    need to guess which elements are in the tuplet. Since we know the starting object and the
    ending object, we'll assume that all the tuplet objects are in the same Voice, so we'll use a
    list of all the Note/Rest/Chord objects in that Voice and change the duration for each of the
    objects between the @startid and @endid ones. (Grace notes retain a 0.0 duration).

    .. note:: At the moment, this will likely only work for simple tuplets---not nested tuplets.

    .. note:: At the moment, this will likely only work for a tuplet in one voice at a time.

    :param post: The :class:`Score` in which to search for objects that have the
        :attr:`m21TupletSearch` attribute.
    :type post: :class:`music21.stream.Score`
    :returns: The same :class:`Score` adjusted for tuplets.
    '''
    environLocal.printDebug('*** correcting durations by guessing tuplets')

    for eachPart in post.parts:
        inATuplet = False
        tupletNum = None
        tupletNumbase = None
        previousOffset = None
        previousQuarterLength = None
        activeVoiceId = None
        missingDuration = 0.0
        # "missingDuration" is the quarterLength of the duration left by making a tuplet (i.e.,
        # the difference between a tuplet's actual duration and its duration it would have (if it
        # weren't in a tuplet, which is the duration it has on initial creation)

        for eachNote in eachPart._yieldElementsDownward(streamsOnly=False,
                                                        classFilter=[note.GeneralNote]):
            if hasattr(eachNote, 'm21TupletSearch') and eachNote.m21TupletSearch == 'start':
                inATuplet = True
                tupletNum = int(eachNote.m21TupletNum)
                tupletNumbase = int(eachNote.m21TupletNumbase)
                activeVoiceId = getVoiceId(eachNote.sites.get())

                del eachNote.m21TupletSearch
                del eachNote.m21TupletNum
                del eachNote.m21TupletNumbase

            if inATuplet and getVoiceId(eachNote.sites.get()) == activeVoiceId:
                previousDuration = eachNote.duration.quarterLength

                scaleToTuplet(eachNote, ETree.Element('', m21TupletNum=tupletNum,
                                                      m21TupletNumbase=tupletNumbase))

                missingDuration += (previousDuration - eachNote.duration.quarterLength)

                if previousOffset is None:
                    # if this is the first note in the tuplet, set it to "start"; the offset remains
                    eachNote.duration.tuplets[0].type = 'start'
                else:
                    # the offset of following notes in the tuplet must be adjusted
                    eachNote.offset = previousOffset + previousQuarterLength

                previousOffset = eachNote.offset
                previousQuarterLength = eachNote.duration.quarterLength

                if hasattr(eachNote, 'm21TupletSearch') and eachNote.m21TupletSearch == 'end':
                    # we've reached the end of the tuplet!
                    eachNote.duration.tuplets[0].type = 'stop'

                    # We have to adjust the offset of all the elements following a tuplet, until
                    # the end of that Measure. I have to find a faster way to do it than this.
                    # NOTE: this is very slow
                    # TODO: this causes problems because it adjusts every measure, rather than only the measure with tuplets
                    for eachThing in eachPart.recurse(streamsOnly=True):
                        eachThing.shiftElements(offset=(-1 * missingDuration),
                                                startOffset=(previousOffset + previousQuarterLength))

                    del eachNote.m21TupletSearch
                    del eachNote.m21TupletNum
                    del eachNote.m21TupletNumbase

                    # reset the tuplet-tracking variables
                    inATuplet = False
                    previousOffset = None
                    missingDuration = 0.0

    return post


# Helper Functions
#------------------------------------------------------------------------------
def _processEmbeddedElements(elements, mapping, slurBundle=None):
    '''
    From an iterable of MEI ``elements``, use functions in the ``mapping`` to convert each element
    to its music21 object. This function was designed for use with elements that may contain other
    elements; the contained elements will be converted as appropriate.

    If an element itself has embedded elements (i.e., its convertor function in ``mapping`` returns
    a sequence), those elements will appear in the returned sequence in order---there are no
    hierarchic lists.

    :param elements: A list of :class:`Element` objects to convert to music21 objects.
    :type elements: iterable of :class:`~xml.etree.ElementTree.Element`
    :param mapping: A dictionary where keys are the :attr:`Element.tag` attribute and values are
        the function to call to convert that :class:`Element` to a music21 object.
    :type mapping: mapping of str to function
    :param slurBundle: A slur bundle, as used by the other :func:`*fromElements` functions.
    :type slurBundle: :class:`music21.spanner.SlurBundle`
    :returns: A list of the music21 objects returned by the converter functions, or an empty list
        if no objects were returned.
    :rtype: sequence of :class:`~music21.base.Music21Object`

    **Examples:**

    Because there is no ``'rest'`` key in the ``mapping``, that :class:`Element` is ignored:

    >>> from xml.etree.ElementTree import Element  #_DOCS_HIDE
    >>> from music21.mei.base import _processEmbeddedElements  #_DOCS_HIDE
    >>> elements = [Element('note'), Element('rest'), Element('note')]
    >>> mapping = {'note': lambda x, y: note.Note('D2')}
    >>> _processEmbeddedElements(elements, mapping)
    [<music21.note.Note D>, <music21.note.Note D>]

    The "beam" element holds "note" elements. All elements appear in a single level of the list:

    >>> elements = [Element('note'), Element('beam'), Element('note')]
    >>> mapping = {'note': lambda x, y: note.Note('D2'),
    ...            'beam': lambda x, y: [note.Note('E2') for _ in range(2)]}
    >>> _processEmbeddedElements(elements, mapping)
    [<music21.note.Note D>, <music21.note.Note E>, <music21.note.Note E>, <music21.note.Note D>]
    '''
    post = []

    for eachTag in elements:
        if eachTag.tag in mapping:
            result = mapping[eachTag.tag](eachTag, slurBundle)
            if isinstance(result, (tuple, list)):
                for eachObject in result:
                    post.append(eachObject)
            else:
                post.append(result)
        elif eachTag.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug('found an unprocessed <{}> element'.format(eachTag.tag))

    return post


def _timeSigFromAttrs(elem):
    '''
    From any tag with @meter.count and @meter.unit attributes, make a :class:`TimeSignature`.

    :param :class:`~xml.etree.ElementTree.Element` elem: An :class:`Element` with @meter.count and
        @meter.unit attributes.
    :returns: The corresponding time signature.
    :rtype: :class:`~music21.meter.TimeSignature`
    '''
    return meter.TimeSignature('{!s}/{!s}'.format(elem.get('meter.count'), elem.get('meter.unit')))


def _keySigFromAttrs(elem):
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
    '''
    From any element with the @trans.diat and @trans.semi attributes, make an :class:`Interval` that
    represents the interval of transposition from written to concert pitch.

    :param :class:`~xml.etree.ElementTree.Element` elem: An :class:`Element` with the @trans.diat
        and @trans.semi attributes.
    :returns: The interval of transposition from written to concert pitch.
    :rtype: :class:`music21.interval.Interval`
    '''
    transDiat = int(elem.get('trans.diat', 0))
    transSemi = int(elem.get('trans.semi', 0))

    # If the difference between transSemi and transDiat is greater than five per octave...
    if abs(transSemi - transDiat) > 5 * (abs(transSemi) // 12 + 1):
        # ... we need to add octaves to transDiat so it's the proper size. Otherwise,
        #     intervalFromGenericAndChromatic() tries to create things like AAAAAAAAA5. Except it
        #     actually just fails.
        # NB: we test this against transSemi because transDiat could be 0 when transSemi is a
        #     multiple of 12 *either* greater or less than 0.
        if transSemi < 0:
            transDiat -= 7 * (abs(transSemi) // 12)
        elif transSemi > 0:
            transDiat += 7 * (abs(transSemi) // 12)

    # NB: MEI uses zero-based unison rather than 1-based unison, so for music21 we must make every
    #     diatonic interval one greater than it was. E.g., '@trans.diat="2"' in MEI means to
    #     "transpose up two diatonic steps," which music21 would rephrase as "transpose up by a
    #     diatonic third."
    if transDiat < 0:
        transDiat -= 1
    elif transDiat > 0:
        transDiat += 1

    return interval.intervalFromGenericAndChromatic(interval.GenericInterval(transDiat),
                                                    interval.ChromaticInterval(transSemi))


def _barlineFromAttr(attr):
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


def _tieFromAttr(attr):
    '''
    Convert a @tie attribute to the required :class:`Tie` object.

    :param str attr: The MEI @tie attribute to convert.
    :return: The relevant :class:`Tie` object.
    :rtype: :class:`music21.tie.Tie`
    '''
    if 'm' in attr or ('t' in attr and 'i' in attr):
        return tie.Tie('continue')
    elif 'i' in attr:
        return tie.Tie('start')
    else:
        return tie.Tie('stop')


def addSlurs(elem, obj, slurBundle):
    '''
    If relevant, add a slur to an ``obj``ect that was created from an ``elem``ent.

    :param elem: The :class:`Element` that caused creation of the ``obj``.
    :type elem: :class:`xml.etree.ElementTree.Element`
    :param obj: The musical object (:class:`Note`, :class:`Chord`, etc.) created from ``elem``, to
        which a slur might be attached.
    :type obj: :class:`music21.base.Music21Object`
    :param slurBundle: The :class:`Slur`-holding :class:`SpannerBundle` associated with the
        :class:`Stream` that holds ``obj``.
    :type slurBundle: :class:`music21.spanner.SpannerBundle`
    :returns: Whether at least one slur was added.
    :rtype: bool

    **A Note about Importing Slurs**

    Because of how the MEI format specifies slurs, the strategy required for proper import to
    music21 is not obvious. There are two ways to specify a slur:

    #. With a ``@slur`` attribute, in which case :func:`addSlurs` reads the attribute and manages
       creating a :class:`Slur` object, adding the affected objects to it, and storing the
       :class:`Slur` in the ``slurBundle``.
    #. With a ``<slur>`` element, which requires pre-processing. In this case, :class:`Slur` objects
       must already exist in the ``slurBundle``, and special attributes must be added to the
       affected elements (``@m21SlurStart`` to the element at the start of the slur and
       ``@m21SlurEnd`` to the element at the end). These attributes hold the ``id`` of a
       :class:`Slur` in the ``slurBundle``, allowing :func:`addSlurs` to find the slur and add
       ``obj`` to it.

    .. caution:: If an ``elem`` has an @m21SlurStart or @m21SlurEnd attribute that refer to an
        object not found in the ``slurBundle``, the slur is silently dropped.
    '''
    post = False

    def wrapGetByIdLocal(theId):
        "Avoid crashing when getByIdLocl() doesn't find the slur"
        try:
            slurBundle.getByIdLocal(theId)[0].addSpannedElements(obj)
            return True
        except IndexError:
            # when getByIdLocal() couldn't find the Slur
            return False

    if elem.get('m21SlurStart') is not None:
        post = wrapGetByIdLocal(elem.get('m21SlurStart'))
    if elem.get('m21SlurEnd') is not None:
        post = wrapGetByIdLocal(elem.get('m21SlurEnd'))

    if elem.get('slur') is not None:
        theseSlurs = elem.get('slur').split(' ')
        for eachSlur in theseSlurs:
            slurNum, slurType = eachSlur
            if 'i' == slurType:
                newSlur = spanner.Slur()
                newSlur.idLocal = slurNum
                slurBundle.append(newSlur)
                newSlur.addSpannedElements(obj)
                post = True
            elif 't' == slurType:
                post = wrapGetByIdLocal(slurNum)
            # 'm' is currently ignored; we may need it for cross-staff slurs

    return post


def beamTogether(someThings):
    '''
    Beam some things together. The function beams every object that has a :attrib:`beams` attribute,
    leaving the other objects unmodified.

    :param things: An iterable of things to beam together.
    :type things: iterable of :class:`~music21.base.Music21Object`
    :returns: ``someThings`` with relevant objects beamed together.
    :rtype: same as ``someThings``
    '''
    # Index of the most recent beamedNote/Chord in someThings. Not all Note/Chord objects will
    # necessarily be beamed (especially when this is called from tupletFromElement()), so we have
    # to make that distinction.
    iLastBeamedNote = -1

    for i, thing in enumerate(someThings):
        if hasattr(thing, 'beams'):
            if -1 == iLastBeamedNote:
                beamType = 'start'
            else:
                beamType = 'continue'

            # checking for len(thing.beams) avoids clobbering beams that were set with a nested
            # <beam> element, like a grace note
            if duration.convertTypeToNumber(thing.duration.type) > 4 and 0 == len(thing.beams):
                thing.beams.fill(thing.duration.type, beamType)
                iLastBeamedNote = i

    someThings[iLastBeamedNote].beams.setAll('stop')

    return someThings


def removeOctothorpe(xmlid):
    '''
    Given a string with an @xml:id to search for, remove a leading octothorpe, if present.

    >>> from music21.mei.base import removeOctothorpe  # OMIT_FROM_DOCS
    >>> removeOctothorpe('110a923d-a13a-4a2e-b85c-e1d438e4c5d6')
    '110a923d-a13a-4a2e-b85c-e1d438e4c5d6'
    >>> removeOctothorpe('#e46cbe82-95fc-4522-9f7a-700e41a40c8e')
    'e46cbe82-95fc-4522-9f7a-700e41a40c8e'
    '''
    if xmlid.startswith('#'):
        return xmlid[1:]
    else:
        return xmlid


def makeMetadata(fromThis):
    # TODO: tests
    # TODO: break into sub-functions
    # TODO/NOTE: only returns a single Metadata objects atm
    '''
    Produce metadata objects for all the metadata stored in the MEI header.

    :param fromThis: The MEI file's root tag.
    :type fromThis: :class:`~xml.etree.ElementTree.Element`
    :returns: Metadata objects that hold the metadata stored in the MEI header.
    :rtype: sequence of :class:`music21.metadata.Metadata` and :class:`~music21.metadata.RichMetadata`.
    '''
    fromThis = fromThis.find('.//{}work'.format(_MEINS))
    if fromThis is None:
        return []

    meta = metadata.Metadata()
    #richMeta = metadata.RichMetadata()

    for eachTag in fromThis.iterfind('*'):
        if eachTag.tag == '{}titleStmt'.format(_MEINS):
            for subTag in eachTag.iterfind('*'):
                if subTag.tag == '{}title'.format(_MEINS):
                    if subTag.get('type', '') == 'subtitle':
                        # TODO: this is meaningless because m21's Metadata doesn't do anything with it
                        meta.subtitle = subTag.text
                    elif meta.title is None:
                        meta.title = subTag.text
                elif subTag.tag == '{}respStmt'.format(_MEINS):
                    for subSubTag in subTag.iterfind('*'):
                        if subSubTag.tag == '{}persName'.format(_MEINS):
                            if subSubTag.get('role') == 'composer':
                                meta.composer = subSubTag.text

        elif eachTag.tag == '{}history'.format(_MEINS):
            for subTag in eachTag.iterfind('*'):
                if subTag.tag == '{}creation'.format(_MEINS):
                    for subSubTag in subTag.iterfind('*'):
                        if subSubTag.tag == '{}date'.format(_MEINS):
                            if subSubTag.text is None:
                                dateStart, dateEnd = None, None
                                if subSubTag.get('isodate') is not None:
                                    meta.date = subSubTag.get('isodate')
                                elif subSubTag.get('notbefore') is not None:
                                    dateStart = subSubTag.get('notbefore')
                                elif subSubTag.get('startdate') is not None:
                                    dateStart = subSubTag.get('startdate')

                                if subSubTag.get('notafter') is not None:
                                    dateEnd = subSubTag.get('notafter')
                                elif subSubTag.get('enddate') is not None:
                                    dateEnd = subSubTag.get('enddate')

                                if dateStart is not None and dateEnd is not None:
                                    meta.date = metadata.DateBetween((dateStart, dateEnd))
                            else:
                                meta.date = subSubTag.text

        elif eachTag.tag == '{}tempo'.format(_MEINS):
            # NB: this has to be done after a proper, movement-specific title would have been set
            if meta.movementName is None:
                meta.movementName = eachTag.text

    return meta


def getVoiceId(fromThese):
    '''
    From a list of objects with mixed type, find the "id" of the :class:`music21.stream.Voice`
    instance.

    :param list fromThese: A list of objects of any type, at least one of which must be a
        :class:`~music21.stream.Voice` instance.
    :returns: The ``id`` of the :class:`Voice` instance.
    :raises: :exc:`RuntimeError` if zero or many :class:`Voice` objects are found.
    '''
    fromThese = [item for item in fromThese if isinstance(item, stream.Voice)]
    if 1 == len(fromThese):
        return fromThese[0].id
    else:
        raise RuntimeError('getVoiceId: found too few or too many Voice objects')


def scaleToTuplet(objs, elem):
    '''
    Scale the duration of some objects by a ratio indicated by a tuplet. The ``elem`` must have the
    @m21TupletNum and @m21TupletNumbase attributes set, and optionally the @m21TupletSearch or
    @m21TupletType attributes.

    The @m21TupletNum and @m21TupletNumbase attributes should be equal to the @num and @numbase
    values of the <tuplet> or <tupletSpan> that indicates this tuplet.

    The @m21TupletSearch attribute, whose value must either be ``'start'`` or ``'end'``, is required
    when a <tupletSpan> does not include a @plist attribute. It indicates that the importer must
    "search" for a tuplet near the end of the import process, which involves scaling the durations
    of all objects discvoered between those with the "start" and "end" search values.

    The @m21TupletType attribute is set directly as the :attr:`type` attribute of the music21
    object's :class:`Tuplet` object. If @m21TupletType is not set, the @tuplet attribute will be
    consulted. Note that this attribute is ignored if the @m21TupletSearch attribute is present,
    since the ``type`` will be set later by the tuplet-finding algorithm.

    .. note:: Objects without a :attr:`duration` attribute will be skipped silently, unless they
        will be given the @m21TupletSearch attribute.

    :param objs: The object(s) whose durations will be scaled. You may provie either a single object
        or an iterable; the return type corresponds to the input type.
    :type objs: (list of) :class:`~music21.base.Music21Object`
    :param elem: An :class:`Element` with the appropriate attributes (as specified above).
    :type elem: :class:`xml.etree.ElementTree.Element
    :returns: ``objs`` with scaled durations.
    :rtype: (list of) :class:`~music21.base.Music21Object`
    '''
    if not isinstance(objs, (list, set, tuple)):
        objs = [objs]
        wasList = False
    else:
        wasList = True

    for obj in objs:
        if not isinstance(obj, (note.Note, note.Rest, chord.Chord)):
            # silently skip objects that don't have a duration
            continue

        elif elem.get('m21TupletSearch') is not None:
            obj.m21TupletSearch = elem.get('m21TupletSearch')
            obj.m21TupletNum = elem.get('m21TupletNum')
            obj.m21TupletNumbase = elem.get('m21TupletNumbase')

        else:
            obj.duration.appendTuplet(duration.Tuplet(numberNotesActual=int(elem.get('m21TupletNum')),
                                                      numberNotesNormal=int(elem.get('m21TupletNumbase')),
                                                      durationNormal=obj.duration.type,
                                                      durationActual=obj.duration.type))

            if elem.get('m21TupletType') is not None:
                obj.duration.tuplets[0].type = elem.get('m21TupletType')
            elif elem.get('tuplet', '').startswith('i'):
                obj.duration.tuplets[0].type = 'start'
            elif elem.get('tuplet', '').startswith('t'):
                obj.duration.tuplets[0].type = 'stop'

    if wasList:
        return objs
    else:
        return objs[0]


# Element-Based Converter Functions
#------------------------------------------------------------------------------
def scoreDefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
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

    **Attributes/Elements Implemented:**
    - (att.meterSigDefault.log (@meter.count, @meter.unit))
    - (att.keySigDefault.log (@key.accid, @key.mode, @key.pname, @key.sig))

    **Attributes/Elements in Testing:**
    - none

    **Attributes not Implemented:**
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
    att.scoreDef.vis (all)
    att.scoreDef.ges (all)
    att.scoreDef.anl (none exist)

    **Contained Elements not Implemented:**
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

    return post


def staffDefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <staffDef> Container for staff meta-information.

    In MEI 2013: pg.445 (459 in PDF) (MEI.shared module)

    :returns: A list with an :class:`Instrument` subclass with the staff's metadata, followed by
        other music21 objects specified by the ``<staffDef>``, like a :class:`Clef` or :class:`Key`.
    :rtype: list of :class:`music21.instrument.Instrument` then :class:`music21.base.Music21Object`

    **Attributes/Elements Implemented:**
    - @label (att.common) as Instrument.partName
    - @label.abbr (att.labels.addl) as Instrument.partAbbreviation
    - @n (att.common) as Instrument.partId
    - (att.keySigDefault.log (@key.accid, @key.mode, @key.pname, @key.sig))
    - (att.meterSigDefault.log (@meter.count, @meter.unit))
    - (att.cleffing.log (@clef.shape, @clef.line, @clef.dis, @clef.dis.place)) (via :func:`clefFromElement`)
    - @trans.diat and @trans.demi (att.transposition)
    - <instrDef> held within
    - <clef> held within

    **Attributes/Elements Ignored:**
    - @key.sig.mixed (from att.keySigDefault.log)

    **Attributes/Elements in Testing:**
    - none

    **Attributes not Implemented:**
    att.common (@n, @xml:base)
               (att.id (@xml:id))
    att.declaring (@decls)
    att.staffDef.log (att.duration.default (@dur.default, @num.default, @numbase.default))
                     (att.octavedefault (@octave.default))
                     (att.staffDef.log.cmn (att.beaming.log (@beam.group, @beam.rests)))
                     (att.staffDef.log.mensural (att.mensural.log (@mensur.dot, @mensur.sign,
                                                                   @mensur.slash, @proport.num,
                                                                   @proport.numbase)
                                                (att.mensural.shared (@modusmaior, @modusminor,
                                                                      @prolatio, @tempus))))
    att.staffDef.vis (all)
    att.staffDef.ges (all)
    att.staffDef.anl (none exist)

    **Contained Elements not Implemented:**
    - MEI.cmn: meterSig meterSigGrp  TODO: these
    - MEI.mensural: mensur proport
    - MEI.shared: clefGrp keySig label layerDef  TODO: these
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement}

    # first make the Instrument
    post = elem.find('{}instrDef'.format(_MEINS))
    if post is not None:
        post = [instrDefFromElement(post)]
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
    if elem.get('clef.shape') is not None:
        post.append(clefFromElement(ETree.Element('clef', {'shape': elem.get('clef.shape'),
                                                           'line': elem.get('clef.line'),
                                                           'dis': elem.get('clef.dis'),
                                                           'dis.place': elem.get('clef.dis.place')})))

    # --> transposition
    if elem.get('trans.semi') is not None:
        post[0].transposition = _transpositionFromAttrs(elem)

    post.extend(_processEmbeddedElements(elem.findall('*'), tagToFunction, slurBundle))

    return post


def dotFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <dot> Dot of augmentation or division.

    In MEI 2013: pg.304 (318 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**
    - none

    **Attributes/Elements in Testing:**
    - none

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.facsimile (@facs)
    att.dot.log (all)
    att.dot.vis (all)
    att.dot.gesatt.dot.anl (all)

    **Elements not Implemented:**
    - none
    '''
    # TODO: implement @plist, in att.dot.log
    return 1


def articFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <artic> An indication of how to play a note or chord.

    In MEI 2013: pg.259 (273 in PDF) (MEI.shared module)

    **Attributes Implemented:**
    - none

    **Attributes/Elements in Testing:**
    - @artic

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.facsimile (@facs)
    att.typography (@fontfam, @fontname, @fontsize, @fontstyle, @fontweight)
    att.artic.log (att.controlevent (att.plist (@plist, @evaluate))  # TODO: this
                                    (att.timestamp.musical (@tstamp))
                                    (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                                    (att.staffident (@staff))
                                    (att.layerident (@layer)))
    att.artic.vis (all)
    att.artic.gesatt.artic.anl (all)

    **Contained Elements not Implemented:**
    - none
    '''
    return _makeArticList(elem.get('artic'))


def accidFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <accid> Records a temporary alteration to the pitch of a note.

    In MEI 2013: pg.248 (262 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**
    - none

    **Attributes/Elements in Testing:**
    - @accid (from att.accid.log)

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.facsimile (@facs)
    att.typography (@fontfam, @fontname, @fontsize, @fontstyle, @fontweight)
    att.accid.log (@func)
                  (att.controlevent (att.plist (@plist, @evaluate))  # TODO: this
                                    (att.timestamp.musical (@tstamp))
                                    (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                                    (att.staffident (@staff)) (att.layerident (@layer)))
    att.accid.vis (all)
    att.accid.gesatt.accid.anl (all)

    **Contained Elements not Implemented:**
    - none
    '''
    return _accidentalFromAttr(elem.get('accid'))


def noteFromElement(elem, slurBundle=None):
    # NOTE: this function should stay in sync with chordFromElement() where sensible
    '''
    <note> is a single pitched event.

    In MEI 2013: pg.382 (396 in PDF) (MEI.shared module)

    .. note:: We use the ``id`` attribute (from the @xml:id attribute) to attach slurs and other
        spanners to :class:`Note` objects, so @xml:id *must* be imported from the MEI file.

    **Attributes/Elements Implemented:**
    - @accid and <accid>
    - @pname, from att.pitch: [a--g]
    - @oct, from att.octave: [0..9]
    - @dur, from att.duration.musical: (via _qlDurationFromAttr())
    - @dots: [0..4], and <dot> contained within
    - @xml:id (or id), an XML id (submitted as the Music21Object "id")
    - @artic and <artic>
    - @tie, (many of "[i|m|t]")
    - @slur, (many of "[i|m|t][1-6]")
    - @grace, from att.note.ges.cmn: partial implementation (notes marked as grace, but the
        duration is 0 because we ignore the question of which neighbouring note to borrow time from)

    **Attributes/Elements in Testing:**
    - @tuplet, (many of "[i|m|t][1-6]") ??????

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.note.log (att.event (att.timestamp.musical (@tstamp))
                            (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                            (att.staffident (@staff))
                            (att.layerident (@layer)))
                 (att.fermatapresent (@fermata))
                 (att.syltext (@syl))
                 (att.note.log.cmn (att.beamed (@beam))
                                   (att.lvpresent (@lv))
                                   (att.ornam (@ornam)))
                 (att.note.log.mensural (@lig))
    att.note.vis (all)
    att.note.ges (@oct.ges, @pname.ges, @pnum)
                 (att.accidental.performed (@accid.ges))  # TODO: consider this, in relation to key signature
                 (att.articulation.performed (@artic.ges))
                 (att.duration.performed (@dur.ges))
                 (att.instrumentident (@instr))
                 (att.note.ges.cmn (@gliss)
                                   (att.graced (@grace, @grace.time)))  <-- partially implemented
                 (att.note.ges.mensural (att.duration.ratio (@num, @numbase)))
                 (att.note.ges.tablature (@tab.fret, @tab.string))
    att.note.anl (all)

    **Contained Elements not Implemented:**
    MEI.critapp: app
    MEI.edittrans: (all)
    MEI.lyrics: verse
    MEI.shared: syl
    '''
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}dot': dotFromElement,
                     '{http://www.music-encoding.org/ns/mei}artic': articFromElement,
                     '{http://www.music-encoding.org/ns/mei}accid': accidFromElement}

    # pitch and duration... these are what we can set in the constructor
    post = note.Note(safePitch(elem.get('pname', ''),
                               _accidentalFromAttr(elem.get('accid')),
                               elem.get('oct', '')),
                     duration=makeDuration(_qlDurationFromAttr(elem.get('dur')),
                                           int(elem.get('dots', 0))))

    # iterate all immediate children
    dotElements = 0  # count the number of <dot> elements
    for subElement in _processEmbeddedElements(elem.findall('*'), tagToFunction, slurBundle):
        if isinstance(subElement, six.integer_types):
            dotElements += subElement
        elif isinstance(subElement, articulations.Articulation):
            post.articulations.append(subElement)
        elif isinstance(subElement, six.string_types):
            post.pitch.accidental = pitch.Accidental(subElement)

    # we can only process slurs if we got a SpannerBundle as the "slurBundle" argument
    if slurBundle is not None:
        addSlurs(elem, post, slurBundle)

    # id in the @xml:id attribute
    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

    # articulations in the @artic attribute
    if elem.get('artic') is not None:
        post.articulations.extend(_makeArticList(elem.get('artic')))

    # ties in the @tie attribute
    if elem.get('tie') is not None:
        post.tie = _tieFromAttr(elem.get('tie'))

    # dots from inner <dot> elements
    if dotElements > 0:
        post.duration = makeDuration(_qlDurationFromAttr(elem.get('dur')), dotElements)

    # grace note (only mark as grace note---don't worry about "time-stealing")
    if elem.get('grace') is not None:
        post.duration = duration.GraceDuration(post.duration.quarterLength)

    # beams indicated by a <beamSpan> held elsewhere
    # TODO: test this beam stuff (after you figure out wheter it's sufficient)
    if elem.get('m21Beam') is not None:
        if duration.convertTypeToNumber(post.duration.type) > 4:
            post.beams.fill(post.duration.type, elem.get('m21Beam'))

    # tuplets
    if elem.get('m21TupletNum') is not None:
        post = scaleToTuplet(post, elem)

    return post


def restFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <rest/> is a non-sounding event found in the source being transcribed

    In MEI 2013: pg.424 (438 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**
    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]

    **Attributes/Elements in Testing:**
    - none

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.rest.log (att.event (att.timestamp.musical (@tstamp))
                            (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                            (att.staffident (@staff))
                            (att.layerident (@layer)))
                 (att.fermatapresent (@fermata))
                 (att.tupletpresent (@tuplet))
                 (att.rest.log.cmn (att.beamed (@beam)))
    att.rest.vis (all)
    att.rest.ges (all)
    att.rest.anl (all)

    **Contained Elements not Implemented:**
    - none
    '''
    post = note.Rest(duration=makeDuration(_qlDurationFromAttr(elem.get('dur')),
                                           int(elem.get('dots', 0))))

    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

    # tuplets
    if elem.get('m21TupletNum') is not None:
        post = scaleToTuplet(post, elem)

    return post


def mRestFromElement(elem, slurBundle=None):
    '''
    <mRest/> Complete measure rest in any meter.

    In MEI 2013: pg.375 (389 in PDF) (MEI.cmn module)

    This is a function wrapper for :func:`restFromElement`.
    '''
    # TODO: <mRest> elements sometimes won't have a @dur set; it's simply supposed to take up the
    #       whole measure. But then the quarterLength will be 1.0, which isn't good.
    # TODO: even the algorithm currently in measureFromElement() won't necessarily do this correctly,
    #       since if all parts have a full-measure rest, they will all have the same (incorrect)
    #       duration set.
    return restFromElement(elem, slurBundle)


def spaceFromElement(elem, slurBundle=None):
    '''
    <space>  A placeholder used to fill an incomplete measure, layer, etc. most often so that the
    combined duration of the events equals the number of beats in the measure.

    In MEI 2013: pg.440 (455 in PDF) (MEI.shared module)

    .. note:: Since music21 lacks "spacer" objects, this is imported as a :class:`~music21.note.Rest`.
    '''
    return restFromElement(elem, slurBundle)


def mSpaceFromElement(elem, slurBundle=None):
    '''
    <mSpace/> A measure containing only empty space in any meter.

    In MEI 2013: pg.377 (391 in PDF) (MEI.cmn module)

    This is a function wrapper for :func:`spaceFromElement`.
    '''
    # TODO: <mSpace> elements sometimes won't have a @dur set; it's simply supposed to take up the
    #       whole measure. But then the quarterLength will be 1.0, which isn't good.
    return spaceFromElement(elem, slurBundle)


def chordFromElement(elem, slurBundle=None):
    # NOTE: this function should stay in sync with noteFromElement() where sensible
    '''
    <chord> is a simultaneous sounding of two or more notes in the same layer with the same duration.

    In MEI 2013: pg.280 (294 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**
    - @xml:id (or id), an XML id (submitted as the Music21Object "id")
    - <note> contained within
    - @dur, from att.duration.musical: (via _qlDurationFromAttr())
    - @dots, from att.augmentdots: [0..4]
    - @artic and <artic>
    - @tie, (many of "[i|m|t]")
    - @slur, (many of "[i|m|t][1-6]")

    **Attributes/Elements in Testing:**
    - @tuplet, (many of "[i|m|t][1-6]") ??????
    - @grace, from att.note.ges.cmn: partial implementation (notes marked as grace, but the
        duration is 0 because we ignore the question of which neighbouring note to borrow time from)

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.chord.log (att.event (att.timestamp.musical (@tstamp))
                             (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                             (att.staffident (@staff))
                             (att.layerident (@layer)))
                  (att.fermatapresent (@fermata))
                  (att.syltext (@syl))
                  (att.chord.log.cmn (att.beamed (@beam))
                                     (att.lvpresent (@lv))
                                     (att.ornam (@ornam)))
    att.chord.vis (all)
    att.chord.ges (att.articulation.performed (@artic.ges))
                  (att.duration.performed (@dur.ges))
                  (att.instrumentident (@instr))
                  (att.chord.ges.cmn (att.graced (@grace, @grace.time)))  <-- partially implemented
    att.chord.anl (all)

    **Contained Elements not Implemented:**
    - MEI.edittrans: (all)
    '''
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}note': lambda *x: None,
                     '{http://www.music-encoding.org/ns/mei}artic': articFromElement}

    # pitch and duration... these are what we can set in the constructor
    post = chord.Chord(notes=[noteFromElement(x, slurBundle) for x in elem.iterfind('{}note'.format(_MEINS))])

    # for a Chord, setting "duration" with a Duration object in __init__() doesn't work
    post.duration = makeDuration(_qlDurationFromAttr(elem.get('dur')), int(elem.get('dots', 0)))

    # iterate all immediate children
    for subElement in _processEmbeddedElements(elem.findall('*'), tagToFunction, slurBundle):
        if isinstance(subElement, articulations.Articulation):
            post.articulations.append(subElement)

    # we can only process slurs if we got a SpannerBundle as the "slurBundle" argument
    if slurBundle is not None:
        addSlurs(elem, post, slurBundle)

    # id in the @xml:id attribute
    if elem.get(_XMLID) is not None:
        post.id = elem.get(_XMLID)

    # articulations in the @artic attribute
    if elem.get('artic') is not None:
        post.articulations.extend(_makeArticList(elem.get('artic')))

    # ties in the @tie attribute
    if elem.get('tie') is not None:
        post.tie = _tieFromAttr(elem.get('tie'))

    # grace note (only mark as grace note---don't worry about "time-stealing")
    if elem.get('grace') is not None:
        # TODO: test this
        post.duration = duration.GraceDuration(post.duration.quarterLength)

    # beams indicated by a <beamSpan> held elsewhere
    # TODO: test this beam stuff (after you figure out wheter it's sufficient)
    if elem.get('m21Beam') is not None:
        if duration.convertTypeToNumber(post.duration.type) > 4:
            post.beams.fill(post.duration.type, elem.get('m21Beam'))

    # tuplets
    if elem.get('m21TupletNum') is not None:
        post = scaleToTuplet(post, elem)

    return post


def clefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <clef> Indication of the exact location of a particular note on the staff and, therefore,
    the other notes as well.

    In MEI 2013: pg.284 (298 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**
    - @xml:id (or id), an XML id (submitted as the Music21Object "id")
    - @shape, from att.clef.gesatt.clef.log
    - @line, from att.clef.gesatt.clef.log
    - @dis, from att.clef.gesatt.clef.log
    - @dis.place, from att.clef.gesatt.clef.log

    **Attributes/Elements Ignored:**
    - @cautionary, since this has no obvious implication for a music21 Clef
    - @octave, since this is likely obscure

    **Attributes/Elements in Testing:**
    - none

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.event (att.timestamp.musical (@tstamp))
              (att.timestamp.performed (@tstamp.ges, @tstamp.real))
              (att.staffident (@staff))
              (att.layerident (@layer))
    att.facsimile (@facs)
    att.clef.anl (all)
    att.clef.vis (all)

    **Contained Elements not Implemented:**
    - none
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


def instrDefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    # TODO: write tests
    '''
    <instrDef> (instrument definition)---MIDI instrument declaration.

    In MEI 2013: pg.344 (358 in PDF) (MEI.midi module)

    :returns: An :class:`Instrument`

    **Attributes/Elements Implemented:**
    - none

    **Attributes/Elements in Testing:**
    - @midi.instrname (att.midiinstrument)
    - @midi.instrnum (att.midiinstrument)

    **Attributes/Elements Ignored:**
    - @xml:id

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.channelized (@midi.channel, @midi.duty, @midi.port, @midi.track)
    att.midiinstrument (@midi.pan, @midi.volume)

    **Contained Elements not Implemented:**
    - none
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


def beamFromElement(elem, slurBundle=None):
    # TODO: nested <beam> tags. This requires adjusting the beam.Beams object differently for
    #       every level, which seems to require knowing which level to adjust. Hmm.
    # TODO: write tests
    '''
    <beam> A container for a series of explicitly beamed events that begins and ends entirely
           within a measure.

    In MEI 2013: pg.264 (278 in PDF) (MEI.cmn module)

    :param elem: The ``<beam>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: An iterable of all the objects contained within the ``<beam>`` container.
    :rtype: list of :class:`~music21.base.Music21Object`

    .. note:: Nested <beam> tags do not yet import properly.

    **Attributes/Elements Implemented:**
    - <clef>, <chord>, <note>, <rest>, <space>

    **Attributes/Elements Ignored:**
    - @xml:id

    **Attributes/Elements in Testing:**
    - <tuplet> and <beam> contained within

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.facsimile (@facs)
    att.beam.log (att.event (att.timestamp.musical (@tstamp))
                            (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                            (att.staffident (@staff))
                            (att.layerident (@layer)))
                 (att.beamedwith (@beam.with))
    att.beam.vis (all)
    att.beam.gesatt.beam.anl (all)

    **Contained Elements not Implemented:**
    - MEI.cmn: bTrem beatRpt fTrem halfmRpt meterSig meterSigGrp
    - MEI.critapp: app
    - MEI.edittrans: (all)
    - MEI.mensural: ligature mensur proport
    - MEI.shared: barLine clefGrp custos keySig pad
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement,
                     '{http://www.music-encoding.org/ns/mei}tuplet': tupletFromElement,
                     '{http://www.music-encoding.org/ns/mei}beam': beamFromElement,
                     '{http://www.music-encoding.org/ns/mei}space': spaceFromElement}

    post = _processEmbeddedElements(elem.findall('*'), tagToFunction, slurBundle)
    post = beamTogether(post)

    return post


def tupletFromElement(elem, slurBundle=None):
    '''
    <tuplet> A group of notes with "irregular" (sometimes called "irrational") rhythmic values,
    for example, three notes in the time normally occupied by two or nine in the time of five.

    In MEI 2013: pg.473 (487 in PDF) (MEI.cmn module)

    :param elem: The ``<tuplet>`` tag to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: An iterable of all the objects contained within the ``<tuplet>`` container.
    :rtype: tuple of :class:`~music21.base.Music21Object`

    **Attributes/Elements Implemented:**
    - none

    **Attributes/Elements in Testing:**
    - <tuplet>, <beam>, <note>, <rest>, <chord>, <clef>, <space>
    - @num and @numbase

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.facsimile (@facs)
    att.tuplet.log (att.event (att.timestamp.musical (@tstamp))
                              (att.timestamp.performed (@tstamp.ges, @tstamp.real))
                              (att.staffident (@staff))
                              (att.layerident (@layer)))
                   (att.beamedwith (@beam.with))
                   (att.augmentdots (@dots))
                   (att.duration.additive (@dur))
                   (att.startendid (@endid) (att.startid (@startid)))
    att.tuplet.vis (@bracket.place, @bracket.visible, @dur.visible, @num.format)
                   (att.color (@color))
                   (att.numberplacement (@num.place, @num.visible))
    att.tuplet.ges (att.duration.performed (@dur.ges))
    att.tuplet.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                   (att.alignment (@when)))

    **Contained Elements not Implemented:**
    - MEI.cmn: bTrem beatRpt fTrem halfmRpt meterSig meterSigGrp
    - MEI.critapp: app
    - MEI.edittrans: (all)
    - MEI.mensural: ligature mensur proport
    - MEI.shared: barLine clefGrp custos keySig pad
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}tuplet': tupletFromElement,
                     '{http://www.music-encoding.org/ns/mei}beam': beamFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}space': spaceFromElement}

    # get the @num and @numbase attributes, without which we can't properly calculate the tuplet
    if elem.get('num') is None or elem.get('numbase') is None:
        raise MeiAttributeError(_MISSING_TUPLET_DATA)

    # iterate all immediate children
    post = _processEmbeddedElements(elem.findall('*'), tagToFunction, slurBundle)

    # "tuplet-ify" the duration of everything held within
    newElem = ETree.Element('c', m21TupletNum=elem.get('num'), m21TupletNumbase=elem.get('numbase'))
    post = scaleToTuplet(post, newElem)

    # Set the Tuplet.type property for the first and final note in a tuplet.
    # We have to find the first and last duration-having thing, not just the first and last objects
    # between the <tuplet> tags.
    firstNote = None
    lastNote = None
    for i, eachObj in enumerate(post):
        if firstNote is None and isinstance(eachObj, note.GeneralNote):
            firstNote = i
        elif isinstance(eachObj, note.GeneralNote):
            lastNote = i

    post[firstNote].duration.tuplets[0].type = 'start'
    if lastNote is None:
        # when there is only one object in the tuplet
        post[firstNote].duration.tuplets[0].type = 'stop'
    else:
        post[lastNote].duration.tuplets[0].type = 'stop'

    # beam it all together
    post = beamTogether(post)

    return tuple(post)


def layerFromElement(elem, overrideN=None, slurBundle=None):
    # TODO: clefs that should appear part-way through a measure don't
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

    **Attributes/Elements Implemented:**
    - <clef>, <chord>, <note>, <rest>, <mRest> contained within
    - @n, from att.common

    **Attributes Ignored:**
    - @xml:id

    **Attributes/Elements in Testing:**
    - <beam>, <tuplet>, <space>, <mSpace> contained within

    **Attributes not Implemented:**
    att.common (@label, @xml:base)
    att.declaring (@decls)
    att.facsimile (@facs)
    att.layer.log (@def)
                  (att.meterconformance (@metcon))
    att.layer.vis (att.visibility (@visible))
    att.layer.gesatt.layer.anl (all)

    **Contained Elements not Implemented:**
    - MEI.cmn: arpeg bTrem beamSpan beatRpt bend breath fTrem fermata gliss hairpin halfmRpt
               harpPedal mRpt mRpt2 meterSig meterSigGrp multiRest multiRpt octave pedal
               reh slur tie tuplet tupletSpan
    - MEI.cmnOrnaments: mordent trill turn
    - MEI.critapp: app
    - MEI.edittrans: (all)
    - MEI.harmony: harm
    - MEI.lyrics: lyrics
    - MEI.mensural: ligature mensur proport
    - MEI.midi: midi
    - MEI.neumes: ineume syllable uneume
    - MEI.shared: accid annot artic barLine clefGrp custos dir dot dynam keySig pad pb phrase sb
                  scoreDef staffDef tempo
    - MEI.text: div
    - MEI.usersymbols: anchoredText curve line symbol
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement,
                     '{http://www.music-encoding.org/ns/mei}mRest': mRestFromElement,
                     '{http://www.music-encoding.org/ns/mei}beam': beamFromElement,
                     '{http://www.music-encoding.org/ns/mei}tuplet': tupletFromElement,
                     '{http://www.music-encoding.org/ns/mei}space': spaceFromElement,
                     '{http://www.music-encoding.org/ns/mei}mSpace': mSpaceFromElement}
    post = stream.Voice()

    # iterate all immediate children
    for eachTag in elem.iterfind('*'):
        if eachTag.tag in tagToFunction:
            result = tagToFunction[eachTag.tag](eachTag, slurBundle)
            if not isinstance(result, (tuple, list)):
                post.append(result)
            else:
                for eachObject in result:
                    post.append(eachObject)
        elif eachTag.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug('unprocessed {} in {}'.format(eachTag.tag, elem.tag))

    # try to set the Voice's "id" attribte
    if overrideN:
        post.id = overrideN
    elif elem.get('n') is not None:
        post.id = elem.get('n')
    else:
        raise MeiAttributeError(_MISSING_VOICE_ID)

    return post


def staffFromElement(elem, slurBundle=None):
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

    **Attributes/Elements Implemented:**
    - <layer> contained within

    **Attributes Ignored:**
    - @xml:id

    **Attributes/Elements in Testing:**
    - none

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
    att.declaring (@decls)
    att.facsimile (@facs)
    att.staff.log (@def)
                  (att.meterconformance (@metcon))
    att.staff.vis (att.visibility (@visible))
    att.staff.gesatt.staff.anl (all)

    **Contained Elements not Implemented:**
    - MEI.cmn: ossia
    - MEI.critapp: app
    - MEI.edittrans: (all)
    - MEI.shared: annot pb sb scoreDef staffDef
    - MEI.text: div
    - MEI.usersymbols: anchoredText curve line symbol
    '''
    # mapping from tag name to our converter function
    layerTagName = '{http://www.music-encoding.org/ns/mei}layer'
    tagToFunction = {}
    post = []

    # track the @n values given to layerFromElement()
    currentNValue = '1'

    # iterate all immediate children
    for eachTag in elem.iterfind('*'):
        if layerTagName == eachTag.tag:
            thisLayer = layerFromElement(eachTag, currentNValue, slurBundle=slurBundle)
            # check for objects that must appear in the Measure, but are currently in the Voice
            for eachThing in thisLayer:
                if isinstance(eachThing, (clef.Clef,)):
                    # TODO: this causes problems because a clef-change part-way through the measure
                    #       won't end up appearing part-way through
                    post.append(eachThing)
                    thisLayer.remove(eachThing)
            post.append(thisLayer)
            currentNValue = str(int(currentNValue) + 1)  # inefficient, but we need a string
        elif eachTag.tag in tagToFunction:
            # NB: this won't be tested until there's something in tagToFunction
            post.append(tagToFunction[eachTag.tag](eachTag, slurBundle))
        elif eachTag.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug('unprocessed {} in {}'.format(eachTag.tag, elem.tag))

    return post


def measureFromElement(elem, backupNum=None, expectedNs=None, slurBundle=None):
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

    **Attributes/Elements Implemented:**
    - none

    **Attributes Ignored:**
    - @xml:id
    - <slur> and <tie> contained within. These spanners will usually be attached to their starting
      and ending notes with @xml:id attributes, so it's not necessary to process them when
      encountered in a <measure>. Furthermore, because the possibility exists for cross-measure
      slurs and ties, we can't guarantee we'll be able to process all spanners until all
      spanner-attachable objects are processed. So we manage these tags at a higher level.

    **Attributes/Elements in Testing:**
    - <staff> contained within
    - @right and @left (att.measure.log)

    **Attributes not Implemented:**
    att.common (@label, @n, @xml:base)
               (att.id (@xml:id))
    att.declaring (@decls)
    att.facsimile (@facs)
    att.typed (@type, @subtype)
    att.pointing (@xlink:actuate, @xlink:role, @xlink:show, @target, @targettype, @xlink:title)
    att.measure.log (att.meterconformance.bar (@metcon, @control))
    att.measure.vis (all)
    att.measure.ges (att.timestamp.performed (@tstamp.ges, @tstamp.real))
    att.measure.anl (all)

    **Contained Elements not Implemented:**
    - MEI.cmn: arpeg beamSpan bend breath fermata gliss hairpin harpPedal octave ossia pedal reh
               tupletSpan
    - MEI.cmnOrnaments: mordent trill turn
    - MEI.critapp: app
    - MEI.edittrans: add choice corr damage del gap handShift orig reg restore sic subst supplied
                     unclear
    - MEI.harmony: harm
    - MEI.lyrics: lyrics
    - MEI.midi: midi
    - MEI.shared: annot dir dynam pb phrase sb staffDef tempo
    - MEI.text: div
    - MEI.usersymbols: anchoredText curve line symbol
    '''
    post = {}

    backupNum = 0 if backupNum is None else backupNum
    expectedNs = [] if expectedNs is None else expectedNs

    # mapping from tag name to our converter function
    staffTagName = '{http://www.music-encoding.org/ns/mei}staff'
    tagToFunction = {}

    # track the bar's duration
    maxBarDuration = None

    # iterate all immediate children
    for eachTag in elem.iterfind('*'):
        if staffTagName == eachTag.tag:
            post[eachTag.get('n')] = stream.Measure(staffFromElement(eachTag, slurBundle=slurBundle),
                                                    number=int(elem.get('n', backupNum)))
            thisBarDuration = post[eachTag.get('n')].duration.quarterLength
            if maxBarDuration is None or maxBarDuration < thisBarDuration:
                maxBarDuration = thisBarDuration
        elif eachTag.tag in tagToFunction:
            # NB: this won't be tested until there's something in tagToFunction
            post[eachTag.get('n')] = tagToFunction[eachTag.tag](eachTag, slurBundle)
        elif eachTag.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug('unprocessed {} in {}'.format(eachTag.tag, elem.tag))

    # create rest-filled measures for expected parts that had no <staff> tag in this <measure>
    for eachN in expectedNs:
        if eachN not in post:
            restVoice = stream.Voice([note.Rest(quarterLength=maxBarDuration)])
            restVoice.id = '1'
            post[eachN] = stream.Measure([restVoice], number=int(elem.get('n', backupNum)))

    # see if any of the Measures are shorter than the others; if so, check for <mRest/> tags that
    # didn't have a @dur set
    # TODO: find a better way to deal with full-measure rests
    #for eachN in expectedNs:
        #if post[eachN].duration.quarterLength < maxBarDuration:
            #for eachVoice in post[eachN]:
                #for eachThing in eachVoice:
                    #if isinstance(eachThing, note.Rest):
                        #eachThing.duration = duration.Duration(maxBarDuration -
                                                               #post[eachN].duration.quarterLength +
                                                               #eachThing.duration.quarterLength)

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
    from music21.mei import test_base
    music21.mainTest(test_base.TestMeiToM21Class,
                     test_base.TestThings,
                     test_base.TestAttrTranslators,
                     test_base.TestNoteFromElement,
                     test_base.TestRestFromElement,
                     test_base.TestChordFromElement,
                     test_base.TestClefFromElement,
                     test_base.TestLayerFromElement,
                     test_base.TestStaffFromElement,
                     test_base.TestStaffDefFromElement,
                     test_base.TestScoreDefFromElement,
                     test_base.TestEmbeddedElements,
                     test_base.TestAddSlurs,
                     test_base.TestBeams,
                     test_base.TestPreprocessors,
                     test_base.TestTuplets,
                    )

#------------------------------------------------------------------------------
# eof
