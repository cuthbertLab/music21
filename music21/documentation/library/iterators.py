# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

import os
import types


class ModuleIterator(object):
    '''
    Iterates over music21's packagesystem, yielding module objects:

    ::

        >>> iterator = documentation.ModuleIterator()
        >>> modules = [x for x in iterator]
        >>> for module in modules[:10]:
        ...     module.__name__
        ...
        'music21.articulations'
        'music21.bar'
        'music21.base'
        'music21.beam'
        'music21.chant'
        'music21.chord'
        'music21.chordTables'
        'music21.classCache'
        'music21.clef'
        'music21.common'

    '''

    ### CLASS VARIABLES ###

    _ignoredDirectoryNames = (
        'archive',
        'demos',
        'doc',
        'ext',
        'server',
        'source',
        )

    _ignoredFileNames = (
        'exceldiff.py',
        'testFiles.py',
        )

    ### SPECIAL METHODS ###

    def __iter__(self):
        import music21
        rootFilesystemPath = music21.__path__[0]
        for directoryPath, directoryNames, fileNames in os.walk(
            rootFilesystemPath): 
            directoryNamesToRemove = []
            for directoryName in directoryNames:
                if directoryName in self._ignoredDirectoryNames:
                    directoryNamesToRemove.append(directoryName)
            for directoryName in directoryNamesToRemove:
                directoryNames.remove(directoryName)
            for fileName in fileNames:
                if fileName not in self._ignoredFileNames and \
                    not fileName.startswith('_') and \
                    fileName.endswith('.py'):
                    filePath = os.path.join(directoryPath, fileName)
                    strippedPath = filePath.partition(rootFilesystemPath)[2]
                    pathParts = os.path.splitext(strippedPath)[0].split(
                        os.path.sep)[1:]
                    pathParts = ['music21'] + pathParts
                    packagesystemPath = '.'.join(pathParts)
                    try:
                        module = __import__(packagesystemPath, fromlist=['*'])
                        yield module
                    except:
                        pass
        raise StopIteration


class CodebaseIterator(object):
    '''
    Iterate over music21's packagesystem, yielding all classes and functions.
    '''

    def __iter__(self):
        for module in ModuleIterator():
            for name in dir(module):
                if name.startswith('_'):
                    continue
                named = getattr(module, name)
                validTypes = (type, types.ClassType, types.FunctionType)
                if isinstance(named, validTypes) and \
                    named.__module__ == module.__name__:
                    yield named
        raise StopIteration


class ClassIterator(object):
    '''
    Iterates over music21's packagesystem, yielding all classes discovered:

    ::

        >>> iterator = documentation.ClassIterator()
        >>> classes = [x for x in iterator]
        >>> for cls in classes[:10]:
        ...     cls
        ... 
        <class 'music21.articulations.Accent'>
        <class 'music21.articulations.Articulation'>
        <class 'music21.articulations.ArticulationException'>
        <class 'music21.articulations.Bowing'>
        <class 'music21.articulations.BrassIndication'>
        <class 'music21.articulations.BreathMark'>
        <class 'music21.articulations.Caesura'>
        <class 'music21.articulations.DetachedLegato'>
        <class 'music21.articulations.Doit'>
        <class 'music21.articulations.DoubleTongue'>

    '''

    ### SPECIAL METHODS ###

    def __iter__(self):
        for x in CodebaseIterator():
            if isinstance(x, (type, types.ClassType)):
                yield x
        raise StopIteration


class FunctionIterator(object):
    '''
    Iterates over music21's packagesystem, yielding all functions discovered:

    ::

        >>> iterator = documentation.FunctionIterator()
        >>> functions = [x for x in iterator]
        >>> for function in functions[:10]:
        ...     function.__module__, function.__name__
        ... 
        ('music21.bar', 'standardizeBarStyle')
        ('music21.bar', 'styleToMusicXMLBarStyle')
        ('music21.base', 'mainTest')
        ('music21.chant', 'fromStream')
        ('music21.chord', 'fromForteClass')
        ('music21.chord', 'fromIntervalVector')
        ('music21.chordTables', 'addressToCommonNames')
        ('music21.chordTables', 'addressToForteName')
        ('music21.chordTables', 'addressToIntervalVector')
        ('music21.chordTables', 'addressToNormalForm')

    '''
    
    ### SPECIAL METHODS ###

    def __iter__(self):
        for x in CodebaseIterator():
            if isinstance(x, types.FunctionType):
                yield x
        raise StopIteration


if __name__ == '__main__':
    import music21
    music21.mainTest()

