.. _documenting:


Documenting music21
=============================================

Music21's documentation system uses a combination of handwritten documentation pages (like this one),
IPython notebooks, 
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

music21 documentation for modules is found inside the module itself, at the very top and before the import statements.
This module-level documentation, usually in triple-quoted strings, might look like this::

  '''
  I am documentation for this module!
  '''

The buildDoc/build.py script creates RST files for modules, which are processed 
by Sphinx.   Place all documentation for public modules, module-level 
functions, classes, and class-level attributes, properties, and methods 
as close to the relevant code as possible.  

If you're going to edit docs you'll need the latest version of Sphinx.  Go to the command line and Type::

  sudo pip install sphinx
 
Sphinx uses special characters to identify formatting of documentation. For example, to write a heading you can write:
Helpful tips on Sphinx formatting may be found here:  `Sphinx Documentation Formatting <http://sphinx.pocoo.org/rest.html>`_ 

The code would look like this::

	**This is bold**

The documentation looks like this:
**This is bold**

The code would look like this::

	*This is italics*

The documentation looks like this:
*This is italics*

This is a one-line code sample::
	
	``print variableName``
	
The documentation looks like this:	
``print variableName``

You may also use links in your documentation. For example, if in one method you'd like to link to
another method's documentation, write::

	:meth:`~music21.note.GeneralNote.addLyric`

The documentation looks like this:
:meth:`~music21.note.GeneralNote.addLyric`

Or you would like to link to another class, write::

	:class:`~music21.note.Note`
	
The documentation looks like this:
:class:`~music21.note.Note`

Sometimes pictures are useful to visually describe code to readers or to show the results of a .show() method call, etc.
This is easy with sphinx. Just copy and paste the picture you'd like to use into the buildDoc/rst/images folder, 
and reference it in your documentation like this::

    .. image:: images/completebach.*
        :width: 300

The documentation looks like this:

.. image:: images/completebach.*
    :width: 300
    
Finally, if there is a section of your documentation that you'd rather sphinx
not format at all, append two colons to the last line of formatted text,
followed by a space, followed by the *indented* text block, followed by a
space. Text written after this space will be formatted. For example, in your
code write:

::
	
    ...blah blah blah this text is formatted. now I'm ready for not-formatted
    text, so I put two colons::
	
        this text is NOT formatted it must be indented
		
        line breaks and spacing is preserved **bold** sphinx formatting is not
        observed
		
    Now I'm back to sphinx formatting...**now this is bold!*

The documentation looks like this:

...blah blah blah this text is formatted. now I'm ready for not-formatted text,
so I put two colons:
	
	this text is NOT formatted
	it must be indented
	
	line breaks and spacing is preserved
	**bold** sphinx formatting is not observed
		
Now I'm back to sphinx formatting. **now this is bold!**


Displaying only some of the test code in the documentation
----------------------------------------------------------

We use doctests a lot in music21 -- if you run /music21/test/test.py, it will
run not only all the code in class Test() but also all the code in the
documentation preceeded by '>>>' marks.  This way our documentation and our
test code doesn't get out of sync with each other.  Pretty cool, eh?

