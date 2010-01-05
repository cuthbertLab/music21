# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testPrimitive.py
# Purpose:      MusicXML test files
#
# Authors:      Christopher Ariza
#
# License:      LGPL
#-------------------------------------------------------------------------------


import doctest, unittest

import music21


pitches01a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <movement-title>Pitches and accidentals</movement-title>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">All pitches from G to c'''' in 
          ascending steps; First without accidentals, then with a sharp and then 
          with a flat accidental. Double alterations and cautionary accidentals 
          are tested at the end.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>G</step>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <note>
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7">
      <note>
        <pitch>
          <step>C</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8">
      <note>
        <pitch>
          <step>G</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>7</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="9">
      <note>
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>1</alter>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="10">
      <note>
        <pitch>
          <step>D</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="11">
      <note>
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="12">
      <note>
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="13">
      <note>
        <pitch>
          <step>B</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="14">
      <note>
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="15">
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="16">
      <note>
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>7</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="17">
      <note>
        <pitch>
          <step>G</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="18">
      <note>
        <pitch>
          <step>D</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="19">
      <note>
        <pitch>
          <step>A</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="20">
      <note>
        <pitch>
          <step>E</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="21">
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="22">
      <note>
        <pitch>
          <step>F</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="23">
      <note>
        <pitch>
          <step>C</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="24">
      <note>
        <pitch>
          <step>G</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>6</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>-1</alter>
          <octave>7</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="31">
      <note>
        <pitch>
          <step>C</step>
          <alter>2</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>double-sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>-2</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat-flat</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="32">
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental editorial="yes">sharp</accidental>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

