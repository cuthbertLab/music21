# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         converter/__init__.py
# Purpose:      Provide a common way to create Streams from any data music21
#               handles
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
music21.converter contains tools for loading music from various file formats,
whether from disk, from the web, or from text, into
music21.stream.:class:`~music21.stream.Score` objects (or
other similar stream objects).

The most powerful and easy to use tool is the :func:`~music21.converter.parse`
function. Simply provide a filename, URL, or text string and, if the format
is supported, a :class:`~music21.stream.Score` will be returned.

This is the most general, public interface for all formats.  Programmers
adding their own formats to the system should provide an interface here to
their own parsers (such as humdrum, musicxml, etc.)

The second and subsequent times that a file is loaded it will likely be much
faster since we store a parsed version of each file as a "pickle" object in
the temp folder on the disk.

>>> #_DOCS_SHOW s = converter.parse('d:/myDocs/schubert.krn')
>>> s = converter.parse(humdrum.testFiles.schubert) #_DOCS_HIDE
>>> s
<music21.stream.Score ...>
'''
from __future__ import annotations

from collections import deque
import collections.abc
import copy
from http.client import responses
import io
from math import isclose
import os
import re
import pathlib
import sys
import types
import typing as t
import unittest
import zipfile

import requests

from music21.converter import subConverters
from music21.converter import museScore

from music21 import _version
from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import metadata
from music21 import musedata as musedataModule
from music21 import stream
from music21.metadata import bundles


if t.TYPE_CHECKING:
    from music21 import base


__all__ = [
    'subConverters', 'museScore',
    'ArchiveManagerException', 'PickleFilterException',
    'ConverterException', 'ConverterFileException',
    'ArchiveManager', 'PickleFilter', 'resetSubConverters',
    'registerSubConverter', 'unregisterSubConverter',
    'Converter', 'parseFile', 'parseData', 'parseURL',
    'parse', 'freeze', 'thaw', 'freezeStr', 'thawStr',

]

environLocal = environment.Environment('converter')

_StrOrBytes = t.TypeVar('_StrOrBytes', bound=str | bytes)

# ------------------------------------------------------------------------------
class ArchiveManagerException(exceptions21.Music21Exception):
    pass


class PickleFilterException(exceptions21.Music21Exception):
    pass


class ConverterException(exceptions21.Music21Exception):
    pass


class ConverterFileException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class ArchiveManager:
    r'''
    Before opening a file path, this class can check if this is an
    archived file collection, such as a .zip or .mxl file. This will return the
    data from the archive.

    >>> fnCorpus = corpus.getWork('bwv66.6', fileExtensions=('.xml',))

    This is likely a unicode string

    >>> #_DOCS_SHOW fnCorpus
    >>> '/Users/cuthbert/git/music21base/music21/corpus/bach/bwv66.6.mxl' #_DOCS_HIDE
    '/Users/cuthbert/git/music21base/music21/corpus/bach/bwv66.6.mxl'
    >>> am = converter.ArchiveManager(fnCorpus)
    >>> am.isArchive()
    True
    >>> am.getNames()
    ['bwv66.6.xml', 'META-INF/container.xml']
    >>> data = am.getData()
    >>> data[0:70]
    '<?xml version="1.0" encoding="UTF-8"?>\r<!DOCTYPE score-partwise PUBLIC'


    The only archive type supported now is zip. But .mxl is zip...
    '''
    # for info on mxl files, see
    # http://www.recordare.com/xml/compressed-mxl.html

    def __init__(self, fp: str | pathlib.Path, archiveType='zip'):
        self.fp: pathlib.Path = common.cleanpath(fp, returnPathlib=True)
        self.archiveType: str = archiveType

    def isArchive(self) -> bool:
        '''
        Return True or False if the filepath is an
        archive of the supplied archiveType.
        '''
        if self.archiveType == 'zip':
            # some .md files can be zipped
            if self.fp.suffix in ('.mxl', '.md'):
                # try to open it, as some mxl files are not zips
                try:
                    with zipfile.ZipFile(self.fp, 'r') as unused:
                        pass
                except zipfile.BadZipfile:
                    return False
                return True
            elif self.fp.suffix == '.zip':
                return True
        else:
            raise ArchiveManagerException(f'no support for archiveType: {self.archiveType}')
        return False

    def getNames(self) -> list[str]:
        '''
        Return a list of all names contained in this archive.
        '''
        post: list[str] = []
        if self.archiveType == 'zip':
            with zipfile.ZipFile(self.fp, 'r') as f:
                for subFp in f.namelist():
                    post.append(subFp)
        return post

    def getData(self, dataFormat='musicxml') -> t.Any:
        '''
        Return data from the archive.

        For 'musedata' format this will be a list of strings.
        For 'musicxml' this will be a single string.

        * Changed in v8: name is not used.
        '''
        post = None
        if self.archiveType != 'zip':
            raise ArchiveManagerException(f'no support for extension: {self.archiveType}')

        with zipfile.ZipFile(self.fp, 'r') as f:
            post = self._extractContents(f, dataFormat)

        return post

    def _extractContents(self,
                         f: zipfile.ZipFile,
                         dataFormat: str = 'musicxml') -> t.Any:
        post: t.Any = None
        if dataFormat == 'musicxml':  # try to auto-harvest
            # will return data as a string
            # note that we need to read the META-INF/container.xml file
            # and get the root file full-path
            # a common presentation will be like this:
            # ['musicXML.xml', 'META-INF/', 'META-INF/container.xml']
            for subFp in f.namelist():
                # the name musicXML.xml is often used, or get top level
                # xml file
                if 'META-INF' in subFp:
                    continue
                # include .mxl to be kind to users who zipped up mislabeled files
                if pathlib.Path(subFp).suffix not in ['.musicxml', '.xml', '.mxl']:
                    continue

                post = f.read(subFp)
                if isinstance(post, bytes):
                    foundEncoding = re.match(br"encoding=[\'\"](\S*?)[\'\"]", post[:1000])
                    if foundEncoding:
                        defaultEncoding = foundEncoding.group(1).decode('ascii')
                        # print('FOUND ENCODING: ', defaultEncoding)
                    else:
                        defaultEncoding = 'UTF-8'
                    try:
                        post = post.decode(encoding=defaultEncoding)
                    except UnicodeDecodeError:  # sometimes windows written...
                        post = post.decode(encoding='utf-16-le')
                        post = re.sub(r"encoding=([\'\"]\S*?[\'\"])",
                                      "encoding='UTF-8'", post)

                break

        elif dataFormat == 'musedata':
            # this might concatenate all parts into a single string
            # or, return a list of strings
            # alternative, a different method might return one at a time
            mdd = musedataModule.MuseDataDirectory(f.namelist())
            # environLocal.printDebug(['mdd object, namelist', mdd, f.namelist])

            post = []
            for subFp in mdd.getPaths():
                # this was f.open(subFp, 'rU') for universal newline support
                # but that was removed in Python 3.6 and while it is supposed
                # to be fixed with io.TextIOWrapper, there are no docs that
                # show how to do so.  -- hopefully fixed
                try:
                    with f.open(subFp, 'r') as zipOpen:
                        lines = list(io.TextIOWrapper(zipOpen, newline=None))
                except UnicodeDecodeError:
                    # python3 UTF-8 failed to read haydn/opus103/movement1.zip
                    with f.open(subFp, 'r') as zipOpen:
                        lines = list(io.TextIOWrapper(zipOpen, newline=None,
                                                      encoding='ISO-8859-1'))
                # environLocal.printDebug(['subFp', subFp, len(lines)])
                post.append(''.join(lines))

                # note: the following methods do not properly employ
                # universal new lines; this is a python problem:
                # http://bugs.python.org/issue6759
                # post.append(component.read())
                # post.append(f.read(subFp, 'U'))
                # msg.append('\n/END\n')

        return post


# ------------------------------------------------------------------------------
class PickleFilter:
    '''
    Before opening a file path, this class checks to see if there is an up-to-date
    version of the file pickled and stored in the scratch directory.

    If forceSource is True, then a pickle path will not be created.

    Provide a file path to check if there is pickled version.

    If forceSource is True, pickled files, if available, will not be
    returned.
    '''

    def __init__(self,
                 fp: str | pathlib.Path,
                 forceSource: bool = False,
                 number: int | None = None,
                 # quantizePost: bool = False,
                 # quarterLengthDivisors: Iterable[int] | None = None,
                 **keywords):
        self.fp: pathlib.Path = common.cleanpath(fp, returnPathlib=True)
        self.forceSource: bool = forceSource
        self.number: int | None = number
        self.keywords: dict[str, t.Any] = keywords
        # environLocal.printDebug(['creating pickle filter'])

    def getPickleFp(self,
                    directory: pathlib.Path | str | None = None,
                    zipType: str | None = None) -> pathlib.Path:
        '''
        Returns the file path of the pickle file for this file.

        Returns a pathlib.Path
        '''
        pathLibDirectory: pathlib.Path
        if directory is None:
            pathLibDirectory = environLocal.getRootTempDir()  # pathlibPath
        elif isinstance(directory, str):
            pathLibDirectory = pathlib.Path(directory)
        else:
            pathLibDirectory = directory

        if zipType is None:
            extension = '.p'
        else:
            extension = '.p.gz'

        pythonVersion = 'py' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)

        pathNameToParse = str(self.fp)

        quantization: list[str] = []
        if 'quantizePost' in self.keywords and self.keywords['quantizePost'] is False:
            quantization.append('noQtz')
        elif 'quarterLengthDivisors' in self.keywords:
            for divisor in self.keywords['quarterLengthDivisors']:
                quantization.append('qld' + str(divisor))

        baseName = '-'.join(['m21', _version.__version__, pythonVersion, *quantization,
                             common.getMd5(pathNameToParse)])

        if self.number is not None:
            baseName += '-' + str(self.number)
        baseName += extension

        return pathLibDirectory / baseName

    def removePickle(self) -> None:
        '''
        If a compressed pickled file exists, remove it from disk.

        Generally not necessary to call, since we can just overwrite obsolete pickles,
        but useful elsewhere.
        '''
        pickleFp = self.getPickleFp(zipType='gz')  # pathlib...
        if pickleFp.exists():
            os.remove(pickleFp)

    def status(self) -> tuple[pathlib.Path, bool, pathlib.Path | None]:
        '''
        Given a file path specified with __init__, look for an up-to-date pickled
        version of this file path. If it exists, return its fp, otherwise return the
        original file path.

        Return arguments are file path to load, boolean whether to write a pickle, and
        the file path of the pickle.  All file paths can be pathlib.Path objects or None

        Does not check that fp exists or create the pickle file.

        >>> fp = '/Users/Cuthbert/Desktop/musicFile.mxl'
        >>> pickFilter = converter.PickleFilter(fp)
        >>> #_DOCS_SHOW pickFilter.status()
        (PosixPath('/Users/Cuthbert/Desktop/musicFile.mxl'), True,
              PosixPath('/tmp/music21/m21-7.0.0-py3.9-18b8c5a5f07826bd67ea0f20462f0b8d.p.gz'))
        '''
        fpScratch = environLocal.getRootTempDir()
        m21Format = common.findFormatFile(self.fp)

        if m21Format == 'pickle':  # do not pickle a pickle
            if self.forceSource:
                raise PickleFilterException(
                    'cannot access source file when only given a file path to a pickled file.')
            writePickle = False  # cannot write pickle if no scratch dir
            fpLoad = self.fp
            fpPickle = None
        elif fpScratch is None or self.forceSource:
            writePickle = False  # cannot write pickle if no scratch dir
            fpLoad = self.fp
            fpPickle = None
        else:  # see which is more up to date
            fpPickle = self.getPickleFp(fpScratch, zipType='gz')  # pathlib Path
            if not fpPickle.exists():
                writePickle = True  # if pickled file does not exist
                fpLoad = self.fp
            else:
                if self.fp.stat().st_mtime < fpPickle.stat().st_mtime:
                    # pickle is most recent
                    writePickle = False
                    fpLoad = fpPickle
                else:  # file is most recent
                    writePickle = True
                    fpLoad = self.fp
        return fpLoad, writePickle, fpPickle


# ------------------------------------------------------------------------------
# a deque of additional subConverters to use (in addition to the default ones)
_registeredSubConverters: deque[type[subConverters.SubConverter]] = deque()

# default subConverters to skip
_deregisteredSubConverters: deque[
    type[subConverters.SubConverter] | t.Literal['all']
] = deque()


def resetSubConverters():
    '''
    Reset state to default (removing all registered and deregistered subConverters).
    '''
    _registeredSubConverters.clear()
    _deregisteredSubConverters.clear()


def registerSubConverter(newSubConverter: type[subConverters.SubConverter]) -> None:
    '''
    Add a SubConverter to the list of registered subConverters.

    Example, register a converter for the obsolete Amiga composition software Sonix (so fun...)

    >>> class ConverterSonix(converter.subConverters.SubConverter):
    ...    registerFormats = ('sonix',)
    ...    registerInputExtensions = ('mus',)

    >>> converter.registerSubConverter(ConverterSonix)
    >>> scf = converter.Converter().getSubConverterFormats()
    >>> for x in sorted(scf):
    ...     x, scf[x]
    ('abc', <class 'music21.converter.subConverters.ConverterABC'>)
    ...
    ('sonix', <class 'music21.ConverterSonix'>)
    ...

    See `converter.qmConverter` for an example of an extended subConverter.

    >>> converter.resetSubConverters() #_DOCS_HIDE

    Changed in v.9 -- custom subConverters are registered above default subConverters.
    '''
    _registeredSubConverters.appendleft(newSubConverter)

@common.deprecated('v9', 'v10', 'use unregisterSubconverter with capital C')
def registerSubconverter(
    newSubConverter: type[subConverters.SubConverter]
) -> None:  # pragma: no cover
    '''
    Deprecated: use registerSubConverter w/ capital "C" instead.
    '''
    registerSubConverter(newSubConverter)

def unregisterSubConverter(
    removeSubConverter: t.Literal['all'] | type[subConverters.SubConverter]
) -> None:
    # noinspection PyShadowingNames
    '''
    Remove a SubConverter from the list of registered subConverters.

    >>> converter.resetSubConverters() #_DOCS_HIDE
    >>> mxlConverter = converter.subConverters.ConverterMusicXML

    >>> c = converter.Converter()
    >>> mxlConverter in c.subConvertersList()
    True
    >>> converter.unregisterSubConverter(mxlConverter)
    >>> mxlConverter in c.subConvertersList()
    False

    If there is no such subConverter registered, and it is not a default subConverter,
    then a converter.ConverterException is raised:

    >>> class ConverterSonix(converter.subConverters.SubConverter):
    ...    registerFormats = ('sonix',)
    ...    registerInputExtensions = ('mus',)
    >>> converter.unregisterSubConverter(ConverterSonix)
    Traceback (most recent call last):
    music21.converter.ConverterException: Could not remove <class 'music21.ConverterSonix'> from
                registered subConverters

    The special command "all" removes everything including the default converters:

    >>> converter.unregisterSubConverter('all')
    >>> c.subConvertersList()
    []

    >>> converter.resetSubConverters() #_DOCS_HIDE
    '''
    if removeSubConverter == 'all':
        _registeredSubConverters.clear()
        _deregisteredSubConverters.clear()
        _deregisteredSubConverters.append('all')
        return

    try:
        _registeredSubConverters.remove(removeSubConverter)
    except ValueError:
        c = Converter()
        dsc = c.defaultSubConverters()
        if removeSubConverter in dsc:
            _deregisteredSubConverters.append(removeSubConverter)
        else:
            raise ConverterException(
                f'Could not remove {removeSubConverter!r} from registered subConverters')


@common.deprecated('v9', 'v10', 'use unregisterSubConverter with capital C')
def unregisterSubconverter(
    newSubConverter: type[subConverters.SubConverter]
) -> None:  # pragma: no cover
    '''
    Deprecated: use unregisterSubConverter w/ capital "C" instead.
    '''
    unregisterSubConverter(newSubConverter)


# ------------------------------------------------------------------------------
class Converter:
    '''
    A class used for converting all supported data formats into music21 objects.

    Not a subclass, but a wrapper for different converter objects based on format.
    '''
    _DOC_ATTR: dict[str, str] = {
        'subConverter':
            '''
            a :class:`~music21.converter.subConverters.SubConverter` object
            that will do the actual converting.
            ''',
    }

    def __init__(self) -> None:
        self.subConverter: subConverters.SubConverter | None = None
        # a stream object unthawed
        self._thawedStream: stream.Score | stream.Part | stream.Opus | None = None

    def _getDownloadFp(
        self,
        directory: pathlib.Path | str,
        ext: str,
        url: str,
    ):
        directoryPathlib: pathlib.Path
        if isinstance(directory, str):
            directoryPathlib = pathlib.Path(directory)
        else:
            directoryPathlib = directory

        filename = 'm21-' + _version.__version__ + '-' + common.getMd5(url) + ext
        return directoryPathlib / filename

    # pylint: disable=redefined-builtin
    # noinspection PyShadowingBuiltins
    def parseFileNoPickle(
        self,
        fp: pathlib.Path | str,
        number: int | None = None,
        format: str | None = None,
        forceSource: bool = False,
        **keywords
    ):
        '''
        Given a file path, parse and store a music21 Stream.

        If format is None then look up the format from the file
        extension using `common.findFormatFile`.

        Does not use or store pickles in any circumstance.
        '''
        fpPathlib: pathlib.Path = common.cleanpath(fp, returnPathlib=True)
        # environLocal.printDebug(['attempting to parseFile', fp])
        if not fpPathlib.exists():
            raise ConverterFileException(f'no such file exists: {fp}')
        useFormat = format

        if useFormat is None:
            useFormat = self.getFormatFromFileExtension(fpPathlib)
        self.setSubConverterFromFormat(useFormat)
        if t.TYPE_CHECKING:
            assert isinstance(self.subConverter, subConverters.SubConverter)

        self.subConverter.keywords = keywords
        try:
            self.subConverter.parseFile(
                fp,
                number=number,
                **keywords
            )
        except NotImplementedError:
            raise ConverterFileException(f'File is not in a correct format: {fp}')

        if t.TYPE_CHECKING:
            assert isinstance(self.stream, stream.Stream)

        if not self.stream.metadata:
            self.stream.metadata = metadata.Metadata()
        self.stream.metadata.filePath = str(fpPathlib)
        self.stream.metadata.fileNumber = number
        self.stream.metadata.fileFormat = useFormat

    def getFormatFromFileExtension(self, fp):
        # noinspection PyShadowingNames
        '''
        gets the format from a file extension.

        >>> fp = common.getSourceFilePath() / 'musedata' / 'testZip.zip'
        >>> c = converter.Converter()
        >>> c.getFormatFromFileExtension(fp)
        'musedata'
        '''
        fp = common.cleanpath(fp, returnPathlib=True)
        # if the file path is to a directory, assume it is a collection of
        # musedata parts
        useFormat = None
        if fp.is_dir():
            useFormat = 'musedata'
        else:
            useFormat = common.findFormatFile(fp)
            if useFormat is None:
                raise ConverterFileException(f'cannot find a format extensions for: {fp}')
        return useFormat

    # noinspection PyShadowingBuiltins
    def parseFile(self, fp, number=None,
                  format=None, forceSource=False, storePickle=True, **keywords):
        '''
        Given a file path, parse and store a music21 Stream, set as self.stream.

        If format is None then look up the format from the file
        extension using `common.findFormatFile`.

        Will load from a pickle unless forceSource is True
        Will store as a pickle unless storePickle is False
        '''
        from music21 import freezeThaw
        fp = common.cleanpath(fp, returnPathlib=True)
        if not fp.exists():
            raise ConverterFileException(f'no such file exists: {fp}')
        useFormat = format

        if useFormat is None:
            useFormat = self.getFormatFromFileExtension(fp)

        pfObj = PickleFilter(fp, forceSource, number, **keywords)
        unused_fpDst, writePickle, fpPickle = pfObj.status()
        if writePickle is False and fpPickle is not None and forceSource is False:
            environLocal.printDebug('Loading Pickled version')
            try:
                self._thawedStream = thaw(fpPickle, zipType='zlib')
            except freezeThaw.FreezeThawException:
                environLocal.warn(f'Could not parse pickle, {fpPickle} ...rewriting')
                os.remove(fpPickle)
                self.parseFileNoPickle(fp, number, format, forceSource, **keywords)

            if not self.stream.metadata:
                self.stream.metadata = metadata.Metadata()
            self.stream.metadata.filePath = fp
            self.stream.metadata.fileNumber = number
            self.stream.metadata.fileFormat = useFormat
        else:
            environLocal.printDebug('Loading original version')
            self.parseFileNoPickle(fp, number, format, forceSource, **keywords)
            if writePickle is True and fpPickle is not None and storePickle is True:
                # save the stream to disk...
                environLocal.printDebug('Freezing Pickle')
                s = self.stream
                sf = freezeThaw.StreamFreezer(s, fastButUnsafe=True)
                sf.write(fp=fpPickle, zipType='zlib')

                environLocal.printDebug('Replacing self.stream')
                # get a new stream
                self._thawedStream = thaw(fpPickle, zipType='zlib')

                if not self.stream.metadata:
                    self.stream.metadata = metadata.Metadata()
                self.stream.metadata.filePath = fp
                self.stream.metadata.fileNumber = number
                self.stream.metadata.fileFormat = useFormat

    def parseData(
        self,
        dataStr: str | bytes,
        number=None,
        format=None,
        forceSource=False,
        **keywords,
    ) -> None:
        '''
        Given raw data, determine format and parse into a music21 Stream,
        set as self.stream.
        '''
        useFormat = format
        # get from data in string if not specified
        if useFormat is None:  # it's a string
            dataStr = dataStr.lstrip()
            useFormat, dataStr = self.formatFromHeader(dataStr)

            if isinstance(dataStr, bytes):
                dataStrMakeStr = dataStr.decode('utf-8', 'ignore')
            else:
                dataStrMakeStr = dataStr

            if useFormat is not None:
                pass
            elif dataStrMakeStr.startswith('<?xml'):
                # is it MEI or MusicXML?
                if '<mei' in dataStrMakeStr:
                    useFormat = 'mei'
                else:
                    useFormat = 'musicxml'
            elif dataStrMakeStr.startswith('mei:') or dataStrMakeStr.lower().startswith('mei:'):
                useFormat = 'mei'
            elif dataStrMakeStr.lower().startswith('musicxml:'):
                useFormat = 'musicxml'
            elif dataStrMakeStr.startswith('MThd') or dataStrMakeStr.lower().startswith('midi:'):
                useFormat = 'midi'
            elif (dataStrMakeStr.startswith('!!!')
                    or dataStrMakeStr.startswith('**')
                    or dataStrMakeStr.lower().startswith('humdrum:')):
                useFormat = 'humdrum'
            elif dataStrMakeStr.lower().startswith('tinynotation:'):
                useFormat = 'tinyNotation'

            # assume MuseData must define a meter and a key
            elif 'WK#:' in dataStrMakeStr and 'measure' in dataStrMakeStr:
                useFormat = 'musedata'
            elif 'M:' in dataStrMakeStr and 'K:' in dataStrMakeStr:
                useFormat = 'abc'
            elif 'Time Signature:' in dataStrMakeStr and 'm1' in dataStrMakeStr:
                useFormat = 'romanText'
            else:
                raise ConverterException('File not found or no such format found for: %s' %
                                         dataStrMakeStr)

        self.setSubConverterFromFormat(useFormat)
        if t.TYPE_CHECKING:
            assert isinstance(self.subConverter, subConverters.SubConverter)
        self.subConverter.keywords = keywords
        self.subConverter.parseData(dataStr, number=number)

    def parseURL(
        self,
        url: str,
        *,
        format: str | None = None,
        number: int | None = None,
        forceSource: bool = False,
        **keywords,
    ) -> None:
        '''
        Given a url, download and parse the file
        into a music21 Stream stored in the `stream`
        property of the converter object.

        Note that this checks the user Environment
        `autoDownload` setting before downloading.

        Use `forceSource=True` to download every time rather than
        re-reading from a cached file.

        >>> joplinURL = ('https://github.com/cuthbertLab/music21/raw/master'
        ...              + '/music21/corpus/joplin/maple_leaf_rag.mxl')
        >>> c = converter.Converter()
        >>> #_DOCS_SHOW c.parseURL(joplinURL)
        >>> #_DOCS_SHOW joplinStream = c.stream

        * Changed in v7: made keyword-only and added `forceSource` option.
        '''
        autoDownload = environLocal['autoDownload']
        if autoDownload in ('deny', 'ask'):
            message = f'Automatic downloading of URLs is presently set to {autoDownload!r}; '
            message += 'configure your Environment "autoDownload" setting to '
            message += '"allow" to permit automatic downloading: '
            message += "environment.set('autoDownload', 'allow')"
            raise ConverterException(message)

        # this format check is here first to see if we can find the format
        # in the url; if forcing a format we do not need this
        # we do need the file extension to construct file path below
        if format is None:
            formatFromURL, ext = common.findFormatExtURL(url)
            if formatFromURL is None:  # cannot figure out what it is
                raise ConverterException(f'cannot determine file format of url: {url}')
        else:
            unused_formatType, ext = common.findFormat(format)
            if ext is None:
                ext = '.txt'

        directory = environLocal.getRootTempDir()
        fp = self._getDownloadFp(directory, ext, url)  # returns pathlib.Path

        if forceSource is True or not fp.exists():
            environLocal.printDebug([f'downloading to: {fp}'])
            r = requests.get(url, allow_redirects=True, timeout=20)
            if r.status_code != 200:
                raise ConverterException(
                    f'Could not download {url}, error: {r.status_code} {responses[r.status_code]}')
            fp.write_bytes(r.content)
        else:
            environLocal.printDebug([f'using already downloaded file: {fp}'])

        # update format based on downloaded fp
        if format is None:  # if not provided as an argument
            useFormat = common.findFormatFile(fp)
        else:
            useFormat = format
        if useFormat is None:
            raise ConverterException(f'Cannot automatically find a format for {fp!r}')

        self.setSubConverterFromFormat(useFormat)
        if t.TYPE_CHECKING:
            assert isinstance(self.subConverter, subConverters.SubConverter)

        self.subConverter.keywords = keywords
        self.subConverter.parseFile(fp, number=number)

        if self.stream is None:
            raise ConverterException('Could not create a Stream via a subConverter.')
        self.stream.metadata.filePath = fp
        self.stream.metadata.fileNumber = number
        self.stream.metadata.fileFormat = useFormat


    # -----------------------------------------------------------------------#
    # SubConverters
    @common.deprecated('v9', 'v10', 'use subConvertersList with capital C')
    def subconvertersList(
        self,
        converterType: t.Literal['any', 'input', 'output'] = 'any'
    ) -> list[type[subConverters.SubConverter]]:  # pragma: no cover
        return self.subConvertersList(converterType)

    @staticmethod
    def subConvertersList(
        converterType: t.Literal['any', 'input', 'output'] = 'any'
    ) -> list[type[subConverters.SubConverter]]:
        # noinspection PyAttributeOutsideInit
        '''
        Gives a list of all the subConverter classes that are registered.

        If converterType is 'any' (true), then input or output
        subConverters are listed.

        Otherwise, 'input', or 'output' can be used to filter.

        >>> converter.resetSubConverters() #_DOCS_HIDE
        >>> c = converter.Converter()
        >>> scl = c.subConvertersList()
        >>> defaultScl = c.defaultSubConverters()
        >>> tuple(scl) == tuple(defaultScl)
        True

        >>> sclInput = c.subConvertersList('input')
        >>> sclInput
        [<class 'music21.converter.subConverters.ConverterABC'>,
         <class 'music21.converter.subConverters.ConverterCapella'>,
         <class 'music21.converter.subConverters.ConverterClercqTemperley'>,
         <class 'music21.converter.subConverters.ConverterHumdrum'>,
         <class 'music21.converter.subConverters.ConverterMEI'>,
         <class 'music21.converter.subConverters.ConverterMidi'>,
         <class 'music21.converter.subConverters.ConverterMuseData'>,
         <class 'music21.converter.subConverters.ConverterMusicXML'>,
         <class 'music21.converter.subConverters.ConverterNoteworthy'>,
         <class 'music21.converter.subConverters.ConverterNoteworthyBinary'>,
         <class 'music21.converter.subConverters.ConverterRomanText'>,
         <class 'music21.converter.subConverters.ConverterScala'>,
         <class 'music21.converter.subConverters.ConverterTinyNotation'>,
         <class 'music21.converter.subConverters.ConverterVolpiano'>]

        Get those that can output (note that this is also a static method
        on converter)

        >>> sclOutput = converter.Converter.subConvertersList('output')
        >>> sclOutput
        [<class 'music21.converter.subConverters.ConverterBraille'>,
         <class 'music21.converter.subConverters.ConverterLilypond'>,
         <class 'music21.converter.subConverters.ConverterMidi'>,
         <class 'music21.converter.subConverters.ConverterMusicXML'>,
         <class 'music21.converter.subConverters.ConverterRomanText'>,
         <class 'music21.converter.subConverters.ConverterScala'>,
         <class 'music21.converter.subConverters.ConverterText'>,
         <class 'music21.converter.subConverters.ConverterTextLine'>,
         <class 'music21.converter.subConverters.ConverterVexflow'>,
         <class 'music21.converter.subConverters.ConverterVolpiano'>]

        >>> class ConverterSonix(converter.subConverters.SubConverter):
        ...    registerFormats = ('sonix',)
        ...    registerInputExtensions = ('mus',)
        >>> converter.registerSubConverter(ConverterSonix)
        >>> ConverterSonix in c.subConvertersList()
        True

        Newly registered subConveters appear first, so they will be used instead
        of any default subConverters that work on the same format or extension.

        >>> class BadMusicXMLConverter(converter.subConverters.SubConverter):
        ...    registerFormats = ('musicxml',)
        ...    registerInputExtensions = ('xml', 'mxl', 'musicxml')
        ...    def parseData(self, strData, number=None):
        ...        self.stream = stream.Score(id='empty')

        >>> converter.registerSubConverter(BadMusicXMLConverter)
        >>> c.subConvertersList()
        [<class 'music21.BadMusicXMLConverter'>,
         ...
         <class 'music21.converter.subConverters.ConverterMusicXML'>,
         ...]

        Show that this musicxml file by Amy Beach is now parsed by BadMusicXMLConverter:

        >>> #_DOCS_SHOW s = corpus.parse('beach/prayer_of_a_tired_child')
        >>> #_DOCS_HIDE -- we cannot know if the piece is already parsed or not.
        >>> s = corpus.parse('beach/prayer_of_a_tired_child', forceSource=True)  #_DOCS_HIDE
        >>> s.id
        'empty'
        >>> len(s.parts)
        0

        Note that if the file has already been parsed by another subConverter format
        the parameter `forceSource` is required to force the file to be parsed by the
        newly registered subConverter:

        >>> converter.unregisterSubConverter(BadMusicXMLConverter)
        >>> #_DOCS_HIDE -- the forceSource will not have created a pickle.
        >>> #_DOCS_SHOW s = corpus.parse('beach/prayer_of_a_tired_child')
        >>> s.id
        'empty'
        >>> s = corpus.parse('beach/prayer_of_a_tired_child', forceSource=True)
        >>> len(s.parts)
        6

        >>> converter.resetSubConverters() #_DOCS_HIDE
        '''
        subConverterList = []
        for reg in _registeredSubConverters:
            # print(reg)
            subConverterList.append(reg)

        if _deregisteredSubConverters and _deregisteredSubConverters[0] == 'all':
            pass
        else:
            subConverterList.extend(Converter.defaultSubConverters())
            for unregistered in _deregisteredSubConverters:
                if unregistered == 'all':
                    continue
                try:
                    subConverterList.remove(unregistered)
                except ValueError:
                    pass

        if converterType == 'any':
            return subConverterList

        filteredSubConvertersList = []
        for sc in subConverterList:
            if converterType == 'input' and not sc.registerInputExtensions:
                continue
            if converterType == 'output' and not sc.registerOutputExtensions:
                continue
            filteredSubConvertersList.append(sc)

        return filteredSubConvertersList

    @common.deprecated('v9', 'v10', 'use defaultSubConverters with capital C')
    def defaultSubconverters(self) -> list[type[subConverters.SubConverter]]:  # pragma: no cover
        return self.defaultSubConverters()

    @staticmethod
    def defaultSubConverters() -> list[type[subConverters.SubConverter]]:
        '''
        return an alphabetical list of the default subConverters: those in converter.subConverters
        with the class SubConverter.

        Do not use generally.  Use Converter.subConvertersList()

        >>> c = converter.Converter()
        >>> for sc in c.defaultSubConverters():
        ...     print(sc)
        <class 'music21.converter.subConverters.ConverterABC'>
        <class 'music21.converter.subConverters.ConverterBraille'>
        <class 'music21.converter.subConverters.ConverterCapella'>
        <class 'music21.converter.subConverters.ConverterClercqTemperley'>
        <class 'music21.converter.subConverters.ConverterHumdrum'>
        <class 'music21.converter.subConverters.ConverterIPython'>
        <class 'music21.converter.subConverters.ConverterLilypond'>
        <class 'music21.converter.subConverters.ConverterMEI'>
        <class 'music21.converter.subConverters.ConverterMidi'>
        <class 'music21.converter.subConverters.ConverterMuseData'>
        <class 'music21.converter.subConverters.ConverterMusicXML'>
        <class 'music21.converter.subConverters.ConverterNoteworthy'>
        <class 'music21.converter.subConverters.ConverterNoteworthyBinary'>
        <class 'music21.converter.subConverters.ConverterRomanText'>
        <class 'music21.converter.subConverters.ConverterScala'>
        <class 'music21.converter.subConverters.ConverterText'>
        <class 'music21.converter.subConverters.ConverterTextLine'>
        <class 'music21.converter.subConverters.ConverterTinyNotation'>
        <class 'music21.converter.subConverters.ConverterVexflow'>
        <class 'music21.converter.subConverters.ConverterVolpiano'>
        <class 'music21.converter.subConverters.SubConverter'>
        '''
        defaultSubConverters: list[type[subConverters.SubConverter]] = []
        for i in sorted(subConverters.__dict__):
            possibleSubConverter = getattr(subConverters, i)
            # noinspection PyTypeChecker
            if (callable(possibleSubConverter)
                    and not isinstance(possibleSubConverter, types.FunctionType)
                    and hasattr(possibleSubConverter, '__mro__')
                    and issubclass(possibleSubConverter, subConverters.SubConverter)):
                defaultSubConverters.append(possibleSubConverter)
        return defaultSubConverters

    @common.deprecated('v9', 'v10', 'use getSubConverterFormats with capital C')
    def getSubconverterFormats(
        self
    ) -> dict[str, type[subConverters.SubConverter]]:  # pragma: no cover
        return self.getSubConverterFormats()

    @staticmethod
    def getSubConverterFormats() -> dict[str, type[subConverters.SubConverter]]:
        '''
        Get a dictionary of subConverters for various formats.

        (staticmethod: call on an instance or the class itself)

        >>> scf = converter.Converter.getSubConverterFormats()
        >>> scf['abc']
        <class 'music21.converter.subConverters.ConverterABC'>
        >>> for x in sorted(scf):
        ...     x, scf[x]
        ('abc', <class 'music21.converter.subConverters.ConverterABC'>)
        ('braille', <class 'music21.converter.subConverters.ConverterBraille'>)
        ('capella', <class 'music21.converter.subConverters.ConverterCapella'>)
        ('clercqtemperley', <class 'music21.converter.subConverters.ConverterClercqTemperley'>)
        ('cttxt', <class 'music21.converter.subConverters.ConverterClercqTemperley'>)
        ('har', <class 'music21.converter.subConverters.ConverterClercqTemperley'>)
        ('humdrum', <class 'music21.converter.subConverters.ConverterHumdrum'>)
        ('ipython', <class 'music21.converter.subConverters.ConverterIPython'>)
        ('jupyter', <class 'music21.converter.subConverters.ConverterIPython'>)
        ('lily', <class 'music21.converter.subConverters.ConverterLilypond'>)
        ('lilypond', <class 'music21.converter.subConverters.ConverterLilypond'>)
        ('mei', <class 'music21.converter.subConverters.ConverterMEI'>)
        ('midi', <class 'music21.converter.subConverters.ConverterMidi'>)
        ('musedata', <class 'music21.converter.subConverters.ConverterMuseData'>)
        ('musicxml', <class 'music21.converter.subConverters.ConverterMusicXML'>)
        ('noteworthy', <class 'music21.converter.subConverters.ConverterNoteworthyBinary'>)
        ('noteworthytext', <class 'music21.converter.subConverters.ConverterNoteworthy'>)
        ('rntext', <class 'music21.converter.subConverters.ConverterRomanText'>)
        ('romantext', <class 'music21.converter.subConverters.ConverterRomanText'>)
        ('scala', <class 'music21.converter.subConverters.ConverterScala'>)
        ('t', <class 'music21.converter.subConverters.ConverterText'>)
        ('text', <class 'music21.converter.subConverters.ConverterText'>)
        ('textline', <class 'music21.converter.subConverters.ConverterTextLine'>)
        ('tinynotation', <class 'music21.converter.subConverters.ConverterTinyNotation'>)
        ('txt', <class 'music21.converter.subConverters.ConverterText'>)
        ('vexflow', <class 'music21.converter.subConverters.ConverterVexflow'>)
        ('volpiano', <class 'music21.converter.subConverters.ConverterVolpiano'>)
        ('xml', <class 'music21.converter.subConverters.ConverterMusicXML'>)
        '''
        converterFormats = {}
        for name in Converter.subConvertersList():
            if hasattr(name, 'registerFormats'):
                formatsTuple = name.registerFormats
                for f in formatsTuple:
                    f = f.lower()
                    if f not in converterFormats:
                        converterFormats[f] = name
        return converterFormats

    @staticmethod
    def getSubConverterFromFormat(
        converterFormat: str
    ) -> subConverters.SubConverter:
        '''
        Return a particular subConverter class based on the format
        of the converterFormat string.

        Static method: call on the class itself or an instance:

        >>> converter.Converter.getSubConverterFromFormat('musicxml')
        <music21.converter.subConverters.ConverterMusicXML object at 0x...>
        '''
        if converterFormat is None:
            raise ConverterException('Did not find a format from the source file')
        converterFormat = converterFormat.lower()
        scf = Converter.getSubConverterFormats()
        if converterFormat not in scf:
            raise ConverterException(f'no converter available for format: {converterFormat}')
        subConverterClass = scf[converterFormat]
        return subConverterClass()

    @common.deprecated('v9', 'v10', 'use setSubConverterFromFormat with capital C')
    def setSubconverterFromFormat(self, converterFormat: str):  # pragma: no cover
        self.setSubConverterFromFormat(converterFormat)

    def setSubConverterFromFormat(self, converterFormat: str):
        '''
        sets the .subConverter according to the format of `converterFormat`:

        >>> convObj = converter.Converter()
        >>> convObj.setSubConverterFromFormat('humdrum')
        >>> convObj.subConverter
        <music21.converter.subConverters.ConverterHumdrum object at 0x...>
        '''
        self.subConverter = Converter.getSubConverterFromFormat(converterFormat)

    def formatFromHeader(
        self,
        dataStr: _StrOrBytes
    ) -> tuple[str | None, _StrOrBytes]:
        '''
        if dataStr begins with a text header such as  "tinyNotation:" then
        return that format plus the dataStr with the head removed.

        Else, return (None, dataStr) where dataStr is the original untouched.

        The header is not detected case-sensitive.

        >>> c = converter.Converter()
        >>> c.formatFromHeader('tinynotation: C4 E2')
        ('tinynotation', 'C4 E2')

        Note that the format is always returned in lower case:

        >>> c.formatFromHeader('romanText: m1: a: I b2 V')
        ('romantext', 'm1: a: I b2 V')

        If there is no header then the format is None and the original is
        returned unchanged:

        >>> c.formatFromHeader('C4 E2')
        (None, 'C4 E2')
        >>> c.formatFromHeader(b'binary-data')
        (None, b'binary-data')


        New formats can register new headers, like this old Amiga format:

        >>> class ConverterSonix(converter.subConverters.SubConverter):
        ...    registerFormats = ('sonix',)
        ...    registerInputExtensions = ('mus',)
        >>> converter.registerSubConverter(ConverterSonix)
        >>> c.formatFromHeader('sonix: AIFF data')
        ('sonix', 'AIFF data')
        >>> converter.resetSubConverters() #_DOCS_HIDE

        If bytes are passed in, the data is returned as bytes, but the
        header format is still converted to a string:

        >>> c.formatFromHeader(b'romanText: m1: a: I b2 V')
        ('romantext', b'm1: a: I b2 V')

        Anything except string or bytes raises a ValueError:

        >>> c.formatFromHeader(23)
        Traceback (most recent call last):
        ValueError: Cannot parse a format from <class 'int'>.
        '''
        dataStrStartLower: str
        if isinstance(dataStr, bytes):
            dataStrStartLower = dataStr[:20].decode('utf-8', 'ignore').lower()
        elif isinstance(dataStr, str):
            dataStrStartLower = dataStr[:20].lower()
        else:
            raise ValueError(f'Cannot parse a format from {type(dataStr)}.')

        foundFormat = None
        subConverterList = self.subConvertersList()
        for sc in subConverterList:
            for possibleFormat in sc.registerFormats:
                if dataStrStartLower.startswith(possibleFormat.lower() + ':'):
                    foundFormat = possibleFormat
                    dataStr = t.cast(_StrOrBytes,
                                     dataStr[len(foundFormat) + 1:].lstrip()
                                     )
                    break
        return (foundFormat, dataStr)

    def regularizeFormat(self, fmt: str) -> str | None:
        '''
        Take in a string representing a format, a file extension (w/ or without leading dot)
        etc. and find the format string that best represents the format that should be used.

        Searches SubConverter.registerFormats first, then SubConverter.registerInputExtensions,
        then SubConverter.registerOutputExtensions

        Returns None if no format applies:

        >>> c = converter.Converter()
        >>> c.regularizeFormat('mxl')
        'musicxml'
        >>> c.regularizeFormat('t')
        'text'
        >>> c.regularizeFormat('abc')
        'abc'
        >>> c.regularizeFormat('lily.png')
        'lilypond'
        >>> c.regularizeFormat('blah') is None
        True
        '''
        # make lower case, as some lilypond processing used upper case
        fmt = fmt.lower().strip()
        if fmt.startswith('.'):
            fmt = fmt[1:]  # strip .
        foundSc = None

        formatList = fmt.split('.')
        fmt = formatList[0]
        if len(formatList) > 1:
            unused_subformats = formatList[1:]
        else:
            unused_subformats = []
        scl = self.subConvertersList()

        for sc in scl:
            formats = sc.registerFormats
            for scFormat in formats:
                if fmt == scFormat:
                    foundSc = sc
                    break
            if foundSc is not None:
                break

        if foundSc is None:
            for sc in scl:
                extensions = sc.registerInputExtensions
                for ext in extensions:
                    if fmt == ext:
                        foundSc = sc
                        break
                if foundSc is not None:
                    break
        if foundSc is None:
            for sc in scl:
                extensions = sc.registerInputExtensions
                for ext in extensions:
                    if fmt == ext:
                        foundSc = sc
                        break
                if foundSc is not None:
                    break

        if foundSc and foundSc.registerFormats:
            return foundSc.registerFormats[0]
        else:
            return None

    # --------------------------------------------------------------------------
    # properties
    @property
    def stream(self) -> stream.Score | stream.Part | stream.Opus | None:
        '''
        Returns the .subConverter.stream object.
        '''
        if self._thawedStream is not None:
            return self._thawedStream
        elif self.subConverter is not None:
            return self.subConverter.stream
        else:
            return None
        # not _stream: please don't look in other objects' private variables;
        #              humdrum worked differently.


# ------------------------------------------------------------------------------
# module level convenience methods

# pylint: disable=redefined-builtin
# noinspection PyShadowingBuiltins
def parseFile(fp,
              number=None,
              format=None,
              forceSource=False,
              **keywords) -> stream.Score | stream.Part | stream.Opus:
    '''
    Given a file path, attempt to parse the file into a Stream.
    '''
    v = Converter()
    fp = common.cleanpath(fp, returnPathlib=True)
    v.parseFile(fp, number=number, format=format, forceSource=forceSource, **keywords)
    if t.TYPE_CHECKING:
        assert isinstance(v.stream, (stream.Score, stream.Part, stream.Opus))
    return v.stream

# pylint: disable=redefined-builtin
# noinspection PyShadowingBuiltins
def parseData(dataStr,
              number=None,
              format=None,
              **keywords) -> stream.Score | stream.Part | stream.Opus:
    '''
    Given musical data represented within a Python string, attempt to parse the
    data into a Stream.
    '''
    v = Converter()
    v.parseData(dataStr, number=number, format=format, **keywords)
    if t.TYPE_CHECKING:
        assert isinstance(v.stream, (stream.Score, stream.Part, stream.Opus))
    return v.stream

# pylint: disable=redefined-builtin
# noinspection PyShadowingBuiltins
def parseURL(url,
             *,
             format=None,
             number=None,
             forceSource=False,
             **keywords) -> stream.Score | stream.Part | stream.Opus:
    '''
    Given a URL, attempt to download and parse the file into a Stream. Note:
    URL downloading will not happen automatically unless the user has set their
    Environment "autoDownload" preference to "allow".

    * Changed in v7: made keyword-only.
    '''
    v = Converter()
    v.parseURL(url, format=format, forceSource=forceSource, **keywords)
    if t.TYPE_CHECKING:
        assert isinstance(v.stream, (stream.Score, stream.Part, stream.Opus))
    return v.stream


def parse(value: bundles.MetadataEntry | bytes | str | pathlib.Path,
          *,
          forceSource: bool = False,
          number: int | None = None,
          format: str | None = None,  # pylint: disable=redefined-builtin
          **keywords) -> stream.Score | stream.Part | stream.Opus:
    r'''
    Given a file path, encoded data in a Python string, or a URL, attempt to
    parse the item into a Stream.  Note: URL downloading will not happen
    automatically unless the user has set their Environment "autoDownload"
    preference to "allow".

    Keywords can include `number` which specifies a piece number in a file of
    multi-piece file.

    `format` specifies the format to parse the line of text or the file as.

    `quantizePost` specifies whether to quantize a stream resulting from MIDI conversion.
    By default, MIDI streams are quantized to the nearest sixteenth or triplet-eighth
    (i.e. smaller durations will not be preserved).
    `quarterLengthDivisors` sets the quantization units explicitly.

    A string of text is first checked to see if it is a filename that exists on
    disk.  If not it is searched to see if it looks like a URL.  If not it is
    processed as data.

    PC File:

    >>> #_DOCS_SHOW s = converter.parse(r'c:\users\myke\desktop\myFile.xml')

    Mac File:

    >>> #_DOCS_SHOW s = converter.parse('/Users/cuthbert/Desktop/myFile.xml')

    URL:

    >>> #_DOCS_SHOW s = converter.parse('https://midirepository.org/file220/file.mid')


    Data is preceded by an identifier such as "tinynotation:"

    >>> s = converter.parse("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c", makeNotation=False)
    >>> s[meter.TimeSignature].first()
    <music21.meter.TimeSignature 3/4>

    or the format can be passed directly:

    >>> s = converter.parse("2/16 E4 r f# g=lastG trip{b-8 a g} c", format='tinyNotation')
    >>> s[meter.TimeSignature].first()
    <music21.meter.TimeSignature 2/16>

    * Changed in v8: passing a list of tinyNotation strings was never documented as a
        possibility and has been removed.
    '''
    # environLocal.printDebug(['attempting to parse()', value])
    # see if a work number is defined; for multi-work collections
    valueStr: str
    if isinstance(value, bytes):
        valueStr = value.decode('utf-8', 'ignore')
    if isinstance(value, pathlib.Path):
        valueStr = str(value)
    elif isinstance(value, bundles.MetadataEntry):
        if value.sourcePath.is_absolute():
            valueStr = str(value.sourcePath)
        else:
            valueStr = str(common.getCorpusFilePath() / value.sourcePath)
    elif isinstance(value, str):
        valueStr = value
    else:
        valueStr = ''

    if (common.isListLike(value)
            and isinstance(value, collections.abc.Sequence)
            and len(value) == 2
            and value[1] is None
            and _osCanLoad(str(value[0]))):
        # comes from corpus.search
        return parseFile(value[0], format=format, **keywords)
    elif (common.isListLike(value)
          and isinstance(value, collections.abc.Sequence)
          and len(value) == 2
          and isinstance(value[1], int)
          and _osCanLoad(str(value[0]))):
        # corpus or other file with movement number
        if not isinstance(value[0], str):
            raise ConverterException(
                f'If using a two-element list, the first value must be a string, not {value[0]!r}'
            )
        if not isinstance(value[1], int):
            raise ConverterException(
                'If using a two-element list, the second value must be an integer number, '
                f'not {value[1]!r}'
            )
        sc = parseFile(value[0], format=format, **keywords)
        if isinstance(sc, stream.Opus):
            return sc.getScoreByNumber(value[1])
        else:
            return sc
    # a midi string, must come before os.path.exists test
    elif not isinstance(value, bytes) and valueStr.startswith('MThd'):
        return parseData(value, number=number, format=format, **keywords)
    elif (not isinstance(value, bytes)
          and _osCanLoad(valueStr)):
        return parseFile(valueStr, number=number, format=format,
                         forceSource=forceSource, **keywords)
    elif (not isinstance(value, bytes)
          and _osCanLoad(common.cleanpath(valueStr))):
        return parseFile(common.cleanpath(valueStr), number=number, format=format,
                         forceSource=forceSource, **keywords)
    elif not isinstance(valueStr, bytes) and (valueStr.startswith('http://')
                                              or valueStr.startswith('https://')):
        # it's a url; may need to broaden these criteria
        return parseURL(value, number=number, format=format,
                        forceSource=forceSource, **keywords)
    elif isinstance(value, pathlib.Path):
        raise FileNotFoundError(f'Cannot find file in {str(value)}')
    elif isinstance(value, str) and common.findFormatFile(value) is not None:
        # assume mistyped file path
        raise FileNotFoundError(f'Cannot find file in {str(value)}')
    else:
        # all else, including MidiBytes
        return parseData(value, number=number, format=format, **keywords)

def toData(obj: base.Music21Object, fmt: str, **keywords) -> str | bytes:
    '''
    Convert `obj` to the given format `fmt` and return the information retrieved.

    Currently, this is somewhat inefficient: it calls SubConverter.toData which
    calls `write()` on the object and reads back the value of the file.

    >>> tiny = converter.parse('tinyNotation: 4/4 C4 D E F G1')
    >>> data = converter.toData(tiny, 'braille.ascii')
    >>> type(data)
    <class 'str'>
    >>> print(data)
        #D4
    #A _?:$] (<K
    '''
    if fmt.startswith('.'):
        fmt = fmt[1:]
    regularizedConverterFormat, unused_ext = common.findFormat(fmt)
    if regularizedConverterFormat is None:
        raise ConverterException(f'cannot support output in this format yet: {fmt}')

    formatSubs = fmt.split('.')
    fmt = formatSubs[0]
    subformats = formatSubs[1:]

    scClass = common.findSubConverterForFormat(regularizedConverterFormat)
    if scClass is None:  # pragma: no cover
        raise ConverterException(f'cannot support output in this format yet: {fmt}')
    formatWriter = scClass()
    return formatWriter.toData(
        obj,
        fmt=regularizedConverterFormat,
        subformats=subformats,
        **keywords)


def freeze(streamObj, fmt=None, fp=None, fastButUnsafe=False, zipType='zlib') -> pathlib.Path:
    # noinspection PyShadowingNames
    '''
    Given a StreamObject and a file path, serialize and store the Stream to a file.

    This function is based on the :class:`~music21.converter.StreamFreezer` object.

    The serialization format is defined by the `fmt` argument; 'pickle' (the default) is only one
    presently supported.  'json' or 'jsonnative' will be used once jsonpickle is good enough.

    If no file path is given, a temporary file is used.

    The file path is returned.

    >>> c = converter.parse('tinynotation: 4/4 c4 d e f')
    >>> c.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F>
        {4.0} <music21.bar.Barline type=final>
    >>> fp = converter.freeze(c, fmt='pickle')
    >>> #_DOCS_SHOW fp
    PosixPath('/tmp/music21/sjiwoe.p.gz')

    The file can then be "thawed" back into a Stream using the
    :func:`~music21.converter.thaw` method.

    >>> d = converter.thaw(fp)
    >>> d.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F>
        {4.0} <music21.bar.Barline type=final>

    OMIT_FROM_DOCS

    >>> import os
    >>> os.remove(fp)
    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamFreezer(streamObj, fastButUnsafe=fastButUnsafe)
    return v.write(fmt=fmt, fp=fp, zipType=zipType)  # returns fp


