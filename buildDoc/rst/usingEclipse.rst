.. _usingEclipse:

Using music21 with SVN for Eclipse
==================================

In order to develop music21 and stay current with updates to the latest versions, it is necessary to modify code using SVN for Eclipse. 

**0. Get Eclipse**

First, download and install the appropriate version of Eclipse from the following url if you don't already have it: 				    http://www.eclipse.org/downloads/packages/eclipse-classic-37/indigor

**1A. Get PyDev for Eclipse**

PyDev is a Python IDE for Eclipse, which may be used in Python, Jython, and IronPython development. Make sure you have installed PyDev: 			http://pydev.org/updates

**1B. Get Subclipse**

Subclipse is an Eclipse Team Provider plug-in providing support for Subversion within the Eclipse IDE. You can download it through this website: http://subclipse.tigris.org/subclipse_1.6.x/changes.html. 

For help with installing Subclipse, refer to: https://www.ibm.com/developerworks/opensource/library/os-ecl-subversion

**2. Checkout music21**

Within Eclipse, select Import from the File menu. Select SVN Checkout Projects from SVN. Under New Repositoy Location url, enter: https://music21.googlecode.com/svn/trunk

The latest music21 code will automatically be checked out through SVN. After this process has completed, create a new PyDev project in your standard workspace with a recognizable name, such as music21base.

**3. Add music21 to PYTHONPATH**

In order to ensure that music21 works properly through SVN, you will need to append the music21 folder to your PYTHONPATH. This can be done within the Preferences window of Eclipse. Under the PyDev heading, select Interpreter – Python. In the Libraries window, add the music21base folder that you created in the previous step to you PYTHONPATH.