"""



directions31a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <movement-title>MusicXML directions (attached to staff)</movement-title>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">All &lt;direction&gt; elements 
          defined in MusicXML. The lyrics for each note describes the direction
          element assigned to that note.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <!-- Direction type can contain the following child types:
         rehearsal+ | segno+ | words+ |
         coda+ | wedge | dynamics+ | dashes | bracket | pedal | 
         metronome | octave-shift | harp-pedals | damp | 
         damp-all | eyeglasses | scordatura | image |
         accordion-registration | other-direction -->
    <!-- Rehearsal marks -->
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <direction placement="below">
        <direction-type>
          <rehearsal>A</rehearsal>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>reh.A (def=sq.)</text></lyric>
      </note>
      <direction placement="above">
        <direction-type>
          <rehearsal enclosure="none">B</rehearsal>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>reh.B (none)</text></lyric>
      </note>
      <direction>
        <direction-type>
          <rehearsal enclosure="square">Test</rehearsal>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>reh.Test (sq.)</text></lyric>
      </note>
      <direction>
        <direction-type>
          <rehearsal enclosure="circle">Crc</rehearsal>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>reh.Crc (crc.)</text></lyric>
      </note>
    </measure>
    <!-- Segno, Coda, Words (extra unit test for formatting!),  Eyeglasses -->
    <measure number="2">
      <direction>
        <direction-type>
          <segno/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Segno</text></lyric>
      </note>
      <direction>
        <direction-type>
          <coda/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Coda</text></lyric>
      </note>
      <direction>
        <direction-type>
          <words>words</words>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Words</text></lyric>
      </note>
      <direction>
        <direction-type>
          <eyeglasses/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Eyegl.</text></lyric>
      </note>
    </measure>
    <!-- Dynamics: p | pp | ppp | pppp | ppppp | pppppp |
        f | ff | fff | ffff | fffff | ffffff | mp | mf | sf |
        sfp | sfpp | fp | rf | rfz | sfz | sffz | fz | 
        other-dynamics -->
    <measure number="3">
      <direction>
        <direction-type>
          <dynamics><p/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>p</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><pp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>pp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><ppp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>ppp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><pppp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>pppp</text></lyric>
      </note>
    </measure>
    <measure number="4">
      <direction>
        <direction-type>
          <dynamics><ppppp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>ppppp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><pppppp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>pppppp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><f/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>f</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><ff/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>ff</text></lyric>
      </note>
    </measure>
    <measure number="5">
      <direction>
        <direction-type>
          <dynamics><fff/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>fff</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><ffff/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>ffff</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><fffff/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>fffff</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><ffffff/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>ffffff</text></lyric>
      </note>
    </measure>
    <measure number="6">
      <direction>
        <direction-type>
          <dynamics><mp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>mp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><mf/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>mf</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><sf/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>sf</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><sfp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>sfp</text></lyric>
      </note>
    </measure>
    <measure number="7">
      <direction>
        <direction-type>
          <dynamics><sfpp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>sfpp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><fp/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>fp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><rf/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>rf</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><rfz/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>rfz</text></lyric>
      </note>
    </measure>
    <measure number="8">
      <direction>
        <direction-type>
          <dynamics><sfz/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>sfz</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><sffz/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>sffz</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><fz/></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>fz</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dynamics><other-dynamics>abc-ffz</other-dynamics></dynamics>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>abc-ffz (oth.)</text></lyric>
      </note>
    </measure>
    <!-- Spanners (there is another unit test for testing the various options):
         wedge, dashes, bracket, pedal, octave-shift -->
    <measure number="9">
      <direction>
        <direction-type>
          <wedge type="crescendo"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>hairpin</text></lyric>
      </note>
      <direction>
        <direction-type>
          <wedge type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>cresc</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dashes type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>dash</text></lyric>
      </note>
      <direction>
        <direction-type>
          <dashes type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>es</text></lyric>
      </note>
    </measure>
    <measure number="10">
      <direction>
        <direction-type>
          <bracket type="start" line-end="none"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>bra</text></lyric>
      </note>
      <direction>
        <direction-type>
          <bracket type="stop" line-end="none"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>cket</text></lyric>
      </note>
      <direction>
        <direction-type>
          <octave-shift type="up"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>oct.</text></lyric>
      </note>
      <direction>
        <direction-type>
          <octave-shift type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>shift</text></lyric>
      </note>
    </measure>
    <measure number="11">
      <direction>
        <direction-type>
          <pedal type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>pedal</text></lyric>
      </note>
      <direction>
        <direction-type>
          <pedal type="change"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>continue</syllabic><text>change</text></lyric>
      </note>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <pedal type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>mark</text></lyric>
      </note>
    </measure>
    <!-- metronome, harp-pedals, damp, damp-all, scordatura, accordion-registration -->
    <measure number="12">
      <direction>
        <direction-type>
          <metronome><beat-unit>quarter</beat-unit><per-minute>60</per-minute></metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Metr.</text></lyric>
      </note>
      <direction>
        <direction-type>
          <harp-pedals>
            <pedal-tuning>
              <pedal-step>D</pedal-step>
              <pedal-alter>0</pedal-alter>
            </pedal-tuning>
            <pedal-tuning>
              <pedal-step>C</pedal-step>
              <pedal-alter>-1</pedal-alter>
            </pedal-tuning>
            <pedal-tuning>
              <pedal-step>B</pedal-step>
              <pedal-alter>-1</pedal-alter>
            </pedal-tuning>
            <pedal-tuning>
              <pedal-step>E</pedal-step>
              <pedal-alter>0</pedal-alter>
            </pedal-tuning>
            <pedal-tuning>
              <pedal-step>F</pedal-step>
              <pedal-alter>0</pedal-alter>
            </pedal-tuning>
            <pedal-tuning>
              <pedal-step>G</pedal-step>
              <pedal-alter>1</pedal-alter>
            </pedal-tuning>
            <pedal-tuning>
              <pedal-step>A</pedal-step>
              <pedal-alter>-1</pedal-alter>
            </pedal-tuning>
          </harp-pedals>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Harp ped.</text></lyric>
      </note>
      <direction>
        <direction-type>
          <damp/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Damp</text></lyric>
      </note>
      <direction>
        <direction-type>
          <damp-all/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Damp all</text></lyric>
      </note>
    </measure>
    <measure number="13">
      <direction>
        <direction-type>
          <scordatura>
              <accord string="0"><tuning-step>C</tuning-step><tuning-octave>3</tuning-octave></accord>
              <accord string="1"><tuning-step>G</tuning-step><tuning-octave>5</tuning-octave></accord>
              <accord string="2"><tuning-step>E</tuning-step><tuning-octave>5</tuning-octave></accord>
          </scordatura>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Scord.</text></lyric>
      </note>
      <direction>
        <direction-type>
          <accordion-registration>
              <accordion-high/>
              <accordion-middle>2</accordion-middle>
              <accordion-low/>
          </accordion-registration>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>Accordion reg.</text></lyric>
      </note>
      <note>
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <!-- Other issues: Multiple direction-type elements: "subito p", ppp<fff -->
    <measure number="14">
      <direction placement="below">
        <direction-type>
          <words default-y="-80" font-family="Times New Roman" font-size="10.25" font-style="italic">subito</words>
        </direction-type>
        <direction-type>
          <words default-y="-80" font-family="Times New Roman" font-size="10.25"> </words>
        </direction-type>
        <direction-type>
          <dynamics default-y="-80">
            <p/>
          </dynamics>
        </direction-type>
        <offset>2</offset>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>subp</text></lyric>
      </note>
      <direction placement="below">
        <direction-type>
          <dynamics><ppp/></dynamics>
        </direction-type>
        <direction-type>
          <wedge type="crescendo"/>
        </direction-type>
        <offset>2</offset>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>ppp cresc</text></lyric>
      </note>
      <direction placement="below">
        <direction-type>
          <wedge type="stop"/>
        </direction-type>
        <direction-type>
          <dynamics><fff/></dynamics>
        </direction-type>
        <offset>2</offset>
      </direction>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>to fff</text></lyric>
      </note>
      <note>
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1"><text>subp</text></lyric>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
  </part>
  <!--=========================================================-->
</score-partwise>
"""







lyricsMelisma61d = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">How to treat lyrics and slurred 
          notes. Normally, a slurred group of notes is assigned only one lyrics 
          syllable.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="start"/>
        </notations>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>Me</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <tied type="start"/>
        </notations>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>lis</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="start"/>
        </notations>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>ma.</text>
          <extend/>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

