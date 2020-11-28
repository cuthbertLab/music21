# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testPrimitive.py
# Purpose:      MusicXML test files
#
# Authors:      Christopher Ariza
#
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import unittest
_DOC_IGNORE_MODULE_OR_PACKAGE = True


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

# noinspection SpellCheckingInspection
directions31a = '''<?xml version="1.0" encoding="UTF-8"?>
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
        <lyric number="1"><syllabic>middle</syllabic><text>change</text></lyric>
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
          <metronome>
            <beat-unit>quarter</beat-unit>
            <per-minute>60</per-minute>
          </metronome>
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
'''


lyricsMelisma61d = '''<?xml version="1.0" encoding="UTF-8"?>
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

'''

# noinspection SpellCheckingInspection
notations32a = '''<?xml version="1.0" encoding="UTF-8"?>
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
        <lyric number="1"><syllabic>middle</syllabic><text>wavy</text></lyric>
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
'''


restsDurations02a = '''<?xml version="1.0" encoding="UTF-8"?>
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

'''


rhythmDurations03a = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''


chordsThreeNotesDuration21c = '''<?xml version="1.0"?>
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
'''


beams01 = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''

timeSignatures11c = '''<?xml version="1.0" encoding="UTF-8"?>
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

'''

timeSignatures11d = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''


