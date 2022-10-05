# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         corpus/work.py
# Purpose:      Manage one work
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
This is a lightweight module that stores information about individual corpus works.
'''
from __future__ import annotations

from collections import namedtuple, OrderedDict
import os

from music21 import common
from music21 import prebase

# -----------------------------------------------------------------------------
CorpusWork = namedtuple('CorpusWork', ['title', 'files', 'virtual'])
CorpusFile = namedtuple('CorpusFile', ['path', 'title', 'filename', 'format', 'ext'])
# VirtualCorpusFile = namedtuple('VirtualCorpusFile', ['path', 'title', 'url', 'format'])


class DirectoryInformation(prebase.ProtoM21Object):
    '''
    returns information about a directory in a Corpus.  Called from corpus.corpora.Corpus

    only tested with CoreCorpus so far.
    '''

    def __init__(self, dirName='', dirTitle='', isComposer=True, corpusObject=None):
        self.directoryName = dirName
        self.directoryTitle = dirTitle
        self.isComposer = isComposer
        self.works = OrderedDict()

        self.corpusObject = corpusObject

        self.findWorks()

    def _reprInternal(self):
        return str(self.directoryName)

    def findWorks(self):
        '''
        Populate other information about the directory such as
        files and filenames.

        >>> di = corpus.work.DirectoryInformation('schoenberg',
        ...             corpusObject=corpus.corpora.CoreCorpus())
        >>> di.findWorks()
        OrderedDict([('opus19', CorpusWork(title='Opus 19',
                                    files=[CorpusFile(path='schoenberg...opus19...movement2.mxl',
                                                        title='Movement 2',
                                                        filename='movement2.mxl',
                                                        format='musicxml',
                                                        ext='.mxl'),
                                            CorpusFile(path='schoenberg...opus19...movement6.mxl',
                                                        title='Movement 6',
                                                        filename='movement6.mxl',
                                                        format='musicxml',
                                                        ext='.mxl')],
                                    virtual=False))])
        '''
        self.works.clear()
        works = self.corpusObject.getComposer(self.directoryName)
        # TODO: this should be renamed since not all are composers
        for path in works:
            # split by the composer dir to get relative path
            # environLocal.printDebug(['dir composer', composerDirectory, path])
            junk, fileStub = str(path).split(self.directoryName)
            if fileStub.startswith(os.sep):
                fileStub = fileStub[len(os.sep):]
            # break into file components
            fileComponents = fileStub.split(os.sep)
            # the first is either a directory for containing components
            # or a top-level name
            m21Format, ext = common.findFormatExtFile(fileComponents[-1])
            if ext is None:
                # environLocal.printDebug([
                #    'file that does not seem to have an extension',
                #    ext, path])
                continue
            # if not a file w/ ext, we will get None for format
            if m21Format is None:
                workStub = fileComponents[0]
            else:  # remove the extension
                workStub = fileComponents[0].replace(ext, '')
            # create list location if not already added
            if workStub not in self.works:
                title = common.spaceCamelCase(workStub).title()
                self.works[workStub] = CorpusWork(title=title, files=[], virtual=False)
            # last component is the name
            m21Format, ext = common.findFormatExtFile(fileComponents[-1])
            # all path parts after corpus
            corpusPath = os.path.join(str(self.directoryName), fileStub)
            corpusFileName = fileComponents[-1]  # all after
            title = None
            # this works but takes a long time!
            # title = converter.parse(path).metadata.title
            # TODO: get from RichMetadataBundle!
            if title is None:
                title = common.spaceCamelCase(
                    fileComponents[-1].replace(ext, ''))
                title = title.title()
            fileTuple = CorpusFile(path=corpusPath, title=title, filename=corpusFileName,
                                   format=m21Format, ext=ext)
            self.works[workStub].files.append(fileTuple)
            # add this path
        return self.works

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest()
