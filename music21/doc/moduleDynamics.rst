music21.dynamics
================

Function unitIntervalToName()
-----------------------------

Given a unit interfal value, map to a dynamic name 

Class Dynamic
-------------

Inherits from: base.Music21Object, object

Object representation of Dyanmics. 

Attributes
~~~~~~~~~~

**contexts**

**englishName**

**groups**

**locations**

**longName**

**posDefaultX**

**posDefaultY**

**posPlacement**

**posRelativeX**

**posRelativeY**

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

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

**mx**

    returns a musicxml.Direction object 

    >>> a = Dynamic('ppp')
    >>> a.posRelativeY = -10
    >>> b = a.mx
    >>> b[0][0][0].get('tag')
    'ppp' 
    >>> b.get('placement')
    'below' 

**musicxml**

    Provide a complete MusicXM: representation. 


Class Wedge
-----------

Inherits from: base.Music21Object, object

Object model of crescendeo/decrescendo wedges. 

Attributes
~~~~~~~~~~

**contexts**

**groups**

**locations**

**posPlacement**

**spread**

**type**

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

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

**mx**

    returns a musicxml.Direction object 

    >>> a = Wedge()
    >>> a.type = 'crescendo'
    >>> mxDirection = a.mx
    >>> mxWedge = mxDirection.getWedge()
    >>> mxWedge.get('type')
    'crescendo' 


