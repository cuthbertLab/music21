.. _usingGit:

Using music21 with Git for Eclipse
==================================

In order to develop music21 and stay current with updates to the latest
versions, it is necessary to modify code using SVN for Eclipse.

**IMPORTANT: BEFORE BEGINNING, UNINSTALL ALL EXISTING VERSIONS OF MUSIC21.
ADDITIONAL VERSIONS OF MUSIC21 INSTALLED IN OTHER LOCATIONS CAN CAUSE DIRECTORY
ROUTING PROBLEMS.**


Installing Git
--------------

First, make sure you have Git installed. You can find binaries for Windows, OSX
and Unix at `http://git-scm.com/ <http://git-scm.com/>`_.


Installing Eclipse
------------------

Once you have Git installed, download and install Eclipse. You can find the
most recent version of Eclipse Standard at 
`http://www.eclipse.org/downloads/ <http://www.eclipse.org/downloads/>`_, and
these instructions are written with Eclipse Standard 4.3 (Kepler) in mind.


Installing for Windows
``````````````````````````````````````````````

For Windows users, the safest bet is the 32-bit version, regardless of your
system's capabilities. 

If you download the 32-bit version save the Eclipse folder within the zip file
in your "Program Files (x86)" directory if there is one, or "Program Files" if
there isn't.  

If you choose the 64-bit version (getting more stable) then put the folder in
the "Program Files" directory even if there is an "(x86)" directory.  You may
need to give permission or your password to make this copy.  

After you've put the folder, go into the folder and drag a shortcut (by holding
down Alt when dragging) to Eclipse to your start menu (or know how to find it
later).

If you try running Eclipse and it gives you a warning about not having Java
installed, go to
http://www.java.com/en/download/help/windows_manual_download.xml#download and
download a copy there.


Installing for Mac
``````````````````````````````````````````````

For Mac users, download the version that complies with your system. If in
doubt, 32-bit is a safe option, as 64-bit systems are back-compatible to 32-bit
programs.

For Mac users, once the .tar file has been unzipped, drag the 'eclipse' folder
into the Applications folder in your dock (make sure to drag the folder and not
just the Eclipse icon - there are libraries and other dependencies that need to
be kept together).

..  image:: images/usingEclipse/eclipsefolder.*
    :width: 650
    
Once done, click on the Eclipse icon in the eclipse folder, and it should load. 

..  image:: images/usingEclipse/eclipseicon.*
    :width: 650

You'll be prompted to select a workspace directory, which, by default is
created in your documents folder. Be sure to remember where this directory is,
as it is where music21 will be installed.


Installing for Unix
``````````````````````````````````````````````

You've chosen to run Unix -- you should be able to figure this out on your own.
:-)


Installing PyDev and EGit for Eclipse
-------------------------------------

..  note::
    
    If you are using Windows, make sure to install Python through the normal
    Windows installation routines. See :ref:`installWindows`.

With Eclipse installed, you next need to install two plugins: PyDev and EGit.

PyDev is a Python IDE for Eclipse, which may be used in Python, Jython, and
IronPython development. EGit is a plugin that allows Eclipse to work with Git
repositories. Both of these can be installed via the Eclipse Marketplace.

1.  Launch the Eclipse Marketplace via Eclipse's *Help* menu:

    ..  image:: images/usingGit/eclipse__install_plugins__0.png

2.  Search for PyDev in the Marketplace search box, and click *Install* in the
    proper search results:

    ..  image:: images/usingGit/eclipse__install_plugins__1__edited.png

3.  When asked to confirm the installation, click *Install More* to return to
    the search dialog:

    ..  image:: images/usingGit/eclipse__install_plugins__2__edited.png

4.  Search for EGit in the Marketplace search box, and click *Install* in the
    proper search results:

    ..  image:: images/usingGit/eclipse__install_plugins__3__edited.png

5.  Now, when asked to confirm the installation of both PyDev and EGit, click
    *Confirm*:

    ..  image:: images/usingGit/eclipse__install_plugins__4__edited.png

6.  You will be asked to accept the licensing for both plugins. Choose "I
    accept the terms of the license agreements" and click *Finish*:

    ..  image:: images/usingGit/eclipse__install_plugins__5__edited.png