clefs12a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Various clefs: G, C, F, percussion,
          TAB and none; some are also possible with octavation and  on other
          staff lines than their default (e.g. soprano/alto/tenor/baritone C
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
'''

beams02 = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''


tuplets23a = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''


tuplets23b = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''

tupletsNested23d = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''


articulations01 = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''

keySignatures13a = '''<?xml version="1.0" encoding="UTF-8"?>
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
'''


multipleAttributesPerMeasures = '''<?xml version="1.0" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 0.6a Partwise//EN" "//C:/Program Files/Finale 2003/Component Files/partwise.dtd">

<score-partwise>
    <part-list>
        <score-part id="P1">
            <part-name>cello</part-name>
        </score-part>
    </part-list>

    <part id="P1">
        <measure number="1">
            <attributes>
                <divisions>4</divisions>
            </attributes>
            <attributes>
                <clef>
                    <sign>F</sign>
                    <line>4</line>
                </clef>
            </attributes>
            <attributes>
                <key>
                    <fifths>1</fifths>
                </key>
            </attributes>
            <attributes>
                <time>
                    <beats>4</beats>
                    <beat-type>4</beat-type>
                </time>
            </attributes>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>2</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>2</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
        </measure>
        <measure number="2">
            <note>
                <pitch>
                    <step>G</step>
                    <octave>2</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>4</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>4</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>4</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>2</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>4</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>4</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <beam number="2">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>4</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
                <beam number="2">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>16th</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <beam number="2">end</beam>
            </note>
        </measure>
    </part>
</score-partwise>
'''

barlines46a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Different types of (non-repeat)
          barlines: default (no setting), regular, dotted, dashed, heavy,
          light-light, light-heavy, heavy-light, heavy-heavy, tick, short,
          none.</miscellaneous-field>
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
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>regular</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>dotted</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>dashed</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>heavy</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="7">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="8">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>heavy-light</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="9">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>heavy-heavy</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="10">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>tick</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="11">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>short</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="12">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>none</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="13">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

systemLayoutTwoPart = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
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
    <score-part id="P2">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P2-I1">
        <instrument-name>Acoustic Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P2-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="431">
      <print page-number="1">
        <system-layout>
          <system-margins>
            <left-margin>70</left-margin>
            <right-margin>123</right-margin>
          </system-margins>
          <top-system-distance>172</top-system-distance>
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
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="359">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="579">
      <print new-system="yes">
        <system-layout>
          <system-margins>
            <left-margin>0</left-margin>
            <right-margin>404</right-margin>
          </system-margins>
          <system-distance>119</system-distance>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="714">
      <print new-system="yes">
        <system-layout>
          <system-margins>
            <left-margin>0</left-margin>
            <right-margin>269</right-margin>
          </system-margins>
          <system-distance>112</system-distance>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="338">
      <print new-system="yes">
        <system-layout>
          <system-distance>129</system-distance>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="298">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="334">
      <print new-page="yes" page-number="2">
        <system-layout>
          <system-margins>
            <left-margin>0</left-margin>
            <right-margin>650</right-margin>
          </system-margins>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="334">
      <print new-system="yes">
        <system-layout>
          <system-margins>
            <left-margin>0</left-margin>
            <right-margin>650</right-margin>
          </system-margins>
          <system-distance>70</system-distance>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure number="1" width="431">
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
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="359">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="579">
      <print new-system="yes"/>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="714">
      <print new-system="yes"/>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="338">
      <print new-system="yes"/>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="298">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="334">
      <print new-page="yes"/>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="334">
      <print new-system="yes"/>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

multiMeasureTies = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">

  <part-list>
    <part-group number="1" type="start">
      <group-symbol default-x="-6">bracket</group-symbol>
      <group-barline>yes</group-barline>
    </part-group>
    <score-part id="P1">
      <part-name>1</part-name>
      <score-instrument id="P1-I1">
        <instrument-name> 1</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>-70</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>2</part-name>
      <score-instrument id="P2-I2">
        <instrument-name> 2</instrument-name>
      </score-instrument>
      <midi-instrument id="P2-I2">
        <midi-channel>2</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>-21</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P3">
      <part-name>3</part-name>
      <score-instrument id="P3-I3">
        <instrument-name> 3</instrument-name>
      </score-instrument>
      <midi-instrument id="P3-I3">
        <midi-channel>3</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>29</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P4">
      <part-name>4</part-name>
      <score-instrument id="P4-I4">
        <instrument-name> 4</instrument-name>
      </score-instrument>
      <midi-instrument id="P4-I4">
        <midi-channel>4</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>80</pan>
      </midi-instrument>
    </score-part>
    <part-group number="1" type="stop"/>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="210">
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
          <sign>C</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="82">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="146">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="140">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="516">
      <note default-x="54">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="285">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="467">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="236">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure number="1" width="210">
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
          <sign>C</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="82">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="146">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="140">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="516">
      <print new-system="yes"/>
      <note default-x="54">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="285">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="467">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="236">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P3">
    <measure number="1" width="210">
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
          <sign>C</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="82">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="146">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="140">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="516">
      <print new-system="yes"/>
      <note default-x="54">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="285">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="467">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="236">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P4">
    <measure number="1" width="210">
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
          <sign>C</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="82">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="146">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="141">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="140">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="516">
      <print new-system="yes"/>
      <note default-x="54">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="285">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="467">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="236">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

simpleRepeat45a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">A simple, repeated measure
          (repeated 5 times)</miscellaneous-field>
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
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <repeat direction="backward" />
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''


spannersSlurs33c = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">A note can be the end of one
          slur and the start of a new slur. Also, in MusicXML, nested slurs
          are possible like in the second measure where one slur goes over all
          four notes, and another slur goes from the second to the third
          note.</miscellaneous-field>
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
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" placement="above" type="start"/>
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
          <slur number="1" type="stop"/>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="stop"/>
          <slur number="1" placement="below" type="start"/>
        </notations>
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
          <slur number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" placement="above" type="start"/>
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
          <slur number="2" placement="above" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
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

'''
repeatMultipleTimes45c = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Repeats can also be nested.</miscellaneous-field>
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
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <barline location="left">
        <bar-style>heavy-light</bar-style>
        <repeat direction="forward"/>
      </barline>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <repeat direction="backward" times="5"/>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <repeat direction="backward" times="3"/>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="8">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

voiceDouble = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="913">
      <attributes>
        <divisions>2</divisions>
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
      <note default-x="84">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="24">up</stem>
      </note>
      <note default-x="267">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="14">up</stem>
      </note>
      <note default-x="450">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="19">up</stem>
      </note>
      <note default-x="679">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="5.5">up</stem>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="80">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>half</type>
        <stem default-y="-69">down</stem>
      </note>
      <note default-x="450">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-88">down</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="563">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-90">down</stem>
        <beam number="1">continue</beam>
      </note>
      <note default-x="677">
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-91.5">down</stem>
        <beam number="1">continue</beam>
      </note>
      <note default-x="790">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-93">down</stem>
        <beam number="1">end</beam>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
</score-partwise>
'''

pianoStaff43a = '''<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 0.6b Partwise//EN"
 "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
    <identification>
        <miscellaneous>
            <miscellaneous-field name="description">A simple piano staff</miscellaneous-field>
        </miscellaneous>
    </identification>
    <part-list>
        <score-part id="P1">
            <part-name>MusicXML Part</part-name>
        </score-part>
    </part-list>
    <part id="P1">
        <measure number="1">
            <attributes>
                <divisions>96</divisions>
                <key><fifths>0</fifths></key>
                <time><beats>4</beats><beat-type>4</beat-type></time>
                <staves>2</staves>
                <clef number="1"><sign>G</sign><line>2</line></clef>
                <clef number="2"><sign>F</sign><line>4</line></clef>
            </attributes>
            <note>
                <pitch><step>F</step><octave>4</octave></pitch>
                <duration>384</duration>
                <voice>1</voice>
                <type>whole</type>
                <staff>1</staff>
            </note>
            <backup><duration>384</duration></backup>
            <note>
                <pitch><step>B</step><octave>2</octave></pitch>
                <duration>384</duration>
                <voice>2</voice>
                <type>whole</type>
                <staff>2</staff>
            </note>
        </measure>
    </part>
</score-partwise>
'''

spanners33a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Several spanners defined in
           MusicXML: tuplet, slur (solid, dashed), tie,  wedge (cresc, dim),
           tr + wavy-line, single-note trill spanner, octave-shift (8va,15mb),
           bracket (solid down/down, dashed down/down, solid none/down,
           dashed none/up, solid none/none), dashes, glissando (wavy),
           bend-alter, slide (solid), grouping, two-note tremolo, hammer-on,
           pull-off, pedal (down, change, up).</miscellaneous-field>
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
        <divisions>3</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
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
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <notations>
          <tuplet number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
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
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur line-type="dashed" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4">
      <direction placement="above">
        <direction-type>
          <wedge spread="0" type="crescendo"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5">
      <direction placement="above">
        <direction-type>
          <wedge spread="15" type="diminuendo"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <wedge spread="0" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <trill-mark/>
            <wavy-line number="1" type="start"/>
          </ornaments>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <wavy-line number="1" type="stop"/>
          </ornaments>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments>
            <wavy-line number="1" type="start"/>
            <wavy-line number="1" type="stop"/>
          </ornaments>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>6</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8">
      <direction>
        <direction-type>
          <octave-shift size="8" type="down"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="8" type="stop"/>
        </direction-type>
      </direction>
    </measure>
    <!--=======================================================-->
    <measure number="9">
      <direction>
        <direction-type>
          <octave-shift size="15" type="up"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="15" type="stop"/>
        </direction-type>
      </direction>
    </measure>
    <!--=======================================================-->
    <measure number="10">
      <direction placement="above">
        <direction-type>
          <bracket line-end="down" line-type="solid" number="1" type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction placement="above">
        <direction-type>
          <bracket line-end="down" number="1" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="11">
      <direction placement="above">
        <direction-type>
          <bracket line-end="down" line-type="dashed" number="1" type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction placement="above">
        <direction-type>
          <bracket line-end="down" number="1" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="12">
      <direction placement="above">
        <direction-type>
          <bracket line-end="none" line-type="solid" number="1" type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction placement="above">
        <direction-type>
          <bracket line-end="down" number="1" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="13">
      <direction placement="above">
        <direction-type>
          <bracket line-end="none" line-type="dashed" number="1" type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction placement="above">
        <direction-type>
          <bracket line-end="up" number="1" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="14">
      <direction placement="above">
        <direction-type>
          <bracket line-end="none" line-type="solid" number="1" type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction placement="above">
        <direction-type>
          <bracket line-end="none" number="1" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="15">
      <direction placement="above">
        <direction-type>
          <dashes number="1" type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction placement="above">
        <direction-type>
          <dashes number="1" type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="16">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <glissando line-type="wavy" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <glissando line-type="wavy" number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="17">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <bend>
              <bend-alter>6</bend-alter>
            </bend>
          </technical>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <bend>
              <bend-alter>0</bend-alter>
            </bend>
          </technical>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="18">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slide line-type="solid" number="1" type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <slide line-type="solid" number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="19">
      <direction>
        <direction-type>
          <grouping type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <grouping type="stop"/>
        </direction-type>
      </direction>
    </measure>
    <!--=======================================================-->
    <measure number="20">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><tremolo type="start">2</tremolo></ornaments>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <ornaments><tremolo type="stop"/></ornaments>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="21">
      <note>
        <pitch>
          <step>B</step><octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <hammer-on type="start"/>
          </technical>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step><octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <hammer-on type="stop"/>
          </technical>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="22">
      <note>
        <pitch>
          <step>B</step><octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <pull-off type="start"/>
          </technical>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step><octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notations>
          <technical>
            <pull-off type="stop"/>
          </technical>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="23">
      <direction>
        <direction-type>
          <pedal type="start"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <pedal type="change"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <pedal type="stop"/>
        </direction-type>
      </direction>
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>3</duration>
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
'''

chordIndependentTies = '''<?xml version="1.0" encoding="UTF-8"?>
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
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="560">
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
        <divisions>2</divisions>
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
      <note default-x="83">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="14">up</stem>
      </note>
      <note default-x="83">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>3</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>up</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="83">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>up</stem>
      </note>
      <note default-x="243">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-60">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="243">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note default-x="318">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="14">up</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="318">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="318">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note default-x="438">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="14">up</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="438">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="438">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="424">
      <note default-x="14">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-64">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="14">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="14">
        <chord/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note default-x="127">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-64">down</stem>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="127">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="127">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="240">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-64">down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="240">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem>down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="240">
        <chord/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
        <stem>down</stem>
      </note>
      <note default-x="240">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>half</type>
        <stem>down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
  </part>
</score-partwise>
'''

textExpressions = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="492">
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
      <note default-x="83">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="196">
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note default-x="307">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="421">
      <direction>
        <direction-type>
          <words default-y="60" relative-x="0" line-height="2000" enclosure="rectangle" valign="top" font-size="12">muy agitato
with a long text
with a long text
            </words>
        </direction-type>
      <offset>1.5</offset>
      </direction>

      <note default-x="13">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-10">up</stem>
      </note>
      <direction placement="above">
        <direction-type>
          <words default-y="-80" font-style="italic"  font-size="24" font-weight="bold" relative-x="0" enclosure="rectangle" letter-spacing="0.5">agitato</words>
        </direction-type>
      </direction>
      <note default-x="124">
        <rest/>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note default-x="232">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <direction placement="above">
        <direction-type>
          <words default-y="-60" font-style="italic" font-size="8" relative-x="0" justify="right">after last element</words>
        </direction-type>
      </direction>

      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''


repeatExpressionsA = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
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
    <measure number="1" width="376">
      <barline location="left">
        <bar-style>heavy-light</bar-style>
        <repeat direction="forward"/>
      </barline>
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
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <repeat direction="backward"/>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="268">
      <direction placement="above">
        <direction-type>
          <segno default-x="-2" default-y="18"/>
        </direction-type>
        <sound divisions="1" segno="2"/>
      </direction>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="269">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <direction placement="above">
        <direction-type>
          <words default-x="255" default-y="16" font-size="12" font-weight="bold" justify="right">Fine</words>
        </direction-type>
      </direction>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="983">
      <print new-system="yes">
        <system-layout>
          <system-distance>114</system-distance>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <direction placement="above">
        <direction-type>
          <words default-x="976" default-y="19" font-family="Times" font-size="12" font-weight="bold" justify="right">D.S. al Fine</words>
        </direction-type>
      </direction>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''
repeatExpressionsB = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
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
    <measure number="1" width="376">
      <print>
        <system-layout>
          <system-margins>
            <left-margin>70</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>172</top-system-distance>
        </system-layout>
      </print>
      <barline location="left">
        <bar-style>heavy-light</bar-style>
        <repeat direction="forward"/>
      </barline>
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
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <repeat direction="backward"/>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="268">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="269">
      <direction placement="above">
        <direction-type>
          <coda default-x="1" default-y="16"/>
        </direction-type>
        <sound coda="3" divisions="1"/>
      </direction>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="353">
      <print new-system="yes">
        <system-layout>
          <system-distance>114</system-distance>
        </system-layout>
      </print>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <direction placement="above">
        <direction-type>
          <words default-x="353" default-y="23" font-size="12" font-weight="bold" justify="right">D.C. al Coda</words>
        </direction-type>
      </direction>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="315">
      <direction placement="above">
        <direction-type>
          <coda default-x="-2" default-y="28"/>
        </direction-type>
        <sound coda="5" divisions="1"/>
      </direction>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="315">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

repeatBracketsA = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <movement-title>The Smuggler's -- Reel</movement-title>
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
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="168">
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
        <divisions>4</divisions>
        <key>
          <fifths>3</fifths>
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
      <note default-x="132">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="141">
      <note default-x="13">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="33">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="54">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="74">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="94">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-60">down</stem>
        <beam number="1">end</beam>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <repeat direction="backward"/>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="205">
      <barline location="left">
        <bar-style>heavy-light</bar-style>
        <repeat direction="forward"/>
      </barline>
      <note default-x="32">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="53">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-48">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="74">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-46.5">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="96">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-45">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="118">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="139">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="161">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="183">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="153">
      <barline location="left">
        <ending default-y="40" end-length="30" font-size="8.5" number="1" type="start"/>
      </barline>
      <note default-x="13">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="32">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="12">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="52">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="13.5">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="71">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="90">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="121">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-45">down</stem>
        <beam number="1">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="179">
      <note default-x="13">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-55">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="33">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-55">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="54">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-55">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="74">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-55">down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="94">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="127">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <ending number="1" type="stop"/>
        <repeat direction="backward"/>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="136">
      <barline location="left">
        <ending default-y="40" end-length="30" font-size="8.5" number="2" type="start"/>
      </barline>
      <note default-x="13">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="33">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="53">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="74">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-60">down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note default-x="94">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-60">down</stem>
        <beam number="1">end</beam>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
        <ending number="2" type="discontinue"/>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

'''

graceNotes24a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
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
        <grace/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <grace slash="yes"/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <note>
        <grace slash="yes"/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <note>
        <grace slash="yes"/>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <grace/>
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>D</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>D</step>
          <alter>-1</alter>
          <octave>5</octave>
        </pitch>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <grace/>
        <pitch>
          <step>A</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
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
'''


mixedVoices1a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">

  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I2">
        <instrument-name>Acoustic Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I2">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="313">
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>2</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>3</beats>
          <beat-type>4</beat-type>
        </time>
        <staves>2</staves>
        <clef number="1">
          <sign>G</sign>
          <line>2</line>
        </clef>
        <clef number="2">
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="127">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="189">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-45">down</stem>
        <staff>1</staff>
        <notations>
          <ornaments>
            <turn default-x="-6" default-y="19" placement="above"/>
          </ornaments>
        </notations>
      </note>

      <!-- here, we are going to a new staff, but also going to a new voice -->
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="127">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="189">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-45">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
      </note>
      <note default-x="251">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-50">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
        <lyric default-y="-97" number="2">
          <syllabic>single</syllabic>
          <text>5</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="231">
      <note default-x="14">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-35.5">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="81">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="155">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-45">down</stem>
        <staff>1</staff>
        <notations>
          <ornaments>
            <mordent default-x="-6" default-y="5" placement="above"/>
          </ornaments>
        </notations>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>3</duration>
        <voice>2</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-35">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
        <lyric default-y="-97" number="2">
          <syllabic>single</syllabic>
          <text>4</text>
        </lyric>
      </note>
      <note default-x="114">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="0.5">up</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>7</text>
        </lyric>
      </note>
      <note default-x="155">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-55">down</stem>
        <staff>2</staff>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

mixedVoices1b = '''<?xml version="1.0" encoding="UTF-8"?>
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
    <score-part id="P2">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P2-I1">
        <instrument-name>Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P2-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="524">
      <print>
        <page-layout>
          <page-height>1545</page-height>
          <page-width>1194</page-width>
          <page-margins>
            <left-margin>70</left-margin>
            <right-margin>70</right-margin>
            <top-margin>88</top-margin>
            <bottom-margin>88</bottom-margin>
          </page-margins>
        </page-layout>
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
          <fifths>2</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>3</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="125">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="258">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-45">down</stem>
        <notations>
          <ornaments>
            <turn default-x="-5" default-y="20" placement="above"/>
          </ornaments>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="459">
      <note default-x="16">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-35">down</stem>
      </note>
      <note default-x="155">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="311">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-45">down</stem>
        <notations>
          <ornaments>
            <mordent default-x="-5" default-y="5" placement="above"/>
          </ornaments>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure number="1" width="524">
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>2</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>3</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="125">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0">up</stem>
      </note>
      <note default-x="258">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-45">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
      </note>
      <note default-x="391">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-50.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
        <lyric default-y="-97" number="2">
          <syllabic>single</syllabic>
          <text>5</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="459">
      <note default-x="16">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-35">down</stem>
        <lyric default-y="-80" justify="left" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
        <lyric default-y="-97" justify="left" number="2">
          <syllabic>single</syllabic>
          <text>4</text>
          <extend/>
        </lyric>
      </note>
      <note default-x="225">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="0">up</stem>
        <lyric default-y="-80" justify="left" number="1">
          <syllabic>single</syllabic>
          <text>7</text>
          <extend/>
        </lyric>
      </note>
      <note default-x="311">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55">down</stem>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

'''

mixedVoices2 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <credit page="1">
    <credit-words default-x="794" default-y="92" font-size="8" justify="center" valign="bottom">©</credit-words>
  </credit>
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I2">
        <instrument-name>Acoustic Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I2">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="407">
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>2</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>3</beats>
          <beat-type>4</beat-type>
        </time>
        <staves>2</staves>
        <clef number="1">
          <sign>G</sign>
          <line>2</line>
        </clef>
        <clef number="2">
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="127">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="24">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="220">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="19">up</stem>
        <staff>1</staff>
        <notations>
          <ornaments>
            <turn default-x="-6" default-y="43" placement="above"/>
          </ornaments>
        </notations>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="127">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-54">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="220">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-54">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="314">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-54">down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="127">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-64">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="220">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-45">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
      </note>
      <note default-x="314">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-50">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
        <lyric default-y="-97" number="2">
          <syllabic>single</syllabic>
          <text>5</text>
        </lyric>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="127">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="174">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="220">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="267">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="314">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="360">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>1</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="267">
      <note default-x="16">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="29">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="97">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="24">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="177">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="19">up</stem>
        <staff>1</staff>
        <notations>
          <ornaments>
            <mordent default-x="-7" default-y="28" placement="above"/>
          </ornaments>
        </notations>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="16">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-70">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="56">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-65">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="97">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-60">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="137">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-65">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="177">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-70">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="217">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="-75">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="16">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>3</duration>
        <voice>3</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-35">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>6</text>
        </lyric>
        <lyric default-y="-97" number="2">
          <syllabic>single</syllabic>
          <text>4</text>
        </lyric>
      </note>
      <note default-x="137">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>1</duration>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="-70.5">down</stem>
        <staff>2</staff>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>7</text>
        </lyric>
      </note>
      <note default-x="177">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-55">down</stem>
        <staff>2</staff>
      </note>
      <backup>
        <duration>6</duration>
      </backup>
      <note default-x="16">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="38.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="97">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="38.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="177">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="44">up</stem>
        <staff>2</staff>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>

'''

metronomeMarks31c = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <part-list>
    <score-part id="P1">
      <part-name></part-name>
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
      <direction>
        <direction-type>
          <metronome>
            <beat-unit>quarter</beat-unit>
            <beat-unit-dot/>
            <per-minute>100</per-minute>
          </metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <words>Adagio</words>
        </direction-type>
        <direction-type>
          <metronome>
            <beat-unit>long</beat-unit>
            <per-minute>100</per-minute>
          </metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <direction>
        <direction-type>
          <metronome>
            <beat-unit>quarter</beat-unit>
            <beat-unit-dot/>
            <beat-unit>half</beat-unit>
            <beat-unit-dot/>
          </metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <metronome>
            <beat-unit>long</beat-unit>
            <beat-unit>32nd</beat-unit>
            <beat-unit-dot/>
          </metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <direction>
        <direction-type>
          <metronome parentheses="yes">
            <beat-unit>quarter</beat-unit>
            <beat-unit-dot/>
            <beat-unit>half</beat-unit>
            <beat-unit-dot/>
          </metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <direction>
        <direction-type>
          <metronome parentheses="yes">
            <beat-unit>quarter</beat-unit>
            <beat-unit-dot/>
            <per-minute>77</per-minute>
          </metronome>
        </direction-type>
      </direction>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
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
'''

staffGroupsNested41d = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Two properly nested part groups:
          One group  (with a square bracket) goes from staff 2 to 4) and another
          group (with a curly bracket) goes from staff 3 to 4.</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>MusicXML Part</part-name>
    </score-part>
    <part-group number="1" type="start">
      <group-symbol>line</group-symbol>
      <group-barline>yes</group-barline>
    </part-group>
    <score-part id="P2">
      <part-name>MusicXML Part</part-name>
    </score-part>
    <part-group number="2" type="start">
      <group-symbol>brace</group-symbol>
      <group-barline>yes</group-barline>
    </part-group>
    <score-part id="P3">
      <part-name>MusicXML Part</part-name>
    </score-part>
    <score-part id="P4">
      <part-name>MusicXML Part</part-name>
    </score-part>
    <part-group number="2" type="stop"/>
    <part-group number="1" type="stop"/>
    <score-part id="P5">
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
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
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
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P3">
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
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P4">
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
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P5">
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
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3">
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

