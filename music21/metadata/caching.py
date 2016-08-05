# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         caching.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------


import multiprocessing
import os
import pickle
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


def cacheMetadata(corpusNames=('local', 'core', 'virtual'),
                  useMultiprocessing=True,
                  verbose=False):
    '''
    Cache metadata from corpora in `corpusNames` as local cache files:

    Call as ``metadata.cacheMetadata()``

    '''
    from music21 import corpus
    from music21.corpus import corpora

    if not common.isIterable(corpusNames):
        corpusNames = (corpusNames,)

    timer = common.Timer()
    timer.start()

    # store list of file paths that caused an error
    failingFilePaths = []

    # the core cache is based on local files stored in music21
    # virtual is on-line
    for corpusName in corpusNames:
        if corpusName == 'core':
            metadataBundle = corpora.CoreCorpus().metadataBundle
            paths = corpus.getCorePaths()
            useCorpus = True
        elif corpusName == 'local':
            metadataBundle = corpora.LocalCorpus().metadataBundle
            paths = corpus.getLocalPaths()
            useCorpus = False
        elif corpusName == 'virtual':
            metadataBundle = corpora.VirtualCorpus().metadataBundle
            paths = corpus.getVirtualPaths()
            useCorpus = False
        else:
            message = 'invalid corpus name provided: {0!r}'.format(corpusName)
            raise MetadataCacheException(message)
        message = 'metadata cache: starting processing of paths: {0}'.format(
                len(paths))
        if verbose is True:
            environLocal.warn(message)
        else:
            environLocal.printDebug(message)

        failingFilePaths += metadataBundle.addFromPaths(
            paths,
            useCorpus=useCorpus,
            useMultiprocessing=useMultiprocessing,
            verbose=verbose
            )
        message = 'cache: writing time: {0} md items: {1}'.format(
            timer, len(metadataBundle))
        if verbose is True:
            environLocal.warn(message)
        else:
            environLocal.printDebug(message)
        del metadataBundle
    message = 'cache: final writing time: {0} seconds'.format(timer)
    if verbose is True:
        environLocal.warn(message)
    else:
        environLocal.printDebug(message)
    for failingFilePath in failingFilePaths:
        message = 'path failed to parse: {0}'.format(failingFilePath)
        if verbose is True:
            environLocal.warn(message)
        else:
            environLocal.printDebug(message)
            


#------------------------------------------------------------------------------


