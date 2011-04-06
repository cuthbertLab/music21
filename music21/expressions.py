#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         expressions.py
# Purpose:      notation mods
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
This module provides object representations of expressions, that is
notational symbols such as Fermatas, Mordents, Trills, Turns, etc.
which are stored under a Music21Object's .expressions attribute 
'''
import copy
import doctest, unittest

import music21
import music21.interval
from music21 import musicxml
from music21 import text
from music21 import common

_MOD = 'expressions'

def realizeOrnaments(srcObject):
    '''
    given a Music21Object with Ornament expressions,
    convert them into a list of objects that represents
    the performed version of the object:
    
    >>> from music21 import *
    >>> n1 = note.Note("D5")
    >>> n1.quarterLength = 1
    >>> n1.expressions.append(expressions.WholeStepMordent())
    >>> expList = expressions.realizeOrnaments(n1)
    >>> st1 = stream.Stream()
    >>> st1.append(expList)
    >>> #_DOCS_SHOW st1.show()
    
    .. image:: images/expressionsMordentRealize.*
         :width: 218
    
    
    '''
    if not hasattr(srcObject, "expressions"):
        return [srcObject]
    elif len(srcObject.expressions) == 0:
        return [srcObject]
    else:
        preExpandList = []
        postExpandList = []
        for thisExpression in srcObject.expressions:
            if not hasattr(thisExpression, 'realize'):
                continue
            preExpand, srcObject, postExpand = thisExpression.realize(srcObject)
            for i in preExpand:
                preExpandList.append(i)
            for i in postExpand:
                postExpandList.append(i)
            if srcObject is None: # some ornaments eat up the entire source object. Trills for instance
                break
        retList = []
        for i in preExpandList:
            retList.append(i)
        retList.append(srcObject)
        for i in postExpandList:
            retList.append(i)
        return retList


#-------------------------------------------------------------------------------
class ExpressionException(music21.Music21Exception):
    pass


class Expression(music21.Music21Object):
    '''This base class is inherited by many diverse expressions. 
    '''
    def __init__(self):
        music21.Music21Object.__init__(self)

    def __repr__(self):
        return '<music21.expressions.%s>' % (self.__class__.__name__)



#-------------------------------------------------------------------------------
class TextExpressionException(ExpressionException):
    pass


class TextExpression(Expression, text.TextFormat):
    '''A TextExpression is a word, phrase, or similar bit of text that is positioned in a Stream or Measure. Conventional expressive indications are text like "agitato" or "con fuoco."

    >>> from music21 import *
    >>> te = expressions.TextExpression('testing')
    >>> te.size = 24
    >>> te.size
    24.0
    >>> te.style = 'bolditalic'
    >>> te.letterSpacing = 0.5
    '''

    # always need to be first, before even clefs
    classSortOrder = -10

    def __init__(self, content=None):
        Expression.__init__(self)
        # numerous properties are inherited from TextFormat
        text.TextFormat.__init__(self)

        # the text string to be displayed; not that line breaks
        # are given in the xml with this non-printing character: (#)
        if not common.isStr(content):
            self._content = str(content)
        else:
            self._content = content

        self._enclosure = None

        # numerous parameters are inherited from text.TextFormat

        self._positionDefaultX = None
        self._positionDefaultY = 20 # two staff lines above
        # these values provided for musicxml compatibility
        self._positionRelativeX = None
        self._positionRelativeY = None
        # this does not do anything if default y is defined
        self._positionPlacement = None


    def __repr__(self):
        if self._content is not None and len(self._content) > 10:
            return '<music21.expressions.%s "%s...">' % (self.__class__.__name__, self._content[:10])
        elif self._content is not None:
            return '<music21.expressions.%s "%s">' % (self.__class__.__name__, self._content)
        else:
            return '<music21.expressions.%s>' % (self.__class__.__name__)

    def _getContent(self):
        return self._content
    
    def _setContent(self, value):
        self._content = str(value)
    
    content = property(_getContent, _setContent, 
        doc = '''Get or set the the content.

        >>> from music21 import *
        >>> te = expressions.TextExpression('testing')
        >>> te.content
        'testing'
        ''')



    def _getEnclosure(self):
        return self._enclosure
    
    def _setEnclosure(self, value):
        if value is None:
            self._enclosure = value
        elif value.lower() in ['oval', 'rectangle']:
            self._enclosure = value.lower()
        else:
            raise TextExpressionException('Not a supported justification: %s' % value)
    
    enclosure = property(_getEnclosure, _setEnclosure, 
        doc = '''Get or set the the enclosure.

        >>> from music21 import *
        >>> te = expressions.TextExpression()
        >>> te.justify = 'center'
        >>> te.enclosure = None
        >>> te.enclosure = 'rectangle'
        ''')


    def _getPositionVertical(self):
        return self._positionDefaultY
    
    def _setPositionVertical(self, value):
        if value is None:
            self._positionDefaultY = None
        else:
            try:
                value = float(value)
            except (ValueError):
                raise TextExpressionException('Not a supported size: %s' % value)
            self._positionDefaultY = value
    
    positionVertical = property(_getPositionVertical, _setPositionVertical, 
        doc = '''Get or set the the vertical position, where 0 is the top line of the staff and units are in 10ths of a staff space.

        >>> from music21 import *
        >>> te = expressions.TextExpression()
        >>> te.positionVertical = 10
        >>> te.positionVertical
        10.0
        ''')




#-------------------------------------------------------------------------------
class Ornament(Expression):
    connectedToPrevious = True  
    # should follow directly on previous; true for most "ornaments".
    tieAttach = 'first' # attach to first note of a tied group.

    def __init__(self):
        Expression.__init__(self)

    def realize(self, sourceObject):
        '''
        subclassible method call that takes a sourceObject
        and returns a three-element tuple of a list of notes before the "main note",
        the "main note" itself, and a list of notes after the "main note".
        '''
        return ([], sourceObject, [])

class GeneralMordent(Ornament):
    direction = ""  # up or down
    size = None # music21.interval.Interval (General, etc.) class
    quarterLength = 0.125 # 32nd note default 

    def __init__(self):
        Ornament.__init__(self)

        self.size = music21.interval.GenericInterval(2)

    def realize(self, srcObject):
        '''
        realize a mordent.
        
        returns a three-element tuple.
        The first is a list of the two notes that the beginning of the note were converted to.
        The second is the rest of the note
        The third is an empty list (since there are no notes at the end of a mordent)


        TODO: write more docs...

        '''
        if self.direction != 'up' and self.direction != 'down':
            raise ExpressionException("Cannot realize a mordent if I do not know its direction")
        if self.size == "":
            raise ExpressionException("Cannot realize a mordent if there is no size given")
        if srcObject.duration == None or srcObject.duration.quarterLength == 0:
            raise ExpressionException("Cannot steal time from an object with no duration")

        remainderDuration = srcObject.duration.quarterLength - 2 * self.quarterLength
        if self.direction == "down":
            transposeInterval = self.size.reverse()
        else:
            transposeInterval = self.size
        
        firstNote = copy.deepcopy(srcObject)
        #firstNote.expressions = None
        #todo-clear lyrics.
        firstNote.duration.quarterLength = self.quarterLength
        secondNote = copy.deepcopy(srcObject)
        secondNote.duration.quarterLength = self.quarterLength
        #secondNote.expressions = None
        secondNote.transpose(transposeInterval, inPlace = True)
        remainderNote = copy.deepcopy(srcObject)
        remainderNote.duration.quarterLength = remainderDuration
        #TODO clear just mordent here...
        return ([firstNote, secondNote], remainderNote, [])

class Mordent(GeneralMordent):
    direction = "down"
    def __init__(self):
        GeneralMordent.__init__(self)

class HalfStepMordent(Mordent):
    def __init__(self):
        Mordent.__init__(self)
        self.size = music21.interval.Interval("m2")

class WholeStepMordent(Mordent):
    def __init__(self):
        Mordent.__init__(self)
        self.size = music21.interval.Interval("M2")

class InvertedMordent(GeneralMordent):
    direction = "up"
    def __init__(self):
        GeneralMordent.__init__(self)

class HalfStepInvertedMordent(InvertedMordent):
    def __init__(self):
        InvertedMordent.__init__(self)
        self.size = music21.interval.Interval("m2")

class WholeStepInvertedMordent(InvertedMordent):
    def __init__(self):
        InvertedMordent.__init__(self)
        self.size = music21.interval.Interval("M2")

class Trill(Ornament):
    placement = 'above'
    nachschlag = False # play little notes at the end of the trill?
    tieAttach = 'all'
    quarterLength = 0.125

    def __init__(self):
        Ornament.__init__(self)
        self.size = music21.interval.GenericInterval(2)

    def realize(self):
        '''
        neena will write this...
        with docs...
        and examples...
        '''
        pass


    def _getMX(self):
        '''
        Returns a musicxml.TrillMark object
        >>> a = Trill()
        >>> a.placement = 'above'
        >>> mxTrillMark = a.mx
        >>> mxTrillMark.get('placement')
        'above'
        '''
        mxTrillMark = musicxml.TrillMark()
        mxTrillMark.set('placement', self.placement)
        return mxTrillMark


    def _setMX(self, mxTrillMark):
        '''
        Given an mxTrillMark, load instance

        >>> mxTrillMark = musicxml.TrillMark()
        >>> mxTrillMark.set('placement', 'above')
        >>> a = Trill()
        >>> a.mx = mxTrillMark
        >>> a.placement
        'above'
        '''
        self.placement = mxTrillMark.get('placement')

    mx = property(_getMX, _setMX)


class HalfStepTrill(Trill):
    def __init__(self):
        Trill.__init__(self)
        self.size = music21.interval.Interval("m2")

class WholeStepTrill(Trill):
    def __init__(self):
        Trill.__init__(self)
        self.size = music21.interval.Interval("M2")

class Turn(Ornament):
    pass

class InvertedTurn(Ornament):
    pass



class Fermata(Expression):
    '''
    Fermatas by default get appended to the last
    note if a note is split because of measures.
    To override this (for Fermatas or for any
    expression) set .tieAttach to 'all' or 'first'
    instead of 'last'. 
    
    >>> from music21 import *
    >>> p1 = stream.Part()
    >>> p1.append(meter.TimeSignature('6/8'))
    >>> n1 = note.Note("D-2")
    >>> n1.quarterLength = 6
    >>> n1.expressions.append(expressions.Fermata())
    >>> p1.append(n1)
    >>> #_DOCS_SHOW p1.show()
    .. image:: images/expressionsFermata.*
         :width: 193
    '''
    shape = "normal"
    type  = "upright" # for musicmxml, can be upright, upright-inverted
    lily  = "\\fermata"
    tieAttach = 'last'

    def _getMX(self):
        '''
        Advanced feature: 
        
        As a getter gives the music21.musicxml object for the Fermata
        or as a setter changes the current fermata to have
        the characteristics of the musicxml object to fit this
        type:
        
        >>> from music21 import *
        >>> a = Fermata()
        >>> mxFermata = a.mx
        >>> mxFermata.get('type')
        'upright'

  
        >>> mxFermata2 = musicxml.Fermata()
        >>> mxFermata2.set('type', 'upright-inverted')
        >>> a.mx = mxFermata2
        >>> a.type
        'upright-inverted'

        '''
        mxFermata = musicxml.Fermata()
        mxFermata.set('type', self.type)
        return mxFermata

    def _setMX(self, mxFermata):
        self.type = mxFermata.get('type')

    mx = property(_getMX, _setMX)







#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testRealize(self):
        from music21 import note
        from music21 import stream
        n1 = note.Note("D4")
        n1.quarterLength = 4
        n1.expressions.append(WholeStepMordent())
        expList = realizeOrnaments(n1)
        st1 = stream.Stream()
        st1.append(expList)
        st1n = st1.notes
        self.assertEqual(st1n[0].name, "D")
        self.assertEqual(st1n[0].quarterLength, 0.125)
        self.assertEqual(st1n[1].name, "C")
        self.assertEqual(st1n[1].quarterLength, 0.125)
        self.assertEqual(st1n[2].name, "D")
        self.assertEqual(st1n[2].quarterLength, 3.75)
        
        
if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

