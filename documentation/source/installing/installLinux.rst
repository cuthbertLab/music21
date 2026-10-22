.. _installLinux:


Installing `music21` on GNU/Linux and other operating systems
=============================================================

GNU/Linux, FreeBSD, etc. generally work on `music21`.  Many people, including
all of the major developers of `music21` run it on various deployed GNU/Linux,
Unix, AWS-Unix, Android, iOS, etc. systems throughout the world.
However, no systems except recent Mac and Windows OSes are officially supported.

By choosing to use Unix-like systems you should be an advanced user on your
OS, able to deal with the issues of libraries, linkage, external files, etc.
specific to (and different on) each Unix-like system.  The music21list should not
be used for installation/configuration problems on
your operating system. Because of the number of different Unix variants, the list
maintainers will only entertain `music21`-specific problems that can also be
reproduced on Mac or Windows.

To reiterate: **GNU/Linux/etc. is not a system for which support
questions will be answered**. Ask an AI agent that knows more about your OS
(tell it which one you have, such as Ubuntu 24.04) to help you with the steps below.


Download `music21` 
----------------------------------------------

Download the newest version with uv, in a folder for your `music21` work
(see :ref:`installMac`; the uv install command there works here too)::

    uv init --bare
    uv add music21


Configure `music21`
----------------------------------------------
Configure music21 with:

    uv run python -m music21.configure

The configuration assistant does not ask for your MusicXML reader on these
systems.  `music21` looks for MuseScore at `/usr/bin/mscore3`; if yours is
somewhere else, set it in `uv run python`::

    from music21 import environment
    environment.set('musicxmlPath', '/usr/bin/mscore')
    environment.set('musescoreDirectPNGPath', '/usr/bin/mscore')

If you do not know about
filepaths and how to find them, you should probably not be using
GNU/Linux, FreeBSD, etc. with `music21`.

On most OSes you'll find your configuration file in ~/.music21rc, but
this is not guaranteed.


After Installation
-------------------------------

After a successful installation, you may proceed to
:ref:`Notes <usersGuide_02_notes>` to
begin using `music21`.


Learned Experience
------------------------------
Issues that people have reported **and solved** on non-Mac/Windows systems
include:

* **Android**: there is an issue with semaphores and multiprocessing in Android,
  this seems to be fixed with before importing `music21` running:
  `import _multiprocessing; _multiprocessing.sem_unlink = None`

(If you have other issues that you have solved, please file a PR to add it
to this section).


Still have problems?
-------------------------------

If you have followed all the instructions and still encounter problems, 
start over from scratch and try it again very carefully.  
If you still have problems ask an AI agent that knows about your operating system
or contact an expert in your operating system. Please do not bring Unix issues to
the mailing list or GitHub unless you're also arriving with solutions (that go
beyond problems created by boutique installations).
