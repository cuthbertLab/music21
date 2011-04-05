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

class RepeatExpression(RepeatMark, expressions.Expression):
    '''
    This class models any mark added to a Score to mark repeat start and end points that are designated by expressions. 
    '''
    def __init__(self):
        expressions.Expression.__init__(self)



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

# finale represents fine as a text expression <words> tag:
#       <direction placement="above">
#         <direction-type>
#           <words default-x="255" default-y="16" font-size="12" font-weight="bold" justify="right">Fine</words>
#         </direction-type>
#       </direction>

#d.s. indicatinos are also <word> tags

#       <direction placement="above">
#         <direction-type>
#           <words default-x="353" default-y="23" font-size="12" font-weight="bold" justify="right">D.C. al Coda</words>
#         </direction-type>
#       </direction>


# segno is represetned as follows:
#       <direction placement="above">
#         <direction-type>
#           <segno default-x="-2" default-y="18"/>
#         </direction-type>
#         <sound divisions="1" segno="2"/>
#       </direction>

# coda also has a tag
#       <direction placement="above">
#         <direction-type>
#           <coda default-x="-2" default-y="28"/>
#         </direction-type>
#         <sound coda="5" divisions="1"/>
#       </direction>




class ExpanderException(Exception):
    pass

class Expander(object):
    '''Expand a single Part or Part-like stream.
    '''

    def __init__(self, streamObj):
        self._src = streamObj
        # get and store the source measure count
        self._srcMeasureStream = self._src.getElementsByClass('Measure')
        self._srcMeasureCount = len(self._srcMeasureStream)
        
        if self._srcMeasureCount == 0:
            raise ExpanderException('no measures found in the source stream to be expanded')

    def _stripRepeatBarlines(self, m):
        '''Strip barlines if they are repeats, and replace with Barlines that are of the same style. Modify in place.
        '''
        # bar import repeat to make Repeat inherit from RepeatMark
        from music21 import bar

        lb = m.leftBarline
        rb = m.rightBarline

        if lb is not None and 'Repeat' in lb.classes:
            if lb.style in [None, 'none']:
                m.leftBarline = None
            else:
                environLocal.printDebug(['Expander._stripRepeatBarlines: add new left barline based on style:', lb.style])
                m.leftBarline = bar.Barline(lb.style)

        if rb is not None and 'Repeat' in rb.classes:
            if rb.style in [None, 'none']:
                m.rightBarline = None
            else:
                m.rightBarline = bar.Barline(rb.style)


    def repeatBarsAreCoherent(self):
        '''Check that all repeat bars are paired properly.
        '''
        # TODO: add case where we have a end, but not a start at the beginning
        # of a work
        startCount = 0
        endCount = 0

        repeatOpen = 0 # increment decrement for open close
        repeatBadOrder = False

        for m in self._srcMeasureStream:
            lb = m.leftBarline
            rb = m.rightBarline
            
            if lb is not None and 'Repeat' in lb.classes:
                if lb.direction == 'start':
                    startCount += 1
                    # if we try to open a new repeat and we have not closed
                    # an old start yet, then we have a problem
                    if repeatOpen == 1:
                        repeatBadOrder = True
                        break
                    repeatOpen += 1
                else:
                    raise ExpanderException('a left barline is found that cannot be processed: %s, %s' % (m, lb))

            if rb is not None and 'Repeat' in rb.classes:
                if rb.direction == 'end':
                    endCount += 1
                    if repeatOpen != 1:
                        repeatBadOrder = True
                        break
                    repeatOpen -= 1 # should now be zero
                else:
                    raise ExpanderException('a right barline is found that cannot be processed: %s, %s' % (m, rb))

        if repeatBadOrder:
            environLocal.printDebug(['found repeats that are started before being ended, or vice versa: %s' % (m)])
            return False
        if startCount != endCount:
            return False

        environLocal.printDebug(['matched start and end repeat barline count of: %s/%s' % (startCount, endCount)])
        return True

    


    def process(self):
        '''Process and return a new Stream.
        '''

        new = self._src.__class__()

        # need to gather everything that is not a Meausre (e.g., Instrument)
        # and add copies to new
        
        # renumber measures starting with the first number found here
        number = self._srcMeasureStream[0].number
        if number is None:
            number = 1
        # may define space not covered by a coda
        codaGapIndices = []
        segnoIndex = []

        # bar designated repeat
        barRepeatIndices = []
        barRepeatOpen = False
        # use index values instead of an interator
        for i in range(self._srcMeasureCount):
            m = copy.deepcopy(self._srcMeasureStream[i])

            lb = m.leftBarline
            rb = m.rightBarline

            if (lb is not None and 'Repeat' in lb.classes and 
                lb.direction == 'start'):
                barRepeatIndices.append(i)
                barRepeatOpen = True
            elif barRepeatOpen:
                barRepeatIndices.append(i)

            # after looking at the left barline, we can
            m.number = number
            new.append(m)
            number += 1

            if (rb is not None and 'Repeat' in rb.classes and 
                rb.direction == 'end'):
                # handle case of a repeat given after the first bar
                # without a start repeat
                if not barRepeatOpen and len(barRepeatIndices) == 0:
                    # get from first to this one
                    barRepeatIndices = range(0, i+1)
                else: # normal case, detected a start
                    # must test as may have been added above
                    if i not in barRepeatIndices:                    
                        barRepeatIndices.append(i)

                # TODO: check for times; if found, multiply indices
                barRepeatOpen = False

            # strip now, after processing (will change in place)
            self._stripRepeatBarlines(m)

            # if bar repeat open has been closed, and we have repeat
            # bar indices ready for processing, add these new measures
            if not barRepeatOpen and len(barRepeatIndices) > 0:
                for j in barRepeatIndices:
                    mSub = copy.deepcopy(self._srcMeasureStream[j])
                    self._stripRepeatBarlines(mSub)
                    mSub.number = number
                    new.append(mSub)
                    number += 1
                barRepeatIndices = []

        return new



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
        self.assertEqual(len(post.flat.notes), 16)
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

        ex = repeat.Expander(s)
        post = ex.process()

        self.assertEqual(len(post.getElementsByClass('Measure')), 5)
        self.assertEqual(len(post.flat.notes), 20)
        self.assertEqual([m.offset for m in post.getElementsByClass('Measure')], [0.0, 4.0, 8.0, 12.0, 16.0])
        self.assertEqual([n.nameWithOctave for n in post.flat.getElementsByClass('Note')], ['G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'F3', 'F3', 'F3', 'F3', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4'])

#         post.show('t')
#         post.show()
        

    def testExpandRepeatB(self):
        from music21.abc import testFiles
        from music21 import converter
        
        s = converter.parse(testFiles.draughtOfAle)
        #s.show()
        post = s.expand()
        # add tests
        #post.show()

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

        # check coherance
        ex = repeat.Expander(s)
        self.assertEqual(ex.repeatBarsAreCoherent(), False)


        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        #m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()
        m2.leftBarline = bar.Repeat(direction='start')
        #m2.rightBarline = bar.Repeat(direction='end', times=2)
        m2.repeatAppend(note.Note('d4', quarterLength=1), 4)

        m3 = stream.Measure()
        #m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end', times=2)
        m3.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m4 = stream.Measure()
        #m4.leftBarline = bar.Repeat(direction='start')
        m4.rightBarline = bar.Repeat(direction='end', times=2)
        m4.repeatAppend(note.Note('d4', quarterLength=1), 4)


        s.append(m1)
        s.append(m2)
        s.append(m3)
        s.append(m4)

        # check coherance
        ex = repeat.Expander(s)
        self.assertEqual(ex.repeatBarsAreCoherent(), False)



if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

