# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         repeat.py
# Purpose:      Base classes for processing repeats
#
# Authors:      Christopher Ariza
#               Daniel Manesh
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------


'''
This module provides the base class for all RepeatMark objects: entities that denote repeats.

Some RepeatMark objects are Expression objects; others are Bar objects. See for instance,
:class:`~music21.bar.Repeat` which represents a normal barline repeat.

'''
import copy
import unittest

from music21 import exceptions21
from music21 import expressions
from music21 import spanner


from music21 import environment
_MOD = 'repeat.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class RepeatMark(object):
    '''Base class of all repeat objects, including RepeatExpression objects and Repeat (Barline) objects. 

    This object is used to for multiple-inheritance of such objects and to filter by class in order
    to get all things that mark repeats.

    The RepeatMark is not itself a :class:`~music21.base.Music21Object` so you should use multiple
    inheritance to put these things in Streams.
    
    The following demonstration shows how a user might see if a Stream has any repeats in it.
    
    
    >>> class PartialRepeat(repeat.RepeatMark, base.Music21Object):
    ...    def __init__(self):
    ...        base.Music21Object.__init__(self)

    >>> s = stream.Stream()
    >>> s.append(note.Note())
    >>> s.append(PartialRepeat())
    >>> repeats = s.getElementsByClass(repeat.RepeatMark)
    >>> if len(repeats) > 0:
    ...    print("Stream has %d repeat(s) in it" % (len(repeats)))
    Stream has 1 repeat(s) in it
    '''
    def __init__(self):
        pass



#-------------------------------------------------------------------------------
class RepeatExpressionException(exceptions21.Music21Exception):
    pass

class RepeatExpression(RepeatMark, expressions.Expression):
    '''
    This class models any mark added to a Score to mark 
    repeat start and end points that are designated by 
    text expressions or symbols, such as D.S. Al Coda, etc.

    N.B. Repeat(Barline) objects are not RepeatExpression objects, 
    but both are RepeatMark subclasses. 

    This class stores internally a 
    :class:`~music21.expressions.TextExpression`. This object 
    is used for rendering text output in translation. A 
    properly configured TextExpression object can also be 
    used to create an instance of a RepeatExpressions.
    '''
    def __init__(self):
        expressions.Expression.__init__(self)
        RepeatMark.__init__(self)
        # store a text version of this expression
        self._textExpression = None
        # store a lost of alternative text representations
        self._textAlternatives = []
        # store a default text justification
        self._textJustification = 'center'
        # for those that have symbols, declare if the symbol is to be used
        self.useSymbol = False

        # for musicxml compatibility
        self._positionDefaultX = None
        self._positionDefaultY = 20 # two staff lines above
        # these values provided for musicxml compatibility
        self._positionRelativeX = None
        self._positionRelativeY = None
        # this does not do anything if default y is defined
        self._positionPlacement = None

    def __repr__(self):
        content = self.getText()
        if content is not None and len(content) > 16:
            return '<music21.repeat.%s "%s...">' % (self.__class__.__name__, content[:16])
        elif content is not None:
            return '<music21.repeat.%s "%s">' % (self.__class__.__name__, content)
        else:
            return '<music21.repeat.%s>' % (self.__class__.__name__)

    def getText(self):
        '''Get the text used for this expression.
        '''
        return self._textExpression.content

    def setText(self, value):
        '''Set the text of this repeat expression. This is also the primary way that the stored TextExpression object is created.
        '''
        if self._textExpression is None:
            self._textExpression = expressions.TextExpression(value)
            self.applyTextFormatting()
        else:
            self._textExpression.content = value
        
    def applyTextFormatting(self, te=None):
        '''Apply the default text formatting to the text expression version of of this repeat
        '''
        if te is None: # use the stored version if possible
            te = self._textExpression
        te.justify = self._textJustification
        return te

    def setTextExpression(self, value):
        '''Directly set a TextExpression object. 
        '''
        if not isinstance(value, expressions.TextExpression):
            raise RepeatExpressionException('must set with a TextExpression object, not: %s' % value)
        self._textExpression = value
        self.applyTextFormatting()

    def getTextExpression(self):
        '''Return a copy of the TextExpression stored in this object.
        '''
        # whenever getting, set justifation
        #self._textJustification
        if self._textExpression is None:
            return None
        else:
            return copy.deepcopy(self._textExpression)

    def isValidText(self, value):
        '''Return True or False if the supplied text could be used for this RepeatExpression.  
        '''
        def stripText(s):
            # remove all spaces, punctuation, and make lower
            s = s.strip()
            s = s.replace(' ', '')
            s = s.replace('.', '')
            s = s.lower()
            return s
        for candidate in self._textAlternatives:
            candidate = stripText(candidate)
            value = stripText(value)
            if value == candidate:
                return True
        return False



class RepeatExpressionMarker(RepeatExpression):
    '''
    Some repeat expressions are markers of positions 
    in the score to jump to; these classes model those makers, 
    such as Coda, Segno, and Fine, which are subclassed below.
    '''
    def __init__(self):
        RepeatExpression.__init__(self)
        # these are generally centered
        self._textJustification = 'center'


class Coda(RepeatExpressionMarker):
    '''The coda symbol, or the word coda, as placed in a score. 

    
    >>> rm = repeat.Coda()
    '''
    # note that only Coda and Segno have non-text expression forms
    def __init__(self, text=None):
        RepeatExpressionMarker.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['Coda', 'to Coda', 'al Coda']
        if text is not None and self.isValidText(text):
            self.setText(text)
            self.useSymbol = False
        else:
            self.setText(self._textAlternatives[0])
            self.useSymbol = True


class Segno(RepeatExpressionMarker):
    '''The segno sign as placed in a score. 

    
    >>> rm = repeat.Segno()
    >>> rm.useSymbol
    True

    '''
    # note that only Coda and Segno have non-text expression forms
    def __init__(self):
        RepeatExpressionMarker.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['Segno']
        self.setText(self._textAlternatives[0])
        self.useSymbol = True

class Fine(RepeatExpressionMarker):
    '''The fine word as placed in a score. 

    
    >>> rm = repeat.Fine()
    '''
    def __init__(self):
        RepeatExpressionMarker.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['fine']
        self.setText(self._textAlternatives[0])
        self._textJustification = 'right'







class RepeatExpressionCommand(RepeatExpression):
    '''
    Some repeat expressions are commands, instructing 
    the reader to go somewhere else. DaCapo and 
    related are examples.
    '''
    def __init__(self):
        RepeatExpression.__init__(self)
        # whether any internal repeats encountered within a jumped region are also repeated.
        self.repeatAfterJump = False
        # generally these should be right aligned, as they are placed 
        # at the end of the measure they alter
        self._textJustification = 'right'


class DaCapo(RepeatExpressionCommand):
    '''
    The Da Capo command, indicating a return to the beginning 
    and a continuation to the end. By default, 
    `repeatAfterJump` is False, indicating that any repeats 
    encountered on the Da Capo repeat not be repeated. 
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['Da Capo', 'D.C.']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])


class DaCapoAlFine(RepeatExpressionCommand):
    '''
    The Da Capo al Fine command, indicating a return to 
    the beginning and a continuation to the 
    :class:`~music21.repeat.Fine` object. By default, 
    `repeatAfterJump` is False, indicating that any 
    repeats encountered on the Da Capo repeat not 
    be repeated. 

    
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['Da Capo al fine', 'D.C. al fine']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])


class DaCapoAlCoda(RepeatExpressionCommand):
    '''
    The Da Capo al Coda command, indicating a return 
    to the beginning and a continuation to the 
    :class:`~music21.repeat.Coda` object. The music 
    resumes at a second :class:`~music21.repeat.Coda` 
    object. By default, `repeatAfterJump` is False, 
    indicating that any repeats encountered on the 
    Da Capo repeat not be repeated. 

    
    >>> rm = repeat.DaCapoAlCoda() 
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)

        self._textAlternatives = ['Da Capo al Coda', 'D.C. al Coda']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])


class AlSegno(RepeatExpressionCommand):
    '''
    Jump to the sign. Presumably a forward jump, not a repeat.

    
    >>> rm = repeat.AlSegno()
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['al Segno']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])


class DalSegno(RepeatExpressionCommand):
    '''
    The Dal Segno command, indicating a return to the segno 
    and a continuation to the end. By default, `repeatAfterJump` 
    is False, indicating that any repeats encountered on 
    the Da Capo repeat not be repeated. 

    
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['Dal Segno', 'D.S.']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])

class DalSegnoAlFine(RepeatExpressionCommand):
    '''
    The Dal Segno al Fine command, indicating a return to the 
    segno and a continuation to the :class:`~music21.repeat.Fine` 
    object. By default, `repeatAfterJump` is False, indicating 
    that any repeats encountered on the Dal Segno repeat not 
    be repeated. 

    
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['Dal Segno al fine', 'D.S. al fine']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])

