# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         bundles.py
# Purpose:      music21 classes for representing score and work metadata
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Josiah Oberholtzer
#
# Copyright:    Copyright © 2010, 2012-14, '17, '19-20
#               Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
import gzip
import os
import pathlib
import pickle
import time
import unittest

from collections import OrderedDict

from music21 import common
from music21.common.fileTools import readPickleGzip
from music21 import exceptions21
from music21 import prebase

# -----------------------------------------------------------------------------
__all__ = [
    'MetadataEntry',
    'MetadataBundle',
    'MetadataBundleException',
]


from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))


class MetadataBundleException(exceptions21.Music21Exception):
    pass

# -----------------------------------------------------------------------------


class MetadataEntry(prebase.ProtoM21Object):
    '''
    An entry in a metadata bundle.

    The metadata entry holds information about the source of the metadata,
    and can be parsed to reconstitute the score object the metadata was
    derived from:

    >>> from music21 import metadata
    >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
    >>> metadataEntry = coreBundle.search('bwv66.6')[0]
    >>> metadataEntry
    <music21.metadata.bundles.MetadataEntry 'bach_bwv66_6_mxl'>

    The sourcePath of the metadata entry refers to the file path at which its
    score file is found:

    >>> metadataEntry.sourcePath
    PosixPath('bach/bwv66.6.mxl')

    The metadata property contains its :class:`~music21.metadata.RichMetadata` object:

    >>> metadataEntry.metadata
    <music21.metadata.RichMetadata id=0x...>

    Note that the id is not necessarily the current memory location.

    And the metadata entry can be parsed:

    >>> metadataEntry.parse()
    <music21.stream.Score ...>
    '''

    # INITIALIZER #

    def __init__(self,
                 sourcePath=None,
                 number=None,
                 metadataPayload=None,
                 corpusName=None,
                 ):
        self._sourcePath = str(sourcePath)
        self._number = number
        self._metadataPayload = metadataPayload
        self._corpusName = corpusName

    # SPECIAL METHODS #

    def __getnewargs__(self):
        return (
            self.sourcePath,
            self.metadata,
            self.number,
        )

    def _reprInternal(self):
        return repr(self.corpusPath)

    def __fspath__(self):
        '''
        for Py3.6 to allow MetadataEntries to be used where file paths are being employed

        Returns self.sourcePath() as a string

        >>> mde1 = metadata.bundles.MetadataEntry(sourcePath='/tmp/myFile.xml')
        >>> mde1.__fspath__()
        '/tmp/myFile.xml'
        '''
        return self._sourcePath

    # PUBLIC METHODS #

    def parse(self):
        from music21 import corpus
        if self.number is not None:
            return corpus.parse(self.sourcePath, number=self.number)
        else:
            return corpus.parse(self.sourcePath)

    def show(self, showFormat=None):
        score = self.parse()
        score.show(showFormat)

    def search(self, query=None, field=None, **kwargs):
        # runs search on the RichMetadata object
        return self.metadata.search(query, field, **kwargs)

    # PUBLIC PROPERTIES #

    @property
    def corpusPath(self):
        return MetadataBundle.corpusPathToKey(self.sourcePath, self.number)

    @property
    def metadata(self):
        '''
        Returns the Metadata object that is stored in the bundle.
        '''
        return self._metadataPayload

    @property
    def number(self):
        return self._number

    @property
    def sourcePath(self):
        return pathlib.Path(self._sourcePath)

    @property
    def corpusName(self):
        return self._corpusName


# -----------------------------------------------------------------------------


