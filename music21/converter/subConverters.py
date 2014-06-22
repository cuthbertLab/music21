# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         converter/__init__.py
# Purpose:      Specific subconverters for formats music21 should handle
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''
Each subconverter should inherit from the base SubConverter object and have at least a 
parseData method that sets self.stream
'''
#-------------------------------------------------------------------------------
# Converters are associated classes; they are not subclasses, but most define a pareData() method, a parseFile() method, and a .stream attribute or property.
import os
import unittest

from music21.ext import six
from music21 import common
from music21 import stream
from music21 import exceptions21

from music21 import environment
_MOD = 'converter/subConverters.py'
environLocal = environment.Environment(_MOD)


class SubConverterException(exceptions21.Music21Exception):
    pass

class SubConverter(object):
    '''
    Class wrapper for parsing data or outputting data.  
    
    All other Converter types should inherit from this and
    have ways of dealing with various data formats.
    
    Attributes that should be set: 
    
        readBinary = True or False (default False)
        registerFormats = tuple of formats that can be handled; eg: ('musicxml',)
        registerShowFormats = tuple of format calls that can be handled in .show() and .write()
        registerInputExtensions = tuple of input extensions that should be handled in converter
        registerOutputExtensions = tuple of output extensions that can be written. Order matters:
            the first will be used in calls to .write()
        canBePickled = True or False (default True; does not do anything yet)
        codecWrite = True or False (default False) if codecs need to be used to write
        stringEncoding = string (default 'utf-8') if codecWrite is True, what encoding to use

    '''
    readBinary = False
    canBePickled = True
    registerFormats = ()
    registerShowFormats = ()
    registerInputExtensions = ()
    registerOutputExtensions = ()
    registerOutputSubformatExtensions = None
    launchKey = None
    
    codecWrite = False
    stringEncoding='utf-8'
    
    def __init__(self):
        self._stream = stream.Score()

    def parseData(self, dataString, number=None):
        '''
        Called when a string (or binary) data is encountered.
        
        This method MUST be implemented to do anything.
        '''
        return self.stream
    
    def parseFile(self, filePath, number=None):
        '''
        Called when a file is encountered. If all that needs to be done is
        loading the file and putting the data into parseData then there is no need
        to do anything except set self.readBinary (True|False).
        '''
        if self.readBinary is False:
            with open(filePath) as f:
                dataStream = f.read()
        else:
            with open(filePath, 'rb') as f:
                dataStream = f.read()
        self.parseData(dataStream, number)
        return self.stream
    
    def _getStream(self):
        return self._stream

    def _setStream(self, newStream):
        self._stream = newStream

    stream = property(_getStream, _setStream, doc='''
        Returns or sets the stream in the converter.  Must be defined for subconverter to work.
        ''')
    
    def checkShowAbility(self, **keywords):
        '''
        return bool on whether the *system* is
        equipped to show in this format.
        
        Default True. Might be False if, say
        a Lilypond converter is used and Lilypond
        is not installed.
        '''
        return True

    def launch(self, filePath, fmt=None, options='', app=None, key=None):
        if fmt is None and len(self.registerShowFormats) > 0:
            fmt = self.registerShowFormats[0]    
        if app is None:
            if key is not None:
                app = environLocal._ref[key]
            elif self.launchKey is not None:
                app = environLocal._ref[self.launchKey]
            else:
                app = environLocal.formatToApp(fmt)

        platform = common.getPlatform()
        if app is None:
            if platform == 'win':
                # no need to specify application here:
                # windows starts the program based on the file extension
                cmd = 'start %s' % (filePath)
            elif platform == 'darwin':
                cmd = 'open %s %s' % (options, filePath)
            else:
                raise SubConverterException(
                    "Cannot find a valid application path for format {}. "
                    "Specify this in your Environment by calling "
                    "environment.set({!r}, 'pathToApplication')".format(
                        self.registerFormats[0], self.launchKey))
        elif platform == 'win':  # note extra set of quotes!
            cmd = '""%s" %s "%s""' % (app, options, filePath)
        elif platform == 'darwin':
            cmd = 'open -a"%s" %s %s' % (app, options, filePath)
        elif platform == 'nix':
            cmd = '%s %s %s' % (app, options, filePath)
        os.system(cmd)

    def show(self, obj, fmt, app=None, subformats=None, **keywords):
        returnedFilePath = self.write(obj, fmt, subformats=subformats, **keywords)
        self.launch(returnedFilePath, fmt=fmt, app=app)

    def getExtensionForFormatOrSubformats(self, fmt=None, subformats=None):
        exts = self.registerOutputExtensions
        if len(exts) == 0:
            raise SubConverterException("Cannot show or write -- no output extension")
        ext = exts[0]
        if self.registerOutputSubformatExtensions is not None and subformats is not None:
            joinedSubformats = '.'.join(subformats)
            if joinedSubformats in self.registerOutputSubformatExtensions:
                ext = self.registerOutputSubformatExtensions[joinedSubformats]
        return "." + ext

    def getTemporaryFile(self, fmt=None, subformats=None):
        ext = self.getExtensionForFormatOrSubformats(fmt, subformats)
        fp = environLocal.getTempFile(ext)
        return fp

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        dataStr = repr(obj)
        self.writeDataStream(fp, dataStr)
        return fp
    
    def writeDataStream(self, fp, dataStr):
        if fp is None:
            fp = self.getTemporaryFile()

        if self.readBinary is False:
            writeFlags = 'w'
        else:
            writeFlags = 'wb'
        
        if self.codecWrite is False:
            with open(fp, writeFlags) as f:
                try:
                    f.write(dataStr)
                except TypeError as te:
                    raise SubConverterException("Could not convert %r : %r" % (dataStr, te))
        else:
            import codecs
            f = codecs.open(fp, mode=writeFlags, encoding=self.stringEncoding)
            f.write(dataStr)
            f.close()
        return fp
    
class ConverterIPython(SubConverter):
    registerFormats = ('ipython',)
    registerOutputExtensions = ()
    registerOutputSubformatExtensions = {'lilypond': 'ly'}
    def vfshow(self, s):
        import random
        from music21.vexflow import toMusic21j
        from IPython.display import HTML
        vfp = toMusic21j.VexflowPickler()
        vfp.mode = 'jsonSplit'
        outputCode = vfp.fromObject(s)
        idName = 'canvasDiv' + str(random.randint(0, 10000))
        htmlBlock = '<div id="' + idName + '"><canvas/></div>'
        js = '''
        <script>
             data = ''' + outputCode + ''';       
             var jpc = new music21.jsonPickle.Converter();
             var streamObj = jpc.run(data);
             streamObj.replaceLastCanvas("#''' + idName + '''");
        </script>
        '''
        return HTML(htmlBlock + js)
    
    def show(self, obj, fmt, app=None, subformats=None, **keywords):    
        if subformats is None:
            subformats = ['vexflow']
        
        if len(subformats) > 0 and subformats[0] == 'vexflow':
            return self.vfshow(obj)
            #subformats = ['lilypond','png']
        helperFormat = subformats[0]
        helperSubformats = subformats[1:]
        from music21 import converter
        helperConverter = converter.Converter()
        helperConverter.setSubconverterFromFormat(helperFormat)
        helperSubConverter = helperConverter.subConverter
        fp = helperSubConverter.write(obj, helperFormat, subformats=helperSubformats)
        if helperSubformats[0] == 'png':
            from music21.ipython21 import objects as ipythonObjects
            ipo = ipythonObjects.IPythonPNGObject(fp)
            return ipo
                
class ConverterLilypond(SubConverter):
    registerFormats = ('lilypond', 'lily')
    registerOutputExtensions = ('ly','png','pdf','svg')
    registerOutputSubformatExtensions = {'png': 'png',
                                         'pdf': 'pdf',
                                         'svg': ''} # sic!
    codecWrite = True

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        from music21 import lily
        conv = lily.translate.LilypondConverter()
        if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
            conv.coloredVariants = True
            
        if subformats is not None and 'pdf' in subformats:
            conv.loadFromMusic21Object(obj)
            convertedFilePath = conv.createPDF(fp)        
            return convertedFilePath

        elif subformats is not None and 'png' in subformats:
            conv.loadFromMusic21Object(obj)
            convertedFilePath = conv.createPNG(fp)
            if 'ipython' in subformats:
                from music21.ipython21 import objects as ipythonObjects
                ipo = ipythonObjects.IPythonPNGObject(convertedFilePath)
                return ipo
            else:
                return convertedFilePath
            
        elif subformats is not None and 'svg' in subformats:
            conv.loadFromMusic21Object(obj)
            convertedFilePath = conv.createSVG(fp)
            return convertedFilePath
        
        else:
            dataStr = conv.textFromMusic21Object(obj).encode('utf-8')
            fp = self.writeDataStream(fp, dataStr)
            return fp

    def show(self, obj, fmt, app=None, subformats=None, **keywords):
        if subformats is None or len(subformats) == 0:
            subformats = ['png']
        returnedFilePath = self.write(obj, fmt, subformats=subformats, **keywords)
        if subformats is not None and len(subformats) > 0:
            outFormat = subformats[0]
        else:
            outFormat = 'png'
        if app is None:
            app = environLocal.formatToApp(outFormat)
        self.launch(returnedFilePath, app=app)


class ConverterBraille(SubConverter):
    registerFormats = ('braille',)
    registerOutputExtensions = ('txt',)
    codecWrite = True

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        from music21 import braille
        dataStr = braille.translate.objectToBraille(obj)
        fp = self.writeDataStream(fp, dataStr)
        return fp
    
class ConverterVexflow(SubConverter):
    registerFormats = ('vexflow',)
    registerOutputExtensions = ('html',)

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        #from music21 import vexflow
        from music21.vexflow import toMusic21j as vexflow
        dataStr = vexflow.fromObject(obj, mode='html')
        fp = self.writeDataStream(fp, dataStr)
        return fp


class ConverterText(SubConverter):
    '''
    standard text presentation has line breaks, is printed.
    '''
    
    registerFormats = ('text','txt','t')
    registerOutputExtensions = ('txt',)

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        dataStr = obj._reprText()
        self.writeDataStream(fp, dataStr)
        return fp
    
    def show(self, obj, *args, **keywords):
        print(obj._reprText())

class ConverterTextLine(SubConverter):
    '''
    a text line compacts the complete recursive representation into a
    single line of text; most for debugging. returned, not printed
    
    >>> s = corpus.parse('bwv66.6')
    >>> s.measures(1,4).show('textline')
    u'{0.0} <music21.stream.Part Soprano> / {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>...' 
    '''
    registerFormats = ('textline',)
    registerOutputExtensions = ('txt',)

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        dataStr = obj._reprTextLine()
        self.writeDataStream(fp, dataStr)
        return fp

    def show(self, obj, *args, **keywords):
        return obj._reprTextLine()


class ConverterScala(SubConverter):
    registerFormats = ('scala',)
    registerInputExtensions = ('scl',)
    registerOutputExtensions = ('scl',)
    
#-------------------------------------------------------------------------------
class ConverterHumdrum(SubConverter):
    '''Simple class wrapper for parsing Humdrum data provided in a file or in a string.
    '''
    registerFormats = ('humdrum',)
    registerInputExtensions = ('krn',)

    #---------------------------------------------------------------------------
    def parseData(self, humdrumString, number=None):
        '''Open Humdrum data from a string -- calls humdrum.parseData()

        >>> humdata = '**kern\\n*M2/4\\n=1\\n24r\\n24g#\\n24f#\\n24e\\n24c#\\n24f\\n24r\\n24dn\\n24e-\\n24gn\\n24e-\\n24dn\\n*-'
        >>> c = converter.subConverters.ConverterHumdrum()
        >>> s = c.parseData(humdata)
        >>> c.stream.show('text')
        {0.0} <music21.stream.Part spine_0>
            {0.0} <music21.humdrum.spineParser.MiscTandem **kern humdrum control>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.meter.TimeSignature 2/4>
                {0.0} <music21.note.Rest rest>
                {0.1667} <music21.note.Note G#>
                {0.3333} <music21.note.Note F#>
                {0.5} <music21.note.Note E>
                {0.6667} <music21.note.Note C#>
                {0.8333} <music21.note.Note F>
                {1.0} <music21.note.Rest rest>
                {1.1667} <music21.note.Note D>
                {1.3333} <music21.note.Note E->
                {1.5} <music21.note.Note G>
                {1.6667} <music21.note.Note E->
                {1.8333} <music21.note.Note D>        
        '''
        from music21 import humdrum
        self.data = humdrum.parseData(humdrumString)
        #self.data.stream.makeNotation()

        self.stream = self.data.stream
        return self.data

    def parseFile(self, filepath, number=None):
        '''
        Open Humdram data from a file path.
        
        Calls humdrum.parseFile on filepath.
        
        Number is ignored here.
        '''
        from music21 import humdrum
        self.data = humdrum.parseFile(filepath)
        #self.data.stream.makeNotation()

        self.stream = self.data.stream
        return self.data

#-------------------------------------------------------------------------------
class ConverterTinyNotation(SubConverter):
    '''
    Simple class wrapper for parsing TinyNotation data provided in a file or 
    in a string.
    '''
    registerFormats = ('tinynotation',)
    registerInputExtensions = ('tntxt', 'tinynotation')
    #---------------------------------------------------------------------------
    def parseData(self, tnData, number=None):
        '''Open TinyNotation data from a string or list

        >>> tnData = ["E4 r f# g=lastG trip{b-8 a g} c", "3/4"]
        >>> c = converter.subConverters.ConverterTinyNotation()
        >>> s = c.parseData(tnData)
        >>> c.stream.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Rest rest>
        {2.0} <music21.note.Note F#>
        {3.0} <music21.note.Note G>
        {4.0} <music21.note.Note B->
        {4.3333} <music21.note.Note A>
        {4.6667} <music21.note.Note G>
        {5.0} <music21.note.Note C>        
        '''
        if common.isStr(tnData):
            tnStr = tnData
            tnTs = None
        else: # assume a 2 element sequence
            tnStr = tnData[0]
            tnTs = tnData[1]
        from music21 import tinyNotation
        self.stream = tinyNotation.TinyNotationStream(tnStr, tnTs)


class ConverterNoteworthy(SubConverter):
    '''
    Simple class wrapper for parsing NoteworthyComposer data provided in a 
    file or in a string.

    Gets data with the file format .nwctxt

    Users should not need this routine.  The basic format is converter.parse("file.nwctxt")


    >>> import os #_DOCS_HIDE
    >>> nwcTranslatePath = common.getSourceFilePath() + os.path.sep + 'noteworthy'
    >>> paertPath = nwcTranslatePath + os.path.sep + 'Part_OWeisheit.nwctxt' #_DOCS_HIDE
    >>> #_DOCS_SHOW paertPath = converter.parse(r'd:/desktop/arvo_part_o_weisheit.nwctxt')
    >>> paertStream = converter.parse(paertPath)
    >>> len(paertStream.parts)
    4

    For developers: see the documentation for :meth:`parseData` and :meth:`parseFile`
    to see the low-level usage.
    '''
    registerFormats = ('noteworthytext',)
    registerInputExtensions = ('nwctxt',)

    #---------------------------------------------------------------------------
    def parseData(self, nwcData):
        r'''Open Noteworthy data from a string or list

        >>> nwcData = "!NoteWorthyComposer(2.0)\n|AddStaff\n|Clef|Type:Treble\n|Note|Dur:Whole|Pos:1^"
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


    def parseFile(self, fp, number=None):
        '''
        Open Noteworthy data (as nwctxt) from a file path.


        >>> import os #_DOCS_HIDE
        >>> nwcTranslatePath = common.getSourceFilePath() + os.path.sep + 'noteworthy'
        >>> filePath = nwcTranslatePath + os.path.sep + 'Part_OWeisheit.nwctxt' #_DOCS_HIDE
        >>> #_DOCS_SHOW paertPath = converter.parse('d:/desktop/arvo_part_o_weisheit.nwctxt')
        >>> c = converter.subConverters.ConverterNoteworthy()
        >>> c.parseFile(filePath)
        >>> #_DOCS_SHOW c.stream.show()
        '''
        from music21.noteworthy import translate as noteworthyTranslate
        self.stream = noteworthyTranslate.NoteworthyTranslator().parseFile(fp)