class DalSegnoAlCoda(RepeatExpressionCommand):
    '''
    The Dal Segno al Coda command, indicating a return to the 
    beginning and a continuation to the :class:`~music21.repeat.Coda` 
    object. The music resumes at a second 
    :class:`~music21.repeat.Coda` object. By default, 
    `repeatAfterJump` is False, indicating that any repeats encountered 
    on the Da Segno repeat not be repeated. 

    
    >>> rm = repeat.DaCapoAlCoda() 
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['Dal Segno al Coda', 'D.S. al Coda']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])




    
#-------------------------------------------------------------------------------
# store a list of one each of RepeatExpression objects; these are used for t
# testing TextExpressions 
repeatExpressionReference = [Coda(), Segno(), Fine(), DaCapo(), DaCapoAlFine(), 
    DaCapoAlCoda(), AlSegno(), DalSegno(), DalSegnoAlFine(), DalSegnoAlCoda()]



#-------------------------------
def insertRepeatEnding(s, start, end, endingNumber=1, inPlace=False):
    '''
    Designates a range of measures as being repeated endings (i.e. first and second endings) 
    within a stream s, where s either contains measures,
    or contains parts which contain measures.  Start and end are integers corresponding to the first and last measure
    number of the "repeatNum" ending.  e.g. if start=6, end=7, and repeatNum=2, the method adds a second ending
    from measures 6 to 7.

    Does not (yet) add a :class:`~music21.bar.RepeatMark` to the end of the first ending.

    Example: create first and second endings over measures 4-6 and measures 11-13 of a chorale, respectively.
            
    
    >>> c1 = corpus.parse('bwv10.7.mxl')
    >>> repeat.insertRepeatEnding(c1,  4,  6, 1, inPlace=True)
    >>> repeat.insertRepeatEnding(c1, 11, 13, 2, inPlace=True)

    We now have 8 repeatBrackets since each part gets its own first and second ending.

    >>> repeatBrackets = c1.flat.getElementsByClass(spanner.RepeatBracket)
    >>> len(repeatBrackets)
    8
    >>> len(c1.parts[0].getElementsByClass(spanner.RepeatBracket))
    2
    '''
    
    if not inPlace:
        s = copy.deepcopy(s)
        
    if s == None:
        return None #or raise an exception!

    
    if not s.hasMeasures():
        for part in s.parts:
            insertRepeatEnding(part, start, end, endingNumber, inPlace=True)
        if inPlace:
            return
        else:
            return s
    
    measures = [ s.measure(i) for i in range(start, end+1) ]
    rb = spanner.RepeatBracket(measures, number=endingNumber)
    rbOffset = measures[0].getOffsetBySite(s)   #adding repeat bracket to stream at beginning of repeated section.  
                                                #Maybe better at end?
    s.insert(rbOffset, rb)
    
    if inPlace is True:
        return
    else:
        return s


def insertRepeat(s, start, end, inPlace=False):
    '''
    Given a stream s, inserts a start-repeat at the beginning of the 
    bar specified by start and inserts an end-repeat at the bar specified
    by barEnd. Only alters the stream s if inPlace=True. 
    
    
    >>> from copy import deepcopy
    >>> chorale1 = corpus.parse('bwv10.7.mxl')
    >>> s = repeat.insertRepeat(chorale1, 3, 6, inPlace=False)
    >>> m4 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
    >>> resm4 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
    >>> m6 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
    >>> resm6 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
    >>> m7 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
    >>> resm7 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
    >>> m4 == resm4
    True
    >>> m6 == resm6
    True
    >>> m7 == resm7
    True
    
    We should have 2 repeats in each part (a start and end) for a total of 8 repeats
    
    >>> len(s.parts[0].flat.getElementsByClass(bar.Repeat))
    2
    >>> len(s.flat.getElementsByClass(bar.Repeat))
    8
    >>> s.parts[0].measure(3).leftBarline.direction
    'start'
    >>> s.parts[0].measure(6).rightBarline.direction
    'end'
    
    '''
    
    if s is None:
        return None
    
    if not inPlace:
        s = copy.deepcopy(s)
    
    if not s.hasMeasures():
        for part in s.parts:
            insertRepeat(part, start, end, True)
        if inPlace:
            return
        else:
            return s
            
    from music21 import bar
    s.measure(end).rightBarline = bar.Repeat(direction='end', times=2)
    
    #Place a starting repeat, if needed
    if start != 1 or RepeatFinder(s).getQuarterLengthOfPickupMeasure() != 0:
        s.measure(start).leftBarline = bar.Repeat(direction='start')
        
    if inPlace:
        return
    else:
        return s

def deleteMeasures(s, toDelete, inPlace=False):
    '''
    Given a stream s and a list of numbers, toDelete, removes each measure with a number
    corresponding to a number in toDelete and then renumbers the remaining measures in the stream.
            
    
    
    >>> from copy import deepcopy
    >>> chorale1 = corpus.parse('bwv10.7.mxl')
    >>> s = deepcopy(chorale1)
    >>> repeat.deleteMeasures(s, [6, 3, 4], inPlace=True)
    >>> m2 = search.translateStreamToString( chorale1.parts[1].measure(2).notesAndRests)
    >>> resm2 = search.translateStreamToString( s.parts[1].measure(2).notesAndRests)
    >>> m2 == resm2
    True
    >>> m5 = search.translateStreamToString( chorale1.parts[1].measure(5).notesAndRests)
    >>> resm3 = search.translateStreamToString( s.parts[1].measure(3).notesAndRests)
    >>> m5 == resm3
    True
    >>> m7 = search.translateStreamToString( chorale1.parts[1].measure(7).notesAndRests)
    >>> resm4 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
    >>> m7 == resm4
    True
    >>> lenS = len(s.parts[0].getElementsByClass(stream.Measure))
    >>> lenChorale1 = len(chorale1.parts[0].getElementsByClass(stream.Measure))
    >>> lenS + 3 == lenChorale1
    True
    
    OMIT_FROM_DOCS
    >>> chorale2 = corpus.parse('bwv101.7.mxl')
    >>> s = deepcopy(chorale2)
    >>> repeat.deleteMeasures(s, [3, 4, 5], True)
    >>> m2 = search.translateStreamToString( chorale2.parts[0].measure(2).notesAndRests)
    >>> resm2 = search.translateStreamToString( s.parts[0].measure(2).notesAndRests)
    >>> m3 = search.translateStreamToString( chorale2.parts[0].measure(3).notesAndRests)
    >>> m6 = search.translateStreamToString( chorale2.parts[0].measure(6).notesAndRests)
    >>> resm3 = search.translateStreamToString( s.parts[0].measure(3).notesAndRests)
    >>> m2 == resm2
    True
    >>> resm3 == m3
    False
    >>> resm3 == m6
    True
    >>> chorale3 = corpus.parse('bwv102.7.mxl')
    >>> s = repeat.deleteMeasures(chorale3, [2, 3])
    >>> len(s.parts[2].getElementsByClass(stream.Measure)) == len(chorale3.parts[2].getElementsByClass(stream.Measure)) - 2
    True
    >>> s = repeat.deleteMeasures(chorale3, [2, 3])
    >>> len(s.parts[2].getElementsByClass(stream.Measure)) == len(chorale3.parts[2].getElementsByClass(stream.Measure)) - 2
    True
    >>> s = repeat.deleteMeasures(chorale3, [999, 1001001])
    >>> len(s.parts[2]) == len(chorale3.parts[2])
    True
    
    '''
    
    if s is None:
        return None
    
    if not inPlace:
        s = copy.deepcopy(s)
    
    if s.hasMeasures():
        for mNumber in toDelete:
            try:
                removeMe = s.measure(mNumber)
            except exceptions21.Music21Exception: # More specific?
                removeMe = None
                
            if removeMe is not None:
                s.remove( removeMe )
    else:
        for part in s.parts:
            deleteMeasures(part, toDelete, inPlace=True)
        if inPlace:
            return
        else:
            return s
    
    #correct the measure numbers
    measures = s.getElementsByClass("Measure")
    if len(measures) is not 0:
        i = measures[0].number
        
        #if we deleted the first measure...  TODO: test this case
        if i is not 0 and i is not 1:
            i = 1   #can simplify to one line with above.
        
        for measure in measures:
            measure.number = i
            i += 1
    
    if inPlace:
        return
    else:
        return s 


# from musicxml
# Dacapo indicates to go back to the beginning of the movement. When used it always has the value "yes".
# 	
# Segno and dalsegno are used for backwards jumps to a segno sign; coda and tocoda are used for forward jumps to a coda sign.

# By default, a dalsegno or dacapo attribute indicates that the jump should occur the first time through, while a  tocoda attribute indicates the jump should occur the second time through. The time that jumps occur can be changed by using the time-only attribute.

# finale defines:

# d.c. al fine: da capo al fine: go back to beginnig and repeat complete or up to word fine
# d.c. al coda: da capo al coda: repeat from beginning to an indicated place and then play the tail part; two coda symbols are used

# d.s. al fine: da segno al fine: go back to segno, and play until fine
# d.s. al coda: go back to segno, then when al coda is reached, jump to coda
# to coda #
# fine
# coda sign: circle symbol with cross
# segno
# go to measure number




class ExpanderException(exceptions21.Music21Exception):
    pass

class Expander(object):
    '''
    The Expander object can expand a single Part or Part-like Stream with repeats. Nested 
    repeats given with :class:`~music21.bar.Repeat` objects, or 
    repeats and sections designated with 
    :class:`~music21.repeat.RepeatExpression` objects, are all expanded.

    This class is a utility processor. Direct usage is more commonly 
    from the :meth:`~music21.stream.Stream.expandRepeats` method.

    To use this object directly, call :meth:`~music21.repeat.Expander.process` on the
    score
    
    >>> s = converter.parse('tinynotation: 3/4 A2. C4 D E F2.')
    >>> s.makeMeasures(inPlace = True)
    >>> s.measure(2).leftBarline = bar.Repeat(direction='start')
    >>> s.measure(2).rightBarline = bar.Repeat(direction='end', times=3)
    >>> s.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note A>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.bar.Repeat direction=start>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Repeat direction=end times=3>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.0} <music21.note.Note F>
        {3.0} <music21.bar.Barline style=final>

    >>> e = repeat.Expander(s)
    >>> e.repeatBarsAreCoherent()
    True
    >>> s2 = e.process()
    >>> s2.show('text') 
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note A>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.bar.Barline style=double>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Barline style=double>
    {6.0} <music21.stream.Measure 2 offset=6.0>
        {0.0} <music21.bar.Barline style=double>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Barline style=double>
    {9.0} <music21.stream.Measure 2 offset=9.0>
        {0.0} <music21.bar.Barline style=double>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Barline style=double>
    {12.0} <music21.stream.Measure 3 offset=12.0>
        {0.0} <music21.note.Note F>
        {3.0} <music21.bar.Barline style=final>

    OMIT_FROM_DOCS
    
    TODO: Note bug: barline style = double for each!  Clefs and TimesSignatures should only be in first one!

    Test empty expander:
    
    >>> e = repeat.Expander()

    '''
    def __init__(self, streamObj = None):
        self._src = streamObj
        self._repeatBrackets = None
        if streamObj is not None:
            self._setup()
    
    def _setup(self):
        '''
        run several setup routines.
        '''    
        # get and store the source measure count; this is presumed to
        # be a Stream with Measures
        self._srcMeasureStream = self._src.getElementsByClass('Measure')
        # store all top-level non Measure elements for later insertion
        self._srcNotMeasureStream = self._src.getElementsNotOfClass('Measure')

        # see if there are any repeat brackets
        self._repeatBrackets = self._src.flat.getElementsByClass(
                   'RepeatBracket')

        self._srcMeasureCount = len(self._srcMeasureStream)
        if self._srcMeasureCount == 0:
            raise ExpanderException('no measures found in the source stream to be expanded')

        # store counts of all non barline elements.
        # doing class matching by string as problems matching in some test cases
        reStream = self._srcMeasureStream.flat.getElementsByClass(
                   'RepeatExpression')
        self._codaCount = len(reStream.getElementsByClass('Coda'))
        self._segnoCount = len(reStream.getElementsByClass('Segno'))
        self._fineCount = len(reStream.getElementsByClass('Fine'))

        self._dcCount = len(reStream.getElementsByClass('DaCapo'))
        self._dcafCount = len(reStream.getElementsByClass('DaCapoAlFine'))
        self._dcacCount = len(reStream.getElementsByClass('DaCapoAlCoda'))

        self._asCount = len(reStream.getElementsByClass('AlSegno'))
        self._dsCount = len(reStream.getElementsByClass('DalSegno'))
        self._dsafCount = len(reStream.getElementsByClass('DalSegnoAlFine'))
        self._dsacCount = len(reStream.getElementsByClass('DalSegnoAlCoda'))

    def process(self, deepcopy=True):
        '''
        This is the main call for Expander
        
        Processes all repeats. Note that this processing only 
        happens for Measures contained in the given Stream. 
        Other objects in that Stream are neither processed nor copied. 

        if deepcopy is False then it will leave the stream in a unusual state, but acceptable if
        the source stream has already been deepcopied and will be discarded later
        '''
        if not self.isExpandable():
            raise ExpanderException('cannot expand Stream: badly formed repeats or repeat expressions')

        # need to copy source measures, as may later measures before copying
        # them, and this can result in orphaned spanners
        if deepcopy is not False:
            srcStream = copy.deepcopy(self._srcMeasureStream) 
        else:
            srcStream = self._srcMeasureStream
        # these must by copied, otherwise we have the original still
        self._repeatBrackets = copy.deepcopy(self._repeatBrackets)

        #srcStream = self._srcMeasureStream
        # after copying, update repeat brackets (as spanners)
        for m in srcStream:
            # processes uses the spanner bundle stored on this Stream
            self._repeatBrackets.spannerBundle.replaceSpannedElement(
                id(m.derivation.origin), m)

        #srcStream = self._srcMeasureStream
        #post = copy.deepcopy(self._srcMeasureStream)
        hasDaCopoOrSegno = self._daCapoOrSegno()
        # will deep copy
        if hasDaCopoOrSegno is None:
            post = self._processRecursiveRepeatBars(srcStream)
        else: # we have a segno or capo
            post = self._processRepeatExpressionAndRepeats(srcStream)        

        # TODO: need to copy spanners from each sub-group into their newest conects; must be done here as more than one connection is made

        return post

    def measureMap(self, returnType='index'):
        '''
        returns a list where for each measure in the expanded stream, the index of the measure in the original
        stream is given.  if returnType = 'measureNumber' then the str(measureNumber) of the original instead of the
        index of the original is used -- suffixes are important here for endings etc..
        
        Inefficient, because the entire stream is expanded before making this call, rather than just seeing
        what needs to be expanded and returning that.
        
        
        >>> s = converter.parse('tinynotation: 3/4 A2.  C4 D E   F2.    G4 a b   c2.')
        >>> s.makeMeasures(inPlace = True)
        >>> s.measure(2).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(2).rightBarline = bar.Repeat(direction='end', times=3)
        >>> s.measure(4).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(4).rightBarline = bar.Repeat(direction='end', times=2)
        >>> e = repeat.Expander(s)
        >>> e.measureMap()
        [0, 1, 1, 1, 2, 3, 3, 4]
        >>> e.measureMap(returnType='measureNumber')
        ['1', '2', '2', '2', '3', '4', '4', '5']        
        '''
        measureNumberList = []
        post = self.process()
        
        #if post.hasPartlikeStreams:
        #    measureContainingStreams = post.parts[0]
        #else:
        # apparently the object works only on a part anyhow...
        measureContainingStreams = post
        
        for i, m in enumerate(measureContainingStreams.getElementsByClass('Measure')):
            measureNumberList.append(m.measureNumberWithSuffix())
        
        if returnType == 'measureNumber':
            return measureNumberList
        
        measureNumberDict = {}
        for i, m in enumerate(self._srcMeasureStream):
            measureNumberDict[m.measureNumberWithSuffix()] = i
            # could be overwritten if the same measureNumber is used multiple times...

        indexList = []
        for measureNumberWithSuffix in measureNumberList:
            indexList.append(measureNumberDict[measureNumberWithSuffix])
        return indexList
        

    def _stripRepeatBarlines(self, m, newStyle='double'):
        '''
        Given a measure, strip barlines if they are repeats, and 
        replace with Barlines that are of the same style. Modify in place.
        '''
        # bar import repeat to make Repeat inherit from RepeatMark
        from music21 import bar
        lb = m.leftBarline
        rb = m.rightBarline
        if lb is not None and 'Repeat' in lb.classes:
            #environLocal.printDebug(['inserting new barline: %s' % newStyle])
            m.leftBarline = bar.Barline(newStyle)
        if rb is not None and 'Repeat' in rb.classes:
            m.rightBarline = bar.Barline(newStyle)

    def _stripRepeatExpressions(self, streamObj):
        '''
        Given a Stream of measures or a Measure, strip all RepeatExpression 
        objects in place.
        '''
        if not streamObj.hasMeasures():
            # it probably is a measure; place in temporary containers
            mList = [streamObj]
        else:
            mList = streamObj.getElementsByClass('Measure')
        for m in mList:
            remove = []
            for e in m.getElementsByClass('RepeatExpression'):
                remove.append(e)
            for e in remove:
                m.remove(e)

    def repeatBarsAreCoherent(self):
        '''
        Check that all repeat bars are paired properly. Returns True or False
        '''
        startCount = 0
        endCount = 0
        countBalance = 0
        for m in self._srcMeasureStream:
            lb = m.leftBarline
            rb = m.rightBarline
            
            if lb is not None and 'Repeat' in lb.classes:
                if lb.direction == 'start':
                    startCount += 1
                    countBalance += 1
                # ends may be encountered on left of bar
                elif lb.direction == 'end':
                    if countBalance == 0: # the first repeat found
                        startCount += 1 # simulate first
                        countBalance += 1 # simulate first
                    endCount += 1
                    countBalance -= 1
            if rb is not None and 'Repeat' in rb.classes:
                if rb.direction == 'end':
                    # if this is the first of all repeats found, then we
                    # have an acceptable case where the first repeat is omitted
                    if countBalance == 0: # the first repeat found
                        startCount += 1 # simulate first
                        countBalance += 1 # simulate first
                    endCount += 1
                    countBalance -= 1
                else:
                    raise ExpanderException('a right barline is found that cannot be processed: %s, %s' % (m, rb))
        if countBalance != 0:
            environLocal.printDebug(['Repeats are not balanced: countBalance: %s' % (countBalance)])
            return False
        if startCount != endCount:
            environLocal.printDebug(['start count not the same as end count: %s / %s' % (startCount, endCount)])
            return False
        #environLocal.printDebug(['matched start and end repeat barline count of: %s/%s' % (startCount, endCount)])
        return True


    def _daCapoOrSegno(self):
        '''
        Return a DaCapo object if this piece uses any form of DaCapo; return 
        a Segno object if this piece uses any form of Segno. Returns None if 
        incoherent or the piece uses neither.
        
        '''
        sumDc = self._dcCount + self._dcafCount + self._dcacCount
        # for now, only accepting one segno
        sumDs = (self._dsCount + self._dsacCount + 
                self._dsafCount + self._asCount)
        #environLocal.printDebug(['_daCapoOrSegno', sumDc, sumDs])
        if sumDc == 1 and sumDs == 0:
            return DaCapo
        elif sumDs == 1 and sumDc == 0:
            return Segno
        else:
            return None
        
    def _getRepeatExpressionCommandType(self):
        '''
        Return the class of the repeat expression command. This should 
        only be called if it has been determine that there is one 
        repeat command in this Stream.
        '''
        if self._dcCount == 1:
            return 'DaCapo'
        elif self._dcacCount == 1:
            return 'DaCapoAlCoda'
        elif self._dcafCount == 1:
            return 'DaCapoAlFine'
        elif self._asCount == 1:
            return 'AlSegno'
        elif self._dsCount == 1:
            return 'DalSegno'
        elif self._dsacCount == 1:
            return 'DalSegnoAlCoda'
        elif self._dsafCount == 1:
            return 'DalSegnoAlFine'
        else:
            raise ExpanderException('no repeat command found')
    
    def _getRepeatExpressionCommand(self, streamObj):
        '''Get the instance found in this stream; assumes that there is one.
        '''
        return streamObj.flat.getElementsByClass('RepeatExpressionCommand')[0]

    def _daCapoIsCoherent(self):
        '''Check of a DC statement is coherent.
        '''
        # there can be only one da capo statement for the provided span
        sumDc = self._dcCount + self._dcafCount + self._dcacCount
        if sumDc > 1:
            return False

        # if dc, there can be no codas
        if self._dcCount == 1 and self._codaCount == 0:
            #environLocal.printDebug(['returning true on dc'])
            return True

        # if we have a da capo al fine, must have one fine
        elif self._dcafCount == 1 and self._fineCount == 1:
            #environLocal.printDebug(['returning true on dcaf'])
            return True

        # if we have a da capo al coda, must have two coda signs
        elif self._dcacCount == 1 and self._codaCount == 2:
            #environLocal.printDebug(['returning true on dcac'])
            return True

        # return false for all other cases
        return False
        

    def _dalSegnoIsCoherent(self):
        '''Check of a sa segno statement is coherent.
        '''
        # there can be only one da segno statement for the provided span
        sumDs = (self._asCount + self._dsCount + self._dsacCount + 
                self._dsafCount)
        if sumDs > 1:
            return False

        # if al segno, there can be no codas, and one segno
        if (self._asCount == 1 and self._segnoCount == 1 and 
            self._codaCount == 0):
            #environLocal.printDebug(['returning true on as'])
            return True

        if (self._dsCount == 1 and self._segnoCount == 1 and 
            self._codaCount == 0):
            #environLocal.printDebug(['returning true on ds'])
            return True

        # if we have a da capo al fine, must have one fine
        elif (self._dsafCount == 1 and self._codaCount == 0 and 
            self._segnoCount == 1 and self._fineCount == 1):
            #environLocal.printDebug(['returning true on dsaf'])
            return True

        # if we have a da capo al coda, must have two coda signs
        elif (self._dsacCount == 1 and self._codaCount == 2 and 
            self._segnoCount == 1 and self._fineCount == 0):
            #environLocal.printDebug(['returning true on dsac'])
            return True

        # return false for all other cases
        return False
        



    def _groupRepeatBracketIndices(self, streamObj):
        '''
        Return a list of dictionaries that contains two 
        entries: one for all indices that are involved with 
        a collection of repeat bracket, and the repeat brackets 
        themselves.

        This is used to handle when there are more than 
        one group of repeat brackets per Stream. 

        
        >>> s = converter.parse('tinynotation: 3/4 A2.  C4 D E   F2.    G4 a b   c2.')
        >>> s.makeMeasures(inPlace = True)
        >>> s.measure(2).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(2).rightBarline = bar.Repeat(direction='end', times=3)
        >>> s.measure(4).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(4).rightBarline = bar.Repeat(direction='end', times=2)
        >>> e = repeat.Expander(s)
        
        Does nothing, because only searching for repeatBrackets, not repeat signs.  Need a better test.
        
        >>> from pprint import pprint as pp
        >>> pp(e._groupRepeatBracketIndices(s))
        [{'measureIndices': [], 'repeatBrackets': []}]
        ''' 
        groups = []
        mEnumerated = [x for x in enumerate(streamObj)]

        # use known self._repeatBrackets and correlate with indices
        # store numbers to find when we have a new group
        foundRBNumbers = []
        groupIndices = {'repeatBrackets':[], 'measureIndices':[]}
        i = 0
        #for i in range(len(streamObj)):
        while i < len(streamObj):
            m = streamObj[i]
            #shiftedIndex = False
            for rb in self._repeatBrackets:
                #environLocal.printDebug(['_groupRepeatBracketIndices', rb])
                #match = False
                if rb.isFirst(m): # for this rb, is this the first measures
                    if rb.getNumberList()[0] in foundRBNumbers:
                        # we have a new group
                        groups.append(groupIndices)
                        foundRBNumbers = []
                        groupIndices = {'repeatBrackets':[], 'measureIndices':[]}
                    # store rb numbers to monitor when we are in a new group
                    foundRBNumbers += rb.getNumberList() # concat list
                    #groupIndices['measureIndices'].append(i)
                    # need to jump to the index of the last measure this 
                    # rb contains; need to add indices for measures found within
                    groupIndices['repeatBrackets'].append(rb)
                    mLast = rb.getLast()
                    for iSub, mSub in mEnumerated:
                        # when we are at or higher index then our 
                        # current context
                        # need to include
                        if iSub >= i and id(mSub) != id(mLast): 
                            groupIndices['measureIndices'].append(iSub)
                        elif id(mLast) == id(mSub): # add last
                            groupIndices['measureIndices'].append(iSub)
                            # cannot skip ahead here b/c looking for overlaps
                            # as error checking
                            #i = iSub + 1 # go to next index in outer loop
                            #shiftedIndex = True
                            #match = True
                            break
#                 if match:
#                     break
            #if not shiftedIndex:
            i += 1
        if len(groupIndices) > 0:
            groups.append(groupIndices)
        return groups



    def _repeatBracketsAreCoherent(self):
        '''Check if repeat brackets are coherent.

        This must be done for each group of brackets, not for the entire Stream.
        '''
        for group in self._groupRepeatBracketIndices(self._srcMeasureStream):
            # get for each group and look at one at a time.

            rBrackets = group['repeatBrackets']
            #environLocal.printDebug(['_repeatBracketsAreCoherent', "group['measureIndices']",  group['measureIndices']])
            #environLocal.printDebug(['_repeatBracketsAreCoherent', "group['repeatBrackets']",  group['repeatBrackets']])

            # the numbers must be consecutive
            if len(rBrackets) == 0:
                return True
            # accept if any single repeat bracket        
            if len(rBrackets) == 1:
                pass
            elif len(rBrackets) > 1:
                # spanner numbers must be in order, integers, and consecutive
                target = []
                for rb in rBrackets:
                    # number here may be a string 1,2
                    # get number list will return inclusive values; i.e., 
                    # 1,3 will
                    # return 1, 2, 3
                    target += rb.getNumberList()
                match = list(range(1, max(target)+1)) # max of target + 1
                if match != target:
                    environLocal.printDebug(['repeat brackets are not numbered consecutively: %s, %s' % (match, target)])
                    return False
            # there needs to be repeat after each bracket except the last
            spannedMeasureIds = []
            for rbCount, rb in enumerate(rBrackets):
                #environLocal.printDebug(['rbCount', rbCount, rb])
                # get the last, which is a measure, see if it has a repeat
                m = rb.getLast()
                # check that they do not overlap: look at all components (starts
                # and ends) and make sure that none have been found already
                for m in rb.getSpannedElements():
                    if id(m) in spannedMeasureIds:
                        environLocal.printDebug(['found overlapping repeat brackets'])
                        return False
                    spannedMeasureIds.append(id(m))
                # check the right bar while iterating
                rightBar = m.rightBarline
                if rightBar is None or 'Repeat' not in rightBar.classes:
                    # all but the last must have repeat bars; except if we just
                    # have one bracket or the last
                    if (len(rBrackets) == 1 or 
                        rbCount < len(rBrackets) - 1):
                        environLocal.printDebug(['repeat brackets are not terminated with a repeat barline'])
                        return False
        return True


    def _hasRepeat(self, streamObj):
        '''
        Return True if this Stream of Measures has a repeat 
        pair still to process.
        '''
        #environLocal.printDebug(['hasRepeat', streamObj])
        for i in range(len(streamObj)):
            m = streamObj[i]
            lb = m.leftBarline
            rb = m.rightBarline

            # this does not check for well-balanced formations, 
            # only presence
            if (lb is not None and 'Repeat' in lb.classes):
                return True
            if (rb is not None and 'Repeat' in rb.classes and 
                rb.direction == 'end'):
                return True
        return False

    
    def _findInnermostRepeatIndices(self, streamObj):
        '''
        Find the innermost repeat bars. Return raw index values.
        For a single measure, this could be [2]
        For many contiguous measures, this might be [2, 3, 4, 5]

        The provided Stream must be a Stream only of Measures. 

        
        >>> s = converter.parse('tinynotation: 3/4 A2.  C4 D E   F2.    G4 a b   c2.')
        >>> s.makeMeasures(inPlace = True)
        >>> s.measure(2).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(2).rightBarline = bar.Repeat(direction='end', times=3)
        >>> s.measure(4).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(4).rightBarline = bar.Repeat(direction='end', times=2)
        >>> e = repeat.Expander(s)
        >>> e._findInnermostRepeatIndices(s)
        [1]
        
        >>> s.measure(2).rightBarline = None
        >>> s.measure(4).leftBarline = None
        >>> e2 = repeat.Expander(s)
        >>> e2._findInnermostRepeatIndices(s)
        [1, 2, 3]
        '''
        # need to find only the first open and closed pair
        startIndices = []
        # use index values instead of an interator
        for i in range(len(streamObj)):
            # iterate through each measure
            m = streamObj[i]
            try:
                lb = m.leftBarline
                rb = m.rightBarline
            except AttributeError:
                continue # probably not a measure

            if lb is not None and 'Repeat' in lb.classes: 
                if lb.direction == 'start':
                    startIndices.append(i)
                # an end may be placed on the left barline; of the next measuer
                # meaning that we only want up until the previous
                elif lb.direction == 'end':
                    #environLocal.printDebug(['found an end in left barline: %s' % lb])
                    if len(startIndices) == 0:
                        # get from first to this one
                        barRepeatIndices = range(0, i)
                        break
                    else: # otherwise get the last start index
                        barRepeatIndices = range(startIndices[-1], i)
                        break
            if (rb is not None and 'Repeat' in rb.classes and 
                rb.direction == 'end'):
                # if this is the first end found and no starts found, 
                # assume we are counting from zero
                if len(startIndices) == 0: # get from first to this one
                    barRepeatIndices = range(0, i+1)
                    break
                else: # otherwise get the last start index
                    barRepeatIndices = range(startIndices[-1], i+1)
                    break
        return list(barRepeatIndices)


    def _getEndRepeatBar(self, streamObj, index):
        '''
        Get the last measure to be processed in the repeat, 
        as well as the measure that has the end barline. 
        These may not be the same: if an end repeat bar is 
        placed on the left of a measure that is not actually 
        being copied. 


        The `index` parameter is the index of the last 
        measure to be copied. The streamObj must only have Measures. 
        '''
        mLast = streamObj[index]
        rb = mLast.rightBarline
        # if right barline of end is a repeat
        if (rb is not None and 'Repeat' in rb.classes and 
            rb.direction == 'end'):
            mEndBarline = mLast # they are the same
            repeatTimes = rb.times
        else:
            # try the next measure
            if index >= len(streamObj) - 1:
                raise ExpanderException('cannot find an end Repeat bar after the given end: %s' % index)

            mEndBarline = streamObj[index+1]
            lb = mEndBarline.leftBarline
            if (lb is not None and 'Repeat' in lb.classes and 
                lb.direction == 'end'):
                repeatTimes = lb.times
            else:
                raise ExpanderException('cannot find an end Repeat bar in the expected position')
        # the default is 2 times, or 1 repeat
        if repeatTimes is None:
            repeatTimes = 2
        return mLast, mEndBarline, repeatTimes


    def processInnermostRepeatBars(self, streamObj, repeatIndices=None, 
        repeatTimes=None, returnExpansionOnly=False):
        '''
        Process and return a new Stream of Measures, likely a Part.

        If `repeatIndices` are given, only these indices will be copied. 
        All inclusive indices must be listed, not just the start and end.

        If `returnExpansionOnly` is True, only the expanded portion is 
        returned, the rest of the Stream is not retained.
        
        
        >>> s = converter.parse('tinynotation: 3/4 A2.  C4 D E   F2.    G4 a b   c2.')
        >>> s.makeMeasures(inPlace = True)
        >>> s.measure(2).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(2).rightBarline = bar.Repeat(direction='end', times=3)
        >>> s.measure(4).leftBarline = bar.Repeat(direction='start')
        >>> s.measure(4).rightBarline = bar.Repeat(direction='end', times=2)

        processInnermostRepeatBars only will expand the first time.
        
        >>> e = repeat.Expander(s)
        >>> s2 = e.processInnermostRepeatBars(s)
        >>> s2.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note A>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.bar.Barline style=double>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.bar.Barline style=double>
        {6.0} <music21.stream.Measure 2 offset=6.0>
            {0.0} <music21.bar.Barline style=double>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.bar.Barline style=double>
        {9.0} <music21.stream.Measure 2 offset=9.0>
            {0.0} <music21.bar.Barline style=double>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.bar.Barline style=double>
        {12.0} <music21.stream.Measure 3 offset=12.0>
            {0.0} <music21.note.Note F>
        {15.0} <music21.stream.Measure 4 offset=15.0>
            {0.0} <music21.bar.Repeat direction=start>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note B>
            {3.0} <music21.bar.Repeat direction=end times=2>
        {18.0} <music21.stream.Measure 5 offset=18.0>
            {0.0} <music21.note.Note C>
            {3.0} <music21.bar.Barline style=final>
        
        Calling it again does the trick..., as _processRecursiveRepeatBars does
        
        >>> s3 = e.processInnermostRepeatBars(s2)
        >>> s3.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
        ...
        {3.0} <music21.stream.Measure 2 offset=3.0>
        ...
        {6.0} <music21.stream.Measure 2 offset=6.0>
        ...
        {9.0} <music21.stream.Measure 2 offset=9.0>
        ...
        {12.0} <music21.stream.Measure 3 offset=12.0>
        ...
        {15.0} <music21.stream.Measure 4 offset=15.0>
            {0.0} <music21.bar.Barline style=double>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note B>
            {3.0} <music21.bar.Barline style=double>
        {18.0} <music21.stream.Measure 4 offset=18.0>
            {0.0} <music21.bar.Barline style=double>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note B>
            {3.0} <music21.bar.Barline style=double>
        {21.0} <music21.stream.Measure 5 offset=21.0>
        ...
        '''
        # get class from src
        new = streamObj.__class__()

        # can provide indices
        forcedIndices = False
        if repeatIndices is None:
            # find innermost
            repeatIndices = self._findInnermostRepeatIndices(streamObj)
        else: # use passed
            forcedIndices = True
        #environLocal.printDebug(['got new repeat indices:', repeatIndices])

        # renumber measures starting with the first number found here
#         number = streamObj[0].number
#         if number is None:
#             number = 1
        # handling of end repeat as left barline
        stripFirstNextMeasure = False
        # use index values instead of an interator
        i = 0
        while i < len(streamObj):
            #environLocal.printDebug(['processing measure index:', i, 'repeatIndices', repeatIndices])
            # if this index is the start of the repeat
            if i == repeatIndices[0]:
                mEndBarline = None
                mLast = None
                try:
                    mLast, mEndBarline, repeatTimesFound = self._getEndRepeatBar(streamObj, repeatIndices[-1])
                except ExpanderException: 
                    # this may fail if we have supplied arbitrary repeat indices
                    if not forcedIndices:
                        raise # raise error
                    # otherwise let pass; mLast is mEndBarline, as we want
                    
                if repeatTimes is None: # if not passed as arg
                    repeatTimes = repeatTimesFound

                for times in range(repeatTimes):
                    #environLocal.printDebug(['repeat times:', times])    
                    # copy the range of measures; this will include the first
                    # always copying from the same source
                    for j in repeatIndices:
                        mSub = copy.deepcopy(streamObj[j])
                        # must do for each pass, b/c not changing source
                        # stream
                        #environLocal.printDebug(['got j, repeatIndicies', j, repeatIndices])
                        if j in [repeatIndices[0], repeatIndices[-1]]:
                            self._stripRepeatBarlines(mSub)
                        #mSub.number = number
                        # only keep repeat expressions found at the end  
                        # only remove anything if we have 2 or more repeats
                        # and this is not the last time 
                        if repeatTimes >= 2 and times < repeatTimes - 1: 
                            self._stripRepeatExpressions(mSub)
                        new.append(mSub)
                        # renumber at end
                        #number += 1
                # check if need to clear repeats from next bar
                if mLast is not mEndBarline:
                    stripFirstNextMeasure = True
                # set i to next measure after mLast
                i = repeatIndices[-1] + 1
            # if is not in repeat indicies, just add this measure
            else:
                # iterate through each measure, always add first
                if not returnExpansionOnly:
                    # TODO: this deepcopy is necessary to avoid a problem in 
                    # testExpandRepeatH; the copy is not actually used, but
                    # for some reason removes an id clash when inserting into
                    # new
                    junk = copy.deepcopy(streamObj[i])
                    # cannot deepcopy here, as we might orphan a spanner
                    # attached to bracket after this repeat segment
                    m = streamObj[i]
                    #environLocal.printDebug(['about to insert m into new', 'id(m)', id(m), 'new', id(new), 'all ids:', [id(e) for e in new]])
                        #m = copy.deepcopy(streamObj[i])
                        #new.show('t')
                    if stripFirstNextMeasure:
                        #environLocal.printDebug(['got stripFirstNextMeasure'])
                        self._stripRepeatBarlines(m)
                        # change in source too
                        self._stripRepeatBarlines(streamObj[i])
                        stripFirstNextMeasure = False
                    # renumber at end
                    #m.number = number
                    new.append(m) # this may be the first version
                #number += 1
                i += 1
        # return the complete stream with just the expanded measures
        return new



    def _processInnermostRepeatsAndBrackets(self, streamObj, 
        repeatBracketsMemo=None):
        '''
        Return a new complete Stream with repeats and brackets 
        expanded.

        The `repeatBracketsMemo` is a dictionary that stores 
        id(rb): rb entries for all RepeatBrackets.

        This is not recursively applied here, but done in __processRecursiveRepeatBars
        '''
        if repeatBracketsMemo == None:
            repeatBracketsMemo = {}

        # possible replace calls to above with this
        
        # need to remove groups that are already used
        groups = self._groupRepeatBracketIndices(streamObj)
        # if we do not groups when expected it is probably b/c spanners have
        # been orphaned
        #environLocal.printDebug(['got groups:', groups])   
        if len(groups) == 0: # none found:
            return self.processInnermostRepeatBars(streamObj)

        # need to find innermost repeat, and then see it it has any
        # repeat brackets that are relevant for the span
        # this group may ultimately extend beyond the innermost, as this may
        # be the first of a few brackets
        innermost = self._findInnermostRepeatIndices(streamObj)
        groupFocus = None # find a group to apply to, or None
        for group in groups:
            rBrackets = group['repeatBrackets']
            mStart = streamObj[innermost[0]]
            mEnd = streamObj[innermost[-1]]
            for rb in rBrackets:
                if id(rb) in repeatBracketsMemo:
                    #environLocal.printDebug(['skipping rb as in memo keys:', rb])   
                    break # do not need to look at components         
                elif rb.hasSpannedElement(mStart) or rb.hasSpannedElement(mEnd):
                    #environLocal.printDebug(['matched rb as component' ])
                    groupFocus = group
                    break
                else:
                    pass
                    #environLocal.printDebug(['rb does not have measure as a spanned element', 'rb', rb, 'mEnd', mEnd])
            if groupFocus is not None:
                break

        # if the innermost measures are not part of a group, process normally
        if groupFocus is None:
            #environLocal.printDebug(['cannot find innermost in a group:', 'innermost', innermost, 'groupFocus', groupFocus])
            return self.processInnermostRepeatBars(streamObj)
        else: # have innermost in a bracket
            rBrackets = groupFocus['repeatBrackets']
            # get all measures before bracket
            streamObjPre = streamObj[:innermost[0]]
            streamBracketRepeats = [] # store a list

            # will need to know index of last measure copied
            highestIndexRepeated = None

            # store for each rb {repeatBracket:[], validIndices=[]}
            boundaries = [] 
            # it is critical that the brackets are in order as presented
            for rb in rBrackets:
                repeatBracketsMemo[id(rb)] = rb
                startIndex = innermost[0]
                # first measure under spanner is not the start index, but the
                # measure that begins the spanned repeat bracket
                mFirst = rb.getFirst() 
                mLast = rb.getLast()
                endIndex = None
                bracketStartIndex = None # not the startIndex
                # iterate over all provided measures to find the last index
                for i, m in enumerate(streamObj):
                    if id(m) == id(mLast):
                        endIndex = i
                    # use if: start and end may be the same
                    if id(m) == id(mFirst):
                        bracketStartIndex = i
                # error check: probably orphaned spanners
                if endIndex is None or bracketStartIndex is None:
                    raise ExpanderException('failed to find start or end index of bracket expansion')

                # if mLast does not have a repeat bar, its probably not a repeat
                mLastRightBar = mLast.rightBarline
                if (mLastRightBar is not None and 'Repeat' in     
                    mLastRightBar.classes):
                    indices = list(range(startIndex, endIndex+1))
                # condition of when to repeat next is not always clear
                # if we have  [1 x :|[2 x | x still need to repeat
                else: 
                    indices = list(range(startIndex, endIndex+1))
                    #indices = None # mark as not for repeating
                # get bracket indices
                bracketIndices = list(range(bracketStartIndex, endIndex+1))
                # remove last found bracket indices from next indices to copy
                if indices is not None:
                    # go over all past if bracketIndicies and remove
                    for data in boundaries:
                        for q in data['bracketIndices']:
                            if q in indices:
                                indices.remove(q)

                data = {'repeatBracket':rb, 'validIndices':indices, 
                        'bracketIndices':bracketIndices}
                boundaries.append(data)

            for data in boundaries:
                #environLocal.printDebug(['processing data bundle:', data])

                # each number in a racket corresponds to one or more repeat
                # find indices to process and times based on repeat brackets

                # TODO: need to pass parameter to keep opening repeat until
                # are at the last repeat under this bracket
                if data['validIndices'] is not None:
                    # repeat times is the number of elements in the list
                    repeatTimes = len(data['repeatBracket'].getNumberList())
                    # just get the expanded section
                    #streamObj.show('t')
                    out = self.processInnermostRepeatBars(streamObj,     
                           repeatIndices=data['validIndices'], repeatTimes=repeatTimes, 
                           returnExpansionOnly=True) 
                    #environLocal.printDebug(['got bracket segment:', [n.name for n in out.flat.pitches]])
                    streamBracketRepeats.append(out)
                    # highest index will always be the last copied, up until end
                    highestIndexRepeated = max(data['validIndices'])

            new = streamObj.__class__()
            for m in streamObjPre:
                new.append(m)
            for sub in streamBracketRepeats:
                for m in sub:
                    self._stripRepeatBarlines(m)
                    new.append(m)
            # need 1 more than highest measure counted
            streamObjPost = streamObj[highestIndexRepeated+1:]
            for m in streamObjPost:
                new.append(m)
            return new

        raise ExpanderException('condition for inner expansion not caught')


    def getRepeatExpressionIndex(self, streamObj, target):
        '''
        Return a list of index positions of a Measure given a 
        stream of measures. This requires the provided stream 
        to only have measures. 
        
        
        >>> s = converter.parse('tinynotation: 3/4 A2. C4 D E F2.')
        >>> s.makeMeasures(inPlace = True)
        >>> s.measure(3).append(repeat.Segno())
        >>> e = repeat.Expander()
        
        getRepeatExpressionIndex returns the measureIndex not measure number
        
        >>> e.getRepeatExpressionIndex(s.getElementsByClass('Measure'), 'Segno')
        [2]
        '''
        post = []
        for i, m in enumerate(streamObj):
            for e in m.getElementsByClass('RepeatExpression'):
                if target in e.classes or (
                        not isinstance(target, str) and isinstance(e, target)):
                    post.append(i)
        # if not found
        if len(post) > 0: 
            return post            
        return None
            


    def isExpandable(self):
        '''
        Return True or False if this Stream is expandable, that is, 
        if it has balanced repeats or sensible da copo or dal segno
        indications. 
        '''
        match = self._daCapoOrSegno()
        # if neither repeats nor segno/capo, than not expandable
        if match is None and not self._hasRepeat(self._srcMeasureStream):
            environLocal.printDebug('no dc/segno, no repeats')
            return False

        if not self.repeatBarsAreCoherent():
            environLocal.printDebug('repeat bars not coherent')
            return False

        if not self._repeatBracketsAreCoherent():
            environLocal.printDebug('repeat brackets are not coherent')
            return False

        if match is not None:
            if match == DaCapo:
                if not self._daCapoIsCoherent():
                    environLocal.printDebug('dc not coherent')
                    return False
            elif match == Segno:
                if not self._dalSegnoIsCoherent():
                    environLocal.printDebug('ds not coherent')
                    return False            
        return True



    def _processRecursiveRepeatBars(self, streamObj, makeDeepCopy = False):
        '''
        Recursively expand any number of nested repeat bars. 
        Will also expand all repeat brackets.
        
        if makeDeepCopy is True, then it will make a deepcopy of the stream.  Otherwise
        assumes it has already been done.
        '''
        # this assumes just a stream of measures
        # assume already copied
        if makeDeepCopy is True:
            streamObj = copy.deepcopy(streamObj)
        repeatBracketsMemo = {} # store completed brackets
        
        maxProcesses = 100 # safety check
        while maxProcesses > 0:
            maxProcesses = maxProcesses - 1
            #environLocal.printDebug(['process(): top of loop'])
            #post.show('t')
            #post = self.processInnermostRepeatBars(post)
            streamObj = self._processInnermostRepeatsAndBrackets(streamObj, repeatBracketsMemo=repeatBracketsMemo)

            #post.show('t')
            if self._hasRepeat(streamObj):   
                pass                     
                #environLocal.printDebug(['process() calling: self._findInnermostRepeatIndices(post)', self._findInnermostRepeatIndices(post)])
            else:
                break # nothing left to process
        return streamObj


    def _processRepeatExpressionAndRepeats(self, streamObj):
        '''
        Process and return a new Stream of Measures, likely a Part.
        Expand any repeat expressions found within.
        '''
        # should already be a stream of measures
        # assume already copied
        capoOrSegno = self._daCapoOrSegno()
        recType = self._getRepeatExpressionCommandType() # a string form
        recObj = self._getRepeatExpressionCommand(streamObj)
        jumpBack = self.getRepeatExpressionIndex(streamObj, recType)[0]

        # start position is dependent on capo or segno
        if capoOrSegno is DaCapo:
            start = 0
        elif capoOrSegno is Segno:
            start = self.getRepeatExpressionIndex(streamObj, 'Segno')[0]

        # this is either fine or the end
        if recType in ['DaCapoAlFine', 'DalSegnoAlFine']:
            end = self.getRepeatExpressionIndex(streamObj, 'Fine')[0]
        else:
            end = len(streamObj) - 1
        #environLocal.printDebug(['got end/fine:', end])

        # coda jump/start
        if recType in ['DaCapoAlCoda', 'DalSegnoAlCoda']:
            # there must always be two coda symbols; the jump and start
            codaJump = self.getRepeatExpressionIndex(streamObj, 'Coda')[0]
            codaStart = self.getRepeatExpressionIndex(streamObj, 'Coda')[1]
        else:
            codaJump = None
            codaStart = None

        # store segments of measure indices to build
        # expand repeats for sections later
        indexSegments = []
        # get from begining to jump back
        indexSegments.append([0, jumpBack])    
        # get from post-jump start to 
        if recType in ['DaCapoAlCoda', 'DalSegnoAlCoda']:
            # if there is a coda, then start to coda jump, coda to end
            indexSegments.append([start, codaJump])    
            indexSegments.append([codaStart, len(streamObj) - 1])    
        else: # no coda (fine or normal end), get start to end
            indexSegments.append([start, end])    

        # process measures
        new = streamObj.__class__()
        # try to start from first number
        number = streamObj[0].number
        if number is None:
            number = 1

        #environLocal.printDebug(['_processRepeatExpressionAndRepeats', 'index segments', indexSegments])
        # recType.repeatAfterJump

        # build segments form the source, copying as necessary, and 
        # expanding repeats
        for subCount, sub in enumerate(indexSegments):
            # 1 is the second group, and is always pre coda
            subStream = streamObj.__class__()
            # get all values inclusive for each range
            for i in range(sub[0], sub[1]+1):
                # great a subgroup
                m = copy.deepcopy(streamObj[i])
                m.number = number
                subStream.append(m)
                number += 1
            if self._hasRepeat(subStream):
                # if we are in the jump section, check setting of repeats after 
                # jump; otherwise, take all repeats
                if subCount == 1 and not recObj.repeatAfterJump:
                    pass
                else:
                    subStream = self._processRecursiveRepeatBars(subStream)
                    # update measure number from last option
                    number = subStream[-1].number + 1 # add for next
                # no matter what, always strip repeat bars
                for m in subStream:
                    self._stripRepeatBarlines(m, newStyle='light-light')

            # add sub to new
            for m in subStream:
                new.append(m)
        # can strip all repeat expressions in place
        self._stripRepeatExpressions(new)
        return new    

    _DOC_ORDER = ['process', 'measureMap']

#----------------------------------------------------------

class UnequalPartsLengthException(exceptions21.Music21Exception):
    pass

class InsufficientLengthException(exceptions21.Music21Exception):
    pass

class NoInternalStreamException(exceptions21.Music21Exception):
    pass


#TODO: change terminology for defaultHash.  It's not really a hash function...
class RepeatFinder(object):
    '''
    An object for finding and simplifying repeated sections of music. Must be passed a stream 
    which contains either measures or parts containing measures.

    To collapse a repeated section, call RepeatFinder.simplify() and to see which sections of a piece 
    are repeated, call either RepeatFinder.getMeasureSimilarityList() or 
    RepeatFinder.getSimilarMeasureGroups (see below for full documentation).
    
    If the internal stream passed to RepeatFinder is altered in any way (e.g. if you call simplify() with inplace=True)
    then to ensure proper functionality, you should use a new RepeatFinder object. 
    
    Below is an example of calling simplify on a Bach chorale.
    
    >>> chorale = corpus.parse('bwv117.4.mxl')
    >>> #_DOCS_SHOW chorale.show()
    
    Only the first 8 bars are displayed

    .. image:: images/repeat-SimplifyExample_Chorale.*
       :width: 600
            
    >>> #_DOCS_SHOW repeat.RepeatFinder(chorale).simplify().show()
    
    The same chorale as before, but simplified
    
    .. image:: images/repeat-SimplifyExample_ChoraleSimplified.*
       :width: 600
    
    '''
    _DOC_ORDER = ['simplify', 'getMeasureSimilarityList', 'getSimilarMeasureGroups', 'getQuarterLengthOfPickupMeasure', 
                  'hasPickup']
        
    _DOC_ATTR = {
                'defaultHash': 'A function that takes a stream of notes and rests and returns a string or an \
                                integer such that two measures are equal if their hashes are equal under the \'==\' operator',
                's': 'The internal stream which is being analyzed for repeated sections'}
    def __init__(self, inpStream=None, defaultMeasureHashFunction=None):
        from music21 import search

        self.s = inpStream
        if defaultMeasureHashFunction is None:
            self.defaultHash = search.translateStreamToString
        else:
            self.defaultHash = defaultMeasureHashFunction
            
        self._mList = None
        self._mGroups = None
        
        #self.quarterLengthOfPickup = None
        #self.hasPickup = None
    
    def getQuarterLengthOfPickupMeasure(self):
        '''
        Looks at RepeatFinder's internal stream and returns the duration of the pickup bar 
        in quarterlengths.  If there is no pickup, returns 0.0. 
        
        Raises an exception if RepeatFinder's internal stream is too short (i.e. fewer than 3 measures long)
        
        
        >>> noPickup = corpus.parse('bwv10.7.mxl')
        >>> repeat.RepeatFinder(noPickup).getQuarterLengthOfPickupMeasure()
        0.0
        >>> #_DOCS_SHOW noPickup.parts[0].measures(0,5).show()
        
        .. image:: images/repeat-rf_noPickup.*
           :width: 600
        
        >>> hasPickup = corpus.parse('bwv101.7.mxl')
        >>> repeat.RepeatFinder(hasPickup).getQuarterLengthOfPickupMeasure()
        1.0
        >>> #_DOCS_SHOW hasPickup.parts[0].measures(0,2).show()
        
        .. image:: images/repeat-rf_hasPickup.*
           :width: 600
            
        >>> tooShort = noPickup.parts[0].measures(1, 2)
        >>> repeat.RepeatFinder(tooShort).getQuarterLengthOfPickupMeasure()
        Traceback (most recent call last):
        InsufficientLengthException: Cannot determine length of pickup given fewer than 3 measures
        
        _OMIT_FROM_DOCS_
        >>> repeat.RepeatFinder().getQuarterLengthOfPickupMeasure()
        Traceback (most recent call last):
        NoInternalStreamException: RepeatFinder must be initialized with a stream
        
        '''            
        if self.s is None:
            raise NoInternalStreamException("RepeatFinder must be initialized with a stream")
        
        if self.s.hasMeasures():
            s2 = self.s
        else:
            s2 = self.s.parts[0]

        
        mOffsets = list(s2.measureOffsetMap().keys())
        mOffsets.sort()
        if len(mOffsets) < 3:
            raise InsufficientLengthException("Cannot determine length of pickup given fewer than 3 measures")
        
        pickup = mOffsets[1]-mOffsets[0]
        normMeasure = mOffsets[2]-mOffsets[1]
        return pickup % normMeasure
        
    def hasPickup(self):
        '''
        Returns True when the RepeatFinder's internal stream has a pickup bar.  
        
        Raises an exception if the internal stream is too short
        (i.e. fewer than 3 bars long).
        
        >>> noPickup = corpus.parse('bwv10.7.mxl')
        >>> repeat.RepeatFinder(noPickup).hasPickup()
        False
        >>> #_DOCS_SHOW noPickup.parts[0].measures(0,5).show()
        
        .. image:: images/repeat-rf_noPickup.*
           :width: 600
            
        >>> hasPickup = corpus.parse('bwv101.7.mxl')
        >>> repeat.RepeatFinder(hasPickup).hasPickup()
        True
        >>> #_DOCS_SHOW hasPickup.parts[0].measures(0,2).show()
        
        .. image:: images/repeat-rf_hasPickup.*
           :width: 600
        
        _OMIT_FROM_DOCS_
        >>> repeat.RepeatFinder(noPickup.parts[0].measures(1, 2)).hasPickup()
        Traceback (most recent call last):
        InsufficientLengthException: Cannot determine length of pickup given fewer than 3 measures
        >>> repeat.RepeatFinder().hasPickup()
        Traceback (most recent call last):
        NoInternalStreamException: RepeatFinder must be initialized with a stream
        '''
        if self.s is None:
            raise NoInternalStreamException("RepeatFinder must be initialized with a stream")
        
        return self.getQuarterLengthOfPickupMeasure() != 0.0
        
    def getMeasureSimilarityList(self):
        '''
        Returns a list mList = [ [2, 3], [3], ... ] such that measures i and j are the same (with i < j) if and only 
        if mList[i] contains j.  NOTE: this function refers to the very first measure as measure 0 regardless of whether
        s starts with measure 0 or 1 (i.e. treats a pickup bar as an entire measure).
        
        For instance, if getMeasureSimilarityList returned [[4], [5], [6], [7,8], [], [], [], [8], []], we would know that the first 
        four measures repeat and the 4th, 8th, and 9th measures are the same.  
        
        Measures are considered the same if the defaultHash maps them to two values which are equal under the '==' operator.
        
        >>> chorales = corpus.getBachChorales()
        >>> chorale = corpus.parse('bwv154.3.mxl')
        >>> repeat.RepeatFinder(chorale).getMeasureSimilarityList()
        [[4], [5], [6], [7, 15], [], [], [], [15], [], [], [], [], [], [], [], []]
        >>> repeat.RepeatFinder(chorale.parts[0]).getMeasureSimilarityList()
        [[4, 12], [5], [6], [7, 15], [12], [], [], [15], [], [], [], [], [], [], [], []]
        >>> chorale2 = corpus.parse('bwv153.5.mxl')
        >>> repeat.RepeatFinder(chorale2).getMeasureSimilarityList()    #bwv153.5 has a pickup
        [[], [5], [6], [7], [], [], [], [], [], [], [], [], [], [], [], [], []]
        >>> hashFunction = lambda m : str(len(m))
        >>> repeat.RepeatFinder(chorale.parts[0].measures(1, 8), defaultMeasureHashFunction=hashFunction).getMeasureSimilarityList()
        [[1, 2, 4, 5, 6], [2, 4, 5, 6], [4, 5, 6], [7], [5, 6], [6], [], []]
        
        _OMIT_FROM_DOCS_
        >>> repeat.RepeatFinder().getMeasureSimilarityList()
        Traceback (most recent call last):
        NoInternalStreamException: RepeatFinder must be initialized with a stream
        '''
        
        if self.s is None:
            raise NoInternalStreamException("RepeatFinder must be initialized with a stream")
        
        if self._mList is not None:
            return self._mList
        
        hashFunction = self.defaultHash

        s = self.s
            
        #Check for different parts and change mlist to a list of
        # measure-streams: [<measures from part1>, <measures from part2>, ... ]
        if s.hasMeasures():
            mlists = [s.getElementsByClass("Measure")]
        else:
            mlists = [ p.getElementsByClass("Measure") for p in s.parts ]
            
        #Check for unequal lengths
        for i in range(len(mlists)-1):
            if len(mlists[i]) != len(mlists[i+1]):
                raise UnequalPartsLengthException("Parts must each have the same number of measures.")
        
        #Change mlist so each element of mlist is a list of hashed measuresg for each measure in a part.  
        #May look something like [['sdlkfj', 'ej2k', 'r9u3kj'...], ['fjk2', '23ijf9', ... ], ... ]
        for i in range(len(mlists)):
            mlists[i] = [hashFunction(mlists[i][j].notesAndRests) for j in range(len(mlists[i]))]
        
        #mlists is now one list for the whole stream, containing a tuple with the hashed measure over each part,
        # i.e. mlists = [(part1_measure1_hash, part2_measure1_hash, ...), (part1_measure2_hash, part2_measure2_hash, ... ), ... ]
        mlists = list(zip(*mlists))
        
        tempDict = {}   #maps the measure-hashes to the lowest examined measure number with that hash.   
        res = []
        
        #initialize res
        for i in range(len(mlists)):
            res.append([])
        
        for i in range(len(mlists)-1, -1, -1):
            #mHash is a the concatenation of the measure i for each part.     
            mHash = ''.join(mlists[i])
            
            if mHash in tempDict:
                #We found a repeated measure 
                res[i].append( tempDict[mHash] )
                res[i].extend( res[tempDict[mHash]] )
                
                #tempDict now stores the earliest known measure with mHash. 
                tempDict[mHash] = i
            else:
                tempDict[mHash] = i
                
        self._mList = res
        return res
                  
    def _getSimiliarMeasuresHelper(self, measures, source, compare, resDict, useDict):
        '''
        Recursive helper function used by getSimilarMeasureGroupsFromList.  
        Should only be called if the "source" measure of a piece is the same as the "compare" measure.
        
        When called, updates resDict such that resDict[(source, compare)] is equal to 
        ( sourceList=[source, source+1, source+2, ...], compareList=[compare, compare+1, compare+2, ...]), where
        measure sourceList[i] is the same as measure compareList[i] 
        
        Inputs: 
        measures -  A list returned from getMeasureSimilarityList.  
        source   -  The measure number which you are considering 
        compare  -  The measure number which is compared to the source measure (this is a repeat of the source measure)
        resDict  -  A dictionary of memoized results where for each key (i,j), there is stored a tuple
                    ([i, i+1, i+2, ...], [j, j+1, j+2, ...]) where measures i and j are equal, measure i+1 and j+1 are equal, and 
                    measures i+2 and j+2 are equal, etc. 
        useDict  -  A dictionary for each input that maps to False if and only if the function calls 
                    the same input m and i. Has the result that if resDict((i, j)) maps to something like ([i, i+1, i+2...], 
                    [j, j+1, j+2, ...]), then useDict(i,j) is only False if resDict(i-1, j-1) is something like ([i-1, i, i+1, ...],
                    [j-1, j, j+1, ..])
        
        See getSimilarMeasureGroupsFromList documentation for tests.
        '''
                
        if (source, compare) in resDict:
            return #resDict[(source, compare)]   
        elif compare+1 in measures[source+1]:  #we have a repeated section at least 2 measures in length; check to see how far it goes
            nextOne = self._getSimiliarMeasuresHelper(measures, source+1, compare+1, resDict, useDict)
            #make sure we don't have overlap
            res = ([source], [compare])
            res[0].extend(nextOne[0])
            res[1].extend(nextOne[1])
            
            if res[0][-1] < res[1][0]:
                #If there is no overlap, then resdict[(source+1, compare+1)] is no longer useful because  
                #the information is already stored in resdict[(source, compare)]
                useDict[(source+1, compare+1)] = False
            else:   
                #truncate the result so we don't have overlap.  (i.e. avoid something like ([1, 2, 3],[2, 3, 4])
                while res[0][-1] >= res[1][0]:
                    res = (res[0][:-1], res[1][:-1])
                
        else:
            res = ([source], [compare])
        
        
        resDict[(source, compare)] = res
        useDict[(source, compare)] = True
        
        return res
    
    def _getSimilarMeasureTuples(self, mList, hasPickup=False):
        '''
        Input is a list formatted as the output described in getMeasureSimilarityList().  
        Output is a list of tuples of the form (l1, l2), where l1 and l2 are lists of measure numbers such that measure l1[i]
        is identical to measure l2[i] and l1[-1] < l2[0]
                
        For all tuples t1 and t2, it is guaranteed that we never have t1.l1 contains t2.l1 or t2.l2 contains t2.l2
                
        >>> mList = [[5, 6], [7], [8], [9], [11, 12], [6, 13], [], [], [], [], [], [12], [], []]
        >>> res1 = repeat.RepeatFinder()._getSimilarMeasureTuples(mList, False)
        >>> ([1, 2, 3, 4], [7, 8, 9, 10]) in res1
        True
        >>> ([1], [6]) in res1
        True
        >>> ([5],[12]) in res1
        True
        >>> ([5, 6], [13, 14]) in res1
        True
        >>> ([6],[7]) in res1
        True
        >>> ([12],[13]) in res1
        True
        >>> len(res1)
        6
        >>> mList = [[], [5, 10], [6, 11], [7, 12], [8, 13], [10], [11], [12], [13], [], [], [], [], []]
        >>> res2 = repeat.RepeatFinder()._getSimilarMeasureTuples(mList, True)
        >>> ([1, 2, 3, 4], [5, 6, 7, 8]) in res2
        True
        >>> ([1, 2, 3, 4], [10, 11, 12, 13]) in res2
        True
        >>> ([5, 6, 7, 8], [10, 11, 12, 13]) in res2
        True
        >>> len(res2)
        3
        
        >>> s = stream.Stream()
        >>> n1 = note.Note('C')
        >>> n2 = note.Note('D')
        >>> n3 = note.Note('E')
        >>> n4 = note.Note('F')
        >>> for i in range(3):
        ...    m = stream.Measure()
        ...    s.append(m)
        ...    m.append(n1)
        ...    m.append(n2)
        ...    m.append(n3)
        ...    m.append(n4)
        >>> res3 = repeat.RepeatFinder()._getSimilarMeasureTuples([[1,2],[2],[]], False)
        >>> ([1], [2]) in res3
        True
        >>> ([2], [3]) in res3
        True
        >>> ([1], [3]) in res3
        True
        >>> len(res3)
        3
        
        >>> s = stream.Stream()
        >>> n1 = note.Note('C')
        >>> n2 = note.Note('D')
        >>> n3 = note.Note('E')
        >>> n4 = note.Note('F')
        >>> for i in range(5):
        ...    m = stream.Measure()
        ...    s.append(m)
        ...    m.append(n1)
        ...    m.append(n2)
        ...    m.append(n3)
        ...    m.append(n4)
        >>> res3 = repeat.RepeatFinder()._getSimilarMeasureTuples([[1,2,3,4],[2,3,4],[3,4],[4],[]], False)
        >>> ([1, 2], [3, 4]) in res3
        True
        >>> ([1, 2], [4, 5]) in res3
        True
        >>> ([2, 3], [4, 5]) in res3
        True
        >>> ([1],[3]) in res3
        False
        >>> ([1],[4]) in res3
        False
        >>> ([1],[5]) in res3
        True
        
        '''        
        pickupCorrection = not hasPickup
        
        res = {}
        useful = {}
        
        for m in range(len(mList)):
            for i in mList[m]:
                self._getSimiliarMeasuresHelper(mList, m, i, res, useful)   #add correct value to res
        
        for k in list(res.keys()):
            if not useful[k]:
                del res[k]  
                        
        realRes = []
        for mTuple in res.values():
            realRes.append( ([i+pickupCorrection for i in mTuple[0]], [j+pickupCorrection for j in mTuple[1]]))
        
        self._mGroups = realRes
        return realRes
            
            
#     """       
#     def _createRepeatsFromSimilarMeasureGroups(self, mGroups, threshold = 4, inPlace=False):
#         '''
#         Returns a stream with a repeat inserted on all instances of adjacent similar measure groups
#         which contain at least enough measures to satisfy the threshold (by default 4).  mGroup is the
#         result of calling getSimilarMeasureGroupsFromlist( getMeasureSimilarityList(s)).
#         i.e. if 4+ measures repeat themselves, this function returns a stream with a repeat sign instead
#         of the second iteration of those measures.
# 
#         
#         >>> from copy import deepcopy
#         >>> chorale1 = corpus.parse(corpus.getBachChorales()[1])
#         >>> rf = repeat.RepeatFinder(chorale1)
#         >>> s = rf._createRepeatsFromSimilarMeasureGroups( [([1, 2, 3, 4], [5, 6, 7, 8])], 4)
#         >>> len(s.parts)
#         4
#         >>> m4 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
#         >>> resm4 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests )
#         >>> m10 = search.translateStreamToString( chorale1.parts[1].measure(10).notesAndRests)
#         >>> resm6 = search.translateStreamToString( s.parts[1].measure(6).notesAndRests)
#         >>> resm10 = search.translateStreamToString( s.parts[1].measure(10).notesAndRests)
#         >>> m4 == resm4
#         True
#         >>> m10 == resm10
#         False
#         >>> m10 == resm6
#         True
#         
#         _OMIT_FROM_DOCS_
#         >>> repeat.RepeatFinder().getMeasureSimilarityList()
#         Traceback (most recent call last):
#         NoInternalStreamException: RepeatFinder must be initialized with a stream
#         
#         >>> s = stream.Stream()
#         >>> n1 = note.Note('C')
#         >>> n2 = note.Note('D')
#         >>> n3 = note.Note('E')
#         >>> n4 = note.Note('F')
#         >>> for i in range(3):
#         ...    m = stream.Measure()
#         ...    s.append(m)
#         ...    m.append(n1)
#         ...    m.append(n2)
#         ...    m.append(n3)
#         ...    m.append(n4)
#         #this isn't finished
#         '''
#          
#          
#         if self.s is None:
#             raise NoInternalStreamException("RepeatFinder must be initialized with a stream")
#            
#         if inPlace:
#             s = self.s
#         else:
#             s = copy.deepcopy(self.s)
#             
#         
#         
#         toRepeat = [] # (measureStart, measureEnd)
#         toDelete = []
#         for mGroup in mGroups:
#             if len( mGroup[0] ) >= threshold and mGroup[0][-1]+1 == mGroup[1][0]:
#                 startBar, endBar = mGroup[0][0], mGroup[0][-1]
#                 
#                 toRepeat.append((startBar, endBar))
#                 toDelete.extend(mGroup[1])
#                 
#                 
#         #think about including this above and scrapping the toRepeat list altogether
#         for startBar, endBar in toRepeat:
#             RepeatFinder(s).insertRepeat(startBar, endBar, True)
#         
#         RepeatFinder(s).deleteMeasures(toDelete, True)
#         
#         if inPlace:
#             return
#         else:
#             return s
#         
#         
#     """
#     
#     """  
#     def insertRepeat(self, barStart, barEnd, inPlace=False):
#         '''
#         Given a stream s, inserts a start-repeat at the beginning of the 
#         bar specified by barStart and inserts an end-repeat at the bar specified
#         by barEnd. Operates on RepeatFinder's internal stream, but only alters this
#         stream if inPlace=True.
#         
#         
#         >>> from copy import deepcopy
#         >>> chorale1 = corpus.parse('bwv10.7.mxl')
#         >>> s = repeat.RepeatFinder(chorale1).insertRepeat(3, 6, inPlace=False)
#         >>> m4 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
#         >>> resm4 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
#         >>> m6 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
#         >>> resm6 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
#         >>> m7 = search.translateStreamToString( chorale1.parts[1].measure(4).notesAndRests)
#         >>> resm7 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
#         >>> m4 == resm4
#         True
#         >>> m6 == resm6
#         True
#         >>> m7 == resm7
#         True
#         >>> len(s.parts[0].flat.getElementsByClass(bar.Repeat))
#         2
#         >>> len(s.flat.getElementsByClass(bar.Repeat))
#         8
#         >>> s.parts[0].measure(3).leftBarline.direction
#         'start'
#         >>> s.parts[0].measure(6).rightBarline.direction
#         'end'
#         
#         '''
#         
#         if self.s is None:
#             raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
#         
#         if inPlace:
#             s = self.s
#         else:
#             s = copy.deepcopy(self.s)
#         
#             
#         if s is None:
#             raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
#         
#         
#         if not s.hasMeasures():
#             for part in s.parts:
#                 insertRepeat(part, barStart, barEnd, True)
#             if inPlace:
#                 return
#             else:
#                 return s
#                 
#         s.measure(barEnd).rightBarline = music21.bar.Repeat(direction='end', times=2)
#         
#         #Place a starting repeat, if needed
#         if RepeatFinder(s).getQuarterLengthOfPickupMeasure() != 0 or barStart != 1:
#             s.measure(barStart).leftBarline = music21.bar.Repeat(direction='start')
#             
#         if inPlace:
#             return
#         else:
#             return s
#             
#     
#     
#     def insertRepeatEnding(self, start, end, endingNumber=1, inPlace=False):
#         '''
#         Inserts a repeated ending (i.e. first or second endings) into stream s, where s either contains measures,
#         or contains parts which contain measures.  Start and end are integers corresponding to the first and last measure
#         number of the "repeatNum" ending.  e.g. if start=4, end=6, and repeatNum=2, we have a second ending
#         from measures 4 to 6.
#                 
#         
#         
#         >>> c1 = corpus.parse('bwv10.7.mxl')
#         >>> repeat.RepeatFinder(c1).insertRepeatEnding( 4, 6, 1, True)
#         >>> repeat.RepeatFinder(c1).insertRepeatEnding( 11, 13, 2, True)
#         >>> repeatBrackets = c1.flat.getElementsByClass(spanner.RepeatBracket)
#         >>> len(repeatBrackets)
#         8
#         >>> len(c1.parts[0].getElementsByClass(spanner.RepeatBracket))
#         2
#         '''
#         
#         if self.s is None:
#             raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
#     
#         if inPlace:
#             s = self.s
#         else:
#             s = copy.deepcopy(self.s)
#             
#         if s is None:
#             raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
# 
#         
#         if not s.hasMeasures():
#             for part in s.parts:
#                 RepeatFinder(part).insertRepeatEnding(start, end, endingNumber, True)
#             if inPlace:
#                 return
#             else:
#                 return s
#         
#         
#         measures = [ s.measure(i) for i in range(start, end+1) ]
#         rb = spanner.RepeatBracket(measures, number=endingNumber)
#         rbOffset = measures[0].getOffsetBySite(s)   #adding repeat bracket to stream at beginning of repeated section.  Maybe better at end?
#         s.insert(rbOffset, rb)
#         
#         if inPlace:
#             return
#         else:
#             return s
# 
#     """
#     """       
#     def _createFirstAndSecondEndingsFromSimilarMeasureGroups(self, mGroups, threshold=3, inPlace=False):
#         '''
#         Returns a stream with first and second endings with repeats substituted in when appropriate.
#         Does not detect sections that are more than 16 measure apart.
#         
#         mGroup is the result of calling getSimilarMeasureGroupsFromlist( SimilarityList(s)).
#         
#         
#     
#         '''
#         
#         #fix this function for inPlace
#         
#         #There might be a way to break this by trying to put a repeated section into where the second ending should go.
#         #i.e. let's not replace the second ending with a repeat
#         
#         if self.s is None:
#             raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
#         
#         if inPlace:
#             s = self.s
#         else:
#             s = copy.deepcopy(self.s)
#         
#         
#         toProcess = [] # (measureStart, measureOfFirstEnding, repeatSignMeasure)
#         toDelete = [] 
#         for mGroup in mGroups:
#             distance = mGroup[1][0] - mGroup[0][-1] - 1
#             maxAcceptableDistance = min(16, len(mGroup[0])/2.0 + 1)  #talk about this line more in documentation
#             if len( mGroup[0] ) >= threshold and distance <= maxAcceptableDistance and distance != 0:
#                 startingBar = mGroup[0][0]
#                 firstEndingBar = mGroup[0][-1]+1
#                 repeatSignBar = mGroup[1][0]-1
#                 
#                 toProcessTuple = (startingBar, firstEndingBar, repeatSignBar)
#                 toProcess.append(toProcessTuple)
#                 toDelete.extend(mGroup[1])
#                 
#              
#         for startingBar, firstEndingBar, repeatSignBar in toProcess:
#             self.insertRepeat(startingBar, repeatSignBar, True)                
#             lengthOfRepeatEnding = repeatSignBar - firstEndingBar + 1
#             lengthOfRepeatedSection = firstEndingBar - startingBar + 1
#             startOfSecondEnding = repeatSignBar + lengthOfRepeatedSection
#             insertRepeatEnding(s, firstEndingBar, repeatSignBar, 1, True)
#             insertRepeatEnding(s, startOfSecondEnding, startOfSecondEnding + lengthOfRepeatEnding, 2, True)
#         
#         self.deleteMeasures(toDelete, True)
#         
#         if inPlace:
#             return
#         else:
#             return s
#         
#             
#     """
#     
#     """
# 
#     def deleteMeasures(self, toDelete, inPlace=False):
#         '''
#         Given a stream s and a list of numbers, toDelete, removes each measure with a number
#         corresponding to a number in toDelete.  Renumbers the remaining measures in the stream.
#                 
#         
#         
#         >>> from copy import deepcopy
#         >>> chorale1 = corpus.parse('bwv10.7.mxl')
#         >>> s = deepcopy(chorale1)
#         >>> repeat.RepeatFinder(s).deleteMeasures([6, 3, 4], inPlace=True)
#         >>> m2 = search.translateStreamToString( chorale1.parts[1].measure(2).notesAndRests)
#         >>> resm2 = search.translateStreamToString( s.parts[1].measure(2).notesAndRests)
#         >>> m2 == resm2
#         True
#         >>> m5 = search.translateStreamToString( chorale1.parts[1].measure(5).notesAndRests)
#         >>> resm3 = search.translateStreamToString( s.parts[1].measure(3).notesAndRests)
#         >>> m5 == resm3
#         True
#         >>> m7 = search.translateStreamToString( chorale1.parts[1].measure(7).notesAndRests)
#         >>> resm4 = search.translateStreamToString( s.parts[1].measure(4).notesAndRests)
#         >>> m7 == resm4
#         True
#         >>> lenS = len(s.parts[0].getElementsByClass(stream.Measure))
#         >>> lenChorale1 = len(chorale1.parts[0].getElementsByClass(stream.Measure))
#         >>> lenS + 3 == lenChorale1
#         True
#         >>> chorale2 = corpus.parse('bwv101.7.mxl')
#         >>> s = deepcopy(chorale2)
#         >>> repeat.RepeatFinder(s).deleteMeasures([3, 4, 5], True)
#         >>> m2 = search.translateStreamToString( chorale2.parts[0].measure(2).notesAndRests)
#         >>> resm2 = search.translateStreamToString( s.parts[0].measure(2).notesAndRests)
#         >>> m3 = search.translateStreamToString( chorale2.parts[0].measure(3).notesAndRests)
#         >>> m6 = search.translateStreamToString( chorale2.parts[0].measure(6).notesAndRests)
#         >>> resm3 = search.translateStreamToString( s.parts[0].measure(3).notesAndRests)
#         >>> m2 == resm2
#         True
#         >>> resm3 == m3
#         False
#         >>> resm3 == m6
#         True
#         >>> chorale3 = corpus.parse('bwv102.7.mxl')
#         >>> s = repeat.RepeatFinder(chorale3).deleteMeasures([2, 3])
#         >>> len(s.parts[2].getElementsByClass(stream.Measure)) == len(chorale3.parts[2].getElementsByClass(stream.Measure)) - 2
#         True
#         >>> s = repeat.RepeatFinder(chorale3).deleteMeasures([2, 3])
#         >>> len(s.parts[2].getElementsByClass(stream.Measure)) == len(chorale3.parts[2].getElementsByClass(stream.Measure)) - 2
#         True
#         >>> s = repeat.RepeatFinder(chorale3).deleteMeasures([999, 1001001])
#         >>> len(s.parts[2]) == len(chorale3.parts[2])
#         True
#         
#         '''
#         
#         if self.s is None:
#             raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
#         
#         if inPlace:
#             s = self.s
#         else:
#             s = copy.deepcopy(self.s)
#         
#             
#             
#         if s.hasMeasures():
#             for mNumber in toDelete:
#                 try:
#                     removeMe = s.measure(mNumber)
#                 except:
#                     removeMe = None
#                     
#                 if removeMe is not None:
#                     s.remove( removeMe )
#         else:
#             for part in s.parts:
#                 deleteMeasures(part, toDelete, inPlace=True)
#             if inPlace:
#                 return
#             else:
#                 return s
#         
#         #correct the measure numbers
#         measures = s.getElementsByClass(music21.stream.Measure)
#         if len(measures) is not 0:
#             i = measures[0].number
#             
#             #if we deleted the first measure...  TODO: test this case
#             if i is not 0 and i is not 1:
#                 i = 1   #can simplify to one line with above.
#             
#             for measure in measures:
#                 measure.number = i
#                 i += 1
#         
#         if inPlace:
#             return
#         else:
#             return s 
#         
#     """
        
        
    def simplify(self, repeatThreshold=4, repeatEndingThreshold=3, inPlace=False):
        '''
        Takes the piece stored in the RepeatFinder object and collapses repeated sections by
        replacing them with repeat signs. Includes first and second endings where appropriate.  
        
        Only detects repeated sections which are repeatThreshold bars long and only detecs repeat endings
        where the repeated sections is more than repeatEndingThreshold bars long. 
        If inPlace is True, does not return a new music21 object, but instead alters the stream passed to
        the RepeatFinder object.
        
        In the below example, we have an 8-measure stream where the last four measures are identical to the
        first four.  
        
        
        >>> s = stream.Stream()
        >>> notes = [note.Note('D'), note.Note('E-'), note.Note('C'), note.Note('B3'),
        ...           note.Note('D'), note.Note('E-'), note.Note('C'), note.Note('B3')]
        >>> for i in range(8):
        ...    m = stream.Measure()
        ...    m.number = i+1
        ...    myNote = notes[i]
        ...    myNote.duration.quarterLength = 4.0
        ...    m.append(myNote)
        ...    s.append(m)
        >>> #_DOCS_SHOW s.show()
        
        
        .. image:: images/repeat-RepeatFinderDSCH.*
            :width: 600
        
        >>> s2 = repeat.RepeatFinder(s).simplify()
        >>> #_DOCS_SHOW s2.show()
        
        
        .. image:: images/repeat-RepeatFinderDSCHsimplified.*
            :width: 600
        
        
        
        OMIT_FROM_DOCS 
        
        >>> chorales = corpus.getBachChorales()
        >>> c1 = corpus.parse('bwv115.6.mxl')    #has a repeated section
        >>> c1simple = repeat.RepeatFinder(c1).simplify()
        >>> m4 = search.translateStreamToString( c1.parts[0].measure(4).notesAndRests)
        >>> m5 = search.translateStreamToString( c1.parts[0].measure(5).notesAndRests)
        >>> m9 = search.translateStreamToString( c1.parts[0].measure(9).notesAndRests)
        >>> resm4 = search.translateStreamToString( c1simple.parts[0].measure(4).notesAndRests)
        >>> resm5 = search.translateStreamToString( c1simple.parts[0].measure(5).notesAndRests)
        >>> m4 == resm4
        True
        >>> m5 == resm5
        False
        >>> m9 == resm5
        True
        >>> initialRepeats = c1.flat.getElementsByClass(bar.Repeat)
        >>> len(initialRepeats)
        0
        >>> resRepeats = c1simple.flat.getElementsByClass(bar.Repeat)
        >>> len(resRepeats)
        4
        
        >>> c2 = corpus.parse('bwv117.4.mxl')
        >>> m3 = search.translateStreamToString( c2.parts[0].measure(3).notesAndRests)
        >>> m6 = search.translateStreamToString( c2.parts[0].measure(6).notesAndRests)
        >>> m9 = search.translateStreamToString( c2.parts[0].measure(9).notesAndRests)
        >>> initialRepeats = c2.flat.getElementsByClass(bar.Repeat)
        >>> initialBrackets = c2.flat.getElementsByClass(spanner.RepeatBracket)
        >>> repeat.RepeatFinder(c2).simplify(inPlace=True)
        >>> resm3 = search.translateStreamToString( c2.parts[0].measure(3).notesAndRests)
        >>> resm6 = search.translateStreamToString( c2.parts[0].measure(6).notesAndRests)
        >>> simplifiedRepeats = c2.flat.getElementsByClass(bar.Repeat)
        >>> simplifiedBrackets = c2.flat.getElementsByClass(spanner.RepeatBracket)
        >>> m3 == resm3
        True
        >>> m6 == resm6
        False
        >>> m9 == resm6
        True
        >>> len(initialRepeats)
        0
        >>> len(initialBrackets)
        0
        >>> len(simplifiedRepeats)
        8
        >>> len(simplifiedBrackets)
        8
        
        >>> s = stream.Stream()
        >>> for i in range(1, 6):
        ...    m = stream.Measure()
        ...    s.append(m)
        ...    m.number = i
        ...    m.append(note.Note('D'))
        ...    m.append(note.Note('E-'))
        ...    m.append(note.Note('C'))
        ...    m.append(note.Note('B3'))
        >>> s2 = repeat.RepeatFinder(s).simplify(repeatThreshold = 2)
        >>> len(s2.getElementsByClass(stream.Measure))
        3
        >>> len(s2.flat.getElementsByClass(bar.Repeat))
        1
        '''
        mList = self.getMeasureSimilarityList()
        mGroups = self._getSimilarMeasureTuples(mList, self.hasPickup())
        
        processed = {}
        
        # Want to give priority first to the longest repeated sections, and then to the repeated sections that happen earlier.  
        # We sort the tuples of mGroups accordingly  
