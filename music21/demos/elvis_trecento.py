# -*- coding: utf-8 -*-

'''
Demos of research done on automatic reduction of chords in the Trecento
repertory.

Used by Josiah and Myke for the ELVIS project
'''
import multiprocessing
import pickle
from music21 import analysis
from music21 import common
from music21 import corpus
from music21 import interval


class NGramJobHandler(object):
    r'''Processes ``QuantizationJob`` instances in parallel,
    based on the number of CPUs available.
    '''

    ### PUBLIC METHODS ###

    @staticmethod
    def execute(jobs):
        finishedJobs = []
        jobQueue = multiprocessing.JoinableQueue()
        resultQueue = multiprocessing.Queue()
        workers = [NGramJobHandlerWorker(jobQueue, resultQueue)
            for i in range(multiprocessing.cpu_count() / 2)]
        for worker in workers:
            worker.start()
        for job in jobs:
            jobQueue.put(pickle.dumps(job, protocol=0))
        for i in range(len(jobs)):
            finishedJobs.append(pickle.loads(resultQueue.get()))
        for worker in workers:
            jobQueue.put(None)
        jobQueue.join()
        resultQueue.close()
        jobQueue.close()
        for worker in workers:
            worker.join()
        return finishedJobs


class NGramJobHandlerWorker(multiprocessing.Process):
    r'''Worker process which runs ``QuantizationJobs``.

    Not composer-safe.

    Used internally by ``ParallelJobHandler``.
    '''

    ### INITIALIZER ###

    def __init__(self, jobQueue=None, resultQueue=None):
        multiprocessing.Process.__init__(self)
        jobQueue = jobQueue or ()
        resultQueue = resultQueue or ()
        self.jobQueue = jobQueue
        self.resultQueue = resultQueue

    ### PUBLIC METHODS ###

    def run(self):
        r'''Runs parallel job handler worker.

        Returns none.
        '''
        while True:
            job = self.jobQueue.get()
            if job is None:
                # poison pill causes worker shutdown
                #print '{}: Exiting'.format(process_name)
                self.jobQueue.task_done()
                break
            #print '{}: {!r}'.format(process_name, job)
            job = pickle.loads(job)
            job.run()
            self.jobQueue.task_done()
            self.resultQueue.put(pickle.dumps(job, protocol=0))
        return


class NGramJob(common.SlottedObject):

    ### CLASS VARIABLES ###

    __slots__ = (
        'filename',
        'jobNumber',
        'jobTotal',
        'results',
        )

    ### INITIALIZER ###

    def __init__(self, filename, jobNumber=0, jobTotal=0):
        self.filename = filename
        self.jobNumber = jobNumber
        self.jobTotal = jobTotal
        self.results = {}

    def run(self):
        score = corpus.parse(self.filename)
        self.debug('PARSED')
        if 2 < len(score.parts):
            self.debug('MORE THAN TWO PARTS')
            self.results = None
            return
        chordifiedScore = score.chordify()
        self.debug('CHORDIFIED')
        try:
            chordReducer = analysis.reduceChords.ChordReducer()
            reducedScore = chordReducer(score).parts[0]
        except AssertionError as e:
            self.debug('REDUCTION ERROR')
            print(e)
            return
        self.debug('REDUCED')
        self.results['chordified'] = []
        self.results['reduced'] = []
        for i in range(1, 5):
            ngrams = self.computeNGrams(reducedScore, nGramLength=i)
            self.results['chordified'].append(ngrams)
            self.debug('NGRAMS: {}'.format(i))
        for i in range(1, 5):
            ngrams = self.computeNGrams(chordifiedScore, nGramLength=i)
            self.results['reduced'].append(ngrams)
            self.debug('NGRAMS: {}'.format(i))
        self.debug('DONE!')

    ### PUBLIC METHODS ###

    def debug(self, message):
        print('[{}/{}] {}: {}'.format(
            self.jobNumber,
            self.jobTotal,
            self.filename,
            message,
            ))

    def iterateChordsNwise(self, chords, n=2):
        chordBuffer = []
        for chord in chords:
            if not chordBuffer or chord.pitches != chordBuffer[-1].pitches:
                chordBuffer.append(chord)
            if len(chordBuffer) == n:
                yield(tuple(chordBuffer))
                chordBuffer.pop(0)

    def chordToIntervalString(self, chord):
        if len(chord) == 1:
            intervalString = 'P1'
        else:
            intervalString = interval.Interval(chord[0], chord[1]).name
        return intervalString

    def chordsToBassMelodictIntervalString(self, chordOne, chordTwo):
        bassPitchOne = min(chordOne)
        bassPitchTwo = min(chordTwo)
        bassMelodicInterval = interval.Interval(bassPitchOne, bassPitchTwo)
        bassMelodicIntervalString = bassMelodicInterval.directedName
        return bassMelodicIntervalString

    def computeNGrams(self, part, nGramLength=2):
        stripped = part.stripTies(matchByPitch=True)
        allChords = tuple(stripped.flat.getElementsByClass('Chord'))
        nGrams = []
        for chords in self.iterateChordsNwise(allChords, n=nGramLength):
            nGram = []
            intervalString = self.chordToIntervalString(chords[0])
            nGram.append(intervalString)
            for chordOne, chordTwo in self.iterateChordsNwise(chords, n=2):
                bassMelodicIntervalString = \
                    self.chordsToBassMelodictIntervalString(
                        chordOne, chordTwo)
                nGram.append(bassMelodicIntervalString)
                intervalString = self.chordToIntervalString(chordTwo)
                nGram.append(intervalString)
            nGrams.append(tuple(nGram))
        return nGrams

    def hashNGrams(self, nGrams):
        import collections
        nGramDict = collections.Counter()
        for nGram in nGrams:
            nGramDict[nGram] += 1
        sortedDict = tuple(nGramDict.most_common())
        return sortedDict


if __name__ == '__main__':
    import os
    import json
    coreCorpus = corpus.CoreCorpus()
    paths = [x for x in coreCorpus.getPaths() if 'trecento' in x]
    #paths = paths[:2]
    paths = [os.path.join('trecento', os.path.split(x)[-1]) for x in paths]
    jobs = []
    jobTotal = len(paths)
    for i, path in enumerate(paths):
        job = NGramJob(
            path,
            jobNumber=i,
            jobTotal=jobTotal,
            )
        jobs.append(job)
    processedJobs = NGramJobHandler.execute(jobs)
    processedJobs.sort(key=lambda x: x.filename)
    result = {}
    failedJobs = []
    for job in processedJobs:
        if job.results:
            result[job.filename] = job.results
        elif job.results is not None:
            failedJobs.append(job)
    formattedResult = json.dumps(
        result,
        indent=4,
        separators=(',', ': '),
        sort_keys=True,
        )
    formattedResult = 'ngrams = ' + formattedResult
    outputDirectory = os.path.abspath(os.path.dirname(__file__))
    outputFilename = os.path.join(outputDirectory, 'elvis_trecento_results.py')
    with open(outputFilename, 'w') as f:
        f.write(formattedResult)
    if failedJobs:
        print('FAILURES:')
        for failedJob in failedJobs:
            print('\t{}'.format(failedJob.filename))
