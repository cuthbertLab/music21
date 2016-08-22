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
.. codeauthor:: Chistopher Antila <christopher@antila.ca>

These are the public methods for the MEI module.

To convert a string with MEI markup into music21 objects, 
use :meth:`MeiToM21Converter.convertFromString`.

In the future, most of the functions in this module should be moved to a separate, import-only
module, so that functions for writing music21-to-MEI will fit nicely.

**Simple "How-To"**

Use :class:`MeiToM21Converter` to convert a string to a set of music21 objects. In the future, the
:class:`M21ToMeiConverter` class will convert a set of music21 objects into a string with an MEI
document.

>>> meiString = """<?xml version="1.0" encoding="UTF-8"?>
... <mei xmlns="http://www.music-encoding.org/ns/mei" meiversion="2013">
...     <music>
...     <score>
...         <scoreDef meter.count="6" meter.unit="8">
...             <staffGrp>
...                 <staffDef n="1" clef.shape="F" clef.line="4"/>
...             </staffGrp>
...         </scoreDef>
...         <section>
...             <scoreDef key.sig="1f" key.mode="major"/>
...             <measure n="1">
...                 <staff n="1">
...                     <layer n="1">
...                         <beam>
...                             <note pname="E" oct="3" dur="8" artic="stacc"/>
...                             <note pname="E" oct="3" dur="8"/>
...                             <note pname="E" oct="3" dur="8"/>
...                         </beam>
...                         <chord dur="4" dots="1">
...                             <note pname="F" oct="2"/>
...                             <note pname="A" oct="2" accid="f"/>
...                         </chord>
...                     </layer>
...                 </staff>
...             </measure>
...         </section>
... </score>
...     </music>
... </mei>
... """
>>> from music21 import *
>>> conv = mei.MeiToM21Converter(meiString)
>>> result = conv.run()
>>> type(result)
<class 'music21.stream.Score'>

**Terminology**

This module's documentation adheres to the following terminology regarding XML documents, using
this snippet, ``<note pname="C"/>`` as an example:

- the entire snippet is an *element*.
- the word ``note`` is the *tag*.
- the word ``pname`` is an *attribute*.
- the letter ``C`` is a *value*.

Because Python also uses "attributes," an XML attribute is always preceded by an "at sign," as in
@pname, whereas a Python attribute is set as :attr:`pname`.

**Ignored Elements**

The following elements are not yet imported, though you might expect they would be:

* <sb>: a system break, since this is not usually semantically significant
* <lb>: a line break, since this is not usually semantically significant
* <pb>: a page break, since this is not usually semantically significant

**Where Elements Are Processed**

Most elements are processed in functions called :func:`tagFromElement`, where "tag" is replaced by
the element's tag name (e.g., :func:`staffDefFromElement` for <staffDef> elements). These functions
convert from a Python :class:`xml.etree.ElementTree.Element` 
object to the appropriate music21 object.

However, certain elements are processed primarily in 
another way, by "private" functions that are not
documented in this API. Rather than converting an :class:`Element` object into a music21 object,
these functions modify the MEI document tree by adding instructions for the :func:`tagFromElement`
functions. The elements processed by private functions include:

* <slur>
* <tie>
* <beamSpan>
* <tupletSpan>

Whereas you can expect functions like :func:`clefFromElement` 
to convert a <clef> into a :class:`Clef`
with no loss of information. Because we cannot provide a simple one-to-one conversion for  slurs,
ties, and tuplets, we have kept their conversion functions "private," 
to emphasize the fact that you
must use the :class:`MeiToM21Converter` to process them properly.

**Guidelines for Encoders**

While we aim for the best possible compatibility, the MEI 
specification is very large. The following
guidelines will help you produce a file that this MEI-to-music21 module will import correctly and
in the most efficient way. These should not necessarily be considered recommendations when using
MEI in any other context.

* Tuplets indicated only in a @tuplet attribute do not work.
* For elements that allow @startid, @endid, and @plist attributes, 
  use all three for faster importing.
* For a <tupletSpan> that does not specify a @plist attribute, a tuplet spanning more than two
  measures will always and unavoidably be imported incorrectly.
* For any tuplet, specify at least @num and @numbase. The module refuses to import a tuplet that
  does not have the @numbase attribute.
* Retain consistent @n values for the same layer, staff, and instrument throughout the score.
* Always indicate the duration of <mRest> and <mSpace> elements.
* Avoid using the <barLine> element if you require well-formatted output from music21, since (as of
  January 2015) the music21-to-something converters will only output a :class:`Barline` that is
  part of a :class:`Measure`.

**List of Supported Elements**

Alphabetical list of the elements currently supported by this module:

* :func:`accidFromElement`
* :func:`articFromElement`
* :func:`barLineFromElement`
* :func:`beamFromElement`
* :func:`chordFromElement`
* :func:`clefFromElement`
* :func:`dotFromElement`
* :func:`instrDefFromElement`
* :func:`layerFromElement`
* :func:`measureFromElement`
* :func:`noteFromElement`
* :func:`restFromElement`
* :func:`mRestFromElement`
* :func:`spaceFromElement`
* :func:`mSpaceFromElement`
* :func:`scoreFromElement`
* :func:`scoreDefFromElement`
* :func:`sectionFromElement`
* :func:`staffFromElement`
* :func:`staffDefFromElement`
* :func:`staffGrpFromElement`
* :func:`sylFromElement`
* :func:`tupletFromElement`
* :func:`verseFromElement`

To know which MEI attributes are known to import correctly, read the documentation for the relevant
element. For example, to know whether the @color attribute on a <note> element is supported, read
the "Attributes/Elements Implemented" section of the :func:`noteFromElement` documentation.

**List of Ignored Elements**

The following elements are (silently) ignored by the MEI-to-music21 converter because they primarily
affect the layout and typesetting of a musical score. We may choose to implement these elements in
the future, but they are a lower priority because music21 is not primarily a layout or typesetting
tool.

* <multiRest>: a multi-measure rest (these will be "converted" to single-measure rests)
* <pb>: a page break
* <lb>: a line break
* <sb>: a system break

'''

# Determine which ElementTree implementation to use.
# We'll prefer the C-based versions if available, since they provide better performance.
try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree

from collections import defaultdict
import unittest
from uuid import uuid4

# music21
from music21 import articulations
from music21 import bar
from music21 import chord
from music21 import clef
from music21 import duration
from music21 import environment
from music21 import exceptions21
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
from music21 import spanner
from music21 import tie

_MOD = 'mei.base'
environLocal = environment.Environment(_MOD)

from music21.ext import six


# Module-Level Constants
#------------------------------------------------------------------------------
_XMLID = '{http://www.w3.org/XML/1998/namespace}id'
_MEINS = '{http://www.music-encoding.org/ns/mei}'
# when these tags aren't processed, we won't worry about them (at least for now)
_IGNORE_UNPROCESSED = (
   '{}sb'.format(_MEINS),  # system break
   '{}lb'.format(_MEINS),  # line break
   '{}pb'.format(_MEINS),  # page break
   '{}slur'.format(_MEINS),  # slurs; handled in convertFromString()
   '{}tie'.format(_MEINS),  # ties; handled in convertFromString()
   '{}tupletSpan'.format(_MEINS),  # tuplets; handled in convertFromString()
   '{}beamSpan'.format(_MEINS),  # beams; handled in convertFromString()
   '{}instrDef'.format(_MEINS),  # instrument; handled separately by staffDefFromElement()
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
# NOTE: these are all collected handily at the top for two reasons: help you find the easier, and
#       help you translate them easier
_TEST_FAILS = 'MEI module had {} failures and {} errors; run music21/mei/base.py to find out more.'
_INVALID_XML_DOC = 'MEI document is not valid XML.'
_WRONG_ROOT_ELEMENT = 'Root element should be <mei> in the MEI namespace, not <{}>.'
_UNKNOWN_TAG = 'Found unexpected tag while parsing MEI: <{}>.'
_UNEXPECTED_ATTR_VALUE = 'Unexpected value for "{}" attribute: {}'
_SEEMINGLY_NO_PARTS = 'There appear to be no <staffDef> tags in this score.'
_MISSING_VOICE_ID = 'Found a <layer> without @n attribute and no override.'
_CANNOT_FIND_XMLID = 'Could not find the @{} so we could not create the {}.'
_MISSING_TUPLET_DATA = 'Both @num and @numbase attributes are required on <tuplet> tags.'
_UNIMPLEMENTED_IMPORT = 'Importing {} without {} is not yet supported.'
_UNPROCESSED_SUBELEMENT = 'Found an unprocessed <{}> element in a <{}>.'
_MISSED_DATE = 'Unable to decipher the composition date "{}"'
_BAD_VERSE_NUMBER = 'Verse number must be an int (got "{}")'


# Module-level Functions
#------------------------------------------------------------------------------
class MeiToM21Converter(object):
    '''
    A :class:`MeiToM21Converter` instance manages the conversion of an MEI document into music21
    objects.

    If ``theDocument`` does not have <mei> as the root element, the class raises an
    :class:`MeiElementError`. If ``theDocument`` is not a valid XML file, the class raises an
    :class:`MeiValidityError`.

    :param str theDocument: A string containing an MEI document.
    :raises: :exc:`MeiElementError` when the root element is not <mei>
    :raises: :exc:`MeiValidityError` when the MEI file is not valid XML.
    '''

    def __init__(self, theDocument=None):
        '''
        The __init__() documentation doesn't isn't processed by Sphinx, so I put it at class level.
        '''
        environLocal.printDebug('*** initializing MeiToM21Converter')

        if theDocument is None:
            # Without this, the class can't be pickled.
            self.documentRoot = ETree.Element('{http://www.music-encoding.org/ns/mei}mei')
        else:
            try:
                self.documentRoot = ETree.fromstring(theDocument)
            except ETree.ParseError as parseErr:
                environLocal.printDebug(
                        '\n\nERROR: Parsing the MEI document with ElementTree failed.')
                environLocal.printDebug('We got the following error:\n{}'.format(parseErr))
                raise MeiValidityError(_INVALID_XML_DOC)

            if isinstance(self.documentRoot, ETree.ElementTree):
                # pylint warns that :class:`Element` doesn't have a getroot() method, which is
                # true enough, but...
                self.documentRoot = self.documentRoot.getroot()  # pylint: disable=maybe-no-member

            if '{http://www.music-encoding.org/ns/mei}mei' != self.documentRoot.tag:
                raise MeiElementError(_WRONG_ROOT_ELEMENT.format(self.documentRoot.tag))

        # This defaultdict stores extra, music21-specific attributes that we add to elements to help
        # importing. The key is an element's @xml:id, and the value is a regular dict with keys
        # corresponding to attributes we'll add and values 
        # corresponding to those attributes's values.
        self.m21Attr = defaultdict(lambda: {})

        # This SpannerBundle holds the slurs that will be created by _ppSlurs() and used while
        # importing whatever note, rest, chord, or other object.
        self.slurBundle = spanner.SpannerBundle()

    def run(self):
        '''
        Run conversion of the internal MEI document to produce a music21 object.

        :returns: A :class:`Stream` subclass, depending on the MEI document.
        :rtype: :class:`music21.stream.Stream`
        '''

        environLocal.printDebug('*** pre-processing spanning elements')
        _ppSlurs(self)
        _ppTies(self)
        _ppBeams(self)
        _ppTuplets(self)
        _ppConclude(self)

        environLocal.printDebug('*** processing <score> elements')
        theScore = scoreFromElement(
                    self.documentRoot.find('.//{mei}music//{mei}score'.format(mei=_MEINS)),
                    self.slurBundle)

        environLocal.printDebug('*** preparing metadata')
        theScore.metadata = makeMetadata(self.documentRoot)

        return theScore


# Module-level Functions
#------------------------------------------------------------------------------
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
    Given a ``base`` duration and a number of ``dots``, create a :class:`~music21.duration.Duration` 
    instance with the
    appropriate ``quarterLength`` value.

    :param float base: The base duration that will be augmented.
    :param int dots: The number of dots with which to augment the ``base`` duration.
    :returns: A :class:`Duration` corresponding to the fully-augmented value.
    :rtype: :class:`music21.duration.Duration`

    **Examples**

    >>> from music21 import *
    >>> from fractions import Fraction
    >>> mei.base.makeDuration(base=2.0, dots=0).quarterLength  # half note, no dots
    2.0
    >>> mei.base.makeDuration(base=2.0, dots=1).quarterLength  # half note, one dot
    3.0
    >>> mei.base.makeDuration(base=2, dots=2).quarterLength  # 'base' can be an int or float
    3.5
    >>> mei.base.makeDuration(2.0, 10).quarterLength  # you want ridiculous dots? Sure...
    3.998046875
    >>> mei.base.makeDuration(0.33333333333333333333, 0).quarterLength  # works with fractions too
    Fraction(1, 3)
    >>> mei.base.makeDuration(Fraction(1, 3), 1).quarterLength
    0.5
    '''
    returnDuration = duration.Duration(base)
    returnDuration.dots = dots  # pylint: disable=assigning-non-slot
    return returnDuration


