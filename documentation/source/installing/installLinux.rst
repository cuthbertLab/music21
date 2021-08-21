.. _installLinux:


Installing `music21` on GNU/Linux
============================================

GNU/Linux, FreeBSD, etc. are supported by `music21`. However, by choosing to use 
Unix-like systems you should be an advanced user -- the music21list should not
be used for general installation/configuration problems that are specific to
your operating system. Because of the number of different Unix variants, the list
maintainers can only help with `music21`-specific problems post installation or
Mac/PC problems.

To reiterate: **GNU/Linux is not a system for which support questions will be answered**


Check Your Version of Python
----------------------------------------------

`Music21` requires Python 3.7+.

To determine the Python version you have installed, open a shell 
or terminal and enter the following command-line argument (where "$" is the prompt):

    $ python3 -V
    
it should display something like:

    Python 3.9.2

if so, you're okay.  If not, go to https://www.python.org/downloads/
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems. 


Download `music21` 
----------------------------------------------

Download the newest version with:

    pip3 install --upgrade music21


After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` to 
begin using `music21`.


Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, 
start over from scratch and try it again very carefully.  
If you still have problems contact an expert in your operating system.
The `music21` staff cannot help with Unix installation problems except
as paid support.
