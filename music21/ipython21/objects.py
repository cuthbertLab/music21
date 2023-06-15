# -*- coding: utf-8 -*-
'''
This module is no longer needed in v9 and just kept for historical reasons.
'''
from __future__ import annotations

# import os

_DOC_IGNORE_MODULE_OR_PACKAGE = True

# class IPythonPNGObject:
#     '''
#     Given a filepath to a PNG file, have one method to read it and delete the
#     file.  This class may be removed, renamed, or otherwise altered in v8 or later
#     as it no longer has anything special to PNGs.
#     '''
#     def __init__(self, fp=None):
#         self.fp = fp
#
#     def getData(self, remove=True):
#         fp = self.fp
#         with open(fp, 'rb') as f:
#             data = f.read()
#         if remove:
#             os.remove(fp)
#         return data
