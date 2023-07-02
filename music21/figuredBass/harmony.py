# ------------------------------------------------------------------------------
# Name:         figuredBass.harmony.py
# Purpose:      Music21Object for FiguredBass as a Harmony subclass
#
# Authors:      Moritz Heffter
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2011-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The FiguredBass object is a subclass of Harmony that will (eventually) be able
to represent figured bass symbols in music notation and also realize it.

BETA at this point.

Based on work by Jose Cabal-Ugaz.
'''
from __future__ import annotations

from collections.abc import Iterable

from music21.harmony import Harmony

from music21.figuredBass import notation


class FiguredBass(Harmony):
    '''
    *BETA*: FiguredBass objects are currently in beta and may change without warning.

    The FiguredBass objects store information about thorough bass figures.
    It is created as a representation for <fb> tags in MEI and <figured-bass> tags in MusicXML.
    The FiguredBass object derives from the Harmony object and can be used
    in the following way:

    >>> fb = figuredBass.FiguredBass('#,6#')
    >>> fb
    <music21.figuredBass.harmony.FiguredBass #,6#>

    (note that the FiguredBass object can be found in either music21.figuredBass.FiguredBass
    or music21.figuredBass.harmony.FiguredBass.  It is the same class)

    The single figures are stored as figuredBass.notation.Figure objects:

    >>> fb.notation.figures[0]
    <music21.figuredBass.notation.Figure 3 <Modifier # sharp>>

    The figures can be accessed and manipulated individually by passing in `figureStrings`
    (plural), and extenders are allowed as with `_`:

    >>> fb2 = figuredBass.FiguredBass(figureStrings=['#_', '6#'])
    >>> fb2
    <music21.figuredBass.harmony.FiguredBass #_,6#>
    >>> fb2.notation.hasExtenders
    True

    Currently, figured bass objects do not have associated pitches.  This will change.

    >>> fb.pitches
    ()

    * new in v9.3
    '''
    def __init__(self,
                 figureString: str = '',
                 *,
                 figureStrings: Iterable[str] = (),
                 **keywords):
        super().__init__(**keywords)

        self._figs: str = ''

        if figureString != '':
            self.figureString = figureString
        elif figureStrings:
            self.figureString = ','.join(figureStrings)
        else:
            self.figureString = ''

        self._figNotation: notation.Notation = notation.Notation(self._figs)

    @property
    def notation(self) -> notation.Notation:
        return self._figNotation

    @notation.setter
    def notation(self, figureNotation: notation.Notation):
        '''
        Sets the notation property of the FiguresBass object and updates the
        figureString property if needed.

        >>> fb = figuredBass.FiguredBass('6,#')
        >>> fb.figureString, fb.notation
        ('6,#', <music21.figuredBass.notation.Notation 6,#>)

        >>> fb.notation = figuredBass.notation.Notation('7b,b')
        >>> fb.figureString, fb.notation
        ('7b,b', <music21.figuredBass.notation.Notation 7b,b>)
        '''

        self._figNotation = figureNotation
        if figureNotation.notationColumn != self._figs:
            self.figureString = figureNotation.notationColumn

    @property
    def figureString(self) -> str:
        return self._figs

    @figureString.setter
    def figureString(self, figureString: str):
        '''
        Sets the figureString property of the FiguresBass object and updates the
        notation property if needed.

        >>> fb = figuredBass.FiguredBass('6,#')
        >>> fb.figureString, fb.notation
        ('6,#', <music21.figuredBass.notation.Notation 6,#>)

        >>> fb.figureString = '5,b'
        >>> fb.figureString, fb.notation
        ('5,b', <music21.figuredBass.notation.Notation 5,b>)
        '''

        if isinstance(figureString, str) and figureString != '':
            if ',' in figureString:
                self._figs = figureString
            else:
                self._figs = ','.join(figureString)

            self.notation = notation.Notation(self._figs)


    def _reprInternal(self):
        return self.notation.notationColumn


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest()