#         def myComp(x,y):
#             if len(x[0]) != len(y[0]):
#                 return len(y[0])-len(x[0])
#             elif x[0][0] != y[0][0]:
#                 return x[0][0]-y[0][0]
#             else:
#                 return x[1][0] - y[1][0]

        mGroups = sorted(mGroups, key=lambda x: (-1 * len(x[0]), x[0][0], x[1][0]))
            
        #mGroups = sorted(mGroups, cmp=myComp)
        
        if inPlace:
            s = self.s
        else:
            s = copy.deepcopy(self.s)
            
        if s is None:
            raise NoInternalStreamException("This function only works when RepeatFinder is initialized with a stream")
        
        repeatEndingBars = [] # (measureStart, measureOfFirstEnding, repeatSignMeasure)
        toDelete = []
        repeatBars = []  
        for mGroup in mGroups:
            
            #make sure we haven't already processed these measures
            alreadyProcessed = False
            measureNumbers = [x for x in mGroup[0]]
            measureNumbers.extend(mGroup[1])
            for mNum in measureNumbers:
                if mNum in processed:
                    alreadyProcessed = True
                    break
            if alreadyProcessed:
                continue
                
            distance = mGroup[1][0] - mGroup[0][-1] - 1
            maxAcceptableDistance = min(16, len(mGroup[0])/2.0 + 1)  #talk about this line more in documentation
            
            if len( mGroup[0] ) >= repeatThreshold and distance == 0:
                startBar, endBar = mGroup[0][0], mGroup[0][-1]
                
                repeatBars.append((startBar, endBar))
                toDelete.extend(mGroup[1])
                                
            elif len( mGroup[0] ) >= repeatEndingThreshold and distance <= maxAcceptableDistance and distance > 0:
                startingBar = mGroup[0][0]
                firstEndingBar = mGroup[0][-1]+1
                repeatSignBar = mGroup[1][0]-1
                
                toProcessTuple = (startingBar, firstEndingBar, repeatSignBar)
                repeatEndingBars.append(toProcessTuple)
                toDelete.extend(mGroup[1])
            else:
                continue
            
            #only add the measure numbers to the list of processed measures if those measures were actually part of a repeat or repeat ending
            for mNum in measureNumbers:
                processed[mNum] = True
        
        for startingBar, firstEndingBar, repeatSignBar in repeatEndingBars:
            #print startingBar, firstEndingBar, repeatSignBar
            insertRepeat(s, startingBar, repeatSignBar, True)                
            lengthOfRepeatEnding = repeatSignBar - firstEndingBar + 1
            lengthOfRepeatedSection = firstEndingBar - startingBar + 1
            startOfSecondEnding = repeatSignBar + lengthOfRepeatedSection
            insertRepeatEnding(s, firstEndingBar, repeatSignBar, 1, True)
            insertRepeatEnding(s, startOfSecondEnding, startOfSecondEnding + lengthOfRepeatEnding, 2, True)
            
        for startBar, endBar in repeatBars:            
            insertRepeat(s, startBar, endBar, True)
        
        #might want to look at stream._removeOrExpand and stream._fixMeasureNumbers
        deleteMeasures(s, toDelete, True)
        
        if inPlace:
            return
        else:
            return s

    def getSimilarMeasureGroups(self, threshold=1):
        '''
        Returns a list of tuples containing information on repeated groups of measures.  
        
        Specifically, returns a list of tuples of the form (l1, l2) where l1 and l2 are lists
        of measure numbers such that measure l1[i] is the same as measure l2[i].
        
        >>> chorale = corpus.parse('bwv117.4.mxl')
        >>> #_DOCS_SHOW chorale.show()
    
        Measures 1-3 are the same as measures 4-6.  

        .. image:: images/repeat-SimplifyExample_Chorale.*
           :width: 600
        
        >>> repeat.RepeatFinder(chorale).getSimilarMeasureGroups()
        [([1, 2, 3], [5, 6, 7])]
        
        Notice that although measures 2-3 are the same as measures 6-7, we
        don't have ([2, 3], [6, 7]) in our result, since ([1, 2, 3], [5, 6, 7])
        already contains that information.
        
        '''
        #see if we've already done this computation
        if self._mGroups is None:
            if self._mList is None:
                mList = self.getMeasureSimilarityList()
            else:
                mList = self._mList
            mGroups = self._getSimilarMeasureTuples(mList, self.hasPickup())
        else:
            mGroups = self._mGroups
            
        mGroups = [x for x in mGroups if len(x[0]) >= threshold]    #only want long enough measure groups
            
        #sort them giving first priority to larger groups, then to groups that occur earlier