7.  Eclipse will now go through the process of automatically installing the two
    plugins. When it finishes, you'll be asked to confirm the certificate for
    PyDev. Click the checkbox and press OK:

    ..  image:: images/usingGit/eclipse__install_plugins__6__edited.png

8.  Finally, Eclipse will ask to restart. Click *Yes* to complete the plugin
    installation process:

    ..  image:: images/usingGit/eclipse__install_plugins__7.png


Forking music21 on GitHub
-------------------------


Cloning your music21 fork in Eclipse
------------------------------------

Once you've forked music21 on GitHub, you need to clone your fork locally to
your machine in order to start working.

To start the cloning process, choose *"Import..."* from Eclipse's *File* menu,
or right-click in the Package Explorer and choose *"Import"* from the
contextual menu that appears.

1.  In the *Import* dialog, open the *Git* folder and select *Projects from
    Git*, then click *Next*:

    ..  image:: images/usingGit/eclipse__clone__1__edited.png

2.  You'll now be asked to choose a repository source. While you can try using
    the *"GitHub"* repository source - which allows dynamically searching
    GitHub for repositories - if you've just made your fork a few minutes ago
    it won't show up when searching. We recommend selecting the *"Clone URI"*
    option. Once you've selected *"Clone URI"*, click *"Next"*:

    ..  image:: images/usingGit/eclipse__clone__2__edited.png

3.  

    ..  image:: images/usingGit/eclipse__clone__3__edited.png

4.  

    ..  image:: images/usingGit/eclipse__clone__4__edited.png

5.  

    ..  image:: images/usingGit/eclipse__clone__5__edited.png

6.  

    ..  image:: images/usingGit/eclipse__clone__6.png

7.  

    ..  image:: images/usingGit/eclipse__clone__7__edited.png

8.  

    ..  image:: images/usingGit/eclipse__clone__8__edited.png




Configuring PyDev
-----------------

..  image:: images/usingGit/eclipse__configure_pydev.png


Configuring the music21 Environment
-----------------------------------

Configuring the music21 Environment is done mostly like a normal install with
one big difference noted below.

To create a user environment settings file, open the music21/configure.py file
and run it by pressing the green circle with a white arrowhead in it at the top
of the Eclipse interface.

..  image:: images/usingEclipse/runningconfigure.*
    :width: 650
    
A new "Run As" window will appear in which you will be prompted to select a way
to run configure.py. Choose "Python Run" and click on "OK." (You should always
click this when running Python programs)

..  image:: images/usingEclipse/runas.*
    :width: 650

In the console, you may see errors about installing additional packages, after
which you will see a message beginning with "Welcome to the music21
Configuration Assisstant." 

..  image:: images/usingEclipse/welcometoconfigassistant.*
    :width: 650
    
When asked if you would like to install music21 in the normal place for Python
packages, type ``no`` and press Enter.

..  warning::

    Make sure you write ``no`` here.

..  image:: images/usingEclipse/saynotosavingmusic21.*
    :width: 650

See :ref:`environment` for more information on configuring user settings.
Otherwise, head to: :ref:`usersGuide_00_introduction` for further demos and
tutorials on using music21.


Committing, pushing and pulling in Eclipse
------------------------------------------


Configurating Git remotes in Eclipse
------------------------------------

..  image:: images/usingGit/eclipse__add_upstream_remote__1.png

..  image:: images/usingGit/eclipse__add_upstream_remote__2.png

..  image:: images/usingGit/eclipse__add_upstream_remote__3__edited.png

..  image:: images/usingGit/eclipse__add_upstream_remote__4__edited.png

..  image:: images/usingGit/eclipse__add_upstream_remote__5.png

..  image:: images/usingGit/eclipse__add_upstream_remote__6__edited.png


Fetching from upstream
----------------------

..  image:: images/usingGit/eclipse__fetch_from_upstream__1.png

..  image:: images/usingGit/eclipse__fetch_from_upstream__2__edited.png

..  image:: images/usingGit/eclipse__fetch_from_upstream__3.png

