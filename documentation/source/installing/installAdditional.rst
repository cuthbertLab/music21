.. _installAdditional:


Extending `music21` with Additional Software
=======================================================


Installing Additional Python Modules
-----------------------------------------------

`Music21` can do more things, such as plotting graphs, if you
install additional Python libraries. 

The following topics cover additional software used by `music21`.
For each library, visit the websites listed below, download the
additional python libraries, and install them just as you did with
`music21` above.  If you don't feel like installing them now, no worries:
you can always install them later.

It's best not to install these until you have `music21` working without
the external modules.


Matplotlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphing and visual displays in Music21 are provided by Matplotlib. 
Matplotlib itself has additional dependencies (such as NumPy). 

On Mac if you are using the version of python 3 from python.org, run:

`pip3 install matplotlib`

and you should be set.  If you are using a version from anaconda
(conda, miniconda, etc.), you should run these lines:

`conda install matplotlib`
`conda install python.app`

and then use `pythonw` instead of `python`.  For more details, see
http://matplotlib.org/2.0.0b4/faq/osx_framework.html


Users of 64-bit windows or Python 2.7 will need to download
numpy and scipy from:

http://www.lfd.uci.edu/~gohlke/pythonlibs/


numpy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Numeric extensions to Python.  Included with Matplotlib.

On Mac if you are using the version of python 3 from python.org, run:

`pip3 install numpy`

and you should be set.  If using python 2, substitute `pip` for `pip3`




scipy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Scientific extensions to Python.

On Mac if you are using the version of python 3 from python.org, run:

`pip3 install scipy`

and you should be set.  If using python 2, substitute `pip` for `pip3`




pyaudio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for recording within python.  We use it for the audioSearch module, and nowhere else.
Not essential. Requires `portaudio` and, on the Mac, the XCode command-line development tools.

On the Mac, run:

`xcode-select --install`
`brew install portaudio`
`pip3 install pyaudio`


pygame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for realtime MIDI performance.  We use it in the midi.realtime module, and nowhere else
Not essential.

On the Mac, run:

`pip3 install pygame`


Python Imaging Library (`pillow` or PIL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python Imaging Library (pillow; formerly PIL) 
provides resources for transforming 
and editing graphics files.  Without this library, the output from
Lilypond is less good. Not essential.

On the command line type `pip3 install pillow` and you should get the latest version
of pillow.




Installing Additional Software Components
-----------------------------------------------

Additional functionality of `music21` is available with the 
installation of numerous helper applications. While not essential 
for all applications, these tools will aid in working with `music21`.



MuseScore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MuseScore offers a free, full-featured, cross-platform (Windows, Mac OS, Ubuntu,
Debian, and Fedora) application for viewing and editing music notation. 
MuseScore can import and export MusicXML, and provides an excellent way to view, 
edit, and export musical data for working in `music21`. 
Downloading MuseScore (version 2 or higher) 
is highly recommended for working with `music21`. 

http://www.musescore.org



Finale or Finale NotePad
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finale is one of the industry leaders in creating musical scores.  It
can import MusicXML that `music21` generates and let you see, edit, or print
these scores for your own use.  There is also a free version of Finale,
Finale NotePad that can load MusicXML files but cannot edit all aspects of them.  
NotePad is available for Windows and Mac OS computers. Use of Finale or Finale NotePad 
is recommended for working with `music21`. 

http://www.finalemusic.com/products/finale-notepad/

On Windows, after you install Finale or Finale Notepad, you will probably want
to associate .xml files so that they are automatically opened by Finale or
Finale Reader.  To do so download http://web.mit.edu/music21/blank.xml 
to your desktop.  Right click the file in on your desktop 
and click "Open with" then choose "browse", select 
c:\\Program Files\\Finale Notepad\\Finale NotePad.exe (or c:\\Programs\\Finale\\Finale.exe 
depending on if you're on Windows Vista/7/8/10 or if you're using Finale vs. Finale
NotePad), and the check the box for always using this program for 
opening xml files.  (Thanks to Craig Sapp for this missing step)


Lilypond
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lilypond is a free, open-source music display program that can produce
beautiful scores.  `Music21` can generate PDF or PNG (like JPG) files 
automatically if Lilypond is installed on your system.  Download it at:

http://lilypond.org/


Eclipse + PyDev + Git
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Eclipse is a free, open-source integrated development environment (IDE),
essentially a program that makes writing (and finding bugs in) other 
programs much easier.  Eclipse is set up primarily for editing in Java,
but the add-in PyDev makes it extremely powerful for creating Python scripts
as well.  Eclipse + PyDev + Git is the
only supported method for developers to get help in contributing to `music21`.  

Details are at :ref:`Using Git <usingGit>`
