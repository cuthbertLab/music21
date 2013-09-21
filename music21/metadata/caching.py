# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         caching.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
#               Project 
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------


import multiprocessing
import os
import pickle
import time
import traceback
import unittest

from music21 import common
from music21 import exceptions21


#------------------------------------------------------------------------------


from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))


#------------------------------------------------------------------------------


class MetadataCacheException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------


def cacheMetadata(
    domains=('local', 'core', 'virtual'),
    useMultiprocessing=True,
    ):
    '''
    Cache metadata from corpuses in `domains` as local cache files:

    ::

        >>> metadata.cacheMetadata(
        ...     domains='core', 
        ...     useMultiprocessing=False,
        ...     )

    '''
    from music21 import corpus
    from music21 import metadata

    if not common.isListLike(domains):
        domains = (domains,)

    timer = common.Timer()
    timer.start()

    # store list of file paths that caused an error
    failingFilePaths = []

    domainGetPathsProcedures = {
       'core': corpus.getCorePaths,
       'local': corpus.getLocalPaths,
       'virtual': corpus.getVirtualPaths,
       }

    # the core cache is based on local files stored in music21
    # virtual is on-line
    for domain in domains:
        # the domain passed here becomes the name of the bundle
        # determines the file name of the json bundle
        metadataBundle = metadata.MetadataBundle(domain)
        if domain not in domainGetPathsProcedures:
            raise MetadataCacheException('invalid domain provided: {0}'.format(
                domain))
        if os.path.exists(metadataBundle.filePath):
            metadataBundle.read()
        paths = domainGetPathsProcedures[domain]()
        environLocal.warn(
            'metadata cache: starting processing of paths: {0}'.format(
                len(paths)))
        # returns any paths that failed to load
        failingFilePaths += metadataBundle.addFromPaths(
            paths,
            useMultiprocessing=useMultiprocessing,
            )
        environLocal.warn(
            'cache: writing time: {0} md items: {1}'.format(
                timer, len(metadataBundle)))
        del metadataBundle

    environLocal.warn('cache: final writing time: {0} seconds'.format(timer))
    for failingFilePath in failingFilePaths:
        environLocal.warn('path failed to parse: {0}'.format(failingFilePath))


#------------------------------------------------------------------------------


class MetadataCachingJob(object):
    '''
    Parses one corpus path, and attempts to extract metadata from it:

    ::

        >>> job = metadata.MetadataCachingJob(
        ...     'bach/bwv66.6',
        ...     useCorpus=True,
        ...     )
        >>> job()
        ((<music21.metadata.bundles.MetadataEntry: bach_bwv66_6>,), ())
        >>> results = job.getResults()
        >>> errors = job.getErrors()

    '''
    
    ### INITIALIZER ###

    def __init__(self, filePath, jobNumber=0, useCorpus=True):
        self.filePath = filePath
        self.filePathErrors = []
        self.jobNumber = int(jobNumber)
        self.results = []
        self.useCorpus = bool(useCorpus)

    ### SPECIAL METHODS ###

    def __call__(self):
        import gc
        self.results = []
        parsedObject = self._parseFilePath()
        if parsedObject is not None:
            if 'Opus' in parsedObject.classes:
                self._parseOpus(parsedObject)
            else:
                self._parseNonOpus(parsedObject)
        del parsedObject
        gc.collect()
        return self.getResults(), self.getErrors()

    ### PRIVATE METHODS ###

    def _parseFilePath(self):
        from music21 import converter
        from music21 import corpus
        parsedObject = None
        try:
            if self.useCorpus is False:
                parsedObject = converter.parse(
                    self.filePath, forceSource=True)
            else:
                parsedObject = corpus.parse(
                    self.filePath, forceSource=True)
        except Exception, e:
            environLocal.warn('parse failed: {0}, {1}'.format(
                self.filePath, str(e)))
            self.filePathErrors.append(self.filePath)
        return parsedObject

    def _parseNonOpus(self, parsedObject):
        from music21 import metadata
        try:
            corpusPath = metadata.MetadataBundle.corpusPathToKey(
                self.filePath)
            if parsedObject.metadata is not None:
                richMetadata = metadata.RichMetadata()
                richMetadata.merge(parsedObject.metadata)
                richMetadata.update(parsedObject) # update based on Stream
                environLocal.printDebug(
                    'updateMetadataCache: storing: {0}'.format(corpusPath))
                metadataEntry = metadata.MetadataEntry(
                    sourcePath=self.filePath,
                    metadataPayload=richMetadata,
                    )
                self.results.append(metadataEntry)
            else:
                environLocal.warn(
                    'addFromPaths: got stream without metadata, '
                    'creating stub: {0}'.format(
                        os.path.relpath(self.filePath)))
                #metadataEntry = metadata.MetadataEntry(
                #    sourcePath=self.filePath,
                #    metadataPayload=None,
                #    )
        except Exception:
            environLocal.warn('Had a problem with extracting metadata '
            'for {0}, piece ignored'.format(self.filePath))
            traceback.print_exc()

    def _parseOpus(self, parsedObject):
        from music21 import metadata
        # need to get scores from each opus?
        # problem here is that each sub-work has metadata, but there
        # is only a single source file
        try:
            for scoreNumber, score in enumerate(parsedObject.scores):
                self._parseOpusScore(score, scoreNumber)
                del score # for memory conservation
        except Exception as exception:
            environLocal.warn(
                'Had a problem with extracting metadata for score {0} '
                'in {1}, whole opus ignored: {2}'.format(
                    scoreNumber, self.filePath, str(exception)))
            traceback.print_exc()
        else:
            # Create a dummy metadata entry, representing the entire opus.
            # This lets the metadata bundle know it has already processed this
            # entire opus on the next cache update.
            #metadataEntry = metadata.MetadataEntry(
            #    sourcePath=self.filePath,
            #    metadataPayload=None,
            #    )
            #self.results.append(metadataEntry)
            pass

    def _parseOpusScore(self, score, scoreNumber):
        from music21 import metadata
        try:
            # updgrade metadata to richMetadata
            richMetadata = metadata.RichMetadata()
            richMetadata.merge(score.metadata)
            richMetadata.update(score) # update based on Stream
            if score.metadata is None or score.metadata.number is None:
                environLocal.warn(
                    'addFromPaths: got Opus that contains '
                    'Streams that do not have work numbers: '
                    '{0}'.format(self.filePath))
            else:
                # update path to include work number
                corpusPath = metadata.MetadataBundle.corpusPathToKey(
                    self.filePath, 
                    number=score.metadata.number,
                    )
                environLocal.printDebug(
                    'addFromPaths: storing: {0}'.format(
                        corpusPath))
                metadataEntry = metadata.MetadataEntry(
                    sourcePath=self.filePath,
                    number=scoreNumber,
                    metadataPayload=richMetadata,
                    )
                self.results.append(metadataEntry)
        except Exception as exception:
            environLocal.warn(
                'Had a problem with extracting metadata '
                'for score {0} in {1}, whole opus ignored: '
                '{2}'.format(
                    scoreNumber, self.filePath, str(exception)))
            traceback.print_exc()

    ### PUBLIC METHODS ###

    def getErrors(self):
        return tuple(self.filePathErrors)

    def getResults(self):
        return tuple(self.results)


