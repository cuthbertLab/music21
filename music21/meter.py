#-------------------------------------------------------------------------------
# Name:         meter.py
# Purpose:      Classes for meters
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import re, copy
#import fractions # available in 2.6 and greater

import music21

from music21 import common
from music21 import duration
from music21 import lily
from music21 import note
from music21 import musicxml
from music21 import environment
_MOD = 'meter.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

validDenominators = [1,2,4,8,16,32,64,128] # in order
# also [pow(2,x) for x in range(8)]
MIN_DENOMINATOR_TYPE = '128th'

def slashToFraction(value):
    '''
    >>> slashToFraction('3/8')
    (3, 8)
    >>> slashToFraction('7/32')
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
        return None

def slashCompoundToFraction(value):
    '''
    >>> slashCompoundToFraction('3/8+2/8')
    [(3, 8), (2, 8)]
    >>> slashCompoundToFraction('5/8')
    [(5, 8)]
    >>> slashCompoundToFraction('5/8+2/4+6/8')
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

    >>> slashMixedToFraction('3/8+2/8')
    ([(3, 8), (2, 8)], False)

    >>> slashMixedToFraction('3+2/8')
    ([(3, 8), (2, 8)], True)

    >>> slashMixedToFraction('3+2+5/8')
    ([(3, 8), (2, 8), (5, 8)], True)

    >>> slashMixedToFraction('3+2+5/8+3/4')
    ([(3, 8), (2, 8), (5, 8), (3, 4)], True)

    >>> slashMixedToFraction('3+2+5/8+3/4+2+1+4/16')
    ([(3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)], True)

    >>> slashMixedToFraction('3+2+5/8+3/4+2+1+4')
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
            pre.append(list(slashToFraction(part)))
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

    >>> fractionToSlashMixed([(3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)])
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
    
    >>> fractionSum([(3,8), (5,8), (1,8)])
    (9, 8)
    >>> fractionSum([(1,6), (2,3)])
    (5, 6)
    >>> fractionSum([(3,4), (1,2)])
    (5, 4)
    >>> fractionSum([(1,13), (2,17)])
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






#-------------------------------------------------------------------------------
class MeterException(Exception):
    pass

class TimeSignatureException(MeterException):
    pass


