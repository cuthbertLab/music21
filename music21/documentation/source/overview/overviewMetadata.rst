.. _overviewMetadata:

Overview: Corpora and Metadata Bundles
======================================

One of music21's important features is its capability to help users examine
large bodies of musical works, or *corpora*.  Music21 provides tools for
extracting useful metadata - the key signatures used in each piece, their
durations, ambitus and so forth - into collections called metadata bundles. It
also allows users to search those bundles, and persist them disk for later
research.


Types of corpora
----------------

Music21 works with three categories of *corpora*, made explicit via the
``corpus.Corpus`` abstract class.

The first category is the *core* corpus, a large collection of musical works
packaged with most music21 installations, including many works from the common
practice era, and inumerable folk songs, in a variety of formats:

::

    >>> coreCorpus = corpus.CoreCorpus()
    >>> len(coreCorpus.getPaths())
    3045


..  note::

    If you've installed a "no corpus" version of music21, you can still access
    the *core* corpus with a little work.  Download the *core* corpus from
    music21's website, and install it on your system somewhere. Then, teach
    music21 where you installed it like this:    

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
configured by individual music21 users for their own research. *Local* corpora
behave identically to the *core* and *virtual* corpora, and can be searched and
cached in the same manner:

::

    >>> localCorpus = corpus.LocalCorpus()

You can add and remove paths from a *local* corpus with the ``addPath()`` and
``removePath()`` methods:

::

    >>> localCorpus.addPath('~/Desktop')
    >>> localCorpus.directoryPaths
    ('/Users/josiah/Desktop',)

::

    >>> localCorpus.removePath('~/Desktop')

Creating local corpora
----------------------

In addition to the default local corpus, music21 allows users to create
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

In music21, metadata is information *about* a score, such as its composer,
title, initial key signature or ambitus. A metadata *bundle* is a collection of
metadata pulled from an arbitrarily large group of different scores. Users can
search through metadata bundles to find scores with certain qualities, such as
all scores in a given corpus with a time signature of ``6/8``, or all scores
composed by Monteverdi.

There are a number of different ways to acquire a metadata bundle.  One is to
access the ``metadataBundle`` attribute of any ``Corpus`` instance to get its
corresponding metadata bundle:

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
will cache the metadata bundle in memory once it has been read from disk,
potentially saving you a lot of time.

You can also make metadata bundles manually, by passing in the name of the
corpus you want the bundle to refer to, or an actual ``Corpus`` instance
itself:

::

    >>> coreBundle = metadata.MetadataBundle('core')
    >>> coreBundle = metadata.MetadataBundle(corpus.CoreCorpus())

However, you'll need to read the bundle's saved data from disk before you can
do anything useful with the bundle. Bundles don't read their associated JSON
files automatically when they're manually instantiated.

::

    >>> coreBundle
    <music21.metadata.bundles.MetadataBundle 'core': {0 entries}>

::

    >>> coreBundle.read()
    <music21.metadata.bundles.MetadataBundle 'core': {14956 entries}>

That's a lot of information! Now let's see what we can do with it ...


Searching metadata bundles
--------------------------

When you search metadata bundles, music21 examines each metadata object in the
entire bundle and attempts to match your search string against the contents of
the various search fields saved in that metadata object.  Just as with creating
metadata bundles, there are few different ways to search them.

You can use ``corpus.search()`` to search the metadata associated with all
known corpora, *core*, *virtual* and even each *local* corpus:

::

    >>> corpus.search('6/8')
    <music21.metadata.bundles.MetadataBundle {2211 entries}> 

You can also search against a single ``Corpus`` instance, like this:

::

    >>> corpus.CoreCorpus().search('6/8')
    <music21.metadata.bundles.MetadataBundle {2211 entries}> 

Finally, if you already have a reference to a metadata bundle, you can search
there too:

::

    >>> bachBundle = coreBundle.search('bach', 'composer')
    >>> bachBundle
    <music21.metadata.bundles.MetadataBundle {21 entries}>

Because the result of every metadata search is also a metadata bundle, you can
search your search results!

