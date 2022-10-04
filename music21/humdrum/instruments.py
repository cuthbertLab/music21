# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         humdrum.instruments.py
# Purpose:      Instrument Lists for Humdrum and kern in particular
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Instrument translations from
https://web.archive.org/web/20100115001258/http://www.music-cog.ohio-state.edu/Humdrum/guide.append2.html
'''
from __future__ import annotations

import unittest

from music21 import exceptions21

# noinspection SpellCheckingInspection
humdrumInstrumentClassToInstrument = {
    'vox': 'Vocalist',
    'str': 'StringInstrument',
    'ww': 'WoodwindInstrument',
    'bras': 'BrassInstrument',
    'klav': 'KeyboardInstrument',
    'perc': 'Percussion',
}

# The following table identifies five pre-defined instrument groups:
#
#    *IGacmp    accompaniment instrument
#    *IGsolo    solo instrument
#    *IGcont    basso-continuo instrument
#    *IGripn    ripieno instrument
#    *IGconc    concertino instrument

# noinspection SpellCheckingInspection
humdrumInstruments = {
    'soprn': 'Soprano',
    'cant': 'Soprano',  # Found in many sources, but not a predefined humdrum instrument
    'mezzo': 'MezzoSoprano',
    'calto': 'Alto',  # no distinction with contralto
    'tenor': 'Tenor',
    'barit': 'Baritone',
    'bass': 'Bass',
    'vox': 'Vocalist',
    # *Ifeme    female voice
    # *Imale    male voice
    # *Infant    child's voice
    # *Irecit    recitativo
    # *Ilyrsp    lyric soprano
    # *Idrmsp    dramatic soprano
    # *Icolsp    coloratura soprano
    'alto': 'Alto',
    # *Ictenor    counter-tenor
    # *Iheltn    Heldentenor, tenore robusto
    # *Ilyrtn    lyric tenor
    # *Ibspro    basso profondo
    # *Ibscan    basso cantante
    # *Ifalse    falsetto
    # *Icastr    castrato

    # String Instruments
    # *Iarchl    archlute; archiluth (Fr.); liuto attiorbato/arcileuto/arciliuto (It.)
    'arpa': 'Harp',  # harp; arpa (It.), arpa (Span.)
    'banjo': 'Banjo',
    # *Ibiwa        biwa
    'bguit': 'ElectricBass',
    'cbass': 'Contrabass',
    'cello': 'Violoncello',
    'cemba': 'Harpsichord',  # ; clavecin (Fr.); Cembalo (Ger.); cembalo (It.)
    # *Icetra    cittern; cistre/sistre (Fr.); Cither/Zitter (Ger.); cetra/cetera (It.)
    'clavi': 'Clavichord',  # ; clavicordium (Lat.); clavicorde (Fr.)
    'dulc': 'Dulcimer',  # or cimbalom; Cimbal or Hackbrett (Ger.)
    'eguit': 'ElectricGuitar',
    # *Iforte    fortepiano
    'guitr': 'Guitar',  # ; guitarra (Span.); guitare (Fr.); Gitarre (Ger.); chitarra (It.)
    # *Ihurdy    hurdy-gurdy; variously named in other languages
    'liuto': 'Lute',  # ; lauto, liuto leuto (It.); luth (Fr.); Laute (Ger.)
    # *Ikit        kit; variously named in other languages
    # *Ikokyu    kokyu (Japanese spike fiddle)
    # *Ikomun    komun'go (Korean long zither)
    'koto': 'Koto',  # (Japanese long zither)
    'mando': 'Mandolin',  # ; mandolino (It.); mandoline (Fr.); Mandoline (Ger.)
    'piano': 'Piano',  # forte
    # *Ipipa    Chinese lute
    # *Ipsalt    psaltery (box zither)
    # *Iqin    qin, ch'in (Chinese zither)
    # *Iquitr    gittern (short-necked lute); quitarre (Fr.); Quinterne (Ger.)
    # *Irebec    rebec; rebeca (Lat.); rebec (Fr.); Rebec (Ger.)
    # *Ibansu    bansuri
    # *Isarod    sarod
    'shami': 'Shamisen',  # (Japanese fretless lute)
    'sitar': 'Sitar',
    # *Itambu    tambura, tanpura
    # *Itanbr    tanbur
    # *Itiorb    theorbo; tiorba (It.); tèorbe (Fr.); Theorb (Ger.)
    # *Iud    ud
    'ukule': 'Ukulele',
    # *Ivina    vina
    'viola': 'Viola',  # ; alto (Fr.); Bratsche (Ger.)
    # *Iviolb    bass viola da gamba; viole (Fr.); Gambe (Ger.)
    # *Iviold    viola d'amore; viole d'amour (Fr.); Liebesgeige (Ger.)
    'violn': 'Violin',  # ; violon (Fr.); Violine or Geige (Ger.); violino (It.)
    # *Iviolp    piccolo violin; violino piccolo (It.)
    # *Iviols    treble viola da gamba; viole (Fr.); Gambe (Ger.)
    # *Iviolt    tenor viola da gamba; viole (Fr.); Gambe (Ger.)
    # 'zithr':    'Zither', #; Zither (Ger.); cithare (Fr.); cetra da tavola (It.)

    # Wind Instruments
    'accor': 'Accordion',  # ; accordéon (Fr.); Akkordeon (Ger.)
    'armon': 'Harmonica',  # ; armonica (It.)
    'bagpS': 'Bagpipes',  # (Scottish)
    'bagpI': 'Bagpipes',  # (Irish)
    # *Ibaset    bassett horn
    # *Icalam    chalumeau; calamus (Lat.); kalamos (Gk.)
    # *Icalpe    calliope
    'cangl': 'EnglishHorn',  # ; cor anglais (Fr.)
    # *Ichlms    soprano shawm, chalmeye, shalme, etc.; chalemie (Fr.); ciaramella (It.)
    # *Ichlma    alto shawm, chalmeye, shalme, etc.
    # *Ichlmt    tenor shawm, chalmeye, shalme, etc.
    # *Iclars    soprano clarinet (in either B-flat or A); clarinetto (It.)
    # *Iclarp    piccolo clarinet
    # *Iclara    alto clarinet (in E-flat)
    'clarb': 'BassClarinet',  # (in B-flat)
    'cor': 'Horn',  # ; cor (Fr.); corno (It.); Horn (Ger.)
    # *Icornm    cornemuse; French bagpipe
    # *Icorno    cornett (woodwind instr.); cornetto (It.); cornaboux (Fr.); Zink (Ger.)
    # *Icornt    cornet (brass instr.); cornetta (It.); cornet à pistons (Fr.); Cornett (Ger.)
    # *Ictina    concertina; concertina (Fr.); Konzertina (Ger.)
    'fagot': 'Bassoon',  # ; fagotto (It.)
    # *Ifag_c    contrabassoon; contrafagotto (It.)
    # *Ifife    fife
    'flt': 'Flute',  # ; flauto (It.); Flöte (Ger.); flûte (Fr.)
    # *Iflt_a    alto flute
    # *Iflt_b    bass flute
    # *Ifltds    soprano recorder; flûte à bec, flûte douce (Fr.);
    #            Blockflöte (Ger.); flauto dolce (It.)
    # *Ifltdn    sopranino recorder
    # *Ifltda    alto recorder
    # *Ifltdt    tenor recorder
    # *Ifltdb    bass recorder
    # *Iflugh    flugelhorn
    # *Ihichi    hichiriki (Japanese double reed used in gagaku)
    # *Ikrums    soprano crumhorn; Krummhorn/Krumbhorn (Ger.); tournebout (Fr.)
    # *Ikruma    alto crumhorn
    # *Ikrumt    tenor crumhorn
    # *Ikrumb    bass crumhorn
    # *Inokan    nokan (Japanese flute for the no theatre)
    'oboe': 'Oboe',  # ; hautbois (Fr.); Hoboe, Oboe (Ger.): oboe (It.)
    # *IoboeD    oboe d'amore
    # *Iocari    ocarina
    'organ': 'PipeOrgan',  # ; organum (Lat.); organo (It.); orgue (Fr.); Orgel (Ger.)
    'panpi': 'PanFlute',  # panpipe
    'picco': 'Piccolo',  # flute
    # *Ipiri     Korean p'iri
    # *Iporta    portative organ
    # *Irackt    racket; Rackett (Ger.); cervelas (Fr.)
    'reedo': 'ReedOrgan',
    # *Isarus    sarrusophone
    # *IsaxN    sopranino saxophone (in E-flat)
    'saxS': 'SopranoSaxophone',  # (in B-flat)
    'saxA': 'AltoSaxophone',  # (in E-flat)
    'saxT': 'TenorSaxophone',  # (in B-flat)
    'saxR': 'BaritoneSaxophone',  # (in E-flat)
    # *IsaxB    bass saxophone (in B-flat)
    # *IsaxC    contrabass saxophone (in E-flat)
    'shaku': 'Shakuhachi',
    # *Isheng    mouth organ (Chinese)
    # *Isho    mouth organ (Japanese)
    # *IsxhS    soprano saxhorn (in B-flat)
    # *IsxhA    alto saxhorn (in E-flat)
    # *IsxhT    tenor saxhorn (in B-flat)
    # *IsxhR    baritone saxhorn (in E-flat)
    # *IsxhB    bass saxhorn (in B-flat)
    # *IsxhC    contrabass saxhorn (in E-flat)
    'tromt': 'Trombone',  # tenor; trombone (It.); trombone (Fr.); Posaune (Ger.)
    'tromb': 'BassTrombone',
    'tromp': 'Trumpet',  # ; tromba (It.); trompette (Fr.); Trompete (Ger.)
    'tuba': 'Tuba',
    # *Izurna    zurna

    # Percussion Instruments
    'bdrum': 'BassDrum',  # (kit)
    'campn': 'ChurchBells',  # bell; campana (It.); cloche (Fr.); campana (Span.)
    'caril': 'ChurchBells',  # carillon
    'casts': 'Castanets',  # ; castañetas (Span.); castagnette (It.)
    'chime': 'TubularBells',  # chimes
    # *Iclest    celesta; céleste (Fr.)
    'crshc': 'CrashCymbals',  # (kit)
    # *Ifingc    finger cymbal
    'glock': 'Glockenspiel',
    'gong': 'Gong',
    'marac': 'Maracas',
    'marim': 'Marimba',
    'piatt': 'Cymbals',  # ; piatti (It.); cymbales (Fr.); Becken (Ger.); kymbos (Gk.)
    'ridec': 'RideCymbals',  # (kit)
    'sdrum': 'SnareDrum',  # (kit)
    'spshc': 'SplashCymbals',  # (kit)
    'steel': 'SteelDrum',  # , tinpanny
    # *Itabla    tabla
    'tambn': 'Tambourine',  # , timbrel; tamburino (It.); Tamburin (Ger.)
    'timpa': 'Timpani',  # ; timpani (It.); timbales (Fr.); Pauken (Ger.)
    'tom': 'TomTom',  # drum
    'trngl': 'Triangle',  # ; triangle (Fr.); Triangel (Ger.); triangolo (It.)
    'vibra': 'Vibraphone',
    'xylo': 'Xylophone',  # ; xylophone (Fr.); silofono (It.)

    # Keyboard Instruments
    # dup *Iaccor    accordion; accordéon (Fr.); Akkordeon (Ger.)
    # dup *Icaril    carillon
    # dup *Icemba    harpsichord; clavecin (Fr.); Cembalo (Ger.); cembalo (It.)
    # dup *Iclavi    clavichord; clavicordium (Lat.); clavicorde (Fr.)
    'clest': 'Celesta',  # ; céleste (Fr.)
    # dup *Iforte    fortepiano
    'hammd': 'ElectricOrgan',  # Hammond electronic organ
    # dup *Iorgan    pipe organ; orgue (Fr.); Orgel (Ger.);
    # organo (It.); organo (Span.); organum (Lat.)
    # dup *Ipiano    pianoforte
    # dup *Iporta    portative organ
    # dup *Ireedo    reed organ
    # 'rhode':    'ElectricPiano',  # Fender-Rhodes electric piano
    # *Isynth    keyboard synthesizer
}


class HumdrumInstrumentException(exceptions21.Music21Exception):
    pass


def fromHumdrumClass(hdClass):
    '''
    Get a music21 instrument object from a humdrum instrument class abbreviation

    >>> humdrum.instruments.fromHumdrumClass('vox')
    <music21.instrument.Vocalist 'Voice'>
    '''
    from music21 import instrument
    try:
        i = humdrumInstrumentClassToInstrument[hdClass]
        iObj = getattr(instrument, i)()
        return iObj
    except:
        raise HumdrumInstrumentException(
            f'Cannot get an instrument from this humdrum class *IC{hdClass}')


def fromHumdrumInstrument(hdInst):
    # noinspection SpellCheckingInspection
    '''
    Get a music21 instrument object from a humdrum instrument abbreviation

    >>> humdrum.instruments.fromHumdrumInstrument('calto')
    <music21.instrument.Alto 'Alto'>
    '''
    from music21 import instrument
    try:
        i = humdrumInstruments[hdInst]
        iObj = getattr(instrument, i)()
        return iObj
    except:
        raise HumdrumInstrumentException(
            f'Cannot get an instrument from this humdrum class: *I{hdInst}')


class Test(unittest.TestCase):

    def testClasses(self):
        from music21 import instrument

        for x in humdrumInstrumentClassToInstrument:
            i = humdrumInstrumentClassToInstrument[x]
            self.assertNotEqual(getattr(instrument, i)().instrumentName, None)

    def testIndividuals(self):
        from music21 import instrument

        for x in humdrumInstruments:
            i = humdrumInstruments[x]
            self.assertNotEqual(getattr(instrument, i)().instrumentName, None)

    def testHumdrumParse(self):
        from music21 import corpus
        c = corpus.parse('Palestrina/Kyrie_40')
        foundInstruments = []
        for x in c.recurse():
            if 'Instrument' in x.classes:
                foundInstruments.append(str(x))
        self.assertEqual(foundInstruments,
                         ['Soprano', 'Alto', 'Tenor', 'Tenor', 'Bass'])
        alto = c.parts[1].flatten().getInstrument()
        self.assertIn('Alto', alto.classes)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