class ConverterNoteworthyBinary(SubConverter):
    '''
    Simple class wrapper for parsing NoteworthyComposer binary data provided in a file or in a string.

    Gets data with the file format .nwc

    Users should not need this routine.  Call converter.parse directly
    '''
    readBinary = True
    registerFormats = ('noteworthy',)
    registerInputExtensions = ('nwc', )
    #---------------------------------------------------------------------------
    def parseData(self, nwcData):
        from music21.noteworthy import binaryTranslate as noteworthyBinary 
        self.stream = noteworthyBinary.NWCConverter().parseString(nwcData)


    def parseFile(self, fp, number=None):
        from music21.noteworthy import binaryTranslate as noteworthyBinary 
        self.stream = noteworthyBinary.NWCConverter().parseFile(fp)

#-------------------------------------------------------------------------------
class ConverterMusicXML(SubConverter):
    '''Converter for MusicXML
    '''
    registerFormats = ('musicxml','xml')
    registerInputExtensions = ('xml', 'mxl', 'mx', 'musicxml')
    registerOutputExtensions = ('xml', 'mxl')
    
    def __init__(self):
        self._mxScore = None # store the musicxml object representation
        SubConverter.__init__(self)

    #---------------------------------------------------------------------------
    def partIdToNameDict(self):
        return self._mxScore.partIdToNameDict()

    def load(self):
        '''Load all parts from a MusicXML object representation.
        This determines the order parts are found in the stream
        '''
        #t = common.Timer()
        #t.start()
        from music21.musicxml import fromMxObjects
        fromMxObjects.mxScoreToScore(self._mxScore, inputM21 = self.stream)
        #self._stream._setMX(self._mxScore)
        #t.stop()
        #environLocal.printDebug(['music21 object creation time:', t])

    #---------------------------------------------------------------------------
    def parseData(self, xmlString, number=None):
        '''Open MusicXML data from a string.'''
        from music21.musicxml import xmlHandler as musicxmlHandler
        c = musicxmlHandler.Document()
        c.read(xmlString)
        self._mxScore = c.score #  the mxScore object from the musicxml Document
        if len(self._mxScore) == 0:
            #print xmlString
            raise SubConverterException('score from xmlString (%s...) either has no parts defined or was incompletely parsed' % xmlString[:30])
        self.load()

    def parseFile(self, fp, number=None):
        '''
        Open from a file path; check to see if there is a pickled
        version available and up to date; if so, open that, otherwise
        open source.
        '''
        # return fp to load, if pickle needs to be written, fp pickle
        # this should be able to work on a .mxl file, as all we are doing
        # here is seeing which is more recent
        from music21 import converter        
        from music21.musicxml import xmlHandler as musicxmlHandler

        musxmlDocument = musicxmlHandler.Document()

        environLocal.printDebug(['opening musicxml file:', fp])

        # here, we can see if this is a mxl or similar archive
        arch = converter.ArchiveManager(fp)
        if arch.isArchive():
            archData = arch.getData()
            musxmlDocument.read(archData)
        else: # its a file path or a raw musicxml string
            musxmlDocument.open(fp)

        # get mxScore object from .score attribute
        self._mxScore = musxmlDocument.score
        #print self._mxScore
        # check that we have parts
        if self._mxScore is None or len(self._mxScore) == 0:
            raise SubConverterException('score from file path (%s) no parts defined' % fp)

        # movement titles can be stored in more than one place in musicxml
        # manually insert file name as a title if no titles are defined
        if self._mxScore.get('movementTitle') == None:
            mxWork = self._mxScore.get('workObj')
            if mxWork == None or mxWork.get('workTitle') == None:
                junk, fn = os.path.split(fp)
                # set as movement title
                self._mxScore.set('movementTitle', fn)
        self.load()

    def runThroughMusescore(self, fp, **keywords):
        import sys
        musescoreFile = environLocal['musescoreDirectPNGPath']
        if musescoreFile == "":
            raise SubConverterException("To create PNG files directly from MusicXML you need to download MuseScore")
        elif not os.path.exists(musescoreFile):
            raise SubConverterException("Cannot find a path to the 'mscore' file at %s -- download MuseScore" % musescoreFile)

        fpOut = fp[0:len(fp) - 3]
        fpOut += "png"
        musescoreRun = musescoreFile + " " + fp + " -o " + fpOut
        if 'dpi' in keywords:
            musescoreRun += " -r " + str(keywords['dpi'])
        if common.runningUnderIPython():
            musescoreRun += " -r 72"

        storedStrErr = sys.stderr
        if six.PY2:
            from StringIO import StringIO # @UnusedImport
        else:
            from io import StringIO # @Reimport
        fileLikeOpen = StringIO()
        sys.stderr = fileLikeOpen
        os.system(musescoreRun)
        fileLikeOpen.close()
        sys.stderr = storedStrErr

        fp = fpOut[0:len(fpOut) - 4] + "-1.png"
        return fp
    
    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        from music21.musicxml import m21ToString
        dataStr = m21ToString.fromMusic21Object(obj)
        fp = self.writeDataStream(fp, dataStr)        
        
        if subformats is not None and 'png' in subformats:
            fp = self.runThroughMusescore(fp, **keywords)
        return fp