transposingInstruments72a = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="1.1">
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">Transposing instruments: Trumpet
          in Bb, Horn in Eb, Piano; All of them show the C major scale (the
          trumpet with 2 sharp, the horn with 3 sharp).</miscellaneous-field>
    </miscellaneous>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Trumpet in Bb</part-name>
      <part-abbreviation>Bb Tpt.</part-abbreviation>
    </score-part>
    <score-part id="P2">
      <part-name>Horn in Eb</part-name>
      <part-abbreviation>Hn.</part-abbreviation>
    </score-part>
    <score-part id="P3">
      <part-name>Piano</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>2</fifths>
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
        <transpose>
          <diatonic>-1</diatonic>
          <chromatic>-2</chromatic>
        </transpose>
      </attributes>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
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
          <alter>1</alter>
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
    </measure>
    <!--=======================================================-->
    <measure number="2">
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
          <alter>1</alter>
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
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>3</fifths>
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
        <transpose>
          <diatonic>-5</diatonic>
          <chromatic>-9</chromatic>
        </transpose>
      </attributes>
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
          <alter>1</alter>
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
    </measure>
    <!--=======================================================-->
    <measure number="2">
      <note>
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
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
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
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P3">
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
    </measure>
    <!--=======================================================-->
    <measure number="2">
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
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