def allPartsPresent(scoreElem):
    '''
    Find the @n values for all <staffDef> elements in a <score> element. This assumes that every
    MEI <staff> corresponds to a music21 :class:`Part`.

    :param scoreElem: The <score> :class:`Element` in which to find the part names.
    :returns: All the unique @n values associated with a part in the <score>.
    :rtype: tuple of str

    **Example**

    >>> meiDoc = """<?xml version="1.0" encoding="UTF-8"?>
    ... <score xmlns="http://www.music-encoding.org/ns/mei">
    ...     <scoreDef>
    ...         <staffGrp>
    ...             <staffDef n="1" clef.shape="G" clef.line="2"/>
    ...             <staffDef n="2" clef.shape="F" clef.line="4"/>
    ...         </staffGrp>
    ...     </scoreDef>
    ...     <section>
    ...         <!-- ... some music ... -->
    ...         <staffDef n="2" clef.shape="C" clef.line="4"/>
    ...         <!-- ... some music ... -->
    ...     </section>
    ... </score>"""
    >>> import xml.etree.ElementTree as ETree
    >>> from music21 import *
    >>> meiDoc = ETree.fromstring(meiDoc)
    >>> mei.base.allPartsPresent(meiDoc)
    ('1', '2')

    Even though there are three <staffDef> elements in the document, there are only two unique @n
    attributes. The second appearance of <staffDef> with @n="2" signals a change of clef on that
    same staff---not that there is a new staff.
    '''
    #xpathQuery = './/{mei}music//{mei}score//{mei}staffDef'.format(mei=_MEINS)
    xpathQuery = './/{}staffDef'.format(_MEINS)
    partNs = []  # hold the @n attribute for all the parts

    for staffDef in scoreElem.findall(xpathQuery):
        if staffDef.get('n') not in partNs:
            partNs.append(staffDef.get('n'))
    if 0 == len(partNs):
        raise MeiValidityError(_SEEMINGLY_NO_PARTS)
    return tuple(partNs)


# Constants for One-to-One Translation
#------------------------------------------------------------------------------
# for _accidentalFromAttr()
# None is for when @accid is omitted
_ACCID_ATTR_DICT = {'s': '#', 'f': '-', 'ss': '##', 'x': '##', 'ff': '--', 'xs': '###',
                    'ts': '###', 'tf': '---', 'n': 'n', 'nf': '-', 'ns': '#', 'su': '#~',
                    'sd': '~', 'fu': '`', 'fd': '-`', 'nu': '~', 'nd': '`', None: None}

# for _accidGesFromAttr()
# None is for when @accid is omitted
_ACCID_GES_ATTR_DICT = {'s': '#', 'f': '-', 'ss': '##', 'ff': '--', 'n': 'n', 'su': '#~',
                        'sd': '~', 'fu': '`', 'fd': '-`', None: None}

# for _qlDurationFromAttr()
# None is for when @dur is omitted; it's silly so it can be identified
_DUR_ATTR_DICT = {'long': 16.0, 'breve': 8.0, '1': 4.0, '2': 2.0, '4': 1.0, '8': 0.5, '16': 0.25,
                  '32': 0.125, '64': 0.0625, '128': 0.03125, '256': 0.015625, '512': 0.0078125,
                  '1024': 0.00390625, '2048': 0.001953125, None: 0.00390625}

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
                    'tap': articulations.Articulation, 'lhpizz': articulations.Articulation,
                    'dot': articulations.Articulation, 'stroke': articulations.Articulation,
                    'rip': articulations.Articulation, 'bend': articulations.Articulation,
                    'flip': articulations.Articulation, 'smear': articulations.Articulation,
                    'fingernail': articulations.Articulation,  # (u1D1B3)
                    'damp': articulations.Articulation, 'dampall': articulations.Articulation}

# for _barlineFromAttr()
# TODO: make new music21 Barline styles for 'dbldashed' and 'dbldotted'
_BAR_ATTR_DICT = {'dashed': 'dashed', 'dotted': 'dotted', 'dbl': 'double', 'end': 'final',
                  'invis': 'none', 'single': 'regular'}


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
    music21.mei.base.MeiValueError: Unexpected value for "dur" attribute: 9
    '''
    try:
        return mapping[attr]
    except KeyError:
        raise MeiValueError(_UNEXPECTED_ATTR_VALUE.format(name, attr))


def _accidentalFromAttr(attr):
    '''
    Use :func:`_attrTranslator` to convert the value of an "accid" attribute to its music21 string.

    >>> from music21 import *
    >>> mei.base._accidentalFromAttr('s')
    '#'
    '''
    return _attrTranslator(attr, 'accid', _ACCID_ATTR_DICT)


def _accidGesFromAttr(attr):
    '''
    Use :func:`_attrTranslator` to convert the value of an @accid.ges 
    attribute to its music21 string.

    >>> from music21 import *
    >>> mei.base._accidGesFromAttr('s')
    '#'
    '''
    return _attrTranslator(attr, 'accid.ges', _ACCID_GES_ATTR_DICT)


def _qlDurationFromAttr(attr):
    '''
    Use :func:`_attrTranslator` to convert an MEI "dur" attribute to a music21 quarterLength.

    >>> from music21 import *
    >>> mei.base._qlDurationFromAttr('4')
    1.0

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
    articList = []
    for eachArtic in attr.split(' '):
        articList.extend(_articulationFromAttr(eachArtic))
    return articList


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
def _ppSlurs(theConverter):
    '''
    Pre-processing helper for :func:`convertFromString` that handles slurs specified in <slur>
    elements. The input is a :class:`MeiToM21Converter` with data about the file currently being
    processed. This function reads from ``theConverter.documentRoot`` and writes into
    ``theConverter.m21Attr`` and ``theConverter.slurBundle``.

    :param theConverter: The object responsible for storing data about this import.
    :type theConverter: :class:`MeiToM21Converter`.

    **This Preprocessor**

    The slur preprocessor adds @m21SlurStart and @m21SlurEnd attributes to elements that are at the
    beginning or end of a slur. The value of these attributes is the ``idLocal`` of a :class:`Slur`
    in the :attr:`slurBundle` attribute of ``theConverter``. This attribute is not part of the MEI
    specification, and must therefore be handled specially.

    If :func:`noteFromElement` encounters an element like ``<note m21SlurStart="82f87cd7"/>``, the
    resulting :class:`music21.note.Note` should be set as the starting point of the slur with an
    ``idLocal`` of ``'82f87cd7'``.

    **Example of Changes to ``m21Attr``**

    The ``theConverter.m21Attr`` attribute must be a defaultdict that returns an empty (regular)
    dict for non-existant keys. The defaultdict stores the @xml:id attribute of an element; the
    dict holds attribute names and their values that should be added to the element with the
    given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.

    **Example**

    Consider the following example.

    >>> meiDoc = """<?xml version="1.0" encoding="UTF-8"?>
    ... <mei xmlns="http://www.music-encoding.org/ns/mei" meiversion="2013">
    ...     <music><score>
    ...     <section>
    ...         <note xml:id="1234"/>
    ...         <note xml:id="2345"/>
    ...         <slur startid="#1234" endid="#2345"/>
    ...     </section>
    ...     </score></music>
    ... </mei>"""
    >>> from music21 import *
    >>> theConverter = mei.base.MeiToM21Converter(meiDoc)
    >>>
    >>> mei.base._ppSlurs(theConverter)
    >>> 'm21SlurStart' in theConverter.m21Attr['1234']
    True
    >>> 'm21SlurEnd' in theConverter.m21Attr['2345']
    True
    >>> theConverter.slurBundle
    <music21.spanner.SpannerBundle of size 1>
    >>> (theConverter.m21Attr['1234']['m21SlurStart'] ==
    ...  theConverter.m21Attr['2345']['m21SlurEnd'] ==
    ...  theConverter.slurBundle.list[0].idLocal)
    True

    This example is a little artificial because of the limitations of a doctest, where we need to
    know all values in advance. The point here is that the values of 'm21SlurStart' and 'm21SlurEnd'
    of a particular slur-attached object will match the 'idLocal' of a slur in :attr:`slurBundle`.
    The "id" is a UUID determined at runtime, which looks something like
    ``'d3731f89-8a2f-4b82-ad02-f0bc6f5f8b04'``.
    '''
    environLocal.printDebug('*** pre-processing slurs')
    # for readability, we use a single-letter variable
    c = theConverter  # pylint: disable=invalid-name
    # pre-processing for <slur> tags
    for eachSlur in c.documentRoot.iterfind(
                            './/{mei}music//{mei}score//{mei}slur'.format(mei=_MEINS)):
        if eachSlur.get('startid') is not None and eachSlur.get('endid') is not None:
            thisIdLocal = str(uuid4())
            thisSlur = spanner.Slur()
            thisSlur.idLocal = thisIdLocal
            c.slurBundle.append(thisSlur)

            c.m21Attr[removeOctothorpe(eachSlur.get('startid'))]['m21SlurStart'] = thisIdLocal
            c.m21Attr[removeOctothorpe(eachSlur.get('endid'))]['m21SlurEnd'] = thisIdLocal
        else:
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<slur>', '@startid and @endid'))


def _ppTies(theConverter):
    '''
    Pre-processing helper for :func:`convertFromString` that handles ties specified in <tie>
    elements. The input is a :class:`MeiToM21Converter` with data about the file currently being
    processed. This function reads from ``theConverter.documentRoot`` and writes into
    ``theConverter.m21Attr``.

    :param theConverter: The object responsible for storing data about this import.
    :type theConverter: :class:`MeiToM21Converter`.

    **This Preprocessor**

    The tie preprocessor works similarly to the slur preprocessor, adding @tie attributes. The
    value of these attributes conforms to the MEI Guidelines, so no special action is required.

    **Example of ``m21Attr``**

    The ``theConverter.m21Attr`` attribute must be a defaultdict that returns an empty (regular)
    dict for non-existant keys. The defaultdict stores the @xml:id attribute of an element; the
    dict holds attribute names and their values that should be added to the element with the
    given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.
    '''
    environLocal.printDebug('*** pre-processing ties')
    # for readability, we use a single-letter variable
    c = theConverter  # pylint: disable=invalid-name

    for eachTie in c.documentRoot.iterfind(
                        './/{mei}music//{mei}score//{mei}tie'.format(mei=_MEINS)):
        if eachTie.get('startid') is not None and eachTie.get('endid') is not None:
            c.m21Attr[removeOctothorpe(eachTie.get('startid'))]['tie'] = 'i'
            c.m21Attr[removeOctothorpe(eachTie.get('endid'))]['tie'] = 't'
        else:
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<tie>', '@startid and @endid'))


def _ppBeams(theConverter):
    '''
    Pre-processing helper for :func:`convertFromString` that handles beams specified in <beamSpan>
    elements. The input is a :class:`MeiToM21Converter` with data about the file currently being
    processed. This function reads from ``theConverter.documentRoot`` and writes into
    ``theConverter.m21Attr``.

    :param theConverter: The object responsible for storing data about this import.
    :type theConverter: :class:`MeiToM21Converter`.

    **This Preprocessor**

    The beam preprocessor works similarly to the slur preprocessor, adding the @m21Beam attribute.
    The value of this attribute is either ``'start'``, ``'continue'``, or ``'stop'``, indicating
    the music21 ``type`` of the primary beam attached to this element. This attribute is not
    part of the MEI specification, and must therefore be handled specially.

    **Example of ``m21Attr``**

    The ``theConverter.m21Attr`` argument must be a defaultdict that returns an empty (regular)
    dict for non-existant keys. The defaultdict stores the @xml:id attribute of an element; the
    dict holds attribute names and their values that should be added to the element with the
    given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.
    '''
    environLocal.printDebug('*** pre-processing beams')
    # for readability, we use a single-letter variable
    c = theConverter  # pylint: disable=invalid-name

    # pre-processing for <beamSpan> elements
    for eachBeam in c.documentRoot.iterfind(
                        './/{mei}music//{mei}score//{mei}beamSpan'.format(mei=_MEINS)):
        if eachBeam.get('startid') is None or eachBeam.get('endid') is None:
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<beamSpan>', '@startid and @endid'))
            continue

        c.m21Attr[removeOctothorpe(eachBeam.get('startid'))]['m21Beam'] = 'start'
        c.m21Attr[removeOctothorpe(eachBeam.get('endid'))]['m21Beam'] = 'stop'

        # iterate things in the @plist attribute
        for eachXmlid in eachBeam.get('plist', '').split(' '):
            eachXmlid = removeOctothorpe(eachXmlid)
            if 0 == len(eachXmlid):
                # this is either @plist not set or extra spaces around the contained xml:id values
                pass
            if 'm21Beam' not in c.m21Attr[eachXmlid]:
                # only set to 'continue' if it wasn't previously set to 'start' or 'stop'
                c.m21Attr[eachXmlid]['m21Beam'] = 'continue'


