#-------------------------------------------------------------------------------
# Name:         meter.py
# Purpose:      Classes for meters
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
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
_MOD = 'meter'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

validDenominators = [1,2,4,8,16,32,64] # in order

def slashToFraction(value):
    '''
    TODO: it seems like this should return only integers; not sure
    why these originally were floats.

    >>> slashToFraction('3/8')
    (3, 8)
    >>> slashToFraction('7/32')
    (7, 32)

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



#-------------------------------------------------------------------------------
class MeterTerminal(object):
    '''A meter is a nestable primitive of rhythmic division

    This object might also store accent patterns based on numerator or
    set as another internal representation.

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
    def __init__(self, slashNotation=None):
        self._numerator   = 0     # musicXML: beats
        self._denominator = 1     # musicXML: beat-type
        self._overriddenDuration = None

        if slashNotation != None:
            self.numerator, self.denominator = slashToFraction(slashNotation)
        self._ratioChanged() # sets self._duration


    def __str__(self):
        return str(int(self.numerator)) + "/" + str(int(self.denominator))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        '''Equality. 

        >>> a = MeterTerminal('2/4')
        >>> b = MeterTerminal('3/4')
        '''
#         if not isinstnace(other, MeterTerminal):
#             return False
        if other == None: return False
        if (other.numerator == self.numerator and 
            other.denominator == self.denominator):
            return True
        else:
            return False

    def __ne__(self, other):
        '''Inequality.
        '''
