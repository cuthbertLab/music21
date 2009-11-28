music21.meter
=============

Function fractionSum()
----------------------

Given a list of fractions represented as a list, find the sum 

>>> fractionSum([(3,8), (5,8), (1,8)])
(9, 8) 
>>> fractionSum([(1,6), (2,3)])
(5, 6) 
>>> fractionSum([(3,4), (1,2)])
(5, 4) 
>>> fractionSum([(1,13), (2,17)])
(43, 221) 



Function fractionToSlashMixed()
-------------------------------

Given a lost of fraction values, compact numerators by sum if denominators are the same 

>>> fractionToSlashMixed([(3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)])
[('3+2+5', 8), ('3', 4), ('2+1+4', 16)] 

Function slashCompoundToFraction()
----------------------------------



>>> slashCompoundToFraction('3/8+2/8')
[(3, 8), (2, 8)] 
>>> slashCompoundToFraction('5/8')
[(5, 8)] 
>>> slashCompoundToFraction('5/8+2/4+6/8')
[(5, 8), (2, 4), (6, 8)] 



Function slashMixedToFraction()
-------------------------------

Given a mixture if possible meter fraction representations, return a list of pairs. If originally given as a summed numerator; break into separate fractions. 

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

Function slashToFraction()
--------------------------

TODO: it seems like this should return only integers; not sure why these originally were floats. 

>>> slashToFraction('3/8')
(3, 8) 
>>> slashToFraction('7/32')
(7, 32) 

Class CompoundTimeSignature
---------------------------

Inherits from: meter.TimeSignature, base.Music21Object, object


Attributes
~~~~~~~~~~

**accent**

**beam**

**beat**

**contexts**

**display**

**groups**

**inherited**

**location**

**summedNumerator**

**symbol**

**symbolizeDenominator**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**deepcopy()**

**copy()**

**contexts()**


Inherited from meter.TimeSignature

**quarterPositionToBeat()**

**loadRatio()**

**load()**

**getBeat()**

**getBeams()**

**getAccent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**parent**

**duration**


Inherited from meter.TimeSignature

**totalLength**

**quarterLengthToBeatLengthRatio**

**numerator**

**mx**

**musicxml**

**lily**

**denominator**

**beatLengthToQuarterLengthRatio**

**barDuration**


Class DurationDenominatorTimeSignature
--------------------------------------

Inherits from: meter.TimeSignature, base.Music21Object, object

If you have played Hindemith you know these, 3/(dot-quarter) etc. 

Attributes
~~~~~~~~~~

**accent**

**beam**

**beat**

**contexts**

**display**

**groups**

**inherited**

**location**

**summedNumerator**

**symbol**

**symbolizeDenominator**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**deepcopy()**

**copy()**

**contexts()**


Inherited from meter.TimeSignature

**quarterPositionToBeat()**

**loadRatio()**

**load()**

**getBeat()**

**getBeams()**

**getAccent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**parent**

**duration**


Inherited from meter.TimeSignature

**totalLength**

**quarterLengthToBeatLengthRatio**

**numerator**

**mx**

**musicxml**

**lily**

**denominator**

**beatLengthToQuarterLengthRatio**

**barDuration**


Class MeterException
--------------------

Inherits from: exceptions.Exception, exceptions.BaseException, object


Methods
~~~~~~~


Inherited from exceptions.BaseException

**message()**

**args()**


Class MeterSequence
-------------------

Inherits from: meter.MeterTerminal, object

A meter sequence is a list of MeterTerminals, or other MeterSequences 

Attributes
~~~~~~~~~~

**summedNumerator**

Methods
~~~~~~~


Inherited from meter.MeterTerminal

**subdivideByList()**

**subdivideByCount()**

**subdivide()**

**ratioEqual()**

**deepcopy()**


Locally Defined

**positionToSpan()**

    Given a lenPos, return the span of the active region. Only applies to the top most level of partitions 

    >>> a = MeterSequence('3/4', 3)
    >>> a.positionToSpan(.5)
    (0, 1.0) 
    >>> a.positionToSpan(1.5)
    (1.0, 2.0) 

    

