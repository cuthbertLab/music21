.. _overviewMetadata

Overview: Metadata bundles and corpora
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

Music21 also has the notion of a *virtual* corpus: a collection of musical
works to be found at various locations online which, for reasons of filesize or
licensing, haven't been included in the *core* corpus:

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

    You should only see ``None`` along with the names of any non-default
    *local* corpora you've manually created yourself. In the above example,
    a number of other corpora have already been created.

::

    >>> aNewLocalCorpus.delete()
    >>> aNewLocalCorpus.existsInSettings
    False

Creating metadata bundles
-------------------------

::

    >>> coreBundle = metadata.MetadataBundle('core')
    >>> coreBundle = metadata.MetadataBundle(corpus.CoreCorpus())

::

    >>> coreBundle = metadata.MetadataBundle.fromCoreCorpus()

::

    >>> coreBundle = metadata.MetadataBundle('core').read()

Searching metadata bundles
--------------------------

::

    >>> corpus.search('6/8')

::

    >>> coreCorpus.search('6/8')

::

    >>> bachBundle = coreBundle.search('bach', 'composer')
    >>> bachBundle

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

