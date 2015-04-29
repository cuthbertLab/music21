# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import abc  # for @abc.abstractmethod decorator: requires a function to be defined in subclasses
import os
import types

from music21 import common
from music21.ext import six

class Iterator(object):
    '''
    Abstract base class for documentation iterators.
    '''

    ### INITIALIZER ###

    def __init__(self, verbose=True):
        self.verbose = verbose

    ### SPECIAL METHODS ###

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError


class IPythonNotebookIterator(Iterator):
    '''
    Iterates over music21's documentation directory, yielding .ipynb files.
    '''

    ### SPECIAL METHODS ###

    def __iter__(self):
        import music21
        rootFilesystemPath = music21.__path__[0]
        documentationPath = os.path.join(
            rootFilesystemPath,
            'documentation',
            'source',
            )
        for pathParts in os.walk(documentationPath):
            directoryPath, fileNames = pathParts[0], pathParts[2]
            for fileName in fileNames:
                if fileName.endswith('.ipynb'):
                    filePath = os.path.join(
                        directoryPath,
                        fileName,
                        )
                    yield filePath


class ModuleIterator(Iterator):
    '''
    Iterates over music21's package system, yielding module objects:

    ::

        >>> iterator = documentation.ModuleIterator(verbose=False)
        >>> modules = [x for x in iterator]
        >>> for module in sorted(modules, key=lambda x: x.__name__)[:8]:
        ...     module.__name__
        ...
        'music21.__init__'
        'music21.abcFormat.__init__'
        'music21.abcFormat.translate'
        'music21.analysis.__init__'
        'music21.analysis.correlate'
        'music21.analysis.discrete'
        'music21.analysis.floatingKey'
        'music21.analysis.metrical'

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
        'base-archive.py',
        'exceldiff.py',
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
            if '__init__.py' in fileNames:
                strippedPath = directoryPath.partition(rootFilesystemPath)[2]
                pathParts = [x for x in strippedPath.split(os.path.sep) if x]
                pathParts.insert(0, 'music21')
                packagesystemPath = '.'.join(pathParts)
                try:
                    module = __import__(packagesystemPath, fromlist=['*'])
                    if getattr(module, '_DOC_IGNORE_MODULE_OR_PACKAGE', False):
                        # Skip examining any other file or directory below
                        # this directory.
                        if self.verbose:
                            print('\tIGNORED {0}/*'.format(
                                common.relativepath(directoryPath)))
                        directoryNames[:] = []
                        continue
                except ImportError:
                    pass
            for fileName in fileNames:
                if fileName in self._ignoredFileNames:
                    continue
                if not fileName.endswith('.py'):
                    continue
                if fileName.startswith('_') and not fileName.startswith('__'):
                    continue
                filePath = os.path.join(directoryPath, fileName)
                strippedPath = filePath.partition(rootFilesystemPath)[2]
                pathParts = [x for x in os.path.splitext(
                    strippedPath)[0].split(os.path.sep)[1:] if x]
                pathParts = ['music21'] + pathParts
                packagesystemPath = '.'.join(pathParts)
                try:
                    module = __import__(packagesystemPath, fromlist=['*'])
                    if getattr(module, '_DOC_IGNORE_MODULE_OR_PACKAGE',
                        False):
                        if self.verbose:
                            print('\tIGNORED {0}'.format(
                                common.relativepath(filePath)))
                        continue
                    yield module
                except ImportError:
                    pass
        raise StopIteration


class CodebaseIterator(Iterator):
    '''
    Iterate over music21's package system, yielding all classes and functions.
    '''

    ### SPECIAL METHODS ###

    def __iter__(self):
        for module in ModuleIterator(verbose=self.verbose):
            for name in dir(module):
                if name.startswith('_'):
                    continue
                named = getattr(module, name)
                validTypes = six.class_types + (types.FunctionType,)
                if isinstance(named, validTypes) and \
                    named.__module__ == module.__name__:
                    yield named
        raise StopIteration


class ClassIterator(Iterator):
    '''
    Iterates over music21's package system, yielding all classes discovered:

    ::

        >>> iterator = documentation.ClassIterator(verbose=False)
        >>> classes = sorted([x for x in iterator],
        ...     key=lambda x: (x.__module__, x.__name__))
        >>> for cls in classes[:10]:
        ...     cls
        ...
        <class 'music21.abcFormat.__init__.ABCAccent'>
        <class 'music21.abcFormat.__init__.ABCBar'>
        <class 'music21.abcFormat.__init__.ABCBrokenRhythmMarker'>
        <class 'music21.abcFormat.__init__.ABCChord'>
        <class 'music21.abcFormat.__init__.ABCCrescStart'>
        <class 'music21.abcFormat.__init__.ABCDimStart'>
        <class 'music21.abcFormat.__init__.ABCDownbow'>
        <class 'music21.abcFormat.__init__.ABCFile'>
        <class 'music21.abcFormat.__init__.ABCFileException'>
        <class 'music21.abcFormat.__init__.ABCGraceStart'>

    '''

    ### SPECIAL METHODS ###

    def __iter__(self):
        for x in CodebaseIterator(verbose=self.verbose):
            if isinstance(x, six.class_types):
                yield x
        raise StopIteration


class FunctionIterator(Iterator):
    '''
    Iterates over music21's package system, yielding all functions discovered:

    ::

        >>> from music21 import documentation
        >>> iterator = documentation.FunctionIterator(verbose=False)
        >>> functions = [x for x in iterator]
        >>> for function in sorted(functions,
        ...     key=lambda x: (x.__module__, x.__name__))[:10]:
        ...     function.__module__, function.__name__
        ...
        ('music21.abcFormat.__init__', 'mergeLeadingMetaData')
        ('music21.abcFormat.translate', 'abcToStreamOpus')
        ('music21.abcFormat.translate', 'abcToStreamPart')
        ('music21.abcFormat.translate', 'abcToStreamScore')
        ('music21.abcFormat.translate', 'parseTokens')
        ('music21.abcFormat.translate', 'reBar')
        ('music21.analysis.discrete', 'analyzeStream')
        ('music21.analysis.floatingKey', 'divide')
        ('music21.analysis.metrical', 'labelBeatDepth')
        ('music21.analysis.metrical', 'thomassenMelodicAccent')

    '''

    ### SPECIAL METHODS ###

    def __iter__(self):
        for x in CodebaseIterator(verbose=self.verbose):
            if isinstance(x, types.FunctionType):
                yield x
        raise StopIteration


if __name__ == '__main__':
    import music21
    music21.mainTest()

