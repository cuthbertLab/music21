.. _installMac:


Installing Music21 on Mac
============================================



Alternative Installation Methods
----------------------------------------------

The following instructions are for general users. If you are an advanced user and have installed other Python packages before, or want to use an EGG, SVN, PIP, or setuptools, you should read :ref:`installAdvanced`.

If you have experience working with the command line, the instructions given for GNU/Linux users will work the same for Mac users. See :ref:`installLinux`.



Check your version of Python
----------------------------------------------

Python is a simple but powerful programming language that music21
is written in and in which you will write your own programs that 
use music21.  

Mac OS X comes with Python, but it might not be a new enough version 
to run music21.  Music21 requires Python 2.6 to run (though many functions 
can run on 2.5 or 2.4). Python 3 is not yet supported. 

To determine the Python version you have installed, open a terminal (by going to Applications, then Utilities, and then double clicking "Terminal") and enter the following command-line argument (don't type the "$")

    $ python -V

it should display something like:

    Python 2.6.2


.. image:: images/macScreenPythonVersion.*
    :width: 600


if so, you're okay.  If not, go to http://www.python.org/download
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
    >>> print(distutils.sysconfig.get_python_lib())

.. image:: images/macScreenSitePackages.*
    :width: 600


Installing Music21 with the Configuration Assistant
-----------------------------------------------------


The Configuration Assistant provides a convenient way to install and configure music21. 

First, uncompress the .tar.gz file. You will see the following files stored in the directory.


.. image:: images/macScreenMusic21Folder.*
    :width: 600


TODO:


.. image:: images/macScreenConfigAssistantStart.*
    :width: 600


TODO:


.. image:: images/macScreenConfigAssistantStart.*
    :width: 600


TODO:

.. image:: images/macScreenConfigAssistantReader.*
    :width: 600


TODO:

.. image:: images/macScreenConfigAssistantFinaleInstall.*
    :width: 600


TODO:

.. image:: images/macScreenConfigAssistantSelect.*
    :width: 600


TODO:

.. image:: images/macScreenConfigAssistantQuestions.*
    :width: 600


TODO:


.. image:: images/macScreenShow.*
    :width: 600





After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`quickStart` to 
begin using music21.

You may need to install additional software to take advantage of some features of music21. For information on additional software you may need, see :ref:`installAdditional`.

You may want to configure your Environment to support opening MusicXML files. A tutorial for this is provided here: :ref:`tutorialFinaleMac`.

To configure all settings in music21, see :ref:`environment`.







