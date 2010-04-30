#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         duration.py
# Purpose:      music21 classes for representing durations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Classes and functions for creating and processing durations. Durations, while a fundamental component of Note objects, are also used to describe the duration of other Music21Objects, such as Stream and TimeSignature objects.
'''

import unittest, doctest
import copy

# NOT import music21
# duration.py is imported by base.py, and is thus a lower level object
# than most other objects. 

from music21 import defaults
from music21 import common
from music21 import musicxml as musicxmlMod


from music21 import environment
_MOD = "duration.py"  
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
# duration constants and reference

# MusicXML uses long instead of longa
typeToDuration = {'duplex-maxima': 64.0, 'maxima': 32.0, 'longa': 16.0,
                  'breve': 8.0, 'whole': 4.0,
                  'half': 2.0, 'quarter': 1.0, 'eighth': 0.5,
                  '16th': 0.25, '32nd': 0.125,
                  '64th': 0.0625, '128th': 0.03125, '256th': 0.015625,
                  '512th': 0.015625 / 2.0, '1024th': 0.015625 / 4.0,
                  'zero': 0.0} 

typeFromNumDict = {1: 'whole',
                   2: 'half',
                   4: 'quarter',
                   8: 'eighth',
                   16: '16th',
                   32: '32nd',
                   64: '64th',
                   128: '128th',
                   256: '256th',
                   512: '512th',
                   1024: '1024th',
                   0: 'zero',
                   0.5: 'breve',
                   0.25: 'longa',
                   0.125: 'maxima',
                   0.0625: 'duplex-maxima'}

ordinalTypeFromNum = ["duplex-maxima", "maxima", "longa", "breve", "whole",
    "half", "quarter", "eighth", "16th", "32nd", "64th", "128th", "256th",
    "512th", "1024th"]

defaultTupletNumerators = [3, 5, 7, 11, 13]

def roundDuration(qLen):
    return round(qLen, 5)

def unitSpec(durationObjectOrObjects):
    '''
    A simple data representation of most Duration objects. Processes a single Duration or a List of Durations, returning a single or list of unitSpecs.
    
    A unitSpec is a tuple of qLen, durType, dots, tupleNumerator, tupletDenominator, and tupletType (assuming top and bottom tuplets are the same).
    
    This function does not deal with nested tuplets, etc.

    >>> aDur = Duration()
    >>> aDur.quarterLength = 3
    >>> unitSpec(aDur)
    (3.0, 'half', 1, None, None, None)

    >>> bDur = Duration()
    >>> bDur.quarterLength = 1.125
    >>> unitSpec(bDur)
    (1.125, 'complex', None, None, None, None)

    >>> cDur = Duration()
    >>> cDur.quarterLength = 0.3333333
    >>> unitSpec(cDur)
    (0.33333..., 'eighth', 0, 3, 2, 'eighth')

    >>> unitSpec([aDur, bDur, cDur])
    [(3.0, 'half', 1, None, None, None), (1.125, 'complex', None, None, None, None), (0.333333..., 'eighth', 0, 3, 2, 'eighth')]
    '''
    if common.isListLike(durationObjectOrObjects):
        ret = []
        for dO in durationObjectOrObjects:
            if dO.tuplets == None or len(dO.tuplets) == 0:
                ret.append((dO.quarterLength, dO.type, dO.dots, None, None, None))
            else:
                ret.append((dO.quarterLength, dO.type, dO.dots, dO.tuplets[0].numberNotesActual, dO.tuplets[0].numberNotesNormal, dO.tuplets[0].durationNormal.type))
        return ret
    else:
        dO = durationObjectOrObjects
        if dO.tuplets == None or len(dO.tuplets) == 0:
            return (dO.quarterLength, dO.type, dO.dots, None, None, None)
        else:
            return (dO.quarterLength, dO.type, dO.dots, dO.tuplets[0].numberNotesActual, dO.tuplets[0].numberNotesNormal, dO.tuplets[0].durationNormal.type)

def nextLargerType(durType):
    '''
    Given a type (such as 16th or quarter), return the next larger type.
    
    >>> nextLargerType("16th")
    'eighth'
    >>> nextLargerType("whole")
    'breve'
    >>> nextLargerType("duplex-maxima")
    'unexpressible'
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException("cannot get the next larger of %s" % durType)
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 0: # TODO: should this raise an exception?
        return 'unexpressible'
    else:
        return ordinalTypeFromNum[thisOrdinal - 1]
    
def quarterLengthToClosestType(qLen):
    '''
    Returns a two-unit tuple consisting of
    
    1. The type string ("quarter") that is smaller than or equal to the quarterLength of provided.

    2. Boolean, True or False, whether the conversion was exact.

    >>> quarterLengthToClosestType(.5)
    ('eighth', True)
    >>> quarterLengthToClosestType(.75)
    ('eighth', False)
    >>> quarterLengthToClosestType(1.8)
    ('quarter', False)
    '''
    if (4.0 / qLen) in typeFromNumDict:
        return (typeFromNumDict[4.0 / qLen], True)
    else:
        for numDict in sorted(typeFromNumDict.keys()):
            if numDict == 0: 
                continue
            elif (4.0 / qLen) < numDict and (8.0 / qLen) > numDict:
                return (typeFromNumDict[numDict], False)
        raise DurationException("Cannot return types greater than double duplex-maxima: remove this when we are sure this works...")

def musicXMLTypeToType(value):
    '''Convert a MusicXML type to an music21 type.

    >>> musicXMLTypeToType('long')
    'longa'
    >>> musicXMLTypeToType('quarter')
    'quarter'
    >>> musicXMLTypeToType(None)
    Traceback (most recent call last):
    DurationException...
    '''
    # MusicXML uses long instead of longa
    if value not in typeToDuration.keys():
        if value == 'long':
            return 'longa'
        else:
            raise DurationException('found unknown MusicXML type: %s' % value)
    else:
        return value

def typeToMusicXMLType(value):
    '''Convert a music21 type to a MusicXML type.

    >>> typeToMusicXMLType('longa')
    'long'
    >>> typeToMusicXMLType('quarter')
    'quarter'
    '''
    # MusicXML uses long instead of longa
    if value == 'longa': 
        return 'long'
    else:
        return value


def convertQuarterLengthToType(qLen):
    '''Return a type if there exists a type that is exactly equal to the duration of the provided quarterLength. Similar to quarterLengthToClosestType() but this function only returns exact matches.
    
    >>> convertQuarterLengthToType(2)
    'half'
    >>> convertQuarterLengthToType(0.125)
    '32nd'   
    >>> convertQuarterLengthToType(0.33333)
    Traceback (most recent call last):
    DurationException: cannot convert quarterLength 0.33333 exactly to type
    '''
    dtype, match = quarterLengthToClosestType(qLen)
    if match is False:
        raise DurationException("cannot convert quarterLength %s exactly to type" % qLen)
    else:
        return dtype

def dottedMatch(qLen, maxDots=4):
    '''Given a quarterLength, determine if there is a dotted (or non-dotted) type that exactly matches. Returns a pair of (numDots, type) or (False, False) if no exact matches are found.
    
    Returns a maximum of four dots by default.

    >>> dottedMatch(3.0)
    (1, 'half')
    >>> dottedMatch(1.75)
    (2, 'quarter')

    This value is not equal to any dotted note length
    >>> dottedMatch(1.6)
    (False, False)
    
    maxDots can be lowered for certain searches
    >>> dottedMatch(1.875)
    (3, 'quarter')
    >>> dottedMatch(1.875, 2)
    (False, False)

    '''
    for dots in range(0, maxDots + 1):
        ## assume qLen has n dots, so find its non-dotted length
        preDottedLength = (qLen + 0.0) / common.dotMultiplier(dots)
        durType, match = quarterLengthToClosestType(preDottedLength)
        if match is True:
            return (dots, durType)
    return (False, False)


def quarterLengthToTuplet(qLen, maxToReturn=4):
    '''    
    Returns a list of possible Tuplet objects for a given `qLen` (quarterLength). As there may be more than one possible solution, the `maxToReturn` integer specifies the maximum number of values returned.

    Searches for numerators specified in duration.defaultTupletNumerators (3, 5, 7, 11, 13). Does not return dotted tuplets, nor nested tuplets.

    Note that 4:3 tuplets won't be found, but will be found as dotted notes
    by dottedMatch.

    >>> quarterLengthToTuplet(.33333333)
    [<music21.duration.Tuplet 3/2/eighth>, <music21.duration.Tuplet 3/1/quarter>]

    By specifying only 1 `maxToReturn`, the a single-length list containing the Tuplet with the smallest type will be returned.    

    >>> quarterLengthToTuplet(.3333333, 1)
    [<music21.duration.Tuplet 3/2/eighth>]

    >>> quarterLengthToTuplet(.20)
    [<music21.duration.Tuplet 5/4/16th>, <music21.duration.Tuplet 5/2/eighth>, <music21.duration.Tuplet 5/1/quarter>]

    >>> c = quarterLengthToTuplet(.3333333, 1)[0]
    >>> c.tupletMultiplier()
    0.6666...
    '''
    post = []
    # type, qLen pairs
    durationToType = []
    for key, value in typeToDuration.items():
        durationToType.append((value, key))
    durationToType.sort()

    for typeValue, typeKey in durationToType:
        # try tuplets
        for i in defaultTupletNumerators:
            qLenBase = typeValue / float(i)
            # try multiples of the tuplet division, from 1 to max-1
            for m in range(1, i):
                qLenCandidate = qLenBase * m
                # need to use a courser grain here
                if common.almostEquals(qLenCandidate, qLen, 1e-5):
                    tupletDuration = Duration(typeKey)
                    newTuplet = Tuplet(numberNotesActual=i,
                                       numberNotesNormal=m,
                                       durationActual=tupletDuration,
                                       durationNormal=tupletDuration,)
                    post.append(newTuplet)
                    break
        # not looking for these matches will add tuple alternative
        # representations; this could be useful
            if len(post) >= maxToReturn: break
        if len(post) >= maxToReturn: break
    return post

