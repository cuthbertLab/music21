.. _moduleEnvironment:

music21.environment
===================

Class Environment
-----------------

Inherits from: object

Environment stores platform-specific, user preferences 

Attributes
~~~~~~~~~~

**modNameParent**

**ref**

Methods
~~~~~~~


Locally Defined:

**write()**

    Write an XML file. This must be manually called to store preferences. fp is the file path. preferences are stored in self.ref 

**read()**

    Load from an XML file if and only if available and has been written in the past. This means that no preference file will ever be written unless manually done so. 

**printDebug()**

    Format one or more data elements into string suitable for printing straight to stderr or other outputs. The first arg can be a list of string; lists are concatenated with common.formatStr(). 

**loadDefaults()**

    Keys are derived from these defaults 

**launch()**

    Open a file with an application specified by a preference (?) Optionally, can add additional command to erase files, if necessary Erase could be called from os or command-line arguemtns after opening the file and then a short time delay. TODO: Move showImageDirectfrom lilyString.py ; add MIDI 

**keys()**


**getTempFile()**

    Return a file path to a temporary file with the specified suffix 

**getSettingsPath()**

    Return the path to the platform specific settings file. 


Class Preference
----------------

Inherits from: node.Node (of module :ref:`moduleNode`), object





Attributes
~~~~~~~~~~

**charData**

Properties
~~~~~~~~~~


Inherited from node.Node (of module :ref:`moduleNode`): **tag**

Methods
~~~~~~~


Inherited from node.Node (of module :ref:`moduleNode`): **xmlStr()**, **toxml()**, **setDefaults()**, **set()**, **merge()**, **loadAttrs()**, **getNewDoc()**, **get()**


Class Settings
--------------

Inherits from: node.NodeList (of module :ref:`moduleNode`), node.Node (of module :ref:`moduleNode`), object





Attributes
~~~~~~~~~~

**charData**

**componentList**

Properties
~~~~~~~~~~


Inherited from node.Node (of module :ref:`moduleNode`): **tag**

Methods
~~~~~~~


Inherited from node.Node (of module :ref:`moduleNode`): **xmlStr()**, **toxml()**, **setDefaults()**, **set()**, **merge()**, **loadAttrs()**, **getNewDoc()**, **get()**


Inherited from node.NodeList (of module :ref:`moduleNode`): **append()**


