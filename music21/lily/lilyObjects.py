# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         lily/objects.py
# Purpose:      python objects representing lilypond
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2007-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
music21 translates to Lilypond format and if Lilypond is installed on the
local computer, can automatically generate .pdf, .png, and .svg versions
of musical files using Lilypond

this replaces (April 2012) the old LilyString() conversion methods.

The Grammar for Lilypond comes from http://lilypond.org/doc/v2.14/Documentation/notation/lilypond-grammar
'''
import unittest, doctest


class LilyObjectsException(Exception):
    pass

class LyObject(object):
    supportedClasses = []  # ordered list of classes to support
    m21toLy = {}
    defaultAttributes = {}
    
    
    def __init__(self):
        #self.context = context
        self.lilyAttributes = {}
        #self.setLilyAttributes(inObject, context, **keywords)
    
    def setAttributes(self, m21Object):
        r'''
        Returns a dictionary and sets self.lilyAttributes to that dictionary, for a m21Object
        of class classLookup using the mapping of self.m21toLy[classLookup]
        
        >>> from music21 import *
        >>> class Mock(base.Music21Object): pass
        >>> m = Mock()
        >>> m.mockAttribute = 32
        >>> m.mockAttribute2 = None
        
        >>> lm = LyMock()
        
        LyMock (our test class) defines mappings for two classes:
        to LyMock.lilyAttributes:
        
        >>> print lm.supportedClasses
        ['Mock', 'Mocker']
        
        Thus we can get attributes from the Mock class (see `setAttributesFromClassObject`):
        
        >>> lilyAttributes = lm.setAttributes(m)
        >>> for x in sorted(lilyAttributes.keys()):
        ...    print "%s: %s" % (x, lilyAttributes[x])
        mock-attribute: 32
        mock-attribute-2: None
            
        >>> lilyAttributes is lm.lilyAttributes
        True
        '''
        
        foundClass = False
        for tryClass in self.supportedClasses:
            if tryClass in m21Object.classes or tryClass == '*':
                attrs = self.setAttributesFromClassObject(tryClass, m21Object)
                foundClass = True
                break
        if foundClass is False:
            raise LilyObjectsException('Could not support setting attributes from %s: supported classes: %s' % (m21Object, self.supportedClasses))
        else:
            return attrs
    
    def setAttributesFromClassObject(self, classLookup, m21Object):
        '''
        Returns a dictionary and sets self.lilyAttributes to that dictionary, for a m21Object
        of class classLookup using the mapping of self.m21toLy[classLookup]
        
        >>> from music21 import *
        >>> class Mock(base.Music21Object): pass
        >>> m = Mock()
        >>> lm = LyMock()
        
        LyMock (our test class) defines certain mappings from the m21 Mock class
        to LyMock.lilyAttributes:
        
        >>> for x in sorted(lm.m21toLy['Mock'].keys()):
        ...    print "%s: %s" % (x, lm.m21toLy['Mock'][x])
        mockAttribute: mock-attribute
        mockAttribute2: mock-attribute-2
        
        
        Some of these attributes have defaults:
        
        >>> for x in sorted(lm.defaultAttributes.keys()):
        ...    print "%s: %s" % (x, lm.defaultAttributes[x])
        mockAttribute2: 7
        
        
        >>> m.mockAttribute = "hello"
        
        
        >>> lilyAttributes = lm.setAttributesFromClassObject('Mock', m)
        >>> for x in sorted(lilyAttributes.keys()):
        ...    print "%s: %s" % (x, lilyAttributes[x])
        mock-attribute: hello
        mock-attribute-2: 7
            
        >>> lilyAttributes is lm.lilyAttributes
        True

        '''
        
        if classLookup not in self.m21toLy:
            raise LilyObjectsException('Could not support setting attributes from %s error in self.m21toLy, missing class definitions and no "*"' % (m21Object))
        classDict = self.m21toLy[classLookup]
        for m21Attribute in classDict:
            try:
                value = getattr(m21Object, m21Attribute)
            except AttributeError:
                if m21Attribute in self.defaultAttributes:
                    value = self.defaultAttributes[m21Attribute]
                else:
                    value = None
            lyAttribute = classDict[m21Attribute]
            #print m21Attribute, lyAttribute, value
            self.lilyAttributes[lyAttribute] = value
        return self.lilyAttributes
    
    def lyString(self):
        return ""

class LyMock(LyObject):
    '''
    A test object for trying various music21 to Lily conversions

    '''
    supportedClasses = ['Mock', 'Mocker']
    m21toLy = {'Mock': {'mockAttribute': 'mock-attribute',
                         'mockAttribute2': 'mock-attribute-2',
                         },
               'Mocker': {'mockerAttribute': 'mock-attribute',
                          'greg': 'mock-attribute-2',},
                }
    defaultAttributes = {'mockAttribute2': 7,
                 }

#-----------Grammar------------------#

class LyLilypondTop(LyObject):
    r'''
    corresponds to the highest level lilypond object in Appendix C:
    
    
    `lilypond: /* empty */
             | lilypond toplevel_expression
             | lilypond assignment
             | lilypond error
             | lilypond "\invalid"`
             
             
    error and \invalid are not defined by music21
    '''
    canContain = [None, "TopLevelExpression", "Assignment"]
    
    def stringOutput(self):
        return self.newlineSeparateStringOutputIfNotNone(self.contents)

class LyTopLevelExpression(LyObject):
    '''
    can contain one of:
    
      lilypondHeader
      bookBlock
      bookPartBlock
      scoreBlock
      compositeMusic
      fullMarkup
      fullMarkupList
      outputDef
    '''
    
    
    def __init__(self):
        self.lilypondHeader = None
        self.bookBlock = None
        self.bookPartBlock = None
        self.scoreBlock = None
        self.compositeMusic = None
        self.fullMarkup = None
        self.fullMarkupList = None
        self.outputDef = None
    
    def stringOutput(self):
        outputObject = self.getFirstNonNoneAttribute('lilypondHeader', 'bookBlock', 'bookPartBlock', 'scoreBlock',
                                                     'compositeMusic', 'fullMarkup', 'fullMarkupList', 'outputDef')
        if outputObject is None:
            raise Exception()
        else:
            return outputObject.stringOutput()
    
class LyAssignment(LyObject):
    pass


class LyHeader(LyTopLevelExpression):
    
    def stringOutput(self):
        return self.backslash + "header" + self.encloseCurly(self.lilypondHeaderBody.stringOutput())
    
    
class LyBookpartBlock(LyTopLevelExpression):
    pass
class LyScoreBlock(LyTopLevelExpression):
    pass
class LyCompositeMusic(LyTopLevelExpression):
    pass
class LyFullMarkup(LyTopLevelExpression):
    pass
class LyFullMarkupList(LyTopLevelExpression):
    pass
class LyOutputDef(LyTopLevelExpression):
    def __init__(self):
        self.scmToken = None
        self.scmIdentifier = None
        
    def stringOutput(self):
        outputObject = self.getFirstNonNoneAttribute('scmToken', 'scmIdentifier')
        if outputObject is None:
            raise Exception()
        else:
            return outputObject.stringOutput()

class LyEmbeddedScm(LyObject):
    '''
    represents Scheme embedded in Lilypond code.  
    
    Can be either a SCM_TOKEN (Scheme Token) or SCM_IDENTIFIER String stored in self.content
    
    Note that if any LyEmbeddedScm is found in an output then the output SHOULD be marked as unsafe.
    '''
    
    def __init__(self):
        self.content = None
    
    def stringOutput(self):
        return self.content

class LyLilypondHeaderBody(LyObject):
    
    def __init__(self):
        self.headerBody = None
        self.assignment = None

    def stringOutput(self):        
        return self.newlineSeparateStringOutputIfNotNone([self.headerBody, self.assignment])

class LyAssignmentId(self):
    
    def __init__(self):
        self.content = None
        self.isLyricString = False
    
    def stringOutput(self):
        return self.content

class LyAssignment(self):
    '''
    one of three forms of assignment:
    
      assignment_id '=' identifier_init
      assignment_id property_path '=' identifier_init  
      embedded_scm
    
    if self.embeddedScm is not None, uses type 3
    if self.propertyPath is not None, uses type 2
    else uses type 1 or raises an exception.
    '''
    def __init__(self):
        self.assignmentId = None
        self.identifierInit = None
        self.propertyPath = None
        self.embeddedScm = None
        
    def stringOutput(self):
        if self.embeddedScm is not None:
            return self.embeddedScm.stringOutput()
        elif self.propertyPath is not None:
            if self.assignmentId is None or self.identifierInit is None:
                raise Exception()
            else:
                return ''.join(self.assignmentId.stringOutput(), ' ' ,
                               self.propertyPath.stringOutput(), "=", self.identifierInit.stringOutput())
        else:
            if self.assignmentId is None or self.identifierInit is None:
                raise Exception()
            else:
                return ' '.join(self.assignmentId.stringOutput(), "=", self.identifierInit.stringOutput())

def LyIndentifierInit(LyObject):

    def __init__(self):
        self.scoreBlock = None
        self.bookBlock = None
        self.bookPartBlock = None
        self.outputDef = None
        self.contextDefSpecBlock = None
        self.music = None
        self.postEvent = None
        self.numberExpression = None
        self.string = None
        self.embeddedScm = None
        self.fullMarkup = None
        self.fullMarkupList = None
        self.digit = None
        self.contextModification = None
    
    def stringOutput(self):
        outputObject = self.getFirstNonNoneAttribute('scoreBlock', 'bookBlock', 'bookPartBlock', 'outputDef',
                                                     'contextDefSpecBlock', 'music', 'postEvent', 'numberExpression',
                                                     'string', 'embeddedScm', 'fullMarkup', 'fullMarkupList',
                                                     'digit', 'contextModification')
        if outputObject is None:
            raise Exception()
        elif outputObject == self.digit:  #better test for digit
            return str(outputObject)
        else:
            return outputObject.stringOutput()

class LyContextDefSpecBlock(LyObject):
    
    def __init__(self):
        self.contextDefSpecBody = None
    
    def stringOutput(self):
        return self.backslash + "context " + self.encloseCurly(self.contextDefSpecBody.stringOutput())

class LyContextDefSpecBody(LyObject):
    r'''
    None or one of four forms:
    
       CONTEXT_DEF_IDENTIFIER
       context_def_spec_body "\grobdescriptions" embedded_scm 
       context_def_spec_body context_mod
       context_def_spec_body context_modification
    '''
    
    
    def __init__(self):
        self.contextDefIdentifier = None
        self.contextDefSpecBody = None
        self.embeddedScm = None
        self.contextMod = None
        self.contextModification = None
        
    def stringOutput(self):
        if self.contextDefIdentifier is not None:
            return self.contextDefIdentifier
        elif self.embeddedScm is not None:
            out = ""
            if self.contextDefSpecBody is not None:
                out = self.contextDefSpecBody.stringOutput() + " " + self.backslash + "grobdescriptions" + " "
            out += self.embeddedScm.stringOutput()
            return out
        elif self.contextMod is not None:
            if self.contextDefSpecBody is not None:
                return self.contextDefSpecBody.stringOutput() + " " + self.contextMod.stringOutput()
            else:
                return self.contextMod.stringOutput()
        elif self.contextModification is not None:
            if self.contextDefSpecBody is not None:
                return self.contextDefSpecBody.stringOutput() + " " + self.contextModification.stringOutput()
            else:
                return self.contextModification.stringOutput()            
        else:
            return None

class LyBookBlock(LyObject):
    
    def __init__(self):
        self.bookBody = None
        
    def stringOutput(self):
        return self.backslash + "book" + " " + self.encloseCurly(self.bookBody.stringOutput())

class LyBookBody(LyObject):
    r'''
    Contains None, bookIdentifier (string?) or one or more of the following:
    
       paperBlock
       bookPartBlock
       scoreBlock
       compositeMusic
       fullMarkup
       fullMarkupList
       lilypondHeader
       error
    
    '''
    
    
    def __init__(self):
        self.contents = []
        self.bookIdentifier = None
        
    def stringOutput(self):
        if self.bookIdentifier is not None:
            return self.bookIdentifier
        elif len(self.contents) == 0:
            return None
        else:
            return self.newlineSeparateStringOutputIfNotNone(self.contents)

class LyBookpartBlock(LyObject):
    
    def __init__(self):
        self.bookpartBody = None
    
    def stringOutput(self):
        if self.bookpartBody is None:
            self.backslash + "bookpart " + self.encloseCurly(None)
        else:
            return self.backslash + "bookpart " + self.encloseCurly(self.bookpartBody.stringOutput())

class LyBookpartBody(LyObject):
    r'''
    Contains None, bookIdentifier (string?) or one or more of the following:
    
       paperBlock
       scoreBlock
       compositeMusic
       fullMarkup
       fullMarkupList
       lilypondHeader
       error    
    '''
    
    
    def __init__(self):
        self.contents = []
        self.bookIdentifier = None
        
    def stringOutput(self):
        if self.bookIdentifier is not None:
            return self.bookIdentifier
        elif len(self.contents) == 0:
            return None
        else:
            return self.newlineSeparateStringOutputIfNotNone(self.contents)

class LyScoreBlock(self):

    def __init__(self):
        self.scoreBody = None
    
    def stringOutput(self):
        if self.scoreBody is None:
            raise Exception()
        else:
            return self.backslash + "score " + self.encloseCurly(self.scoreBody.stringOutput())
    
class LyScoreBody(self):
    
    def __init__(self):
        self.music = None
        self.scoreIdentifier = None
        self.scoreBody = None
        self.lilypondHeader = None
        self.outputDef = None
        self.error = None
        
    def stringOutput(self):
        if self.music is not None:
            return self.music.stringOutput()
        elif self.scoreIdentifier is not None:
            return self.scoreIdentifier
        elif self.scoreBody is None:
            raise Exception("scoreBody cannot be None if music and scoreIdentifier are None")
        elif self.lilypondHeader is not None:
            return self.scoreBody.stringOutput() + " " + self.lilypondHeader.stringOutput()
        elif self.outputDef is not None:
            return self.scoreBody.stringOutput() + " " + self.outputDef.stringOutput()
        elif self.error is not None:
            return self.scoreBody.stringOutput() + " " + self.error.stringOutput()
        else:
            raise Exception("one of music, scoreIdentifier, lilypondHeader, outputDef, or error must not be None")
        
class LyPaperBlock(LyObject):
    
    def __init__(self):
        self.outputDef = None
        
    def stringOutput(self):
        if self.outputDef is None: # legal??
            return None
        else:
            return self.outputDef.stringOutput()

class LyOutputDef(LyObject):
    '''
    ugly grammar since it doesnt close curly bracket...
    '''
    
    def __init__(self):
        self.outputDefBody = None
    
    def stringOutput(self):
        if self.outputDefBody is None:
            raise Exception("Need outputDefBody to be set")
        else:
            return self.outputDefBody.stringOutput() + "}"

class LyOutputDefHead(LyObject):
    r'''
    defType can be paper, midi, or layout.

    >>> lyODH = LyOutputDefHead()
    >>> lyODH.defType = 'midi'
    >>> print lyODH.stringOutput()
    \midi

    According to Appendix C, is the same as LyOutputDefHeadWithModeSwitch
    '''
    def __init__(self):
        self.defType = None
        
    def stringOutput(self):
        if self.defType not in ['paper', 'midi', 'layout']:
            raise Exception("self.defType must be one of 'paper', 'midi', or 'layout'")
        else:
            return self.backslash + self.defType

class LyOutputDefBody(LyObject):
    r'''
    
    output_def_body: output_def_head_with_mode_switch '{'
                    | output_def_head_with_mode_switch 
                         '{' 
                         OUTPUT_DEF_IDENTIFIER 
                    | output_def_body assignment
                    | output_def_body context_def_spec_block
                    | output_def_body error
    '''
    
    def __init__(self):
        self.outputDefHead = None
        self.outputDefIdentifier = None
        self.outputDefBody = None
        self.assignment = None
        self.contextDefSpecBlock = None
        self.error = None
    
    def stringOutput(self):
        if self.outputDefHead is not None:
            out = self.outputDefHead + " { "
            if self.outputDefIdentifier is not None:
                return out + self.outputDefIdentifier
            else:
                return out
        elif self.outputDefBody is not None:
            raise Exception("Need embedded outputDefBody if outputDefIdentifier or outputDefHead are not defined")
        elif self.assignment is not None:
            return self.outputDefBody.stringOutput() + " " + self.assignment.stringOutput()
        elif self.contextDefSpecBlock is not None:
            return self.outputDefBody.stringOutput() + " " + self.contextDefSpecBlock.stringOutput()
        elif self.error is not None:
            return self.outputDefBody.stringOutput() + " " + self.error.stringOutput()
        else:
            raise Exception("Need to define at least one of assignment, contextDefSpecBlock, or error if outputDefHead is None")

class LyTempoEvent(LyObject):
    r'''
    tempo_event: "\tempo" steno_duration '=' tempo_range
               | "\tempo" scalar steno_duration '=' tempo_range
               | "\tempo" scalar
    '''
    
    def __init__(self):
        self.tempoRange = None
        self.stenoDuration = None
        self.scalar = None
        
    def stringOutput(self):
        base = self.backslash + "tempo"
        if self.tempoRange is not None:
            if self.stenoDuration is None:
                raise Exception("If tempoRange is defined then need a stenoDuration")
            elif self.scalar is not None:
                return " ".join(base, self.scalar.stringOutput(), self.stenoDuration.stringOutput(), "=", self.tempoRange.stringOutput())
            else:
                return " ".join(base, self.stenoDuration.stringOutput(), "=", self.tempoRange.stringOutput())
        elif self.scalar is None:
            raise Exception("If tempoRange is not defined then need scalar")
            return base + " " + self.scalar.stringOutput()
        
class LyMusicList(LyObject):
    '''
    can take any number of LyMusic, LyEmbeddedScm, or LyError objects
    '''
    
    def __init__(self):
        self.contents = []

    def stringOutput(self):
        return self.newlineSeparateStringOutputIfNotNone(self.contents)

class LyMusic(LyObject):
    
    def __init__(self):
        self.simpleMusic = None
        self.compositeMusic = None
        
    def stringOutput(self):
        if self.simpleMusic is not None:
            return self.simpleMusic.stringOutput()
        elif self.compositeMusic is not None:
            return self.compositeMusic.stringOutput()
        else:
            raise Exception("Need to define one of simpleMusic or compositeMusic")

class LyAlternativeMusic(LyObject):
    
    def __init__(self):
        self.musicList = None
        
    def stringOutput(self):
        if self.musicList is None:
            return None
        else:
            return self.backslash + "alternative" + self.encloseCurly(self.musicList.stringOutput())
        
class LyRepeatedMusic(LyObject):
    
    def __init__(self):
        self.simpleString = None
        self.unsignedNumber = None
        self.music = None
        self.alternativeMusic = None
        
    def stringOutput(self):
        out = self.backslash + "repeat " + self.simpleString.stringOutput() + self.unsignedNumber.stringOutput() + self.music.stringOutput()
        if self.alternativeMusic is None:
            return out
        else:
            return out + ' ' + self.alternativeMusic.stringOutput()
        
class LySequentialMusic(LyObject):
    r'''
    represents sequential music.
    
    Can be explicitly tagged with "\sequential" if displayTag is True
    '''
    
    def __init__(self):
        self.displayTag = False
        self.musicList = None
    
    def stringOutput(self):
        if self.musicList is not None:
            musicListSO = self.musicList.stringOutput()
        else:
            musicListSO = None
        tag = ""
        if self.displayTag is True:
            tag = self.backslash + "sequential "
        return tag + self.encloseCurly(musicListSO)

class LySimultaneousMusic(LyObject):
    r'''
    represents simultaneous music.
    
    Can be explicitly tagged with "\simultaneous" if displayTag is True
    otherwise encloses in double angle brackets
    '''
    
    def __init__(self):
        self.displayTag = False
        self.musicList = None
    
    def stringOutput(self):
        if self.musicList is not None:
            musicListSO = self.musicList.stringOutput()
        else:
            musicListSO = None
        tag = ""
        if self.displayTag is True:
            return self.backslash + "simultaneous " + self.encloseCurly(musicListSO)
        else:
            return "<< " + musicListSO + " >>"

class LySimpleMusic(LyObject):
    
    def __init__(self):
        self.eventChord = None
        self.musicIdentifier = None
        self.musicPropertyDef = None
        self.contextChange = None
        
    def stringOutput(self):
        outputObject = self.getFirstNonNoneAttribute('eventChord', 'musicIdentifier', 'musicPropertyDef', 'contextChange')
        if outputObject is None:
            raise Exception()
        else:
            return outputObject.stringOutput()

class LyContextModification(LyObject):
    '''
    represents both context_modification and optional_context_mod
    
    but not context_mod!!!!!
    '''
    def __init__(self):
        self.contextModList = None
        self.contextModIdentifier = None # String?
        self.displayWith = True # optional... but not supported without so far...
        
    def stringOutput(self):
        if self.contextModList is not None:
            return self.backslash + "with " + self.encloseCurly(self.contextModList.stringOutput())
        elif self.contextModIdentifier is not None:
            return self.backslash + 'with ' + self.contextModIdentifier
        else:
            return ""

class LyContextModList(LyObject):
    '''
    contains zero or more LyContextMod objects and an optional contextModIdentifier
    '''
    def __init__(self):
        self.contents = []
        self.contextModIdentifier = None # STRING
    
    def stringOutput(self):
        output = self.newlineSeparateStringOutputIfNotNone(self.contents)
        if self.contextModIdentifier is not None:
            return output + ' ' + self.contextModIdentifier
        else:
            return output

class LyCompositeMusic(LyObject):
    '''
    one of LyPrefixCompositeMusic or LyGroupedMusicList stored in self.content
    '''
    
    def __init__(self):
        self.content = None
    
    def stringOutput(self):
        return self.content.stringOutput()
    
class LyGroupedMusic(LyObject):
    '''
    one of LySimultaneousMusic or LySequentialMusic stored in self.content
    '''
    
    def __init__(self):
        self.content = None
    
    def stringOutput(self):
        return self.content.stringOutput()


class LySchemeFunction(LyObject):
    '''
    Unsupported for now, represents all of:
    
