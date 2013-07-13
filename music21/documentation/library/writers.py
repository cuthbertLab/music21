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

import abc
import json
import os


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

    def write(self, filePath, rst): #
        '''
        Write ``lines`` to ``filePath``, only overwriting an existing file
        if the content differs.
        '''
        shouldWrite = True
        if os.path.exists(filePath):
            with open(filePath, 'r') as f:
                oldRst = f.read()
            if rst == oldRst:
                shouldWrite = False
        if shouldWrite:
            with open(filePath, 'w') as f:
                f.write(rst)
            print 'WROTE   {0}'.format(os.path.relpath(filePath))
        else:
            print 'SKIPPED {0}'.format(os.path.relpath(filePath))


class ModuleReferenceReSTWriter(ReSTWriter):
    '''
    Writes module reference ReST files, and their index ReST file.
    '''

    ### SPECIAL METHODS ###
    
    def __call__(self):
        from music21 import documentation
        moduleReferenceDirectoryPath = os.path.join(
            documentation.__path__[0],
            'source',
            'moduleReference',
            )
        referenceNames = []
        for module in [x for x in documentation.ModuleIterator()]:
            moduleDocumenter = documentation.ModuleDocumenter(module)
            rst = '\n'.join(moduleDocumenter())
            referenceName = moduleDocumenter.referenceName
            referenceNames.append(referenceName)
            fileName = '{0}.rst'.format(referenceName)
            filePath = os.path.join(
                moduleReferenceDirectoryPath,
                fileName,
                )
            self.write(filePath, rst)
        
        lines = []
        lines.append('.. moduleReference:')
        lines.append('')
        lines.append('Module Reference')
        lines.append('================')
        lines.append('')
        lines.append('.. toctree::')
        lines.append('   :maxdepth: 1')
        lines.append('')
        for referenceName in sorted(referenceNames):
            lines.append('   {0}'.format(referenceName))
        rst = '\n'.join(lines)
        indexFilePath = os.path.join(
            moduleReferenceDirectoryPath,
            'index.rst',
            )
        self.write(indexFilePath, rst)


class CorpusReferenceReSTWriter(ReSTWriter):
    '''
    Write the corpus reference ReST file.
    '''

    ### SPECIAL METHODS ###

    def __call__(self):
        from music21 import documentation
        systemReferenceDirectoryPath = os.path.join(
            documentation.__path__[0],
            'source',
            'systemReference',
            )
        corpusReferenceFilePath = os.path.join(
            systemReferenceDirectoryPath,
            'referenceCorpus.rst',
            )
        lines = documentation.CorpusDocumenter()()
        rst = '\n'.join(lines)
        self.write(corpusReferenceFilePath, rst)


class IPythonNotebookReSTWriter(ReSTWriter):
    '''
    Converts IPython notebooks into ReST, and handles their associated image
    files.

    This class wraps the 3rd-party ``nbconvert`` Python script.
    '''

    ### SPECIAL METHODS ###

    def __call__(self):
        pass
        from music21 import documentation
        ipythonNotebookFilePaths = [x for x in
            documentation.IPythonNotebookIterator()()]
        for ipythonNotebookFilePath in ipythonNotebookFilePaths:
            with open(ipythonNotebookFilePath, 'r') as f:
                contents = f.read()
                contentsAsJson = json.loads(contents)
            directoryPath, sep, baseName = ipythonNotebookFilePath.rpartition(
                os.path.sep)
            baseNameWithoutExtension = os.path.splitext(baseName)[0]
            imageFilesDirectoryPath = os.path.join(
                directoryPath,
                '{0}_files'.format(baseNameWithoutExtension),
                )
            rstFilePath = os.path.join(
                directoryPath,
                '{0}.rst'.format(baseNameWithoutExtension),
                )
            lines, imageData = documentation.IPythonNotebookDocumenter(
                contentsAsJson)()
            rst = '\n'.join(lines)
            self.write(rstFilePath, rst)
            if not imageData:
                continue
            if not os.path.exists(imageFilesDirectoryPath):
                os.mkdir(imageFilesDirectoryPath)
            for imageFileName, imageFileData in imageData.iteritems():
                imageFilePath = os.path.join(
                    imageFilesDirectoryPath,
                    imageFileName,
                    )
                shouldOverwriteImage = True
                with open(imageFilePath, 'rb') as f:
                    oldImageFileData = f.read()
                    if oldImageFileData == imageFileData:
                        shouldOverwriteImage = False
                if shouldOverwriteImage:
                    with open(imageFilePath, 'wb') as f:
                        f.write(imageFileData)
            

if __name__ == '__main__':
    import music21
    music21.mainTest()

