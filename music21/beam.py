# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         beam.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

'''
The module defines Beam and Beams (note plural) objects.

The Beams object holds multiple Beam objects (e.g., a 32nd note might
have three Beam objects in its Beam object).

The Beams object is stored in :class:`~music21.note.Note` 
and :class:`~music21.chord.Chord` objects as their 
:attr:`~music21.note.Note.beams` attributes.   Beams objects can
largely be treated as a list.

See `meter.TimeSignature`.:meth:`~music21.meter.TimeSignature.getBeams` for a way of getting
beam information for a measure given the meter.  
The `meter.TimeSignature`.:attr:`~music21.meter.TimeSignature.beamSequence`
attribute holds information about how to beam given the TimeSignature

Run `stream.Stream`.:meth:`~music21.stream.Stream.makeBeams` to set beaming information
automatically given the current meter.


Suppose you had a measure of two eighths and a quarter and wanted to explicitly beam the two eighth notes.
You could do this:

>>> from music21 import *
>>> m = stream.Measure()
>>> n1 = note.Note('C4', quarterLength = 0.5)
>>> n2 = note.Note('D4', quarterLength = 0.5)
>>> n3 = note.Note('E4', quarterLength = 1.0)
>>> m.append(n1)
>>> m.append(n2)
>>> m.append(n3)
>>> n1.beams.fill('eighth', type='start')
>>> n2.beams.fill('eighth', type='stop')
>>> n1.beams
<music21.beam.Beams <music21.beam.Beam 1/start>>
>>> n2.beams
<music21.beam.Beams <music21.beam.Beam 1/stop>>


But suppose you wanted something harder: two 16ths, an 8th, a quarter, 
with the first 3 notes beamed?  The first note and 3rd are easy to do, using the
method above:

>>> m = stream.Measure()
>>> n1 = note.Note('C4', quarterLength = 0.25)
>>> n2 = note.Note('D4', quarterLength = 0.25)
>>> n3 = note.Note('E4', quarterLength = 0.5)
>>> n4 = note.Note('F4', quarterLength = 1.0)
>>> for n in [n1, n2, n3, n4]:
...     m.append(n)
>>> n1.beams.fill('16th', type='start')
>>> n3.beams.fill('eighth', type='stop')

but the second note has an 8th beam that continues and a 16th beam that stops.  So you will need to set them separately:

>>> n2.beams.append('continue')
>>> n2.beams.append('stop')
>>> n2.beams
<music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>

To get rid of beams on a note do:

>>> n2.beams.beamsList = []

'''

import unittest, doctest

import music21
from music21 import common
from music21 import duration
from music21 import musicxml
musicxmlMod = musicxml # alias


class BeamException(Exception):
    pass