::

    >>> bachBundle.search('3/4')
    <music21.metadata.bundles.MetadataBundle {4 entries}>


Metadata search fields
----------------------

When you search metadata bundles, you can search either through every search
field in every metadata instance, or through a single, specific search field.
For example, searching for "bach" as a composer renders different results from
searching for the word "bach" in general:

::

    >>> coreBundle.search('bach', 'composer')
    <music21.metadata.bundles.MetadataBundle {21 entries}>

::

    >>> coreBundle.search('bach', 'title')
    <music21.metadata.bundles.MetadataBundle {20 entries}>

::

    >>> coreBundle.search('bach')
    <music21.metadata.bundles.MetadataBundle {150 entries}>

So what fields can we actually search through? You can find out like this:

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

Now that we know what all the search fields are, we can search through some of
the more obscure corners of the *core* corpus:

::

    >>> corpus.CoreCorpus().search('taiwan', 'locale')
    <music21.metadata.bundles.MetadataBundle {27 entries}>

Inspecting metadata bundle search results
-----------------------------------------

Now let's take a closer look at some search results:

::

    >>> bachBundle = corpus.CoreCorpus().search('bach', 'composer')
    >>> bachBundle[0]
    <music21.metadata.bundles.MetadataEntry: bach_choraleAnalyses_riemenschneider014_rntxt> 

Metadata bundles are composed of metadata *entries*. These *entries* allow us
to associate a given ``RichMetadata`` object with a file name, and also allow
us to parse the associated file into a music21 score:

::

    >>> bachBundle[0].sourcePath
    u'bach/choraleAnalyses/riemenschneider014.rntxt'

::

    >>> bachBundle[0].metadataPayload
    <music21.metadata.RichMetadata object at 0x112f54250>

::

    >>> bachBundle[0].parse()
    <music21.stream.Score 4421475216>

Manipulating multiple metadata bundles
--------------------------------------

Another useful feature of music21's metadata bundles is that they can be
operated on as though they were sets, allowing you to union, intersect and
difference multiple metadata bundles, thereby creating more complex search
results:

::

    >>> beethovenBundle = corpus.search('beethoven', 'composer')
    >>> beethovenBundle
    <music21.metadata.bundles.MetadataBundle {16 entries}>

::

    >>> bachBundle.union(beethovenBundle)
    <music21.metadata.bundles.MetadataBundle {37 entries}>

Consult :py:class:`~music21.metadata.bundles.MetadataBundle`'s API for a more
in depth look at how this works.

Managing metadata bundles
-------------------------

Metadata bundles can be written to and read from disk. They can also be
completely rebuilt:

::

    >>> coreBundle = metadata.MetadataBundle('core')
    >>> coreBundle.read()

::

    >>> coreBundle.write()

To add information to a bundle, use the ``addFromPaths()`` method:

::

    >>> newBundle = metadata.MetadataBundle()
    >>> paths = corpus.CoreCorpus().getBachChorales()
    >>> failedPaths = newBundle.addFromPaths(paths)
    >>> failedPaths
    []

::

    >>> newBundle
    <music21.metadata.bundles.MetadataBundle {402 entries}>

..  note::

    Building metadata information can be an incredibly intensive process. For
    example, building the *core* metadata bundle can easily take as long as an
    hour! Please use caution, and be patient, when building metadata bundles
    from large corpora. To monitor the corpus-building progress, make sure to
    set 'debug' to True in your user settings:

    ::

        >>> environment.UserSettings()['debug'] = True

You can delete, rebuild and save a metadata bundle in one go with the
``rebuild()`` method:

::

    >>> virtualBundle = metadata.MetadataBundle.fromVirtualCorpus()
    >>> virtualBundle.rebuild()

To delete a metadata bundle's cached-to-disk JSON file, use the ``delete()``
method:

::

    >>> virtualBundle.delete()

Deleting a metadata bundle's JSON file won't empty the in-memory contents of
that bundle. For that, use ``clear()``:

::

    >>> virtualBundle.clear()