function_scm_argument: embedded_scm
  116                      | simple_string

  117 function_arglist_music_last: EXPECT_MUSIC function_arglist music

  118 function_arglist_nonmusic_last: EXPECT_MARKUP 
                                        function_arglist 
                                        full_markup 
  119                               | EXPECT_MARKUP 
                                        function_arglist 
                                        simple_string 
  120                               | EXPECT_SCM 
                                        function_arglist 
                                        function_scm_argument 

  121 function_arglist_nonmusic: EXPECT_NO_MORE_ARGS
  122                          | EXPECT_MARKUP 
                                   function_arglist_nonmusic 
                                   full_markup 
  123                          | EXPECT_MARKUP 
                                   function_arglist_nonmusic 
                                   simple_string 
  124                          | EXPECT_SCM 
                                   function_arglist_nonmusic 
                                   function_scm_argument 

  125 function_arglist: EXPECT_NO_MORE_ARGS
  126                 | function_arglist_music_last
  127                 | function_arglist_nonmusic_last

  128 generic_prefix_music_scm: MUSIC_FUNCTION function_arglist
'''
    pass
  
    


##-------------older-------------



class LyPitch(LyObject):
    pass

class LyNote(LyObject):
    pass

class LyDuration(LyObject):
    pass

class LyLyricGroup(LyObject):
    pass

##---------Layout----------##

class LyPaper(LyObject):
    m21toLy = {'PageLayout': {'pageWidth': 'paper-width',
                               'pageHeight': 'paper-height',
                               'topMargin': 'top-margin',
                               'bottomMargin': 'bottom-margin',
                               'leftMargin': 'left-margin',
                               'rightMargin': 'right-margin',
                               },
                }
    
    defaultAttributes = {'pageWidth': None,
                 'pageHeight': None,
                 'topMargin': None,
                 'bottomMargin': None,
                 'leftMargin': None,
                 'rightMargin': None,
                 }
    

class LyLayout(LyObject):
    pass


##--------Tools-----------##
class LyCodePrinter(object):
    pass

    def __init__(self):
        currentIndent = 0
        bracketNesting = 0
        angleBracketNest = 0

##-------Tests------------##

class Test(unittest.TestCase):
    pass

##-------Main-------------##
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


