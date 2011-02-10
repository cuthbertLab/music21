#-------------------------------------------------------------------------------
# Name:         meter.py
# Purpose:      Classes for meters
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module defines the :class:`~music21.meter.TimeSignature` object, as well as component objects for defining nested metrical structures, :class:`~music21.meter.MeterTerminal` and :class:`~music21.meter.MeterSequence` objects.
'''

import unittest, doctest
import re, copy
#import fractions # available in 2.6 and greater

import music21

from music21 import common
from music21 import duration
from music21 import lily
from music21 import beam
from music21 import musicxml
from music21.musicxml import translate as musicxmlTranslate
from music21 import environment
_MOD = 'meter.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

validDenominators = [1,2,4,8,16,32,64,128] # in order
# also [pow(2,x) for x in range(8)]
MIN_DENOMINATOR_TYPE = '128th'

# store a module-level dictionary of partitioned meter sequences used
# for setting default accent weights; store as needed
_meterSequenceAccentArchetypes = {}

# performance tests showed that caching this additional structures did not
# show immediate performance benefits
#_meterSequenceBeatArchetypes = {}
#_meterSequenceBeamArchetypes = {}
# store meter sequence division options, once created, in a module
# level dictionary
_meterSequenceDivisionOptions = {}

def slashToFraction(value):
    '''
    >>> from music21 import *
    >>> meter.slashToFraction('3/8')
    (3, 8)
    >>> meter.slashToFraction('7/32')
    (7, 32)

    OMIT_FROM_DOCS
    TODO: it seems like this should return only integers; not sure
    why these originally were floats.
    '''
    value = value.strip() # rem whitespace
    matches = re.match("(\d+)\/(\d+)", value)
    if matches is not None:
        n = int(matches.group(1))
        d = int(matches.group(2))
        return n,d
    else:
        environLocal.printDebug(['slashToFraction() cannot find two part fraction', value])
        return None

def slashCompoundToFraction(value):
    '''
    >>> from music21 import *
    >>> meter.slashCompoundToFraction('3/8+2/8')
    [(3, 8), (2, 8)]
    >>> meter.slashCompoundToFraction('5/8')
    [(5, 8)]
    >>> meter.slashCompoundToFraction('5/8+2/4+6/8')
    [(5, 8), (2, 4), (6, 8)]

    '''
    post = []
    value = value.strip() # rem whitespace
    value = value.split('+')
    for part in value:
        m = slashToFraction(part)
        if m == None: 
            pass
        else:
            post.append(m)
    return post


def slashMixedToFraction(valueSrc):
    '''Given a mixture if possible meter fraction representations, return       
    a list of pairs. If originally given as a summed numerator; break
    into separate fractions.

    >>> from music21 import *
    >>> meter.slashMixedToFraction('3/8+2/8')
    ([(3, 8), (2, 8)], False)

    >>> meter.slashMixedToFraction('3+2/8')
    ([(3, 8), (2, 8)], True)

    >>> meter.slashMixedToFraction('3+2+5/8')
    ([(3, 8), (2, 8), (5, 8)], True)

    >>> meter.slashMixedToFraction('3+2+5/8+3/4')
    ([(3, 8), (2, 8), (5, 8), (3, 4)], True)

    >>> meter.slashMixedToFraction('3+2+5/8+3/4+2+1+4/16')
    ([(3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)], True)

    >>> meter.slashMixedToFraction('3+2+5/8+3/4+2+1+4')
    Traceback (most recent call last):
    ...
    MeterException: cannot match denominator to numerator in: 3+2+5/8+3/4+2+1+4
    '''
    pre = []
    post = []
    summedNumerator = False

    value = valueSrc.strip() # rem whitespace
    value = value.split('+')
    for part in value:
        if '/' in part:
            fraction = slashToFraction(part)
            if fraction == None:
                raise TimeSignatureException('cannot create time signature from:', valueSrc)
            pre.append(list(fraction))
        else: # its just a numerator
            pre.append([int(part), None])
    # when encountering a missing denominator, find the fist defined
    # and apply to all previous
    for i in range(len(pre)):
        if pre[i][1] != None: # there is a denominator   
            post.append(tuple(pre[i]))
        else: # search ahead for next defined denominator
            summedNumerator = True
            match = None
            for j in range(i, len(pre)):
                if pre[j][1] != None:
                    match = pre[j][1]
                    break
            if match == None:
                raise MeterException('cannot match denominator to numerator in: %s' % valueSrc)
            else:
                pre[i][1] = match
            post.append(tuple(pre[i]))

    return post, summedNumerator


def fractionToSlashMixed(fList):
    '''Given a list of fraction values, compact numerators by sum if
    denominators are the same 

    >>> from music21 import *
    >>> meter.fractionToSlashMixed([(3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)])
    [('3+2+5', 8), ('3', 4), ('2+1+4', 16)]
    '''
    pre = []
    for i in range(len(fList)):
        n, d = fList[i]
        # look at previous fration and determin if denominator is the same

        match = None
        search = range(0,len(pre))
        search.reverse() # go backwards
        for j in search:
            if pre[j][1] == d:
                match = j # index to add numerator
                break
            else:
                break # if not found in one less

        if match == None:
            pre.append([[n], d])
        else: # appnd nuemrator
            pre[match][0].append(n)
    # create string representation
    post = []
    for part in pre:
        n = [str(x) for x in part[0]]
        n = '+'.join(n)
        d = part[1]
        post.append((n, d))

    return post


def fractionSum(fList):
    '''Given a list of fractions represented as a list, find the sum
    
    >>> from music21 import *
    >>> meter.fractionSum([(3,8), (5,8), (1,8)])
    (9, 8)
    >>> meter.fractionSum([(1,6), (2,3)])
    (5, 6)
    >>> meter.fractionSum([(3,4), (1,2)])
    (5, 4)
    >>> meter.fractionSum([(1,13), (2,17)])
    (43, 221)

    '''
    nList = []
    dList = []
    nListUnique = []
    dListUnique = []

    for n,d in fList:
        nList.append(n)
        if n not in nListUnique:
            nListUnique.append(n)
        dList.append(d)
        if d not in dListUnique:
            dListUnique.append(d)

    if len(dListUnique) == 1:
        n = sum(nList)
        d = dList[0]
        return (n, d)
    else: # there might be a better way to do this
        d = 1
        d = common.lcm(dListUnique)
        # after finding d, multuple each numerator
        nShift = []
        for i in range(len(nList)):
            nSrc = nList[i]
            dSrc = dList[i]
            scalar = d / dSrc
            nShift.append(nSrc*scalar)
        return (sum(nShift), d)


def proportionToFraction(value):
    '''Given a floating point proportional value between 0 and 1, return the best-fit slash-base fraction

    >>> from music21 import *
    >>> meter.proportionToFraction(.5)
    (1, 2)
    >>> meter.proportionToFraction(.25)
    (1, 4)
    >>> meter.proportionToFraction(.75)
    (3, 4)
    >>> meter.proportionToFraction(.125)
    (1, 8)
    >>> meter.proportionToFraction(.375) 
    (3, 8)
    >>> meter.proportionToFraction(.625) 
    (5, 8)
    >>> meter.proportionToFraction(.333) 
    (1, 3)
    >>> meter.proportionToFraction(0.83333) 
    (5, 6)
    '''
    # TODO: this is a brut-force method: is there a more elegant alternative?
    for i in range(2,16+1):
        xBase = 1. / i
        for j in range(1,i+1): # take all multiples
            x = xBase * j
            if common.almostEquals(value, x, grain=1e-3):
                return (j, i)
    return None


#-------------------------------------------------------------------------------
class MeterException(Exception):
    pass

class TimeSignatureException(MeterException):
    pass


#-------------------------------------------------------------------------------
class MeterTerminal(object):
    '''A MeterTerminal is a nestable primitive of rhythmic division

    >>> from music21 import *
    >>> a = meter.MeterTerminal('2/4')
    >>> a.duration.quarterLength
    2.0
    >>> a = meter.MeterTerminal('3/8')
    >>> a.duration.quarterLength
    1.5
    >>> a = meter.MeterTerminal('5/2')
    >>> a.duration.quarterLength
    10.0

    '''
    def __init__(self, slashNotation=None, weight=1):
        self._numerator = 0 
        self._denominator = 1
        self._overriddenDuration = None

        if slashNotation != None:
            # assign directly to values, not properties, to avoid
            # calling _ratioChanged more than necessary
            self._numerator, self._denominator = slashToFraction(slashNotation)
        self._ratioChanged() # sets self._duration

        # this will call _setWeight property for data checking
        # explicitly calling base class method to avoid problems
        # in the derived class MeterSequence
        MeterTerminal._setWeight(self, weight)


    def __deepcopy__(self, memo=None):
        '''Helper method to copy.py's deepcopy function. Call it from there.

        Defining a custom __deepcopy__ here is a performance boost, particularly in not copying _duration, directly assigning _weight, and other benefits.

        >>> from copy import deepcopy
        '''
        # call class to get a new, empty instance
        new = self.__class__()
        #for name in dir(self):
        new._numerator = self._numerator
        new._denominator = self._denominator    
        new._ratioChanged() # faster than copying dur
        #new._duration = copy.deepcopy(self._duration, memo)
        new._weight = self._weight # these are numbers
        return new

    def __str__(self):
        return str(int(self.numerator)) + "/" + str(int(self.denominator))

    def __repr__(self):
        return '<MeterTerminal %s>' % self.__str__()

# now using ratioEqual()

#     def __eq__(self, other):
#         '''Equality. 
# 
#         >>> a = MeterTerminal('2/4')
#         >>> b = MeterTerminal('3/4')
#         '''
# #         if not isinstnace(other, MeterTerminal):
# #             return False
#         if other == None: return False
#         if (other.numerator == self.numerator and 
#             other.denominator == self.denominator):
#             return True
#         else:
#             return False
# 
#     def __ne__(self, other):
#         '''Inequality.
#         '''
# #         if not isinstnace(other, MeterTerminal):
# #             return True
#         if other == None: return True
#         if (other.numerator == self.numerator and 
#             other.denominator == self.denominator):
#             return False
#         else:
#             return True


    def ratioEqual(self, other):        
        '''Compare the numerator and denominator of another object.
        Note that these have to be exact matches; 3/4 is not the same as 6/8

        >>> from music21 import meter
        >>> a = meter.MeterTerminal('3/4')
        >>> b = meter.MeterTerminal('6/4')
        >>> c = meter.MeterTerminal('2/4')
        >>> d = meter.MeterTerminal('3/4')
        >>> a.ratioEqual(b)
        False
        >>> a.ratioEqual(c)
        False
        >>> a.ratioEqual(d)
        True
        '''
        if other == None: return False
        if (other.numerator == self.numerator and 
            other.denominator == self.denominator):
            return True
        else:
            return False


    #---------------------------------------------------------------------------
    def subdivideByCount(self, countRequest=None):
        '''retrun a MeterSequence

        >>> from music21 import *
        >>> a = meter.MeterTerminal('3/4')
        >>> b = a.subdivideByCount(3)
        >>> isinstance(b, meter.MeterSequence)
        True
        >>> len(b)
        3
        '''
        # elevate to meter sequence
        ms = MeterSequence()
        # cannot set the weight of this MeterSequence w/o having offsets
        # pass this MeterTerminal as an argument
        # when subdividing, use autoWeight
        ms.load(self, countRequest, autoWeight=True, targetWeight=self.weight) 
        return ms

    def subdivideByList(self, numeratorList):
        '''Return a MeterSequence
        countRequest is within the context of the beatIndex

        >>> from music21 import *
        >>> a = meter.MeterTerminal('3/4')
        >>> b = a.subdivideByList([1,1,1])
        >>> len(b)
        3
        '''
        # elevate to meter sequence
        ms = MeterSequence()
        ms.load(self) # do not need to autoWeight here
        ms.partitionByList(numeratorList) # this will split weight
        return ms    

    def subdivideByOther(self, other):
        '''Return a MeterSequence
        based on another MeterSequence

        >>> from music21 import *
        >>> a = meter.MeterSequence('1/4+1/4+1/4')
        >>> a
        <MeterSequence {1/4+1/4+1/4}>
        >>> b = meter.MeterSequence('3/8+3/8')
        >>> a.subdivideByOther(b)
        <MeterSequence {{3/8+3/8}}>
        '''
        # elevate to meter sequence
        ms = MeterSequence()
        if other.duration.quarterLength != self.duration.quarterLength:
            raise MeterException('cannot subdivide by other: %s' % other)
        ms.load(other) # do not need to autoWeight here
        #ms.partitionByOther(other) # this will split weight
        return ms    


    def subdivide(self, value):
        '''Subdivision takes a MeterTerminal and, making it into a a collection of MeterTerminals, Returns a MeterSequence.

        This is different than a partitioning a MeterSequence in that this does not happen in place and instead returns a new object.

        If an integer is provided, assume it is a partition count
        '''
        if common.isListLike(value):
            return self.subdivideByList(value)
        elif isinstance(value, MeterSequence):
            return self.subdivideByOther(value)
        elif common.isNum(value):
            return self.subdivideByCount(value)
        else:
            raise MeterException('cannot process partition argument %s' % value)



    #---------------------------------------------------------------------------
    # properties

    def _getWeight(self):
        return self._weight

    def _setWeight(self, value):
        '''
        >>> from music21 import *
        >>> a = meter.MeterTerminal('2/4')
        >>> a.weight = .5
        >>> a.weight
        0.5
        '''
