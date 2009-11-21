music21.common
==============



Utility constants, dictionaries, functions, and objects used throughout music21.

Function EuclidGCD()
--------------------

use Euclid's algorithm to find the GCD of a and b 

Function almostEquals()
-----------------------

The following four routines work for comparisons between floats that are normally inconsistent. almostEquals(x, y) -- returns True if x and y are within 0.0000001 of each other 

Function basicallyEqual()
-------------------------

returns true if a and b are equal except for whitespace differences 

>>> a = " hello there "
>>> b = "hello there"
>>> c = " bye there "
>>> basicallyEqual(a,b)
True 
>>> basicallyEqual(a,c)
False 

Function decimalToTuplet()
--------------------------

For simple decimals (mostly > 1), a quick way to figure out the fraction in lowest terms that gives a valid tuplet. No it does not work really fast.  No it does not return tuplets with denominators over 100.  Too bad, math geeks.  This is real life. returns (numerator, denominator) 

Function dotMultiplier()
------------------------

dotMultiplier(dots) returns how long to multiply the note length of a note in order to get the note length with n dots 

>>> dotMultiplier(1)
1.5 
>>> dotMultiplier(2)
1.75 
>>> dotMultiplier(3)
1.875 

Function findFormat()
---------------------

Given a format defined either by a format name or an extension, return the format name as well as the output exensions 

>>> findFormat('mx')
('musicxml', '.mxl') 
>>> findFormat('.mxl')
('musicxml', '.mxl') 
>>> findFormat('musicxml')
('musicxml', '.mxl') 
>>> findFormat('jpeg')
('jpeg', '.jpg') 
>>> findFormat('lily')
('lilypond', '.ly') 
>>> findFormat('jpeg')
('jpeg', '.jpg') 
>>> findFormat('humdrum')
('humdrum', '.krn') 

Function findFormatFile()
-------------------------

Given a file path (relative or absolute) return the format 

>>> findFormatFile('test.xml')
'musicxml' 
>>> findFormatFile('long/file/path/test-2009.03.02.xml')
'musicxml' 
>>> findFormatFile('long/file/path.intermediate.png/test-2009.03.xml')
'musicxml' 
Windows drive + pickle 
>>> findFormatFile('d:/long/file/path/test.p')
'pickle' 
On a windows networked filesystem 
>>> findFormatFile('\\long\file\path\test.krn')
'humdrum' 



Function findInputExtension()
-----------------------------

Given an input format, find and return all possible input extensions. 

>>> a = findInputExtension('musicxml')
>>> a
['xml', 'mxl', 'mx'] 
>>> a = findInputExtension('mx')
>>> a
['xml', 'mxl', 'mx'] 
>>> a = findInputExtension('humdrum')
>>> a
['krn'] 

Function findSimpleFraction()
-----------------------------


Function formatStr()
--------------------

Format one or more data elements into string suitable for printing straight to stderr or other outputs 

>>> a = formatStr('test', '1', 2, 3)
>>> print a
test 1 2 3 
<BLANKLINE> 

Function fromRoman()
--------------------


Function getMd5()
-----------------

Return a string from an md5 haslib 

>>> getMd5('test')
'098f6bcd4621d373cade4e832627b4f6' 

Function getPlatform()
----------------------

Shared function to get platform names. 

Function greaterThan()
----------------------

greaterThan returns True if x is greater than and not almostEquals y 

Function isIterable()
---------------------

Returns True if is the object can be iter'd over 

>>> isIterable([])
True 
>>> isIterable('sharp')
False 
>>> isIterable((None, None))
True 
>>> import music21.stream
>>> isIterable(music21.stream.Stream())
True 

Function isListLike()
---------------------

Returns True if is a List or a Set or a Tuple #TODO: add immutable sets and pre 2.6 set support 

>>> isListLike([])
True 
>>> isListLike('sharp')
False 
>>> isListLike((None, None))
True 
>>> import music21.stream
>>> isListLike(music21.stream.Stream())
False 

Function isNum()
----------------

check if usrData is a number (float, int, long, Decimal), return boolean IMPROVE: when 2.6 is everwhere: add numbers class. 

>>> isNum(3.0)
True 
>>> isNum(3)
True 
>>> isNum('three')
False 

Function isPowerOfTwo()
-----------------------

returns True if argument is either a power of 2 or a reciprocal of a power of 2. Uses almostEquals so that a float whose reminder after taking a log is nearly zero is still True 

>>> isPowerOfTwo(3)
False 
>>> isPowerOfTwo(18)
False 
>>> isPowerOfTwo(1024)
True 
>>> isPowerOfTwo(1024.01)
False 
>>> isPowerOfTwo(1024.00001)
True 

Function isStr()
----------------

Check of usrData is some form of string, including unicode. 

>>> isStr(3)
False 
>>> isStr('sharp')
True 
>>> isStr(u'flat')
True 

Function lcm()
--------------



>>> lcm([3,4,5])
60 
>>> lcm([3,4])
12 
>>> lcm([1,2])
2 
>>> lcm([3,6])
6 