def thaw(fp, zipType='zlib'):
    '''
    Given a file path of a serialized Stream, defrost the file into a Stream.

    This function is based on the :class:`~music21.converter.StreamFreezer` object.

    See the documentation for :meth:`~music21.converter.freeze` for demos.
    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamThawer()
    v.open(fp, zipType=zipType)
    return v.stream


def freezeStr(streamObj, fmt=None):
    '''
    Given a StreamObject
    serialize and return a serialization string.

    This function is based on the
    :class:`~music21.converter.StreamFreezer` object.

    The serialization format is defined by
    the `fmt` argument; 'pickle' (the default),
    is the only one presently supported.


    >>> c = converter.parse('tinyNotation: 4/4 c4 d e f', makeNotation=False)
    >>> c.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note D>
    {2.0} <music21.note.Note E>
    {3.0} <music21.note.Note F>
    >>> data = converter.freezeStr(c, fmt='pickle')
    >>> len(data) > 20  # pickle implementation dependent
    True
    >>> d = converter.thawStr(data)
    >>> d.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note D>
    {2.0} <music21.note.Note E>
    {3.0} <music21.note.Note F>

    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamFreezer(streamObj)
    return v.writeStr(fmt=fmt)  # returns a string


def thawStr(strData):
    '''
    Given a serialization string, defrost into a Stream.

    This function is based on the :class:`~music21.converter.StreamFreezer` object.
    '''
    from music21 import freezeThaw
    v = freezeThaw.StreamThawer()
    v.openStr(strData)
    return v.stream


