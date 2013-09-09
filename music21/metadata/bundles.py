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
        accessPath=None,
        cacheTime=None,
        filePath=None, 
        number=None, 
        richMetadata=None, 
        ):
        self._accessPath = accessPath
        self._cacheTime = cacheTime
        self._filePath = filePath
        self._number = number
        self._richMetadata = richMetadata

    ### SPECIAL METHODS ###

    def __getnewargs__(self):
        return (
            self.accessPath,
            self.cacheTime,
            self.filePath,
            self.richMetadata,
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
            return corpus.parse(self.filePath, number=self.number)
        else:
            return corpus.parse(self.filePath)

    def search(self, query, field=None):
        return self.richMetadata.search(query, field)

    ### PUBLIC PROPERTIES ###

    @apply
    def accessPath(): # @NoSelf
        def fget(self):
            return self._accessPath
        def fset(self, expr):
            self._accessPath = expr
        return property(**locals())

    @property
    def cacheTime(self):
        return self._cacheTime

    @property
    def corpusPath(self):
        return MetadataBundle.corpusPathToKey(self.filePath, self.number)

    @property
    def filePath(self):
        return self._filePath

    @property
    def richMetadata(self):
        return self._richMetadata

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
        'storage': 'A dictionary containing the Metadata objects that have '
            'been parsed.  Keys are strings',
        'name': 'The name of the type of MetadataBundle being made, can be '
            '"default", "corpus", or "virtual".  Possibly also "local".'
        }
    
    ### INITIALIZER ###

    def __init__(self, name='default'):
        # all keys are strings, all value are Metadata
        # there is apparently a performance boost for using all-string keys
        self.storage = {}
        # name is used to write storage file and access this bundle from multiple # bundles
        self.name = name
        # need to store local abs file path of each component
        # this will need to be refreshed after loading json data
        # keys are the same for self.storage
        self._accessPaths = {}

    ### SPECIAL METHODS ###

    def __getitem__(self, i):
        return self.storage.values()[i]

    def __len__(self):
        return len(self.storage)

    ### PRIVATE METHODS ###

    @property
    def filePath(self):
        filePath = None
        if self.name in ['virtual', 'core']:
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
        metadata in `self.storage`.
        
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

            >>> len(metadataBundle.storage)
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
            if key in self.storage:
                metadataEntry = self.storage[key]  
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
                self.storage[metadataEntry.corpusPath] = metadataEntry
                #self.storage[corpusPath] = richMetadata
            if (currentIteration % 50) == 0:
                self.write()
        self.updateAccessPaths(paths)
        self.write()
        return accumulatedErrors

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
            len(self.storage)
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

            >>> updateCount = metadataBundle.updateAccessPaths(workList)
            >>> searchResult = metadataBundle.search('cicon', 'composer')
            >>> searchResult
            <music21.metadata.bundles.MetadataBundle object at 0x...>

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
        for key in self.storage:
            metadataEntry = self.storage[key]
            # ignore stub entries
            if metadataEntry.richMetadata is None:
                continue
            if metadataEntry.search(query, field)[0]:
                include = False
                if fileExtensions is not None:
                    for fileExtension in fileExtensions:
                        if metadataEntry.accessPath.endswith(fileExtension):
                            include = True
                            break
                        elif fileExtension.endswith('xml') and \
                            metadataEntry.accessPath.endswith(('mxl', 'mx')):
                            include = True
                            break
                else:
                    include = True
                if include and key not in newMetadataBundle.storage:
                    newMetadataBundle.storage[key] = metadataEntry
        return newMetadataBundle

    def updateAccessPaths(self, pathList):
        r'''

        For each stored Metatadata object, create an entry in the dictionary
        ._accessPaths where each key is a simple version of the corpus name of
        the file and the value is the complete, local file path that returns
        this.

        Uses :meth:`~music21.metadata.MetadataBundle.corpusPathToKey` to
        generate the keys

        The `pathList` parameter is a list of all file paths on the users local
        system. 
        
        ::

            >>> mb = metadata.MetadataBundle()
            >>> mb.addFromPaths(
            ...     corpus.getWorkList('bwv66.6'),
            ...     useCorpus=True,
            ...     useMultiprocessing=False,
            ...     )
            []

        ::

            >>> mb.updateAccessPaths(corpus.getWorkList('bwv66.6'))
            2

        ::

            >>> #_DOCS_SHOW print mb._accessPaths
            >>> print r"{u'bach_bwv66_6_mxl': u'D:\\eclipse_dev\\music21base\\music21\\corpus\\bach\\bwv66.6.mxl'}" #_DOCS_HIDE
            {u'bach_bwv66_6_mxl': u'D:\\eclipse_dev\\music21base\\music21\\corpus\\bach\\bwv66.6.mxl'}
        
        A slower (but not too slow test) that should do much more. This is what
        corpus._updateMetadataBundle() does.  Notice that many of our files
        contain multiple scores, so while there are 2,300 files, there are over
        13,000 scores.
        
        ::

            >>> coreCorpusPaths = corpus.getCorePaths()
            >>> #_DOCS_SHOW len(coreCorpusPaths)
            >>> if len(coreCorpusPaths) > 2200: print '2300' #_DOCS_HIDE
            2300

        ::

            >>> mdCoreBundle = metadata.MetadataBundle('core')
            >>> mdCoreBundle.read()
            <music21.metadata.bundles.MetadataBundle object at 0x...>

        ::

            >>> updateCount = mdCoreBundle.updateAccessPaths(coreCorpusPaths)
            >>> #_DOCS_SHOW updateCount
            >>> if updateCount > 10000: print '14158' #_DOCS_HIDE
            14158
        
        Note that some scores inside an Opus file may have a number in the key
        that is not present in the path:
        
        ::

            >>> #_DOCS_SHOW mdCoreBundle._accessPaths['essenFolksong_han1_abc_1']
            >>> print r"u'D:\\eclipse_dev\\music21base\\music21\\corpus\\essenFolksong\\han1.abc'" #_DOCS_HIDE
            u'D:\\eclipse_dev\\music21base\\music21\\corpus\\essenFolksong\\han1.abc'

        '''
        import music21
        music21Path = music21.__path__[0]
        # always clear first
        # create a copy to manipulate
        for metadataEntry in self.storage.viewvalues():
            metadataEntry.accessPath = None
        updateCount = 0
        for filePath in pathList:
            # this key may not be valid if it points to an Opus work that
            # has multiple numbers; thus, need to get a stub that can be 
            # used for conversion
            corpusPath = self.corpusPathToKey(filePath)
            accessPath = filePath
            if accessPath.startswith(music21Path):
                accessPath = os.path.join(
                    'music21',
                    os.path.relpath(filePath, music21Path),
                    )
            # a version of the path that may not have a work number
            if corpusPath in self.storage:
                self.storage[corpusPath].accessPath = accessPath
                updateCount += 1
                # get all but last underscore
                corpusPathStub = '_'.join(corpusPath.split('_')[:-1]) 
                for key in self.storage.viewkeys():
                    if key.startswith(corpusPathStub):
                        self.storage[key].accessPath = accessPath
                        updateCount += 1
        return updateCount

    def write(self):
        '''
        Write the JSON storage of all Metadata or 
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