def _ppTuplets(theConverter):
    '''
    Pre-processing helper for :func:`convertFromString` that handles tuplets specified in
    <tupletSpan> elements. The input is a :class:`MeiToM21Converter` with data about the file
    currently being processed. This function reads from ``theConverter.documentRoot`` and writes
    into ``theConverter.m21Attr``.

    :param theConverter: The object responsible for storing data about this import.
    :type theConverter: :class:`MeiToM21Converter`.

    **This Preprocessor**

    The slur preprocessor works similarly to the slur preprocessor, adding @m21TupletNum and
    @m21TupletNumbase attributes. The value of these attributes corresponds to the @num and
    @numbase attributes found on a <tuplet> element. This preprocessor also performs a significant
    amount of guesswork to try to handle <tupletSpan> elements that do not include a @plist
    attribute. This attribute is not part of the MEI specification, and must therefore be handled
    specially.

    **Example of ``m21Attr``**

    The ``theConverter.m21Attr`` attribute must be a defaultdict that returns an empty (regular)
    dict for non-existant keys. The defaultdict stores the @xml:id attribute of an element; the
    dict holds attribute names and their values that should be added to the element with the
    given @xml:id.

    For example, if the value of ``m21Attr['fe93129e']['tie']`` is ``'i'``, then this means the
    element with an @xml:id of ``'fe93129e'`` should have the @tie attribute set to ``'i'``.
    '''
    environLocal.printDebug('*** pre-processing tuplets')
    # for readability, we use a single-letter variable
    c = theConverter  # pylint: disable=invalid-name

    # pre-processing <tupletSpan> tags
    for eachTuplet in c.documentRoot.iterfind(
                            './/{mei}music//{mei}score//{mei}tupletSpan'.format(mei=_MEINS)):
        if ((eachTuplet.get('startid') is None or eachTuplet.get('endid') is None)
                and eachTuplet.get('plist') is None):
            environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<tupletSpan>', 
                                                           '@startid and @endid or @plist'))
        elif eachTuplet.get('plist') is not None:
            # Ideally (for us) <tupletSpan> elements will have a @plist that enumerates the
            # @xml:id of every affected element. In this case, tupletSpanFromElement() can use the
            # @plist to add our custom @m21TupletNum and @m21TupletNumbase attributes.
            for eachXmlid in eachTuplet.get('plist', '').split(' '):
                eachXmlid = removeOctothorpe(eachXmlid)
                if 0 < len(eachXmlid):
                    # protect against extra spaces around the contained xml:id values
                    c.m21Attr[eachXmlid]['m21TupletNum'] = eachTuplet.get('num')
                    c.m21Attr[eachXmlid]['m21TupletNumbase'] = eachTuplet.get('numbase')
        else:
            # For <tupletSpan> elements that don't give a @plist attribute, we have to do some
            # guesswork and hope we find all the related elements. Right here, we're only setting
            # the "flags" that this guesswork must be done later.
            startid = removeOctothorpe(eachTuplet.get('startid'))
            endid = removeOctothorpe(eachTuplet.get('endid'))

            c.m21Attr[startid]['m21TupletSearch'] = 'start'
            c.m21Attr[startid]['m21TupletNum'] = eachTuplet.get('num')
            c.m21Attr[startid]['m21TupletNumbase'] = eachTuplet.get('numbase')
            c.m21Attr[endid]['m21TupletSearch'] = 'end'
            c.m21Attr[endid]['m21TupletNum'] = eachTuplet.get('num')
            c.m21Attr[endid]['m21TupletNumbase'] = eachTuplet.get('numbase')


def _ppConclude(theConverter):
    '''
    Pre-processing helper for :func:`convertFromString` that adds attributes from ``m21Attr`` to the
    appropriate elements in ``documentRoot``. The input is a :class:`MeiToM21Converter` with data
    about the file currently being processed. This function reads from ``theConverter.m21Attr`` and
    writes into ``theConverter.documentRoot``.

    :param theConverter: The object responsible for storing data about this import.
    :type theConverter: :class:`MeiToM21Converter`.

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
    # for readability, we use a single-letter variable
    c = theConverter  # pylint: disable=invalid-name

    # conclude pre-processing by adding music21-specific attributes to their respective elements
    for eachObject in c.documentRoot.iterfind('*//*'):
        # we have a defaultdict, so this "if" isn't strictly necessary; but without it, every single
        # element with an @xml:id creates a new, empty dict, which would consume a lot of memory
        if eachObject.get(_XMLID) in c.m21Attr:
            for eachAttr in c.m21Attr[eachObject.get(_XMLID)]:
                eachObject.set(eachAttr, (eachObject.get(eachAttr, '') +
                                          c.m21Attr[eachObject.get(_XMLID)][eachAttr]))


# Helper Functions
#------------------------------------------------------------------------------
def _processEmbeddedElements(elements, mapping, callerTag=None, slurBundle=None):
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
    :param str callerTag: The tag of the element on behalf of which this function is processing
        sub-elements (e.g., 'note' or 'staffDef'). Do not include < and >. This is used in a
        warning message on finding an unprocessed element.
    :param slurBundle: A slur bundle, as used by the other :func:`*fromElements` functions.
    :type slurBundle: :class:`music21.spanner.SlurBundle`
    :returns: A list of the music21 objects returned by the converter functions, or an empty list
        if no objects were returned.
    :rtype: sequence of :class:`~music21.base.Music21Object`

    **Examples:**

    Because there is no ``'rest'`` key in the ``mapping``, that :class:`Element` is ignored.

    >>> from xml.etree.ElementTree import Element
    >>> from music21 import *
    >>> elements = [Element('note'), Element('rest'), Element('note')]
    >>> mapping = {'note': lambda x, y: note.Note('D2')}
    >>> mei.base._processEmbeddedElements(elements, mapping, 'doctest')
    [<music21.note.Note D>, <music21.note.Note D>]

    If debugging is enabled for the previous example, this warning would be displayed:

    ``mei.base: Found an unprocessed <rest> element in a <doctest>.

    The "beam" element holds "note" elements. All elements appear in a single level of the list:

    >>> elements = [Element('note'), Element('beam'), Element('note')]
    >>> mapping = {'note': lambda x, y: note.Note('D2'),
    ...            'beam': lambda x, y: [note.Note('E2') for _ in range(2)]}
    >>> mei.base._processEmbeddedElements(elements, mapping)
    [<music21.note.Note D>, <music21.note.Note E>, <music21.note.Note E>, <music21.note.Note D>]
    '''
    processed = []

    for eachElem in elements:
        if eachElem.tag in mapping:
            result = mapping[eachElem.tag](eachElem, slurBundle)
            if isinstance(result, (tuple, list)):
                for eachObject in result:
                    processed.append(eachObject)
            else:
                processed.append(result)
        elif eachElem.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug(_UNPROCESSED_SUBELEMENT.format(eachElem.tag, callerTag))

    return processed


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
        ks = key.KeySignature(sharps=_sharpsFromAttr(elem.get('key.sig')))
        return ks.asKey(mode=elem.get('key.mode'))


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
    :class:`Barline` or :class:`Repeat` or occaionsally a list of :class:`Repeat`. The only time a
    list is returned is when "attr" is ``'rptboth'``, in which case the end and start barlines are
    both returned.

    :param str attr: The MEI @left or @right attribute to convert to a barline.
    :returns: The barline.
    :rtype: :class:`music21.bar.Barline` or :class:`~music21.bar.Repeat` or list of them
    '''
    # NB: the MEI Specification says @left is used only for legcay-format conversions, so we'll
    #     just assume it's a @right attribute. Not a huge deal if we get this wrong (I hope).
    if attr.startswith('rpt'):
        if 'rptboth' == attr:
            return _barlineFromAttr('rptend'), _barlineFromAttr('rptstart')
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
    If relevant, add a slur to an ``obj`` (object) that was created from an ``elem`` (element).

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
    addedSlur = False

    def wrapGetByIdLocal(theId):
        "Avoid crashing when getByIdLocl() doesn't find the slur"
        try:
            slurBundle.getByIdLocal(theId)[0].addSpannedElements(obj)
            return True
        except IndexError:
            # when getByIdLocal() couldn't find the Slur
            return False

    if elem.get('m21SlurStart') is not None:
        addedSlur = wrapGetByIdLocal(elem.get('m21SlurStart'))
    if elem.get('m21SlurEnd') is not None:
        addedSlur = wrapGetByIdLocal(elem.get('m21SlurEnd'))

    if elem.get('slur') is not None:
        theseSlurs = elem.get('slur').split(' ')
        for eachSlur in theseSlurs:
            slurNum, slurType = eachSlur
            if 'i' == slurType:
                newSlur = spanner.Slur()
                newSlur.idLocal = slurNum
                slurBundle.append(newSlur)
                newSlur.addSpannedElements(obj)
                addedSlur = True
            elif 't' == slurType:
                addedSlur = wrapGetByIdLocal(slurNum)
            # 'm' is currently ignored; we may need it for cross-staff slurs

    return addedSlur


def beamTogether(someThings):
    '''
    Beam some things together. The function beams every object that has a :attr:`beams` attribute,
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

    >>> from music21.mei.base import removeOctothorpe
    >>> removeOctothorpe('110a923d-a13a-4a2e-b85c-e1d438e4c5d6')
    '110a923d-a13a-4a2e-b85c-e1d438e4c5d6'
    >>> removeOctothorpe('#e46cbe82-95fc-4522-9f7a-700e41a40c8e')
    'e46cbe82-95fc-4522-9f7a-700e41a40c8e'
    '''
    if xmlid.startswith('#'):
        return xmlid[1:]
    else:
        return xmlid


def makeMetadata(documentRoot):
    '''
    Produce metadata objects for all the metadata stored in the MEI header.

    :param documentRoot: The MEI document's root element.
    :type documentRoot: :class:`~xml.etree.ElementTree.Element`
    :returns: A :class:`Metadata` object with some of the metadata stored in the MEI document.
    :rtype: :class:`music21.metadata.Metadata`
    '''
    meta = metadata.Metadata()
    work = documentRoot.find('.//{}work'.format(_MEINS))
    if work is not None:
        # title, subtitle, and movement name
        meta = metaSetTitle(work, meta)
        # composer
        meta = metaSetComposer(work, meta)
        # date
        meta = metaSetDate(work, meta)

    return meta


def metaSetTitle(work, meta):
    '''
    From a <work> element, find the title, subtitle, and movement name (<tempo> element) and store
    the values in a :class:`Metadata` object.

    :param work: A <work> :class:`~xml.etree.ElementTree.Element` with metadata you want to find.
    :param meta: The :class:`~music21.metadata.Metadata` object in which to store the metadata.
    :return: The ``meta`` argument, having relevant metadata added.
    '''
    # title, subtitle, and movement name
    for title in work.findall('./{mei}titleStmt/{mei}title'.format(mei=_MEINS)):
        if title.get('type', '') == 'subtitle':
            meta.subtitle = title.text
        elif meta.title is None:
            meta.title = title.text

    if hasattr(meta, 'subtitle'):
        # Since m21.Metadata doesn't actually have a "subtitle" attribute, we'll put the subtitle
        # in the title
        meta.title = '{} ({})'.format(meta.title, meta.subtitle)
        del meta.subtitle

    tempo = work.find('./{}tempo'.format(_MEINS))
    if tempo is not None:
        meta.movementName = tempo.text

    return meta


def metaSetComposer(work, meta):
    '''
    From a <work> element, find the composer(s) and store the values in a :class:`Metadata` object.

    :param work: A <work> :class:`~xml.etree.ElementTree.Element` with metadata you want to find.
    :param meta: The :class:`~music21.metadata.Metadata` object in which to store the metadata.
    :return: The ``meta`` argument, having relevant metadata added.
    '''
    composers = []
    for persName in work.findall('./{mei}titleStmt/{mei}respStmt/{mei}persName'.format(mei=_MEINS)):
        if persName.get('role') == 'composer' and persName.text:
            composers.append(persName.text)
    for composer in work.findall('./{mei}titleStmt/{mei}composer'.format(mei=_MEINS)):
        if composer.text:
            composers.append(composer.text)
        else:
            persName = composer.find('./{}persName'.format(_MEINS))
            if persName.text:
                composers.append(persName.text)
    if 1 == len(composers):
        meta.composer = composers[0]
    elif 1 < len(composers):
        meta.composer = composers

    return meta


def metaSetDate(work, meta):
    '''
    From a <work> element, find the date (range) of composition and store the values in a
    :class:`Metadata` object.

    :param work: A <work> :class:`~xml.etree.ElementTree.Element` with metadata you want to find.
    :param meta: The :class:`~music21.metadata.Metadata` object in which to store the metadata.
    :return: The ``meta`` argument, having relevant metadata added.
    '''
    date = work.find('./{mei}history/{mei}creation/{mei}date'.format(mei=_MEINS))
    if date is not None:  # must use explicit "is not None" for an Element
        if date.text or date.get('isodate'):
            dateStr = date.get('isodate') if date.get('isodate') else date.text
            theDate = metadata.Date()
            try:
                theDate.loadStr(dateStr.replace('-', '/'))
            except ValueError:
                environLocal.warn(_MISSED_DATE.format(dateStr))
            else:
                meta.date = theDate
        else:
            dateStart = date.get('notbefore') if date.get('notbefore') else date.get('startdate')
            dateEnd = date.get('notafter') if date.get('notafter') else date.get('enddate')
            if dateStart and dateEnd:
                meta.date = metadata.DateBetween((dateStart, dateEnd))

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
    :type elem: :class:`xml.etree.ElementTree.Element`
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
            obj.duration.appendTuplet(duration.Tuplet(
                                          numberNotesActual=int(elem.get('m21TupletNum')),
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


def _guessTuplets(theLayer):
    # TODO: nested tuplets don't work when they're both specified with <tupletSpan>
    # TODO: adjust this to work with cross-measure tuplets (i.e., where only the "start" or "end"
    #       is found in theLayer)
    '''
    Given a list of music21 objects, possibly containing :attr:`m21TupletSearch`,
    :attr:`m21TupletNum`, and :attr:`m21TupletNumbase` attributes, adjust the durations of the
    objects as specified by those "m21Tuplet" attributes, then remove the attributes.

    This function finishes processing for tuplets encoded as a <tupletSpan> where @startid and
    @endid are indicated, but not @plist. Knowing the starting and ending object in the tuplet, we
    can guess that all the Note, Rest, and Chord objects between the starting and ending objects
    in that <layer> are part of the tuplet. (Grace notes retain a 0.0 duration).

    .. note:: At the moment, this will likely only work for simple tuplets---not nested tuplets.

    :param theLayer: Objects from the <layer> in which to search for objects that have the
        :attr:`m21TupletSearch` attribute.
    :type theScore: list
    :returns: The same list, with durations adjusted to account for tuplets.
    '''
    # NB: this is a hidden function because it uses the "m21TupletSearch" attribute, which are only
    #     supposed to be used within the MEI import module

    inATuplet = False  # we hit m21TupletSearch=='start' but not 'end' yet
    tupletNum = None
    tupletNumbase = None

    for eachNote in theLayer:
        # we'll skip objects that don't have a duration
        if not isinstance(eachNote, (note.Note, note.Rest, chord.Chord)):
            continue

        if hasattr(eachNote, 'm21TupletSearch') and eachNote.m21TupletSearch == 'start':
            inATuplet = True
            tupletNum = int(eachNote.m21TupletNum)
            tupletNumbase = int(eachNote.m21TupletNumbase)

            del eachNote.m21TupletSearch
            del eachNote.m21TupletNum
            del eachNote.m21TupletNumbase

        if inATuplet:
            scaleToTuplet(eachNote, ETree.Element('',
                                                  m21TupletNum=tupletNum,
                                                  m21TupletNumbase=tupletNumbase))

            if hasattr(eachNote, 'm21TupletSearch') and eachNote.m21TupletSearch == 'end':
                # we've reached the end of the tuplet!
                eachNote.duration.tuplets[0].type = 'stop'

                del eachNote.m21TupletSearch
                del eachNote.m21TupletNum
                del eachNote.m21TupletNumbase

                # reset the tuplet-tracking variables
                inATuplet = False

    return theLayer


# Element-Based Converter Functions
#------------------------------------------------------------------------------
def scoreDefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <scoreDef> Container for score meta-information.

    In MEI 2013: pg.431 (445 in PDF) (MEI.shared module)

    This function returns a dictionary with objects that may relate to the entire score, to all
    parts at a particular moment, or only to a specific part at a particular moment. The dictionary
    keys determine the object's scope. If the key is...

    * ``'whole-score objects'``, it applies to the entire score (e.g., page size);
    * ``'all-part objects'``, it applies to all parts at the moment this <scoreDef> appears;
    * the @n attribute of a part, it applies only to 
      that part at the moment this <scoreDef> appears.

    While the multi-part objects will be held in a list, the single-part objects will be in a dict
    like that returned by :func:`staffDefFromElement`.

    Note that it is the caller's responsibility to determine the right action if there are
    conflicting objects in the returned dictionary.

    For example:

    >>> meiDoc = """<?xml version="1.0" encoding="UTF-8"?>
    ... <scoreDef meter.count="3" meter.unit="4" xmlns="http://www.music-encoding.org/ns/mei">
    ...     <staffGrp>
    ...         <staffDef n="1" label="Clarinet"/>
    ...         <staffGrp>
    ...             <staffDef n="2" label="Flute"/>
    ...             <staffDef n="3" label="Violin"/>
    ...         </staffGrp>
    ...     </staffGrp>
    ... </scoreDef>
    ... """
    >>> from music21 import *
    >>> from xml.etree import ElementTree as ET
    >>> scoreDef = ET.fromstring(meiDoc)
    >>> result = mei.base.scoreDefFromElement(scoreDef)
    >>> len(result)
    5
    >>> result['1']
    {'instrument': <music21.instrument.Instrument 1: Clarinet: Clarinet>}
    >>> result['3']
    {'instrument': <music21.instrument.Instrument 3: Violin: Violin>}
    >>> result['all-part objects']
    [<music21.meter.TimeSignature 3/4>]
    >>> result['whole-score objects']
    []

    :param elem: The ``<scoreDef>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: Objects from the ``<scoreDef>``, as described above.
    :rtype: dict

    **Attributes/Elements Implemented:**

    - (att.meterSigDefault.log (@meter.count, @meter.unit))
    - (att.keySigDefault.log (@key.accid, @key.mode, @key.pname, @key.sig))
    - contained <staffGrp>

    **Attributes/Elements in Testing:** None

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.scoreDef.log

        - (att.cleffing.log (@clef.shape, @clef.line, @clef.dis, @clef.dis.place))
        - (att.duration.default (@dur.default, @num.default, @numbase.default))
        - (att.keySigDefault.log (@key.sig.mixed))
        - (att.octavedefault (@octave.default))
        - (att.transposition (@trans.diat, @trans.semi))
        - (att.scoreDef.log.cmn (att.beaming.log (@beam.group, @beam.rests)))
        - (att.scoreDef.log.mensural

            - (att.mensural.log (@mensur.dot, @mensur.sign, 
                 @mensur.slash, @proport.num, @proport.numbase)
            - (att.mensural.shared (@modusmaior, @modusminor, @prolatio, @tempus))))

    - att.scoreDef.vis (all)
    - att.scoreDef.ges (all)
    - att.scoreDef.anl (none exist)

    **Contained Elements not Implemented:**

    - MEI.cmn: meterSig meterSigGrp
    - MEI.harmony: chordTable
    - MEI.linkalign: timeline
    - MEI.midi: instrGrp
    - MEI.shared: keySig pgFoot pgFoot2 pgHead pgHead2
    - MEI.usersymbols: symbolTable
    '''

    # make the dict
    allParts = 'all-part objects'
    wholeScore = 'whole-score objects'
    post = {allParts: [], wholeScore: []}

    # 1.) process all-part attributes
    # --> time signature
    if elem.get('meter.count') is not None:
        post[allParts].append(_timeSigFromAttrs(elem))

    # --> key signature
    if elem.get('key.pname') is not None or elem.get('key.sig') is not None:
        post[allParts].append(_keySigFromAttrs(elem))

    # 2.) staff-specific things (from contained <staffGrp> >> <staffDef>)
    for eachGrp in elem.iterfind('{http://www.music-encoding.org/ns/mei}staffGrp'):
        post.update(staffGrpFromElement(eachGrp, slurBundle))

    return post


