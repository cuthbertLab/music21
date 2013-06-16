.. _tutorialFinaleMac:




Tutorial: Setting up Finale on Mac
=============================================================

Most of the features of music21 work the same no matter whether 
you're working on a Mac or PC, use Finale or Lilypond, make
graphics or just analyze scores.  But some features of music21
require external applications to do their job, and music21 needs
to find these applications.  Often the software can find them
itself, but sometimes it needs a little help.  The most common
scenario is that you are a Mac user who has Finale installed on 
your system but music21 isn't finding it.  Here's how you can 
help it along:

Start python by typing 'python' in the Terminal app.  Then
type the following commands to create a user environment
for music21 and change the musicxml reader path.

>>> from music21 import *
>>> us = environment.UserSettings()
>>> us.create()  # doctest: +SKIP
>>> us['musicxmlPath']  # doctest: +SKIP
'/Applications/Finale Reader.app'
>>> us['musicxmlPath'] = '/Applications/Finale 2009/Finale 2009.app' # doctest: +SKIP


if you discover that you made a mistake in the filename, 
do what you did above, but you can skip the us.create() step (as
well as the next step, which just lets you see what you've currently
done)





Further Details
---------------------------------------

For further details on setting up your Environment, see:
:ref:`environment`.

For complete instructions on installing music21 on the Mac, see:
:ref:`installMac`.