Here's the thing: good programming means that you test as much as possible in
the code, but good documentation means showing enough example code that the
readers get it, but not so much that they want to claw out their own eyeballs.
So how to proceed?  simply add the line "OMIT_FROM_Docs"  in ALL CAPS
instead of lowercase. (I can't write it in all caps here or nothing else will display!)

Anything after that line in your documentation code won't display.  For instance, 
say we wanted to demonstrate the difference between note.name and note.step, but also wanted
to test to make sure that flats and sharps both were equally eliminated.  We
could write documentation/test-code like this (but with all caps)

::
 
   '''
   >>> from music21 import *
   >>> c1 = note.Note('C#')
   >>> c1.step
   'C'
   
   OMIT_FROM_Docs
   
   >>> c2 = note.Note('C-')
   >>> c2.step
   'C'
   '''
   
and what you'll get in your documentation is:

:: 

   >>> from music21 import * 
   >>> c1 = note.Note('C#')
   >>> c1.step
   'C'
 
Lines can be omitted on an individual basis by adding the expression 
"#_DOCS_Hide" (again in all caps) somewhere on the line.  On the other hand, the text 
"#_DOCS_Show" (again in all caps) is removed from any line before it appears in the 
documentation.  So you could use some of the same lines to test 
code and also to give an example like so::

   >>> d1 = note.Note("D-")
   >>> assert(d1.name == 'D-')  #_DOCS_Hide
   >>> #_DOCS_Show d1.show('lily.png')
   
in this case, the assertion code is omitted from the documentation 
generated from the module, while the lilypond file is not generated
during doctests.  It will look to your users like:

:: 

   >>> d1 = note.Note("D-")
   >>> d1.show('lily.png')


Together with OMIT_FROM_Docs, it's a great way to
have your cake and eat it too. (remember that these need to be in all caps)

Ordering Module-Level Class Names and Module-Level Functions
-----------------------------------------------------------------------------

Classes are by default presented in the order in which they appear in the module. Module-level functions
are by default sorted alphabetically. If that's not what you want, then create a list called `_DOC_ORDER` 
which is a list of the class and/or function names in the module. These values are given as evaluated names, not strings. 

Since this list uses classes and not strings, this list must come at the end of the module, after the Test classes 
and before calling `music21.mainTest()`

At the end of note.py for instance, we write::

    _DOC_ORDER = [Note, Rest]
    
    if __name__ == "__main__":
        music21.mainTest(Test)


Ordering Class-Level Names
------------------------------------------------------

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

Documenting Class-Level Properties
---------------------------------------------------

To document a property do something like this:

::

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
--------------------------------------------------------------

Class-level attributes, names that are neither properties not methods, 
can place their documentation in a dictionary called `_DOC_ATTR`.  The keys of the dictionary 
are strings (not evaluated names) corresponding to the name of the attribute, and the value
is the documentation.

Like `_DOC_ORDER`, don't put this in `__init__()`.

Here's an example from note.py::

    class Note(NotRest):
        '''
        Class doc string goes here.
        '''
        isNote = True
        isRest = False
        
        # define order to present names in documentation; use strings
        _DOC_ORDER = ['duration', 'quarterLength', 'nameWithOctave', 'pitchClass']
        
        # documentation for all attributes (that are not properties or methods)
        _DOC_ATTR = {
        'isNote': 'Boolean read-only value describing if this object is a Note.',
        'isRest': 'Boolean read-only value describing if this is a Rest.',
        'beams': 'A :class:`music21.note.Beams` object.',
        'pitch': 'A :class:`music21.pitch.Pitch` object.',
        }

        def __init__(self, *arguments, **keywords):
            pass

If a `_DOC_ATTR` attribute is not defined, the most-recently inherited `_DOC_ATTR` 
attribute will be used.  To explicitly merge an inherited `_DOC_ATTR` attribute with 
a locally defined `_DOC_ATTR`, use the dictionary's `update()` method.

The following abbreviated example, showing the updating of the `_DOC_ATTR` inherited from NotRest, 
is from chord.py::

    class Chord(note.NotRest):
        '''
        Class doc strings.
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

Documenting Class-Level Methods
-----------------------------------------------------------------

This is the most common type of documentation, and it ensures both excellent 
documentation and doctests. A typical example of source code might look like this::

	class className():
		[instance variables, __init__, etc.]
		def myNewMethod(self,parameters):
		    '''
		    This is documentation for this method
		    
		    >>> myInstance = className()
		    >>> myInstance.myNewMethod(someParameters)
		    >>> myUnicorn.someInstanceVariable
		    'value'
		    '''
			[method code]

			