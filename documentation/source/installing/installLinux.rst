.. _installLinux:


Installing `music21` on GNU/Linux
============================================

GNU/Linux, FreeBSD, etc. generally work on `music21`.  Many people, including
all of the major developers of `music21` run it on various deployed GNU/Linux,
Unix, AWS-Unix, etc. systems throughout the world.  However, no system except
recent Mac and Windows OSes are officially supported.

By choosing to use Unix-like systems you should be an advanced user on your
OS, able to deal with the issues of libraries, linkage, external files, etc.
specific to (and different on) each Unix-like system.  The music21list should not
be used for installation/configuration problems on
your operating system. Because of the number of different Unix variants, the list
maintainers will only entertain `music21`-specific problems on Unix **post**
installation and configuration.

To reiterate: **GNU/Linux is not a system for which support
questions will be answered**


Check Your Version of Python
----------------------------------------------

`Music21` requires Python 3.8+.

To determine the Python version you have installed, open a shell 
or terminal and enter the following command-line argument (where "$" is the prompt):

    $ python3 -V
    
it should display something like:

    Python 3.10.7

if so, you're okay.  If not, upgrade your version of Python.  This is
often a problem on some AWS configuations, Google Colab, etc.
which do not ship by default with recent versions of Python.


Download `music21` 
----------------------------------------------

Download the newest version with:

    pip3 install --upgrade music21


Configure `music21`
----------------------------------------------
Configure music21 with:

    python3 -m music21.configure

It is important to put the path to your MusicXML reader during these
prompts.  Music21 cannot find where your XML reader (probably MuseScore)
is installed on most Unix/Linux systems.  If you do not know about
filepaths and how to find them, you should probably not be using
GNU/Linux, FreeBSD, etc. with `music21`.


After Installation
-------------------------------

After a successful installation, you may proceed to
:ref:`Notes <usersGuide_02_notes>` to
begin using `music21`.


Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, 
start over from scratch and try it again very carefully.  
If you still have problems **contact an expert in your operating system**.

The `music21` maintainers cannot help with Unix installation problems except
as paid support.  See Consulting in the FAQ for details on paid support.