transposing01 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <part-list>
    <part-group number="1" type="start">
      <group-symbol default-x="-6">bracket</group-symbol>
      <group-barline>yes</group-barline>
    </part-group>
    <score-part id="P1">
      <part-name>Oboe</part-name>
      <part-abbreviation>Ob.</part-abbreviation>
      <score-instrument id="P1-I2">
        <instrument-name>Oboe</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I2">
        <midi-channel>2</midi-channel>
        <midi-program>69</midi-program>
        <volume>80</volume>
        <pan>-34</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Clarinet in Bb</part-name>
      <part-name-display>
        <display-text>Clarinet in B</display-text>
        <accidental-text>flat</accidental-text>
      </part-name-display>
      <part-abbreviation>Bb Cl.</part-abbreviation>
      <part-abbreviation-display>
        <display-text>B</display-text>
        <accidental-text>flat</accidental-text>
        <display-text> Cl.</display-text>
      </part-abbreviation-display>
      <score-instrument id="P2-I3">
        <instrument-name>Clarinet in Bb</instrument-name>
      </score-instrument>
      <midi-instrument id="P2-I3">
        <midi-channel>3</midi-channel>
        <midi-program>72</midi-program>
        <volume>80</volume>
        <pan>4</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P3">
      <part-name>Horn in F</part-name>
      <part-abbreviation>Hn.</part-abbreviation>
      <score-instrument id="P3-I4">
        <instrument-name>Horn in F</instrument-name>
      </score-instrument>
      <midi-instrument id="P3-I4">
        <midi-channel>4</midi-channel>
        <midi-program>61</midi-program>
        <volume>80</volume>
        <pan>41</pan>
      </midi-instrument>
    </score-part>
    <part-group number="1" type="stop"/>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="295">
      <print>
        <system-layout>
          <system-margins>
            <left-margin>72</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>296</top-system-distance>
        </system-layout>
        <measure-numbering>system</measure-numbering>
      </print>
      <attributes>
        <divisions>2</divisions>
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
      <note default-x="122">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="165">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="208">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="251">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="236">
      <note default-x="62">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="106">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="149">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
      <note default-x="192">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="214">
      <attributes>
        <key>
          <fifths>1</fifths>
          <mode>major</mode>
        </key>
        <transpose>
          <diatonic>-4</diatonic>
          <chromatic>-7</chromatic>
        </transpose>
      </attributes>
      <note default-x="41">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="84">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="127">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="171">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="188">
      <note default-x="14">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="57">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="101">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="144">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="368">
      <print new-system="yes">
        <system-layout>
          <system-distance>258</system-distance>
        </system-layout>
      </print>
      <note default-x="100">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="167">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="234">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="301">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="329">
      <note default-x="61">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="128">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="195">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="262">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="308">
      <attributes>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <transpose>
          <diatonic>0</diatonic>
          <chromatic>0</chromatic>
          <octave-change>0</octave-change>
        </transpose>
      </attributes>
      <note default-x="39">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10">up</stem>
      </note>
      <note default-x="104">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10">up</stem>
      </note>
      <note default-x="169">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10">up</stem>
      </note>
      <note default-x="233">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="10">up</stem>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure number="1" width="295">
      <print>
        <measure-numbering>none</measure-numbering>
      </print>
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>2</fifths>
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
        <transpose>
          <diatonic>-1</diatonic>
          <chromatic>-2</chromatic>
        </transpose>
      </attributes>
      <sound tempo="120"/>
      <note default-x="122">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="165">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="208">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="251">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="236">
      <attributes>
        <key>
          <fifths>3</fifths>
          <mode>major</mode>
        </key>
        <transpose>
          <diatonic>2</diatonic>
          <chromatic>3</chromatic>
        </transpose>
      </attributes>
      <note default-x="62">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="106">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="149">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="192">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="214">
      <note default-x="41">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="84">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="127">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="171">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="188">
      <note default-x="14">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="57">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="101">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="144">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="368">
      <print new-system="yes"/>
      <note default-x="100">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="167">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="234">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
      <note default-x="301">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0.5">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="329">
      <attributes>
        <key>
          <fifths>2</fifths>
          <mode>major</mode>
        </key>
        <transpose>
          <diatonic>-1</diatonic>
          <chromatic>-2</chromatic>
        </transpose>
      </attributes>
      <note default-x="61">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="128">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="195">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="262">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="308">
      <note default-x="39">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="104">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="167">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P3">
    <measure number="1" width="295">
      <print>
        <measure-numbering>none</measure-numbering>
      </print>
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>1</fifths>
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
        <transpose>
          <diatonic>-4</diatonic>
          <chromatic>-7</chromatic>
        </transpose>
      </attributes>
      <sound tempo="120"/>
      <note default-x="122">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="165">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="208">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="251">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="236">
      <note default-x="62">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="106">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="149">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="192">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="214">
      <note default-x="41">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="84">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="127">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="171">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="188">
      <note default-x="14">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="57">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="101">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
      <note default-x="144">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="368">
      <print new-system="yes"/>
      <note default-x="100">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="167">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="234">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="301">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="329">
      <note default-x="61">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="128">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="195">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="262">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="308">
      <note default-x="39">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="104">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note default-x="167">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

