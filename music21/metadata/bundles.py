# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         bundles.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
#               Project 
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------


import os
import re
import time
import unittest

from music21 import base
from music21 import common
from music21 import freezeThaw


#------------------------------------------------------------------------------


from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))


#------------------------------------------------------------------------------


class MetadataEntry(object):
    
    ### INITIALIZER ###
    
    def __init__(self, 
        sourcePath=None, 
        number=None, 
        metadataPayload=None, 
        ):
        self._sourcePath = sourcePath
        self._number = number
        self._metadataPayload = metadataPayload

    ### SPECIAL METHODS ###

    def __getnewargs__(self):
        return (
            self.sourcePath,
            self.metadataPayload,
            self.number,
            )

    def __repr__(self):
        return '<{0}.{1}: {2}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.corpusPath,
            )

    ### PUBLIC METHODS ###

    def parse(self):
        from music21 import corpus
        if self.number is not None:
            return corpus.parse(self.sourcePath, number=self.number)
        else:
            return corpus.parse(self.sourcePath)

    def search(self, query, field=None):
        return self.metadataPayload.search(query, field)

    ### PUBLIC PROPERTIES ###

    @property
    def corpusPath(self):
        return MetadataBundle.corpusPathToKey(self.sourcePath, self.number)

    @property
    def metadataPayload(self):
        return self._metadataPayload

    @property
    def number(self):
        return self._number

    @property
    def sourcePath(self):
        return self._sourcePath


#------------------------------------------------------------------------------


