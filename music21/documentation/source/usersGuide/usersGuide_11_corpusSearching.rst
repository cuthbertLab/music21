.. _usersGuide_11_corpusSearching:

User's Guide: Chapter 11: Corpus Searching
==========================================

One of music21's important features is its capability to help users examine
large bodies of musical works, or *corpora*.  

Music21 comes with a substantial corpus called the *core* corpus. When you
download music21 you can immediately start working with the files in the 
corpus directory, including the complete chorales of Bach, many Haydn and
Beethoven string quartets, three books of madrigals by Monteverdi, thousands
of folk songs from the Essen and various ABC databases, and many more.

To load a file from the corpus, simply call *corpus.parse* and assign that
file to a variable:

::

    >>> from music21 import *
    >>> bach = corpus.parse('bach/bwv66.6')
    

Users can also build their own corpora to index and quickly search their own
collections on disk.  Version 1.7 of music21 introduces the ability to have
multiple local corpora that can be accessed individually.
    
This user's guide will cover more about the corpus's basic features soon.  This
chapter focuses on music21's tools for extracting useful metadata - titles,
locations, composers names, the key signatures used in each piece, total
durations, ambitus (range) and so forth.

This metadata is collected in *metadata bundles* for each corpus. The *corpus*
module has tools to search these bundles and persist them disk for later
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
    2567


..  note::

    If you've installed a "no corpus" version of music21, you can still access
    the *core* corpus with a little work.  Download the *core* corpus from
    music21's website, and install it on your system somewhere. Then, teach
    music21 where you installed it like this:    

    ::

        >>> coreCorpus = corpus.CoreCorpus()
        >>> #_DOCS_SHOW coreCorpus.manualCoreCorpusPath = 'path/to/core/corpus'

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
    >>> #_DOCS_SHOW localCorpus.directoryPaths
    >>> ('/Users/josiah/Desktop',) #_DOCS_HIDE
    ('/Users/josiah/Desktop',)

::

    >>> localCorpus.removePath('~/Desktop')


By default, a call to ``corpus.parse`` or ``corpus.search`` will look for
files in any corpus, core, local, or virtual.



Creating local corpora
----------------------

In addition to the default local corpus, music21 allows users to create
and save as many named local corpora as they like, which will persist from
session to session.

Let's create a new *local* corpus, give it a directory to find music files in,
and then save it:

::

    >>> aNewLocalCorpus = corpus.LocalCorpus(u'A new corpus')
    >>> aNewLocalCorpus.existsInSettings
    False

::

    >>> aNewLocalCorpus.addPath('~/Desktop')
    >>> #_DOCS_SHOW aNewLocalCorpus.directoryPaths
    >>> print("('/Users/josiah/Desktop',)") #_DOCS_HIDE
    ('/Users/josiah/Desktop',)

::

    >>> aNewLocalCorpus.save()
    >>> aNewLocalCorpus.existsInSettings
    True

We can see that our new *local* corpus is saved by checking for the names of
all saved *local* corpora:

::

    >>> #_DOCS_SHOW corpus.LocalCorpus.listLocalCorporaNames()
    >>> print [None, u'trecento', u'A new corpus', u'bach', u'fake'] #_DOCS_HIDE
    [None, u'trecento', u'A new corpus', u'bach', u'fake']

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


Simple searches of the corpus
-----------------------------

When you search the corpus, music21 examines each metadata object in the
metadata bundle for the whole corpus and attempts to match your search string 
against the contents of
the various search fields saved in that metadata object.  

You can use ``corpus.search()`` to search the metadata associated with all
known corpora, *core*, *virtual* and even each *local* corpus:

::

    >>> sixEight = corpus.search('6/8')
    >>> sixEight
    <music21.metadata.bundles.MetadataBundle {2174 entries}> 

To work with these 2174 pieces, you can parse treat the MetadataBundle
like a list and call ``.parse()`` on any element:

::

    >>> myPiece = sixEight[0].parse()
    
This will return a ``music21.stream.Score`` object which you can work
with like any other stream. Or if you just want to see it, there's a 
convenience ``.show()`` method you can call directly on a MetadataEntry.