def quarterLengthToDurations(qLen):
    '''
    Returns a List of new Duration Units given a quarter length.

    For many simple quarterLengths, the list will have only a single element.  However, for more complex durations, the list could contain several durations (presumably to be tied to each other).

    (All quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we don't like doing that).
    
    This is mainly a utility function. Much faster for many purposes is:
       d = Duration()
       d.quarterLength = 251.231312
    and then let Duration automatically create Duration Components as necessary.

    These examples use unitSpec() to get a concise summary of the contents

    >>> unitSpec(quarterLengthToDurations(2))
    [(2.0, 'half', 0, None, None, None)]
 
    Dots are supported

    >>> unitSpec(quarterLengthToDurations(3))
    [(3.0, 'half', 1, None, None, None)]
    >>> unitSpec(quarterLengthToDurations(6.0))
    [(6.0, 'whole', 1, None, None, None)]

    Double and triple dotted half note.

    >>> unitSpec(quarterLengthToDurations(3.5))
    [(3.5, 'half', 2, None, None, None)]
    >>> unitSpec(quarterLengthToDurations(3.75))
    [(3.75, 'half', 3, None, None, None)]

    A triplet quarter note, lasting .6666 qLen
    Or, a quarter that is 1/3 of a half.
    Or, a quarter that is 2/3 of a quarter.

    >>> unitSpec(quarterLengthToDurations(2.0/3.0))
    [(0.666..., 'quarter', 0, 3, 2, 'quarter')]

    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter
    Or, an eighth that is 2/3 of eighth

    >>> post = unitSpec(quarterLengthToDurations(.3333333))
    >>> common.almostEquals(post[0][0], .3333333)
    True
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth')

    A half that is 1/3 of a whole, or a triplet half note.
    Or, a half that is 2/3 of a half

    >>> unitSpec(quarterLengthToDurations(4.0/3.0))
    [(1.33..., 'half', 0, 3, 2, 'half')]

    A sixteenth that is 1/5 of a quarter
    Or, a sixteenth that is 4/5ths of a 16th

    >>> unitSpec(quarterLengthToDurations(1.0/5.0))
    [(0.2..., '16th', 0, 5, 4, '16th')]

    A 16th that is  1/7th of a quarter
    Or, a 16th that is 4/7 of a 16th

    >>> unitSpec(quarterLengthToDurations(1.0/7.0))
    [(0.142857..., '16th', 0, 7, 4, '16th')]

    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter

    >>> unitSpec(quarterLengthToDurations(4.0/7.0))
    [(0.571428..., 'quarter', 0, 7, 4, 'quarter')]

    If a duration is not containable in a single unit, this method
    will break off the largest type that fits within this type
    and recurse, adding as my units as necessary.

    >>> unitSpec(quarterLengthToDurations(2.5))
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)]

    >>> unitSpec(quarterLengthToDurations(2.3333333))
    [(2.0, 'half', 0, None, None, None), (0.333..., 'eighth', 0, 3, 2, 'eighth')]

    >>> unitSpec(quarterLengthToDurations(1.0/6.0))
    [(0.1666..., '16th', 0, 3, 2, '16th')]

    '''
    post = []
    typeLargest = None # largest found type that is less than
    match = False

    if qLen < 0:
        raise DurationException("qLen cannot be less than Zero.  Read Lewin, GMIT for more details...")
    elif common.almostEquals(qLen, 0.0):
        post.append(ZeroDuration)
        return post
    
    # try match to type, get next lowest
    typeFound, match = quarterLengthToClosestType(qLen) 
    if match:
        post.append(DurationUnit(typeFound))
    else:
        if typeFound == None :
            raise DurationException('cannot find duration types near quarter length %s' % qLen)

    # try dots
    # using typeFound here is the largest type that is not greater than qLen
    if not match:
        dots, durType = dottedMatch(qLen)
        if durType is not False:
            dNew = DurationUnit(durType)
            dNew.dots = dots
            post.append(dNew)
            match = True

    typeNext = nextLargerType(typeFound)
    # try tuplets
    # using typeNext is the next type that is larger than then the qLen
    if not match:
        # just get the first candidate
        tupleCandidates = quarterLengthToTuplet(qLen, 1)
        if len(tupleCandidates) > 0:
            # assume that the first, using the smallest type, is best
            dNew = DurationUnit(typeNext)
            dNew.tuplets = (tupleCandidates[0],)
            post.append(dNew)
            match = True

    # if we do not have a match, remove the largest type not greater 
    # and recursively apply
    if not match:
        post.append(DurationUnit(typeFound))
        qLenRemainder = qLen - typeToDuration[typeFound]
        if qLenRemainder < 0: 
            raise DurationException('cannot reduce quarter length (%s)' % qLenRemainder)
        # trying a fixed minimumum limit
        # this it do deal with common errors in processing
        if qLenRemainder > .003:

            try:
                if len(post) > 6: # we probably have a problem
                    raise DurationException('duration exceeds 6 components, with %s qLen left' % (qLenRemainder))
                else:    
                    post += quarterLengthToDurations(qLenRemainder)
            except RuntimeError: # if recursion exceeded
                msg = 'failed to find duration for qLen %s, qLenRemainder %s, post %s' % (qLen, qLenRemainder, post)
                raise DurationException(msg)
    return post

        
def partitionQuarterLength(qLen, qLenDiv=4):
    '''
    Given a `qLen` (quarterLength) and a `qLenDiv`, that is, a base quarterLength to divide the `qLen` into
    (default = 4; i.e., into whole notes), returns a list of Durations that
    partition the given quarterLength so that there is no leftovers. 
    
    This is a useful tool for partitioning a duration by Measures (i.e., take a long Duration and
    make it fit within several measures) or by beat groups.

    >>> # Here is a Little demonstration function that will show how we can use partitionQuarterLength: 
    >>> def pql(qLen, qLenDiv):
    ...    partitionList = partitionQuarterLength(qLen, qLenDiv)
    ...    for dur in partitionList: 
    ...        print(unitSpec(dur))
    
    >>> #Divide 2.5 quarters worth of time into eighth notes.
    >>> pql(2.5,.5)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)

    >>> #Dividing 5 qLen into 2.5 qLen bundles (i.e., 5/8 time)
    >>> pql(5, 2.5)
    (2.0, 'half', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (2.0, 'half', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)

    >>> #Dividing 5.25 qLen into dotted halves
    >>> pql(5.25,3)
    (3.0, 'half', 1, None, None, None)
    (2.0, 'half', 0, None, None, None)
    (0.25, '16th', 0, None, None, None)

    >>> #Dividing 1.33333 qLen into triplet eighths:
    >>> pql(4.0/3.0, 1.0/3.0)
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    
    >>> #Dividing 1.5 into triplet eighths
    >>> pql(1.5,.33333333333333)
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.333..., 'eighth', 0, 3, 2, 'eighth')
    (0.1666..., '16th', 0, 3, 2, '16th')

    >>> #There is no problem if the division unit is larger then the source duration, it
    just will not be totally filled.
    >>> pql(1.5, 4)
    (1.5, 'quarter', 1, None, None, None)
    '''

    post = []

    while qLen >= qLenDiv:
        post += quarterLengthToDurations(qLenDiv)
        qLen = qLen - qLenDiv
    if common.almostEquals(qLen, 0, grain=1e-5):
        #return post, True
        return post
    else:
        post += quarterLengthToDurations(qLen)
        #return post, False
        return post


def convertTypeToQuarterLength(dType, dots=0, tuplets=[], dotGroups=[]):
    '''
    Given a rhythm type (`dType`), number of dots (`dots`), an optional list of 
    Tuplet objects (`tuplets`), and a (very) optional list of Medieval dot groups (`dotGroups`), 
    return the equivalent quarter length.
    
    >>> convertTypeToQuarterLength('whole')
    4.0
    >>> convertTypeToQuarterLength('16th')
    0.25
    >>> convertTypeToQuarterLength('quarter', 2)
    1.75
    
    >>> tup = Tuplet(numberNotesActual = 5, numberNotesNormal = 4)
    >>> convertTypeToQuarterLength('quarter', 0, [tup])
    0.800000...

    >>> tup = Tuplet(numberNotesActual = 3, numberNotesNormal = 4)
    >>> convertTypeToQuarterLength('quarter', 0, [tup])
    1.333333...

    Also can handle those rare medieval dot groups (such as dotted-dotted half notes that take a full measure of 9/8).
    >>> convertTypeToQuarterLength('half', dotGroups = [1,1])
    4.5
    '''
    
    if dType in typeToDuration.keys():
        durationFromType = typeToDuration[dType]
    else:
        raise DurationException(
        "no such type (%s) avaliable for conversion" % dType)

    qtrLength = durationFromType

    # weird medieval notational device; rarely used.
    if len(dotGroups) > 0:
        for dot in dotGroups:
            qtrLength *= common.dotMultiplier(dot)
    else:
        qtrLength *= common.dotMultiplier(dots)
    for tup in tuplets:
        qtrLength *= tup.tupletMultiplier()
    return qtrLength


def convertTypeToNumber(dType):
    '''Convert a duration type string (`dType`) to a numerical scalar representation that shows
    how many of that duration type fits within a whole note.

    >>> convertTypeToNumber('quarter')
    4
    >>> convertTypeToNumber('half')
    2
    >>> convertTypeToNumber('1024th')
    1024
    >>> convertTypeToNumber('maxima')
    0.125
    '''
    dTypeFound = None
    for num, typeName in typeFromNumDict.items():
        if dType == typeName:
            #dTypeFound = int(num) # not all of these are integers
            dTypeFound = num
            break
    if dTypeFound == None:
        raise DurationException("Could not determine durationNumber from %s" 
        % dTypeFound)
    else:
        return dTypeFound