#-------------------------------------------------------------------------------
class ConverterMidi(SubConverter):
    '''
    Simple class wrapper for parsing MIDI and sending MIDI data out.
    '''
    readBinary = True
    registerFormats = ('midi',)
    registerInputExtensions = ('mid', 'midi')
    registerOutputExtensions = ('mid', )
    
    def parseData(self, strData, number=None):
        '''
        Get MIDI data from a binary string representation.

        Calls midi.translate.midiStringToStream.
        '''
        from music21.midi import translate as midiTranslate
        self.stream = midiTranslate.midiStringToStream(strData)

    def parseFile(self, fp, number=None):
        '''
        Get MIDI data from a file path.

        Calls midi.translate.midiFilePathToStream.
        '''
        from music21.midi import translate as midiTranslate
        midiTranslate.midiFilePathToStream(fp, self.stream)

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        from music21.midi import translate as midiTranslate
        if fp is None:
            fp = self.getTemporaryFile()
        mf = midiTranslate.music21ObjectToMidiFile(obj)
        mf.open(fp, 'wb') # write binary
        mf.write()
        mf.close()
        return fp



#-------------------------------------------------------------------------------
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
        else: # just one work
            abcFormat.translate.abcToStreamScore(abcHandler, self.stream)

    def parseFile(self, fp, number=None):
        '''Get MIDI data from a file path. If more than one work is defined in the ABC data, a  :class:`~music21.stream.Opus` object will be returned; otherwise, a :class:`~music21.stream.Score` is returned.

        If `number` is provided, and this ABC file defines multiple works with a X: tag, just the specified work will be returned.
        '''
        #environLocal.printDebug(['ConverterABC.parseFile: got number', number])
        from music21 import abcFormat

        af = abcFormat.ABCFile()
        af.open(fp)
        # returns a handler instance of parse tokens
        abcHandler = af.read(number=number)
        af.close()

        # only create opus if multiple ref numbers
        # are defined; if a number is given an opus will no be created
        if abcHandler.definesReferenceNumbers():
            # this creates a Score or Opus object, depending on if a number
            # is given
            self.stream = abcFormat.translate.abcToStreamOpus(abcHandler,
                           number=number)
        # just get a single work
        else:
            abcFormat.translate.abcToStreamScore(abcHandler, self.stream)


