# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/xmlObjects.py
# Purpose:      MusicXML objects for conversion to and from music21
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------


# these single-entity tags are bundled together. 
from music21 import articulations
from music21 import expressions

DYNAMIC_MARKS = ['p', 'pp', 'ppp', 'pppp', 'ppppp', 'pppppp',
        'f', 'ff', 'fff', 'ffff', 'fffff', 'ffffff',
        'mp', 'mf', 'sf', 'sfp', 'sfpp', 'fp', 'rf', 'rfz', 'sfz', 'sffz', 'fz',
        'other-dynamics' # non-empty...
        ] 

ARTICULATION_MARKS = {'accent'       : articulations.Accent,
                   'strong-accent'   : articulations.StrongAccent,
                   'staccato'        : articulations.Staccato,
                   'staccatissimo'   : articulations.Staccatissimo,
                   'spiccato'        : articulations.Spiccato,
                   'tenuto'          : articulations.Tenuto,
                   'detached-legato' : articulations.DetachedLegato,
                   'scoop'           : articulations.Scoop,
                   'plop'            : articulations.Plop,
                   'doit'            : articulations.Doit,
                   'falloff'         : articulations.Falloff,
                   'breath-mark'     : articulations.BreathMark,
                   'caesura'         : articulations.Caesura,
                   'stress'          : articulations.Stress,
                   'unstress'        : articulations.Unstress,
                   'other-articulation': articulations.Articulation,
                   }

TECHNICAL_MARKS = {'up-bow'          : articulations.UpBow,
                   'down-bow'        : articulations.DownBow,
                   'harmonic'        : articulations.Harmonic,
                   'open-string'     : articulations.OpenString,
                   'thumb-position'  : articulations.StringThumbPosition,
                   'fingering'       : articulations.StringFingering,
                   'pluck'           : articulations.FrettedPluck,
                   'double-tongue'   : articulations.DoubleTongue,
                   'triple-tongue'   : articulations.TripleTongue,
                   'stopped'         : articulations.Stopped,
                   'snap-pizzicato'  : articulations.SnapPizzicato,
                   'fret'            : articulations.FretIndication,
                   'string'          : articulations.StringIndication,
                   'hammer-on'       : articulations.HammerOn,
                   'pull-off'        : articulations.PullOff,
                   #bend not implemented because it needs many sub components
                   #bend'            : articulations.FretBend,
                   'tap'             : articulations.FretTap,
                   'heel'            : articulations.OrganHeel,
                   'toe'             : articulations.OrganToe,
                   'fingernails'     : articulations.HarpFingerNails,
                   'other-technical' : articulations.TechnicalIndication,
                   }

# NON-spanner ornaments that go into Expressions
ORNAMENT_MARKS = {'trill-mark'       : expressions.Trill,
                  'turn'             : expressions.Turn,
                  # TODO: 'delayed-turn'
                  'inverted-turn'    : expressions.InvertedTurn,
                  # TODO: 'delayed-inverted-turn'
                  # TODO: 'vertical-turn'
                  'shake'            : expressions.Shake,
                  'schleifer'        : expressions.Schleifer,
                  'other-ornament'   : expressions.Ornament
                  # TODO: 'accidental-mark' -- something else...
                  }
#-------------------------------------------------------------------------------
# helpers

def yesNoToBoolean(value):
    if value in ('yes', True):
        return True
    return False

def booleanToYesNo(value):
    if value:
        return 'yes'
    return 'no'

#-------------------------------------------------------------------------------