#         if not common.isNum(value):
#             raise MeterException('weight values must be numbers')
        self._weight = value
    
    weight = property(_getWeight, _setWeight)


    def _getNumerator(self):
        return self._numerator

    def _setNumerator(self, value):
        '''
        >>> from music21 import *
        >>> a = meter.MeterTerminal('2/4')
        >>> a.duration.quarterLength
        2.0
        >>> a.numerator = 11
        >>> a.duration.quarterLength
        11.0
        '''
        self._numerator = value
        self._ratioChanged()

    numerator = property(_getNumerator, _setNumerator)

    def _getDenominator(self):
        return self._denominator

    def _setDenominator(self, value):
        '''
        >>> from music21 import *
        >>> a = meter.MeterTerminal('2/4')
        >>> a.duration.quarterLength
        2.0
        >>> a.numerator = 11
        >>> a.duration.quarterLength
        11.0
        ''' 
        # use duration.typeFromNumDict?
        if value not in validDenominators:
            raise MeterException('bad denominator value: %s' % value)
        self._denominator = value
        self._ratioChanged()

    denominator = property(_getDenominator, _setDenominator)


    def _ratioChanged(self):
        '''If ratio has been changed, call this to update duration 
        '''
        # NOTE: this is a performance critical method and should only be
        # called when necessary
        if self.numerator == None or self.denominator == None:
            self._duration = None
        else:
            self._duration = duration.Duration()
            try:
                self._duration.quarterLength = ((4.0 * 
                            self.numerator)/self.denominator)
            except duration.DurationException:
                environLocal.printDebug(['DurationException encountered', 
                    'numerator/denominator', self.numerator, self.denominator])
                self._duration = None

    def _getDuration(self):
        '''
        barDuration gets or sets a duration value that
        is equal in length to the totalLength
        
        >>> from music21 import *
        >>> a = meter.MeterTerminal()
        >>> a.numerator = 3
        >>> a.denominator = 8
        >>> d = a.duration
        >>> d.type
        'quarter'
        >>> d.dots
        1
        >>> d.quarterLength
        1.5
        '''
        
        if self._overriddenDuration:
            return self._overriddenDuration
        else:
            return self._duration

    def _setDuration(self, value):
        self._overriddenDuration = value

    duration = property(_getDuration, _setDuration)


    def _getDepth(self):
        '''Return how many levels deep this part is. Depth of a terminal is always 1
        '''
        return 1

    depth = property(_getDepth)




#     def _getBeatLengthToQuarterLengthRatio(self):
#         '''
#         >>> a = MeterTerminal()
#         >>> a.numerator = 3
#         >>> a.denominator = 2
#         >>> a.beatLengthToQuarterLengthRatio
#         2.0
#         '''
#         return 4.0/self.denominator
# 
#     beatLengthToQuarterLengthRatio = property(_getBeatLengthToQuarterLengthRatio)
# 
# 
#     def _getQuarterLengthToBeatLengthRatio(self):
#         return self.denominator/4.0
# 
#     quarterLengthToBeatLengthRatio = property(_getQuarterLengthToBeatLengthRatio)
# 
# 
#     def quarterPositionToBeat(self, currentQtrPosition = 0):
#         return ((currentQtrPosition * self.quarterLengthToBeatLengthRatio) + 1)
#     

















#-------------------------------------------------------------------------------
class MeterSequence(MeterTerminal):
    '''A meter sequence is a list of MeterTerminals, or other MeterSequences
    '''

    def __init__(self, value=None, partitionRequest=None):
        MeterTerminal.__init__(self)

        self._numerator = None # rationalized
        self._denominator = None # lowest common multiple 
        self._partition = [] # a list of terminals or MeterSequences
        self._overriddenDuration = None
        self._levelListCache = {}

        # this atribute is only used in MeterTermainals, and note 
        # in MeterSequences; a MeterSequences weight is based solely
        # on the sum of its components
        del self._weight

        # store whether this meter was provided as a summed nuemerator
        self.summedNumerator = False 
        # an optional parameter used only in displaying this meter sq
        # needed in cases where a meter component is parenthetical 
        self.parenthesis = False

        if value != None:
            self.load(value, partitionRequest)

    def __deepcopy__(self, memo=None):
        '''Helper method to copy.py's deepcopy function. Call it from there.

        Defining a custom __deepcopy__ here is a performance boost, particularly in not copying _duration and other benefits. Notably, self._levelListCache is not copied, with may not be needed in the copy and may be large. 

        >>> from copy import deepcopy
        '''
        # call class to get a new, empty instance
        new = self.__class__()
        #for name in dir(self):
        new._numerator = self._numerator
        new._denominator = self._denominator    
        new._partition = copy.deepcopy(self._partition, memo)
        new._ratioChanged() # faster than copying dur
        #new._duration = copy.deepcopy(self._duration, memo)

        new._overriddenDuration = self._overriddenDuration   
        new.summedNumerator = self.summedNumerator 
        new.parenthesis = self.parenthesis 

        return new

    def __str__(self):
        msg = []
        for mt in self._partition:
            msg.append(str(mt))
        return '{%s}' % '+'.join(msg)

    def __repr__(self):
        return '<MeterSequence %s>' % self.__str__()

    def __len__(self):
        '''Return the length of the partition list
       
        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4', 4)
        >>> len(a)
        4
        '''
        return len(self._partition)

    def __iter__(self):
        '''Support iteration of top level partitions
        '''
        return common.Iterator(self._partition)

    def __getitem__(self, key):
        '''Get an MeterTerminal from _partition

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4', 4)
        >>> a[3].numerator
        1
        '''
        if abs(key) >= self.__len__():
            raise IndexError
        else:
            return self._partition[key]

    def __setitem__(self, key, value):
        '''Insert items at index positions.

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4', 4)
        >>> a[0] = a[0].subdivide(2)
        >>> a
        <MeterSequence {{1/8+1/8}+1/4+1/4+1/4}>
        >>> a[0][0] = a[0][0].subdivide(2)
        >>> a
        <MeterSequence {{{1/16+1/16}+1/8}+1/4+1/4+1/4}>
        >>> a[3] = a[0][0].subdivide(2)
        Traceback (most recent call last):
        ...
        MeterException: cannot insert {1/16+1/16} into space of 1/4
        '''
        # comparison of numerator and denominator
        if not isinstance(value, MeterTerminal):
            raise MeterException('values in MeterSequences must be MeterTerminals or MeterSequences, not %s' % value)
        if value.ratioEqual(self[key]): 
            self._partition[key] = value
        else:    
            raise MeterException('cannot insert %s into space of %s' % (value, self[key]))

        # clear cache
        self._levelListCache = {}

    #---------------------------------------------------------------------------
    # load common meter templates into this sequence

    def _divisionOptionsAlgo(self, n, d):
        '''
        This is a primitive approach to algorithmic division production.
        This can be extended.
       
        It is assumed that these values are provided in order of priority

        >>> from music21 import *
        >>> a = meter.MeterSequence()
        >>> a._divisionOptionsAlgo(4,4)
        [['1/4', '1/4', '1/4', '1/4'], ['1/2', '1/2'], ['4/4'], ['2/4', '2/4'], ['2/2'], ['1/1'], ['8/8'], ['16/16'], ['32/32'], ['64/64'], ['128/128']]

        >>> a._divisionOptionsAlgo(1,4)
        [['1/4'], ['1/8', '1/8'], ['1/16', '1/16', '1/16', '1/16'], ['1/32', '1/32', '1/32', '1/32', '1/32', '1/32', '1/32', '1/32'], ['1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64'], ['1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128', '1/128'], ['2/8'], ['4/16'], ['8/32'], ['16/64'], ['32/128']]

        >>> a._divisionOptionsAlgo(2,2)
        [['1/2', '1/2'], ['2/2'], ['1/1'], ['4/4'], ['8/8'], ['16/16'], ['32/32'], ['64/64'], ['128/128']]

        >>> a._divisionOptionsAlgo(3,8)
        [['1/8', '1/8', '1/8'], ['3/8'], ['6/16'], ['12/32'], ['24/64'], ['48/128']]

        >>> a._divisionOptionsAlgo(6,8)
        [['3/8', '3/8'], ['1/8', '1/8', '1/8', '1/8', '1/8', '1/8'], ['1/4', '1/4', '1/4'], ['6/8'], ['3/4'], ['12/16'], ['24/32'], ['48/64'], ['96/128']]

        >>> a._divisionOptionsAlgo(12,8)
        [['3/8', '3/8', '3/8', '3/8'], ['1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8'], ['1/4', '1/4', '1/4', '1/4', '1/4', '1/4'], ['1/2', '1/2', '1/2'], ['12/8'], ['6/8', '6/8'], ['6/4'], ['3/2'], ['24/16'], ['48/32'], ['96/64'], ['192/128']]

        >>> a._divisionOptionsAlgo(5,8)
        [['2/8', '3/8'], ['3/8', '2/8'], ['1/8', '1/8', '1/8', '1/8', '1/8'], ['5/8'], ['10/16'], ['20/32'], ['40/64'], ['80/128']]


        >>> a._divisionOptionsAlgo(18,4)
        [['3/4', '3/4', '3/4', '3/4', '3/4', '3/4'], ['1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4', '1/4'], ['1/2', '1/2', '1/2', '1/2', '1/2', '1/2', '1/2', '1/2', '1/2'], ['18/4'], ['9/4', '9/4'], ['4/4', '4/4', '4/4', '4/4'], ['2/4', '2/4', '2/4', '2/4', '2/4', '2/4', '2/4', '2/4'], ['9/2'], ['36/8'], ['72/16'], ['144/32'], ['288/64'], ['576/128']]

        '''
        opts = []

        # compound meters; 6, 9, 12, 15, 18
        # 9/4, 9/2, 6/2 are all considered compound without d>4
        #if n % 3 == 0 and n > 3 and d > 4:
        if n % 3 == 0 and n > 3:
            nMod = n / 3
            seq = []
            for x in range(n/3):
                seq.append('%s/%s' % (3, d))
            opts.append(seq)

        # odd meters with common groupings
        if n == 5:
            for group in [[2,3], [3,2]]:
                seq = []
                for nMod in group:
                    seq.append('%s/%s' % (nMod, d))
                opts.append(seq)

        if n == 7:
            for group in [[2,2,3], [3,2,2], [2,3,2]]:
                seq = []
                for nMod in group:
                    seq.append('%s/%s' % (nMod, d))
                opts.append(seq)

        # not really necessary but an example of a possibility
        if n == 10:
            for group in [[2,2,3,3]]:
                seq = []
                for nMod in group:
                    seq.append('%s/%s' % (nMod, d))
                opts.append(seq)

        # simple additive options uses the minimum numerator of 1
        if n > 1 and d >= 1:
            seq = []
            for x in range(n):
                seq.append('%s/%s' % (1, d))    
            opts.append(seq)

        # divided additive multiples
        if n % 2 == 0 and d / 2 >= 1:
            nMod = n / 2
            dMod = d / 2
            while True:
                if dMod < 1 or nMod <= 1:
                    break
                seq = []
                for x in range(nMod):
                    seq.append('%s/%s' % (1, dMod))    
                opts.append(seq)
                if nMod % 2 != 0: # if no longer even must stop
                    break
                dMod = dMod / 2
                nMod = nMod / 2

        # add src representation
        opts.append(['%s/%s' % (n,d)])

        # additive multiples with the same denominators
        # numerators must be even, do not take numerator to 1
        if n > 3 and n % 2 == 0:
            i = 2
            nMod = n / 2
            while True:
                if nMod <= 1:
                    break
                seq = []
                for x in range(i):
                    seq.append('%s/%s' % (nMod, d))  
                if seq not in opts:  # may be cases defined elsewhere 
                    opts.append(seq)
                nMod = nMod / 2
                i *= 2

        # additive multiples with smaller denominators
        # only doing this for numerators of 1 for now
        if d < validDenominators[-1] and n == 1:
            i = 2
            dMod = d * 2
            while True:
                if dMod > validDenominators[-1]:
                    break
                seq = []
                for x in range(i):
                    seq.append('%s/%s' % (n, dMod))    
                opts.append(seq)
                dMod = dMod * 2
                i *= 2
                  
        # equivalent fractions downward
        if d > validDenominators[0] and n % 2 == 0:
            nMod = n / 2
            dMod = d / 2
            while True:
                if dMod < validDenominators[0]:
                    break
                opts.append(['%s/%s' % (nMod, dMod)])    
                if nMod % 2 != 0: # no longer even
                    break
                dMod = dMod / 2
                nMod = nMod / 2

        # equivalent fractions upward
        if d < validDenominators[-1]:
            nMod = n * 2
            dMod = d * 2
            while True:
                if dMod > validDenominators[-1]:
                    break
                opts.append(['%s/%s' % (nMod, dMod)])    
                dMod = dMod * 2
                nMod = nMod * 2

        return opts            


    def _divisionOptionsPreset(self, n, d):
        '''Provide fixed set of meter divisions that will not be  easily 
        obtained algorithmically
        '''
        opts = []
        return opts


    #---------------------------------------------------------------------------
    def _clearPartition(self):
        '''This will not sync with .numerator and .denominator if called alone
        '''
        self._partition = [] 
        # clear cache
        self._levelListCache = {}

    def _addTerminal(self, value):
        '''Add a an object to the partition list. This does not update numerator and denominator.

        targetWeight is the expected total Weight for this MeterSequence. This
        would be self.weight, but offten partitions are cleared before _addTerminal is called. 
        '''
        # NOTE: this is a performance critical method

        if isinstance(value, MeterTerminal): # may be a MeterSequence
            mt = value
        else: # assume it is a string
            mt = MeterTerminal(value)