"""





notations32a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <movement-title>MusicXML notations (attached to note)</movement-title>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">All &lt;notation&gt; elements 
          defined in MusicXML. The lyrics show the notation assigned to each 
          note.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name></part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <!-- General Notation elements (no spanners, which are tested separately):
         fermata | arpeggiate | non-arpeggiate | accidental-mark -->
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <fermata type="upright"/>
        </notations>
        <lyric number="1"><text>ferm.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <fermata>normal</fermata>
        </notations>
        <lyric number="1"><text>normal ferm.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <fermata>angled</fermata>
        </notations>
        <lyric number="1"><text>angled ferm.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <fermata>square</fermata>
        </notations>
        <lyric number="1"><text>square ferm.</text></lyric>
      </note>
    </measure>
    <measure number="2">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <fermata type="inverted"/>
        </notations>
        <lyric number="1"><text>inv.ferm.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations><arpeggiate/></notations>
        <lyric number="1"><text>arp.</text></lyric>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>E</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations><arpeggiate/></notations>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>G</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations><arpeggiate/></notations>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations><non-arpeggiate type="bottom"/></notations>
        <lyric number="1"><text>non-arp.</text></lyric>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>E</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>G</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations><non-arpeggiate type="top"/></notations>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <accidental-mark placement="above">double-sharp</accidental-mark>
        </notations>
        <lyric number="1"><text>acc.mark</text></lyric>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>

    <!-- Articulations: 
            accent | strong-accent | staccato | tenuto |
            detached-legato | staccatissimo | spiccato |
            scoop | plop | doit | falloff | breath-mark |
            caesura | stress | unstress | other-articulation -->
    <measure number="3">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><accent/></articulations>
        </notations>
        <lyric number="1"><text>acc.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><strong-accent/></articulations>
        </notations>
        <lyric number="1"><text>str.-acc.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><staccato/></articulations>
        </notations>
        <lyric number="1"><text>stacc.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><tenuto/></articulations>
        </notations>
        <lyric number="1"><text>ten.</text></lyric>
      </note>
    </measure>
    <measure number="4">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><detached-legato/></articulations>
        </notations>
        <lyric number="1"><text>det.-leg.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><staccatissimo/></articulations>
        </notations>
        <lyric number="1"><text>stacc.ss</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><spiccato/></articulations>
        </notations>
        <lyric number="1"><text>spicc.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><scoop/></articulations>
        </notations>
        <lyric number="1"><text>scoop</text></lyric>
      </note>
    </measure>
    <measure number="5">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><plop/></articulations>
        </notations>
        <lyric number="1"><text>plop</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><doit/></articulations>
        </notations>
        <lyric number="1"><text>doit</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><falloff/></articulations>
        </notations>
        <lyric number="1"><text>falloff</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><breath-mark/></articulations>
        </notations>
        <lyric number="1"><text>breath</text></lyric>
      </note>
    </measure>
    <measure number="6">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><caesura/></articulations>
        </notations>
        <lyric number="1"><text>caes.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><stress/></articulations>
        </notations>
        <lyric number="1"><text>stress</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations><unstress/></articulations>
        </notations>
        <lyric number="1"><text>unstr.</text></lyric>
      </note>
      <note>
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>

    <!-- Ornaments:
         trill-mark | turn | delayed-turn | inverted-turn |
         shake | wavy-line | mordent | inverted-mordent | 
         schleifer | tremolo | other-ornament), 
         accidental-mark 
         
         Test cases for various tremolo options are in a separate 
         unit test file
         -->
    <measure number="7">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><trill-mark/></ornaments>
        </notations>
        <lyric number="1"><text>tr.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><turn/></ornaments>
        </notations>
        <lyric number="1"><text>turn</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><delayed-turn/></ornaments>
        </notations>
        <lyric number="1"><text>del.turn</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><inverted-turn/></ornaments>
        </notations>
        <lyric number="1"><text>inv.turn</text></lyric>
      </note>
    </measure>
    <measure number="8">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><shake/></ornaments>
        </notations>
        <lyric number="1"><text>shake</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <wavy-line placement="below" type="start"/>
          </ornaments>
        </notations>
        <lyric number="1"><syllabic>begin</syllabic><text>wavy</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <wavy-line placement="below" type="stop"/>
            <wavy-line placement="below" type="start"/>
          </ornaments>
        </notations>
        <lyric number="1"><syllabic>continue</syllabic><text>wavy</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <wavy-line placement="below" type="stop"/>
          </ornaments>
        </notations>
        <lyric number="1"><syllabic>end</syllabic><text>line</text></lyric>
      </note>
    </measure>
    <measure number="9">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><mordent/></ornaments>
        </notations>
        <lyric number="1"><text>mord.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><inverted-mordent/></ornaments>
        </notations>
        <lyric number="1"><text>inv.mord.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><schleifer/></ornaments>
        </notations>
        <lyric number="1"><text>schl.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><tremolo/></ornaments>
        </notations>
        <lyric number="1"><text>trem.</text></lyric>
      </note>
    </measure>
    <measure number="10">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <turn/>
            <accidental-mark>natural</accidental-mark>
          </ornaments>
        </notations>
        <lyric number="1"><text>turn+acc.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <turn/>
            <accidental-mark placement="above">sharp</accidental-mark>
            <accidental-mark placement="above">three-quarters-flat</accidental-mark>
          </ornaments>
        </notations>
        <lyric number="1"><text>turn+acc.(ab.+bel./rel to turn)</text></lyric>
      </note>
      <note>
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>

    <!-- Technical:
         up-bow | down-bow | harmonic | open-string |
         thumb-position | fingering | pluck | double-tongue |
         triple-tongue | stopped | snap-pizzicato | fret |
         string | hammer-on | pull-off | bend | tap | heel |
         toe | fingernails | other-technical -->
    <measure number="11">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><up-bow/></technical>
        </notations>
        <lyric number="1"><text>up-b.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><down-bow/></technical>
        </notations>
        <lyric number="1"><text>down-b.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><harmonic/></technical>
        </notations>
        <lyric number="1"><text>harm.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><harmonic><natural/></harmonic></technical>
        </notations>
        <lyric number="1"><text>nat.harm.</text></lyric>
      </note>
    </measure>
    <measure number="12">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><harmonic><artificial/></harmonic></technical>
        </notations>
        <lyric number="1"><text>art.harm.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><harmonic><natural/><base-pitch/></harmonic></technical>
        </notations>
        <lyric number="1"><text>nat.h./base</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><harmonic><natural/><touching-pitch/></harmonic></technical>
        </notations>
        <lyric number="1"><text>nat.h./touching</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><harmonic><natural/><sounding-pitch/></harmonic></technical>
        </notations>
        <lyric number="1"><text>nat.h./sounding</text></lyric>
      </note>
    </measure>
    <measure number="13">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><open-string/></technical>
        </notations>
        <lyric number="1"><text>open-str.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><thumb-position/></technical>
        </notations>
        <lyric number="1"><text>thumb-pos.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering/></technical>
        </notations>
        <lyric number="1"><text>empty fing.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>1</fingering></technical>
        </notations>
        <lyric number="1"><text>fing.1</text></lyric>
      </note>
    </measure>
    <measure number="14">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>2</fingering></technical>
        </notations>
        <lyric number="1"><text>fing.2</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>3</fingering></technical>
        </notations>
        <lyric number="1"><text>fing.3</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>4</fingering></technical>
        </notations>
        <lyric number="1"><text>fing.4</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>5</fingering></technical>
        </notations>
        <lyric number="1"><text>fing.5</text></lyric>
      </note>
    </measure>
    <measure number="15">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>something</fingering></technical>
        </notations>
        <lyric number="1"><text>fing.sth.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingering>5</fingering><fingering substitution="yes">3</fingering><fingering alternate="yes">2</fingering></technical>
        </notations>
        <lyric number="1"><text>mult.fing.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><pluck/></technical>
        </notations>
        <lyric number="1"><text>empty pluck</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><pluck>a</pluck></technical>
        </notations>
        <lyric number="1"><text>pluck a</text></lyric>
      </note>
    </measure>
    <measure number="16">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><double-tongue/></technical>
        </notations>
        <lyric number="1"><text>dbl.tng.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><triple-tongue/></technical>
        </notations>
        <lyric number="1"><text>trpl.tng.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><stopped/></technical>
        </notations>
        <lyric number="1"><text>stopped</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><snap-pizzicato/></technical>
        </notations>
        <lyric number="1"><text>snp.pizz.</text></lyric>
      </note>
    </measure>
    <measure number="17">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fret/></technical>
        </notations>
        <lyric number="1"><text>empty fret</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fret>0</fret></technical>
        </notations>
        <lyric number="1"><text>fret0</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><string/></technical>
        </notations>
        <lyric number="1"><text>empty str.</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <string>5</string>
          </technical>
        </notations>
        <lyric number="1"><text>str. 5</text></lyric>
      </note>
    </measure>
    <measure number="18">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <hammer-on type="start"/>
          </technical>
        </notations>
        <lyric number="1"><syllabic>begin</syllabic><text>hammer</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <hammer-on type="stop"/>
          </technical>
        </notations>
        <lyric number="1"><syllabic>end</syllabic><text>on</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <pull-off type="start"/>
          </technical>
        </notations>
        <lyric number="1"><syllabic>begin</syllabic><text>pull</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <pull-off type="stop"/>
          </technical>
        </notations>
        <lyric number="1"><syllabic>end</syllabic><text>off</text></lyric>
      </note>
    </measure>
    <measure number="19">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <bend><bend-alter>4</bend-alter></bend>
          </technical>
        </notations>
        <lyric number="1"><text>bend</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <bend><bend-alter>3</bend-alter><release/><with-bar/></bend>
          </technical>
        </notations>
        <lyric number="1"><text>b.3 with-bar</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <bend><bend-alter>-0.5</bend-alter><pre-bend/></bend>
          </technical>
        </notations>
        <lyric number="1"><text>pre-b. -0.5</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <bend><bend-alter>3.5</bend-alter><release/></bend>
          </technical>
        </notations>
        <lyric number="1"><text>b. release 3.5</text></lyric>
      </note>
    </measure>
    <measure number="20">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><tap/></technical>
        </notations>
        <lyric number="1"><text>tap</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><tap>T</tap></technical>
        </notations>
        <lyric number="1"><text>tap T</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><heel/></technical>
        </notations>
        <lyric number="1"><text>heel</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><toe substitution="yes"/></technical>
        </notations>
        <lyric number="1"><text>toe</text></lyric>
      </note>
    </measure>
    <measure number="21">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical><fingernails/></technical>
        </notations>
        <lyric number="1"><text>fingern.</text></lyric>
      </note>
      <note>
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    
    <!-- Dynamics, attached to notes by putting them inside <notations> tags -->
    <measure number="22">
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <dynamics><f/></dynamics>
        </notations>
        <lyric number="1"><text>f</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <dynamics><ppp/></dynamics>
        </notations>
        <lyric number="1"><text>ppp</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <dynamics><sfp/></dynamics>
        </notations>
        <lyric number="1"><text>sfp</text></lyric>
      </note>
      <note>
        <pitch>
          <step>C</step><octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <dynamics><other-dynamics>sfffz</other-dynamics></dynamics>
        </notations>
        <lyric number="1"><text>Oth.dyn.</text></lyric>
      </note>
    </measure>
    
    <!-- General tests: multiple notations, directions, etc. -->
    <measure number="23">
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations>
            <strong-accent placement="above" type="up"/>
            <staccato placement="above"/>
          </articulations>
        </notations>
        <lyric number="1"><text>both above</text></lyric>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <articulations>
            <accent placement="below"/>
            <tenuto placement="below"/>
            <staccato placement="above"/>
          </articulations>
        </notations>
        <lyric number="1"><text>ab./bel./bel.</text></lyric>
      </note>
      <note>
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
</score-partwise>
"""


