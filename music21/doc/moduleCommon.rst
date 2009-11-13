music21.common
==============



Utility functions and objects.

Class Scalar
------------

for those of us who miss perl scalars.... 

Public Attributes
~~~~~~~~~~~~~~~~~

+ valType
+ value

Public Methods
~~~~~~~~~~~~~~

**toFloat()**

    No documentation.

**toInt()**

    No documentation.

**toUnicode()**

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

    No documentation.

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testToRoman()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


Class Timer
-----------

Timing 

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _tDif
+ _tStart
+ _tStop

Public Methods
~~~~~~~~~~~~~~

**clear()**

    No documentation.

**start()**

    explicit start method; will clear previous values 

**stop()**

    No documentation.


Class defHash
-------------

a replacement for dictionaries that behave a bit more like perl hashes.  No more KeyErrors for dummies like Myke Cuthbert who cannot get used to differences between Perl and Python the difference between defHash and defaultdict is that the Dict values come first and that default can be set to None (which it is...) or any object. If you want a factory that makes hashes with a particular different default, use: falsehash = lambda h = None: defHash(h, default = False) a = falsehash({"A": falsehash(), "B": falsehash()}) print a["A"]["hi"] # returns False there's probably a way to use this to create a data structure of arbitrary dimensionality, though it escapes this author. if callDefault is True then the default is called: defHash(default = list, callDefault = True) will create a new List for each element 

Public Attributes
~~~~~~~~~~~~~~~~~

+ callDefault
+ default

Public Methods
~~~~~~~~~~~~~~

**clear()**

    D.clear() -> None.  Remove all items from D. 

**copy()**

    D.copy() -> a shallow copy of D 

**fromkeys()**

    dict.fromkeys(S[,v]) -> New dict with keys from S and values equal to v. v defaults to None. 

**get()**

    No documentation.

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

    D.pop(k[,d]) -> v, remove specified key and return the corresponding value. If key is not found, d is returned if given, otherwise KeyError is raised 

**popitem()**

    D.popitem() -> (k, v), remove and return some (key, value) pair as a 2-tuple; but raise KeyError if D is empty. 

**setdefault()**

    D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D 

**update()**

    D.update(E, **F) -> None.  Update D from dict/iterable E and F. If E has a .keys() method, does:     for k in E: D[k] = E[k] If E lacks .keys() method, does:     for (k, v) in E: D[k] = v In either case, this is followed by: for k in F: D[k] = F[k] 

**values()**

    D.values() -> list of D's values 


Class defList
-------------

a replacement for lists that behave a bit more like perl arrays.  No more ListErrors for dummies like Myke Cuthbert who cannot get used to differences between Perl and Python 

Public Attributes
~~~~~~~~~~~~~~~~~

+ callDefault
+ default

Public Methods
~~~~~~~~~~~~~~

**append()**

    L.append(object) -- append object to end 

**count()**

    L.count(value) -> integer -- return number of occurrences of value 

**extend()**

    L.extend(iterable) -- extend list by appending elements from the iterable 

**index()**

    L.index(value, [start, [stop]]) -> integer -- return first index of value. Raises ValueError if the value is not present. 

**insert()**

    L.insert(index, object) -- insert object before index 

**pop()**

    L.pop([index]) -> item -- remove and return item at index (default last). Raises IndexError if list is empty or index is out of range. 

**remove()**

    L.remove(value) -- remove first occurrence of value. Raises ValueError if the value is not present. 

**reverse()**

    L.reverse() -- reverse *IN PLACE* 

**sort()**

    L.sort(cmp=None, key=None, reverse=False) -- stable sort *IN PLACE*; cmp(x, y) -> -1, 0, 1 


