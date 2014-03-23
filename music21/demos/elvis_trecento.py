# -*- coding: utf-8 -*-

'''
Demos of research dene on automatic reduction of chords in the Trecento
repertory.

Used by Josiah and Myke for the ELVIS project
'''
import multiprocessing
import pickle
from music21 import analysis
from music21 import base
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
            for i in range(multiprocessing.cpu_count() * 2)]
        for worker in workers:
            worker.start()
        for job in jobs:
            jobQueue.put(pickle.dumps(job, protocol=0))
        for i in xrange(len(jobs)):
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
            job()
            self.jobQueue.task_done()
            self.resultQueue.put(pickle.dumps(job, protocol=0))
        return


class NGramJob(base.SlottedObject):

    ### CLASS VARIABLES ###

    __slots__ = (
        'filename',
        'chordifiedNGrams',
        'reducedNGrams',
        )

    ### INITIALIZER ###

    def __init__(self, filename):
        self.filename = filename
        self.chordifiedNGrams = None
        self.reducedNGrams = None

    ### SPECIAL METHODS ###

    def __call__(self):
        score = corpus.parse('trecento/' + self.filename).measures(1, 30)
        chordReducer = analysis.reduceChords.ChordReducer()
        reduction = chordReducer(score).parts[0]
        chordifiedNGrams = self.computeNGrams(reduction)
        chordified = score.chordify()
        reducedNGrams = self.computeNGrams(chordified)
        self.chordifiedNGrams = chordifiedNGrams
        self.reducedNGrams = reducedNGrams

    ### PUBLIC METHODS ###

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
    import pprint
    filename = 'PMFC_06_Giovanni-05_Donna_Gia_Fu_Leggiadra.xml'
    jobs = [NGramJob(filename)]
    processedJobs = NGramJobHandler.execute(jobs)
    chordifiedNGrams = processedJobs[0].chordifiedNGrams
    reducedNGrams = processedJobs[0].reducedNGrams
    pprint.pprint(chordifiedNGrams)
    pprint.pprint(reducedNGrams)
