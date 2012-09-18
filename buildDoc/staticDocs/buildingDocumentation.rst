.. _buildingDocumentation:


Building Documentation
==================================

Creating or updating the music21 documentation requires a few additional programs to be installed, 
most importantly one called Sphinx. Sphinx is a documentation generator that uses 
reStructuredText (rst) as its markup language and outputs HTML documents. 



**1) Installing setuptools**
First, you’ll need setuptools if you don’t already have it. Setuptools is a package management 
software that makes it easy to download, build, upgrade, and uninstall Python packages. 
To download, go to http://pypi.python.org/pypi/setuptools and follow the instructions for whichever 
system you’re running. Be sure to get the version of setuptools that corresponds to the 
version of python you’re using as well (they’re all listed at http://pypi.python.org/pypi/setuptools#files). In the terminal, enter ``sudo sh setuptools-0.6c9-py2.4.egg`` (or rather, use the filename of 
the egg version that you downloaded). For Python 2.7, it’ll look like this:	``sudo sh setuptools-0.6c11-py2.7.egg``Note: depending on where you saved the .egg when you downloaded it, you may have to change the directory.You should be prompted for your password, and then you should see something resembling this: 	``Installing easy_install script to /Library/Frameworks/Python.framework/Versions/2.7/bin``
		``Installing easy_install-2.7 script to /Library/Frameworks/Python.framework/Versions/2.7/bin``
		``Installed /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg``
		``Processing dependencies for setuptools==0.6c11``
		``Finished processing dependencies for setuptools==0.6c11``If you run python in the terminal, you should be able to ``import easy_install`` without any errors.(Additional instructions for installing and using setuptools/easy_install are available at: 
http://peak.telecommunity.com/DevCenter/EasyInstall?action=highlight&value=EasyInstall)


**2) Downloading and Installing Sphinx**

Once setuptools is installed, head to http://pypi.python.org/pypi/Sphinx/1.0.7 to download 
the Sphinx egg that corresponds to your version of Python.In the terminal, type in ``easy_install Sphinx-1.0.7-py2.7.egg`` (again, you may have to change 
the directory depending on where you saved the egg). 

**3) Running build.py** 

Once that finishes running, go to Eclipse and under the ``buildDoc`` folder of ``trunk``, open ``build.py`` and run it. 
HTML documents should be generated and stored in ``music21/docs/html``, which you can then open in your web browser.
Static documentation goes in the ``buildDoc/staticDocs`` folder.  It is tested by running ``test/testDocumentation.py``.

To add a module to ``buildDoc``, it needs to be listed twice, first at the top import then in the list of modules below.
Keep all modules in alphabetical order.