#         def aGoodOrder(x,y):
#             if len(x[0]) != len(y[0]):
#                 return len(y[0])-len(x[0])
#             elif x[0][0] != y[0][0]:
#                 return x[0][0]-y[0][0]
#             else:
#                 return x[1][0] - y[1][0]
            
        #mGroups = sorted(mGroups, cmp=aGoodOrder)
        mGroups = sorted(mGroups, key=lambda x: (-1 * len(x[0]), x[0][0], x[1][0]))
        return mGroups
            

#-------------------------------------------------------------------------------


class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testFilterByRepeatMark(self):
        from music21 import stream, bar, repeat, note

        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        self.assertEqual(len(m1.getElementsByClass('RepeatMark')), 2)

        m2 = stream.Measure()
        m2.leftBarline = bar.Repeat(direction='start')
        m2.rightBarline = bar.Repeat(direction='end', times=2)
        m2.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)

        #s.show()

        # now have 4
        self.assertEqual(len(s.flat.getElementsByClass('RepeatMark')), 4)

        # check coherance
        ex = repeat.Expander(s)
        self.assertEqual(ex.repeatBarsAreCoherent(), True)
        self.assertEqual(ex._findInnermostRepeatIndices(s), [0])



    def testRepeatCoherenceB(self):
        from music21 import stream, bar, repeat, note

        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        #m3.rightBarline = bar.Repeat(direction='end', times=2)
        m3.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)
        s.append(m3)

        # check coherance: will raise
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)
        self.assertEqual(ex._findInnermostRepeatIndices(s), [0])


    def testRepeatCoherenceB2(self):
        from music21 import stream, bar, repeat, note

        # a nested repeat; acceptable
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        #m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()
        m2.leftBarline = bar.Repeat(direction='start')
        #m2.rightBarline = bar.Repeat(direction='end', times=2)
        m2.repeatAppend(note.Note('b3', quarterLength=1), 4)

        m3 = stream.Measure()
        #m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end', times=2)
        m3.repeatAppend(note.Note('d4', quarterLength=1), 4)

        m4 = stream.Measure()
        #m4.leftBarline = bar.Repeat(direction='start')
        m4.rightBarline = bar.Repeat(direction='end', times=2)
        m4.repeatAppend(note.Note('f4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)
        s.append(m3)
        s.append(m4)

        #s.show()

        # check coherance
        ex = repeat.Expander(s)
        self.assertEqual(ex.repeatBarsAreCoherent(), True)
        self.assertEqual(ex._findInnermostRepeatIndices(s), [1, 2])

        post = ex.process()
        #post.show()
        self.assertEqual(len(post.getElementsByClass('Measure')), 12)
        self.assertEqual(len(post.flat.notesAndRests), 48)
        self.assertEqual([m.offset for m in post.getElementsByClass('Measure')], [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 44.0])

        self.assertEqual([n.nameWithOctave for n in post.flat.getElementsByClass('Note')], ['G3', 'G3', 'G3', 'G3', 'B3', 'B3', 'B3', 'B3', 'D4', 'D4', 'D4', 'D4', 'B3', 'B3', 'B3', 'B3', 'D4', 'D4', 'D4', 'D4', 'F4', 'F4', 'F4', 'F4', 'G3', 'G3', 'G3', 'G3', 'B3', 'B3', 'B3', 'B3', 'D4', 'D4', 'D4', 'D4', 'B3', 'B3', 'B3', 'B3', 'D4', 'D4', 'D4', 'D4', 'F4', 'F4', 'F4', 'F4'])



    def testRepeatCoherenceC(self):
        '''Using da capo/dal segno
        '''
        from music21 import stream, repeat

        # no repeats
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)    

        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(DaCapo())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)    

        # missing segno
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(DalSegno())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)    

        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m2.append(Segno())
        m3 = stream.Measure()
        m3.append(DalSegno())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)    

        # dc al fine
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m2.append(Fine())
        m3 = stream.Measure()
        m3.append(DaCapoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)    

        # dc al fine but missing fine
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(DaCapoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)    

        # ds al fine
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(Segno())
        m2 = stream.Measure()
        m2.append(Fine())
        m3 = stream.Measure()
        m3.append(DalSegnoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)    

        # ds al fine missing fine
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(Segno())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(DalSegnoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)    

        # dc al coda
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(Coda())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(Coda())
        m3.append(DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)    

        # dc al coda missing one of two codas
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(Coda())
        m3.append(DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)   

        # ds al coda 
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(Segno())
        m1.append(Coda())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(Coda())
        m3.append(DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)   
        #ex._processRepeatExpression(s, s)




    def testExpandRepeatA(self):
        from music21 import stream, bar, repeat, note

        # two repeat bars in a row
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end')
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()
        m2.leftBarline = bar.Repeat(direction='start')
        m2.rightBarline = bar.Repeat(direction='end')
        m2.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)

        ex = repeat.Expander(s)
        post = ex.process()

        self.assertEqual(len(post.getElementsByClass('Measure')), 4)
        self.assertEqual(len(post.flat.notesAndRests), 16)
        self.assertEqual([m.offset for m in post.getElementsByClass('Measure')], [0.0, 4.0, 8.0, 12.0])

        self.assertEqual([n.nameWithOctave for n in post.flat.getElementsByClass('Note')], ['G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4'])



        # two repeat bars with another bar in between
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end')
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('f3', quarterLength=1), 4)

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end')
        m3.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)
        s.append(m3)
        #s.show('t')

        ex = repeat.Expander(s)
        post = ex.process()

        self.assertEqual(len(post.getElementsByClass('Measure')), 5)
        self.assertEqual(len(post.flat.notesAndRests), 20)
        self.assertEqual([m.offset for m in post.getElementsByClass('Measure')], [0.0, 4.0, 8.0, 12.0, 16.0])
        self.assertEqual([n.nameWithOctave for n in post.flat.getElementsByClass('Note')], ['G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'F3', 'F3', 'F3', 'F3', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4'])

        #post.show('t')
        #post.show()
        

    def testExpandRepeatB(self):
        from music21.abcFormat import testFiles
        from music21 import converter, repeat
        
        s = converter.parse(testFiles.draughtOfAle)
        #s.show()
        self.assertEqual(s.parts[0].getElementsByClass('Measure').__len__(), 18)
        self.assertEqual(s.metadata.title, '"A Draught of Ale"    (jig)     0912')
        self.assertEqual(len(s.flat.notesAndRests), 88)

        #s.show()
        unused_ex = repeat.Expander(s.parts[0])
        # check boundaries here

        post = s.expandRepeats()
        self.assertEqual(post.parts[0].getElementsByClass('Measure').__len__(), 36)
        # make sure metadata is copied
        self.assertEqual(post.metadata.title, '"A Draught of Ale"    (jig)     0912')
        self.assertEqual(len(post.flat.notesAndRests), 88 * 2)

        #post.show()


    def testExpandRepeatC(self):
        from music21.abcFormat import testFiles
        from music21 import converter, repeat
        
        s = converter.parse(testFiles.kingOfTheFairies)
        self.assertEqual(s.parts[0].getElementsByClass('Measure').__len__(), 26)
        self.assertEqual(s.metadata.title, 'King of the fairies')
        self.assertEqual(len(s.flat.notesAndRests), 145)

        #s.show()
        ex = repeat.Expander(s.parts[0])
        self.assertEqual(ex._findInnermostRepeatIndices(s.parts[0].getElementsByClass('Measure')), [0, 1, 2, 3, 4, 5, 6, 7, 8])
        # check boundaries here

        # TODO: this is not yet correct, and is making too many copies
        post = s.expandRepeats()
        self.assertEqual(post.parts[0].getElementsByClass('Measure').__len__(), 35)
        # make sure metadata is copied
        self.assertEqual(post.metadata.title, 'King of the fairies')
        self.assertEqual(len(post.flat.notesAndRests), 192)

        #post.show()


    def testExpandRepeatD(self):
        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note

        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.rightBarline = bar.Repeat(direction='end')
        self.assertEqual(m2.rightBarline.location, 'right')

        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('b-4', type='half'), 2)
    
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        self.assertEqual(len(s.flat.notes), 8)
        post = s.expandRepeats()
        self.assertEqual(len(post.getElementsByClass('Measure')), 6)
        self.assertEqual(len(post.flat.notes), 12)


    def testExpandRepeatE(self):
        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note

        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.leftBarline = bar.Repeat(direction='start')
        rb = bar.Repeat(direction='end')
        m2.rightBarline = rb
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
    
        s = stream.Part()
        s.append([m1, m2, m3])

        self.assertEqual(len(s.flat.notes), 6)
        self.assertEqual(len(s.getElementsByClass('Measure')), 3)

        # default times is 2, or 1 repeat
        post = s.expandRepeats()
        self.assertEqual(len(post.flat.notes), 8)
        self.assertEqual(len(post.getElementsByClass('Measure')), 4)

        # can change times
        rb.times = 1 # one is no repeat
        post = s.expandRepeats()
        self.assertEqual(len(post.flat.notes), 6)
        self.assertEqual(len(post.getElementsByClass('Measure')), 3)

        rb.times = 0 # removes the entire passage
        post = s.expandRepeats()
        self.assertEqual(len(post.flat.notes), 4)
        self.assertEqual(len(post.getElementsByClass('Measure')), 2)

        rb.times = 4
        post = s.expandRepeats()
        self.assertEqual(len(post.flat.notes), 12)
        self.assertEqual(len(post.getElementsByClass('Measure')), 6)



    def testExpandRepeatF(self):
        # an algorithmic generation approach
        import random
        from music21 import bar, note, stream, meter
        
        dur = [.125, .25, .5, .125]
        durA = dur
        durB = dur[1:] + dur[:1]
        durC = dur[2:] + dur[:2]
        durD = dur[3:] + dur[:3]
        
        s = stream.Stream()
        repeatHandles = []
        for dur in [durA, durB, durC, durD]:
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature('1/4')
            for d in dur:
                m.append(note.Note(quarterLength=d))
                m.leftBarline = bar.Repeat(direction='start')
                rb = bar.Repeat(direction='end')
                m.rightBarline = rb
                m.makeBeams(inPlace=True)
                repeatHandles.append(rb)
            s.append(m)
        
        final = stream.Stream()
        # alter all repeatTimes values, expand, and append to final
        for i in range(6):
            for rb in repeatHandles:
                rb.times = random.choice([0,1,3])    
            expanded = s.expandRepeats()
            for m in expanded:
                final.append(m)
        #final.show()    
            


    def testExpandRepeatG(self):        
        from music21.abcFormat import testFiles
        from music21 import converter
        
        unused_s = converter.parse(testFiles.hectorTheHero)
        # TODO: this file does not import correctly due to first/secon
        # ending issues
        #s.show()


    def testExpandRepeatH(self):
        # an algorithmic generation approach

        from music21 import bar, note, stream, meter, pitch
        from music21 import features
        
        dur = [.125, .25, .5, .125]
        repeatTimesCycle = [0, 1, 3, 5]
        pitches = [pitch.Pitch(p) for p in ['a2', 'b-3', 'a2', 'a2']]
        
        s = stream.Stream()
        repeatHandles = []
        for i in range(8):
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature('1/4')
            for j, p in enumerate(pitches):
                m.append(note.Note(p.transpose(i*3), quarterLength=dur[j]))
            m.leftBarline = bar.Repeat(direction='start')
            rb = bar.Repeat(direction='end')
            rb.times = repeatTimesCycle[i%len(repeatTimesCycle)]
            te = rb.getTextExpression()
            m.rightBarline = rb
            m.append(te)
            m.makeBeams(inPlace=True)
            repeatHandles.append(rb) # store for annoation
            s.append(m)
        
        self.assertEqual(len(s), 8)
        self.assertEqual(str(s.flat.pitches[0]), 'A2')
            
        self.assertEqual(features.vectorById(s, 'p20'), [1.0, 0.333333333333333333333, 0.0, 1.0, 0.3333333333333333333, 0.0, 1.0, 0.3333333333333333, 0.0, 1.0, 0.333333333333333333333, 0.0])
        self.assertEqual([x.nameWithOctave for x in s.flat.pitches], ['A2', 'B-3', 'A2', 'A2', 'C3', 'D-4', 'C3', 'C3', 'E-3', 'F-4', 'E-3', 'E-3', 'F#3', 'G4', 'F#3', 'F#3', 'A3', 'B-4', 'A3', 'A3', 'C4', 'D-5', 'C4', 'C4', 'E-4', 'F-5', 'E-4', 'E-4', 'F#4', 'G5', 'F#4', 'F#4'])
        #s.show()    
        
        s1 = s.expandRepeats()
        #s1.show()

        self.assertEqual(len(s1), 18)            
        # first bar is an A, but repeat is zero, will be removed
        self.assertEqual(str(s1.flat.pitches[0]), 'C3')
        
        self.assertEqual(features.vectorById(s1, 'p20'), [0.2, 0.06666666666666666, 0.0, 0.6, 0.2, 0.0, 1.0, 0.3333333333333333333333, 0.0, 0.0, 0.0, 0.0])
        
        self.assertEqual([x.nameWithOctave for x in s1.flat.pitches], ['C3', 'D-4', 'C3', 'C3', 'E-3', 'F-4', 'E-3', 'E-3', 'E-3', 'F-4', 'E-3', 'E-3', 'E-3', 'F-4', 'E-3', 'E-3', 'F#3', 'G4', 'F#3', 'F#3', 'F#3', 'G4', 'F#3', 'F#3', 'F#3', 'G4', 'F#3', 'F#3', 'F#3', 'G4', 'F#3', 'F#3', 'F#3', 'G4', 'F#3', 'F#3', 'C4', 'D-5', 'C4', 'C4', 'E-4', 'F-5', 'E-4', 'E-4', 'E-4', 'F-5', 'E-4', 'E-4', 'E-4', 'F-5', 'E-4', 'E-4', 'F#4', 'G5', 'F#4', 'F#4', 'F#4', 'G5', 'F#4', 'F#4', 'F#4', 'G5', 'F#4', 'F#4', 'F#4', 'G5', 'F#4', 'F#4', 'F#4', 'G5', 'F#4', 'F#4'])

        
        #s1.show()


    def testRepeatExpressionValidText(self):
        from music21 import repeat
        rm = repeat.Coda()
        self.assertEqual(rm.isValidText('coda'), True)
        self.assertEqual(rm.isValidText('Coda'), True)
        self.assertEqual(rm.isValidText('TO Coda'), True)
        self.assertEqual(rm.isValidText('D.C.'), False)

        rm = repeat.Segno()
        self.assertEqual(rm.isValidText('segno  '), True)
        self.assertEqual(rm.isValidText('segNO  '), True)
        
        rm = repeat.Fine()
        self.assertEqual(rm.isValidText('FINE'), True)
        self.assertEqual(rm.isValidText('fine'), True)
        self.assertEqual(rm.isValidText('segno'), False)

        rm = repeat.DaCapo()
        self.assertEqual(rm.isValidText('DC'), True)
        self.assertEqual(rm.isValidText('d.c.'), True)
        self.assertEqual(rm.isValidText('d. c.   '), True)
        self.assertEqual(rm.isValidText('d. c. al capo'), False)


        rm = repeat.DaCapoAlFine()
        self.assertEqual(rm.isValidText('d.c. al fine'), True)
        self.assertEqual(rm.isValidText('da capo al fine'), True)

        rm = repeat.DaCapoAlCoda()
        self.assertEqual(rm.isValidText('da capo al coda'), True)

        rm = repeat.DalSegnoAlFine()
        self.assertEqual(rm.isValidText('d.s. al fine'), True)
        self.assertEqual(rm.isValidText('dal segno al fine'), True)

        rm = repeat.DalSegnoAlCoda()
        self.assertEqual(rm.isValidText('d.s. al coda'), True)
        self.assertEqual(rm.isValidText('dal segno al coda'), True)


    def testRepeatExpressionOnStream(self):
        from music21 import stream, repeat, meter, converter
        from music21.musicxml import m21ToString

        template = stream.Stream()
        for i in range(5):
            m = stream.Measure()
            template.append(m)
        s = copy.deepcopy(template)
        s[3].insert(0, repeat.DaCapo())
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapo)), 1)


        raw = m21ToString.fromMusic21Object(s)

        self.assertEqual(raw.find('Da Capo') > 0, True)

        # can do the same thing starting form a text expression
        s = copy.deepcopy(template)
        s[0].timeSignature = meter.TimeSignature('4/4')
        s[3].insert(0, expressions.TextExpression('da capo'))
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapo)), 0)
        
        raw = m21ToString.fromMusic21Object(s)
        self.assertEqual(raw.find('da capo') > 0, True)
            
        s2 = converter.parse(raw)
        # now, reconverted from the musicxml, we have a RepeatExpression
        self.assertEqual(len(s2.flat.getElementsByClass(repeat.DaCapo)), 1)

        #s2.show('t')
        #s2.show()



    def testExpandDaCapoA(self):
        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note

        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.leftBarline = bar.Repeat(direction='start')
        rb = bar.Repeat(direction='end')
        m2.rightBarline = rb
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(DaCapo())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
    
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        ex = Expander(s)
        self.assertEqual(ex._daCapoIsCoherent(), True)
        self.assertEqual(ex._daCapoOrSegno(), DaCapo)

        # test incorrect da capo
        sAlt1 = copy.deepcopy(s)
        sAlt1[1].append(DaCapoAlFine())
        ex = Expander(sAlt1)
        self.assertEqual(ex._daCapoIsCoherent(), False)
        # rejected here b/c there is more than one
        self.assertEqual(ex._daCapoOrSegno(), None)


        # a da capo with a coda is not valid
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(Coda())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(DaCapo())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
    
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        ex = Expander(s)
        self.assertEqual(ex._daCapoIsCoherent(), False)
        self.assertEqual(ex._daCapoOrSegno(), DaCapo)



    def testRemoveRepeatExpressions(self):
        from music21 import stream, repeat, bar

        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(DaCapo())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), True)    
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'DaCapo'), [2])    

        ex._stripRepeatExpressions(m3)
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)    

        s = stream.Part()
        m1 = stream.Measure()
        m1.append(Segno())
        m1.append(Coda())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(Coda())
        m3.append(DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.getRepeatExpressionIndex(s, Segno), [0])    
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'Segno'), [0])    
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'Coda'), [0, 2])    
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'DaCapoAlCoda'), [2])    

        ex._stripRepeatExpressions(s) # entire part works too
        ex = repeat.Expander(s)
        self.assertEqual(ex.isExpandable(), False)   

        # case where a d.c. statement is placed at the end of bar that is repeated
        m1 = stream.Measure()
        m1.insert(4, Coda('To Coda'))
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end')
        m3.insert(4, DaCapoAlCoda())
        m4 = stream.Measure()
        m5 = stream.Measure()
        m5.append(Coda('Coda'))
        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        ex = repeat.Expander(s)
        self.assertEqual(ex.getRepeatExpressionIndex(s, Coda), [0, 4])    
        self.assertEqual(ex.getRepeatExpressionIndex(s, DaCapoAlCoda), [2])    

        dummy = ex.process()
        #dummy.show()        


    def testExpandRepeatExpressionA(self):
        
        # test one back repeat at end of a measure
        from music21 import stream, note

        # a da capo al fine without a fine is not valid
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(DaCapoAlFine())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
    
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        ex = Expander(s)
        self.assertEqual(ex._daCapoIsCoherent(), False)
        self.assertEqual(ex._daCapoOrSegno(), DaCapo)


        # has both da capo and da segno
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m1.append(DaCapoAlFine())
        m2 = stream.Measure()
        m1.append(DalSegnoAlCoda())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2])
        ex = Expander(s)
        self.assertEqual(ex._daCapoIsCoherent(), False)
        self.assertEqual(ex._daCapoOrSegno(), None)

        # segno alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m1.append(DalSegnoAlCoda())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2])
        ex = Expander(s)
        self.assertEqual(ex._daCapoIsCoherent(), False)
        self.assertEqual(ex._daCapoOrSegno(), Segno)
        self.assertEqual(ex._dalSegnoIsCoherent(), False)

        # if nothing, will return None
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        s = stream.Part()
        s.append([m1])
        ex = Expander(s)
        self.assertEqual(ex._daCapoOrSegno(), None)


    def testExpandRepeatExpressionB(self):
        
        # test one back repeat at end of a measure
        from music21 import stream, note

        # simple da capo alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(DaCapo())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        self.assertEqual(len(s.getElementsByClass('Measure')), 4)
        #s.show()
        ex = Expander(s)
        post = ex.process()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 7)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'A4', 'A4'])

    def testExpandRepeatExpressionC(self):
        from music21 import stream, note

        # da capo al fine
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(Fine())
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(DaCapoAlFine())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        self.assertEqual(len(s.getElementsByClass('Measure')), 4)
        #s.show()
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 5)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4'] )



    def testExpandRepeatExpressionD(self):
        from music21 import stream, note

        # da capo al coda
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(Coda('to coda'))
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(DaCapoAlCoda())
        m4 = stream.Measure()
        m4.append(Coda())
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        self.assertEqual(len(s.getElementsByClass('Measure')), 5)
        #s.show()
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 7)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4', 'A4', 'A4', 'B4', 'B4'])

    def testExpandRepeatExpressionE(self):
        from music21 import repeat, stream, note
        # dal segno simple
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        m3.append(repeat.DalSegno())

        s = stream.Part()
        s.append([m1, m2, m3, m4])
        #s.show()
        self.assertEqual(len(s.getElementsByClass('Measure')), 4)
        #s.show()
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 6)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'E4', 'E4', 'G4', 'G4', 'A4', 'A4'])


    def testExpandRepeatExpressionF(self):
        from music21 import stream, note
        from music21 import repeat
        # dal segno al fine
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.Fine())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        m4.append(repeat.DalSegnoAlFine())
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        #s.show()
        self.assertEqual(len(s.getElementsByClass('Measure')), 5)
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 6)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'A4', 'A4', 'E4', 'E4', 'G4', 'G4'])


    def testExpandRepeatExpressionG(self):
        from music21 import stream, note
        from music21 import repeat
        # dal segno al coda
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('e4', type='half'), 2)
        
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('g4', type='half'), 2)
        m4.append(repeat.DalSegnoAlCoda())
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('g4', type='half'), 2)
        m6 = stream.Measure()
        m6.append(repeat.Coda('CODA'))
        m6.repeatAppend(note.Note('a4', type='half'), 2)
        m7 = stream.Measure()
        m7.repeatAppend(note.Note('b4', type='half'), 2)
        
        s = stream.Part()
        s.append([m1, m2, m3, m4, m5, m6, m7])
        #s.show()
        self.assertEqual(len(s.getElementsByClass('Measure')), 7)
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 7)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'E4', 'E4', 'G4', 'G4', 'E4', 'E4', 'A4', 'A4', 'B4', 'B4'] )

    def testExpandRepeatExpressionH(self):        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note

        # simple da capo alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.rightBarline = bar.Repeat(direction='end')

        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        dcHandle = DaCapo('D.C.')
        m4.append(dcHandle)

        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        self.assertEqual(len(s.getElementsByClass('Measure')), 5)
        #s.show()
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 10)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'A4', 'A4', 'C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'A4', 'A4', 'B4', 'B4'])

        # test changing repeat after jump
        dcHandle.repeatAfterJump = True
        ex = Expander(s)
        post = ex.process()
        #post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass('Measure')), 11)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'A4', 'A4', 'C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'A4', 'A4', 'B4', 'B4'])



    def testExpandRepeatExpressionI(self):        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note, repeat

        # simple da capo alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))
        
        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        dcHandle = repeat.DaCapoAlCoda()
        m3.append(dcHandle)
        m3.rightBarline = bar.Repeat(direction='end')
        
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        
        m5 = stream.Measure()
        m5.append(repeat.Coda())
        m5.repeatAppend(note.Note('b4', type='half'), 2)
        
        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        self.assertEqual(len(s.getElementsByClass('Measure')), 5)
        #s.show()
        #s.expandRepeats().show()
        ex = Expander(s)
        post = ex.process()
        #post.show()
        self.assertEqual(len(post.getElementsByClass('Measure')), 7)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4', 'B4', 'B4'] )


    def testExpandRepeatExpressionJ(self):        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note, repeat, instrument

        # simple da capo alone
        m1 = stream.Measure()
        m1.append(repeat.Segno())
        m1.repeatAppend(note.Note('c4', type='half'), 2)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        dsHandle = repeat.DalSegnoAlCoda()
        m3.append(dsHandle)
        m3.rightBarline = bar.Repeat(direction='end')

        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)

        m5 = stream.Measure()
        m5.append(repeat.Coda())
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        # add an insturment
        s.insert(0, instrument.Trumpet())
        s.insert(0, spanner.Slur(m1[1], m2[1]))

        self.assertEqual(len(s.getElementsByClass('Measure')), 5)

        #s.show()
        #ex = Expander(s)
        #post = ex.process()
        post = s.expandRepeats()
        #post.show()
        self.assertEqual(len(post.getElementsByClass('Measure')), 7)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4', 'B4', 'B4'] )
        
        # instrument is copied in Stream
        self.assertEqual(post.getElementsByClass(
            'Instrument')[0].instrumentName, 'Trumpet')



    def testExpandRepeatsImportedA(self):
        '''
        tests expanding repeats in a piece with repeats midmeasure
        
        Also has grace notes so it tests our importing of grace notes
        '''
        
        from music21 import corpus
        s = corpus.parse('ryansMammoth/BanjoReel')
        #s.show('text')
        self.assertEqual(len(s.parts), 1)        
        self.assertEqual(len(s.parts[0].getElementsByClass('Measure')), 11)
        self.assertEqual(len(s.parts[0].flat.notes), 58)        

        bars = s.parts[0].flat.getElementsByClass('Barline')
        self.assertEqual(len(bars), 3)        

        s2 = s.expandRepeats()
        #s2.show('text')

        self.assertEqual(len(s2.parts[0].getElementsByClass('Measure')), 20)
        self.assertEqual(len(s2.parts[0].flat.notes), 105)        
    

    def testExpandRepeatsImportedB(self):
        from music21 import corpus
        s = corpus.parse('GlobeHornpipe')
        self.assertEqual(len(s.parts), 1)        
        self.assertEqual(len(s.parts[0].getElementsByClass('Measure')), 18)        
        self.assertEqual(len(s.parts[0].flat.notes), 125)        

        s2 = s.expandRepeats()    
        #s2.show()
        self.assertEqual(len(s2.parts[0].getElementsByClass('Measure')), 36)        
        self.assertEqual(len(s2.parts[0].flat.notes), 250)        
        # make sure barlines are stripped
        bars = s2.parts[0].flat.getElementsByClass('Repeat')
        self.assertEqual(len(bars), 0)        