#         if not isinstnace(other, MeterTerminal):
#             return True
        if other == None: return True
        if (other.numerator == self.numerator and 
            other.denominator == self.denominator):
            return False
        else:
            return True



    def deepcopy(self):
        '''Return a complete copy. Here, copy and deepcopy should be the same.
        >>> a = MeterTerminal('2/4')
        >>> b = a.deepcopy()
        '''
        return copy.deepcopy(self)
  


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
        ms.load(self, countRequest)
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
        ms.load(self)
        ms.partitionByList(numeratorList)
        return ms    

    def subdivide(self, value):
        '''Retuirn a MeterSequence

        If an integer is provided, assume it is a partition count
        '''
        if common.isListLike(value):
            return self.subdivideByList(value)
        else:
            return self.subdivideByCount(value)



    #---------------------------------------------------------------------------
    # properties

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

        if value != None:
            self.load(value, partitionRequest)

    def __str__(self):
        msg = []
        for mt in self._partition:
            msg.append(str(mt))
        return '{%s}' % '+'.join(msg)

    def __repr__(self):
        return self.__str__()

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
        self._index = 0 
        return self

    def next(self):
        '''Top-level partitions are iterated

        >>> a = MeterSequence('4/4', 4)
        >>> len(a)
        4
        >>> sum = 0
        >>> for x in a: sum += x.numerator
        >>> sum
        4
        '''
        if abs(self._index) >= self.__len__():
            self._index = 0 # reset for next run
            raise StopIteration
        out = self._partition[self._index]
        self._index += 1
        return out


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
        {{1/8+1/8}+1/4+1/4+1/4}
        >>> a[0][0] = a[0][0].subdivide(2)
        >>> a
        {{{1/16+1/16}+1/8}+1/4+1/4+1/4}
        >>> a[3] = a[0][0].subdivide(2)
        Traceback (most recent call last):
        ...
        MeterException: cannot insert {1/16+1/16} into space of 1/4
        '''
        if value == self[key]: # comparison of nuemrator and denominator
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
        [['1/4', '1/4', '1/4', '1/4'], ['1/2', '1/2'], ['4/4'], ['2/4', '2/4'], ['2/2'], ['1/1'], ['8/8'], ['16/16'], ['32/32'], ['64/64']]

        >>> a._divisionOptionsAlgo(1,4)
        [['1/4'], ['1/8', '1/8'], ['1/16', '1/16', '1/16', '1/16'], ['1/32', '1/32', '1/32', '1/32', '1/32', '1/32', '1/32', '1/32'], ['1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64', '1/64'], ['2/8'], ['4/16'], ['8/32'], ['16/64']]

        >>> a._divisionOptionsAlgo(2,2)
        [['1/2', '1/2'], ['2/2'], ['1/1'], ['4/4'], ['8/8'], ['16/16'], ['32/32'], ['64/64']]


        >>> a._divisionOptionsAlgo(3,8)
        [['1/8', '1/8', '1/8'], ['3/8'], ['6/16'], ['12/32'], ['24/64']]

        >>> a._divisionOptionsAlgo(6,8)
        [['3/8', '3/8'], ['1/8', '1/8', '1/8', '1/8', '1/8', '1/8'], ['1/4', '1/4', '1/4'], ['6/8'], ['3/4'], ['12/16'], ['24/32'], ['48/64']]

        >>> a._divisionOptionsAlgo(12,8)
        [['3/8', '3/8', '3/8', '3/8'], ['1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8', '1/8'], ['1/4', '1/4', '1/4', '1/4', '1/4', '1/4'], ['1/2', '1/2', '1/2'], ['12/8'], ['6/8', '6/8'], ['6/4'], ['3/2'], ['24/16'], ['48/32'], ['96/64']]


        >>> a._divisionOptionsAlgo(5,8)
        [['2/8', '3/8'], ['3/8', '2/8'], ['1/8', '1/8', '1/8', '1/8', '1/8'], ['5/8'], ['10/16'], ['20/32'], ['40/64']]

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
        '''
        if common.isStr(value):
            self._partition.append(MeterTerminal(value))
        elif isinstance(value, MeterTerminal):
            self._partition.append(value)
        else:
            raise MeterException('cannot add %s to this sequence' % value)

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
            self._clearPartition()
            for mStr in optMatch:
                self._addTerminal(mStr)
        else:
            raise MeterException('Cannot set partition by %s' % countRequest)


    def partitionByList(self, numeratorList):
        '''
        >>> a = MeterSequence('4/4')
        >>> a.partitionByList([1,1,1,1])
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'
        >>> a.partitionByList(['3/4', '1/8', '1/8'])
        >>> a
        {3/4+1/8+1/8}
        >>> a.partitionByList(['3/4', '1/8', '5/8'])
        Traceback (most recent call last):
        MeterException: Cannot set partition by ['3/4', '1/8', '5/8']

        '''
        # assume a lost of terminal definitions
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


        else: # search options
            opts = self._getOptions()
            optMatch = None
            for opt in opts:
                # get numerators as numbers
                nFound = [int(x.split('/')[0]) for x in opt]
                if nFound == numeratorList:
                    optMatch = opt
                    break

        if optMatch != None:
            self._clearPartition()
            for mStr in optMatch:
                self._addTerminal(mStr)
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
        if (self.numerator == other.numerator and self.denominator ==     
            other.denominator):

            self._clearPartition()
            for mt in other:
                self._addTerminal(mt.deepcopy())
        else:
            raise MeterException('Cannot set partition for unequal MeterSequences')

    def partition(self, value):
        '''A simple way to partition based on arguement time. Single integers are treated as beat counts; lists are treated as numerator lists; MeterSequence objects are call partitionByOther(). 

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

    def load(self, value, partitionRequest=None):
        '''User can enter a list of values or an abbreviated slash notation

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
        if common.isStr(value):
            self._clearPartition()
            ratioList = slashCompoundToFraction(value)
            for n,d in ratioList:
                slashNotation = '%s/%s' % (n,d)
                #print _MOD, 'candidate slash', slashNotation
                self._addTerminal(MeterTerminal(slashNotation)) 
            self._updateRatio()
        elif isinstance(value, MeterTerminal):
            self._clearPartition()
            self._addTerminal(value) 
            self._updateRatio()
        elif common.isListLike(value): # a lost of Terminals
            self._clearPartition()
            for obj in value:
                self._addTerminal(obj) 
            self._updateRatio()

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
    # do not permit setting of numerator

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
        {1/4+{1/16+1/16+1/16+1/16}+1/4}
        >>> len(a)
        3
        >>> b = a._getFlatList()
        >>> len(b)
        6

        >>> a[1][2] = a[1][2].subdivide(4)
        >>> a
        {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}
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
        {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}
        >>> b = a.flat
        >>> len(b)
        9

        '''
        post = MeterSequence()
        post.load(self._getFlatList())
        return post

    flat = property(_getFlat)



    #---------------------------------------------------------------------------
    # given a quarter note position, return the active index

    def positionToIndex(self, qLenPos, includeCoincidentBoundaries=False):
        '''Given a qLen pos (0 through self.duration.quarterLength), return
        the active MeterTerminal or MeterSequence

        >>> a = MeterSequence('4/4')
        >>> a.positionToIndex(5)
        Traceback (most recent call last):
        ...
        MeterException: cannot access from qLenPos 5

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
            raise MeterException('cannot access from qLenPos %s' % qLenPos)

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
                if qLenPos >= start and qLenPos < end:
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
        {1/4+{1/16+1/16+1/16+1/16}+1/4}
        >>> len(a)
        3
        >>> a.positionToAddress(.5)
        [0]
        >>> a[0]    
        1/4
        >>> a.positionToAddress(1.0)
        [1, 0]
        >>> a.positionToAddress(1.5)
        [1, 2]
        >>> a[1][2]
        1/16
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