# noinspection SpellCheckingInspection
colors01 = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<score-partwise>
  <movement-title>Music21 Fragment</movement-title>
  <identification>
    <creator type="composer">Music21</creator>
  </identification>
  <part-list>
    <score-part id="P8befe8ade6cb9feea3290cc9239209d1">
      <part-name></part-name>
    </score-part>
  </part-list>
  <part id="P8befe8ade6cb9feea3290cc9239209d1">
    <measure number="1">
      <attributes>
        <divisions>10080</divisions>
        <time>
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
          <octave>4</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <notehead>normal</notehead>
        <notations/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <notehead color="#ff1111">normal</notehead>
        <notations/>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <notehead color="#1111ff"></notehead>
        <notations/>
      </note>
      <note color="#11ff11">
        <rest/>
        <duration>10080</duration>
        <type>quarter</type>
        <notations/>
      </note>

      <note>
        <pitch>
          <step>C</step>
          <octave>2</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <notehead color="#ff1111">normal</notehead>
        <notations/>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <notehead color="#11ff11">normal</notehead>
        <notations/>
      </note>
      <note>
        <chord/>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <notehead color="#1111ff">normal</notehead>
        <notations/>
      </note>

      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
</score-partwise>
'''

triplets01 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <part-list>
    <part-group number="1" type="start">
      <group-symbol default-x="-6">bracket</group-symbol>
      <group-barline>yes</group-barline>
    </part-group>
    <score-part id="P1">
      <part-name>Baritone 1</part-name>
      <part-abbreviation>Bar. 1</part-abbreviation>
      <score-instrument id="P1-I1">
        <instrument-name>Baritone 1</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>58</midi-program>
        <volume>80</volume>
        <pan>-70</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Baritone 2</part-name>
      <part-abbreviation>Bar. 2</part-abbreviation>
      <score-instrument id="P2-I2">
        <instrument-name>Baritone 2</instrument-name>
      </score-instrument>
      <midi-instrument id="P2-I2">
        <midi-channel>2</midi-channel>
        <midi-program>58</midi-program>
        <volume>80</volume>
        <pan>80</pan>
      </midi-instrument>
    </score-part>
    <part-group number="1" type="stop"/>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="307">
      <print>
        <system-layout>
          <system-margins>
            <left-margin>70</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>152</top-system-distance>
        </system-layout>
      </print>
      <attributes>
        <divisions>6</divisions>
        <key>
          <fifths>-2</fifths>
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
      <note default-x="122">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tuplet number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="158">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-51">down</stem>
      </note>
      <note default-x="194">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-55.5">down</stem>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="229">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="11">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="224">
      <note default-x="14">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="11">up</stem>
        <notations>
          <tuplet number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="51">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-55.5">down</stem>
      </note>
      <note default-x="74">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-55">down</stem>
        <beam number="1">begin</beam>
      </note>
      <note default-x="96">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-57.5">down</stem>
        <beam number="1">continue</beam>
      </note>
      <note default-x="119">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="-60">down</stem>
        <beam number="1">end</beam>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="142">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="6">up</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="242">
      <note default-x="14">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="10">up</stem>
        <beam number="1">begin</beam>
        <notations>
          <tuplet number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="37">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="10">up</stem>
        <beam number="1">continue</beam>
      </note>
      <note default-x="60">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>eighth</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="10">up</stem>
        <beam number="1">end</beam>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="82">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="1">up</stem>
      </note>
      <note default-x="131">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="1">up</stem>
        <notations>
          <tuplet number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="167">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="6">up</stem>
      </note>
      <note default-x="203">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <time-modification>
          <actual-notes>3</actual-notes>
          <normal-notes>2</normal-notes>
        </time-modification>
        <stem default-y="1">up</stem>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="140">
      <note default-x="13">
        <pitch>
          <step>E</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>24</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure number="1" width="307">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>-2</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <sound tempo="120"/>
      <note default-x="122">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="224">
      <note default-x="14">
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>whole</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="242">
      <note default-x="14">
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-40.5">down</stem>
      </note>
      <note default-x="131">
        <pitch>
          <step>E</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-51">down</stem>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="140">
      <note default-x="13">
        <pitch>
          <step>G</step>
          <octave>3</octave>
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
'''