def staffGrpFromElement(elem, slurBundle=None, staffDefDict=None):
    '''
    <staffGrp> A group of bracketed or braced staves.

    In MEI 2013: pg.448 (462 in PDF) (MEI.shared module)

    For now, this function is merely a container-processor  for <staffDef> elements contained
    in this <staffGrp> element given as the "elem" argument. That is, the function does not yet
    create the brackets/braces and labels expected of a staff group. 
    Note however that all <staffDef>
    elements will be processed, even if they're contained within several layers of <staffGrp>.

    :param elem: The ``<staffGrp>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: Dictionary where keys are the @n attribute on a contained <staffDef>, and values are
        the result of calling :func:`staffDefFromElement` with that <staffDef>.

    **Attributes/Elements Implemented:**

    - contained <staffDef>
    - contained <staffGrp>

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.declaring (@decls)
    - att.facsimile (@facs)
    - att.staffGrp.vis (@barthru)

        - (att.labels.addl (@label.abbr))
        - (att.staffgroupingsym (@symbol))
        - (att.visibility (@visible))

    - att.staffGrp.ges (att.instrumentident (@instr))

    **Contained Elements not Implemented:**

    - MEI.midi: instrDef
    - MEI.shared: grpSym label
    '''
    
    staffDefTag = '{http://www.music-encoding.org/ns/mei}staffDef'
    staffGroupTag = '{http://www.music-encoding.org/ns/mei}staffGrp'

    staffDefDict = staffDefDict if staffDefDict is not None else {}

    for el in elem.findall("*"):
        # return all staff defs in this staff group
        if el.tag == staffDefTag:
            staffDefDict[el.get('n')] = staffDefFromElement(el, slurBundle)

        # recurse if there are more groups, append to the working staffDefDict    
        elif el.tag == staffGroupTag:
            staffGrpFromElement(el, slurBundle, staffDefDict)

    return staffDefDict

def staffDefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <staffDef> Container for staff meta-information.

    In MEI 2013: pg.445 (459 in PDF) (MEI.shared module)

    :returns: A dict with various types of metadata information, depending on what is specified in
        this <staffDef> element. Read below for more information.
    :rtype: dict

    **Possible Return Values**

    The contents of the returned dictionary depend on the contents of the <staffDef> element. The
    dictionary keys correspond to types of information. Possible keys include:

    - ``'instrument'``: for a :class:`music21.instrument.Instrument` subclass
    - ``'clef'``: for a :class:`music21.clef.Clef` subclass
    - ``'key'``: for a :class:`music21.key.Key` or :class:`~music21.key.KeySignature` subclass
    - ``'meter'``: for a :class:`music21.meter.TimeSignature`

    **Examples**

    This <staffDef> only returns a single item.

    >>> meiDoc = """<?xml version="1.0" encoding="UTF-8"?>
    ... <staffDef n="1" label="Clarinet" xmlns="http://www.music-encoding.org/ns/mei"/>
    ... """
    >>> from music21 import *
    >>> from xml.etree import ElementTree as ET
    >>> staffDef = ET.fromstring(meiDoc)
    >>> result = mei.base.staffDefFromElement(staffDef)
    >>> len(result)
    1
    >>> result
    {'instrument': <music21.instrument.Instrument 1: Clarinet: Clarinet>}
    >>> result['instrument'].partId
    '1'
    >>> result['instrument'].partName
    'Clarinet'

    This <staffDef> returns many objects.

    >>> meiDoc = """<?xml version="1.0" encoding="UTF-8"?>
    ... <staffDef n="2" label="Tuba" key.pname="B" key.accid="f" key.mode="major"
    ...  xmlns="http://www.music-encoding.org/ns/mei">
    ...     <clef shape="F" line="4"/>
    ... </staffDef>
    ... """
    >>> from music21 import *
    >>> from xml.etree import ElementTree as ET
    >>> staffDef = ET.fromstring(meiDoc)
    >>> result = mei.base.staffDefFromElement(staffDef)
    >>> len(result)
    3
    >>> result['instrument']
    <music21.instrument.Instrument 2: Tuba: Tuba>
    >>> result['clef']
    <music21.clef.BassClef>
    >>> result['key']
    <music21.key.Key of B- major>

    **Attributes/Elements Implemented:**

    - @label (att.common) as Instrument.partName
    - @label.abbr (att.labels.addl) as Instrument.partAbbreviation
    - @n (att.common) as Instrument.partId
    - (att.keySigDefault.log (@key.accid, @key.mode, @key.pname, @key.sig))
    - (att.meterSigDefault.log (@meter.count, @meter.unit))
    - (att.cleffing.log (@clef.shape, @clef.line, @clef.dis, @clef.dis.place)) 
      (via :func:`clefFromElement`)
    - @trans.diat and @trans.demi (att.transposition)
    - <instrDef> held within
    - <clef> held within

    **Attributes/Elements Ignored:**

    - @key.sig.mixed (from att.keySigDefault.log)

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@n, @xml:base) (att.id (@xml:id))
    - att.declaring (@decls)
    - att.staffDef.log

        - (att.duration.default (@dur.default, @num.default, @numbase.default))
        - (att.octavedefault (@octave.default))
        - (att.staffDef.log.cmn (att.beaming.log (@beam.group, @beam.rests)))
        - (att.staffDef.log.mensural

            - (att.mensural.log (@mensur.dot, @mensur.sign, @mensur.slash, 
                                 @proport.num, @proport.numbase)
            - (att.mensural.shared (@modusmaior, @modusminor, @prolatio, @tempus))))

    - att.staffDef.vis (all)
    - att.staffDef.ges (all)
    - att.staffDef.anl (none exist)

    **Contained Elements not Implemented:**

    - MEI.cmn: meterSig meterSigGrp
    - MEI.mensural: mensur proport
    - MEI.shared: clefGrp keySig label layerDef
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement}

    # first make the Instrument
    post = elem.find('{}instrDef'.format(_MEINS))
    if post is not None:
        post = {'instrument': instrDefFromElement(post)}
    else:
        try:
            post = {'instrument': instrument.fromString(elem.get('label', ''))}
        except instrument.InstrumentException:
            post = {}

    if 'instrument' in post:
        post['instrument'].partName = elem.get('label')
        post['instrument'].partAbbreviation = elem.get('label.abbr')
        post['instrument'].partId = elem.get('n')

    # --> transposition
    if elem.get('trans.semi') is not None:
        if 'instrument' not in post:
            post['instrument'] = instrument.Instrument()
        post['instrument'].transposition = _transpositionFromAttrs(elem)

    # process other part-specific information
    # --> time signature
    if elem.get('meter.count') is not None:
        post['meter'] = _timeSigFromAttrs(elem)

    # --> key signature
    if elem.get('key.pname') is not None or elem.get('key.sig') is not None:
        post['key'] = _keySigFromAttrs(elem)

    # --> clef
    if elem.get('clef.shape') is not None:
        post['clef'] = clefFromElement(ETree.Element('clef', {
                                                      'shape': elem.get('clef.shape'),
                                                      'line': elem.get('clef.line'),
                                                      'dis': elem.get('clef.dis'),
                                                      'dis.place': elem.get('clef.dis.place')}))

    embeddedItems = _processEmbeddedElements(elem.findall('*'), tagToFunction, elem.tag, slurBundle)
    for eachItem in embeddedItems:
        if isinstance(eachItem, clef.Clef):
            post['clef'] = eachItem

    return post


def dotFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    Returns ``1`` no matter what is passed in.

    <dot> Dot of augmentation or division.

    In MEI 2013: pg.304 (318 in PDF) (MEI.shared module)

    :returns: 1
    :rtype: int

    **Attributes/Elements Implemented:** none

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.dot.log (all)
    - att.dot.vis (all)
    - att.dot.gesatt.dot.anl (all)

    **Elements not Implemented:** none
    '''
    return 1


def articFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <artic> An indication of how to play a note or chord.

    In MEI 2013: pg.259 (273 in PDF) (MEI.shared module)

    :returns: A list of :class:`~music21.articulations.Articulation` objects.

    **Examples**

    This function is normally called by, for example, :func:`noteFromElement`, to determine the
    :class:`Articulation` objects that will be assigned to the
    :attr:`~music21.note.GeneralNote.articulations` attribute.

    >>> from xml.etree import ElementTree as ET
    >>> from music21 import *
    >>> meiSnippet = """<artic artic="acc" xmlns="http://www.music-encoding.org/ns/mei"/>"""
    >>> meiSnippet = ET.fromstring(meiSnippet)
    >>> mei.base.articFromElement(meiSnippet)
    [<music21.articulations.Accent>]

    A single <artic> element may indicate many :class:`Articulation` objects.

    >>> meiSnippet = """<artic artic="acc ten" xmlns="http://www.music-encoding.org/ns/mei"/>"""
    >>> meiSnippet = ET.fromstring(meiSnippet)
    >>> mei.base.articFromElement(meiSnippet)
    [<music21.articulations.Accent>, <music21.articulations.Tenuto>]

    **Attributes Implemented:**

    - @artic

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.typography (@fontfam, @fontname, @fontsize, @fontstyle, @fontweight)
    - att.artic.log

        - (att.controlevent

            - (att.plist (@plist, @evaluate))
            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff))
            - (att.layerident (@layer)))

    - att.artic.vis (all)
    - att.artic.gesatt.artic.anl (all)

    **Contained Elements not Implemented:** none
    '''
    return _makeArticList(elem.get('artic'))


def accidFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <accid> Records a temporary alteration to the pitch of a note.

    In MEI 2013: pg.248 (262 in PDF) (MEI.shared module)

    :returns: A string indicating the music21 representation of this accidental.

    **Examples**

    Unlike most of the ___FromElement() functions, this does not return any music21 object---just
    a string. Accidentals up to triple-sharp and triple-flat are supported.

    >>> from xml.etree import ElementTree as ET
    >>> from music21 import *
    >>> meiSnippet = """<accid accid="s" xmlns="http://www.music-encoding.org/ns/mei"/>"""
    >>> meiSnippet = ET.fromstring(meiSnippet)
    >>> mei.base.accidFromElement(meiSnippet)
    '#'
    >>> meiSnippet = """<accid accid="tf" xmlns="http://www.music-encoding.org/ns/mei"/>"""
    >>> meiSnippet = ET.fromstring(meiSnippet)
    >>> mei.base.accidFromElement(meiSnippet)
    '---'

    **Attributes/Elements Implemented:**

    - @accid (from att.accid.log)

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.typography (@fontfam, @fontname, @fontsize, @fontstyle, @fontweight)
    - att.accid.log (@func)

        - (att.controlevent

            - (att.plist (@plist, @evaluate))
            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff)) (att.layerident (@layer)))

    - att.accid.vis (all)
    - att.accid.gesatt.accid.anl (all)

    **Contained Elements not Implemented:** none
    '''
    return _accidentalFromAttr(elem.get('accid'))


def sylFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <syl> Individual lyric syllable.

    In MEI 2013: pg.454 (468 in PDF) (MEI.shared module)

    :returns: An appropriately-configured :class:`music21.note.Lyric`.

    **Attributes/Elements Implemented:**

    - @con and @wordpos (from att.syl.log)

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.syl.vis (att.typography (@fontfam, @fontname, @fontsize, @fontstyle, @fontweight))

        - (att.visualoffset (att.visualoffset.ho (@ho))

            - (att.visualoffset.to (@to))
            - (att.visualoffset.vo (@vo)))

        - (att.xy (@x, @y))
        - (att.horizontalalign (@halign))

    - att.syl.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)

        -  (att.alignment (@when)))

    **Contained Elements not Implemented:**

    - MEI.edittrans: (all)
    - MEI.figtable: fig
    - MEI.namesdates: corpName geogName periodName persName styleName
    - MEI.ptrref: ptr ref
    - MEI.shared: address bibl date identifier lb name num rend repository stack title
    '''
    wordpos = elem.get('wordpos')
    wordposDict = {'i': 'begin', 'm': 'middle', 't': 'end', None: None}

    conDict = {'s': ' ', 'd': '-', 't': '~', 'u': '_', None: '-'}
    if 'i' == wordpos:
        text = elem.text + conDict[elem.get('con')]
    elif 'm' == wordpos:
        text = conDict[elem.get('con')] + elem.text + conDict[elem.get('con')]
    elif 't' == wordpos:
        text = conDict[elem.get('con')] + elem.text
    else:
        text = elem.text

    syllabic = wordposDict[wordpos]

    if syllabic:
        return note.Lyric(text=text, syllabic=syllabic, applyRaw=True)
    else:
        return note.Lyric(text=text)


def verseFromElement(elem, backupN=None, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <verse> Lyric verse.

    In MEI 2013: pg.480 (494 in PDF) (MEI.lyrics module)

    :param int backupN: The backup verse number to use if no @n attribute exists on ``elem``.
    :returns: The appropriately-configured :class:`Lyric` objects.
    :rtype: list of :class:`music21.note.Lyric`

    **Attributes/Elements Implemented:**

    - @n and <syl>

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.lang (@xml:lang)
    - att.verse.log (@refrain, @rhythm)
    - att.verse.vis (att.typography (@fontfam, @fontname, @fontsize, @fontstyle, @fontweight))

        - (att.visualoffset.to (@to))
        - ((att.visualoffset.vo (@vo))

            - (att.xy (@x, @y))

    - att.verse.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)

        - (att.alignment (@when)))

    **Contained Elements not Implemented:**

    - MEI.shared: dir dynam lb space tempo
    '''
    syls = [sylFromElement(s) for s in elem.findall('./{}syl'.format(_MEINS))]
    for eachSyl in syls:
        try:
            eachSyl.number = int(elem.get('n', backupN))
        except (TypeError, ValueError):
            environLocal.warn(_BAD_VERSE_NUMBER.format(elem.get('n', backupN)))
    return syls


def noteFromElement(elem, slurBundle=None):
    # NOTE: this function should stay in sync with chordFromElement() where sensible
    '''
    <note> is a single pitched event.

    In MEI 2013: pg.382 (396 in PDF) (MEI.shared module)

    .. note:: If set, the @accid.ges attribute is always imported as the music21 :class:`Accidental`
        for this note. We assume it corresponds to the accidental implied by a key signature.

    .. note:: If ``elem`` contains both <syl> and <verse> elements as immediate children, the lyrics
        indicated with <verse> element(s) will always obliterate those given indicated with <syl>
        elements.

    **Attributes/Elements Implemented:**

    - @accid and <accid>
    - @accid.ges for key signatures
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
    - <syl> and <verse>

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.facsimile (@facs)
    - att.note.log

        - (att.event

            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff))
            - (att.layerident (@layer)))

        - (att.fermatapresent (@fermata))
        - (att.syltext (@syl))
        - (att.note.log.cmn

            - (att.tupletpresent (@tuplet))
            - (att.beamed (@beam))
            - (att.lvpresent (@lv))
            - (att.ornam (@ornam)))

        - (att.note.log.mensural (@lig))

    - att.note.vis (all)

    - att.note.ges

        - (@oct.ges, @pname.ges, @pnum)
        - att.articulation.performed (@artic.ges))
        - (att.duration.performed (@dur.ges))
        - (att.instrumentident (@instr))
        - (att.note.ges.cmn (@gliss)

            - (att.graced (@grace, @grace.time)))  <-- partially implemented

        - (att.note.ges.mensural (att.duration.ratio (@num, @numbase)))
        - (att.note.ges.tablature (@tab.fret, @tab.string))

    - att.note.anl (all)

    **Contained Elements not Implemented:**

    - MEI.critapp: app
    - MEI.edittrans: (all)
    '''
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}dot': dotFromElement,
                     '{http://www.music-encoding.org/ns/mei}artic': articFromElement,
                     '{http://www.music-encoding.org/ns/mei}accid': accidFromElement,
                     '{http://www.music-encoding.org/ns/mei}syl': sylFromElement}

    # start with a Note with Pitch
    theNote = _accidentalFromAttr(elem.get('accid'))
    theNote = safePitch(elem.get('pname', ''), theNote, elem.get('oct', ''))
    theNote = note.Note(theNote)

    # set the Note's duration
    theDuration = _qlDurationFromAttr(elem.get('dur'))
    theDuration = makeDuration(theDuration, int(elem.get('dots', 0)))
    theNote.duration = theDuration

    # iterate all immediate children
    dotElements = 0  # count the number of <dot> elements
    for subElement in _processEmbeddedElements(elem.findall('*'),
                                               tagToFunction, 
                                               elem.tag, 
                                               slurBundle):
        if isinstance(subElement, six.integer_types):
            dotElements += subElement
        elif isinstance(subElement, articulations.Articulation):
            theNote.articulations.append(subElement)
        elif isinstance(subElement, six.string_types):
            theNote.pitch.accidental = pitch.Accidental(subElement)
        elif isinstance(subElement, note.Lyric):
            theNote.lyrics = [subElement]

    # adjust for @accid.ges if present
    if elem.get('accid.ges') is not None:
        theNote.pitch.accidental = pitch.Accidental(_accidGesFromAttr(elem.get('accid.ges', '')))

    # we can only process slurs if we got a SpannerBundle as the "slurBundle" argument
    if slurBundle is not None:
        addSlurs(elem, theNote, slurBundle)

    # id in the @xml:id attribute
    if elem.get(_XMLID) is not None:
        theNote.id = elem.get(_XMLID)

    # articulations in the @artic attribute
    if elem.get('artic') is not None:
        theNote.articulations.extend(_makeArticList(elem.get('artic')))

    # ties in the @tie attribute
    if elem.get('tie') is not None:
        theNote.tie = _tieFromAttr(elem.get('tie'))

    # dots from inner <dot> elements
    if dotElements > 0:
        theNote.duration = makeDuration(_qlDurationFromAttr(elem.get('dur')), dotElements)

    # grace note (only mark as grace note---don't worry about "time-stealing")
    if elem.get('grace') is not None:
        theNote.duration = duration.GraceDuration(theNote.duration.quarterLength)

    # beams indicated by a <beamSpan> held elsewhere
    if elem.get('m21Beam') is not None:
        if duration.convertTypeToNumber(theNote.duration.type) > 4:
            theNote.beams.fill(theNote.duration.type, elem.get('m21Beam'))

    # tuplets
    if elem.get('m21TupletNum') is not None:
        theNote = scaleToTuplet(theNote, elem)

    # lyrics indicated with <verse>
    if elem.find('./{}verse'.format(_MEINS)) is not None:
        tempLyrics = []
        for i, eachVerse in enumerate(elem.findall('./{}verse'.format(_MEINS))):
            tempLyrics.extend(verseFromElement(eachVerse, backupN=i + 1))
        theNote.lyrics = tempLyrics

    return theNote


def restFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <rest/> is a non-sounding event found in the source being transcribed

    In MEI 2013: pg.424 (438 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**

    - xml:id (or id), an XML id (submitted as the Music21Object "id")
    - dur, from att.duration.musical: (via _qlDurationFromAttr())
    - dots, from att.augmentdots: [0..4]

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.facsimile (@facs)
    - att.rest.log

        - (att.event

            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff))
            - (att.layerident (@layer)))

        - (att.fermatapresent (@fermata))

            - (att.tupletpresent (@tuplet))
            - (att.rest.log.cmn (att.beamed (@beam)))

    - att.rest.vis (all)
    - att.rest.ges (all)
    - att.rest.anl (all)

    **Contained Elements not Implemented:** none
    '''
    # NOTE: keep this in sync with spaceFromElement()

    theDuration = _qlDurationFromAttr(elem.get('dur'))
    theDuration = makeDuration(theDuration, int(elem.get('dots', 0)))
    theRest = note.Rest(duration=theDuration)

    if elem.get(_XMLID) is not None:
        theRest.id = elem.get(_XMLID)

    # tuplets
    if elem.get('m21TupletNum') is not None:
        theRest = scaleToTuplet(theRest, elem)

    return theRest


def mRestFromElement(elem, slurBundle=None):
    '''
    <mRest/> Complete measure rest in any meter.

    In MEI 2013: pg.375 (389 in PDF) (MEI.cmn module)

    This is a function wrapper for :func:`restFromElement`.

    .. note:: If the <mRest> element does not have a @dur attribute, it will have the default
        duration of 1.0. This must be fixed later, so the :class:`Rest` object returned from this
        method is given the :attr:`m21wasMRest` attribute, set to True.
    '''
    # NOTE: keep this in sync with mSpaceFromElement()

    if elem.get('dur') is not None:
        return restFromElement(elem, slurBundle)
    else:
        theRest = restFromElement(elem, slurBundle)
        theRest.m21wasMRest = True
        return theRest


def spaceFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <space>  A placeholder used to fill an incomplete measure, layer, etc. most often so that the
    combined duration of the events equals the number of beats in the measure.

    In MEI 2013: pg.440 (455 in PDF) (MEI.shared module)
    '''
    # NOTE: keep this in sync with restFromElement()

    theDuration = _qlDurationFromAttr(elem.get('dur'))
    theDuration = makeDuration(theDuration, int(elem.get('dots', 0)))
    theSpace = note.SpacerRest(duration=theDuration)

    if elem.get(_XMLID) is not None:
        theSpace.id = elem.get(_XMLID)

    # tuplets
    if elem.get('m21TupletNum') is not None:
        theSpace = scaleToTuplet(theSpace, elem)

    return theSpace


def mSpaceFromElement(elem, slurBundle=None):
    '''
    <mSpace/> A measure containing only empty space in any meter.

    In MEI 2013: pg.377 (391 in PDF) (MEI.cmn module)

    This is a function wrapper for :func:`spaceFromElement`.

    .. note:: If the <mSpace> element does not have a @dur attribute, it will have the default
        duration of 1.0. This must be fixed later, so the :class:`Space` object returned from this
        method is given the :attr:`m21wasMRest` attribute, set to True.
    '''
    # NOTE: keep this in sync with mRestFromElement()

    if elem.get('dur') is not None:
        return spaceFromElement(elem, slurBundle)
    else:
        theSpace = spaceFromElement(elem, slurBundle)
        theSpace.m21wasMRest = True
        return theSpace


def chordFromElement(elem, slurBundle=None):
    # NOTE: this function should stay in sync with noteFromElement() where sensible
    '''
    <chord> is a simultaneous sounding of two or 
    more notes in the same layer with the same duration.

    In MEI 2013: pg.280 (294 in PDF) (MEI.shared module)

    **Attributes/Elements Implemented:**

    - @xml:id (or id), an XML id (submitted as the Music21Object "id")
    - <note> contained within
    - @dur, from att.duration.musical: (via _qlDurationFromAttr())
    - @dots, from att.augmentdots: [0..4]
    - @artic and <artic>
    - @tie, (many of "[i|m|t]")
    - @slur, (many of "[i|m|t][1-6]")
    - @grace, from att.note.ges.cmn: partial implementation (notes marked as grace, but the
        duration is 0 because we ignore the question of which neighbouring note to borrow time from)

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.facsimile (@facs)
    - att.chord.log

        - (att.event

            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff))
            - (att.layerident (@layer)))

        - (att.fermatapresent (@fermata))
        - (att.syltext (@syl))
        - (att.chord.log.cmn

            - (att.tupletpresent (@tuplet))
            - (att.beamed (@beam))
            - (att.lvpresent (@lv))
            - (att.ornam (@ornam)))

    - att.chord.vis (all)
    - att.chord.ges

        - (att.articulation.performed (@artic.ges))
        - (att.duration.performed (@dur.ges))
        - (att.instrumentident (@instr))
        - (att.chord.ges.cmn (att.graced (@grace, @grace.time)))  <-- partially implemented

    - att.chord.anl (all)

    **Contained Elements not Implemented:**

    - MEI.edittrans: (all)
    '''
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}note': lambda *x: None,
                     '{http://www.music-encoding.org/ns/mei}artic': articFromElement}

    # start with a Chord with a bunch of Notes
    theChord = []
    for eachNote in elem.iterfind('{}note'.format(_MEINS)):
        theChord.append(noteFromElement(eachNote, slurBundle))
    theChord = chord.Chord(notes=theChord)

    # set the Chord's duration
    theDuration = _qlDurationFromAttr(elem.get('dur'))
    theDuration = makeDuration(theDuration, int(elem.get('dots', 0)))
    theChord.duration = theDuration


    # iterate all immediate children
    for subElement in _processEmbeddedElements(elem.findall('*'), 
                                               tagToFunction, 
                                               elem.tag, 
                                               slurBundle):
        if isinstance(subElement, articulations.Articulation):
            theChord.articulations.append(subElement)

    # we can only process slurs if we got a SpannerBundle as the "slurBundle" argument
    if slurBundle is not None:
        addSlurs(elem, theChord, slurBundle)

    # id in the @xml:id attribute
    if elem.get(_XMLID) is not None:
        theChord.id = elem.get(_XMLID)

    # articulations in the @artic attribute
    if elem.get('artic') is not None:
        theChord.articulations.extend(_makeArticList(elem.get('artic')))

    # ties in the @tie attribute
    if elem.get('tie') is not None:
        theChord.tie = _tieFromAttr(elem.get('tie'))

    # grace note (only mark as grace note---don't worry about "time-stealing")
    if elem.get('grace') is not None:
        theChord.duration = duration.GraceDuration(theChord.duration.quarterLength)

    # beams indicated by a <beamSpan> held elsewhere
    if elem.get('m21Beam') is not None:
        if duration.convertTypeToNumber(theChord.duration.type) > 4:
            theChord.beams.fill(theChord.duration.type, elem.get('m21Beam'))

    # tuplets
    if elem.get('m21TupletNum') is not None:
        theChord = scaleToTuplet(theChord, elem)

    return theChord


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

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.event

        - (att.timestamp.musical (@tstamp))
        - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
        - (att.staffident (@staff))
        - (att.layerident (@layer))

    - att.facsimile (@facs)
    - att.clef.anl (all)
    - att.clef.vis (all)

    **Contained Elements not Implemented:** none
    '''
    if 'perc' == elem.get('shape'):
        theClef = clef.PercussionClef()
    elif 'TAB' == elem.get('shape'):
        theClef = clef.TabClef()
    else:
        theClef = clef.clefFromString(elem.get('shape') + elem.get('line'),
                                      octaveShift=_getOctaveShift(elem.get('dis'),
                                                                  elem.get('dis.place')))

    if elem.get(_XMLID) is not None:
        theClef.id = elem.get(_XMLID)

    return theClef


def instrDefFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    # TODO: robuster handling of <instrDef>, including <instrGrp> and if held in a <staffGrp>
    '''
    <instrDef> (instrument definition)---MIDI instrument declaration.

    In MEI 2013: pg.344 (358 in PDF) (MEI.midi module)

    :returns: An :class:`Instrument`

    **Attributes/Elements Implemented:**

    - @midi.instrname (att.midiinstrument)
    - @midi.instrnum (att.midiinstrument)

    **Attributes/Elements in Testing:** none

    **Attributes/Elements Ignored:**

    - @xml:id

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.channelized (@midi.channel, @midi.duty, @midi.port, @midi.track)
    - att.midiinstrument (@midi.pan, @midi.volume)

    **Contained Elements not Implemented:** none
    '''
    if elem.get('midi.instrnum') is not None:
        return instrument.instrumentFromMidiProgram(int(elem.get('midi.instrnum')))
    else:
        try:
            return instrument.fromString(elem.get('midi.instrname'))
        except (AttributeError, instrument.InstrumentException):
            theInstr = instrument.Instrument()
            theInstr.partName = elem.get('midi.instrname', '')
            return theInstr


def beamFromElement(elem, slurBundle=None):
    '''
    <beam> A container for a series of explicitly beamed events that begins and ends entirely
           within a measure.

    In MEI 2013: pg.264 (278 in PDF) (MEI.cmn module)

    :param elem: The ``<beam>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: An iterable of all the objects contained within the ``<beam>`` container.
    :rtype: list of :class:`~music21.base.Music21Object`

    **Example**

    Here, three :class:`Note` objects are beamed together. Take note that the function returns
    a list of three objects, none of which is a :class:`Beam` or similar.

    >>> from xml.etree import ElementTree as ET
    >>> from music21 import *
    >>> meiSnippet = """<beam xmlns="http://www.music-encoding.org/ns/mei">
    ...     <note pname='A' oct='7' dur='8'/>
    ...     <note pname='B' oct='7' dur='8'/>
    ...     <note pname='C' oct='6' dur='8'/>
    ... </beam>"""
    >>> meiSnippet = ET.fromstring(meiSnippet)
    >>> result = mei.base.beamFromElement(meiSnippet)
    >>> isinstance(result, list)
    True
    >>> len(result)
    3
    >>> result[0].pitch.nameWithOctave
    'A7'
    >>> result[0].beams
    <music21.beam.Beams <music21.beam.Beam 1/start>>
    >>> result[1].pitch.nameWithOctave
    'B7'
    >>> result[1].beams
    <music21.beam.Beams <music21.beam.Beam 1/continue>>
    >>> result[2].pitch.nameWithOctave
    'C6'
    >>> result[2].beams
    <music21.beam.Beams <music21.beam.Beam 1/stop>>

    **Attributes/Elements Implemented:**

    - <clef>, <chord>, <note>, <rest>, <space>, <tuplet>, <beam>, <barLine>

    **Attributes/Elements Ignored:**

    - @xml:id

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.facsimile (@facs)
    - att.beam.log

        - (att.event

            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff))
            - (att.layerident (@layer)))

        - (att.beamedwith (@beam.with))

    - att.beam.vis (all)
    - att.beam.gesatt.beam.anl (all)

    **Contained Elements not Implemented:**

    - MEI.cmn: bTrem beatRpt fTrem halfmRpt meterSig meterSigGrp
    - MEI.critapp: app
    - MEI.edittrans: (all)
    - MEI.mensural: ligature mensur proport
    - MEI.shared: clefGrp custos keySig pad
    '''
    # NB: The doctest is a sufficient integration test. Since there is no logic, I don't think we
    #     need to bother with unit testing.

    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement,
                     '{http://www.music-encoding.org/ns/mei}tuplet': tupletFromElement,
                     '{http://www.music-encoding.org/ns/mei}beam': beamFromElement,
                     '{http://www.music-encoding.org/ns/mei}space': spaceFromElement,
                     '{http://www.music-encoding.org/ns/mei}barLine': barLineFromElement}

    beamedStuff = _processEmbeddedElements(elem.findall('*'), tagToFunction, elem.tag, slurBundle)
    beamedStuff = beamTogether(beamedStuff)

    return beamedStuff


def barLineFromElement(elem, slurBundle=None):  # pylint: disable=unused-argument
    '''
    <barLine> Vertical line drawn through one or more staves that divides musical notation into
    metrical units.

    In MEI 2013: pg.262 (276 in PDF) (MEI.shared module)

    :returns: A :class:`music21.bar.Barline` or :class:`~music21.bar.Repeat`, depending on the
        value of @rend. If @rend is ``'rptboth'``, a 2-tuplet of :class:`Repeat` objects will be
        returned, represented an "end" and "start" barline, as specified in the :mod:`music21.bar`
        documentation.

    .. note:: The music21-to-other converters expect that a :class:`Barline` will be attached to a
        :class:`Measure`, which it will not be when imported from MEI as a <barLine> element.
        However, this function does import correctly to a :class:`Barline` that you can access from
        Python in the :class:`Stream` object as expected.

    **Attributes/Elements Implemented:**

    - @rend from att.barLine.log

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.pointing (@xlink:actuate, @xlink:role, @xlink:show, @target, @targettype, @xlink:title)
    - att.barLine.log

        - (att.meterconformance.bar (@metcon, @control))

    - att.barLine.vis

        - (att.barplacement (@barplace, @taktplace))
        - (att.color (@color))
        - (att.measurement (@unit))
        - (att.width (@width))

    - att.barLine.ges (att.timestamp.musical (@tstamp))
    - att.barLine.anl

        - (att.common.anl

            - (@copyof, @corresp, @next, @prev, @sameas, @synch)
            - (att.alignment (@when)))

    **Contained Elements not Implemented:** none
    '''
    return _barlineFromAttr(elem.get('rend', 'single'))


def tupletFromElement(elem, slurBundle=None):
    '''
    <tuplet> A group of notes with "irregular" (sometimes called "irrational") rhythmic values,
    for example, three notes in the time normally occupied by two or nine in the time of five.

    In MEI 2013: pg.473 (487 in PDF) (MEI.cmn module)

    :param elem: The ``<tuplet>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: An iterable of all the objects contained within the ``<tuplet>`` container.
    :rtype: tuple of :class:`~music21.base.Music21Object`

    **Attributes/Elements Implemented:**

    - <tuplet>, <beam>, <note>, <rest>, <chord>, <clef>, <space>, <barLine>
    - @num and @numbase

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.facsimile (@facs)
    - att.tuplet.log

        - (att.event

            - (att.timestamp.musical (@tstamp))
            - (att.timestamp.performed (@tstamp.ges, @tstamp.real))
            - (att.staffident (@staff))
            - (att.layerident (@layer)))

        - (att.beamedwith (@beam.with))
        - (att.augmentdots (@dots))
        - (att.duration.additive (@dur))
        - (att.startendid (@endid) (att.startid (@startid)))

    - att.tuplet.vis (all)
    - att.tuplet.ges (att.duration.performed (@dur.ges))
    - att.tuplet.anl (all)

    **Contained Elements not Implemented:**

    - MEI.cmn: bTrem beatRpt fTrem halfmRpt meterSig meterSigGrp
    - MEI.critapp: app
    - MEI.edittrans: (all)
    - MEI.mensural: ligature mensur proport
    - MEI.shared: clefGrp custos keySig pad
    '''
    # mapping from tag name to our converter function
    tagToFunction = {'{http://www.music-encoding.org/ns/mei}tuplet': tupletFromElement,
                     '{http://www.music-encoding.org/ns/mei}beam': beamFromElement,
                     '{http://www.music-encoding.org/ns/mei}note': noteFromElement,
                     '{http://www.music-encoding.org/ns/mei}rest': restFromElement,
                     '{http://www.music-encoding.org/ns/mei}chord': chordFromElement,
                     '{http://www.music-encoding.org/ns/mei}clef': clefFromElement,
                     '{http://www.music-encoding.org/ns/mei}space': spaceFromElement,
                     '{http://www.music-encoding.org/ns/mei}barLine': barLineFromElement}

    # get the @num and @numbase attributes, without which we can't properly calculate the tuplet
    if elem.get('num') is None or elem.get('numbase') is None:
        raise MeiAttributeError(_MISSING_TUPLET_DATA)

    # iterate all immediate children
    tupletMembers = _processEmbeddedElements(elem.findall('*'), tagToFunction, elem.tag, slurBundle)

    # "tuplet-ify" the duration of everything held within
    newElem = ETree.Element('c', m21TupletNum=elem.get('num'), m21TupletNumbase=elem.get('numbase'))
    tupletMembers = scaleToTuplet(tupletMembers, newElem)

    # Set the Tuplet.type property for the first and final note in a tuplet.
    # We have to find the first and last duration-having thing, not just the first and last objects
    # between the <tuplet> tags.
    firstNote = None
    lastNote = None
    for i, eachObj in enumerate(tupletMembers):
        if firstNote is None and isinstance(eachObj, note.GeneralNote):
            firstNote = i
        elif isinstance(eachObj, note.GeneralNote):
            lastNote = i

    tupletMembers[firstNote].duration.tuplets[0].type = 'start'
    if lastNote is None:
        # when there is only one object in the tuplet
        tupletMembers[firstNote].duration.tuplets[0].type = 'stop'
    else:
        tupletMembers[lastNote].duration.tuplets[0].type = 'stop'

    # beam it all together
    tupletMembers = beamTogether(tupletMembers)

    return tuple(tupletMembers)


