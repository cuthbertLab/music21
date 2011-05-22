#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         repeat.py
# Purpose:      Base classes for processing repeats
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''
This module provides the base class for all RepeatMark objects: entities that denote repeats.

Some RepeatMark objects are Expression objecs; others are Bar objects. 
'''
import copy
import doctest, unittest

import music21
from music21 import expressions


from music21 import environment
_MOD = 'repeat.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class RepeatMark(object):
    '''Base class of all repeat objects, including RepeatExpression objects and Repeat (Barline) objects. 

    This object is used to for multiple-inheritance of such objects and to filter by class.
    '''
    def __init__(self):
        pass



#-------------------------------------------------------------------------------
class RepeatExpressionException(music21.Music21Exception):
    pass

class RepeatExpression(RepeatMark, expressions.Expression):
    '''
    This class models any mark added to a Score to mark repeat start and end points that are designated by text expressions or symbols.

    Repeat(Barlin) objects are not RepeatExpression objects, but both are RepeatMark subclasses. 

    This class stores internally a :class:`~music21.expressions.TextExpression`. This object is used for rendering text output in translation. A properly configured TextExpression object can also be used to create an instance of a RepeatExpressions.
    '''
    def __init__(self):
        expressions.Expression.__init__(self)

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
        self._textJustification
        if self._textExpression is None:
            return None
        else:
            # first, apply defaults 
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
    '''Some repeat expressions are markers of positions in the score; these classes model those makers, such as Coda, Segno, and Fine.
    '''
    def __init__(self):
        RepeatExpression.__init__(self)
        # these are generally centered
        self._textJustification = 'center'


class Coda(RepeatExpressionMarker):
    '''The coda symbol, or the word coda, as placed in a score. 

    >>> from music21 import *
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
    '''The fine word as placed in a score. 

    >>> from music21 import *
    >>> rm = repeat.Segno()
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

    >>> from music21 import *
    >>> rm = repeat.Fine()
    '''
    def __init__(self):
        RepeatExpressionMarker.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['fine']
        self.setText(self._textAlternatives[0])
        self._textJustification = 'right'







class RepeatExpressionCommand(RepeatExpression):
    '''Some repeat expressions are commands, instructing the reader to go somewhere else. DaCapo and related are examples.
    '''
    def __init__(self):
        RepeatExpression.__init__(self)
        # whether any internal repeats encountered within a jumped region are also repeated.
        self.repeatAfterJump = False
        # generally these should be right aligned, as they are placed 
        # at the end of the measure they alter
        self._textJustification = 'right'


class DaCapo(RepeatExpressionCommand):
    '''The Da Capo command, indicating a return to the beginning and a continuation to the end. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Capo repeat not be repeated. 
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
    '''The Da Capo al Fine command, indicating a return to the beginning and a continuation to the :class:`~music21.repeat.Fine` object. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Capo repeat not be repeated. 

    >>> from music21 import *
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
    '''The Da Capo al Coda command, indicating a return to the beginning and a continuation to the :class:`~music21.repeat.Coda` object. The music resumes at a second :class:`~music21.repeat.Coda` object. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Capo repeat not be repeated. 

    >>> from music21 import *
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
    '''Jump to the sign. Presumably a forward jump, not a repeat.

    >>> from music21 import *
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self, text=None):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['al Segno']
        if text is not None and self.isValidText(text):
            self.setText(text)
        else:
            self.setText(self._textAlternatives[0])


