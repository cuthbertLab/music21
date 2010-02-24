.. _moduleTempo:

music21.tempo
=============

Class MetronomeMark
-------------------

Inherits from: tempo.TempoMark (of module :ref:`moduleTempo`), base.Music21Object (of module :ref:`moduleBase`), object



>>> a = MetronomeMark(40)
>>> a.number
40 

Attributes
~~~~~~~~~~

**contexts**

**groups**

**id**

**locations**

**number**

**referent**

**value**

Properties
~~~~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **priority**, **parent**, **offset**, **duration**

Methods
~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **write()**, **show()**, **searchParent()**, **isClass()**, **id()**, **getOffsetBySite()**, **contexts()**, **addLocationAndParent()**


Class TempoMark
---------------

Inherits from: base.Music21Object (of module :ref:`moduleBase`), object



>>> tm = TempoMark("adagio")
>>> tm.value
'adagio' 

Attributes
~~~~~~~~~~

**contexts**

**groups**

**id**

**locations**

**value**

Properties
~~~~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **priority**, **parent**, **offset**, **duration**

Methods
~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **write()**, **show()**, **searchParent()**, **isClass()**, **id()**, **getOffsetBySite()**, **contexts()**, **addLocationAndParent()**