class ConverterRomanText(SubConverter):
    '''Simple class wrapper for parsing roman text harmonic definitions.
    '''
    registerFormats = ('romantext', 'rntext')
    registerInputExtensions = ('rntxt', 'rntext', 'romantext', 'rtxt')
    

    def parseData(self, strData, number=None):
        '''
        '''
        from music21 import romanText as romanTextModule
        from music21.romanText import translate as romanTextTranslate
        rtf = romanTextModule.RTFile()
        rtHandler = rtf.readstr(strData)
        if rtHandler.definesMovements():
            # this re-defines Score as an Opus
            self.stream = romanTextTranslate.romanTextToStreamOpus(rtHandler)
        else:
            romanTextTranslate.romanTextToStreamScore(rtHandler, self.stream)

    def parseFile(self, fp, number=None):
        '''
        '''
        from music21 import romanText as romanTextModule
        from music21.romanText import translate as romanTextTranslate
        rtf = romanTextModule.RTFile()
        rtf.open(fp)
        # returns a handler instance of parse tokens
        rtHandler = rtf.read()
        rtf.close()
        romanTextTranslate.romanTextToStreamScore(rtHandler, self.stream)


class ConverterCapella(SubConverter):
    '''
    Simple class wrapper for parsing Capella .capx XML files.  See capella/fromCapellaXML.
    '''
    registerFormats = ('capella',)
    registerInputExtensions = ('capx',)
    
    def parseData(self, strData, number=None):
        '''
        parse a data stream of uncompessed capella xml

        N.B. for web parsing, it gets more complex.
        '''
        from music21.capella import fromCapellaXML
        ci = fromCapellaXML.CapellaImporter()
        ci.parseXMLText(strData)
        scoreObj = ci.systemScoreFromScore(self.mainDom.documentElement)
        partScore = ci.partScoreFromSystemScore(scoreObj)
        self.stream = partScore
        
    def parseFile(self, fp, number=None):
        '''
        Read a file
        '''
        from music21.capella import fromCapellaXML
        ci = fromCapellaXML.CapellaImporter()
        self.stream = ci.scoreFromFile(fp)


