.. _installWindows:


Installing Music21 in Windows
============================================


Get Python
-------------------------------

Python is a simple but powerful programming language that music21
is written in and in which you will write your own programs that 
use music21.  

Windows users should download and install Python version 3.4. Python 2.7
is still supported, but if you're learning Python for the first time,
definitely go for Python 3.X.

To get Python 3.4 for Windows, go to http://www.python.org/download/ 
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
Make sure it begins with 2.7.3 or higher or 3.3 or higher.

If your version is too old, download a newer version as above.

Download music21
-------------------------------

Download the most-recent music21 package from the following URL:

  https://github.com/cuthbertLab/music21/releases

Windows users should download the .exe file to their desktops
and then click on it.


Install music21
-------------------------------

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
displays "`>>>`" and perhaps a warning about missing packages, then 
you've installed everything properly.  (If the system
cannot find `music21` then you may have more than one version of 
Python on your system.  Try uninstalling all of them along with `music21`
and then restarting from scratch).



After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` 
to begin using music21.




Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, start over from scratch
and try it again very carefully.  If you still have problems
contact the music21 group and someone should be able to help:

http://groups.google.com/group/music21list






