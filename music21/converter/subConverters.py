# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         converter/__init__.py
# Purpose:      Specific subConverters for formats music21 should handle
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
SubConverters parse or display a single format.

Each subConverter should inherit from the base SubConverter object and have at least a
parseData method that sets self.stream.
'''
from __future__ import annotations

# ------------------------------------------------------------------------------
# Converters are associated classes; they are not subclasses,
# but most define a parseData() method,
# a parseFile() method, and a .stream attribute or property.
from io import IOBase
import os
import pathlib
import subprocess
import typing as t
import unittest

from music21 import common
from music21 import defaults
from music21 import environment
from music21.exceptions21 import SubConverterException
from music21 import stream


if t.TYPE_CHECKING:
    from collections.abc import Iterable

environLocal = environment.Environment('converter.subConverters')

# pylint complains when abstract methods are not overwritten, but that's okay.
# pylint: disable=abstract-method

class SubConverter:
    '''
    Class wrapper for parsing data or outputting data.

    All other Converter types should inherit from this and
    have ways of dealing with various data formats.

    Attributes that should be set::

        readBinary = True or False (default False)
        registerFormats = tuple of formats that can be handled; eg: ('musicxml',)
        registerShowFormats = tuple of format calls that can be handled in .show() and .write()
        registerInputExtensions = tuple of input extensions that should be handled in converter
        registerOutputExtensions = tuple of output extensions that can be written. Order matters:
            the first will be used in calls to .write()
        canBePickled = True or False (default True; does not do anything yet)
        codecWrite = True or False (default False) if encodings need to be used to write
        stringEncoding = string (default 'utf-8'). If codecWrite is True, this specifies what
            encoding to use


    '''
    readBinary: bool = False
    canBePickled: bool = True
    registerFormats: tuple[str, ...] = ()
    registerShowFormats: tuple[str, ...] = ()
    registerInputExtensions: tuple[str, ...] = ()  # if converter supports input
    registerOutputExtensions: tuple[str, ...] = ()  # if converter supports output
    registerOutputSubformatExtensions: dict[str, str] = {}
    launchKey: str | pathlib.Path | None = None

    codecWrite: bool = False
    stringEncoding: str = 'utf-8'

    def __init__(self, **keywords) -> None:
        self._stream: stream.Score | stream.Part | stream.Opus = stream.Score()
        self.keywords: dict[str, t.Any] = keywords

    def parseData(self, dataString, number: int | None = None):
        '''
        Called when a string (or binary) data is encountered.

        This method MUST be implemented to do anything in parsing.

        Return self.stream in the end
        '''
        raise NotImplementedError
        # return self.stream

    def parseFile(self,
                  filePath: str | pathlib.Path,
                  number: int | None = None,
                  **keywords):
        '''
        Called when a file is encountered. If all that needs to be done is
        loading the file and putting the data into parseData then there is no need
        to implement this method.  Just set self.readBinary to True | False.
        '''
        if self.readBinary is False:
            import locale
            with open(filePath, encoding=locale.getpreferredencoding()) as f:
                dataStream = f.read()
        else:
            with open(filePath, 'rb') as f:
                dataStream = f.read()  # type: ignore

        # might raise NotImplementedError
        self.parseData(dataStream, number)

        return self.stream

    def _getStream(self):
        return self._stream

    def _setStream(self, newStream):
        self._stream = newStream

    stream = property(_getStream, _setStream, doc='''
        Returns or sets the stream in the converter.  Must be defined for subConverter to work.
        ''')

    def checkShowAbility(self, **keywords) -> bool:
        '''
        return bool on whether the *system* is
        equipped to show in this format.

        Default True. Might be False if, say
        a Lilypond converter is used and Lilypond
        is not installed.
        '''
        return True

    def launch(self,
               filePath: pathlib.Path,
               fmt=None,
               options: str = '',
               app: str | None = None,
               launchKey=None):  # pragma: no cover
        '''
        Opens the appropriate viewer for the file generated by .write()

        app is the path to an application to launch.  Specify it and/or a launchKey.
        launchKey is the specific key in .music21rc (such as graphicsPath), etc.
        to search for the application.  If it's not specified then there might be
        a default one for the converter in self.launchKey.  If it can't find it
        there then environLocal.formatToApp(fmt) will be used.

        Not needed for formats for which .show() just prints to the console.
        '''
        if fmt is None and self.registerShowFormats:
            fmt = self.registerShowFormats[0]
        elif fmt is None:  # pragma: no cover
            raise ValueError('launch: fmt can only be None if there is a registered show format.')

        if app is None:
            if launchKey is not None:
                app = environLocal[launchKey]
            elif self.launchKey is not None:
                launchKey = self.launchKey
                app = environLocal[launchKey]
            else:
                launchKey = environLocal.formatToKey(fmt)
                app = environLocal.formatToApp(fmt)
            # app may still be None

        platform: str = common.getPlatform()
        shell: bool = False
        cmd: tuple[str, ...]
        if app is None:
            if platform == 'win':
                # no need to specify application here:
                # windows starts the program based on the file extension
                # Q: should options be here?
                cmd = ('start', str(filePath))
                shell = True
            elif platform == 'darwin':
                if options:
                    cmd = ('open', options, str(filePath))
                else:
                    cmd = ('open', str(filePath))
            else:
                raise SubConverterException(
                    f'Cannot find a valid application path for format {fmt}. '
                    + 'Specify this in your Environment by calling '
                    + f"environment.set({launchKey!r}, '/path/to/application')"
                )
        elif platform in ('win', 'nix'):
            if options:
                cmd = (app, options, str(filePath))
            else:
                cmd = (app, str(filePath))
        elif platform == 'darwin':
            if options:
                cmd = ('open', '-a', str(app), options, str(filePath))
            else:
                cmd = ('open', '-a', str(app), str(filePath))
        else:
            raise SubConverterException(f'Cannot launch files on {platform}')
        try:
            subprocess.run(cmd, check=False, shell=shell)
        except FileNotFoundError as e:
            # musicXML path misconfigured
            raise SubConverterException(
                'Most issues with show() can be resolved by calling configure.run()'
            ) from e

    def show(
        self,
        obj,
        fmt: str | None,
        app=None,
        subformats=(),
        **keywords
    ) -> None:
        '''
        Write the data, then show the generated data, using `.launch()` or printing
        to a console.

        Some simple formats that do not need launching, may skip .launch() and
        simply return the output.
        '''
        returnedFilePath = self.write(obj, fmt, subformats=subformats, **keywords)
        self.launch(returnedFilePath, fmt=fmt, app=app)

    def getExtensionForSubformats(self, subformats: Iterable[str] = ()) -> str:
        '''
        Given a default format or subformats, give the file extension it should have:

        >>> c = converter.subConverters.ConverterMidi()
        >>> c.getExtensionForSubformats()
        '.mid'
        '''
        extensions = self.registerOutputExtensions
        if not extensions:
            raise SubConverterException(
                'This subConverter cannot show or write: '
                + 'no output extensions are registered for it')
        # start by trying the first one.
        ext = extensions[0]
        if self.registerOutputSubformatExtensions and subformats:
            joinedSubformats = '.'.join(subformats)
            if joinedSubformats in self.registerOutputSubformatExtensions:
                ext = self.registerOutputSubformatExtensions[joinedSubformats]
        return '.' + ext

    def getTemporaryFile(self, subformats: Iterable[str] = ()) -> pathlib.Path:
        '''
        Return a temporary file with an extension appropriate for the format.

        >>> c = corpus.parse('bwv66.6')
        >>> lpConverter = converter.subConverters.ConverterLilypond()
        >>> tf = str(lpConverter.getTemporaryFile(subformats=['png']))
        >>> tf.endswith('.png')
        True
        >>> import os  #_DOCS_HIDE
        >>> os.remove(tf)  #_DOCS_HIDE

        * Changed in v6: returns pathlib.Path
        '''
        ext = self.getExtensionForSubformats(subformats)
        fp = environLocal.getTempFile(ext, returnPathlib=True)
        return fp

    def write(self,
              obj: music21.base.Music21Object,
              fmt: str | None,
              fp: str | pathlib.Path | IOBase | None = None,
              subformats: Iterable[str] = (),
              **keywords):  # pragma: no cover
        '''
        Calls .writeDataStream on the repr of obj, and returns the fp returned by it.
        '''
        dataStr = repr(obj)
        fp = self.writeDataStream(fp, dataStr, **keywords)
        return fp

    def writeDataStream(self,
                        fp: str | pathlib.Path | IOBase | None,
                        dataStr: str | bytes,
                        **keywords) -> pathlib.Path:  # pragma: no cover
        '''
        Writes the data stream to `fp` or to a temporary file and returns the
        Path object of the filename written.
        '''
        if fp is None:
            fp = self.getTemporaryFile()

        if self.readBinary is False:
            writeFlags = 'w'
        else:
            writeFlags = 'wb'

        if self.codecWrite is False and isinstance(dataStr, bytes):
            try:
                dataStr = dataStr.decode('utf-8')
            except UnicodeDecodeError:
                # Reattempt below with self.stringEncoding
                self.codecWrite = True
                # Close file if already open, because we need to reopen with encoding
                if isinstance(fp, IOBase):
                    fp.close()

        if isinstance(fp, (str, pathlib.Path)):
            fp = common.cleanpath(fp, returnPathlib=True)
            with open(fp,
                      mode=writeFlags,
                      encoding=self.stringEncoding if self.codecWrite else None
                      ) as f:
                f.write(dataStr)
            return fp
        else:
            # file-like object
            fp.write(dataStr)
            fp.close()
            return pathlib.Path('')

    def toData(
        self,
        obj,
        fmt: str | None,
        subformats: Iterable[str] = (),
        **keywords,
    ) -> str | bytes:
        '''
        Write the object out in the given format and then read it back in
        and return the object (str or bytes) returned.
        '''
        fp = self.write(obj, fmt=fmt, subformats=subformats, **keywords)
        if self.readBinary is False:
            readFlags = 'r'
        else:
            readFlags = 'rb'
        with open(fp,
                  mode=readFlags,
                  encoding=self.stringEncoding if self.codecWrite else None
                  ) as f:
            out = f.read()
        fp.unlink(missing_ok=True)
        return out


class ConverterIPython(SubConverter):
    '''
    Meta-subConverter for displaying image data in a Notebook
    using either png (via MuseScore or LilyPond) or directly via
    Vexflow/music21j, or MIDI using music21j.
    '''
    registerFormats = ('ipython', 'jupyter')
    registerOutputExtensions = ()
    registerOutputSubformatExtensions = {'lilypond': 'ly'}

    def show(self, obj, fmt, app=None, subformats=(),
             **keywords):  # pragma: no cover
        '''
        show a specialized for Jupyter Notebook using the appropriate subformat.

        For MusicXML runs it through MuseScore and returns the PNG data.
        (use multipageWidget to get an experimental interactive page display).

        For MIDI: loads a music21j-powered MIDI player in to the Notebook.
        '''
        from music21.converter import Converter
        from music21.ipython21 import converters as ip21_converters

        if subformats:
            helperFormat = subformats[0]
            helperSubformats = subformats[1:]
        else:
            helperFormat = 'musicxml'
            helperSubformats = []

        if not helperSubformats:
            helperSubformats = ['png']

        helperSubConverter = Converter.getSubConverterFromFormat(helperFormat)

        if helperFormat in ('musicxml', 'xml', 'lilypond', 'lily'):
            ip21_converters.showImageThroughMuseScore(
                obj,
                subConverter=helperSubConverter,
                fmt=helperFormat,
                subformats=helperSubformats,
                **keywords,
            )
        elif helperFormat == 'midi':
            if t.TYPE_CHECKING:
                assert isinstance(helperSubConverter, ConverterMidi)
            ip21_converters.displayMusic21jMIDI(
                obj,
                subConverter=helperSubConverter,
                fmt=helperFormat,
                subformats=helperSubformats,
                **keywords,
            )


class ConverterLilypond(SubConverter):
    '''
    Convert to Lilypond and from there usually to png, pdf, or svg.

    Note: that the proper format for displaying Lilypond in Jupyter
    notebook in v9 is ipython.lily.png and not lily.ipython.png
    '''
    registerFormats = ('lilypond', 'lily')
    registerOutputExtensions = ('ly', 'png', 'pdf', 'svg')
    registerOutputSubformatExtensions = {'png': 'png',
                                         'pdf': 'pdf',
                                         'svg': ''}  # sic! (Why?)
    codecWrite = True

    def write(self,
              obj,
              fmt,
              fp=None,
              subformats=(),
              *,
              coloredVariants: bool = False,
              **keywords):  # pragma: no cover
        from music21 import lily
        conv = lily.translate.LilypondConverter()
        conv.coloredVariants = coloredVariants
        conv.loadFromMusic21Object(obj)

        if 'pdf' in subformats:
            convertedFilePath = conv.createPDF(fp)
        elif 'png' in subformats:
            convertedFilePath = conv.createPNG(fp)
        elif 'svg' in subformats:
            convertedFilePath = conv.createSVG(fp)
        else:
            convertedFilePath = conv.writeLyFile(ext='.ly', fp=fp)
        return convertedFilePath

    def show(self, obj, fmt, app=None, subformats=(), **keywords):  # pragma: no cover
        '''
        Call .write (write out the lilypond (.ly) file; convert to .png/.pdf, etc.)
        then launch the appropriate viewer for .png/.pdf (graphicsPath) or .svg
        (vectorPath)
        '''
        if not subformats:
            subformats = ['png']
        returnedFilePath = self.write(obj, fmt, subformats=subformats, **keywords)
        if subformats is not None and subformats:
            outFormat = subformats[0]
        else:
            outFormat = 'png'

        # TODO: replace with run_subprocess_capturing_stderr.
        launchKey = environLocal.formatToKey(outFormat)
        self.launch(returnedFilePath, fmt=outFormat, app=app, launchKey=launchKey)


class ConverterBraille(SubConverter):
    registerFormats = ('braille',)
    registerOutputExtensions = ('txt',)
    codecWrite = True

    def show(
        self,
        obj,
        fmt,
        app=None,
        subformats=(),
        **keywords
    ):  # pragma: no cover
        if not common.runningInNotebook():
            super().show(obj, fmt, app=None, subformats=subformats, **keywords)
        else:
            from music21 import braille
            dataStr = braille.translate.objectToBraille(obj)
            print(dataStr)

    def write(
        self,
        obj,
        fmt,
        fp=None,
        subformats=(),
        **keywords
    ):  # pragma: no cover
        from music21 import braille
        dataStr = braille.translate.objectToBraille(obj, **keywords)
        if 'ascii' in subformats:
            dataStr = braille.basic.brailleUnicodeToBrailleAscii(dataStr)
        fp = self.writeDataStream(fp, dataStr)
        return fp


class ConverterVexflow(SubConverter):
    registerFormats = ('vexflow',)
    registerOutputExtensions = ('html',)

    def write(self,
              obj,
              fmt,
              fp=None,
              subformats=(),
              *,
              local: bool = False,
              **keywords):  # pragma: no cover
        # from music21 import vexflow
        from music21.vexflow import toMusic21j as vexflow
        dataStr = vexflow.fromObject(obj, mode='html', local=local)
        fp = self.writeDataStream(fp, dataStr)
        return fp


class ConverterText(SubConverter):
    '''
    standard text presentation has line breaks, is printed.

    Two keyword options are allowed: addEndTimes=Boolean and useMixedNumerals=Boolean
    '''

    registerFormats = ('text', 'txt', 't')
    registerOutputExtensions = ('txt',)

    def write(self, obj, fmt, fp=None, subformats=(), **keywords):  # pragma: no cover
        dataStr = obj._reprText(**keywords)
        self.writeDataStream(fp, dataStr)
        return fp

    def show(self, obj, fmt, app=None, subformats=(), **keywords):
        print(obj._reprText(**keywords))


class ConverterTextLine(SubConverter):
    '''
    a text line compacts the complete recursive representation into a
    single line of text; most for debugging. returned, not printed

    >>> s = corpus.parse('bwv66.6')
    >>> s.measures(1, 4).show('textline')
    "{0.0} <music21.stream.Part Soprano> / {0.0} <music21.instrument.Instrument '... 1'>..."
    '''
    registerFormats = ('textline',)
    registerOutputExtensions = ('txt',)

    def write(self, obj, fmt, fp=None, subformats=(), **keywords):  # pragma: no cover
        dataStr = obj._reprTextLine()
        self.writeDataStream(fp, dataStr)
        return fp

    def show(self, obj, fmt, app=None, subformats=(), **keywords):
        return obj._reprTextLine()


class ConverterVolpiano(SubConverter):
    '''
    Reads or writes volpiano (Chant encoding).

    Normally, just use 'converter' and .show()/.write()

    >>> p = converter.parse('volpiano: 1---c-d-ef----4')
    >>> p.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F>
        {4.0} <music21.volpiano.Neume <music21.note.Note E><music21.note.Note F>>
        {4.0} <music21.bar.Barline type=double>
    >>> p.show('volpiano')
    1---c-d-ef----4
    '''
    registerFormats = ('volpiano',)
    registerInputExtensions = ('volpiano', 'vp')
    registerOutputExtensions = ('txt', 'vp')

    def parseData(
        self,
        dataString,
        number: int | None = None,
        *,
        breaksToLayout: bool = False,
        **keywords,
    ):
        from music21 import volpiano
        self.stream = volpiano.toPart(dataString, breaksToLayout=breaksToLayout)

    def getDataStr(self, obj, **keywords):
        '''
        Get the raw data, for storing as a variable.
        '''
        from music21 import volpiano
        if obj.isStream:
            s = obj
        else:
            s = stream.Stream()
            s.append(obj)

        return volpiano.fromStream(s)

    def write(self, obj, fmt, fp=None, subformats=(), **keywords):  # pragma: no cover
        dataStr = self.getDataStr(obj, **keywords)
        self.writeDataStream(fp, dataStr)
        return fp

    def show(self, obj, fmt, app=None, subformats=(), **keywords):
        print(self.getDataStr(obj, **keywords))


class ConverterScala(SubConverter):
    registerFormats = ('scala',)
    registerInputExtensions = ('scl',)
    registerOutputExtensions = ('scl',)


# ------------------------------------------------------------------------------
class ConverterHumdrum(SubConverter):
    '''
    Simple class wrapper for parsing Humdrum data provided in a file or in a string.
    '''
    registerFormats = ('humdrum',)
    registerInputExtensions = ('krn',)

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.data = None

    # --------------------------------------------------------------------------

    def parseData(self, humdrumString, number=None):
        '''
        Open Humdrum data from a string -- calls
        :meth:`~music21.humdrum.spineParser.HumdrumDataCollection.parse()`.

        >>> humData = ('**kern\\n*M2/4\\n=1\\n24r\\n24g#\\n24f#\\n24e\\n24c#\\n' +
        ...     '24f\\n24r\\n24dn\\n24e-\\n24gn\\n24e-\\n24dn\\n*-')
        >>> c = converter.subConverters.ConverterHumdrum()
        >>> s = c.parseData(humData)
        >>> c.stream.show('text')
        {0.0} <music21.metadata.Metadata object at 0x7f33545027b8>
        {0.0} <music21.stream.Part spine_0>
            {0.0} <music21.humdrum.spineParser.MiscTandem **kern>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.meter.TimeSignature 2/4>
                {0.0} <music21.note.Rest 1/6ql>
                {0.1667} <music21.note.Note G#>
                {0.3333} <music21.note.Note F#>
                {0.5} <music21.note.Note E>
                {0.6667} <music21.note.Note C#>
                {0.8333} <music21.note.Note F>
                {1.0} <music21.note.Rest 1/6ql>
                {1.1667} <music21.note.Note D>
                {1.3333} <music21.note.Note E->
                {1.5} <music21.note.Note G>
                {1.6667} <music21.note.Note E->
                {1.8333} <music21.note.Note D>
        '''
        from music21.humdrum.spineParser import HumdrumDataCollection

        hdf = HumdrumDataCollection(humdrumString)
        hdf.parse()
        self.data = hdf
        self.stream = self.data.stream
        return self.data

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number: int | None = None,
                  **keywords):
        '''
        Open Humdrum data from a file path.

        Calls humdrum.parseFile on filepath.

        Number is ignored here.
        '''
        from music21.humdrum.spineParser import HumdrumFile
        hf = HumdrumFile(filePath)
        hf.parseFilename()
        self.data = hf
        # self.data.stream.makeNotation()

        self.stream = self.data.stream
        return self.data

# ------------------------------------------------------------------------------


class ConverterTinyNotation(SubConverter):
    '''
    Simple class wrapper for parsing TinyNotation data provided in a file or
    in a string.

    Input only for now.
    '''
    registerFormats = ('tinynotation',)
    registerInputExtensions = ('tntxt', 'tinynotation')

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.data = None

    # --------------------------------------------------------------------------
    def parseData(self, tnData, number=None):
        # noinspection PyShadowingNames
        '''
        Open TinyNotation data from a string

        >>> tnData = "3/4 E4 r f# g=lastG trip{b-8 a g} c"
        >>> c = converter.subConverters.ConverterTinyNotation()
        >>> s = c.parseData(tnData)
        >>> c.stream.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Rest quarter>
            {2.0} <music21.note.Note F#>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note B->
            {1.3333} <music21.note.Note A>
            {1.6667} <music21.note.Note G>
            {2.0} <music21.note.Note C>
            {2.5} <music21.bar.Barline type=final>
        '''
        if isinstance(tnData, str):
            tnStr = tnData
        else:  # assume a 2 element sequence  # pragma: no cover
            raise SubConverterException(
                'TinyNotation no longer supports two-element calls; put the time signature '
                + 'in the stream')
        from music21 import tinyNotation
        self.stream = tinyNotation.Converter(tnStr, **self.keywords).parse().stream


class ConverterNoteworthy(SubConverter):
    # noinspection SpellCheckingInspection
    '''
    Simple class wrapper for parsing NoteworthyComposer data provided in a
    file or in a string.

    Gets data with the file format .nwctxt

    Users should not need this routine.  The basic format is converter.parse('file.nwctxt')


    >>> nwcTranslatePath = common.getSourceFilePath() / 'noteworthy' #_DOCS_HIDE
    >>> paertPath = nwcTranslatePath / 'Part_OWeisheit.nwctxt' #_DOCS_HIDE
    >>> #_DOCS_SHOW paertPath = converter.parse(r'd:/desktop/arvo_part_o_weisheit.nwctxt')
    >>> paertStream = converter.parse(paertPath)
    >>> len(paertStream.parts)
    4

    For developers: see the documentation for :meth:`parseData` and :meth:`parseFile`
    to see the low-level usage.
    '''
    registerFormats = ('noteworthytext',)
    registerInputExtensions = ('nwctxt',)

    # --------------------------------------------------------------------------
    def parseData(self, nwcData):
        # noinspection PyShadowingNames
        r'''
        Open Noteworthy data from a string or list

        >>> nwcData = ('!NoteWorthyComposer(2.0)\n|AddStaff\n|Clef|' +
        ...     'Type:Treble\n|Note|Dur:Whole|Pos:1^')
        >>> c = converter.subConverters.ConverterNoteworthy()
        >>> c.parseData(nwcData)
        >>> c.stream.show('text')
        {0.0} <music21.stream.Part ...>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.note.Note C>
        '''
        from music21.noteworthy import translate as noteworthyTranslate
        self.stream = noteworthyTranslate.NoteworthyTranslator().parseString(nwcData)

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number: int | None = None,
                  **keywords):
        # noinspection SpellCheckingInspection,PyShadowingNames
        '''
        Open Noteworthy data (as nwctxt) from a file path.

        >>> nwcTranslatePath = common.getSourceFilePath() / 'noteworthy' #_DOCS_HIDE
        >>> filePath = nwcTranslatePath / 'Part_OWeisheit.nwctxt' #_DOCS_HIDE
        >>> #_DOCS_SHOW paertPath = converter.parse('d:/desktop/arvo_part_o_weisheit.nwctxt')
        >>> c = converter.subConverters.ConverterNoteworthy()
        >>> c.parseFile(filePath)
        >>> #_DOCS_SHOW c.stream.show()
        '''
        from music21.noteworthy import translate as noteworthyTranslate
        self.stream = noteworthyTranslate.NoteworthyTranslator().parseFile(filePath)


class ConverterNoteworthyBinary(SubConverter):
    '''
    Simple class wrapper for parsing NoteworthyComposer binary data
    provided in a file or in a string.

    Gets data with the file format .nwc

    Users should not need this routine.  Call converter.parse directly
    '''
    readBinary = True
    registerFormats = ('noteworthy',)
    registerInputExtensions = ('nwc', )

    # --------------------------------------------------------------------------
    def parseData(self, nwcData):  # pragma: no cover
        from music21.noteworthy import binaryTranslate as noteworthyBinary
        self.stream = noteworthyBinary.NWCConverter().parseString(nwcData)

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number: int | None = None,
                  **keywords):
        from music21.noteworthy import binaryTranslate as noteworthyBinary
        self.stream = noteworthyBinary.NWCConverter().parseFile(filePath)


# ------------------------------------------------------------------------------
class ConverterMusicXML(SubConverter):
    '''
    Converter for MusicXML using the 2015 ElementTree system.

    Users should not need this Object.  Call converter.parse directly
    '''
    registerFormats = ('musicxml', 'xml')
    registerInputExtensions = ('xml', 'mxl', 'musicxml')
    registerOutputExtensions = ('musicxml', 'xml', 'mxl')
    registerOutputSubformatExtensions = {'png': 'png',
                                         'pdf': 'pdf',
                                         }

    def parseData(self, xmlString: str, number=None):
        '''
        Open MusicXML data from a string.
        '''
        from music21.musicxml import xmlToM21

        c = xmlToM21.MusicXMLImporter()
        c.xmlText = xmlString
        c.parseXMLText()
        self.stream = c.stream

    def parseFile(self,
                  filePath: str | pathlib.Path,
                  number: int | None = None,
                  **keywords):
        '''
        Open from a file path; check to see if there is a pickled
        version available and up to date; if so, open that, otherwise
        open source.
        '''
        # return fp to load, if pickle needs to be written, fp pickle
        # this should be able to work on a .mxl file, as all we are doing
        # here is seeing which is more recent
        from music21 import converter
        from music21.musicxml import xmlToM21

        c = xmlToM21.MusicXMLImporter()

        # here, we can see if this is a mxl or similar archive
        arch = converter.ArchiveManager(filePath)
        if arch.isArchive():
            archData = arch.getData()
            c.xmlText = archData
            c.parseXMLText()
        else:  # it is a file path or a raw musicxml string
            c.readFile(filePath)

        # movement titles can be stored in more than one place in musicxml
        # manually insert file name as a movementName title if no titles are defined
        if c.stream.metadata.movementName is None:
            junk, fn = os.path.split(filePath)
            c.stream.metadata.movementName = fn  # this should become a Path
        self.stream = c.stream

    def writeDataStream(self,
                        fp,
                        dataStr: str | bytes,
                        **keywords) -> pathlib.Path:  # pragma: no cover
        # noinspection PyShadowingNames
        '''
        Writes `dataStr` which must be bytes to `fp`.
        Adds `.musicxml` suffix to `fp` if it does not already contain some suffix.

        * Changed in v7: returns a pathlib.Path

        OMIT_FROM_DOCS

        >>> import os
        >>> from music21.converter.subConverters import ConverterMusicXML
        >>> fp = 'noSuffix'
        >>> sub = ConverterMusicXML()
        >>> outFp = sub.writeDataStream(fp, b'')
        >>> str(outFp).endswith('.musicxml')
        True

        >>> os.remove(outFp)
        >>> fp = 'other.suffix'
        >>> outFp = sub.writeDataStream(fp, b'')
        >>> str(outFp).endswith('.suffix')
        True
        >>> os.remove(outFp)
        '''
        if not isinstance(dataStr, bytes):
            raise ValueError(f'{dataStr} must be bytes to write to this format')
        dataBytes = dataStr

        fpPath: pathlib.Path
        if fp is None:
            fpPath = self.getTemporaryFile()
        else:
            fpPath = common.cleanpath(fp, returnPathlib=True)

        if not fpPath.suffix or fpPath.suffix == '.mxl':
            fpPath = fpPath.with_suffix('.musicxml')

        writeFlags = 'wb'

        with open(fpPath, writeFlags) as f:
            f.write(dataBytes)  # type: ignore

        return fpPath

    def write(self,
              obj: music21.Music21Object,
              fmt,
              fp=None,
              subformats=(),
              *,
              makeNotation=True,
              compress: bool | None = None,
              **keywords):
        '''
        Write to a .musicxml file.

        Set `makeNotation=False` to prevent fixing up the notation, and where possible,
        to prevent making additional deepcopies. (This option cannot be used if `obj` is not a
        :class:`~music21.stream.Score`.) `makeNotation=True` generally solves common notation
        issues, whereas `makeNotation=False` is intended for advanced users facing
        special cases where speed is a priority or making notation reverses user choices.

        Set `compress=True` to immediately compress the output to a .mxl file.  Set
        to True automatically if format='mxl' or if `fp` is given and ends with `.mxl`
        '''
        from music21.musicxml import archiveTools, m21ToXml

        savedDefaultTitle = defaults.title
        savedDefaultAuthor = defaults.author

        if compress is None:
            if fp and str(fp).endswith('.mxl'):
                compress = True
            elif fmt.startswith('mxl'):
                # currently unreachable from Music21Object.write()
                compress = True
            else:
                compress = False

        # hack to make MuseScore excerpts -- fix with a converter class in MusicXML
        if 'png' in subformats:
            # do not print a title or author -- to make the PNG smaller.
            defaults.title = ''
            defaults.author = ''

        dataBytes: bytes = b''
        generalExporter = m21ToXml.GeneralObjectExporter(obj)
        generalExporter.makeNotation = makeNotation
        dataBytes = generalExporter.parse()

        writeDataStreamFp = fp
        if fp is not None and subformats:  # could be empty list
            fpStr = str(fp)
            noExtFpStr = os.path.splitext(fpStr)[0]
            writeDataStreamFp = noExtFpStr + '.musicxml'

        xmlFp: pathlib.Path = self.writeDataStream(writeDataStreamFp, dataBytes)

        if 'png' in subformats:
            defaults.title = savedDefaultTitle
            defaults.author = savedDefaultAuthor

        if (('png' in subformats or 'pdf' in subformats)
                and not str(environLocal['musescoreDirectPNGPath']).startswith('/skip')):
            from music21.converter.museScore import runThroughMuseScore
            outFp = runThroughMuseScore(xmlFp, subformats, **keywords)
        elif compress:
            archiveTools.compressXML(xmlFp,
                                     deleteOriginal=True,
                                     silent=True,
                                     strictMxlCheck=False)
            filenameOut = xmlFp.with_suffix('.mxl')
            outFp = common.pathTools.cleanpath(filenameOut, returnPathlib=True)
        else:
            outFp = xmlFp

        return outFp

    def show(self, obj, fmt, app=None, subformats=(), **keywords):  # pragma: no cover
        '''
        Override to do something with png...
        '''
        returnedFilePath = self.write(obj, fmt, subformats=subformats, **keywords)
        if 'png' in subformats:
            fmt = 'png'
        elif 'pdf' in subformats:
            fmt = 'pdf'
        self.launch(returnedFilePath, fmt=fmt, app=app)


# ------------------------------------------------------------------------------
class ConverterMidi(SubConverter):
    '''
    Simple class wrapper for parsing MIDI and sending MIDI data out.
    '''
    readBinary = True
    registerFormats = ('midi',)
    registerInputExtensions = ('mid', 'midi')
    registerOutputExtensions = ('mid',)

    def parseData(self, strData, number=None):
        '''
        Get MIDI data from a binary string representation.

        Calls midi.translate.midiStringToStream.

        Keywords to control quantization:
        `quantizePost` controls whether to quantize the output. (Default: True)
        `quarterLengthDivisors` allows for overriding the default quantization units
        in defaults.quantizationQuarterLengthDivisors. (Default: (4, 3)).
        '''
        from music21.midi import translate as midiTranslate
        self.stream = midiTranslate.midiStringToStream(strData, **self.keywords)

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number: int | None = None,
                  **keywords):
        '''
        Get MIDI data from a file path.

        Calls midi.translate.midiFilePathToStream.

        Keywords to control quantization:
        `quantizePost` controls whether to quantize the output. (Default: True)
        `quarterLengthDivisors` allows for overriding the default quantization units
        in defaults.quantizationQuarterLengthDivisors. (Default: (4, 3)).
        '''
        from music21.midi import translate as midiTranslate
        midiTranslate.midiFilePathToStream(filePath, inputM21=self.stream, **keywords)

    def write(self,
              obj,
              fmt,
              fp=None,
              subformats=(),
              *,
              addStartDelay: bool = False,
              **keywords):  # pragma: no cover
        from music21.midi import translate as midiTranslate
        if fp is None:
            fp = self.getTemporaryFile()

        mf = midiTranslate.music21ObjectToMidiFile(obj, addStartDelay=addStartDelay)
        mf.open(fp, 'wb')  # write binary
        mf.write()
        mf.close()
        return fp


# ------------------------------------------------------------------------------
class ConverterABC(SubConverter):
    '''
    Simple class wrapper for parsing ABC.

    Input only
    '''
    registerFormats = ('abc',)
    registerInputExtensions = ('abc',)

    def parseData(self, strData, number=None):
        '''
        Get ABC data, as token list, from a string representation.
        If more than one work is defined in the ABC data, a
        :class:`~music21.stream.Opus` object will be returned;
        otherwise, a :class:`~music21.stream.Score` is returned.
        '''
        from music21 import abcFormat
        af = abcFormat.ABCFile()
        # do not need to call open or close
        abcHandler = af.readstr(strData, number=number)
        # set to stream
        if abcHandler.definesReferenceNumbers():
            # this creates an Opus object, not a Score object
            self.stream = abcFormat.translate.abcToStreamOpus(abcHandler,
                                                              number=number)
        else:  # just one work
            abcFormat.translate.abcToStreamScore(abcHandler, self.stream)

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number: int | None = None,
                  **keywords):
        '''
        Get ABC data from a file path. If more than one work is defined in the ABC
        data, a  :class:`~music21.stream.Opus` object will be returned;
        otherwise, a :class:`~music21.stream.Score` is returned.

        If `number` is provided, and this ABC file defines multiple works
        with an X: tag, just the specified work will be returned.
        '''
        # environLocal.printDebug(['ConverterABC.parseFile: got number', number])
        from music21 import abcFormat

        af = abcFormat.ABCFile()
        af.open(filePath)
        # returns a handler instance of parse tokens
        abcHandler = af.read(number=number)
        af.close()

        # only create opus if multiple ref numbers
        # are defined; if a number is given an opus will not be created
        if abcHandler.definesReferenceNumbers():
            # this creates a Score or Opus object, depending on if a number
            # is given
            self.stream = abcFormat.translate.abcToStreamOpus(abcHandler,
                                                              number=number)
        # just get a single work
        else:
            abcFormat.translate.abcToStreamScore(abcHandler, self.stream)


class ConverterRomanText(SubConverter):
    '''
    Simple class wrapper for parsing roman text harmonic definitions.
    '''
    registerFormats = ('romantext', 'rntext')
    registerInputExtensions = ('rntxt', 'rntext', 'romantext', 'rtxt')
    registerOutputExtensions = ('rntxt',)

    def parseData(self, strData, number=None):
        from music21.romanText import rtObjects
        from music21.romanText import translate as romanTextTranslate
        rtf = rtObjects.RTFile()
        rtHandler = rtf.readstr(strData)
        if rtHandler.definesMovements():
            # this re-defines Score as an Opus
            self.stream = romanTextTranslate.romanTextToStreamOpus(rtHandler)
        else:
            romanTextTranslate.romanTextToStreamScore(rtHandler, self.stream)

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number: int | None = None,
                  **keywords):
        from music21.romanText import rtObjects
        from music21.romanText import translate as romanTextTranslate
        rtf = rtObjects.RTFile()
        rtf.open(filePath)
        # returns a handler instance of parse tokens
        rtHandler = rtf.read()
        rtf.close()
        romanTextTranslate.romanTextToStreamScore(rtHandler, self.stream)

    def write(self, obj, fmt, fp=None, subformats=(), **keywords):  # pragma: no cover
        '''
        Writes 'RomanText' files (using the extension .rntxt) from a music21.stream.
        '''

        from music21.romanText import writeRoman
        if fp is None:
            fp = self.getTemporaryFile()

        if not hasattr(fp, 'write'):
            with open(fp, 'w', encoding='utf-8') as text_file:
                for entry in writeRoman.RnWriter(obj).combinedList:
                    text_file.write(entry + '\n')
        else:
            # file-like object
            for entry in writeRoman.RnWriter(obj).combinedList:
                fp.write(entry + '\n')

        return fp


class ConverterClercqTemperley(SubConverter):
    '''
    Wrapper for parsing harmonic definitions in Trevor de Clercq and
    David Temperley's format.
    '''
    registerFormats = ('cttxt', 'har', 'clercqTemperley')
    registerInputExtensions = ('cttxt', 'har', 'clercqTemperley')

    def parseData(self, strData: str | pathlib.Path, number=None):
        from music21.romanText import clercqTemperley
        ctSong = clercqTemperley.CTSong(strData)
        self.stream = ctSong.toPart()

    def parseFile(self,
                  filePath: pathlib.Path | str,
                  number=None,
                  **keywords):
        self.parseData(filePath)


class ConverterCapella(SubConverter):
    '''
    Simple class wrapper for parsing Capella .capx XML files.  See capella/fromCapellaXML.
    '''
    registerFormats = ('capella',)
    registerInputExtensions = ('capx',)

    def parseData(self, strData, number=None):
        '''
        parse a data stream of uncompressed capella xml

        N.B. for web parsing, it gets more complex.
        '''
        from music21.capella import fromCapellaXML
        ci = fromCapellaXML.CapellaImporter()
        ci.parseXMLText(strData)
        scoreObj = ci.systemScoreFromScore(ci.mainDom.documentElement)
        partScore = ci.partScoreFromSystemScore(scoreObj)
        self.stream = partScore

    def parseFile(self,
                  filePath: str | pathlib.Path,
                  number: int | None = None,
                  **keywords):
        '''
        Parse a Capella file
        '''
        from music21.capella import fromCapellaXML
        ci = fromCapellaXML.CapellaImporter()
        self.stream = ci.scoreFromFile(filePath)


# ------------------------------------------------------------------------------
class ConverterMuseData(SubConverter):
    '''
    Simple class wrapper for parsing MuseData.
    '''
    registerFormats = ('musedata',)
    registerInputExtensions = ('md', 'musedata', 'zip')

    def parseData(self, strData, number=None):  # pragma: no cover
        '''
        Get musedata from a string representation.
        '''
        from music21 import musedata as musedataModule
        from music21.musedata import translate as musedataTranslate

        if isinstance(strData, str):
            strDataList = [strData]
        else:
            strDataList = strData

        mdw = musedataModule.MuseDataWork()

        for strDataInner in strDataList:
            mdw.addString(strDataInner)

        musedataTranslate.museDataWorkToStreamScore(mdw, self.stream)

    def parseFile(self,
                  filePath: str | pathlib.Path,
                  number: int | None = None,
                  **keywords):
        '''
        parse fp (a pathlib.Path()) and number
        '''
        fp: pathlib.Path
        if not isinstance(filePath, pathlib.Path):
            fp = pathlib.Path(filePath)
        else:
            fp = filePath

        from music21 import converter
        from music21 import musedata as musedataModule
        from music21.musedata import translate as musedataTranslate

        mdw = musedataModule.MuseDataWork()

        af = converter.ArchiveManager(fp)

        # environLocal.printDebug(['ConverterMuseData: parseFile', fp, af.isArchive()])
        # for dealing with one or more files
        if fp.suffix == '.zip' or af.isArchive():
            # environLocal.printDebug(['ConverterMuseData: found archive', fp])
            # get data will return all data from the zip as a single string
            for partStr in af.getData(dataFormat='musedata'):
                # environLocal.printDebug(['partStr', len(partStr)])
                mdw.addString(partStr)
        else:
            if fp.is_dir():
                mdd = musedataModule.MuseDataDirectory(fp)
                fpList = mdd.getPaths()
            elif not common.isListLike(fp):
                fpList = [fp]
            else:
                fpList = fp

            for fpInner in fpList:
                mdw.addFile(fpInner)

        # environLocal.printDebug(['ConverterMuseData: mdw file count', len(mdw.files)])

        musedataTranslate.museDataWorkToStreamScore(mdw, self.stream)


class ConverterMEI(SubConverter):
    '''
    Converter for MEI. You must use an ".mei" file extension for MEI files because music21 will
    parse ".xml" files as MusicXML.
    '''
    registerFormats = ('mei',)
    registerInputExtensions = ('mei',)
    # NOTE: we're only working on import for now
    # registerShowFormats = ('mei',)
    # registerOutputExtensions = ('mei',)

    def parseData(self, dataString: str, number=None) -> stream.Stream:
        '''
        Convert a string with an MEI document into its corresponding music21 elements.

        * dataString: The string with XML to convert.

        * number: Unused in this class. Default is ``None``.

        Returns the music21 objects corresponding to the MEI file.
        '''
        from music21 import mei
        if dataString.startswith('mei:'):
            dataString = dataString[4:]

        self.stream = mei.MeiToM21Converter(dataString).run()

        return self.stream

    def parseFile(
        self,
        filePath: str | pathlib.Path,
        number: int | None = None,
        **keywords,
    ) -> stream.Stream:
        '''
        Convert a file with an MEI document into its corresponding music21 elements.

        * filePath: Full pathname to the file containing MEI data as a string or Path.

        * number: Unused in this class. Default is ``None``.

        Returns the music21 objects corresponding to the MEI file.
        '''
        # In Python 3 we try the two most likely encodings to work. (UTF-16 is outputted from
        # "sibmei", the Sibelius-to-MEI exporter).
        try:
            with open(filePath, 'rt', encoding='utf-8') as f:
                dataStream = f.read()
        except UnicodeDecodeError:
            with open(filePath, 'rt', encoding='utf-16') as f:
                dataStream = f.read()

        self.parseData(dataStream, number)

        return self.stream

    def checkShowAbility(self, **keywords):
        '''
        MEI export is not yet implemented.
        '''
        return False

    # def launch(self, filePath, fmt=None, options='', app=None, key=None):
    #     raise NotImplementedError('MEI export is not yet implemented.')

    def show(self, obj, fmt, app=None, subformats=(), **keywords):  # pragma: no cover
        raise NotImplementedError('MEI export is not yet implemented.')

    # def getTemporaryFile(self, subformats=()):
    #     raise NotImplementedError('MEI export is not yet implemented.')

    def write(self, obj, fmt, fp=None, subformats=(), **keywords):  # pragma: no cover
        raise NotImplementedError('MEI export is not yet implemented.')

    # def writeDataStream(self, fp, dataStr):
    #     raise NotImplementedError('MEI export is not yet implemented.')


class Test(unittest.TestCase):

    def testSimpleTextShow(self):
        from music21 import note
        n = note.Note()
        s = stream.Stream()
        s.append(n)
        unused_x = s.show('textLine')

    def testImportMei1(self):
        '''
        When the string starts with "mei:"
        '''
        from unittest import mock
        with mock.patch('music21.mei.MeiToM21Converter') as mockConv:
            testConverter = ConverterMEI()
            testConverter.parseData('mei: <?xml><mei><note/></mei>')
            mockConv.assert_called_once_with(' <?xml><mei><note/></mei>')

    def testImportMei2(self):
        '''
        When the string doesn't start with "mei:"
        '''
        from unittest import mock
        with mock.patch('music21.mei.MeiToM21Converter') as mockConv:
            testConverter = ConverterMEI()
            testConverter.parseData('<?xml><mei><note/></mei>')
            mockConv.assert_called_once_with('<?xml><mei><note/></mei>')

    def testImportMei3(self):
        '''
        When the file uses UTF-16 encoding rather than UTF-8 (which happens if
        it was exported from
        the "sibmei" plug-in for Sibelius).
        '''
        from unittest import mock  # pylint: disable=no-name-in-module
        with mock.patch('music21.mei.MeiToM21Converter') as mockConv:
            testPath = common.getSourceFilePath() / 'mei' / 'test' / 'notes_in_utf16.mei'
            testConverter = ConverterMEI()
            testConverter.parseFile(testPath)
            self.assertEqual(1, mockConv.call_count)

    def testImportMei4(self):
        '''
        For the sake of completeness, this is the same as testImportMei3() but with a UTF-8 file.
        '''
        from unittest import mock  # pylint: disable=no-name-in-module
        with mock.patch('music21.mei.MeiToM21Converter') as mockConv:
            testPath = common.getSourceFilePath() / 'mei' / 'test' / 'notes_in_utf8.mei'
            testConverter = ConverterMEI()
            testConverter.parseFile(testPath)
            self.assertEqual(1, mockConv.call_count)

    def testWriteMXL(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parseData(testPrimitive.multiDigitEnding)
        mxlPath = s.write('mxl')
        self.assertTrue(str(mxlPath).endswith('.mxl'), f'{mxlPath} does not end with .mxl')

        # Just the filepath ending in .mxl is sufficient to write .mxl
        s.write(fp=mxlPath)
        # Verify that it actually wrote bytes
        with self.assertRaises(UnicodeDecodeError):
            with open(mxlPath, 'r', encoding='utf-8') as f:
                f.read(20)

        # Also test ConverterMusicXML object directly
        conv = ConverterMusicXML()
        mxlPath2 = conv.write(obj=s, fmt='mxl')
        with self.assertRaises(UnicodeDecodeError):
            with open(mxlPath2, 'r', encoding='utf-8') as f:
                f.read(20)

        os.remove(mxlPath)
        os.remove(mxlPath2)

    def testWriteMusicXMLMakeNotation(self):
        from music21 import converter
        from music21 import note
        from music21.musicxml.xmlObjects import MusicXMLExportException

        m1 = stream.Measure(note.Note(quarterLength=5.0))
        m2 = stream.Measure()
        p = stream.Part([m1, m2])
        s = stream.Score(p)

        self.assertEqual(len(m1.notes), 1)
        self.assertEqual(len(m2.notes), 0)

        out1 = s.write()  # makeNotation=True is assumed
        # 4/4 will be assumed; quarter note will be moved to measure 2
        round_trip_back = converter.parse(out1)
        self.assertEqual(
            len(round_trip_back.parts.first().getElementsByClass(stream.Measure)[0].notes), 1)
        self.assertEqual(
            len(round_trip_back.parts.first().getElementsByClass(stream.Measure)[1].notes), 1)

        with self.assertRaises(MusicXMLExportException):
            # must splitAtDurations()!
            s.write(makeNotation=False)

        s = s.splitAtDurations(recurse=True)[0]
        out2 = s.write(makeNotation=False)
        round_trip_back = converter.parse(out2)
        # 4/4 will not be assumed; quarter note will still be split out from 5.0QL,
        # but it will remain in measure 1
        # and there will be no rests in measure 2
        self.assertEqual(
            len(round_trip_back.parts.first().getElementsByClass(stream.Measure)[0].notes), 2)
        self.assertEqual(
            len(round_trip_back.parts.first().getElementsByClass(stream.Measure)[1].notes), 0)

        # makeNotation = False cannot be used on non-scores
        with self.assertRaises(MusicXMLExportException):
            p.write(makeNotation=False)

        for out in (out1, out2):
            os.remove(out)

    def testBrailleKeywords(self):
        from music21 import converter

        p = converter.parse('tinyNotation: c1 d1 e1 f1')
        out = p.write('braille', debug=True)
        with open(out, 'r', encoding='utf-8') as f:
            self.assertIn('<music21.braille.segment BrailleSegment>', f.read())
        os.remove(out)

    def testWriteRomanText(self):
        import textwrap
        from io import StringIO
        from music21 import converter

        rntxt = textwrap.dedent('''
            Time Signature: 3/4
            m1 C: I
        ''')
        s = converter.parse(rntxt, format='romanText')
        text_stream = StringIO()
        s.write('romanText', text_stream)
        self.assertTrue(text_stream.getvalue().endswith(rntxt))

class TestExternal(unittest.TestCase):
    show = True

    def testXMLShow(self):
        from music21 import corpus
        c = corpus.parse('bwv66.6')
        if self.show:
            c.show()  # musicxml

    def testWriteLilypond(self):
        from music21 import note
        n = note.Note()
        n.duration.type = 'whole'
        s = stream.Stream()
        s.append(n)
        if self.show:
            s.show('lily.png')
            print(s.write('lily.png'))

    def testMultiPageXMlShow1(self):
        '''
        tests whether show() works for music that is 10-99 pages long
        '''
        from music21 import omr
        from music21 import converter
        K525 = omr.correctors.K525groundTruthFilePath
        K525 = converter.parse(K525)
        if self.show:
            K525.show('musicxml.png')
            print(K525.write('musicxml.png'))

    # def testMultiPageXMlShow2(self):
    #     '''
    #      tests whether show() works for music that is 100-999 pages long.
    #      Currently, takes way too long to run.
    #      '''
    #     from music21 import stream, note
    #     biggerStream = stream.Stream()
    #     note1 = note.Note('C4')
    #     note1.duration.type = 'whole'
    #     biggerStream.repeatAppend(note1, 10000)
    #     biggerStream.show('musicxml.png')
    #     biggerStream.show()
    #     print(biggerStream.write('musicxml.png'))


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
    # run command below to test commands that open museScore, etc.
    # music21.mainTest(TestExternal)