**positionToIndex()**

    Given a qLen pos (0 through self.duration.quarterLength), return the active MeterTerminal or MeterSequence 

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

**positionToAddress()**

    Give a list of values that show all indices necessary to access the exact terminal at a given qLenPos. The len of the returned list also provides the depth at the specified qLen. 

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

    

**partitionByOther()**

    Set partition to that found in another object 

    >>> a = MeterSequence('4/4', 4)
    >>> b = MeterSequence('4/4', 2)
    >>> a.partitionByOther(b)
    >>> len(a)
    2 

**partitionByList()**

    

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

    

**partitionByCount()**

    This will destroy any struct in the _partition 

    >>> a = MeterSequence('4/4')
    >>> a.partitionByCount(2)
    >>> str(a)
    '{1/2+1/2}' 
    >>> a.partitionByCount(4)
    >>> str(a)
    '{1/4+1/4+1/4+1/4}' 

**partition()**

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

**load()**

    User can enter a list of values or an abbreviated slash notation 

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

    

**getLevel()**

    Return a complete MeterSequence with the same numerator/denominator reationship but that represents any partitions found at the rquested level. A sort of flatness with variable depth. 

    >>> b = MeterSequence('4/4', 4)
    >>> b[1] = b[1].subdivide(2)
    >>> b[3] = b[3].subdivide(2)
    >>> b[3][0] = b[3][0].subdivide(2)
    >>> b
    {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}} 
    >>> b.getLevel(0)
    {1/4+1/4+1/4+1/4} 
    >>> b
    {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}} 
    >>> b.getLevel(1)
    {1/4+1/8+1/8+1/4+1/8+1/8} 
    >>> b.getLevel(2)
    {1/4+1/8+1/8+1/4+1/16+1/16+1/8} 

Properties
~~~~~~~~~~


Inherited from meter.MeterTerminal

**numerator**

**duration**

**denominator**


Locally Defined

**flat**

    Retrun a new MeterSequence composed of the flattend representation. 

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

    


Class MeterTerminal
-------------------

Inherits from: object

A meter is a nestable primitive of rhythmic division This object might also store accent patterns based on numerator or set as another internal representation. 

>>> a = MeterTerminal('2/4')
>>> a.duration.quarterLength
2.0 
>>> a = MeterTerminal('3/8')
>>> a.duration.quarterLength
1.5 
>>> a = MeterTerminal('5/2')
>>> a.duration.quarterLength
10.0 



Methods
~~~~~~~


Locally Defined

**subdivideByList()**

    Return a MeterSequence countRequest is within the context of the beatIndex 

    >>> a = MeterTerminal('3/4')
    >>> b = a.subdivideByList([1,1,1])
    >>> len(b)
    3 

**subdivideByCount()**

    retrun a MeterSequence 

    >>> a = MeterTerminal('3/4')
    >>> b = a.subdivideByCount(3)
    >>> isinstance(b, MeterSequence)
    True 
    >>> len(b)
    3 

**subdivide()**

    Retuirn a MeterSequence If an integer is provided, assume it is a partition count 

**ratioEqual()**

    Compare the numerator and denominator of another object. 

**deepcopy()**

    Return a complete copy. Here, copy and deepcopy should be the same. 

    >>> a = MeterTerminal('2/4')
    >>> b = a.deepcopy()

Properties
~~~~~~~~~~


Locally Defined

**numerator**


**duration**

    barDuration gets or sets a duration value that is equal in length to the totalLength 

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

**denominator**



Class NonPowerOfTwoTimeSignature
--------------------------------

Inherits from: meter.TimeSignature, base.Music21Object, object


Attributes
~~~~~~~~~~

**accent**

**beam**

**beat**

**contexts**

**display**

**groups**

**inherited**

**location**

**summedNumerator**

**symbol**

**symbolizeDenominator**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**deepcopy()**

**copy()**

**contexts()**


Inherited from meter.TimeSignature

**quarterPositionToBeat()**

**loadRatio()**

**load()**

**getBeat()**

**getBeams()**

**getAccent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**parent**

**duration**


Inherited from meter.TimeSignature