#-------------------------------------------------------------------------------
class _TimeSignature(music21.Music21Object):

    def __init__(self, value=None, partitionRequest=None):
        music21.Music21Object.__init__(self)

        # whether the TimeSignature object is inherited from 
        self.inherited = False 
        self._lilyOut = None    
        self.symbol = "" # common, cut, single-number, normal
                    # a difference from musicXML: empty is different from normal:
                    #   normal = 4/4;  empty lets the interpreting program decide
                    # does not do anything at present

        # a parameter to determin if the denominator is represented
        # as either a symbol (a note) or as a numebr
        self.symbolizeDenominator = False
        self._overriddenBarDuration = None

        # creates MeterSequence data representations
        # creates .display, .beam, .beat, .accent
        self.load(value, partitionRequest)

    def __str__(self):
        return str(int(self.numerator)) + "/" + str(int(self.denominator))

    def __repr__(self):
        return "<music21.meter.TimeSignature %s>" % self.__str__()



    #---------------------------------------------------------------------------
    def load(self, value, partitionRequest=None):
        '''Loading a meter destroys all internal representations
        '''
        # create parallel MeterSequence objects to provide all data
        # these all refer to the same .numerator/.denominator 
        # relationship

        # used for drawing the time signature
        self.display = MeterSequence(value, partitionRequest)
        # used for beaming
        self.beam = MeterSequence(value, partitionRequest)
        # used for getting beat divisions
        self.beat = MeterSequence(value, partitionRequest)
        # used for setting one level of accents
        self.accent = MeterSequence(value, partitionRequest)


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
        
        >>> a = _TimeSignature('3/8')
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
            return self.beam.duration

    def _setBarDuration(self, value):
        self._overriddenBarDuration = value

    barDuration = property(_getBarDuration, _setBarDuration)


    def _getBeatLengthToQuarterLengthRatio(self):
        '''
        >>> a = _TimeSignature('3/2')
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
    # not implemented

    def getBeam(self, qLenPos):
        pass

    def getAccent(self, qLenPos):
        '''Return true or false if the qLenPos is at the start of an accent
        '''
        pass

    def getBeat(self, qLenPos):
        '''Get the beat, where beats count from 1

        >>> a = _TimeSignature('3/4', 3)
        >>> a.getBeat(0)
        1
        >>> a.getBeat(2.5)
        3
        >>> a.beat.partition(['3/8', '3/8'])
        >>> a.getBeat(2.5)
        2
        '''

        return self.beat.positionToIndex(qLenPos) + 1


    def quarterPositionToBeat(self, currentQtrPosition = 0):
        '''For backward compatibility.
        '''
        return self_getBeat(qLenPos)
    


    #---------------------------------------------------------------------------
    def _getLily(self):
        '''
        returns the lilypond representation of the timeSignature
        
        >>> a = _TimeSignature('3/16')
        >>> a.lily
        \\time 3/16
        '''
        
        if self._lilyOut is not None:
            return self._lilyOut
        return lily.LilyString("\\time " + str(self) + " ")
    
    def _setLily(self, newLily):
        self._lilyOut = newLily
    
    lily = property(_getLily, _setLily)



    def _getMX(self):
        '''Returns a lost of one or more mxTime objects.
        
        Compound meters are represented as multiple pairs of beat
        and beat-type elements

        >>> a = _TimeSignature('3/4')
        >>> b = a.mx
        '''
        mxTime = musicxml.Time()
        mxTime.set('beats', int(self.numerator))
        mxTime.set('beat-type', int(self.denominator))
        # can set this to common when necessary
        mxTime.set('symbol', None)
        # for declaring no time signature present
        mxTime.set('senza-misura', None)
        # number is for assigning to staves
        mxTime.set('senza-misura', None)

        mxTimeList = []
        mxTimeList.append(mxTime)
        return mxTimeList


    def _setMX(self, mxAttributes):
        '''Given an mxAttributute object, load this object 
        >>> a = musicxml.Time()
        >>> a.set('beats', 3)
        >>> a.set('beat-type', 8)
        >>> b = musicxml.Attributes()
        >>> b.timeList.append(a)
        >>> c = _TimeSignature()
        >>> c.mx = b
        >>> c.numerator
        3
        '''
        mxTimeList = mxAttributes.timeList
        # only take the first until we can accomodate compound
        for mxTime in mxTimeList[:1]:
            # for combound meters, this may be a 3+2 string
            n = int(mxTime.get('beats'))
            d = int(mxTime.get('beat-type'))
            self.loadRatio(n, d)

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

class TimeSignature(music21.Music21Object):
    inherited   = False # whether the TimeSignature object is inherited from 
    _lilyOut = None    
    symbol = "" # common, cut, single-number, normal
                # a difference from musicXML: empty is different from normal:
                #   normal = 4/4;  empty lets the interpreting program decide
                # does not do anything at present

    def __init__(self, asSlash = ""):
        music21.Music21Object.__init__(self)

        self._barDuration = duration.Duration()
        self._overriddenBarDuration = None

        self._numerator   = 0     # musicXML: beats
        self._denominator = 1     # musicXML: beat-type


        if (asSlash):
            asSlash = asSlash.strip() # rem whitespace
            matches = re.match("(\d+)\/(\d+)", asSlash)
            if matches is not None:
                self._numerator = float(matches.group(1))
                self._denominator = float(matches.group(2))

        #self.beatLengthToQuarterLengthRatio = 4.0/self.denominator
        #self.quarterLengthToBeatLengthRatio = self.denominator/4.0
        self._ratioChanged()


    def __str__(self):
        return str(int(self.numerator)) + "/" + str(int(self.denominator))

    def __repr__(self):
        return "<music21.meter.TimeSignature %s>" % self.__str__()


    # temp for backward compat
    def _getTotalLength(self):
        return self._barDuration.quarterLength
 
    totalLength = property(_getTotalLength)



    def _getNumerator(self):
        return self._numerator

    def _setNumerator(self, value):
        self._numerator = value
        self._ratioChanged()

    numerator = property(_getNumerator, _setNumerator)



    def _getDenominator(self):
        return self._denominator

    def _setDenominator(self, value):
        self._denominator = value
        self._ratioChanged()

    denominator = property(_getDenominator, _setDenominator)




    def _ratioChanged(self):
        '''If ratio has been changed, call this to update
        barDuration 
        '''
        self._barDuration = duration.Duration()
        try:
            self._barDuration.quarterLength = ((4.0 * 
                        self.numerator)/self.denominator)
        except duration.DurationException:
            environLocal.printDebug(['DuratioinException encountered', 
                'numerator/denominator', self.numerator, self.denominator])
            self._barDuration = None


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
            return self._barDuration


    def _setBarDuration(self, value):
        self._overriddenBarDuration = value

    barDuration = property(_getBarDuration, _setBarDuration)



    def _getBeatLengthToQuarterLengthRatio(self):
        '''
        >>> a = TimeSignature()
        >>> a.numerator = 3
        >>> a.denominator = 2
        >>> a.beatLengthToQuarterLengthRatio
        2.0
        '''
        return 4.0/self.denominator

    beatLengthToQuarterLengthRatio = property(_getBeatLengthToQuarterLengthRatio)


    def _getQuarterLengthToBeatLengthRatio(self):
        return self.denominator/4.0

    quarterLengthToBeatLengthRatio = property(_getQuarterLengthToBeatLengthRatio)



    #---------------------------------------------------------------------------
    # not implemented
    def setBeamDivisions(self, beamDivs):
        pass


    #---------------------------------------------------------------------------
    # utility methods
    def quarterPositionToBeat(self, currentQtrPosition = 0):
        return ((currentQtrPosition * self.quarterLengthToBeatLengthRatio) + 1)
    


    #---------------------------------------------------------------------------
    def _getLily(self):
        '''
        returns the lilypond representation of the timeSignature
        
        >>> a = TimeSignature('3/16')
        >>> a.lily
        \\time 3/16
        '''
        
        if self._lilyOut is not None:
            return self._lilyOut
        return lily.LilyString("\\time " + str(self) + " ")
    
    def _setLily(self, newLily):
        self._lilyOut = newLily
    
    lily = property(_getLily, _setLily)



    def _getMX(self):
        '''Returns a lost of one or more mxTime objects.
        
        Compound meters are represented as multiple pairs of beat
        and beat-type elements

        >>> a = TimeSignature('3/4')
        >>> b = a.mx
        '''
        mxTime = musicxml.Time()
        mxTime.set('beats', int(self.numerator))
        mxTime.set('beat-type', int(self.denominator))
        # can set this to common when necessary
        mxTime.set('symbol', None)
        # for declaring no time signature present
        mxTime.set('senza-misura', None)
        # number is for assigning to staves
        mxTime.set('senza-misura', None)

        mxTimeList = []
        mxTimeList.append(mxTime)
        return mxTimeList


    def _setMX(self, mxAttributes):
        '''Given an mxAttributute object, load this object 
        >>> a = musicxml.Time()
        >>> a.set('beats', 3)
        >>> a.set('beat-type', 8)
        >>> b = musicxml.Attributes()
        >>> b.timeList.append(a)
        >>> c = TimeSignature()
        >>> c.mx = b
        >>> c.numerator
        3
        '''
        mxTimeList = mxAttributes.timeList
        # only take the first until we can accomodate compound
        for mxTime in mxTimeList[:1]:
            # for combound meters, this may be a 3+2 string
            self.numerator = int(mxTime.get('beats'))
            self.denominator = int(mxTime.get('beat-type'))

        self._ratioChanged()


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
                ts = TimeSignature('%s/%s' % (meterStrNumerator, 
                                            meterStrDenominator))
                m = stream.Measure()
                m.timeSignature = ts
                a.insertAtOffset(m, m.timeSignature.barDuration.quarterLength)
        a.show()


class Test(unittest.TestCase):
    '''Unit tests
    '''

    def runTest(self):
        pass
    

    def setUp(self):
        pass

    def testMeterSubdivision(self):
        a = MeterSequence()
        a.load('4/4', 4)
        str(a) == '{1/4+1/4+1/4+1/4}'
        
        a[0] = a[0].subdivide(2)
        str(a) == '{{1/8+1/8}+1/4+1/4+1/4}'
        
        a[3].subdivide(4)
        str(a) == '{{1/8+1/8}+1/4+1/4+{1/16+1/16+1/16+1/16}}'
        





#-----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    music21.mainTest(Test)




