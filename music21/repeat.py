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
    '''Bass class of all repeat objects, including RepeatExpression objects and Repeat(Barline) objects. 

    This object is used to for multiple-inheritance of such objects. 
    '''
    def __init__(self):
        pass



#-------------------------------------------------------------------------------
class RepeatExpressionException(music21.Music21Exception):
    pass

class RepeatExpression(RepeatMark, expressions.Expression):
    '''
    This class models any mark added to a Score to mark repeat start and end points that are designated by text expressions. 

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
        self._useSymbol = False

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
    def __init__(self):
        RepeatExpressionMarker.__init__(self)

        # default text expression is coda
        self._textAlternatives = ['Coda', 'to Coda', 'al Coda']
        self.setText(self._textAlternatives[0])
        self._useSymbol = True

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
        self._useSymbol = True

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
    def __init__(self):
        RepeatExpressionCommand.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['Da Capo', 'D.C.']
        self.setText(self._textAlternatives[0])

class DaCapoAlFine(RepeatExpressionCommand):
    '''The Da Capo al Fine command, indicating a return to the beginning and a continuation to the :class:`~music21.repeat.Fine` object. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Capo repeat not be repeated. 

    >>> from music21 import *
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self):
        RepeatExpressionCommand.__init__(self)
        # default text expression is coda
        self._textAlternatives = ['Da Capo al fine', 'D.C. al fine']
        self.setText(self._textAlternatives[0])


class DaCapoAlCoda(RepeatExpressionCommand):
    '''The Da Capo al Coda command, indicating a return to the beginning and a continuation to the :class:`~music21.repeat.Coda` object. The music resumes at a second :class:`~music21.repeat.Coda` object. By default, `repeatAfterJump` is False, indicating that any repeats encountered on the Da Capo repeat not be repeated. 

    >>> from music21 import *
    >>> rm = repeat.DaCapoAlCoda() 
    '''
    def __init__(self):
        RepeatExpressionCommand.__init__(self)

        self._textAlternatives = ['Da Capo al Coda', 'D.C. al Coda']
        self.setText(self._textAlternatives[0])