#         self.assertEqual(len(s2.parts[0].flat.notes), 111)        
    

    def testExpandRepeatsImportedC(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.repeatExpressionsA)
        self.assertEqual(len(s.flat.getElementsByClass('RepeatExpression')), 3)

        s = converter.parse(testPrimitive.repeatExpressionsB)
        self.assertEqual(len(s.flat.getElementsByClass('RepeatExpression')), 3)

        #s.show()

    def testRepeatsEndingsA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        from music21.musicxml import m21ToString
        #from music21.musicxml import testPrimitive
        # this has repeat brackets
        # these are stored in bar objects as ending tags, 
        # given at start and end
        #         <ending number="2" type="discontinue"/>

        s = converter.parse(testPrimitive.repeatBracketsA)

        raw = m21ToString.fromMusic21Object(s)

        self.assertEqual(raw.find("<repeat direction=")>1, True)    
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="1" type="stop"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)   
 
        # TODO: after calling .musicxml, repeat brackets are getting lost
        #s.show()        
        raw = m21ToString.fromMusic21Object(s)

        self.assertEqual(raw.find("<repeat direction=")>1, True)    
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="1" type="stop"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)   

        s1 = copy.deepcopy(s)
        #s.show()

        #s1.show()
        raw = m21ToString.fromMusic21Object(s1)
        ex = Expander(s1.parts[0])
        self.assertEqual(len(ex._repeatBrackets), 2)



    def testRepeatEndingsB(self):
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        m3.rightBarline = bar.Repeat()
        self.assertEqual(rb1.hasSpannedElement(m2), True)
        self.assertEqual(rb1.hasSpannedElement(m3), True)
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=2)
        self.assertEqual(rb2.hasSpannedElement(m4), True)
        m4.rightBarline = bar.Repeat()
        p.append(rb2)

        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        
        # if we change the numbers no longer cohereent
        rb2.number = 30
        self.assertEqual(ex._repeatBracketsAreCoherent(), False)
        rb2.number = 2
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        rb1.number = 2
        rb2.number = 1
        self.assertEqual(ex._repeatBracketsAreCoherent(), False)

        rb1.number = 1
        rb2.number = 2
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)

        self.assertEqual(ex.repeatBarsAreCoherent(), True)

        #p.show()


    def testRepeatEndingsB2(self):
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        m3.rightBarline = bar.Repeat()
        self.assertEqual(rb1.hasSpannedElement(m2), True)
        self.assertEqual(rb1.hasSpannedElement(m3), True)
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=2)
        self.assertEqual(rb2.hasSpannedElement(m4), True)
        m4.rightBarline = bar.Repeat()
        p.append(rb2)

        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        
        # if we change the numbers no longer cohereent
        rb2.number = 30
        self.assertEqual(ex._repeatBracketsAreCoherent(), False)
        rb2.number = 2
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        rb1.number = 2
        rb2.number = 1
        self.assertEqual(ex._repeatBracketsAreCoherent(), False)

        rb1.number = 1
        rb2.number = 2
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)

        self.assertEqual(ex.repeatBarsAreCoherent(), True)

        #p.show()



    def testRepeatEndingsC(self):
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        p.append(rb1)
        # one repeat bracket w/o a repeat bar; makes no sense, should be 
        # rejected
        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), False)

        m3.rightBarline = bar.Repeat()
        # coherent after setting the barline
        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)

        # a second repeat bracket need not have a repeat ending
        rb2 = spanner.RepeatBracket(m4, number=2)
        p.append(rb2)
        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)

        m4.rightBarline = bar.Repeat()
        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)



    def testRepeatEndingsD(self):
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        p.append(rb1)
        m3.rightBarline = bar.Repeat()

        unused_ex = Expander(p)
        #self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        # overlapping at m3
        rb2 = spanner.RepeatBracket([m3, m4], number=2)
        p.append(rb2)
        m4.rightBarline = bar.Repeat()
        #p.show()
        # even with the right repeat, these are overlapping and should fail
        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), False)
        # can fix overlap even after insertion
