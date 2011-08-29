.. _usingEclipse:

Using music21 with SVN for Eclipse
==================================

In order to develop music21 and stay current with updates to the latest versions, it is necessary 
to modify code using SVN for Eclipse.

**IMPORTANT: BEFORE BEGINNING, UNINSTALL ALL EXISTING VERSIONS OF MUSIC21. ADDITIONAL VERSIONS OF 
MUSIC21 INSTALLED IN OTHER LOCATIONS CAN CAUSE DIRECTORY ROUTING PROBLEMS.**


Installing Eclipse
----------------------------------------------

First, download and install the appropriate version of Eclipse from the following url if you 
don't already have it: http://www.eclipse.org/downloads/packages/eclipse-classic-37/indigor

For Windows users, we recommend installing the 32-bit version, regardless of your system's 
capabilities. For Mac users, choose the version that complies with your system. If in 
doubt, 32-bit is a safe option, as 64-bit systems are back-compatible to 32-bit programs.

For Mac users, once the .tar file has been unzipped, drag the 'eclipse' folder into the Applications 
folder in your dock (make sure to drag the folder and not just the Eclipse icon - there are libraries 
and other dependencies that need to be kept together).

.. image:: images/usingEclipse/eclipsefolder.*
    :width: 650
    

Once done, click on the Eclipse icon in the eclipse folder, and it should load. 

.. image:: images/usingEclipse/eclipseicon.*
    :width: 650


You'll be prompted to select a workspace directory, which, by default is created in your documents 
folder. Be sure to remember where this directory is, as it is where music21 will be installed.



Installing PyDev for Eclipse
----------------------------------------------

PyDev is a Python IDE for Eclipse, which may be used in Python, Jython, 
and IronPython development. Installing PyDev must be done from inside Eclipse. 

First, click on "Help" in the Eclipse menu bar. Then select "Install New Software..." A new 
dialog box will open up.

.. image:: images/usingEclipse/installingpydev1.*
    :width: 650


Enter the website "http://pydev.org/updates" in the "Work with:" field. Do not click on "add;" 
rather, simply press Enter and two programs will load in the field below (PyDev and PyDev Mylyn Integration). 
Check both boxes and click on "Next" at the bottom of the dialog box. Accept the terms, and wait 
for it to install. A security warning window will open, and you will be prompted to allow the 
certificate for Aptana.

.. image:: images/usingEclipse/aptana_certificate.*
    :width: 650


Check the box, click OK, and the install will continue.

After the install is finished, you will be prompted to restart Eclipse, which you should do.

(For more help, visit http://pydev.org/manual_101_install.html.)



Installing Subversive
~~~~~~~~~~~~~~~~~~~~~

In order for Eclipse to connect to the SVN, you will also have to install Subversive.

To install Subversive, click on "Help," then "Install new software..." In the pull-down menu, select "Indigo."  

.. image:: images/usingEclipse/install_subversive1.*
    :width: 650
    
    
When the list of programs loads in the field below, expand "Collaboration."

.. image:: images/usingEclipse/expand_collaboration.*
    :width: 650


Select the four options that begin with "Subversive" and click "Next." 

.. image:: images/usingEclipse/select_4subversive.*
    :width: 650


Accept the terms and allow the install to finish. Afterwards, you will be prompted to restart 
Eclipse, which you should do.

Upon restarting, an "Install Connectors" window will open, in which you should select the "SVN Kit 
1.3.5" option and click "Finish."

.. image:: images/usingEclipse/SVNconnectors.*
    :width: 650


An "Install" window will open, outlining the packets you are installing. Click on "Next >." 

.. image:: images/usingEclipse/installSVNconnectors.*
    :width: 650


Again, you'll be prompted to accept terms, and your software will be installed (be sure to allow the 
software when the security warning appears). And once again, you will be prompted to restart Eclipse.


Checking Out music21 with Subversion
----------------------------------------------

Click on "File" from the Eclipse menu bar, and select "Import." Expand the "SVN" option. If you see 
two SVN folders, expand the one that contains "Project from SVN" and select it. Click on "Next."
 
.. image:: images/usingEclipse/projectfromSVN.*
    :width: 650
    
If you have commit access, refer to `Checking Out music21 with Commit Access`_ for more details.
For standard checkout procedure, continue below.
 
In the "Checkout from SVN" window, enter http://music21.googlecode.com/svn into the "URL:" field. 
Select the "Use the repository URL as the label" option, and click on "Next." 
 
.. image:: images/usingEclipse/checkoutfromSVN.*
    :width: 650
 
Keep the defaults as shown and click "Finish" in the window that follows.
 
.. image:: images/usingEclipse/selectresource_checkoutfromSVN.*
    :width: 650
 
A "Check Out As" window will appear. Keep the defaults as shown and click "Finish."  
 
.. image:: images/usingEclipse/checkoutas.*
    :width: 650
 
Continue the process with `Creating a new PyDev Project`_.


Checking Out music21 with Commit Access
----------------------------------------------

In the "Checkout from SVN" window, enter https://music21.googlecode.com/svn into the "URL:" field. 
Select the "Use the repository URL as the label" option. Under "Authentication," enter the email 
address of the Google account that you will be using to which commit access has been granted by the 
developers, and the password that you have been provided. Be sure to check the "Save authentication"
box if you'd like to avoid being prompted for the same info in the future. Also, make sure the box next to
"Validate Repository Location on Finish" is selected, and click on "Next."

.. image:: images/usingEclipse/checkingoutwithcommit.*
    :width: 650

Keep the defaults as shown and click "Finish" in the window that follows.
 
.. image:: images/usingEclipse/selectresource_checkoutfromSVN.*
    :width: 650
 
