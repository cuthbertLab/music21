.. _documenting:


Documenting music21 Modules and Classes
=============================================

The music21 documentation is generated with Sphinx. RST files for modules, before being processed by Sphinx, are created by the buildDoc/build.py script. All documentation for public modules, module-level functions, classes, and class-level attributes, properties, and methods are contained in the code fill as close to the relevant names as possible. 


Prohibiting Docstrings from Display in Documentation
----------------------------------------------------

It may be desirable to hide some docstrings from display in the public documentation. All docstring lines following the constant `OMIT_FROM_DOCS` will be omitted from documentation. 



Ordering Module-Level Names
---------------------------

To specify the order in which module-level names are presented in documentation, the module must define `_DOC_ORDER`, a list of the class and/or function names in the module. These values are given as evaluated names, not strings. 

Only the first-most names need be specified; any names not included will be presented in default order

As this list defines evaluated names, this list must come at the end of the module, after Test classes and before calling `music21.mainTest()`

The following example is from the end of note.py::

    _DOC_ORDER = [Note, Rest]
    
    if __name__ == "__main__":
        music21.mainTest(Test)



Documenting Module-Level Functions
----------------------------------

Module-level functions should have a documentation string and doctest-compatible examples. 



Ordering Class-Level Names
----------------------------

To specify the order in which class-level names are presented in documentation, the class must define `_DOC_ORDER` attribute, a list of the attribute, property, and/or method names in the class. These values are given as strings, not evaluated names. The `_DOC_ORDER` attribute must be defined outside of the `__init__()` method to ensure that these values can be read from a Class object alone.

The following abbreviated example is from pitch.py::


    class Pitch(music21.Music21Object):
        '''Class doc strings.
        '''
        # define order to present names in documentation; use strings
        _DOC_ORDER = ['name', 'nameWithOctave', 'step', 'pitchClass', 'octave', 'midi']

        def __init__(self, name=None):
            pass



Documenting Class-Level Attributes
----------------------------------

Class-level attributes, names that are neither properties not methods, must define their documentation in the `_DOC_ATTR` dictionary. All values are given as strings, not evaluated names. The `_DOC_ATTR` attribute must be defined outside of the `__init__()` method to ensure that these values can be read from a Class object alone.

The following abbreviated example is from note.py::

    class Note(NotRest):
        '''Class doc strings.
        '''
        isNote = True
        isUnpitched = False
        isRest = False
        
        # define order to present names in documentation; use strings
        _DOC_ORDER = ['duration', 'quarterLength', 'nameWithOctave', 'pitchClass']
        # documentation for all attributes (not properties or methods)
        _DOC_ATTR = {
        'isNote': 'Boolean read-only value describing if this object is a Note.',
        'isUnpitched': 'Boolean read-only value describing if this is Unpitched.',
        'isRest': 'Boolean read-only value describing if this is a Rest.',
        'beams': 'A :class:`music21.note.Beams` object.',
        'pitch': 'A :class:`music21.pitch.Pitch` object.',
        }

        def __init__(self, *arguments, **keywords):
            pass


If a `_DOC_ATTR` attribute is not defined, the most-recently inherited `_DOC_ATTR` attribute will be used. To explicitly merge an inherited `_DOC_ATTR` attribute with a locally defined `_DOC_ATTR`, use the dictionaries `update()` method.

The following abbreviated example, showing the updating of the `_DOC_ATTR` inherited from NotRest, is from chord.py::

    class Chord(note.NotRest):
        '''Class doc strings.
        '''
        isChord = True
        isNote = False
        isRest = False
    
        # define order to present names in documentation; use strings
        _DOC_ORDER = ['pitches']
        # documentation for all attributes (not properties or methods)
        _DOC_ATTR = {
        'isNote': 'Boolean read-only value describing if this object is a Chord.',
        'isRest': 'Boolean read-only value describing if this is a Rest.',
        'beams': 'A :class:`music21.note.Beams` object.',
        }
        # update inherited _DOC_ATTR dictionary
        note.NotRest._DOC_ATTR.update(_DOC_ATTR)
        _DOC_ATTR = note.NotRest._DOC_ATTR

        def __init__(self, notes = [], **keywords):
            pass



Documenting Class-Level Properties
-------------------------------------

Class-level property definitions must pass a `doc` argument to the the `property()` global function. Included doctests will be presented in documentation and run as doctests.  



Documenting Class-Level Methods
-------------------------------------

Class-level methods should have a documentation string and doctest-compatible examples. 