**totalLength**

**quarterLengthToBeatLengthRatio**

**numerator**

**mx**

**musicxml**

**lily**

**denominator**

**beatLengthToQuarterLengthRatio**

**barDuration**


Class TimeSignature
-------------------

Inherits from: base.Music21Object, object


Attributes
~~~~~~~~~~

**accent**

**beam**

**beat**

**contexts**

**display**

**groups**

**inherited**

**location**

**summedNumerator**

**symbol**

**symbolizeDenominator**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**deepcopy()**

**copy()**

**contexts()**


Locally Defined

**quarterPositionToBeat()**

    For backward compatibility. 

**loadRatio()**

    Convenience method 

**load()**

    Loading a meter destroys all internal representations 

**getBeat()**

    Get the beat, where beats count from 1 

    >>> a = TimeSignature('3/4', 3)
    >>> a.getBeat(0)
    1 
    >>> a.getBeat(2.5)
    3 
    >>> a.beat.partition(['3/8', '3/8'])
    >>> a.getBeat(2.5)
    2 

**getBeams()**

    Given a qLen position and a list of Duration objects, return a list of Beams object. Duration objects are assumed to be adjoining; offsets are not used. This can be modified to take lists of rests and notes Must process a list at  time, because we cannot tell when a beam ends unless we see the context of adjoining durations. 

    >>> a = TimeSignature('2/4', 2)
    >>> a.beam[0] = a.beam[0].subdivide(2)
    >>> a.beam[1] = a.beam[1].subdivide(2)
    >>> a.beam
    {{1/8+1/8}+{1/8+1/8}} 
    >>> b = [duration.Duration('16th')] * 8
    >>> c = a.getBeams(b)
    >>> len(c) == len(b)
    True 
    >>> print c
    [<music21.note.Beams <music21.note.Beam 1/start/None>/<music21.note.Beam 2/start/None>>, <music21.note.Beams <music21.note.Beam 1/continue/None>/<music21.note.Beam 2/stop/None>>, <music21.note.Beams <music21.note.Beam 1/continue/None>/<music21.note.Beam 2/start/None>>, <music21.note.Beams <music21.note.Beam 1/stop/None>/<music21.note.Beam 2/stop/None>>, <music21.note.Beams <music21.note.Beam 1/start/None>/<music21.note.Beam 2/start/None>>, <music21.note.Beams <music21.note.Beam 1/continue/None>/<music21.note.Beam 2/stop/None>>, <music21.note.Beams <music21.note.Beam 1/continue/None>/<music21.note.Beam 2/start/None>>, <music21.note.Beams <music21.note.Beam 1/stop/None>/<music21.note.Beam 2/stop/None>>] 

**getAccent()**

    Return true or false if the qLenPos is at the start of an accent division 

    >>> a = TimeSignature('3/4', 3)
    >>> a.accent.partition([2,1])
    >>> a.accent
    {2/4+1/4} 
    >>> a.getAccent(0)
    True 
    >>> a.getAccent(1)
    False 
    >>> a.getAccent(2)
    True 

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**parent**

**duration**


Locally Defined

**totalLength**


**quarterLengthToBeatLengthRatio**


**numerator**


**mx**

    Returns a list of one mxTime object. Compound meters are represented as multiple pairs of beat and beat-type elements 

    >>> a = TimeSignature('3/4')
    >>> b = a.mx
    >>> a = TimeSignature('3/4+2/4')
    >>> b = a.mx

    

**musicxml**

    Return a complete MusicXML string 

**lily**

    returns the lilypond representation of the timeSignature 

    >>> a = TimeSignature('3/16')
    >>> a.lily
    \time 3/16 

**denominator**


**beatLengthToQuarterLengthRatio**

    

    >>> a = TimeSignature('3/2')
    >>> a.beatLengthToQuarterLengthRatio
    2.0 

**barDuration**

    barDuration gets or sets a duration value that is equal in length to the totalLength 

    >>> a = TimeSignature('3/8')
    >>> d = a.barDuration
    >>> d.type
    'quarter' 
    >>> d.dots
    1 
    >>> d.quarterLength
    1.5 


