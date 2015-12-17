.. _installLinux:


Installing Music21 on GNU/Linux
============================================

GNU/Linux, FreeBSD, etc. are supported by music21. However, by choosing to use 
Unix-like systems you should be an advanced user -- the music21list should not
be used for general installation/configuration problems that are specific to
your operating system. Because of the number of different Unix variants, the list
maintainers can only help with music21-specific problems post installation or
Mac/PC problems.


Check Your Version of Python
----------------------------------------------

Music21 requires Python 2.7.3+ or Python 3.3+.

To determine the Python version you have installed, open a shell 
or terminal and enter the following command-line argument (where "$" is the prompt):

    $ python -V
    
or in many 3.X installation cases:

    $ python3 -V

it should display something like:

    Python 3.4.1

if so, you're okay.  If not, go to http://www.python.org/download
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems. 


Download music21 
----------------------------------------------

Download the most-recent music21 package from the following URL. 

    https://github.com/cuthbertLab/music21/releases

Linux users should download the .tar.gz file. 




Installing Music21 with setup.py
----------------------------------------------


First, uncompress the .tar.gz file. 

Open a shell or terminal, enter the outer-most music21 directory, and use `python` 
to execute the setup.py file with the 'install' argument: ::

    $ cd /path/to/dir/music21-version
    $ python setup.py install

You may need special  permission to write in the Python site-packages directory. 
An easy way to temporarily gain this permission is to use the 
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

This can be done permanently by adding the music21 directory to the 
Python PYTHONPATH environment variable. This is not necessary if 
music21 is installed in the Python site-packages directory. See 
the following link for more details:

http://docs.python.org/using/cmdline.html#envvar-PYTHONPATH


After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` to 
begin using `music21`.



Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, 
start over from scratch
and try it again very carefully.  If you still have problems contact an
expert in your operating system.