class Beam(music21.JSONSerializer):
    '''
    A Beam is an object representation of one single beam, that is, one horizontal
    line connecting two notes together (or less commonly a note to a rest).  Thus it
    takes two separate Beam objects to represent the beaming of a 16th note.  
    
    The Beams object (note the plural) is the object that handles groups of Beam objects;
    it is defined later on.
    
    Here are two ways to define the start of a beam
    >>> from music21 import *
    >>> b1 = beam.Beam(type = 'start')
    >>> b2 = beam.Beam('start')
    
    Here is a partial beam (that is, one that does not
    connect to any other note, such as the second beam of
    a dotted eighth, sixteenth group)
    
    Two ways of doing the same thing
    >>> b3 = beam.Beam(type = 'partial', direction = 'left')
    >>> b4 = beam.Beam('partial', 'left')
    >>> b4.number = 1
    
    >>> print b4
    <music21.beam.Beam 1/partial/left>
    >>> print b2
    <music21.beam.Beam None/start>
    '''

    def __init__(self, type = None, direction = None):
        self.type = type # start, stop, continue, partial
        self.direction = direction # left or right for partial
        self.independentAngle = None
        # represents which beam line referred to
        # 8th, 16th, etc represented as 1, 2, ...
        self.number = None 

    def jsonAttributes(self):
        '''
        Define all attributes of this object that should be JSON serialized for storage and re-instantiation.
        
        >>> from music21 import *
        >>> print beam.Beam().jsonAttributes()
        ['type', 'direction', 'independentAngle', 'number']
        '''
        # add to base class
        return ['type', 'direction', 'independentAngle', 'number']

    def __repr__(self):
        if self.direction == None:
            return '<music21.beam.Beam %s/%s>' % (self.number, self.type)
        else:
            return '<music21.beam.Beam %s/%s/%s>' % (self.number, self.type, self.direction)        


    def _getMX(self):
        '''

        >>> from music21 import *
        >>> a = beam.Beam()
        >>> a.type = 'start'
        >>> a.number = 1
        >>> b = a.mx
        >>> b.get('charData')
        'begin'
        >>> b.get('number')
        1

        >>> a.type = 'continue'
        >>> b = a.mx
        >>> b.get('charData')
        'continue'

        >>> a.type = 'stop'
        >>> b = a.mx
        >>> b.get('charData')
        'end'

        >>> a.type = 'partial'
        >>> a.direction = 'left'
        >>> b = a.mx
        >>> b.get('charData')
        'backward hook'

        >>> a.direction = 'right'
        >>> b = a.mx
        >>> b.get('charData')
        'forward hook'

        >>> a.direction = None
        >>> b = a.mx
        Traceback (most recent call last):
        BeamException: partial beam defined without a direction set (set to None)

        >>> a.type = 'crazy'
        >>> b = a.mx
        Traceback (most recent call last):
        BeamException: unexpected beam type encountered (crazy)
        '''
        mxBeam = musicxmlMod.Beam()
        if self.type == 'start':
            mxBeam.set('charData', 'begin') 
        elif self.type == 'continue':
            mxBeam.set('charData', 'continue') 
        elif self.type == 'stop':
            mxBeam.set('charData', 'end') 
        elif self.type == 'partial':
            if self.direction == 'left':
                mxBeam.set('charData', 'backward hook')
            elif self.direction == 'right':
                mxBeam.set('charData', 'forward hook') 
            else:
                raise BeamException('partial beam defined without a direction set (set to %s)' % self.direction)
        else:
            raise BeamException('unexpected beam type encountered (%s)' % self.type)

        mxBeam.set('number', self.number)
        return mxBeam


    def _setMX(self, mxBeam):
        '''given a list of mxBeam objects

        >>> from music21 import *
        >>> mxBeam = musicxmlMod.Beam()
        >>> mxBeam.set('charData', 'begin')
        >>> a = beam.Beam()
        >>> a.mx = mxBeam
        >>> a.type
        'start'

        >>> mxBeam.set('charData', 'continue')
        >>> a.mx = mxBeam
        >>> a.type
        'continue'

        >>> mxBeam.set('charData', 'end')
        >>> a.mx = mxBeam
        >>> a.type
        'stop'

        >>> mxBeam.set('charData', 'forward hook')
        >>> a.mx = mxBeam
        >>> a.type
        'partial'
        >>> a.direction
        'right'

        >>> mxBeam.set('charData', 'backward hook')
        >>> a.mx = mxBeam
        >>> a.type
        'partial'
        >>> a.direction
        'left'

        >>> mxBeam.set('charData', 'crazy')
        >>> a.mx = mxBeam
        Traceback (most recent call last):
        BeamException: unexpected beam type encountered (crazy)
        '''

        mxType = mxBeam.get('charData')
        if mxType == 'begin':
            self.type = 'start'
        elif mxType == 'continue':
            self.type = 'continue'
        elif mxType == 'end':
            self.type = 'stop'
        elif mxType == 'forward hook':
            self.type = 'partial'
            self.direction = 'right'
        elif mxType == 'backward hook':
            self.type = 'partial'
            self.direction = 'left'
        else:
            raise BeamException('unexpected beam type encountered (%s)' % mxType)

    mx = property(_getMX, _setMX)    