def layerFromElement(elem, overrideN=None, slurBundle=None):
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

    :param elem: The ``<layer>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param str overrideN: The value to be set as the ``id`` 
        attribute in the outputted :class:`Voice`.
    :returns: A :class:`Voice` with the objects found in the provided :class:`Element`.
    :rtype: :class:`music21.stream.Voice`
    :raises: :exc:`MeiAttributeError` if neither ``overrideN`` nor @n are specified.

    **Attributes/Elements Implemented:**

    - <clef>, <chord>, <note>, <rest>, <mRest>, <beam>, <tuplet>, <space>, <mSpace> , and
      <barLine> contained within
    - @n, from att.common

    **Attributes Ignored:**

    - @xml:id

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @xml:base)
    - att.declaring (@decls)
    - att.facsimile (@facs)
    - att.layer.log (@def) and (att.meterconformance (@metcon))
    - att.layer.vis (att.visibility (@visible))
    - att.layer.gesatt.layer.anl (all)

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
                     '{http://www.music-encoding.org/ns/mei}mSpace': mSpaceFromElement,
                     '{http://www.music-encoding.org/ns/mei}barLine': barLineFromElement}

    # iterate all immediate children
    theLayer = _processEmbeddedElements(elem.iterfind('*'), tagToFunction, elem.tag, slurBundle)

    # adjust the <layer>'s elements for possible tuplets
    theLayer = _guessTuplets(theLayer)

    # make the Voice
    theVoice = stream.Voice()
    for each in theLayer:
        theVoice._appendCore(each)  # pylint: disable=protected-access
    theVoice.elementsChanged()

    # try to set the Voice's "id" attribte
    if overrideN:
        theVoice.id = overrideN
    elif elem.get('n') is not None:
        theVoice.id = elem.get('n')
    else:
        raise MeiAttributeError(_MISSING_VOICE_ID)

    return theVoice


