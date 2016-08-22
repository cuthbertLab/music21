# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         medren.py
# Purpose:      classes for dealing with medieval and Renaissance Music
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Tools for working with medieval and Renaissance music -- see also the 
trecento directory which works particularly on 14th-century Italian
music. Objects representing the punctus and the divisione can be found there.
'''
import copy
import unittest

from music21 import bar
from music21 import base
from music21 import clef
from music21 import common
from music21 import duration
from music21 import exceptions21
from music21 import interval
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
from music21 import tempo
from music21.alpha import trecento

from music21 import environment
environLocal = environment.Environment('medren')

allowableStrettoIntervals = { 
        -8: [(3, True), 
             (-3, True),
             (5, False),
             (-4, False),
             (1, True)],
        8:  [(3, True), 
             (-3, True),
             (5, False),
             (4, False),
             (1, True)],
        -5: [(-3, True), 
             (-5, False),
             (2, True),
             (4, False),
             (1, True)],
        5:  [(3, True), 
             (5, False),
             (-2, True),
             (-4, False),
             (1, True)],
        -4: [(3, True), 
             (5, False),
             (2, False),
             (-2, True),
             (-4, False)],
        4:  [(-3, True), 
             (-5, False),
             (2, True),
             (-2, False),
             (4, False)],
    }

_validMensuralTypes = [None,'maxima', 'longa', 'brevis', 'semibrevis', 'minima', 'semiminima']
_validMensuralAbbr = [None, 'Mx', 'L', 'B', 'SB', 'M', 'SM']


#---------------------------------------------------------------------------------
class MensuralClef(clef.Clef):
    '''
    An object representing a mensural clef found in medieval and Renaissance music.
    
    >>> from music21.alpha import medren
    
    >>> fclef = medren.MensuralClef('F')
    >>> fclef.line
    3
    >>> fclef.fontString 
    '0x5c'
    '''
    
    def __init__(self, sign = 'C'):
        clef.Clef.__init__(self)
        self._line = None
        self._fontString = None
        
        if sign == 'C':
            self.sign = sign
            self._line = 4
        elif sign == 'F':
            self.sign = sign
            self._line = 3
        else:
            raise MedRenException('A %s-clef is not a recognized mensural clef'  % sign)
            
    def _getLine(self):
        return self._line
    
    def _setLine(self, line):
        self._line = line
    
    line = property(_getLine, _setLine,
                    doc = '''The staff line the clef resides on''')
    
    @property
    def fontString(self):
        '''Returns the utf-8 code corresponding to the 
                              mensural clef in Ciconia font'''
        if self.sign == 'C':
            self._fontString = '0x4b'
        else:
            self._fontString = '0x5c'
        return self._fontString


class Mensuration(meter.TimeSignature):
    '''
    An object representing a mensuration sign found in French notation.
    Takes four optional arguments: tempus, prolation, mode, and maximode. 
    Defaults are 'perfect', 'minor', 'perfect', and None respectively.
    
    Valid values for tempus and mode are 'perfect' and 'imperfect'. 
    Valid values for prolation and maximode are 'major' and 'minor'.
    
    >>> from music21.alpha import medren
    
    >>> ODot = medren.Mensuration(tempus = 'perfect', prolation = 'major')
    >>> ODot.standardSymbol
    'O-dot'
    >>> ODot.fontString
    '0x50'
    '''
    
    def __init__(self, tempus='perfect', prolation='minor', mode='perfect', 
                 maximode=None, scalingFactor=4):
        self.tempus = tempus
        self.prolation = prolation
        self.mode = mode
        self.maximode = maximode
        # self._scalingFactor = scalingFactor still don't get why this is here...
        self._fontString = ''
        self.timeString = None
        self._minimaPerBrevis = 0
        
        if tempus == 'perfect' and prolation == 'major':
            self.timeString = '9/8'
            self.standardSymbol = 'O-dot'
            self._fontString = '0x50'
            self._minimaPerBrevis = 9
        elif tempus == 'perfect' and prolation == 'minor':
            self.timeString = '6/8'
            self.standardSymbol = 'C-dot'
            self._fontString = '0x63'
            self._minimaPerBrevis = 6
        elif tempus == 'imperfect' and prolation == 'major':
            self.timeString = '3/4'
            self.standardSymbol = 'O'
            self._fontString = '0x4f'
            self._minimaPerBrevis = 6
        elif tempus == 'imperfect' and prolation == 'minor':
            self.timeString = '2/4'
            self.standardSymbol = 'C'
            self._fontString = '0x43'
            self._minimaPerBrevis = 4
        else:
            raise MedRenException(
                'cannot make out the mensuration from tempus %s and prolation %s' % 
                (tempus, prolation)) 

        meter.TimeSignature.__init__(self, self.timeString)
        
    def __str__(self):
        return '<music21.medren.Mensuration %s>' % self.standardSymbol
    
    def __repr__(self):
        return str(self)
    
    def _getMinimaPerMeasure(self):
        return self._minimaPerBrevis
    
    def _setMinimaPerMeasure(self, mPM):
        self._minimaPerBrevis = mPM
    
    minimaPerBrevis = property(_getMinimaPerMeasure, _setMinimaPerMeasure,
                                doc = '''Used to get or set the number of minima in a 
                                'measure' under the given mensuration.
                                        
                                >>> from music21.alpha import medren
                                
                                >>> c = medren.Mensuration('imperfect', 'minor')
                                >>> c.minimaPerBrevis
                                4
                                >>> c.minimaPerBrevis = 8
                                >>> c.minimaPerBrevis
                                8
                                ''')
    
    @property
    def fontString(self):
        '''
        The utf-8 code corresponding to the mensuration character in Ciconia font 
          
        TODO: Convert to SMuFL
        
        >>> from music21.alpha import medren
        
        >>> O = medren.Mensuration('imperfect', 'major')
        >>> O.fontString
        '0x4f'
        '''
        return self._fontString

#    def _getScalingFactor(self):
#        return self._scalingFactor
    
#    def _setScalingFactor(self, newScalingFactor):
#        pass

class GeneralMensuralNote(base.Music21Object):
    '''
    The base class object for :class:`music21.medren.MensuralNote` and 
    :class:`music21.medren.MensuralRest`. This is arguably the most important mensural object, 
    since it is responsible for getting the context and determining the contextual duration of 
    objects within both subclasses.
    A :class:`music21.medren.GeneralMensuralNote` object takes a mensural type or its 
    abbreviation as an argument. The default value for this argument is 'brevis'.
    
    Valid mensural types are 'maxima', 'longa', 'brevis', 'semibrevis', 'minima', and 'semiminima'.
    The corresponding abbreviations are 'Mx', 'L', 'B', 'SB', 'M', and 'SM'.
    
    The object's mensural type can be set and accessed via the property 
    :attr:`music21.medren.GeneralMensuralNote.mensuralType`.
    The duration of a general mensural note can be set and accessed using the property 
    :attr:`music21.medren.GeneralMensuralNote.duration`. If the duration of an general 
    mensural note cannot be determined from context, it is set to 0. For more specific 
    examples of this, please see the :attr:`music21.medren.GeneralMensuralNote.duration` 
    documentation.
    
    Two general mensural notes are considered equal if they have the same mensural type, 
    are present in the same context, and have the same offset within that context.
    '''
    def __init__(self, mensuralTypeOrAbbr = 'brevis'):
        base.Music21Object.__init__(self)
        self._gettingDuration = False
        self._duration = None
        if mensuralTypeOrAbbr in _validMensuralTypes:
            self._mensuralType = mensuralTypeOrAbbr
        elif mensuralTypeOrAbbr in _validMensuralAbbr:
            self.mensuralType = _validMensuralTypes[_validMensuralAbbr.index(mensuralTypeOrAbbr)]
        else:
            raise MedRenException('%s is not a valid mensural type or abbreviation' % 
                                  mensuralTypeOrAbbr)
        
        self.lenList = []
        
    
    def __repr__(self):
        return '<music21.medren.GeneralMensuralNote %s>' % self.mensuralType
    
    def __eq__(self, other):
        '''
        Essentially the same as music21.base.Music21Object.__eq__, but equality of 
        mensural type is tested rather than equality of duration
        
        >>> from music21.alpha import medren
        
        >>> m = medren.GeneralMensuralNote('minima')
        >>> n = medren.GeneralMensuralNote('brevis')
        >>> m == n
        False
        >>> n = medren.GeneralMensuralNote('minima')
        >>> m == n
        True
        >>> s_1 = stream.Stream()
        >>> s_1.append(m)
        >>> m == n
        False
        >>> s_1.append(n)
        >>> m == n
        True
        '''
        
        eq = hasattr(other, 'mensuralType')
        if eq:
            eq = eq and (self.mensuralType == other.mensuralType)
        if eq and hasattr(self, 'activeSite'):
            eq = eq and hasattr(other, 'activeSite')
            if eq:
                eq = eq and (self.activeSite == other.activeSite)
        if eq and hasattr(self, 'offset'):
            eq = eq and hasattr(other, 'offset')
            if eq:
                eq = eq and (self.offset == other.offset)
        return eq
    
    def _getMensuralType(self):
        return self._mensuralType
    
    def _setMensuralType(self, mensuralTypeOrAbbr):
        if mensuralTypeOrAbbr in _validMensuralTypes:
            self._mensuralType = mensuralTypeOrAbbr
        elif mensuralTypeOrAbbr in _validMensuralAbbr:
            self.mensuralType = _validMensuralTypes[_validMensuralAbbr.index(mensuralTypeOrAbbr)]
        else:
            raise MedRenException('%s is not a valid mensural type or abbreviation' % 
                                  mensuralTypeOrAbbr)
    
    mensuralType = property(_getMensuralType, _setMensuralType,
                        doc = '''Name of the mensural length of the general mensural note 
                        (brevis, longa, etc.):
                        
                        >>> from music21.alpha import medren
                        
                        >>> gmn = medren.GeneralMensuralNote('maxima')
                        >>> gmn.mensuralType
                        'maxima'
                        >>> gmn_1 = medren.GeneralMensuralNote('SB')
                        >>> gmn_1.mensuralType
                        'semibrevis'
                        >>> gmn_2 = medren.GeneralMensuralNote('blah')
                        Traceback (most recent call last):
                        MedRenException: blah is not a valid mensural type or abbreviation
                        ''')
    
    def updateDurationFromMensuration(self, mensuration=None, surroundingStream=None):
        '''
        The duration of a :class:`music21.medren.GeneralMensuralNote` object can be accessed 
        and set using the :attr:`music21.medren.GeneralMensuralNote.duration` property. 
        The duration of a general mensural note is by default 0. If the object's subclass 
        is not specified (:class:`music21.medren.MensuralNote` or 
        :class:`music21.medren.MensuralRest`), the duration will remain 0 unless set to 
        some other value.
        If a general mensural note has no context, the duration will remain 0 since 
        duration is context dependant. 
        Finally, if a mensural note or a mensural rest has context, but a 
        mensuration or divisione cannot be found or determined from that context, 
        the duration will remain 0.
        
        Every time a duration is changed, the method 
        :meth:`music21.medren.GeneralMensuralNote.updateDurationFromMensuration`` should be called.
        
        >>> from music21.alpha import medren
        
        >>> mn = medren.GeneralMensuralNote('B')
        >>> mn.duration.quarterLength
        0.0
        >>> mn = medren.MensuralNote('A', 'B')
        >>> mn.duration.quarterLength
        0.0
        
        However, if subclass is given, context (a stream) is given, and a mensuration or 
        divisione is given, duration can be determined.
        
        >>> from music21.alpha import medren
        >>> from music21.alpha import trecento
        
        >>> s = stream.Stream()
        >>> s.append(trecento.notation.Divisione('.p.'))
        >>> for i in range(3):
        ...    s.append(medren.MensuralNote('A', 'SB'))
        >>> s.append(trecento.notation.Punctus())
        >>> s.append(medren.MensuralNote('B', 'SB'))
        >>> s.append(medren.MensuralNote('B', 'SB'))
        >>> s.append(trecento.notation.Punctus())
        >>> s.append(medren.MensuralNote('A', 'B'))
        >>> for mn in s:
        ...    if isinstance(mn, medren.GeneralMensuralNote):
        ...        mn.updateDurationFromMensuration(surroundingStream=s)
        ...        print(mn.duration.quarterLength)
        1.0
        1.0
        1.0
        1.0
        2.0
        3.0
        
        Note: French notation not yet supported.    
        '''
        mLen, mDur = 0, 0
        if self._gettingDuration is True:
            return duration.Duration(0.0)
        
        if mensuration is None:
            mOrD = self._determineMensurationOrDivisione()
            
        else:
            mOrD = mensuration
            
        index = self._getTranslator(mensurationOrDivisione=mOrD, 
                                    surroundingStream=surroundingStream)
        
        if self.lenList:
            if mOrD.standardSymbol in ['.q.', '.p.', '.i.', '.n.']:
                mDur = 0.5
            else:
                mDur = 0.25
            mLen = self.lenList[index]
        #print("MDUR! " + str(mDur) + "MLEN " + str(mLen) + "index " + str(index) +
        # " MEASURE " + str(self._getSurroundingMeasure()[0]))
            self.duration = duration.Duration(mLen*mDur)
        else:
            self.duration = duration.Duration(0.0)
    
    
    def _getTranslator(self, mensurationOrDivisione = None, surroundingStream = None):

        mOrD = mensurationOrDivisione
        if mOrD is None:
            mOrD = self._determineMensurationOrDivisione()
        measure, index = self._getSurroundingMeasure(mensurationOrDivisione=mOrD, 
                                                     activeSite=surroundingStream)
        
        self._gettingDuration = True
        if measure and 'Divisione' in mOrD.classes:
            if index == 0:
                self.lenList = trecento.notation.BrevisLengthTranslator(
                                    mOrD, measure).getKnownLengths()
            elif index != -1:
                tempMN = measure[0]
                self.lenList = tempMN.lenList
        self._gettingDuration = False
        return index
    
    #Using Music21Object.getContextByClass makes _getDuration go into 
    #an infinite loop. Thus, the alternative method. 
    def _determineMensurationOrDivisione(self):
        '''
        If the general mensural notes has context which contains a mensuration 
        or divisione sign, it returns the mensuration or divisione sign 
        closest to but before itself.
        
        Otherwise, it tries to determine the mensuration sign from the context. 
        
        If no mensuration sign can be determined, it throws an error.
        
        If no context is present, returns None.
        
        >>> from music21.alpha import medren
        >>> from music21.alpha import trecento
        
        >>> gmn = medren.GeneralMensuralNote('longa')
        >>> gmn._determineMensurationOrDivisione()
        >>> 
        >>> s_1 = stream.Stream()
        >>> s_2 = stream.Stream()
        >>> s_3 = stream.Stream()
        >>> s_3.insert(3, gmn)
        >>> s_2.insert(1, trecento.notation.Divisione('.q.'))
        >>> s_1.insert(2, medren.Mensuration('perfect', 'major'))
        >>> s_2.insert(2, s_3)
        >>> s_1.insert(3, s_2)
        >>> gmn._determineMensurationOrDivisione()
        <music21.alpha.trecento.notation.Divisione .q.>
        '''
        
        #mOrD = music21.medren._getTargetBeforeOrAtObj(self, 
        #        [Mensuration, trecento.notation.Divisione])
        searchClasses = (Mensuration, trecento.notation.Divisione)
        mOrD = self.getContextByClass(searchClasses)
        if mOrD is not None:
            return mOrD
        else:
            return None
#        if len(mOrD)> 0:
#            mOrD = mOrD[0] #Gets most recent M or D
#        else:
#            mOrD = None #TODO: try to determine mensuration for French Notation
#        
#        return mOrD
    
    def _getSurroundingMeasure(self, mensurationOrDivisione=None, activeSite=None):
        '''
        Returns a list of the objects (ordered by offset) that are within 
        the measure containing the general mensural note.
        If the general mensural note has no context, returns an empty list.
        If the general mensural note has more than one context, only the 
        surrounding measure of the first context is returned.
        
        >>> from music21.alpha import medren
        >>> from music21.alpha import trecento
        
        >>> s_1 = stream.Stream()
        >>> s_1.append(trecento.notation.Divisione('.p.'))
        >>> l = medren.MensuralNote('A', 'longa')
        >>> s_1.append(l)
        >>> for i in range(4):
        ...     s_1.append(medren.MensuralNote('B', 'minima'))
        >>> gmn_1 = medren.GeneralMensuralNote('minima')
        >>> s_1.append(gmn_1)
        >>> s_1.append(medren.MensuralNote('C', 'minima'))
        >>> s_1.append(trecento.notation.Punctus())
        >>> gmn_1._getSurroundingMeasure(activeSite = s_1)
        ([<music21.medren.MensuralNote minima B>, 
          <music21.medren.MensuralNote minima B>, 
          <music21.medren.MensuralNote minima B>, 
          <music21.medren.MensuralNote minima B>, 
          <music21.medren.GeneralMensuralNote minima>, 
          <music21.medren.MensuralNote minima C>], 4) 
        
        >>> s_2 = stream.Stream()
        >>> s_2.append(trecento.notation.Divisione('.p.'))
        >>> s_2.append(trecento.notation.Punctus())
        >>> s_2.append(medren.MensuralNote('A', 'semibrevis'))
        >>> s_2.append(medren.MensuralNote('B', 'semibrevis'))
        >>> gmn_2 = medren.GeneralMensuralNote('semibrevis')
        >>> s_2.append(gmn_2)
        >>> s_2.append(medren.Ligature(['A','B']))
        >>> gmn_2._getSurroundingMeasure(activeSite = s_2)
        ([<music21.medren.MensuralNote semibrevis A>, 
          <music21.medren.MensuralNote semibrevis B>, 
          <music21.medren.GeneralMensuralNote semibrevis>], 2)
        '''
        
        mOrD = mensurationOrDivisione
        if mOrD is None:
            mOrD = self._determineMensurationOrDivisione()
        
        if activeSite is None:
            site = self.activeSite
        else:
            site = activeSite
        
        if site is None:
            return [], -1
        if self.mensuralType in ['brevis', 'longa', 'maxima']:
            return [self], 0

        tempList = list(site.recurse())[1:]
        if site.isMeasure:
            return tempList, -1

        # else...
        mList = []
        currentIndex, index = -1, -1
        indOffset = 0 
        
        for ind, item in enumerate(tempList):
            if self is item:
                currentIndex = ind
                           
        for i in range(currentIndex-1, -1, -1):
            # Punctus and ligature marks indicate a new measure
            if (('Punctus' in tempList[i].classes) or 
                    ('Ligature' in tempList[i].classes)):
                indOffset = i+1
                break
            elif 'GeneralMensuralNote' in tempList[i].classes:
                # In Italian notation, brevis, longa, and maxima indicate a new measure
                if (('Divisione' in mOrD.classes) and
                        (tempList[i].mensuralType in ['brevis', 'longa', 'maxima'])):
                    indOffset = i+1
                    break
                else:
                    mList.insert(i, tempList[i])
            else:
                indOffset += 1
        
        mList.reverse()
        mList.insert(currentIndex, self)
        for j in range(currentIndex+1,len(tempList), 1):
            if (('Punctus' in tempList[j].classes) or 
                    ('Ligature' in tempList[j].classes)):
                break
            if 'GeneralMensuralNote' in tempList[j].classes:
                if (('Divisione' in mOrD.classes) and 
                        (tempList[j].mensuralType in ['brevis', 'longa', 'maxima'])):
                    break
                else:
                    mList.insert(j, tempList[j])
        
        index = currentIndex - indOffset        
        return mList, index
            
class MensuralRest(GeneralMensuralNote, note.Rest):
    '''
    An object representing a mensural rest. First argument is mensural type.
    The utf-8 code for the Ciconia font character can be accessed via the property 
    :attr:`music21.medren.MensuralNote.fontString`
    
    Additional methods regarding color, duration, equality, and mensural type are inherited from 
    :class:`music21.medren.GeneralMensuralNote`.
    '''
    
    # scaling?
    def __init__(self, *arguments, **keywords):
        note.Rest.__init__(self, *arguments, **keywords)
        GeneralMensuralNote.__init__(self)
        self._gettingDuration = False
        self._mensuralType = 'brevis'
        
        if arguments:
            tOrA = arguments[0]
            if tOrA in _validMensuralTypes:
                self._mensuralType = tOrA
            elif tOrA in _validMensuralAbbr:
                self._mensuralType = _validMensuralTypes[_validMensuralAbbr.index(tOrA)]
            else:
                raise MedRenException('%s is not a valid mensural type or abbreviation' % tOrA)
        
        self._duration = None
        self._fontString = ''
        if self.mensuralType == 'Longa':
            self._fontString = '0x30'
        elif self.mensuralType == 'brevis':
            self._fontString = '0x31'
        elif self.mensuralType == 'semibrevis':
            self._fontString = '0x32'
        elif self.mensuralType == 'minima':
            self._fontString = '0x33'
        
        self.lenList = []
        
    def __repr__(self):
        return '<music21.medren.MensuralRest %s>' % self.mensuralType  
    
    @property
    def fullName(self):
        msg = []
        msg.append(self.mensuralType)
        msg.append(' rest')
        return ''.join(msg)
       
    @property
    def fontString(self):
        ''' 
        The utf-8 code corresponding to the mensural rest 
        in Ciconia font.

        Note that there is no character for a semiminima rest yet.
                            
        TODO: Replace w/ SMuFL
        
        >>> from music21.alpha import medren
        
        >>> mr = medren.MensuralRest('SB')
        >>> mr.fontString
        '0x32'
        '''
        return self._fontString
    

class MensuralNote(GeneralMensuralNote, note.Note):
    '''
    An object representing a mensural note commonly found in medieval and renaissance music.
    Takes pitch and mensural type as arguments, but defaults to 'C' and 'brevis'.
    Pitch and and mensural type can also be set using the properties 
    :attr:`music21.medren.MensuralNote.pitch` and :attr:`music21.medren.MensuralNote.mensuralType` 
    respectively.
    The utf-8 code for the Ciconia font character can be accessed via the property 
    :attr:`music21.medren.MensuralNote.fontString`

    The note stems can can be set using the method :meth:`music21.medren.MensuralNote.setStem`. 
    A note's stems can be displayed using the method :meth:`music21.medren.MensuralNote.getStems`.
    Stems may only be added to notes shorter than a brevis. For additional detail, see the 
    documentation for :meth:`music21.medren.MensuralNote.setStem`.
    
    The note flags can be set using the method :meth:`music21.medren.MensuralNote.setFlag`. 
    A note's flags can be displayed using the method :meth:`music21.medren.MensuralNote.getFlags`.
    Flags may only be added to stems that exist for the given note. For additional detail, 
    see the documentation for :meth:`music21.medren.MensuralNote.setFlag`.
    
    Two mensural notes are considered equal if they match in pitch, articulation, 
    and are equal as general mensural notes.
    
    Additional methods regarding color, duration, mensural type are inherited from 
    :class:`music21.medren.GeneralMensuralNote`.
    '''
    
    # scaling? 
    def __init__(self, *arguments, **keywords):
        note.Note.__init__(self, *arguments, **keywords)
        GeneralMensuralNote.__init__(self)
        self._gettingDuration = False        
        self._mensuralType = 'brevis'    
        
        if len(arguments) > 1:
            tOrA = arguments[1]
            if tOrA in _validMensuralTypes:
                self._mensuralType = tOrA
            elif tOrA in _validMensuralAbbr:
                self._mensuralType = _validMensuralTypes[_validMensuralAbbr.index(tOrA)]
            else:
                raise MedRenException('%s is not a valid mensural type or abbreviation' % tOrA)
        
        if self.mensuralType in ['minima', 'semiminima']:
            self.stems = ['up']
        else:
            self.stems = []
        
        self.flags = dict((s, None) for s in self.stems)
        if self._mensuralType == 'semiminima':
            self.flags['up'] = 'right'
            
        self._duration = None
        self._fontString = ''
        
        self.lenList = []
    
    def __repr__(self):
        return '<music21.medren.MensuralNote %s %s>' % (self.mensuralType, self.name)
    
    def __eq__(self, other):
        '''
        Same as music21.medren.GeneralNote.__eq__, but also tests equality of pitch 
        and articulation.
        Only pitch is shown as a test. For other cases, please see the docs for 
        :meth:``music21.medren.GeneralMensuralNote.__eq__``
        
        >>> from music21.alpha import medren
        >>> from music21.alpha import trecento
        
        >>> m = medren.MensuralNote('A', 'minima')
        >>> n = medren.MensuralNote('B', 'minima')
        >>> m == n
        False
        >>> s_2 = stream.Stream()
        >>> s_2.append(trecento.notation.Divisione('.q.'))
        >>> s_2.append(m)
        >>> s_2.append(n)
        >>> m == n
        False
        '''        
        eq = GeneralMensuralNote.__eq__(self, other)
        eq  = eq and hasattr(other, 'pitch')
        if eq:
            eq = eq and (self.pitch == other.pitch)
        eq = eq and hasattr(other, 'articulations')
        if eq:
            eq = eq and (sorted(list(set(self.articulations))) == 
                                        sorted(list(set(other.articulations))) )
        return eq
    
    @property
    def fullName(self):
        msg = []
        msg.append(self.mensuralType)
        msg.append(' %s ' % self.pitch.fullName)
        return ''.join(msg)
    
    @property
    def fontString(self):
        '''
        The utf-8 code corresponding to a mensural note in Ciconia font.
        Note that semiminima with a left flag on the upper stem 
        and any flag on the lower stem, semiminima with a right flag on the 
        upperstem and on the lowerstem, and any red or unfilled notes with 
        sidestems have no corresponding characters in the Cicionia font.
        
        TODO: Replace with SMuFL
        
        >>> from music21.alpha import medren
        
        >>> mn = medren.MensuralNote('A', 'M')
        >>> mn.setStem('down')
        >>> mn.fontString
        '0x44'
        >>> mn.setFlag('down', 'right')
        >>> mn.fontString
        '0x47'
        >>> mn.setFlag('down', None)
        >>> mn.setStem(None)
        >>> mn.fontString
        '0x4d'
        >>> mn.color = 'red'
        >>> mn.fontString
        '0x6d'        
        '''
        if self.mensuralType == 'maxima':
            self._fontString = '0x58'
        elif self.mensuralType == 'Longa':
            self._fontString = '0x4c'
        elif self.mensuralType == 'brevis':
            self._fontString = '0x42'
        elif self.mensuralType == 'semibrevis':
            if 'down' in self.stems:
                self._fontString = '0x4e'
            elif 'side' in self.stems:
                self._fontString = '0x41'
            else:
                self._fontString = '0x53'
        elif self.mensuralType == 'minima':
            if 'down' in self.stems:
                if 'down' in self.flags and self.flags['down'] == 'left':
                    self._fontString = '0x46'
                elif 'down' in self.flags and self.flags['down'] == 'right':
                    self._fontString = '0x47'
                else:
                    self._fontString = '0x44'
            elif 'side' in self.stems:
                self._fontString = '0x61'
            else:
                self._fontString = '0x4d'
        else:
            if self.flags['up'] == 'left':
                self._fontString = '0x49'
            else:
                if 'down' in self.stems: 
                    if 'down' in self.flags and self.flags['down'] == 'left':
                        self._fontString = '0x48'
                    else:
                        self._fontString = '0x45'
                else:
                    self._fontString = '0x59'
        
        if self.color ==  'red':
            if self._fontString in ['41', '61']:
                self._fontString = ''
            else:
                self._fontString = hex(int(self._fontString, 16)+32)
        
        return self._fontString
    

    def _setMensuralType(self, mensuralTypeOrAbbr):
        GeneralMensuralNote._setMensuralType(self, mensuralTypeOrAbbr)
        
        if self.mensuralType in ['minima', 'semiminima']:
            self.stems = ['up']
        else:
            self.stems = []
        
        self.flags = dict((s, None) for s in self.stems)
        if self._mensuralType == 'semiminima':
            self.flags['up'] = 'right'
     
    mensuralType = property(GeneralMensuralNote._getMensuralType, _setMensuralType,
                          doc = ''' See documentation in `music21.medren.GeneralMensuralType`''')
    
    def _setColor(self, value):
        if value in ['black', 'red']:
            note.Note._setColor(self, value)
        else:
            raise MedRenException('color %s not supported for mensural notes' % value)
    
    color = property(note.GeneralNote._getColor, _setColor,
                     doc = '''The only valid colors for mensural notes are red and black
                     
                     >>> from music21.alpha import medren
                     
                     >>> n = medren.MensuralNote('A', 'brevis')
                     >>> n.color
                     >>> 
                     >>> n.color = 'red'
                     >>> n.color
                     'red'
                     >>> n.color = 'green'
                     Traceback (most recent call last):
                     MedRenException: color green not supported for mensural notes
                     ''')
    
    def getNumDots(self):
        ''' 
        Used for French notation. Not yet implemented
        '''
        return 0 #TODO: figure out how dots work
    
    def getStems(self):
        '''
        Returns a list of stem directions. If the note has no stem, returns an empty list
        '''
        return self.stems
    
    def setStem(self, direction):
        '''
        Takes one argument: direction.
        
        Adds a stem to a note. Any note with length less than or equal to a minima gets an 
        upstem by default.
        Any note can have at most two stems. Valid stem directions are "down" and "side". 
        Downstems can be applied to any note with length less than or equal to a brevis.
        Side stems in Trecento notation are the equivalent of dots, but may only be 
        applied to notes of the type semibrevis and minima (hence, a dotted note may not 
        have a side stem, and vice versa).
        Setting stem direction to None removes all but the default number of stems. 
        
        >>> from music21.alpha import medren
        
        >>> r_1 = medren.MensuralNote('A', 'brevis')
        >>> r_1.setStem('down')
        Traceback (most recent call last):
        MedRenException: A note of type brevis cannot be equipped with a stem
        >>> r_2 = medren.MensuralNote('A', 'semibrevis')
        >>> r_2.setStem('down')
        >>> r_2.setStem('side')
        >>> r_2.getStems()
        ['down', 'side']
        >>> r_3 = medren.MensuralNote('A', 'minima')
        >>> r_3.setStem('side')
        >>> r_3.getStems()
        ['up', 'side']
        >>> r_3.setStem('down')
        Traceback (most recent call last):
        MedRenException: This note already has the maximum number of stems
        >>> r_3.setStem(None)
        >>> r_3.getStems()
        ['up']
        '''
        #NOTE: This method makes it possible to have a semibrevis with a sidestem and a 
        # downstem. This doesn't mean anything so far as I can tell.
        
        if direction in [None, 'none', 'None']:
            if self.mensuralType in ['minima', 'semiminima']:
                self.stems = ['up']
            else:
                self.stems = []
            return    
            
        if self.mensuralType in ['brevis','longa', 'maxima']:
            raise MedRenException('A note of type %s cannot be equipped with a stem' % 
                                  self.mensuralType)

        
        if direction in ['down', 'Down']:
            direction = 'down'
            if len(self.stems) > 1:
                raise MedRenException('This note already has the maximum number of stems')
            else:
                self.stems.append(direction)
                    
        elif direction in ['side', 'Side']:
            direction = 'side'
            if ((self.mensuralType not in ['semibrevis', 'minima']) or 
                self.getNumDots() > 0):
                raise MedRenException('This note may not have a stem of direction %s' % 
                                      direction)
            elif len(self.stems) > 1:
                raise MedRenException('This note already has the maximum number of stems')
            else:
                self.stems.append(direction)
        else:
            raise MedRenException('%s not recognized as a valid stem direction' % direction)
                
    def getFlags(self):
        '''
        Returns a dictionary of each stem with its corresponding flag. 
        '''
        return self.flags
    
    def setFlag(self, stemDirection, orientation):
        '''
        Takes two arguments: stemDirection and orientation.
        
        stemDirection may be 'up' or 'down' (sidestems cannot have flags), and orientation 
        may be 'left' or 'right'.
        If the note has a stem with direction stemDirection, a flag with the specified 
        orientation is added.
        Any stem may only have up to one flag, so setting a flag overrides whatever 
        flag was previously present.
        Setting the orientation of a flag to None returns that stem to its default 
        flag setting ('right' for semiminima, None otherwise).
        
        A minima may not have a flag on its upstem, while a semiminima always has a 
        flag on its upstem. The flag orientation for a semiminima is 'right' by default, 
        but may be set to 'left'. 
        Any note with a downstem may also have a flag on that stem. 
        
        >>> from music21.alpha import medren
        
        >>> r_1 = medren.MensuralNote('A', 'minima')
        >>> r_1.setFlag('up', 'right')
        Traceback (most recent call last):
        MedRenException: a flag may not be added to an upstem of note type minima
        >>> r_1.setStem('down')
        >>> r_1.setFlag('down', 'left')
        >>> r_1.getFlags()['down']
        'left'
        >>> r_1.getFlags()['up'] is None
        True
        >>> r_2 = medren.MensuralNote('A', 'semiminima')
        >>> r_2.getFlags()
        {'up': 'right'}
        >>> r_2.setFlag('up', 'left')
        >>> r_2.getFlags()
        {'up': 'left'}
        >>> r_3 = medren.MensuralNote('A','semibrevis')
        >>> r_3.setStem('side')
        >>> r_3.setFlag('side','left')
        Traceback (most recent call last):
        MedRenException: a flag cannot be added to a stem with direction side
        '''
        
        if stemDirection == 'up':
            if self.mensuralType != 'semiminima':
                raise MedRenException('a flag may not be added to an upstem of note type %s' % 
                                      self.mensuralType)
            else:
                if orientation in ['left', 'Left']:
                    orientation = 'left'
                    self.flags[stemDirection] = orientation
                elif orientation in ['right', 'Right']:
                    orientation = 'right'
                    self.flags[stemDirection] = orientation
                elif orientation in ['none', 'None', None]:
                    orientation = 'right'
                    self.flags[stemDirection] = orientation
                else:
                    raise MedRenException('a flag of orientation %s not supported' % orientation)
        elif stemDirection == 'down':
            if stemDirection in self.stems:
                if orientation in ['left', 'Left']:
                    orientation = 'left'
                    self.flags[stemDirection] = orientation
                elif orientation in ['right', 'Right']:
                    orientation = 'right'
                    self.flags[stemDirection] = orientation
                elif orientation in ['none', 'None', None]:
                    orientation = None
                    self.flags[stemDirection] = orientation
                else:
                    raise MedRenException('a flag of orientation %s not supported' % orientation)
            else:
                raise MedRenException('this note does not have a stem with direction %s' % 
                                      stemDirection)
        else:
            raise MedRenException(
                'a flag cannot be added to a stem with direction %s' % stemDirection)  
        
        
class Ligature(base.Music21Object):
    '''
    An object that represents a ligature commonly found in medieval and Renaissance music. 
    Initialization takes a list of the pitches in the ligature as a required argument.
    Color of the ligature is an optional argument (default is 'black'). Color can also be set 
    with the :meth:`music21.medren.Ligature.setColor` method. 
    Color of a ligature can be determined with the :meth:`music21.medren.Ligature.getColor` method.
    Whether the noteheads of the ligature are filled is an optional argument (default is 'yes'). 
    Noteheads can be also filled with the :meth:`music21.medren.Ligature.setFillStatus` method. 
    Fill status of a ligature can be determined with the 
    :meth:`music21.medren.Ligature.getFillStatus` method.
    
    The notes of the ligature can be accessed via the property 
    :attr:`music21.medren.Ligature.notes`.
    The mensural length of each note is calculated automatically. 
    To determine if a ligature is cum proprietate, use the 
    :meth:`music21.medren.Ligature.isCumProprietate` method.
    Similarly, to determine if a ligautre is cum perfectione, use the 
    :meth:`music21.medren.Ligature.isCumPerfectione` method.
    Finally, to determine if a ligature is cum opposita proprietate (C.O.P), use the 
    :meth:`music21.medren.Ligature.isCOP` method. 
    
    Noteheads can be set to have oblique shape using the 
    :meth:`music21.medren.Ligature.makeOblique` method. Similarly, oblique noteheads 
    can be set to have a square shape using the :meth:`music21.medren.Ligature.makeSquare` method. 
    The shape of a notehead can be determined using the 
    :meth:`music21.medren.Ligature.getNoteheadShape` method. By default, all noteheads in a 
    ligature are square.
    
    A note in the ligature can be made to be maxima by the 
    :meth:`music21.medren.Ligature.setMaxima` method. It can be determined whether a note 
    is a maxima by the :meth:`music21.medren.Ligature.isMaxima` method.
    By default, no notes in a ligature are maxima.
    
    A note in the ligature can be set to have an upstem, a downstem, or no 
    stem by the :meth:`music21.medren.Ligature.setStem` method.
    It can be determined whether a note has a stem by the 
    :meth:`music21.medren.Ligature.getStem` method. By default, no notes in a ligature have stems.
    
    A note in the ligature can be 'reversed' by the `music21.medren.Ligature.setReverse` 
    method. A 'reversed' note is displayed as stacked upon the preceding note 
    (see the second note in the example).
    It can be determined whether a note is 
    reversed by the `music21.medren.Ligature.isReversed` method. By default, no notes 
    in a ligature are reversed. 
    --------------------------------------------------------
    
    Example:
    
    .. image:: images/medren_Ligature_Mensural-Example.*
        :width: 600
    
    
    Roman de Fauvel.  f. 1r.  Paris, Bibliothèque Nationale de France, MS fr.

    The ligatures outlined in blue would be constructed as follows:
    
    >>> from music21.alpha import medren
    
    >>> l1 = medren.Ligature(['A4','F4','G4','A4','B-4'])
    >>> l1.makeOblique(0)
    >>> l1.setStem(0, 'down', 'left')
    >>> print([n.fullName for n in l1.notes])
    ['brevis A in octave 4 ', 'brevis F in octave 4 ', 
     'brevis G in octave 4 ', 'brevis A in octave 4 ', 'brevis B-flat in octave 4 ']
    >>>
    >>> l2 = medren.Ligature(['F4','G4','A4','B-4','D5'])
    >>> l2.setStem(4, 'down', 'left')
    >>> l2.setReverse(4, True)
    >>> print([(n.mensuralType, n.pitch.nameWithOctave) for n in l2.notes])
    [('brevis', 'F4'), ('brevis', 'G4'), ('brevis', 'A4'), ('brevis', 'B-4'), ('longa', 'D5')]
    
    Note that ligatures cannot be displayed yet. 
    '''

    def __init__(self, pitches=None, color='black', filled='yes'):
        base.Music21Object.__init__(self)
        self.noteheadShape = None
        self.stems = None
        self.maximaNotes = None
        self.reversedNotes = None
        self._pitches = []
        
        if pitches is not None:
            self.pitches = pitches
        
        self._notes = []
        self.color = color
        self.filled = filled
        
    
    def _getPitches(self):
        return self._pitches
    
    def _setPitches(self, pitches):
        self._pitches = []
        for p in pitches:
            if isinstance(p, pitch.Pitch):
                self._pitches.append(p)
            else:
                self._pitches.append(pitch.Pitch(p))
        
        self.noteheadShape = dict([(ind, 'square') for ind in range(self._ligatureLength())])
        self.stems = dict([(ind, (None,None)) for ind in range(self._ligatureLength())])
        self.maximaNotes = dict([(ind, False) for ind in range(self._ligatureLength())])
        self.reversedNotes = dict([(ind, False) for ind in range(self._ligatureLength())])
        
    pitches = property(_getPitches, _setPitches,
                       doc = '''A list of pitches comprising the ligature''')
    
    @property
    def notes(self):
        '''
        Returns the ligature as a list of mensural notes
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','B4'])
        >>> print([n.mensuralType for n in l.notes])
        ['brevis', 'brevis']
        >>> l.makeOblique(0)
        >>> print([n.mensuralType for n in l.notes])
        ['longa', 'brevis']
        >>> l = medren.Ligature(['B4','A4'])
        >>> print([n.mensuralType for n in l.notes])
        ['longa', 'longa']
        >>> l.makeOblique(0)
        >>> print([n.mensuralType for n in l.notes])
        ['longa', 'brevis']
        >>> l.setStem(0, 'down','left')
        >>> print([n.mensuralType for n in l.notes])
        ['brevis', 'brevis']
        >>> l = medren.Ligature(['G4','A4','B4','A4'])
        >>> l.setStem(2, 'up','left')
        >>> print([n.mensuralType for n in l.notes])
        ['brevis', 'brevis', 'semibrevis', 'semibrevis']
        >>> l = medren.Ligature(['B4','A4','G4','A4','G4','A4','F4'])
        >>> l.makeOblique(0)
        >>> l.makeOblique(4)
        >>> l.setStem(2, 'down', 'left')
        >>> l.setStem(4, 'up','left')
        >>> l.setMaxima(6, True)
        >>> print([n.mensuralType for n in l.notes])
        ['longa', 'brevis', 'longa', 'brevis', 'semibrevis', 'semibrevis', 'maxima']
        '''
        if self._notes == []:
            self._notes = self._expandLigature()
        return self._notes
        
    def _ligatureLength(self):
        return len(self.pitches)
    
    #def _getDuration(self):
        #return sum[n.duration for n in self.notes]
        
    def isCumProprietate(self):
        '''
        Takes no arguments.
        
        Returns True if the ligature is cum proprietate, and 
        False if the ligature is sine proprietate.
        '''
        return self.notes[0].mensuralType == 'brevis'
    
    def isCumPerfectione(self):
        '''
        Takes no arguments.
        
        Returns True if the ligature is cum perfectione, 
        and False if the ligature is sine perfectione.
        '''
        return self.notes[self._ligatureLength()-1].mensuralType == 'longa'
    
    def isCOP(self):
        '''
        Takes no arguments
        
        Returns True if the ligature is cum opposita proprietate (C.O.P), and False otherwise
        '''
        return self.notes[0].mensuralType == 'semibrevis'
    
    def getColor(self, index=None):
        '''
        Take one argument: index (optional, default is None).
        
        Returns the color of the note at the given index. If no index specified, 
        returns the color of the ligature.
        If multiple colors are present, returns mixed.
        '''
        if index == 'None' or index == 'none':
            index = None
        if index != None:
            if index < self._ligatureLength():
                return self.notes[index]._getColor()
            else:
                raise MedRenException('no note exists at index %d' % index)
        else: 
            return self.color
        
    def setColor(self, value, index=None):
        '''
        Takes two arguments: value, index (optional, default is None).
        
        Sets the color of note at index to value. If no index is specified, or 
        index is set to None, every note in the ligature is given value as a color. 
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','C5','B4'])
        >>> l.setColor('red')
        >>> l.getColor()
        'red'
        >>> l.setColor('black',1)
        >>> l.getColor()
        'mixed'
        '''
        tempColor = self.getColor()
        if index == 'None' or index == 'none':
            index = None
        if index != None:
            if index < self._ligatureLength():
                if value != tempColor:
                    self.color = 'mixed'
                    self.notes[index]._setColor(value)
            else:
                raise MedRenException('no note exists at index %d' % index)
        else:
            if value in ['black', 'red']:
                self.color = value
                for n in self.notes:
                    n._setColor(value)
            else:
                raise MedRenException('color %s not supported for ligatures' % value)
    
    def getFillStatus(self, index = None):
        '''
        Take one argument: index (optional, default is None).
        
        Returns whether the notehead is filled at the given index. If no index specified, 
        returns whether fill status of the ligature.
        If noteheads are not consistent throughout the ligature, returns mixed.
        '''
        if index == 'None' or index == 'none':
            index = None
        if index != None:
            if index < self._ligatureLength():
                return self.notes[index]._getNoteheadFill()
            else:
                raise MedRenException('no note exists at index %d' % index) 
        else:
            return self.filled
    
    def setFillStatus(self, value, index=None):
        '''
        Takes two arguments: value, index (optional, default is None).
        
        Sets the fill status of the notehead at index to value. If no index is specified, 
        or if index is set to None, every notehead is give fill status value.
        To set a notehead as filled, value should be 'yes' or 'filled'. 
        To set a notehead as empty, value should be 'no' or 'empty' .
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','C5','B4'])
        >>> l.setFillStatus('filled')
        >>> l.getFillStatus()
        'yes'
        >>> l.setFillStatus('no', 1)
        >>> l.getFillStatus()
        'mixed'
        '''
        tempFillStatus = self.getFillStatus()
        if index == 'None' or index == 'none':
            index = None
        if index != None:
            if index < self._ligatureLength():
                if value != tempFillStatus:
                    self.filled = 'mixed'
                    self.notes[index]._setNoteheadFill(value)
            else:
                raise MedRenException('no note exists at index %d' % index)
        else:
            if value in ['yes','fill','filled']:
                value = 'yes'
                self.filled = value
                for n in self.notes:
                    n._setNoteheadFill(value)
            elif value in ['no', 'empty']:
                value = 'no'
                self.filled = value
                for n in self.notes:
                    n._setNoteheadFill(value)
            else:
                raise MedRenException('fillStatus %s not supported for ligatures' % value)
                    
    
    def getNoteheadShape(self, index):
        '''
        Takes one argument: index.
        
        Returns the notehead shape (either square or oblique) of the note at index
        '''
        if index < self._ligatureLength():
            return self.noteheadShape[index][0]
        else:
            raise MedRenException('no note exists at index %d' % index)
            
    def makeOblique(self, startIndex):
        '''
        Takes one argument: startIndex.
        
        Make the notes at startIndex and the note following startIndex into an oblique notehead. 
        Note that an oblique notehead cannot start on the last note of a ligature.
        Also, a note that is a maxima cannot be the start or end of an oblique notehead.
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','C5','B4','A4'])
        >>> l.makeOblique(1)
        >>> l.getNoteheadShape(1)
        'oblique'
        >>> l.getNoteheadShape(2)
        'oblique'
        >>> l.makeOblique(0)
        Traceback (most recent call last):
        MedRenException: cannot start oblique notehead at index 0
        >>> l.makeOblique(2)
        Traceback (most recent call last):
        MedRenException: cannot start oblique notehead at index 2
        >>> l.makeOblique(3)
        Traceback (most recent call last):
        MedRenException: no note exists at index 4
        '''
        if startIndex < self._ligatureLength() - 1:
            currentShape = self.noteheadShape[startIndex]
            nextShape = self.noteheadShape[startIndex+1]
            if  ((currentShape == ('oblique','end') or nextShape == ('oblique', 'start')) or
                 (self.isMaxima(startIndex) or self.isMaxima(startIndex+1))): 
                raise MedRenException('cannot start oblique notehead at index %d' % startIndex)
            
            else:
                self.noteheadShape[startIndex] = ('oblique', 'start')
                self.noteheadShape[startIndex+1] = ('oblique', 'end')
        else:
            raise MedRenException('no note exists at index %d' % (startIndex+1))
        self._notes = []
    
    def makeSquare(self, index):
        '''
        Takes one argument: index.
        
        Sets the note at index to have a square notehead. 
        If the note at index is part of an oblique notehead, all other notes that 
        are part of that notehead are also set to have square noteheads.

        >>> from music21.alpha import medren
        
        
        >>> l = medren.Ligature(['A4','C5','B4','A4'])
        >>> l.makeOblique(1)
        >>> l.makeSquare(2)
        >>> l.getNoteheadShape(2)
        'square'
        >>> l.getNoteheadShape(1)
        'square'
        '''
        if index < self._ligatureLength():
            currentShape = self.noteheadShape[index]
            if currentShape[0] == 'oblique':
                self.noteheadShape[index] = 'square',
                if currentShape[1] == 'start':
                    self.noteheadShape[index+1] = 'square',
                else:
                    self.noteheadShape[index-1] = 'square',
            else:
                pass #Already square
        else:
            raise MedRenException('no note exists at index %d' % index)
        self._notes = []
    
    def isMaxima(self, index):
        '''
        Takes one argument: index.
        
        If the note at index is a maxima, returns True. Otherwise, it returns False.
        '''
        if index < self._ligatureLength():
            return self.maximaNotes[index]
        else:
            raise MedRenException('no note exists at index %d' % index)
    
    def setMaxima(self, index, value):
        '''
        Takes two arguments: index, value.
        
        Sets the note at index to value. If value is True, that note is a maxima. 
        If value if False, that note is not.
        A note with an oblique notehead cannot be a maxima. 
        A note cannot be a maxima if that note has a stem. 
        A note cannot be a maxima if the previous note has an up-stem.
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','C5','B4'])
        >>> l.setStem(0, 'up', 'left')
        >>> l.setMaxima(2, True)
        >>> l.isMaxima(2)
        True
        >>> l.setMaxima(1, True)
        Traceback (most recent call last):
        MedRenException: cannot make note at index 1 a maxima
        >>> l.setMaxima(0, True)
        Traceback (most recent call last):
        MedRenException: cannot make note at index 0 a maxima
        >>> l.setMaxima(2, False)
        >>> l.isMaxima(2)
        False
        '''
        if index < self._ligatureLength():
            # TODO: fix so there's only one right way...
            if value in (True, 'True', 'true'):
                if ((self.getNoteheadShape(index) == 'oblique') or 
                        (self.getStem(index) != (None, None)) or 
                        (index > 0 and self.getStem(index-1)[0] == 'up')):
                    raise MedRenException('cannot make note at index %d a maxima' % index)
                else:
                    self.maximaNotes[index] = value
            elif value in (False, 'False', 'false'):
                self.maximaNotes[index] = value
            else:
                raise MedRenException('%s is not a valid value' % value)
        else:
            raise MedRenException('no note exists at index %d' % index)
        self._notes = []
    
    def getStem(self, index):
        '''
        Takes one argument: index
        If the note at index has a stem, it returns direction (up or down) 
        and orientation (left, right)
        '''
        if index < self._ligatureLength():
            return self.stems[index]
        else:
            raise MedRenException('no note exists at index %d' % index)
                
    def setStem(self, index, direction, orientation):
        '''
        Takes three arguments: index, direction, orientation.
        
        Index determines which note in the ligature the stem will be placed on.
        Direction determines which way the stem faces. Permitted directions 
        are 'up','down', and 'none'.
        Orientation determines on which side of the note the stem sits. 
        Permitted orientations are 'left', 'right', and 'none'. 
        Setting the direction and orientation of a stem to 'none' removes the stem from the note.
        
        Note that if the direction of a stem is 'none', then no stem is present on that note. 
        So the orientation must also be 'none'.
        Also note that an up-stem followed consecutively by a stemmed note is not permitted. 
        An up-stem cannot be on the last note of a ligature.
        Stems may also not overlap. So two consecutive notes may note have stem orientations 
        'right' and 'left' respectively.
        
        Finally, a stem cannot be set on a note that is a maxima. An up-stem cannot 
        be set on a note preceding a maxima.
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','C5','B4','A4','B4'])
        >>> l.setStem(0, 'none','left')
        Traceback (most recent call last):
        MedRenException: direction "None" and orientation "left" not supported for ligatures
        >>> l.setStem(1,'up', 'left')
        >>> l.getStem(1)
        ('up', 'left')
        >>> l.setStem(2, 'down', 'right')
        Traceback (most recent call last):
        MedRenException: a stem with direction "down" not permitted at index 2
        >>> l.setMaxima(4, True)
        >>> l.setStem(4, 'up', 'left')
        Traceback (most recent call last):
        MedRenException: cannot place stem at index 4
        >>> l.setStem(3, 'up','left')
        Traceback (most recent call last):
        MedRenException: a stem with direction "up" not permitted at index 3
        '''
        if direction == 'None' or direction == 'none':
            direction = None
        if orientation == 'None' or direction == 'none':
            index = None
        if index >= self._ligatureLength():
            raise MedRenException('no note exists at index %d' % index)

        if self.isMaxima(index):
            raise MedRenException('cannot place stem at index %d' % index)

        if orientation is None and direction is None:
            self.stems[index] = (direction, orientation)
        elif orientation in ['left', 'right']:
            if index == 0:
                prevStem = (None,None)
                nextStem = self.getStem(1)
            elif index == self._ligatureLength() - 1:
                prevStem = self.getStem(self._ligatureLength() - 2)
                nextStem = (None,None)
            else:
                prevStem = self.getStem(index - 1)
                nextStem = self.getStem(index + 1)
                
            if ((orientation == 'left' and prevStem[1] != 'right') 
                    or (orientation == 'right' and nextStem[1] != 'left')):
                if direction == 'down':
                    if prevStem[0] != 'up':
                        self.stems[index] = (direction, orientation)
                    else:
                        raise MedRenException(
                            'a stem with direction "%s" not permitted at index %d' % 
                            (direction, index))
                elif direction == 'up':
                    if ((index < self._ligatureLength() - 1) 
                            and (prevStem[0] != 'up') 
                            and (nextStem[0] is None) 
                            and not self.isMaxima(index + 1)):
                        self.stems[index] = (direction, orientation)
                    else:
                        raise MedRenException(
                            'a stem with direction "%s" not permitted at index %d' % 
                            (direction, index))
                else:
                    raise MedRenException(
                        'direction "%s" and orientation "%s" not supported for ligatures' %
                        (direction, orientation))
            else:
                raise MedRenException(
                    'a stem with orientation "%s" not permitted at index %d' % 
                    (orientation,index))
        else:
            raise MedRenException(
                'direction "%s" and orientation "%s" not supported for ligatures' % 
                (direction,orientation))
        self._notes = []     
       
    def isReversed(self, index):
        '''
        Takes one argument: index.
        
        If the note at index is reversed, returns True. Otherwise, it returns False.
        '''
        if index < self._ligatureLength():
            return self.reversedNotes[index]
        else:
            raise MedRenException('no note exists at index %d' % index)
        
    def setReverse(self, endIndex, value):
        '''
        Takes two arguments: endIndex, value.
        
        endIndex designates the note to be reversed. value may be True or False.
        Setting value to True reverses the note at endIndex. 
        Setting value to False 'de-reverses' the note at endIndex.
         
        If the note at endIndex has a stem with direction 'down' and orientation 'left', 
        and is at least a step above the preceding note, it can be reversed.
        No two consecutive notes can be reversed. Also, if the note at endIndex is 
        preceded by a note with an upstem, it cannot be reversed.
        
        A reversed note is displayed directly on top of the preceeding note in the ligature. 
        
        >>> from music21.alpha import medren
        
        >>> l = medren.Ligature(['A4','C5','F5','F#5'])
        >>> l.setStem(1, 'down', 'left')
        >>> l.setStem(2, 'down', 'left')
        >>> l.setStem(3, 'down', 'left')
        >>> l.setReverse(1,True)
        >>> l.isReversed(1)
        True
        >>> l.setReverse(2,True)
        Traceback (most recent call last):
        MedRenException: the note at index 2 cannot be given reverse value True
        >>> l.setReverse(3,True)
        Traceback (most recent call last):
        MedRenException: the note at index 3 cannot be given reverse value True
        '''
        if value == 'True' or value == 'true':
            value = True
        if value == 'False' or value == 'false':
            value = False
            
        if endIndex < self._ligatureLength():
            if value in [True, False]:
                if not value:
                    self.reversedNotes[endIndex] = value
                else:
                    if endIndex > 0:
                        tempPitchCurrent = copy.copy(self.pitches[endIndex])
                        tempPitchPrev = copy.copy(self.pitches[endIndex-1])
                       
                        tempPitchCurrent._setAccidental(None)
                        tempPitchPrev._setAccidental(None)
                        if ((not self.isReversed(endIndex-1)) 
                                and (self.getStem(endIndex-1)[0] != 'up') 
                                and (self.getStem(endIndex) == ('down','left')) 
                                and (tempPitchCurrent > tempPitchPrev)):
                            self.reversedNotes[endIndex] = True
                        else:                           
                            #environLocal.warn([tempPitchCurrent, tempPitchPrev])
                            raise MedRenException(
                                'the note at index %d cannot be given reverse value %s' % 
                                (endIndex, value))
                    else:
                        raise MedRenException('no note exists at index %d' % (endIndex-1,)) 
            else:
                raise MedRenException('reverse value %s not supported for ligatures.' % (value,))
        else:
            raise MedRenException('no note exists at index %d' % (endIndex,))
    
    def _expandLigature(self):
        '''
        Given pitch, notehead, and stem information, assigns a mensural note 
        to each note of the ligature.
        '''
        
        ind = 0
        notes = []
        
        if self._ligatureLength() < 2:
            raise MedRenException('Ligatures must contain at least two notes')
            
        if self.getStem(ind)[0] == 'up':
            notes.append(MensuralNote(self.pitches[ind], 'semibrevis'))
            notes.append(MensuralNote(self.pitches[ind+1], 'semibrevis'))
            ind += 2
        elif self.getStem(ind)[0] == 'down':
            if self.getNoteheadShape(ind) == 'oblique':
                notes.append(MensuralNote(self.pitches[ind], 'brevis'))
            else:
                if self.pitches[ind+1] < self.pitches[ind]:
                    notes.append(MensuralNote(self.pitches[ind], 'brevis'))
                else:
                    notes.append(MensuralNote(self.pitches[ind], 'longa'))
            ind += 1
        else:
            if self.isMaxima(ind):
                notes.append(MensuralNote(self.pitches[ind], 'maxima'))
            else:
                if self.getNoteheadShape(ind) == 'oblique':
                    notes.append(MensuralNote(self.pitches[ind], 'longa'))
                else:
                    if self.pitches[ind+1] < self.pitches[ind]:
                        notes.append(MensuralNote(self.pitches[ind], 'longa'))
                    else:
                        notes.append(MensuralNote(self.pitches[ind], 'brevis'))
            ind += 1
            
        while ind < self._ligatureLength()-1:
            if self.getStem(ind)[0] == 'up':
                notes.append(MensuralNote(self.pitches[ind],  'semibrevis'))
                notes.append(MensuralNote(self.pitches[ind+1], 'semibrevis'))
                ind += 2
            elif self.getStem(ind)[0] == 'down':
                notes.append(MensuralNote(self.pitches[ind], 'longa'))
                ind += 1
            else:
                if self.isMaxima(ind):
                    notes.append(MensuralNote(self.pitches[ind], 'maxima'))
                else:
                    notes.append(MensuralNote(self.pitches[ind], 'brevis'))
                ind += 1
        
        if ind == self._ligatureLength() - 1:
            if self.getStem(ind)[0] == 'down':
                if self.getNoteheadShape(ind) == 'oblique':
                    notes.append(MensuralNote(self.pitches[ind], 'longa'))
                else:
                    if self.pitches[ind-1] < self.pitches[ind]:
                        notes.append(MensuralNote(self.pitches[ind], 'longa'))
                    else:
                        notes.append(MensuralNote(self.pitches[ind], 'brevis'))
            else:
                if self.isMaxima(ind):
                    notes.append(MensuralNote(self.pitches[ind], 'maxima'))
                else:
                    if self.getNoteheadShape(ind) == 'oblique':
                        notes.append(MensuralNote(self.pitches[ind], 'brevis'))
                    else:
                        if self.pitches[ind-1] < self.pitches[ind]:
                            notes.append(MensuralNote(self.pitches[ind], 'brevis'))
                        else:
                            notes.append(MensuralNote(self.pitches[ind], 'longa'))
            
        return notes
    
#-------------------------------------------------------------------------------------
def breakMensuralStreamIntoBrevisLengths(inpStream, inpMOrD=None, printUpdates=False):
    '''
    Takes a stream as an argument. Takes a mensuration or divisione object as an optional argument.
     
    To work effectively, this stream must contain only mensural objects. 
    The function :meth:`music21.medren.breakMensuralStreamIntoBrevisLengths` 
    takes the mensural stream, and returns a measured stream.
    This measured stream preserves the structure of the original stream. 
    The mensural object present in the original stream are also present in the measured stream. 
    Each brevis length worth of objects in the original are stored in the mensural 
    stream as a mensural object.
    
    No substream of the original stream can contain both stream and mensural type objects, 
    otherwise the stream cannot be processed. 
    
    Furthermore, no stream can contain higher hierarchy stream types. The stream type 
    hierarchy is :class:`music21.stream.Stream`, followed by :class:`music21.stream.Score`, 
    :class:`music21.stream.Part`, then :class:`music21.stream.Measure`.
    
    Finally, a mensuration or divisione must be present or determinable, 
    otherwise the stream cannot be converted. If multiple mensurations are present, 
    they must change only at the highest stream instance.
    
    Otherwise, this causes a inconsistency when converting the stream.
    
    >>> from music21.alpha import medren
    
    >>> s = stream.Score()
    >>> p = stream.Part()
    >>> m = stream.Measure()
    >>> s.append(p)
    >>> s.append(medren.GeneralMensuralNote('B'))
    >>> medren.breakMensuralStreamIntoBrevisLengths(s)
    Traceback (most recent call last):
    MedRenException: cannot combine objects of type <class 'music21.stream.Part'>, 
       <class 'music21.alpha.medren.GeneralMensuralNote'> within stream

    >>> s = stream.Score()
    >>> p.append(s)
    >>> medren.breakMensuralStreamIntoBrevisLengths(p)
    Traceback (most recent call last):
    MedRenException: Hierarchy of <class 'music21.stream.Part'> 
       violated by <class 'music21.stream.Score'>

    >>> from music21.alpha import trecento
    >>> p = stream.Part()
    >>> m.append(medren.MensuralNote('G','B'))
    >>> p.append(trecento.notation.Divisione('.q.'))
    >>> p.repeatAppend(medren.MensuralNote('A','SB'),2)
    >>> p.append(trecento.notation.Punctus())
    >>> p.repeatAppend(medren.MensuralNote('B','M'),4)
    >>> p.append(trecento.notation.Punctus())
    >>> p.append(medren.MensuralNote('C','B'))
    >>> s.append(trecento.notation.Divisione('.p.'))
    >>> s.append(p)
    >>> s.append(m)
    >>> medren.breakMensuralStreamIntoBrevisLengths(s, printUpdates = True)
    Traceback (most recent call last):
    MedRenException: Mensuration or divisione 
       <music21.alpha.trecento.notation.Divisione .q.> not consistent within hierarchy
    
    >>> s = stream.Stream()
    >>> s.append(trecento.notation.Divisione('.q.'))
    >>> s.append(p)
    >>> s.append(m)
    >>> t = medren.breakMensuralStreamIntoBrevisLengths(s, printUpdates = True)
    Getting measure 0...
    ...
    >>> t.show('text')
    {0.0} <music21.alpha.trecento.notation.Divisione .q.>
    {0.0} <music21.stream.Part...>
        {0.0} <music21.stream.Measure...>  
            {0.0} <music21.medren.MensuralNote semibrevis A>
            {0.0} <music21.medren.MensuralNote semibrevis A>
        {0.0} <music21.stream.Measure...> 
            {0.0} <music21.medren.MensuralNote minima B>
            {0.0} <music21.medren.MensuralNote minima B>
            {0.0} <music21.medren.MensuralNote minima B>
            {0.0} <music21.medren.MensuralNote minima B>
        {0.0} <music21.stream.Measure...> 
            {0.0} <music21.medren.MensuralNote brevis C>
    {0.0} <music21.stream.Measure...> 
        {0.0} <music21.medren.MensuralNote brevis G> 
    '''
    
    mOrD = inpMOrD
    mOrDInAsNone = True
    if mOrD is not None:
        mOrDInAsNone = False
    
    inpStream_copy = copy.deepcopy(inpStream) #Preserve your input
    newStream = inpStream.__class__()
         
    def isHigherInhierarchy(l, u):
        hierarchy = ['Stream', 'Score',  'Part', 'Measure']
        uclass0 = None
        for tryClass in u.classes:
            if tryClass in hierarchy:
                uclass0 = tryClass
                break

        lclass0 = None
        for tryClass in l.classes:
            if tryClass in hierarchy:
                lclass0 = tryClass
                break


        if uclass0 is None:
            raise MedRenException("Cannot find class in our hierarchy of streams: %s" % (u))
        if lclass0 is None:
            raise MedRenException("Cannot find class in our hierarchy of streams: %s" % (l))
            
        if hierarchy.index(uclass0) == 0:
            return False
        else:
            return hierarchy.index(lclass0) <= hierarchy.index(uclass0)
    
    tempStream_1, tempStream_2 = inpStream_copy.splitByClass(None, lambda x: x.isStream)
    if tempStream_1:
        if tempStream_2 and tempStream_2.hasElementOfClass(GeneralMensuralNote):
            raise MedRenException(
                'cannot combine objects of type %s, %s within stream' % (
                                        tempStream_1[0].__class__, tempStream_2[0].__class__))
        else:
            for item in tempStream_2:
                
                newStream.append(item)
                if ('Mensuration' in item.classes) or ('Divisione' in item.classes):
                    if mOrDInAsNone: #If first case or changed mOrD
                        mOrD = item
                    elif mOrD.standardSymbol != item.standardSymbol: 
                        #If higher, different mOrD found
                        raise MedRenException(
                            'Mensuration or divisione %s not consistent within hierarchy' % item)
                    
            tempStream_1_1, tempStream_1_2 = tempStream_1.splitByClass(None, 
                                                lambda x: isHigherInhierarchy(x, tempStream_1))
            if tempStream_1_1:
                raise MedRenException('Hierarchy of %s violated by %s' % 
                                      (tempStream_1.__class__, tempStream_1_1[0].__class__))
            elif tempStream_1_2:
                for e in tempStream_1_2:
                    
                    if e.isMeasure:
                        newStream.append(e)
                    else:
                        newStream.append(breakMensuralStreamIntoBrevisLengths(e, 
                                                                              mOrD, 
                                                                              printUpdates))
    else:
        measureNum = 0
        mensuralMeasure = []
        
        for e in inpStream_copy:
            
            if 'MensuralClef' in e.classes:
                newStream.append(e)
            elif ('Mensuration' in e.classes) or ('Divisione' in e.classes):
                if mOrDInAsNone: #If first case or changed mOrD
                    mOrD = e
                    newStream.append(e)
                elif mOrD.standardSymbol != e.standardSymbol: #If higher, different mOrD found 
                    raise MedRenException(
                        'Mensuration or divisione %s not consistent within hierarchy' % e)
            elif 'Ligature' in e.classes:
                tempStream = stream.Stream()
                for mn in e.notes:
                    tempStream.append(mn)
                for m in breakMensuralStreamIntoBrevisLengths(tempStream, printUpdates):
                    newStream.append(m)
            elif ('GeneralMensuralNote' in e.classes) and (e not in mensuralMeasure):
                m = stream.Measure(number = measureNum)
                if printUpdates is True:
                    print('Getting measure %s...' % measureNum)
                mensuralMeasure = e._getSurroundingMeasure(mOrD, inpStream_copy)[0]
                if printUpdates is True:               
                    print('mensuralMeasure %s' % mensuralMeasure)
                for item in mensuralMeasure:
                    m.append(item)
                newStream.append(m)
                measureNum += 1 
            
    return newStream

#------------------------------------------------------------
def setBarlineStyle(score, newStyle, oldStyle='regular', inPlace=True):
    '''
    Converts any right barlines in the previous style (oldStyle; default = 'regular')
    to have the newStyle (such as 'tick', 'none', etc., see bar.py).  
    
    Leaves alone any other barline types (such as
    double bars, final bars, etc.).  Also changes any measures with no specified
    barlines (which come out as 'regular') to have the new style.

    returns the Score object.
    '''
    if inPlace is False:
        score = copy.deepcopy(score)
    
    oldStyle = oldStyle.lower()
    for m in score.semiFlat:
        if isinstance(m, stream.Measure):
            barline = m.rightBarline
            if barline is None:
                m.rightBarline = bar.Barline(style = newStyle)
            else:
                if barline.style == oldStyle:
                    barline.style = newStyle
    return score

def scaleDurations(score, scalingNum=1, inPlace=False, scaleUnlinked=True):
    '''
    scale all notes and TimeSignatures by the scaling amount.
    
    returns the Score object
    '''
    if inPlace is False:
        score = copy.deepcopy(score)

    for el in score.recurse():
        el.offset = el.offset * scalingNum
        if el.duration is not None:
            el.duration.quarterLength = el.duration.quarterLength * scalingNum
            if (hasattr(el.duration, 'linked') and 
                    el.duration.linked is False and 
                    scaleUnlinked is True):
                raise MedRenException('scale unlinked is not yet supported')
        if isinstance(el, tempo.MetronomeMark):
            el.value = el.value * scalingNum
        elif isinstance(el, meter.TimeSignature):
            newNum = el.numerator
            newDem = el.denominator / (1.0 * scalingNum) # float division
            iterationNum = 0
            while (newDem != int(newDem)):
                newNum = newNum * 2
                newDem = newDem * 2
                iterationNum += 1
                if iterationNum > 4:
                    raise MedRenException(
                        'cannot create a scaling of the TimeSignature for this ratio')
            newDem = int(newDem)
            el.loadRatio(newNum, newDem)
    
    for p in score.parts:
        p.makeBeams(inPlace=True)
    return score

def transferTies(score, inPlace=True):
    '''
    transfer the duration of tied notes (if possible) to the first note and 
    fill the remaining places
    with invisible rests:
    
    returns the new Score object
    '''
    if inPlace is False:
        score = copy.deepcopy(score)
    tiedNotes = []
    tieBeneficiary = None 
    for el in score.recurse():
        if not isinstance(el, note.Note):
            continue
        if el.tie is not None:
            if el.tie.type == 'start':
                tieBeneficiary = el
            elif el.tie.type == 'continue':
                tiedNotes.append(el)
            elif el.tie.type == 'stop':
                tiedNotes.append(el)
                tiedQL = tieBeneficiary.duration.quarterLength
                for tiedEl in tiedNotes:
                    tiedQL += tiedEl.duration.quarterLength
                tempDuration = duration.Duration(tiedQL)
                if (tempDuration.type != 'complex' and 
                    len(tempDuration.tuplets) == 0):
                    # successfully can combine these notes into one unit
                    ratioDecimal = tiedQL/float(tieBeneficiary.duration.quarterLength)
                    (tupAct, tupNorm) = common.decimalToTuplet(ratioDecimal)
                    if (tupAct != 0): # error...
                        tempTuplet = duration.Tuplet(tupAct, tupNorm, 
                                                     copy.deepcopy(tempDuration.components[0]))
                        tempTuplet.tupletActualShow = "none"
                        tempTuplet.bracket = False
                        tieBeneficiary.duration = tempDuration
                        tieBeneficiary.duration.tuplets = (tempTuplet,)
                        tieBeneficiary.tie = None #.style = 'hidden'
                        for tiedEl in tiedNotes:
                            tiedEl.tie = None #.style = 'hidden'
                            tiedEl.hideObjectOnPrint = True
                tiedNotes = []

    return score

def convertHouseStyle(score, durationScale=2, barlineStyle='tick', 
                      tieTransfer=True, inPlace=False):
    '''
    The method :meth:`music21.medren.convertHouseStyle` takes a score, 
    durationScale, barlineStyle, tieTransfer, and inPlace as arguments. Of these, 
    only score is not optional.
    
    Default values for durationScale, barlineStyle, tieTransfer, and inPlace are 
    2, 'tick', True, and False respectively. 
    
    Changing :attr:`music21.medren.convertHouseStyle.barlineStyle` 
    changes how the barlines are displayed within the piece. 
    
    Changing :attr:`music21.medren.convertHouseStyle.durationScale` 
    keeps ratios of note durations constant, but scales each duration by the specified value. 
    
    If changing the duration scale causes tied notes, and 
    :attr:`music21.medren.convertHouseStyle.tieTransfer` is set to True, 
    the total duration is transferred to the first note, and all remaining space is left blank.
    
    Examples:
    The first image shows the original score.
    The second image shows the score with each note's duration scaled by 2, 
    and with the barline style set to 'tick'. The circled area shows a space 
    left blank due to tieTransfer being True. 
    
    
    >>> gloria = corpus.parse('luca/gloria')
    >>> #_DOCS_HIDE gloria.show()
    
    
    .. image:: images/medren_convertHouseStyle_1.*
        :width: 600
    
    >>> from music21.alpha import medren
    
    >>> gloria = corpus.parse('luca/gloria')
    >>> newGloria = medren.convertHouseStyle(gloria, durationScale=2, 
    ...                barlineStyle='tick', tieTransfer=True)
    >>> #_DOCS_HIDE newGloria.show()
    
    .. image:: images/medren_convertHouseStyle_2.*
        :width: 600
    '''
    
    if inPlace is False:
        score = copy.deepcopy(score)
    if durationScale != False:
        scaleDurations(score, durationScale, inPlace=True)
    if barlineStyle != False:
        setBarlineStyle(score, barlineStyle, inPlace=True)
    if tieTransfer != False:
        transferTies(score, inPlace=True)
    
    return score

def cummingSchubertStrettoFuga(score):
    '''
    evaluates how well a given score works as a Stretto fuga would work at different intervals
    '''
    lastInterval = None
    sn = score.flat.notes
    strettoKeys = {8: 0, -8: 0, 5: 0, -5: 0, 4: 0, -4: 0}
    
    for i in range(len(sn)-1):
        thisInt = interval.notesToInterval(sn[i], sn[i+1])
        thisGeneric = thisInt.generic.directed
        for strettoType in [8, -8, 5, -5, 4, -4]:
            strettoAllowed = [x[0] for x in allowableStrettoIntervals[strettoType]] 
            #inefficent but who cares
            repeatAllowed = [x[1] for x in allowableStrettoIntervals[strettoType]]
            for j in range(len(strettoAllowed)):
                thisStrettoAllowed = strettoAllowed[j]
                if thisGeneric == thisStrettoAllowed:
                    if thisGeneric != lastInterval:
                        strettoKeys[strettoType] += 1
                    elif thisGeneric == lastInterval and repeatAllowed[j] is True:
                        strettoKeys[strettoType] += 1
            
        lastInterval = thisGeneric
    if score.title:
        print(score.title)
    
    print("intv.\tcount\tpercent")
    for l in sorted(strettoKeys):
        print("%2d\t%3d\t%2d%%" % (l, strettoKeys[l], strettoKeys[l] * 100/len(sn) - 1))
    print("\n")
        
class MedRenException(exceptions21.Music21Exception):
    pass

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   
class TestExternal(unittest.TestCase):   
    def runTest(self):
        pass    
    
    def xtestBarlineConvert(self):
        from music21 import corpus
        testPiece = corpus.parse('luca/gloria')
        setBarlineStyle(testPiece, 'tick')
        testPiece.show()

    def xtestScaling(self):
        from music21 import corpus
        testPiece = corpus.parse('luca/gloria')
        scaleDurations(testPiece, .5, inPlace=True)
        testPiece.show()

    def xtestTransferTies(self):
        from music21 import corpus
        testPiece = corpus.parse('luca/gloria')
        transferTies(testPiece)
        testPiece.show()

    def xtestUnlinked(self):
        s = stream.Stream()
        m = meter.TimeSignature('4/4')
        s.append(m)
        n1 = note.Note('C4', type='whole')
        n2 = note.Note('D4', type='half')
        n1.duration.unlink()
        n1.duration.quarterLength = 2.0
        s.append([n1, n2])

    def xtestPythagSharps(self):
        from music21 import corpus, midi
        gloria = corpus.parse('luca/gloria')
        p = gloria.parts[0].flat
        for n in p.notes:
            if n.name == 'F#':
                n.pitch.microtone = 20
            elif n.name == 'C#':
                n.pitch.microtone = 20
            elif n.step != 'B' and n.accidental is not None and n.accidental.name == 'flat':
                n.pitch.microtone = -20
        unused_mts = midi.translate.streamHierarchyToMidiTracks(p)

        p.show('midi')

    def testHouseStyle(self):
        from music21 import corpus
        gloria = corpus.parse('luca/gloria')
        gloriaNew = convertHouseStyle(gloria)
        gloriaNew.show()

def testStretto():
    from music21 import converter
    salve = converter.parse("A4 A G A D A G F E F G F E D", '4/4') # salveRegina liber 276 (pdf 400)
    adTe = converter.parse("D4 F A G G F A E G F E D G C D E D G F E D", '4/4') # ad te clamamus
    etJesum = converter.parse("D4 AA C D D D E E D D C G F E D G F E D C D", '4/4') 
    salve.title = "Salve Regina (opening)LU p. 276"
    adTe.title = "...ad te clamamus"
    etJesum.title = "...et Jesum"
    for piece in [salve, adTe, etJesum]:
        cummingSchubertStrettoFuga(piece)        

if __name__ == '__main__':
    import music21
    music21.mainTest(Test) #TestExternal)
    #music21.medren.testConvertMensuralMeasure()
#    almaRedemptoris = converter.parse("C4 E F G A G G G A B c G", '4/4') #liber 277 (pdf401)
#    puer = converter.parse('G4 d d d e d c c d c e d d', '4/4') # puer natus est 408 (pdf 554)
#    almaRedemptoris.title = "Alma Redemptoris Mater LU p. 277"
#    puer.title = "Puer Natus Est Nobis"