restsDurations02a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <movement-title>Rest unit test</movement-title>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">All different rest lengths: A 
          two-bar multi-measure rest, a whole rest, a half, etc. until a 
          128th-rest; Then the same with dotted durations.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>32</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
        <measure-style>
          <multiple-rest>2</multiple-rest>
        </measure-style>
      </attributes>
      <note>
        <rest/>
        <duration>128</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <rest/>
        <duration>128</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>128</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <note>
        <rest/>
        <duration>64</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <note>
        <rest/>
        <duration>32</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>32nd</type>
      </note>
      <note>
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>64th</type>
      </note>
      <note>
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>128th</type>
      </note>
      <note>
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>128th</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <note>
        <rest/>
        <duration>96</duration>
        <voice>1</voice>
        <type>half</type>
        <dot/>
      </note>
      <note>
        <rest/>
        <duration>32</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <note>
        <rest/>
        <duration>48</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
      </note>
      <note>
        <rest/>
        <duration>24</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
      </note>
      <note>
        <rest/>
        <duration>12</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
      </note>
      <note>
        <rest/>
        <duration>6</duration>
        <voice>1</voice>
        <type>32nd</type>
        <dot/>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>64th</type>
        <dot/>
      </note>
      <note>
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>128th</type>
        <dot/>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