#         rb2.replaceSpannedElement(m3, m5)
#         self.assertEqual(ex._repeatBracketsAreCoherent(), True)



    def testRepeatEndingsE(self):
        '''Expanding two endings (1,2, then 3) without a start repeat
        '''
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)
        rb2 = spanner.RepeatBracket(m4, number=3)
        # second ending may not have repeat
        p.append(rb2)
        #p.show()

        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        self.assertEqual(ex.isExpandable(), True)


        self.assertEqual(ex._findInnermostRepeatIndices(p), [0, 1, 2])
        # get groups of brackets; note that this does not get the end
        post = ex._groupRepeatBracketIndices(p)
        self.assertEqual(post[0]['measureIndices'], [1, 2, 3])

        

    def testRepeatEndingsF(self):
        '''Two sets of two endings (1,2, then 3) without a start repeat
        '''
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure()
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure()
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure()
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)
        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)

        # second group
        m5.leftBarline = bar.Repeat()
        m6.rightBarline = bar.Repeat()
        rb3 = spanner.RepeatBracket(m6, number='1-3')
        p.append(rb3)
        m7.rightBarline = bar.Repeat()
        rb4 = spanner.RepeatBracket(m7, number=4)
        p.append(rb4)
        rb5 = spanner.RepeatBracket(m8, number=5)
        p.append(rb5)
        # second ending may not have repeat
        #p.show()

        ex = Expander(p)
        self.assertEqual(ex._repeatBracketsAreCoherent(), True)
        self.assertEqual(ex.isExpandable(), True)
 
        self.assertEqual(ex._findInnermostRepeatIndices(p[3:]), [1, 2])
