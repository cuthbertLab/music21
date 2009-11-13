music21.environment
===================

Class Environment
-----------------

Environment stores platform-specific, user preferences 

Public Attributes
~~~~~~~~~~~~~~~~~

+ ref

Public Methods
~~~~~~~~~~~~~~

**getSettingsPath()**

    Return the path to the platform specific settings file. 

**getTempFile()**

    Return a file path to a temporary file with the specified suffix 

**keys()**

    No documentation.

**launch()**

    Open a file with an application specified by a preference (?) Optionally, can add additional command to erase files, if necessary Erase could be called from os or command-line arguemtns after opening the file and then a short time delay. TODO: Move showImageDirectfrom lilyString.py ; add MIDI 

**loadDefaults()**

    Keys are derived from these defaults 

**read()**

    Load from an XML file if and only if available and has been written in the past. This means that no preference file will ever be written unless manually done so. 

**write()**

    Write an XML file. This must be manually called to store preferences. fp is the file path. preferences are stored in self.ref 


Class EnvironmentException
--------------------------

No documentation.

Public Methods
~~~~~~~~~~~~~~

**args()**

    No documentation.

**message()**

    No documentation.


Class Preference
----------------





Public Attributes
~~~~~~~~~~~~~~~~~

+ charData

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _attr
+ _crossReference
+ _doctypeName
+ _doctypePublic
+ _doctypeSystem
+ _tag

Public Methods
~~~~~~~~~~~~~~

**clone()**

    No documentation.

**get()**

    No documentation.

**getNewDoc()**

    No documentation.

**loadAttrs()**

    Given a SAX attrs object, load all atributes that are named within this object's _attr dictionary. 

**merge()**

    Given another similar or commonly used Node object, combine all attributes and return a new object. 

    >>> a = Node()
    >>> a.set('charData', 'green')
    >>> b = Node()
    >>> c = b.merge(a)
    >>> c.get('charData')
    'green' 

**set()**

    No documentation.

**setDefaults()**

    provide defaults for all necessary attributes at this level 

**tag()**

    No documentation.

**toxml()**

    Provides XML output as either a text string or as DOM node. This method can be called recursively to build up nodes on a DOM tree. This method will assume that if an self.charData attribute has been defined this is a text element for this node. Attributes, sub entities, and sub nodes are obtained via subclassed method calls. 

**xmlStr()**

    Shortcut method to provide quick xml out. 

Private Methods
~~~~~~~~~~~~~~~

**_convertNameCrossReference()**

    Define mappings from expected MusicXML names and specially named attributes in object. Return a list of zero or 1 name Speialize in sublcasses as needed, calling this base class to get general defaults All options need to be lower case. 

    >>> a = Node()
    >>> a._convertNameCrossReference('characterData')
    'charData' 

**_convertNameFromXml()**

    Given an xml attribute/entity name, try to convert it to a Python attribute name. If the python name is given, without and - dividers, the the proper name should be returned 

    >>> a = Node()
    >>> a._convertNameFromXml('char-data')
    'charData' 

**_convertNameToXml()**

    Given an a Python attribute name, try to convert it to a XML name. If already an XML name, leave alone. 

    >>> a = Node()
    >>> a._convertNameToXml('charData')
    'char-data' 

**_getAttributes()**

    Return a list of attribute names / value pairs 

    >>> a = Node()
    >>> a._getAttributes()
    [] 

**_getComponents()**

    Get all sub-components, in order. This may be Node subclasses, or may be simple entities. Simple entities do not have attributes and are only used as containers for character data. These entities are generally not modelled as objects 

**_getTag()**

    No documentation.

**_mergeSpecial()**

    Provide handling of merging when given an object of a different class. Objects can define special merge operations for dealing with Lower or upper level objects. Define in subclass 

**_publicAttributes()**

    Get all public names from this object. Used in merging. 

    >>> a = Node()
    >>> len(a._publicAttributes())
    2 
    >>> print a._publicAttributes()
    ['charData', 'tag'] 

    

**_setTag()**

    No documentation.


Class Settings
--------------





Public Attributes
~~~~~~~~~~~~~~~~~

+ charData
+ componentList

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _attr
+ _crossReference
+ _doctypeName
+ _doctypePublic
+ _doctypeSystem
+ _index
+ _tag

Public Methods
~~~~~~~~~~~~~~

**append()**

    No documentation.

**clone()**

    No documentation.

**get()**

    No documentation.

**getNewDoc()**

    No documentation.

**loadAttrs()**

    Given a SAX attrs object, load all atributes that are named within this object's _attr dictionary. 

**merge()**

    Given another similar or commonly used Node object, combine all attributes and return a new object. 

    >>> a = Node()
    >>> a.set('charData', 'green')
    >>> b = Node()
    >>> c = b.merge(a)
    >>> c.get('charData')
    'green' 

**next()**

    Method for treating this object as an iterator Returns each node in sort order; could be in tree order. 

**set()**

    No documentation.

**setDefaults()**

    provide defaults for all necessary attributes at this level 

**tag()**

    No documentation.

**toxml()**

    Provides XML output as either a text string or as DOM node. This method can be called recursively to build up nodes on a DOM tree. This method will assume that if an self.charData attribute has been defined this is a text element for this node. Attributes, sub entities, and sub nodes are obtained via subclassed method calls. 

**xmlStr()**

    Shortcut method to provide quick xml out. 

Private Methods
~~~~~~~~~~~~~~~

**_convertNameCrossReference()**

    Define mappings from expected MusicXML names and specially named attributes in object. Return a list of zero or 1 name Speialize in sublcasses as needed, calling this base class to get general defaults All options need to be lower case. 

    >>> a = Node()
    >>> a._convertNameCrossReference('characterData')
    'charData' 

**_convertNameFromXml()**

    Given an xml attribute/entity name, try to convert it to a Python attribute name. If the python name is given, without and - dividers, the the proper name should be returned 

    >>> a = Node()
    >>> a._convertNameFromXml('char-data')
    'charData' 

**_convertNameToXml()**

    Given an a Python attribute name, try to convert it to a XML name. If already an XML name, leave alone. 

    >>> a = Node()
    >>> a._convertNameToXml('charData')
    'char-data' 

**_getAttributes()**

    Return a list of attribute names / value pairs 

    >>> a = Node()
    >>> a._getAttributes()
    [] 

**_getComponents()**

    No documentation.

**_getTag()**

    No documentation.

**_mergeSpecial()**

    Provide handling of merging when given an object of a different class. Objects can define special merge operations for dealing with Lower or upper level objects. Define in subclass 

**_publicAttributes()**

    Get all public names from this object. Used in merging. 

    >>> a = Node()
    >>> len(a._publicAttributes())
    2 
    >>> print a._publicAttributes()
    ['charData', 'tag'] 

    

**_setTag()**

    No documentation.


Class Test
----------

Unit tests 

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

**testSettings()**

    No documentation.

**testTest()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