#-------------------------------------------------------------------------------
class ConverterMuseData(SubConverter):
    '''Simple class wrapper for parsing MuseData.
    '''
    registerFormats = ('musedata',)
    registerInputExtensions = ('md', 'musedata', 'zip')

    def parseData(self, strData, number=None):
        '''Get musedata from a string representation.

        '''
        from music21 import musedata as musedataModule
        from music21.musedata import translate as musedataTranslate

        if common.isStr(strData):
            strDataList = [strData]
        else:
            strDataList = strData

        mdw = musedataModule.MuseDataWork()

        for strData in strDataList:
            mdw.addString(strData)

        musedataTranslate.museDataWorkToStreamScore(mdw, self.stream)

    def parseFile(self, fp, number=None):
        '''
        '''
        from music21 import converter
        from music21 import musedata as musedataModule
        from music21.musedata import translate as musedataTranslate

        mdw = musedataModule.MuseDataWork()

        af = converter.ArchiveManager(fp)

        #environLocal.printDebug(['ConverterMuseData: parseFile', fp, af.isArchive()])
        # for dealing with one or more files
        if fp.endswith('.zip') or af.isArchive():
            #environLocal.printDebug(['ConverterMuseData: found archive', fp])
            # get data will return all data from the zip as a single string
            for partStr in af.getData(dataFormat='musedata'):
                #environLocal.printDebug(['partStr', len(partStr)])
                mdw.addString(partStr)
        else:
            if os.path.isdir(fp):
                mdd = musedataModule.MuseDataDirectory(fp)
                fpList = mdd.getPaths()
            elif not common.isListLike(fp):
                fpList = [fp]
            else:
                fpList = fp

            for fp in fpList:
                mdw.addFile(fp)

        #environLocal.printDebug(['ConverterMuseData: mdw file count', len(mdw.files)])

        musedataTranslate.museDataWorkToStreamScore(mdw, self.stream)

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
        
    def testSimpleTextShow(self):
        from music21 import stream, note
        n = note.Note()
        s = stream.Stream()
        s.append(n)
        unused_x = s.show('textLine')

        
class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
        
    def testXMLShow(self):
        from music21 import corpus
        c = corpus.parse('bwv66.6')
        c.show() # musicxml

    def testWriteLilypond(self):
        from music21 import stream, note
        n = note.Note()
        n.duration.type = 'whole'
        s = stream.Stream()
        s.append(n)
        s.show('lily.png')
        print(s.write('lily.png'))


if __name__ == '__main__':
    import music21
    #import sys
    #sys.argv.append('SimpleTextShow')
    music21.mainTest(Test)