#-------------------------------------------------------------------------------
class MeterTerminal(object):
    '''A MeterTerminal is a nestable primitive of rhythmic division

    >>> a = MeterTerminal('2/4')
    >>> a.duration.quarterLength
    2.0
    >>> a = MeterTerminal('3/8')
    >>> a.duration.quarterLength
    1.5
    >>> a = MeterTerminal('5/2')
    >>> a.duration.quarterLength
    10.0

    '''
    def __init__(self, slashNotation=None, weight=1):
        self._numerator = 0 
        self._denominator = 1
        self._overriddenDuration = None

        if slashNotation != None:
            self.numerator, self.denominator = slashToFraction(slashNotation)
        self._ratioChanged() # sets self._duration

        # this will call _setWeight property for data checking
        # explicitly calling base class method to avoid problems
        # in the derived class MeterSequence
        MeterTerminal._setWeight(self, weight)

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

        >>> a = MeterTerminal('3/4')
        >>> b = a.subdivideByCount(3)
        >>> isinstance(b, MeterSequence)
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

        >>> a = MeterTerminal('3/4')
        >>> b = a.subdivideByList([1,1,1])
        >>> len(b)
        3
        '''
        # elevate to meter sequence
        ms = MeterSequence()
        ms.load(self) # do not need to autoWeight here
        ms.partitionByList(numeratorList) # this will split weight
        return ms    

    def subdivide(self, value):
        '''Subdivision takes a MeterTerminal and, making it into a a collection of MeterTerminals, Returns a MeterSequence.

        This is different than a partitioning a MeterSequence in that this does not happen in place and instead returns a new object.

        If an integer is provided, assume it is a partition count
        '''
        if common.isListLike(value):
            return self.subdivideByList(value)
        else:
            return self.subdivideByCount(value)



    #---------------------------------------------------------------------------
    # properties

    def _getWeight(self):
        return self._weight

    def _setWeight(self, value):
        '''
        >>> a = MeterTerminal('2/4')
        >>> a.weight = .5
        >>> a.weight
        0.5
        '''
        if not common.isNum(value):
            raise MeterException('weight values must be numbers')
        self._weight = value
    
    weight = property(_getWeight, _setWeight)


    def _getNumerator(self):
        return self._numerator

    def _setNumerator(self, value):
        '''
        >>> a = MeterTerminal('2/4')
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
        >>> a = MeterTerminal('2/4')
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
        if self.numerator == None or self.denominator == None:
            self._duration = None
        else:
            self._duration = duration.Duration()
            try:
                self._duration.quarterLength = ((4.0 * 
                            self.numerator)/self.denominator)
            except duration.DurationException:
                environLocal.printDebug(['DuratioinException encountered', 
                    'numerator/denominator', self.numerator, self.denominator])
                self._duration = None

    def _getDuration(self):
        '''
        barDuration gets or sets a duration value that
        is equal in length to the totalLength
        
        >>> a = MeterTerminal()
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

    def __str__(self):
        msg = []
        for mt in self._partition:
            msg.append(str(mt))
        return '{%s}' % '+'.join(msg)

    def __repr__(self):
        return '<MeterSequence %s>' % self.__str__()

    def __len__(self):
        '''Return the length of the partition list
       
        >>> a = MeterSequence('4/4', 4)
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

        >>> a = MeterSequence('4/4', 4)
        >>> a[3].numerator
        1
        '''
        if abs(key) >= self.__len__():
            raise IndexError
        else:
            return self._partition[key]

    def __setitem__(self, key, value):
        '''Insert items at index positions.

        >>> a = MeterSequence('4/4', 4)
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

    #---------------------------------------------------------------------------
    # load common meter templates into this sequence

    def _divisionOptionsAlgo(self, n, d):
        '''
        This is a primitive approach to algorithmic division production.
        This can be extended.
       
        It is assumed that these values are provided in order of priority

        >>> a = MeterSequence()
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

        '''
        opts = []

        # compound meters; 6, 9, 12, 15
        if n % 3 == 0 and n > 3 and d > 4:
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

    def _addTerminal(self, value):
        '''Add a an object to the partition list. This does not update numerator and denominator.

        targetWeight is the expected total Weight for this MeterSequence. This
        would be self.weight, but offten partitions are cleared before _addTerminal is called. 
        '''
        if common.isStr(value):
            mt = MeterTerminal(value)
        elif isinstance(value, MeterTerminal): # may be a MeterSequence
            mt = value
        else:
            raise MeterException('cannot add %s to this sequence' % value)
        self._partition.append(mt)


    def _getOptions(self):
        n = int(self.numerator)
        d = int(self.denominator)
        opts = []
        opts += self._divisionOptionsAlgo(n, d)
        opts += self._divisionOptionsPreset(n, d)
        return opts


    #---------------------------------------------------------------------------
    def partitionByCount(self, countRequest, loadDefault=True):
        '''This will destroy any struct in the _partition

        >>> a = MeterSequence('4/4')
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
            raise MeterException('Cannot set partition by %s' % countRequest)


    def partitionByList(self, numeratorList):
        '''Given a numerator list, partition MeterSequence inot a new list
        of MeterTerminals

        >>> a = MeterSequence('4/4')
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

        elif sum(numeratorList) == self.numerator:
            optMatch = []
            for n in numeratorList:
                optMatch.append('%s/%s' % (n, self.denominator))

        # low integer multiples
        elif sum(numeratorList) == self.numerator * 2:
            optMatch = []
            for n in numeratorList:
                optMatch.append('%s/%s' % (n, self.denominator * 2))
        elif sum(numeratorList) == self.numerator * 3:
            optMatch = []
            for n in numeratorList:
                optMatch.append('%s/%s' % (n, self.denominator * 3))
        elif sum(numeratorList) == self.numerator * 4:
            optMatch = []
            for n in numeratorList:
                optMatch.append('%s/%s' % (n, self.denominator * 4))

        # last resot: search options
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
            raise MeterException('Cannot set partition by %s' % numeratorList)


    def partitionByOther(self, other):
        '''Set partition to that found in another object

        >>> a = MeterSequence('4/4', 4)
        >>> b = MeterSequence('4/4', 2)
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

    def partition(self, value):
        ''' Partitioning creates and sets a number of MeterTerminals that make up this MeterSequence.

        A simple way to partition based on arguement time. Single integers are treated as beat counts; lists are treated as numerator lists; MeterSequence objects are call partitionByOther(). 

        >>> a = MeterSequence('5/4+3/8')
        >>> len(a)
        2
        >>> b = MeterSequence('13/8')
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


    #---------------------------------------------------------------------------
    # loading is always destructive

    def load(self, value, partitionRequest=None, autoWeight=False,
            targetWeight=None):
        '''This method is called when a MeterSequence is created, or if a MeterSequece is re-set. 

        User can enter a list of values or an abbreviated slash notation.

        autoWeight, if True, will attempt to set weights.
        tragetWeight, if given, will be used instead of self.weight        

        >>> a = MeterSequence()
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
        if autoWeight:
            if targetWeight != None:
                targetWeight = targetWeight
            else: # get from current MeterSequence
                targetWeight = self.weight # store old
        else: # None will not set any value
            targetWeight = None

        #environLocal.printDebug(['calling load in MeterSequence, got targetWeight', targetWeight])

        if common.isStr(value):
            self._clearPartition()
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
            self._clearPartition()
            self._addTerminal(value) 
            self._updateRatio()
            # do not need to set weight, as based on terminal
            #environLocal.printDebug(['created MeterSequence from MeterTerminal; old weight, new weight', value.weight, self.weight])
    
        elif common.isListLike(value): # a list of Terminals or Sequenc es
            self._clearPartition()
            for obj in value:
                #environLocal.printDebug('creating MeterSequence with %s' % obj)
                self._addTerminal(obj) 
            self._updateRatio()
            self.weight = targetWeight # may be None
        else:
            raise MeterException('cannot create a MeterSequence with a %s' % repr(value))

        if partitionRequest != None:
            self.partition(partitionRequest)

    
    def _updateRatio(self):
        '''Look at _partition to determine the total
        numerator and denominator values for this sequence

        This should only be called internally, as MeterSequences
        are supposed to be immutable (mostly)
        '''
        fList = [(mt.numerator, mt.denominator) for mt in self._partition]
        # clear first to avoid partial updating
        # can only set to private attributes
        self._numerator, self._denominator = None, 1            
        self._numerator, self._denominator = fractionSum(fList)
        self._ratioChanged()



    #---------------------------------------------------------------------------
    # properties
    # do not permit setting of numerator/denominator

    def _getWeight(self):
        '''
        >>> a = MeterSequence('3/4')
        >>> a.partition(3)
        >>> a.weight = 1
        >>> a[0].weight
        0.333...
        >>> b = MeterTerminal('1/4', .25)
        >>> c = MeterTerminal('1/4', .25)
        >>> d = MeterSequence([b, c])
        >>> d.weight
        0.5
        '''
        sum = 0
        for obj in self:
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
            totalRatio = self.numerator / float(self.denominator)
            for mt in self:
                partRatio = mt.numerator / float(mt.denominator)
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

        This retursn a list and not a new MeterSequence b/c MeterSequence objects are generally immutable and thus it does not make sense
        to concatenate them.

        >>> a = MeterSequence('3/4')
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
        for obj in self:
            if not isinstance(obj, MeterSequence):
                mtList.append(obj)
            else: # its a meter sequence
                mtList += obj._getFlatList()
        return mtList

    def _getFlat(self):
        '''Retrun a new MeterSequence composed of the flattend representation.

        >>> a = MeterSequence('3/4', 3)
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



    #---------------------------------------------------------------------------
    # alternative representations



    def _getLevelList(self, levelCount, flat=True):
        '''Recursive utility function

        >>> b = MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> MeterSequence(b._getLevelList(0))
        <MeterSequence {1/4+1/4+1/4+1/4}>
        >>> MeterSequence(b._getLevelList(1))
        <MeterSequence {1/4+1/8+1/8+1/4+1/8+1/8}>
        >>> MeterSequence(b._getLevelList(2))
        <MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        >>> MeterSequence(b._getLevelList(3))
        <MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        '''
        mtList = []
        for i in range(len(self)):
            #environLocal.printDebug(['_getLevelList weight', i, self[i].weight])
            if not isinstance(self[i], MeterSequence):
                mt = self[i] # a meter terminal
                mtList.append(mt)   
            else: # its a sequence
                if levelCount > 0: # retain this sequence but get lower level
                    # reduce level by 1 when recursing; do not
                    # change levelCount here
                    mtList += self[i]._getLevelList(levelCount-1, flat)
                else: # level count is at zero
                    if flat: # make sequence into a terminal
                        mt = MeterTerminal('%s/%s' % (
                                  self[i].numerator, self[i].denominator))
                        # set weight to that of the sequence
                        mt.weight = self[i].weight
                        mtList.append(mt)   
                    else: # its not a terminal, its a meter sequence
                        mtList.append(self[i])   
        return mtList


    def getLevel(self, level=0, flat=True):
        '''Return a complete MeterSequence with the same numerator/denominator
        reationship but that represents any partitions found at the rquested
        level. A sort of flatness with variable depth.
        
        >>> b = MeterSequence('4/4', 4)
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

        >>> b = MeterSequence('4/4', 4)
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

        >>> a = MeterSequence('4/4', 4)
        >>> a.getLevelWeight()
        [0.25, 0.25, 0.25, 0.25]

        >>> b = MeterSequence('4/4', 4)
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

    

    #---------------------------------------------------------------------------
    # given a quarter note position, return the active index

    def positionToIndex(self, qLenPos, includeCoincidentBoundaries=False):
        '''Given a qLen pos (0 through self.duration.quarterLength), return
        the active MeterTerminal or MeterSequence

        >>> a = MeterSequence('4/4')
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

        >>> a = MeterSequence('3/4', 3)
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

        >>> a = MeterSequence('3/4', 3)
        >>> a.positionToSpan(.5)
        (0, 1.0)
        >>> a.positionToSpan(1.5)
        (1.0, 2.0)

        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException('cannot access from qLenPos %s' % qLenPos)
        
        iMatch = self.positionToIndex(qLenPos)
        
        pos = 0
        for i in range(len(self)):
            if i == iMatch:
                start = pos
                end = pos + self[i].duration.quarterLength
            else:
                pos += self[i].duration.quarterLength
        return start, end


    def positionToDepth(self, qLenPos, align='quantize'):
        '''Given a qLenPos, return the maximum available depth at this position

        >>> b = MeterSequence('4/4', 4)
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

    def __init__(self, value=None, partitionRequest=None):
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
        # creates .display, .beam, .beat, .accent
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
    def _setDefaultBeamPartitions(self):
 
        # more general, based only on numerator
        if self.numerator in [2, 3, 4]:
            self.beam.partition(self.numerator)
            # if denominator is 4, subdivide each partition
            if self.denominator in [4]:
                for i in range(len(self.beam)): # subdivide  each beat in 2
                    self.beam[i] = self.beam[i].subdivide(2)

        elif self.numerator == 5:
            default = [2,3]
            self.beam.partition(default)
            # if denominator is 4, subdivide each partition
            if self.denominator in [4]:
                for i in range(len(self.beam)): # subdivide  each beat in 2
                    self.beam[i] = self.beam[i].subdivide(default[i])

        elif self.numerator == 7:
            self.beam.partition(3)

        elif self.numerator in [6,9,12,15,18,21]:
            self.beam.partition([3] * (self.numerator / 3))
        else:
            pass # doing nothing will beam all together

        #environLocal.printDebug('default beam partitions set to: %s' % self.beam)


    def load(self, value, partitionRequest=None):
        '''Loading a meter destroys all internal representations
        '''
        # create parallel MeterSequence objects to provide all data
        # these all refer to the same .numerator/.denominator 
        # relationship

        # used for drawing the time signature symbol
        # this is the only one that can be  unlinked
        # generaly not partitioned as others?
        self.display = MeterSequence(value)
        # used for beaming
        self.beam = MeterSequence(value, partitionRequest)
        # used for getting beat divisions
        self.beat = MeterSequence(value, partitionRequest)
        # used for setting one level of accents
        self.accent = MeterSequence(value, partitionRequest)

        # update summed numerator based on import
        # all have the same value
        self.summedNumerator = self.display.summedNumerator

        if partitionRequest == None: # set default beam partitions
            self._setDefaultBeamPartitions()


    def loadRatio(self, numerator, denominator, partitionRequest=None):
        '''Convenience method
        '''
        value = '%s/%s' % (numerator, denominator)
        self.load(value, partitionRequest)


    #---------------------------------------------------------------------------
    # properties

    # temp for backward compat
    def _getTotalLength(self):
        return self.beam.duration.quarterLength
 
    totalLength = property(_getTotalLength)

    def _getNumerator(self):
        return self.beam.numerator

    numerator = property(_getNumerator)

    def _getDenominator(self):
        return self.beam.denominator

    denominator = property(_getDenominator)



    def _getBarDuration(self):
        '''
        barDuration gets or sets a duration value that
        is equal in length to the totalLength
        
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
            # could come from self.beam, self.accent, self.display, self.accent 
            return self.beam.duration

    def _setBarDuration(self, value):
        self._overriddenBarDuration = value

    barDuration = property(_getBarDuration, _setBarDuration)


    def _getBeatLengthToQuarterLengthRatio(self):
        '''
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
    # access data for other processing

    def getBeams(self, srcList):
        '''Given a qLen position and a list of Duration objects, return a list of Beams object.

        Can alternatively provide a flat stream, from which Durations are extracted.

        Duration objects are assumed to be adjoining; offsets are not used.

        This can be modified to take lists of rests and notes

        Must process a list at  time, because we cannot tell when a beam ends
        unless we see the context of adjoining durations.

        >>> a = TimeSignature('2/4', 2)
        >>> a.beam[0] = a.beam[0].subdivide(2)
        >>> a.beam[1] = a.beam[1].subdivide(2)
        >>> a.beam
        <MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> b = [duration.Duration('16th')] * 8
        >>> c = a.getBeams(b)
        >>> len(c) == len(b)
        True
        >>> print(c)
        [<music21.note.Beams <music21.note.Beam 1/start>/<music21.note.Beam 2/start>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/stop>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/start>>, <music21.note.Beams <music21.note.Beam 1/stop>/<music21.note.Beam 2/stop>>, <music21.note.Beams <music21.note.Beam 1/start>/<music21.note.Beam 2/start>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/stop>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/start>>, <music21.note.Beams <music21.note.Beam 1/stop>/<music21.note.Beam 2/stop>>]

        >>> a = TimeSignature('6/8')
        >>> b = [duration.Duration('eighth')] * 6
        >>> c = a.getBeams(b)
        >>> print(c)
        [<music21.note.Beams <music21.note.Beam 1/start>>, <music21.note.Beams <music21.note.Beam 1/continue>>, <music21.note.Beams <music21.note.Beam 1/stop>>, <music21.note.Beams <music21.note.Beam 1/start>>, <music21.note.Beams <music21.note.Beam 1/continue>>, <music21.note.Beams <music21.note.Beam 1/stop>>]
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
            elif srcStream != None and isinstance(srcStream[i], note.Rest):
                beamsList.append(None) # placeholder
            else:
                # we have a beamable duration
                b = note.Beams()
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
                archetype = self.beam.getLevel(depth)
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

        >>> a = TimeSignature()
        >>> a.load('3/4')
        >>> a.setDisplay('2/8+2/8+2/8')
        >>> a.display
        <MeterSequence {2/8+2/8+2/8}>
        >>> a.beam
        <MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
        >>> a.beat
        <MeterSequence {3/4}>
        >>> a.setDisplay(a.beat)
        >>> a.display
        <MeterSequence {3/4}>
        '''
        if isinstance(value, MeterSequence): # can set to an existing meterseq
            # must make a copy
            self.display = copy.deepcopy(value)
        else:
            # create a new object; it will not be linked
            self.display = MeterSequence(value, partitionRequest)

        # need to update summed numerator states
        self.summedNumerator = self.display.summedNumerator


    def getAccent(self, qLenPos):
        '''Return true or false if the qLenPos is at the start of an accent
        division

        >>> a = TimeSignature('3/4', 3)
        >>> a.accent.partition([2,1])
        >>> a.accent
        <MeterSequence {2/4+1/4}>
        >>> a.getAccent(0)
        True
        >>> a.getAccent(1)
        False
        >>> a.getAccent(2)
        True
        '''
        pos = 0
        for i in range(len(self.accent)):
            if common.almostEquals(pos, qLenPos):
                return True
            pos += self.accent[i].duration.quarterLength
        return False


    def setAccentWeight(self, weightList, level=0):
        '''Set accent weight, or floating point scalars, for the accent MeterSequence. Provide a list of values; if this list is shorter than the length of the MeterSequence, it will be looped; if this list is longer, only the first relevant value will be used.

        If the accent MeterSequence is subdivided, the level of depth to set is given by the optional level argument.

        >>> a = TimeSignature('4/4', 4)
        >>> len(a.accent)
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

        msLevel = self.accent.getLevel(level)
        for i in range(len(msLevel)):
            msLevel[i].weight = weightList[i % len(weightList)]

    def getAccentWeight(self, qLenPos, level=0):
        '''Given a qLenPos,  return an accent level. 
        '''
        msLevel = self.accent.getLevel(level)
        return msLevel[msLevel.positionToIndex(qLenPos)].weight

    def getBeat(self, qLenPos):
        '''Given a quarterLenght position, get the beat, where beats count from 1

        >>> a = TimeSignature('3/4', 3)
        >>> a.getBeat(0)
        1
        >>> a.getBeat(2.5)
        3
        >>> a.beat.partition(['3/8', '3/8'])
        >>> a.getBeat(2.5)
        2
        '''
        return self.beat.positionToIndex(qLenPos) + 1


    def getBeatProgress(self, qLenPos):
        '''Given a quarterLenght position, get the beat, where beats count from 1, and return the the amount of qLen into this beat the supplied qLenPos
        is. 

        >>> a = TimeSignature('3/4', 3)
        >>> a.getBeatProgress(0)
        (1, 0)
        >>> a.getBeatProgress(0.75)
        (1, 0.75)
        >>> a.getBeatProgress(2.5)
        (3, 0.5)
        >>> a.beat.partition(['3/8', '3/8'])
        >>> a.getBeatProgress(2.5)
        (2, 1.0)
        '''
        beatIndex = self.beat.positionToIndex(qLenPos)
        start, end = self.beat.positionToSpan(qLenPos)
        return beatIndex + 1, qLenPos - start


    def getBeatDepth(self, qLenPos, align='quantize'):
        '''
        >>> a = TimeSignature('3/4', 3)
        >>> a.getBeatDepth(0)
        1
        >>> a.getBeatDepth(1)
        1
        >>> a.getBeatDepth(2)
        1

        >>> b = TimeSignature('3/4', 1)
        >>> b.beat[0] = b.beat[0].subdivide(3)
        >>> b.beat[0][0] = b.beat[0][0].subdivide(2)
        >>> b.beat[0][1] = b.beat[0][1].subdivide(2)
        >>> b.beat[0][2] = b.beat[0][2].subdivide(2)
        >>> b.getBeatDepth(0)
        3
        >>> b.getBeatDepth(.5)
        1
        >>> b.getBeatDepth(1)
        2
        '''
        return self.beat.positionToDepth(qLenPos, align)



    def quarterPositionToBeat(self, currentQtrPosition = 0):
        '''For backward compatibility. Ultimately, remove. 
        '''
        #return ((currentQtrPosition * self.quarterLengthToBeatLengthRatio) + 1)
        return self.getBeat(currentQtrPosition)
    


    #---------------------------------------------------------------------------
    def _getLily(self):
        '''
        returns the lilypond representation of the timeSignature
        
        >>> a = TimeSignature('3/16')
        >>> a.lily
        \\time 3/16
        '''
        
        # TODO: values need to be taken from self.display

        if self._lilyOut is not None:
            return self._lilyOut
        return lily.LilyString("\\time " + str(self) + " ")
    
    def _setLily(self, newLily):
        self._lilyOut = newLily
    
    lily = property(_getLily, _setLily)



    def _getMX(self):
        '''Returns a list of one mxTime object.
        
        Compound meters are represented as multiple pairs of beat
        and beat-type elements

        >>> a = TimeSignature('3/4')
        >>> b = a.mx
        >>> a = TimeSignature('3/4+2/4')
        >>> b = a.mx

        '''
        mxTimeList = []
        mxTime = musicxml.Time()
        
        # always get a flat version to display any subivisions created
        fList = [(mt.numerator, mt.denominator) for mt in self.display.flat]
        if self.summedNumerator:
            # this will try to reduce any common denominators into 
            # a common group
            fList = fractionToSlashMixed(fList)

        for n,d in fList:
            mxBeats = musicxml.Beats(n)
            mxBeatType = musicxml.BeatType(d)
            mxTime.componentList.append(mxBeats)
            mxTime.componentList.append(mxBeatType)

        # can set this to common when necessary
        mxTime.set('symbol', None)
        # for declaring no time signature present
        mxTime.set('senza-misura', None)
        mxTimeList.append(mxTime)
        return mxTimeList


    def _setMX(self, mxTimeList):
        '''Given an mxTimeList, load this object 
        >>> a = musicxml.Time()
        >>> a.setDefaults()
        >>> b = musicxml.Attributes()
        >>> b.timeList.append(a)
        >>> c = TimeSignature()
        >>> c.mx = b.timeList
        >>> c.numerator
        4
        '''
        if len(mxTimeList) == 0:
            raise MeterException('cannot create a TimeSignature from an empty MusicXML timeList: %s' % musicxml.Attributes() )
        mxTime = mxTimeList[0] # only one for now
        n = []
        d = []
        for obj in mxTime.componentList:
            if isinstance(obj, musicxml.Beats):
                n.append(obj.charData) # may be 3+2
            if isinstance(obj, musicxml.BeatType):
                d.append(obj.charData)
        assert len(n) == len(d)

        #n = mxTime.get('beats')
        #d = mxTime.get('beat-type')
        # convert into a string
        msg = []
        for i in range(len(n)):
            msg.append('%s/%s' % (n[i], d[i]))

        #environLocal.printDebug(['loading meter string:', '+'.join(msg)])
        self.load('+'.join(msg))

    mx = property(_getMX, _setMX)




    def _getMusicXML(self):
        '''Return a complete MusicXML string
        '''
        mxAttributes = musicxml.Attributes()
        # need a lost of time 
        mxAttributes.set('time', self._getMX())

        mxMeasure = musicxml.Measure()
        mxMeasure.setDefaults()
        mxMeasure.set('attributes', mxAttributes)

        mxPart = musicxml.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure)

        mxScorePart = musicxml.ScorePart()
        mxScorePart.setDefaults()
        mxPartList = musicxml.PartList()
        mxPartList.append(mxScorePart)

        mxIdentification = musicxml.Identification()
        mxIdentification.setDefaults() # will create a composer

        mxScore = musicxml.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)
        return mxScore.xmlStr()


    def _setMusicXML(self, mxNote):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)






#-------------------------------------------------------------------------------

class CompoundTimeSignature(TimeSignature):
    pass

class DurationDenominatorTimeSignature(TimeSignature):
    '''If you have played Hindemith you know these, 3/(dot-quarter) etc.'''
    pass

class NonPowerOfTwoTimeSignature(TimeSignature):
    pass



















#-----------------------------------------------------------------||||||||||||--
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
        from music21 import stream
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
        match = '''[<music21.note.Beams <music21.note.Beam 1/start>/<music21.note.Beam 2/start>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/continue>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/continue>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/stop>>, <music21.note.Beams <music21.note.Beam 1/stop>>, <music21.note.Beams <music21.note.Beam 1/start>/<music21.note.Beam 2/start>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/continue>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/continue>>, <music21.note.Beams <music21.note.Beam 1/continue>/<music21.note.Beam 2/stop>>, <music21.note.Beams <music21.note.Beam 1/stop>>]'''

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



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TimeSignature, CompoundTimeSignature]


if __name__ == "__main__":
    #music21.mainTest(Test, TestExternal)
    music21.mainTest(Test)




