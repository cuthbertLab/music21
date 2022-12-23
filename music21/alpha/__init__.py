# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         alpha/__init__.py
# Purpose:      music21 modules not fully ready for prime-time
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009-2015 Michael Scott Asato Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Over time music21 has gained a lot of features that never became fully developed
or ready for prime time.  They're useful for some things, but the sheer number of
modules that have been added over time started to make the system feel bloated.

The alpha module/directory contains features that are useful for some things, but
not a core part of the system.  Some of these modules may require external
libraries that are obscure and not part of the recommended "additional music21
features" set. (For instance, alpha.chant requires Gregorio and LaTeX -- a daunting
requirement)

This directory is a compromise between removing the features altogether and
putting them in the main documentation.  Some of these features may "graduate"
to the main music21 module set.  Some may be moved to
https://github.com/cuthbertLab/music21-demos .  Some may stay here
indefinitely.

medren will probably reappear in another form in a directory called "medren" at some
point, along with chant and trecento.

When adding files here, update documentation.library.iterators
'''
from __future__ import annotations

__all__ = [
    # dirs
    'analysis',

    # files
]

from music21.alpha import analysis


