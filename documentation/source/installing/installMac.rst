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

Though Macs come with Python, it's a very old version.  We recommend 
updating that by going to http://www.python.org/ and getting Python 3.6
or later.

(The `music21` team strongly recommends using the version of
Python 3 from the python.org website and not the Conda version
(or Enthought Canopy) because it is fully compatiable with 
matplotlib.  If you have no plans on plotting functions, 
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

(If you didn't install Python 3.6, then replace "pip3" with "pip"


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

If it says 3.4 or higher (or possibly a number like 3.4.2), you're okay.  
If it says 2.4 or 2.5 or 2.6, 
go to http://www.python.org/download
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems.

Try typing:

    `2+2`

You should see `4`.  This means Python is working.  Now see if
`music21` is working by typing:

    `import music21`
    
Hopefully this should work fine.

Exit python by typing `quit()`.


Starting the Configuration Assistant
-----------------------------------------------------

Double click on the installer.command file to start. 
This file should open a Terminal window and begin running the Configuration Assistant. 
As this is a program downloaded from the Internet, the System will likely warn you about 
running it. Go ahead and click "Open".

After waiting a few moments to load modules, the Configuration Assistant begins. 

.. image:: images/macScreenConfigAssistantStart.*
    :width: 650

The first option is to install `music21` in its standard location 
(see below, The Installation Destination). Enter "y" or "yes", or 
press return to accept the default of "yes". 

Before installation begins you may be asked for your Mac password. (The cursor
won't move or display any letters when you type in the password.  Just rest assured
that the characters are being transmitted). 
As Python packages are stored in a System directory, you need to give permission 
to write files to that location.  

(If you don't get a prompt but instead start getting
a lot of errors, you probably do not have an administrator account on your Mac.
To make yourself one, quit the installation program (just close the window), open
System Preferences from the Apple menu in the upper left corner of your screen, click on
Users and Groups (4th Row).  Click on the lock on the lower-left corner -- you'll need
your Mac password.  Then click "Allow user to administer this computer".  Then
close System Preferences and click the music21 `installer.command` button again and
go back one step.)

During installation, a large amount of text will display showing files being copied.
Sorry about the mess.  Just ignore it!  It means it's working.

.. image:: images/macScreenConfigAssistantStart.*
    :width: 650

After installation the Configuration Assistant will try to 
configure your setup. If you have never used `music21` before, 
following these prompts is recommended.

Selecting a MusicXML reader is the first step. 
MusicXML is one of many display formats used by `music21`, and 
will provide an easy way for you to visualize, print, and 
transfer the music you edit or develop in `music21`. 

The Configuration Assistant will attempt to find a MusicXML 
reader on your system. If it can't find any, you will be asked 
to open a URL to download Finale Notepad 2012, a simple and free 
MusicXML reader and easy writer. Installing this reader is 
recommended for users who do not have Finale, Sibelius, MuseScore, 
or another MusicXML reader. You might want to try MuseScore instead,
which is also free and doesn't require you to register to download it.

If one or more MusicXML readers are found, skip ahead to the next instructions.

.. image:: images/macScreenConfigAssistantReader.*
    :width: 650

If you choose to install Finale Notepad (formerly Finale Reader; hence the pictures below), 
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

CONGRATS! You're done with installing.  You can delete the `music21-4.0.0.tar.gz` file
and `music21-4.0.0` folder from your desktop now.  

Open up the Mac Terminal (under Applications/Utilities/Terminal). You might want
to drag it to the dock.  You'll use it often.

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` to 
begin using music21.



Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, start over from scratch
and try it again very carefully.  If you still have problems
contact the `music21` group and someone should be able to help:

http://groups.google.com/group/music21list