#         if common.isStr(value):
#             mt = MeterTerminal(value)
#         elif isinstance(value, MeterTerminal): # may be a MeterSequence
#             mt = value
#         else:
#             raise MeterException('cannot add %s to this sequence' % value)
        self._partition.append(mt)
        # clear cache
        self._levelListCache = {}


    def _getOptions(self):
        # all-string python dictionaries are optimized; use string key
        n = int(self.numerator)
        d = int(self.denominator)
        tsStr = '%s/%s' % (n, d)
        try: 
            # return a stored, cached value
            return _meterSequenceDivisionOptions[tsStr]
        except KeyError:
            opts = []
            opts += self._divisionOptionsAlgo(n, d)
            opts += self._divisionOptionsPreset(n, d)
            # store for access later
            _meterSequenceDivisionOptions[tsStr] = opts
        return opts


    #---------------------------------------------------------------------------
    def partitionByCount(self, countRequest, loadDefault=True):
        '''This will destroy any structure in the _partition

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4')
        >>> a.partitionByCount(2)
        >>> str(a)
        '{1/2+1/2}'
        >>> a.partitionByCount(4)
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'
        '''
        opts = self._getOptions()
        optMatch = None
        # get the first encountered load string with the desired
        # number of beats
        if countRequest != None:
            for opt in opts:
                if len(opt) == countRequest:
                    optMatch = opt
                    break

        # if no matches this method provides a deafult
        if optMatch == None and loadDefault: 
            optMatch = opts[0]
            
        if optMatch != None:
            targetWeight = self.weight
            #environLocal.printDebug(['partitionByCount, targetWeight', targetWeight])
            self._clearPartition() # weight will now be zero
            for mStr in optMatch:
                self._addTerminal(mStr)
            self.weight = targetWeight
        else:
            raise MeterException('Cannot set partition by %s (%s/%s)' % (countRequest, self.numerator, self.denominator))

        # clear cache
        self._levelListCache = {}

    def partitionByList(self, numeratorList):
        '''Given a numerator list, partition MeterSequence inot a new list
        of MeterTerminals

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4')
        >>> a.partitionByList([1,1,1,1])
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'
        >>> a.partitionByList(['3/4', '1/8', '1/8'])
        >>> a
        <MeterSequence {3/4+1/8+1/8}>
        >>> a.partitionByList(['3/4', '1/8', '5/8'])
        Traceback (most recent call last):
        MeterException: Cannot set partition by ['3/4', '1/8', '5/8']

        '''
        # assume a list of terminal definitions
        if common.isStr(numeratorList[0]):        
            test = MeterSequence()
            for mtStr in numeratorList:
                test._addTerminal(mtStr)
            test._updateRatio()
            # if durations are equal, this can be used as a partition
            if self.duration.quarterLength == test.duration.quarterLength:
                optMatch = test
            else:
                raise MeterException('Cannot set partition by %s' % numeratorList)

        elif sum(numeratorList) in [self.numerator * x for x in range(1,9)]:
            for i in range(1, 9):
                if sum(numeratorList) == self.numerator * i:
                    optMatch = []
                    for n in numeratorList:
                        optMatch.append('%s/%s' % (n, self.denominator * i))
                    break

        # last resort: search options
        else: 
            opts = self._getOptions()
            optMatch = None
            for opt in opts:
                # get numerators as numbers
                nFound = [int(x.split('/')[0]) for x in opt]
                if nFound == numeratorList:
                    optMatch = opt
                    break

        # if a n/d match, now set this MeterSequence
        if optMatch != None:
            targetWeight = self.weight
            self._clearPartition() # clears self.weight
            for mStr in optMatch:
                self._addTerminal(mStr)
            self.weight = targetWeight
        else:
            raise MeterException('Cannot set partition by %s (%s/%s)' % (numeratorList, self.numerator, self.denominator))

        # clear cache
        self._levelListCache = {}


    def partitionByOther(self, other):
        '''Set partition to that found in another object

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4', 4)
        >>> b = meter.MeterSequence('4/4', 2)
        >>> a.partitionByOther(b)
        >>> len(a)
        2
        '''       
        if (self.numerator == other.numerator and 
            self.denominator == other.denominator):

            targetWeight = self.weight
            self._clearPartition()
            for mt in other:
                self._addTerminal(copy.deepcopy(mt))
            self.weight = targetWeight
        else:
            raise MeterException('Cannot set partition for unequal MeterSequences')

        # clear cache
        self._levelListCache = {}


    def partition(self, value):
        ''' Partitioning creates and sets a number of MeterTerminals that make up this MeterSequence.

        A simple way to partition based on argument time. Single integers are treated as beat counts; lists are treated as numerator lists; MeterSequence objects are call partitionByOther(). 

        >>> from music21 import *
        >>> a = meter.MeterSequence('5/4+3/8')
        >>> len(a)
        2
        >>> b = meter.MeterSequence('13/8')
        >>> len(b)
        1
        >>> b.partition(13)
        >>> len(b)
        13
        >>> a.partition(b)
        >>> len(a)
        13
        '''
        if common.isListLike(value):
            self.partitionByList(value)
        elif isinstance(value, MeterSequence):
            self.partitionByOther(value)
        elif common.isNum(value):
            self.partitionByCount(value, loadDefault=False)
        else:
            raise MeterException('cannot process partition arguemtn %s' % value)


    def subdividePartitionsEqual(self, divisions=None):
        '''Subdivide all partitions by equally-spaced divisions, given a divisions value. Manipulates this MeterSequence in place.

        Divisions value may optionally be a MeterSequence, from which a top-level partitioning structure is derived.

        >>> from music21 import *
        >>> ms = meter.MeterSequence('2/4')
        >>> ms.partition(2)
        >>> ms
        <MeterSequence {1/4+1/4}>
        >>> ms.subdividePartitionsEqual(2)
        >>> ms
        <MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> ms[0].subdividePartitionsEqual(2)
        >>> ms
        <MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{1/8+1/8}}>
        >>> ms[1].subdividePartitionsEqual(2)
        >>> ms
        <MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}>

        >>> ms = meter.MeterSequence('2/4+3/4')
        >>> ms.subdividePartitionsEqual(None)

        '''
        for i in range(len(self)):
            if divisions == None: # get dynamically
                if self[i].numerator in [1, 2, 4, 8, 16]:
                    divisionsLocal = 2
                elif self[i].numerator in [3]:
                    divisionsLocal = 3
                elif self[i].numerator in [6, 9, 12, 15, 18]:
                    divisionsLocal = self[i].numerator / 3
                else:
                    divisionsLocal = self[i].numerator
            else:
                divisionsLocal = divisions
            #environLocal.printDebug(['got divisions:', divisionsLocal, 'for numerator', self[i].numerator, 'denominator', self[i].denominator])
            self[i] = self[i].subdivide(divisionsLocal)

        # clear cache
        self._levelListCache = {}

    def _subdivideNested(self, processObjList, divisions):
        '''Recursive nested call routine. Return a reference to the newly created level.

        >>> from music21 import *
        >>> ms = meter.MeterSequence('2/4')
        >>> ms.partition(2)
        >>> ms
        <MeterSequence {1/4+1/4}>
        >>> post = ms._subdivideNested([ms], 2)
        >>> ms
        <MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> post = ms._subdivideNested(post, 2) # pass post here
        >>> ms
        <MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}>
        '''
        for obj in processObjList:
            obj.subdividePartitionsEqual(divisions)
        # gather references for recursive processing
        post = []
        for obj in processObjList:
            for sub in obj:
                post.append(sub)
        # clear cache
        self._levelListCache = {}
        return post


    def subdivideNestedHierarchy(self, depth, firstPartitionForm=None, 
            normalizeDenominators=True):
        '''Create nested structure down to a specified depth; the first division is set to one; the second division may be by 2 or 3; remaining divisions are always by 2.

        This a destructive procedure that will remove any existing partition structures. 

        `normalizeDenominators`, if True, will reduce all denominators to the same minimum level. 

        >>> from music21 import *
        >>> ms = meter.MeterSequence('4/4')
        >>> ms.subdivideNestedHierarchy(1)
        >>> ms
        <MeterSequence {{1/2+1/2}}>
        >>> ms.subdivideNestedHierarchy(2)
        >>> ms
        <MeterSequence {{{1/4+1/4}+{1/4+1/4}}}>
        >>> ms.subdivideNestedHierarchy(3)
        >>> ms
        <MeterSequence {{{{1/8+1/8}+{1/8+1/8}}+{{1/8+1/8}+{1/8+1/8}}}}>
        >>> ms.subdivideNestedHierarchy(4)
        >>> ms
        <MeterSequence {{{{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}+{{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}}}>
        >>> ms.subdivideNestedHierarchy(5)
        >>> ms
        <MeterSequence {{{{{{1/32+1/32}+{1/32+1/32}}+{{1/32+1/32}+{1/32+1/32}}}+{{{1/32+1/32}+{1/32+1/32}}+{{1/32+1/32}+{1/32+1/32}}}}+{{{{1/32+1/32}+{1/32+1/32}}+{{1/32+1/32}+{1/32+1/32}}}+{{{1/32+1/32}+{1/32+1/32}}+{{1/32+1/32}+{1/32+1/32}}}}}}>

        '''
        # as a hierarchical representation, zeroth subdivision must be 1
        self.partition(1)
        depthCount = 0

        # initial divisions are often based on numerator or are provided
        # by looking at the number of top-level beat partitions
        # thus, 6/8 will have 2, 18/4 should have 5
        if isinstance(firstPartitionForm, MeterSequence):
            # change self in place, as we cannot re-assign to self
            #self = self.subdivideByOther(firstPartitionForm.getLevel(0))
            self.load(firstPartitionForm.getLevel(0))
            depthCount += 1
        else: # can be just a number
            if firstPartitionForm == None: 
                firstPartitionForm = self.numerator
            # use a fixed mapping for first divider; may be a good algo solution
            if firstPartitionForm in [1, 2, 4, 8, 16, 32]:
                divFirst = 2
            elif firstPartitionForm in [3]:
                divFirst = 3
    #             elif firstPartitionForm in [6, 9, 12, 15, 18]:
    #                 divFirst = firstPartitionForm / 3
            # otherwise, set the first div to the number of beats; in 18/4
            # this should be 6
            else: # set to numerator
                divFirst = firstPartitionForm

            # use partitions equal, divide by number
            self.subdividePartitionsEqual(divFirst)
            # self[h] = self[h].subdivide(divFirst)
            depthCount += 1

