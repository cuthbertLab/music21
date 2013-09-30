# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         corpora.py
# Purpose:      corpus classes
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------


import os

from music21 import common
from music21 import converter

from music21 import environment
environLocal = environment.Environment(__file__)


#------------------------------------------------------------------------------


class Corpus(object):

    @staticmethod
    def parse(
        workName,
        movementNumber=None,
        number=None,
        fileExtensions=None,
        forceSource=False,
        ):
        '''
        The most important method call for corpus.

        Similar to the :meth:`~music21.converter.parse` method of converter
        (which takes in a filepath on the local hard drive), this method
        searches the corpus (including the virtual corpus) for a work fitting
        the workName description and returns a :class:`music21.stream.Stream`.

        If `movementNumber` is defined, and a movement is included in the
        corpus, that movement will be returned.

        If `number` is defined, and the work is a collection with multiple
        components, that work number will be returned.  For instance, some of
        our ABC documents contain dozens of folk songs within a single file.

        Advanced: if `forceSource` is True, the original file will always be
        loaded freshly and pickled (e.g., pre-parsed) files will be ignored.
        This should not be needed if the file has been changed, since the
        filetime of the file and the filetime of the pickled version are
        compared.  But it might be needed if the music21 parsing routine has
        changed.

        Example, get a chorale by Bach.  Note that the source type does not
        need to be specified, nor does the name Bach even (since it's the only
        piece with the title BWV 66.6)

        ::

            >>> from music21 import corpus

        ::

            >>> bachChorale = corpus.parse('bwv66.6')
            >>> len(bachChorale.parts)
            4

        After parsing, the file path within the corpus is stored as
        `.corpusFilePath`

        ::

            >>> bachChorale.corpusFilepath
            u'bach/bwv66.6.mxl'

        '''
        from music21 import corpus

        if workName in [None, '']:
            raise corpus.CorpusException(
                'a work name must be provided as an argument')

        if not common.isListLike(fileExtensions):
            fileExtensions = [fileExtensions]

        workList = corpus.getWorkList(
            workName, movementNumber, fileExtensions)
        #environLocal.printDebug(['result of getWorkList()', post])
        if not workList:
            if common.isListLike(workName):
                workName = os.path.sep.join(workName)
            if workName.endswith(".xml"):
                # might be compressed MXL file
                newWorkName = os.path.splitext(workName)[0] + ".mxl"
                try:
                    return Corpus.parse(
                        newWorkName,
                        movementNumber,
                        number,
                        fileExtensions,
                        forceSource,
                        )
                except corpus.CorpusException:
                    # avoids having the name come back with .mxl instead of
                    # .xmlrle
                    raise corpus.CorpusException(
                        'Could not find an xml or mxl work that met this '
                        'criterion: {0}'.format(workName))

            workList = corpus.getVirtualWorkList(
                workName,
                movementNumber,
                fileExtensions,
                )

        if len(workList) == 1:
            filePath = workList[0]
        elif not len(workList):
            raise corpus.CorpusException(
                "Could not find a work that met this criterion: %s" % workName)
        else:
            filePath = workList[0]
        streamObject = converter.parse(
            filePath,
            forceSource=forceSource,
            number=number,
            )
        corpus._addCorpusFilepath(streamObject, filePath)
        return streamObject


class CoreCorpus(Corpus):
    pass


class VirtualCorpus(Corpus):
    pass


class LocalCorpus(Corpus):
    pass


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