def updateTupletType(durationList):
    '''Given a list of Durations or DurationUnits (not yet working properly), 
    examine each Duration, and each component, and set Tuplet type to 
    start or stop, as necessary.

    >>> a = Duration(); a.quarterLength = .33333
    >>> b = Duration(); b.quarterLength = .33333
    >>> c = DurationUnit(); c.quarterLength = .33333
    >>> d = Duration(); d.quarterLength = 2
    >>> e = Duration(); e.quarterLength = .33333
    >>> f = DurationUnit(); f.quarterLength = .33333
    >>> g = Duration(); g.quarterLength = .33333

    >>> a.tuplets[0].type == None
    True
    >>> updateTupletType([a, b, c, d, e, f, g])
    >>> a.tuplets[0].type == 'start'
    True
    >>> b.tuplets[0].type == None
    True
    >>> c.tuplets[0].type == 'stop'
    True
    >>> e.tuplets[0].type == 'start'
    True
    >>> g.tuplets[0].type == 'stop'
    True
    '''
    #environLocal.printDebug(['calling updateTupletType'])
    tupletMap = [] # a list of tuplet obj / dur pairs  

    if isinstance(durationList, Duration): # if a Duration object alone
        durationList = [durationList] # put in list

    for part in durationList: # can be Durations or DurationUnits
        if isinstance(part, Duration):
            partGroup = part.components
        else:
            partGroup = [part] # emulate Duration.components
        for dur in partGroup: # all DurationUnits
            tuplets = dur.tuplets
            if tuplets in [(), None]: # no tuplets, length is zero
                tupletMap.append([None, dur])
            elif len(tuplets) > 1:
                raise Exception('got multi-tuplet DurationUnit; cannot yet handle this. %s' % tuplets)
            elif len(tuplets) == 1:
                tupletMap.append([tuplets[0], dur])
                if tuplets[0] != dur.tuplets[0]:
                    raise Exception('cannot access Tuplets object from within DurationUnit')
            else:
                raise Exception('cannot handle these tuplets: %s' % tuplets)

    # have a list of tuplet, DurationUnit pairs
    completionCount = 0 # qLen currently filled
    completionTarget = None # qLen necessary to fill tuplet
    for i in range(len(tupletMap)):
        tuplet, dur = tupletMap[i]

        if i > 0:
            tupletPrevious, durPrevious = tupletMap[i - 1]
        else: 
            tupletPrevious, durPrevious = None, None

        if i < len(tupletMap) - 1:
            tupletNext, durNext = tupletMap[i + 1]
            if tupletNext != None:
                nextNormalType = tupletNext.durationNormal.type
            else:
                nextNormalType = None
        else: 
            tupletNext, durNext = None, None
            nextNormalType = None

        #environLocal.printDebug(['updateTupletType previous, this, next:', 
        #                         tupletPrevious, tuplet, tupletNext])

        if tuplet != None:
            thisNormalType = tuplet.durationNormal.type
            completionCount += dur.quarterLength
            # if previous tuplet is None, always start
            # always reset completion target
            if tupletPrevious == None or completionTarget == None:
                tuplet.type = 'start'
                # get total quarter length of this tuplet
                completionTarget = (tuplet.numberNotesNormal * 
                                   tuplet.durationNormal.quarterLength)

                #environLocal.printDebug(['starting tuplet type, value:', 
                #                         tuplet, tuplet.type])
                #environLocal.printDebug(['completion count, target:', 
                #                         completionCount, completionTarget])
    
            # if tuplet next is None, always stop
            # if both previous and next are None, just keep a start

            # this, below, is optional:
            # if next normal type is not the same as this one, also stop
            # common.greaterThan uses is >= w/ almost equals
            elif (tupletNext == None or 
                common.greaterThanOrEqual(completionCount, completionTarget)):
                tuplet.type = 'stop'
                completionTarget = None # reset
                completionCount = 0 # rest
                #environLocal.printDebug(['stopping tuplet type, value:', 
                #                         tuplet, tuplet.type])
                #environLocal.printDebug(['completion count, target:', 
                #                         completionCount, completionTarget])

            # if typlet next and previous not None, increment 
            elif tupletPrevious != None and tupletNext != None:
                # do not need to change tuplet type; should be None        
                pass
                #environLocal.printDebug(['completion count, target:', 
                #                         completionCount, completionTarget])




#-------------------------------------------------------------------------------
class TupletException(Exception):
    pass

