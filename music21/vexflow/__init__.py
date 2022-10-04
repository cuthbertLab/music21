# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         vexflow/__init__.py
# Purpose:      music21 classes for converting music21 objects to vexflow
#
# Authors:      Christopher Reyes
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2012-14 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

__all__ = ['toMusic21j', 'fromObject']

from music21.vexflow import toMusic21j
from music21.vexflow.toMusic21j import fromObject