A "Check Out As" window will appear. Keep the defaults as shown and click "Finish."  
 
.. image:: images/usingEclipse/checkoutas.*
    :width: 650
 
Continue the process with `Creating a new PyDev Project`_.    


Creating a new PyDev Project
----------------------------------------------

After the checkout process has completed, a dialog box will open, entitled "New Project," 
asking you to "select a wizard." Expand the "PyDev" option, and select "PyDev Project." 
Click "Next." 

.. image:: images/usingEclipse/creatingnewpydevproj.*
    :width: 650 


A new window with the heading "PyDev Project" will open. In the "Project Name" field, 
enter something recognizable to you that is *NOT* "music21." (There will be a subdirectory 
under the trunk file called "music21," and if name your trunk directory "music21," both you 
and the SVN will be very confused). "music21base," for instance, is a perfectly safe name. 
Click on the "Please configure an interpreter in the related preferences before proceeding" link.

.. image:: images/usingEclipse/creatingnewpydevproj2.*
    :width: 650


Clicking that link will open a new dialog box entitled "Preferences." The fastest way to 
detect any version of Python already isntalled on the system is to click "Auto Config" in 
the right-hand column.

.. image:: images/usingEclipse/creatingnewpydevproj3.*
    :width: 650


Click on "Select All" in the ensuing dialog box and click "OK." 

.. image:: images/usingEclipse/creatingnewpydevproj4.*
    :width: 650
    
    
Next, you must manually add "music21" to your PYTHONPATH?. Click "New Folder" in the right-hand 
column and search for the music21 folder in your workspace (this is typically under the Documents 
directory of your user profile if you kept the default).  

.. image:: images/usingEclipse/blurred_PYTHONPATH.*
    :width: 650

After doing so, be sure to hit "Apply" in the "Preferences" dialog box before hitting "OK."

.. image:: images/usingEclipse/creatingnewpydevproj5.*
    :width: 650

When returning to the new PyDev Project box, a new drop-down menu should appear under the 
title "Interpreter," in which you should select "python". In the three bubbles below that 
field, select "Add project directly to the PYTHONPATH?" and then click on "Finish." 

.. image:: images/usingEclipse/creatingnewpydevproject_cropped.*
    :width: 650


When prompted to open a PyDev perspective, click "Yes."

.. image:: images/usingEclipse/pydevperspective.*
    :width: 650


The SVN checkout will continue (it may take 10-15 minutes) amidst a screen such as the one shown below. 

.. image:: images/usingEclipse/operationinprogress.*
    :width: 650


Once it is finished, files should appear in the left-hand column of Eclipse with the files of music21, with dates of updates 
and names of updaters next to them.

.. image:: images/usingEclipse/SVNfinalview.*
    :width: 650
    
    
    
Checking The Install
----------------------------------------------

In order to check that the install occurred as planned, you should open a PyDev console and attempt 
to import the music21 module.

Click on "Window" in the Eclipse menu bar, then select "Show View" and choose "Console."


.. image:: images/usingEclipse/choosingviewfrommenu.*
    :width: 650
    
    
This will open a console window in the lower portion of the Eclipse interface. To create a Python 
console, find the menu bar above the console, and click on the icon all the way to the right that 
looks like a window with a sparkle on its upper-righthand corner. A new menu will open next to it.


.. image:: images/usingEclipse/wheretogotoopenconsole.*
    :width: 650
    
    
Choose "PyDev Console." A new window will open with a series of buttons. Choose the "Python console" 
button and click "OK."


.. image:: images/usingEclipse/choosingpythonconsole.*
    :width: 650
    
    
A new console window will open in the lower portion of the Eclipse interface and will load Python. 
After it loads, you will be able to type. To verify that your install occurred correctly try typing 
"from music21 import \*."
    
Errors concerning additional packages may appear; if so, refer to :ref:`installAdditional` to 
install them. Most modules in music21 will still function without them, however. If other errors 
persist, contact the music21 staff for assistance: http://groups.google.com/group/music21list



As a quick music21 demo to ensure all of the components are working properly, create a Neopolitan 
sixth chord in the key of A minor by typing in ``n6chord = roman.RomanNumeral('bII6', 'a')`` and press 
Enter. To display the pitches contained in the chord, type ``n6chord.pitches`` and press Enter. The 
output should be ``[D5, F5, B-5]``. 

Next, create an eight-note triplet duration by typing 
``trip = duration.Duration(0.333333333333333333)``. Music21 recognizes what kind of note typically has 
that duration, and prints ``'Eight Triplet (0.33QL)'`` when you type ``trip.fullName`` and press Enter.

.. image:: images/usingEclipse/frommusic21import.*
    :width: 650
    
To create a user environment settings file, open the music21/configure.py file and run it by pressing 
the green circle with a white arrowhead in it at the top of the Eclipse interface.

.. image:: images/usingEclipse/runningconfigure.*
    :width: 650
    
A new "Run As" window will appear in which you will be prompted to select a way to run configure.py. Choose
"Python Run" and click on "OK."

.. image:: images/usingEclipse/runas.*
    :width: 650

In the console, you may see errors about installing additional packages, after which you will see a message 
beginning with "Welcome to the music21 Configuration Assisstant." 

.. image:: images/usingEclipse/welcometoconfigassistant.*
    :width: 650
    
When asked if you would like to install music21 in the normal place for Python packages, type "no" and press Enter.

.. image:: images/usingEclipse/saynotosavingmusic21.*
    :width: 650

See :ref:`environment` for more information on 
configuring user settings. Otherwise, head to: :ref:`quickStart` for further demos and tutorials on 
using music21.