#         environLocal.printDebug(['subdivideNestedHierarchy(): firstPartitionForm:', firstPartitionForm, ': self: ', self])

        # all other partitions are recursive; start first with list
        post = [self[0]]
        while (depthCount < depth):
            # setting divisions to None will get either 2/3 for all components
            post = self._subdivideNested(post, divisions=None)
            depthCount += 1
            # need to detect cases of inequal denominators
            if normalizeDenominators:
                while True:
                    d = []
                    for ref in post:
                        if ref.denominator not in d:
                            d.append(ref.denominator)
                    # if we have more than one denominator; we need to normalize
                    #environLocal.printDebug(['subdivideNestedHierarchy():', 'd',  d, 'post', post, 'depthCount', depthCount])
                    if len(d) > 1: 
                        postNew = []
                        for i in range(len(post)):
                            # if this is a lower denominator (1/4 not 1/8), 
                            # process again
                            if post[i].denominator == min(d):
                                postNew += self._subdivideNested([post[i]], 
                                           divisions=None)
                            else: # keep original if no problem
                                postNew.append(post[i])
                        post = postNew # reassing to original
                    else:
                        break

        # clear cache; done in self._subdivideNested and possibly not
        # needed here
        self._levelListCache = {}

        #environLocal.printDebug(['subdivideNestedHierarchy(): post nested processing:',  self])


    #---------------------------------------------------------------------------
    def _getPartitionStr(self):
        count = len(self) 
        if count == 1:
            return 'Single'
        elif count == 2:
            return 'Duple'
        elif count == 3:
            return 'Triple'
        elif count == 4:
            return 'Quadruple'
        elif count == 5:
            return 'Quintuple'
        elif count == 6:
            return 'Sextuple'
        elif count == 7:
            return 'Septuple'
        elif count == 8:
            return 'Octuple'
        else:
            return None

    partitionStr = property(_getPartitionStr, 
        doc = '''Return the number of top-level partitions in this MeterSequence as a string. 

        >>> from music21 import *
        >>> ms = meter.MeterSequence('2/4+2/4')
        >>> ms
        <MeterSequence {2/4+2/4}>
        >>> ms.partitionStr
        'Duple'
        >>> ms = meter.MeterSequence('6/4', 6)
        >>> ms
        <MeterSequence {1/4+1/4+1/4+1/4+1/4+1/4}>
        >>> ms.partitionStr
        'Sextuple'

        ''')




    #---------------------------------------------------------------------------
    # loading is always destructive

    def load(self, value, partitionRequest=None, autoWeight=False,
            targetWeight=None):
        '''This method is called when a MeterSequence is created, or if a MeterSequece is re-set. 

        User can enter a list of values or an abbreviated slash notation.

        autoWeight, if True, will attempt to set weights.
        tragetWeight, if given, will be used instead of self.weight        

        >>> from music21 import *
        >>> a = meter.MeterSequence()
        >>> a.load('4/4', 4)
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        >>> a.load('4/4', 2) # request 2 beats
        >>> str(a)
        '{1/2+1/2}'

        >>> a.load('5/8', 2) # request 2 beats
        >>> str(a)
        '{2/8+3/8}'

        >>> a.load('5/8+4/4') 
        >>> str(a)
        '{5/8+4/4}'

        '''
        # NOTE: this is a performance critical method
        if autoWeight:
            if targetWeight != None:
                targetWeight = targetWeight
            else: # get from current MeterSequence
                targetWeight = self.weight # store old
        else: # None will not set any value
            targetWeight = None

        #environLocal.printDebug(['calling load in MeterSequence, got targetWeight', targetWeight])
        self._clearPartition()

        if common.isStr(value):
            ratioList, self.summedNumerator = slashMixedToFraction(value)
            for n,d in ratioList:
                slashNotation = '%s/%s' % (n,d)
                self._addTerminal(MeterTerminal(slashNotation)) 
            self._updateRatio()
            self.weight = targetWeight # may be None

        elif isinstance(value, MeterTerminal):
            # if we have a singel MeterTerminal and autoWeight is active
            # set this terminal to the old weight
            if targetWeight != None:
                value.weight = targetWeight
            self._addTerminal(value) 
            self._updateRatio()
            # do not need to set weight, as based on terminal
            #environLocal.printDebug(['created MeterSequence from MeterTerminal; old weight, new weight', value.weight, self.weight])
    
        elif common.isListLike(value): # a list of Terminals or Sequenc es
            for obj in value:
                #environLocal.printDebug('creating MeterSequence with %s' % obj)
                self._addTerminal(obj) 
            self._updateRatio()
            self.weight = targetWeight # may be None
        else:
            raise MeterException('cannot create a MeterSequence with a %s' % repr(value))

        if partitionRequest != None:
            self.partition(partitionRequest)

        # clear cache
        self._levelListCache = {}

    
    def _updateRatio(self):
        '''Look at _partition to determine the total
        numerator and denominator values for this sequence

        This should only be called internally, as MeterSequences
        are supposed to be immutable (mostly)
        '''
        fList = [(mt.numerator, mt.denominator) for mt in self._partition]
        # clear first to avoid partial updating
        # can only set to private attributes
        #self._numerator, self._denominator = None, 1            
        self._numerator, self._denominator = fractionSum(fList)
        # must call ratio changed directly as not using properties
        self._ratioChanged()



    #---------------------------------------------------------------------------
    # properties
    # do not permit setting of numerator/denominator

    def _getWeight(self):
        '''
        >>> from music21 import *
        >>> a = meter.MeterSequence('3/4')
        >>> a.partition(3)
        >>> a.weight = 1
        >>> a[0].weight
        0.333...
        >>> b = meter.MeterTerminal('1/4', .25)
        >>> c = meter.MeterTerminal('1/4', .25)
        >>> d = meter.MeterSequence([b, c])
        >>> d.weight
        0.5
        '''
        sum = 0
        for obj in self._partition:
            sum += obj.weight # may be a MeterTerminal or MeterSequence
        return sum

    def _setWeight(self, value):
        '''Assume this MeterSequence is a whole, not a part of some larger MeterSequence. Thus, we cannot use numerator/denominator relationship
        as a scalar. 
        '''
        #environLocal.printDebug(['calling setWeight with value', value])

        if value == None:
            pass # do nothing
        else:
            if not common.isNum(value):
                raise MeterException('weight values must be numbers')
            totalRatio = self._numerator / float(self._denominator)
            for mt in self._partition:
            #for mt in self:
                partRatio = mt._numerator / float(mt._denominator)
                mt.weight = value * (partRatio/totalRatio)
                #mt.weight = (partRatio/totalRatio) #* totalRatio
                #environLocal.printDebug(['setting weight based on part, total, weight', partRatio, totalRatio, mt.weight])
    
    weight = property(_getWeight, _setWeight)



    def _getNumerator(self):
        return self._numerator

    numerator = property(_getNumerator, None)

    def _getDenominator(self):
        return self._denominator

    denominator = property(_getDenominator, None)


    def _getFlatList(self):
        '''Retern a flat version of this MeterSequence as a list of MeterTerminals.

        This return a list and not a new MeterSequence b/c MeterSequence objects are generally immutable and thus it does not make sense
        to concatenate them.

        >>> from music21 import *
        >>> a = meter.MeterSequence('3/4')
        >>> a.partition(3)
        >>> b = a._getFlatList()
        >>> len(b)
        3

        >>> a[1] = a[1].subdivide(4)
        >>> a
        <MeterSequence {1/4+{1/16+1/16+1/16+1/16}+1/4}>
        >>> len(a)
        3
        >>> b = a._getFlatList()
        >>> len(b)
        6

        >>> a[1][2] = a[1][2].subdivide(4)
        >>> a
        <MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = a._getFlatList()
        >>> len(b)
        9

        '''
        mtList = []
        for obj in self._partition:
            if not isinstance(obj, MeterSequence):
                mtList.append(obj)
            else: # its a meter sequence
                mtList += obj._getFlatList()
        return mtList

    def _getFlat(self):
        '''Retrun a new MeterSequence composed of the flattend representation.

        >>> from music21 import *
        >>> a = meter.MeterSequence('3/4', 3)
        >>> b = a.flat
        >>> len(b)
        3

        >>> a[1] = a[1].subdivide(4)
        >>> b = a.flat
        >>> len(b)
        6

        >>> a[1][2] = a[1][2].subdivide(4)
        >>> a
        <MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = a.flat
        >>> len(b)
        9

        '''
        post = MeterSequence()
        post.load(self._getFlatList())
        return post

    flat = property(_getFlat)

    def _getFlatWeight(self):
        '''Retrun a list of flat weight valuess

        '''
        post = []
        for mt in self._getFlatList():
            post.append(mt.weight)
        return post

    flatWeight = property(_getFlatWeight)


    def _getDepth(self):
        '''Return how many unique levels deep this part is
        
        This should be optimized to store values unless the structure has changed.
        '''
        depth = 0 # start with 0, will count this level
    
        lastMatch = None
        while True:
            test = self._getLevelList(depth)
            if test != lastMatch:
                depth += 1
                lastMatch = test
            else:
                break
        return depth

    depth = property(_getDepth)



    def isUniformPartition(self, depth=0):
        '''Return True if the top-level partitions have equal durations

        >>> from music21 import *
        >>> ms = meter.MeterSequence('3/8+2/8+3/4')
        >>> ms.isUniformPartition()
        False
        >>> ms = meter.MeterSequence('4/4')
        >>> ms.isUniformPartition()
        True
        >>> ms = meter.MeterSequence('2/4+2/4')
        >>> ms.isUniformPartition()
        True
        '''
        n = []
        d = []
        for ms in self._getLevelList(depth):
            if ms.numerator not in n:
                n.append(ms.numerator)
            if ms.denominator not in d:
                d.append(ms.denominator)
            # as soon as we have more than on entry, we do not have unform
            if len(n) > 1 or len(d) > 1:
                return False
        return True


    #---------------------------------------------------------------------------
    # alternative representations

    def _getLevelList(self, levelCount, flat=True):
        '''Recursive utility function

        >>> from music21 import *
        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> meter.MeterSequence(b._getLevelList(0))
        <MeterSequence {1/4+1/4+1/4+1/4}>
        >>> meter.MeterSequence(b._getLevelList(1))
        <MeterSequence {1/4+1/8+1/8+1/4+1/8+1/8}>
        >>> meter.MeterSequence(b._getLevelList(2))
        <MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        >>> meter.MeterSequence(b._getLevelList(3))
        <MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        '''
        cacheKey = (levelCount, flat)
        try: # check in cache 
            return self._levelListCache[cacheKey]
        except KeyError:
            pass

        mtList = []
        for i in range(len(self._partition)):
            #environLocal.printDebug(['_getLevelList weight', i, self[i].weight])
            if not isinstance(self._partition[i], MeterSequence):
                mt = self[i] # a meter terminal
                mtList.append(mt)   
            else: # its a sequence
                if levelCount > 0: # retain this sequence but get lower level
                    # reduce level by 1 when recursing; do not
                    # change levelCount here
                    mtList += self._partition[i]._getLevelList(
                                levelCount-1, flat)
                else: # level count is at zero
                    if flat: # make sequence into a terminal
                        mt = MeterTerminal('%s/%s' % (
                                  self._partition[i]._numerator, self._partition[i]._denominator))
                        # set weight to that of the sequence
                        mt.weight = self._partition[i].weight
                        mtList.append(mt)   
                    else: # its not a terminal, its a meter sequence
                        mtList.append(self._partition[i])   
        # store in cache
        self._levelListCache[cacheKey] = mtList
        return mtList


    def getLevel(self, level=0, flat=True):
        '''Return a complete MeterSequence with the same numerator/denominator
        reationship but that represents any partitions found at the rquested
        level. A sort of flatness with variable depth.
        
        >>> from music21 import *
        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevel(0)
        <MeterSequence {1/4+1/4+1/4+1/4}>
        >>> b.getLevel(1)
        <MeterSequence {1/4+1/8+1/8+1/4+1/8+1/8}>
        >>> b.getLevel(2)
        <MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        '''
        return MeterSequence(self._getLevelList(level, flat))

    def getLevelSpan(self, level=0):
        '''For a given level, return the time span of each terminal or sequnece

        >>> from music21 import *
        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelSpan(0)
        [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0)]
        >>> b.getLevelSpan(1)
        [(0.0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 3.5), (3.5, 4.0)]
        >>> b.getLevelSpan(2)
        [(0.0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 3.25), (3.25, 3.5), (3.5, 4.0)]
        ''' 
        ms = self._getLevelList(level, flat=True)
        map = []
        pos = 0.0

        for i in range(len(ms)):
            start = pos
            end = pos + ms[i].duration.quarterLength
            map.append((start, end))
            pos += ms[i].duration.quarterLength
        return map


    def getLevelWeight(self, level=0):
        '''The weightList is an array of weights found in the components.
        The MeterSequence has a ._weight attribute, but it is not used here

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4', 4)
        >>> a.getLevelWeight()
        [0.25, 0.25, 0.25, 0.25]

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]

        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]

        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]
        >>> b.getLevelWeight(1)
        [0.25, 0.125, 0.125, 0.25, 0.125, 0.125]
        >>> b.getLevelWeight(2)
        [0.25, 0.125, 0.125, 0.25, 0.0625, 0.0625, 0.125]
        '''
        post = []
        for mt in self._getLevelList(level):
            post.append(mt.weight)
        return post

    
    def setLevelWeight(self, weightList, level=0):
        '''The `weightList` is an array of weights to be applied to a single level of the MeterSequence..

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4', 4)
        >>> a.setLevelWeight([1, 2, 3, 4])
        >>> a.getLevelWeight()
        [1, 2, 3, 4]

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b.setLevelWeight([2, 3])
        >>> b.getLevelWeight(0)
        [2, 3, 2, 3]

        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b.getLevelWeight(0)
        [2, 3.0, 2, 3.0]

        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelWeight(0)
        [2, 3.0, 2, 3.0]
        >>> b.getLevelWeight(1)
        [2, 1.5, 1.5, 2, 1.5, 1.5]
        >>> b.getLevelWeight(2)
        [2, 1.5, 1.5, 2, 0.75, 0.75, 1.5]
        '''
        levelObjs = self._getLevelList(level)
        for i in range(len(levelObjs)):
            mt = levelObjs[i]
            mt.weight = weightList[i%len(weightList)]


    #---------------------------------------------------------------------------
    # given a quarter note position, return the active index

    def positionToIndex(self, qLenPos, includeCoincidentBoundaries=False):
        '''Given a qLen pos (0 through self.duration.quarterLength), return
        the index of the active MeterTerminal or MeterSequence

        >>> from music21 import *
        >>> a = meter.MeterSequence('4/4')
        >>> a.positionToIndex(5)
        Traceback (most recent call last):
        ...
        MeterException: cannot access from qLenPos 5 where total duration is 4.0

        >>> a = MeterSequence('4/4')
        >>> a.positionToIndex(.5)
        0
        >>> a.positionToIndex(3.5)
        0
        >>> a.partition(4)
        >>> a.positionToIndex(0.5)
        0
        >>> a.positionToIndex(3.5)
        3
        >>> a.partition([1,2,1])
        >>> len(a)
        3
        >>> a.positionToIndex(2.9)
        1
        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException('cannot access from qLenPos %s where total duration is %s' % (qLenPos, self.duration.quarterLength))

        qPos = 0
        match = None
        for i in range(len(self)):
            start = qPos        
            end = qPos + self[i].duration.quarterLength
            # if adjoing ends are permitted, first match is found
            if includeCoincidentBoundaries:
                if qLenPos >= start and qLenPos <= end:
                    match = i
                    break
            else:    
                # note that this is >=, meaning that the first boundary
                # is coincident
                if (common.greaterThanOrEqual(qLenPos, start) and
                    common.lessThan(qLenPos, end)):
#                if qLenPos >= start and qLenPos < end:
                    match = i
                    break
            qPos += self[i].duration.quarterLength
        return match


    def positionToAddress(self, qLenPos, includeCoincidentBoundaries=False):
        '''Give a list of values that show all indices necessary to access
        the exact terminal at a given qLenPos.

        The len of the returned list also provides the depth at the specified qLen. 

        >>> from music21 import *
        >>> a = meter.MeterSequence('3/4', 3)
        >>> a[1] = a[1].subdivide(4)
        >>> a
        <MeterSequence {1/4+{1/16+1/16+1/16+1/16}+1/4}>
        >>> len(a)
        3
        >>> a.positionToAddress(.5)
        [0]
        >>> a[0]    
        <MeterTerminal 1/4>
        >>> a.positionToAddress(1.0)
        [1, 0]
        >>> a.positionToAddress(1.5)
        [1, 2]
        >>> a[1][2]
        <MeterTerminal 1/16>
        >>> a.positionToAddress(1.99)
        [1, 3]
        >>> a.positionToAddress(2.5)
        [2]

        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException('cannot access from qLenPos %s' % qLenPos)

        qPos = 0
        match = []
        for i in range(len(self)):
            start = qPos        
            end = qPos + self[i].duration.quarterLength
            # if adjoing ends are permitted, first match is found
            if includeCoincidentBoundaries:
                if qLenPos >= start and qLenPos <= end:
                    match.append(i)
                    break
            else:    
                if qLenPos >= start and qLenPos < end:
                    match.append(i)
                    break
            qPos += self[i].duration.quarterLength

        if isinstance(self[i], MeterSequence): # recurse
            # qLenPositin needs to be relative to this subidivison
            # start is our current position that this subdivision 
            # starts at
            qLenPosShift = qLenPos - start
            match += self[i].positionToAddress(qLenPosShift, 
                     includeCoincidentBoundaries)

        return match


    def positionToSpan(self, qLenPos):
        '''Given a lenPos, return the span of the active region.
        Only applies to the top most level of partitions

        >>> from music21 import *
        >>> a = meter.MeterSequence('3/4', 3)
        >>> a.positionToSpan(.5)
        (0, 1.0)
        >>> a.positionToSpan(1.5)
        (1.0, 2.0)

        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            #environLocal.printDebug(['exceeding range:', self, 'self.duration', self.duration])
            raise MeterException('cannot access qLenPos %s when total duration is %s and ts is %s' % (qLenPos, self.duration.quarterLength, self))
        
        iMatch = self.positionToIndex(qLenPos)
        
        pos = 0
        for i in range(len(self)):
            if i == iMatch:
                start = pos
                end = pos + self[i].duration.quarterLength
            else:
                pos += self[i].duration.quarterLength
        return start, end

    def positionToWeight(self, qLenPos):
        '''Given a lenPos, return the weight of the active region.
        Only applies to the top-most level of partitions

        >>> from music21 import *
        >>> a = meter.MeterSequence('3/4', 3)
        >>> a.positionToSpan(.5)
        (0, 1.0)
        >>> a.positionToSpan(1.5)
        (1.0, 2.0)

        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException('cannot access qLenPos %s when total duration is %s and ts is %s' % (qLenPos, self.duration.quarterLength, self))
        iMatch = self.positionToIndex(qLenPos)        
        return self[iMatch].weight


    def positionToDepth(self, qLenPos, align='quantize'):
        '''Given a qLenPos, return the maximum available depth at this position

        >>> from music21 import *
        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.positionToDepth(0)
        3
        >>> b.positionToDepth(0.25) # quantizing active by default
        3
        >>> b.positionToDepth(1)
        3
        >>> b.positionToDepth(1.5)
        2
        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException('cannot access from qLenPos %s' % qLenPos)

        # need to quantize by lowest level
        mapMin = self.getLevelSpan(self.depth-1)
        msMin = self.getLevel(self.depth-1)
        qStart, qEnd = mapMin[msMin.positionToIndex(qLenPos)]
        if align == 'quantize':
            posMatch = qStart
        else:
            posMatch = qLenPos

        score = 0
        for level in range(self.depth):
            map = self.getLevelSpan(level) # get map for each level
            for start, end in map:
                if align in ['start', 'quantize']:
                    srcMatch = start
                elif align == 'end':
                    srcMatch = end
                if common.almostEquals(srcMatch, posMatch):
                    score += 1

        return score
            




#-------------------------------------------------------------------------------
class TimeSignature(music21.Music21Object):

    classSortOrder = 4
    
    def __init__(self, value='4/4', partitionRequest=None):
        music21.Music21Object.__init__(self)

        # whether the TimeSignature object is inherited from 
        self.inherited = False 
        self._lilyOut = None    
        self.symbol = "" # common, cut, single-number, normal

        # a parameter to determine if the denominator is represented
        # as either a symbol (a note) or as a number
        self.symbolizeDenominator = False
        self.summedNumerator = False

        self._overriddenBarDuration = None

        # creates MeterSequence data representations
        # creates .displaySequence, .beamSequence, .beatSequence, .accentSequence
        self.load(value, partitionRequest)

        self._beamableDurationTypes = [duration.typeFromNumDict[8], 
            duration.typeFromNumDict[16], duration.typeFromNumDict[32], 
            duration.typeFromNumDict[64], duration.typeFromNumDict[128]]

    def __str__(self):
        return str(int(self.numerator)) + "/" + str(int(self.denominator))

    def __repr__(self):
        return "<music21.meter.TimeSignature %s>" % self.__str__()


    def ratioEqual(self, other):
        '''A basic form of comparison; does not determine if any internatl structures are equal; only outermost ratio. 
        '''
        if other == None: return False
        if (other.numerator == self.numerator and 
            other.denominator == self.denominator):
            return True
        else:
            return False


    #---------------------------------------------------------------------------
    def _setDefaultBeatPartitions(self):
        '''Set default beat partitions based on numerator and denominator.

        >>> from music21 import *
        >>> ts = meter.TimeSignature('3/4')
        >>> len(ts.beatSequence) # first, not zeroth, level stores beat
        3
        '''
#         tsStr = '%s/%s' % (self.numerator, self.denominator)
#         firstPartitionForm = len(self.displaySequence)
#         cacheKey = None #(tsStr, firstPartitionForm)
# 
#         try:
#             self.beatSequence = copy.deepcopy(
#                                 _meterSequenceBeatArchetypes[cacheKey])
#             #environLocal.printDebug(['using stored accent archetype:'])
#         except KeyError:

        # if a non-compound meter has been given, as in 
        # not 3+1/4; just 5/4
        if len(self.displaySequence) == 1:
            # create toplevel partitions
            if self.numerator in [2, 6]: # duple meters
                self.beatSequence.partition(2)
            elif self.numerator in [3]: # triple meters
                self.beatSequence.partition([1,1,1])
            elif self.numerator in [9]: # triple meters
                self.beatSequence.partition([3,3,3])
            elif self.numerator in [4, 12]: # quadruple meters
                self.beatSequence.partition(4)
            elif self.numerator in [15]: # quintuple meters
                self.beatSequence.partition([3,3,3,3,3])
            # skip 6 numerators; covered above
            elif self.numerator in [18]: # sextuple meters
                self.beatSequence.partition([3,3,3,3,3,3])
            else: # case of odd meters: 5, 7
                self.beatSequence.partition(self.numerator)

        # if a compound meter has been given
        else: # partition by display
            self.beatSequence.partition(self.displaySequence)

        # create subdivisions, and thus define compound/simple distinction
        if len(self.beatSequence) > 1: # if partitioned
            self.beatSequence.subdividePartitionsEqual()

#             if cacheKey != None:
#                 _meterSequenceBeatArchetypes[cacheKey] = copy.deepcopy(self.beatSequence)


                    
    def _setDefaultBeamPartitions(self):
        '''This sets default beam partitions when partitionRequest is None.
        '''
#         tsStr = '%s/%s' % (self.numerator, self.denominator)
#         firstPartitionForm = len(self.displaySequence)
#         cacheKey = None #(tsStr, firstPartitionForm)
# 
#         try:
#             self.beamSequence = copy.deepcopy(
#                                 _meterSequenceBeamArchetypes[cacheKey])
#             #environLocal.printDebug(['using stored beam archetype:'])
#         except KeyError:

        # more general, based only on numerator
        if self.numerator in [2, 3, 4]:
            self.beamSequence.partition(self.numerator)
            # if denominator is 4, subdivide each partition
            if self.denominator in [4]:
                for i in range(len(self.beamSequence)): # subdivide  each beat in 2
                    self.beamSequence[i] = self.beamSequence[i].subdivide(2)

        elif self.numerator == 5:
            default = [2,3]
            self.beamSequence.partition(default)
            # if denominator is 4, subdivide each partition
            if self.denominator in [4]:
                for i in range(len(self.beamSequence)): # subdivide  each beat in 2
                    self.beamSequence[i] = self.beamSequence[i].subdivide(default[i])

        elif self.numerator == 7:
            self.beamSequence.partition(3) # divide into three groups

        elif self.numerator in [6,9,12,15,18,21]:
            self.beamSequence.partition([3] * (self.numerator / 3))
        else:
            pass # doing nothing will beam all together

        #environLocal.printDebug('default beam partitions set to: %s' % self.beamSequence)
#         if cacheKey != None:
#             _meterSequenceBeamArchetypes[cacheKey] = copy.deepcopy(self.beamSequence)


    def _setDefaultAccentWeights(self, depth=3):
        '''This sets default accent weights based on common hierarchical notions for meters; each beat is given a weight, as defined by the top level count of self.beatSequence

        >>> from music21 import *
        >>> ts1 = meter.TimeSignature('4/4')
        >>> ts1._setDefaultAccentWeights(4)
        >>> [mt.weight for mt in ts1.accentSequence]
        [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]

        >>> ts2 = meter.TimeSignature('3/4')
        >>> ts2._setDefaultAccentWeights(4)
        >>> [mt.weight for mt in ts2.accentSequence]
        [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]

        >>> ts2._setDefaultAccentWeights(3) # lower depth
        >>> [mt.weight for mt in ts2.accentSequence]
        [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]

        '''
        # NOTE: this is a performance critical method

        # create a scratch MeterSequence for structure
        tsStr = '%s/%s' % (self.numerator, self.denominator)
        if self.beatSequence.isUniformPartition():
            firstPartitionForm = len(self.beatSequence)
            cacheKey = (tsStr, firstPartitionForm, depth)
        else: # derive from meter sequence
            firstPartitionForm = self.beatSequence
            cacheKey = None # cannot cache based on beat form

        #environLocal.printDebug(['_setDefaultAccentWeights(): firstPartitionForm set to', firstPartitionForm, 'self.beatSequence: ', self.beatSequence, tsStr])
        try:
            self.accentSequence = copy.deepcopy(
                          _meterSequenceAccentArchetypes[cacheKey])
            #environLocal.printDebug(['using stored accent archetype:'])
        except KeyError:
            #environLocal.printDebug(['creating a new accent archetype'])
            ms = MeterSequence(tsStr)    
            # key operation here
            # div count needs to be the number of top-level beat divisions
            ms.subdivideNestedHierarchy(depth, 
                firstPartitionForm=firstPartitionForm)

            # provide a partition for each flat division
            accentCount = len(ms.flat)
            #environLocal.printDebug(['got accentCount', accentCount, 'ms: ', ms])
            divStep = self.barDuration.quarterLength / float(accentCount)
            weightInts = [0] * accentCount # weights as integer/depth counts
            for i in range(accentCount):
                ql = i * divStep
                weightInts[i] = ms.positionToDepth(ql, align='quantize')
    
            maxInt = max(weightInts)
            weightValues = {} # reference dictionary
            # minimum value, something like 1/16., to be multiplied by powers of 2
            weightValueMin = 1.0 / pow(2, maxInt-1)
            for x in range(maxInt):
                # multiply base value (.125) by 1, 2, 4
                # there is never a 0 integer weight, so add 1 to dictionary
                weightValues[x+1] = weightValueMin * pow(2, x)
    
            # set weights on accent partitions
            self.accentSequence.partition([1] * accentCount) 
            for i in range(accentCount):
                # get values from weightValues dictionary
                self.accentSequence[i].weight = weightValues[weightInts[i]]

            if cacheKey != None:
                _meterSequenceAccentArchetypes[cacheKey] = copy.deepcopy(self.accentSequence)


    def load(self, value, partitionRequest=None):
        '''Loading a meter destroys all internal representations
        '''
        # create parallel MeterSequence objects to provide all data
        # these all refer to the same .numerator/.denominator 
        # relationship

        # used for drawing the time signature symbol
        # this is the only one that can be  unlinked
        self.displaySequence = MeterSequence(value)
        self.summedNumerator = self.displaySequence.summedNumerator

        # used for beaming
        self.beamSequence = MeterSequence(value, partitionRequest)
        # used for getting beat divisions
        self.beatSequence = MeterSequence(value, partitionRequest)
        # used for setting one level of accents
        self.accentSequence = MeterSequence(value, partitionRequest)

        if partitionRequest == None: # set default beam partitions
            self._setDefaultBeamPartitions()
            self._setDefaultBeatPartitions()
            # for some summed meters default accent weights are difficult
            # to obtain
            try:
                self._setDefaultAccentWeights(3) # set partitions based on beat
            except MeterException:
                environLocal.printDebug(['cannot set default accents for:', self])
                pass

    def loadRatio(self, numerator, denominator, partitionRequest=None):
        '''Convenience method
        '''
        value = '%s/%s' % (numerator, denominator)
        self.load(value, partitionRequest)


    #---------------------------------------------------------------------------
    # properties


#     def _setStringNotation(self, value):
#         self.load(value)
# 
#     def _getStringNotation(self):
#         return str(self)
#  
#     stringNotation = property(_getStringNotation, _setStringNotation, 
#         doc = '''Get or set the TimeSignature by a simple string value. This permits loading a time signature by a string parameter. 
# 
#         >>> from music21 import *
#         >>> ts = TimeSignature('6/8')
#         >>> ts.stringNotation
#         '6/8'
#         >>> ts.stringNotation = '4/2'
#         >>> ts.stringNotation
#         '4/2'
#         ''')



    # temp for backward compat
    def _getTotalLength(self):
        return self.beamSequence.duration.quarterLength
 
    totalLength = property(_getTotalLength, 
        doc = '''Total length of the TimeSignature, in Quarter Lengths.

        >>> from music21 import *
        >>> ts = TimeSignature('6/8')
        >>> ts.totalLength
        3.0
        ''')

    def _getNumerator(self):
        return self.beamSequence.numerator

    numerator = property(_getNumerator, 
        doc = '''Return the numerator of the TimeSignature as a number.

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.numerator
        3
        ''')

    def _getDenominator(self):
        return self.beamSequence.denominator

    denominator = property(_getDenominator,
        doc = '''Return the denominator of the TimeSignature as a number

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.denominator
        4
        ''')


    def _getBarDuration(self):
        '''
        barDuration gets or sets a duration value that
        is equal in length to the totalLength
        
        >>> from music21 import *
        >>> a = TimeSignature('3/8')
        >>> d = a.barDuration
        >>> d.type
        'quarter'
        >>> d.dots
        1
        >>> d.quarterLength
        1.5
        '''
        
        if self._overriddenBarDuration:
            return self._overriddenBarDuration
        else: 
            # could come from self.beamSequence, self.accentSequence, self.displaySequence, self.accentSequence 
            return self.beamSequence.duration

    def _setBarDuration(self, value):
        self._overriddenBarDuration = value

    barDuration = property(_getBarDuration, _setBarDuration, 
        doc = '''Return a :class:`~music21.duration.Duration` object equal to the total length of this TimeSignature. 

        >>> from music21 import *
        >>> ts = TimeSignature('5/16')
        >>> ts.barDuration
        <music21.duration.Duration 1.25>

        ''')


    def _getBeatLengthToQuarterLengthRatio(self):
        '''
        >>> from music21 import *
        >>> a = TimeSignature('3/2')
        >>> a.beatLengthToQuarterLengthRatio
        2.0
        '''
        return 4.0/self.denominator

    beatLengthToQuarterLengthRatio = property(
                                    _getBeatLengthToQuarterLengthRatio)


    def _getQuarterLengthToBeatLengthRatio(self):
        return self.denominator/4.0

    quarterLengthToBeatLengthRatio = property(
                                    _getQuarterLengthToBeatLengthRatio)




    #---------------------------------------------------------------------------
    # meter classifications used for classifying meters such as 
    # duple triple, etc.

    def _getBeatCount(self):
        # the default is for the beat to be defined by the first, not zero, 
        # level partition. 
        return len(self.beatSequence)

    beatCount = property(_getBeatCount,
        doc = '''Return the count of beat units, or the number of beats in this TimeSignature

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.beatCount
        3
        ''')

    def _getBeatCountName(self):
        # this will use the top-level partitions as the cuunt
        return self.beatSequence.partitionStr 

    beatCountName = property(_getBeatCountName,
        doc = '''Return the beat count name, or the name given for the number of beat units. For example, 2/4 is duple; 9/4 is triple.

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.beatCountName
        'Triple'

        >>> ts = TimeSignature('6/8')
        >>> ts.beatCountName
        'Duple'

        ''')

    def _getBeatDuration(self):
        '''Return a Duration object for the beat unit of this TimeSignature if the beat unit is constant for all top-level beat partitions; otherwise, return None
        '''
        post = []
        if len(self.beatSequence) == 1:
            raise TimeSignatureException('cannot determine beat unit for an unpartitioned beat')
        for ms in self.beatSequence._partition:
            post.append(ms.duration.quarterLength)
        if len(set(post)) == 1:
            return self.beatSequence[0].duration # all are the same
        else:
            raise TimeSignatureException('non uniform beat unit: %s' % post)

    beatDuration = property(_getBeatDuration, 
        doc = '''Return a :class:`~music21.duration.Duration` object equal to the beat unit of this Time Signature, if and only if this TimeSignatyure has a uniform beat unit.

        >>> from music21 import *
        >>> ts = meter.TimeSignature('3/4')
        >>> ts.beatDuration
        <music21.duration.Duration 1.0>
        >>> ts = meter.TimeSignature('6/8')
        >>> ts.beatDuration
        <music21.duration.Duration 1.5>

        >>> ts = meter.TimeSignature('7/8')
        >>> ts.beatDuration
        <music21.duration.Duration 0.5>

        ''')


    def _getBeatDivisionCount(self):
        # first, find if there is more than one beat and if all beats are uniformly partitioned
        post = []
        if len(self.beatSequence) == 1:
            raise TimeSignatureException('cannot determine beat background for an unpartitioned beat')

        # need to see if first-level subdivisions are partitioned
        if not isinstance(self.beatSequence[0], MeterSequence):
            raise TimeSignatureException('cannot determine beat backgrond when each beat is not partitioned')

        # getting length here gives number of subdivisions
        for ms in self.beatSequence._partition:
            post.append(len(ms))

        # convert this to a set; if length is 1, then all beats are uniform
        if len(set(post)) == 1:
            return len(self.beatSequence[0]) # all are the same
        else:
            raise TimeSignatureException('non uniform beat background: %s' % post)

    beatDivisionCount = property(_getBeatDivisionCount,
        doc = '''Return the count of background beat units found within one beat, or the number of subdivisions in the beat unit in this TimeSignature.

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.beatDivisionCount
        2

        >>> ts = TimeSignature('6/8')
        >>> ts.beatDivisionCount
        3

        >>> ts = TimeSignature('15/8')
        >>> ts.beatDivisionCount
        3

        >>> ts = TimeSignature('3/8')
        >>> ts.beatDivisionCount
        2

        >>> ts = TimeSignature('13/8', 13)
        >>> ts.beatDivisionCount
        Traceback (most recent call last):
        TimeSignatureException: cannot determine beat backgrond when each beat is not partitioned
    
        ''')

    def _getBeatDivisionCountName(self):
        bbuc = self._getBeatDivisionCount()
        if bbuc == 2:
            return 'Simple'
        elif bbuc == 3:
            return 'Compound'
        else:
            return None

    beatDivisionCountName = property(_getBeatDivisionCountName,
        doc = '''Return the beat count name, or the name given for the number of beat units. For example, 2/4 is duple; 9/4 is triple.

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.beatDivisionCountName
        'Simple'

        >>> ts = TimeSignature('6/8')
        >>> ts.beatDivisionCountName
        'Compound'

        ''')


    def _getBeatDivisionDurations(self):
        post = []
        if len(self.beatSequence) == 1:
            raise TimeSignatureException('cannot determine beat division for an unpartitioned beat')
        for mt in self.beatSequence._partition:
            for subMt in mt:
                post.append(subMt.duration.quarterLength)
        if len(set(post)) == 1: # all the same 
            out = [] # could be a Stream, but stream.py imports meter.py
            for subMt in self.beatSequence[0]._partition:
                out.append(subMt.duration)
            return out
        else:
            raise TimeSignatureException('non uniform beat division: %s' % post)


    beatDivisionDurations = property(_getBeatDivisionDurations, 
        doc = '''Return the beat division, or the durations that make up one beat, as a list of :class:`~music21.duration.Duration` objects, if and only if the TimeSignature has a uniform beat division for all beats. 

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.beatDivisionDurations
        [<music21.duration.Duration 0.5>, <music21.duration.Duration 0.5>]

        >>> ts = TimeSignature('6/8')
        >>> ts.beatDivisionDurations
        [<music21.duration.Duration 0.5>, <music21.duration.Duration 0.5>, <music21.duration.Duration 0.5>]
        ''')


    def _getBeatSubDivisionDurations(self):
        '''Subdivide each beat division in two. 
        '''
        post = []
        src = self._getBeatDivisionDurations()
        for d in src:
            post.append(d.augmentOrDiminish(.5, inPlace=False))
            post.append(d.augmentOrDiminish(.5, inPlace=False))
        return post

    beatSubDivisionDurations = property(_getBeatSubDivisionDurations, 
        doc = '''Return a subdivision of the beat division, or a list of :class:`~music21.duration.Duration` objects representing each beat division divided by two. 

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.beatSubDivisionDurations
        [<music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>]

        >>> ts = TimeSignature('6/8')
        >>> ts.beatSubDivisionDurations
        [<music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>, <music21.duration.Duration 0.25>]
        '''
        )


    def _getClassification(self):
        return '%s %s' % (self._getBeatDivisionCountName(),
                          self._getBeatCountName())

    classification = property(_getClassification, 
        doc = '''Return the classification of this TimeSignature, such as Simple Triple or Compound Quadruple.

        >>> from music21 import *
        >>> ts = TimeSignature('3/4')
        >>> ts.classification
        'Simple Triple'
        >>> ts = TimeSignature('6/8')
        >>> ts.classification
        'Compound Duple'
        >>> ts = TimeSignature('4/32')
        >>> ts.classification
        'Simple Quadruple'
        ''')


    #---------------------------------------------------------------------------
    # access data for other processing

    def getBeams(self, srcList):
        '''Given a qLen position and a list of Duration objects, return a list of Beams object.

        Can alternatively provide a flat stream, from which Durations are extracted.

        Duration objects are assumed to be adjoining; offsets are not used.

        This can be modified to take lists of rests and notes

        Must process a list at  time, because we cannot tell when a beam ends
        unless we see the context of adjoining durations.

        >>> from music21 import *
        >>> a = TimeSignature('2/4', 2)
        >>> a.beamSequence[0] = a.beamSequence[0].subdivide(2)
        >>> a.beamSequence[1] = a.beamSequence[1].subdivide(2)
        >>> a.beamSequence
        <MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> b = [duration.Duration('16th')] * 8
        >>> c = a.getBeams(b)
        >>> len(c) == len(b)
        True
        >>> print(c)
        [<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>, <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>, <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>, <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>]

        >>> a = TimeSignature('6/8')
        >>> b = [duration.Duration('eighth')] * 6
        >>> c = a.getBeams(b)
        >>> print(c)
        [<music21.beam.Beams <music21.beam.Beam 1/start>>, <music21.beam.Beams <music21.beam.Beam 1/continue>>, <music21.beam.Beams <music21.beam.Beam 1/stop>>, <music21.beam.Beams <music21.beam.Beam 1/start>>, <music21.beam.Beams <music21.beam.Beam 1/continue>>, <music21.beam.Beams <music21.beam.Beam 1/stop>>]
        '''

        if isinstance(srcList, music21.Music21Object):
            durList = []
            for n in srcList:
                durList.append(n.duration)
            srcStream = srcList
        else: # a lost of durations
            durList = srcList
            srcStream = None

        if len(durList) <= 1:
            raise MeterException('length of durList must be 2 or greater, not %s' % len(durList))

        pos = 0 # assume we are always starting at zero w/n this meter
        beamsList = [] # hold complted Beams objects
        for i in range(len(durList)):
            # if a dur cannot be beamable under any circumstance, replace 
            # it with None; this includes Rests
            dur = durList[i]
            if dur.type not in self._beamableDurationTypes:
                beamsList.append(None) # placeholder
            elif srcStream != None and srcStream[i].isRest == True:
                beamsList.append(None) # placeholder
            else:
                # we have a beamable duration
                b = beam.Beams()
                # set the necessary number of internal beamsList, that is, 
                # one for each horizontal line in the beams group
                # this does not set type or direction
                b.fill(dur.type) 
                beamsList.append(b)

        #environLocal.printDebug(['beamsList', beamsList])
        # iter over each beams line, from top to bottom (1 thourgh 5)
        for depth in range(len(self._beamableDurationTypes)):
            beamNumber = depth + 1 # increment to count from 1 not 0
            pos = 0
            for i in range(len(durList)):

                dur = durList[i]
                beams = beamsList[i]

                if beams == None: # if a place holder
                    pos += dur.quarterLength
                    continue

                # see if there is a component defined for this beam number
                # if not, continue
                if beamNumber not in beams.getNumbers(): 
                    pos += dur.quarterLength
                    continue

                start = pos
                end = pos + dur.quarterLength

                startNext = pos + dur.quarterLength
                endPrevious = pos

                if i == len(durList) - 1: # last
                    durNext = None
                    beamNext = None
                else:
                    durNext = durList[i+1]
                    beamNext = beamsList[i+1]

                if i == 0: # previous
                    durPrevious = None
                    beamPrevious = None
                else:
                    durPrevious = durList[i-1]
                    beamPrevious = beamsList[i-1]

                # get an archetype of the MeterSequence for this level
                # level is depth, starting at zero
                archetype = self.beamSequence.getLevel(depth)
                # span is the quarter note duration points for each partition 
                # at this level
                archetypeSpan = archetype.positionToSpan(start)
                #environLocal.printDebug(['at level, got archetype span', depth,
                #                         archetypeSpan])
                if beamNext == None: # last
                    archetypeSpanNext = None
                else:
                    archetypeSpanNext = archetype.positionToSpan(startNext)

                # watch for a special case where a duration completely fills
                # the archetype; this generally should not be beamed
                if (common.almostEquals(start, archetypeSpan[0]) and
                    common.almostEquals(end, archetypeSpan[1])):
                    # increment position and continue loop
                    beamsList[i] = None # replace with None! 
                    pos += dur.quarterLength
                    continue


                # determine beamType
                if i == 0: # if the first, we always start
                    beamType = 'start'
                    # get a partial beam if we cannot continue this 
                    if (beamNext == None or 
                        beamNumber not in beamNext.getNumbers()):
                        beamType = 'partial-right'

                elif i == len(durList) - 1: # last is always stop
                    beamType = 'stop'
                    # get a partial beam if we cannot come form a beam
                    if (beamPrevious == None or 
                        beamNumber not in beamPrevious.getNumbers()):
                        #environLocal.printDebug(['triggering partial left where a stop normally falls'])
                        beamType = 'partial-left'

                # here on we know that it is neither the first nor last

                # if last beam was not defined, we need to either
                # start or have a partial left beam
                # or, if beam number was not active in last beams 
                elif beamPrevious == None or beamNumber not in beamPrevious.getNumbers():
                    beamType = 'start'

                    # case of where we need a partial left:
                    # if the next start value is outside of this span (or at the 
                    # the greater boundary of this span), and we did not have a 
                    # beam or beam number in the previous beam

                    # may need to check: beamNext != None and 
                    #   beamNumber in beamNext.getNumbers()
                    # note: it is cretical that we check archetypeSpan here
                    # not archetypeSpanNext
                    if (common.greaterThanOrEqual(startNext, 
                        archetypeSpan[1])):
                        #environLocal.printDebug(['matching partial left'])
                        beamType = 'partial-left'

                # last beams was active, last beamNumber was active,                # and it was stopped or was a partial-left
                elif (beamPrevious != None and 
                    beamNumber in beamPrevious.getNumbers() and beamPrevious.getTypeByNumber(beamNumber) in ['stop', 'partial-left']):
                    beamType = 'start'

                # if no beam is defined next (we know this already)
                # then must stop
                elif (beamNext == None or 
                    beamNumber not in beamNext.getNumbers()):
                    beamType = 'stop'

                # the last cases are when to stop, or when to continue
                # when we know we have a beam next

                # we continue if the next beam is in the same beaming archetype
                # as this one.
                # if endNext is outside of the archetype span,
                # not sure what to do
                # use common.lessThan to avoid floating point noise
                elif common.lessThan(startNext, archetypeSpan[1]):
                    #environLocal.printDebug(['continue match: durtype, startNext, archetypeSpan', dur.type, startNext, archetypeSpan])
                    beamType = 'continue'

                # we stop if the next beam is not in the same beaming archetype
                # and (as shown above) a valid beam number is not previous
                # use common to avoid floating point noise
                elif common.greaterThanOrEqual(startNext, archetypeSpanNext[0]):
                    beamType = 'stop'

                else:
                    raise TimeSignatureException('cannot match beamType')

                # debugging information displays:
