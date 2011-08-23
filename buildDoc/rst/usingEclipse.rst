.. _usingEclipse:

Using music21 with SVN for Eclipse
==================================

In order to develop music21 and stay current with updates to the latest versions, it is necessary to modify code using SVN for Eclipse. 

Installing Eclipse
----------------------------------------------

First, download and install the appropriate version of Eclipse from the following url if you don't already have it: 				    http://www.eclipse.org/downloads/packages/eclipse-classic-37/indigor

Installing PyDev for Eclipse
----------------------------------------------

PyDev is a Python IDE for Eclipse, which may be used in Python, Jython, 
and IronPython development. Installing PyDev must be done from inside Eclipse. 

First, click on "Help" in the Eclipse menu bar. Then select "Install New Software..." A new dialog box will open up.

.. image:: images/usingEclipse/installingpydev1.*
    :width: 650

Enter the website "http://pydev.org/updates" in the "Work with:" field. Two programs will load in the field below. Check both boxes and click on "Next" at the bottom of the dialog box. Accept the terms, allow the certificate, and finally click on "Finish" when everything is done.

(For more help, visit http://pydev.org/manual_101_install.html.)

Installing Subclipse for Eclipse
----------------------------------------------

Subclipse is an Eclipse Team Provider plug-in providing support for Subversion within the Eclipse IDE. Again, you should install Sublcipse from within Eclipse. Enter the following website into the "Work with:" field of the Install dialog box: http://subclipse.tigris.org/update_1.6.x. Follow the same process as with PyDev.

.. image:: images/usingEclipse/installingsubclipse.*
    :width: 650

For help with installing Subclipse, refer to: https://www.ibm.com/developerworks/opensource/library/os-ecl-subversion


Checking Out music21
----------------------------------------------

Within Eclipse, select "Import" from the "File" menu. Expand the "SVN" option, and then select "Checkout Projects from SVN." and click "Next." 

.. image:: images/usingEclipse/checkingoutfromSVN0.*
    :width: 650

In the "Checkout from SVN" dialog box, select the "Create a new repository location" option.

.. image:: images/usingEclipse/checkingoutfromSVN.*
    :width: 650

"Under New Repositoy Location url, enter: https://music21.googlecode.com/svn/trunk

.. image:: images/usingEclipse/checkingoutfromSVN2.*
    :width: 650
    
The music21 folders should load in the field below. Highlight the "https://music21.googlecode.com/svn/trunk" folder and click "Finish."

.. image:: images/usingEclipse/checkingoutfromSVN3.*
    :width: 650 



During the checkout, you will potentially encounter the following error:

"Subversion Native Library Not Available"

Follow the link provided (http://subclipse.tigris.org/wiki/JavaHL) and follow the instructions for whichever platform you are running.

If you download from CollabNet, you can choose download a version of the available Subversion Binaries, which will contain the proper language bindings, but will not interfere with the installation of Subversion in progress.



The latest music21 code will automatically be checked out through SVN. 


Creating a new PyDev Project
----------------------------------------------

After the checkout process has completed, a dialog box will open, entitled "New Project," asking you to "select a wizard." Expand the "PyDev" option, and select "PyDev Project." Click "Next." 

.. image:: images/usingEclipse/creatingnewpydevproj.*
    :width: 650 

A new window with the heading "PyDev Project" will open. In the "Project Name" field, enter something recognizable to you such as "music21base." You will be asked to specify a Python interpreter, which you must do by clicking on the "Please configure an interpreter in the related preferences before proceeding" link.

.. image:: images/usingEclipse/creatingnewpydevproj2.*
    :width: 650

Clicking that link will open a new dialog box entitled "Preferences." The fastest way to detect any version of Python already isntalled on the system is to click "Auto Config" in the right-hand column.

.. image:: images/usingEclipse/creatingnewpydevproj3.*
    :width: 650

Click on "Select All" in the ensuing dialog box and click "OK." 

.. image:: images/usingEclipse/creatingnewpydevproj4.*
    :width: 650

After doing so, be sure to hit "Apply" in the "Preferences" dialog box before hitting "OK."

.. image:: images/usingEclipse/creatingnewpydevproj5.*
    :width: 650

When returning to the new PyDev Project box, a new drop-down menu should appear under the title "Interpreter," in which you should select "python". In the three bubbles below that field, select "Add project directly to the PYTHONPATH?" and then click on "Finish." 

.. image:: images/usingEclipse/creatingnewpydevproj6.*
    :width: 650


The SVN checkout will continue. Once it is finished, files should appear in the left-hand column of Eclipse with the files of music21, with dates of updates and names of updaters next to them.

.. image:: images/usingEclipse/SVNfinalview.*
    :width: 650
    
Checking The Install
----------------------------------------------

In order to check to the install occurred as planned, you should open a PyDev console and attempt to import the music21 module.

Click on "Window" in the Eclipse menu bar, then select "Show View" and choose "Console."

.. image:: images/usingEclipse/choosingviewfrommenu.*
    :width: 650
    
This will open a console window in the lower portion of the Eclipse interface. To create a Python console, find the menu bar above the console, and click on the icon all the way to the right that looks like a window with a sparkle on its upper-righthand corner. A new menu will open next to it.

.. image:: images/usingEclipse/wheretogotoopenconsole.*
    :width: 650
    
Choose "PyDev Console." A new window will open with a series of buttons. Choose the "Python console" button and click "OK."

.. image:: images/usingEclipse/choosingpythonconsole.*
    :width: 650
    
A new console window will open in the lower portion of the Eclipse interface and will load Python. After it loads, you will be able to type. To verify that your install occurred correctly try typing "import music21."

.. image:: images/usingEclipse/importingmusic21inpythonconsole.*
    :width: 650
    
Errors concerning additional packages may appear; if so, refer to :ref:`installAdditional` to install them. Most modules in music21 will still function without them, however. If other errors persist, contact the music21 staff for assistance: http://groups.google.com/group/music21list


Once you have verified that the install completed successfully, head to: :ref:`quickStart`
