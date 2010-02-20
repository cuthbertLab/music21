.. _install:



Installing Music21
======================================

Music21 can be installed with a number of different methods. Based on your platform, choose the installation method you are most comfortable with using.







Check Your Python
-----------------------

Music21 requires Python 2.6 to run. Python 3.x is not yet supported. Check that you have Python on your system, and that that Python is up to date. 


Downloading Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 2.6 is available for all platforms and can be downloaded from the following URL:
http://www.python.org/download


Windows: Finding Python Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBW

Linux/Mac OS X: Finding Python Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open a shell or terminal (e.g. xterm, Terminal.app) and enter the following comand-line argument ::

    $ python -V
    Python 2.6.2







Downloading a Music21 Package
------------------------------

Download the most-recent music21 paackage from the following URL. Windows users should download the .exe file; Linux / Mac OS X users should download the .tar.gz file. 

http://code.google.com/p/music21/downloads/list

For developers and advanced users, anonymous SVN access is available from Google Code. Enter the following command line argument or SVN commnds::

    svn checkout http://music21.googlecode.com/svn/trunk/ music21-read-only





Installing Music21
------------------------------

After downloading the music21 toolkit, the package is installed like any other Python extension library. Python stores extension libraries in a directory called 'site-packages'. The site-packages directory is located in different places depending on your platform.



Windows Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBW


Linux/Mac OS X Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open a shell or terminal (e.g. xterm, Terminal.app), enter the outer-most music21 directory (using cd), and use python to execute the setup.py file with the 'install' argument: ::

    $ cd /path/to/dir/music21-version
    $ python setup.py install

On Mac OS X, and possible on other systems, you may need special permission to write in the Python site-packages directory. An easy way to tepmorarily gain this permission is to use the sudi command. If the above returns a permissions error, try the following: ::

    $ sudo python setup.py install







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













Installing Additional Python Components
----------------------------------------

Additional functionality of Music21 is available with the installation of Python libraries. The following topics cover additional software used by Music21.


Python Imaging Library (PIL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python Imaging Library provides resources for transforming and editing graphics files. 

http://www.pythonware.com/products/pil/


Matplotlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphing and visual displays in Music21 are provided by Matplotlib. Matplotlib itself has additional dependencies. Please read the detailed instructions below.

http://matplotlib.sourceforge.net/






Installing Additional Software Components
-------------------------------------------

Additional functionality of Music21 is available with the installation of numerous helper applications. While not essential for all applications, these tools will aid in working with Music21.


Lilypond
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Music21 can generate notation as lilypond files. Lilypond is required to render these files into graphical notation output.

http://lilypond.org/



Finale Reader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Finale reader provides a free MusicXML reader for Windows and MacOS computers.

http://www.finalemusic.com/Reader/