class AlSegno(RepeatExpressionCommand):
    '''Jump to the sign. 

    >>> from music21 import *
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['al Segno']
        self.setText(self._textAlternatives[0])


class DalSegnoAlFine(RepeatExpressionCommand):
    '''

    >>> from music21 import *
    >>> rm = repeat.DaCapoAlFine()
    '''
    def __init__(self):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['Dal Segno al fine', 'D.S. al fine']
        self.setText(self._textAlternatives[0])

class DalSegnoAlCoda(RepeatExpressionCommand):
    '''

    >>> from music21 import *
    >>> rm = repeat.DaCapoAlCoda() 
    '''
    def __init__(self):
        RepeatExpressionCommand.__init__(self)
        self._textAlternatives = ['Dal Segno al Coda', 'D.S. al Coda']
        self.setText(self._textAlternatives[0])




    
#-------------------------------------------------------------------------------
# store a list of one each of RepeatExpression objects; these are used for t
# testing TextExpressions 
repeatExpressionReference = [Coda(), Segno(), Fine(), DaCapo(), DaCapoAlFine(), 
    DaCapoAlCoda(), AlSegno(), DalSegnoAlFine(), DalSegnoAlCoda()]




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
        self._srcMeasureCount = len(self._srcMeasureStream)
        if self._srcMeasureCount == 0:
            raise ExpanderException('no measures found in the source stream to be expanded')

        # store counts of all non barline elements.
        reStream = self._srcMeasureStream.flat.getElementsByClass(
                RepeatExpression)
        self._codaCount = len(reStream.getElementsByClass(Coda))
        self._segnoCount = len(reStream.getElementsByClass(Segno))

        self._dcCount = len(reStream.getElementsByClass(DaCapo))
        self._dcafCount = len(reStream.getElementsByClass(DaCapoAlFine))
        self._dcacCount = len(reStream.getElementsByClass(DaCapoAlCoda))

        self._asCount = len(reStream.getElementsByClass(AlSegno))
        self._dsafCount = len(reStream.getElementsByClass(DalSegnoAlFine))
        self._dsacCount = len(reStream.getElementsByClass(DalSegnoAlCoda))


    def _stripRepeatBarlines(self, m, newStyle='light-light'):
        '''Strip barlines if they are repeats, and replace with Barlines that are of the same style. Modify in place.
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


    def _daCapoIsCoherent(self):
        '''Check of a DC statement is coherent.
        '''
        # get all repeatExpression objects 
        reStream = self._srcMeasureStream.flat.getElementsByClass(
                RepeatExpression)

        # note that the offsets of these streams are as found in the flat score
        # this can be used to determine characteristics
        environLocal.printDebug(['_daCapoIsCoherent', 'dcCount', self._dcCount, 'dcafCount', self._dcafCount, 'dcacCount', self._dcacCount])
        # there can be only one da capo statement for the provided span
        sumDc = self._dcCount + self._dcafCount + self._dcacCount
        if sumDc > 1:
            return False
        if sumDc == 1:
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


    def _getEndObjects(self, streamObj, index):
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

    def _processInnermostRepeat(self, streamObj):
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
                mLast, mEndBarline, repeatTimes = self._getEndObjects(
                    streamObj, repeatIndices[-1])
                for times in range(repeatTimes):
                    environLocal.printDebug(['repeat times:', times])    
                # copy the range of measures; this will include the first
                    # do indices directly
                    for j in repeatIndices:
                        mSub = copy.deepcopy(streamObj[j])
                        # must do for each pass, b/c not changing source
                        # stream
                        #environLocal.printDebug(['got j, repeatIndicies', j, repeatIndices])
                        if j in [repeatIndices[0], repeatIndices[-1]]:
                            self._stripRepeatBarlines(mSub)
                        mSub.number = number
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



    def isExpandable(self):
        '''Return True or False if this Stream is expandable.
        '''
        if not self._repeatBarsAreCoherent():
            return False
        return True


    def process(self):
        if not self.isExpandable():
            raise ExpanderException('cannot expand Stream: badly formed repeats')

        post = copy.deepcopy(self._srcMeasureStream)

        # cyclically process inntermost, one at a time
        while True:
            #environLocal.printDebug(['process(): top of loop'])
            #post.show('t')
            post = self._processInnermostRepeat(post)
            #post.show('t')
            if self._hasRepeat(post):                        
                environLocal.printDebug([
                    'process() calling: self._findInnermostRepeatIndices(post)', self._findInnermostRepeatIndices(post)])
            else:
                break # nothing left to process
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



    def testRepeatCoherneceA(self):
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


    def testRepeatCoherneceB(self):
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
            
        self.assertEqual(str(features.vectorById(s, 'p20')), '[1.0, 0.33333333333333331, 0.0, 1.0, 0.33333333333333331, 0.0, 1.0, 0.33333333333333331, 0.0, 1.0, 0.33333333333333331, 0.0]')
        
        #s.show()    
        
        s1 = s.expandRepeats()
        self.assertEqual(len(s1), 18)            
        # first bar is an A, but repeat is zero, will be removed
        self.assertEqual(str(s1.flat.pitches[0]), 'C3')
        
        self.assertEqual(str(features.vectorById(s1, 'p20')), '[0.20000000000000001, 0.066666666666666666, 0.0, 0.59999999999999998, 0.20000000000000001, 0.0, 1.0, 0.33333333333333331, 0.0, 0.0, 0.0, 0.0]')
        
        
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
        #s.show()

        ex = Expander(s)
        self.assertEqual(ex._daCapoIsCoherent(), True)

        # test incorrect da capo
        sAlt1 = copy.deepcopy(s)
        sAlt1[1].append(DaCapoAlFine())
        ex = Expander(sAlt1)
        self.assertEqual(ex._daCapoIsCoherent(), False)



if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

