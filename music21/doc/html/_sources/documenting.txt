.. _documenting:


Documenting music21
=============================================

Music21's documentation system uses a combination of handwritten documentation pages (like this one),
and documentation automatically generated from the documentation found in modules.  

For handwritten pages, the files can be found in the top-level /buildDoc/rst/ directories, outside
the music21 directory.  The files are written using the reStructuredText_ format (file extension: .rst),
which is a pretty simple way of defining structure of documents with things such as hyperlinks, emphasis,
etc.  We then use the excellent module Sphinx_ along with our custom-made build.py to translate the code 
to .html (what you're reading here) and store that code in /music21/doc/html -- letting you read it 
offline.  (And of course we put a copy of that code online.)

.. _reStructuredText: http://docutils.sourceforge.net/rst.html 
.. _Sphinx: http://sphinx.pocoo.org/

But most of the music21 documentation is automatically generated from the documentation strings
found in music21 modules.  We strongly encourage other module writers to create documentation that works
the same way.  In fact, we won't add your module to the music21 repository without documentation
in this form -- we're sort of bastards in how we look out for the users who will come after you -- but
we'll help you learn the ropes.  This doc explains some of the main features (and potential Gotchas!) 
of our automatic documentation system.


Documenting modules and classes
---------------------------------------------------

music21 documentation for modules is found inside the module itself, usually in triple-quoted strings, like this::

  '''
  I am documentation for this module!
  '''

The buildDoc/build.py script creates RST files for modules, which are processed 
by Sphinx.   Place all documentation for public modules, module-level 
functions, classes, and class-level attributes, properties, and methods 
as close to the relevant code as possible.  

If you're going to edit docs you'll need the latest version of Sphinx.  Go to the command line and Type::

  easy_install -U Sphinx
  easy_install rst2pdf
  

Displaying only some of the test code in the documentation
----------------------------------------------------------

We use doctests a lot in music21 -- if you run /music21/test/test.py, it will run
not only all the code in class Test() but also all the code in the documentation
preceeded by '>>>' marks.  This way our documentation and our test code doesn't
get out of sync with each other.  Pretty cool, eh?

Here's the thing: good programming means that you test as much as possible in the
code, but good documentation means showing enough example code that the readers
get it, but not so much that they want to claw out their own eyeballs.  So how to proceed?
simply add the line ::

   OMIT_FROM_DOCS
   
in your documentation code and it won't display.  For instance, say we wanted to
demonstrate the difference between note.name and note.step, but also wanted to 
test to make sure that flats and sharps both were equally eliminated.  We could
write documentation/test-code like this::
 
   '''
   >>> c1 = music21.Note('C#')
   >>> c1.step
   'C'
   
   OMIT_FROM_DOCS
   >>> c2 = music21.Note('C-')
   >>> c2.step
   'C'
   '''
   
and what you'll get in your documentation is:
 
   >>> c1 = music21.Note('C#')
   >>> c1.step
   'C'
 


Ordering Module-Level Names
-------------------------------------------------

Classes, module-level function, etc. are by default presented in the order in which they appear in the module.
If that's not what you want, then create a list called `_DOC_ORDER` which is a list of the class and/or 
function names in the module. These values are given as evaluated names, not strings. 

Since this list uses classes and not strings, this list must come at the end of the module, after the Test classes 
and before calling `music21.mainTest()`

At the end of note.py for instance, we write::

    _DOC_ORDER = [Note, Rest]
    
    if __name__ == "__main__":
        music21.mainTest(Test)


Documenting Module-Level Functions
-------------------------------------------------

Module-level functions should have a documentation string and doctest-compatible examples. 
(DEMO NEEDED)


Ordering Class-Level Names
----------------------------

Classes can define a `_DOC_ORDER` attribute which functions the same as the module-level
`_DOC_ORDER`, that is it defines the order of attributes, properties, and/or methods in the class. 

Unlike for top-level names, these values are given as **strings**, not evaluated names. 
The `_DOC_ORDER` attribute must be defined outside of the `__init__()` method to ensure that 
these values can be read from a Class object and not just instances.

The following abbreviated example is from pitch.py::

    class Pitch(music21.Music21Object):
        '''Class doc strings.
        '''
        # define order to present names in documentation; use strings
        _DOC_ORDER = ['name', 'nameWithOctave', 'step', 'pitchClass', 'octave', 'midi']

        def __init__(self, name=None):
            pass

Documenting Properties
----------------------

To document a property do something like this::

  def _getName(self):
     return self._storedName
  
  def _setName(self, newName):
     if newName == 'Cuthbert':
        raise Exception("what a dumb name!")
     else:
        self._storedName = newName
  
  name = property(_getName, _setName, doc = '''
      The name property stores a name for the object
      unless the name is something truly idiotic.
      '''

Documenting Class-Level Attributes
----------------------------------

Class-level attributes, names that are neither properties not methods, 
can place their documentation in a dictionary called `_DOC_ATTR`.  The keys of the dictionary 
are strings (not evaluated names) corresponding to the name of the attribute, and the value
is the documentation.

Like `_DOC_ORDER`, don't put this in `__init__()`.

Here's an example from note.py::

    class Note(NotRest):
        '''Class doc string. goes here.
        '''
        isNote = True
        isUnpitched = False
        isRest = False
        
        # define order to present names in documentation; use strings
        _DOC_ORDER = ['duration', 'quarterLength', 'nameWithOctave', 'pitchClass']
        
        # documentation for all attributes (that are not properties or methods)
        _DOC_ATTR = {
        'isNote': 'Boolean read-only value describing if this object is a Note.',
        'isUnpitched': 'Boolean read-only value describing if this is Unpitched.',
        'isRest': 'Boolean read-only value describing if this is a Rest.',
        'beams': 'A :class:`music21.note.Beams` object.',
        'pitch': 'A :class:`music21.pitch.Pitch` object.',
        }

        def __init__(self, *arguments, **keywords):
            pass

If a `_DOC_ATTR` attribute is not defined, the most-recently inherited `_DOC_ATTR` attribute will be used. 
To explicitly merge an inherited `_DOC_ATTR` attribute with a locally defined `_DOC_ATTR`, use the 
dictionary's `update()` method.

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