#------------------------------------------------------------------------------


class JobProcessor(object):
    '''
    Processes metadata-caching jobs, either serially (e.g. single-threaded) or
    in parallel, as a generator.

    Yields a dictionary of:
    
    * MetadataEntry instances
    * failed file paths
    * the last processed file path
    * the number of remaining jobs

    ::

        >>> jobs = []
        >>> for corpusPath in corpus.getMonteverdiMadrigals()[:5]:
        ...     job = metadata.MetadataCachingJob(
        ...         corpusPath,
        ...         useCorpus=True,
        ...         )
        ...     jobs.append(job)
        >>> jobGenerator = metadata.JobProcessor.process_serial(jobs)
        >>> for result in jobGenerator:
        ...     print result['metadataEntries'], result['remainingJobs']
        ...
        (<music21.metadata.bundles.MetadataEntry: monteverdi_madrigal_3_1_mxl>,) 4
        (<music21.metadata.bundles.MetadataEntry: monteverdi_madrigal_3_2_mxl>,) 3
        (<music21.metadata.bundles.MetadataEntry: monteverdi_madrigal_3_3_mxl>,) 2
        (<music21.metadata.bundles.MetadataEntry: monteverdi_madrigal_3_4_mxl>,) 1
        (<music21.metadata.bundles.MetadataEntry: monteverdi_madrigal_3_5_mxl>,) 0

    '''

    ### PUBLIC METHODS ###

    @staticmethod
    def process_parallel(jobs, processCount=None):
        processCount = processCount or multiprocessing.cpu_count() - 1
        if processCount < 1:
            processCount = 1
        remainingJobs = len(jobs)
        results = []
        filePathErrors = []
        job_queue = multiprocessing.JoinableQueue()
        result_queue = multiprocessing.Queue()
        workers = [WorkerProcess(job_queue, result_queue) 
            for i in range(processCount)]
        for worker in workers:
            worker.start()
        if jobs:
            for job in jobs:
                job_queue.put(pickle.dumps(job, protocol=0))
            for i in xrange(len(jobs)):
                job = pickle.loads(result_queue.get())
                results = job.getResults()
                errors = job.getErrors()
                remainingJobs -= 1
                yield {
                    'metadataEntries': results, 
                    'errors': errors, 
                    'filePath': job.filePath, 
                    'remainingJobs': remainingJobs,
                    }
        for worker in workers:
            job_queue.put(None)
        job_queue.join()
        result_queue.close()
        job_queue.close()
        for worker in workers:
            worker.join()
        raise StopIteration

    @staticmethod
    def process_serial(jobs):
        remainingJobs = len(jobs)
        results = []
        filePathErrors = []
        for i, job in enumerate(jobs):
            results, errors = job()
            remainingJobs -= 1
            yield {
                'metadataEntries': results, 
                'errors': errors, 
                'filePath': job.filePath, 
                'remainingJobs': remainingJobs,
                }
        raise StopIteration

    @staticmethod
    def report(totalJobs, remainingJobs, filePath, filePathErrorCount):
        message = 'updated {0} of {1} files; ' \
            'total errors: {2} ... last file: {3}'.format(
                totalJobs - remainingJobs,
                totalJobs,
                filePathErrorCount,
                filePath,
                )
        environLocal.warn(message)


#------------------------------------------------------------------------------


class WorkerProcess(multiprocessing.Process):
    '''
    A worker process for use by the multithreaded metadata-caching job
    processor.
    '''
    
    ### INITIALIZER ###

    def __init__(self, job_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.job_queue = job_queue
        self.result_queue = result_queue
        
    ### PUBLIC METHODS ###

    def run(self):
        while True:
            job = self.job_queue.get()
            # "Poison Pill" causes worker shutdown:
            if job is None:
                self.job_queue.task_done()
                break
            job = pickle.loads(job)
            job()
            self.job_queue.task_done()
            self.result_queue.put(pickle.dumps(job, protocol=0))
        return


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = ()

__all__ = [
    'JobProcessor',
    'MetadataCachingJob',
    'cacheMetadata',
    ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
