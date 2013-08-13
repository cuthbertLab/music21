Using ``music21`` with the iPython Notebook
===========================================


To get ``music21`` to work with iPython Notebook, first install the
anaconda distribution of python...

::

    ciconia:~ cuthbert$ cd Downloads
    ciconia:Downloads cuthbert$ bash Anaconda-1.5.1-MacOSX-x86_64.sh
    ciconia:Downloads cuthbert$ cd ~
    ciconia:~ cuthbert$ cd anaconda
    ciconia:anaconda cuthbert$ bin/conda update conda 
    ciconia:anaconda cuthbert$ bin/conda update ipython
    ciconia:anaconda cuthbert$ bin/conda pip music21

::

    Downloading/unpacking music21
      Downloading music21-1.5.0.tar.gz (29.6MB): 29.6MB downloaded
      Running setup.py egg_info for package music21
        
        warning: no files found matching '*.pdf' anywhere in distribution
        no previously-included directories found matching 'dist'
        no previously-included directories found matching 'buildDoc'
        no previously-included directories found matching 'obsolete'
    Installing collected packages: music21
      Running setup.py install for music21
        
        warning: no files found matching '*.pdf' anywhere in distribution
        no previously-included directories found matching 'dist'
        no previously-included directories found matching 'buildDoc'
        no previously-included directories found matching 'obsolete'
    Successfully installed music21
    Cleaning up...
    # files: 8219

    # success
    music21-1.5.0-py27_0.tar.bz2
    music21-1.5.0-py27_0:
        making available
        linking


Anaconda messes with your PATH, so I suggest opening your
~/.bash\_profile and putting the condo command after $PATH not before:

``# added by Anaconda 1.5.1 installer export PATH="$PATH:/Users/cuthbert/anaconda/bin"``

Now you're ready to run iPython. Make sure you're in the anaconda
directory and run:

``ciconia:anaconda cuthbert$ bin/ipython notebook --pylab inline``

Using the web-based IP Notebook
-------------------------------


Now in the webbrowser you can type commands such as the ones below:

.. code:: python

    from music21 import *

.. code:: python

    c = chord.Chord("C4 E4 G4")
    c.isConsonant()


.. parsed-literal::
   :class: ipython-result

    True


All other normal ``music21`` commands will work as they should

Displaying graphics inline
--------------------------


By default, you cannot just call .show() because you'll open up your
MusicXML reader locally...

.. code:: python

    c.show()


.. parsed-literal::
   :class: ipython-result

    <music21.ipython21.objects.IPythonPNGObject at 0x10906ae10>


Nor does just generating a lilypond PNG work as you'd like -- this will
display it on the screen but not in your browser:

.. code:: python

    c.show('lily.png')


.. parsed-literal::
   :class: ipython-result

    u'/var/folders/x5/rymq2tx16lqbpytwb1n_cc4c0000gn/T/music21/tmpI7k6xFly.png'


Instead do this:

.. code:: python

    %load_ext music21.ipython21.ipExtension

Now this will work:

.. code:: python

    c.show()


.. image:: installIPython_files/_fig_04.png


If you don't want to do that, then instead do this...

.. code:: python

    from IPython.core.display import Image

.. code:: python

    Image(filename=c.write('lily.png'))


.. image:: installIPython_files/_fig_06.png


SVG is much faster, but it doesn't work, sadly...

.. code:: python

    Image(filename=c.write('lily.svg'))

::

    ---------------------------------------------------------------------------
    ValueError                                Traceback (most recent call last)
    <ipython-input-9-a78ad09b705c> in <module>()
    ----> 1 Image(filename=c.write('lily.svg'))
    
    /Library/Python/2.7/site-packages/ipython-0.14.dev-py2.7.egg/IPython/core/display.pyc in __init__(self, data, url, filename, format, embed, width, height)
        492 
        493         if self.embed and self.format not in self._ACCEPTABLE_EMBEDDINGS:
    --> 494             raise ValueError("Cannot embed the '%s' image format" % (self.format))
        495         self.width = width
        496         self.height = height

    ValueError: Cannot embed the 'svg' image format

Whole pieces will show properly also now that the extension module is
loaded

.. code:: python

    b = corpus.parse('bach/bwv66.6')

.. code:: python

    b.show()


.. image:: installIPython_files/_fig_08.png


Images from other docs etc. can be loaded into the notebook just like
any other iPython notebook

.. code:: python

    import os
    m21RstDir = common.getBuildDocRstFilePath()
    m21imageFile = os.path.join(m21RstDir, 'images', 'usersGuide', 'overviewNotes-05.png')
    Image(filename=m21imageFile)


.. image:: installIPython_files/_fig_10.png


Turn off pesky prompts. Run this and then hide it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. code:: python

    from IPython.core.display import publish_html

To turn back on change display to 'block'; note that it must be the last
thing on the page!

.. code:: python

    publish_html('<style>.prompt {display: None;}</style>')
