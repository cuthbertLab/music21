# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         features/__init__.py
# Purpose:      Feature extractors
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

__all__ = ['base', 'outputFormats', 'jSymbolic', 'native']

# __init__ can wildcard import base; it's how it is designed.
from music21.features.base import *  # pylint: disable=wildcard-import

from music21.features import base
from music21.features import outputFormats

from music21.features import jSymbolic
from music21.features import native

# pylint: disable=redefined-builtin
__doc__ = base.__doc__