textBoxes01 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <credit page="1">
    <credit-words default-x="427" default-y="999" font-size="24" halign="center" valign="top">This is a text box!</credit-words>
  </credit>

    <!-- this will not create additional pages if page number is not needed -->
  <credit page="1">
    <credit-words default-x="200" default-y="300" font-size="12" halign="center" valign="top">pos 200/300 (lower left)</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="1000" default-y="300" font-size="12" halign="center" valign="top" enclosure="oval">pos 1000/300 (lower right)</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="200" default-y="1500" font-size="12" halign="center" valign="top">pos 200/1500 (upper left)</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="1000" default-y="1500" font-size="12" halign="center" valign="top">pos 1000/1500 (upper right)</credit-words>
  </credit>

  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="351">
      <attributes>
        <divisions>2</divisions>
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
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="281">
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
      </note>
    </measure>

  </part>
  <!--=========================================================-->
</score-partwise>
'''

octaveShifts33d = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
  <identification>
    <miscellaneous>
      <miscellaneous-field name="description">All types of octave shifts (15ma,
            15mb, 8va, 8vb)</miscellaneous-field>
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
        <divisions>8</divisions>
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
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">continue</beam>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="15" type="down"/>
        </direction-type>
        <offset>-4</offset>
      </direction>
      <note>
        <pitch>
          <step>A</step>
          <octave>6</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">continue</beam>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="15" type="stop"/>
        </direction-type>
        <offset>-4</offset>
      </direction>
      <direction>
        <direction-type>
          <octave-shift size="15" type="up"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="15" type="stop"/>
        </direction-type>
        <offset>-4</offset>
      </direction>
      <direction>
        <direction-type>
          <octave-shift size="8" type="down"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>A</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <beam number="1">begin</beam>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="8" type="stop"/>
        </direction-type>
        <offset>-3</offset>
      </direction>
      <direction>
        <direction-type>
          <octave-shift size="8" type="up"/>
        </direction-type>
      </direction>
      <note>
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <direction>
        <direction-type>
          <octave-shift size="8" type="stop"/>
        </direction-type>
        <offset>-2</offset>
      </direction>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

# Copyright string in the Creator name...
# noinspection SpellCheckingInspection
unicodeStrWithNonAscii = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<score-partwise>
  <movement-title>Music21 Fragment</movement-title>
  <identification>
    <creator type="composer">© Someone Else</creator>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Soprano</part-name>
      <score-instrument id="Ia5c7ffd3fddaf34e01aba22cc7675e84">
        <instrument-name>Instrument 1</instrument-name>
      </score-instrument>
      <midi-instrument id="Ia5c7ffd3fddaf34e01aba22cc7675e84">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Alto</part-name>
      <score-instrument id="I81a3ccc830fc582b8da480f89085ce86">
        <instrument-name>Instrument 2</instrument-name>
      </score-instrument>
      <midi-instrument id="I81a3ccc830fc582b8da480f89085ce86">
        <midi-channel>2</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P3">
      <part-name>Tenor</part-name>
      <score-instrument id="I3fe5d663307a3f4b6af18a6834007735">
        <instrument-name>Instrument 3</instrument-name>
      </score-instrument>
      <midi-instrument id="I3fe5d663307a3f4b6af18a6834007735">
        <midi-channel>3</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P4">
      <part-name>Bass</part-name>
      <score-instrument id="I787c2e658336b11931730747a2db2687">
        <instrument-name>Instrument 4</instrument-name>
      </score-instrument>
      <midi-instrument id="I787c2e658336b11931730747a2db2687">
        <midi-channel>4</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
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
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>up</stem>
        <beam>begin</beam>
        <notations/>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>up</stem>
        <beam>end</beam>
        <notations/>
      </note>
    </measure>
  </part>
  <part id="P2">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
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
      <note>
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <stem>up</stem>
        <notations/>
      </note>
    </measure>
  </part>
  <part id="P3">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>down</stem>
        <beam>begin</beam>
        <notations/>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>down</stem>
        <beam>end</beam>
        <notations/>
      </note>
    </measure>
  </part>
  <part id="P4">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <stem>down</stem>
        <notations/>
      </note>
    </measure>
  </part>
</score-partwise>
'''