class MetadataCachingJob(object):
    '''
    Parses one corpus path, and attempts to extract metadata from it:

    >>> from music21 import metadata
    >>> job = metadata.caching.MetadataCachingJob(
    ...     'bach/bwv66.6',
    ...     useCorpus=True,
    ...     )
    >>> job.run()
    ((<music21.metadata.bundles.MetadataEntry: bach_bwv66_6>,), ())
    >>> results = job.getResults()
    >>> errors = job.getErrors()
    
    TODO: error list, nut just numbers needs to be reported back up.
    
    '''

    ### INITIALIZER ###

    def __init__(self, filePath, jobNumber=0, useCorpus=True):
        self.filePath = filePath
        self.filePathErrors = []
        self.jobNumber = int(jobNumber)
        self.results = []
        self.useCorpus = bool(useCorpus)

    def run(self):
        import gc
        self.results = []
        parsedObject = self.parseFilePath()
        environLocal.printDebug(
            'Got ParsedObject from {0}: {1}'.format(self.filePath, parsedObject))
        if parsedObject is not None:
            if 'Opus' in parsedObject.classes:
                self.parseOpus(parsedObject)
            else:
                self.parseNonOpus(parsedObject)
        del parsedObject
        gc.collect()
        return self.getResults(), self.getErrors()

    def parseFilePath(self):
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
        except Exception as e: # wide catch is fine. pylint: disable=broad-except
            environLocal.printDebug('parse failed: {0}, {1}'.format(
                self.filePath, str(e)))
            environLocal.printDebug(traceback.format_exc())
            self.filePathErrors.append(self.filePath)
        return parsedObject

    def parseNonOpus(self, parsedObject):
        from music21 import metadata
        try:
            corpusPath = metadata.bundles.MetadataBundle.corpusPathToKey(
                self.cleanFilePath)
            if parsedObject.metadata is not None:
                richMetadata = metadata.RichMetadata()
                richMetadata.merge(parsedObject.metadata)
                richMetadata.update(parsedObject)  # update based on Stream
                environLocal.printDebug(
                    'updateMetadataCache: storing: {0}'.format(corpusPath))
                metadataEntry = metadata.bundles.MetadataEntry(
                    sourcePath=self.cleanFilePath,
                    metadataPayload=richMetadata,
                    )
                self.results.append(metadataEntry)
            else:
                environLocal.printDebug(
                    'addFromPaths: got stream without metadata, '
                    'creating stub: {0}'.format(
                        common.relativepath(self.cleanFilePath)))
                metadataEntry = metadata.bundles.MetadataEntry(
                    sourcePath=self.cleanFilePath,
                    metadataPayload=None,
                    )
                self.results.append(metadataEntry)
        except Exception: # wide catch is fine. pylint: disable=broad-except
            environLocal.warn('Had a problem with extracting metadata '
            'for {0}, piece ignored'.format(self.filePath))
            environLocal.warn(traceback.format_exc())

    def parseOpus(self, parsedObject):
        from music21 import metadata
        # need to get scores from each opus?
        # problem here is that each sub-work has metadata, but there
        # is only a single source file
        try:
            for scoreNumber, score in enumerate(parsedObject.scores):
                self.parseOpusScore(score, scoreNumber)
                del score  # for memory conservation
        except Exception as exception: # wide catch is fine. pylint: disable=broad-except
            environLocal.warn(
                'Had a problem with extracting metadata for score {0} '
                'in {1}, whole opus ignored: {2}'.format(
                    scoreNumber, self.filePath, str(exception)))
            environLocal.printDebug(traceback.format_exc())
        # Create a dummy metadata entry, representing the entire opus.
        # This lets the metadata bundle know it has already processed this
        # entire opus on the next cache update.
        metadataEntry = metadata.bundles.MetadataEntry(
            sourcePath=self.cleanFilePath,
            metadataPayload=None,
            )
        self.results.append(metadataEntry)

    def parseOpusScore(self, score, scoreNumber):
        # scoreNumber is a zeroIndexed value.
        # score.metadata.number is the retrieval code; which is
        # probably 1 indexed, and might have gaps
        from music21 import metadata
        try:
            # updgrade metadata to richMetadata
            richMetadata = metadata.RichMetadata()
            richMetadata.merge(score.metadata)
            richMetadata.update(score)  # update based on Stream
            if score.metadata is None or score.metadata.number is None:
                environLocal.printDebug(
                    'addFromPaths: got Opus that contains '
                    'Streams that do not have work numbers: '
                    '{0}'.format(self.filePath))
            else:
                # update path to include work number
                corpusPath = metadata.bundles.MetadataBundle.corpusPathToKey(
                    self.cleanFilePath,
                    number=score.metadata.number,
                    )
                environLocal.printDebug(
                    'addFromPaths: storing: {0}'.format(
                        corpusPath))
                metadataEntry = metadata.bundles.MetadataEntry(
                    sourcePath=self.cleanFilePath,
                    number=score.metadata.number,
                    metadataPayload=richMetadata,
                    )
                self.results.append(metadataEntry)
        except Exception as exception: # pylint: disable=broad-except
            environLocal.warn(
                'Had a problem with extracting metadata '
                'for score {0} in {1}, whole opus ignored: '
                '{2}'.format(
                    scoreNumber, self.filePath, str(exception)))
            environLocal.printDebug(traceback.format_exc())

    ### PUBLIC METHODS ###

    def getErrors(self):
        return tuple(self.filePathErrors)

    def getResults(self):
        return tuple(self.results)

    ### PUBLIC PROPERTIES ###

    @property
    def cleanFilePath(self):
        corpusPath = os.path.abspath(common.getCorpusFilePath())
        if self.filePath.startswith(corpusPath):
            cleanFilePath = common.relativepath(self.filePath, corpusPath)
        else:
            cleanFilePath = self.filePath
        return cleanFilePath


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

    >>> jobs = []
    >>> for corpusPath in corpus.getMonteverdiMadrigals()[:3]:
    ...     job = metadata.caching.MetadataCachingJob(
    ...         corpusPath,
    ...         useCorpus=True,
    ...         )
    ...     jobs.append(job)
    >>> jobGenerator = metadata.caching.JobProcessor.process_serial(jobs)
    >>> for result in jobGenerator:
    ...     print(result['remainingJobs'])
    ...
    2
    1
    0
    '''

    ### PRIVATE METHODS ###

    @staticmethod
    def _report(totalJobs, remainingJobs, filePath, filePathErrorCount):
        '''
        Report on the current job status.
        '''
        message = 'updated {0} of {1} files; total errors: {2} ... last file: {3}'.format(
                totalJobs - remainingJobs,
                totalJobs,
                filePathErrorCount,
                filePath,
                )
        return message

    ### PUBLIC METHODS ###

    @staticmethod
    def process_parallel(jobs, processCount=None):
        '''
        Process jobs in parallel, with `processCount` processes.

        If `processCount` is none, use 1 fewer process than the number of
        available cores.
        
        jobs is a list of :class:`~music21.metadata.MetadataCachingJob` objects.
        
        '''
        processCount = processCount or common.cpus()  # @UndefinedVariable
        if processCount < 1:
            processCount = 1
        remainingJobs = len(jobs)
        if processCount > remainingJobs: # do not start more processes than jobs...
            processCount = remainingJobs
            
        environLocal.printDebug(
            'Processing {0} jobs in parallel, with {1} processes.'.format(
                remainingJobs, processCount))
        results = []
        job_queue = multiprocessing.JoinableQueue() # @UndefinedVariable
        result_queue = multiprocessing.Queue() # @UndefinedVariable
        workers = [WorkerProcess(job_queue, result_queue)
            for _ in range(processCount)]
        for worker in workers:
            worker.start()
        if jobs:
            for job in jobs:
                job_queue.put(pickle.dumps(job, protocol=pickle.HIGHEST_PROTOCOL))
            for unused_jobCounter in range(len(jobs)):
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
        '''
        Process jobs serially.
        '''
        remainingJobs = len(jobs)
        results = []
        for job in jobs:
            results, errors = job.run()
            remainingJobs -= 1
            yield {
                'metadataEntries': results,
                'errors': errors,
                'filePath': job.filePath,
                'remainingJobs': remainingJobs,
                }
        raise StopIteration


#------------------------------------------------------------------------------


class WorkerProcess(multiprocessing.Process): # @UndefinedVariable pylint: disable=inherit-non-class
    '''
    A worker process for use by the multithreaded metadata-caching job
    processor.
    '''

    ### INITIALIZER ###

    def __init__(self, job_queue, result_queue):
        super(WorkerProcess, self).__init__()
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
            job.run()
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
