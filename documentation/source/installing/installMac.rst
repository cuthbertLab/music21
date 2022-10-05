.. _installMac:

Installing `music21` on Mac
============================================

Because Apple changes their system details so much
from one version of OS X to another, installing `music21`
is probably the hardest part of the experience.
Once you have that set, the rest should be much less painful.
Trust us that it should work.


Downloading Python 3 from python.org
---------------------------------------

Though most Macs come with Python, it's usually a very old version.
We recommend updating that by going to https://www.python.org/downloads
and getting the latest version.

(The `music21` team strongly recommends using the version of
Python 3 from the python.org website and not the Conda version
(or Enthought Canopy) because music21 is fully compatible with
`matplotlib` on the python.org site.
If you have no plans on plotting functions,
feel free to use any flavor of Python 3.)


Simple install on macOS Sierra or OS X El Capitan
--------------------------------------------------

If you're on the newest versions of OS X, Sierra or El Capitan, then
installation is very easy.  Open up "Terminal" in "Applications -> Utilities",
then type at the prompt:

     sudo pip3 install music21

it will prompt you for your password.  TADA: you have `music21` for Python!

To upgrade later, just do

    sudo pip3 install --upgrade music21

If you have a techy friend, he or she may recommend you use a virtual
environment to keep your `music21` installation separate from other
installations.  If you friend is willing to help you through
the additional problems that come with that (and the additional features),
listen to them.  Otherwise, do it our way above.



Starting Python and Checking the Version
----------------------------------------------

Python is a simple but powerful programming language that `music21`
is written in and in which you will write your own programs that
use `music21`.

To determine the Python version you have installed, open a
terminal (by going to Applications, then Utilities, and then
double clicking "Terminal") and enter the following command-line argument:

    `python3 -V`

it should display in Terminal something like the following:

.. image:: images/macScreenPythonVersion.*
    :width: 650

If it says 3.8 or higher (or possibly a number like 3.10.7), you're okay.
If it says 2.7 or 3.4 or something,
go to https://www.python.org/downloads/
and download a newer version.  Multiple versions of Python can exist
on a single computer without any problems.

After starting Python, try typing:

    `2+2`

You should see `4`.  This means Python is working.  Now see if
`music21` is working by typing:

    `import music21`

Hopefully this should work fine.

Exit python by typing `quit()`.


Starting the Configuration Assistant
-----------------------------------------------------

If you only installed the `music21` package with `pip` (for
instance, by running `sudo pip3 install music21`), you should run
the assistant from a command prompt::

    python3 -m music21.configure

You can also run the Configuration Assistant from a Python shell
 like this::

    import music21
    music21.configure.run()

After waiting a few moments to load modules, the Configuration Assistant begins.

.. image:: images/macScreenConfigAssistantStart.*
    :width: 650

If you have never used `music21` before,
following these prompts is recommended.

Selecting a MusicXML reader is the first step.
MusicXML is one of many display formats used by `music21`, and
will provide an easy way for you to visualize, print, and
transfer the music you edit or develop in `music21`.

The Configuration Assistant will attempt to find a MusicXML
reader on your system. If it can't find any, you will be asked
to open a URL to download MuseScore, a simple and free
MusicXML reader and easy writer. Installing MuseScore is
recommended for users who do not have Finale, Sibelius, Dorico, MuseScore,
or another MusicXML reader.

If one or more MusicXML readers are found, skip ahead to the next instructions.

.. image:: images/macScreenConfigAssistantReader.*
    :width: 650

If you choose to install MuseScore (formerly we suggested Finale Reader; hence the pictures below),
you will download an installer. Launch the installer immediately, and follow the instructions.

.. image:: images/macScreenConfigAssistantFinaleInstall.*
    :width: 650

After installing a MusicXML reader, or if you already have
one or more installed, the Configuration Assistant will present you with a
list of MusicXML readers from which to select one to use with music21 by
default. This means that `music21` will attempt to open MusicXML files
with this application. This setting can be easily changed later.
Enter the number of the selection as presented in the list:

.. image:: images/macScreenConfigAssistantSelect.*
    :width: 650

After selecting a MusicXML reader, you will be asked a number of
questions about working with `music21`. They concern whether music21 can access
the Internet, and whether you are willing to comply with the license for
use of music21 and the included corpus of scores.  You have to accept the
license to continue (we need to retain some rights you know!), but you
don't have to give us access to the Internet.

.. image:: images/macScreenConfigAssistantQuestions.*
    :width: 650

After the Configuration Assistant is complete, you can close the window when
it says "[process terminated]".


After Installation
-------------------------------

Open up the Mac Terminal (under Applications/Utilities/Terminal). You might want
to drag it to the dock.  You'll use it often.

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` to
begin using music21.


Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, start over from scratch
and try it again very carefully.  If you still have problems
contact the `music21` group and someone should be able to help:

https://groups.google.com/g/music21list