# noinspection SpellCheckingInspection
unicodeStrNoNonAscii = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<score-partwise>
  <movement-title>Music21 Fragment</movement-title>
  <identification>
    <creator type="composer">Music21</creator>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Soprano</part-name>
      <score-instrument id="Ia5c7ffd3fddaf34e01aba22cc7675e84">
        <instrument-name>Instrument 1</instrument-name>
      </score-instrument>
      <midi-instrument id="Ia5c7ffd3fddaf34e01aba22cc7675e84">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Alto</part-name>
      <score-instrument id="I81a3ccc830fc582b8da480f89085ce86">
        <instrument-name>Instrument 2</instrument-name>
      </score-instrument>
      <midi-instrument id="I81a3ccc830fc582b8da480f89085ce86">
        <midi-channel>2</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P3">
      <part-name>Tenor</part-name>
      <score-instrument id="I3fe5d663307a3f4b6af18a6834007735">
        <instrument-name>Instrument 3</instrument-name>
      </score-instrument>
      <midi-instrument id="I3fe5d663307a3f4b6af18a6834007735">
        <midi-channel>3</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P4">
      <part-name>Bass</part-name>
      <score-instrument id="I787c2e658336b11931730747a2db2687">
        <instrument-name>Instrument 4</instrument-name>
      </score-instrument>
      <midi-instrument id="I787c2e658336b11931730747a2db2687">
        <midi-channel>4</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
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
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>up</stem>
        <beam>begin</beam>
        <notations/>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>up</stem>
        <beam>end</beam>
        <notations/>
      </note>
    </measure>
  </part>
  <part id="P2">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
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
      <note>
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <stem>up</stem>
        <notations/>
      </note>
    </measure>
  </part>
  <part id="P3">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>down</stem>
        <beam>begin</beam>
        <notations/>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>5040</duration>
        <type>eighth</type>
        <stem>down</stem>
        <beam>end</beam>
        <notations/>
      </note>
    </measure>
  </part>
  <part id="P4">
    <measure number="0">
      <attributes>
        <divisions>10080</divisions>
        <key>
          <fifths>2</fifths>
          <mode>minor</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>10080</duration>
        <type>quarter</type>
        <stem>down</stem>
        <notations/>
      </note>
    </measure>
  </part>
</score-partwise>
'''

tremoloTest = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.0">
  <identification>
    <encoding>
      <software>Finale 2014 for Mac</software>
      <software>Dolet Light for Finale 2014</software>
      <encoding-date>2015-08-05</encoding-date>
      <supports attribute="new-system" element="print" type="yes" value="yes"/>
      <supports attribute="new-page" element="print" type="yes" value="yes"/>
      <supports element="accidental" type="yes"/>
      <supports element="beam" type="yes"/>
      <supports element="stem" type="yes"/>
    </encoding>
  </identification>
  <defaults>
    <scaling>
      <millimeters>7.2319</millimeters>
      <tenths>40</tenths>
    </scaling>
    <page-layout>
      <page-height>1545</page-height>
      <page-width>1194</page-width>
      <page-margins type="both">
        <left-margin>70</left-margin>
        <right-margin>70</right-margin>
        <top-margin>88</top-margin>
        <bottom-margin>88</bottom-margin>
      </page-margins>
    </page-layout>
    <system-layout>
      <system-margins>
        <left-margin>0</left-margin>
        <right-margin>0</right-margin>
      </system-margins>
      <system-distance>121</system-distance>
      <top-system-distance>70</top-system-distance>
    </system-layout>
    <appearance>
      <line-width type="stem">0.7487</line-width>
    </appearance>
    <music-font font-family="Maestro,engraved" font-size="20.5"/>
    <word-font font-family="Times New Roman" font-size="10.25"/>
  </defaults>
  <credit page="1">
    <credit-words default-x="70" default-y="1453" font-size="12" valign="top">Score</credit-words>
  </credit>
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I1">
        <instrument-name>SmartMusic SoftSynth 1</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-bank>15489</midi-bank>
        <midi-program>1</midi-program>
        <volume>80</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="504">
      <print>
        <system-layout>
          <system-margins>
            <left-margin>70</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>211</top-system-distance>
        </system-layout>
        <measure-numbering>system</measure-numbering>
      </print>
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
      <sound tempo="120"/>
      <note default-x="84">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55">down</stem>
        <notations>
          <ornaments>
            <tremolo default-x="-5" default-y="-52" type="single">3</tremolo>
          </ornaments>
        </notations>
      </note>
      <note default-x="293">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="10.5">up</stem>
        <notations>
          <ornaments>
            <tremolo default-x="6" default-y="-13" type="single">2</tremolo>
          </ornaments>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="480">
      <note default-x="14">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <stem default-y="-55">down</stem>
        <notations>
          <ornaments>
            <tremolo default-x="-4" default-y="-45" type="single">1</tremolo>
          </ornaments>
        </notations>
      </note>
      <note default-x="222">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>32nd</type>
        <time-modification>
          <actual-notes>1</actual-notes>
          <normal-notes>8</normal-notes>
          <normal-type>16th</normal-type>
        </time-modification>
        <stem default-y="-62">down</stem>
        <notehead filled="no">normal</notehead>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <beam number="3">begin</beam>
        <notations>
          <tuplet bracket="no" number="1" show-number="none" type="start">
            <tuplet-actual>
              <tuplet-number>1</tuplet-number>
              <tuplet-type>16th</tuplet-type>
            </tuplet-actual>
            <tuplet-normal>
              <tuplet-number>1</tuplet-number>
              <tuplet-type>half</tuplet-type>
            </tuplet-normal>
          </tuplet>
        </notations>
      </note>
      <note default-x="351">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>32nd</type>
        <time-modification>
          <actual-notes>1</actual-notes>
          <normal-notes>8</normal-notes>
          <normal-type>16th</normal-type>
        </time-modification>
        <stem default-y="-67.5">down</stem>
        <notehead filled="no">normal</notehead>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">end</beam>
        <notations>
          <tuplet number="1" type="stop"/>
        </notations>
      </note>
    </measure>
  </part>
  <!--=========================================================-->
</score-partwise>
'''