#         # get groups of brackets
        # returns a list of dictionaries
        post = ex._groupRepeatBracketIndices(p)
        self.assertEqual(post[0]['measureIndices'], [1, 2, 3])
        self.assertEqual(post[1]['measureIndices'], [5, 6, 7])




    def testRepeatEndingsG(self):
        '''Two sets of two endings (1,2, then 3) without a start repeat
        '''
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure()
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure()
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure()
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        #p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)
        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        #p.show()

        ex = Expander(p)
        self.assertEqual(ex.isExpandable(), True)
        post = ex.process()
        #post.show()
        self.assertEqual(len(post), 9)
        self.assertEqual([n.name for n in post.flat.notes], 
            ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'G'])
        #post.show()


    def testRepeatEndingsH(self):
        '''Two sets of two endings (1,2, then 3) without a start repeat
        '''
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure(number=6)
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure(number=7)
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure(number=8)
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        m4.rightBarline = bar.Repeat()

        rb3 = spanner.RepeatBracket(m5, number=4)
        p.append(rb3)

        #p.show()
        ex = Expander(p)
        self.assertTrue(ex.isExpandable())
        post = ex.process()
        environLocal.printDebug(['post process', [n.name for n in post.flat.notes]])
        #post.show()
        self.assertEqual(len(post), 13)
        self.assertEqual([n.name for n in post.flat.notes], 
            ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'C', 'G', 'A', 'B', 'C'])
 


    def testRepeatEndingsI(self):
        '''Two sets of two endings (1,2, then 3) without a start repeat
        '''
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure(number=6)
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure(number=7)
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure(number=8)
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        m4.rightBarline = bar.Repeat()
        


        # second group
        m5.leftBarline = bar.Repeat()
        m6.rightBarline = bar.Repeat()
        rb3 = spanner.RepeatBracket(m6, number='1-3')
        p.append(rb3)
        m7.rightBarline = bar.Repeat()
        rb4 = spanner.RepeatBracket(m7, number=4)
        p.append(rb4)
        rb5 = spanner.RepeatBracket(m8, number=5)
        p.append(rb5)
        # second ending may not have repeat
        #p.show()


        #p.show()
        ex = Expander(p)
        self.assertEqual(ex.isExpandable(), True)
        post = ex.process()
        #post.show()