class MetadataBundle(object):
    r'''
    An object that provides access to, searches within, and stores and loads
    multiple Metadata objects.

    Additionally, multiple MetadataBundles can be merged for additional
    processing.  See corpus.metadata.metadataCache for the module that builds
    these.
    '''
    
    ### INITIALIZER ###

    def __init__(self, name=None):
        self._metadataEntries = {}
        assert name in ('core', 'local', 'virtual', None)
        self._name = name

    ### SPECIAL METHODS ###

    def __and__(self, metadataBundle):
        r'''
        Compute the set-wise `and` of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4')
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle & tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {4 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            '__and__',
            )

    def __eq__(self, expr):
        '''
        True if `expr` is of the same type, and contains an identical set of
        entries, otherwise false:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()
            >>> bachBundle = coreBundle.search('bach', 'composer')
            >>> beethovenBundle = coreBundle.search('beethoven', 'composer')
            >>> bachBundle == beethovenBundle
            False

        ::

            >>> bachBundle == coreBundle.search('bach', 'composer')
            True

        ::

            >>> bachBundle == 'foo'
            False

        '''
        if type(self) == type(expr):
            if self._metadataEntries == expr._metadataEntries:
                return True
        return False

    def __ge__(self, metadataBundle):
        return self._apply_set_predicate(metadataBundle, '__ge__')

    def __getitem__(self, i):
        return self._metadataEntries.values()[i]

    def __gt__(self, metadataBundle):
        return self._apply_set_predicate(metadataBundle, '__gt__')

    def __le__(self, metadataBundle):
        return self._apply_set_predicate(metadataBundle, '__le__')
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return selfKeys.__le__(otherKeys)

    def __len__(self):
        return len(self._metadataEntries)
    
    def __lt__(self, metadataBundle):
        return self._apply_set_predicate(metadataBundle, '__lt__')

    def __ne__(self, expr):
        return self != expr

    def __or__(self, metadataBundle):
        r'''
        Compute the set-wise `or` of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> beethovenBundle = coreBundle.search(
            ...     'beethoven', 
            ...     field='composer',
            ...     )
            >>> beethovenBundle
            <music21.metadata.bundles.MetadataBundle {16 entries}>

        ::

            >>> bachBundle | beethovenBundle
            <music21.metadata.bundles.MetadataBundle {37 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle, 
            '__or__',
            )

    def __repr__(self):
        if len(self) == 1:
            status = '{1 entry}'
        else:
            status = '{{{0} entries}}'.format(len(self))
        if self.name is not None:
            status = '{0!r}: '.format(self.name) + status
        return '<{0}.{1} {2}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            status,
            )

    def __sub__(self, metadataBundle):
        r'''
        Compute the set-wise `subtraction` of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4') 
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle - tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {17 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle, 
            '__sub__',
            )

    def __xor__(self, metadataBundle):
        r'''
        Compute the set-wise `exclusive or` of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4') 
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle ^ tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2025 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle, 
            '__xor__',
            )

    ### PRIVATE METHODS ###

    def _apply_set_operation(self, metadataBundle, operator):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        resultKeys = getattr(selfKeys, operator)(otherKeys)
        resultBundle = type(self)()
        for key in resultKeys:
            if key in self._metadataEntries:
                metadataEntry = self._metadataEntries[key]
            else:
                metadataEntry = metadataBundle._metadataEntries[key]
            resultBundle._metadataEntries[key] = metadataEntry
        return resultBundle

    def _apply_set_predicate(self, metadataBundle, predicate):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return getattr(selfKeys, predicate)(otherKeys)

    ### PUBLIC PROPERTIES ###

    @property
    def filePath(self):
        r'''
        The filesystem name of the cached metadata bundle, if the metadata
        bundle's name is not None.
        '''
        filePath = None
        if self.name in ('virtual', 'core'):
            filePath = os.path.join(common.getMetadataCacheFilePath(), 
                self.name + '.json')
        elif self.name == 'local':
            # write in temporary dir
            filePath = os.path.join(environLocal.getRootTempDir(), 
                self.name + '.json')
        return filePath

    @apply
    def name():
        def fget(self):
            r'''
            The name of the metadata bundle.

            Can be 'core', 'local', 'virtual' or None.

            The names 'core', 'local' and 'virtual refer to the core, local and
            virtual corpuses respectively:

            ::

                >>> metadata.MetadataBundle().name is None
                True

            ::
                
                >>> metadata.MetadataBundle.fromCoreCorpus().name
                u'core'

            Return string or None.
            '''
            return self._name
        def fset(self, expr):
            assert expr in ('core', 'local', 'virtual', None)
            self._name = expr
        return property(**locals())

    ### PUBLIC METHODS ###

    def addFromPaths(
        self, 
        paths, 
        printDebugAfter=0, 
        useCorpus=False,
        useMultiprocessing=True,
        ):
        '''
        Parse and store metadata from numerous files.

        If any files cannot be loaded, their file paths will be collected in a
        list that is returned.

        Returns a list of file paths with errors and stores the extracted
        metadata in `self._metadataEntries`.
        
        If `printDebugAfter` is set to an int, say 100, then after every 100
        files are parsed a message will be printed to stderr giving an update
        on progress.
        
        ::

            >>> metadataBundle = metadata.MetadataBundle()
            >>> metadataBundle.addFromPaths(
            ...     corpus.getWorkList('bwv66.6'),
            ...     useCorpus=True,
            ...     useMultiprocessing=False,
            ...     )
            []

        ::

            >>> len(metadataBundle._metadataEntries)
            1

        '''
        import music21
        from music21 import metadata
        music21Path = music21.__path__[0]
        jobs = []
        accumulatedResults = []
        accumulatedErrors = []
        if self.filePath is not None and os.path.exists(self.filePath):
            metadataBundleModificationTime = os.path.getctime(self.filePath)
        else:
            metadataBundleModificationTime = time.time()
        environLocal.warn([
            'MetadataBundle Modification Time: {0}'.format(
                metadataBundleModificationTime)
            ])
        currentJobNumber = 0
        for filePath in paths:
            key = self.corpusPathToKey(filePath)
            if key in self._metadataEntries:
                metadataEntry = self._metadataEntries[key]  
                filePathModificationTime = os.path.getctime(filePath)
                if filePathModificationTime < metadataBundleModificationTime:
                    environLocal.warn([
                        'Skipping job: {0}; already in cache.'.format(
                            os.path.relpath(filePath)),
                        ])
                    continue
            environLocal.warn([
                'Preparing job: {0}'.format(os.path.relpath(filePath)),
                ])
            currentJobNumber += 1
            if filePath.startswith(music21Path):
                filePath = os.path.join(
                    'music21',
                    os.path.relpath(filePath, music21Path),
                    )
            job = metadata.MetadataCachingJob(
                filePath,
                jobNumber=currentJobNumber,
                useCorpus=useCorpus,
                )
            jobs.append(job)
        currentIteration = 0
        if useMultiprocessing:
            jobProcessor = metadata.JobProcessor.process_parallel
        else:
            jobProcessor = metadata.JobProcessor.process_serial
        for result in jobProcessor(jobs):
            metadata.JobProcessor.report(
                len(jobs),
                result['remainingJobs'],
                result['filePath'],
                len(accumulatedErrors),
                )
            currentIteration += 1
            accumulatedResults.extend(result['metadataEntries'])
            accumulatedErrors.extend(result['errors'])
            for metadataEntry in result['metadataEntries']:
                self._metadataEntries[metadataEntry.corpusPath] = metadataEntry
            if (currentIteration % 50) == 0:
                self.write()
        self.validate()
        self.write()
        return accumulatedErrors

    def clear(self):
        r'''
        Clear all keys in a metadata bundle:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()
            >>> bachBundle = coreBundle.search(
            ...     'bach',
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> bachBundle.clear()
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {0 entries}>

        Return none.
        '''
        self._metadataEntries.clear()

    @staticmethod
    def corpusPathToKey(filePath, number=None):
        '''Given a file path or corpus path, return the meta-data path
    
        ::

            >>> mb = metadata.MetadataBundle()
            >>> key = mb.corpusPathToKey('bach/bwv1007/prelude')
            >>> key.endswith('bach_bwv1007_prelude')
            True

        ::

            >>> key = mb.corpusPathToKey('/beethoven/opus59no1/movement1.xml')
            >>> key.endswith('beethoven_opus59no1_movement1_xml')
            True

        '''
        if 'corpus' in filePath and 'music21' in filePath:
            corpusPath = filePath.split('corpus')[-1] # get filePath after corpus
        else:
            corpusPath = filePath
    
        if corpusPath.startswith(os.sep):
            corpusPath = corpusPath[1:]
    
        corpusPath = corpusPath.replace('/', '_')
        corpusPath = corpusPath.replace(os.sep, '_')
        corpusPath = corpusPath.replace('.', '_')
    
        # append name to metadata path
        if number == None:
            return corpusPath
        else:
            # append work number
            return corpusPath+'_%s' % number
    
    def delete(self):
        r'''
        Delete the filesystem cache of a named metadata bundle.

        Does not delete the in-memory metadata bundle.

        Return none.
        '''
        if self.filePath is not None:
            if os.path.exists(self.filePath):
                os.remove(self.filePath)
        return self

    def difference(self, metadataBundle):
        r'''
        Compute the set-wise difference of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4')
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle.difference(tripleMeterBundle)
            <music21.metadata.bundles.MetadataBundle {17 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle, 
            'difference',
            )

    @classmethod
    def fromCoreCorpus(cls):
        r'''
        Return a metadata bundle for the core corpus.
        
        Read from disk and cache it in memory if the bundle doesn't already
        exist, otherwise pull from memory:

        ::

            >>> coreCorpusA = metadata.MetadataBundle.fromCoreCorpus()
            >>> coreCorpusB = metadata.MetadataBundle.fromCoreCorpus()
            >>> coreCorpusA is coreCorpusB
            True
        
        '''
        from music21.corpus.base import _METADATA_BUNDLES
        domain = 'core'
        if domain in _METADATA_BUNDLES and _METADATA_BUNDLES[domain]:
            return _METADATA_BUNDLES[domain]
        bundle = cls(domain).read()
        _METADATA_BUNDLES[domain] = bundle
        return bundle

    @classmethod
    def fromLocalCorpus(cls):
        r'''
        Return a metadata bundle for the local corpus.
        
        Read from disk and cache it in memory if the bundle doesn't already
        exist, otherwise pull from memory:

        ::

            >>> localCorpusA = metadata.MetadataBundle.fromLocalCorpus()
            >>> localCorpusB = metadata.MetadataBundle.fromLocalCorpus()
            >>> localCorpusA is localCorpusB
            True
        
        '''
        from music21.corpus.base import _METADATA_BUNDLES
        domain = 'local'
        if domain in _METADATA_BUNDLES and _METADATA_BUNDLES[domain]:
            return _METADATA_BUNDLES[domain]
        bundle = cls(domain).read()
        _METADATA_BUNDLES[domain] = bundle
        return bundle

    @classmethod
    def fromVirtualCorpus(cls):
        r'''
        Return a metadata bundle for the virtual corpus.
        
        Read from disk and cache it in memory if the bundle doesn't already
        exist, otherwise pull from memory:

        ::

            >>> virtualCorpusA = metadata.MetadataBundle.fromVirtualCorpus()
            >>> virtualCorpusB = metadata.MetadataBundle.fromVirtualCorpus()
            >>> virtualCorpusA is virtualCorpusB
            True
        
        '''
        from music21.corpus.base import _METADATA_BUNDLES
        domain = 'virtual'
        if domain in _METADATA_BUNDLES and _METADATA_BUNDLES[domain]:
            return _METADATA_BUNDLES[domain]
        bundle = cls(domain).read()
        _METADATA_BUNDLES[domain] = bundle
        return bundle

    def intersection(self, metadataBundle):
        r'''
        Compute the set-wise intersection of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach',
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4')
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle.intersection(tripleMeterBundle)
            <music21.metadata.bundles.MetadataBundle {4 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle, 
            'intersection',
            )

    def isdisjoint(self, metadataBundle):
        r'''
        True if the set of keys in one metadata bundle are disjoint with
        the set of keys in another:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach',
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> beethovenBundle = coreBundle.search(
            ...     'beethoven',
            ...     field='composer',
            ...     )
            >>> beethovenBundle
            <music21.metadata.bundles.MetadataBundle {16 entries}>

        ::

            >>> bachBundle.isdisjoint(beethovenBundle)
            True

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4')
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle.isdisjoint(tripleMeterBundle)
            False

        Return boolean.
        '''
        return self._apply_set_predicate(metadataBundle, 'isdisjoint')

    def issubset(self, metadataBundle):
        r'''
        True if the set of keys in one metadata bundle are a subset of
        the keys in another:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBachBundle = bachBundle.search('3/4')
            >>> tripleMeterBachBundle
            <music21.metadata.bundles.MetadataBundle {4 entries}>

        ::

            >>> tripleMeterBachBundle.issubset(bachBundle)
            True

        ::

            >>> bachBundle.issubset(tripleMeterBachBundle)
            False

        Return boolean.
        '''
        return self._apply_set_predicate(metadataBundle, 'issubset')

    def issuperset(self, metadataBundle):
        r'''
        True if the set of keys in one metadata bundle are a superset of
        the keys in another:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBachBundle = bachBundle.search('3/4')
            >>> tripleMeterBachBundle
            <music21.metadata.bundles.MetadataBundle {4 entries}>

        ::

            >>> tripleMeterBachBundle.issuperset(bachBundle)
            False

        ::

            >>> bachBundle.issuperset(tripleMeterBachBundle)
            True

        Return boolean.
        '''
        return self._apply_set_predicate(metadataBundle, 'issuperset')

    def read(self, filePath=None):
        r'''
        Load cached metadata from the file path suggested by the name of this 
        MetadataBundle ('core', 'local', or 'virtual').
        
        If a specific filepath is given with the `filePath` keyword, attempt to
        load cached metadata from the file at that location.

        If `filePath` is None, and `self.filePath` is also None, do nothing.

        ::

            >>> anonymousBundle = metadata.MetadataBundle().read()

        ::

            >>> coreBundle = metadata.MetadataBundle('core').read()

        '''
        timer = common.Timer()
        timer.start()
        if filePath is None:
            filePath = self.filePath
        if filePath is None or not os.path.exists(filePath):
            environLocal.warn('no metadata found for: {0!r}; '
            'try building cache with corpus.cacheMetadata({1!r})'.format(
                self.name, self.name))
            return self
        jst = freezeThaw.JSONThawer(self)
        jst.jsonRead(filePath)
        environLocal.printDebug([
            'MetadataBundle: loading time:', 
            self.name, 
            timer, 
            'md items:', 
            len(self._metadataEntries)
            ])
        return self

    def search(self, query, field=None, fileExtensions=None):
        r'''
        Perform search, on all stored metadata, permit regular expression 
        matching. 

        ::

            >>> workList = corpus.getWorkList('ciconia')
            >>> metadataBundle = metadata.MetadataBundle()
            >>> metadataBundle.addFromPaths(
            ...     workList,
            ...     useCorpus=True,
            ...     useMultiprocessing=False,
            ...     )
            []

        ::

            >>> searchResult = metadataBundle.search(
            ...     'cicon', 
            ...     field='composer'
            ...     )
            >>> searchResult
            <music21.metadata.bundles.MetadataBundle {1 entry}>

        ::

            >>> len(searchResult)
            1

        ::

            >>> searchResult[0]
            <music21.metadata.bundles.MetadataEntry: ciconia_quod_jactatur_xml>

        ::

            >>> searchResult = metadataBundle.search(
            ...     'cicon',
            ...     field='composer', 
            ...     fileExtensions=('.krn',),
            ...     )
            >>> len(searchResult) # no files in this format
            0

        ::

            >>> searchResult = metadataBundle.search(
            ...     'cicon',
            ...     field='composer', 
            ...     fileExtensions=('.xml'),
            ...     )
            >>> len(searchResult) # shouldn't this be 11?
            1   

        '''
        newMetadataBundle = MetadataBundle()
        for key in self._metadataEntries:
            metadataEntry = self._metadataEntries[key]
            # ignore stub entries
            if metadataEntry.metadataPayload is None:
                continue
            if metadataEntry.search(query, field)[0]:
                include = False
                if fileExtensions is not None:
                    for fileExtension in fileExtensions:
                        if metadataEntry.sourcePath.endswith(fileExtension):
                            include = True
                            break
                        elif fileExtension.endswith('xml') and \
                            metadataEntry.sourcePath.endswith(('mxl', 'mx')):
                            include = True
                            break
                else:
                    include = True
                if include and key not in newMetadataBundle._metadataEntries:
                    newMetadataBundle._metadataEntries[key] = metadataEntry
        return newMetadataBundle

    def symmetric_difference(self, metadataBundle):
        r'''
        Compute the set-wise symmetric differnce of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> tripleMeterBundle = coreBundle.search('3/4')
            >>> tripleMeterBundle
            <music21.metadata.bundles.MetadataBundle {2012 entries}>

        ::

            >>> bachBundle.symmetric_difference(tripleMeterBundle)
            <music21.metadata.bundles.MetadataBundle {2025 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle, 
            'symmetric_difference',
            )

    def union(self, metadataBundle):
        r'''
        Compute the set-wise union of two metadata bundles:

        ::

            >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

        ::

            >>> bachBundle = coreBundle.search(
            ...     'bach', 
            ...     field='composer',
            ...     )
            >>> bachBundle
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> beethovenBundle = coreBundle.search(
            ...     'beethoven', 
            ...     field='composer',
            ...     )
            >>> beethovenBundle
            <music21.metadata.bundles.MetadataBundle {16 entries}>

        ::

            >>> bachBundle.union(beethovenBundle)
            <music21.metadata.bundles.MetadataBundle {37 entries}>

        Emit new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            'union',
            )

    def validate(self):
        r'''
        Validate each metadata entry in a metadata bundle.

        If the entry represents a non-virtual corpus asset, test that its
        source path is locatable on disk.  If not, remove the metadata entry
        from the metadata bundle.
        '''
        from music21 import corpus
        timer = common.Timer()
        timer.start()
        environLocal.warn(['MetadataBundle: validating...'])
        invalidatedKeys = []
        validatedPaths = set()
        corpusPrefix = os.path.join('music21', 'corpus')
        for key, metadataEntry in self._metadataEntries.iteritems():
            # MetadataEntries for core corpus items use a relative path as
            # their source path, always starting with 'music21/corpus'.
            sourcePath = metadataEntry.sourcePath
            if sourcePath in validatedPaths:
                continue
            if sourcePath.startswith(corpusPrefix):
                sourcePath = os.path.join(
                    common.getCorpusFilePath(),
                    os.path.relpath(
                        sourcePath,
                        corpusPrefix,
                        ))
            if sourcePath.startswith('http:') or os.path.exists(sourcePath):
                validatedPaths.add(metadataEntry.sourcePath)
            else:
                invalidatedKeys.append(key)
        for key in invalidatedKeys:
            print key
            del(self._metadataEntries[key])
        message = 'MetadataBundle: finished validating in {0} seconds.'.format(
            timer)
        environLocal.warn(message)
        return len(invalidatedKeys)

    def write(self, filePath=None):
        r'''
        Write the metadata bundle to disk as a JSON file.

        If `filePath` is None, use `self.filePath`.
       
        Returns the metadata bundle.

        ::

            >>> bachBundle = metadata.MetadataBundle.fromCoreCorpus().search(
            ...     'bach', 'composer')
            >>> bachBundle.filePath is None
            True

        ::

            >>> import os
            >>> import tempfile
            >>> tempFilePath = tempfile.mkstemp()[1]
            >>> bachBundle.write(filePath=tempFilePath) 
            <music21.metadata.bundles.MetadataBundle {21 entries}>

        ::

            >>> os.remove(tempFilePath)

        '''
        filePath = filePath or self.filePath
        if self.filePath is not None:
            filePath = self.filePath
            environLocal.warn(['MetadataBundle: writing:', filePath])
            jsf = freezeThaw.JSONFreezer(self)
            return jsf.jsonWrite(filePath)
        return self


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (
    MetadataBundle,
    )

__all__ = [
    'MetadataEntry',
    'MetadataBundle',
    ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