#                 if beamPrevious != None:
#                     environLocal.printDebug(['beamPrevious', beamPrevious, 'beamPrevious.getNumbers()', beamPrevious.getNumbers(), 'beamPrevious.getByNumber(beamNumber).type'])
#                     if beamNumber in beamPrevious.getNumbers():
#                         environLocal.printDebug(['beamPrevious type', beamPrevious.getByNumber(beamNumber).type])
                        
                #environLocal.printDebug(['beamNumber, start, archetypeSpan, beamType', beamNumber, start, dur.type, archetypeSpan, beamType])

                beams.setByNumber(beamNumber, beamType)

                # increment position and continue loop
                pos += dur.quarterLength

        return beamsList


    def setDisplay(self, value, partitionRequest=None):
        '''Set an indendent display value

        >>> from music21 import *
        >>> a = TimeSignature()
        >>> a.load('3/4')
        >>> a.setDisplay('2/8+2/8+2/8')
        >>> a.displaySequence
        <MeterSequence {2/8+2/8+2/8}>
        >>> a.beamSequence
        <MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
        >>> a.beatSequence # a single top-level partition is default for beat
        <MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
        >>> a.setDisplay('3/4')
        >>> a.displaySequence
        <MeterSequence {3/4}>
        '''
        if isinstance(value, MeterSequence): # can set to an existing meterseq
            # must make a copy
            self.displaySequence = copy.deepcopy(value)
        else:
            # create a new object; it will not be linked
            self.displaySequence = MeterSequence(value, partitionRequest)

        # need to update summed numerator states
        self.summedNumerator = self.displaySequence.summedNumerator


    def getAccent(self, qLenPos):
        '''Return True or False if the qLenPos is at the start of an accent
        division.

        >>> from music21 import *
        >>> a = TimeSignature('3/4', 3)
        >>> a.accentSequence.partition([2,1])
        >>> a.accentSequence
        <MeterSequence {2/4+1/4}>
        >>> a.getAccent(0)
        True
        >>> a.getAccent(1)
        False
        >>> a.getAccent(2)
        True
        '''
        pos = 0
        for i in range(len(self.accentSequence)):
            if common.almostEquals(pos, qLenPos):
                return True
            pos += self.accentSequence[i].duration.quarterLength
        return False


    def setAccentWeight(self, weightList, level=0):
        '''Set accent weight, or floating point scalars, for the accent MeterSequence. Provide a list of values; if this list is shorter than the length of the MeterSequence, it will be looped; if this list is longer, only the first relevant value will be used.

        If the accent MeterSequence is subdivided, the level of depth to set is given by the optional level argument.

        >>> from music21 import *
        >>> a = TimeSignature('4/4', 4)
        >>> len(a.accentSequence)
        4
        >>> a.setAccentWeight([.8, .2])
        >>> a.getAccentWeight(0)
        0.800...
        >>> a.getAccentWeight(.5)
        0.800...
        >>> a.getAccentWeight(1)
        0.200...
        >>> a.getAccentWeight(2.5)
        0.800...
        >>> a.getAccentWeight(3.5)
        0.200...
        '''
        if not common.isListLike(weightList):
            weightList = [weightList]

        msLevel = self.accentSequence.getLevel(level)
        for i in range(len(msLevel)):
            msLevel[i].weight = weightList[i % len(weightList)]

    def getAccentWeight(self, qLenPos, level=0, forcePositionMatch=False):
        '''Given a qLenPos,  return an accent level. In general, accents are assumed to define only a first-level weight. 

        If `forcePositionMatch` is True, an accent will only returned if the provided qLenPos is a near exact match to the provided quarter length. Otherwise, half of the minimum quarter length will be provided.

        >>> from music21 import *
        >>> ts1 = meter.TimeSignature('3/4')
        >>> [ts1.getAccentWeight(x) for x in range(3)]
        [1.0, 0.5, 0.5]
        '''

        # might store this weight every time it is set, rather than
        # getting it here
        minWeight = min([mt.weight for mt in self.accentSequence._partition]) * .5

        msLevel = self.accentSequence.getLevel(level)

        if forcePositionMatch:
            # only return values for qLen positions that are at the start
            # of a span; for those that are not, we need to return a minWeight
            localSpan = msLevel.positionToSpan(qLenPos)
            if not common.almostEquals(qLenPos, localSpan[0]):
                return minWeight
        return msLevel[msLevel.positionToIndex(qLenPos)].weight

    def getBeat(self, qLenPos):
        '''Given a quarterLength position, get the beat, where beats count from 1

        >>> from music21 import *
        >>> a = TimeSignature('3/4', 3)
        >>> a.getBeat(0)
        1
        >>> a.getBeat(2.5)
        3
        >>> a.beatSequence.partition(['3/8', '3/8'])
        >>> a.getBeat(2.5)
        2
        '''
        return self.beatSequence.positionToIndex(qLenPos) + 1

    def getBeatOffsets(self):
        '''Return offset positions in a list for the start of each beat, assuming this object is found at offset zero.

        >>> from music21 import *
        >>> a = TimeSignature('3/4')
        >>> a.getBeatOffsets()
        [0.0, 1.0, 2.0]
        >>> a = TimeSignature('6/8')
        >>> a.getBeatOffsets()
        [0.0, 1.5]
        '''
        post = []
        post.append(0.0)
        if len(self.beatSequence) == 1:
            return post    
        else:       
            endOffset = self.barDuration.quarterLength
            o = 0.0
            for ms in self.beatSequence._partition:
                o += ms.duration.quarterLength
                if common.almostEquals(o, endOffset) or o >= endOffset:
                    return post # do not add offset for end of bar
                post.append(o)
                

    def getBeatDuration(self, qLenPos):
        '''Give a quarter length position into this meter, return a :class:`~music21.duration.Duration` object active for the top-level beat. Unlike the :attr:`music21.meter.TimeSignature.beatDuration` parameter, this will work for asymmetrical meters.

        >>> from music21 import *
        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getBeatDuration(.5)
        <music21.duration.Duration 1.0>
        >>> ts1.getBeatDuration(2.5)
        <music21.duration.Duration 1.0>

        >>> ts2 = meter.TimeSignature('6/8')
        >>> ts2.getBeatDuration(2.5)
        <music21.duration.Duration 1.5>

        >>> ts3 = meter.TimeSignature(['3/8','2/8']) # will partition as 2 beat
        >>> ts3.getBeatDuration(.5)
        <music21.duration.Duration 1.5>
        >>> ts3.getBeatDuration(1.5)
        <music21.duration.Duration 1.0>
        '''
        return self.beatSequence[self.beatSequence.positionToIndex(qLenPos)].duration


    def getOffsetFromBeat(self, beat):
        '''Given a beat value, convert into an offset position. 

        >>> from music21 import *
        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getOffsetFromBeat(1)
        0.0
        >>> ts1.getOffsetFromBeat(2)
        1.0
        >>> ts1.getOffsetFromBeat(3)
        2.0
        >>> ts1.getOffsetFromBeat(3.5)
        2.5
        >>> ts1.getOffsetFromBeat(3.25)
        2.25

        >>> ts1 = meter.TimeSignature('6/8')
        >>> ts1.getOffsetFromBeat(1)
        0.0
        >>> ts1.getOffsetFromBeat(2)
        1.5
        >>> ts1.getOffsetFromBeat(2.33)
        2.0
        >>> ts1.getOffsetFromBeat(2.5) # will be + .5 * 1.5
        2.25
        >>> ts1.getOffsetFromBeat(2.66)
        2.5
        '''
        # divide into integer and floating point components
        beatInt, beatFraction = divmod(beat, 1)
        beatInt = int(beatInt) # convert to integer
        # resolve .33 to .3333333
        beatFraction = common.nearestCommonFraction(beatFraction)

        if beatInt-1 > len(self.beatSequence)-1:
            raise TimeSignatureException('requested beat value (%s) not found in beat partitions (%s) of ts %s' % (beatInt, self.beatSequence, self))
        # get a duration object for the beat; will translate into quarterLength
        # beat int counts from 1; subtrack 1 to get index
        beatDur = self.beatSequence[beatInt-1].duration
        oStart, oEnd = self.beatSequence.getLevelSpan()[beatInt-1]
        post = oStart + (beatDur.quarterLength * beatFraction)
        # round to 3 values
        return round(post, 4)



    def getBeatProgress(self, qLenPos):
        '''Given a quarterLength position, get the beat, where beats count from 1, and return the the amount of qLen into this beat the supplied qLenPos
        is. 

        >>> from music21 import *
        >>> a = meter.TimeSignature('3/4', 3)
        >>> a.getBeatProgress(0)
        (1, 0)
        >>> a.getBeatProgress(0.75)
        (1, 0.75)
        >>> a.getBeatProgress(2.5)
        (3, 0.5)
        >>> a.beatSequence.partition(['3/8', '3/8'])
        >>> a.getBeatProgress(2.5)
        (2, 1.0)
        '''
        beatIndex = self.beatSequence.positionToIndex(qLenPos)
        start, end = self.beatSequence.positionToSpan(qLenPos)
        return beatIndex + 1, qLenPos - start


    def getBeatProportion(self, qLenPos):
        '''Given a quarter length position into the meter, return a numerical progress through the beat (where beats count from one) with a floating-point value between 0 and 1 appended to this value that gives the proportional progress into the beat. 

        >>> from music21 import *
        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getBeatProportion(0)
        1.0
        >>> ts1.getBeatProportion(0.5)
        1.5
        >>> ts1.getBeatProportion(1)
        2.0

        >>> ts3 = meter.TimeSignature(['3/8','2/8']) # will partition as 2 beat
        >>> ts3.getBeatProportion(.75)
        1.5
        >>> ts3.getBeatProportion(2)
        2.5
        '''
        beatIndex = self.beatSequence.positionToIndex(qLenPos)
        start, end = self.beatSequence.positionToSpan(qLenPos)
        range = end - start
        progress = qLenPos - start # how far in QL
        return beatIndex + 1 + (progress / range)


    def getBeatProportionStr(self, qLenPos):
        '''Return a string presentation of the beat. 

        >>> from music21 import *
        >>> ts1 = meter.TimeSignature('3/4')
        >>> ts1.getBeatProportionStr(0)
        '1'
        >>> ts1.getBeatProportionStr(0.5)
        '1 1/2'
        >>> ts1.getBeatProportionStr(1)
        '2'
        >>> ts3 = meter.TimeSignature(['3/8','2/8']) # will partition as 2 beat
        >>> ts3.getBeatProportionStr(.75)
        '1 1/2'
        >>> ts3.getBeatProportionStr(2)
        '2 1/2'

        >>> ts4 = meter.TimeSignature(['6/8']) # will partition as 2 beat
        '''

        beatIndex = int(self.beatSequence.positionToIndex(qLenPos))
        start, end = self.beatSequence.positionToSpan(qLenPos)
        range = end - start
        progress = qLenPos - start # how far in QL

        if (progress / range) == 0.0:
            post = '%s' % (beatIndex + 1) # just show beat 
        else:
            a, b = proportionToFraction(progress / range)
            post = '%s %s/%s' % (beatIndex + 1, a, b) # just show beat 
        return post


    def getBeatDepth(self, qLenPos, align='quantize'):
        '''Return the number of levels of beat partitioning given a QL into the TimeSignature. Note that by default beat partitioning always has a single, top-level partition.

        The `align` parameter is passed to the :meth:`~music21.meter.MeterSequence.positionToDepth` method, and can be used to find depths based on start position overlaps. 

        >>> from music21 import *
        >>> a = TimeSignature('3/4', 3)
        >>> a.getBeatDepth(0)
        1
        >>> a.getBeatDepth(1)
        1
        >>> a.getBeatDepth(2)
        1

        >>> b = TimeSignature('3/4', 1)
        >>> b.beatSequence[0] = b.beatSequence[0].subdivide(3)
        >>> b.beatSequence[0][0] = b.beatSequence[0][0].subdivide(2)
        >>> b.beatSequence[0][1] = b.beatSequence[0][1].subdivide(2)
        >>> b.beatSequence[0][2] = b.beatSequence[0][2].subdivide(2)
        >>> b.getBeatDepth(0)
        3
        >>> b.getBeatDepth(.5)
        1
        >>> b.getBeatDepth(1)
        2
        '''
        return self.beatSequence.positionToDepth(qLenPos, align)



    def quarterPositionToBeat(self, currentQtrPosition = 0):
        '''For backward compatibility. Ultimately, remove. 
        '''
        #return ((currentQtrPosition * self.quarterLengthToBeatLengthRatio) + 1)
        return self.getBeat(currentQtrPosition)
    


    #---------------------------------------------------------------------------
    def _getLily(self):
        '''
        returns the lilypond representation of the timeSignature
        
        >>> from music21 import *
        >>> a = TimeSignature('3/16')
        >>> a.lily
        \\time 3/16
        '''
        
        # TODO: values need to be taken from self.displaySequence

        if self._lilyOut is not None:
            return self._lilyOut
        return lily.LilyString("\\time " + str(self) + " ")
    
    def _setLily(self, newLily):
        self._lilyOut = newLily
    
    lily = property(_getLily, _setLily)



    def _getMX(self):
        return musicxmlTranslate.timeSignatureToMx(self)
        