You can also search against a single ``Corpus`` instance, like this one
which ignores anything in your local corpus:

::

    >>> corpus.CoreCorpus().search('6/8')
    <music21.metadata.bundles.MetadataBundle {2174 entries}> 


Because the result of every metadata search is also a metadata bundle, you can
search your search results to do more complex searches.  Remember that 
bachBundle is a collection of all works where the composer is Bach.  Here we
will limit to those pieces in 3/4 time:

::

    >>> bachBundle = corpus.search('bach', 'composer')
    >>> bachBundle
    <music21.metadata.bundles.MetadataBundle {21 entries}>

    >>> bachBundle.search('3/4')
    <music21.metadata.bundles.MetadataBundle {4 entries}>

..  note::

    There are actually many more pieces by Bach in the music21 corpus,
    but many of them are without the metadata specifying him as a
    composer; his name is only in the filename. To get all the pieces
    by Bach use:
    
    ::
    
        >>> allBach = corpus.search('bach')
        
    This will search filenames as well.  We will aim to get more complete
    metadata in the core corpus in the near future, and would appreciate
    community help to achieve this goal.



Metadata search fields
----------------------

When you search metadata bundles, you can search either through every search
field in every metadata instance, or through a single, specific search field.
As we mentioned above, searching for "bach" as a composer renders different 
results from searching for the word "bach" in general:

::

    >>> corpus.search('bach', 'composer')
    <music21.metadata.bundles.MetadataBundle {21 entries}>

::

    >>> corpus.search('bach', 'title')
    <music21.metadata.bundles.MetadataBundle {20 entries}>

::

    >>> corpus.search('bach')
    <music21.metadata.bundles.MetadataBundle {150 entries}>

So what fields can we actually search through? You can find out like this:

::

    >>> for field in corpus.Corpus.listSearchFields():
    ...     field
    ...
    'alternativeTitle'
    'ambitus'
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

This field will grow in the near future now that the development team is seeing
how useful this searching method can be! Now that we know what all the search
fields are, we can search through some of the more obscure corners of the
*core* corpus:

::

    >>> corpus.search('taiwan', 'locale')
    <music21.metadata.bundles.MetadataBundle {27 entries}>

What if you are not searching for an exact match?  If you're searching for
short pieces, you probably don't want to find pieces with exactly 1 note then
union that set with pieces with exactly 2 notes, etc.  Or for pieces from the
19th century, you won't want to search for 1801, 1802, etc.  What you can do is
set up a "predicate callable" which is a function (either a full python ``def``
statement or a short ``lambda`` function) to filter the results.  Each piece
will be checked against your predicate and only those that return true.  Here
we'll search for pieces with between 400 and 500 notes, only in the ``core``
corpus:

::

    >>> predicate = lambda x: 400 < x < 500
    >>> corpus.CoreCorpus().search(predicate, 'noteCount')
    <music21.metadata.bundles.MetadataBundle {49 entries}>

You can also pass in compiled regular expressions into the search:

::

    >>> import re
    >>> haydnOrHandel = re.compile('ha.d.*', re.IGNORECASE)
    >>> bundle = corpus.search(haydnOrHandel)

Though what you mostly get are Shandys.  Best to use a *^* to match
at the beginning of the word next time.


Inspecting metadata bundle search results
-----------------------------------------

Now let's take a closer look at some search results:

::

    >>> bachBundle = corpus.CoreCorpus().search('bach', 'composer')
    >>> bachBundle[0]
    <music21.metadata.bundles.MetadataEntry: bach_choraleAnalyses_riemenschneider001_rntxt> 

Metadata bundles are composed of metadata *entries*. These *entries* allow us
to associate a given ``RichMetadata`` object with a file name, and as we said earlier 
also allow us to parse the associated file into a music21 score:

::

    >>> bachBundle[0].sourcePath
    u'bach/choraleAnalyses/riemenschneider001.rntxt'

::

    >>> bachBundle[0].metadataPayload
    <music21.metadata.RichMetadata object at 0x...>

