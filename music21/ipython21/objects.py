# -*- coding: utf-8 -*-
import os


_DOC_IGNORE_MODULE_OR_PACKAGE = True


class IPythonPNGObject:
    '''
    Given a filepath to a PNG file, have one method to read it and delete the
    file.  This class may be removed, renamed, or otherwise altered in v8 --
    it no longer has anything special to PNGs.
    '''
    def __init__(self, fp=None):
        self.fp = fp

    def getData(self):
        fp = self.fp
        with open(fp, 'rb') as f:
            data = f.read()
        os.remove(fp)
        return data