#         '''Returns a single mxTime object.
#         
#         Compound meters are represented as multiple pairs of beat
#         and beat-type elements
# 
#         >>> from music21 import *
#         >>> a = TimeSignature('3/4')
#         >>> b = a.mx
#         >>> a = TimeSignature('3/4+2/4')
#         >>> b = a.mx
# 
#         '''
#         #mxTimeList = []
#         mxTime = musicxml.Time()
#         
#         # always get a flat version to display any subivisions created
#         fList = [(mt.numerator, mt.denominator) for mt in self.displaySequence.flat._partition]
#         if self.summedNumerator:
#             # this will try to reduce any common denominators into 
#             # a common group
#             fList = fractionToSlashMixed(fList)
# 
#         for n,d in fList:
#             mxBeats = musicxml.Beats(n)
#             mxBeatType = musicxml.BeatType(d)
#             mxTime.componentList.append(mxBeats)
#             mxTime.componentList.append(mxBeatType)
# 
#         # can set this to common when necessary
#         mxTime.set('symbol', None)
#         # for declaring no time signature present
#         mxTime.set('senza-misura', None)
#         #mxTimeList.append(mxTime)
#         #return mxTimeList
#         return mxTime

    def _setMX(self, mxTimeList):
        return musicxmlTranslate.mxToTimeSignature(mxTimeList, self)

