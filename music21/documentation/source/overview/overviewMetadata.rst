.. _overviewMetadata

Overview: Metadata bundles and corpora
======================================


Types of corpora
----------------

::

    >>> coreCorpus = corpus.CoreCorpus()
    >>> localCorpus = corpus.LocalCorpus()
    >>> virtualCorpus = corpus.VirtualCorpus()

Creating local corpora
----------------------

In addition to the main *core*, *virtual* and *local* corpora, music21 also
allows users to create and save as many other named local corpora as they like:

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

::

    >>> corpus.LocalCorpus.listLocalCorporaNames()
    [None, u'trecento', 'A new corpus', u'bach', u'fake']


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

