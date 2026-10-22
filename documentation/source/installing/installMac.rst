.. _installMac:

Installing `music21` on Mac
============================================

These steps give you a folder for your `music21` work, with Python, `music21`,
and Jupyter inside it. Jupyter lets you write and run `music21` code in your
web browser and see the results (including notation) right under it.
You don't need to install Python first; the steps below do that for you.


Open Terminal
---------------------------------------

Terminal is where you type commands to your Mac. It's in Applications, then
Utilities, then "Terminal" (or press Command-Space and type "Terminal").
You'll use it often, so you might want to drag it to the Dock.


Install uv
---------------------------------------

uv is a free tool that installs Python and Python packages like `music21`.
Copy this line into Terminal and press Return::

    curl -LsSf https://astral.sh/uv/install.sh | sh

When it finishes, close the Terminal window and open a new one, so that
Terminal knows where uv is. (If you use Homebrew, `brew install uv` works too.)


Make a folder for music21
---------------------------------------

Type these lines one at a time, pressing Return after each::

    mkdir ~/m21play
    cd ~/m21play
    uv init --bare
    uv add music21
    uv add notebook

This makes a folder called `m21play` (or whatever you want to call your music21
playing around applications) in your home folder (the one with
the house icon in Finder) and installs Python, `music21`, and Jupyter Notebook
into it. Just don't call the folder `music21`
itself.


Set up music notation
---------------------------------------

To see notation in the browser, `music21` needs MuseScore -- so download it even if
you normally use Dorico or Sibelius or Finale. It's free at https://musescore.org;
install it before going on.

Then run the Configuration Assistant. In the same Terminal window, type::

    uv run python -m music21.configure

After waiting a few moments to load modules, the Configuration Assistant begins.
It lists the notation programs it finds on your Mac. Type the number of your
favorite and press Return: outside of Jupyter, `music21` will open scores there.

Next you will be asked a number of
questions about working with `music21`. They concern whether music21 can access
the Internet, and whether you are willing to comply with the license for
use of music21 and the included corpus of scores.  You have to accept the
license to continue (we need to retain some rights you know!), but you
don't have to give us access to the Internet.


Start Jupyter
---------------------------------------

Still in the `m21play` folder, type::

    uv run jupyter notebook

Your web browser opens with a list of the files in your folder. Choose
"New", then "Notebook", and pick the Python kernel if asked. In the first box
(a "cell"), type::

    from music21 import *
    n = note.Note('A4')
    n.pitch.frequency

and press Shift-Return. You should see `440.0`: `music21` is working. Now try
`n.show()` in the next cell to see the note as notation.

When you're done, close the browser tab and press Control-C in Terminal.


Coming back later
---------------------------------------

Open Terminal and type::

    cd ~/m21play
    uv run jupyter notebook

To get the newest version of `music21`, type this in the folder (not the jupyter notebook)::

    uv add --upgrade music21

Other packages go in the same way; for instance, `uv add matplotlib` for
`music21`'s graphs.

If you'd rather use Python without Jupyter, `uv run python` in the folder
starts it with `music21` ready to import.

If you already have your own Python setup (a virtual environment, conda, and so on),
`pip install music21` there works too.


After Installation
-------------------------------

After a successful installation, you may proceed to :ref:`Notes <usersGuide_02_notes>` to
begin using music21.


Installation Help
-------------------------------

If you have followed all the instructions and still encounter problems, start over from scratch
and try it again very carefully.  If you still have problems ask an AI agent (most know
music21 pretty well) or lean on humans and contact the `music21` group and it's a friendly
group with users always happy to help:

https://groups.google.com/g/music21list
