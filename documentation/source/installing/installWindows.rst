.. _installWindows:


Installing `music21` in Windows
============================================


Get Python
-------------------------------

Python is a simple but powerful programming language that `music21`
is written in and in which you will write your own programs that
use `music21`.

Windows users should download and install Python version
3.8 or higher.

To get Python for Windows, go to https://www.python.org/downloads/
and click on the "Windows installer" link.  It is probably the
first link.  Save the file to your desktop
and then click on it there.

To test to see if Python has been installed properly, go
to the start menu and run (either by clicking "Run" in older
Windows or by typing in the search box) a program called `IDLE`.
Once it's started, type `2+2`.  If your system then
displays `4` python is working properly and we can start thinking
about installing `music21`.


Updating Python
-------------------------------
If you have already installed Python on your computer,
launch IDLE (a Python interpreter and code editor) by clicking
the start menu and clicking Run (on Windows XP or older) and
typing in "IDLE" or (on Windows Vista and newer) typing
in "IDLE" in the Search Programs list.

The first lines of text displayed will include a version number.
Make sure it begins with 3.7 or higher.

If your version is too old, download a newer version as above.


Install `music21`
-------------------------------

Open up a command prompt and type:

    pip install music21

This will download and install `music21`.  If you already
have `music21` but want to upgrade to the latest version, run:

    pip install --upgrade music21


To test to see if `music21` has been installed properly, go
to the start menu and run (either by clicking "Run" in older
Windows or by typing in the search box) IDLE.  Type
"`import music21`".  If your system waits for a few seconds and then
displays "`>>>`" and perhaps a warning about missing packages, then
you've installed everything properly.  (If the system
cannot find `music21` then you may have more than one version of
Python on your system.  Try uninstalling all of them along with `music21`
and then restarting from scratch).

You should then configure `music21` to find your helper programs
such as MuseScore or Finale.  In IDLE
type::

    import music21
    music21.configure.run()

or in the command prompt, type::

    python3 -m music21.configure

After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>`
to begin using `music21`.


Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, start over from scratch
and try it again very carefully.  If you still have problems
contact the `music21` group and someone should be able to help:

https://groups.google.com/g/music21list