"""


rhythmDurations03a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">All note durations, from long, 
          brevis, whole until 128th; First with their plain values, then dotted 
          and finally doubly-dotted.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>64</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>16</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1024</duration>
        <voice>1</voice>
        <type>longa</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>512</duration>
        <voice>1</voice>
        <type>breve</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>256</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>128</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>64</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>32</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>32nd</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>64th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>128th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>128th</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <attributes>
        <time>
          <beats>24</beats>
          <beat-type>4</beat-type>
        </time>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1536</duration>
        <voice>1</voice>
        <type>longa</type>
        <dot/>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>768</duration>
        <voice>1</voice>
        <type>breve</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>384</duration>
        <voice>1</voice>
        <type>whole</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>192</duration>
        <voice>1</voice>
        <type>half</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>96</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>48</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>24</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>32nd</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>64th</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>128th</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>128th</type>
        <dot/>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <attributes>
        <time>
          <beats>28</beats>
          <beat-type>4</beat-type>
        </time>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1792</duration>
        <voice>1</voice>
        <type>longa</type>
        <dot/>
        <dot/>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>896</duration>
        <voice>1</voice>
        <type>breve</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>448</duration>
        <voice>1</voice>
        <type>whole</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>224</duration>
        <voice>1</voice>
        <type>half</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>112</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>14</duration>
        <voice>1</voice>
        <type>32nd</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>7</duration>
        <voice>1</voice>
        <type>64th</type>
        <dot/>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>7</duration>
        <voice>1</voice>
        <type>64th</type>
        <dot/>
        <dot/>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""



chordsThreeNotesDuration21c = """<?xml version="1.0"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 0.6 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
	<identification> 
		<miscellaneous>
			<miscellaneous-field name="description">Some three-note 
                            chords, with various durations.</miscellaneous-field>
		</miscellaneous>
	</identification> 
	<part-list>
		<score-part id="P0">
			<part-name>MusicXML Part</part-name>
		</score-part>
	</part-list>
	<part id="P0">
		<measure number="1">
			<attributes>
				<divisions>960</divisions>
				<time>
				<beats>4</beats>
				<beat-type>4</beat-type>
				</time>
				<clef>
				<sign>G</sign>
				<line>2</line>
				</clef>
			</attributes>
			<note>
				<pitch>
					<step>F</step>
					<octave>4</octave>
				</pitch>
				<duration>1440</duration>
				<voice>1</voice>
				<type>quarter</type>
				<dot/>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>1440</duration>
				<voice>1</voice>
				<type>quarter</type>
				<dot/>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>C</step>
					<octave>5</octave>
				</pitch>
				<duration>1440</duration>
				<voice>1</voice>
				<type>quarter</type>
				<dot/>
			</note>
			<note>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>480</duration>
				<voice>1</voice>
				<type>eighth</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>G</step>
					<octave>5</octave>
				</pitch>
				<duration>480</duration>
				<voice>1</voice>
				<type>eighth</type>
			</note>
			<note>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>F</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>C</step>
					<octave>5</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>F</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>C</step>
					<octave>5</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
		</measure>

		<measure number="2">
			<note>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>F</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>E</step>
					<octave>5</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>F</step>
					<octave>4</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>F</step>
					<octave>5</octave>
				</pitch>
				<duration>960</duration>
				<voice>1</voice>
				<type>quarter</type>
			</note>
			<note>
				<pitch>
					<step>A</step>
					<octave>4</octave>
				</pitch>
				<duration>1920</duration>
				<voice>1</voice>
				<type>half</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>F</step>
					<octave>4</octave>
				</pitch>
				<duration>1920</duration>
				<voice>1</voice>
				<type>half</type>
			</note>
			<note>
				<chord/>
				<pitch>
					<step>D</step>
					<octave>5</octave>
				</pitch>
				<duration>1920</duration>
				<voice>1</voice>
				<type>half</type>
			</note>
		</measure>
	</part>