Function lessThan()
-------------------

lessThan -- returns True if x is less than and not almostEquals y 

Function sortFilesRecent()
--------------------------

Given two files, sort by most recent. Return only the file paths. 

>>> a = os.listdir(os.curdir)
>>> b = sortFilesRecent(a)

Function sortModules()
----------------------

Sort a lost of imported module names such that most recently modified is first 

Function stripAddresses()
-------------------------

Function that changes all memory addresses in the given textString with (replacement).  This is useful for testing that a function gives an expected result even if the result contains references to memory locations.  So for instance: 

>>> stripAddresses("{0.0} <music21.clef.TrebleClef object at 0x02A87AD0>")
'{0.0} <music21.clef.TrebleClef object at ADDRESS>' 
while this is left alone: 
>>> stripAddresses("{0.0} <music21.humdrum.MiscTandam *>I humdrum control>")
'{0.0} <music21.humdrum.MiscTandam *>I humdrum control>' 

Function toRoman()
------------------


Function unwrapWeakref()
------------------------

utility function that gets an object that might be an object itself or a weak reference to an object. 

>>> class A(object):
...    pass 
>>> a1 = A()
>>> a2 = A()
>>> a2.strong = a1
>>> a2.weak = wrapWeakref(a1)
>>> unwrapWeakref(a2.strong) is a1
True 
>>> unwrapWeakref(a2.weak) is a1
True 
>>> unwrapWeakref(a2.strong) is unwrapWeakref(a2.weak)
True 

Function wrapWeakref()
----------------------

utility function that wraps objects as weakrefs but does not wrap already wrapped objects 

Class Scalar
------------

for those of us who miss perl scalars.... 

Attributes
~~~~~~~~~~

+ valType
+ value

Methods
~~~~~~~

**toFloat()**


**toInt()**


**toUnicode()**



Class Timer
-----------

An object for timing. 

Methods
~~~~~~~

**clear()**


**start()**

    Explicit start method; will clear previous values. Start always happens on initialization. 

**stop()**



Class defHash
-------------

A replacement for dictionaries that behave a bit more like perl hashes.  No more KeyErrors. The difference between defHash and defaultdict is that the Dict values come first and that default can be set to None (which it is...) or any object. If you want a factory that makes hashes with a particular different default, use: falsehash = lambda h = None: defHash(h, default = False) a = falsehash({"A": falsehash(), "B": falsehash()}) print a["A"]["hi"] # returns False there's probably a way to use this to create a data structure of arbitrary dimensionality, though it escapes this author. if callDefault is True then the default is called: defHash(default = list, callDefault = True) will create a new List for each element 

Attributes
~~~~~~~~~~

+ callDefault
+ default

Methods
~~~~~~~

**clear()**

    D.clear() -> None.  Remove all items from D. 

**copy()**

    D.copy() -> a shallow copy of D 

**fromkeys()**

    dict.fromkeys(S[,v]) -> New dict with keys from S and values equal to v. v defaults to None. 

**get()**


**has_key()**

    D.has_key(k) -> True if D has a key k, else False 

**items()**

    D.items() -> list of D's (key, value) pairs, as 2-tuples 

**iteritems()**

    D.iteritems() -> an iterator over the (key, value) items of D 

**iterkeys()**

    D.iterkeys() -> an iterator over the keys of D 

**itervalues()**

    D.itervalues() -> an iterator over the values of D 

**keys()**

    D.keys() -> list of D's keys 

**pop()**

    D.pop(k[,d]) -> v, remove specified key and return the corresponding value If key is not found, d is returned if given, otherwise KeyError is raised 

**popitem()**

    D.popitem() -> (k, v), remove and return some (key, value) pair as a 2-tuple; but raise KeyError if D is empty 

**setdefault()**

    D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D 

**update()**

    D.update(E, **F) -> None.  Update D from E and F: for k in E: D[k] = E[k] (if E has keys else: for (k, v) in E: D[k] = v) then: for k in F: D[k] = F[k] 

**values()**

    D.values() -> list of D's values 


Class defList
-------------

A replacement for lists that behave a bit more like perl arrays. No more ListErrors. 

Attributes
~~~~~~~~~~

+ callDefault
+ default

Methods
~~~~~~~

**append()**

    L.append(object) -- append object to end 

**count()**

    L.count(value) -> integer -- return number of occurrences of value 

**extend()**

    L.extend(iterable) -- extend list by appending elements from the iterable 

**index()**

    L.index(value, [start, [stop]]) -> integer -- return first index of value 

**insert()**

    L.insert(index, object) -- insert object before index 

**pop()**

    L.pop([index]) -> item -- remove and return item at index (default last) 

**remove()**

    L.remove(value) -- remove first occurrence of value 

**reverse()**

    L.reverse() -- reverse *IN PLACE* 

**sort()**

    L.sort(cmp=None, key=None, reverse=False) -- stable sort *IN PLACE*; cmp(x, y) -> -1, 0, 1 


