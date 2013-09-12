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
    def sourcePath(self):
        return self._sourcePath

    @property
    def metadataPayload(self):
        return self._metadataPayload

    @property
    def number(self):
        return self._number


#------------------------------------------------------------------------------


class MetadataBundle(object):
    '''
    An object that provides access to, searches within, and stores and loads
    multiple Metadata objects.

    Additionally, multiple MetadataBundles can be merged for additional
    processing.  See corpus.metadata.metadataCache for the module that builds
    these.
    '''
    
    ### CLASS VARIABLES ###

    _DOC_ATTR = {
        'name': 'The name of the type of MetadataBundle being made, can be '
            'None, "core", "local" or "virtual".'
        }
    
    ### INITIALIZER ###

    def __init__(self, name=None):
        self._metadataEntries = {}
        self.name = name

    ### SPECIAL METHODS ###

    def __and__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        resultKeys = selfKeys.__and__(otherKeys)
        resultBundle = type(self)()
        for key in resultKeys:
            if key in self._metadataEntries:
                metadataEntry = self._metadataEntries[key]
            else:
                metadataEntry = metadataBundle._metadataEntries[key]
            resultBundle._metadataEntries[key] = metadataEntry
        return resultBundle

    def __eq__(self, expr):
        if type(self) == type(other):
            if self._metadataEntries == other._metadataEntries:
                return True
        return False

    def __ge__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return selfKeys.__ge__(otherKeys)

    def __getitem__(self, i):
        return self._metadataEntries.values()[i]

    def __gt__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return selfKeys.__gt__(otherKeys)

    def __le__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return selfKeys.__le__(otherKeys)

    def __len__(self):
        return len(self._metadataEntries)
    
    def __lt__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return selfKeys.__lt__(otherKeys)

    def __ne__(self, expr):
        return self != expr

    def __or__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        resultKeys = selfKeys.__and__(otherKeys)
        resultBundle = type(self)()
        for key in resultKeys:
            if key in self._metadataEntries:
                metadataEntry = self._metadataEntries[key]
            else:
                metadataEntry = metadataBundle._metadataEntries[key]
            resultBundle._metadataEntries[key] = metadataEntry
        return resultBundle

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
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        resultKeys = selfKeys.__and__(otherKeys)
        resultBundle = type(self)()
        for key in resultKeys:
            if key in self._metadataEntries:
                metadataEntry = self._metadataEntries[key]
            else:
                metadataEntry = metadataBundle._metadataEntries[key]
            resultBundle._metadataEntries[key] = metadataEntry
        return resultBundle

    def __xor__(self, metadataBundle):
        assert isinstance(metadataBundle, type(self))
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        resultKeys = selfKeys.__and__(otherKeys)
        resultBundle = type(self)()
        for key in resultKeys:
            if key in self._metadataEntries:
                metadataEntry = self._metadataEntries[key]
            else:
                metadataEntry = metadataBundle._metadataEntries[key]
            resultBundle._metadataEntries[key] = metadataEntry
        return resultBundle

    ### PRIVATE METHODS ###

    @property
    def filePath(self):
        filePath = None
        if self.name in ('virtual', 'core'):
            filePath = os.path.join(common.getMetadataCacheFilePath(), 
                self.name + '.json')
        elif self.name == 'local':
            # write in temporary dir
            filePath = os.path.join(environLocal.getRootTempDir(), 
                self.name + '.json')
        return filePath

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
        for results, errors, lastJobFilePath, remainingJobs in jobProcessor(
            jobs):
            metadata.JobProcessor.report(
                len(jobs),
                remainingJobs,
                lastJobFilePath,
                len(accumulatedErrors),
                )
            currentIteration += 1
            accumulatedResults.extend(results)
            accumulatedErrors.extend(errors)
            for metadataEntry in results:
                self._metadataEntries[metadataEntry.corpusPath] = metadataEntry
                #self._metadataEntries[corpusPath] = richMetadata
            if (currentIteration % 50) == 0:
                self.write()
        self.validate()
        self.write()
        return accumulatedErrors

    def clear(self):
        self._metadataEntries.clear()

    @staticmethod
    def corpusPathToKey(filePath, number=None):
        '''Given a file path or corpus path, return the meta-data path
    
        ::

            >>> mb = metadata.MetadataBundle()
            >>> mb.corpusPathToKey('bach/bwv1007/prelude'
            ...     ).endswith('bach_bwv1007_prelude')
            True

        ::

            >>> mb.corpusPathToKey('/beethoven/opus59no1/movement1.xml'
            ...     ).endswith('beethoven_opus59no1_movement1_xml')
            True

        '''
        if 'corpus' in filePath and 'music21' in filePath:
            cp = filePath.split('corpus')[-1] # get filePath after corpus
        else:
            cp = filePath
    
        if cp.startswith(os.sep):
            cp = cp[1:]
    
        cp = cp.replace('/', '_')
        cp = cp.replace(os.sep, '_')
        cp = cp.replace('.', '_')
    
        # append name to metadata path
        if number == None:
            return cp
        else:
            # append work number
            return cp+'_%s' % number
    
    def delete(self):
        if self.filePath is not None:
            if os.path.exists(self.filePath):
                os.remove(self.filePath)
        return self

    @classmethod
    def fromCoreCorpus(cls):
        return cls('core').read()

    @classmethod
    def fromLocalCorpus(cls):
        return cls('local').read()

    @classmethod
    def fromVirtualCorpus(cls):
        return cls('virtual').read()

    def read(self, filePath=None):
        '''
        Load self from the file path suggested by the name 
        of this MetadataBundle.
        
        If filePath is None (typical), run self.filePath.
        '''
        timer = common.Timer()
        timer.start()
        if filePath is None:
            filePath = self.filePath
        if not os.path.exists(filePath):
            environLocal.warn('no metadata found for: %s; try building cache with corpus.cacheMetadata("%s")' % (self.name, self.name))
            return
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
        '''
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

            >>> searchResult = metadataBundle.search('cicon', 'composer')
            >>> searchResult
            <music21.metadata.bundles.MetadataBundle {1 entry}>

        ::

            >>> len(searchResult)
            1

        ::

            >>> searchResult[0]
            <music21.metadata.bundles.MetadataEntry: ciconia_quod_jactatur_xml>

        ::

            >>> searchResult = metadataBundle.search('cicon', 'composer', 
            ...     fileExtensions=['.krn'])
            >>> len(searchResult) # no files in this format
            0

        ::

            >>> searchResult = metadataBundle.search('cicon', 'composer', 
            ...     fileExtensions=['.xml'])
            >>> len(searchResult)  # shouldn't this be 11?
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

    def validate(self):
        from music21 import corpus
        timer = common.Timer()
        timer.start()
        environLocal.warn(['MetadataBundle: validating...'])
        invalidatedKeys = []
        validatedPaths = set()
        corpusPrefix = os.path.join('music21', 'corpus')
        for key, metadataEntry in self._metadataEntries.iteritems():
            #print 'KEY:', key, metadataEntry, len(validatedPaths), \
            #    len(invalidatedKeys)

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
        environLocal.warn(
            'MetadataBundle: finished validating in {0} seconds.'.format(
                timer),
            )
        return len(invalidatedKeys)

    def write(self):
        '''
        Write the JSON _metadataEntries of all Metadata or 
        RichMetadata contained in this object. 

        TODO: Test!
        '''
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
