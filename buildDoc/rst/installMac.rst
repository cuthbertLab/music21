.. _installMac:


Installing Music21 on Mac
============================================



Alternative Installation Methods
----------------------------------------------

The following instructions are for general users. If you are an advanced user and have installed other Python packages before, or want to use an EGG, SVN, PIP, or setuptools, you should read :ref:`installAdvanced`.

If you have experience working with the command line, the instructions given for GNU/Linux users will work the same for Mac users. See :ref:`installLinux`.



Check Your Version of Python
----------------------------------------------

Python is a simple but powerful programming language that music21
is written in and in which you will write your own programs that 
use music21.  

Mac OS X comes with Python, but it might not be a new enough version 
to run music21. Music21 requires Python 2.6 to run. Python 3 is not yet supported. 

To determine the Python version you have installed, open a terminal (by going to Applications, then Utilities, and then double clicking "Terminal") and enter the following command-line argument (don't type the "$")

    $ python -V

it should display in Terminal something like the following:

.. image:: images/macScreenPythonVersion.*
    :width: 650


If so, you're okay.  If not, go to http://www.python.org/download
and download a newer version.  Multiple versions of Python can exist 
on a single computer without any problems. 


Download music21 
----------------------------------------------

Download the most-recent music21 package from the following URL. 

    http://code.google.com/p/music21/downloads/list

Mac OS X users should download the .tar.gz file. 




The Installation Destination
----------------------------------------------

After downloading the music21 toolkit, the package is installed like any other Python extension library. Python stores extension libraries in a directory called 'site-packages'. The site-packages directory is located in different places depending on your platform. To find where your site-packages directory is located, you can enter the following command in the Python interpreter:

    >>> import distutils.sysconfig
    >>> print(distutils.sysconfig.get_python_lib())  # doctest: +SKIP

In Terminal, this looks like this:

.. image:: images/macScreenSitePackages.*
    :width: 650



Installing Music21 with the Configuration Assistant
-----------------------------------------------------


The music21 Configuration Assistant provides a convenient way to both install and configure music21. You use the Configuration Assistant through the Terminal. You will be guided through a number of simple questions and prompts.


First, uncompress the music21 .tar.gz file. You will see the following files stored in the outermost directory.


.. image:: images/macScreenMusic21Folder.*
    :width: 650


Double click on the installer.command file. This file will open a Terminal and begin running the Configuration Assistant. As this is a program downloaded from the internet, the System will likely warn you about running it. After waiting a few moments to load modules, the Configuration Assistant begins. 


.. image:: images/macScreenConfigAssistantStart.*
    :width: 650


The first option is to install music21 in its standard location (see above, The Installation Destination). Enter "y" or "yes", or press return to accept the default. Before installation begins you may be asked for your password. As Python packages are stored in a System directory, you need to give permission to write files to that location. During installation, a large amount of text will display the transfering of files. 


.. image:: images/macScreenConfigAssistantStart.*
    :width: 650


After installation the Configuration Assistant will try to configure your setup. If you have never used music21 before, following these prompts is recommended. 

Selecting a MusicXML reader is the first step. MusicXML is one of many display formats used by music21, and will provide an easy way for you to visualize, print, and transfer the music you edit or develop in music21. 

The Configuration Assistant will attempt to find a MusicXML reader on your system. If none are found, you will be asked to open a URL to download the Finale Reader, a simple and free MusicXML reader. Installing this reader is recommended for users who do not have Finale, Sibelius, MuseData, or another MusicXML reader. If one or more MusicXML readers are found, skip ahead to the next instructions.


.. image:: images/macScreenConfigAssistantReader.*
    :width: 650


If you choose to install the Finale Reader, you will download an installer. Launch the installer immediately, and follow the instructions. 


.. image:: images/macScreenConfigAssistantFinaleInstall.*
    :width: 650


After installing a MusicXML reader, or if you already have one or more installed, the Configuration Assistant will present you with a list of MusicXML readers from which to select one to use with music21 by default. This means that music21 will attempt to open MusicXML files with this application. This setting can be easily changed later. Enter the number of the selection as presented in the list:


.. image:: images/macScreenConfigAssistantSelect.*
    :width: 650


After selecting a MusicXML reader, you will be asked a number of questions about working with music21. Please read these carefully. 


.. image:: images/macScreenConfigAssistantQuestions.*
    :width: 650


After the Configuration Assistant is complete, you can open a fresh Terminal window, enter python, and execute a bit of music21 code to test your installation and MusicXML reader configuration:


    >>> from music21 import *
    >>> s = corpus.parse('bach/bwv65.2.xml')
    >>> s.show()  # doctest: +SKIP


Assuming your installation and configuration went as expected, the MusicXML reader should launch and display the work, as shown below:


.. image:: images/macScreenShow.*
    :width: 650





After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`quickStart` to 
begin using music21.

You may need to install additional software to take advantage of some features of music21. For information on additional software you may need, see :ref:`installAdditional`.

You may want to configure your Environment to support opening MusicXML files with a different Reader. A tutorial for this is provided here: :ref:`tutorialFinaleMac`.

To configure all settings in music21 directly, see :ref:`environment`.





Installation Help
-------------------------------

If you have followed all the instructions and encounter problems, contact the music21 group for help:

http://groups.google.com/group/music21list