class DalSegno(RepeatExpressionCommand):
    '''The Dal Segno command, indicating a return to the segno and a continuation to the end. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Capo repeat not be repeated. 

    >>> from music21 import *
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
    '''The Dal Segno al Fine command, indicating a return to the segno and a continuation to the :class:`~music21.repeat.Fine` object. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Dal Segno repeat not be repeated. 

    >>> from music21 import *
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
    '''The Dal Segno al Coda command, indicating a return to the beginning and a continuation to the :class:`~music21.repeat.Coda` object. The music resumes at a second :class:`~music21.repeat.Coda` object. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Segno repeat not be repeated. 

    >>> from music21 import *
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



class ExpanderException(Exception):
    pass

class Expander(object):
    '''Expand a single Part or Part-like stream with repeats.
    '''

    def __init__(self, streamObj):
        self._src = streamObj
        # get and store the source measure count
        self._srcMeasureStream = self._src.getElementsByClass('Measure')
        # store all top-level non Measure elements for later insertion
        self._srcNotMeasureStream = self._src.getElementsNotOfClass('Measure')

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


    def _stripRepeatBarlines(self, m, newStyle='light-light'):
        '''Given a measure, strip barlines if they are repeats, and replace with Barlines that are of the same style. Modify in place.
        '''
        # bar import repeat to make Repeat inherit from RepeatMark
        from music21 import bar
        lb = m.leftBarline
        rb = m.rightBarline
        if lb is not None and 'Repeat' in lb.classes:
            environLocal.printDebug(['inserting new barline: %s' % newStyle])
            m.leftBarline = bar.Barline(newStyle)
        if rb is not None and 'Repeat' in rb.classes:
            m.rightBarline = bar.Barline(newStyle)

    def _stripRepeatExpressions(self, streamObj):
        '''Given a Stream of measures or a Measure, strip all RepeatExpression objects in place.
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

    def _repeatBarsAreCoherent(self):
        '''Check that all repeat bars are paired properly.
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
        '''Return a DaCapo if this is any form of DaCapo; return a Segno if this is any form of Segno. Return None if incoherent.
        '''
        sumDc = self._dcCount + self._dcafCount + self._dcacCount
        # for now, only accepting one segno
        sumDs = (self._dsCount + self._dsacCount + 
                self._dsafCount + self._asCount)
        environLocal.printDebug(['_daCapoOrSegno', sumDc, sumDs])
        if sumDc == 1 and sumDs == 0:
            return DaCapo
        elif sumDs == 1 and sumDc == 0:
            return Segno
        else:
            return None
        
    def _getRepeatExpressionCommandType(self):
        '''Return the class of the repeat expression command. This should only be called if it has been determine that there is one repeat command in this Stream.
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
            environLocal.printDebug(['returning true on dc'])
            return True

        # if we have a da capo al fine, must have one fine
        elif self._dcafCount == 1 and self._fineCount == 1:
            environLocal.printDebug(['returning true on dcaf'])
            return True

        # if we have a da capo al coda, must have two coda signs
        elif self._dcacCount == 1 and self._codaCount == 2:
            environLocal.printDebug(['returning true on dcac'])
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
            environLocal.printDebug(['returning true on as'])
            return True

        if (self._dsCount == 1 and self._segnoCount == 1 and 
            self._codaCount == 0):
            environLocal.printDebug(['returning true on ds'])
            return True

        # if we have a da capo al fine, must have one fine
        elif (self._dsafCount == 1 and self._codaCount == 0 and 
            self._segnoCount == 1 and self._fineCount == 1):
            environLocal.printDebug(['returning true on dsaf'])
            return True

        # if we have a da capo al coda, must have two coda signs
        elif (self._dsacCount == 1 and self._codaCount == 2 and 
            self._segnoCount == 1 and self._fineCount == 0):
            environLocal.printDebug(['returning true on dsac'])
            return True

        # return false for all other cases
        return False
        

    def _hasRepeat(self, streamObj):
        '''Return True if this Stream of Measures has a repeat pair left to process.
        '''
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
        '''Find the innermost repeat bars. Return raw index values.
        For a single measure, this might be [2, 2]
        For many contiguous measures, this might be [2, 3, 4, 5]
        '''
        # need to find only the first open and closed pair
        startIndices = []
        # use index values instead of an interator
        for i in range(len(streamObj)):
            # iterate through each measure
            m = streamObj[i]
            lb = m.leftBarline
            rb = m.rightBarline

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
        return barRepeatIndices


    def _getEndRepeatBar(self, streamObj, index):
        '''Get the last measure to be processed in the repeat, as well as the measure that has the end barline. These may not be the same: if an end repeat bar is placed on the left of a measure that is not actually being copied. 

        The `index` parameter is the index of the last measure to be copied. The streamObj expects to only have Measures. 
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
            if len(streamObj) < index:
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

    def _processInnermostRepeatBars(self, streamObj):
        '''Process and return a new Stream of Measures, likely a Part.
        '''
        # get class from src
        new = streamObj.__class__()

        # need to gather everything that is not a Meausre (e.g., Instrument)
        # and add copies to new
        repeatIndices = self._findInnermostRepeatIndices(streamObj)
        environLocal.printDebug(['got new repeat indices:', repeatIndices])

        # renumber measures starting with the first number found here
        number = streamObj[0].number
        if number is None:
            number = 1
        # handling of end repeat as left barline
        stripFirstNextMeasure = False
        # use index values instead of an interator
        i = 0
        while i < len(streamObj):
        #for i in range(len(streamObj)):
            environLocal.printDebug(['processing measure index:', i, 'repeatIndices', repeatIndices])
            # if this index is the start of the repeat
            if i == repeatIndices[0]:
                mLast, mEndBarline, repeatTimes = self._getEndRepeatBar(
                    streamObj, repeatIndices[-1])
                for times in range(repeatTimes):
                    environLocal.printDebug(['repeat times:', times])    
                    # copy the range of measures; this will include the first
                    # always copying from the same source
                    for j in repeatIndices:
                        mSub = copy.deepcopy(streamObj[j])
                        # must do for each pass, b/c not changing source
                        # stream
                        #environLocal.printDebug(['got j, repeatIndicies', j, repeatIndices])
                        if j in [repeatIndices[0], repeatIndices[-1]]:
                            self._stripRepeatBarlines(mSub)
                        mSub.number = number
                        # only keep repeat expressions found at the end  
                        # only remove anything if we have 2 or more repeats
                        # and this is not the last time 
                        if repeatTimes >= 2 and times < repeatTimes - 1: 
                            self._stripRepeatExpressions(mSub)
                        new.append(mSub)
                        number += 1
                # check if need to clear repeats from next bar
                if mLast is not mEndBarline:
                    stripFirstNextMeasure = True
                # set i to next measure after mLast
                i = repeatIndices[-1] + 1
            # if is not in repeat indicies, just add this measure
            else:
                # iterate through each measure, always add first
                m = copy.deepcopy(streamObj[i])
                if stripFirstNextMeasure:
                    self._stripRepeatBarlines(m)
                    # change in source too
                    self._stripRepeatBarlines(streamObj[i])
                    stripFirstNextMeasure = False
                m.number = number
                new.append(m) # this may be the first version
                number += 1
                i += 1
        return new


    def _getRepeatExpressionIndex(self, streamObj, target):
        '''Return a list of index position of a Measure given a stream of measures. This requires the provided stream to only have measures. 
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
        '''Return True or False if this Stream is expandable, that is, if it has balanced repeats or sensible da copo or dal segno indications. 
        '''
        match = self._daCapoOrSegno()
        # if neither repeats nor segno/capo, than not expandable
        if match is None and not self._hasRepeat(self._srcMeasureStream):
            environLocal.printDebug('no dc/segno, no repeats')
            return False

        if not self._repeatBarsAreCoherent():
            environLocal.printDebug('repeat bars not coherent')
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



    def _processRecursiveRepeatBars(self, streamObj):
        '''Recursively expand any number of nested repeat bars
        '''
        # this assumes just a stream of measures
        post = copy.deepcopy(streamObj)
        while True:
            #environLocal.printDebug(['process(): top of loop'])
            #post.show('t')
            post = self._processInnermostRepeatBars(post)
            #post.show('t')
            if self._hasRepeat(post):                        
                environLocal.printDebug([
                    'process() calling: self._findInnermostRepeatIndices(post)', self._findInnermostRepeatIndices(post)])
            else:
                break # nothing left to process
        return post


    def _processRepeatExpressionAndRepeats(self, streamObj):
        '''Process and return a new Stream of Measures, likely a Part.
        Expand any repeat expressions found within.

        streamObj 
        '''
        # should already be a stream of measures
        capoOrSegno = self._daCapoOrSegno()
        recType = self._getRepeatExpressionCommandType() # a string form
        recObj = self._getRepeatExpressionCommand(streamObj)
        jumpBack = self._getRepeatExpressionIndex(streamObj, recType)[0]

        # start position is dependent on capo or segno
        if capoOrSegno is DaCapo:
            start = 0
        elif capoOrSegno is Segno:
            start = self._getRepeatExpressionIndex(streamObj, 'Segno')[0]

        # this is either fine or the end
        if recType in ['DaCapoAlFine', 'DalSegnoAlFine']:
            end = self._getRepeatExpressionIndex(streamObj, 'Fine')[0]
        else:
            end = len(streamObj) - 1
        environLocal.printDebug(['got end/fine:', end])

        # coda jump/start
        if recType in ['DaCapoAlCoda', 'DalSegnoAlCoda']:
            # there must always be two coda symbols; the jump and start
            codaJump = self._getRepeatExpressionIndex(streamObj, 'Coda')[0]
            codaStart = self._getRepeatExpressionIndex(streamObj, 'Coda')[1]
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

        environLocal.printDebug(['_processRepeatExpressionAndRepeats', 'index segments', indexSegments])
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



    def process(self):
        '''Process all repeats. Note that this processing only happens for Measures contained in the given Stream. Other objects in that Stream are neither processed nor copied. 
        '''
        if not self.isExpandable():
            raise ExpanderException('cannot expand Stream: badly formed repeats or repeat expressions')

        #post = copy.deepcopy(self._srcMeasureStream)
        match = self._daCapoOrSegno()
        # will deep copy
        if match is None:
            post = self._processRecursiveRepeatBars(self._srcMeasureStream)
        else: # we have a segno or capo
            post = self._processRepeatExpressionAndRepeats(
                self._srcMeasureStream)        

        # TODO: need to copy spanners from each sub-group into their newest conects; must be done here as more than one connection is made

        return post


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
        self.assertEqual(ex._repeatBarsAreCoherent(), True)
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


    def testRepeatCoherenceB(self):
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
        self.assertEqual(ex._repeatBarsAreCoherent(), True)
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
        from music21 import stream, bar, repeat, note

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
        from music21.abc import testFiles
        from music21 import converter, repeat
        
        s = converter.parse(testFiles.draughtOfAle)
        self.assertEqual(s.parts[0].getElementsByClass('Measure').__len__(), 18)
        self.assertEqual(s.metadata.title, '"A Draught of Ale"    (jig)     0912')
        self.assertEqual(len(s.flat.notesAndRests), 88)

        #s.show()
        ex = repeat.Expander(s.parts[0])
        # check boundaries here

        post = s.expandRepeats()
        self.assertEqual(post.parts[0].getElementsByClass('Measure').__len__(), 36)
        # make sure metadata is copied
        self.assertEqual(post.metadata.title, '"A Draught of Ale"    (jig)     0912')
        self.assertEqual(len(post.flat.notesAndRests), 88 * 2)

        #post.show()


    def testExpandRepeatC(self):
        from music21.abc import testFiles
        from music21 import converter, repeat
        
        s = converter.parse(testFiles.kingOfTheFairies)
        self.assertEqual(s.parts[0].getElementsByClass('Measure').__len__(), 26)
        self.assertEqual(s.metadata.title, 'King of the fairies')
        self.assertEqual(len(s.flat.notesAndRests), 145)

        #s.show()
        ex = repeat.Expander(s.parts[0])
        self.assertEqual(ex._findInnermostRepeatIndices(s.parts[0]), [0, 1, 2, 3, 4, 5, 6, 7, 8])
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
        
        from music21.abc import testFiles
        from music21 import converter, repeat, bar
        
        s = converter.parse(testFiles.hectorTheHero)
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
        from music21 import stream, repeat, expressions, musicxml, meter

        template = stream.Stream()
        for i in range(5):
            m = stream.Measure()
            template.append(m)
        s = copy.deepcopy(template)
        s[3].insert(0, repeat.DaCapo())
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapo)), 1)
        raw = s.musicxml
        self.assertEqual(raw.find('Da Capo') > 0, True)

        # can do the same thing starting form a text expression
        s = copy.deepcopy(template)
        s[0].timeSignature = meter.TimeSignature('4/4')
        s[3].insert(0, expressions.TextExpression('da capo'))
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapo)), 0)
        raw = s.musicxml
        self.assertEqual(raw.find('da capo') > 0, True)
            
        mxlDocument = musicxml.Document()
        mxlDocument.read(raw)
        s2 = musicxml.translate.mxToStream(mxlDocument.score)
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
        self.assertEqual(ex._getRepeatExpressionIndex(s, 'DaCapo'), [2])    

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
        self.assertEqual(ex._getRepeatExpressionIndex(s, Segno), [0])    
        self.assertEqual(ex._getRepeatExpressionIndex(s, 'Segno'), [0])    
        self.assertEqual(ex._getRepeatExpressionIndex(s, 'Coda'), [0, 2])    
        self.assertEqual(ex._getRepeatExpressionIndex(s, 'DaCapoAlCoda'), [2])    

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
        self.assertEqual(ex._getRepeatExpressionIndex(s, Coda), [0, 4])    
        self.assertEqual(ex._getRepeatExpressionIndex(s, DaCapoAlCoda), [2])    

        post = ex.process()
        #post.show()        


    def testExpandRepeatExpressionA(self):
        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note

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
        from music21 import stream, bar, note

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
        import stream, note, repeat

        # da capo al fine
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Fine())
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapoAlFine())
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
        import stream, note, repeat

        # da capo al coda
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapoAlCoda())
        m4 = stream.Measure()
        m4.append(repeat.Coda())
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


    def testExpandRepeatExpressionD(self):
        import stream, note, repeat

        # da capo al coda
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapoAlCoda())
        m4 = stream.Measure()
        m4.append(repeat.Coda())
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
        import stream, note, repeat

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
        import stream, note, repeat
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
        import stream, note, repeat
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
        ex = Expander(s)
        post = ex.process()
        #post.show()
        self.assertEqual(len(post.getElementsByClass('Measure')), 7)
        self.assertEqual([x.nameWithOctave for x in post.flat.pitches], ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4', 'B4', 'B4'] )


    def testExpandRepeatExpressionJ(self):        
        # test one back repeat at end of a measure
        from music21 import stream, bar, note, repeat, instrument, spanner

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



if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

