# ------------------------------------------------------------------------------
# Name:         lily/objects.py
# Purpose:      Python objects representing LilyPond
#
# Authors:      Michael Scott Asato Cuthbert
#               Jeremy Teitelbaum (LilyPond 2.24 adaptations)
#
# Copyright:    Copyright © 2007-2025 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
music21 translates to LilyPond format and if LilyPond is installed on the
local computer, can automatically generate .pdf, .png, and .svg versions
of musical files using LilyPond.

The class hierarchy mirrors the grammar in
https://lilypond.org/doc/v2.14/Documentation/notation/lilypond-grammar
(the last LilyPond to publish one is v2.19; since then it is `lily/parser.yy`).

Output is written for LilyPond 2.24 and checked against it.  Aim to support
3-4 years of LilyPond.
'''
from __future__ import annotations

import typing as t
import unittest
import weakref

from music21 import common
from music21 import exceptions21
from music21 import prebase

if t.TYPE_CHECKING:
    from music21 import base


class LilyObjectsException(exceptions21.Music21Exception):
    pass


class LyObject(prebase.ProtoM21Object):
    r'''
    LyObject is the base class of all other Lily Objects

    >>> lyo = lily.lilyObjects.LyObject()
    >>> lyo.stringOutput()
    ''

    * Changed in v11: `stringOutput()` always returns a `str`, never None.
    '''
    supportedClasses: list[str] = []  # ordered list of classes to support
    m21toLy: dict[str, dict[str, str]] = {}
    defaultAttributes: dict[str, t.Any] = {}
    backslash = '\\'

    def __init__(self) -> None:
        # self.context = context
        self.lilyAttributes: dict[str, t.Any] = {}
        self._parent: weakref.ReferenceType[LyObject]|None = None
        self.thisIndent = 0
        self.markupTop: LyObject|str|None = None
        self.lyricMarkupOrIdentifier: LyObject|str|None = None
        self.markupListOrIdentifier: LyObject|str|None = None
        self.markupTopOrIdentifier: LyObject|str|None = None
        # self.setLilyAttributes(inObject, context, **keywords)

    def __setattr__(self, name: str, value: t.Any) -> None:
        if isinstance(value, LyObject):
            value.setParent(self)
        elif common.isIterable(value):
            for v in value:
                if isinstance(v, LyObject):
                    if v._parent is None:
                        v.setParent(self)

        object.__setattr__(self, name, value)

    def getParent(self) -> LyObject|None:
        if self._parent is None:
            return None
        return self._parent()

    def setParent(self, parentObject: LyObject) -> None:
        self._parent = weakref.ref(parentObject)

    def ancestorList(self) -> list[LyObject]:
        r'''
        returns a list of all unwrapped parent objects for the current object
        '''
        ancestors = []
        currentParent = self.getParent()
        while currentParent is not None:
            ancestors.append(currentParent)
            currentParent = currentParent.getParent()
        return ancestors

    def getAncestorByClass(
        self,
        classObj: type[LyObject],
        getAncestorNumber: int = 1,
    ) -> LyObject|None:
        currentIter = 1
        for a in self.ancestorList():
            if isinstance(a, classObj):
                if currentIter == getAncestorNumber:
                    return a
                else:
                    currentIter += 1
        return None

    @property
    def newlineIndent(self) -> str:
        # totalIndents = self.thisIndent
        ancestors = self.ancestorList()
        # for ancestor in ancestors:
        #    totalIndents += ancestor.thisIndent
        totalIndents = len(ancestors)
        indentSpaces = ' ' * totalIndents
        return '\n' + indentSpaces

    def setAttributes(self, m21Object: base.Music21Object) -> dict[str, t.Any]:
        r'''
        Returns a dictionary and sets self.lilyAttributes to that dictionary, for a m21Object
        of class classLookup using the mapping of self.m21toLy[classLookup]

        >>> class Mock(base.Music21Object):
        ...     pass
        >>> m = Mock()
        >>> m.mockAttribute = 32
        >>> m.mockAttribute2 = None

        >>> lm = lily.lilyObjects.LyMock()

        LyMock (our test class) defines mappings for two classes:
        to LyMock.lilyAttributes:

        >>> print(lm.supportedClasses)
        ['Mock', 'Mocker']

        Thus, we can get attributes from the Mock class (see `setAttributesFromClassObject`):

        >>> lilyAttributes = lm.setAttributes(m)
        >>> for x in sorted(lilyAttributes.keys()):
        ...    print(f'{x}: {lilyAttributes[x]}')
        mock-attribute: 32
        mock-attribute-2: None

        >>> lilyAttributes is lm.lilyAttributes
        True
        '''
        for tryClass in self.supportedClasses:
            if tryClass in m21Object.classes or tryClass == '*':
                return self.setAttributesFromClassObject(tryClass, m21Object)

        raise LilyObjectsException(  # pragma: no cover
            'Could not support setting attributes from '
            f'{m21Object}: supported classes: {self.supportedClasses}')

    def setAttributesFromClassObject(
        self,
        classLookup: str,
        m21Object: base.Music21Object,
    ) -> dict[str, t.Any]:
        r'''
        Returns a dictionary and sets self.lilyAttributes to that dictionary, for a m21Object
        of class classLookup using the mapping of self.m21toLy[classLookup]

        >>> class Mock(base.Music21Object): pass
        >>> m = Mock()
        >>> lm = lily.lilyObjects.LyMock()

        LyMock (our test class) defines certain mappings from the m21 Mock class
        to LyMock.lilyAttributes:

        >>> for x in sorted(lm.m21toLy['Mock'].keys()):
        ...    print(f"{x}: {lm.m21toLy['Mock'][x]}")
        mockAttribute: mock-attribute
        mockAttribute2: mock-attribute-2

        Some of these attributes have defaults:

        >>> for x in sorted(lm.defaultAttributes.keys()):
        ...    print(f'{x}: {lm.defaultAttributes[x]}')
        mockAttribute2: 7

        >>> m.mockAttribute = 'hello'
        >>> lilyAttributes = lm.setAttributesFromClassObject('Mock', m)
        >>> for x in sorted(lilyAttributes.keys()):
        ...    print(f'{x}: {lilyAttributes[x]}')
        mock-attribute: hello
        mock-attribute-2: 7

        >>> lilyAttributes is lm.lilyAttributes
        True
        '''
        if classLookup not in self.m21toLy:  # pragma: no cover
            raise LilyObjectsException(
                'Could not support setting attributes from '
                f'{m21Object} error in self.m21toLy,'
                ' missing class definitions and no "*"'
            )
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
            # print(m21Attribute, lyAttribute, value)
            self.lilyAttributes[lyAttribute] = value
        return self.lilyAttributes

    def _reprInternal(self) -> str:
        msg = str(self)
        msg = msg.replace('\n', '  ')
        if len(msg) >= 13:
            msg = msg[:10] + '...'
        return msg

    def __str__(self) -> str:
        so = self.stringOutput()
        so = so.replace('\n\n', '\n')
        return so

    def stringOutput(self) -> str:
        return ''

    def getFirstNonNoneAttribute(self, attributeList: t.Iterable[str]) -> t.Any:
        for a in attributeList:
            if getattr(self, a) is not None:
                return getattr(self, a)
        return None

    def newlineSeparateStringOutputIfNotNone(
        self,
        contents: t.Iterable[LyObject|str|None],
    ) -> str:
        c = ''
        for n in contents:
            if n is None:
                continue
            c += str(n) + self.newlineIndent

        return c

    def encloseCurly(self, arg: t.Sequence[str]|LyObject|str|None) -> str:
        if isinstance(arg, list):
            strArg = self.newlineIndent.join(arg)
            return ''.join([' { ', self.newlineIndent, strArg, self.newlineIndent,
                            ' } ', self.newlineIndent])
        elif arg is not None:
            return ''.join([' { ', self.newlineIndent, str(arg), self.newlineIndent,
                            ' } ', self.newlineIndent])
        else:
            return ' { } '

    def quoteString(self, stringIn: str) -> str:
        r'''
        returns a string that is quoted with
        internal quotation marks backslash'd out
        and an extra space at the end.

        >>> m = lily.lilyObjects.LyObject()
        >>> print(m.quoteString(r'Hello "there"!'))
        "Hello \"there\"!"
        '''
        stringNew = stringIn.replace('"', r'\"')
        return '"' + stringNew + '" '

    # noinspection GrazieInspection
    def comment(self, stringIn: str) -> str:
        r'''
        returns a comment that is %{ stringIn.strip() %}

        (Don't put %} etc. in comments -- it will break the system.)
        '''
        return ' %{ ' + stringIn.strip() + ' %} '


class LyMock(LyObject):
    r'''
    A test object for trying various music21 to Lily conversions
    '''
    supportedClasses = ['Mock', 'Mocker']
    m21toLy = {'Mock': {'mockAttribute': 'mock-attribute',
                        'mockAttribute2': 'mock-attribute-2',
                        },
               'Mocker': {'mockerAttribute': 'mock-attribute',
                          'greg': 'mock-attribute-2', },
               }
    defaultAttributes = {'mockAttribute2': 7,
                         }

# ----------Grammar------------------#


class LyLilypondTop(LyObject):
    r'''
    corresponds to the highest level lilypond object in Appendix C:

    ::

      `lilypond: /* empty */
             | lilypond toplevel_expression
             | lilypond assignment
             | lilypond error
             | lilypond "\invalid"`

    error and \invalid are not defined by music21
    '''
    canContain = [None, 'TopLevelExpression', 'Assignment']

    def __init__(self, contents: list[LyObject|str]|None = None) -> None:
        if contents is None:
            contents = []
        super().__init__()
        self.contents = contents

    def stringOutput(self) -> str:
        return self.newlineSeparateStringOutputIfNotNone(self.contents)


class LyTopLevelExpression(LyObject):
    r'''
    can contain one of:

      lilypondHeader
      bookBlock
      bookPartBlock
      scoreBlock
      compositeMusic
      fullMarkup
      fullMarkupList
      outputDef

    >>> bookBlock = lily.lilyObjects.LyBookBlock()
    >>> lyTopLevel = lily.lilyObjects.LyTopLevelExpression(bookBlock=bookBlock)
    >>> str(lyTopLevel)
    '\\book  { } '
    '''
    def __init__(self,
                 lilypondHeader: LyLilypondHeader|None = None,
                 bookBlock: LyBookBlock|None = None,
                 bookPartBlock: LyBookpartBlock|None = None,
                 scoreBlock: LyScoreBlock|None = None,
                 compositeMusic: LyCompositeMusic|None = None,
                 fullMarkup: LyFullMarkup|None = None,
                 fullMarkupList: LyFullMarkupList|None = None,
                 outputDef: LyOutputDef|None = None,
                 ) -> None:
        super().__init__()
        self.lilypondHeader = lilypondHeader
        self.bookBlock = bookBlock
        self.bookPartBlock = bookPartBlock
        self.scoreBlock = scoreBlock
        self.compositeMusic = compositeMusic
        self.fullMarkup = fullMarkup
        self.fullMarkupList = fullMarkupList
        self.outputDef = outputDef

    def stringOutput(self) -> str:
        outputObject = self.getFirstNonNoneAttribute([
            'lilypondHeader', 'bookBlock', 'bookPartBlock', 'scoreBlock',
            'compositeMusic', 'fullMarkup', 'fullMarkupList', 'outputDef'])
        if outputObject is None:
            raise LilyObjectsException('Need an outputObject to report')  # pragma: no cover
        return outputObject.stringOutput()


class LyLilypondHeader(LyObject):
    r'''
    A header object with a LyHeaderBody

    >>> lyh = lily.lilyObjects.LyLilypondHeader()
    >>> str(lyh)
    '\\header { } '
    '''
    def __init__(self, lilypondHeaderBody: LyLilypondHeaderBody|None = None) -> None:
        super().__init__()
        self.lilypondHeaderBody = lilypondHeaderBody

    def stringOutput(self) -> str:
        return self.backslash + 'header' + self.encloseCurly(self.lilypondHeaderBody)


class LyEmbeddedScm(LyObject):
    r'''
    represents Scheme embedded in LilyPond code.

    Can be either an SCM_TOKEN (Scheme Token) or SCM_IDENTIFIER String stored in self.content

    Note that if any LyEmbeddedScm is found in an output then the output SHOULD be marked as unsafe.
    But a lot of standard lilypond functions are actually embedded scheme.
    For instance, \clef, which
    as https://lilypond.org/doc/v2.12/input/lsr/lilypond-snippets/Pitches#Tweaking-clef-properties
    shows is a macro to run a lot of \set commands.

    >>> lyScheme = lily.lilyObjects.LyEmbeddedScm('##t')
    >>> str(lyScheme)
    '##t'
    '''
    def __init__(self, content: str = '') -> None:
        super().__init__()
        self.content = content

    def stringOutput(self) -> str:
        return self.content


class LyLilypondHeaderBody(LyObject):
    def __init__(self, assignments: list[LyAssignment]|None = None) -> None:
        if assignments is None:
            assignments = []
        super().__init__()
        self.assignments = assignments

    def stringOutput(self) -> str:
        return self.newlineSeparateStringOutputIfNotNone(self.assignments)


class LyAssignmentId(LyObject):
    '''
    >>> lyAssignmentId = lily.lilyObjects.LyAssignmentId('title', isLyricString=False)
    >>> str(lyAssignmentId)
    'title'
    '''
    def __init__(self, content: str = '', isLyricString: bool = False) -> None:
        super().__init__()
        self.content = content
        self.isLyricString = isLyricString

    def stringOutput(self) -> str:
        return self.content


class LyAssignment(LyObject):
    r'''
    one of three forms of assignment:

      assignment_id '=' identifier_init
      assignment_id property_path '=' identifier_init
      embedded_scm

    if self.embeddedScm is not None, uses type 3
    if self.propertyPath is not None, uses type 2
    else uses type 1 or raises an exception.

    >>> lyIdInit = lily.lilyObjects.LyIdentifierInit(string='hi')
    >>> lya = lily.lilyObjects.LyAssignment(assignmentId='title', identifierInit=lyIdInit)
    >>> print(lya)
    title = "hi"

    Note that you could also pass assignmentId a LyAssignmentId object,
    but that's overkill for a lot of things.
    '''
    def __init__(self,
                 assignmentId: LyAssignmentId|str|None = None,
                 identifierInit: LyIdentifierInit|None = None,
                 propertyPath: LyPropertyPath|None = None,
                 embeddedScm: LyEmbeddedScm|None = None,
                 ) -> None:
        super().__init__()
        self.assignmentId = assignmentId
        self.identifierInit = identifierInit
        self.propertyPath = propertyPath
        self.embeddedScm = embeddedScm

    def stringOutput(self) -> str:
        if self.embeddedScm is not None:
            return self.embeddedScm.stringOutput()
        elif self.propertyPath is not None:
            if self.assignmentId is None or self.identifierInit is None:  # pragma: no cover
                raise LilyObjectsException('need an assignmentId or identifierInit')

            return ''.join([str(self.assignmentId), ' ',
                            self.propertyPath.stringOutput(), ' = ',
                            self.identifierInit.stringOutput(), ' '])
        else:
            if self.assignmentId is None or self.identifierInit is None:  # pragma: no cover
                raise LilyObjectsException('need an assignmentId or identifierInit')
            return ' '.join([str(self.assignmentId), '=',
                             self.identifierInit.stringOutput(), ' '])


class LyIdentifierInit(LyObject):
    r'''
    >>> lyIdInit = lily.lilyObjects.LyIdentifierInit(string='hello')
    >>> print(lyIdInit)
    "hello"
    '''
    def __init__(self,
                 scoreBlock: LyScoreBlock|None = None,
                 bookBlock: LyBookBlock|None = None,
                 bookPartBlock: LyBookpartBlock|None = None,
                 outputDef: LyOutputDef|None = None,
                 contextDefSpecBlock: LyContextDefSpecBlock|None = None,
                 music: LyMusic|None = None,
                 postEvent: LyPostEvent|None = None,
                 numberExpression: LyNumberExpression|None = None,
                 string: str|None = None,
                 embeddedScm: LyEmbeddedScm|None = None,
                 fullMarkup: LyFullMarkup|None = None,
                 fullMarkupList: LyFullMarkupList|None = None,
                 digit: int|None = None,
                 contextModification: LyContextModification|None = None,
                 ) -> None:
        super().__init__()
        self.scoreBlock = scoreBlock
        self.bookBlock = bookBlock
        self.bookPartBlock = bookPartBlock
        self.outputDef = outputDef
        self.contextDefSpecBlock = contextDefSpecBlock
        self.music = music
        self.postEvent = postEvent
        self.numberExpression = numberExpression
        self.string = string
        self.embeddedScm = embeddedScm
        self.fullMarkup = fullMarkup
        self.fullMarkupList = fullMarkupList
        self.digit = digit
        self.contextModification = contextModification

    def stringOutput(self) -> str:
        outputObject = self.getFirstNonNoneAttribute([
            'scoreBlock', 'bookBlock', 'bookPartBlock', 'outputDef',
            'contextDefSpecBlock', 'music', 'postEvent', 'numberExpression',
            'string', 'embeddedScm', 'fullMarkup', 'fullMarkupList',
            'digit', 'contextModification'])
        if outputObject is None:
            raise LilyObjectsException('need an outputObject')  # pragma: no cover

        if outputObject is self.digit:  # better test for digit
            return str(outputObject)
        elif self.string is not None and outputObject is self.string:
            return self.quoteString(self.string)
        else:
            return outputObject.stringOutput()


class LyContextDefSpecBlock(LyObject):
    def __init__(self, contextDefSpecBody: LyContextDefSpecBody|None = None) -> None:
        super().__init__()
        self.contextDefSpecBody = contextDefSpecBody

    def stringOutput(self) -> str:
        return self.backslash + 'context ' + self.encloseCurly(self.contextDefSpecBody)


class LyContextDefSpecBody(LyObject):
    r'''
    None or one of four forms:

       CONTEXT_DEF_IDENTIFIER
       context_def_spec_body "\grobdescriptions" embedded_scm
       context_def_spec_body context_mod
       context_def_spec_body context_modification

    >>> lyContextBody = lily.lilyObjects.LyContextDefSpecBody(contextDefIdentifier='cdi')
    >>> lyContextBody.stringOutput()
    'cdi'

    >>> embedScm = lily.lilyObjects.LyEmbeddedScm('#t')
    >>> lyContextBody = lily.lilyObjects.LyContextDefSpecBody(
    ...                 contextDefSpecBody='body', embeddedScm=embedScm)
    >>> lyContextBody.stringOutput()
    'body \\grobdescriptions #t'
    '''
    def __init__(self,
                 contextDefIdentifier: str|None = None,
                 contextDefSpecBody: str|None = None,
                 embeddedScm: LyEmbeddedScm|None = None,
                 contextMod: LyContextMod|None = None,
                 contextModification: LyContextModification|None = None,
                 ) -> None:
        super().__init__()
        self.contextDefIdentifier = contextDefIdentifier
        self.contextDefSpecBody = contextDefSpecBody
        self.embeddedScm = embeddedScm
        self.contextMod = contextMod
        self.contextModification = contextModification

    def stringOutput(self) -> str:
        if self.contextDefIdentifier is not None:
            return self.contextDefIdentifier
        elif self.embeddedScm is not None:
            out = ''
            if self.contextDefSpecBody is not None:
                out = ''.join([self.contextDefSpecBody, ' ', self.backslash,
                               'grobdescriptions', ' '])
            out += self.embeddedScm.stringOutput()
            return out
        elif self.contextMod is not None:
            if self.contextDefSpecBody is not None:
                return self.contextDefSpecBody + ' ' + self.contextMod.stringOutput()
            else:
                return self.contextMod.stringOutput()
        elif self.contextModification is not None:
            if self.contextDefSpecBody is not None:
                return ' '.join([self.contextDefSpecBody,
                                 self.contextModification.stringOutput()])
            else:
                return self.contextModification.stringOutput()
        else:
            return ''


class LyBookBlock(LyObject):
    def __init__(self, bookBody: LyBookBody|None = None) -> None:
        super().__init__()
        self.bookBody = bookBody

    def stringOutput(self) -> str:
        return self.backslash + 'book' + ' ' + self.encloseCurly(self.bookBody)


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

    >>> lyBookBody = lily.lilyObjects.LyBookBody(bookIdentifier='bookId')
    >>> lyBookBody.stringOutput()
    'bookId'

    >>> lyBookBody = lily.lilyObjects.LyBookBody()
    >>> lyBookBody.stringOutput()
    ''

    >>> lyBookBody = lily.lilyObjects.LyBookBody(contents=['a', 'b', 'c'])
    >>> print(lyBookBody.stringOutput())
    a
    b
    c
    '''
    def __init__(self,
                 contents: list[LyObject|str]|None = None,
                 bookIdentifier: str|None = None,
                 ) -> None:
        if contents is None:
            contents = []
        super().__init__()
        self.contents = contents
        self.bookIdentifier = bookIdentifier

    def stringOutput(self) -> str:
        if self.bookIdentifier is not None:
            return self.bookIdentifier
        elif not self.contents:
            return ''
        else:
            return self.newlineSeparateStringOutputIfNotNone(self.contents)


class LyBookpartBlock(LyObject):
    r'''
    >>> lbb = lily.lilyObjects.LyBookpartBlock()
    >>> lbb.stringOutput()
    '\\bookpart  { \n\n } \n'
    '''
    def __init__(self, bookpartBody: LyBookpartBody|None = None) -> None:
        super().__init__()
        self.bookpartBody = bookpartBody

    def stringOutput(self) -> str:
        if self.bookpartBody is None:
            return self.backslash + 'bookpart ' + self.encloseCurly('')
        else:
            return self.backslash + 'bookpart ' + self.encloseCurly(
                self.bookpartBody.stringOutput())


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

    >>> lyBookpartBody = lily.lilyObjects.LyBookpartBody(bookIdentifier='bookId')
    >>> lyBookpartBody.stringOutput()
    'bookId'

    >>> lyBookpartBody = lily.lilyObjects.LyBookpartBody()
    >>> lyBookpartBody.stringOutput()
    ''

    >>> lyBookpartBody = lily.lilyObjects.LyBookpartBody(contents=['a', 'b', 'c'])
    >>> print(lyBookpartBody.stringOutput())
    a
    b
    c
    '''
    def __init__(self,
                 contents: list[LyObject|str]|None = None,
                 bookIdentifier: str|None = None,
                 ) -> None:
        if contents is None:
            contents = []
        super().__init__()
        self.contents = contents
        self.bookIdentifier = bookIdentifier

    def stringOutput(self) -> str:
        if self.bookIdentifier is not None:
            return self.bookIdentifier
        elif not self.contents:
            return ''
        else:
            return self.newlineSeparateStringOutputIfNotNone(self.contents)


class LyScoreBlock(LyObject):
    r'''
    represents the container for a score ( \score { ... } )

    with all the real stuff being in self.scoreBody

    >>> lyScoreBlock = lily.lilyObjects.LyScoreBlock(scoreBody='hello')
    >>> print(lyScoreBlock)
    \score { hello }
    '''
    def __init__(self, scoreBody: LyScoreBody|str|None = None) -> None:
        super().__init__()
        self.scoreBody = scoreBody

    def stringOutput(self) -> str:
        if self.scoreBody is None:
            raise LilyObjectsException('scoreBody object cannot be empty!')  # pragma: no cover

        return self.backslash + 'score ' + self.encloseCurly(self.scoreBody)


class LyScoreBody(LyObject):
    r'''
    represents the contents of a \score { contents }
    block

    can take one of the following attributes:
    music, scoreIdentifier, scoreBody, lilypondHeader, outputDef, error

    >>> lsb = lily.lilyObjects.LyScoreBody(scoreIdentifier='score')
    >>> str(lsb)
    'score'
    '''
    def __init__(self,
                 music: LyMusic|None = None,
                 scoreIdentifier: str|None = None,
                 scoreBody: LyScoreBody|None = None,
                 lilypondHeader: LyLilypondHeader|None = None,
                 outputDef: LyOutputDef|None = None,
                 error: LyObject|None = None,
                 ) -> None:
        super().__init__()
        self.music = music
        self.scoreIdentifier = scoreIdentifier
        self.scoreBody = scoreBody
        self.lilypondHeader = lilypondHeader
        self.outputDef = outputDef
        self.error = error

    def stringOutput(self) -> str:
        if self.music is not None:
            return self.music.stringOutput()
        elif self.scoreIdentifier is not None:
            return self.scoreIdentifier
        elif self.scoreBody is None:
            raise LilyObjectsException(
                'scoreBody cannot be None if music and scoreIdentifier are None')
        elif self.lilypondHeader is not None:
            return self.scoreBody.stringOutput() + ' ' + self.lilypondHeader.stringOutput()
        elif self.outputDef is not None:
            return self.scoreBody.stringOutput() + ' ' + self.outputDef.stringOutput()
        elif self.error is not None:
            return self.scoreBody.stringOutput() + ' ' + self.error.stringOutput()
        else:
            raise LilyObjectsException(
                'one of music, scoreIdentifier, lilypondHeader, outputDef, or error '
                + 'must not be None')


class LyPaperBlock(LyObject):

    def __init__(self, outputDef: LyOutputDef|None = None) -> None:
        super().__init__()
        self.outputDef = outputDef

    def stringOutput(self) -> str:
        if self.outputDef is None:  # legal??
            return ''
        else:
            return self.outputDef.stringOutput()

class LyLayout(LyObject):
    def stringOutput(self) -> str:
        theseStrings = [self.backslash + 'layout {',
                        ' ' + self.backslash + 'context {',
                        '   ' + self.backslash + 'RemoveEmptyStaves',
                        '   ' + self.backslash + 'override VerticalAxisGroup.remove-first = ##t',
                        ' ' + '}', '}']

        return self.newlineSeparateStringOutputIfNotNone(theseStrings)


class LyOutputDef(LyObject):
    r'''
    This is an ugly grammar, since it does not close the curly bracket.
    '''
    def __init__(self, outputDefBody: LyOutputDefBody|None = None) -> None:
        super().__init__()
        self.outputDefBody = outputDefBody

    def stringOutput(self) -> str:
        if self.outputDefBody is None:
            raise LilyObjectsException('Need outputDefBody to be set')  # pragma: no cover
        return self.outputDefBody.stringOutput() + '}'


class LyOutputDefHead(LyObject):
    r'''
    defType can be paper, midi, or layout.

    >>> lyODH = lily.lilyObjects.LyOutputDefHead()
    >>> lyODH.defType = 'midi'
    >>> print(lyODH.stringOutput())
    \midi

    According to Appendix C, is the same as LyOutputDefHeadWithModeSwitch
    '''
    def __init__(self, defType: str|None = None) -> None:
        super().__init__()
        self.defType = defType

    def stringOutput(self) -> str:
        if self.defType not in ('paper', 'midi', 'layout'):  # pragma: no cover
            raise LilyObjectsException("self.defType must be one of 'paper', 'midi', or 'layout'")

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
    def __init__(self,
                 outputDefHead: LyOutputDefHead|None = None,
                 outputDefIdentifier: str|None = None,
                 outputDefBody: LyOutputDefBody|None = None,
                 assignment: LyAssignment|None = None,
                 contextDefSpecBlock: LyContextDefSpecBlock|None = None,
                 error: LyObject|None = None,
                 ) -> None:
        super().__init__()
        self.outputDefHead = outputDefHead
        self.outputDefIdentifier = outputDefIdentifier
        self.outputDefBody = outputDefBody
        self.assignment = assignment
        self.contextDefSpecBlock = contextDefSpecBlock
        self.error = error

    def stringOutput(self) -> str:
        if self.outputDefHead is not None:
            out = str(self.outputDefHead) + ' { '
            if self.outputDefIdentifier is not None:
                return out + str(self.outputDefIdentifier)
            else:
                return out
        elif self.outputDefBody is None:  # pragma: no cover
            raise LilyObjectsException('Need embedded outputDefBody if outputDefIdentifier '
                                       + 'or outputDefHead are not defined')
        elif self.assignment is not None:
            return self.outputDefBody.stringOutput() + ' ' + self.assignment.stringOutput()
        elif self.contextDefSpecBlock is not None:
            return self.outputDefBody.stringOutput() + ' ' + self.contextDefSpecBlock.stringOutput()
        elif self.error is not None:
            return self.outputDefBody.stringOutput() + ' ' + self.error.stringOutput()
        else:  # pragma: no cover
            raise LilyObjectsException('Need to define at least one of assignment, '
                                       + 'contextDefSpecBlock, or error if outputDefHead is None')


class LyTempoEvent(LyObject):
    r'''
    tempo_event: "\tempo" steno_duration '=' tempo_range
               | "\tempo" scalar steno_duration '=' tempo_range
               | "\tempo" steno_duration '=' scalar
               | "\tempo" scalar

    >>> lte = lily.lilyObjects.LyTempoEvent(scalar='40')
    >>> str(lte)
    '\\tempo 40'

    A steno_duration paired with a single bpm scalar (and no tempoRange)
    is the common case for a music21 MetronomeMark, e.g. quarter = 87:

    >>> steno = lily.lilyObjects.LyStenoDuration(4)
    >>> lte = lily.lilyObjects.LyTempoEvent(stenoDuration=steno, scalar=87)
    >>> str(lte)
    '\\tempo 4  = 87'

    More complex, with a tempo range:

    >>> tempoRange = lily.lilyObjects.LyTempoRange(70, 100)
    >>> lte = lily.lilyObjects.LyTempoEvent(tempoRange=tempoRange, stenoDuration=steno)
    >>> str(lte)
    '\\tempo 4  = 70-100 '

    >>> lte.scalar = 85
    >>> str(lte)
    '\\tempo 85 4  = 70-100 '
    '''
    def __init__(self,
                 tempoRange: LyTempoRange|None = None,
                 stenoDuration: LyStenoDuration|None = None,
                 scalar: int|str|None = None,
                 ) -> None:
        super().__init__()
        self.tempoRange = tempoRange
        self.stenoDuration = stenoDuration
        self.scalar = scalar

    def stringOutput(self) -> str:
        base = self.backslash + 'tempo'
        if self.tempoRange is not None:
            if self.stenoDuration is None:  # pragma: no cover
                raise LilyObjectsException('If tempoRange is defined then need a stenoDuration')

            if self.scalar is not None:
                return ' '.join([base,
                                 str(self.scalar),
                                 self.stenoDuration.stringOutput(), '=',
                                 self.tempoRange.stringOutput()])
            else:
                return ' '.join([base, self.stenoDuration.stringOutput(),
                                 '=', self.tempoRange.stringOutput()])
        elif self.stenoDuration is not None:
            if self.scalar is None:  # pragma: no cover
                raise LilyObjectsException(
                    'If tempoRange is not defined but stenoDuration is, need a scalar')
            return ' '.join([base, self.stenoDuration.stringOutput(), '=', str(self.scalar)])
        elif self.scalar is None:  # pragma: no cover
            raise LilyObjectsException('If tempoRange is not defined then need scalar')

        return base + ' ' + str(self.scalar)


class LyMusicList(LyObject):
    r'''
    can take any number of LyMusic, LyEmbeddedScm, or LyError objects
    '''
    def __init__(self, contents: list[LyObject|str]|None = None) -> None:
        super().__init__()
        if contents is None:
            contents = []
        self.contents = contents

    def stringOutput(self) -> str:
        return self.newlineSeparateStringOutputIfNotNone(self.contents)


class LyMusic(LyObject):

    def __init__(self,
                 simpleMusic: LySimpleMusic|None = None,
                 compositeMusic: LyCompositeMusic|None = None,
                 ) -> None:
        super().__init__()
        self.simpleMusic = simpleMusic
        self.compositeMusic = compositeMusic

    def stringOutput(self) -> str:
        if self.simpleMusic is not None:
            return self.simpleMusic.stringOutput()
        elif self.compositeMusic is not None:
            return self.compositeMusic.stringOutput()
        else:  # pragma: no cover
            raise LilyObjectsException('Need to define one of simpleMusic or compositeMusic')


class LyAlternativeMusic(LyObject):

    def __init__(self, musicList: LyMusicList|None = None) -> None:
        super().__init__()
        self.musicList = musicList

    def stringOutput(self) -> str:
        if self.musicList is None:
            return ''
        else:
            return self.backslash + 'alternative' + self.encloseCurly(self.musicList)


class LyRepeatedMusic(LyObject):

    def __init__(self,
                 simpleString: LyObject|None = None,
                 unsignedNumber: LyObject|None = None,
                 music: LyMusic|None = None,
                 alternativeMusic: LyAlternativeMusic|None = None,
                 ) -> None:
        super().__init__()
        self.simpleString = simpleString
        self.unsignedNumber = unsignedNumber
        self.music = music
        self.alternativeMusic = alternativeMusic

    def stringOutput(self) -> str:
        if (self.simpleString is None
                or self.unsignedNumber is None
                or self.music is None):  # pragma: no cover
            raise LilyObjectsException(
                'need simpleString, unsignedNumber, and music to output repeated music')
        out = (self.backslash
               + 'repeat '
               + self.simpleString.stringOutput()
               + self.unsignedNumber.stringOutput()
               + self.music.stringOutput())
        if self.alternativeMusic is None:
            return out
        else:
            return out + ' ' + self.alternativeMusic.stringOutput()


class LySequentialMusic(LyObject):
    r'''
    represents sequential music.

    Can be explicitly tagged with "\sequential" if displayTag is True
    '''
    def __init__(self,
                 musicList: LyObject|None = None,
                 displayTag: bool = False,
                 beforeMatter: str|None = None,
                 ) -> None:
        super().__init__()
        self.musicList = musicList
        self.displayTag = displayTag
        self.beforeMatter = beforeMatter

    def stringOutput(self) -> str:
        if self.musicList is not None:
            musicListSO = self.musicList.stringOutput()
        else:
            musicListSO = ''
        tag = ''
        if self.displayTag:
            tag = self.backslash + 'sequential '

        if self.beforeMatter == 'startStaff':
            beforeMatter = self.backslash + 'startStaff '
        else:
            beforeMatter = ''

        return tag + '{ ' + beforeMatter + musicListSO + ' } ' + self.newlineIndent
        # + self.encloseCurly(musicListSO)


class LyOssiaMusic(LyObject):
    r'''
    represents ossia music.

    Can be tagged with \startStaff and \stopStaff if startstop is True
    '''
    def __init__(self, musicList: LyMusicList|None = None, startstop: bool = True) -> None:
        super().__init__()
        self.musicList = musicList
        self.startstop = startstop

    def stringOutput(self) -> str:
        if self.startstop:
            start = self.backslash + 'startStaff '
            stop = self.backslash + 'stopStaff'
        else:
            start, stop = '', ''

        if self.musicList is not None:
            musicListSO = self.musicList.stringOutput()
        else:
            musicListSO = ''

        return '{' + start + musicListSO + ' ' + stop + '}' + self.newlineIndent


class LySimultaneousMusic(LyObject):
    r'''
    represents simultaneous music.

    Can be explicitly tagged with '\simultaneous' if displayTag is True
    otherwise encloses in double angle brackets
    '''
    def __init__(self, musicList: LyMusicList|None = None, displayTag: bool = False) -> None:
        super().__init__()
        self.musicList = musicList
        self.displayTag = displayTag

    def stringOutput(self) -> str:
        if self.musicList is not None:
            musicListSO = self.musicList.stringOutput()
        else:
            musicListSO = ''
        # tag = ''
        if self.displayTag is True:
            return self.backslash + 'simultaneous ' + self.encloseCurly(musicListSO)
        else:
            return ''.join([self.newlineIndent, '<< ', musicListSO, ' >>', self.newlineIndent])


class LySimpleMusic(LyObject):

    def __init__(self,
                 eventChord: LyEventChord|None = None,
                 musicIdentifier: LyObject|None = None,
                 musicPropertyDef: LyMusicPropertyDef|None = None,
                 contextChange: LyContextChange|None = None,
                 ) -> None:
        super().__init__()
        self.eventChord = eventChord
        self.musicIdentifier = musicIdentifier
        self.musicPropertyDef = musicPropertyDef
        self.contextChange = contextChange

    def stringOutput(self) -> str:
        outputObject = self.getFirstNonNoneAttribute(['eventChord', 'musicIdentifier',
                                                      'musicPropertyDef', 'contextChange'])
        if outputObject is None:
            raise LilyObjectsException('need one attribute set')  # pragma: no cover
        return outputObject.stringOutput()


class LyContextModification(LyObject):
    r'''
    represents both context_modification and optional_context_mod

    but not context_mod!!!!!
    '''
    def __init__(self,
                 contextModList: LyContextModList|list[str]|None = None,
                 contextModIdentifier: str|None = None,
                 displayWith: bool = True,
                 ) -> None:
        super().__init__()
        self.contextModList = contextModList
        self.contextModIdentifier = contextModIdentifier
        self.displayWith = displayWith  # optional, but not supported without so far

    def stringOutput(self) -> str:
        if self.contextModList is not None:
            return self.backslash + 'with ' + self.encloseCurly(self.contextModList)
        elif self.contextModIdentifier is not None:
            return self.backslash + 'with ' + self.contextModIdentifier
        else:
            return ''


class LyContextModList(LyObject):
    r'''
    contains zero or more LyContextMod objects and an optional contextModIdentifier
    '''
    def __init__(self,
                 contents: list[LyContextMod]|None = None,
                 contextModIdentifier: str|None = None,
                 ) -> None:
        if contents is None:
            contents = []
        super().__init__()
        self.contents = contents
        self.contextModIdentifier = contextModIdentifier

    def stringOutput(self) -> str:
        output = self.newlineSeparateStringOutputIfNotNone(self.contents)
        if self.contextModIdentifier is not None:
            return output + ' ' + self.contextModIdentifier
        else:
            return output


class LyCompositeMusic(LyObject):
    r'''
    one of LyPrefixCompositeMusic or LyGroupedMusicList stored in self.contents
    '''
    def __init__(self,
                 prefixCompositeMusic: LyPrefixCompositeMusic|None = None,
                 groupedMusicList: LyObject|None = None,
                 newLyrics: LyNewLyrics|None = None,
                 ) -> None:
        super().__init__()
        self.prefixCompositeMusic = prefixCompositeMusic
        self.groupedMusicList = groupedMusicList
        self.newLyrics = newLyrics

    @property
    def contents(self) -> LyObject|None:
        if self.prefixCompositeMusic is not None:
            return self.prefixCompositeMusic
        else:
            return self.groupedMusicList

    def stringOutput(self) -> str:
        newLyrics: LyNewLyrics|str
        if self.newLyrics is not None:
            newLyrics = self.newLyrics
        else:
            newLyrics = ''

        if self.prefixCompositeMusic is not None:
            return str(self.prefixCompositeMusic) + '\n' + str(newLyrics)
        elif self.groupedMusicList is not None:
            return str(self.groupedMusicList) + '\n' + str(newLyrics)
        else:
            raise LilyObjectsException(
                'Need to define either prefixCompositeMusic or groupedMusicList')


class LyGroupedMusicList(LyObject):
    r'''
    one of LySimultaneousMusic or LySequentialMusic
    '''
    def __init__(self,
                 simultaneousMusic: LySimultaneousMusic|None = None,
                 sequentialMusic: LySequentialMusic|None = None,
                 ) -> None:
        super().__init__()
        self.simultaneousMusic = simultaneousMusic
        self.sequentialMusic = sequentialMusic

    def stringOutput(self) -> str:
        if self.simultaneousMusic is not None:
            return str(self.simultaneousMusic)
        elif self.sequentialMusic is not None:
            return str(self.sequentialMusic)
        else:  # pragma: no cover
            raise LilyObjectsException(
                'Need to define either simultaneousMusic or sequentialMusic')


class LySchemeFunction(LyObject):
    r'''
    Unsupported for now, represents all of::

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

    We have usually been using LyEmbeddedScm for this
    '''
    def __init__(self, content: LyObject|str|None = None) -> None:
        super().__init__()
        self.content = content

    def stringOutput(self) -> str:
        if self.content is None:
            return ''
        else:
            return str(self.content)


class LyOptionalId(LyObject):
    r'''
    an optional id setting
    '''
    def __init__(self, content: str|None = None) -> None:
        super().__init__()
        self.content = content

    def stringOutput(self) -> str:
        if self.content is None:
            return ''
        else:
            return ' = ' + self.content


class LyPrefixCompositeMusic(LyObject):
    r'''
    type must be specified.  Should be one of:

    scheme, context, new, tuplet, repeated, transpose,
    modeChanging, modeChangingWith, relative,
    rhythmed

    The 'tuplet' fraction is actual/normal: `3/2` is three notes in the time of two.

    prefix_composite_music: generic_prefix_music_scm
                       | "\context"
                                simple_string
                                optional_id
                                optional_context_mod
                                music
                       | "\new"
                                simple_string
                                optional_id
                                optional_context_mod
                                music
                       | "\tuplet" fraction music
                       | repeated_music
                       | "\transpose"
                                pitch_also_in_chords
                                pitch_also_in_chords
                                music
                       | mode_changing_head grouped_music_list
                       | mode_changing_head_with_context
                                optional_context_mod
                                grouped_music_list
                       | relative_music
                       | re_rhythmed_music
    '''
    # pylint: disable=redefined-builtin
    def __init__(self,
                 type: str|None = None,
                 genericPrefixMusicScm: LyObject|None = None,
                 simpleString: str|None = None,
                 optionalId: LyOptionalId|None = None,
                 optionalContextMod: LyContextModification|None = None,
                 music: LyObject|str|None = None,
                 fraction: str|None = None,
                 repeatedMusic: LyRepeatedMusic|None = None,
                 pitchAlsoInChords1: LyPitch|None = None,
                 pitchAlsoInChords2: LyPitch|None = None,
                 modeChangingHead: LyModeChangingHead|None = None,
                 groupedMusicList: LyGroupedMusicList|None = None,
                 modeChangingHeadWithContext: LyModeChangingHead|None = None,
                 relativeMusic: LyRelativeMusic|None = None,
                 reRhythmedMusic: LyReRhythmedMusic|None = None,
                 ) -> None:
        super().__init__()
        self.type = type
        self.genericPrefixMusicScm = genericPrefixMusicScm
        self.simpleString = simpleString
        self.optionalId = optionalId
        self.optionalContextMod = optionalContextMod
        self.music = music
        self.fraction = fraction
        self.repeatedMusic = repeatedMusic
        self.pitchAlsoInChords1 = pitchAlsoInChords1
        self.pitchAlsoInChords2 = pitchAlsoInChords2
        self.modeChangingHead = modeChangingHead
        self.groupedMusicList = groupedMusicList
        self.modeChangingHeadWithContext = modeChangingHeadWithContext
        self.relativeMusic = relativeMusic
        self.reRhythmedMusic = reRhythmedMusic

    def stringOutput(self) -> str:
        myType = self.type
        if myType == 'scheme':
            return str(self.genericPrefixMusicScm)
        elif myType in ('context', 'new'):
            c = self.backslash + myType + ' ' + str(self.simpleString) + ' '
            if self.optionalId is not None:
                c += str(self.optionalId) + ' '
            if self.optionalContextMod is not None:
                c += str(self.optionalContextMod) + ' '
            c += str(self.music) + ' '
            return c
        elif myType == 'tuplet':
            return self.backslash + 'tuplet ' + str(self.fraction) + ' ' + str(self.music) + ' '
        elif myType == 'repeated':
            return str(self.repeatedMusic)
        elif myType == 'transpose':
            return ''.join([self.backslash, 'transpose ', str(self.pitchAlsoInChords1), ' ',
                            str(self.pitchAlsoInChords2), ' ', str(self.music), ' '])
        elif myType == 'modeChanging':
            return str(self.modeChangingHead) + ' ' + str(self.groupedMusicList)
        elif myType == 'modeChangingWith':
            c = str(self.modeChangingHeadWithContext) + ' '
            if self.optionalContextMod is not None:
                c += str(self.optionalContextMod) + ' '
            c += str(self.groupedMusicList) + ' '
            return c
        elif myType == 'relative':
            return str(self.relativeMusic)
        elif myType == 'rhythmed':
            return str(self.reRhythmedMusic)
        else:  # pragma: no cover
            raise LilyObjectsException(f'unknown self.type or None: {self.type}')


class LyModeChangingHead(LyObject):
    r'''
    represents both mode_changing_head and mode_changing_head_with_context

    .hasContext = False
    .mode = ['note', 'drum', 'figure', 'chord', 'lyric']

    >>> l = lily.lilyObjects.LyModeChangingHead(hasContext=True, mode='drum')
    >>> print(l.stringOutput())
    \drummode
    >>> l2 = lily.lilyObjects.LyModeChangingHead(hasContext=False, mode='chord')
    >>> print(l2.stringOutput())
    \chords

    Mode 'note' always gives `\notemode`:

    >>> l3 = lily.lilyObjects.LyModeChangingHead(hasContext=False, mode='note')
    >>> print(l3.stringOutput())
    \notemode
    '''
    allowableModes = ['note', 'drum', 'figure', 'chord', 'lyric']

    def __init__(self, hasContext: bool = False, mode: str|None = None) -> None:
        super().__init__()
        self.hasContext = hasContext
        self.mode = mode

    def stringOutput(self) -> str:
        mode = self.mode
        if mode is None:
            raise LilyObjectsException('Mode must be set')  # pragma: no cover
        if mode not in self.allowableModes:
            raise LilyObjectsException(f'Not an allowable mode {mode}')  # pragma: no cover

        if self.hasContext or mode == 'note':
            return self.backslash + mode + 'mode'
        else:
            return self.backslash + mode + 's'


class LyRelativeMusic(LyObject):
    r'''
    relative music
    '''
    def __init__(self, content: LyObject|None = None) -> None:
        super().__init__()
        self.content = content

    def stringOutput(self) -> str:
        if self.content is None:  # pragma: no cover
            raise LilyObjectsException('need content for relative music')
        return self.backslash + 'relative ' + self.content.stringOutput()


class LyNewLyrics(LyObject):
    r'''
    contains a list of LyGroupedMusicList objects or identifiers
    '''
    def __init__(self, groupedMusicLists: list[LyGroupedMusicList|str]|None = None) -> None:
        if groupedMusicLists is None:
            groupedMusicLists = []
        super().__init__()
        self.groupedMusicLists = groupedMusicLists

    def stringOutput(self) -> str:
        outputString = ''
        for c in self.groupedMusicLists:
            outputString += self.backslash + 'addlyrics '
            if isinstance(c, LyObject):
                outputString += c.stringOutput()
            else:
                outputString += c + ' '

        return outputString


class LyReRhythmedMusic(LyObject):
    def __init__(self,
                 groupedMusic: LyGroupedMusicList|str|None = None,
                 newLyrics: LyNewLyrics|None = None,
                 ) -> None:
        super().__init__()
        self.groupedMusic = groupedMusic
        self.newLyrics = newLyrics

    def stringOutput(self) -> str:
        c = self.groupedMusic
        if isinstance(c, LyObject):
            outputString = c.stringOutput()
        elif c is not None:
            outputString = c + ' '
        else:  # pragma: no cover
            raise LilyObjectsException('need groupedMusic for re-rhythmed music')
        if self.newLyrics is not None:
            outputString += self.newLyrics.stringOutput()
        return outputString


class LyContextChange(LyObject):
    r'''
    >>> lcc = lily.lilyObjects.LyContextChange('x', 'y')
    >>> str(lcc)
    '\\change x = y '
    '''
    def __init__(self, before: str = '', after: str = '') -> None:
        super().__init__()
        self.before = before
        self.after = after

    def stringOutput(self) -> str:
        return self.backslash + 'change ' + self.before + ' = ' + self.after + ' '


class LyPropertyPath(LyObject):
    r'''
    represents both property_path and property_path_revved

    has one or more of LyEmbeddedScm objects
    '''
    def __init__(self, embeddedScheme: list[LyEmbeddedScm]|None = None) -> None:
        if embeddedScheme is None:
            embeddedScheme = []

        super().__init__()
        self.embeddedScheme = embeddedScheme

    def stringOutput(self) -> str:
        return ' '.join([es.stringOutput() for es in self.embeddedScheme])


class LyPropertyOperation(LyObject):
    r'''
    Represents:

       property_operation: STRING '=' scalar
                       | "\unset" simple_string
                       | "\override" simple_string property_path '=' scalar
                       | "\revert" simple_string embedded_scm

    mandatory mode in ['set', 'unset', 'override', 'revert']

    also represents simple_music_property_def which has the same forms

    >>> lpo = lily.lilyObjects.LyPropertyOperation('unset', 'simple')
    >>> str(lpo)
    '\\unset simple '

    >>> lpo = lily.lilyObjects.LyPropertyOperation('override', 'simple', 'x', 'y')
    >>> str(lpo)
    '\\override simple.x = y '

    >>> lpo = lily.lilyObjects.LyPropertyOperation('revert', 'x', 'y')
    >>> str(lpo)
    '\\revert x.y '
    '''
    # TODO: should \set be given?
    def __init__(self,
                 mode: str|None = None,
                 value1: str = '',
                 value2: str = '',
                 value3: str = '',
                 ) -> None:
        super().__init__()
        self.mode = mode
        self.value1 = value1
        self.value2 = value2
        self.value3 = value3

    def stringOutput(self) -> str:
        if self.mode == 'set':
            return self.backslash + 'set ' + self.value1 + ' = ' + self.value2 + ' '
        elif self.mode == 'unset':
            return self.backslash + 'unset ' + self.value1 + ' '
        elif self.mode == 'override':
            return ''.join([self.backslash, 'override ', self.value1, '.', self.value2,
                            ' = ', self.value3, ' '])
        elif self.mode == 'revert':
            return self.backslash + 'revert ' + self.value1 + '.' + self.value2 + ' '
        else:
            raise LilyObjectsException(f'invalid mode {self.mode}')


class LyContextDefMod(LyObject):
    r'''
    one of consists, remove, accepts, defaultchild, denies, alias, type, description, name
    '''
    def __init__(self, contextDef: str = '') -> None:
        super().__init__()
        self.contextDef = contextDef

    def stringOutput(self) -> str:
        return self.backslash + self.contextDef + ' '


class LyContextMod(LyObject):
    def __init__(self,
                 contextDefOrProperty: LyContextDefMod|LyPropertyOperation|None = None,
                 scalar: str|None = None,
                 ) -> None:
        super().__init__()
        self.contextDefOrProperty = contextDefOrProperty
        self.scalar = scalar

    def stringOutput(self) -> str:
        if self.contextDefOrProperty is None:  # pragma: no cover
            raise LilyObjectsException('need a contextDef or property to modify a context')
        if self.scalar is None:
            return self.contextDefOrProperty.stringOutput()
        else:
            return self.contextDefOrProperty.stringOutput() + ' ' + self.scalar + ' '

# no need for context_prop_spec -- just strings
# see LyPropertyOperation for simple_music_property_def


class LyMusicPropertyDef(LyObject):

    def __init__(self, isOnce: bool = False, propertyDef: LyPropertyOperation|None = None) -> None:
        super().__init__()
        self.isOnce = isOnce
        self.propertyDef = propertyDef

    def stringOutput(self) -> str:
        if self.propertyDef is None:  # pragma: no cover
            raise LilyObjectsException('need a propertyDef for a music property definition')
        s = ''
        if self.isOnce:
            s += self.backslash + 'once '
        return s + self.propertyDef.stringOutput()

# string, simple_string, scalar, etc. not needed


class LyEventChord(LyObject):
    r'''
    takes all the parts as a list of up to three elements::

        event_chord: simple_chord_elements post_events
               | CHORD_REPETITION optional_notemode_duration post_events
               | MULTI_MEASURE_REST optional_notemode_duration post_events
               | command_element
               | note_chord_element

    simple_chord_elements can be a LySimpleElement object.  Or it can be a
    LyNewChord or LyFigureSpec + Duration
    once that is done.  But there is no LySimpleChordElements object yet.
    '''
    def __init__(self,
                 simpleChordElements: LySimpleElement|None = None,
                 postEvents: list[LyObject|str]|None = None,
                 chordRepetition: LyObject|str|None = None,
                 multiMeasureRest: LyObject|str|None = None,
                 duration: str|None = None,
                 commandElement: LyCommandElement|None = None,
                 noteChordElement: LyNoteChordElement|None = None,
                 ) -> None:
        super().__init__()
        self.simpleChordElements = simpleChordElements
        self.postEvents = postEvents
        self.chordRepetition = chordRepetition
        self.multiMeasureRest = multiMeasureRest
        self.duration = duration
        self.commandElement = commandElement
        self.noteChordElement = noteChordElement

    def stringOutput(self) -> str:
        if self.noteChordElement is not None:
            return str(self.noteChordElement) + ' '
        elif self.commandElement is not None:
            return str(self.commandElement) + ' '
        elif self.multiMeasureRest is not None:
            c = str(self.multiMeasureRest)
            if self.duration is not None:
                c += ' ' + self.duration
            if self.postEvents is not None:
                for pe in self.postEvents:
                    c += str(pe)
            c += ' '
            return c
        elif self.chordRepetition is not None:
            c = str(self.chordRepetition)
            if self.duration is not None:
                c += ' ' + self.duration
            if self.postEvents is not None:
                for pe in self.postEvents:
                    c += ' ' + str(pe)
            c += ' '
            return c
        else:
            c = str(self.simpleChordElements)
            if self.postEvents is not None:
                for pe in self.postEvents:
                    c += ' ' + str(pe)
            c += ' '
            return c


class LyNoteChordElement(LyObject):
    def __init__(self,
                 chordBody: LyChordBody|LyPitch|None = None,
                 optionalNoteModeDuration: LyMultipliedDuration|None = None,
                 postEvents: list[LyObject|str]|None = None,
                 ) -> None:
        if postEvents is None:
            postEvents = []
        super().__init__()
        self.chordBody = chordBody
        self.optionalNoteModeDuration = optionalNoteModeDuration
        self.postEvents = postEvents

    def stringOutput(self) -> str:
        c = str(self.chordBody)
        if self.optionalNoteModeDuration is not None:
            c += str(self.optionalNoteModeDuration) + ' '
        for pe in self.postEvents:
            c += str(pe) + ' '
        return c


class LyChordBody(LyObject):

    def __init__(self, chordBodyElements: list[LyChordBodyElement]|None = None) -> None:
        if chordBodyElements is None:
            chordBodyElements = []

        super().__init__()
        self.chordBodyElements = chordBodyElements

    def stringOutput(self) -> str:
        c = ' '.join([str(cbe) for cbe in self.chordBodyElements])
        return ' '.join(['<', c, '> '])


class LyChordBodyElement(LyObject):
    r'''
    Contains a note or a drum pitch or a music function::

      chord_body_element: pitch
                            exclamations (a string of zero or more ! marks)
                            questions (a string of zero or more ? marks)
                            octave_check
                            post_events
                       | DRUM_PITCH post_events
                       | music_function_chord_body
    '''
    # TODO: only the first form is currently supported in creation
    def __init__(self, parts: list[LyObject|str]|None = None) -> None:
        if parts is None:
            parts = []
        super().__init__()
        self.parts = parts

    def stringOutput(self) -> str:
        return ' '.join([str(p) for p in self.parts])

# music_function_identifier_musicless_prefix: MUSIC_FUNCTION

# NOT Supported
#  217 music_function_chord_body: music_function_identifier_musicless_prefix
#                                   EXPECT_MUSIC
#                                   function_arglist_nonmusic
#                                   chord_body_element
#  218                          | music_function_identifier_musicless_prefix
#                                   function_arglist_nonmusic
#
#  219 music_function_event: music_function_identifier_musicless_prefix
#                              EXPECT_MUSIC
#                              function_arglist_nonmusic
#                              post_event
#  220                     | music_function_identifier_musicless_prefix
#                              function_arglist_nonmusic


class LyCommandElement(LyObject):
    def __init__(self,
                 commandType: LyObject|str|None = None,
                 argument: LyObject|str|None = None,
                 ) -> None:
        super().__init__()
        self.commandType = commandType
        self.argument = argument

    def stringOutput(self) -> str:
        ct = self.commandType
        if not isinstance(ct, str):
            if ct is None:  # pragma: no cover
                raise LilyObjectsException('need a commandType to output a command element')
            return ct.stringOutput()

        arg = self.argument
        if ct in ('skip', 'partial'):
            argOut = arg.stringOutput() if isinstance(arg, LyObject) else str(arg)
            return self.backslash + ct + ' ' + argOut
        elif ct == '[':
            # ligature brackets; manual beams are plain [ and ]
            return self.backslash + '[ '
        elif ct == ']':
            return self.backslash + '] '
        elif ct == self.backslash:
            return ct + ' '
        elif ct in ('time', 'mark'):
            return self.backslash + ct + ' ' + str(arg) + ' '
        else:  # pragma: no cover
            raise LilyObjectsException(f'unknown commandType {ct}')


class LyCommandEvent(LyObject):
    def __init__(self,
                 commandType: LyTempoEvent|str|None = None,
                 argument1: str = '',
                 argument2: str = '',
                 ) -> None:
        super().__init__()
        self.commandType = commandType
        self.argument1 = argument1
        self.argument2 = argument2

    def stringOutput(self) -> str:
        ct = self.commandType
        if ct == '~':
            # E_TILDE, the pes-or-flexa ligature event
            return self.backslash + '~ '
        elif ct == 'mark-default':
            return self.backslash + 'mark ' + self.backslash + 'default '
        elif ct == 'key-default':
            return self.backslash + 'key ' + self.backslash + 'default '
        elif ct == 'key':
            # \key NOTENAME_PITCH SCM_IDENTIFIER
            return self.backslash + 'key ' + self.argument1 + ' ' + self.argument2 + ' '
        elif isinstance(ct, LyTempoEvent):
            return ct.stringOutput()
        else:  # pragma: no cover
            raise LilyObjectsException(f'unknown commandType {ct}')


class LyPostEvents(LyObject):
    def __init__(self, eventList: list[LyObject]|None = None) -> None:
        if eventList is None:
            eventList = []
        super().__init__()
        self.eventList = eventList

    def stringOutput(self) -> str:
        return ' '.join([e.stringOutput() for e in self.eventList])


class LyPostEvent(LyObject):

    def __init__(self, arg1: LyObject|str|None = None, arg2: LyObject|str|None = None) -> None:
        super().__init__()
        self.arg1 = arg1
        self.arg2 = arg2

    def stringOutput(self) -> str:
        c = str(self.arg1)
        if self.arg2 is not None:
            c += ' ' + str(self.arg2)
        return c + ' '


class LyDirectionLessEvent(LyObject):
    r'''
    represents ['[', ']', '~', '(', ')', '\!', '\(', '\)', '\>', '\<']
    or an EVENT_IDENTIFIER or a tremolo_type
    '''
    def __init__(self, event: LyObject|str|None = None) -> None:
        super().__init__()
        self.event = event

    def stringOutput(self) -> str:
        return str(self.event) + ' '


# noinspection SpellCheckingInspection
class LyDirectionReqdEvent(LyObject):
    def __init__(self, event: LyObject|str|None = None) -> None:
        super().__init__()
        self.event = event

    def stringOutput(self) -> str:
        return str(self.event) + ' '


class LyOctaveCheck(LyObject):

    def __init__(self, equalOrQuotesOrNone: str|None = None) -> None:
        super().__init__()
        self.equalOrQuotesOrNone = equalOrQuotesOrNone

    def stringOutput(self) -> str:
        eqn = self.equalOrQuotesOrNone
        if eqn is None:
            return ''
        elif eqn == '=':
            return '= '
        else:
            return '= ' + eqn + ' '


class LyPitch(LyObject):
    r'''
    represents a pitch name and zero or more sup or sub quotes
    also used for steno_pitch and steno_tonic_pitch
    '''
    def __init__(self, noteNamePitch: str = '', quotes: str = '') -> None:
        super().__init__()
        self.noteNamePitch = noteNamePitch
        self.quotes = quotes

    def stringOutput(self) -> str:
        return self.noteNamePitch + self.quotes + ' '

# no need for pitch_also_in_chords


class LyGenTextDef(LyObject):
    r'''
    holds either full_markup, string, or DIGIT
    '''
    def __init__(self, value: LyFullMarkup|str|int|None = None) -> None:
        super().__init__()
        self.value = value

    def stringOutput(self) -> str:
        return str(self.value) + ' '


class LyScriptAbbreviation(LyObject):
    r'''
    Holds a script abbreviation (for articulations etc.), one of::

        ^ + - | > . _
    '''
    def __init__(self, value: str = '') -> None:
        super().__init__()
        self.value = value

    def stringOutput(self) -> str:
        return self.value + ' '


class LyScriptDir(LyObject):
    r'''
    Holds a script direction abbreviation (above, below etc.), one of::

        _ ^ -
    '''
    def __init__(self, value: str = '') -> None:
        super().__init__()
        self.value = value

    def stringOutput(self) -> str:
        return self.value + ' '

# no need for absolute_pitch
# no need for optional_notemode_duration -- we can use LyMultipliedDuration or None


class LyStenoDuration(LyObject):
    r'''
    the main thing that we think of as non-tuplet duration.

    a duration number followed by one or more dots

    >>> lsd = lily.lilyObjects.LyStenoDuration('2', 2)
    >>> print(lsd)
    2..
    '''
    def __init__(self, durationNumber: int|str|None = None, numDots: int = 0) -> None:
        super().__init__()
        self.durationNumber = durationNumber
        self.numDots = numDots

    def stringOutput(self) -> str:
        dotStr = '.' * self.numDots
        return str(self.durationNumber) + dotStr + ' '


class LyMultipliedDuration(LyObject):
    r'''
    represents either a simple LyStenoDuration or a list of things that
    the steno duration should be multiplied by.

    if stenoDur is None then output is empty -- thus also represents
    optional_notemode_duration
    '''
    def __init__(self,
                 stenoDur: LyStenoDuration|None = None,
                 multiply: list[int|str]|None = None,
                 ) -> None:
        if multiply is None:
            multiply = []
        super().__init__()
        self.stenoDur = stenoDur
        self.multiply = multiply

    def stringOutput(self) -> str:
        if self.stenoDur is None:
            return ''
        else:
            s = str(self.stenoDur)
            for m in self.multiply:
                s += ' * ' + str(m)
            return s


class LyTremoloType(LyObject):

    def __init__(self, tremTypeOrNone: int|str|None = None) -> None:
        super().__init__()
        self.tremTypeOrNone = tremTypeOrNone

    def stringOutput(self) -> str:
        if self.tremTypeOrNone is not None:
            return ':' + str(self.tremTypeOrNone) + ' '
        else:
            return ': '

# SKIPPING figured bass objects (lines 305 - 325) for now


class LyOptionalRest(LyObject):
    def __init__(self, rest: bool = False) -> None:
        super().__init__()
        self.rest = rest

    def stringOutput(self) -> str:
        if self.rest is False:
            return ''
        else:
            return self.backslash + 'rest '


class LySimpleElement(LyObject):
    r'''
    A single note, lyric element, drum pitch or hidden rest::

        simple_element: pitch
                        exclamations (a string of zero or more ! marks)
                        questions (a string of zero or more ? marks)
                        octave_check
                        optional_notemode_duration
                        optional_rest
                    | DRUM_PITCH optional_notemode_duration
                    | RESTNAME optional_notemode_duration
                    | lyric_element optional_notemode_duration
    '''
    def __init__(self, parts: list[LyObject|str]|None = None) -> None:
        if parts is None:
            parts = []
        super().__init__()
        self.parts = parts

    def stringOutput(self) -> str:
        return ''.join([str(p) for p in self.parts])

# SKIPPING ALL ChordSymbol Markup for now


class LyLyricElement(LyObject):
    r'''
    Object represents a single Lyric in lilypond.

    >>> lle = lily.lilyObjects.LyLyricElement('hel_')
    >>> lle
    <music21.lily.lilyObjects.LyLyricElement hel_>
    >>> print(lle)
    hel_
    '''
    def __init__(self, lyMarkupOrString: LyMarkup|str|None = None) -> None:
        super().__init__()
        self.lyMarkupOrString = lyMarkupOrString

    def stringOutput(self) -> str:
        return str(self.lyMarkupOrString) + ' '


class LyTempoRange(LyObject):
    r'''
    defines either a single tempo or a range

    >>> print(lily.lilyObjects.LyTempoRange(70, 100))
    70-100
    '''
    def __init__(self,
                 lowestOrOnlyTempo: int|str|None = None,
                 highestTempoOrNone: int|str|None = None,
                 ) -> None:
        super().__init__()
        self.lowestOrOnlyTempo = lowestOrOnlyTempo
        self.highestTempoOrNone = highestTempoOrNone

    def stringOutput(self) -> str:
        if self.highestTempoOrNone is None:
            return str(self.lowestOrOnlyTempo) + ' '
        else:
            return str(self.lowestOrOnlyTempo) + '-' + str(self.highestTempoOrNone) + ' '


class LyNumberExpression(LyObject):
    r'''
    any list of numbers or LyNumberTerms separated by '+' or '-' objects.
    '''
    def __init__(self, numberAndSepList: list[LyNumberTerm|int|str]|None = None) -> None:
        if numberAndSepList is None:
            numberAndSepList = []
        super().__init__()
        self.numberAndSepList = numberAndSepList

    def stringOutput(self) -> str:
        c = ' '.join([str(s) for s in self.numberAndSepList])
        return c + ' '


class LyNumberTerm(LyObject):
    r'''
    any list of numbers separated by '*' or '/' strings.
    '''
    def __init__(self, numberAndSepList: list[int|str]|None = None) -> None:
        if numberAndSepList is None:
            numberAndSepList = []
        super().__init__()
        self.numberAndSepList = numberAndSepList

    def stringOutput(self) -> str:
        c = ' '.join([str(s) for s in self.numberAndSepList])
        return c + ' '


class LyLyricMarkup(LyObject):
    def __init__(self,
                 lyricMarkupOrIdentifier: LyObject|str|None = None,
                 markupTop: LyMarkupTop|None = None,
                 ) -> None:
        super().__init__()
        self.lyricMarkupOrIdentifier = lyricMarkupOrIdentifier
        self.markupTop = markupTop

    def stringOutput(self) -> str:
        if self.markupTop is None:
            return str(self.lyricMarkupOrIdentifier) + ' '
        else:
            return str(self.lyricMarkupOrIdentifier) + ' ' + str(self.markupTop)


class LyFullMarkupList(LyObject):
    r'''
    >>> markupList = lily.lilyObjects.LyMarkupList('{ "a" "b" }')
    >>> print(lily.lilyObjects.LyFullMarkupList(markupList))
    \markuplist { "a" "b" }
    '''
    def __init__(self, markupListOrIdentifier: LyMarkupList|str|None = None) -> None:
        super().__init__()
        self.markupListOrIdentifier = markupListOrIdentifier

    def stringOutput(self) -> str:
        mli = self.markupListOrIdentifier
        if isinstance(mli, str):
            return mli + ' '
        elif mli is None:  # pragma: no cover
            raise LilyObjectsException('need a markup list or identifier')
        else:
            return self.backslash + 'markuplist ' + mli.stringOutput()


class LyFullMarkup(LyObject):
    def __init__(self, markupTopOrIdentifier: LyMarkupTop|str|None = None) -> None:
        super().__init__()
        self.markupTopOrIdentifier = markupTopOrIdentifier

    def stringOutput(self) -> str:
        mti = self.markupTopOrIdentifier
        if isinstance(mti, str):
            return mti + ' '
        elif mti is None:  # pragma: no cover
            raise LilyObjectsException('need a markup top or identifier')
        else:
            return self.backslash + 'markup ' + mti.stringOutput()


class LyMarkupTop(LyObject):
    def __init__(self, argument1: str = '', argument2: str|None = None) -> None:
        super().__init__()
        self.argument1 = argument1
        self.argument2 = argument2

    def stringOutput(self) -> str:
        if self.argument2 is None:
            return self.argument1
        else:
            return ' '.join([self.argument1, self.argument2])


class LyMarkupList(LyObject):
    def __init__(self, markupIdentifierOrList: LyObject|str|None = None) -> None:
        super().__init__()
        self.markupIdentifierOrList = markupIdentifierOrList

    def stringOutput(self) -> str:
        return str(self.markupIdentifierOrList)


class LyMarkupComposedList(LyObject):
    def __init__(self, markupHeadList: str = '', markupBracedList: str = '') -> None:
        super().__init__()
        self.markupHeadList = markupHeadList
        self.markupBracedList = markupBracedList

    def stringOutput(self) -> str:
        return ' '.join([self.markupHeadList, self.markupBracedList])


class LyMarkupBracedList(LyObject):
    def __init__(self, listBody: str = '') -> None:
        super().__init__()
        self.listBody = listBody

    def stringOutput(self) -> str:
        return ' '.join(['{', self.listBody, '}'])


class LyMarkupBracedListBody(LyObject):
    def __init__(self, markupOrMarkupList: list[LyObject|str]|None = None) -> None:
        if markupOrMarkupList is None:
            markupOrMarkupList = []

        super().__init__()
        self.markupOrMarkupList = markupOrMarkupList

    def stringOutput(self) -> str:
        c = ''
        for m in self.markupOrMarkupList:
            c += str(m) + ' '
        return c

# skip markup_command_list and arguments for now
# skip markup_head_1_item
# skip markup_head_1_list

# simple_markup can be string or more complex


class LySimpleMarkup(LyObject):
    r'''
    simpleType can be 'string' (or markup identifier or lyric markup identifier, etc.) or
    'score-body' or 'markup-function'

    takes 1 required arg, 2nd for markup_function
    '''
    def __init__(self,
                 simpleType: str = 'string',
                 argument1: str = '',
                 argument2: LyObject|str|None = None,
                 ) -> None:
        super().__init__()
        self.simpleType = simpleType
        self.argument1 = argument1
        self.argument2 = argument2

    def stringOutput(self) -> str:
        if self.simpleType == 'string':
            return self.argument1 + ' '
        elif self.simpleType == 'score-body':
            return self.backslash + 'score { ' + self.argument1 + ' } '
        elif self.simpleType == 'markup-function':
            return self.argument1 + ' ' + str(self.argument2) + ' '
        else:  # pragma: no cover
            raise LilyObjectsException(f'unknown simpleType {self.simpleType}')


class LyMarkup(LyObject):
    def __init__(self,
                 simpleMarkup: LySimpleMarkup|None = None,
                 optionalMarkupHeadList: str|None = None,
                 ) -> None:
        super().__init__()
        self.simpleMarkup = simpleMarkup
        self.optionalMarkupHeadList = optionalMarkupHeadList

    def stringOutput(self) -> str:
        if self.optionalMarkupHeadList is not None:
            c = self.optionalMarkupHeadList + ' '
        else:
            c = ''
        return c + str(self.simpleMarkup)


# ------------older-------------
#
# class LyNote(LyObject):
#    pass
#
# class LyDuration(LyObject):
#    pass
#
# class LyLyricGroup(LyObject):
#    pass
#
# ## --------Layout----------##
#
# class LyPaper(LyObject):
#    m21toLy = {'PageLayout': {'pageWidth': 'paper-width',
#                               'pageHeight': 'paper-height',
#                               'topMargin': 'top-margin',
#                               'bottomMargin': 'bottom-margin',
#                               'leftMargin': 'left-margin',
#                               'rightMargin': 'right-margin',
#                               },
#                }
#
#    defaultAttributes = {'pageWidth': None,
#                 'pageHeight': None,
#                 'topMargin': None,
#                 'bottomMargin': None,
#                 'leftMargin': None,
#                 'rightMargin': None,
#                 }
#
#
# class LyLayout(LyObject):
#    pass
#
#
# ## -------Tools-----------##
# class LyCodePrinter:
#    pass
#
#    def __init__(self):
#        currentIndent = 0
#        bracketNesting = 0
#        angleBracketNest = 0

# # ------Tests------------##

class Test(unittest.TestCase):

    def testOneNoteTheHardWay(self):
        r'''
        make a dotted-half note c.
        '''
        lyPitch = LyPitch('c', "''")

        stenoDuration = LyStenoDuration('2', 1)
        multipliedDuration = LyMultipliedDuration(stenoDuration)

        simpleElement = LySimpleElement(parts=[lyPitch, multipliedDuration])

        eventChord = LyEventChord(simpleElement)
        simpleMusic = LySimpleMusic(eventChord=eventChord)
        musicInner = LyMusic(simpleMusic=simpleMusic)
        musicList = LyMusicList([musicInner])
        sequentialMusic = LySequentialMusic(musicList)
        compositeMusic = LyCompositeMusic(groupedMusicList=sequentialMusic)
        lilypondTop = LyLilypondTop([compositeMusic])
        lilypondOutput = lilypondTop.stringOutput()

        self.assertEqual(lilypondOutput.strip(), "{ c'' 2.  \n    }")

        ancestors = []
        for n in lyPitch.ancestorList():
            ancestors.append(n.__class__.__name__)

        self.assertEqual(ancestors, ['LySimpleElement', 'LyEventChord', 'LySimpleMusic', 'LyMusic',
                                     'LyMusicList', 'LySequentialMusic', 'LyCompositeMusic',
                                     'LyLilypondTop'])
        ancestorCompositeMusic = lyPitch.getAncestorByClass(LyCompositeMusic)
        self.assertIs(ancestorCompositeMusic, compositeMusic)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

