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


import abc
import os

from music21 import common
from music21 import converter

from music21 import environment
environLocal = environment.Environment(__file__)


#------------------------------------------------------------------------------


class Corpus(object):

    ### CLASS VARIABLES ###

    _allExtensions = (
        common.findInputExtension('abc') +
        common.findInputExtension('lily') +
        common.findInputExtension('midi') +
        common.findInputExtension('musicxml') +
        common.findInputExtension('musedata') +
        common.findInputExtension('humdrum') +
        common.findInputExtension('romantext') +
        common.findInputExtension('noteworthytext') +
        common.findInputExtension('noteworthy')
        )

    _metadataBundles = {
        'core': None,
        'local': None,
        'virtual': None,
        }

    _pathsCache = {}

    ### PRIVATE METHODS ###

    def _findPaths(self, rootDirectoryPath, fileExtensions):
        '''
        Given a root filePath file path, recursively search all contained paths
        for files in `rootFilePath` matching any of the file extensions in
        `fileExtensions`.

        The `fileExtensions` is a list of file file extensions.

        NB: we've tried optimizing with `fnmatch` but it does not save any
        time.
        '''
        from music21 import corpus
        matched = []
        rootDirectoryPath = unicode(rootDirectoryPath)
        for rootDirectory, directoryNames, filenames in os.walk(
            rootDirectoryPath):
            if '.svn' in directoryNames:
                directoryNames.remove('.svn')
            for filename in filenames:
                try:
                    if filename.startswith('.'):
                        continue
                except UnicodeDecodeError as error:
                    raise corpus.CorpusException(
                        'Incorrect filename in corpus path: {}: {!r}'.format(
                            filename, error))
                for extension in fileExtensions:
                    if filename.endswith(extension):
                        matched.append(os.path.join(rootDirectory, filename))
                        break
        return matched

    def _translateExtensions(
        self,
        fileExtensions=None,
        expandExtensions=True,
        ):
        '''
        Utility to get default extensions, or, optionally, expand extensions to
        all known formats.

        ::

            >>> from music21.corpus import corpora
            >>> coreCorpus = corpora.CoreCorpus()
            >>> for extension in coreCorpus._translateExtensions():
            ...     extension
            ...
            '.abc'
            '.ly'
            '.lily'
            '.mid'
            '.midi'
            '.xml'
            '.mxl'
            '.mx'
            '.md'
            '.musedata'
            '.zip'
            '.krn'
            '.rntxt'
            '.rntext'
            '.romantext'
            '.rtxt'
            '.nwctxt'
            '.nwc'

        ::

            >>> coreCorpus._translateExtensions('.mid', False)
            ['.mid']

        ::

            >>> coreCorpus._translateExtensions('.mid', True)
            ['.mid', '.midi']

        '''
        if not common.isListLike(fileExtensions):
            fileExtensions = [fileExtensions]
        if fileExtensions == [None]:
            fileExtensions = Corpus._allExtensions
        elif expandExtensions:
            expandedExtensions = []
            for extension in fileExtensions:
                expandedExtensions += common.findInputExtension(extension)
            return expandedExtensions
        return fileExtensions

    @staticmethod
    def _updateAllMetadataBundles():
        CoreCorpus().updateMetadataBundle()
        LocalCorpus().updateMetadataBundle()
        VirtualCorpus().updateMetadataBundle()

    ### PUBLIC METHODS ###

    @abc.abstractmethod
    def updateMetadataBundle(self):
        raise NotImplementedError

    @staticmethod
    def fromName(name):
        if name == 'core':
            return CoreCorpus()
        elif name == 'virtual':
            return VirtualCorpus()
        elif name == 'local':
            return LocalCorpus()
        return LocalCorpus(name)

    @abc.abstractmethod
    def getPaths(self):
        raise NotImplementedError

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
        if workName in (None, ''):
            raise corpus.CorpusException(
                'a work name must be provided as an argument')
        if not common.isListLike(fileExtensions):
            fileExtensions = [fileExtensions]
        workList = corpus.getWorkList(
            workName, movementNumber, fileExtensions)
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
                'Could not find a work that met this criterion: %s'.format(
                    workName))
        else:
            filePath = workList[0]
        streamObject = converter.parse(
            filePath,
            forceSource=forceSource,
            number=number,
            )
        corpus._addCorpusFilepath(streamObject, filePath)
        return streamObject

    @staticmethod
    def search(
        query,
        field=None,
        domain=('core', 'virtual', 'local'),
        fileExtensions=None,
        ):
        '''
        Search all stored metadata and return a list of file paths; to return a
        list of parsed Streams, use `searchParse()`.

        The `domain` parameter can be used to specify one of three corpora:
        core (included with music21), virtual (defined in music21 but hosted
        online), and local (hosted on the user's system (not yet implemented)).

        This method uses stored metadata and thus, on first usage, will incur a
        performance penalty during metadata loading.
        '''
        Corpus._updateAllMetadataBundles()
        searchResults = []
        if domain is None:
            domain = ('core', 'virtual', 'local')
        for name in domain:
            if name in Corpus._metadataBundles:
                searchResults += Corpus._metadataBundles[name].search(
                    query, field, fileExtensions)
        return searchResults

    ### PUBLIC PROPERTIES ###

    @abc.abstractproperty
    def metadataBundle(self):
        raise NotImplementedError



#------------------------------------------------------------------------------


