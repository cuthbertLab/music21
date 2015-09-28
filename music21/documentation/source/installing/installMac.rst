.. _installMac:

Installing Music21 on Mac
============================================

Because Apple changes their system details so much
from one version of OS X to another, installing music21 
is probably the hardest part of the experience.  
Once you have that set, the rest should be much less painful.
Trust us that it should work.

Simple install on OS X El Capitan
--------------------------------------------

If you're on the newest version of OS X, El Capitan (October 2015), then
installation is very easy.  Open up "Terminal" in "Applications -> Utilities",
then type at the prompt:

     sudo pip install music21

it will prompt you for your password.  TADA: you have `music21` for Python 2.7.

If you're not on El Cap, or if you want Python 3 (much better!) or something else
comes up, just follow the instructions below *carefully* and you shouldn't
have any problems.


To upgrade later, just do

    sudo pip install --upgrade music21


Starting Python and Checking the Version
----------------------------------------------

Python is a simple but powerful programming language that music21
is written in and in which you will write your own programs that 
use music21.

Mac OS X comes with Python, but if you have an older version of OS X
(Leopard or earlier) it might not be a new enough version 
to run music21. Music21 requires Python 2.7 (2.7.3 or later) or Python 3.3 or 3.4. 

To determine the Python version you have installed, open a 
terminal (by going to Applications, then Utilities, and then 
double clicking "Terminal") and enter the following command-line argument (don't type the "$")

    $ python -V

it should display in Terminal something like the following:

.. image:: images/macScreenPythonVersion.*
    :width: 650

If it says 2.7.3 (possibly with a following number like
2.7.10) or 3.3 or higher, you're okay.  If it says 2.4 or 2.5 or 2.6, 
go to http://www.python.org/download
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems.


Download music21 
----------------------------------------------

Download the most-recent music21 package by getting the first .tar.gz file
from the following URL. 

    https://github.com/cuthbertLab/music21/releases

The newest version should be at the top.  ``Do not download`` the `-no-corpus`
version of the file.

Once it's downloaded, double-click the icon on your desktop named
something like music21-2.0.0.tar.gz -- this will create a new directory
on your desktop called something like "music21-2.0.0".  Look inside it.

You will see the following files:

.. image:: images/macScreenMusic21Folder.*
    :width: 650

If you're with us so far, you're halfway there.


Starting the Configuration Assistant
-----------------------------------------------------

The music21 Configuration Assistant installs music21 in a place where
Python can find it and lets you configure music21. 

Double click on the installer.command file to start. 
This file should open a Terminal window and begin running the Configuration Assistant. 
As this is a program downloaded from the Internet, the System will likely warn you about 
running it. Go ahead and click "Open".

After waiting a few moments to load modules, the Configuration Assistant begins. 

.. image:: images/macScreenConfigAssistantStart.*
    :width: 650

The first option is to install music21 in its standard location 
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
configure your setup. If you have never used music21 before, 
following these prompts is recommended.

Selecting a MusicXML reader is the first step. 
MusicXML is one of many display formats used by music21, and 
will provide an easy way for you to visualize, print, and 
transfer the music you edit or develop in music21. 

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
default. This means that music21 will attempt to open MusicXML files 
with this application. This setting can be easily changed later. 
Enter the number of the selection as presented in the list:

.. image:: images/macScreenConfigAssistantSelect.*
    :width: 650

After selecting a MusicXML reader, you will be asked a number of 
questions about working with music21. They concern whether music21 can access
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

CONGRATS! You're done with installing.  You can delete the `music21-2.0.0.tar.gz` file
and `music21-2.0.0` folder from your desktop now.  

Open up the Mac Terminal (under Applications/Utilities/Terminal). You might want
to drag it to the dock.  You'll use it often.

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` to 
begin using music21.



Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, start over from scratch
and try it again very carefully.  If you still have problems
contact the music21 group and someone should be able to help:

http://groups.google.com/group/music21list

