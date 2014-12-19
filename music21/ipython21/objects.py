# -*- coding: utf-8 -*-
_DOC_IGNORE_MODULE_OR_PACKAGE = True


class IPythonPNGObject(object):
    '''
    we need to define a certain type of object that when encountered we
    can handle. see ipExtension.
    '''
    def __init__(self, fp=None):
        self.fp = fp