#         '''Given an mxTimeList, load this object 
# 
#         >>> from music21 import *
#         >>> a = musicxml.Time()
#         >>> a.setDefaults()
#         >>> b = musicxml.Attributes()
#         >>> b.timeList.append(a)
#         >>> c = TimeSignature()
#         >>> c.mx = b.timeList
#         >>> c.numerator
#         4
#         '''
#         if not common.isListLike(mxTimeList): # if just one
#             mxTime = mxTimeList
#         else: # there may be more than one if we have more staffs per part
#             mxTime = mxTimeList[0]
# 
# #         if len(mxTimeList) == 0:
# #             raise MeterException('cannot create a TimeSignature from an empty MusicXML timeList: %s' % musicxml.Attributes() )
# #         mxTime = mxTimeList[0] # only one for now
# 
#         n = []
#         d = []
#         for obj in mxTime.componentList:
#             if isinstance(obj, musicxml.Beats):
#                 n.append(obj.charData) # may be 3+2
#             if isinstance(obj, musicxml.BeatType):
#                 d.append(obj.charData)
#         assert len(n) == len(d)
# 
#         #n = mxTime.get('beats')
#         #d = mxTime.get('beat-type')
#         # convert into a string
#         msg = []
#         for i in range(len(n)):
#             msg.append('%s/%s' % (n[i], d[i]))
# 
#         #environLocal.printDebug(['loading meter string:', '+'.join(msg)])
#         self.load('+'.join(msg))

    mx = property(_getMX, _setMX)


    def _getMusicXML(self):
        return musicxmlTranslate.timeSignatureToMusicXML(self)