class CoreCorpus(Corpus):

    ### CLASS VARIABLES ###

    _composers = (
        ('airdsAirs', 'Aird\'s Airs'),
        ('bach', 'Johann Sebastian Bach'),
        ('beethoven', 'Ludwig van Beethoven'),
        ('cpebach', 'C.P.E. Bach'),
        ('ciconia', 'Johannes Ciconia'),
        ('essenFolksong', 'Essen Folksong Collection'),
        ('handel', 'George Frideric Handel'),
        ('haydn', 'Joseph Haydn'),
        ('josquin', 'Josquin des Prez'),
        ('luca', 'D. Luca'),
        ('miscFolk', "Miscellaneous Folk"),
        ('monteverdi', "Claudio Monteverdi"),
        ('mozart', 'Wolfgang Amadeus Mozart'),
        ('oneills1850', 'Oneill\'s 1850'),
        ('ryansMammoth', 'Ryan\'s Mammoth Collection'),
        ('schoenberg', 'Arnold Schoenberg'),
        ('schumann', 'Robert Schumann'),
        )

    _noCorpus = False

    ### PUBLIC METHODS ###

    def getPaths(
        self,
        fileExtensions=None,
        expandExtensions=True,
        ):
        '''
        Get all paths in the core corpus that match a known extension, or an
        extenion provided by an argument.

        If `expandExtensions` is True, a format for an extension, and related
        extensions, will replaced by all known input extensions.

        This is convenient when an input format might match for multiple
        extensions.

        ::

            >>> from music21.corpus import corpora
            >>> coreCorpus = corpora.CoreCorpus()
            >>> corpusFilePaths = coreCorpus.getPaths()
            >>> len(corpusFilePaths)
            3045

        ::

            >>> kernFilePaths = coreCorpus.getPaths('krn')
            >>> len(kernFilePaths) >= 500
            True

        ::

            >>> abcFilePaths = coreCorpus.getPaths('abc')
            >>> len(abcFilePaths) >= 100
            True

        '''
        fileExtensions = self._translateExtensions(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
            )
        cacheKey = ('core', tuple(fileExtensions))
        # not cached, fetch and reset
        if cacheKey not in Corpus._pathsCache:
            Corpus._pathsCache[cacheKey] = self._findPaths(
                common.getCorpusFilePath(),
                fileExtensions,
                )
        return Corpus._pathsCache[cacheKey]

    def updateMetadataBundle(self):
        from music21 import metadata
        domain = 'core'
        if Corpus._metadataBundles[domain] is None:
            metadataBundle = metadata.MetadataBundle(domain)
            metadataBundle.read()
            metadataBundle.validate()
            Corpus._metadataBundles[domain] = metadataBundle

    ### PUBLIC PROPERTIES ###

    @property
    def noCorpus(self):
        '''
        Return True or False if this is a `corpus` or `noCoprus` distribution.

        ::

            >>> from music21.corpus import corpora
            >>> corpora.CoreCorpus().noCorpus
            False

        '''
        if CoreCorpus._noCorpus is None:
            if self.getComposerDir('bach') is None:
                CoreCorpus._noCorpus = True
            else:
                CoreCorpus._noCorpus = False
        return CoreCorpus._noCorpus


#------------------------------------------------------------------------------


class VirtualCorpus(Corpus):

    def getPaths(
        self,
        fileExtensions=None,
        expandExtensions=True,
        ):
        '''
        Get all paths in the virtual corpus that match a known extension.

        An extension of None will return all known extensions.

        ::

            >>> from music21.corpus import corpora
            >>> len(corpora.VirtualCorpus().getPaths()) > 6
            True

        '''
        from music21 import corpus
        fileExtensions = self._translateExtensions(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
            )
        paths = []
        for obj in corpus.VIRTUAL:
            if obj.corpusPath is not None:
                for fileExtension in fileExtensions:
                    results = obj.getUrlByExt(fileExtension)
                    for result in results:
                        if result not in paths:
                            paths.append(result)
        return paths

    def updateMetadataBundle(self):
        from music21 import metadata
        domain = 'virtual'
        if Corpus._metadataBundles[domain] is None:
            metadataBundle = metadata.MetadataBundle(domain)
            metadataBundle.read()
            metadataBundle.validate()
            Corpus._metadataBundles[domain] = metadataBundle

#------------------------------------------------------------------------------


class LocalCorpus(Corpus):

    ### CLASS VARIABLES ###

    _temporaryLocalPaths = []

    ### PUBLIC METHODS ###

    def getPaths(
        self,
        fileExtensions=None,
        expandExtensions=True,
        ):
        '''
        Access files in additional directories supplied by the user and defined
        in environment settings in the 'localCorpusSettings' list.

        If additional paths are added on a per-session basis with the
        :func:`~music21.corpus.addPath` function, these paths are also returned
        with this method.
        '''
        fileExtensions = self._translateExtensions(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
            )
        cacheKey = ('local', tuple(fileExtensions))
        # not cached, fetch and reset
        if cacheKey not in Corpus._pathsCache:
            # check paths before trying to search
            candidatePaths = environLocal['localCorpusSettings']
            validPaths = []
            for filePath in candidatePaths + LocalCorpus._temporaryLocalPaths:
                if not os.path.isdir(filePath):
                    environLocal.warn(
                        'invalid path set as localCorpusSetting: {}'.format(
                            filePath))
                else:
                    validPaths.append(filePath)
            # append successive matches into one list
            matched = []
            for filePath in validPaths:
                #environLocal.printDebug(['finding paths in:', filePath])
                matched += self._findPaths(filePath, fileExtensions)
            Corpus._pathsCache[cacheKey] = matched
        return Corpus._pathsCache[cacheKey]

    def updateMetadataBundle(self):
        from music21 import metadata
        domain = 'local'
        if Corpus._metadataBundles[domain] is None:
            metadataBundle = metadata.MetadataBundle(domain)
            metadataBundle.read()
            metadataBundle.validate()
            Corpus._metadataBundles[domain] = metadataBundle

#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
