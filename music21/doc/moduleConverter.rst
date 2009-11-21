music21.converter
=================



Public interface for importing file formats into music21.

Function parse()
----------------

Determine if the file is a file path or a string 

Function parseData()
--------------------


Function parseFile()
--------------------


Class Converter
---------------

Not a subclass, but a wrapper for different converter objects based on format. 

Methods
~~~~~~~

**parseData()**

    need to look at data and determine if it is xml or humdrum 

**parseFile()**


**stream()**


Private Methods
~~~~~~~~~~~~~~~

**_getStream()**


**_setConverter()**



Class ConverterException
------------------------


Methods
~~~~~~~

**args()**


**message()**



Class ConverterFileException
----------------------------


Methods
~~~~~~~

**args()**


**message()**



Class ConverterHumdrum
----------------------


Attributes
~~~~~~~~~~

+ stream

Methods
~~~~~~~

**parseData()**

    Open from a string 

**parseFile()**

    Open from file path 


Class ConverterMusicXML
-----------------------


Methods
~~~~~~~

**getPartNames()**


**load()**

    Load all parts. This determines the order parts are found in the stream 

**parseData()**

    Open from a string 

**parseFile()**

    Open from file path; check to see if there is a pickled version available and up to date; if so, open that, otherwise open source. 

**stream()**


Private Methods
~~~~~~~~~~~~~~~

**_getStream()**



Class PickleFilter
------------------

Before opening a file path, this class can check if there is an up to date version pickled and stored in the scratch directory. If the user has not specified a scratch directory, a pickle path will not be created. 

Methods
~~~~~~~

**status()**


Private Methods
~~~~~~~~~~~~~~~

**_getPickleFp()**



Class PickleFilterException
---------------------------


Methods
~~~~~~~

**args()**


**message()**



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

**testConversionMusicXml()**


**testMusicXMLConversion()**


Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