class MetadataBundle(prebase.ProtoM21Object):
    r'''
    An object that provides access to, searches within, and stores and loads
    multiple Metadata objects.

    >>> from music21 import corpus, metadata
    >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
    >>> coreBundle
    <music21.metadata.bundles.MetadataBundle 'core': {151... entries}>

    >>> searchResults = coreBundle.search('bach', field='composer')
    >>> searchResults
    <music21.metadata.bundles.MetadataBundle {363 entries}>

    >>> resultsEntries = searchResults.search('3/4')
    >>> resultsEntries
    <music21.metadata.bundles.MetadataBundle {40 entries}>


    Results are ordered by their source path:

    >>> resultsEntries[0]
    <music21.metadata.bundles.MetadataEntry 'bach_bwv11_6_mxl'>

    To get a score out of the entry, call .parse()

    >>> resultsEntries[0].parse()
    <music21.stream.Score ...>

    Or pass it into converter:

    >>> converter.parse(resultsEntries[0])
    <music21.stream.Score ...>


    A metadata bundle can be instantiated in three ways, (1) from a ``Corpus`` instance,
    or (2) a string indicating which corpus name to draw from, and then calling
    .read() or (3) by calling
    .metadataBundle on a corpus object.  This
    calls `.read()` automatically:


    Method 1:

    >>> coreCorpus = corpus.corpora.CoreCorpus()
    >>> coreBundle = metadata.bundles.MetadataBundle(coreCorpus)
    >>> localCorpus = corpus.corpora.LocalCorpus()
    >>> localBundle = metadata.bundles.MetadataBundle(localCorpus)

    Method 2:

    >>> coreBundle = metadata.bundles.MetadataBundle('core')
    >>> localBundle = metadata.bundles.MetadataBundle('local')

    After calling these you'll need to call ``read()``:

    >>> coreBundle
    <music21.metadata.bundles.MetadataBundle 'core': {0 entries}>
    >>> coreBundle.read()
    <music21.metadata.bundles.MetadataBundle 'core': {151... entries}>
    >>> coreBundle
    <music21.metadata.bundles.MetadataBundle 'core': {151... entries}>

    Method 3:

    >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
    >>> localBundle = corpus.corpora.LocalCorpus().metadataBundle

    >>> coreBundle
    <music21.metadata.bundles.MetadataBundle 'core': {151... entries}>



    Additionally, any two metadata bundles can be operated on together as
    though they were sets, allowing us to build up more complex searches:

    >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
    >>> bachBundle = coreBundle.search(
    ...     'bach',
    ...     field='composer',
    ...     )
    >>> bachBundle
    <music21.metadata.bundles.MetadataBundle {363 entries}>
    >>> tripleMeterBundle = coreBundle.search('3/4')
    >>> tripleMeterBundle
    <music21.metadata.bundles.MetadataBundle {1875 entries}>
    >>> bachBundle.intersection(tripleMeterBundle)
    <music21.metadata.bundles.MetadataBundle {40 entries}>

    Finally, a metadata bundle need not be associated with any corpus at all,
    and can be populated ad hoc:

    >>> anonymousBundle = metadata.bundles.MetadataBundle()
    >>> mdb = corpus.corpora.CoreCorpus().search('monteverdi')[:4]
    >>> paths = [common.getCorpusFilePath() / x.sourcePath for x in mdb]
    >>> failedPaths = anonymousBundle.addFromPaths(
    ...     paths, useMultiprocessing=False)
    >>> failedPaths
    []
    >>> anonymousBundle
    <music21.metadata.bundles.MetadataBundle {4 entries}>
    '''

    # INITIALIZER #

    def __init__(self, expr=None):
        from music21 import corpus
        self._metadataEntries = OrderedDict()
        if not isinstance(expr, (str, corpus.corpora.Corpus, type(None))):
            raise MetadataBundleException('Need to take a string, corpus, or None as expression')

        self._corpus = None

        if isinstance(expr, corpus.corpora.Corpus):
            self._name = expr.name
            self.corpus = expr
        else:
            self._name = expr
            self.corpus = None

    # SPECIAL METHODS #

    def __and__(self, metadataBundle):
        r'''
        Compute the set-wise `and` of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>
        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>
        >>> bachBundle & tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {40 entries}>

        Returns a new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            '__and__',
        )

    def __eq__(self, other):
        '''
        True if `expr` is of the same type, and contains an identical set of
        entries, otherwise false:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )
        >>> bachBundle == corelliBundle
        False
        >>> bachBundle == coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        True
        >>> bachBundle == 'foo'
        False

        '''
        if hasattr(other, '_metadataEntries'):
            if self._metadataEntries == other._metadataEntries:
                return True
        return False

    def __ge__(self, metadataBundle):
        '''
        True when one metadata bundle is either a superset or an identical set
        to another bundle:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )
        >>> bachBundle >= bachBundle
        True
        >>> bachBundle >= corelliBundle
        False
        >>> bachBundle >= coreBundle
        False
        >>> corelliBundle >= bachBundle
        False
        >>> corelliBundle >= corelliBundle
        True
        >>> corelliBundle >= coreBundle
        False
        >>> coreBundle >= bachBundle
        True
        >>> coreBundle >= corelliBundle
        True
        >>> coreBundle >= coreBundle
        True

        Returns boolean.
        '''
        return self._apply_set_predicate(metadataBundle, '__ge__')

    def __getitem__(self, i):
        return list(self._metadataEntries.values())[i]

    def __gt__(self, metadataBundle):
        '''
        True when one metadata bundle is either a subset or an identical set to
        another bundle:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )
        >>> bachBundle > bachBundle
        False
        >>> bachBundle > corelliBundle
        False
        >>> bachBundle > coreBundle
        False
        >>> corelliBundle > bachBundle
        False
        >>> corelliBundle > corelliBundle
        False
        >>> corelliBundle > coreBundle
        False
        >>> coreBundle > bachBundle
        True
        >>> coreBundle > corelliBundle
        True
        >>> coreBundle > coreBundle
        False


        Returns boolean.
        '''
        return self._apply_set_predicate(metadataBundle, '__gt__')

    def __le__(self, metadataBundle):
        '''
        True when one metadata bundle is either a subset or an identical set to
        another bundle:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )

        >>> bachBundle <= bachBundle
        True
        >>> bachBundle <= corelliBundle
        False
        >>> bachBundle <= coreBundle
        True
        >>> corelliBundle <= bachBundle
        False
        >>> corelliBundle <= corelliBundle
        True
        >>> corelliBundle <= coreBundle
        True
        >>> coreBundle <= bachBundle
        False
        >>> coreBundle <= corelliBundle
        False
        >>> coreBundle <= coreBundle
        True

        Returns boolean.
        '''
        return self._apply_set_predicate(metadataBundle, '__le__')

    def __len__(self):
        return len(self._metadataEntries)

    def __lt__(self, metadataBundle):
        '''
        True when one metadata bundle is a subset of another bundle:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )
        >>> bachBundle < bachBundle
        False
        >>> bachBundle < corelliBundle
        False
        >>> bachBundle < coreBundle
        True
        >>> corelliBundle < bachBundle
        False
        >>> corelliBundle < corelliBundle
        False
        >>> corelliBundle < coreBundle
        True
        >>> coreBundle < bachBundle
        False
        >>> coreBundle < corelliBundle
        False
        >>> coreBundle < coreBundle
        False

        Return boolean.
        '''
        return self._apply_set_predicate(metadataBundle, '__lt__')

    def __or__(self, metadataBundle):
        r'''
        Compute the set-wise `or` of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>
        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )
        >>> corelliBundle
        <music21.metadata.bundles.MetadataBundle {1 entry}>
        >>> bachBundle | corelliBundle
        <music21.metadata.bundles.MetadataBundle {364 entries}>

        Returns a new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            '__or__',
        )

    def _reprInternal(self):
        if len(self) == 1:
            status = '{1 entry}'
        else:
            status = '{' + str(len(self)) + ' entries}'

        if self.name is not None:
            status = f'{self.name!r}: {status}'
        return status

    def __sub__(self, metadataBundle):
        r'''
        Compute the set-wise `subtraction` of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>
        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>
        >>> bachBundle - tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {323 entries}>

        Returns a new metadata bundle.

        >>> bachBundle - bachBundle
        <music21.metadata.bundles.MetadataBundle {0 entries}>
        '''
        return self._apply_set_operation(
            metadataBundle,
            '__sub__',
        )

    def __xor__(self, metadataBundle):
        r'''
        Compute the set-wise `exclusive or` of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>
        >>> bachBundle ^ tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {2158 entries}>

        Returns a new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            '__xor__',
        )

    # PRIVATE METHODS #

    def _apply_set_operation(self, metadataBundle, operator):
        if not isinstance(metadataBundle, type(self)):
            raise MetadataBundleException('metadataBundle must be a MetadataBundle')
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

        mdbItems = list(resultBundle._metadataEntries.items())
        resultBundle._metadataEntries = OrderedDict(sorted(mdbItems,
                                                           key=lambda mde: mde[1].sourcePath))
        return resultBundle

    def _apply_set_predicate(self, metadataBundle, predicate):
        '''
        Applies a predicate such as '__or__' to self and another metadataBundle.
        '''
        if not isinstance(metadataBundle, type(self)):
            raise MetadataBundleException('metadataBundle must be a MetadataBundle')
        selfKeys = set(self._metadataEntries.keys())
        otherKeys = set(metadataBundle._metadataEntries.keys())
        return getattr(selfKeys, predicate)(otherKeys)

    # PUBLIC PROPERTIES #

    # PUBLIC PROPERTIES #

    @property
    def corpus(self):
        r'''
        The `corpus.corpora.Corpus` object associated with the metadata
        bundle's name.

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> coreBundle
        <music21.metadata.bundles.MetadataBundle 'core': {151... entries}>
        >>> coreBundle.corpus
        <music21.corpus.corpora.CoreCorpus>
        '''
        if self._corpus is not None:
            cObj = common.unwrapWeakref(self._corpus)
            if cObj is not None:
                return cObj

        if self.name is None:
            return None

        from music21.corpus import manager
        return manager.fromName(self.name)

    @corpus.setter
    def corpus(self, newCorpus):
        self._corpus = common.wrapWeakref(newCorpus)

    @property
    def filePath(self):
        r'''
        The filesystem name of the cached metadata bundle, if the metadata
        bundle's name is not None.

        >>> ccPath = corpus.corpora.CoreCorpus().metadataBundle.filePath
        >>> ccPath.name
        'core.p.gz'
        >>> '_metadataCache' in ccPath.parts
        True

        >>> localPath = corpus.corpora.LocalCorpus().metadataBundle.filePath
        >>> localPath.name
        'local.p.gz'

        Local corpora metadata is stored in the scratch dir, not the
        corpus directory

        >>> '_metadataCache' in localPath.parts
        False

        >>> funkCorpus = corpus.corpora.LocalCorpus('funk')
        >>> funkPath = funkCorpus.metadataBundle.filePath
        >>> funkPath.name
        'local-funk.p.gz'
        '''
        c = self.corpus
        if c is None:
            return None
        else:
            cfp = c.cacheFilePath
            if not isinstance(cfp, pathlib.Path):
                return pathlib.Path(cfp)
            else:
                return cfp

    @property
    def name(self):
        r'''
        The name of the metadata bundle.

        Can be 'core', 'local', '{name}' where name is the name
        of a named local corpus or None.

        The names 'core' and 'local' refer to the core and local
        corpora respectively: (virtual corpus is currently offline)

        >>> from music21 import metadata
        >>> metadata.bundles.MetadataBundle().name is None
        True
        >>> corpus.corpora.CoreCorpus().metadataBundle.name
        'core'

        >>> funkCorpus = corpus.corpora.LocalCorpus('funk')
        >>> funkCorpus.metadataBundle.name
        'funk'

        Return string or None.
        '''
        return self._name

    # PUBLIC METHODS #

    def addFromPaths(
        self,
        paths,
        parseUsingCorpus=False,
        useMultiprocessing=True,
        storeOnDisk=True,
        verbose=False
    ):
        '''
        Parse and store metadata from numerous files.

        If any files cannot be loaded, their file paths will be collected in a
        list that is returned.

        Returns a list of file paths with errors and stores the extracted
        metadata in `self._metadataEntries`.

        >>> from music21 import corpus, metadata
        >>> metadataBundle = metadata.bundles.MetadataBundle()
        >>> p = corpus.corpora.CoreCorpus().getWorkList('bach/bwv66.6')
        >>> metadataBundle.addFromPaths(
        ...     p,
        ...     parseUsingCorpus=False,
        ...     useMultiprocessing=False,
        ...     storeOnDisk=False, #_DOCS_HIDE
        ...     )
        []
        >>> len(metadataBundle._metadataEntries)
        1

        Set Verbose to True to get updates even if debug is off.
        '''
        from music21 import metadata
        jobs = []
        accumulatedResults = []
        accumulatedErrors = []
        if self.filePath is not None and self.filePath.exists():
            metadataBundleModificationTime = self.filePath.stat().st_ctime
        else:
            metadataBundleModificationTime = time.time()

        message = 'MetadataBundle Modification Time: {0}'.format(
            metadataBundleModificationTime)

        if verbose is True:
            environLocal.warn(message)
        else:
            environLocal.printDebug(message)

        currentJobNumber = 0
        skippedJobsCount = 0
        for path in paths:
            key = self.corpusPathToKey(path)
            if key in self._metadataEntries:
                pathModificationTime = path.stat().st_ctime
                if pathModificationTime < metadataBundleModificationTime:
                    skippedJobsCount += 1
                    continue
            currentJobNumber += 1
            corpusName = self.name
            if corpusName is None:
                corpusName = 'core'  # TODO: remove this after rebuilding

            if corpusName.startswith('local-'):
                corpusName = corpusName[6:]

            job = metadata.caching.MetadataCachingJob(
                path,
                jobNumber=currentJobNumber,
                parseUsingCorpus=parseUsingCorpus,
                corpusName=corpusName,
            )
            jobs.append(job)
        currentIteration = 0
        message = 'Skipped {0} sources already in cache.'.format(
            skippedJobsCount)
        if verbose is True:
            environLocal.warn(message)
        else:
            environLocal.printDebug(message)

        if useMultiprocessing:
            jobProcessor = metadata.caching.JobProcessor.process_parallel
        else:
            jobProcessor = metadata.caching.JobProcessor.process_serial
        for result in jobProcessor(jobs):
            message = metadata.caching.JobProcessor._report(
                len(jobs),
                result['remainingJobs'],
                result['filePath'],
                len(accumulatedErrors),
            )
            if verbose is True:
                environLocal.warn(message)
            else:
                environLocal.printDebug(message)

            currentIteration += 1
            accumulatedResults.extend(result['metadataEntries'])
            accumulatedErrors.extend(result['errors'])
            for metadataEntry in result['metadataEntries']:
                self._metadataEntries[metadataEntry.corpusPath] = metadataEntry
            if (currentIteration % 50) and (storeOnDisk is True) == 0:
                self.write()
        self.validate()
        if storeOnDisk is True:
            self.write()
        return accumulatedErrors

    def clear(self):
        r'''
        Clear all keys in a metadata bundle:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> bachBundle.clear()
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {0 entries}>

        Returns None.
        '''
        self._metadataEntries.clear()

    @staticmethod
    def corpusPathToKey(filePath, number=None):
        r'''
        Given a file path or corpus path, return the metadata key:

        >>> from music21 import metadata
        >>> mb = metadata.bundles.MetadataBundle()
        >>> key = mb.corpusPathToKey('bach/bwv1007/prelude')
        >>> key.endswith('bach_bwv1007_prelude')
        True

        >>> key = mb.corpusPathToKey('corelli/opus3no1/1grave.xml')
        >>> key.endswith('corelli_opus3no1_1grave_xml')
        True
        '''
        if isinstance(filePath, pathlib.Path):
            try:
                filePath = filePath.relative_to(common.getSourceFilePath() / 'corpus')
            except ValueError:
                pass

            parts = filePath.parts
            if parts[0] == '/' and len(parts) > 1:
                parts = parts[1:]

            corpusPath = '_'.join(parts)
        else:
            if 'corpus' in filePath:
                # get filePath after corpus
                corpusPath = filePath.split('corpus')[-1]
            else:
                corpusPath = filePath

            if corpusPath.startswith(os.sep):
                corpusPath = corpusPath[1:]
            corpusPath = corpusPath.replace('/', '_')
            corpusPath = corpusPath.replace(os.sep, '_')

        corpusPath = corpusPath.replace('.', '_')
        # append name to metadata path
        if number is not None:
            return '{0}_{1}'.format(corpusPath, number)
        return corpusPath

    def delete(self):
        r'''
        Delete the filesystem cache of a named metadata bundle.

        Does not delete the in-memory metadata bundle.

        Return none.
        '''
        if self.filePath is not None:
            if self.filePath.exists():
                self.filePath.unlink()
        return self

    def difference(self, metadataBundle):
        r'''
        Compute the set-wise difference of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle

        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>

        >>> bachBundle.difference(tripleMeterBundle)
        <music21.metadata.bundles.MetadataBundle {323 entries}>

        Returns a new metadata bundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            'difference',
        )

    def intersection(self, metadataBundle):
        r'''
        Compute the set-wise intersection of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle

        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>

        >>> bachBundle.intersection(tripleMeterBundle)
        <music21.metadata.bundles.MetadataBundle {40 entries}>

        Returns a new MetadataBundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            'intersection',
        )

    def isdisjoint(self, metadataBundle):
        r'''
        True if the set of keys in one metadata bundle are disjoint with
        the set of keys in another:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle

        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> corelliBundle = coreBundle.search(
        ...     'corelli',
        ...     field='composer',
        ...     )
        >>> corelliBundle
        <music21.metadata.bundles.MetadataBundle {1 entry}>

        >>> bachBundle.isdisjoint(corelliBundle)
        True

        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>

        >>> bachBundle.isdisjoint(tripleMeterBundle)
        False

        Returns boolean.
        '''
        return self._apply_set_predicate(metadataBundle, 'isdisjoint')

    def issubset(self, metadataBundle):
        r'''
        True if the set of keys in one metadata bundle are a subset of
        the keys in another:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle

        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> tripleMeterBachBundle = bachBundle.search('3/4')
        >>> tripleMeterBachBundle
        <music21.metadata.bundles.MetadataBundle {40 entries}>

        >>> tripleMeterBachBundle.issubset(bachBundle)
        True

        >>> bachBundle.issubset(tripleMeterBachBundle)
        False

        Returns boolean.
        '''
        return self._apply_set_predicate(metadataBundle, 'issubset')

    def issuperset(self, metadataBundle):
        r'''
        True if the set of keys in one metadata bundle are a superset of
        the keys in another:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle

        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>

        >>> tripleMeterBachBundle = bachBundle.search('3/4')
        >>> tripleMeterBachBundle
        <music21.metadata.bundles.MetadataBundle {40 entries}>

        >>> tripleMeterBachBundle.issuperset(bachBundle)
        False

        >>> bachBundle.issuperset(tripleMeterBachBundle)
        True

        Returns boolean.
        '''
        return self._apply_set_predicate(metadataBundle, 'issuperset')

    @staticmethod
    def listSearchFields():
        r'''
        List all available search field names:

        >>> for field in metadata.bundles.MetadataBundle.listSearchFields():
        ...     field
        ...
        'actNumber'
        'alternativeTitle'
        'ambitus'
        'associatedWork'
        'collectionDesignation'
        'commission'
        'composer'
        'copyright'
        'countryOfComposition'
        'date'
        'dedication'
        'groupTitle'
        'keySignatureFirst'
        'keySignatures'
        'localeOfComposition'
        'movementName'
        'movementNumber'
        'noteCount'
        'number'
        'numberOfParts'
        'opusNumber'
        'parentTitle'
        'pitchHighest'
        'pitchLowest'
        'popularTitle'
        'quarterLength'
        'sceneNumber'
        'sourcePath'
        'tempoFirst'
        'tempos'
        'textLanguage'
        'textOriginalLanguage'
        'timeSignatureFirst'
        'timeSignatures'
        'title'
        'volume'
        '''
        from music21 import metadata
        return tuple(sorted(metadata.RichMetadata.searchAttributes))

    def read(self, filePath=None):
        r'''
        Load cached metadata from the file path suggested by the name of this
        MetadataBundle ('core', 'local', or a name).

        If a specific filepath is given with the `filePath` keyword, attempt to
        load cached metadata from the file at that location.

        If `filePath` is None, and `self.filePath` is also None, do nothing.

        >>> #_DOCS_SHOW coreBundle = metadata.bundles.MetadataBundle('core').read()

        If a metadata is unnamed, and no file path is specified, an exception
        will be thrown:

        >>> anonymousBundle = metadata.bundles.MetadataBundle().read()
        Traceback (most recent call last):
        music21.exceptions21.MetadataException: Unnamed MetadataBundles have
            no default file path to read from.

        '''
        timer = common.Timer()
        timer.start()
        if filePath is None:
            filePath = self.filePath
        if filePath is None and self.name is None:
            raise exceptions21.MetadataException(
                'Unnamed MetadataBundles have no default file path to read '
                'from.')
        if not isinstance(filePath, pathlib.Path):
            filePath = pathlib.Path(filePath)

        if not filePath.exists():
            environLocal.printDebug('no metadata found for: {0!r}; '
                                    'try building cache with corpus.cacheMetadata({1!r})'.format(
                                        self.name, self.name))
            return self

        newMdb = readPickleGzip(filePath)
        self._metadataEntries = newMdb._metadataEntries

        environLocal.printDebug([
            'MetadataBundle: loading time:',
            self.name,
            timer(),
            'md items:',
            len(self._metadataEntries)
        ])
        return self

    def search(self, query=None, field=None, fileExtensions=None, **kwargs):
        r'''
        Perform search, on all stored metadata, permit regular expression
        matching.

        >>> workList = corpus.corpora.CoreCorpus().getWorkList('ciconia')
        >>> metadataBundle = metadata.bundles.MetadataBundle()
        >>> failedPaths = metadataBundle.addFromPaths(
        ...     workList,
        ...     parseUsingCorpus=False,
        ...     useMultiprocessing=False,
        ...     storeOnDisk=False, #_DOCS_HIDE
        ...     )
        >>> failedPaths
        []

        >>> searchResult = metadataBundle.search(
        ...     'cicon',
        ...     field='composer'
        ...     )
        >>> searchResult
        <music21.metadata.bundles.MetadataBundle {1 entry}>
        >>> len(searchResult)
        1
        >>> searchResult[0]
        <music21.metadata.bundles.MetadataEntry 'ciconia_quod_jactatur_xml'>
        >>> searchResult = metadataBundle.search(
        ...     'cicon',
        ...     field='composer',
        ...     fileExtensions=('.krn',),
        ...     )
        >>> len(searchResult)  # no files in this format
        0

        >>> searchResult = metadataBundle.search(
        ...     'cicon',
        ...     field='composer',
        ...     fileExtensions=('.xml',),
        ...     )
        >>> len(searchResult)
        1

        Searches can also use keyword args:

        >>> metadataBundle.search(composer='cicon')
        <music21.metadata.bundles.MetadataBundle {1 entry}>
        '''
        if fileExtensions is not None and not common.isIterable(fileExtensions):
            fileExtensions = [fileExtensions]

        newMetadataBundle = MetadataBundle()
        if query is None and field is None:
            if not kwargs:
                raise MetadataBundleException('Query cannot be empty')
            field, query = kwargs.popitem()

        for key in self._metadataEntries:
            metadataEntry = self._metadataEntries[key]
            # ignore stub entries
            if metadataEntry.metadata is None:
                continue
            sp = metadataEntry.sourcePath

            if metadataEntry.search(query, field)[0]:
                include = False
                if fileExtensions is not None:
                    for fileExtension in fileExtensions:
                        if fileExtension and fileExtension[0] != '.':
                            fileExtension = '.' + fileExtension

                        if sp.suffix == fileExtension:
                            include = True
                            break
                        elif (fileExtension.endswith('xml')
                                and sp.suffix in ('.mxl', '.mx')):
                            include = True
                            break
                else:
                    include = True
                if include and key not in newMetadataBundle._metadataEntries:
                    newMetadataBundle._metadataEntries[key] = metadataEntry
        newMetadataBundle._metadataEntries = OrderedDict(
            sorted(list(newMetadataBundle._metadataEntries.items()),
                                                        key=lambda mde: mde[1].sourcePath))

        if kwargs:
            return newMetadataBundle.search(**kwargs)

        return newMetadataBundle

    def symmetric_difference(self, metadataBundle):
        r'''
        Compute the set-wise symmetric difference of two metadata bundles:

        >>> from music21 import metadata
        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>
        >>> tripleMeterBundle = coreBundle.search('3/4')
        >>> tripleMeterBundle
        <music21.metadata.bundles.MetadataBundle {1875 entries}>
        >>> bachBundle.symmetric_difference(tripleMeterBundle)
        <music21.metadata.bundles.MetadataBundle {2158 entries}>

        Returns a new MetadataBundle.
        '''
        return self._apply_set_operation(
            metadataBundle,
            'symmetric_difference',
        )

    def union(self, metadataBundle):
        r'''
        Compute the set-wise union of two metadata bundles:

        >>> coreBundle = corpus.corpora.CoreCorpus().metadataBundle
        >>> bachBundle = coreBundle.search(
        ...     'bach',
        ...     field='composer',
        ...     )
        >>> bachBundle
        <music21.metadata.bundles.MetadataBundle {363 entries}>
        >>> beethovenBundle = coreBundle.search(
        ...     'beethoven',
        ...     field='composer',
        ...     )
        >>> beethovenBundle
        <music21.metadata.bundles.MetadataBundle {23 entries}>

        >>> bachBundle.union(beethovenBundle)
        <music21.metadata.bundles.MetadataBundle {386 entries}>

        Returns a new MetadataBundle.
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
        timer = common.Timer()
        timer.start()
        environLocal.printDebug(['MetadataBundle: validating...'])
        invalidatedKeys = []
        validatedPaths = set()
        for key, metadataEntry in self._metadataEntries.items():
            # MetadataEntries for core corpus items use a relative path as
            # their source path, always starting with 'music21/corpus'.
            sourcePath = metadataEntry.sourcePath
            if sourcePath in validatedPaths:
                continue

            if isinstance(sourcePath, str) and sourcePath.startswith('http:'):
                validatedPaths.add(metadataEntry.sourcePath)
                continue
            elif isinstance(sourcePath, str):
                sourcePath = pathlib.Path(sourcePath)

            if not sourcePath.is_absolute():
                sourcePath = common.getCorpusFilePath() / sourcePath

            if not sourcePath.exists():
                invalidatedKeys.append(key)

            validatedPaths.add(metadataEntry.sourcePath)
        for key in invalidatedKeys:
            del(self._metadataEntries[key])
        message = 'MetadataBundle: finished validating in {0} seconds.'.format(
            timer)
        environLocal.printDebug(message)
        return len(invalidatedKeys)

    def write(self, filePath=None):
        r'''
        Write the metadata bundle to disk as a pickle file.

        If `filePath` is None, use `self.filePath`.

        Returns the metadata bundle.

        >>> from music21 import metadata
        >>> bachBundle = corpus.corpora.CoreCorpus().metadataBundle.search(
        ...     'bach',
        ...     'composer',
        ...     )
        >>> bachBundle.filePath is None
        True

        >>> import os
        >>> import tempfile
        >>> tempFilePath = tempfile.mkstemp()[1]
        >>> bachBundle.write(filePath=tempFilePath)
        <music21.metadata.bundles.MetadataBundle {363 entries}>
        >>> os.remove(tempFilePath)
        '''
        filePath = filePath or self.filePath
        if self.filePath is not None:
            filePath = self.filePath
            environLocal.printDebug(['MetadataBundle: writing:', filePath])
            storedCorpusClient = self._corpus  # no weakrefs allowed...
            self._corpus = None
            uncompressed = pickle.dumps(self, protocol=3)
            # 3 is a safe protocol for some time to come.

            with gzip.open(filePath, 'wb') as outFp:
                outFp.write(uncompressed)
            self._corpus = storedCorpusClient

        return self


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testOneFromCorpus(self):
        from music21.corpus.corpora import CoreCorpus
        cc = CoreCorpus()
        coreBundle = cc.metadataBundle
        metadataEntry = coreBundle.search('bwv66.6')[0]
        self.assertEqual(repr(metadataEntry),
                         "<music21.metadata.bundles.MetadataEntry 'bach_bwv66_6_mxl'>")

    def testFileExtensions(self):
        from music21.corpus.corpora import CoreCorpus
        cc = CoreCorpus()
        workList = cc.getWorkList('ciconia')
        mdb = MetadataBundle()
        failedPaths = mdb.addFromPaths(
            workList,
            parseUsingCorpus=False,
            useMultiprocessing=False,
            storeOnDisk=False,
        )
        self.assertFalse(failedPaths)
        searchResult = mdb.search(
            'cicon',
            field='composer'
        )
        self.assertEqual(len(searchResult), 1)
        self.assertEqual(repr(searchResult[0]),
                         "<music21.metadata.bundles.MetadataEntry 'ciconia_quod_jactatur_xml'>")
        searchResult = mdb.search(
            'cicon',
            field='composer',
            fileExtensions=('.krn',),
        )
        self.assertEqual(len(searchResult), 0)
        searchResult = mdb.search(
            'cicon',
            field='composer',
            fileExtensions=('.xml',),
        )
        self.assertEqual(len(searchResult), 1)

# -----------------------------------------------------------------------------


_DOC_ORDER = (
    MetadataBundle,
    MetadataEntry,
)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testFileExtensions')


# -----------------------------------------------------------------------------