</score-partwise>
"""


beams01 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <identification>
    <rights>©</rights>
    <encoding>
      <software>Finale 2010 for Macintosh</software>
      <software>Dolet Light for Finale 2010</software>
      <encoding-date>2009-11-05</encoding-date>
    </encoding>
  </identification>

  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I1">
        <instrument-name>Acoustic Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="490">
      <attributes>
        <divisions>8</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note default-x="87">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10">up</stem>
      </note>
      <note default-x="153">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="196">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
      </note>
      <note default-x="240">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="265">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="293">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="319">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="346">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="364">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="382">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="400">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="418">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="436">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="453">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="472">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="423">
      <note default-x="17">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10">up</stem>
      </note>
      <note default-x="82">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="125">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
      </note>
      <note default-x="169">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="194">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="221">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="248">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="275">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="293">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="311">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="330">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
      </note>
      <note default-x="349">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="367">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="384">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">continue</beam>
      </note>
      <note default-x="403">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="392">
      <print new-system="yes">
        <system-layout>
          <system-distance>114</system-distance>
        </system-layout>
      </print>
      <note default-x="55">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="100">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="130">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
      </note>
      <note default-x="161">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="181">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="202">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="224">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="245">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="263">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">end</beam>
      </note>
      <note default-x="281">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="300">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
      </note>
      <note default-x="318">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="336">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">end</beam>
      </note>
      <note default-x="354">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="372">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="18">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="592">
      <note default-x="13">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="74">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="104">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="134">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-57">down</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="209">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="228">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">end</beam>
      </note>
      <note default-x="247">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="285">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-57">down</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="361">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="398">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">begin</beam>
      </note>
      <note default-x="418">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
      </note>
      <note default-x="436">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <beam number="3">forward hook</beam>
      </note>
      <note default-x="459">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="494">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="514">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
        <beam number="3">forward hook</beam>
      </note>
      <note default-x="533">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="572">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-57">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="702">
      <print new-system="yes">
        <system-layout>
          <system-distance>114</system-distance>
        </system-layout>
      </print>
      <note default-x="52">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="0">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">forward hook</beam>
      </note>
      <note default-x="100">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="148">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="0">up</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
      <note default-x="196">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="244">
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note default-x="379">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="7.5">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">forward hook</beam>
        <beam number="3">forward hook</beam>
      </note>
      <note default-x="401">
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
      </note>
      <note default-x="431">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="479">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="7.5">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="527">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="7.5">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="576">
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="281">
      <note>
        <rest/>
        <duration>32</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""

timeSignatures11c = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Compound time signatures with 
          same denominator: (3+2)/8 and (5+3+1)/4.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>3+2</beats>
          <beat-type>8</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <attributes>
        <time>
          <beats>5+3+1</beats>
          <beat-type>4</beat-type>
        </time>
      </attributes>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie/>
        <voice>1</voice>
        <type>whole</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>half</type>
        <dot/>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

"""