class Tuplet(object):
    '''A tuplet object is a representation of one or more ratios that modify duration values and are stored in Duration objects.

    Note that this is a duration modifier.  We should also have a tupletGroup
    object that groups note objects into larger groups.

    >>> myTup = Tuplet(numberNotesActual = 5, numberNotesNormal = 4)
    >>> print(myTup.tupletMultiplier())
    0.8
    >>> myTup2 = Tuplet(8, 5)
    >>> print(myTup2.tupletMultiplier())
    0.625
    >>> myTup2 = Tuplet(6, 4, "16th")
    >>> print(myTup2.durationActual.type)
    16th
    >>> print(myTup2.tupletMultiplier())
    0.666...
    
    Tuplets may be frozen, in which case they become immutable. Tuplets
    which are attached to Durations are automatically frozen
    
    >>> myTup.frozen = True
    >>> myTup.tupletActual = [3, 2]
    Traceback (most recent call last):
    ...
    TupletException: A frozen tuplet (or one attached to a duration) is immutable
    
    >>> myHalf = Duration("half")
    >>> myHalf.appendTuplet(myTup2)
    >>> myTup2.tupletActual = [5, 4]
    Traceback (most recent call last):
    ...
    TupletException: A frozen tuplet (or one attached to a duration) is immutable
    
    OMIT_FROM_DOCS
    # TODO: use __setattr__ to freeze all properties, and make a metaclass
    # exceptions: tuplet type, tuplet id: things that don't affect length

    '''

    frozen = False

    def __init__(self, *arguments, **keywords):
        #environLocal.printDebug(['creating Tuplet instance'])

        # necessary for some complex tuplets, interrupted, for instance

        if len(arguments) == 3:
            keywords['numberNotesActual'] = arguments[0]
            keywords['numberNotesNormal'] = arguments[1]
            keywords['durationActual'] = arguments[2]
            keywords['durationNormal'] = arguments[2]
        elif len(arguments) == 2:
            keywords['numberNotesActual'] = arguments[0]
            keywords['numberNotesNormal'] = arguments[1]
        
        if 'tupletId' in keywords:
            self.tupletId = keywords['tupletId']
        else:
            self.tupletId = 0

        if 'nestedLevel' in keywords:
            self.nestedLevel = keywords['nestedLevel']
        else:
            self.nestedLevel = 1

        # actual is the count of notes that happen in this space
        # this it not the real duration of notes that happen
        if 'numberNotesActual' in keywords:
            self.numberNotesActual = keywords['numberNotesActual']
        else:
            self.numberNotesActual = 3.0
        
        # this previously stored a Duration, not a DurationUnit
        if 'durationActual' in keywords:
            if isinstance(keywords['durationActual'], basestring):
                self.durationActual = DurationUnit(keywords['durationActual'])
            else:
                self.durationActual = keywords['durationActual']
        else:
            self.durationActual = DurationUnit("eighth") 

        # normal is the space that would normally be occupied
        if 'numberNotesNormal' in keywords:
            self.numberNotesNormal = keywords['numberNotesNormal']
        else:
            self.numberNotesNormal = 2.0
        
        # this previously stored a Duration, not a DurationUnit
        if 'durationNormal' in keywords:
            if isinstance(keywords['durationNormal'], basestring):
                self.durationNormal = DurationUnit(keywords['durationNormal'])
            else:
                self.durationNormal = keywords['durationNormal']
        else:
            self.durationNormal = DurationUnit("eighth") 

        # type needs to be set at the start/stop of each group
        # if set to None, will not be included
        self.type = None # start/stop: for mxl bracket/group drawing 
        self.bracket = True # true or false
        self.placement = "above" # above or below
        self.tupletActualShow = "number" # could be "number","type", or "none"
        self.tupletNormalShow = None

        # this attribute is not yet used anywhere
        #self.nestedInside = ""  # could be a tuplet object


    def __repr__(self):
        return ("<music21.duration.Tuplet %d/%d/%s>" % (self.numberNotesActual, self.numberNotesNormal, self.durationNormal.type))


    #---------------------------------------------------------------------------
    # properties

    def _setTupletActual(self, tupList=[]):
        if self.frozen == True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        self.numberNotesActual, self.durationActual = tupList
 
    def _getTupletActual(self):
        return [self.numberNotesActual, self.durationActual]

    tupletActual = property(_getTupletActual, _setTupletActual, 
        doc = '''Get or set a two element list of number notes actual and duration actual. 
        ''')


    def _setTupletNormal(self, tupList=[]):
        if self.frozen == True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        self.numberNotesNormal, self.durationNormal = tupList   
 
    def _getTupletNormal(self):
        return self.numberNotesNormal, self.durationNormal

    tupletNormal = property(_getTupletNormal, _setTupletNormal,
        doc = '''Get or set a two element list of number notes actual and duration normal. 
        ''')

    #---------------------------------------------------------------------------
    def tupletMultiplier(self):
        '''Get a floating point value by which to scale the duration that 
        this Tuplet is associated with.

        >>> myTuplet = Tuplet()
        >>> print(round(myTuplet.tupletMultiplier(), 3))
        0.667
        >>> myTuplet.tupletActual = [5, Duration('eighth')]
        >>> myTuplet.numberNotesActual
        5
        >>> myTuplet.durationActual.type
        'eighth'
        >>> print(myTuplet.tupletMultiplier())
        0.4
        '''
        lengthActual = self.durationActual.quarterLength
        return (self.totalTupletLength() / (
                self.numberNotesActual * lengthActual))

    def totalTupletLength(self):
        '''
        The total length in quarters of the tuplet as defined, assuming that
        enough notes existed to fill all entire tuplet as defined.

        For instance, 3 quarters in the place of 2 quarters = 2.0
        5 half notes in the place of a 2 dotted half notes = 6.0
        (In the end it's only the denominator that matters) 

        >>> a = Tuplet()
        >>> a.totalTupletLength()
        1.0
        >>> a.numberNotesActual = 3
        >>> a.durationActual = Duration('half')
        >>> a.numberNotesNormal = 2 
        >>> a.durationNormal = Duration('half')
        >>> a.totalTupletLength()
        4.0
        >>> a.setRatio(5,4)
        >>> a.totalTupletLength()
        8.0
        >>> a.setRatio(5,2)
        >>> a.totalTupletLength()
        4.0
        '''
        return self.numberNotesNormal * self.durationNormal.quarterLength


    def setRatio(self, actual, normal):
        '''Set the ratio of actual divisions to represented in normal divisions.
        A triplet is 3 actual in the time of 2 normal.

        >>> a = Tuplet()
        >>> a.tupletMultiplier()
        0.666...
        >>> a.setRatio(6,2)
        >>> a.tupletMultiplier()
        0.333...

        One way of expressing 6/4-ish triplets without numbers:
        >>> a = Tuplet()
        >>> a.setRatio(3,1)
        >>> a.durationActual = DurationUnit('quarter')
        >>> a.durationNormal = DurationUnit('half')
        >>> a.tupletMultiplier()
        0.666...
        >>> a.totalTupletLength()
        2.0
        '''
        if self.frozen == True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")

        self.numberNotesActual = actual
        self.numberNotesNormal = normal

    def setDurationType(self, type):
        '''Set the Duration for both actual and normal.

        >>> a = Tuplet()
        >>> a.tupletMultiplier()
        0.666...
        >>> a.totalTupletLength()
        1.0
        >>> a.setDurationType('half')
        >>> a.tupletMultiplier()
        0.6666...
        >>> a.totalTupletLength()
        4.0
        '''
        # these used to be Duration; now using DurationUnits
        if self.frozen == True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        self.durationActual = DurationUnit(type) 
        self.durationNormal = DurationUnit(type)        


    def augmentOrDiminish(self, scalar, inPlace=True):
        '''
        >>> a = Tuplet()
        >>> a.setRatio(6,2)
        >>> a.tupletMultiplier()
        0.333...
        >>> a.durationActual
        <music21.duration.DurationUnit 0.5>
        >>> a.augmentOrDiminish(.5)
        >>> a.durationActual
        <music21.duration.DurationUnit 0.25>
        >>> a.tupletMultiplier()
        0.333...
        '''
        if not scalar > 0:
            raise DurationException('scalar must be greater than zero')
        # TODO: scale the triplet in the same manner as Durations

        if inPlace:
            post = self
            self.frozen = False # have to unfreeze
        else:
            post = copy.deepcopy()

        # duration units scale
        post.durationActual.augmentOrDiminish(scalar, inPlace=True)
        post.durationNormal.augmentOrDiminish(scalar, inPlace=True)

        # ratios stay the same
        #self.numberNotesActual = actual
        #self.numberNotesNormal = normal


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''From this object return both an mxTimeModification object and an mxTuplet object configured for this Triplet.
        mxTuplet needs to be on the Notes mxNotations field

        >>> a = Tuplet()
        >>> a.bracket = True
        >>> b, c = a.mx
        '''
        mxTimeModification = musicxmlMod.TimeModification()
        mxTimeModification.set('actual-notes', self.numberNotesActual)
        mxTimeModification.set('normal-notes', self.numberNotesNormal)
        mxTimeModification.set('normal-type', self.durationNormal.type)

        if self.type != None and self.type != "":
            if self.type not in ["start", "stop"]:
                raise TupletException("Cannot create music XML from a tuplet of type " + self.type)
            mxTuplet = musicxmlMod.Tuplet()
            # start/stop; needs to bet set by group
            mxTuplet.set('type', self.type) 
            # only provide other parameters if this tuplet is a start
            if self.type == 'start':
                mxTuplet.set('bracket', musicxmlMod.booleanToYesNo(
                             self.bracket)) 
                mxTuplet.set('placement', self.placement) 
        else: # cannot provide an empty tuplet; return None
            mxTuplet = None 

        return mxTimeModification, mxTuplet

    def _setMX(self, mxNote):
        '''Given an mxNote, based on mxTimeModification and mxTuplet objects, return a Tuplet object
        ''' 
        if self.frozen == True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")

        mxTimeModification = mxNote.get('timemodification')
        #environLocal.printDebug(['got mxTimeModification', mxTimeModification])

        self.numberNotesActual = int(mxTimeModification.get('actual-notes'))
        self.numberNotesNormal = int(mxTimeModification.get('normal-notes'))
        mxNormalType = mxTimeModification.get('normal-type')
        # TODO: implement dot
        mxNormalDot = mxTimeModification.get('normal-dot')

        if mxNormalType != None:
            # this value does not seem to frequently be supplied by mxl
            # encodings, unless it is different from the main duration
            # this sets both actual and noraml types to the same type
            self.setDurationType(musicXMLTypeToType(
                mxTimeModification.get('normal-type')))
        else: # set to type of duration
            self.setDurationType(musicXMLTypeToType(mxNote.get('type')))

        mxNotations = mxNote.get('notations')
        #environLocal.printDebug(['got mxNotations', mxNotations])

        if mxNotations != None and len(mxNotations.getTuplets()) > 0:
            mxTuplet = mxNotations.getTuplets()[0] # a list, but only use first
            #environLocal.printDebug(['got mxTuplet', mxTuplet])

            self.type = mxTuplet.get('type') 
            self.bracket = musicxmlMod.yesNoToBoolean(mxTuplet.get('bracket'))
            #environLocal.printDebug(['got bracket', self.bracket])

            self.placement = mxTuplet.get('placement') 

    mx = property(_getMX, _setMX)





#-------------------------------------------------------------------------------
class DurationCommon(object):
    '''A base class for both Duration and DurationUnit objects.
    '''

    def aggregateTupletRatio(self):
        '''Return the aggregate tuplet ratio. Say you have 3:2 under a 5:4.  This will give the equivalent
        in non-nested tuplets. Returns a tuple representing the tuplet(!).  In the case of 3:2 under 5:4,
        it will return (15, 8).

        This tuple is needed for MusicXML time-modification among other places

        >>> complexDur = Duration('eighth')
        >>> complexDur.appendTuplet(Tuplet())
        >>> complexDur.aggregateTupletRatio()
        (3, 2)
        >>> tup2 = Tuplet()
        >>> tup2.setRatio(5, 4)
        >>> complexDur.appendTuplet(tup2)
        >>> complexDur.aggregateTupletRatio()
        (15, 8)
        '''        
        currentMultiplier = 1
        for thisTuplet in self.tuplets:
            currentMultiplier *= thisTuplet.tupletMultiplier()
        return common.decimalToTuplet(1.0 / currentMultiplier)


#-------------------------------------------------------------------------------
class DurationUnit(DurationCommon):
    '''A DurationUnit is a duration notation that (generally) can be notated with a a single notation unit, such as one note head, without a tie. 
    
    DurationUnits are not usually instantiated by users of music21, 
    but are used within Duration objects to model the containment of numerous summed components.

    Like Durations, DurationUnits have the option of unlinking the quarterLength
    and its representation on the page. For instance, in 12/16, Brahms sometimes
    used a dotted half note to indicate the length of 11/16th of a note. (see Don 
    Byrd's Extreme Notation webpage for more information). Since this duration can
    be expressed by a single graphical unit in Brahms's shorthand, it can be modeled
    by a single DurationUnit of unliked graphical/temporal representation.

    Additional types are needed beyond those in Duration: 'zero' type for zero-length
     durations and 'unexpressable' 
    type for anything that cannot be expressed as a single notation unit, and thus 
    needs a full Duration object (such as 2.5 quarterLengths.)
    '''
  
    def __init__(self, prototype='quarter'):

        self._type = ""
        # rarely used: dotted-dotted notes; e.g. dotted-dotted half in 9/8
        # dots can be a float for expressing Crumb dots (1/2 dots)
        self._dots = [0] 
        self._tuplets = ()
        
        if common.isNum(prototype):
            self._qtrLength = prototype
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = False
        else:
            if prototype not in typeToDuration.keys():
                raise DurationException('type (%s) is not valid' % type)
            self.type = prototype 
            self._qtrLength = 0.0
            self._typeNeedsUpdating = False
            self._quarterLengthNeedsUpdating = True
        
        # this parameters permits linking type, dots, and tuplets to qLen
        self.linkStatus = True


    #---------------------------------------------------------------------------
    def __repr__(self):
        '''Return a string representation.

        >>> aDur = DurationUnit('quarter')
        >>> repr(aDur)
        '<music21.duration.DurationUnit 1.0>'
        '''
        return '<music21.duration.DurationUnit %s>' % self._getQuarterLength()


    def __eq__(self, other):
        '''Test equality. Note: this may not work with Tuplets until we 
        define equality tests for tuplets.

        >>> aDur = DurationUnit('quarter')
        >>> bDur = DurationUnit('16th') 
        >>> cDur = DurationUnit('16th') 
        >>> aDur == bDur
        False
        >>> cDur == bDur        
        True
        '''
        if not isinstance(other, DurationCommon):
            return False

        if (self.type == other.type and 
            self.dots == other.dots and 
            self.tuplets == other.tuplets and 
            #self.linkStatus == other.linkStatus and
            self.quarterLength == other.quarterLength):
            return True
        else:
            return False

    def __ne__(self, other):
        '''Test not equality.

        >>> aDur = DurationUnit('quarter')
        >>> bDur = DurationUnit('16th') 
        >>> cDur = DurationUnit('16th') 
        >>> aDur != bDur
        True
        >>> cDur != bDur        
        False
        '''
        return not self.__eq__(other)

    def updateQuarterLength(self):
        '''
        Updates the quarterLength if linkStatus is True. Called by self._getQuarterLength if _quarterLengthNeedsUpdating is set
        to True.
        
        To set quarterLength, use self.quarterLength.

        >>> bDur = DurationUnit('16th') 
        >>> bDur.quarterLength
        0.25
        >>> bDur.unlink()
        >>> bDur.quarterLength = 234
        >>> bDur.quarterLength
        234
        >>> bDur.type
        '16th'
        >>> bDur.link() # if linking is restored, type is used to get qLen
        >>> bDur.updateQuarterLength()
        >>> bDur.quarterLength
        0.25
        '''
        if self.linkStatus is True:
            self._qtrLength = convertTypeToQuarterLength(self.type,
                            self.dots, self.tuplets) # add self.dotGroups
        self._quarterLengthNeedsUpdating = False

    def link(self):
        self.linkStatus = True

    def unlink(self):
        self.linkStatus = False


    def augmentOrDiminish(self, scalar, inPlace=True):
        '''Given a scalar greater than one, return a scaled version of this duration.

        >>> bDur = DurationUnit('16th') 
        >>> bDur.augmentOrDiminish(2)
        >>> bDur.quarterLength
        0.5
        >>> bDur.type
        'eighth'
        >>> bDur.augmentOrDiminish(4)
        >>> bDur.type
        'half'
        >>> bDur.augmentOrDiminish(.125)
        >>> bDur.type
        '16th'

        >>> cDur = bDur.augmentOrDiminish(16, inPlace=False)
        >>> cDur, bDur
        (<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>)
        '''
        if not scalar > 0:
            raise DurationException('scalar must be greater than zero')

        if inPlace:
            post = self
        else:
            post = DurationUnit()
            
        # note: this is not yet necessary, as changes are configured
        # by quarterLength, and this process generates new tuplets
        # if altnerative scaling methods are used for performance, this
        # method can be used. 
#         for tup in post._tuplets:
#             tup.augmentOrDiminish(scalar, inPlace=True)

        # possible look for convenient optimizations for easy scaling
        # not sure if linkStatus should be altered?
        post.quarterLength = self.quarterLength * scalar

        if not inPlace:
            return post
        else:
            return None


    #---------------------------------------------------------------------------
    def _getQuarterLength(self):
        '''determine the length in quarter notes from current information'''
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        return self._qtrLength
        
    def _setQuarterLength(self, value):
        '''Set the quarter note length to the specified value. 
        
        (We no longer unlink if quarterLength is greater than a long)

        >>> a = DurationUnit()
        >>> a.quarterLength = 3
        >>> a.type
        'half'
        >>> a.dots
        1
        >>> a.quarterLength = .5
        >>> a.type
        'eighth'
        >>> a.quarterLength = .75
        >>> a.type
        'eighth'
        >>> a.dots
        1
        >>> b = DurationUnit()
        >>> b.quarterLength = 16
        >>> b.type
        'longa'

        >>> c = DurationUnit()
        >>> c.quarterLength = 129
        >>> c.type
        Traceback (most recent call last):
            ...
        DurationException: Cannot return types greater than double duplex-maxima: remove this when we are sure this works...
        '''
        if not common.isNum(value):
            raise DurationException(
            "not a valid quarter length (%s)" % value)
        if self.linkStatus is True:
            self._typeNeedsUpdating = True
        self._qtrLength = value

    quarterLength = property(_getQuarterLength, _setQuarterLength,
    doc='''Property for getting or setting the quarterLength of a DurationUnit. 

    >>> a = DurationUnit()
    >>> a.quarterLength = 3
    >>> a.type
    'half'
    >>> a.dots
    1
    >>> a.quarterLength = .5
    >>> a.type
    'eighth'
    >>> a.quarterLength = .75
    >>> a.type
    'eighth'
    >>> a.dots
    1
    >>> b = DurationUnit()
    >>> b.quarterLength = 16
    >>> b.type
    'longa'

    ''')

    def updateType(self):
        if self.linkStatus == True:
            # cant update both at same time
            self._quarterLengthNeedsUpdating = False 
            tempDurations = quarterLengthToDurations(self.quarterLength)
            if len(tempDurations) > 1:
                self.type = 'unexpressible'
                self.dots = 0
                self.tuplets = ()
            else:
                self.type = tempDurations[0].type
                self.dots = tempDurations[0].dots
                self.tuplets = tempDurations[0].tuplets
        self._typeNeedsUpdating = False

    def _getType(self):
        '''Get the duration type.'''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._type
        
    def _setType(self, value):
        '''Set the type length to the specified value. Check for bad types.

        >>> a = Duration()
        >>> a.type = '128th'
        >>> a.quarterLength
        0.03125
        >>> a.type = 'half'
        >>> a.quarterLength
        2.0
        '''
        # validate
        if value not in typeToDuration.keys():
            raise DurationException("no such type exists: %s" % value)
        if value != self._type: # only update if different
            self._quarterLengthNeedsUpdating = True
        self._type = value

    type = property(_getType, _setType,
    doc='''Property for getting or setting the type of a DurationUnit. 

    >>> a = DurationUnit()
    >>> a.quarterLength = 3
    >>> a.type
    'half'
    >>> a.dots
    1
    >>> a.type = 'quarter'
    >>> a.quarterLength
    1.5
    >>> a.type = '16th'
    >>> a.quarterLength
    0.375
    ''')

    def setTypeFromNum(self, typeNum):
        numberFound = None
        if str(typeNum) in typeFromNumDict.keys():
            self.type = typeFromNumDict[str(typeNum)]
        else:
            raise DurationException("cannot find number %s" % typeNum)

    def _getOrdinal(self):
        '''
        Converts type to an ordinal number where maxima = 1 and 1024th = 14;  whole = 4 and quarter = 6. 
        Based on duration.ordinalTypeFromNum
    
        >>> a = DurationUnit('whole')
        >>> a.ordinal
        4
        >>> b = DurationUnit('maxima')
        >>> b.ordinal
        1
        >>> c = DurationUnit('1024th')
        >>> c.ordinal
        14
        '''
        if self._typeNeedsUpdating:
            self.updateType()

        ordinalFound = None
        for i in range(len(ordinalTypeFromNum)):
            if self.type == ordinalTypeFromNum[i]:
                ordinalFound = i        
                break
        if ordinalFound == None:
            raise DurationException(
                "Could not determine durationNumber from %s" % ordinalFound)
        else:
            return ordinalFound
    
    ordinal = property(_getOrdinal)

    def _getDots(self):
        '''
        _dots is a list (so we can do weird things like Crumb half-dots)
        Normally we only want the first element. 
        So that's what _getDots returns...
        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._dots[0]

    def _setDots(self, value):
        '''
        Sets the number of dots 

        Having this as a method permits error checking.

        >>> a = DurationUnit()
        >>> a.type = 'quarter'
        >>> a.dots = 1
        >>> a.quarterLength
        1.5
        >>> a.dots = 2
        >>> a.quarterLength
        1.75

        '''
        if value != self._dots[0]:
            self._quarterLengthNeedsUpdating = True
        if common.isNum(value):
            self._dots[0] = value
        else:
            raise DurationException("number of dots must be a number")

    dots = property(_getDots, _setDots)

    def _getTuplets(self):
        '''Return a tuple of Tuplet objects '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._tuplets

    def _setTuplets(self, value):
        '''Takes in a tuple of Tuplet objects
        '''
        if not isinstance(value, tuple):
            raise DurationException(
            "value submitted (%s) is not a tuple of tuplets" % value)
        if self._tuplets != value:
            self._quarterLengthNeedsUpdating = True
        # note that in some cases this methods seems to be called more 
        # often than necessary
        #environLocal.printDebug(['assigning tuplets in DurationUnit', 
        #                         value, id(value)])
        for thisTuplet in value:
            thisTuplet.frozen = True
        
        self._tuplets = value

    tuplets = property(_getTuplets, _setTuplets)

    def appendTuplet(self, newTuplet):
        newTuplet.frozen = True
        self._tuplets = self._tuplets + (newTuplet,)
        self._quarterLengthNeedsUpdating = True

    def _getLily(self):
        '''Simple lily duration: does not include tuplets; 
        these appear in the Stream object, because of 
        how lily represents triplets
        '''
        if self._typeNeedsUpdating:
            self.updateType()

        number_type = convertTypeToNumber(self.type)
        dots = "." * int(self.dots)
        return (str(number_type) + dots)

    lily = property(_getLily)



#-------------------------------------------------------------------------------
class ZeroDuration(DurationUnit):
    
    def __init__(self):
        DurationUnit.__init__(self)
        self.unlink()
        self.type = 'zero'
        self.quarterLength = 0.0

#-------------------------------------------------------------------------------
class DurationException(Exception):
    pass


class Duration(DurationCommon):
    '''
    Durations are one of the most important objects in music21. A Duration
    represents a span of musical time measurable in terms of quarter notes
    (or in advanced usage other units). For instance, "57 quarter notes" 
    or "dotted half tied to quintuplet sixteenth note" or simply "quarter note."
    
    A Duration object is made of one or more DurationUnit objects stored on the `components` list. 

    Multiple DurationUnits in a single Duration may be used to express tied notes, or may be used to split duration across barlines or beam groups. Some Duration objects are not expressable as a single notation unit. 

    Duration objects are not Music21Objects. Duration objects share many properties and attributes with DurationUnit objects, but Duration is not a subclass of DurationUnit.
    '''

    def __init__(self, *arguments, **keywords):
        '''
        First positional argument is assumed to be type string or a quarterLength. 
        '''
        self._qtrLength = 0.0
        # always have one DurationUnit object
        self._components = []
        # assume first arg is a duration type
        self._componentsNeedUpdating = False
        # defer updating until necessary
        self._quarterLengthNeedsUpdating = False
        
        if len(arguments) > 0:
            if common.isNum(arguments[0]):
                self.quarterLength = arguments[0]
            else:
                self.addDurationUnit(DurationUnit(arguments[0]))
        
        if "components" in keywords:
            self.components = keywords["components"]
            self._quarterLengthNeedsUpdating = True
        if 'type' in keywords:
            self.addDurationUnit(DurationUnit(keywords['type']))
      
        # only apply default if components are empty
        # looking at private _components so as not to trigger
        # _updateComponents
        if self.quarterLength == 0 and len(self._components) == 0:
            self.addDurationUnit(DurationUnit('quarter'))

        # linkages are a list of things used to connect durations.  
        # If undefined, Ties are used.  Other sorts of things could be 
        # dotted-ties, arrows, none, etc. As of Sep. 2008 -- not used.
        if "linkages" in keywords:
            self.linkages = keywords["linkages"]
        else:
            self.linkages = []
        
    def __repr__(self):
        '''Provide a representation.
        '''
        return '<music21.duration.Duration %s>' % self.quarterLength

    def updateQuarterLength(self):
        '''Look to components and determine quarter length.
        '''
        self._qtrLength = 0.0
        for dur in self.components:
            # if components quarterLength needs to be updated, it will
            # be updated when this property is called
            self._qtrLength += dur.quarterLength
        self._quarterLengthNeedsUpdating = False

    def _getComponents(self):
        if self._componentsNeedUpdating:
            self._updateComponents()
        return self._components
    
    def _setComponents(self, value):
        '''Provide components directly
        '''
        # previously, self._componentsNeedUpdating was not set here
        # this needs to be set because if _componentsNeedUpdating is True
        # new components will be derived from quarterLength
        if self._components is not value:
            self._componentsNeedUpdating = False
            self._components = value
            # this is Ture b/c components are note the same
            self._quarterLengthNeedsUpdating = True
            
    components = property(_getComponents, _setComponents)

    #---------------------------------------------------------------------------
    def _isComplex(self):
        if len(self.components) > 1:
            return True
        for dur in self.components:
            #environLocal.printDebug(['dur in components', dur])
            # any one unlinked component means this is complex
            if dur.linkStatus == False:
                return True
        else: return False
    
    isComplex = property(_isComplex,
        doc='''Property defining if this Duration has more than one DurationUnit object on the `component` list.

        >>> aDur = Duration()
        >>> aDur.quarterLength = 1.375
        >>> aDur.isComplex
        True
        >>> len(aDur.components)
        2

        >>> aDur = Duration()
        >>> aDur.quarterLength = 1.6666666
        >>> aDur.isComplex
        True
        >>> len(aDur.components)
        2

        >>> aDur = Duration()
        >>> aDur.quarterLength = .25
        >>> aDur.isComplex
        False
        >>> len(aDur.components)
        1
        ''')


    def _getQuarterLength(self):
        '''Can be the same as the base class.'''
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        self._quarterLengthNeedsUpdating = False
        return self._qtrLength
        
    def _setQuarterLength(self, value):
        '''Set the quarter note length to the specified value.
        
        Currently (if the value is different from what is already stored)
        this wipes out any existing components, not preserving
        their type.  So if you've set up Duration(1.5) as 3-eighth notes,
        setting Duration to 1.75 will NOT dot the last eighth note, but
        instead give you a single double-dotted half note.

        >>> a = Duration()
        >>> a.quarterLength = 3.5
        >>> a.quarterLength 
        3.5
        >>> for thisUnit in a.components:
        ...    print(unitSpec(thisUnit))
        (3.5, 'half', 2, None, None, None)
        
        >>> a.quarterLength = 2.5
        >>> a.quarterLength
        2.5
        >>> for thisUnit in a.components:
        ...    print(unitSpec(thisUnit))
        (2.0, 'half', 0, None, None, None)
        (0.5, 'eighth', 0, None, None, None)
        '''
        
        if self._qtrLength != value:
            self._qtrLength = value            
            self._componentsNeedUpdating = True
            self._quarterLengthNeedsUpdating = False

    quarterLength = property(_getQuarterLength, _setQuarterLength)         
    
    def _updateComponents(self):
        '''This method will re-construct components and thus is not 
        good if the components are already configured as you like
        '''
        self._quarterLengthNeedsUpdating = False
        self.components = quarterLengthToDurations(self.quarterLength)
        self._componentsNeedUpdating = False


    def _getType(self):
        '''Get the duration type.'''
        if self._componentsNeedUpdating == True:
            self._updateComponents()
            
        if len(self.components) > 1:
            return 'complex'
        elif len(self.components) == 1:
            return self.components[0].type
        else:
            return 'zero'
#            raise DurationException("zero DurationUnits in components")

    def _setType(self, value):
        '''Set the type length to the specified value.
        >>> a = Duration()
        >>> a.type = 'half'
        >>> a.quarterLength 
        2.0
        >>> a.type= '16th'
        >>> a.quarterLength 
        0.25
        '''
        # need to check that type is valid
        if value not in ordinalTypeFromNum:
            raise DurationException("no such type exists: %s" % value)

        if self.isComplex:
            raise DurationException("setting type on Complex note: Myke and Chris need to decide what that means")
            # what do we do if we already have multiple DurationUnits
        elif len(self.components) == 1:
            self.components[0].type = value
            self._quarterLengthNeedsUpdating = True
        else: # permit creating a new comoponent
            self.addDurationUnit(DurationUnit(value)) # updates
            self._quarterLengthNeedsUpdating = True

    type = property(_getType, _setType)

    def _getDots(self):
        '''
        Returns the number of dots in the Duration
        if it is a simple Duration.  Otherwise raises error.
        '''
        if self._componentsNeedUpdating == True:
            self._updateComponents()

        if len(self.components) > 1:
            return None
        elif len(self.components) == 1:
            return self.components[0].dots
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")

    def _setDots(self, value):
        '''Set dots if a number, as first element

        Having this as a method permits error checking.

        >>> a = Duration()
        >>> a.type = 'quarter'
        >>> a.dots = 1
        >>> a.quarterLength
        1.5

        >>> a.dots = 2
        >>> a.quarterLength
        1.75
        '''
        if not common.isNum(value):
            raise DurationException('only numeric dot values can be used iwth this method.')

        if len(self.components) > 1:
            raise DurationException("setting type on Complex note: Myke and Chris need to decide what that means")
        elif len(self.components) == 1:
            self.components[0].dots = value
            self._quarterLengthNeedsUpdating = True
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")        

    dots = property(_getDots, _setDots)

    def _getTuplets(self):
        if self._componentsNeedUpdating == True:
            self._updateComponents()
        if len(self.components) > 1:
            return None
        elif len(self.components) == 1:
            return self.components[0].tuplets
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")

    def _setTuplets(self, tupletTuple):
        #environLocal.printDebug(['assigning tuplets in Duration', tupletTuple])
        if len(self.components) > 1:
            raise DurationException("setting tuplets on Complex note: Myke and Chris need to decide what that means")
        elif len(self.components) == 1:
            for thisTuplet in tupletTuple:
                thisTuplet.frozen = True
            self.components[0].tuplets = tupletTuple
            self._quarterLengthNeedsUpdating = True
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")
        
    tuplets = property(_getTuplets, _setTuplets)

    def appendTuplet(self, newTuplet):
        self.tuplets = self.tuplets + (newTuplet,)



    #---------------------------------------------------------------------------
    # output formats

    def _getLily(self):
        '''
        Simple lily duration: does not include tuplets
        These are taken care of in the lily processing in stream.Stream
        since lilypond requires tuplets to be in groups

        '''
        msg = []
        for dur in self.components:
            msg.append(dur.lily)
        return ''.join(msg)

    lily = property(_getLily)


    def _getMX(self):
        '''
        Returns a list of one or more musicxml.Note() objects with all rhythms
        and ties necessary. mxNote objects are incompletely specified, lacking full representation and information on pitch, etc.

        >>> a = Duration()
        >>> a.quarterLength = 3
        >>> b = a.mx
        >>> len(b) == 1
        True
        >>> isinstance(b[0], musicxmlMod.Note)
        True

        >>> a = Duration()
        >>> a.quarterLength = .33333333
        >>> b = a.mx
        >>> len(b) == 1
        True
        >>> isinstance(b[0], musicxmlMod.Note)
        True
        '''
        post = [] # rename mxNoteList for consistencuy

        for dur in self.components:
            mxDivisions = int(defaults.divisionsPerQuarter * 
                              dur.quarterLength)
            mxType = typeToMusicXMLType(dur.type)
            # check if name is not in collection of MusicXML names, which does 
            # not have maxima, etc.
            mxDotList = []
            # only presently looking at first dot group
            # also assuming that these are integer values
            # need to handle fractional dots differently
            for x in range(int(dur.dots)):
                # only need to create object
                mxDotList.append(musicxmlMod.Dot())

            mxNote = musicxmlMod.Note()
            mxNote.set('duration', mxDivisions)
            mxNote.set('type', mxType)
            mxNote.set('dotList', mxDotList)
            post.append(mxNote)

        # second pass for ties if more than one components
        # this assumes that all component are tied

        # need to look for start and stop of tuplets
        tupletStatus = None

        for i in range(len(self.components)):
            dur = self.components[i]
            mxNote = post[i]

            # contains Tuplet, Dynamcs, Articulations
            mxNotations = musicxmlMod.Notations()

            # only need ties if more than one component
            mxTieList = []
            if len(self.components) > 1:
                if i == 0:
                    mxTie = musicxmlMod.Tie()
                    mxTie.set('type', 'start') # start, stop
                    mxTieList.append(mxTie)
                    mxTied = musicxmlMod.Tied()
                    mxTied.set('type', 'start') 
                    mxNotations.append(mxTied)
                elif i == len(self.components) - 1: #end 
                    mxTie = musicxmlMod.Tie()
                    mxTie.set('type', 'stop') # start, stop
                    mxTieList.append(mxTie)
                    mxTied = musicxmlMod.Tied()
                    mxTied.set('type', 'stop') 
                    mxNotations.append(mxTied)
                else: # continuation
                    for type in ['stop', 'start']:
                        mxTie = musicxmlMod.Tie()
                        mxTie.set('type', type) # start, stop
                        mxTieList.append(mxTie)
                        mxTied = musicxmlMod.Tied()
                        mxTied.set('type', type) 
                        mxNotations.append(mxTied)

            if len(self.components) > 1:
                mxNote.set('tieList', mxTieList)

            if len(dur.tuplets) > 0:
                mxTimeModification, mxTuplet = dur.tuplets[0].mx
                mxNote.set('timemodification', mxTimeModification)
                if mxTuplet != None:
                    mxNotations.append(mxTuplet)

            # add notations to mxNote
            mxNote.set('notations', mxNotations)
        return post # a list of mxNotes

    def _setMX(self, mxNote):
        '''
        Given a single MusicXML Note object, read in and create a
        Duration

        mxNote must have a defined _measure attribute that is a reference to the
        MusicXML Measure that contains it

        >>> from music21 import musicxml
        >>> a = musicxml.Note()
        >>> a.setDefaults()
        >>> m = musicxml.Measure()
        >>> m.setDefaults()
        >>> a.external['measure'] = m # assign measure for divisions ref
        >>> a.external['divisions'] = m.external['divisions']
        >>> c = Duration()
        >>> c.mx = a
        >>> c.quarterLength
        1.0
        '''
        if mxNote.external['measure'] == None:
            raise DurationException(
            "cannont determine MusicXML duration without a reference to a measure (%s)" % mxNote)

        mxDivisions = mxNote.external['divisions']

        if mxNote.duration != None: 

            if mxNote.get('type') != None:
                type = musicXMLTypeToType(mxNote.get('type'))
                forceRaw = False
            else: # some rests do not define type, and only define induration
                type = None # no type to get, must use raw
                forceRaw = True
    
            mxDotList = mxNote.get('dotList')
            qLen = float(mxNote.duration) / float(mxDivisions)

            mxNotations = mxNote.get('notations')
            mxTimeModification = mxNote.get('timemodification')

            if mxTimeModification != None:
                tup = Tuplet()
                tup.mx = mxNote # get all necessary config from mxNote

                #environLocal.printDebug(['created Tuplet', tup])
                # need to see if there is more than one component
                #self.components[0]._tuplets.append(tup)
            else:
                tup = None

            # two ways to create durations, raw and cooked
            durRaw = Duration() # raw just uses qLen
            durRaw.quarterLength = qLen

            if forceRaw:
                #environLocal.printDebug(['forced to use raw duration', durRaw])
                self.components = durRaw.components
            else: # a cooked version builds up from pieces
                durUnit = DurationUnit()
                durUnit.type = type
                durUnit.dots = len(mxDotList)
                if not tup == None:
                    durUnit.appendTuplet(tup)
                durCooked = Duration(components=[durUnit])
    
                #environLocal.printDebug(['got durRaw, durCooked:', durRaw, durCooked])
                if durUnit.quarterLength != durCooked.quarterLength:
                    environLocal.printDebug(['error in stored MusicXML representaiton and duration value', durRaw, durCooked])
                # old way just used qLen
                #self.quarterLength = qLen
                self.components = durCooked.components


    mx = property(_getMX, _setMX)


    def _getMusicXML(self):
        '''Return a complete MusicXML string with defaults.
        '''
        # as this is a rhythm alone, can set a different note head default
        mxNotehead = musicxmlMod.Notehead()
        mxNotehead.set('charData', defaults.noteheadUnpitched)

        # make a copy, as we this process will change tuple types
        selfCopy = copy.deepcopy(self)
        updateTupletType(selfCopy.components) # modifies in place

        mxNoteList = selfCopy.mx # getting durations here as mxNotes
        for i in range(len(mxNoteList)):
            mxNoteDefault = musicxmlMod.Note()
            mxNoteDefault.setDefaults()    
            mxNoteDefault.set('notehead', mxNotehead)
            mxNoteList[i] = mxNoteList[i].merge(mxNoteDefault, favorSelf=True)

        mxMeasure = musicxmlMod.Measure()
        mxMeasure.setDefaults()
        for mxNote in mxNoteList:
            mxMeasure.append(mxNote)
        mxPart = musicxmlMod.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure)

        mxScorePart = musicxmlMod.ScorePart()
        mxScorePart.setDefaults()
        mxPartList = musicxmlMod.PartList()
        mxPartList.append(mxScorePart)

        mxIdentification = musicxmlMod.Identification()
        mxIdentification.setDefaults() # will create a composer

        mxScore = musicxmlMod.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)
        return mxScore.xmlStr()

    musicxml = property(_getMusicXML)

    def write(self, fmt='musicxml', fp=None):
        '''
        As in Music21Object.write: Writes a file in the given format (musicxml by default)
        
        A None file path will result in temporary file
        '''
        format, ext = common.findFormat(fmt)
        if format == None:
            raise DurationException('bad format (%s) provided to write()' % fmt)
        elif format == 'musicxml':
            if fp == None:
                fp = environLocal.getTempFile(ext)
            dataStr = self.musicxml
        else:
            raise DurationException('cannot support writing in this format, %s yet' % format)
        f = open(fp, 'w')
        f.write(dataStr)
        f.close()
        return fp

    def show(self, format='musicxml'):
        '''
        Same as Music21Object.show()
        '''
        environLocal.launch(format, self.write(format))


    #---------------------------------------------------------------------------
    # methods for manipulating components

    def clear(self):
        ''' 
        Permit all componets to be removed. 
        (It is not clear yet if this is needed)

        >>> a = Duration()
        >>> a.quarterLength = 4
        >>> a.type
        'whole'
        >>> a.clear()
        >>> a.quarterLength
        0.0
        >>> a.type
        'zero'
        '''
        self.components = [] 
        self._quarterLengthNeedsUpdating = True

    def addDurationUnit(self, dur):
        ''' 
        Add a DurationUnit or a Duration's components to this Duration.

        >>> a = Duration('quarter')
        >>> b = Duration('quarter')
        >>> a.addDurationUnit(b)
        >>> a.quarterLength
        2.0
        >>> a.type
        'complex'
        '''

        if isinstance(dur, Duration): # its a Duration object
            self.components += dur.components   
        elif isinstance(dur, DurationUnit): 
            self.components.append(dur)
        else:
            self.components += Duration(dur).components
        self._quarterLengthNeedsUpdating = True

    def consolidate(self):
        '''Given a Duration with multiple components, consolidate into a single
        Duration. This can only be based on quarterLength; this is 
        destructive: information is lost from coponents.

        This cannot be done for all Durations, as DurationUnits cannot express all durations

        >>> a = Duration()
        >>> a.fill(['quarter', 'half', 'quarter'])
        >>> a.quarterLength
        4.0
        >>> len(a.components)
        3
        >>> a.consolidate()
        >>> a.quarterLength
        4.0
        >>> len(a.components)
        1
        
        But it gains a type!
        >>> a.type
        'whole'
        '''
        if len(self.components) == 1:
            pass # nothing to be done
        else:
            dur = DurationUnit()
            # if quarter length is not notatable, will automatically unlink
            # some notations will not properly unlin, and raise an error
            dur.quarterLength = self.quarterLength
            self.components = [dur]

    def expand(self, qLenDiv=4):
        '''
        Make a duration notatable by partitioning it into smaller
        units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength
        '''
        self.components = partitionQuarterLength(self.quarterLength,
                                                    qLenDiv)        
        self._componentsNeedUpdating = False



    def augmentOrDiminish(self, scalar, retainComponents=False, inPlace=True):
        '''Given a scalar greater than one, return a scaled version of this duration.

        >>> aDur = Duration()
        >>> aDur.quarterLength = 1.5 # dotted quarter
        >>> aDur.augmentOrDiminish(2)
        >>> aDur.quarterLength
        3.0
        >>> aDur.type
        'half'
        >>> aDur.dots
        1

        >>> bDur = Duration()
        >>> bDur.quarterLength = 2.125 # requires components
        >>> len(bDur.components)
        2
        >>> cDur = bDur.augmentOrDiminish(2, retainComponents=True, inPlace=False)
        >>> cDur.quarterLength
        4.25
        >>> cDur.components
        [<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>]

        >>> dDur = bDur.augmentOrDiminish(2, retainComponents=False, inPlace=False)
        >>> dDur.components
        [<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>]


        '''
        if not scalar > 0:
            raise DurationException('scalar must be greater than zero')

        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)

        if retainComponents:
            for d in post.components:
                d.augmentOrDiminish(scalar, inPlace=True)
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = True
        else:
            post.quarterLength = post.quarterLength * scalar

        if not inPlace:
            return post
        else:
            return None



    def componentIndexAtQtrPosition(self, quarterPosition):
        '''returns the index number of the duration component sounding at
        the given quarter position.

        Note that for 0 and the last value, the object is returned.

        >>> components = []

        TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like)
              better is just to copy and paste three times.  Very easy to see what
              is happening.
        
        >>> for x in [1,1,1]: 
        ...   components.append(Duration('quarter'))
        >>> a = Duration()
        >>> a.components = components
        >>> a.updateQuarterLength()
        >>> a.quarterLength
        3.0
        >>> a.componentIndexAtQtrPosition(.5)
        0
        >>> a.componentIndexAtQtrPosition(1.5)
        1
        >>> a.componentIndexAtQtrPosition(2.5)
        2

        this is odd behavior:
        e.g. given d1, d2, d3 as 3 quarter notes and
        self.components = [d1, d2, d3]
        then
        self.componentIndexAtQtrPosition(1.5) == d2
        self.componentIndexAtQtrPosition(2.0) == d3
        self.componentIndexAtQtrPosition(2.5) == d3
        '''        

#         if self._expansionNeeded:
#             self.expand()
#             self._expansionNeeded = False


        if self.components == []:
            raise DurationException(
                "Need components to run getComponentIndexAtQtrPosition")
        elif quarterPosition > self.quarterLength:
            raise DurationException(
                "position is after the end of the duration")

        elif quarterPosition < 0:
            # values might wrap around from the other side
            raise DurationException(
                "position is before the start of the duration")
        
        # it seems very odd that thes return objects
        # while the method name suggests indices will be returned 
        if common.almostEquals(quarterPosition, 0):
            return self.components[0]
        elif common.almostEquals(quarterPosition, self.quarterLength):
            return self.components[-1]
        
        currentPosition = 0.0
        indexFound = None
        for i in range(len(self.components)):
            currentPosition += self.components[i].quarterLength
            if (currentPosition > quarterPosition and 
                not common.almostEquals(currentPosition, quarterPosition)):
                indexFound = i
                break
        if indexFound == None:
            raise DurationException(
                "Could not match quarter length within an index.")
        else:
            return indexFound

    def componentStartTime(self, componentIndex):
        '''
        For a valid component index value, this returns the quarter note offset
        at which that component would start.

        This does not handle fractional arguments.

        >>> components = []
        >>> for x in [1,1,1]: 
        ...    components.append(Duration('quarter'))
        >>> a = Duration()
        >>> a.components = components
        >>> a.updateQuarterLength()
        >>> a.quarterLength
        3.0
        >>> a.componentStartTime(0)
        0.0
        >>> a.componentStartTime(1)
        1.0
        '''

        if componentIndex not in range(len(self.components)):
            raise DurationException(('invalid component index value (%s) ' + \
                'submitted; value must be integers between 0 and %s') % (
                componentIndex, len(self.components) - 1))

        currentPosition = 0.0
        for i in range(componentIndex):
            currentPosition += self.components[i].quarterLength
        return currentPosition
           

    def sliceComponentAtPosition(self, quarterPosition):
        '''Given a quarter position within a component, divide that 
        component into two components.

        >>> a = Duration()
        >>> a.clear() # need to remove default
        >>> components = []

        >>> a.addDurationUnit(Duration('quarter'))
        >>> a.addDurationUnit(Duration('quarter'))
        >>> a.addDurationUnit(Duration('quarter'))

        >>> a.quarterLength
        3.0
        >>> a.sliceComponentAtPosition(.5)
        >>> a.quarterLength
        3.0
        >>> len(a.components)
        4
        >>> a.components[0].type
        'eighth'
        >>> a.components[1].type
        'eighth'
        >>> a.components[2].type
        'quarter'
        '''

        # this may return a Duration object; we are not sure
        sliceIndex = self.componentIndexAtQtrPosition(quarterPosition)

        # get durObj that qPos is within 
        if common.isNum(sliceIndex):
            durObjSlice = self.components[sliceIndex]
        else: # assume that we got an object 
            durObjSlice = sliceIndex

        # this will not work if componentIndexAtQtrPosition returned an obj
        # get the start pos in ql of this dur obj
        durationStartTime = self.componentStartTime(sliceIndex)
        # find difference between desired split and start pos of this dur obj
        # this is the left side dur
        slicePoint = quarterPosition - durationStartTime
        # this is the right side dur
        remainder = durObjSlice.quarterLength - slicePoint

        if remainder == 0 or slicePoint == 0: # nothing to be done
            # this might not be an error
            raise DurationException(
            "no slice is possible at this quarter position")
        else:
            d1 = Duration()
            d1.quarterLength = slicePoint

            d2 = Duration()
            d2.quarterLength = remainder

            self.components[sliceIndex: (sliceIndex + 1)] = [d1, d2]
            # lengths should be the same as it was before
            self.updateQuarterLength()

    def fill(self, quarterLengthList=['quarter', 'half', 'quarter']):
        '''Utility method for testing; a quick way to fill components. This will
        remove any exisiting values.
        '''
        self.components = []
        for x in quarterLengthList:
            self.addDurationUnit(Duration(x))


class GraceDuration(Duration):
    def __init__(self):
        Duration.__init__(self)

        # TODO: these cannot be unlinked presently like this because
        # this objec is a subclass of Duration, not DurationUnit
        #self.unlink()
        self.quarterLength = 0

class LongGraceDuration(Duration):
    def __init__(self):
        Duration.__init__(self)
        #self.unlink()
        self.quarterLength = 0        

class AppogiaturaStartDuration(Duration):
    pass

class AppogiaturaStopDuration(Duration):
    pass


#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass


    def testSingle(self):
        a = Duration()
        a.quarterLength = 2.66666
        a.show()
    
    def testBasic(self):
        import random
        from music21 import stream
        from music21 import note

        a = stream.Stream()

        for x in range(30):
            ql = random.choice([1, 2, 3, 4, 5]) + random.choice([0, .25, .5, .75])
            # w/ random.choice([0,.33333,.666666] gets an error
            n = note.Note()
            b = Duration()
            b.quarterLength = ql
            n.duration = b
            a.append(n)

        a.show()




class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testTuple(self):
#         note1 = Note()
#         note1.duration.type = "quarter"
        
        # create a tuplet with 5 dotted eighths in the place of 3 double-dotted 
        #eighths
        dur1 = Duration()
        dur1.type = "eighth"
        dur1.dots = 1
        
        dur2 = Duration()
        dur2.type = "eighth"
        dur2.dots = 2
        
        tup1 = Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur2]
        
        #print "For 5 dotted eighths in the place of 3 double-dotted eighths"
        #print "Total tuplet length is",
        self.assertEqual(tup1.totalTupletLength(), 2.625)
        #print tup1.totalTupletLength(), # 2.625
        #print "quarter notes.\nEach note is",
        #print "times as long as it would normally be."
        
        ### create a new dotted quarter and apply the tuplet to it
        dur3 = Duration()
        dur3.type = "quarter"
        dur3.dots = 1
        dur3.tuplets = (tup1,)
        #print "So a tuplet-dotted-quarter's length is",
        self.assertEqual(round(dur3.quarterLength, 2), 1.05)

        # print "quarter notes"
        
        # create a tuplet with 3 sixteenths in the place of 2 sixteenths
        tup2 = Tuplet()
        dur4 = Duration()
        dur4.type = "16th"
        tup2.tupletActual = [3, dur4]
        tup2.tupletNormal = [2, dur4]
        
#         print "\nTup2:\nTotal tuplet length is",
#         print tup2.totalTupletLength(),
#         print "quarter notes.\nEach note is",
#         print tup2.tupletMultiplier(),
#         print "times as long as it would normally be."
        
        self.assertEqual(tup2.totalTupletLength(), 0.5)
        self.assertEqual(common.almostEquals(
            tup2.tupletMultiplier(), 0.666666666667), True)

        dur3.tuplets = (tup1, tup2)
#         print "So a tuplet-dotted-quarter's length under both tuplets is",
#         print dur3.getQuarterLength(),
#         print "quarter notes"

        self.assertEqual(common.almostEquals(
            dur3.quarterLength, 0.7), True)

        myTuplet = Tuplet()
        self.assertAlmostEquals(round(myTuplet.tupletMultiplier(), 3), 0.667)
        myTuplet.tupletActual = [5, DurationUnit('eighth')]
        self.assertAlmostEquals(myTuplet.tupletMultiplier(), 0.4)


    def testMxLoading(self):
        from music21 import musicxml
        a = musicxml.Note()
        a.setDefaults()
        m = musicxml.Measure()
        m.setDefaults()
        a.external['measure'] = m # assign measure for divisions ref
        a.external['divisions'] = m.external['divisions']
        c = Duration()
        c.mx = a


    def testTupletTypeComplete(self):
        '''Test settinf of tuplet type when durations sum to expected completion
        '''
        # default tuplets group into threes when possible
        test, match = ([.333333] * 3 + [.1666666] * 6,
            ['start', None, 'stop', 'start', None, 'stop', 'start', None, 'stop'])
        input = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            input.append(d)
        updateTupletType(input)
        output = []
        for d in input:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)


        tup6 = Duration()
        tup6.quarterLength = .16666666
        tup6.tuplets[0].numberNotesActual = 6
        tup6.tuplets[0].numberNotesNormal = 4

        tup5 = Duration()
        tup5.quarterLength = .2 # default is 5 in the space of 4 16th

        input = [copy.deepcopy(tup6), copy.deepcopy(tup6), copy.deepcopy(tup6),
        copy.deepcopy(tup6), copy.deepcopy(tup6), copy.deepcopy(tup6),
        copy.deepcopy(tup5), copy.deepcopy(tup5), copy.deepcopy(tup5),
        copy.deepcopy(tup5), copy.deepcopy(tup5)]

        match = ['start', None, None, None, None, 'stop',
                 'start', None, None, None, 'stop']

        updateTupletType(input)
        output = []
        for d in input:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)



    def testTupletTypeIncomplete(self):
        '''Test setting of tuplet type when durations do not sum to expected
        completion. 
        '''

        # the current match results here are a good compromise
        # for a difficult situation. 
        test, match = ([.333333] * 2 + [.1666666] * 5,
            ['start', None, None, 'stop', 'start', None, 'stop']
            )
        input = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            input.append(d)
        updateTupletType(input)
        output = []
        for d in input:
            output.append(d.tuplets[0].type)
        #environLocal.printDebug(['got', output])
        self.assertEqual(output, match)


    def testAugmentOrDiminish(self):

        # test halfs and doubles

        for ql, half, double in [(2,1,4), (.5,.25,1), (1.5, .75, 3), 
                                 (.6666666, .3333333, 1.3333333)]:
        
            d = Duration()
            d.quarterLength = ql
            a = d.augmentOrDiminish(.5, inPlace=False)
            self.assertAlmostEquals(a.quarterLength, half, 5)

            b = d.augmentOrDiminish(2, inPlace=False)
            self.assertAlmostEquals(b.quarterLength, double, 5)


        # testing tuplets in duration units

        a = DurationUnit()
        a.quarterLength = .3333333
        self.assertAlmostEqual(a.tuplets[0].tupletMultiplier(), .666666, 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.5>')

        a.augmentOrDiminish(2)
        self.assertAlmostEqual(a.tuplets[0].tupletMultiplier(), .666666, 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 1.0>')

        a.augmentOrDiminish(.25)
        self.assertAlmostEqual(a.tuplets[0].tupletMultiplier(), .666666, 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.25>')


        # testing tuplets on Durations
        a = Duration()
        a.quarterLength = .3333333
        self.assertAlmostEqual(a.tuplets[0].tupletMultiplier(), .666666, 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.5>')

        a.augmentOrDiminish(2)
        self.assertAlmostEqual(a.tuplets[0].tupletMultiplier(), .666666, 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 1.0>')

        a.augmentOrDiminish(.25)
        self.assertAlmostEqual(a.tuplets[0].tupletMultiplier(), .666666, 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.25>')



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [convertQuarterLengthToType, Duration, Tuplet]

if __name__ == "__main__":
    import sys
    import music21
    #music21.mainTest(Test, TestExternal)

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:

        a = Test()
        a.testAugmentOrDiminish()