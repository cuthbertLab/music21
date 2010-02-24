.. _moduleTempo:

music21.tempo
=============

Class MetronomeMark
-------------------

Inherits from: tempo.TempoMark, base.Music21Object, object



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

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Class TempoMark
---------------

Inherits from: base.Music21Object, object



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

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