timeSignatures11d = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Compound time signatures with 
          separate fractions displayed: 3/8+2/8+3/4 and 5/2+1/8.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>3</beats>
          <beat-type>8</beat-type>
          <beats>2</beats>
          <beat-type>8</beat-type>
          <beats>3</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <attributes>
        <time>
          <beats>5</beats>
          <beat-type>2</beat-type>
          <beats>1</beats>
          <beat-type>8</beat-type>
        </time>
      </attributes>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>breve</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""


clefs12a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Various clefs: G, C, F, percussion, 
          TAB and none; some are also possible with octavation and  on other 
          staff lines than their default (e.g. soprano/alto/tenor/bariton C 
          clefs); Each measure shows a different clef (measure 17 has the "none" 
          clef), only measure 18 has the same treble clef as measure 
          1.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <attributes>
        <clef>
          <sign>C</sign>
          <line>3</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <attributes>
        <clef>
          <sign>C</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <attributes>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <attributes>
        <clef>
          <sign>percussion</sign>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <attributes>
        <clef>
          <sign>G</sign>
          <line>2</line>
          <clef-octave-change>-1</clef-octave-change>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7">
      <attributes>
        <clef>
          <sign>F</sign>
          <line>4</line>
          <clef-octave-change>-1</clef-octave-change>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8">
      <attributes>
        <clef>
          <sign>F</sign>
          <line>3</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="9">
      <attributes>
        <clef>
          <sign>G</sign>
          <line>1</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="10">
      <attributes>
        <clef>
          <sign>C</sign>
          <line>5</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="11">
      <attributes>
        <clef>
          <sign>C</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="12">
      <attributes>
        <clef>
          <sign>C</sign>
          <line>1</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="13">
      <attributes>
        <clef>
          <sign>percussion</sign>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="14">
      <attributes>
        <clef>
          <sign>G</sign>
          <line>2</line>
          <clef-octave-change>1</clef-octave-change>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="15">
      <attributes>
        <clef>
          <sign>F</sign>
          <line>4</line>
          <clef-octave-change>1</clef-octave-change>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="16">
      <attributes>
        <clef>
          <sign>TAB</sign>
          <line>5</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="17">
      <attributes>
        <clef>
          <sign>none</sign>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="18">
      <attributes>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""

beams02 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <identification>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I1">
        <instrument-name>Acoustic Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="492">
      <print>
        <system-layout>
          <system-margins>
            <left-margin>70</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>172</top-system-distance>
        </system-layout>
      </print>
      <attributes>
        <divisions>8</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>2</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="83">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="153">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="185">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="249">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="287">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="359">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="391">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="459">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="421">
      <note default-x="13">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="81">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="113">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="175">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="213">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="282">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
      <note default-x="314">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="-62">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="379">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="-62">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""


tuplets23a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Some tuplets (3:2, 3:2, 3:2, 4:2, 
          4:1, 7:3, 6:2) with the default tuplet bracket displaying the number 
          of actual notes played. The second tuplet does not have a number 
          attribute set.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>84</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>14</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>56</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>42</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>42</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>42</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>5</octave>
        </pitch>
        <duration>42</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>5</octave>
        </pitch>
        <duration>21</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>1</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>6</octave>
        </pitch>
        <duration>21</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>1</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>6</octave>
        </pitch>
        <duration>21</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>1</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>5</octave>
        </pitch>
        <duration>21</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>1</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>7</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>6</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>6</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>6</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>6</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>6</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>28</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>6</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""


tuplets23b = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Different tuplet styles:
          default, none, x:y, x:y-note; Each with bracket, slur and none.
          Finally, non-standard 4:3 and 17:2 tuplets are given.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>408</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>5</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" number="1" show-number="none" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" number="1" show-number="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" number="1" show-number="both" show-type="actual" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" number="1" show-number="both" show-type="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" line-shape="curved" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" line-shape="curved" number="1" show-number="none" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" line-shape="curved" number="1" show-number="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" line-shape="curved" number="1" show-number="both" show-type="actual" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="yes" line-shape="curved" number="1" show-number="both" show-type="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="no" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="no" number="1" show-number="none" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="no" number="1" show-number="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="no" number="1" show-number="both" show-type="actual" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet bracket="no" number="1" show-number="both" show-type="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>136</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>153</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" placement="below" show-number="both" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>153</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>153</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>153</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>4</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>36</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>17</actual-notes>
          <normal-notes>3</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>204</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>204</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
"""

tupletsNested23d = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Tuplets can be nested. Here 
          there is a 5:2 tuplet inside a 3:2 tuple (all consisting of written
          eighth notes).</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>30</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>2</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>10</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
          <normal-type>quarter</normal-type>
        </time-modification>
        <beam number="1">begin</beam>
        <notations>
          <tuplet bracket="yes" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>10</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
          <normal-type>quarter</normal-type>
        </time-modification>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>15</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <beam number="1">begin</beam>
        <notations>
          <tuplet bracket="yes" number="2" type="start">
            <tuplet-actual>
              <tuplet-number>5</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-actual>
            <tuplet-normal>
              <tuplet-number>2</tuplet-number>
              <tuplet-type>eighth</tuplet-type>
            </tuplet-normal>
          </tuplet>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>15</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>15</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>15</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>15</actual-notes>
          <normal-notes>4</normal-notes>
        </time-modification>
        <beam number="1">end</beam>
        <notations>
          <tuplet number="2" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>10</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
          <normal-type>quarter</normal-type>
        </time-modification>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>10</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
          <normal-type>quarter</normal-type>
        </time-modification>
        <beam number="1">end</beam>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
</score-partwise>
"""


