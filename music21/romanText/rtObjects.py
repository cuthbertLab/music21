# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/rtObjects.py
# Purpose:      music21 objects for processing roman numeral analysis text files
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2012, 2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Translation routines for roman numeral analysis text files, as defined
and demonstrated by Dmitri Tymoczko, Mark Gotham, Michael Scott Cuthbert,
and Christopher Ariza in ISMIR 2019.
'''
import fractions
import io
import re
import unittest

from music21 import common
from music21 import exceptions21
from music21 import environment
from music21 import key
from music21 import prebase

_MOD = 'romanText.rtObjects'
environLocal = environment.Environment(_MOD)

# alternate endings might end with a, b, c for non
# zero or more for everything after the first number
reMeasureTag = re.compile(r'm[0-9]+[a-b]*-*[0-9]*[a-b]*')
reVariant = re.compile(r'var[0-9]+')
reVariantLetter = re.compile(r'var([A-Z]+)')

reOptKeyOpenAtom = re.compile(r'\?\([A-Ga-g]+[b#]*:')
reOptKeyCloseAtom = re.compile(r'\?\)[A-Ga-g]+[b#]*:?')
# ?g:( ?
reKeyAtom = re.compile('[A-Ga-g]+[b#]*;:')
reAnalyticKeyAtom = re.compile('[A-Ga-g]+[b#]*:')
reKeySignatureAtom = re.compile(r'KS-?[0-7]')
# must distinguish b3 from bVII; there may be b1.66.5
reBeatAtom = re.compile(r'b[1-9.]+')
reRepeatStartAtom = re.compile(r'\|\|:')
reRepeatStopAtom = re.compile(r':\|\|')
reNoChordAtom = re.compile('(NC|N.C.|nc)')


# ------------------------------------------------------------------------------

class RomanTextException(exceptions21.Music21Exception):
    pass


class RTTokenException(exceptions21.Music21Exception):
    pass


class RTHandlerException(exceptions21.Music21Exception):
    pass


class RTFileException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------

class RTToken(prebase.ProtoM21Object):
    '''Stores each linear, logical entity of a RomanText.

    A multi-pass parsing procedure is likely necessary, as RomanText permits
    variety of groupings and markings.

    >>> rtt = romanText.rtObjects.RTToken('||:')
    >>> rtt
    <music21.romanText.rtObjects.RTToken '||:'>

    A standard RTToken returns `False` for all of the following.

    >>> rtt.isComposer() or rtt.isTitle() or rtt.isPiece()
    False
    >>> rtt.isAnalyst() or rtt.isProofreader()
    False
    >>> rtt.isTimeSignature() or rtt.isKeySignature() or rtt.isNote()
    False
    >>> rtt.isForm() or rtt.isPedal() or rtt.isMeasure() or rtt.isWork()
    False
    >>> rtt.isMovement() or rtt.isVersion() or rtt.isAtom()
    False
    '''

    def __init__(self, src=''):
        self.src = src  # store source character sequence
        self.lineNumber = 0

    def _reprInternal(self):
        return repr(self.src)

    def isComposer(self):
        return False

    def isTitle(self):
        return False

    def isPiece(self):
        return False

    def isAnalyst(self):
        return False

    def isProofreader(self):
        return False

    def isTimeSignature(self):
        return False

    def isKeySignature(self):
        return False

    def isNote(self):
        return False

    def isForm(self):
        '''Occasionally found in header.
        '''
        return False

    def isMeasure(self):
        return False

    def isPedal(self):
        return False

    def isWork(self):
        return False

    def isMovement(self):
        return False

    def isVersion(self):
        return False

    def isAtom(self):
        '''Atoms are any untagged data; generally only found inside of a
        measure definition.
        '''
        return False


class RTTagged(RTToken):
    '''In romanText, some data elements are tags, that is a tag name, a colon,
    optional whitespace, and data. In non-RTTagged elements, there is just
    data.

    All tagged tokens are subclasses of this class. Examples are:

        Title: Die Jahrzeiten
        Composer: Fanny Mendelssohn

    >>> rtTag = romanText.rtObjects.RTTagged('Title: Die Jahrzeiten')
    >>> rtTag.tag
    'Title'
    >>> rtTag.data
    'Die Jahrzeiten'
    >>> rtTag.isTitle()
    True
    >>> rtTag.isComposer()
    False
    '''

    def __init__(self, src=''):
        super().__init__(src)
        # try to split off tag from data
        self.tag = ''
        self.data = ''
        if ':' in src:
            iFirst = src.find(':')  # first index found at
            self.tag = src[:iFirst].strip()
            # add one to skip colon
            self.data = src[iFirst + 1:].strip()
        else:  # we do not have a clear tag; perhaps store all as data
            self.data = src

    def isComposer(self):
        '''True is the tag represents a composer.

        >>> rth = romanText.rtObjects.RTTagged('Composer: Claudio Monteverdi')
        >>> rth.isComposer()
        True
        >>> rth.isTitle()
        False
        >>> rth.isWork()
        False
        >>> rth.data
        'Claudio Monteverdi'
        '''
        if self.tag.lower() == 'composer':
            return True
        return False

    def isTitle(self):
        '''True if tag represents a title, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Title: This is a title.')
        >>> tag.isTitle()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isTitle()
        False
        '''
        if self.tag.lower() == 'title':
            return True
        return False

    def isPiece(self):
        '''
        True if tag represents a piece, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Piece: This is a piece.')
        >>> tag.isPiece()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isPiece()
        False
        '''
        if self.tag.lower() == 'piece':
            return True
        return False

    def isAnalyst(self):
        '''True if tag represents a analyst, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Analyst: This is an analyst.')
        >>> tag.isAnalyst()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isAnalyst()
        False
        '''
        if self.tag.lower() == 'analyst':
            return True
        return False

    def isProofreader(self):
        '''True if tag represents a proofreader, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Proofreader: This is a proofreader.')
        >>> tag.isProofreader()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isProofreader()
        False
        '''
        if self.tag.lower() in ('proofreader', 'proof reader'):
            return True
        return False

    def isTimeSignature(self):
        '''True if tag represents a time signature, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('TimeSignature: This is a time signature.')
        >>> tag.isTimeSignature()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isTimeSignature()
        False

        TimeSignature header data can be found intermingled with measures.
        '''
        if self.tag.lower() in ('timesignature', 'time signature'):
            return True
        return False

    def isKeySignature(self):
        '''
        True if tag represents a key signature, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('KeySignature: This is a key signature.')
        >>> tag.isKeySignature()
        True
        >>> tag.data
        'This is a key signature.'

        KeySignatures are a type of tagged data found outside of measures,
        such as "Key Signature: -1" meaning one flat.

        Key signatures are generally numbers representing the number of sharps (or
        negative for flats).  Non-standard key signatures are not supported.

        >>> tag = romanText.rtObjects.RTTagged('KeySignature: -3')
        >>> tag.data
        '-3'

        music21 supports one legacy key signature type: `KeySignature: Bb` which
        represents a one-flat signature.  Important to note: no other key signatures
        of this type are supported.  (For instance, `KeySignature: Ab` has no effect)

        >>> tag = romanText.rtObjects.RTTagged('KeySignature: Bb')
        >>> tag.data
        'Bb'

        Testing that `.isKeySignature` returns `False` for non-key signatures:

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isKeySignature()
        False


        N.B.: this is not the same as a key definition found inside of a
        Measure. These are represented by RTKey rtObjects, defined below, and are
        not RTTagged rtObjects, but RTAtom subclasses.
        '''
        if self.tag.lower() in ('keysignature', 'key signature'):
            return True
        else:
            return False

    def isNote(self):
        '''True if tag represents a note, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Note: This is a note.')
        >>> tag.isNote()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isNote()
        False
        '''
        if self.tag.lower() == 'note':
            return True
        return False

    def isForm(self):
        '''True if tag represents a form, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Form: This is a form.')
        >>> tag.isForm()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isForm()
        False
        '''
        if self.tag.lower() == 'form':
            return True
        return False

    def isPedal(self):
        '''True if tag represents a pedal, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Pedal: This is a pedal.')
        >>> tag.isPedal()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isPedal()
        False
        '''
        if self.tag.lower() in ['pedal']:
            return True
        return False

    def isVersion(self):
        '''True if tag defines the version of RomanText standard used,
        otherwise False.

        Pieces without the tag are defined to conform to RomanText 1.0,
        the version described in the ISMIR publication.

        >>> rth = romanText.rtObjects.RTTagged('RTVersion: 1.0')
        >>> rth.isTitle()
        False
        >>> rth.isVersion()
        True
        >>> rth.tag
        'RTVersion'
        >>> rth.data
        '1.0'
        '''
        if self.tag.lower() == 'rtversion':
            return True
        else:
            return False

    def isWork(self):
        '''True if tag represents a work, otherwise False.

        The "work" is not defined as a header tag, but is used to represent
        all tags, often placed after Composer, for the work or pieces designation.

        >>> rth = romanText.rtObjects.RTTagged('Work: BWV232')
        >>> rth.isWork()
        True
        >>> rth.tag
        'Work'
        >>> rth.data
        'BWV232'

        For historical reasons, the tag 'Madrigal' also designates a work.

        >>> rth = romanText.rtObjects.RTTagged('Madrigal: 4.12')
        >>> rth.isTitle()
        False
        >>> rth.isWork()
        True
        >>> rth.tag
        'Madrigal'
        >>> rth.data
        '4.12'
        '''
        if self.tag.lower() in ('work', 'madrigal'):
            return True
        else:
            return False

    def isMovement(self):
        '''True if tag represents a movement, otherwise False.

        >>> tag = romanText.rtObjects.RTTagged('Movement: This is a movement.')
        >>> tag.isMovement()
        True

        >>> tag = romanText.rtObjects.RTTagged('Nothing: Nothing at all.')
        >>> tag.isMovement()
        False
        '''
        if self.tag.lower() == 'movement':
            return True
        return False

    def isSixthMinor(self):
        '''
        True if tag represents a configuration setting for setting vi/vio/VI in minor

        >>> tag = romanText.rtObjects.RTTagged('Sixth Minor: Flat')
        >>> tag.isSixthMinor()
        True
        >>> tag.data
        'Flat'
        '''
        return self.tag.lower() in ('sixthminor', 'sixth minor')  # e.g. 'Sixth Minor: FLAT'

    def isSeventhMinor(self):
        '''
        True if tag represents a configuration setting for setting vii/viio/VII in minor

        >>> tag = romanText.rtObjects.RTTagged('Seventh Minor: Courtesy')
        >>> tag.isSeventhMinor()
        True
        >>> tag.data
        'Courtesy'
        '''
        return self.tag.lower() in ('seventhminor', 'seventh minor')


class RTMeasure(RTToken):
    '''In RomanText, measures are given one per line and always start with 'm'.

    For instance:

        m4 i b3 v b4 VI
        m5 b2 g: IV b4 V
        m6 i
        m7 D: V

    Measure ranges can be used and copied, such as:

        m8-m9=m4-m5

    RTMeasure objects can also define variant readings for a measure:

        m1     ii
        m1var1 ii b2 ii6 b3 IV

    Variants are not part of the tag, but are read into an attribute.

    Endings are indicated by a single letter after the measure number, such as
    "a" for first ending.

    >>> rtm = romanText.rtObjects.RTMeasure('m15a V6 b1.5 V6/5 b2 I b3 viio6')
    >>> rtm.data
    'V6 b1.5 V6/5 b2 I b3 viio6'
    >>> rtm.number
    [15]
    >>> rtm.repeatLetter
    ['a']
    >>> rtm.isMeasure()
    True


    '''

    def __init__(self, src=''):
        super().__init__(src)
        # try to split off tag from data
        self.tag = ''  # the measure number or range
        self.data = ''  # only chord, phrase, and similar definitions
        self.number = []  # one or more measure numbers
        self.repeatLetter = []  # one or more repeat letters
        self.variantNumber = None  # a one-measure or short variant
        # a longer-variant that
        # defines a different way of reading a large section
        self.variantLetter = None
        # store boolean if this measure defines copying another range
        self.isCopyDefinition = False
        # store processed tokens associated with this measure
        self.atoms = []

        if src:
            self._parseAttributes(src)

    def _getMeasureNumberData(self, src):
        '''Return the number or numbers as a list, as well as any repeat
        indications.

        >>> rtm = romanText.rtObjects.RTMeasure()
        >>> rtm._getMeasureNumberData('m77')
        ([77], [''])
        >>> rtm._getMeasureNumberData('m123b-432b')
        ([123, 432], ['b', 'b'])
        '''
        # note: this is separate procedure b/c it is used to get copy
        # boundaries
        if '-' in src:  # its a range
            mnStart, mnEnd = src.split('-')
            proc = [mnStart, mnEnd]
        else:
            proc = [src]  # treat as one
        number = []
        repeatLetter = []
        for mn in proc:
            # append in order, start, end
            numStr, alphaStr = common.getNumFromStr(mn)
            number.append(int(numStr))
            # remove all 'm' in alpha
            alphaStr = alphaStr.replace('m', '')
            repeatLetter.append(alphaStr)
        return number, repeatLetter

    def _parseAttributes(self, src):
        # assume that we have already checked that this is a measure
        g = reMeasureTag.match(src)
        if g is None:  # not measure tag found
            raise RTHandlerException('found no measure tag: %s' % src)
        iEnd = g.end()  # get end index
        rawTag = src[:iEnd].strip()
        self.tag = rawTag
        rawData = src[iEnd:].strip()  # may have variant

        # get the number list from the tag
        self.number, self.repeatLetter = self._getMeasureNumberData(rawTag)

        # strip a variant indication off of rawData if found
        g = reVariant.match(rawData)
        if g is not None:  # there is a variant tag
            varStr = g.group(0)
            self.variantNumber = int(common.getNumFromStr(varStr)[0])
            self.data = rawData[g.end():].strip()
        else:
            self.data = rawData
        g = reVariantLetter.match(rawData)
        if g is not None:  # there is a variant letter tag
            varStr = g.group(1)
            self.variantLetter = varStr
            self.data = rawData[g.end():].strip()

        if self.data.startswith('='):
            self.isCopyDefinition = True

    def _reprInternal(self):
        if len(self.number) == 1:
            numberStr = '%s' % self.number[0]
        else:
            numberStr = '%s-%s' % (self.number[0], self.number[1])
        return numberStr

    def isMeasure(self):
        return True

    def getCopyTarget(self):
        '''If this measure defines a copy operation, return two lists defining
        the measures to copy; the second list has the repeat data.

        >>> rtm = romanText.rtObjects.RTMeasure('m35-36 = m29-30')
        >>> rtm.number
        [35, 36]
        >>> rtm.getCopyTarget()
        ([29, 30], ['', ''])

        >>> rtm = romanText.rtObjects.RTMeasure('m4 = m1')
        >>> rtm.number
        [4]
        >>> rtm.getCopyTarget()
        ([1], [''])
        '''
        # remove equal sign
        rawData = self.data.replace('=', '').strip()
        return self._getMeasureNumberData(rawData)


class RTAtom(RTToken):
    '''In RomanText, definitions of chords, phrases boundaries, open/close
    parenthesis, beat indicators, etc. appear within measures (RTMeasure
    objects). These individual elements will be called Atoms, as they are data
    that is not tagged.

    Each atom store a reference to its container (normally an RTMeasure).

    >>> chordIV = romanText.rtObjects.RTAtom('IV')
    >>> beat4 = romanText.rtObjects.RTAtom('b4')
    >>> beat4
    <music21.romanText.rtObjects.RTAtom 'b4'>
    >>> beat4.isAtom()
    True

    However, see RTChord, RTBeat, etc. which are subclasses of RTAtom
    specifically for storing chords, beats, etc.
    '''

    def __init__(self, src='', container=None):
        # this stores the source
        super().__init__(src)
        self.container = container

    def isAtom(self):
        return True

    # for lower level distinctions, use isinstance(), as each type has its own subclass.


class RTChord(RTAtom):
    r'''An RTAtom subclass that defines a chord.  Also contains a reference to
    the container.

    >>> chordIV = romanText.rtObjects.RTChord('IV')
    >>> chordIV
    <music21.romanText.rtObjects.RTChord 'IV'>
    '''

    def __init__(self, src='', container=None):
        super().__init__(src, container)

        # store offset within measure
        self.offset = None
        # store a quarterLength duration
        self.quarterLength = None


class RTNoChord(RTAtom):
    r'''An RTAtom subclass that defines absence of a chord.  Also contains a
    reference to the container.

    >>> chordNC = romanText.rtObjects.RTNoChord('NC')
    >>> chordNC
    <music21.romanText.rtObjects.RTNoChord 'NC'>

    >>> rth = romanText.rtObjects.RTHandler()
    >>> rth.tokenizeAtoms('nc NC N.C.')
    [<music21.romanText.rtObjects.RTNoChord 'nc'>,
     <music21.romanText.rtObjects.RTNoChord 'NC'>,
     <music21.romanText.rtObjects.RTNoChord 'N.C.'>]
    '''

    def __init__(self, src='', container=None):
        super().__init__(src, container)

        # store offset within measure
        self.offset = None
        # store a quarterLength duration
        self.quarterLength = None


class RTBeat(RTAtom):
    r'''An RTAtom subclass that defines a beat definition.  Also contains a
    reference to the container.

    >>> beatFour = romanText.rtObjects.RTBeat('b4')
    >>> beatFour
    <music21.romanText.rtObjects.RTBeat 'b4'>
    '''

    def getBeatFloatOrFrac(self):
        '''
        Gets the beat number as a float or fraction. Time signature independent

        >>> RTB = romanText.rtObjects.RTBeat

        Simple ones:

        >>> RTB('b1').getBeatFloatOrFrac()
        1.0
        >>> RTB('b2').getBeatFloatOrFrac()
        2.0

        etc.

        with easy float:

        >>> RTB('b1.5').getBeatFloatOrFrac()
        1.5
        >>> RTB('b1.25').getBeatFloatOrFrac()
        1.25

        with harder:

        >>> RTB('b1.33').getBeatFloatOrFrac()
        Fraction(4, 3)

        >>> RTB('b2.66').getBeatFloatOrFrac()
        Fraction(8, 3)

        >>> RTB('b1.2').getBeatFloatOrFrac()
        Fraction(6, 5)


        A third digit of 0.5 adds 1/2 of 1/DENOM of before.  Here DENOM is 3 (in 5/3) so
        we add 1/6 to 5/3 to get 11/6:


        >>> RTB('b1.66').getBeatFloatOrFrac()
        Fraction(5, 3)

        >>> RTB('b1.66.5').getBeatFloatOrFrac()
        Fraction(11, 6)


        Similarly 0.25 adds 1/4 of 1/DENOM... to get 21/12 or 7/4 or 1.75

        >>> RTB('b1.66.25').getBeatFloatOrFrac()
        1.75

        And 0.75 adds 3/4 of 1/DENOM to get 23/12

        >>> RTB('b1.66.75').getBeatFloatOrFrac()
        Fraction(23, 12)


        A weird way of writing 'b1.5'

        >>> RTB('b1.33.5').getBeatFloatOrFrac()
        1.5
        '''
        beatStr = self.src.replace('b', '')
        # there may be more than one decimal in the number, such as
        # 1.66.5, to show halfway through 2/3rd of a beat
        parts = beatStr.split('.')
        mainBeat = int(parts[0])
        if len(parts) > 1:  # 1.66
            fracPart = common.addFloatPrecision('.' + parts[1])
        else:
            fracPart = 0.0

        if len(parts) > 2:  # 1.66.5
            fracPartDivisor = float('.' + parts[2])  # 0.5
            if isinstance(fracPart, float):
                fracPart = fractions.Fraction.from_float(fracPart)
            denom = fracPart.denominator
            fracBeatFrac = common.opFrac(1. / (denom / fracPartDivisor))
        else:
            fracBeatFrac = 0.0

        if len(parts) > 3:
            environLocal.printDebug(['got unexpected beat: %s' % self.src])
            raise RTTokenException('cannot handle specification: %s' % self.src)

        beat = common.opFrac(mainBeat + fracPart + fracBeatFrac)
        return beat

    def getOffset(self, timeSignature):
        '''Given a time signature, return the offset position specified by this
        beat.

        >>> rtb = romanText.rtObjects.RTBeat('b1.5')
        >>> rtb.getOffset(meter.TimeSignature('3/4'))
        0.5
        >>> rtb.getOffset(meter.TimeSignature('6/8'))
        0.75
        >>> rtb.getOffset(meter.TimeSignature('2/2'))
        1.0

        >>> rtb = romanText.rtObjects.RTBeat('b2')
        >>> rtb.getOffset(meter.TimeSignature('3/4'))
        1.0
        >>> rtb.getOffset(meter.TimeSignature('6/8'))
        1.5

        >>> rtb = romanText.rtObjects.RTBeat('b1.66')
        >>> rtb.getOffset(meter.TimeSignature('6/8'))
        1.0
        >>> rtc = romanText.rtObjects.RTBeat('b1.66.5')
        >>> rtc.getOffset(meter.TimeSignature('6/8'))
        1.25
        '''
        from music21 import meter
        beat = self.getBeatFloatOrFrac()

        # environLocal.printDebug(['using beat value:', beat])
        # TODO: check for exceptions/errors if this beat is bad
        try:
            post = timeSignature.getOffsetFromBeat(beat)
        except meter.TimeSignatureException:
            environLocal.printDebug(['bad beat specification: %s in a meter of %s' % (
                                    self.src, timeSignature)])
            post = 0.0

        return post


class RTKeyTypeAtom(RTAtom):
    '''RTKeyTypeAtoms contain utility functions for all Key-type tokens, i.e.
    RTKey, RTAnalyticKey, but not KeySignature.

    >>> gMinor = romanText.rtObjects.RTKeyTypeAtom('g;:')
    >>> gMinor
    <music21.romanText.rtObjects.RTKeyTypeAtom 'g;:'>
    '''

    def getKey(self):
        '''
        This returns a Key, not a KeySignature object
        '''
        myKey = self.src.rstrip(self.footerStrip)
        myKey = key.convertKeyStringToMusic21KeyString(myKey)
        return key.Key(myKey)

    def getKeySignature(self):
        '''Get a KeySignature object.
        '''
        myKey = self.getKey()
        return key.KeySignature(myKey.sharps)


class RTKey(RTKeyTypeAtom):
    '''An RTKey(RTAtom) defines both a change in KeySignature and a change
    in the analyzed Key.

    They are defined by ";:" after the Key.

    >>> gMinor = romanText.rtObjects.RTKey('g;:')
    >>> gMinor
    <music21.romanText.rtObjects.RTKey 'g;:'>
    >>> gMinor.getKey()
    <music21.key.Key of g minor>

    >>> bMinor = romanText.rtObjects.RTKey('bb;:')
    >>> bMinor
    <music21.romanText.rtObjects.RTKey 'bb;:'>
    >>> bMinor.getKey()
    <music21.key.Key of b- minor>
    >>> bMinor.getKeySignature()
    <music21.key.KeySignature of 5 flats>

    >>> eFlatMajor = romanText.rtObjects.RTKey('Eb;:')
    >>> eFlatMajor
    <music21.romanText.rtObjects.RTKey 'Eb;:'>
    >>> eFlatMajor.getKey()
    <music21.key.Key of E- major>
    '''
    footerStrip = ';:'


class RTAnalyticKey(RTKeyTypeAtom):
    '''An RTAnalyticKey(RTKeyTypeAtom) only defines a change in the key
    being analyzed.  It does not in itself create a :class:~'music21.key.Key'
    object.

    >>> gMinor = romanText.rtObjects.RTAnalyticKey('g:')
    >>> gMinor
    <music21.romanText.rtObjects.RTAnalyticKey 'g:'>
    >>> gMinor.getKey()
    <music21.key.Key of g minor>

    >>> bMinor = romanText.rtObjects.RTAnalyticKey('bb:')
    >>> bMinor
    <music21.romanText.rtObjects.RTAnalyticKey 'bb:'>
    >>> bMinor.getKey()
    <music21.key.Key of b- minor>

    '''
    footerStrip = ':'


class RTKeySignature(RTAtom):
    '''
    An RTKeySignature(RTAtom) only defines a change in the KeySignature.
    It does not in itself create a :class:~'music21.key.Key' object, nor
    does it change the analysis taking place.

    The number after KS defines the number of sharps (negative for flats).

    >>> gMinor = romanText.rtObjects.RTKeySignature('KS-2')
    >>> gMinor
    <music21.romanText.rtObjects.RTKeySignature 'KS-2'>
    >>> gMinor.getKeySignature()
    <music21.key.KeySignature of 2 flats>

    >>> aMajor = romanText.rtObjects.RTKeySignature('KS3')
    >>> aMajor.getKeySignature()
    <music21.key.KeySignature of 3 sharps>
    '''

    def getKeySignature(self):
        numSharps = int(self.src[2:])
        return key.KeySignature(numSharps)


class RTOpenParens(RTAtom):
    '''
    A simple open parenthesis Atom with a sensible default

    >>> romanText.rtObjects.RTOpenParens('(')
    <music21.romanText.rtObjects.RTOpenParens '('>
    '''

    def __init__(self, src='(', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


class RTCloseParens(RTAtom):
    '''
    A simple close parenthesis Atom with a sensible default

    >>> romanText.rtObjects.RTCloseParens(')')
    <music21.romanText.rtObjects.RTCloseParens ')'>
    '''

    def __init__(self, src=')', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


class RTOptionalKeyOpen(RTAtom):
    '''
    Marks the beginning of an optional Key area which does not
    affect the roman numeral analysis.  (For instance, it is
    possible to analyze in Bb major, while remaining in g minor)

    >>> possibleKey = romanText.rtObjects.RTOptionalKeyOpen('?(Bb:')
    >>> possibleKey
    <music21.romanText.rtObjects.RTOptionalKeyOpen '?(Bb:'>
    >>> possibleKey.getKey()
    <music21.key.Key of B- major>
    '''

    def getKey(self):
        # alter flat symbol
        if self.src == '?(b:':
            return key.Key('b')
        else:
            keyStr = self.src.replace('b', '-')
            keyStr = keyStr.replace(':', '')
            keyStr = keyStr.replace('?', '')
            keyStr = keyStr.replace('(', '')
            # environLocal.printDebug(['create a key from:', keyStr])
            return key.Key(keyStr)


class RTOptionalKeyClose(RTAtom):
    '''
    Marks the end of an optional Key area which does not affect the roman
    numeral analysis.

    For example, it is possible to analyze in Bb major, while remaining in g
    minor.

    >>> possibleKey = romanText.rtObjects.RTOptionalKeyClose('?)Bb:')
    >>> possibleKey
    <music21.romanText.rtObjects.RTOptionalKeyClose '?)Bb:'>
    >>> possibleKey.getKey()
    <music21.key.Key of B- major>
    '''

    def getKey(self):
        # alter flat symbol
        if self.src == '?)b:' or self.src == '?)b':
            return key.Key('b')
        else:
            keyStr = self.src.replace('b', '-')
            keyStr = keyStr.replace(':', '')
            keyStr = keyStr.replace('?', '')
            keyStr = keyStr.replace(')', '')
            # environLocal.printDebug(['create a key from:', keyStr])
            return key.Key(keyStr)


class RTPhraseMarker(RTAtom):
    '''
    A Phrase Marker:

    >>> rtPhraseMarker = romanText.rtObjects.RTPhraseMarker('')
    >>> rtPhraseMarker
    <music21.romanText.rtObjects.RTPhraseMarker ''>
    '''


class RTPhraseBoundary(RTPhraseMarker):
    '''
    >>> phrase = romanText.rtObjects.RTPhraseBoundary('||')
    >>> phrase
    <music21.romanText.rtObjects.RTPhraseBoundary '||'>
    '''

    def __init__(self, src='||', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


class RTEllisonStart(RTPhraseMarker):
    '''
    >>> phrase = romanText.rtObjects.RTEllisonStart('|*')
    >>> phrase
    <music21.romanText.rtObjects.RTEllisonStart '|*'>
    '''

    def __init__(self, src='|*', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


class RTEllisonStop(RTPhraseMarker):
    '''
    >>> phrase = romanText.rtObjects.RTEllisonStop('*|')
    >>> phrase
    <music21.romanText.rtObjects.RTEllisonStop '*|'>
    '''

    def __init__(self, src='*|', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


class RTRepeat(RTAtom):
    '''
    >>> repeat = romanText.rtObjects.RTRepeat('||:')
    >>> repeat
    <music21.romanText.rtObjects.RTRepeat '||:'>
    '''


class RTRepeatStart(RTRepeat):
    '''
    >>> repeat = romanText.rtObjects.RTRepeatStart()
    >>> repeat
    <music21.romanText.rtObjects.RTRepeatStart ...'||:'>
    '''

    def __init__(self, src='||:', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


class RTRepeatStop(RTRepeat):
    '''
    >>> repeat = romanText.rtObjects.RTRepeatStop()
    >>> repeat
    <music21.romanText.rtObjects.RTRepeatStop ...':||'>
    '''

    def __init__(self, src=':||', container=None):  # pylint: disable=useless-super-delegation
        super().__init__(src, container)


# ------------------------------------------------------------------------------

class RTHandler:

    # divide elements of a character stream into rtObjects and handle
    # store in a list, and pass global information to components
    def __init__(self):
        # tokens are ABC rtObjects in a linear stream
        # tokens are strongly divided between header and body, so can
        # divide here
        self._tokens = []
        self.currentLineNumber = 0

    def splitAtHeader(self, lines):
        '''Divide string into header and non-header; this is done before
        tokenization.

        >>> rth = romanText.rtObjects.RTHandler()
        >>> rth.splitAtHeader(['Title: s', 'Time Signature:', '', 'm1 g: i'])
        (['Title: s', 'Time Signature:', ''], ['m1 g: i'])

        '''
        # iterate over lines and find the first measure definition
        iStartBody = None
        for i, l in enumerate(lines):
            if reMeasureTag.match(l.strip()) is not None:
                # found a measure definition
                iStartBody = i
                break
        if iStartBody is None:
            raise RomanTextException('Cannot find the first measure definition in this file. '
                                     + 'Dumping contexts: %s', lines)
        return lines[:iStartBody], lines[iStartBody:]

    def tokenizeHeader(self, lines):
        '''In the header, we only have :class:`~music21.romanText.base.RTTagged`
        tokens. We can this process these all as the same class.
        '''
        post = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line == '':
                continue
            # wrap each line in a header token
            rtt = RTTagged(line)
            rtt.lineNumber = i + 1
            post.append(rtt)
        self.currentLineNumber = len(lines) + 1
        return post

    def tokenizeBody(self, lines):
        '''In the body, we may have measure, time signature, or note
        declarations, as well as possible other tagged definitions.
        '''
        post = []
        startLineNumber = self.currentLineNumber
        for i, line in enumerate(lines):
            currentLineNumber = startLineNumber + i
            try:
                line = line.strip()
                if line == '':
                    continue
                # first, see if it is a measure definition, if not, than assume it is tagged data
                if reMeasureTag.match(line) is not None:
                    rtm = RTMeasure(line)
                    rtm.lineNumber = currentLineNumber
                    # note: could places these in-line, after post
                    rtm.atoms = self.tokenizeAtoms(rtm.data, container=rtm)
                    for a in rtm.atoms:
                        a.lineNumber = currentLineNumber
                    post.append(rtm)
                else:
                    # store items in a measure tag outside of the measure
                    rtt = RTTagged(line)
                    rtt.lineNumber = currentLineNumber
                    post.append(rtt)
            except Exception:
                import traceback
                tracebackMessage = traceback.format_exc()
                raise RTHandlerException('At line %d (%s) an exception was raised: \n%s' % (
                    currentLineNumber, line, tracebackMessage))
        return post

    def tokenizeAtoms(self, line, container=None):
        '''Given a line of data stored in measure consisting only of Atoms,
        tokenize and return a list.

        >>> rth = romanText.rtObjects.RTHandler()
        >>> rth.tokenizeAtoms('IV b3 ii7 b4 ii')
        [<music21.romanText.rtObjects.RTChord 'IV'>,
         <music21.romanText.rtObjects.RTBeat 'b3'>,
         <music21.romanText.rtObjects.RTChord 'ii7'>,
         <music21.romanText.rtObjects.RTBeat 'b4'>,
         <music21.romanText.rtObjects.RTChord 'ii'>]

        >>> rth.tokenizeAtoms('V7 b2 V13 b3 V7 iio6/5[no5]')
        [<music21.romanText.rtObjects.RTChord 'V7'>,
         <music21.romanText.rtObjects.RTBeat 'b2'>,
         <music21.romanText.rtObjects.RTChord 'V13'>,
         <music21.romanText.rtObjects.RTBeat 'b3'>,
         <music21.romanText.rtObjects.RTChord 'V7'>,
         <music21.romanText.rtObjects.RTChord 'iio6/5[no5]'>]

        >>> tokenList = rth.tokenizeAtoms('I b2 I b2.25 V/ii b2.5 bVII b2.75 V g: IV')
        >>> tokenList
        [<music21.romanText.rtObjects.RTChord 'I'>,
         <music21.romanText.rtObjects.RTBeat 'b2'>,
         <music21.romanText.rtObjects.RTChord 'I'>,
         <music21.romanText.rtObjects.RTBeat 'b2.25'>,
         <music21.romanText.rtObjects.RTChord 'V/ii'>,
         <music21.romanText.rtObjects.RTBeat 'b2.5'>,
         <music21.romanText.rtObjects.RTChord 'bVII'>,
         <music21.romanText.rtObjects.RTBeat 'b2.75'>,
         <music21.romanText.rtObjects.RTChord 'V'>,
         <music21.romanText.rtObjects.RTAnalyticKey 'g:'>,
         <music21.romanText.rtObjects.RTChord 'IV'>]

        >>> tokenList[-2].getKey()
        <music21.key.Key of g minor>

        >>> rth.tokenizeAtoms('= m3')
        []

        >>> tokenList = rth.tokenizeAtoms('g;: ||: V b2 ?(Bb: VII7 b3 III b4 ?)Bb: i :||')
        >>> tokenList
        [<music21.romanText.rtObjects.RTKey 'g;:'>,
         <music21.romanText.rtObjects.RTRepeatStart '||:'>,
         <music21.romanText.rtObjects.RTChord 'V'>,
         <music21.romanText.rtObjects.RTBeat 'b2'>,
         <music21.romanText.rtObjects.RTOptionalKeyOpen '?(Bb:'>,
         <music21.romanText.rtObjects.RTChord 'VII7'>,
         <music21.romanText.rtObjects.RTBeat 'b3'>,
         <music21.romanText.rtObjects.RTChord 'III'>,
         <music21.romanText.rtObjects.RTBeat 'b4'>,
         <music21.romanText.rtObjects.RTOptionalKeyClose '?)Bb:'>,
         <music21.romanText.rtObjects.RTChord 'i'>,
         <music21.romanText.rtObjects.RTRepeatStop ':||'>]
        '''
        post = []
        # break by spaces
        for word in line.split(' '):
            word = word.strip()
            if word == '':
                continue
            elif word == '=':
                # if an = is found, this is a copy definition, and no atoms here
                break
            elif word == '||':
                post.append(RTPhraseBoundary(word, container))
            elif word == '(':
                post.append(RTOpenParens(word, container))
            elif word == ')':
                post.append(RTCloseParens(word, container))
            elif reBeatAtom.match(word) is not None:
                post.append(RTBeat(word, container))
            # from here, all that is left is keys or chords
            elif reOptKeyOpenAtom.match(word) is not None:
                post.append(RTOptionalKeyOpen(word, container))
            elif reOptKeyCloseAtom.match(word) is not None:
                post.append(RTOptionalKeyClose(word, container))
            elif reKeyAtom.match(word) is not None:
                post.append(RTKey(word, container))
            elif reAnalyticKeyAtom.match(word) is not None:
                post.append(RTAnalyticKey(word, container))
            elif reKeySignatureAtom.match(word) is not None:
                post.append(RTKeySignature(word, container))
            elif reRepeatStartAtom.match(word) is not None:
                post.append(RTRepeatStart(word, container))
            elif reRepeatStopAtom.match(word) is not None:
                post.append(RTRepeatStop(word, container))
            elif reNoChordAtom.match(word) is not None:
                post.append(RTNoChord(word, container))
            else:  # only option is that it is a chord
                post.append(RTChord(word, container))
        return post

    def tokenize(self, src):
        '''
        Walk the RT string, creating RT rtObjects along the way.
        '''
        # break into lines
        lines = src.split('\n')
        linesHeader, linesBody = self.splitAtHeader(lines)
        # environLocal.printDebug([linesHeader])
        self._tokens += self.tokenizeHeader(linesHeader)
        self._tokens += self.tokenizeBody(linesBody)

    def process(self, src):
        '''
        Given an entire specification as a single source string, strSrc, tokenize it.
        This is usually provided in a file.
        '''
        self._tokens = []
        self.tokenize(src)

    def definesMovements(self, countRequired=2):
        '''Return True if more than one movement is defined in a RT file.

        >>> rth = romanText.rtObjects.RTHandler()
        >>> rth.process('Movement: 1 \\n Movement: 2 \\n \\n m1')
        >>> rth.definesMovements()
        True
        >>> rth.process('Movement: 1 \\n m1')
        >>> rth.definesMovements()
        False
        '''
        if not self._tokens:
            raise RTHandlerException('must create tokens first')
        count = 0
        for t in self._tokens:
            if t.isMovement():
                count += 1
                if count >= countRequired:
                    return True
        return False

    def definesMovement(self):
        '''Return True if this handler has 1 or more movement.

        >>> rth = romanText.rtObjects.RTHandler()
        >>> rth.process('Movement: 1 \\n \\n m1')
        >>> rth.definesMovements()
        False
        >>> rth.definesMovement()
        True
        '''
        return self.definesMovements(countRequired=1)

    def splitByMovement(self, duplicateHeader=True):
        '''If we have movements defined, return a list of RTHandler rtObjects,
        representing header information and each movement, in order.

        >>> rth = romanText.rtObjects.RTHandler()
        >>> rth.process('Title: Test \\n Movement: 1 \\n m1 \\n Movement: 2 \\n m1')
        >>> post = rth.splitByMovement(False)
        >>> len(post)
        3

        >>> len(post[0])
        1

        >>> post[0].__class__
        <class 'music21.romanText.rtObjects.RTHandler'>
        >>> len(post[1]), len(post[2])
        (2, 2)

        >>> post = rth.splitByMovement(duplicateHeader=True)
        >>> len(post)
        2

        >>> len(post[0]), len(post[1])
        (3, 3)
        '''
        post = []
        sub = []
        for t in self._tokens:
            if t.isMovement():
                # when finding a movement, we are ending a previous
                # and starting a new; this may just have metadata
                rth = RTHandler()
                rth.tokens = sub
                post.append(rth)
                sub = []
            sub.append(t)

        if sub:
            rth = RTHandler()
            rth.tokens = sub
            post.append(rth)

        if duplicateHeader:
            alt = []
            # if no movement in this first handler, assume it is header info
            if not post[0].definesMovement():
                handlerHead = post[0]
                iStart = 1
            else:
                handlerHead = None
                iStart = 0
            for h in post[iStart:]:
                if handlerHead is not None:
                    h = handlerHead + h  # add metadata
                alt.append(h)
            # reassign
            post = alt

        return post

    # --------------------------------------------------------------------------
    # access tokens

    def _getTokens(self):
        if not self._tokens:
            raise RTHandlerException('must process tokens before calling split')
        return self._tokens

    def _setTokens(self, tokens):
        '''Assign tokens to this Handler.
        '''
        self._tokens = tokens

    tokens = property(_getTokens, _setTokens,
                      doc='''Get or set tokens for this Handler.
        ''')

    def __len__(self):
        return len(self._tokens)

    def __add__(self, other):
        '''Return a new handler adding the tokens in both
        '''
        rth = self.__class__()  # will get the same class type
        rth.tokens = self._tokens + other._tokens
        return rth


# ------------------------------------------------------------------------------

class RTFile(prebase.ProtoM21Object):
    '''
    Roman Text File access.
    '''

    def __init__(self):
        self.file = None
        self.filename = None

    def open(self, filename):
        '''Open a file for reading, trying a variety of encodings and then
        trying them again with an ignore if it is not possible.
        '''
        for encoding in ('utf-8', 'macintosh', 'latin-1', 'utf-16'):
            try:
                self.file = io.open(filename, encoding=encoding)
                if self.file is not None:
                    break
            except UnicodeDecodeError:
                pass
        if self.file is None:
            for encoding in ('utf-8', 'macintosh', 'latin-1', 'utf-16', None):
                try:
                    self.file = io.open(filename, encoding=encoding, errors='ignore')
                    if self.file is not None:
                        break
                except UnicodeDecodeError:
                    pass
            if self.file is None:
                raise RomanTextException(
                    'Cannot parse file %s, possibly a broken codec?' % filename)

        self.filename = filename

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an
        open file object.
        '''
        self.file = fileLike  # already 'open'

    def _reprInternal(self):
        return ''

    def close(self):
        self.file.close()

    def read(self):
        '''Read a file. Note that this calls readstr, which processes all tokens.

        If `number` is given, a work number will be extracted if possible.
        '''
        return self.readstr(self.file.read())

    def readstr(self, strSrc):
        '''Read a string and process all Tokens. Returns a ABCHandler instance.
        '''
        handler = RTHandler()
        # return the handler instance
        handler.process(strSrc)
        return handler


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def testBasicA(self):
        from music21.romanText import testFiles
        for fileStr in testFiles.ALL:
            f = RTFile()
            unused_rth = f.readstr(fileStr)  # get a handler from a string

    def testReA(self):
        # gets the index of the end of the measure indication
        g = reMeasureTag.match('m1 g: V b2 i')
        self.assertEqual(g.end(), 2)
        self.assertEqual(g.group(0), 'm1')

        self.assertEqual(reMeasureTag.match('Time Signature: 2/2'), None)

        g = reMeasureTag.match('m3-4=m1-2')
        self.assertEqual(g.end(), 4)
        self.assertEqual(g.start(), 0)
        self.assertEqual(g.group(0), 'm3-4')

        g = reMeasureTag.match('m123-432=m1120-24234')
        self.assertEqual(g.group(0), 'm123-432')

        g = reMeasureTag.match('m231a IV6 b4 C: V')
        self.assertEqual(g.group(0), 'm231a')

        g = reMeasureTag.match('m123b-432b=m1120a-24234a')
        self.assertEqual(g.group(0), 'm123b-432b')

        g = reMeasureTag.match('m231var1 IV6 b4 C: V')
        self.assertEqual(g.group(0), 'm231')

        # this only works if it starts the string
        g = reVariant.match('var1 IV6 b4 C: V')
        self.assertEqual(g.group(0), 'var1')

        g = reAnalyticKeyAtom.match('Bb:')
        self.assertEqual(g.group(0), 'Bb:')
        g = reAnalyticKeyAtom.match('F#:')
        self.assertEqual(g.group(0), 'F#:')
        g = reAnalyticKeyAtom.match('f#:')
        self.assertEqual(g.group(0), 'f#:')
        g = reAnalyticKeyAtom.match('b:')
        self.assertEqual(g.group(0), 'b:')
        g = reAnalyticKeyAtom.match('bb:')
        self.assertEqual(g.group(0), 'bb:')
        g = reAnalyticKeyAtom.match('g:')
        self.assertEqual(g.group(0), 'g:')

        # beats do not have a colon
        self.assertEqual(reKeyAtom.match('b2'), None)
        self.assertEqual(reKeyAtom.match('b2.5'), None)

        g = reBeatAtom.match('b2.5')
        self.assertEqual(g.group(0), 'b2.5')

        g = reBeatAtom.match('bVII')
        self.assertEqual(g, None)

        g = reBeatAtom.match('b1.66.5')
        self.assertEqual(g.group(0), 'b1.66.5')

    def testMeasureAttributeProcessing(self):
        rtm = RTMeasure('m17var1 vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.data, 'vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.number, [17])
        self.assertEqual(rtm.tag, 'm17')
        self.assertEqual(rtm.variantNumber, 1)

        rtm = RTMeasure('m17varC vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.data, 'vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.variantLetter, 'C')

        rtm = RTMeasure('m20 vi b2 ii6/5 b3 V b3.5 V7')
        self.assertEqual(rtm.data, 'vi b2 ii6/5 b3 V b3.5 V7')
        self.assertEqual(rtm.number, [20])
        self.assertEqual(rtm.tag, 'm20')
        self.assertEqual(rtm.variantNumber, None)
        self.assertFalse(rtm.isCopyDefinition)

        rtm = RTMeasure('m0 b3 G: I')
        self.assertEqual(rtm.data, 'b3 G: I')
        self.assertEqual(rtm.number, [0])
        self.assertEqual(rtm.tag, 'm0')
        self.assertEqual(rtm.variantNumber, None)
        self.assertFalse(rtm.isCopyDefinition)

        rtm = RTMeasure('m59 = m57')
        self.assertEqual(rtm.data, '= m57')
        self.assertEqual(rtm.number, [59])
        self.assertEqual(rtm.tag, 'm59')
        self.assertEqual(rtm.variantNumber, None)
        self.assertTrue(rtm.isCopyDefinition)

        rtm = RTMeasure('m3-4 = m1-2')
        self.assertEqual(rtm.data, '= m1-2')
        self.assertEqual(rtm.number, [3, 4])
        self.assertEqual(rtm.tag, 'm3-4')
        self.assertEqual(rtm.variantNumber, None)
        self.assertTrue(rtm.isCopyDefinition)

    def testTokenDefinition(self):
        # test that we are always getting the right number of tokens
        from music21.romanText import testFiles

        rth = RTHandler()
        rth.process(testFiles.mozartK279)

        count = 0
        for t in rth._tokens:
            if t.isMovement():
                count += 1
        self.assertEqual(count, 3)

        rth.process(testFiles.riemenschneider001)
        count = 0
        for t in rth._tokens:
            if t.isMeasure():
                # print(t.src)
                count += 1
        # 21, 2 variants, and one pickup
        self.assertEqual(count, 21 + 2 + 1)

        count = 0
        for t in rth._tokens:
            if t.isMeasure():
                for a in t.atoms:
                    if isinstance(a, RTAnalyticKey):
                        count += 1
        self.assertEqual(count, 1)


# ------------------------------------------------------------------------------
# define presented order in documentation
# _DOC_ORDER = []

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

