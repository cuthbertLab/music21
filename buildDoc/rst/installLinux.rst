.. _installLinux:


Installing Music21 on GNU/Linux
============================================


Alternative Installation Methods
----------------------------------------------

The following instructions are for general users. If you are an advanced user and have installed other Python packages before, or want to use an EGG, SVN, PIP, or setuptools, you should read :ref:`installAdvanced`.




Check Your Version of Python
----------------------------------------------

Music21 requires Python 2.6 to run. Python 3 is not yet supported. 

To determine the Python version you have installed, open a shell 
or terminal and enter the following command-line argument (where "$" is the prompt):

    $ python -V

it should display something like:

    Python 2.6.2

if so, you're okay.  If not, go to http://www.python.org/download
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems. 


Download music21 
----------------------------------------------

Download the most-recent music21 package from the following URL. 

    http://code.google.com/p/music21/downloads/list

Linux users should download the .tar.gz file. 




The Installation Destination
----------------------------------------------


After downloading the music21 toolkit, the package is installed like any other Python extension library. Python stores extension libraries in a directory called 'site-packages'. The site-packages directory is located in different places depending on your system. To find where your site-packages directory is located, you can enter the following command in the Python interpreter:

    >>> import distutils.sysconfig
    >>> print(distutils.sysconfig.get_python_lib())  # doctest: +SKIP




Installing Music21 with setup.py
----------------------------------------------


First, uncompress the .tar.gz file. 

Open a shell or terminal, enter the outer-most music21 directory, and use `python` to execute the setup.py file with the 'install' argument: ::

    $ cd /path/to/dir/music21-version
    $ python setup.py install

You may need special  permission to write in the Python site-packages directory. An  easy way to temporarily gain this permission is to use the 
`sudo` command. If the above returns a permissions error, 
try the following: ::

    $ sudo python setup.py install

If you cannot gain permission to install music21 in the Python 
site-packages directory, you can still run and use music21. 
Place the music21 folder anywhere convenient and note the file path. 
Start Python, and add this file path to Python's list of directories 
searched for modules:

    >>> import sys
    >>> sys.path.append('/Users/ariza/Desktop/music21')  # doctest: +SKIP
    >>>

This can be done permanently by adding the music21 directory to the 
Python PYTHONPATH environment variable. This is not necessary if 
music21 is installed in the Python site-packages directory. See 
the following link for more details:

http://docs.python.org/using/cmdline.html#envvar-PYTHONPATH





After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`quickStart` to 
begin using music21.

You may need to install additional software to take advantage of some features of music21. For information on additional software you may need, see :ref:`installAdditional`.

You may want to configure your Environment to support opening MusicXML files in MuseData or adjusting other settings. To do so, see :ref:`environment`.






Installation Help
-------------------------------

If you have followed all the instructions and encounter problems, contact the music21 group for help:

http://groups.google.com/group/music21list










