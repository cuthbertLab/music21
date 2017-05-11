# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         corpora.py
# Purpose:      corpus classes
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2009-2012, 2014 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------


import abc
import os
from music21.ext import six

from music21 import common
from music21.corpus import virtual
from music21.corpus import work

from music21 import environment
environLocal = environment.Environment(__file__)

from music21.exceptions21 import CorpusException

#------------------------------------------------------------------------------

class Corpus(object):
    r'''
    Abstract base class of all corpora subclasses.
    '''

    ### CLASS VARIABLES ###

    __metaclass__ = abc.ABCMeta

    _allExtensions = (
        common.findInputExtension('abc') +
        common.findInputExtension('capella') +
        common.findInputExtension('midi') +
        common.findInputExtension('musicxml') +
        common.findInputExtension('musedata') +
        common.findInputExtension('humdrum') +
        common.findInputExtension('romantext') +
        common.findInputExtension('noteworthytext') +
        common.findInputExtension('noteworthy')
        )

    _pathsCache = {}

    _directoryInformation = () # a tuple of triples -- see coreCorpus
    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<{0}.{1}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            )

    ### PRIVATE METHODS ###

    def _removeNameFromCache(self, name):
        for key in Corpus._pathsCache.keys():
            if key[0] == name:
                del(Corpus._pathsCache[key])

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
        if six.PY2:
            rootDirectoryPath = unicode(rootDirectoryPath) # @UndefinedVariable
            
        for rootDirectory, directoryNames, filenames in os.walk(rootDirectoryPath):
            if '.svn' in directoryNames:
                directoryNames.remove('.svn')
            for filename in filenames:
                try:
                    if filename.startswith('.'):
                        continue
                except UnicodeDecodeError as error:
                    raise corpus.CorpusException(
                        'Incorrect filename in corpus path: {0}: {1!r}'.format(filename, error))
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

        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> for extension in coreCorpus._translateExtensions():
        ...     extension
        ...
        '.abc'
        '.capx'
        '.mid'
        '.midi'
        '.xml'
        '.mxl'
        '.mx'
        '.musicxml'
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

        >>> coreCorpus._translateExtensions('.mid', False)
        ['.mid']

        >>> coreCorpus._translateExtensions('.mid', True)
        ['.mid', '.midi']

        '''
        if not common.isListLike(fileExtensions):
            fileExtensions = [fileExtensions]
        if len(fileExtensions) == 1 and fileExtensions[0] is None:
            fileExtensions = Corpus._allExtensions
        elif expandExtensions:
            expandedExtensions = []
            for extension in fileExtensions:
                allInputExtensions = common.findInputExtension(extension)
                if allInputExtensions is None:
                    pass
                else:
                    expandedExtensions += allInputExtensions
            return expandedExtensions
        return fileExtensions

    ### PRIVATE PROPERTIES ###

    @abc.abstractproperty
    def cacheName(self):
        raise NotImplementedError

    ### PUBLIC METHODS ###
    @abc.abstractmethod
    def getPaths(self, fileExtensions=None, expandExtensions=True):
        r'''
        The paths of the files in a given corpus.
        '''
        raise NotImplementedError


    def getWorkList(
        self,
        workName,
        movementNumber=None,
        fileExtensions=None,
        ):
        r'''
        Search the corpus and return a list of filenames of works, always in a
        list.

        If no matches are found, an empty list is returned.

        >>> from music21 import corpus
        >>> coreCorpus = corpus.corpora.CoreCorpus()
        
        # returns 1 even though there is a '.mus' file, which cannot be read...
        
        >>> len(coreCorpus.getWorkList('cpebach/h186'))
        1
        >>> len(coreCorpus.getWorkList('cpebach/h186', None, '.xml'))
        1

        >>> len(coreCorpus.getWorkList('schumann_clara/opus17', 3))
        1
        >>> len(coreCorpus.getWorkList('schumann_clara/opus17', 2))
        0

        Make sure that 'verdi' just gets the single Verdi piece and not the
        Monteverdi pieces:

        >>> len(coreCorpus.getWorkList('verdi'))
        1

        '''
        if not common.isListLike(fileExtensions):
            fileExtensions = [fileExtensions]
        paths = self.getPaths(fileExtensions)
        results = []
        # permit workName to be a list of paths/branches
        if common.isIterable(workName):
            workName = os.path.sep.join(workName)
        workSlashes = workName.replace('/', os.path.sep)
        # find all matches for the work name
        # TODO: this should match by path component, not just
        # substring
        for path in paths:
            if workName.lower() in path.lower():
                results.append(path)
            elif workSlashes.lower() in path.lower():
                results.append(path)
        if results:
            # more than one matched...use more stringent criterion:
            # must have a slash before the name
            previousResults = results
            results = []
            longName = os.sep + workSlashes.lower()
            for path in previousResults:
                if longName in path.lower():
                    results.append(path)
            if not results:
                results = previousResults
        movementResults = []
        if movementNumber is not None and results:
            # store one ore more possible mappings of movement number
            movementStrList = []
            # see if this is a pair
            if common.isIterable(movementNumber):
                movementStrList.append(
                    ''.join(str(x) for x in movementNumber))
                movementStrList.append(
                    '-'.join(str(x) for x in movementNumber))
                movementStrList.append('movement' +
                    '-'.join(str(x) for x in movementNumber))
                movementStrList.append('movement' +
                    '-0'.join(str(x) for x in movementNumber))
            else:
                movementStrList += [
                    '0{0}'.format(movementNumber),
                    str(movementNumber),
                    'movement{0}'.format(movementNumber),
                    ]
            for filePath in sorted(results):
                filename = os.path.split(filePath)[1]
                if '.' in filename:
                    filenameWithoutExtension = os.path.splitext(filename)[0]
                else:
                    filenameWithoutExtension = None
                searchPartialMatch = True
                if filenameWithoutExtension is not None:
                    # look for direct matches first
                    for movementStr in movementStrList:
                        #if movementStr.lower() in filePath.lower():
                        if filenameWithoutExtension.lower() == movementStr.lower():
                            movementResults.append(filePath)
                            searchPartialMatch = False
                # if we have one direct match, all other matches must
                # be direct. this will match multiple files with different
                # file extensions
                if movementResults:
                    continue
                if searchPartialMatch:
                    for movementStr in movementStrList:
                        if filename.startswith(movementStr.lower()):
                            movementResults.append(filePath)
            if not movementResults:
                pass
        else:
            movementResults = results
        return sorted(set(movementResults))

    def search(self, 
               query, 
               field=None, 
               fileExtensions=None):
        r'''
        Search this corpus for metadata entries, returning a metadataBundle

        >>> corpus.corpora.CoreCorpus().search('3/4')
        <music21.metadata.bundles.MetadataBundle {1867 entries}>

        >>> corpus.corpora.CoreCorpus().search(
        ...      'bach',
        ...      field='composer',
        ...      )
        <music21.metadata.bundles.MetadataBundle {22 entries}>

        >>> predicate = lambda noteCount: noteCount < 20
        >>> corpus.corpora.CoreCorpus().search(
        ...     predicate,
        ...     field='noteCount',
        ...     )
        <music21.metadata.bundles.MetadataBundle {132 entries}>

        '''
        return self.metadataBundle.search(
            query,
            field=field,
            fileExtensions=fileExtensions,
            )

    ### PUBLIC PROPERTIES ###

    @property
    def directoryInformation(self):
        '''
        Returns a tuple of DirectoryInformation objects for a
        each directory in self._directoryInformation.
        
        >>> core = corpus.corpora.CoreCorpus()
        >>> diBrief = core.directoryInformation[0:4]
        >>> diBrief
        (<music21.corpus.work.DirectoryInformation airdsAirs>,
         <music21.corpus.work.DirectoryInformation bach>, 
         <music21.corpus.work.DirectoryInformation beethoven>, 
         <music21.corpus.work.DirectoryInformation ciconia>)
        >>> diBrief[3].directoryTitle
        'Johannes Ciconia'
        '''
        dirInfo = []
        for infoTriple in self._directoryInformation:
            dirInfo.append(work.DirectoryInformation(*infoTriple, corpusObject=self))
        return tuple(dirInfo)


    @abc.abstractproperty
    def name(self):
        r'''
        The name of a given corpus.
        '''
        raise NotImplementedError

    @property
    def metadataBundle(self):
        r'''
        The metadata bundle for a corpus:

        >>> from music21 import corpus
        >>> corpus.corpora.CoreCorpus().metadataBundle
        <music21.metadata.bundles.MetadataBundle 'core': {144... entries}>

        As a technical aside, the metadata bundle for a corpus is actually
        stored in corpus.manager, in order to cache most effectively over
        multiple calls. There might be good reasons to eventually move them
        to each Corpus object, so long as its cached across instances of the
        class.
        '''
        from music21.corpus import manager
        return manager.getMetadataBundleByCorpus(self)

    def getComposer(
        self,
        composerName,
        fileExtensions=None,
        ):
        '''
        Return all filenames in the corpus that match a composer's or a
        collection's name. An `fileExtensions`, if provided, defines which
        extensions are returned. An `fileExtensions` of None (default) returns
        all extensions.

        Note that xml and mxl are treated equivalently.

        >>> from music21 import corpus
        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> a = coreCorpus.getComposer('bach')
        >>> len(a) > 100
        True

        >>> a = coreCorpus.getComposer('bach', 'krn')
        >>> len(a) < 10
        True

        >>> a = coreCorpus.getComposer('bach', 'xml')
        >>> len(a) > 10
        True
        '''
        paths = self.getPaths(fileExtensions)
        results = []
        for path in paths:
            # iterate through path components; cannot match entire string
            # composer name may be at any level
            stubs = path.split(os.sep)
            for stub in stubs:
                # need to remove extension if found
                if composerName.lower() == stub.lower():
                    results.append(path)
                    break
                # get all but the last dot group
                # this is done for file names that function like composer names
                elif '.' in stub:
                    newStub = '.'.join(stub.split('.')[:-1]).lower()
                    if newStub == composerName.lower():
                        results.append(path)
                        break
        results.sort()
        return results

    def getWorkReferences(self):
        '''
        Return a data dictionary for all works in this corpus 
        Returns a list of corpus.work.DirectoryInformation objects, one
        for each directory. A 'works' dictionary for each composer
        provides references to dictionaries for all associated works.
    
        This is used in the generation of corpus documentation
    
        >>> workRefs = corpus.corpora.CoreCorpus().getWorkReferences()
        >>> workRefs[1:3]
        [<music21.corpus.work.DirectoryInformation bach>, 
         <music21.corpus.work.DirectoryInformation beethoven>]
                 '''
        results = [di for di in self.directoryInformation]
    
        return results

#------------------------------------------------------------------------------


class CoreCorpus(Corpus):
    r'''
    A model of the *core* corpus.

    >>> coreCorpus = corpus.corpora.CoreCorpus()

    '''

    ### CLASS VARIABLES ###

    _directoryInformation = ( # filepath, composer/collection name, isComposer
        ('airdsAirs', 'Aird\'s Airs', False),
        ('bach', 'Johann Sebastian Bach', True),
        ('beethoven', 'Ludwig van Beethoven', True),
        ('ciconia', 'Johannes Ciconia', True),
        ('corelli', 'Arcangelo Corelli', True),
        ('cpebach', 'C.P.E. Bach', True),
        ('demos', 'Demonstration Files', False),
        ('essenFolksong', 'Essen Folksong Collection', False),
        ('handel', 'George Frideric Handel', True),
        ('haydn', 'Joseph Haydn', True),
        ('josquin', 'Josquin des Prez', True),
        ('leadSheet', 'Leadsheet demos', False),
        ('luca', 'D. Luca', False),
        ('miscFolk', "Miscellaneous Folk", False),
        ('monteverdi', "Claudio Monteverdi", True),
        ('mozart', 'Wolfgang Amadeus Mozart', True),
        ('oneills1850', 'Oneill\'s 1850 Collection', False),
        ('palestrina', 'Giovanni Palestrina', True),
        ('ryansMammoth', 'Ryan\'s Mammoth Collection', False),
        ('schoenberg', 'Arnold Schoenberg', True),
        ('schumann', 'Robert Schumann', True),
        ('schumann_clara', 'Clara Schumann', True),
        ('theoryExercises', 'Theory Exercises', False),
        ('trecento', 'Fourteenth-Century Italian Music', False),
        ('verdi', 'Giuseppe Verdi', True),
        ('weber', 'Carl Maria von Weber', True),
        )

    _noCorpus = False

    ### PRIVATE PROPERTIES ###

    @property
    def cacheName(self):
        return 'core'

    ### PUBLIC METHODS ###

    def getBachChorales(
        self,
        fileExtensions='xml',
        ):
        r'''
        Return the file name of all Bach chorales.

        By default, only Bach Chorales in xml format are returned, because the
        quality of the encoding and our parsing of those is superior.

        N.B. Look at the module corpus.chorales for many better ways to work
        with the chorales.

        >>> from music21 import corpus
        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> a = coreCorpus.getBachChorales()
        >>> len(a) > 400
        True

        >>> a = coreCorpus.getBachChorales('krn')
        >>> len(a) > 10
        False

        >>> a = coreCorpus.getBachChorales('xml')
        >>> len(a) > 400
        True

        >>> #_DOCS_SHOW a[0]
        >>> '/Users/cuthbert/Documents/music21/corpus/bach/bwv1.6.mxl' #_DOCS_HIDE
        '/Users/cuthbert/Documents/music21/corpus/bach/bwv1.6.mxl'

        '''
        names = ( 'bwv1.6.mxl', 'bwv10.7.mxl', 'bwv101.7.mxl', 'bwv102.7.mxl',
        'bwv103.6.mxl', 'bwv104.6.mxl', 'bwv108.6.mxl', 'bwv11.6.mxl',
        'bwv110.7.mxl', 'bwv111.6.mxl', 'bwv112.5-sc.mxl', 'bwv112.5.mxl',
        'bwv113.8.mxl', 'bwv114.7.mxl', 'bwv115.6.mxl', 'bwv116.6.mxl',
        'bwv117.4.mxl', 'bwv119.9.mxl', 'bwv12.7.mxl', 'bwv120.6.mxl',
        'bwv120.8-a.mxl', 'bwv121.6.mxl', 'bwv122.6.mxl', 'bwv123.6.mxl',
        'bwv124.6.mxl', 'bwv125.6.mxl', 'bwv126.6.mxl', 'bwv127.5.mxl',
        'bwv128.5.mxl', 'bwv13.6.mxl', 'bwv130.6.mxl', 'bwv133.6.mxl',
        'bwv135.6.mxl', 'bwv136.6.mxl', 'bwv137.5.mxl', 'bwv139.6.mxl',
        'bwv14.5.mxl', 'bwv140.7.mxl', 'bwv144.3.mxl', 'bwv144.6.mxl',
        'bwv145-a.mxl', 'bwv145.5.mxl', 'bwv146.8.mxl', 'bwv148.6.mxl',
        'bwv149.7.mxl', 'bwv151.5.mxl', 'bwv153.1.mxl', 'bwv153.5.mxl',
        'bwv153.9.mxl', 'bwv154.3.mxl', 'bwv154.8.mxl', 'bwv155.5.mxl',
        'bwv156.6.mxl', 'bwv157.5.mxl', 'bwv158.4.mxl', 'bwv159.5.mxl',
        'bwv16.6.mxl', 'bwv161.6.mxl', 'bwv162.6-lpz.mxl', 'bwv164.6.mxl',
        'bwv165.6.mxl', 'bwv166.6.mxl', 'bwv168.6.mxl', 'bwv169.7.mxl',
        'bwv17.7.mxl', 'bwv171.6.mxl', 'bwv172.6.mxl', 'bwv174.5.mxl',
        'bwv175.7.mxl', 'bwv176.6.mxl', 'bwv177.5.mxl', 'bwv178.7.mxl',
        'bwv179.6.mxl', 'bwv18.5-lz.mxl', 'bwv18.5-w.mxl', 'bwv180.7.mxl',
        'bwv183.5.mxl', 'bwv184.5.mxl', 'bwv185.6.mxl', 'bwv187.7.mxl',
        'bwv188.6.mxl', 'bwv19.7.mxl', 'bwv190.7-inst.mxl', 'bwv190.7.mxl',
        'bwv194.12.mxl', 'bwv194.6.mxl', 'bwv195.6.mxl', 'bwv197.10.mxl',
        'bwv197.5.mxl', 'bwv197.7-a.mxl', 'bwv2.6.mxl', 'bwv20.11.mxl',
        'bwv20.7.mxl', 'bwv226.2.mxl', 'bwv227.1.mxl', 'bwv227.11.mxl',
        'bwv227.3.mxl', 'bwv227.7.mxl', 'bwv229.2.mxl', 'bwv244.10.mxl',
        'bwv244.15.mxl', 'bwv244.17.mxl', 'bwv244.25.mxl', 'bwv244.29-a.mxl',
        'bwv244.3.mxl', 'bwv244.32.mxl', 'bwv244.37.mxl', 'bwv244.40.mxl',
        'bwv244.44.mxl', 'bwv244.46.mxl', 'bwv244.54.mxl', 'bwv244.62.mxl',
        'bwv245.11.mxl', 'bwv245.14.mxl', 'bwv245.15.mxl', 'bwv245.17.mxl',
        'bwv245.22.mxl', 'bwv245.26.mxl', 'bwv245.28.mxl', 'bwv245.3.mxl',
        'bwv245.37.mxl', 'bwv245.40.mxl', 'bwv245.5.mxl', 'bwv248.12-2.mxl',
        'bwv248.17.mxl', 'bwv248.23-2.mxl', 'bwv248.23-s.mxl', 'bwv248.28.mxl',
        'bwv248.33-3.mxl', 'bwv248.35-3.mxl', 'bwv248.35-3c.mxl',
        'bwv248.42-4.mxl', 'bwv248.42-s.mxl', 'bwv248.46-5.mxl',
        'bwv248.5.mxl', 'bwv248.53-5.mxl', 'bwv248.59-6.mxl',
        'bwv248.64-6.mxl', 'bwv248.64-s.mxl', 'bwv248.9-1.mxl',
        'bwv248.9-s.mxl', 'bwv25.6.mxl', 'bwv250.mxl', 'bwv251.mxl',
        'bwv252.mxl', 'bwv253.mxl', 'bwv254.mxl', 'bwv255.mxl', 'bwv256.mxl',
        'bwv257.mxl', 'bwv258.mxl', 'bwv259.mxl', 'bwv26.6.mxl', 'bwv260.mxl',
        'bwv261.mxl', 'bwv262.mxl', 'bwv263.mxl', 'bwv264.mxl', 'bwv265.mxl',
        'bwv266.mxl', 'bwv267.mxl', 'bwv268.mxl', 'bwv269.mxl', 'bwv27.6.mxl',
        'bwv270.mxl', 'bwv271.mxl', 'bwv272.mxl', 'bwv273.mxl', 'bwv276.mxl',
        'bwv277.krn', 'bwv277.mxl', 'bwv278.mxl', 'bwv279.mxl', 'bwv28.6.mxl',
        'bwv280.mxl', 'bwv281.krn', 'bwv281.mxl', 'bwv282.mxl', 'bwv283.mxl',
        'bwv284.mxl', 'bwv285.mxl', 'bwv286.mxl', 'bwv287.mxl', 'bwv288.mxl',
        'bwv289.mxl', 'bwv29.8.mxl', 'bwv290.mxl', 'bwv291.mxl', 'bwv292.mxl',
        'bwv293.mxl', 'bwv294.mxl', 'bwv295.mxl', 'bwv296.mxl', 'bwv297.mxl',
        'bwv298.mxl', 'bwv299.mxl', 'bwv3.6.mxl', 'bwv30.6.mxl', 'bwv300.mxl',
        'bwv301.mxl', 'bwv302.mxl', 'bwv303.mxl', 'bwv304.mxl', 'bwv305.mxl',
        'bwv306.mxl', 'bwv307.mxl', 'bwv308.mxl', 'bwv309.mxl', 'bwv31.9.mxl',
        'bwv310.mxl', 'bwv311.mxl', 'bwv312.mxl', 'bwv313.mxl', 'bwv314.mxl',
        'bwv315.mxl', 'bwv316.mxl', 'bwv317.mxl', 'bwv318.mxl', 'bwv319.mxl',
        'bwv32.6.mxl', 'bwv320.mxl', 'bwv321.mxl', 'bwv322.mxl', 'bwv323.mxl',
        'bwv324.mxl', 'bwv325.mxl', 'bwv326.mxl', 'bwv327.mxl', 'bwv328.mxl',
        'bwv329.mxl', 'bwv33.6.mxl', 'bwv330.mxl', 'bwv331.mxl', 'bwv332.mxl',
        'bwv333.mxl', 'bwv334.mxl', 'bwv335.mxl', 'bwv336.mxl', 'bwv337.mxl',
        'bwv338.mxl', 'bwv339.mxl', 'bwv340.mxl', 'bwv341.mxl', 'bwv342.mxl',
        'bwv343.mxl', 'bwv344.mxl', 'bwv345.mxl', 'bwv346.mxl', 'bwv347.mxl',
        'bwv348.mxl', 'bwv349.mxl', 'bwv350.mxl', 'bwv351.mxl', 'bwv352.mxl',
        'bwv353.mxl', 'bwv354.mxl', 'bwv355.mxl', 'bwv356.mxl', 'bwv357.mxl',
        'bwv358.mxl', 'bwv359.mxl', 'bwv36.4-2.mxl', 'bwv36.8-2.mxl',
        'bwv360.mxl', 'bwv361.mxl', 'bwv362.mxl', 'bwv363.mxl', 'bwv364.mxl',
        'bwv365.mxl', 'bwv366.krn', 'bwv366.mxl', 'bwv367.mxl', 'bwv368.mxl',
        'bwv369.mxl', 'bwv37.6.mxl', 'bwv370.mxl', 'bwv371.mxl', 'bwv372.mxl',
        'bwv373.mxl', 'bwv374.mxl', 'bwv375.mxl', 'bwv376.mxl', 'bwv377.mxl',
        'bwv378.mxl', 'bwv379.mxl', 'bwv38.6.mxl', 'bwv380.mxl', 'bwv381.mxl',
        'bwv382.mxl', 'bwv383.mxl', 'bwv384.mxl', 'bwv385.mxl', 'bwv386.mxl',
        'bwv387.mxl', 'bwv388.mxl', 'bwv389.mxl', 'bwv39.7.mxl', 'bwv390.mxl',
        'bwv391.mxl', 'bwv392.mxl', 'bwv393.mxl', 'bwv394.mxl', 'bwv395.mxl',
        'bwv396.mxl', 'bwv397.mxl', 'bwv398.mxl', 'bwv399.mxl', 'bwv4.8.mxl',
        'bwv40.3.mxl', 'bwv40.6.mxl', 'bwv40.8.mxl', 'bwv400.mxl',
        'bwv401.mxl', 'bwv402.mxl', 'bwv403.mxl', 'bwv404.mxl', 'bwv405.mxl',
        'bwv406.mxl', 'bwv407.mxl', 'bwv408.mxl', 'bwv41.6.mxl', 'bwv410.mxl',
        'bwv411.mxl', 'bwv412.mxl', 'bwv413.mxl', 'bwv414.mxl', 'bwv415.mxl',
        'bwv416.mxl', 'bwv417.mxl', 'bwv418.mxl', 'bwv419.mxl', 'bwv42.7.mxl',
        'bwv420.mxl', 'bwv421.mxl', 'bwv422.mxl', 'bwv423.mxl', 'bwv424.mxl',
        'bwv425.mxl', 'bwv426.mxl', 'bwv427.mxl', 'bwv428.mxl', 'bwv429.mxl',
        'bwv43.11.mxl', 'bwv430.mxl', 'bwv431.mxl', 'bwv432.mxl', 'bwv433.mxl',
        'bwv434.mxl', 'bwv435.mxl', 'bwv436.mxl', 'bwv437.mxl', 'bwv438.mxl',
        'bwv44.7.mxl', 'bwv45.7.mxl', 'bwv47.5.mxl', 'bwv48.3.mxl',
        'bwv48.7.mxl', 'bwv5.7.mxl', 'bwv52.6.mxl', 'bwv55.5.mxl',
        'bwv56.5.mxl', 'bwv57.8.mxl', 'bwv59.3.mxl', 'bwv6.6.mxl',
        'bwv60.5.mxl', 'bwv64.2.mxl', 'bwv64.4.mxl', 'bwv64.8.mxl',
        'bwv65.2.mxl', 'bwv65.7.mxl', 'bwv66.6.mxl', 'bwv67.4.mxl',
        'bwv67.7.mxl', 'bwv69.6-a.mxl', 'bwv69.6.mxl', 'bwv7.7.mxl',
        'bwv70.11.mxl', 'bwv70.7.mxl', 'bwv72.6.mxl', 'bwv73.5.mxl',
        'bwv74.8.mxl', 'bwv77.6.mxl', 'bwv78.7.mxl', 'bwv79.3.mxl',
        'bwv79.6.mxl', 'bwv8.6.mxl', 'bwv80.8.mxl', 'bwv81.7.mxl',
        'bwv83.5.mxl', 'bwv84.5.mxl', 'bwv85.6.mxl', 'bwv86.6.mxl',
        'bwv87.7.mxl', 'bwv88.7.mxl', 'bwv89.6.mxl', 'bwv9.7.mxl',
        'bwv90.5.mxl', 'bwv91.6.mxl', 'bwv92.9.mxl', 'bwv93.7.mxl',
        'bwv94.8.mxl', 'bwv95.7.mxl', 'bwv96.6.mxl', 'bwv97.9.mxl',
        'bwv99.6.mxl',
        )
        composerDirectory = self.getComposerDirectoryPath('bach')
        results = []
        if composerDirectory is None:  # case where we have no corpus
            return results
        paths = self.getPaths(fileExtensions)
        for filename in names:
            candidate = os.path.join(composerDirectory, filename)
            if candidate not in paths:  # it may not match extensions
                if not os.path.exists(candidate):  # it does not exist at all
                    filename2 = filename.replace('mxl', 'xml')
                    candidate2 = os.path.join(composerDirectory, filename2)
                    if candidate2 in paths:
                        results.append(candidate2)
                    else:
                        environLocal.printDebug([
                            'corpus missing expected file path',
                            candidate,
                            ])
            else:
                results.append(candidate)
        return results

    def getComposerDirectoryPath(self, composerName):
        '''
        To be DEPRECATED 
        
        Given the name of a composer, get the path to the top-level directory
        of that composer:

        >>> import os
        >>> from music21 import corpus
        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> a = coreCorpus.getComposerDirectoryPath('ciconia')
        >>> a.endswith(os.path.join('corpus', os.sep, 'ciconia'))
        True

        >>> a = coreCorpus.getComposerDirectoryPath('bach')
        >>> a.endswith(os.path.join('corpus', os.sep, 'bach'))
        True

        >>> a = coreCorpus.getComposerDirectoryPath('handel')
        >>> a.endswith(os.path.join('corpus', os.sep, 'handel'))
        True

        '''
        match = None
        for moduleName in sorted(os.listdir(common.getCorpusFilePath())):
            candidate = moduleName
            if composerName.lower() not in candidate.lower():
                continue
            directory = os.path.join(common.getCorpusFilePath(), moduleName)
            if directory.lower().endswith(composerName.lower()):
                match = directory
                break
        return match

    def getMonteverdiMadrigals(
        self,
        fileExtensions='xml',
        ):
        '''
        Return a list of the filenames of all Monteverdi madrigals.

        >>> from music21 import corpus
        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> a = coreCorpus.getMonteverdiMadrigals()
        >>> len(a) > 40
        True

        '''
        results = []
        names = (
            'madrigal.3.1.mxl', 'madrigal.3.2.mxl', 'madrigal.3.3.mxl',
            'madrigal.3.4.mxl', 'madrigal.3.5.mxl', 'madrigal.3.6.mxl',
            'madrigal.3.7.mxl', 'madrigal.3.8.mxl', 'madrigal.3.9.mxl',
            'madrigal.3.10.mxl', 'madrigal.3.11.mxl', 'madrigal.3.12.mxl',
            'madrigal.3.13.mxl', 'madrigal.3.14.mxl', 'madrigal.3.15.mxl',
            'madrigal.3.16.mxl', 'madrigal.3.17.mxl', 'madrigal.3.18.mxl',
            'madrigal.3.19.mxl', 'madrigal.3.20.mxl', 'madrigal.4.1.mxl',
            'madrigal.4.2.mxl', 'madrigal.4.3.mxl', 'madrigal.4.4.mxl',
            'madrigal.4.5.mxl', 'madrigal.4.6.mxl', 'madrigal.4.7.mxl',
            'madrigal.4.8.mxl', 'madrigal.4.9.mxl', 'madrigal.4.10.mxl',
            'madrigal.4.11.mxl', 'madrigal.4.12.mxl', 'madrigal.4.13.mxl',
            'madrigal.4.14.mxl', 'madrigal.4.15.mxl', 'madrigal.4.16.mxl',
            'madrigal.4.17.mxl', 'madrigal.4.18.mxl', 'madrigal.4.19.mxl',
            'madrigal.4.20.mxl', 'madrigal.5.1.mxl', 'madrigal.5.2.mxl',
            'madrigal.5.3.mxl', 'madrigal.5.5.mxl', 'madrigal.5.5.mxl',
            'madrigal.5.6.mxl', 'madrigal.5.7.mxl', 'madrigal.5.8.mxl',
            )
        composerDirectoryPath = self.getComposerDirectoryPath('monteverdi')
        if composerDirectoryPath is None:
            return results
        paths = self.getPaths(fileExtensions)
        for filename in names:
            candidate = os.path.join(composerDirectoryPath, filename)
            if candidate not in paths:
                if not os.path.exists(candidate):
                    environLocal.printDebug([
                        'corpus missing expected file path',
                        candidate,
                        ])
            else:
                results.append(candidate)
        return results

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

        >>> from music21 import corpus
        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> corpusFilePaths = coreCorpus.getPaths()
        >>> 2500 < len(corpusFilePaths) < 2600
        True

        >>> kernFilePaths = coreCorpus.getPaths('krn')
        >>> len(kernFilePaths) >= 500
        True

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

    ### PUBLIC PROPERTIES ###

    @property
    def manualCoreCorpusPath(self):
        r'''
        Set music21's core corpus to a directory, and save that information in
        the user settings.

        This is specifically for use with "no corpus" music21 packages, where
        the core corpus was not included with the rest of the package
        functionality, and had to be installed separately.

        Set it to a directory:

        >>> coreCorpus = corpus.corpora.CoreCorpus()
        >>> coreCorpus.manualCoreCorpusPath = '~/Desktop'

        Unset it:

        >>> coreCorpus.manualCoreCorpusPath = None
        >>> coreCorpus.manualCoreCorpusPath is None
        True

        '''
        userSettings = environment.UserSettings()
        if 'manualCoreCorpusPath' in userSettings.keys():
            return userSettings['manualCoreCorpusPath']
        return None

    @manualCoreCorpusPath.setter
    def manualCoreCorpusPath(self, expr):
        userSettings = environment.UserSettings() 
        if expr is not None:
            path = common.cleanpath(expr)
            if not os.path.isdir(path) or not os.path.exists(path):
                raise CorpusException("path needs to be a path to an existing directory")
            userSettings['manualCoreCorpusPath'] = path
        else:
            userSettings['manualCoreCorpusPath'] = None
        environment.Environment().write()

    @property
    def name(self):
        return 'core'

    @property
    def noCorpus(self):
        '''
        Return True or False if this is a `corpus` or `noCoprus` distribution.

        >>> from music21 import corpus
        >>> corpus.corpora.CoreCorpus().noCorpus
        False

        '''
        if CoreCorpus._noCorpus is None:
            # assume that there will always be a 'bach' dir
            if self.getComposerDirectoryPath('bach') is None:
                CoreCorpus._noCorpus = True
            else:
                CoreCorpus._noCorpus = False
        
        return CoreCorpus._noCorpus


#------------------------------------------------------------------------------


class LocalCorpus(Corpus):
    r'''
    A model of a *local* corpus.

    >>> localCorpus = corpus.corpora.LocalCorpus()

    The default local corpus is unnamed (or called "local" or None), but an arbitrary number of
    independent, named local corpora can be defined and persisted:

    >>> namedLocalCorpus = corpus.corpora.LocalCorpus('with a name')
    '''

    ### CLASS VARIABLES ###

    _temporaryLocalPaths = {}

    ### INITIALIZER ###

    def __init__(self, name=None):
        if not isinstance(name, (six.string_types, type(None))):
            raise CorpusException("Name must be a string or None")
        if name is not None and not name:
            raise CorpusException("Name cannot be blank")
        if name == 'local':
            self._name = None
        else:
            self._name = name

    ### SPECIAL METHODS ###

    def __repr__(self):
        if self.name is None:
            return '<{0}.{1}>'.format(
                self.__class__.__module__,
                self.__class__.__name__,
                )
        return '<{0}.{1}: {2!r}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.name
            )

    ### PRIVATE METHODS ###

    def _getSettings(self):
        userSettings = environment.UserSettings()
        if self.name == 'local':
            return userSettings['localCorpusSettings']
        return userSettings['localCorporaSettings'].get(self.name, None)

    ### PRIVATE PROPERTIES ###

    @property
    def cacheName(self):
        cacheName = 'local'
        if self.name is not None and self.name != 'local':
            cacheName += '-{0}'.format(self.name)
        return cacheName

    ### PUBLIC METHODS ###

    def addPath(self, directoryPath):
        r'''
        Add a directory path to a local corpus:

        >>> localCorpus = corpus.corpora.LocalCorpus('a new corpus')
        >>> localCorpus.addPath('~/Desktop')

        Paths added in this way will not be persisted from session to session
        unless explicitly saved by a call to ``LocalCorpus.save()``.
        '''
        from music21 import corpus
        if not isinstance(directoryPath, six.string_types):
            raise corpus.CorpusException(
                'an invalid file path has been provided: {0!r}'.format(
                    directoryPath))
        directoryPath = os.path.expanduser(directoryPath)
        if (not os.path.exists(directoryPath) or 
                not os.path.isdir(directoryPath)):
            raise corpus.CorpusException(
                'an invalid file path has been provided: {0!r}'.format(
                    directoryPath))
        if self.cacheName not in LocalCorpus._temporaryLocalPaths:
            LocalCorpus._temporaryLocalPaths[self.cacheName] = set()
        LocalCorpus._temporaryLocalPaths[self.cacheName].add(directoryPath)
        self._removeNameFromCache(self.cacheName)

    def delete(self):
        r'''
        Delete a non-default local corpus from the user settings.
        '''
        if self.name is None or self.name == 'local':
            return
        elif not self.existsInSettings:
            return
        userSettings = environment.UserSettings()
        del(userSettings['localCorporaSettings'][self.name])
        environment.Environment().write()

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
        cacheKey = (self.cacheName, tuple(fileExtensions))
        # not cached, fetch and reset
        #if cacheKey not in Corpus._pathsCache:
            # check paths before trying to search
        validPaths = []
        for directoryPath in self.directoryPaths:
            if not os.path.isdir(directoryPath):
                environLocal.warn(
                    'invalid path set as localCorpusSetting: {0}'.format(
                        directoryPath))
            else:
                validPaths.append(directoryPath)
        # append successive matches into one list
        matches = []
        for directoryPath in validPaths:
            matches += self._findPaths(directoryPath, fileExtensions)
        Corpus._pathsCache[cacheKey] = matches

        return Corpus._pathsCache[cacheKey]

    def removePath(self, directoryPath):
        r'''
        Remove a directory path from a local corpus.

        If that path is included in the list of persisted paths for the given
        corpus, it will be removed permanently.
        '''
        temporaryPaths = LocalCorpus._temporaryLocalPaths.get(
            self.cacheName, [])
        directoryPath = os.path.abspath(os.path.expanduser(directoryPath))
        if directoryPath in temporaryPaths:
            temporaryPaths.remove(directoryPath)
        if self.existsInSettings:
            settings = self._getSettings()
            if settings is not None and directoryPath in settings:
                settings.remove(directoryPath)
            self.save()
        self._removeNameFromCache(self.cacheName)

    def save(self):
        r'''
        Save the current list of directory paths in use by a given corpus in
        the user settings.
        '''
        userSettings = environment.UserSettings()
        if self.name == 'local':
            userSettings['localCorpusSettings'] = self.directoryPaths
        else:
            userSettings['localCorporaSettings'][self.name] = self.directoryPaths
        environment.Environment().write()


    ### PUBLIC PROPERTIES ###

    @property
    def directoryPaths(self):
        r'''
        The directory paths in use by a given local corpus.
        '''
        candidatePaths = []
        if self.existsInSettings:
            if self.name == 'local':
                candidatePaths = environLocal['localCorpusSettings']
            else:
                candidatePaths = environLocal['localCorporaSettings'][self.name]
        temporaryPaths = LocalCorpus._temporaryLocalPaths.get(
            self.cacheName, [])
        allPaths = tuple(sorted(set(candidatePaths).union(temporaryPaths)))
        return allPaths

    @property
    def existsInSettings(self):
        r'''
        True if this local corpus has a corresponding entry in music21's user
        settings, otherwise false.
        '''
        if self.name == 'local':
            return True
        userSettings = environment.UserSettings()
        return self.name in userSettings['localCorporaSettings']

    @property
    def name(self):
        r'''
        The name of a given local corpus.

        >>> from music21 import corpus
        >>> corpus.corpora.LocalCorpus().name
        'local'

        >>> corpus.corpora.LocalCorpus(name='Bach Chorales').name
        'Bach Chorales'

        '''
        if self._name is None:
            return 'local'
        return self._name


#------------------------------------------------------------------------------


class VirtualCorpus(Corpus):
    r'''
    A model of the *virtual* corpus. that stays online...

    >>> virtualCorpus = corpus.corpora.VirtualCorpus()

    '''

    ### CLASS VARIABLES ###

    _virtual_works = []
    
    corpusName = None
    for corpusName in dir(virtual):
        className = getattr(virtual, corpusName)
        if callable(className):
            obj = className()
            if isinstance(obj, virtual.VirtualWork): # @UndefinedVariable
                if obj.corpusPath is not None:
                    _virtual_works.append(obj)
    del corpusName
    del className
    del obj
    ### PRIVATE PROPERTIES ###

    @property
    def cacheName(self):
        return 'virtual'

    ### PUBLIC METHODS ###

    def getPaths(
        self,
        fileExtensions=None,
        expandExtensions=True,
        ):
        '''
        Get all paths in the virtual corpus that match a known extension.

        An extension of None will return all known extensions.

        >>> len(corpus.corpora.VirtualCorpus().getPaths()) > 6
        True

        '''
        fileExtensions = self._translateExtensions(
            fileExtensions=fileExtensions,
            expandExtensions=expandExtensions,
            )
        paths = []
        for obj in self._virtual_works:
            if obj.corpusPath is not None:
                for fileExtension in fileExtensions:
                    results = obj.getUrlByExt(fileExtension)
                    for result in results:
                        if result not in paths:
                            paths.append(result)
        return paths

    def getWorkList(
        self,
        workName,
        movementNumber=None,
        fileExtensions=None,
        ):
        '''
        Given a work name, search all virtual works and return a list of URLs
        for any matches.

        >>> virtualCorpus = corpus.corpora.VirtualCorpus()
        >>> virtualCorpus.getWorkList('bach/bwv1007/prelude')
        ['http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml']

        >>> virtualCorpus.getWorkList('junk')
        []

        '''
        if not common.isListLike(fileExtensions):
            fileExtensions = [fileExtensions]
        for obj in VirtualCorpus._virtual_works:
            if obj.corpusPath is not None and workName.lower() in obj.corpusPath.lower():
                return obj.getUrlByExt(fileExtensions)
        return []


    @property
    def name(self):
        r'''
        The name of the virtual corpus:

        >>> corpus.corpora.VirtualCorpus().name
        'virtual'

        '''
        return 'virtual'



__all__ = (
    'Corpus',
    'CoreCorpus',
    'LocalCorpus',
    'VirtualCorpus',
    )

_DOC_ORDER = (
    Corpus,
    CoreCorpus,
    LocalCorpus,
    VirtualCorpus,
    )

if __name__ == "__main__":
    import music21
    music21.mainTest()
