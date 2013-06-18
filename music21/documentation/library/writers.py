# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

import abc


class ReSTWriter(object):
    '''
    Abstract base class for ReST writers.
    '''

    ### CLASS VARIABLES ###

    __metaclass__ = abc.ABCMeta

    ### SPECIAL METHODS ###

    @abc.abstractmethod
    def __call__(self):
        raise NotImplemented

    ### PUBLIC METHODS ###

    def write(filePath, lines):
        '''
        Write ``lines`` to ``filePath``, only overwriting an existing file
        if the content differs.
        '''
        if os.path.exists(filePath):
            with open(filePath, 'r') as f:
                oldLines = filePath.read().splitlines()
            if lines != oldLines:
                with open(filePath, 'w') as f:
                    f.write('\n'.join(lines))
        else:
            with open(filePath, 'w') as f:
                f.write('\n'.join(lines))


class ModuleReferenceReSTWriter(ReSTWriter):
    '''
    Writes module reference ReST files, and their index ReST file.
    '''
    pass


class CorpusReferenceReSTWriter(ReSTWriter):
    '''
    Write the corpus reference ReST file.
    '''
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest()

