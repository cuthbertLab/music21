# -*- coding: utf-8 -*-
import os


_DOC_IGNORE_MODULE_OR_PACKAGE = True


class IPythonPNGObject:
    '''
    we need to define a certain type of object that when encountered we
    can handle. see ipExtension.
    '''
    def __init__(self, fp=None):
        self.fp = fp

    def getData(self):
        fp = self.fp
        with open(fp, 'rb') as f:
            data = f.read()
        os.remove(fp)
        return data