def _osCanLoad(fp: str) -> bool:
    '''
    Return os.path.exists, but catch `ValueError` and return False.

    os.path.exists raises ValueError for paths over 260 chars
    on all versions of Windows lacking the `LongPathsEnabled` setting,
    which is absent below Windows 10.1607 and opt-in on higher versions.
    '''
    try:
        return os.path.exists(fp)
    except ValueError:  # pragma: no cover
        return False


# ------------------------------------------------------------------------------
class TestSlow(unittest.TestCase):  # pragma: no cover

    def testMusicXMLConversion(self):
        from music21.musicxml import testFiles
        for mxString in testFiles.ALL:
            a = subConverters.ConverterMusicXML()
            a.parseData(mxString)


class TestExternal(unittest.TestCase):
    show = True

    def testConversionMusicXml(self):
        c = stream.Score()

        from music21.musicxml import testPrimitive
        mxString = testPrimitive.chordsThreeNotesDuration21c
        a = parseData(mxString)

        mxString = testPrimitive.beams01
        b = parseData(mxString)
        # b.show()

        c.append(a[0])
        c.append(b[0])
        if self.show:
            c.show()
        # TODO: this is only showing the minimum number of measures

    def testFreezer(self):
        from music21 import corpus
        s = corpus.parse('bach/bwv66.6.xml')
        fp = freeze(s)
        s2 = thaw(fp)
        if self.show:
            s2.show()
        os.remove(fp)

    def testMusicXMLTabConversion(self):
        from music21.musicxml import testFiles

        mxString = testFiles.ALL[5]
        a = subConverters.ConverterMusicXML()
        a.parseData(mxString)

        b = parseData(mxString)
        if self.show:
            b.show('text')
            b.show()

        # {0.0} <music21.metadata.Metadata object at 0x04501CD0>
        # {0.0} <music21.stream.Part Electric Guitar>
        #    {0.0} <music21.instrument.Instrument P0: Electric Guitar: >
        #    {0.0} <music21.stream.Measure 0 offset=0.0>
        #        {0.0} <music21.layout.StaffLayout distance None, ...staffLines 6>
        #        {0.0} <music21.clef.TabClef>
        #        {0.0} <music21.tempo.MetronomeMark animato Quarter=120.0>
        #        {0.0} <music21.key.KeySignature of no sharps or flats, mode major>
        #        {0.0} <music21.meter.TimeSignature 4/4>
        #        {0.0} <music21.note.Note F>
        #        {2.0} <music21.note.Note F#>


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())

    def testConversionMX(self):
        from music21.musicxml import testPrimitive
        from music21 import dynamics
        from music21 import note

        mxString = testPrimitive.pitches01a
        a = parse(mxString)
        a = a.flatten()
        b = a.getElementsByClass(note.Note)
        # there should be 102 notes
        self.assertEqual(len(b), 102)

        # test directions, dynamics, wedges
        mxString = testPrimitive.directions31a
        a = parse(mxString)
        a = a.flatten()
        b = a.getElementsByClass(dynamics.Dynamic)
        # there should be 27 dynamics found in this file
        self.assertEqual(len(b), 27)
        c = a.getElementsByClass(note.Note)
        self.assertEqual(len(c), 53)

        # two starts and two stops == 2!
        d = a.getElementsByClass(dynamics.DynamicWedge)
        self.assertEqual(len(d), 2)

        # test lyrics
        mxString = testPrimitive.lyricsMelisma61d
        a = parse(mxString)
        a = a.flatten()
        b = a.getElementsByClass(note.Note)
        found = []
        for noteObj in b:
            for obj in noteObj.lyrics:
                found.append(obj)
        self.assertEqual(len(found), 3)

        # test we are getting rests
        mxString = testPrimitive.restsDurations02a
        a = parse(mxString)
        a = a.flatten()
        b = a.getElementsByClass(note.Rest)
        self.assertEqual(len(b), 19)

        # test if we can get trills
        mxString = testPrimitive.notations32a
        a = parse(mxString)
        a = a.flatten()
        b = a.getElementsByClass(note.Note)

        mxString = testPrimitive.rhythmDurations03a
        a = parse(mxString)
        # a.show('t')
        self.assertEqual(len(a), 2)  # one part, plus metadata
        for part in a.getElementsByClass(stream.Part):
            self.assertEqual(len(part), 7)  # seven measures
            measures = part.getElementsByClass(stream.Measure)
            self.assertEqual(int(measures[0].number), 1)
            self.assertEqual(int(measures[-1].number), 7)

        # print(a.recurseRepr())

        # print(a.recurseRepr())

        # # get the third movement
        # mxFile = corpus.getWork('opus18no1')[2]
        # a = parse(mxFile)
        # a = a.flatten()
        # b = a.getElementsByClass(dynamics.Dynamic)
        # # 110 dynamics
        # self.assertEqual(len(b), 110)
        #
        # c = a.getElementsByClass(note.Note)
        # # over 1000 notes
        # self.assertEqual(len(c), 1289)

    def testConversionMXChords(self):
        from music21 import chord
        from music21.musicxml import testPrimitive

        mxString = testPrimitive.chordsThreeNotesDuration21c
        a = parse(mxString)
        for part in a.getElementsByClass(stream.Part):
            chords = part[chord.Chord]
            self.assertEqual(len(chords), 7)
            knownSize = [3, 2, 3, 3, 3, 3, 3]
            for i in range(len(knownSize)):
                # print(chords[i].pitches, len(chords[i].pitches))
                self.assertEqual(knownSize[i], len(chords[i].pitches))

    def testConversionMXBeams(self):
        from music21 import note
        from music21.musicxml import testPrimitive

        mxString = testPrimitive.beams01
        a = parse(mxString)
        part = a.parts[0]
        notes = part.recurse().notesAndRests
        beams = []
        for n in notes:
            if isinstance(n, note.Note):
                beams += n.beams.beamsList
        self.assertEqual(len(beams), 152)

    def testConversionMXTime(self):

        from music21.musicxml import testPrimitive

        mxString = testPrimitive.timeSignatures11c
        a = parse(mxString)
        unused_part = a.parts[0]

        mxString = testPrimitive.timeSignatures11d
        a = parse(mxString)
        part = a.parts[0]

        notes = part.recurse().notesAndRests
        self.assertEqual(len(notes), 11)

    def testConversionMXClefPrimitive(self):
        from music21 import clef
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.clefs12a
        a = parse(mxString)
        part = a.parts[0]

        clefs = part[clef.Clef]
        self.assertEqual(len(clefs), 18)

    def testConversionMXClefTimeCorpus(self):
        from music21 import corpus
        from music21 import clef
        from music21 import meter
        a = corpus.parse('luca')

        # there should be only one clef in each part
        clefs = a.parts[0][clef.Clef]
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].sign, 'G')

        # second part
        clefs = a.parts[1][clef.Clef]
        self.assertEqual(len(clefs), 1)
        self.assertEqual(clefs[0].octaveChange, -1)
        self.assertEqual(type(clefs[0]).__name__, 'Treble8vbClef')

        # third part
        clefs = a.parts[2][clef.Clef]
        self.assertEqual(len(clefs), 1)

        # check time signature count
        ts = a.parts[1][meter.TimeSignature]
        self.assertEqual(len(ts), 4)

    def testConversionMXArticulations(self):
        from music21 import note
        from music21.musicxml import testPrimitive

        mxString = testPrimitive.articulations01
        a = parse(mxString)
        part = a.parts[0]

        notes = part.flatten().getElementsByClass(note.Note)
        self.assertEqual(len(notes), 4)
        post = []
        match = ["<class 'music21.articulations.Staccatissimo'>",
                 "<class 'music21.articulations.Accent'>",
                 "<class 'music21.articulations.Staccato'>",
                 "<class 'music21.articulations.Tenuto'>"]
        for i in range(len(notes)):
            post.append(str(notes[i].articulations[0].__class__))
        self.assertEqual(post, match)
        # a.show()

    def testConversionMXKey(self):
        from music21 import key
        from music21.musicxml import testPrimitive
        mxString = testPrimitive.keySignatures13a
        a = parse(mxString)
        part = a.parts[0]

        keyList = part[key.KeySignature]
        self.assertEqual(len(keyList), 46)

    def testConversionMXMetadata(self):
        from music21.musicxml import testFiles

        a = parse(testFiles.mozartTrioK581Excerpt)
        self.assertEqual(a.metadata.composer, 'Wolfgang Amadeus Mozart')
        self.assertEqual(a.metadata.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(a.metadata.movementName, 'Menuetto (Excerpt from Second Trio)')

        a = parse(testFiles.binchoisMagnificat)
        self.assertEqual(a.metadata.composer, 'Gilles Binchois')
        # this gets the best title available, even though this is movement title
        self.assertEqual(a.metadata.bestTitle, 'Excerpt from Magnificat secundi toni')

    def testConversionMXBarlines(self):
        from music21 import bar
        from music21.musicxml import testPrimitive
        a = parse(testPrimitive.barlines46a)
        part = a.parts[0]
        barlineList = part[bar.Barline]
        self.assertEqual(len(barlineList), 11)

    def testConversionXMLayout(self):

        from music21.musicxml import testPrimitive
        from music21 import layout

        a = parse(testPrimitive.systemLayoutTwoPart)
        # a.show()

        part = a.getElementsByClass(stream.Part).first()
        systemLayoutList = part[layout.SystemLayout]
        measuresWithSL = []
        for e in systemLayoutList:
            measuresWithSL.append(e.measureNumber)
        self.assertEqual(measuresWithSL, [1, 3, 4, 5, 7, 8])
        self.assertEqual(len(systemLayoutList), 6)

    def testConversionMXTies(self):

        from music21.musicxml import testPrimitive
        from music21 import clef

        a = parse(testPrimitive.multiMeasureTies)
        # a.show()

        countTies = 0
        countStartTies = 0
        for p in a.parts:
            post = p.recurse().notes[0].getContextByClass(clef.Clef)
            self.assertIsInstance(post, clef.TenorClef)
            for n in p.recurse().notes:
                if n.tie is not None:
                    countTies += 1
                    if n.tie.type in ('start', 'continue'):
                        countStartTies += 1

        self.assertEqual(countTies, 57)
        self.assertEqual(countStartTies, 40)

    def testConversionMXInstrument(self):
        from music21 import corpus
        from music21 import instrument
        s = corpus.parse('schumann_clara/opus17', 3)
        # s.show()
        is1 = s.parts[0][instrument.Instrument]
        self.assertEqual(len(is1), 1)
        # self.assertIn('Violin', is1[0].classes)
        is2 = s.parts[1][instrument.Instrument]
        self.assertEqual(len(is2), 1)
        # self.assertIn('Violoncello', is1[0].classes)
        is3 = s.parts[2][instrument.Instrument]
        self.assertEqual(len(is3), 1)
        # self.assertIn('Piano', is1[0].classes)

    def testConversionMidiBasic(self):
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test01.mid'

        # a simple file created in athenacl

        unused_s = parseFile(fp)
        unused_s = parse(fp)

        c = subConverters.ConverterMidi()
        c.parseFile(fp)

        # try low level string data passing
        with fp.open('rb') as f:
            data = f.read()

        c.parseData(data)

        # try module-level; function
        parseData(data)
        parse(data)

    def testConversionMidiNotes(self):
        from music21 import meter
        from music21 import key
        from music21 import chord
        from music21 import note

        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test01.mid'
        # a simple file created in athenacl
        # for fn in ['test01.mid', 'test02.mid', 'test03.mid', 'test04.mid']:
        s = parseFile(fp)
        # s.show()
        self.assertEqual(len(s[note.Note]), 18)

        # has chords and notes
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test05.mid'
        s = parseFile(fp)
        # s.show()
        # environLocal.printDebug(['\n' + 'opening fp', fp])

        self.assertEqual(len(s[note.Note]), 2)
        self.assertEqual(len(s[chord.Chord]), 5)

        # MIDI import makes measures, so we will have one 4/4 time sig
        self.assertEqual(len(s[meter.TimeSignature]), 1)
        self.assertEqual(len(s[key.KeySignature]), 0)

        # this sample has eighth note triplets
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test06.mid'
        s = parseFile(fp)
        # s.show()

        # environLocal.printDebug(['\n' + 'opening fp', fp])

        # s.show()
        from fractions import Fraction as F
        dList = [n.quarterLength for n in s.flatten().notesAndRests[:30]]
        match = [0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5,
                 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                 0.5, 0.5, 0.5, 0.5, F(1, 3), F(1, 3), F(1, 3), 0.5, 0.5, 1.0]
        self.assertEqual(dList, match)

        self.assertEqual(len(s[meter.TimeSignature]), 1)
        self.assertEqual(len(s[key.KeySignature]), 1)

        # this sample has sixteenth note triplets
        # TODO much work is still needed on getting timing right
        # this produces numerous errors in makeMeasure partitioning
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test07.mid'
        # environLocal.printDebug(['\n' + 'opening fp', fp])
        s = parseFile(fp)
        # s.show('t')
        self.assertEqual(len(s[meter.TimeSignature]), 1)
        self.assertEqual(len(s[key.KeySignature]), 1)

        # this sample has dynamic changes in key signature
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test08.mid'
        # environLocal.printDebug(['\n' + 'opening fp', fp])
        s = parseFile(fp)
        # s.show('t')
        self.assertEqual(len(s[meter.TimeSignature]), 1)
        found = s[key.KeySignature]
        self.assertEqual(len(found), 3)
        # test the right keys
        self.assertEqual(found[0].sharps, -3)
        self.assertEqual(found[1].sharps, 3)
        self.assertEqual(found[2].sharps, -1)

    def testConversionMXRepeats(self):
        from music21 import bar
        from music21.musicxml import testPrimitive

        mxString = testPrimitive.simpleRepeat45a
        s = parse(mxString)

        part = s.parts[0]
        measures = part.getElementsByClass(stream.Measure)
        self.assertEqual(measures[0].leftBarline, None)
        self.assertEqual(measures[0].rightBarline.type, 'final')

        self.assertEqual(measures[1].leftBarline, None)
        self.assertEqual(measures[1].rightBarline.type, 'final')

        mxString = testPrimitive.repeatMultipleTimes45c
        s = parse(mxString)

        self.assertEqual(len(s[bar.Barline]), 4)
        part = s.parts[0]
        measures = part.getElementsByClass(stream.Measure)

        # s.show()

    def testConversionABCOpus(self):
        from music21.abcFormat import testFiles
        from music21 import corpus

        s = parse(testFiles.theAleWifesDaughter)
        # get a Stream object, not an opus
        self.assertIsInstance(s, stream.Score)
        self.assertNotIsInstance(s, stream.Opus)
        self.assertEqual(len(s.recurse().notesAndRests), 66)

        # a small essen collection
        op = corpus.parse('essenFolksong/teste')
        # get a Stream object, not an opus
        # self.assertIsInstance(op, stream.Score)
        self.assertIsInstance(op, stream.Opus)
        self.assertEqual([len(s.recurse().notesAndRests) for s in op.scores],
                         [33, 51, 59, 33, 29, 174, 67, 88])
        # op.show()

        # get one work from the opus
        s = corpus.parse('essenFolksong/teste', number=6)
        self.assertIsInstance(s, stream.Score)
        self.assertNotIsInstance(s, stream.Opus)
        self.assertEqual(s.metadata.title, 'Moli hua')

        # s.show()

    def testConversionABCWorkFromOpus(self):
        # test giving a work number at loading
        from music21 import corpus
        s = corpus.parse('essenFolksong/han1', number=6)
        self.assertIsInstance(s, stream.Score)
        # noinspection SpellCheckingInspection
        self.assertEqual(s.metadata.title, 'Yi gan hongqi kongzhong piao')
        # make sure that beams are being made
        self.assertEqual(
            str(s.parts[0].recurse().notesAndRests[4].beams),
            '<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>')
        # s.show()

    def testConversionMusedata(self):
        fp = common.getSourceFilePath() / 'musedata' / 'testPrimitive' / 'test01'
        s = parse(fp)
        self.assertEqual(len(s.parts), 5)
        # s.show()

    def testMixedArchiveHandling(self):
        '''
        Test getting data out of musedata or musicxml zip files.
        '''
        fp = common.getSourceFilePath() / 'musicxml' / 'testMxl.mxl'
        af = ArchiveManager(fp)
        # for now, only support zip
        self.assertEqual(af.archiveType, 'zip')
        self.assertTrue(af.isArchive())
        # if this is a musicxml file, there will only be single file; we
        # can call getData to get this
        post = af.getData()
        self.assertEqual(post[:38], '<?xml version="1.0" encoding="UTF-8"?>')
        self.assertEqual(af.getNames(), ['musicXML.xml', 'META-INF/', 'META-INF/container.xml'])

        # # test from a file that ends in zip
        # # note: this is a stage1 file!
        # fp = common.getSourceFilePath() / 'musedata' / 'testZip.zip'
        # af = ArchiveManager(fp)
        # # for now, only support zip
        # self.assertEqual(af.archiveType, 'zip')
        # self.assertTrue(af.isArchive())
        # self.assertEqual(af.getNames(), ['01/', '01/04', '01/02', '01/03', '01/01'] )
        #
        # # returns a list of strings
        # self.assertEqual(af.getData(dataFormat='musedata')[0][:30],
        #                  '378\n1080  1\nBach Gesells\nchaft')

        # mdw = musedataModule.MuseDataWork()
        # # can add a list of strings from getData
        # mdw.addString(af.getData(dataFormat='musedata'))
        # self.assertEqual(len(mdw.files), 4)
        #
        # mdpList = mdw.getParts()
        # self.assertEqual(len(mdpList), 4)

        # try to load parse the zip file
        # s = parse(fp)

        # test loading a directory
        fp = common.getSourceFilePath() / 'musedata' / 'testPrimitive' / 'test01'
        cmd = subConverters.ConverterMuseData()
        cmd.parseFile(fp)

    def testMEIvsMX(self):
        '''
        Ensure Converter.parseData() distinguishes between a string with MEI data and a string with
        MusicXML data. The "subConverter" module is mocked out because we don't actually need to
        test the conversion process in this unit test.
        '''
        # These strings aren't valid documents, but they are enough to pass the detection we're
        # testing in parseData(). But it does mean we'll be testing in a strange way.
        meiString = '<?xml version="1.0" encoding="UTF-8"?><mei><note/></mei>'
        # mxlString = ('<?xml version="1.0" encoding="UTF-8"?>' +
        #                '<score-partwise><note/></score-partwise>')

        # The "mei" module raises an MeiElementError with "meiString," so as long as that's raised,
        # we know that parseData() chose correctly.
        from music21.mei.base import MeiElementError
        testConv = Converter()
        self.assertRaises(MeiElementError, testConv.parseData, meiString)

        # TODO: another test -- score-partwise is good enough for new converter.
        # The ConverterMusicXML raises a SubConverterException with "mxlString," so as long as
        # that's raised, we know that parseData()... well at least that it didn't choose MEI.
        # from music21.converter.subConverters import SubConverterException
        # testConv = Converter()
        # self.assertRaises(SubConverterException, testConv.parseData, mxlString)

    def testParseMidiQuantize(self):
        '''
        Checks quantization when parsing a stream. Here everything snaps to the 8th note.
        '''
        from music21 import note
        from music21 import omr

        midiFp = omr.correctors.pathName + os.sep + 'k525short.mid'
        midiStream = parse(midiFp, forceSource=True, storePickle=False, quarterLengthDivisors=(2,))
        # midiStream.show()
        for n in midiStream[note.Note]:
            self.assertTrue(isclose(n.quarterLength % 0.5, 0.0, abs_tol=1e-7))

    def testParseMidiNoQuantize(self):
        '''
        Checks that quantization is not performed if quantizePost=False.
        Source MIDI file contains only: 3 16th notes, 2 32nd notes.
        '''
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test15.mid'

        # Don't forceSource: test that pickles contemplate quantization keywords
        streamFpQuantized = parse(fp)
        self.assertNotIn(0.875, streamFpQuantized.flatten()._uniqueOffsetsAndEndTimes())

        streamFpNotQuantized = parse(fp, quantizePost=False)
        self.assertIn(0.875, streamFpNotQuantized.flatten()._uniqueOffsetsAndEndTimes())

        streamFpCustomQuantized = parse(fp, quarterLengthDivisors=(2,))
        self.assertNotIn(0.75, streamFpCustomQuantized.flatten()._uniqueOffsetsAndEndTimes())

        # Also check raw data: https://github.com/cuthbertLab/music21/issues/546
        with fp.open('rb') as f:
            data = f.read()
        self.assertIsInstance(data, bytes)
        streamDataNotQuantized = parse(data, quantizePost=False)
        self.assertIn(0.875, streamDataNotQuantized.flatten()._uniqueOffsetsAndEndTimes())

        # Remove pickles so that failures are possible in future
        pf1 = PickleFilter(fp)
        pf1.removePickle()
        pf2 = PickleFilter(fp, quantizePost=False)
        pf2.removePickle()
        pf3 = PickleFilter(fp, quarterLengthDivisors=(2,))
        pf3.removePickle()

    def testIncorrectNotCached(self):
        '''
        Here is a filename with an incorrect extension (.txt for .rnText).  Make sure that
        it is not cached the second time...
        '''
        from music21 import harmony

        fp = common.getSourceFilePath() / 'converter' / 'incorrectExtension.txt'
        pf = PickleFilter(fp)
        pf.removePickle()

        with self.assertRaises(ConverterFileException):
            parse(fp)

        c = parse(fp, format='romantext')
        self.assertEqual(len(c[harmony.Harmony]), 1)

    def testConverterFromPath(self):
        fp = common.getSourceFilePath() / 'corpus' / 'bach' / 'bwv66.6.mxl'
        s = parse(fp)
        self.assertIn('Stream', s.classes)

        fp = common.getSourceFilePath() / 'corpus' / 'bach' / 'bwv66.6'

        with self.assertRaises(FileNotFoundError):
            parse(fp)
        with self.assertRaises(ConverterException):
            # nonexistent path ending in incorrect extension
            # no way to tell apart from data, so failure happens later
            parse(str(fp))
        with self.assertRaises(FileNotFoundError):
            parse('nonexistent_path_ending_in_correct_extension.musicxml')

    def testParseURL(self):
        '''
        This should be the only test that requires an internet connection.
        '''
        from music21.humdrum.spineParser import HumdrumException

        urlBase = 'https://raw.githubusercontent.com/craigsapp/chopin-preludes/'
        url = urlBase + 'f8fb01f09d717e84929fb8b2950f96dd6bc05686/kern/prelude28-20.krn'

        e = environment.Environment()
        e['autoDownload'] = 'allow'
        s = parseURL(url)
        self.assertEqual(len(s.parts), 2)

        # This file should have been written, above
        destFp = Converter()._getDownloadFp(e.getRootTempDir(), '.krn', url)
        # Hack garbage into it so that we can test whether forceSource works
        with open(destFp, 'a', encoding='utf-8') as fp:
            fp.write('all sorts of garbage that Humdrum cannot parse')

        with self.assertRaises(HumdrumException):
            s = parseURL(url, forceSource=False)

        # make sure that forceSource still overrides the system.
        s = parseURL(url, forceSource=True)
        self.assertEqual(len(s.parts), 2)

        # make sure that the normal parse system can handle URLs, not just parseURL.
        s = parse(url)
        self.assertEqual(len(s.parts), 2)

        os.remove(destFp)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [parse, parseFile, parseData, parseURL, freeze, thaw, freezeStr, thawStr,
              Converter, registerSubConverter, unregisterSubConverter]


if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)  # , runTest='testConverterFromPath')