hiddenRests = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>2</divisions>
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
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>half</type>
        <stem>up</stem>
      </note>
      <forward>
        <duration>2</duration>
        <voice>1</voice>
      </forward>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>2</voice>
      </forward>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <forward>
        <duration>2</duration>
        <voice>2</voice>
      </forward>
    </measure>
  </part>
</score-partwise>
'''

multiDigitEnding = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <barline location="left">
        <repeat direction="forward"/>
      </barline>
      <attributes>
        <divisions>2</divisions>
      </attributes>
      <note>
      <rest measure="yes"/>
        <duration>8</duration>
      </note>
      <barline location="right">
      </barline>
    </measure>
    <measure number="2">
      <barline location="left">
        <ending number="1,2" type="start"/>
      </barline>
      <note>
      <rest measure="yes"/>
        <duration>8</duration>
      </note>
      <barline location="right">
        <ending number="1,2" type="stop"/>
        <repeat direction="backward" times="3"/>
      </barline>
    </measure>
    <measure number="3">
      <barline location="left">
        <ending number="3" type="start"/>
      </barline>
      <note>
      <rest measure="yes"/>
        <duration>8</duration>
      </note>
      <barline location="right">
        <ending number="3" type="stop"/>
      </barline>
    </measure>
  </part>
</score-partwise>
'''

ALL = [
    articulations01, pitches01a, directions31a, lyricsMelisma61d, notations32a,  # 0
    restsDurations02a, rhythmDurations03a, chordsThreeNotesDuration21c,  # 5
    beams01, timeSignatures11c, timeSignatures11d, clefs12a, beams02,  # 8
    tuplets23a, tuplets23b, tupletsNested23d, keySignatures13a,  # 13
    barlines46a, simpleRepeat45a, repeatMultipleTimes45c,  # 17
    spannersSlurs33c, metronomeMarks31c,  # 20
    multipleAttributesPerMeasures, systemLayoutTwoPart, multiMeasureTies,  # 22
    chordIndependentTies, textExpressions, repeatExpressionsA, repeatExpressionsB,  # 25
    repeatBracketsA,  # 29
    voiceDouble, pianoStaff43a, spanners33a, staffGroupsNested41d,  # 30
    graceNotes24a, transposingInstruments72a, transposing01,  # 34
    mixedVoices1a, mixedVoices1b, mixedVoices2,  # 37
    colors01, triplets01, textBoxes01, octaveShifts33d,  # 40
    unicodeStrNoNonAscii, unicodeStrWithNonAscii,  # 44
    tremoloTest, hiddenRests, multiDigitEnding  # 46
]


def get(contentRequest):
    '''
    Get test material by type of content

    >>> from music21.musicxml.testPrimitive import get

    >>> a = get('lyrics')
    '''
    if contentRequest in ['pitch']:
        return pitches01a
    elif contentRequest in ['lyrics']:
        return lyricsMelisma61d
    elif contentRequest in ['beams']:
        return beams02
    elif contentRequest in ['tremolos']:
        return tremoloTest


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testBasic(self):
        # a basic test to make sure each parse
        from music21 import converter
        for i, testMaterial in enumerate(ALL):
            try:
                dummy = converter.parse(testMaterial)
            except Exception:
                print('Failure in test ', i)
                raise

    def testMidMeasureClef1(self):
        '''
        Tests if there are mid-measure clefs clefs: single staff
        '''
        from music21 import stream, note, clef, musicxml, converter, meter

        orig_stream = stream.Stream()
        orig_stream.append(meter.TimeSignature('4/4'))
        orig_stream.append(clef.TrebleClef())
        orig_stream.repeatAppend(note.Note('C4'), 2)
        orig_stream.append(clef.BassClef())
        orig_stream.repeatAppend(note.Note('C4'), 2)
        orig_clefs = orig_stream.flat.getElementsByClass('Clef')

        xml = musicxml.m21ToXml.GeneralObjectExporter().parse(orig_stream)
        self.assertEqual(xml.count(b'<clef>'), 2)  # clefs got out
        self.assertEqual(xml.count(b'<measure'), 1)  # in one measure

        new_stream = converter.parse(xml)
        new_clefs = new_stream.flat.getElementsByClass('Clef')

        self.assertEqual(len(new_clefs), len(orig_clefs))
        self.assertEqual([c.offset for c in new_clefs], [c.offset for c in orig_clefs])
        self.assertEqual([c.classes for c in new_clefs], [c.classes for c in orig_clefs])

    def testMidMeasureClefs2(self):
        '''
        Tests if there are mid-measure clefs clefs: multiple staves.
        '''
        from music21 import stream, note, clef, musicxml, converter, meter

        orig_stream = stream.Stream()
        orig_stream.append(stream.Part())
        orig_stream.append(stream.Part())
        orig_stream.append(meter.TimeSignature('3/4'))

        for item in [clef.TrebleClef(), note.Note('C4'), clef.BassClef(),
                     note.Note('C4'), note.Note('C4')]:
            orig_stream[0].append(item)

        for item in [clef.BassClef(), note.Note('C4'), note.Note('C4'),
                     clef.TrebleClef(), note.Note('C4')]:
            orig_stream[1].append(item)

        orig_clefs = [staff.flat.getElementsByClass('Clef').stream() for staff in
                      orig_stream.getElementsByClass('Part')]

        xml = musicxml.m21ToXml.GeneralObjectExporter().parse(orig_stream)

        new_stream = converter.parse(xml.decode('utf-8'))
        new_clefs = [staff.flat.getElementsByClass('Clef').stream() for staff in
                     new_stream.getElementsByClass('Part')]

        self.assertEqual([len(clefs) for clefs in new_clefs],
                         [len(clefs) for clefs in orig_clefs])
        self.assertEqual([c.offset for c in new_clefs],
                         [c.offset for c in orig_clefs])
        self.assertEqual([c.classes for c in new_clefs],
                         [c.classes for c in orig_clefs])

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)

