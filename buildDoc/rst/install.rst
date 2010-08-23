.. _install:



Installing Music21
======================================

Music21 can be installed with a number of different methods. We give two 
different options depending on if you are a PC (Windows) or Mac (OS X) / Linux / Unix user. 


Windows Install instructions
-------------------------------

1A. Get Python
~~~~~~~~~~~~~~~~~~~~~~

Python is a simple but powerful programming language that music21
is written in and in which you will write your own programs that 
use music21.  

Whereas many operating systems come with Python, Windows does not. 
Windows users will need to download and install Python version 2.6
(or 2.7, 2.8, etc. but NOT 3.0 or above).

Go to http://www.python.org/download/ and click on the "Windows installer"
link.  It is probably the first link.  Save the file to your desktop
and then click on it there.

To test to see if Python has been installed properly, go
to the start menu and run (either by clicking "Run" in older
Windows or by typing in the search box) IDLE.  Type 
`2+2`.  If your system then
displays `4` you've installed everything properly so far.


1B. Updating Python
~~~~~~~~~~~~~~~~~~~~~~~~~
If you have already installed Python on your computer, launch IDLE (a Python interpreter and code editor) by clicking the start menu and clicking Run (on Windows XP or older) and typing in "IDLE" or (on Windows Vista and newer) typing in "IDLE" in the Search Programs list.

The first lines of text displayed will include a version number.  
Make sure it begins with 2.6.0 or higher, but not 3.0 or 3.1, etc.

If your version is too old, download a newer version as above.


2. Download music21
~~~~~~~~~~~~~~~~~~~~~~~~~~

Download the most-recent music21 package from the following URL:

  http://code.google.com/p/music21/downloads/list

Windows users should download the .exe file to their desktops
and then click on it.


3.  Install music21
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Windows installation is easy. After downloading the music21.exe 
installer, click on it on your desktop, then follow and accept 
the prompts for default install options. This installer simply 
copies files into the Python site-packages directory. If the 
installer quits without further notice the installation has 
been successful. 

To test to see if music21 has been installed properly, go
to the start menu and run (either by clicking "Run" in older
Windows or by typing in the search box) IDLE.  Type 
"`import music21`".  If your system waits for a few seconds and then
displays "`>>>`" you've installed everything properly.  (If the system
cannot find `music21` then you may have more than one version of 
Python on your system.  Try uninstalling all of them along with `music21`
and then restarting from scratch).

After a successful installation, proceed to :ref:`quickStart` to 
begin using music21, or skip ahead to Installing Additional Python 
Components below.



Mac OS X / Linux / Unix Install instructions
----------------------------------------------

1. Check your version of Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python is a simple but powerful programming language that music21
is written in and in which you will write your own programs that 
use music21.  

Mac OS X comes with Python, but it might not be a new enough version 
to run music21.  Music21 requires Python 2.6 to run (though many functions 
can run on 2.5 or 2.4). Python 3 is not yet supported. 

To determine the Python version you have installed, open a shell 
or terminal by going to Applications, then Utilities, and then double clicking "Terminal" (if you have xterm installed, that will work
fine too) and enter the following command-line argument (don't type the
"$")

    $ python -V

it should display something like:

    Python 2.6.2

if so, you're okay.  If not, go to http://www.python.org/download
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems. 


2. Download music21 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download the most-recent music21 package from the following URL. 

    http://code.google.com/p/music21/downloads/list

Linux / Mac OS X users should download the .tar.gz file. 




3.  Install Music21
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After downloading the music21 toolkit, the package is installed like any other Python extension library. Python stores extension libraries in a directory called 'site-packages'. The site-packages directory is located in different places depending on your platform. To find where your site-packages directory is located, you can enter the following command in the Python interpreter:

    >>> import distutils.sysconfig
    >>> print(distutils.sysconfig.get_python_lib())

First, uncompress the .tar.gz file. 

Open a shell or terminal (e.g. Applications -> Utilities -> Terminal), 
enter the outer-most music21 directory (using `cd`), and use 
`python` to execute the setup.py file with the 'install' argument: ::

    $ cd /path/to/dir/music21-version
    $ python setup.py install

On Mac OS X, and possibly on other systems, you may need special 
permission to write in the Python site-packages directory. An 
easy way to temporarily gain this permission is to use the 
`sudo` command. If the above returns a permissions error, 
try the following: ::

    $ sudo python setup.py install

If you cannot gain permission to install music21 in the Python 
site-packages directory, you can still run and use music21. 
Place the music21 folder anywhere convenient and note the file path. 
Start Python, and add this file path to Python's list of directories 
searched for modules:

    >>> import sys
    >>> sys.path.append('/Users/ariza/Desktop/music21')
    >>>

This can be done permanently by adding the music21 directory to the 
Python PYTHONPATH environment variable. This is not necessary if 
music21 is installed in the Python site-packages directory. See 
the following link for more details:

http://docs.python.org/using/cmdline.html#envvar-PYTHONPATH

After successful installation, proceed to :ref:`quickStart` to begin 
using music21.





Installing Additional Python Components
----------------------------------------

Additional functionality of `music21`, such as plotting graphs, is available with the installation of additional Python libraries. 
The following topics cover additional software used by music21.
For each library, visit the websites listed below, download the
additional python libraries, and install them just as you did with
music21 above.  If you don't feel like installing them now, no worries:
you can always install them later.


Python Imaging Library (PIL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python Imaging Library provides resources for transforming 
and editing graphics files.  Without this library, the output from
Lilypond is less good.

http://www.pythonware.com/products/pil


Matplotlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphing and visual displays in Music21 are provided by Matplotlib. 
Matplotlib itself has additional dependencies (such as SciPy). 
Please read the detailed instructions in the link below.

http://matplotlib.sourceforge.net






Installing Additional Software Components
-------------------------------------------

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


Eclipse + PyDev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Eclipse is a free, open-source integrated development environment (IDE),
essentially a program that makes writing (and finding bugs in) other 
programs much easier.  Eclipse is set up primarily for editing in Java,
but the add-in PyDev makes it extremely powerful for creating Python scripts
as well.  First download Eclipse at:

http://www.eclipse.org/

Then follow the "Quick Install" instructions in the right-hand column of:

http://pydev.org/download.html




Installation Help
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have followed these instructions and encounter problems, contact the music21 group for help:

http://groups.google.com/group/music21list










Advanced Topics
---------------------------------

For developers and advanced users, anonymous SVN access is available from 
Google Code. Enter the following command line argument or SVN commands::

    svn checkout http://music21.googlecode.com/svn/trunk/ music21-read-only



Downloading and Installing Music21 with setuptools or pip
-----------------------------------------------------------

The easiest way to download and install music21 is with one of the powerful automated Python package installers available. This tools can also be used to update an existing music21 installation to the most-recent version.


Automated Installation with setuptools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install setuptools:

http://pypi.python.org/pypi/setuptools

Second, install and/or update music21 with the following command-line argument: ::

    $ sudo easy_install music21


Automated Installation with pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install pip:

http://pypi.python.org/pypi/pip

Second, install and/or update music21 with the following command-line argument: ::

    $ pip install music21







