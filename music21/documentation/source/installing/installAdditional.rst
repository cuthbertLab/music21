.. _installAdditional:




Extending Music21 with Additional Software
=======================================================




Installing Additional Python Resources
-----------------------------------------------


Additional functionality of `music21`, such as plotting graphs, is available with the installation of additional Python libraries. 
The following topics cover additional software used by music21.
For each library, visit the websites listed below, download the
additional python libraries, and install them just as you did with
music21 above.  If you don't feel like installing them now, no worries:
you can always install them later.

It's best not to install these until you have music21 working without
the external modules.



Python Imaging Library (PIL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python Imaging Library provides resources for transforming 
and editing graphics files.  Without this library, the output from
Lilypond is less good.

Windows 32-bit can download from:
http://www.pythonware.com/products/pil

Users of 64-bit windows will want to install from the site below.
The paradox is that if you are using 64-bit windows but 32-bit Python
(as most people will) you will probably want to download the 32-bit install
(x86) rather than the 64-bit (AMD64).

http://www.lfd.uci.edu/~gohlke/pythonlibs/


PIL (which is only used in audiosearch and to make slightly better PNGs from
Lilypond) has been a particular problem on the Mac over the past few years.
If it's really important to you
Mac Users may to download MacPorts from
http://www.macports.org/install.php .  After installing, 
open up a terminal and type:
"sudo port -v selfupdate"  then when that is done install with
"sudo port install py27-pil" (replace with py26-pil if you are
on python2.6.)  This method takes a while but at least it is safe.
However, it does install a whole nother copy of python on your
computer which might have its own problems...  Then type:
"sudo port select python python27" to use the new version of python
(if you hate it, type "sudo port select python python27-apple" to get
back)



Matplotlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphing and visual displays in Music21 are provided by Matplotlib. 
Matplotlib itself has additional dependencies (such as SciPy). 
Please read the detailed instructions in the link below.

http://matplotlib.sourceforge.net

Users of 64-bit windows or Python 2.7 will need to download
numpy and scipy from:

http://www.lfd.uci.edu/~gohlke/pythonlibs/


Mac Users can get Matplotlib, Numpy, Scipy, and a few other systems
compiled for Mac OS X 10.8 (Mountain Lion) or whatever the most recent
OS is from this site:

http://fonnesbeck.github.com/ScipySuperpack/



pyaudio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for recording within python.  We use it for the audioSearch module, and nowhere else.
Not essential.


pygame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows for realtime MIDI performance.  We use it in the midi.realtime module, and nowhere else
Not essential.



Installing Additional Software Components
-----------------------------------------------

Additional functionality of Music21 is available with the 
installation of numerous helper applications. While not essential 
for all applications, these tools will aid in working with Music21.




MuseScore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MuseScore offers a free, full-featured, cross-platform (Windows, Mac OS, Ubuntu, Debian, and Fedora) application for viewing and editing music notation. MuseScore can import and export MusicXML, and provides an excellent way to view, edit, and export musical data for working in music21. Use of MuseScore is highly recommended for working with music21. 

http://www.musescore.org





Finale or Finale Reader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finale is one of the industry leaders in creating musical scores.  It
can import MusicXML that music21 generates and let you see, edit, or print
these scores for your own use.  There is also a free version of Finale,
Finale Reader that can load MusicXML files but cannot edit them.  The reader
is available for Windows and Mac OS computers. Use of Finale or Finale reader 
is highly recommended for working with music21. 

http://www.finalemusic.com/Reader

On Windows, after you install Finale or Finale Reader, you will probably want
to associate .xml files so that they are automatically opened by Finale or
Finale Reader.  To do so download http://web.mit.edu/music21/blank.xml 
to your desktop.  Right click the file in on your desktop 
and click "Open with" then choose "browse", select 
c:\\Program Files\\Finale Reader\\Finale Reader.exe (or c:\\Programs\\Finale\\Finale.exe 
depending on if you're on Windows Vista or if you're using Finale vs. Finale
Reader), and the check the box for always using this program for 
opening xml files.  (Thanks to Craig Sapp for this missing step)



Lilypond
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lilypond is a free, open-source music display program that can produce
beautiful scores.  Music21 can generate PDF or PNG (like JPG) files 
automatically if Lilypond is installed on your system.  Download it at:

http://lilypond.org/


Eclipse + PyDev + SVN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Eclipse is a free, open-source integrated development environment (IDE),
essentially a program that makes writing (and finding bugs in) other 
programs much easier.  Eclipse is set up primarily for editing in Java,
but the add-in PyDev makes it extremely powerful for creating Python scripts
as well.  In addition, the SVN features of Eclipse let you stay updated
with the latest versions of music21.  Eclipse + PyDev + SVN is the
only supported method for developers to contribute to music21.  

Details are at :ref:`usingEclipse`