def staffFromElement(elem, slurBundle=None):
    '''
    <staff> A group of equidistant horizontal lines on which notes are placed in order to
    represent pitch or a grouping element for individual 'strands' of notes, rests, etc. that may
    or may not actually be rendered on staff lines; that is, both diastematic and non-diastematic
    signs.

    In MEI 2013: pg.444 (458 in PDF) (MEI.shared module)

    :param elem: The ``<staff>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :returns: The :class:`Voice` classes corresponding to the ``<layer>`` tags in ``elem``.
    :rtype: list of :class:`music21.stream.Voice`

    **Attributes/Elements Implemented:**

    - <layer> contained within

    **Attributes Ignored:**

    - @xml:id

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base)
    - att.declaring (@decls)
    - att.facsimile (@facs)
    - att.staff.log (@def) (att.meterconformance (@metcon))
    - att.staff.vis (att.visibility (@visible))
    - att.staff.gesatt.staff.anl (all)

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
    layers = []

    # track the @n values given to layerFromElement()
    currentNValue = '1'

    # iterate all immediate children
    for eachTag in elem.iterfind('*'):
        if layerTagName == eachTag.tag:
            layers.append(layerFromElement(eachTag, currentNValue, slurBundle=slurBundle))
            currentNValue = '{}'.format(int(currentNValue) + 1)  # inefficient, but we need a string
        elif eachTag.tag in tagToFunction:
            # NB: this won't be tested until there's something in tagToFunction
            layers.append(tagToFunction[eachTag.tag](eachTag, slurBundle))
        elif eachTag.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug(_UNPROCESSED_SUBELEMENT.format(eachTag.tag, elem.tag))

    return layers


def _correctMRestDurs(staves, targetLength):
    '''
    Helper function for measureFromElement(), not intended to be used elsewhere. It's a separate
    function only (1) to reduce duplication, and (2) to improve testability.

    Iterate the imported objects of <layer> elements in the <staff> elements in a <measure>,
    detecting those with the "m21wasMRest" attribute and setting their duration to "targetLength."

    The "staves" argument should be a dictionary where the values are Measure objects with at least
    one Voice object inside.

    The "targetLength" argument should be the duration of the measure.

    Nothing is returned; the duration of affected objects is modified in-place.
    '''
    for eachMeasure in six.itervalues(staves):
        for eachVoice in eachMeasure:
            if not isinstance(eachVoice, stream.Stream):
                continue
            for eachObject in eachVoice:
                if hasattr(eachObject, 'm21wasMRest'):
                    eachObject.quarterLength = targetLength
                    eachVoice.duration = duration.Duration(targetLength)
                    eachMeasure.duration = duration.Duration(targetLength)
                    del eachObject.m21wasMRest


def _makeBarlines(elem, staves):
    '''
    This is a helper function for :func:`measureFromElement`, made independent only to improve
    that function's ease of testing.

    Given a <measure> element and a dictionary with the :class:`Measure` objects that have already
    been processed, change the barlines of the :class:`Measure` objects in accordance with the
    element's @left and @right attributes.

    :param :class:`~xml.etree.ElementTree.Element` elem: The ``<measure>`` tag to process.
    :param dict staves: Dictionary where keys are @n attributes and values are corresponding
        :class:`~music21.stream.Measure` objects.
    :returns: The ``staves`` dictionary with properly-set barlines.
    :rtype: dict
    '''
    if elem.get('left') is not None:
        barz = _barlineFromAttr(elem.get('left'))
        if hasattr(barz, '__len__'):
            # this means @left was "rptboth"
            barz = barz[1]
        for eachMeasure in six.itervalues(staves):
            if isinstance(eachMeasure, stream.Measure):
                eachMeasure.leftBarline = barz

    if elem.get('right') is not None:
        barz = _barlineFromAttr(elem.get('right'))
        if hasattr(barz, '__len__'):
            # this means @right was "rptboth"
            staves['next @left'] = barz[1]
            barz = barz[0]
        for eachMeasure in six.itervalues(staves):
            if isinstance(eachMeasure, stream.Measure):
                eachMeasure.rightBarline = barz

    return staves


def measureFromElement(elem, backupNum, expectedNs, slurBundle=None, activeMeter=None):
    '''
    <measure> Unit of musical time consisting of a fixed number of note-values of a given type, as
    determined by the prevailing meter, and delimited in musical notation by two bar lines.

    In MEI 2013: pg.365 (379 in PDF) (MEI.cmn module)

    :param elem: The ``<measure>`` element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param int backupNum: A fallback value for the resulting 
        :class:`~music21.measure.Measure` objects' number attribute.
    :param expectedNs: A list of the expected @n attributes for the <staff> tags in this <measure>.
        If an expected <staff> isn't in the <measure>, it will be created with a full-measure rest.
    :type expectedNs: iterable of str
    :param activeMeter: The :class:`~music21.meter.TimeSignature` active in this <measure>. This is
        used to adjust the duration of an <mRest> that was given without a @dur attribute.
    :returns: A dictionary where keys are the @n attributes for <staff> tags found in this
        <measure>, and values are :class:`~music21.stream.Measure` objects that should be appended
        to the :class:`Part` instance with the value's @n attributes.
    :rtype: dict of :class:`music21.stream.Measure`

    .. note:: When the right barline is set to ``'rptboth'`` in MEI, it requires adjusting the left
        barline of the following <measure>. If this happens, the :class:`Repeat` object is assigned
        to the ``'next @left'`` key in the returned dictionary.

    **Attributes/Elements Implemented:**

    - contained elements: <staff> and <staffDef>
    - @right and @left (att.measure.log)
    - @n (att.common)

    **Attributes Ignored:**

    - @xml:id (att.id)
    - <slur> and <tie> contained within. These spanners will usually be attached to their starting
      and ending notes with @xml:id attributes, so it's not necessary to process them when
      encountered in a <measure>. Furthermore, because the possibility exists for cross-measure
      slurs and ties, we can't guarantee we'll be able to process all spanners until all
      spanner-attachable objects are processed. So we manage these tags at a higher level.

    **Attributes/Elements in Testing:** none

    **Attributes not Implemented:**

    - att.common (@label, @xml:base)
    - att.declaring (@decls)
    - att.facsimile (@facs)
    - att.typed (@type, @subtype)
    - att.pointing (@xlink:actuate, @xlink:role, @xlink:show, @target, @targettype, @xlink:title)
    - att.measure.log (att.meterconformance.bar (@metcon, @control))
    - att.measure.vis (all)
    - att.measure.ges (att.timestamp.performed (@tstamp.ges, @tstamp.real))
    - att.measure.anl (all)

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
    - MEI.shared: annot dir dynam pb phrase sb tempo
    - MEI.text: div
    - MEI.usersymbols: anchoredText curve line symbol
    '''
    staves = {}
    stavesWaiting = {}  # for staff-specific objects processed before the corresponding staff

    # mapping from tag name to our converter function
    staffTag = '{http://www.music-encoding.org/ns/mei}staff'
    staffDefTag = '{http://www.music-encoding.org/ns/mei}staffDef'

    # track the bar's duration
    maxBarDuration = None

    # iterate all immediate children
    for eachElem in elem.iterfind('*'):
        if staffTag == eachElem.tag:
            staves[eachElem.get('n')] = stream.Measure(staffFromElement(eachElem, 
                                                                        slurBundle=slurBundle),
                                                       number=int(elem.get('n', backupNum)))
            thisBarDuration = staves[eachElem.get('n')].duration.quarterLength
            if maxBarDuration is None or maxBarDuration < thisBarDuration:
                maxBarDuration = thisBarDuration
        elif staffDefTag == eachElem.tag:
            whichN = eachElem.get('n')
            if whichN is None:
                environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<staffDef>', '@n'))
            else:
                stavesWaiting[whichN] = staffDefFromElement(eachElem, slurBundle)
        elif eachElem.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug(_UNPROCESSED_SUBELEMENT.format(eachElem.tag, elem.tag))

    # Process objects from a <staffDef>...
    # We must process them now because, if we did it in the loop above, the respective <staff> may
    # not be processed before the <staffDef>.
    for whichN, eachDict in six.iteritems(stavesWaiting):
        for eachObj in six.itervalues(eachDict):
            # We must insert() these objects because a <staffDef> signals its changes for the
            # *start* of the <measure> in which it appears.
            staves[whichN].insert(0, eachObj)

    # create rest-filled measures for expected parts that had no <staff> tag in this <measure>
    for eachN in expectedNs:
        if eachN not in staves:
            restVoice = stream.Voice([note.Rest(quarterLength=maxBarDuration)])
            restVoice.id = '1'
            # just in case (e.g., when all the other voices are <mRest>)
            restVoice[0].m21wasMRest = True  
            staves[eachN] = stream.Measure([restVoice], number=int(elem.get('n', backupNum)))

    # First search for Rest objects created by an <mRest> element that didn't have @dur set. This
    # will only work in cases where not all of the parts are resting. However, it avoids a more
    # time-consuming search later.
    if (maxBarDuration == _DUR_ATTR_DICT[None] 
            and activeMeter is not None 
            and maxBarDuration != activeMeter.barDuration.quarterLength):
        # In this case, all the staves have <mRest> elements without a @dur.
        _correctMRestDurs(staves, activeMeter.barDuration.quarterLength)
    else:
        # In this case, some or none of the staves have an <mRest> element without a @dur.
        _correctMRestDurs(staves, maxBarDuration)

    # assign left and right barlines
    staves = _makeBarlines(elem, staves)

    return staves


def sectionScoreCore(elem, allPartNs, slurBundle, **kwargs):
    '''
    This function is the "core" of both :func:`sectionFromElement` and :func:`scoreFromElement`,
    since both elements are treated quite similarly (though not identically). It's a separate and
    shared function to reduce code duplication and 
    increase ease of testing. It's a "public" function
    to help spread the burden of API documentation complexity: while the parameters and return
    values are described in this function, the compliance with the MEI Guidelines is described in
    both :func:`sectionFromElement` and :func:`scoreFromElement`, as expected.

    **Required Parameters**

    :param elem: The <section> or <score> element to process.
    :type elem: :class:`xml.etree.ElementTree.Element`
    :param allPartNs: A list or tuple of the expected @n attributes for the <staff> tags in this
        <section>. This tells the function how many parts there are and what @n values they use.
    :type allPartNs: iterable of str
    :param slurBundle: This :class:`SpannerBundle` holds the :class:`~music21.spanner.Slur` objects
        created during pre-processing. The slurs are attached to their respective :class:`Note` and
        :class:`Chord` objects as they are processed.
    :type slurBundle: :class:`music21.spanner.SpannerBundle`

    **Optional Keyword Parameters**

    The following parameters are all optional, and must be specified as a keyword argument (i.e.,
    you specify the parameter name before its value).

    :param activeMeter: The :class:`~music21.meter.TimeSignature` active at the start of this
        <section> or <score>. This is updated automatically as the music is processed, and the
        :class:`TimeSignature` active at the end of the element is returned.
    :type activeMeter: :class:`music21.meter.TimeSignature`
    :param nextMeasureLeft: The @left attribute to use for the next <measure> element encountered.
        This is used for situations where one <measure> element specified a @right attribute that
        must be imported by music21 as *both* the right barline of one measure and the left barline
        of the following; at the moment this is only @rptboth, which requires a :class:`Repeat` in
        both cases.
    :type nextMeasureLeft: :class:`music21.bar.Barline` or :class:`music21.bar.Repeat`
    :param backupMeasureNum: In case a <measure> element is missing its @n attribute,
        :func:`measureFromElement` will use this automatically-incremented number instead. The
        ``backupMeasureNum`` corresponding to the final <measure> in this <score> or <section> is
        returned from this function.
    :type backupMeasureNum: int
    :returns: Four-tuple with a dictionary of results, the new value of ``activeMeter``, the new
        value of ``nextMeasureLeft``, and the new value of ``backupMeasureNum``.
    :rtype: (dict, :class:`~music21.meter.TimeSignature`, :class:`~music21.bar.Barline`, int)

    **Return Value**

    In short, it's ``parsed``, ``activeMeter``, ``nextMeasureLeft``, ``backupMeasureNum``.

    - ``'parsed'`` is a dictionary where the keys are the values in ``allPartNs`` and the values are
        a list of all the :class:`Measure` objects in that part, as found in this <section> or
        <score>.
    - ``'activeMeter'`` is the :class:`~music21.meter.TimeSignature` in effect at the end of this
        <section> or <score>.
    - ``'nextMeasureLeft'`` is the value that should be 
        assigned to the :attr:`leftBarline` attribute
        of the first :class:`Measure` found in the next <section>. This will almost always be None.
    - ``'backupMeasureNum'`` is equal to the ``backupMeasureNum`` argument plus the number of
        <measure> elements found in this <score> or <section>.
    '''
    # pylint: disable=too-many-nested-blocks
    # ^^^ -- was not required at time of contribution
    
    # TODO: replace the returned 4-tuple with a namedtuple

    # set the optional kwargs
    activeMeter = kwargs['activeMeter'] if 'activeMeter' in kwargs else None
    nextMeasureLeft = kwargs['nextMeasureLeft'] if 'nextMeasureLeft' in kwargs else None
    backupMeasureNum = kwargs['backupMeasureNum'] if 'backupMeasureNum' in kwargs else 0

    # NOTE: "activeMeter" holds the TimeSignature object that's currently active; it's used in the
    # loop below to help determine the proper duration of a full-measure rest. It must persist
    # between <section> elements, so it's a parameter for this function.

    scoreTag = '{http://www.music-encoding.org/ns/mei}score'
    sectionTag = '{http://www.music-encoding.org/ns/mei}section'
    measureTag = '{http://www.music-encoding.org/ns/mei}measure'
    scoreDefTag = '{http://www.music-encoding.org/ns/mei}scoreDef'
    staffDefTag = '{http://www.music-encoding.org/ns/mei}staffDef'

    # hold the music21.stream.Part that we're building
    parsed = {n: [] for n in allPartNs}
    # hold things that belong in the following "Thing" (either Measure or Section)
    inNextThing = {n: [] for n in allPartNs}

    for eachElem in elem.iterfind('*'):
        # only process <measure> elements if this is a <section>
        if measureTag == eachElem.tag and sectionTag == elem.tag:
            backupMeasureNum += 1
            # process all the stuff in the <measure>
            measureResult = measureFromElement(eachElem, backupMeasureNum, allPartNs,
                                               slurBundle=slurBundle,
                                               activeMeter=activeMeter)
            # process and append each part's stuff to the staff
            for eachN in allPartNs:
                # insert objects specified in the immediately-preceding <scoreDef>
                for eachThing in inNextThing[eachN]:
                    measureResult[eachN].insert(0, eachThing)
                inNextThing[eachN] = []
                # if we got a left-side barline from the previous measure, use it
                if nextMeasureLeft is not None:
                    measureResult[eachN].leftBarline = nextMeasureLeft
                # add this Measure to the Part
                parsed[eachN].append(measureResult[eachN])
            # if we got a barline for the next <measure>
            if 'next @left' in measureResult:
                nextMeasureLeft = measureResult['next @left']
            else:
                nextMeasureLeft = None

        elif scoreDefTag == eachElem.tag:
            localResult = scoreDefFromElement(eachElem, slurBundle)
            for allPartObject in localResult['all-part objects']:
                if isinstance(allPartObject, meter.TimeSignature):
                    activeMeter = allPartObject
                for eachN in allPartNs:
                    inNextThing[eachN].append(allPartObject)
            for eachN in allPartNs:
                if eachN in localResult:
                    for eachObj in six.itervalues(localResult[eachN]):
                        inNextThing[eachN].append(eachObj)

        elif staffDefTag == eachElem.tag:
            if eachElem.get('n') is not None:
                for eachObj in six.itervalues(staffDefFromElement(eachElem, slurBundle)):
                    if isinstance(eachObj, meter.TimeSignature):
                        activeMeter = eachObj
                    inNextThing[eachElem.get('n')].append(eachObj)
            else:
                # At the moment, to process this here, we need an @n on the <staffDef>. A document
                # may have a still-valid <staffDef> if the <staffDef> has an @xml:id with which
                # <staff> elements may refer to it.
                environLocal.warn(_UNIMPLEMENTED_IMPORT.format('<staffDef>', '@n'))

        elif sectionTag == eachElem.tag:
            # NOTE: same as scoreFE() (except the name of "inNextThing")
            localParsed, activeMeter, nextMeasureLeft, backupMeasureNum = sectionFromElement(
                                                                 eachElem,
                                                                 allPartNs,
                                                                 activeMeter=activeMeter,
                                                                 nextMeasureLeft=nextMeasureLeft,
                                                                 backupMeasureNum=backupMeasureNum,
                                                                 slurBundle=slurBundle)
            for eachN, eachList in six.iteritems(localParsed):
                # NOTE: "eachList" is a list of objects that will become a music21 Part.
                #
                # first: if there were objects from a previous <scoreDef> or <staffDef>, we need to
                #        put those into the first Measure object we encounter in this Part
                # TODO: this is where the Instruments get added
                # TODO: I think "eachList" really means "each list that will become a Part"
                if len(inNextThing[eachN]) > 0:
                    # we have to put Instrument objects just before the Measure to which they apply
                    theInstr = None
                    theInstrI = None
                    for i, eachInsertion in enumerate(inNextThing[eachN]):
                        if isinstance(eachInsertion, instrument.Instrument):
                            theInstr = eachInsertion
                            theInstrI = i
                            break

                    # Put the Instrument right in front, then remove it from "inNextThing" so it
                    # doesn't show up twice.
                    if theInstr:
                        eachList.insert(0, theInstr)
                        del inNextThing[eachN][theInstrI]

                    for eachObj in eachList:
                        # NOTE: "eachObj" is one of the things that will be in the Part, which are
                        #       probably but not necessarily Measures
                        if isinstance(eachObj, stream.Stream):
                            # NOTE: ... but now eachObj is virtually guaranteed to be a Measure
                            for eachInsertion in inNextThing[eachN]:
                                eachObj.insert(0.0, eachInsertion)
                            break
                    inNextThing[eachN] = []
                # Then we can append the objects in this Part to the dict of all parsed objects, but
                # NOTE that this is different for <section> and <score>.
                if sectionTag == elem.tag:
                    # If this is a <section>, which would really be nested <section> elements, we
                    # must "flatten" everything so it doesn't cause a disaster when we try to make
                    # a Part out of it.
                    for eachObj in eachList:
                        parsed[eachN].append(eachObj)
                elif scoreTag == elem.tag:
                    # If this is a <score>, we can just append the result of each <section> to the
                    # list that will become the Part.
                    parsed[eachN].append(eachList)

        elif eachElem.tag not in _IGNORE_UNPROCESSED:
            environLocal.printDebug(_UNPROCESSED_SUBELEMENT.format(eachElem.tag, elem.tag))

    # TODO: write the <section @label=""> part
    # TODO: check if there's anything left in "inNextThing"

    return parsed, activeMeter, nextMeasureLeft, backupMeasureNum


def sectionFromElement(elem, allPartNs, activeMeter, nextMeasureLeft, backupMeasureNum, slurBundle):
    '''
    <section> Segment of music data.

    In MEI 2013: pg.432 (446 in PDF) (MEI.shared module)

    .. note:: The parameters and return values are exactly the same for :func:`sectionFromElement`
        and :func:`sectionScoreCore`, so refer to the latter function's documentation for more
        information.

    **Attributes/Elements Implemented:**

    **Attributes Ignored:**

    **Attributes/Elements in Testing:**

    - @label
    - contained <measure>, <scoreDef>, <staffDef>, <section>

    **Attributes not Implemented:**

    - att.common (@n, @xml:base) (att.id (@xml:id))
    - att.declaring (@decls)
    - att.facsimile (@facs)
    - att.typed (@type, @subtype)
    - att.pointing (@xlink:actuate, @xlink:role, @xlink:show, @target, @targettype, @xlink:title)
    - att.section.vis (@restart)
    - att.section.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                      (att.alignment (@when)))

    **Contained Elements not Implemented:**

    - MEI.critapp: app
    - MEI.edittrans: add choice corr damage del gap handShift orig reg 
                     restore sic subst supplied unclear
    - MEI.shared: annot ending expansion pb sb section staff
    - MEI.text: div
    - MEI.usersymbols: anchoredText curve line symbol
    '''
    environLocal.printDebug('*** processing a <section>')
    return sectionScoreCore(elem,
                            allPartNs,
                            slurBundle,
                            activeMeter=activeMeter,
                            nextMeasureLeft=nextMeasureLeft,
                            backupMeasureNum=backupMeasureNum)

def scoreFromElement(elem, slurBundle):
    '''
    <score> Full score view of the musical content.

    In MEI 2013: pg.430 (444 in PDF) (MEI.shared module)

    :param elem: The <score> element to process.
    :type elem: :class:`~xml.etree.ElementTree.Element`
    :param slurBundle: This :class:`SpannerBundle` holds the :class:`~music21.spanner.Slur` objects
        created during pre-processing. The slurs are attached to their respective :class:`Note` and
        :class:`Chord` objects as they are processed.
    :type slurBundle: :class:`music21.spanner.SpannerBundle`
    :returns: A completed :class:`~music21.stream.Score` object.

    **Attributes/Elements Implemented:**

    **Attributes Ignored:**

    **Attributes/Elements in Testing:**

    - contained <section>, <scoreDef>, and <staffDef>

    **Attributes not Implemented:**

    - att.common (@label, @n, @xml:base) (att.id (@xml:id))
    - att.declaring (@decls)
    - att.typed (@type, @subtype)
    - att.score.anl (att.common.anl (@copyof, @corresp, @next, @prev, @sameas, @synch)
                                    (att.alignment (@when)))

    **Contained Elements not Implemented:**

    - MEI.critapp: app
    - MEI.edittrans: add choice corr damage del gap handShift orig 
                     reg restore sic subst supplied unclear
    - MEI.shared: annot ending pb sb
    - MEI.text: div
    - MEI.usersymbols: anchoredText curve line symbol
    '''

    environLocal.printDebug('*** processing a <score>')
    # That's an outright lie. We're also processing <scoreDef>, <staffDef>, and other elements!

    # Get a tuple of all the @n attributes for the <staff> tags in this score. Each <staff> tag
    # corresponds to what will be a music21 Part.
    allPartNs = allPartsPresent(elem)

    # This is the actual processing.
    parsed = sectionScoreCore(elem, allPartNs, slurBundle=slurBundle)[0]

    # Convert the dict to a Score
    # We must iterate here over "allPartNs," which preserves the part-order found in the MEI
    # document. Iterating the keys in "parsed" would not preserve the order.
    environLocal.printDebug('*** making the Score')
    theScore = [stream.Part() for _ in range(len(allPartNs))]
    for i, eachN in enumerate(allPartNs):
        # set "atSoundingPitch" so transposition works
        theScore[i].atSoundingPitch = False
        for eachObj in parsed[eachN]:
            theScore[i].append(eachObj)
    theScore = stream.Score(theScore)

    # put slurs in the Score
    theScore.append(slurBundle.list)
    # TODO: when all the Slur objects are at the end, they'll only be outputted properly if the
    #       whole Score is outputted. show()-ing one Part or Measure won't display the slurs.

    return theScore


#------------------------------------------------------------------------------
_DOC_ORDER = [
    accidFromElement,
    articFromElement,
    beamFromElement,
    chordFromElement,
    clefFromElement,
    dotFromElement,
    instrDefFromElement,
    layerFromElement,
    measureFromElement,
    noteFromElement,
    spaceFromElement,
    mSpaceFromElement,
    restFromElement,
    mRestFromElement,
    scoreFromElement,
    sectionFromElement,
    scoreDefFromElement,
    staffFromElement,
    staffDefFromElement,
    staffGrpFromElement,
    tupletFromElement,
    ]

class Test(unittest.TestCase):  # pylint: disable=too-many-public-methods
    '''
    This class runs the tests from all the TestCase sub-classes in the "test_base" module.

    To help keep the MEI module's tests organized, I've grouped them into quite a number of classes.
    To help simplify the test-running process, "multiprocessTest.py" only looks for a TestCase
    sub-class called "Test." This class here allows both of these solutions to coexist.
    '''

    def testAll(self):
        "Run the tests for the MEI module."
        # This is a little confusing, so bear with me for a moment.
        # The unittest.main() function *always* raises a SystemExit, because of how it was designed
        # to be used. We're mis-using it, so we have to catch the SystemExit and inspect its result.
        # If the first argument to the SystemExit is True, that means one of the tests in the
        # module failed---but we don't know any more detail, so we just have to cause testAll() to
        # fail too.
        testResult = unittest.main(module='music21.mei.test_base',
                                   exit=False,  # don't raise SystemExit
                                   buffer=True)  # don't print things from successful tests
        testResult = testResult.result  
        # unittest.main() actually returns a TestProgram; we want a TestResult
        if not testResult.wasSuccessful():
            self.fail(_TEST_FAILS.format(len(testResult.failures), len(testResult.errors)))

if __name__ == "__main__":
    # NOTE: When "multiprocessTest.py" is running the entire music21 test suite, it uses the class
    #       called "Test," which is defined above.
    import music21
    from music21.mei import test_base
    music21.mainTest(
        test_base.TestMeiToM21Class,
        test_base.TestThings,
        test_base.TestMetadata,
        test_base.TestAttrTranslators,
        test_base.TestLyrics,
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
        test_base.TestInstrDef,
        test_base.TestMeasureFromElement,
        test_base.TestSectionScore,
        test_base.TestBarLineFromElement,
        test_base.RegressionIntegrationTests,
    )

#------------------------------------------------------------------------------
# eof