articulations01 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I1">
        <instrument-name>Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1" width="983">
      <print>
        <system-layout>
          <system-margins>
            <left-margin>70</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>211</top-system-distance>
        </system-layout>
      </print>
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="84">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-50.5">down</stem>
        <notations>
          <articulations>
            <staccatissimo default-x="3" default-y="2" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="306">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-50.5">down</stem>
        <notations>
          <articulations>
            <accent default-x="-1" default-y="3" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="529">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-50.5">down</stem>
        <notations>
          <articulations>
            <staccato default-x="3" default-y="-7" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="751">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-50.5">down</stem>
        <notations>
          <articulations>
            <tenuto default-x="1" default-y="-5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
</score-partwise>
"""

keySignatures13a = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <movement-title>Different Key signatures</movement-title>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Various key signature: from 11
            flats to 11 sharps (each one first one measure in major, then one
            measure in minor)</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>-11</fifths>
          <mode>major</mode>
        </key>
        <time symbol="common">
          <beats>2</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="2">
      <attributes>
        <key>
          <fifths>-11</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="3">
      <attributes>
        <key>
          <fifths>-10</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="4">
      <attributes>
        <key>
          <fifths>-10</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="5">
      <attributes>
        <key>
          <fifths>-9</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="6">
      <attributes>
        <key>
          <fifths>-9</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="7">
      <attributes>
        <key>
          <fifths>-8</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="8">
      <attributes>
        <key>
          <fifths>-8</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="9">
      <attributes>
        <key>
          <fifths>-7</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="10">
      <attributes>
        <key>
          <fifths>-7</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="11">
      <attributes>
        <key>
          <fifths>-6</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="12">
      <attributes>
        <key>
          <fifths>-6</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="13">
      <attributes>
        <key>
          <fifths>-5</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="14">
      <attributes>
        <key>
          <fifths>-5</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="15">
      <attributes>
        <key>
          <fifths>-4</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="16">
      <attributes>
        <key>
          <fifths>-4</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="17">
      <attributes>
        <key>
          <fifths>-3</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="18">
      <attributes>
        <key>
          <fifths>-3</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="19">
      <attributes>
        <key>
          <fifths>-2</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="20">
      <attributes>
        <key>
          <fifths>-2</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="21">
      <attributes>
        <key>
          <fifths>-1</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="22">
      <attributes>
        <key>
          <fifths>-1</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="23">
      <attributes>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="24">
      <attributes>
        <key>
          <fifths>0</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="25">
      <attributes>
        <key>
          <fifths>1</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="26">
      <attributes>
        <key>
          <fifths>1</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="27">
      <attributes>
        <key>
          <fifths>2</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="28">
      <attributes>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="29">
      <attributes>
        <key>
          <fifths>3</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="30">
      <attributes>
        <key>
          <fifths>3</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="31">
      <attributes>
        <key>
          <fifths>4</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="32">
      <attributes>
        <key>
          <fifths>4</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="33">
      <attributes>
        <key>
          <fifths>5</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="34">
      <attributes>
        <key>
          <fifths>5</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="35">
      <attributes>
        <key>
          <fifths>6</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="36">
      <attributes>
        <key>
          <fifths>6</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="37">
      <attributes>
        <key>
          <fifths>7</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="38">
      <attributes>
        <key>
          <fifths>7</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="39">
      <attributes>
        <key>
          <fifths>8</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="40">
      <attributes>
        <key>
          <fifths>8</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="41">
      <attributes>
        <key>
          <fifths>9</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="42">
      <attributes>
        <key>
          <fifths>9</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="43">
      <attributes>
        <key>
          <fifths>10</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="44">
      <attributes>
        <key>
          <fifths>10</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="45">
      <attributes>
        <key>
          <fifths>11</fifths>
          <mode>major</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <measure number="46">
      <attributes>
        <key>
          <fifths>11</fifths>
          <mode>minor</mode>
        </key>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
</score-partwise>
"""

ALL = [articulations01, pitches01a, directions31a, lyricsMelisma61d, notations32a, restsDurations02a, rhythmDurations03a, chordsThreeNotesDuration21c,
beams01, timeSignatures11c, timeSignatures11d, clefs12a, beams02, tuplets23a, tuplets23b, tupletsNested23d, keySignatures13a]


def get(contentRequest):
    '''Get test material by type of content

    >>> a = get('lyrics')
    '''
    if contentRequest in ['pitch']:
        return pitches01a
    if contentRequest in ['lyrics']:
        return lyricsMelisma61d
    if contentRequest in ['beams']:
        return beams02



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import converter
        for testMaterial in ALL:
            a = converter.parse(testMaterial)



if __name__ == "__main__":
    music21.mainTest(Test)

