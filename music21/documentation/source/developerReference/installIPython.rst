Using `music21` with the iPython Notebook
==============================================

To get `music21` to work with iPython Notebook, first install the anaconda distribution of python... 

```
ciconia:~ cuthbert$ cd Downloads
ciconia:Downloads cuthbert$ bash Anaconda-1.5.1-MacOSX-x86_64.sh
ciconia:Downloads cuthbert$ cd ~
ciconia:~ cuthbert$ cd anaconda
ciconia:anaconda cuthbert$ bin/conda update conda 
ciconia:anaconda cuthbert$ bin/conda update ipython
ciconia:anaconda cuthbert$ bin/conda pip music21
```

    Downloading/unpacking music21
      Downloading music21-1.5.0.tar.gz (29.6MB): 29.6MB downloaded
      Running setup.py egg_info for package music21
        
        warning: no files found matching '*.pdf' anywhere in distribution
        no previously-included directories found matching 'dist'
        no previously-included directories found matching 'buildDoc'
        no previously-included directories found matching 'obsolete'
    Installing collected packages: music21
      Running setup.py install for music21
        
        warning: no files found matching '*.pdf' anywhere in distribution
        no previously-included directories found matching 'dist'
        no previously-included directories found matching 'buildDoc'
        no previously-included directories found matching 'obsolete'
    Successfully installed music21
    Cleaning up...
    # files: 8219
    
    # success
    music21-1.5.0-py27_0.tar.bz2
    music21-1.5.0-py27_0:
        making available
        linking

Anaconda messes with your PATH, so I suggest opening your ~/.bash_profile and putting the condo command after $PATH not before:

```# added by Anaconda 1.5.1 installer
export PATH="$PATH:/Users/cuthbert/anaconda/bin"```

Now you're ready to run iPython.  Make sure you're in the anaconda directory and run:

```ciconia:anaconda cuthbert$ bin/ipython notebook --pylab inline```

##Using the web-based IP Notebook##

Now in the webbrowser you can type commands such as the ones below:



All other normal `music21` commands will work as they should

Displaying graphics inline
----------------------------

By default, you cannot just call .show() because you'll open up your MusicXML reader locally...


Nor does just generating a lilypond PNG work as you'd like -- this will display it on the screen but not in your browser:


Instead do this:


Now this will work:


If you don't want to do that, then instead do this...



SVG is much faster, but it doesn't work, sadly...


Whole pieces will show properly also now that the extension module is loaded



Images from other docs etc. can be loaded into the notebook just like any other iPython notebook


###Turn off pesky prompts.  Run this and then hide it###


To turn back on change display to 'block'; note that it must be the last thing on the page!

