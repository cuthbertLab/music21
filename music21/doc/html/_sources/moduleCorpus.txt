.. _moduleCorpus:

music21.corpus
==============

Function getBachChorales()
--------------------------


Function getBeethovenStringQuartets()
-------------------------------------


Function getComposer()
----------------------



>>> a = getComposer('beethoven')
>>> len(a) > 10
True 
>>> a = getComposer('mozart')
>>> len(a) > 10
True 

Function getComposerDir()
-------------------------

Given the name of a composer, get the path to the top-level directory of that composer 

>>> import os
>>> a = getComposerDir('beethoven')
>>> a.endswith(os.path.join('corpus', os.sep, 'beethoven'))
True 
>>> a = getComposerDir('bach')
>>> a.endswith(os.path.join('corpus', os.sep, 'bach'))
True 
>>> a = getComposerDir('mozart')
>>> a.endswith(os.path.join('corpus', os.sep, 'mozart'))
True 
>>> a = getComposerDir('luca')
>>> a.endswith(os.path.join('corpus', os.sep, 'luca'))
True 

Function getPaths()
-------------------

Get all paths in the corpus that match a known extension, or an extenion provided by an argument. 

>>> a = getPaths()
>>> len(a) > 30
True 
>>> a = getPaths('krn')
>>> len(a) >= 4
True 

Function getWork()
------------------

Search the corpus and return either a list of file paths or a single file path 

>>> import os
>>> a = getWork('opus74no2', 4)
>>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.xml']))
True 
>>> a = getWork(['haydn', 'opus74no2', 'movement4.xml'])
>>> a.endswith(os.path.sep.join(['haydn', 'opus74no2', 'movement4.xml']))
True 



Function parseWork()
--------------------

Return a parsed stream from a converter by providing only a work name. If forceSource is True, the original file will always be loaded and pickled files, if available, will be ignored. 

>>> aStream = parseWork('opus74no1/movement3')