#-------------------------------------------------------------------------------
class Beams(music21.JSONSerializer):
    '''
    The Beams object stores in it attribute beamsList (a list) all
    the Beam objects defined above.  Thus len(beam.Beams) tells you how many
    beams the note currently has on it, and iterating over a Beams object gives 
    you each Beam.
    
    >>> from music21 import *
    >>> n = note.Note(type='16th')
    >>> isinstance(n.beams, beam.Beams)
    True
    >>> n.beams.fill(2, 'start')
    >>> len(n.beams)
    2
    >>> for thisBeam in n.beams:
    ...     thisBeam.type
    'start'
    'start'

    >>> print n.beams
    <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    '''
    _DOC_ATTR = {
    'feathered': 'Boolean determining if this is a feathered beam or not (does nothing for now).',
    }
    def __init__(self):
        self.beamsList = []
        self.feathered = False

    def jsonAttributes(self):
        '''
        Define all attributes of this object that should be JSON serialized for storage and re-instantiation.
        
        >>> from music21 import *
        >>> beam.Beams().jsonAttributes()
        ['beamsList', 'feathered']
        '''
        # add to base class
        return ['beamsList', 'feathered']

    def __iter__(self):
        return common.Iterator(self.beamsList)

    def __len__(self):
        return len(self.beamsList)

    def __repr__(self):
        msg = []
        for beam in self.beamsList:
            msg.append(str(beam))        
        return '<music21.beam.Beams %s>' % '/'.join(msg)


    def append(self, type=None, direction=None):
        '''
        Append a new Beam object to this Beams, automatically creating the Beam object and incrementing the number count. 
        
        >>> from music21 import *
        >>> beams = beam.Beams()
        >>> beams.append('start')
        >>> beams.beamsList
        [<music21.beam.Beam 1/start>]
        >>> beams.append('partial', 'right')
        >>> beams.beamsList
        [<music21.beam.Beam 1/start>, <music21.beam.Beam 2/partial/right>]
        '''
        obj = Beam(type, direction)
        obj.number = len(self.beamsList) + 1
        self.beamsList.append(obj)


    def fill(self, level=None, type=None):
        '''
        A quick way of setting the beams list for a particular duration,
        for instance, fill("16th") will clear the current list of beams in the
        Beams object and add two beams.  fill(2) will do the same (though note
        that that is an int, not a string).
        
        It does not do anything to the direction that the beams are going in, or by default.
        Either set type here or call setAll() on the Beams object afterwards.
        
        Both "eighth" and "8th" work.  Adding more than six beams (i.e. things like
        512th notes) raises an error.

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> len(a)
        2
        
        >>> a.fill('32nd', type='start')
        >>> len(a)
        3
        >>> a.beamsList[2]
        <music21.beam.Beam 3/start>
        >>> a.beamsList[2].type
        'start'


        Filling a smaller number wipes larger numbers of beams:
        >>> a.fill('eighth', type='start')
        >>> len(a)
        1

        OMIT_FROM_DOCS
        >>> a.fill(4)
        >>> len(a)
        4
        >>> a.fill('128th')
        >>> len(a)
        5
        >>> a.fill('256th')
        >>> len(a)
        6
        >>> a.fill(7)
        Traceback (most recent call last):
        BeamException: cannot fill beams for level 7
        '''
        self.beamsList = []
        # 8th, 16th, etc represented as 1, 2, ...
        if level in [1, '8th', duration.typeFromNumDict[8]]: # eighth
            count = 1
        elif level in [2, duration.typeFromNumDict[16]]:
            count = 2
        elif level in [3, duration.typeFromNumDict[32]]:
            count = 3
        elif level in [4, duration.typeFromNumDict[64]]:
            count = 4
        elif level in [5, duration.typeFromNumDict[128]]:
            count = 5
        elif level in [6, duration.typeFromNumDict[256]]:
            count = 6
        else:
            raise BeamException('cannot fill beams for level %s' % level)

        for i in range(1, count+1):
            if i == 0: raise Exception

            obj = Beam()
            obj.number = i
            self.beamsList.append(obj)

        if type is not None:
            self.setAll(type)

    def setAll(self, type, direction=None):
        '''
        setAll is a method of convenience that sets the type 
        of each of the beam objects within the beamsList to the specified type.
        It also takes an optional "direction" attribute that sets the direction
        for each beam (otherwise the direction of each beam is set to None)
        Acceptable directions (start, stop, continue, etc.) are listed under 
        Beam() above.

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.getTypes()
        ['start', 'start']

        >>> a.setAll('sexy')
        Traceback (most recent call last):
        BeamException: beam type cannot be sexy
        '''
        if type not in ['start', 'stop', 'continue', 'partial']:
            raise BeamException('beam type cannot be %s' %  type)
        for beam in self.beamsList:
            beam.type = type
            beam.direction = direction

    def setByNumber(self, number, type, direction=None):
        '''Set an internal beam object by number, or rhythmic symbol level

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.setByNumber(1, 'continue')
        >>> a.beamsList[0].type
        'continue'
        >>> a.setByNumber(2, 'stop')
        >>> a.beamsList[1].type
        'stop'
        >>> a.setByNumber(2, 'partial-right')
        >>> a.beamsList[1].type
        'partial'
        >>> a.beamsList[1].direction
        'right'


        >>> a.setByNumber(30, 'stop')
        Traceback (most recent call last):
        IndexError: beam number 30 cannot be accessed

        >>> a.setByNumber(2, 'crazy')
        Traceback (most recent call last):
        BeamException: beam type cannot be crazy
        '''
        # permit providing one argument hyphenated
        if '-' in type:
            type, direction = type.split('-')

        if type not in ['start', 'stop', 'continue', 'partial']:
            raise BeamException('beam type cannot be %s' % type)

        if number not in self.getNumbers():
            raise IndexError('beam number %s cannot be accessed' % number)

        for i in range(len(self)):
            if self.beamsList[i].number == number:
                self.beamsList[i].type = type
                self.beamsList[i].direction = direction


    def getByNumber(self, number):
        '''Gets an internal beam object by number...

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.getByNumber(2).type
        'start'
        
        >>> a.getByNumber(30)
        Traceback (most recent call last):
        IndexError: beam number 30 cannot be accessed
        '''
        if number not in self.getNumbers():
            raise IndexError('beam number %s cannot be accessed' % number)

        for i in range(len(self)):
            if self.beamsList[i].number == number:
                return self.beamsList[i]

    def getTypeByNumber(self, number):
        '''Get beam type, with direction, by number

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.setByNumber(2, 'partial-right')
        >>> a.getTypeByNumber(2)
        'partial-right'
        >>> a.getTypeByNumber(1)
        'start'
        '''
        beamObj = self.getByNumber(number)
        if beamObj.direction == None:
            return beamObj.type
        else:
            return '%s-%s' % (beamObj.type, beamObj.direction)
            

    def getTypes(self):
        '''Returns a list of all beam types defined for the current beams

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('16th')
        >>> a.setAll('start')
        >>> a.getTypes()
        ['start', 'start']
        '''
        return [x.type for x in self.beamsList]

    def getNumbers(self):
        '''Returns a list of all defined beam numbers; it should normally be
        a set of consecutive integers, but it might not be.

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill('32nd')
        >>> a.getNumbers()
        [1, 2, 3]
        '''
        return [x.number for x in self.beamsList]


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''
        Returns a list of mxBeam objects

        >>> from music21 import *
        >>> a = beam.Beams()
        >>> a.fill(2, type='start')
        >>> mxBeamList = a.mx
        >>> len(mxBeamList)
        2
        '''
        mxBeamList = []
        for beamObj in self.beamsList:
            mxBeamList.append(beamObj.mx)
        return mxBeamList

    def _setMX(self, mxBeamList):
        '''given a list of mxBeam objects, sets the beamsList

        >>> from music21 import *
        >>> mxBeamList = []
        >>> a = beam.Beams()
        >>> a.mx = mxBeamList
        '''
        for mxBeam in mxBeamList:
            beamObj = Beam()
            beamObj.mx = mxBeam
            self.beamsList.append(beamObj)

    mx = property(_getMX, _setMX)    




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Beams, Beam]


if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

