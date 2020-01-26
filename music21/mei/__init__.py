# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         mei/__init__.py
# Purpose:      Initialize the MEI module
#
# Authors:      Christopher Antila
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The :mod:`mei` module provides functionality related to the interactions between music21 and MEI.

As of December 2014, we provide basic conversion from an MEI document to related music21 objects.
You may import an MEI file in the same way you import any other file to music21. You may also use
the :class:`music21.mei.MeiToM21Converter` directly for a complete file, or one of the functions,
like :func:`music21.mei.base.noteFromElement` to convert from a :class:`xml.etree.Element`
to the corresponding music21 object.

For more information, including about which elements and attributes are currently supported, please
refer to the :mod:`~music21.mei.base` module's documentation.
'''

# NOTE: I want to keep the 'mei' namespace relatively clean---we should only put here those classes
#       and functions that will be used regularly by other parts of music21, which is probably just
#       the MeiToM21Converter used by the MEI-specific SubConverter class. Everything else belongs
#       in its 'music21.mei.base.*' module, or similar.
from music21.mei.base import MeiToM21Converter
