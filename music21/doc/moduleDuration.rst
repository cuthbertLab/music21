music21.duration
================

Function convertQuarterLengthToType()
-------------------------------------

similar to quarterLengthToClosestType but only returns exact matches 

>>> convertQuarterLengthToType(2)
'half' 
>>> convertQuarterLengthToType(0.125)
'32nd' 

Function convertTypeToNumber()
------------------------------



>>> convertTypeToNumber('quarter')
4 
>>> convertTypeToNumber('half')
2 

Function convertTypeToQuarterLength()
-------------------------------------

Given a rhythm type, number of dots, and list of Tuplet objects, give its quarter length. 

>>> convertTypeToQuarterLength('whole')
4.0 
>>> convertTypeToQuarterLength('16th')
0.25 
>>> convertTypeToQuarterLength('quarter', 2)
1.75 
Also can handle medieval dot groups. 
>>> convertTypeToQuarterLength('half', dotGroups = [1,1])
4.5 

Function dottedMatch()
----------------------

(was quarterLengthToDotCandidate) given a qLen, determine if there is a dotted (or non-dotted) type that exactly matches.  Returns (numDots, type) or (False, False) if non matches exactly. Returns a maximum of four dots by default. 

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



Function nextLargerType()
-------------------------

given a type return the next larger one: 

>>> nextLargerType("16th")
'eighth' 
>>> nextLargerType("whole")
'breve' 

Function partitionQuarterLength()
---------------------------------

Given a quarterLength and a base quarterLength to divide it into (default 4 = whole notes), return a list of Durations that partition the given quarterLength after each division. (Little demonstration method) 

>>> def pql(qLen, qLenDiv):
...    partitionList = partitionQuarterLength(qLen, qLenDiv) 
...    for dur in partitionList: 
...        print unitSpec(dur) 


>>> pql(2.5,.5)
(0.5, 'eighth', 0, None, None, None) 
(0.5, 'eighth', 0, None, None, None) 
(0.5, 'eighth', 0, None, None, None) 
(0.5, 'eighth', 0, None, None, None) 
(0.5, 'eighth', 0, None, None, None) 
Dividing 5 qLen into 2.5 qLen bundles 
>>> pql(5, 2.5)
(2.0, 'half', 0, None, None, None) 
(0.5, 'eighth', 0, None, None, None) 
(2.0, 'half', 0, None, None, None) 
(0.5, 'eighth', 0, None, None, None) 
Dividing 5.25 qLen into dotted halves 
>>> pql(5.25,3)
(3.0, 'half', 1, None, None, None) 
(2.0, 'half', 0, None, None, None) 
(0.25, '16th', 0, None, None, None) 
Dividing 1.33333 qLen into triplet eighths: 
>>> pql(4.0/3.0, 1.0/3.0)
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
Dividing 1.5 into triplet eighths 
>>> pql(1.5,.33333333333333)
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.333..., 'eighth', 0, 3, 2, 'eighth') 
(0.1666..., '16th', 0, 3, 2, '16th') 
No problem if the division unit is larger then the source duration. 
>>> pql(1.5, 4)
(1.5, 'quarter', 1, None, None, None) 



Function quarterLengthToClosestType()
-------------------------------------

## was quarterLengthToTypeCandidate Returns a two-unit tuple consisting of 1. the type string ("quarter") that is smaller than or equal to the qLen 2. bool, True or False whether the conversion was exact. 

>>> quarterLengthToClosestType(.5)
('eighth', True) 
>>> quarterLengthToClosestType(.75)
('eighth', False) 
>>> quarterLengthToClosestType(1.8)
('quarter', False) 

Function quarterLengthToDurations()
-----------------------------------

