.. _overviewMetadata

Overview: Corpora and Metadata Bundles
======================================

One of music21's most important features is its capability to help us examine
large bodies of musical works, or *corpora*.  We provide affordances for
extracting useful metadata - the key signatures used in each piece, their
durations, ambitus and so forth - into metadata bundles, and methods for
searching and persisting the metadata to disk.


Types of corpora
----------------

Music21 deals with three categories of *corpora*, made explicit via the
``corpus.Corpus`` abstract class.

The first category is the *core* corpus, a large collection of musical works
packaged with most music21 installations, including many works from the common
practice era, and inumerable folk songs, in a variety of formats:

::

    >>> coreCorpus = corpus.CoreCorpus()
    >>> len(coreCorpus.getPaths())
    3045


..  note::

    If you've installed a "no corpus" version of music21, and have downloaded
    and installed the *core* corpus in a non-standard location, you can teach
    music21 where your copy of the *core* corpus is like this:

    ::

        >>> coreCorpus.manualCoreCorpusPath = 'path/to/core/corpus'

Music21 also has the notion of a *virtual* corpus: a collection of musical
works to be found at various locations online which, for reasons of licensing,
haven't been included in the *core* corpus:

::

    >>> virtualCorpus = corpus.VirtualCorpus()
    >>> virtualCorpus.getPaths()[0]
    'http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml'

Finally, music21 allows for *local* corpora: bodies of works provided and
configured by individual music21 users for their own research, but operable on
by the same machinery of searching and caching as the *core* and *virtual*
corpora:

::

    >>> localCorpus = corpus.LocalCorpus()


Creating local corpora
----------------------

In addition to the default local corpus, music21 also allows users to create
and save as many named local corpora as they like, which will persist from
session to session.

Let's create a new *local* corpus, give it a directory to find music files in,
and then save it:

::

    >>> aNewLocalCorpus = corpus.LocalCorpus('A new corpus')
    >>> aNewLocalCorpus.existsInSettings
    False

::

    >>> aNewLocalCorpus.addPath('~/Desktop')
    >>> aNewLocalCorpus.directoryPaths
    ('/Users/josiah/Desktop',)

::

    >>> aNewLocalCorpus.save()
    >>> aNewLocalCorpus.existsInSettings
    True

We can see that our new *local* corpus is saved by checking for the names of
all saved *local* corpora:

::

    >>> corpus.LocalCorpus.listLocalCorporaNames()
    [None, u'trecento', 'A new corpus', u'bach', u'fake']

..  note::

    When running ``listLocalCorporaNames()``, you will see ``None`` -
    indicating the default *local* corpus - along with the names of any
    non-default *local* corpora you've manually created yourself. In the above
    example, a number of other corpora have already been created.

Finally, we can delete the *local* corpus we previously created like this:

::

    >>> aNewLocalCorpus.delete()
    >>> aNewLocalCorpus.existsInSettings
    False

Creating metadata bundles
-------------------------

Metadata is information *about* a score, such as its composer, title, initial
key signature or ambitus. A metadata *bundle*, however, is a collection of
metadata pulled from an arbitrarily large group of different scores, which you
can then search through to find scores with certain qualities, such as all
scores in 6/8, or all scores by Monteverdi.

There are a number of different ways to acquire a metadata bundle instance.
One way is to access the ``metadataBundle`` attribute of any ``Corpus``
instance to get its corresponding metadata bundle:

::

    >>> coreCorpus.metadataBundle
    <music21.metadata.bundles.MetadataBundle 'core': {14956 entries}>

Music21 also provides a handful of convenience methods for getting metadata
bundles associated with the *virtual*, *local* or *core* corpora:

::

    >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()
    >>> localBundle = metadata.MetadataBundle.fromLocalCorpus()
    >>> otherLocalBundle = metadata.MetadataBundle.fromLocalCorpus('blah')
    >>> virtualBundle = metadata.MetadataBundle.fromVirtualCorpus()

We strongly recommend using the above ``from*()`` methods. Some of these
metadata bundles can become quite large, and methods like ``fromCoreCorpus()``
make sure to cache the metadata bundle in memory once it has been read from
disk, potentially saving you a lot of time.

You can, however, make the metadata bundles by hand, by passing in the name of
the corpus you want the bundle to refer to, or an actual ``Corpus`` instance
itself:

::

    >>> coreBundle = metadata.MetadataBundle('core')
    >>> coreBundle = metadata.MetadataBundle(corpus.CoreCorpus())

However, you'll need to remember to read the data from disk, as that isn't
handled automatically when you manually instantiate metadata bundles:

::

    >>> coreBundle = metadata.MetadataBundle('core').read()
    >>> coreBundle
    <music21.metadata.bundles.MetadataBundle 'core': {14956 entries}>

That's a lot of information! Now let's see what we can do with it ...


Searching metadata bundles
--------------------------

::

    >>> corpus.search('6/8')

::

    >>> coreCorpus.search('6/8')

::

    >>> bachBundle = coreBundle.search('bach', 'composer')
    >>> bachBundle

::

    >>> bachBundle.search('6/8')

::

    >>> for field in corpus.Corpus.listSearchFields():
    ...     field
    ...
    'alternativeTitle'
    'composer'
    'date'
    'keySignatureFirst'
    'keySignatures'
    'localeOfComposition'
    'movementName'
    'movementNumber'
    'noteCount'
    'number'
    'opusNumber'
    'pitchHighest'
    'pitchLowest'
    'quarterLength'
    'tempoFirst'
    'tempos'
    'timeSignatureFirst'
    'timeSignatures'
    'title'

Inspecting metadata bundle search results
-----------------------------------------

::

    >>> bachBundle[0]

::

    >>> bachBundle[0].parse()

Managing metadata bundles
-------------------------

Metadata bundles can be written to and read from disk, as well as rebuilt
completely.

::

    >>> coreBundle = metadata.MetadataBundle('core')
    >>> coreBundle.read()

::

    >>> coreBundle.write()

::

    >>> virtualBundle = metadata.MetadataBundle.fromVirtualCorpus()
    >>> virtualBundle.rebuild()

::

    >>> virtualBundle.delete()

::

    >>> virtualBundle.clear()