# 
        self.assertEqual(len(post), 18)
        self.assertEqual([n.name for n in post.flat.notes], 
            ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'G', 'A', 'G', 'A', 'G', 'A', 'G', 'B', 'G', 'C'])
 

    def testRepeatEndingsJ(self):
        '''Two sets of two endings (1,2, then 3) without a start repeat
        '''
        from music21 import stream, note, bar

        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure(number=6)
        n1 = note.Note('a4', type='half')
        n2 = note.Note('a4', type='half')
        m6.append([n1, n2])
        m7 = stream.Measure(number=7)
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure(number=8)
        m8.append(note.Note('c5', type='whole'))
        
        m9 = stream.Measure(number=9)
        m9.append(note.Note('d5', type='whole'))
        m10 = stream.Measure(number=10)
        m10.append(note.Note('e5', type='whole'))
        m11 = stream.Measure(number=11)
        m11.append(note.Note('f5', type='whole'))
        m12 = stream.Measure(number=12)
        m12.append(note.Note('g5', type='whole'))
        
        p.append([m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12])
        
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        p.append(rb1)
        m3.rightBarline = bar.Repeat()
        
        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        
        # second group
        m5.leftBarline = bar.Repeat()
        m6.leftBarline = bar.Repeat() # nested repeat
        m6.rightBarline = bar.Repeat()
        
        rb3 = spanner.RepeatBracket(m7, number='1-3')
        p.append(rb3)
        m7.rightBarline = bar.Repeat()
        
        rb4 = spanner.RepeatBracket([m8, m10], number='4,5')
        p.append(rb4)
        m10.rightBarline = bar.Repeat()
        
        rb5 = spanner.RepeatBracket([m11], number='6')
        p.append(rb5) # not a repeat per se
        
        #p.show()
        
        
        #         ex = Expander(p)
        #         self.assertEqual(ex.isExpandable(), True)
        #         post = ex.process()
        #         post.show()
        
        post = p.expandRepeats()
        self.assertEqual(len(post), 37)
        #post.show()

# # 
#         self.assertEqual(len(post), 18)
#         self.assertEqual([n.name for n in post.flat.notes], 
#             ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'G', 'A', 'G', 'A', 'G', 'A', 'G', 'B', 'G', 'C'])
 


    def testRepeatEndingsImportedA(self):

        from music21 import corpus
        s = corpus.parse('ryansMammoth/BanjoReel')
        #s.show()
        firstNotesList = s.flat.notes.elements
        #[0:16][16:22][0:16][22:27][27:58][27:58]
        expandedByHandList = firstNotesList[0:16] + firstNotesList[16:22] + firstNotesList[0:16] + firstNotesList[22:27] + firstNotesList[27:58] + firstNotesList[27:58]
        expandedByHandNoteNames = [n.nameWithOctave for n in expandedByHandList]
        ex = Expander(s.parts[0])
        post = ex.process()
        #post.show()
        #print [n.nameWithOctave for n in post.flat.notes]
        #post.show()
        secondNotesList = post.flat.notes.elements
        secondNotesNoteNames = [n.nameWithOctave for n in secondNotesList]
        self.assertEqual(expandedByHandNoteNames, secondNotesNoteNames)




    def testRepeatEndingsImportedB(self):
        from music21 import corpus
        # last alternate endings in last bars
        # need to add import from abc
        s = corpus.parse('ryansMammoth/SmugglersReel')
        #s.parts[0].show()
        ex = Expander(s.parts[0])
        # this is a Stream resulting form getElements
        self.assertEqual(len(ex._repeatBrackets), 2)
        #s.show()
        unused_post = ex.process()
        #post.show()


    def testRepeatEndingsImportedC(self):
        
        
        from music21 import converter
        from music21.abcFormat import testFiles
        
        s = converter.parse(testFiles.mysteryReel)
        #s.show()
        post = s.expandRepeats()    
        #post.show()
        self.assertEqual(len(post.parts[0]), 32)

#         s = converter.parse(testFiles.hectorTheHero)
#         s.show()
#         post = s.expandRepeats()    


    
    

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [RepeatExpression, RepeatExpressionMarker, Coda, Segno, Fine, RepeatExpressionCommand, DaCapo, DaCapoAlFine, 
              DaCapoAlCoda, AlSegno, DalSegno, DalSegnoAlFine, DalSegnoAlCoda, RepeatFinder]

if __name__ == "__main__":
    #import sys
    #sys.argv.append('testRepeatEndingsH')
    
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

