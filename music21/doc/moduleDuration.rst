music21.duration
================

Class Duration
--------------

A Duration is made of one or more DurationUnits. Multiple Duration units may be used to express tied notes, or may be used to split duration accross barlines or beam groups. Some Durations are not expressable as a single notation unit. 

Public Attributes
~~~~~~~~~~~~~~~~~

+ components
+ durationToType
+ linkages
+ ordinalTypeFromNum
+ typeFromNumDict
+ typeToDuration

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _qtrLength
+ _quarterLengthNeedsUpdating

Public Methods
~~~~~~~~~~~~~~

**addDuration()**

    Add either a DurationUnit or a Duration object to this Duration. Adding a Duration always assumes that the Duration is tied. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)

**clear()**

    Permit all componets to be removed. It is not clear yet if this is needed. 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> # a.type

**clone()**

    print here 

**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    >>> for x in [1,1,1]: components.append(Duration('quarter'))
    ... 
    >>> a = Duration()
    >>> a.components = components
    >>> a._updateQuarterLength()
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

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

    >>> components = []
    >>> for x in [1,1,1]: components.append(Duration('quarter'))
    ... 
    >>> a = Duration()
    >>> a.components = components
    >>> a._updateQuarterLength()
    >>> a.quarterLength
    3.0 
    >>> a.componentStartTime(0)
    0.0 
    >>> a.componentStartTime(1)
    1.0 

**consolidate()**

    Given a Duration with multiple comoponents, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

    >>> a = Duration()
    >>> a._fill(['quarter', 'half', 'quarter'])
    >>> a.quarterLength
    4.0 
    >>> len(a.components)
    3 
    >>> a.consolidate()
    >>> a.quarterLength
    4.0 
    >>> len(a.components)
    1 

**convertNumberToType()**

    Convert a number ( 4 = quarter; 8 = eighth), etc. to type. 

    >>> a = DurationCommon()
    >>> a.convertNumberToType(4)
    'quarter' 
    >>> a.convertNumberToType(32)
    '32nd' 

**convertQuarterLengthToDuration()**

    Given a an arbitrary quarter length, convert it into a the parameters necessary to instantiate a DurationUnit object. Note: this now uses quarterLengthToUnitSpec(); this method remains for backward compatibility; but can be replaced 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToDuration(3)
    ('half', [1], []) 
    >>> a.convertQuarterLengthToDuration(1)
    ('quarter', [0], []) 
    >>> a.convertQuarterLengthToDuration(.75)
    ('eighth', [1], []) 
    >>> a.convertQuarterLengthToDuration(.125)
    ('32nd', [0], []) 
    >>> post = a.convertQuarterLengthToDuration(.33333)
    >>> post[0] == 'eighth'
    True 
    >>> post[1] == [0]
    True 
    >>> isinstance(post[2][0], Tuplet)
    True 

**convertQuarterLengthToType()**

    Convert quarter lengths to types. This cannot handle quarter lengths of 3 or .75 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToType(2)
    'half' 
    >>> a.convertQuarterLengthToType(0.125)
    '32nd' 

**convertTypeToNumber()**

    Convert duration type to 

    >>> a = DurationCommon()
    >>> a.convertTypeToNumber('quarter')
    4 
    >>> a.convertTypeToNumber('half')
    2 

**convertTypeToOrdinal()**

    Convert type to an ordinal number based on self.ordinalTypeFromNum 

    >>> a = DurationCommon()
    >>> a.convertTypeToOrdinal('whole')
    4 
    >>> a.convertTypeToOrdinal('maxima')
    1 
    >>> a.convertTypeToOrdinal('1024th')
    14 

**convertTypeToQuarterLength()**

    Given a rhythm type, convert it to a quarter length, given a lost of dots and tuplets. 

    >>> a = DurationCommon()
    >>> a.convertTypeToQuarterLength('whole')
    4.0 
    >>> a.convertTypeToQuarterLength('16th')
    0.25 
    >>> a.convertTypeToQuarterLength('quarter', [2])
    1.75 

**dots()**

    Return dots as a list Assume we only want the first element. 

**expand()**

    Make a duration notatable. Provide a unit of division. 

**isComplex()**

    No documentation.

**lily()**

    Simple lily duration: does not include tuplets NOTE: not sure if this works properly; does not seem to include ties 

**musicxml()**

    Return a complete MusicXML string with defaults. 

**mx()**

    Returns a list of one or more musicxml.Note() objects with all rhythms and ties necessary. mxNote objects are incompletely specified, lacking full representation and information on pitch, etc. TODO: tuplets, notations, ties 

    >>> a = Duration()
    >>> a.quarterLength = 3
    >>> b = a.mx
    >>> len(b) == 1
    True 
    >>> isinstance(b[0], musicxmlMod.Note)
    True 

**ordinalNumFromType()**

    for backward compatibility; replace with property ordinal 