(was quarterLengthToUnitSpec) Returns a List of new Durations (each with only a single component) given a quarter length. For many simple quarterLengths, the list will have only a single element.  However, for more complex durations, the list could contain several durations (presumably to be tied to each other). (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we don't like doing that). This is mainly a utility function.  Much faster for many purposes is: d = Duration() d.quarterLength = 251.231312 and only have the components created as needed. 

These examples use unitSpec() to get a concise summary of the contents 

>>> unitSpec(quarterLengthToDurations(2))
[(2.0, 'half', 0, None, None, None)] 
dots are supported 
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
If a duration is not containable in a single unit, the method 
will break off the largest type that fits within this type 
and recurse, adding as my units as necessary. 
>>> unitSpec(quarterLengthToDurations(2.5))
[(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
>>> unitSpec(quarterLengthToDurations(2.3333333))
[(2.0, 'half', 0, None, None, None), (0.333..., 'eighth', 0, 3, 2, 'eighth')] 
>>> unitSpec(quarterLengthToDurations(1.0/6.0))
[(0.1666..., '16th', 0, 3, 2, '16th')] 



Function quarterLengthToTuplet()
--------------------------------

Returns a list of possible Tuplet objects for a given qLen up to the maxTotReturn Searches for numerators specified in defaultTupletNumerators (3, 5, 7, 11, 13) does not return dotted tuplets, nor nested tuplets. (was quarterLengthToTupletCandidate) Note that 4:3 tuplets won't be found, but will be found as dotted notes by dottedMatch 

>>> quarterLengthToTuplet(.33333333)
[[3, 2, 'eighth'], [3, 1, 'quarter']] 
By specifying only 1 count, the tuple with the smallest type will be 
returned. 
>>> quarterLengthToTuplet(.3333333, 1)
[[3, 2, 'eighth']] 
>>> quarterLengthToTuplet(.20)
[[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
>>> c = quarterLengthToTuplet(.3333333, 1)[0]
>>> c.tupletMultiplier()
0.6666... 

Function roundDuration()
------------------------


Function unitSpec()
-------------------

simple representation of most durationObjects. works on a single DurationObject or a List of them, returning a list of unitSpecs if given a list otherwise returns a single one A unitSpec is a tuple of qLen, durType, dots, tupleNumerator, tupletDenominator, tupletType (assuming top and bottom are the same). Does not deal with nested tuplets, etc. 

Class AppogiaturaStartDuration
------------------------------


Attributes
~~~~~~~~~~

+ linkages

Methods
~~~~~~~

**addDuration()**

    Add a DurationUnit or a Duration's components to this Duration. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)
    >>> a.quarterLength
    2.0 
    >>> a.type
    'complex' 

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**clear()**

    Permit all componets to be removed. (It is not clear yet if this is needed) 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> a.type
    'zero' 

**clone()**


**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like) 
    better is just to copy and paste three times.  Very easy to see what 
    is happening. 
    >>> for x in [1,1,1]:
    ...   components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    ARIZA: let's not call private methods from inside public docs. 
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

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

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

**components()**


**consolidate()**

    Given a Duration with multiple components, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

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

**dots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**expand()**

    Make a duration notatable by partitioning it into smaller units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength 

**fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**isComplex()**


**lily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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

**quarterLength()**

    Can be the same as the base class. 

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
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


**type()**

    Get the duration type. 

**updateQuarterLength()**

    Look to components and determine quarter length. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_getComponents()**


**_getDots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**_getLily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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


**_getType()**

    Get the duration type. 

**_isComplex()**


**_setComponents()**


**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

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

**_setQuarterLength()**

    Set the quarter note length to the specified value. Currently (if the value is different from what is already stored) this wipes out any existing components, not preserving their type.  So if you've set up Duration(1.5) as 3-eighth notes, setting Duration to 1.75 will NOT dot the last eighth note, but instead give you a single double-dotted half note. 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (3.5, 'half', 2, None, None, None) 
    >>> a.quarterLength = 2.5
    >>> a.quarterLength
    2.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (2.0, 'half', 0, None, None, None) 
    (0.5, 'eighth', 0, None, None, None) 

**_setTuplets()**


**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateComponents()**



Class AppogiaturaStopDuration
-----------------------------


Attributes
~~~~~~~~~~

+ linkages

Methods
~~~~~~~

**addDuration()**

    Add a DurationUnit or a Duration's components to this Duration. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)
    >>> a.quarterLength
    2.0 
    >>> a.type
    'complex' 

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**clear()**

    Permit all componets to be removed. (It is not clear yet if this is needed) 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> a.type
    'zero' 

**clone()**


**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like) 
    better is just to copy and paste three times.  Very easy to see what 
    is happening. 
    >>> for x in [1,1,1]:
    ...   components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    ARIZA: let's not call private methods from inside public docs. 
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

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

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

**components()**


**consolidate()**

    Given a Duration with multiple components, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

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

**dots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**expand()**

    Make a duration notatable by partitioning it into smaller units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength 

**fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**isComplex()**


**lily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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

**quarterLength()**

    Can be the same as the base class. 

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
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


**type()**

    Get the duration type. 

**updateQuarterLength()**

    Look to components and determine quarter length. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_getComponents()**


**_getDots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**_getLily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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


**_getType()**

    Get the duration type. 

**_isComplex()**


**_setComponents()**


**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

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

**_setQuarterLength()**

    Set the quarter note length to the specified value. Currently (if the value is different from what is already stored) this wipes out any existing components, not preserving their type.  So if you've set up Duration(1.5) as 3-eighth notes, setting Duration to 1.75 will NOT dot the last eighth note, but instead give you a single double-dotted half note. 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (3.5, 'half', 2, None, None, None) 
    >>> a.quarterLength = 2.5
    >>> a.quarterLength
    2.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (2.0, 'half', 0, None, None, None) 
    (0.5, 'eighth', 0, None, None, None) 

**_setTuplets()**


**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateComponents()**



Class Duration
--------------

Durations are one of the most important objects in music21.  A Duration represents a span of musical time measurable in terms of quarter notes (or in advanced usage other units).  For instance, "57 quarter notes" or "dotted half tied to quintuplet sixteenth note" or simply "quarter note" 

A Duration is made of one or more DurationUnits. Multiple DurationUnits in a single Duration may be used to express tied notes, or may be used to split duration across barlines or beam groups. Some Durations are not expressable as a single notation unit. 

Attributes
~~~~~~~~~~

+ linkages

Methods
~~~~~~~

**addDuration()**

    Add a DurationUnit or a Duration's components to this Duration. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)
    >>> a.quarterLength
    2.0 
    >>> a.type
    'complex' 

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**clear()**

    Permit all componets to be removed. (It is not clear yet if this is needed) 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> a.type
    'zero' 

**clone()**


**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like) 
    better is just to copy and paste three times.  Very easy to see what 
    is happening. 
    >>> for x in [1,1,1]:
    ...   components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    ARIZA: let's not call private methods from inside public docs. 
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

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

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

**components()**


**consolidate()**

    Given a Duration with multiple components, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

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

**dots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**expand()**

    Make a duration notatable by partitioning it into smaller units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength 

**fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**isComplex()**


**lily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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

**quarterLength()**

    Can be the same as the base class. 

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
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


**type()**

    Get the duration type. 

**updateQuarterLength()**

    Look to components and determine quarter length. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_getComponents()**


**_getDots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**_getLily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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


**_getType()**

    Get the duration type. 

**_isComplex()**


**_setComponents()**


**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

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

**_setQuarterLength()**

    Set the quarter note length to the specified value. Currently (if the value is different from what is already stored) this wipes out any existing components, not preserving their type.  So if you've set up Duration(1.5) as 3-eighth notes, setting Duration to 1.75 will NOT dot the last eighth note, but instead give you a single double-dotted half note. 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (3.5, 'half', 2, None, None, None) 
    >>> a.quarterLength = 2.5
    >>> a.quarterLength
    2.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (2.0, 'half', 0, None, None, None) 
    (0.5, 'eighth', 0, None, None, None) 

**_setTuplets()**


**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateComponents()**



Class DurationCommon
--------------------

base class for Duration and DurationUnit to borrow from 

Methods
~~~~~~~

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 


Class DurationException
-----------------------


Methods
~~~~~~~

**args()**


**message()**



Class DurationUnit
------------------

A DurationUnit is a notation that (generally) can be notated with a a single notation unit, such as one note, without a tie. In general, Duration should be used. Like Durations, DurationUnits have the option of unlinking the quarterLength and its representation on the page.  For instance, in 12/16, Brahms sometimes used a dotted half note to indicate the length of 11/16th of a note. (see Don Byrd's Extreme Notation webpage for more information). Additional types are needed: 'zero' type for zero durations 'unexpressable' type for anything that needs a Duration (such as 2.5 quarters) 

Attributes
~~~~~~~~~~

+ linkStatus

Methods
~~~~~~~

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**dots()**

    _dots is a list (so we can do weird things like Crumb half-dots) Normally we only want the first element. So that's what _getDots returns... 

**lily()**

    Simple lily duration: does not include tuplets; these appear in the Stream object, because of how lily represents triplets 

**link()**


**ordinal()**

    Converts type to an ordinal number where maxima = 1 and 1024th = 14; whole = 4 and quarter = 6 based on duration.ordinalTypeFromNum 

    >>> a = DurationUnit('whole')
    >>> a.ordinal
    4 
    >>> b = DurationUnit('maxima')
    >>> b.ordinal
    1 
    >>> c = DurationUnit('1024th')
    >>> c.ordinal
    14 

**quarterLength()**

    determine the length in quarter notes from current information 

**setTypeFromNum()**


**tuplets()**

    Return a list of Tuplet objects 

**type()**

    Get the duration type. 

**unlink()**


**updateQuarterLength()**

    Updates the quarterLength if linkStatus is True Called by self._getQuarterLength if _quarterLengthNeedsUpdating is set to True. (use self.quarterLength = X to set) 

**updateType()**


Private Methods
~~~~~~~~~~~~~~~

**_getDots()**

    _dots is a list (so we can do weird things like Crumb half-dots) Normally we only want the first element. So that's what _getDots returns... 

**_getLily()**

    Simple lily duration: does not include tuplets; these appear in the Stream object, because of how lily represents triplets 

**_getOrdinal()**

    Converts type to an ordinal number where maxima = 1 and 1024th = 14; whole = 4 and quarter = 6 based on duration.ordinalTypeFromNum 

    >>> a = DurationUnit('whole')
    >>> a.ordinal
    4 
    >>> b = DurationUnit('maxima')
    >>> b.ordinal
    1 
    >>> c = DurationUnit('1024th')
    >>> c.ordinal
    14 

**_getQuarterLength()**

    determine the length in quarter notes from current information 

**_getTuplets()**

    Return a list of Tuplet objects 

**_getType()**

    Get the duration type. 

**_setDots()**

    Sets the number of dots Having this as a method permits error checking. 

    >>> a = DurationUnit()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

    

**_setQuarterLength()**

    Set the quarter note length to the specified value. (We no longer unlink if quarterLength is greater than a long) 

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

**_setTuplets()**

    Takes in a list of Tuplet objects 

**_setType()**

    Set the type length to the specified value. Check for bad types. 

    >>> a = Duration()
    >>> a.type = '128th'
    >>> a.quarterLength
    0.03125 
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 


Class GraceDuration
-------------------


Attributes
~~~~~~~~~~

+ linkages

Methods
~~~~~~~

**addDuration()**

    Add a DurationUnit or a Duration's components to this Duration. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)
    >>> a.quarterLength
    2.0 
    >>> a.type
    'complex' 

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**clear()**

    Permit all componets to be removed. (It is not clear yet if this is needed) 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> a.type
    'zero' 

**clone()**


**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like) 
    better is just to copy and paste three times.  Very easy to see what 
    is happening. 
    >>> for x in [1,1,1]:
    ...   components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    ARIZA: let's not call private methods from inside public docs. 
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

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

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

**components()**


**consolidate()**

    Given a Duration with multiple components, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

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

**dots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**expand()**

    Make a duration notatable by partitioning it into smaller units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength 

**fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**isComplex()**


**lily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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

**quarterLength()**

    Can be the same as the base class. 

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
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


**type()**

    Get the duration type. 

**updateQuarterLength()**

    Look to components and determine quarter length. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_getComponents()**


**_getDots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**_getLily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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


**_getType()**

    Get the duration type. 

**_isComplex()**


**_setComponents()**


**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

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

**_setQuarterLength()**

    Set the quarter note length to the specified value. Currently (if the value is different from what is already stored) this wipes out any existing components, not preserving their type.  So if you've set up Duration(1.5) as 3-eighth notes, setting Duration to 1.75 will NOT dot the last eighth note, but instead give you a single double-dotted half note. 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (3.5, 'half', 2, None, None, None) 
    >>> a.quarterLength = 2.5
    >>> a.quarterLength
    2.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (2.0, 'half', 0, None, None, None) 
    (0.5, 'eighth', 0, None, None, None) 

**_setTuplets()**


**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateComponents()**



Class LongGraceDuration
-----------------------


Attributes
~~~~~~~~~~

+ linkages

Methods
~~~~~~~

**addDuration()**

    Add a DurationUnit or a Duration's components to this Duration. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)
    >>> a.quarterLength
    2.0 
    >>> a.type
    'complex' 

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**clear()**

    Permit all componets to be removed. (It is not clear yet if this is needed) 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> a.type
    'zero' 

**clone()**


**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like) 
    better is just to copy and paste three times.  Very easy to see what 
    is happening. 
    >>> for x in [1,1,1]:
    ...   components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    ARIZA: let's not call private methods from inside public docs. 
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

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

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

**components()**


**consolidate()**

    Given a Duration with multiple components, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

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

**dots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**expand()**

    Make a duration notatable by partitioning it into smaller units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength 

**fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**isComplex()**


**lily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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

**quarterLength()**

    Can be the same as the base class. 

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
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


**type()**

    Get the duration type. 

**updateQuarterLength()**

    Look to components and determine quarter length. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_getComponents()**


**_getDots()**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**_getLily()**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

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


**_getType()**

    Get the duration type. 

**_isComplex()**


**_setComponents()**


**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

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

**_setQuarterLength()**

    Set the quarter note length to the specified value. Currently (if the value is different from what is already stored) this wipes out any existing components, not preserving their type.  So if you've set up Duration(1.5) as 3-eighth notes, setting Duration to 1.75 will NOT dot the last eighth note, but instead give you a single double-dotted half note. 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (3.5, 'half', 2, None, None, None) 
    >>> a.quarterLength = 2.5
    >>> a.quarterLength
    2.5 
    >>> for thisUnit in a.components:
    ...    print unitSpec(thisUnit) 
    (2.0, 'half', 0, None, None, None) 
    (0.5, 'eighth', 0, None, None, None) 

**_setTuplets()**


**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateComponents()**



Class TestExternal
------------------


Methods
~~~~~~~

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


**debug()**

    Run the test without collecting errors in a TestResult 

**defaultTestResult()**


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


**run()**


**runTest()**


**setUp()**

    Hook method for setting up the test fixture before exercising it. 

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testBasic()**


**testSingle()**


Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


Class Tuplet
------------

tuplet class: creates tuplet objects which modify duration objects note that this is a duration modifier.  We should also have a tupletGroup object that groups note objects into larger groups. 

>>> myTup = Tuplet(numberNotesActual = 5, numberNotesNormal = 4)
>>> print myTup.tupletMultiplier()
0.8 

Attributes
~~~~~~~~~~

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

Methods
~~~~~~~

**setDurationType()**

    Set the Duration for both actual and normal. 

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

**setRatio()**

    Set the ratio of actual divisions to represented in normal divisions. A triplet is 3 actual in the time of 2 normal. 

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

**totalTupletLength()**

    The total length in quarters of the tuplet as defined, assuming that enough notes existed to fill all entire tuplet as defined. For instance, 3 quarters in the place of 2 quarters = 2.0 5 half notes in the place of a 2 dotted half notes = 6.0 (In the end it's only the denominator that matters) 

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

**tupletActual()**


**tupletMultiplier()**

    Get a floating point value by which to scale the duration that this Tuplet is associated with. 

    >>> myTuplet = Tuplet()
    >>> print round(myTuplet.tupletMultiplier(), 3)
    0.667 
    >>> myTuplet.tupletActual = [5, Duration('eighth')]
    >>> myTuplet.numberNotesActual
    5 
    >>> myTuplet.durationActual.type
    'eighth' 
    >>> print myTuplet.tupletMultiplier()
    0.4 

**tupletNormal()**


Private Methods
~~~~~~~~~~~~~~~

**_getTupletActual()**


**_getTupletNormal()**


**_setTupletActual()**


**_setTupletNormal()**



Class ZeroDuration
------------------


Attributes
~~~~~~~~~~

+ linkStatus

Methods
~~~~~~~

**aggregateTupletRatio()**

    say you have 3:2 under a 5:4.  This will give the equivalent in non-nested tuplets. Returns a tuple! (15, 8) in this case. Needed for MusicXML time-modification 

    >>> complexDur = Duration('eighth')
    >>> complexDur.tuplets.append(Tuplet())
    >>> complexDur.aggregateTupletRatio()
    (3, 2) 
    >>> tup2 = Tuplet()
    >>> tup2.setRatio(5, 4)
    >>> complexDur.tuplets.append(tup2)
    >>> complexDur.aggregateTupletRatio()
    (15, 8) 

**dots()**

    _dots is a list (so we can do weird things like Crumb half-dots) Normally we only want the first element. So that's what _getDots returns... 

**lily()**

    Simple lily duration: does not include tuplets; these appear in the Stream object, because of how lily represents triplets 

**link()**


**ordinal()**

    Converts type to an ordinal number where maxima = 1 and 1024th = 14; whole = 4 and quarter = 6 based on duration.ordinalTypeFromNum 

    >>> a = DurationUnit('whole')
    >>> a.ordinal
    4 
    >>> b = DurationUnit('maxima')
    >>> b.ordinal
    1 
    >>> c = DurationUnit('1024th')
    >>> c.ordinal
    14 

**quarterLength()**

    determine the length in quarter notes from current information 

**setTypeFromNum()**


**tuplets()**

    Return a list of Tuplet objects 

**type()**

    Get the duration type. 

**unlink()**


**updateQuarterLength()**

    Updates the quarterLength if linkStatus is True Called by self._getQuarterLength if _quarterLengthNeedsUpdating is set to True. (use self.quarterLength = X to set) 

**updateType()**


Private Methods
~~~~~~~~~~~~~~~

**_getDots()**

    _dots is a list (so we can do weird things like Crumb half-dots) Normally we only want the first element. So that's what _getDots returns... 

**_getLily()**

    Simple lily duration: does not include tuplets; these appear in the Stream object, because of how lily represents triplets 

**_getOrdinal()**

    Converts type to an ordinal number where maxima = 1 and 1024th = 14; whole = 4 and quarter = 6 based on duration.ordinalTypeFromNum 

    >>> a = DurationUnit('whole')
    >>> a.ordinal
    4 
    >>> b = DurationUnit('maxima')
    >>> b.ordinal
    1 
    >>> c = DurationUnit('1024th')
    >>> c.ordinal
    14 

**_getQuarterLength()**

    determine the length in quarter notes from current information 

**_getTuplets()**

    Return a list of Tuplet objects 

**_getType()**

    Get the duration type. 

**_setDots()**

    Sets the number of dots Having this as a method permits error checking. 

    >>> a = DurationUnit()
    >>> a.type = 'quarter'
    >>> a.dots = 1
    >>> a.quarterLength
    1.5 
    >>> a.dots = 2
    >>> a.quarterLength
    1.75 

    

**_setQuarterLength()**

    Set the quarter note length to the specified value. (We no longer unlink if quarterLength is greater than a long) 

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

**_setTuplets()**

    Takes in a list of Tuplet objects 

**_setType()**

    Set the type length to the specified value. Check for bad types. 

    >>> a = Duration()
    >>> a.type = '128th'
    >>> a.quarterLength
    0.03125 
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 