::

    >>> bachBundle[0].parse()
    <music21.stream.Score ...>


Manipulating multiple metadata bundles
--------------------------------------

Another useful feature of music21's metadata bundles is that they can be
operated on as though they were sets, allowing you to union, intersect and
difference multiple metadata bundles, thereby creating more complex search
results:

::

    >>> corelliBundle = corpus.search('corelli', field='composer')
    >>> corelliBundle
    <music21.metadata.bundles.MetadataBundle {1 entry}>

::

    >>> bachBundle.union(corelliBundle)
    <music21.metadata.bundles.MetadataBundle {22 entries}>

Consult :py:class:`~music21.metadata.bundles.MetadataBundle`'s API for a more
in depth look at how this works.



Getting a metadata bundle
-------------------------

In music21, metadata is information *about* a score, such as its composer,
title, initial key signature or ambitus. A metadata *bundle* is a collection of
metadata pulled from an arbitrarily large group of different scores. Users can
search through metadata bundles to find scores with certain qualities, such as
all scores in a given corpus with a time signature of ``6/8``, or all scores
composed by Monteverdi.

There are a number of different ways to acquire a metadata bundle.  The easiest way
to get the metadataBundle for the core corpus is simply to download music21: we
include a pre-made metadataBundle (in ``corpus/metadataCache/core.json``) so
that this step is unnecessary for the core corpus unless you're contributing to
the project.  But you may want to create metadata bundles for your own local corpora.
Access the ``metadataBundle`` attribute of any ``Corpus`` instance to get its
corresponding metadata bundle:

::

    >>> coreCorpus = corpus.CoreCorpus()
    >>> coreCorpus.metadataBundle
    <music21.metadata.bundles.MetadataBundle 'core': {14478 entries}>

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

Advanced users can also make metadata bundles manually, by passing in the name of the
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
    <music21.metadata.bundles.MetadataBundle 'core': {14478 entries}>



Creating persistent metadata bundles
------------------------------------

Metadata bundles can be written to and read from disk. 

::

    >>> coreBundle = metadata.MetadataBundle('core')
    >>> coreBundle.read()
	<music21.metadata.bundles.MetadataBundle 'core': {14478 entries}>

::

    >>> #_DOCS_SHOW coreBundle.write()

They can also be completely rebuilt, as you will want to do for local
corpora. To add information to a bundle, use the ``addFromPaths()`` method:

::

    >>> newBundle = metadata.MetadataBundle()
    >>> paths = corpus.CoreCorpus().getBachChorales()
    >>> #_DOCS_SHOW failedPaths = newBundle.addFromPaths(paths)
    >>> failedPaths = [] #_DOCS_HIDE
    >>> failedPaths
    []

then call ``.write()`` to save to disk.

::

    >>> #_DOCS_SHOW newBundle
    >>> print "<music21.metadata.bundles.MetadataBundle {402 entries}>" # did not actually run addFromPaths... #_DOCS_HIDE
    <music21.metadata.bundles.MetadataBundle {402 entries}>
    
..  note::

    Building metadata information can be an incredibly intensive process. For
    example, building the *core* metadata bundle can easily take as long as an
    hour! Please use caution, and be patient, when building metadata bundles
    from large corpora. To monitor the corpus-building progress, make sure to
    set 'debug' to True in your user settings:

    ::

        >>> #_DOCS_SHOW environment.UserSettings()['debug'] = True
        

You can delete, rebuild and save a metadata bundle in one go with the
``rebuild()`` method:

::

    >>> virtualBundle = metadata.MetadataBundle.fromVirtualCorpus()
    >>> #_DOCS_SHOW virtualBundle.rebuild()

The process of rebuilding will store the file as it goes so at the end there is 
no need to call ``.write()``.

To delete a metadata bundle's cached-to-disk JSON file, use the ``delete()``
method:

::

    >>> #_DOCS_SHOW virtualBundle.delete()

Deleting a metadata bundle's JSON file won't empty the in-memory contents of
that bundle. For that, use ``clear()``:

::

    >>> virtualBundle.clear()