**partitionToUnitSpec()**

    Given any qLen, partition into one or more quarterLengthUnits based on a specified qLenDiv Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType Dividing 2.5 qLen into eighth notes. 

    >>> a = DurationCommon()
    >>> a.partitionToUnitSpec(2.5,.5)
    ([(0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5 qLen into 2.5 qLen bundles 
    >>> a.partitionToUnitSpec(5,2.5)
    ([(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5.25 qLen into dotted halves 
    >>> a.partitionToUnitSpec(5.25,3)
    ([(3, 'half', 1, None, None, None), (2.0, 'half', 0, None, None, None), (0.25, '16th', 0, None, None, None)], False) 

    
    Dividing 1.33333 qLen into triplet eighths: 
    >>> a.partitionToUnitSpec(1.33333333333333,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth')], True) 

    
    Dividing 1.5 into triplet eighths 
    >>> a.partitionToUnitSpec(1.5,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.16666666666668023, '16th', 0, 3, 2, '16th')], False) 

    
    No problem if the division unit is larger then the source duration. 
    >>> a.partitionToUnitSpec(1.5, 4)
    ([(1.5, 'quarter', 1, None, None, None)], False) 

    

**quarterLength()**

    Can be the same as the base class. 

**quarterLengthToDotCandidate()**

    Given a qLen and type that is less than but not greater than qLen, determine if one or more dots match. TODO: Find and return dotgroups, perhaps based on optional flag 

    >>> a = DurationCommon()
    >>> a.quarterLengthToDotCandidate(3, 'half')
    (1, True) 

**quarterLengthToTupletCandidate()**

    Return one or more possible tuplets for a given qLen. 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTupletCandidate(.33333333)
    [[3, 2, 'eighth'], [3, 1, 'quarter']] 
    By specifying only 1 count, the tuple with the smallest type will be 
    returned. 
    >>> a.quarterLengthToTupletCandidate(.3333333, 1)
    [[3, 2, 'eighth']] 

    
    >>> a.quarterLengthToTupletCandidate(.20)
    [[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
    #ARIZA: would this be more portable if it returned a list of 
    # Tuplet objects instead 
    # this would work fine, but is harder to test in the short term, 
    # b/c the object parameters have be examined. 

**quarterLengthToTypeCandidate()**

    Return the type for a given quarterLength, otherwise return the type that is the largest that is not greater than this qLen 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTypeCandidate(.5)
    ('eighth', None, True) 
    >>> a.quarterLengthToTypeCandidate(.75)
    ('eighth', 'quarter', False) 
    >>> a.quarterLengthToTypeCandidate(1.75)
    ('quarter', 'half', False) 

**quarterLengthToUnitSpec()**

    Given a quarterLength, determine if it can be notated as a single unit, or if it needs to be divided into multiple units. (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we do not use that). Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType 

    >>> a = DurationCommon()
    >>> a.quarterLengthToUnitSpec(2)
    [(2, 'half', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3)
    [(3, 'half', 1, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(6.0)
    [(6.0, 'whole', 1, None, None, None)] 
    Double and triple dotted half note. 
    >>> a.quarterLengthToUnitSpec(3.5)
    [(3.5, 'half', 2, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3.75)
    [(3.75, 'half', 3, None, None, None)] 
    A triplet quarter note, lasting .6666 qLen 
    Or, a quarter that is 1/3 of a half. 
    Or, a quarter that is 2/3 of a quarter. 
    >>> a.quarterLengthToUnitSpec(.6666666666)
    [(0.66666666659999996, 'quarter', 0, 3, 2, 'quarter')] 
    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter 
    Or, an eighth that is 2/3 of eighth 
    >>> post = a.quarterLengthToUnitSpec(.3333333)
    >>> common.almostEquals(post[0][0], .3333333)
    True 
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth') 
    A half that is 1/3 of a whole, or a triplet half note. 
    Or, a half that is 2/3 of a half 
    >>> a.quarterLengthToUnitSpec(1.3333333)
    [(1.3333333000000001, 'half', 0, 3, 2, 'half')] 
    A sixteenth that is 1/5 of a quarter 
    Or, a sixteenth that is 4/5ths of a 16th 
    >>> a.quarterLengthToUnitSpec(.200000000)
    [(0.20000000000000001, '16th', 0, 5, 4, '16th')] 
    A 16th that is  1/7th of a quarter 
    Or, a 16th that is 4/7 of a 16th 
    >>> a.quarterLengthToUnitSpec(0.14285714285714285)
    [(0.14285714285714285, '16th', 0, 7, 4, '16th')] 
    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter 
    >>> a.quarterLengthToUnitSpec(0.5714285714285714)
    [(0.5714285714285714, 'quarter', 0, 7, 4, 'quarter')] 
    If a duration is not containable in a single unit, the method 
    will break off the largest type that fits within this type 
    and recurse, adding as my units as necessary. 
    >>> a.quarterLengthToUnitSpec(2.5)
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(2.3333333)
    [(2.0, 'half', 0, None, None, None), (0.33333330000000005, 'eighth', 0, 3, 2, 'eighth')] 
    >>> a.quarterLengthToUnitSpec(0.166666666667)
    [(0.166666666667, '16th', 0, 3, 2, '16th')] 

    

**setTypeFromNum()**

    No documentation.

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> for x in [1,1,1]: a.addDuration(Duration('quarter'))
    ... 
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

**tuplets()**

    Return dots as a list 

**type()**

    Get the duration type. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**_getDots()**

    Return dots as a list Assume we only want the first element. 

**_getLily()**

    Simple lily duration: does not include tuplets NOTE: not sure if this works properly; does not seem to include ties 

**_getMX()**

    Returns a list of one or more musicxml.Note() objects with all rhythms and ties necessary. mxNote objects are incompletely specified, lacking full representation and information on pitch, etc. TODO: tuplets, notations, ties 

    >>> a = Duration()
    >>> a.quarterLength = 3
    >>> b = a.mx
    >>> len(b) == 1
    True 
    >>> isinstance(b[0], musicxmlMod.Note)
    True 

**_getMusicXML()**

    Return a complete MusicXML string with defaults. 

**_getQuarterLength()**

    Can be the same as the base class. 

**_getTuplets()**

    Return dots as a list 

**_getType()**

    Get the duration type. 

**_isComplex()**

    No documentation.

**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a._setDots(1)
    >>> a.quarterLength
    1.5 
    >>> a._setDots(2)
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

**_setMusicXML()**

    

    

**_setQuarterLength()**

    Set the quarter note length to the specified value. What do we do with existing quarter notes? Additional types are needed: 'zero' type for zero durations 'unexpressable' type for anything that needs a Duration 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> a.quarterLength = 1.75
    >>> a.quarterLength
    1.75 

**_setTuplets()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'

**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateQuarterLength()**

    Look to components and determine quarter length. 


Class DurationCommon
--------------------

Basic conversion methods and resources that are needed by all Duration objects 

Public Attributes
~~~~~~~~~~~~~~~~~

+ durationToType
+ ordinalTypeFromNum
+ typeFromNumDict
+ typeToDuration

Public Methods
~~~~~~~~~~~~~~

**clone()**

    No documentation.

**convertNumberToType()**

    Convert a number ( 4 = quarter; 8 = eighth), etc. to type. 

    >>> a = DurationCommon()
    >>> a.convertNumberToType(4)
    'quarter' 
    >>> a.convertNumberToType(32)
    '32nd' 

**convertQuarterLengthToDuration()**

    Given a an arbitrary quarter length, convert it into a the parameters necessary to instantiate a DurationUnit object. Note: this now uses quarterLengthToUnitSpec(); this method remains for backward compatibility; but can be replaced 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToDuration(3)
    ('half', [1], []) 
    >>> a.convertQuarterLengthToDuration(1)
    ('quarter', [0], []) 
    >>> a.convertQuarterLengthToDuration(.75)
    ('eighth', [1], []) 
    >>> a.convertQuarterLengthToDuration(.125)
    ('32nd', [0], []) 
    >>> post = a.convertQuarterLengthToDuration(.33333)
    >>> post[0] == 'eighth'
    True 
    >>> post[1] == [0]
    True 
    >>> isinstance(post[2][0], Tuplet)
    True 

**convertQuarterLengthToType()**

    Convert quarter lengths to types. This cannot handle quarter lengths of 3 or .75 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToType(2)
    'half' 
    >>> a.convertQuarterLengthToType(0.125)
    '32nd' 

**convertTypeToNumber()**

    Convert duration type to 

    >>> a = DurationCommon()
    >>> a.convertTypeToNumber('quarter')
    4 
    >>> a.convertTypeToNumber('half')
    2 

**convertTypeToOrdinal()**

    Convert type to an ordinal number based on self.ordinalTypeFromNum 

    >>> a = DurationCommon()
    >>> a.convertTypeToOrdinal('whole')
    4 
    >>> a.convertTypeToOrdinal('maxima')
    1 
    >>> a.convertTypeToOrdinal('1024th')
    14 

**convertTypeToQuarterLength()**

    Given a rhythm type, convert it to a quarter length, given a lost of dots and tuplets. 

    >>> a = DurationCommon()
    >>> a.convertTypeToQuarterLength('whole')
    4.0 
    >>> a.convertTypeToQuarterLength('16th')
    0.25 
    >>> a.convertTypeToQuarterLength('quarter', [2])
    1.75 

**ordinalNumFromType()**

    for backward compatibility; replace with property ordinal 

**partitionToUnitSpec()**

    Given any qLen, partition into one or more quarterLengthUnits based on a specified qLenDiv Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType Dividing 2.5 qLen into eighth notes. 

    >>> a = DurationCommon()
    >>> a.partitionToUnitSpec(2.5,.5)
    ([(0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5 qLen into 2.5 qLen bundles 
    >>> a.partitionToUnitSpec(5,2.5)
    ([(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5.25 qLen into dotted halves 
    >>> a.partitionToUnitSpec(5.25,3)
    ([(3, 'half', 1, None, None, None), (2.0, 'half', 0, None, None, None), (0.25, '16th', 0, None, None, None)], False) 

    
    Dividing 1.33333 qLen into triplet eighths: 
    >>> a.partitionToUnitSpec(1.33333333333333,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth')], True) 

    
    Dividing 1.5 into triplet eighths 
    >>> a.partitionToUnitSpec(1.5,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.16666666666668023, '16th', 0, 3, 2, '16th')], False) 

    
    No problem if the division unit is larger then the source duration. 
    >>> a.partitionToUnitSpec(1.5, 4)
    ([(1.5, 'quarter', 1, None, None, None)], False) 

    

**quarterLengthToDotCandidate()**

    Given a qLen and type that is less than but not greater than qLen, determine if one or more dots match. TODO: Find and return dotgroups, perhaps based on optional flag 

    >>> a = DurationCommon()
    >>> a.quarterLengthToDotCandidate(3, 'half')
    (1, True) 

**quarterLengthToTupletCandidate()**

    Return one or more possible tuplets for a given qLen. 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTupletCandidate(.33333333)
    [[3, 2, 'eighth'], [3, 1, 'quarter']] 
    By specifying only 1 count, the tuple with the smallest type will be 
    returned. 
    >>> a.quarterLengthToTupletCandidate(.3333333, 1)
    [[3, 2, 'eighth']] 

    
    >>> a.quarterLengthToTupletCandidate(.20)
    [[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
    #ARIZA: would this be more portable if it returned a list of 
    # Tuplet objects instead 
    # this would work fine, but is harder to test in the short term, 
    # b/c the object parameters have be examined. 

**quarterLengthToTypeCandidate()**

    Return the type for a given quarterLength, otherwise return the type that is the largest that is not greater than this qLen 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTypeCandidate(.5)
    ('eighth', None, True) 
    >>> a.quarterLengthToTypeCandidate(.75)
    ('eighth', 'quarter', False) 
    >>> a.quarterLengthToTypeCandidate(1.75)
    ('quarter', 'half', False) 

**quarterLengthToUnitSpec()**

    Given a quarterLength, determine if it can be notated as a single unit, or if it needs to be divided into multiple units. (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we do not use that). Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType 

    >>> a = DurationCommon()
    >>> a.quarterLengthToUnitSpec(2)
    [(2, 'half', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3)
    [(3, 'half', 1, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(6.0)
    [(6.0, 'whole', 1, None, None, None)] 
    Double and triple dotted half note. 
    >>> a.quarterLengthToUnitSpec(3.5)
    [(3.5, 'half', 2, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3.75)
    [(3.75, 'half', 3, None, None, None)] 
    A triplet quarter note, lasting .6666 qLen 
    Or, a quarter that is 1/3 of a half. 
    Or, a quarter that is 2/3 of a quarter. 
    >>> a.quarterLengthToUnitSpec(.6666666666)
    [(0.66666666659999996, 'quarter', 0, 3, 2, 'quarter')] 
    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter 
    Or, an eighth that is 2/3 of eighth 
    >>> post = a.quarterLengthToUnitSpec(.3333333)
    >>> common.almostEquals(post[0][0], .3333333)
    True 
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth') 
    A half that is 1/3 of a whole, or a triplet half note. 
    Or, a half that is 2/3 of a half 
    >>> a.quarterLengthToUnitSpec(1.3333333)
    [(1.3333333000000001, 'half', 0, 3, 2, 'half')] 
    A sixteenth that is 1/5 of a quarter 
    Or, a sixteenth that is 4/5ths of a 16th 
    >>> a.quarterLengthToUnitSpec(.200000000)
    [(0.20000000000000001, '16th', 0, 5, 4, '16th')] 
    A 16th that is  1/7th of a quarter 
    Or, a 16th that is 4/7 of a 16th 
    >>> a.quarterLengthToUnitSpec(0.14285714285714285)
    [(0.14285714285714285, '16th', 0, 7, 4, '16th')] 
    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter 
    >>> a.quarterLengthToUnitSpec(0.5714285714285714)
    [(0.5714285714285714, 'quarter', 0, 7, 4, 'quarter')] 
    If a duration is not containable in a single unit, the method 
    will break off the largest type that fits within this type 
    and recurse, adding as my units as necessary. 
    >>> a.quarterLengthToUnitSpec(2.5)
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(2.3333333)
    [(2.0, 'half', 0, None, None, None), (0.33333330000000005, 'eighth', 0, 3, 2, 'eighth')] 
    >>> a.quarterLengthToUnitSpec(0.166666666667)
    [(0.166666666667, '16th', 0, 3, 2, '16th')] 

    

**setTypeFromNum()**

    No documentation.


Class DurationException
-----------------------

No documentation.

Public Methods
~~~~~~~~~~~~~~

**args()**

    No documentation.

**message()**

    No documentation.


Class DurationUnit
------------------

A DurationUnit is a notation that (generally) can be notated with a a single notation unit, such as one note, without a tie. A DurationUnit has the option of overriding (unlinking) this behavior to act as two things: a representation (made of type, dots, and tuples) and a quarter note length that may be independent. Additional types are needed: 'zero' type for zero durations 'unexpressable' type for anything that needs a Duration 

Public Attributes
~~~~~~~~~~~~~~~~~

+ durationToType
+ linkStatus
+ ordinalTypeFromNum
+ typeFromNumDict
+ typeToDuration

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _dots
+ _qtrLength
+ _quarterLengthNeedsUpdating
+ _tuplets
+ _type

Public Methods
~~~~~~~~~~~~~~

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  Returns (15,8). Needed for MusicXML time-modification 

**clone()**

    No documentation.

**convertNumberToType()**

    Convert a number ( 4 = quarter; 8 = eighth), etc. to type. 

    >>> a = DurationCommon()
    >>> a.convertNumberToType(4)
    'quarter' 
    >>> a.convertNumberToType(32)
    '32nd' 

**convertQuarterLengthToDuration()**

    Given a an arbitrary quarter length, convert it into a the parameters necessary to instantiate a DurationUnit object. Note: this now uses quarterLengthToUnitSpec(); this method remains for backward compatibility; but can be replaced 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToDuration(3)
    ('half', [1], []) 
    >>> a.convertQuarterLengthToDuration(1)
    ('quarter', [0], []) 
    >>> a.convertQuarterLengthToDuration(.75)
    ('eighth', [1], []) 
    >>> a.convertQuarterLengthToDuration(.125)
    ('32nd', [0], []) 
    >>> post = a.convertQuarterLengthToDuration(.33333)
    >>> post[0] == 'eighth'
    True 
    >>> post[1] == [0]
    True 
    >>> isinstance(post[2][0], Tuplet)
    True 

**convertQuarterLengthToType()**

    Convert quarter lengths to types. This cannot handle quarter lengths of 3 or .75 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToType(2)
    'half' 
    >>> a.convertQuarterLengthToType(0.125)
    '32nd' 

**convertTypeToNumber()**

    Convert duration type to 

    >>> a = DurationCommon()
    >>> a.convertTypeToNumber('quarter')
    4 
    >>> a.convertTypeToNumber('half')
    2 

**convertTypeToOrdinal()**

    Convert type to an ordinal number based on self.ordinalTypeFromNum 

    >>> a = DurationCommon()
    >>> a.convertTypeToOrdinal('whole')
    4 
    >>> a.convertTypeToOrdinal('maxima')
    1 
    >>> a.convertTypeToOrdinal('1024th')
    14 

**convertTypeToQuarterLength()**

    Given a rhythm type, convert it to a quarter length, given a lost of dots and tuplets. 

    >>> a = DurationCommon()
    >>> a.convertTypeToQuarterLength('whole')
    4.0 
    >>> a.convertTypeToQuarterLength('16th')
    0.25 
    >>> a.convertTypeToQuarterLength('quarter', [2])
    1.75 

**dots()**

    Return dots as a list Assume we only want the first element. 

**lily()**

    Simple lily duration: does not include tuplets 

**link()**

    No documentation.

**loadUnitSpec()**

    Given a data list in the form: qLen, durType, dost, tupleDiv, tupletMult, tupletType Load all attributes 

**ordinalNumFromType()**

    for backward compatibility; replace with property ordinal 

**partitionToUnitSpec()**

    Given any qLen, partition into one or more quarterLengthUnits based on a specified qLenDiv Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType Dividing 2.5 qLen into eighth notes. 

    >>> a = DurationCommon()
    >>> a.partitionToUnitSpec(2.5,.5)
    ([(0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5 qLen into 2.5 qLen bundles 
    >>> a.partitionToUnitSpec(5,2.5)
    ([(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5.25 qLen into dotted halves 
    >>> a.partitionToUnitSpec(5.25,3)
    ([(3, 'half', 1, None, None, None), (2.0, 'half', 0, None, None, None), (0.25, '16th', 0, None, None, None)], False) 

    
    Dividing 1.33333 qLen into triplet eighths: 
    >>> a.partitionToUnitSpec(1.33333333333333,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth')], True) 

    
    Dividing 1.5 into triplet eighths 
    >>> a.partitionToUnitSpec(1.5,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.16666666666668023, '16th', 0, 3, 2, '16th')], False) 

    
    No problem if the division unit is larger then the source duration. 
    >>> a.partitionToUnitSpec(1.5, 4)
    ([(1.5, 'quarter', 1, None, None, None)], False) 

    

**quarterLength()**

    determine the length in quarter notes from current information 

**quarterLengthToDotCandidate()**

    Given a qLen and type that is less than but not greater than qLen, determine if one or more dots match. TODO: Find and return dotgroups, perhaps based on optional flag 

    >>> a = DurationCommon()
    >>> a.quarterLengthToDotCandidate(3, 'half')
    (1, True) 

**quarterLengthToTupletCandidate()**

    Return one or more possible tuplets for a given qLen. 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTupletCandidate(.33333333)
    [[3, 2, 'eighth'], [3, 1, 'quarter']] 
    By specifying only 1 count, the tuple with the smallest type will be 
    returned. 
    >>> a.quarterLengthToTupletCandidate(.3333333, 1)
    [[3, 2, 'eighth']] 

    
    >>> a.quarterLengthToTupletCandidate(.20)
    [[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
    #ARIZA: would this be more portable if it returned a list of 
    # Tuplet objects instead 
    # this would work fine, but is harder to test in the short term, 
    # b/c the object parameters have be examined. 

**quarterLengthToTypeCandidate()**

    Return the type for a given quarterLength, otherwise return the type that is the largest that is not greater than this qLen 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTypeCandidate(.5)
    ('eighth', None, True) 
    >>> a.quarterLengthToTypeCandidate(.75)
    ('eighth', 'quarter', False) 
    >>> a.quarterLengthToTypeCandidate(1.75)
    ('quarter', 'half', False) 

**quarterLengthToUnitSpec()**

    Given a quarterLength, determine if it can be notated as a single unit, or if it needs to be divided into multiple units. (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we do not use that). Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType 

    >>> a = DurationCommon()
    >>> a.quarterLengthToUnitSpec(2)
    [(2, 'half', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3)
    [(3, 'half', 1, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(6.0)
    [(6.0, 'whole', 1, None, None, None)] 
    Double and triple dotted half note. 
    >>> a.quarterLengthToUnitSpec(3.5)
    [(3.5, 'half', 2, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3.75)
    [(3.75, 'half', 3, None, None, None)] 
    A triplet quarter note, lasting .6666 qLen 
    Or, a quarter that is 1/3 of a half. 
    Or, a quarter that is 2/3 of a quarter. 
    >>> a.quarterLengthToUnitSpec(.6666666666)
    [(0.66666666659999996, 'quarter', 0, 3, 2, 'quarter')] 
    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter 
    Or, an eighth that is 2/3 of eighth 
    >>> post = a.quarterLengthToUnitSpec(.3333333)
    >>> common.almostEquals(post[0][0], .3333333)
    True 
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth') 
    A half that is 1/3 of a whole, or a triplet half note. 
    Or, a half that is 2/3 of a half 
    >>> a.quarterLengthToUnitSpec(1.3333333)
    [(1.3333333000000001, 'half', 0, 3, 2, 'half')] 
    A sixteenth that is 1/5 of a quarter 
    Or, a sixteenth that is 4/5ths of a 16th 
    >>> a.quarterLengthToUnitSpec(.200000000)
    [(0.20000000000000001, '16th', 0, 5, 4, '16th')] 
    A 16th that is  1/7th of a quarter 
    Or, a 16th that is 4/7 of a 16th 
    >>> a.quarterLengthToUnitSpec(0.14285714285714285)
    [(0.14285714285714285, '16th', 0, 7, 4, '16th')] 
    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter 
    >>> a.quarterLengthToUnitSpec(0.5714285714285714)
    [(0.5714285714285714, 'quarter', 0, 7, 4, 'quarter')] 
    If a duration is not containable in a single unit, the method 
    will break off the largest type that fits within this type 
    and recurse, adding as my units as necessary. 
    >>> a.quarterLengthToUnitSpec(2.5)
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(2.3333333)
    [(2.0, 'half', 0, None, None, None), (0.33333330000000005, 'eighth', 0, 3, 2, 'eighth')] 
    >>> a.quarterLengthToUnitSpec(0.166666666667)
    [(0.166666666667, '16th', 0, 3, 2, '16th')] 

    

**setTypeFromNum()**

    No documentation.

**split()**

    Divide a duration into two component Durations. 

    

**tuplets()**

    Return tuplets as a list 

**type()**

    Get the duration type. 

**unlink()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_getDots()**

    Return dots as a list Assume we only want the first element. 

**_getLily()**

    Simple lily duration: does not include tuplets 

**_getQuarterLength()**

    determine the length in quarter notes from current information 

**_getTuplets()**

    Return tuplets as a list 

**_getType()**

    Get the duration type. 

**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = DurationUnit()
    >>> a.type = 'quarter'
    >>> a._setDots(1)
    >>> a.quarterLength
    1.5 
    >>> a._setDots(2)
    >>> a.quarterLength
    1.75 
    Can we set dots first? 
    >>> a = DurationUnit()
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 

**_setQuarterLength()**

    Set the quarter note length to the specified value. If the quarter length is greater than that of long, unlink. 

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
    >>> c.quarterLength = 36
    >>> c.type
    'quarter' 
    >>> c.linkStatus
    False 

**_setTuplets()**

    A a list of tuplet objects 

**_setType()**

    Set the type length to the specified value. Check for bad types. 

    >>> a = Duration()
    >>> a.type = '128th'
    >>> a.quarterLength
    0.03125 
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 

**_updateQuarterLength()**

    Generally, used without an argument. If unlinked, however, a values can be directly applied to qtrLegnth. 


Class GraceDuration
-------------------

No documentation.

Public Attributes
~~~~~~~~~~~~~~~~~

+ durationToType
+ ordinalTypeFromNum
+ typeFromNumDict
+ typeToDuration

Public Methods
~~~~~~~~~~~~~~

**clone()**

    No documentation.

**convertNumberToType()**

    Convert a number ( 4 = quarter; 8 = eighth), etc. to type. 

    >>> a = DurationCommon()
    >>> a.convertNumberToType(4)
    'quarter' 
    >>> a.convertNumberToType(32)
    '32nd' 

**convertQuarterLengthToDuration()**

    Given a an arbitrary quarter length, convert it into a the parameters necessary to instantiate a DurationUnit object. Note: this now uses quarterLengthToUnitSpec(); this method remains for backward compatibility; but can be replaced 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToDuration(3)
    ('half', [1], []) 
    >>> a.convertQuarterLengthToDuration(1)
    ('quarter', [0], []) 
    >>> a.convertQuarterLengthToDuration(.75)
    ('eighth', [1], []) 
    >>> a.convertQuarterLengthToDuration(.125)
    ('32nd', [0], []) 
    >>> post = a.convertQuarterLengthToDuration(.33333)
    >>> post[0] == 'eighth'
    True 
    >>> post[1] == [0]
    True 
    >>> isinstance(post[2][0], Tuplet)
    True 

**convertQuarterLengthToType()**

    Convert quarter lengths to types. This cannot handle quarter lengths of 3 or .75 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToType(2)
    'half' 
    >>> a.convertQuarterLengthToType(0.125)
    '32nd' 

**convertTypeToNumber()**

    Convert duration type to 

    >>> a = DurationCommon()
    >>> a.convertTypeToNumber('quarter')
    4 
    >>> a.convertTypeToNumber('half')
    2 

**convertTypeToOrdinal()**

    Convert type to an ordinal number based on self.ordinalTypeFromNum 

    >>> a = DurationCommon()
    >>> a.convertTypeToOrdinal('whole')
    4 
    >>> a.convertTypeToOrdinal('maxima')
    1 
    >>> a.convertTypeToOrdinal('1024th')
    14 

**convertTypeToQuarterLength()**

    Given a rhythm type, convert it to a quarter length, given a lost of dots and tuplets. 

    >>> a = DurationCommon()
    >>> a.convertTypeToQuarterLength('whole')
    4.0 
    >>> a.convertTypeToQuarterLength('16th')
    0.25 
    >>> a.convertTypeToQuarterLength('quarter', [2])
    1.75 

**ordinalNumFromType()**

    for backward compatibility; replace with property ordinal 

**partitionToUnitSpec()**

    Given any qLen, partition into one or more quarterLengthUnits based on a specified qLenDiv Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType Dividing 2.5 qLen into eighth notes. 

    >>> a = DurationCommon()
    >>> a.partitionToUnitSpec(2.5,.5)
    ([(0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5 qLen into 2.5 qLen bundles 
    >>> a.partitionToUnitSpec(5,2.5)
    ([(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5.25 qLen into dotted halves 
    >>> a.partitionToUnitSpec(5.25,3)
    ([(3, 'half', 1, None, None, None), (2.0, 'half', 0, None, None, None), (0.25, '16th', 0, None, None, None)], False) 

    
    Dividing 1.33333 qLen into triplet eighths: 
    >>> a.partitionToUnitSpec(1.33333333333333,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth')], True) 

    
    Dividing 1.5 into triplet eighths 
    >>> a.partitionToUnitSpec(1.5,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.16666666666668023, '16th', 0, 3, 2, '16th')], False) 

    
    No problem if the division unit is larger then the source duration. 
    >>> a.partitionToUnitSpec(1.5, 4)
    ([(1.5, 'quarter', 1, None, None, None)], False) 

    

**quarterLength()**

    No documentation.

**quarterLengthToDotCandidate()**

    Given a qLen and type that is less than but not greater than qLen, determine if one or more dots match. TODO: Find and return dotgroups, perhaps based on optional flag 

    >>> a = DurationCommon()
    >>> a.quarterLengthToDotCandidate(3, 'half')
    (1, True) 

**quarterLengthToTupletCandidate()**

    Return one or more possible tuplets for a given qLen. 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTupletCandidate(.33333333)
    [[3, 2, 'eighth'], [3, 1, 'quarter']] 
    By specifying only 1 count, the tuple with the smallest type will be 
    returned. 
    >>> a.quarterLengthToTupletCandidate(.3333333, 1)
    [[3, 2, 'eighth']] 

    
    >>> a.quarterLengthToTupletCandidate(.20)
    [[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
    #ARIZA: would this be more portable if it returned a list of 
    # Tuplet objects instead 
    # this would work fine, but is harder to test in the short term, 
    # b/c the object parameters have be examined. 

**quarterLengthToTypeCandidate()**

    Return the type for a given quarterLength, otherwise return the type that is the largest that is not greater than this qLen 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTypeCandidate(.5)
    ('eighth', None, True) 
    >>> a.quarterLengthToTypeCandidate(.75)
    ('eighth', 'quarter', False) 
    >>> a.quarterLengthToTypeCandidate(1.75)
    ('quarter', 'half', False) 

**quarterLengthToUnitSpec()**

    Given a quarterLength, determine if it can be notated as a single unit, or if it needs to be divided into multiple units. (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we do not use that). Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType 

    >>> a = DurationCommon()
    >>> a.quarterLengthToUnitSpec(2)
    [(2, 'half', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3)
    [(3, 'half', 1, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(6.0)
    [(6.0, 'whole', 1, None, None, None)] 
    Double and triple dotted half note. 
    >>> a.quarterLengthToUnitSpec(3.5)
    [(3.5, 'half', 2, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3.75)
    [(3.75, 'half', 3, None, None, None)] 
    A triplet quarter note, lasting .6666 qLen 
    Or, a quarter that is 1/3 of a half. 
    Or, a quarter that is 2/3 of a quarter. 
    >>> a.quarterLengthToUnitSpec(.6666666666)
    [(0.66666666659999996, 'quarter', 0, 3, 2, 'quarter')] 
    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter 
    Or, an eighth that is 2/3 of eighth 
    >>> post = a.quarterLengthToUnitSpec(.3333333)
    >>> common.almostEquals(post[0][0], .3333333)
    True 
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth') 
    A half that is 1/3 of a whole, or a triplet half note. 
    Or, a half that is 2/3 of a half 
    >>> a.quarterLengthToUnitSpec(1.3333333)
    [(1.3333333000000001, 'half', 0, 3, 2, 'half')] 
    A sixteenth that is 1/5 of a quarter 
    Or, a sixteenth that is 4/5ths of a 16th 
    >>> a.quarterLengthToUnitSpec(.200000000)
    [(0.20000000000000001, '16th', 0, 5, 4, '16th')] 
    A 16th that is  1/7th of a quarter 
    Or, a 16th that is 4/7 of a 16th 
    >>> a.quarterLengthToUnitSpec(0.14285714285714285)
    [(0.14285714285714285, '16th', 0, 7, 4, '16th')] 
    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter 
    >>> a.quarterLengthToUnitSpec(0.5714285714285714)
    [(0.5714285714285714, 'quarter', 0, 7, 4, 'quarter')] 
    If a duration is not containable in a single unit, the method 
    will break off the largest type that fits within this type 
    and recurse, adding as my units as necessary. 
    >>> a.quarterLengthToUnitSpec(2.5)
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(2.3333333)
    [(2.0, 'half', 0, None, None, None), (0.33333330000000005, 'eighth', 0, 3, 2, 'eighth')] 
    >>> a.quarterLengthToUnitSpec(0.166666666667)
    [(0.166666666667, '16th', 0, 3, 2, '16th')] 

    

**setTypeFromNum()**

    No documentation.


Class Test
----------

No documentation.

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _testMethodDoc
+ _testMethodName

Public Methods
~~~~~~~~~~~~~~

**assertAlmostEqual()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertAlmostEquals()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertEqual()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**assertEquals()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**assertFalse()**

    Fail the test if the expression is true. 

**assertNotAlmostEqual()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertNotAlmostEquals()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertNotEqual()**

    Fail if the two objects are equal as determined by the '==' operator. 

**assertNotEquals()**

    Fail if the two objects are equal as determined by the '==' operator. 

**assertRaises()**

    Fail unless an exception of class excClass is thrown by callableObj when invoked with arguments args and keyword arguments kwargs. If a different type of exception is thrown, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception. 

**assertTrue()**

    Fail the test unless the expression is true. 

**assert_()**

    Fail the test unless the expression is true. 

**countTestCases()**

    No documentation.

**debug()**

    Run the test without collecting errors in a TestResult 

**defaultTestResult()**

    No documentation.

**fail()**

    Fail immediately, with the given message. 

**failIf()**

    Fail the test if the expression is true. 

**failIfAlmostEqual()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**failIfEqual()**

    Fail if the two objects are equal as determined by the '==' operator. 

**failUnless()**

    Fail the test unless the expression is true. 

**failUnlessAlmostEqual()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**failUnlessEqual()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**failUnlessRaises()**

    Fail unless an exception of class excClass is thrown by callableObj when invoked with arguments args and keyword arguments kwargs. If a different type of exception is thrown, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception. 

**failureException()**

    Assertion failed. 

**id()**

    No documentation.

**run()**

    No documentation.

**runTest()**

    No documentation.

**setUp()**

    Hook method for setting up the test fixture before exercising it. 

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testTuple()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


Class TestExternal
------------------

No documentation.

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _testMethodDoc
+ _testMethodName

Public Methods
~~~~~~~~~~~~~~

**assertAlmostEqual()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertAlmostEquals()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertEqual()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**assertEquals()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**assertFalse()**

    Fail the test if the expression is true. 

**assertNotAlmostEqual()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertNotAlmostEquals()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertNotEqual()**

    Fail if the two objects are equal as determined by the '==' operator. 

**assertNotEquals()**

    Fail if the two objects are equal as determined by the '==' operator. 

**assertRaises()**

    Fail unless an exception of class excClass is thrown by callableObj when invoked with arguments args and keyword arguments kwargs. If a different type of exception is thrown, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception. 

**assertTrue()**

    Fail the test unless the expression is true. 

**assert_()**

    Fail the test unless the expression is true. 

**countTestCases()**

    No documentation.

**debug()**

    Run the test without collecting errors in a TestResult 

**defaultTestResult()**

    No documentation.

**fail()**

    Fail immediately, with the given message. 

**failIf()**

    Fail the test if the expression is true. 

**failIfAlmostEqual()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**failIfEqual()**

    Fail if the two objects are equal as determined by the '==' operator. 

**failUnless()**

    Fail the test unless the expression is true. 

**failUnlessAlmostEqual()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**failUnlessEqual()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**failUnlessRaises()**

    Fail unless an exception of class excClass is thrown by callableObj when invoked with arguments args and keyword arguments kwargs. If a different type of exception is thrown, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception. 

**failureException()**

    Assertion failed. 

**id()**

    No documentation.

**run()**

    No documentation.

**runTest()**

    No documentation.

**setUp()**

    Hook method for setting up the test fixture before exercising it. 

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testBasic()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


Class Tuplet
------------

tuplet class: creates tuplet objects which modify duration objects note that this is a duration modifier.  We should also have a tupletGroup object that groups note objects into larger groups. 

Public Attributes
~~~~~~~~~~~~~~~~~

+ durationActual
+ durationNormal
+ nestedInside
+ nestedLevel
+ numberNotesActual
+ numberNotesNormal
+ tupletActualShow
+ tupletId
+ tupletNormalShow
+ type

Public Methods
~~~~~~~~~~~~~~

**setDurationType()**

    Set the Duration for both actual and normal. 

    >>> a = Tuplet()
    >>> a.tupletMultiplier()
    0.66666666666666663 
    >>> a.totalTupletLength()
    1.0 
    >>> a.setDurationType('half')
    >>> a.tupletMultiplier()
    0.66666666666666663 
    >>> a.totalTupletLength()
    4.0 

**setRatio()**

    Set the ratio of actual divisions to represented in normal divisions. A triplet is 3 actual in the time of 2 normal. 

    >>> a = Tuplet()
    >>> a.tupletMultiplier()
    0.66666666666666663 
    >>> a.setRatio(6,2)
    >>> a.tupletMultiplier()
    0.33333333333333331 
    >>> a = Tuplet()
    >>> a.setRatio(3,1)
    >>> a.durationActual = DurationUnit('quarter')
    >>> a.durationNormal = DurationUnit('half')
    >>> a.tupletMultiplier()
    0.66666666666666663 
    >>> a.totalTupletLength()
    2.0 

**totalTupletLength()**

    The total length in quarters of the tuplet as defined, assuming that the tuplet has all components present and is complete. 

    >>> a = Tuplet()
    >>> a.totalTupletLength()
    1.0 
    >>> a.numberNotesActual = 3
    >>> a.durationActual = Duration('half')
    >>> a.numberNotesNormal = 3
    >>> a.durationNormal = Duration('half')
    >>> a.totalTupletLength()
    6.0 
    >>> a.setRatio(4,5)
    >>> a.totalTupletLength()
    10.0 
    >>> a.setRatio(2,5)
    >>> a.totalTupletLength()
    10.0 

**tupletActual()**

    No documentation.

**tupletMultiplier()**

    Get a floating point value by which to scale the duration that this Tuplet is associated with. 

    >>> a = Tuplet()
    >>> a.tupletMultiplier()
    0.66666666666666663 
    >>> a.tupletActual = [5, Duration('eighth')]
    >>> a.tupletMultiplier()
    0.40000000000000002 

**tupletNormal()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_getTupletActual()**

    No documentation.

**_getTupletNormal()**

    No documentation.

**_setTupletActual()**

    No documentation.

**_setTupletNormal()**

    No documentation.


Class ZeroDuration
------------------

No documentation.

Public Attributes
~~~~~~~~~~~~~~~~~

+ durationToType
+ ordinalTypeFromNum
+ typeFromNumDict
+ typeToDuration

Public Methods
~~~~~~~~~~~~~~

**clone()**

    No documentation.

**convertNumberToType()**

    Convert a number ( 4 = quarter; 8 = eighth), etc. to type. 

    >>> a = DurationCommon()
    >>> a.convertNumberToType(4)
    'quarter' 
    >>> a.convertNumberToType(32)
    '32nd' 

**convertQuarterLengthToDuration()**

    Given a an arbitrary quarter length, convert it into a the parameters necessary to instantiate a DurationUnit object. Note: this now uses quarterLengthToUnitSpec(); this method remains for backward compatibility; but can be replaced 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToDuration(3)
    ('half', [1], []) 
    >>> a.convertQuarterLengthToDuration(1)
    ('quarter', [0], []) 
    >>> a.convertQuarterLengthToDuration(.75)
    ('eighth', [1], []) 
    >>> a.convertQuarterLengthToDuration(.125)
    ('32nd', [0], []) 
    >>> post = a.convertQuarterLengthToDuration(.33333)
    >>> post[0] == 'eighth'
    True 
    >>> post[1] == [0]
    True 
    >>> isinstance(post[2][0], Tuplet)
    True 

**convertQuarterLengthToType()**

    Convert quarter lengths to types. This cannot handle quarter lengths of 3 or .75 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToType(2)
    'half' 
    >>> a.convertQuarterLengthToType(0.125)
    '32nd' 

**convertTypeToNumber()**

    Convert duration type to 

    >>> a = DurationCommon()
    >>> a.convertTypeToNumber('quarter')
    4 
    >>> a.convertTypeToNumber('half')
    2 

**convertTypeToOrdinal()**

    Convert type to an ordinal number based on self.ordinalTypeFromNum 

    >>> a = DurationCommon()
    >>> a.convertTypeToOrdinal('whole')
    4 
    >>> a.convertTypeToOrdinal('maxima')
    1 
    >>> a.convertTypeToOrdinal('1024th')
    14 

**convertTypeToQuarterLength()**

    Given a rhythm type, convert it to a quarter length, given a lost of dots and tuplets. 

    >>> a = DurationCommon()
    >>> a.convertTypeToQuarterLength('whole')
    4.0 
    >>> a.convertTypeToQuarterLength('16th')
    0.25 
    >>> a.convertTypeToQuarterLength('quarter', [2])
    1.75 

**ordinalNumFromType()**

    for backward compatibility; replace with property ordinal 

**partitionToUnitSpec()**

    Given any qLen, partition into one or more quarterLengthUnits based on a specified qLenDiv Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType Dividing 2.5 qLen into eighth notes. 

    >>> a = DurationCommon()
    >>> a.partitionToUnitSpec(2.5,.5)
    ([(0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5 qLen into 2.5 qLen bundles 
    >>> a.partitionToUnitSpec(5,2.5)
    ([(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5.25 qLen into dotted halves 
    >>> a.partitionToUnitSpec(5.25,3)
    ([(3, 'half', 1, None, None, None), (2.0, 'half', 0, None, None, None), (0.25, '16th', 0, None, None, None)], False) 

    
    Dividing 1.33333 qLen into triplet eighths: 
    >>> a.partitionToUnitSpec(1.33333333333333,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth')], True) 

    
    Dividing 1.5 into triplet eighths 
    >>> a.partitionToUnitSpec(1.5,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.16666666666668023, '16th', 0, 3, 2, '16th')], False) 

    
    No problem if the division unit is larger then the source duration. 
    >>> a.partitionToUnitSpec(1.5, 4)
    ([(1.5, 'quarter', 1, None, None, None)], False) 

    

**quarterLength()**

    No documentation.

**quarterLengthToDotCandidate()**

    Given a qLen and type that is less than but not greater than qLen, determine if one or more dots match. TODO: Find and return dotgroups, perhaps based on optional flag 

    >>> a = DurationCommon()
    >>> a.quarterLengthToDotCandidate(3, 'half')
    (1, True) 

**quarterLengthToTupletCandidate()**

    Return one or more possible tuplets for a given qLen. 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTupletCandidate(.33333333)
    [[3, 2, 'eighth'], [3, 1, 'quarter']] 
    By specifying only 1 count, the tuple with the smallest type will be 
    returned. 
    >>> a.quarterLengthToTupletCandidate(.3333333, 1)
    [[3, 2, 'eighth']] 

    
    >>> a.quarterLengthToTupletCandidate(.20)
    [[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
    #ARIZA: would this be more portable if it returned a list of 
    # Tuplet objects instead 
    # this would work fine, but is harder to test in the short term, 
    # b/c the object parameters have be examined. 

**quarterLengthToTypeCandidate()**

    Return the type for a given quarterLength, otherwise return the type that is the largest that is not greater than this qLen 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTypeCandidate(.5)
    ('eighth', None, True) 
    >>> a.quarterLengthToTypeCandidate(.75)
    ('eighth', 'quarter', False) 
    >>> a.quarterLengthToTypeCandidate(1.75)
    ('quarter', 'half', False) 

**quarterLengthToUnitSpec()**

    Given a quarterLength, determine if it can be notated as a single unit, or if it needs to be divided into multiple units. (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we do not use that). Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType 

    >>> a = DurationCommon()
    >>> a.quarterLengthToUnitSpec(2)
    [(2, 'half', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3)
    [(3, 'half', 1, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(6.0)
    [(6.0, 'whole', 1, None, None, None)] 
    Double and triple dotted half note. 
    >>> a.quarterLengthToUnitSpec(3.5)
    [(3.5, 'half', 2, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3.75)
    [(3.75, 'half', 3, None, None, None)] 
    A triplet quarter note, lasting .6666 qLen 
    Or, a quarter that is 1/3 of a half. 
    Or, a quarter that is 2/3 of a quarter. 
    >>> a.quarterLengthToUnitSpec(.6666666666)
    [(0.66666666659999996, 'quarter', 0, 3, 2, 'quarter')] 
    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter 
    Or, an eighth that is 2/3 of eighth 
    >>> post = a.quarterLengthToUnitSpec(.3333333)
    >>> common.almostEquals(post[0][0], .3333333)
    True 
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth') 
    A half that is 1/3 of a whole, or a triplet half note. 
    Or, a half that is 2/3 of a half 
    >>> a.quarterLengthToUnitSpec(1.3333333)
    [(1.3333333000000001, 'half', 0, 3, 2, 'half')] 
    A sixteenth that is 1/5 of a quarter 
    Or, a sixteenth that is 4/5ths of a 16th 
    >>> a.quarterLengthToUnitSpec(.200000000)
    [(0.20000000000000001, '16th', 0, 5, 4, '16th')] 
    A 16th that is  1/7th of a quarter 
    Or, a 16th that is 4/7 of a 16th 
    >>> a.quarterLengthToUnitSpec(0.14285714285714285)
    [(0.14285714285714285, '16th', 0, 7, 4, '16th')] 
    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter 
    >>> a.quarterLengthToUnitSpec(0.5714285714285714)
    [(0.5714285714285714, 'quarter', 0, 7, 4, 'quarter')] 
    If a duration is not containable in a single unit, the method 
    will break off the largest type that fits within this type 
    and recurse, adding as my units as necessary. 
    >>> a.quarterLengthToUnitSpec(2.5)
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(2.3333333)
    [(2.0, 'half', 0, None, None, None), (0.33333330000000005, 'eighth', 0, 3, 2, 'eighth')] 
    >>> a.quarterLengthToUnitSpec(0.166666666667)
    [(0.166666666667, '16th', 0, 3, 2, '16th')] 

    

**setTypeFromNum()**

    No documentation.