#         from music21 import stream, note
#         tsCopy = copy.deepcopy(self)
# #         m = stream.Measure()
# #         m.timeSignature = tsCopy
# #         m.append(note.Rest())
#         out = stream.Stream()
#         out.append(tsCopy)
#         return out.musicxml

#         mxAttributes = musicxml.Attributes()
#         # need a lost of time 
#         mxAttributes.set('time', [self._getMX()])
# 
#         mxMeasure = musicxml.Measure()
#         mxMeasure.setDefaults()
#         mxMeasure.set('attributes', mxAttributes)
# 
#         mxPart = musicxml.Part()
#         mxPart.setDefaults()
#         mxPart.append(mxMeasure)
# 
#         mxScorePart = musicxml.ScorePart()
#         mxScorePart.setDefaults()
#         mxPartList = musicxml.PartList()
#         mxPartList.append(mxScorePart)
# 
#         mxIdentification = musicxml.Identification()
#         mxIdentification.setDefaults() # will create a composer
# 
#         mxScore = musicxml.Score()
#         mxScore.setDefaults()
#         mxScore.set('partList', mxPartList)
#         mxScore.set('identification', mxIdentification)
#         mxScore.append(mxPart)
#         return mxScore.xmlStr()

    musicxml = property(_getMusicXML)





#-------------------------------------------------------------------------------

class CompoundTimeSignature(TimeSignature):
    pass

class DurationDenominatorTimeSignature(TimeSignature):
    '''If you have played Hindemith you know these, 3/(dot-quarter) etc.'''
    pass

class NonPowerOfTwoTimeSignature(TimeSignature):
    pass



















#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):    
    def runTest(self):
        pass
    
    def testSingle(self):
        '''Need to test direct meter creation w/o stream
        '''
        a = TimeSignature('3/16')
        a.show()

    def testBasic(self):
        from music21 import stream
        a = stream.Stream()
        for meterStrDenominator in [1,2,4,8,16,32]:
            for meterStrNumerator in [2,3,4,5,6,7,9,11,12,13]:
                ts = music21.meter.TimeSignature('%s/%s' % (meterStrNumerator, 
                                                            meterStrDenominator))
                m = stream.Measure()
                m.timeSignature = ts
                a.insert(m.timeSignature.barDuration.quarterLength, m)
        a.show()

    def testCompound(self):
        from music21 import stream
        import random

        a = stream.Stream()
        meterStrDenominator  = [1,2,4,8,16,32]
        meterStrNumerator = [2,3,4,5,6,7,9,11,12,13]
        
        for x in range(30):
            msg = []
            for y in range(1, random.choice([2,4])):
                msg.append('%s/%s' % (random.choice(meterStrNumerator),
                                      random.choice(meterStrDenominator)))
            ts = music21.meter.TimeSignature('+'.join(msg))
            m = stream.Measure()
            m.timeSignature = ts
            a.insert(m.timeSignature.barDuration.quarterLength, m)
        a.show()


    def testMeterBeam(self):
        from music21 import stream, note
        ts = music21.meter.TimeSignature('6/8', 2)
        b = [duration.Duration('16th')] * 12
        s = stream.Stream()
        s.insert(0, ts)
        for x in b:
            n = note.Note()
            n.duration = x
            s.append(n)
        s.show()



class Test(unittest.TestCase):
    '''Unit tests
    '''

    def runTest(self):
        pass
    

    def setUp(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
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


    def testMeterSubdivision(self):
        a = MeterSequence()
        a.load('4/4', 4)
        str(a) == '{1/4+1/4+1/4+1/4}'
        
        a[0] = a[0].subdivide(2)
        str(a) == '{{1/8+1/8}+1/4+1/4+1/4}'
        
        a[3].subdivide(4)
        str(a) == '{{1/8+1/8}+1/4+1/4+{1/16+1/16+1/16+1/16}}'
        


    def testMeterDeepcopy(self):
        import copy
        a = MeterSequence()
        a.load('4/4', 4)        
        b = copy.deepcopy(a)        
        self.assertNotEqual(a, b)


        c = TimeSignature('4/4')
        d = copy.deepcopy(c)
        self.assertNotEqual(c, d)


    def testGetBeams(self):
        from music21 import duration

        a = TimeSignature('6/8')
        b = ([duration.Duration('16th')] * 4  + 
             [duration.Duration('eighth')] * 1) * 2
        c = a.getBeams(b)
        match = '''[<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>, <music21.beam.Beams <music21.beam.Beam 1/stop>>, <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>, <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>, <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''

        self.assertEqual(str(c), match)



    def testPositionToDepth(self):

        # get a maximally divided 4/4 to the level of 1/8
        a = MeterSequence('4/4')
        for h in range(len(a)):
            a[h] = a[h].subdivide(2)
            for i in range(len(a[h])):
                a[h][i] = a[h][i].subdivide(2)
                for j in range(len(a[h][i])):
                    a[h][i][j] = a[h][i][j].subdivide(2)

        # matching with starts result in a lerdahl jackendoff style depth
        match = [4,1,2,1,3,1,2,1]
        for x in range(8):
            pos = x * .5
            test = a.positionToDepth(pos, align='start')
            self.assertEqual(test, match[x])

        match = [1,2,1,3,1,2,1]
        for x in range(7):
            pos = (x * .5) + .5
            test = a.positionToDepth(pos, align='end')
            #environLocal.printDebug(['here', test])
            self.assertEqual(test, match[x])

        # can quantize by lowest value
        match = [4,1,2,1,3,1,2,1]
        for x in range(8):
            pos = (x * .5) + .25
            test = a.positionToDepth(pos, align='quantize')
            self.assertEqual(test, match[x])


    def testDefaultBeatPartitions(self):
        src = [('2/2'), ('2/4'), ('2/8'), ('6/4'), ('6/8'), ('6/16')]
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 2)
            self.assertEqual(ts.beatCountName, 'Duple')
            if ts.numerator == 2:
                for ms in ts.beatSequence: # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 6:
                for ms in ts.beatSequence: # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = [('3/2'), ('3/4'), ('3/8'), ('9/4'), ('9/8'), ('9/16')]
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 3)
            self.assertEqual(ts.beatCountName, 'Triple')
            if ts.numerator == 3:
                for ms in ts.beatSequence: # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 9:
                for ms in ts.beatSequence: # should be divided in three
                    self.assertEqual(len(ms), 3)


        src = [('4/2'), ('4/4'), ('4/8'), ('12/4'), ('12/8'), ('12/16')]
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 4)
            self.assertEqual(ts.beatCountName, 'Quadruple')
            if ts.numerator == 4:
                for ms in ts.beatSequence: # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 12:
                for ms in ts.beatSequence: # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = [('5/2'), ('5/4'), ('5/8'), ('15/4'), ('15/8'), ('15/16')]
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 5)
            self.assertEqual(ts.beatCountName, 'Quintuple')
            if ts.numerator == 5:
                for ms in ts.beatSequence: # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 15:
                for ms in ts.beatSequence: # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = [('18/4'), ('18/8'), ('18/16')]
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 6)
            self.assertEqual(ts.beatCountName, 'Sextuple')
            if ts.numerator == 18:
                for ms in ts.beatSequence: # should be divided in three
                    self.assertEqual(len(ms), 3)

        # odd or unusual partitions
        src = [('13/4'), ('19/8'), ('17/16')]
        for tsStr in src:
            ts = TimeSignature(tsStr)
            #self.assertEqual(len(ts.beatSequence), 6)
            self.assertEqual(ts.beatCountName, None)



    def testBeatProportionFromTimeSignature(self):
        
        # given meter, ql, beat proportion, and beat ql
        data = [
    ['2/4', (0, .5, 1, 1.5), (1, 1.5, 2, 2.5), (1, 1, 1, 1)],
    ['3/4', (0, .5, 1, 1.5), (1, 1.5, 2, 2.5), (1, 1, 1, 1)],
    ['4/4', (0, .5, 1, 1.5), (1, 1.5, 2, 2.5), (1, 1, 1, 1)],

    ['6/8', (0, .5, 1, 1.5, 2), (1, 1.33333, 1.66666, 2.0, 2.33333), 
        (1.5, 1.5, 1.5, 1.5, 1.5)],
    ['9/8', (0, .5, 1, 1.5, 2), (1, 1.33333, 1.66666, 2.0, 2.33333), 
        (1.5, 1.5, 1.5, 1.5, 1.5)],
    ['12/8', (0, .5, 1, 1.5, 2), (1, 1.33333, 1.66666, 2.0, 2.33333), 
        (1.5, 1.5, 1.5, 1.5, 1.5)],

    ['2/8+3/8', (0, .5, 1, 1.5), (1, 1.5, 2, 2.333333), (1, 1, 1.5, 1.5, 1.5)],
        ]

        for tsStr, src, dst, beatDur in data:
            ts = TimeSignature(tsStr)
            for i in range(len(src)):
                ql = src[i]
                self.assertAlmostEqual(ts.getBeatProportion(ql), dst[i], 4)
                self.assertEqual(ts.getBeatDuration(ql).quarterLength,
                                 beatDur[i])



    def testSubdividePartitionsEqual(self):
        
        ms = MeterSequence('2/4')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/4+1/4}}')

        ms = MeterSequence('3/4')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/4+1/4+1/4}}')

        ms = MeterSequence('6/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{3/8+3/8}}')

        ms = MeterSequence('6/16')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{3/16+3/16}}')

        ms = MeterSequence('3/8+3/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8+1/8}+{1/8+1/8+1/8}}')

        ms = MeterSequence('2/8+3/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8}+{1/8+1/8+1/8}}')

        ms = MeterSequence('5/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8+1/8+1/8+1/8}}')


        ms = MeterSequence('3/8+3/4')
        ms.subdividePartitionsEqual(None) # can partition by another 
        self.assertEqual(str(ms), '{{1/8+1/8+1/8}+{1/4+1/4+1/4}}')




    def testSetDefaultAccentWeights(self):
        # these tests take the level to 3. in some cases, a level of 2
        # is not sufficient to normalize all denominators
        pairs = [
        ('4/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

        ('3/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

        ('2/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

        # divided at 4th 8th
        ('6/8', [1.0, 0.125, 0.25, 0.125, 0.25, 0.125, 
                 0.5, 0.125, 0.25, 0.125, 0.25, 0.125] ),

        # all beats are even b/c this is unpartitioned
        ('5/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125] ),

        ('9/4', [1.0, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125]),

        ('18/4', [1.0, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125]),

        ('11/8', [1.0, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125]),


        ('2/8+3/8', [1.0, 0.125, 0.25, 0.125, 
        0.5, 0.125, 0.25, 0.125, 0.25, 0.125] ),

        ('3/8+2/8+3/4', 
        [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 

        0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 

        0.5, 0.03125, 0.0625, 0.03125, 0.125, 0.03125, 0.0625, 0.03125, 
        0.25, 0.03125, 0.0625, 0.03125, 0.125, 0.03125, 0.0625, 0.03125, 
        0.25, 0.03125, 0.0625, 0.03125, 0.125, 0.03125, 0.0625, 0.03125
        ] ), 


        ('1/2+2/16', 
        [1.0, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625, 0.125, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625, 0.25, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625, 0.125, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625, 
        
        0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]  ),


                ]

        for tsStr, match in pairs:
            #environLocal.printDebug([tsStr])
            ts1 = TimeSignature(tsStr)
            ts1._setDefaultAccentWeights(3) # going to a lower level here
            self.assertEqual([mt.weight for mt in ts1.accentSequence], match)
           


#     def testJSONStorage(self):
#         ts = TimeSignature('3/4')
#         # cannot test to json str as __class__ is different based on context 
#         #self.assertEqual(ts.json, '{"__attr__": {"stringNotation": "3/4"}, "__version__": [0, 3, 0], "__class__": "<class \'__main__.TimeSignature\'>"}')
# 
#         jsString = ts.json
#         ts = TimeSignature()
#         ts.json = jsString
#         self.assertEqual(ts.stringNotation, '3/4')


    def testMusicxmlDirectOut(self):
        # test rendering musicxml directly from meter
        ts = TimeSignature('3/8')
        xmlout = ts.musicxml

        match = '<time><beats>3</beats><beat-type>8</beat-type></time>'
        xmlout = xmlout.replace(' ', '')
        xmlout = xmlout.replace('\n', '')
        self.assertEqual(xmlout.find(match), 501)

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TimeSignature, CompoundTimeSignature]


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:

        #music21.mainTest(Test, TestExternal)
        music21.mainTest(Test)
    else:

        t = Test()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()



#------------------------------------------------------------------------------
# eof

