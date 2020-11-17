# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testFiles.py
# Purpose:      MusicXML test files
#
# Authors:      Christopher Ariza
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest

_DOC_IGNORE_MODULE_OR_PACKAGE = True

chantQuemQueritis = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
    <movement-title>Quem queritis</movement-title>
    <identification>
        <rights>Copyright © 2003 Recordare LLC</rights>
        <encoding>
            <software>Finale 2003 for Windows</software>
            <software>Dolet for Finale 1.3</software>
            <encoding-date>2003-03-15</encoding-date>
        </encoding>
    </identification>
    <part-list>
        <score-part id="P1">
            <part-name>Voice</part-name>
        </score-part>
    </part-list>
    <part id="P1">
        <measure number="1">
            <attributes>
                <divisions>2</divisions>
                <clef>
                    <sign>G</sign>
                    <line>2</line>
                </clef>
            </attributes>
            <direction placement="above">
                <direction-type>
                    <words xml:lang="la" relative-y="5" relative-x="-5">Angelus dicit:</words>
                </direction-type>
            </direction>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>single</syllabic>
                    <text>Quem</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>begin</syllabic>
                    <text>que</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>middle</syllabic>
                    <text>ri</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <lyric number="1">
                    <syllabic>end</syllabic>
                    <text>tis</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <lyric number="1">
                    <syllabic>single</syllabic>
                    <text>in</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <lyric number="1">
                    <syllabic>begin</syllabic>
                    <text>se</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>middle</syllabic>
                    <text>pul</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>end</syllabic>
                    <text>chro,</text>
                    <extend/>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <direction placement="below">
                <direction-type>
                    <words relative-y="69">|</words>
                </direction-type>
                <offset>-1</offset>
            </direction>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>single</syllabic>
                    <text>o</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>begin</syllabic>
                    <text>Chri</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
                <lyric number="1">
                    <syllabic>middle</syllabic>
                    <text>sti</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <lyric number="1">
                    <syllabic>middle</syllabic>
                    <text>co</text>
                </lyric>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <lyric number="1">
                    <syllabic>end</syllabic>
                    <text>lae?</text>
                </lyric>
            </note>
            <barline location="right">
                <bar-style>light-light</bar-style>
            </barline>
        </measure>
    </part>
</score-partwise>

"""


schumannOp48No1 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <work>
    <work-number>Op. 48</work-number>
    <work-title>Dichterliebe</work-title>
  </work>
  <movement-number>1</movement-number>
  <movement-title>Im wunderschönen Monat Mai</movement-title>
  <identification>
    <creator type="composer">Robert Schumann</creator>
    <creator type="lyricist">Heinrich Heine</creator>
    <rights>Copyright © 2002 Recordare LLC</rights>
    <encoding>
      <software>Finale 2005 for Windows</software>
      <software>Dolet 4.0 Beta 4 for Finale</software>
      <encoding-date>2007-06-19</encoding-date>
      <supports attribute="new-system" element="print" type="yes" value="yes"/>
      <supports attribute="new-page" element="print" type="yes" value="yes"/>
    </encoding>
  </identification>
  <defaults>
    <scaling>
      <millimeters>6.35</millimeters>
      <tenths>40</tenths>
    </scaling>
    <page-layout>
      <page-height>1760</page-height>
      <page-width>1360</page-width>
      <page-margins type="both">
        <left-margin>80</left-margin>
        <right-margin>80</right-margin>
        <top-margin>80</top-margin>
        <bottom-margin>80</bottom-margin>
      </page-margins>
    </page-layout>
    <system-layout>
      <system-margins>
        <left-margin>0</left-margin>
        <right-margin>0</right-margin>
      </system-margins>
      <system-distance>130</system-distance>
      <top-system-distance>70</top-system-distance>
    </system-layout>
    <staff-layout>
      <staff-distance>80</staff-distance>
    </staff-layout>
    <appearance>
      <line-width type="stem">0.625</line-width>
      <line-width type="beam">3.75</line-width>
      <line-width type="staff">0.9375</line-width>
      <line-width type="light barline">1.4062</line-width>
      <line-width type="heavy barline">3.75</line-width>
      <line-width type="leger">1.4062</line-width>
      <line-width type="ending">0.625</line-width>
      <line-width type="wedge">0.9375</line-width>
      <line-width type="enclosure">0.9375</line-width>
      <line-width type="tuplet bracket">0.625</line-width>
      <note-size type="grace">60</note-size>
      <note-size type="cue">60</note-size>
    </appearance>
    <music-font font-family="Maestro" font-size="18"/>
    <word-font font-family="Times New Roman" font-size="9"/>
    <lyric-font font-family="Times New Roman" font-size="10" name="verse"/>
  </defaults>
  <credit page="1">
    <credit-words default-x="680" default-y="80" font-size="9" halign="center" valign="bottom">Copyright © 2002 Recordare LLC</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="680" default-y="1640" font-size="24" justify="center" valign="top" xml:lang="de">1. Im wunderschönen Monat Mai</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="680" default-y="1680" font-size="14" justify="center" valign="top">DICHTERLIEBE, Op. 48</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="80" default-y="1500" font-size="10" valign="bottom">Heinrich Heine</credit-words>
  </credit>
  <credit page="1">
    <credit-words default-x="1280" default-y="1500" font-size="10" halign="right" valign="bottom">Robert Schumann</credit-words>
  </credit>
  <part-list>
    <score-part id="P1">
      <part-name>Voice</part-name>
      <score-instrument id="P1-I1">
        <instrument-name>Voice</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>53</midi-program>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Piano</part-name>
      <score-instrument id="P2-I2">
        <instrument-name>Acoustic Grand Piano</instrument-name>
      </score-instrument>
      <midi-instrument id="P2-I2">
        <midi-channel>2</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure implicit="yes" number="0" width="198">
      <print page-number="2">
        <system-layout>
          <system-margins>
            <left-margin>120</left-margin>
            <right-margin>0</right-margin>
          </system-margins>
          <top-system-distance>230</top-system-distance>
        </system-layout>
      </print>
      <attributes>
        <divisions>8</divisions>
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
      <direction placement="above">
        <direction-type>
          <words default-y="15" font-size="10.5" font-weight="bold" relative-x="-52" xml:lang="de">Langsam, zart</words>
        </direction-type>
        <sound tempo="38"/>
      </direction>
      <note default-x="149">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="1" width="284">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="313">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="284">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="359">
      <print new-system="yes">
        <system-layout>
          <system-distance>175</system-distance>
        </system-layout>
      </print>
      <note default-x="113">
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note default-x="234">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="293">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <direction placement="above">
        <direction-type>
          <dynamics default-y="10" relative-x="-13">
            <p/>
          </dynamics>
        </direction-type>
        <sound dynamics="54"/>
      </direction>
      <note default-x="323">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>Im</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="324">
      <note default-x="20">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Wun</text>
        </lyric>
      </note>
      <note default-x="133">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-52">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>der</text>
        </lyric>
      </note>
      <note default-x="171">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="22">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>middle</syllabic>
          <text>schö</text>
        </lyric>
      </note>
      <note default-x="209">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>nen</text>
        </lyric>
      </note>
      <note default-x="246">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="17">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Mo</text>
        </lyric>
      </note>
      <note default-x="284">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>nat</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="243">
      <note default-x="19">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="11">up</stem>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>single</syllabic>
          <text>Mai,</text>
        </lyric>
      </note>
      <note default-x="128">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="180">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="209">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>als</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="274">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>al</text>
        </lyric>
      </note>
      <note default-x="107">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-52">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>le</text>
        </lyric>
      </note>
      <note default-x="140">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="below" type="start"/>
        </notations>
        <lyric default-y="-80" number="1" relative-x="10">
          <syllabic>begin</syllabic>
          <text>Knos</text>
        </lyric>
      </note>
      <note default-x="174">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="207">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="239">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>pen</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="330">
      <print new-system="yes">
        <system-layout>
          <system-distance>195</system-distance>
        </system-layout>
      </print>
      <note default-x="112">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="5">up</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>spran</text>
        </lyric>
      </note>
      <note default-x="166">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="5">up</stem>
        <beam number="1">end</beam>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>end</syllabic>
          <text>gen,</text>
        </lyric>
      </note>
      <note default-x="219">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="272">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="299">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="11">up</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>da</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="9" width="302">
      <note default-x="21">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-52">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>ist</text>
        </lyric>
      </note>
      <direction placement="above">
        <direction-type>
          <wedge default-y="13" spread="0" type="crescendo"/>
        </direction-type>
      </direction>
      <note default-x="113">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-52">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>in</text>
        </lyric>
      </note>
      <note default-x="158">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>mei</text>
        </lyric>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <offset>1</offset>
      </direction>
      <note default-x="256">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>nem</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="10" width="256">
      <note default-x="17">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-40">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Her</text>
        </lyric>
      </note>
      <note default-x="78">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-42">down</stem>
        <beam number="1">end</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>zen</text>
        </lyric>
      </note>
      <note default-x="135">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="194">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="224">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-45.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>die</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="11" width="311">
      <note default-x="22">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-42">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Lie</text>
        </lyric>
      </note>
      <direction placement="above">
        <direction-type>
          <wedge default-y="13" spread="0" type="crescendo"/>
        </direction-type>
      </direction>
      <note default-x="124">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-42">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>be</text>
        </lyric>
      </note>
      <note default-x="168">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-40">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>auf</text>
        </lyric>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <offset>1</offset>
      </direction>
      <note default-x="265">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-40">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>ge</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="12" width="356">
      <print new-page="yes" page-number="3"/>
      <note default-x="111">
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <accidental>natural</accidental>
        <stem default-y="-30">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>gan</text>
        </lyric>
      </note>
      <note default-x="172">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-32">down</stem>
        <beam number="1">end</beam>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>end</syllabic>
          <text>gen.</text>
        </lyric>
      </note>
      <note default-x="233">
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="13" width="285">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="14" width="270">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="15" width="289">
      <note default-x="23">
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note default-x="155">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="221">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <direction placement="above">
        <direction-type>
          <dynamics default-y="10" relative-x="-14">
            <p/>
          </dynamics>
        </direction-type>
        <sound dynamics="54"/>
      </direction>
      <note default-x="253">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>Im</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="16" width="432">
      <print new-system="yes">
        <system-layout>
          <system-distance>93</system-distance>
        </system-layout>
      </print>
      <note default-x="109">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Wun</text>
        </lyric>
      </note>
      <note default-x="229">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-52">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>der</text>
        </lyric>
      </note>
      <note default-x="270">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>schö</text>
        </lyric>
      </note>
      <note default-x="310">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>nen</text>
        </lyric>
      </note>
      <note default-x="350">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Mo</text>
        </lyric>
      </note>
      <note default-x="390">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>nat</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="17" width="257">
      <note default-x="19">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="11">up</stem>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>single</syllabic>
          <text>Mai,</text>
        </lyric>
      </note>
      <note default-x="135">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="193">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="223">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>als</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="18" width="267">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>al</text>
        </lyric>
      </note>
      <note default-x="105">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-52">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>le</text>
        </lyric>
      </note>
      <note default-x="137">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="below" type="start"/>
        </notations>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>begin</syllabic>
          <text>Vö</text>
        </lyric>
      </note>
      <note default-x="169">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="200">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="232">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>gel</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="19" width="244">
      <note default-x="15">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="5">up</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>san</text>
        </lyric>
      </note>
      <note default-x="72">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="5">up</stem>
        <beam number="1">end</beam>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>end</syllabic>
          <text>gen,</text>
        </lyric>
      </note>
      <note default-x="128">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="185">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="213">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="11">up</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>da</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="20" width="468">
      <print new-system="yes">
        <system-layout>
          <system-distance>93</system-distance>
        </system-layout>
      </print>
      <note default-x="111">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-52">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1" relative-x="3">
          <syllabic>single</syllabic>
          <text>hab’</text>
        </lyric>
      </note>
      <note default-x="244">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-52">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>ich</text>
        </lyric>
      </note>
      <direction placement="above">
        <direction-type>
          <wedge default-y="12" spread="0" type="crescendo"/>
        </direction-type>
      </direction>
      <note default-x="289">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-50">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>ihr</text>
        </lyric>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <offset>1</offset>
      </direction>
      <note default-x="422">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-50">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>ge</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="21" width="342">
      <note default-x="17">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-40">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>stan</text>
        </lyric>
      </note>
      <note default-x="98">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-42">down</stem>
        <beam number="1">end</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>den</text>
        </lyric>
      </note>
      <note default-x="179">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note default-x="259">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
      </note>
      <note default-x="300">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-45.5">down</stem>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>mein</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="22" width="390">
      <direction placement="above">
        <direction-type>
          <wedge default-y="13" spread="0" type="crescendo"/>
        </direction-type>
      </direction>
      <note default-x="22">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-42">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Seh</text>
        </lyric>
      </note>
      <note default-x="159">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-42">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>end</syllabic>
          <text>nen</text>
        </lyric>
      </note>
      <note default-x="205">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-40">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>single</syllabic>
          <text>und</text>
        </lyric>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <offset>1</offset>
      </direction>
      <note default-x="342">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-40">down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
        <lyric default-y="-80" number="1">
          <syllabic>begin</syllabic>
          <text>Ver</text>
        </lyric>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="23" width="365">
      <print new-system="yes">
        <system-layout>
          <system-distance>93</system-distance>
        </system-layout>
      </print>
      <note default-x="111">
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <accidental>natural</accidental>
        <stem default-y="-30">down</stem>
        <beam number="1">begin</beam>
        <lyric default-y="-80" number="1">
          <syllabic>middle</syllabic>
          <text>lan</text>
        </lyric>
      </note>
      <note default-x="174">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-32">down</stem>
        <beam number="1">end</beam>
        <lyric default-y="-80" number="1" relative-x="4">
          <syllabic>end</syllabic>
          <text>gen.</text>
        </lyric>
      </note>
      <note default-x="237">
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="24" width="303">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="25" width="286">
      <note>
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="26" width="246">
      <note default-x="109">
        <rest/>
        <duration>16</duration>
        <voice>1</voice>
        <type>whole</type>
        <notations>
          <fermata type="upright"/>
          <fermata type="upright"/>
          <fermata type="upright"/>
          <fermata type="upright"/>
        </notations>
      </note>
      <barline location="right">
        <bar-style>light-heavy</bar-style>
      </barline>
    </measure>
  </part>
  <!--=========================================================-->
  <part id="P2">
    <measure implicit="yes" number="0" width="198">
      <attributes>
        <divisions>8</divisions>
        <key>
          <fifths>3</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>2</beats>
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
      <direction placement="below">
        <direction-type>
          <dynamics default-y="-75" relative-x="-3">
            <p/>
          </dynamics>
        </direction-type>
        <staff>1</staff>
        <sound dynamics="54"/>
      </direction>
      <note default-x="149">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>2</duration>
      </backup>
      <direction placement="below">
        <direction-type>
          <pedal default-y="-70" line="no" relative-x="-10" type="start"/>
        </direction-type>
        <staff>2</staff>
      </direction>
      <note default-x="149">
        <rest/>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="1" width="284">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="151">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="184">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="216">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="250">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="151">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-63">down</stem>
        <staff>1</staff>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="28">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="46">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="34.5">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="80">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="41">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="113">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="48">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="151">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-20.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="151">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="313">
      <note default-x="23">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="165">
        <rest>
          <display-step>A</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="199">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="24.5">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="232">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>3</duration>
        <voice>1</voice>
        <type>16th</type>
        <dot/>
        <stem default-y="24.5">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="279">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>32nd</type>
        <stem default-y="24.5">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <beam number="3">backward hook</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="165">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-60.5">down</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="38">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="56">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="41">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="91">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="45">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="133">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="165">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="91">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="165">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>quarter</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="284">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="150">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="184">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="217">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="249">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="150">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-63">down</stem>
        <staff>1</staff>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="47">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="43.5">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="79">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="113">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="150">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-20.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="150">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="359">
      <print new-system="yes">
        <staff-layout number="1">
          <staff-distance>100</staff-distance>
        </staff-layout>
      </print>
      <note default-x="113">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="234">
        <rest>
          <display-step>A</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="264">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="293">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="323">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="234">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-60.5">down</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="113">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="38">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="142">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="41">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="172">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="45">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="205">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="113">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="234">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="172">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="234">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>quarter</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="5" width="324">
      <note default-x="20">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="171">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="22">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="209">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="246">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="17">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="284">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <forward>
        <duration>4</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="246">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-70">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="284">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-77">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="20">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="42">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="58">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="46">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="95">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="133">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <forward>
        <duration>4</duration>
        <voice>3</voice>
        <staff>2</staff>
      </forward>
      <note default-x="246">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="18">up</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="20">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="171">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="209">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-82">down</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="246">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-82">down</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="284">
        <pitch>
          <step>E</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-82">down</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="6" width="243">
      <note default-x="19">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="11">up</stem>
        <staff>1</staff>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="128">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="154">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="180">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="209">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="19">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <tie type="stop"/>
        <voice>2</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-75">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="100">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-80">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
      <note default-x="128">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-65.5">down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="19">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="29">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="46">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="31">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="72">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="33">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="100">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="19">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-63">down</stem>
        <staff>2</staff>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="72">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="128">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="180">
        <rest/>
        <duration>2</duration>
        <voice>5</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="209">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>5</voice>
        <type>16th</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="7" width="274">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="140">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="174">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="207">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="239">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <forward>
        <duration>4</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="207">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-70">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="239">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-77">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="42">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="42">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="46">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="75">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="107">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <forward>
        <duration>4</duration>
        <voice>3</voice>
        <staff>2</staff>
      </forward>
      <note default-x="207">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="-50.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="140">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="174">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="207">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="239">
        <pitch>
          <step>E</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="8" width="330">
      <print new-system="yes">
        <staff-layout number="1">
          <staff-distance>90</staff-distance>
        </staff-layout>
        <staff-layout number="2">
          <staff-distance>90</staff-distance>
        </staff-layout>
      </print>
      <note default-x="112">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="11">up</stem>
        <staff>1</staff>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="219">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="246">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="17">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="273">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="299">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="112">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <tie type="stop"/>
        <voice>2</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-75">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="193">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-80">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
      <note default-x="219">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-65.5">down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="112">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="25">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied orientation="under" type="stop"/>
        </notations>
      </note>
      <note default-x="139">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="29">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="166">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="33">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="193">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="112">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>4</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="-62">down</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="166">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="-50">down</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="219">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>6</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-32">down</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="299">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-32">down</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="9" width="302">
      <note default-x="21">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="82">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="113">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="16">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <direction placement="below">
        <direction-type>
          <wedge default-y="-56" spread="0" type="crescendo"/>
        </direction-type>
        <offset>1</offset>
        <staff>1</staff>
      </direction>
      <note default-x="158">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="16">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="225">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <offset>-1</offset>
        <staff>1</staff>
      </direction>
      <note default-x="256">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="21">
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-25" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="51">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="51">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="82">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="55">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="113">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="158">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="48.5">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-35" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="194">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="53">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="225">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="56">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="256">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="21">
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <accidental>natural</accidental>
        <stem default-y="-40.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="158">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-45.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="10" width="256">
      <note default-x="17">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="78">
        <rest>
          <display-step>D</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="135">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="163">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="194">
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="224">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur bezier-x="-61" bezier-y="26" default-x="7" default-y="10" number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="17">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="28" bezier-y="60" default-x="14" default-y="45" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="45">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="78">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="56">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="107">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="17">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>4</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="194">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>4</duration>
        <voice>4</voice>
        <type>eighth</type>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="11" width="311">
      <note default-x="22">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="91">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="124">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="21">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <direction placement="below">
        <direction-type>
          <wedge default-y="-56" spread="0" type="crescendo"/>
        </direction-type>
        <offset>1</offset>
        <staff>1</staff>
      </direction>
      <note default-x="168">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="21">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="233">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <offset>-1</offset>
        <staff>1</staff>
      </direction>
      <note default-x="265">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="26">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="22">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>flat</accidental>
        <stem default-y="57">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-15" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="54">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="61">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="91">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem default-y="65">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="124">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="168">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="53.5">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-15" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="200">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="57">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="233">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="61">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="265">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="22">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="168">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="12" width="356">
      <print new-page="yes">
        <staff-layout number="1">
          <staff-distance>90</staff-distance>
        </staff-layout>
      </print>
      <note default-x="111">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="26">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="172">
        <rest>
          <display-step>F</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <direction placement="above">
        <direction-type>
          <words default-y="55" font-style="italic">ritard.</words>
        </direction-type>
        <direction-type>
          <dashes default-y="57" number="1" type="start"/>
        </direction-type>
        <staff>1</staff>
      </direction>
      <note default-x="233">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="263">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-51.5">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="294">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="-45.5">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="324">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-40">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="111">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="42">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="42" bezier-y="68" default-x="13" default-y="57" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="141">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="46">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="172">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="202">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="111">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="233">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>4</duration>
        <voice>4</voice>
        <type>eighth</type>
        <staff>2</staff>
      </note>
      <note default-x="294">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="324">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-60.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="13" width="285">
      <note default-x="23">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <notations>
          <slur bezier-x="-72" bezier-y="34" default-x="8" default-y="16" number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="153">
        <rest>
          <display-step>A</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="186">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="218">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="250">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="153">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-60.5">down</stem>
        <staff>1</staff>
        <notations>
          <slur bezier-x="-38" bezier-y="14" default-x="7" default-y="-15" number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="37">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="18" bezier-y="39" default-x="14" default-y="42" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="55">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="41">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="88">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="45">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="121">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>4</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="217">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="250">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="14" width="270">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="146">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="176">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="206">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="237">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="146">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-63">down</stem>
        <staff>1</staff>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="46">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="44">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="76">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="108">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="146">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>12</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>4</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="206">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="237">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-60.5">down</stem>
        <staff>2</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="76">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="146">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="15" width="289">
      <note default-x="23">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <direction placement="below">
        <direction-type>
          <dashes default-y="57" number="1" type="stop"/>
        </direction-type>
      </direction>
      <note default-x="155">
        <rest>
          <display-step>A</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="188">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="221">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="253">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="155">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-60.5">down</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="37">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="56">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="41">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="89">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="45">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="122">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="155">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="89">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="155">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>quarter</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="16" width="432">
      <print new-system="yes">
        <staff-layout number="1">
          <staff-distance>100</staff-distance>
        </staff-layout>
      </print>
      <note default-x="109">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="270">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="310">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="350">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="390">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <forward>
        <duration>4</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="350">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-70">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="390">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-77">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="109">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="43">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-35" number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="149">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="46">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="189">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="229">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <forward>
        <duration>4</duration>
        <voice>3</voice>
        <staff>2</staff>
      </forward>
      <note default-x="350">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="18">up</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="109">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="270">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="310">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-82">down</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="350">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-82">down</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="390">
        <pitch>
          <step>E</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-82">down</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="17" width="257">
      <note default-x="19">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="11">up</stem>
        <staff>1</staff>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="135">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="164">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="193">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="223">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="19">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <tie type="stop"/>
        <voice>2</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-75">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="106">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-80">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
      <note default-x="135">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-65.5">down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="19">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="29">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="48">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="31">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="33">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="106">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="19">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-63">down</stem>
        <staff>2</staff>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="77">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="135">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="193">
        <rest/>
        <duration>2</duration>
        <voice>5</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="223">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>5</voice>
        <type>16th</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="18" width="267">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="137">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="169">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="200">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="232">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <forward>
        <duration>4</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="200">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-70">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="232">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-77">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="42">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="42">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="46">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="73">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="105">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <forward>
        <duration>4</duration>
        <voice>3</voice>
        <staff>2</staff>
      </forward>
      <note default-x="200">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="-50.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>4</voice>
        <staff>2</staff>
      </forward>
      <note default-x="137">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="169">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="200">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="232">
        <pitch>
          <step>E</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="2" type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="19" width="244">
      <note default-x="15">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="11">up</stem>
        <staff>1</staff>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="128">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="15">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="157">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
        <notations>
          <slur default-x="14" default-y="24" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="185">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="20">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="213">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur default-x="13" default-y="28" number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="15">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <tie type="stop"/>
        <voice>2</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-75">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="100">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>16th</type>
        <stem default-y="-80">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
      <note default-x="128">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-65.5">down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="15">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="29">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="43">
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="31">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="72">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="33">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="100">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="15">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>4</duration>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="-62">down</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
      </note>
      <note default-x="72">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>4</voice>
        <type>eighth</type>
        <stem default-y="-50">down</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="128">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>6</duration>
        <tie type="stop"/>
        <voice>4</voice>
        <type>eighth</type>
        <dot/>
        <stem default-y="-32">down</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="213">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-32">down</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="20" width="468">
      <print new-system="yes">
        <staff-layout number="2">
          <staff-distance>90</staff-distance>
        </staff-layout>
      </print>
      <note default-x="111">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="199">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <direction placement="below">
        <direction-type>
          <wedge default-y="-56" relative-x="15" spread="0" type="crescendo"/>
        </direction-type>
        <staff>1</staff>
      </direction>
      <note default-x="244">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="16">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note default-x="289">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="16">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <staff>1</staff>
      </direction>
      <note default-x="377">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="422">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="111">
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem default-y="48">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-16" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="156">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="51">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="199">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="55">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="244">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="289">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="49">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-25" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="333">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="53">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="378">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="56">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="422">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="111">
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <accidental>natural</accidental>
        <stem default-y="-40.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="289">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-45.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="21" width="342">
      <note default-x="17">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="98">
        <rest>
          <display-step>D</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="179">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="219">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="260">
        <pitch>
          <step>G</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="300">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur bezier-x="-66" bezier-y="28" default-x="7" default-y="11" number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="17">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="47" bezier-y="68" default-x="15" default-y="46" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="58">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="98">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="55">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="139">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="17">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>4</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="260">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>4</duration>
        <voice>4</voice>
        <type>eighth</type>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="22" width="390">
      <note default-x="22">
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="114">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <direction placement="below">
        <direction-type>
          <wedge default-y="-55" spread="0" type="crescendo"/>
        </direction-type>
        <offset>1</offset>
        <staff>1</staff>
      </direction>
      <note default-x="159">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="21">up</stem>
        <staff>1</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="205">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="21">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <direction>
        <direction-type>
          <wedge spread="15" type="stop"/>
        </direction-type>
        <staff>1</staff>
      </direction>
      <note default-x="296">
        <rest/>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="342">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="26">up</stem>
        <staff>1</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="22">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>flat</accidental>
        <stem default-y="58">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-6" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="68">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="61">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="114">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem default-y="65">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="159">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note default-x="205">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="54">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur default-x="7" default-y="-16" number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="251">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="58">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="296">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="61">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="342">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="22">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <accidental>flat</accidental>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="205">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-35.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="23" width="365">
      <print new-system="yes">
        <staff-layout number="2">
          <staff-distance>110</staff-distance>
        </staff-layout>
      </print>
      <note default-x="111">
        <pitch>
          <step>E</step>
          <octave>5</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="26">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="174">
        <rest>
          <display-step>F</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <staff>1</staff>
      </note>
      <note default-x="237">
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-57">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
      </note>
      <note default-x="269">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-51.5">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="301">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="-45.5">down</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="332">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="-40">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="111">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="48.5">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="39" bezier-y="71" default-x="13" default-y="53" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="143">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="52">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="174">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="56">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="206">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="111">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>4</voice>
        <type>quarter</type>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="237">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>4</duration>
        <voice>4</voice>
        <type>eighth</type>
        <staff>2</staff>
      </note>
      <note default-x="301">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="332">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-60.5">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="24" width="303">
      <note default-x="23">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>sharp</accidental>
        <stem default-y="23">up</stem>
        <staff>1</staff>
        <notations>
          <slur bezier-x="-114" bezier-y="27" default-x="8" default-y="13" number="1" type="stop"/>
        </notations>
      </note>
      <direction placement="below">
        <direction-type>
          <words default-y="-75" font-style="italic">ritard.</words>
        </direction-type>
        <direction-type>
          <dashes default-y="-73" number="1" type="start"/>
        </direction-type>
        <staff>1</staff>
      </direction>
      <note default-x="162">
        <rest>
          <display-step>A</display-step>
          <display-octave>5</display-octave>
        </rest>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <staff>1</staff>
      </note>
      <note default-x="196">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="22">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="73" bezier-y="39" default-x="14" default-y="37" number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="231">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="22">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="266">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="22">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="162">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-60.5">down</stem>
        <staff>1</staff>
        <notations>
          <slur bezier-x="-43" bezier-y="8" default-x="6" default-y="-15" number="2" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="43.5">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur bezier-x="18" bezier-y="44" default-x="14" default-y="48" number="2" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="58">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="93">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="51">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="128">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>8</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>4</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="231">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="266">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="25" width="286">
      <note default-x="10">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <tie type="start"/>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="18">up</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="152">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note default-x="185">
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="218">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="251">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>8</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="152">
        <pitch>
          <step>F</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="-63">down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="40">up</stem>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="2" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="47">
        <pitch>
          <step>A</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem default-y="43.5">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="80">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="113">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="50">up</stem>
        <staff>2</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="over" type="start"/>
          <slur number="2" type="stop"/>
        </notations>
      </note>
      <note default-x="152">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>eighth</type>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>12</duration>
      </backup>
      <note default-x="10">
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>4</voice>
        <type>quarter</type>
        <dot/>
        <stem default-y="-55.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="218">
        <rest>
          <display-step>D</display-step>
          <display-octave>3</display-octave>
        </rest>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <staff>2</staff>
      </note>
      <note default-x="251">
        <pitch>
          <step>B</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>4</voice>
        <type>16th</type>
        <stem default-y="-60.5">down</stem>
        <staff>2</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="80">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <note default-x="152">
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-30.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
    </measure>
    <!--=======================================================-->
    <measure number="26" width="246">
      <note default-x="23">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>5</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <accidental>sharp</accidental>
        <stem default-y="21">up</stem>
        <staff>1</staff>
        <notations>
          <slur bezier-x="-39" bezier-y="71" default-x="8" default-y="29" number="1" type="stop"/>
          <fermata default-y="32" type="upright"/>
        </notations>
      </note>
      <direction placement="below">
        <direction-type>
          <dashes number="1" type="stop"/>
        </direction-type>
        <offset>-8</offset>
        <staff>1</staff>
      </direction>
      <backup>
        <duration>16</duration>
      </backup>
      <direction placement="below">
        <direction-type>
          <pedal default-y="-105" line="no" type="start"/>
        </direction-type>
        <staff>2</staff>
        <sound damper-pedal="yes"/>
      </direction>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="43.5">up</stem>
        <notehead filled="no">normal</notehead>
        <staff>2</staff>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
        </notations>
      </note>
      <note default-x="55">
        <pitch>
          <step>G</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="47">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="87">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>16th</type>
        <stem default-y="51">up</stem>
        <staff>2</staff>
        <beam number="1">continue</beam>
        <beam number="2">continue</beam>
      </note>
      <note default-x="120">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="start"/>
        <voice>3</voice>
        <type>16th</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
        <notations>
          <tied orientation="under" type="start"/>
        </notations>
      </note>
      <direction placement="below">
        <direction-type>
          <pedal default-y="-105" line="no" type="stop"/>
        </direction-type>
        <offset sound="yes">4</offset>
        <staff>2</staff>
        <sound damper-pedal="no"/>
      </direction>
      <note default-x="154">
        <pitch>
          <step>E</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>3</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>1</staff>
        <notations>
          <tied type="stop"/>
          <slur number="1" type="stop"/>
          <fermata default-y="158" type="upright"/>
        </notations>
      </note>
      <note default-x="154">
        <chord/>
        <pitch>
          <step>B</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <note default-x="23">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>4</voice>
        <type>half</type>
        <stem default-y="-58">down</stem>
        <staff>2</staff>
        <notations>
          <fermata type="inverted"/>
        </notations>
      </note>
      <backup>
        <duration>16</duration>
      </backup>
      <forward>
        <duration>4</duration>
        <voice>5</voice>
        <staff>2</staff>
      </forward>
      <note default-x="87">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>5</voice>
        <type>eighth</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied orientation="over" type="start"/>
        </notations>
      </note>
      <note default-x="154">
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>5</voice>
        <type>quarter</type>
        <stem default-y="-25.5">down</stem>
        <staff>2</staff>
        <notations>
          <tied type="stop"/>
          <fermata default-y="25" type="upright"/>
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


mozartTrioK581Excerpt = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
    <work>
        <work-number>K. 581</work-number>
        <work-title>Quintet for Clarinet and Strings</work-title>
    </work>
    <movement-number>3</movement-number>
    <movement-title>Menuetto (Excerpt from Second Trio)</movement-title>
    <identification>
        <creator type="composer">Wolfgang Amadeus Mozart</creator>
        <rights>Copyright © 2003 Recordare LLC</rights>
        <encoding>
            <software>Finale 2003 for Windows</software>
            <software>Dolet for Finale 1.3</software>
            <encoding-date>2003-12-05</encoding-date>
        </encoding>
    </identification>
    <part-list>
        <part-group type="start" number="1">
            <group-symbol>bracket</group-symbol>
        </part-group>
        <score-part id="P1">
            <part-name>clarinet in A</part-name>
            <score-instrument id="P1-I1">
                <instrument-name>Clarinet</instrument-name>
            </score-instrument>
            <midi-instrument id="P1-I1">
                <midi-channel>1</midi-channel>
                <midi-program>72</midi-program>
            </midi-instrument>
        </score-part>
        <score-part id="P2">
            <part-name>violino I</part-name>
            <score-instrument id="P2-I3">
                <instrument-name>Violin</instrument-name>
            </score-instrument>
            <midi-instrument id="P2-I3">
                <midi-channel>3</midi-channel>
                <midi-program>41</midi-program>
            </midi-instrument>
        </score-part>
        <score-part id="P3">
            <part-name>violino II</part-name>
            <score-instrument id="P3-I4">
                <instrument-name>Violin II</instrument-name>
            </score-instrument>
            <midi-instrument id="P3-I4">
                <midi-channel>4</midi-channel>
                <midi-program>41</midi-program>
            </midi-instrument>
        </score-part>
        <score-part id="P4">
            <part-name>viola</part-name>
            <score-instrument id="P4-I5">
                <instrument-name>Viola</instrument-name>
            </score-instrument>
            <midi-instrument id="P4-I5">
                <midi-channel>6</midi-channel>
                <midi-program>42</midi-program>
            </midi-instrument>
        </score-part>
        <score-part id="P5">
            <part-name>violoncello</part-name>
            <score-instrument id="P5-I6">
                <instrument-name>Cello</instrument-name>
            </score-instrument>
            <midi-instrument id="P5-I6">
                <midi-channel>5</midi-channel>
                <midi-program>43</midi-program>
            </midi-instrument>
        </score-part>
        <part-group type="stop" number="1"/>
    </part-list>
    <part id="P1">
        <measure number="0" implicit="yes">
            <attributes>
                <divisions>6</divisions>
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
                <transpose>
                    <diatonic>-2</diatonic>
                    <chromatic>-3</chromatic>
                </transpose>
            </attributes>
            <direction placement="below">
                <direction-type>
                    <dynamics relative-y="6" relative-x="-14">
                        <p/>
                    </dynamics>
                </direction-type>
                <sound dynamics="54"/>
            </direction>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="1">
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>6</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="2">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>5</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="3">
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="4">
            <note>
                <pitch>
                    <step>D</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <accidental>sharp</accidental>
                <stem>down</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="5">
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <octave>6</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="6">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <accidental>natural</accidental>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>5</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="7">
            <note>
                <rest/>
                <duration>18</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="8">
            <print new-system="yes"/>
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>eighth</type>
                <time-modification>
                    <actual-notes>3</actual-notes>
                    <normal-notes>2</normal-notes>
                </time-modification>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <tuplet type="start" placement="below"/>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>eighth</type>
                <time-modification>
                    <actual-notes>3</actual-notes>
                    <normal-notes>2</normal-notes>
                </time-modification>
                <stem>up</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>3</octave>
                </pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>eighth</type>
                <time-modification>
                    <actual-notes>3</actual-notes>
                    <normal-notes>2</normal-notes>
                </time-modification>
                <stem>up</stem>
                <beam number="1">end</beam>
                <notations>
                    <tuplet type="stop"/>
                </notations>
            </note>
        </measure>
        <measure number="9">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
                <notations>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>4</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
                <notations>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
                <notations>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
                <notations>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">end</beam>
                <notations>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
        </measure>
        <measure number="10">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="11">
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>12</duration>
                <voice>1</voice>
                <type>half</type>
                <stem>down</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>3</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="12">
            <note>
                <pitch>
                    <step>C</step>
                    <octave>5</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
                <repeat direction="backward"/>
            </barline>
        </measure>
        <measure number="X1" implicit="yes">
            <barline location="left">
                <bar-style>heavy-light</bar-style>
                <repeat direction="forward"/>
            </barline>
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="13">
            <note>
                <rest/>
                <duration>18</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="14">
            <note>
                <rest/>
                <duration>18</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="15">
            <note>
                <rest/>
                <duration>18</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="16">
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>5</octave>
                </pitch>
                <duration>6</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
        </measure>
    </part>
    <part id="P2">
        <measure number="0" implicit="yes">
            <attributes>
                <divisions>8</divisions>
                <key>
                    <fifths>3</fifths>
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
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="1">
            <direction placement="below">
                <direction-type>
                    <dynamics>
                        <p/>
                    </dynamics>
                </direction-type>
                <offset>7</offset>
                <sound dynamics="54"/>
            </direction>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="2">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="3">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="4">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="5">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="6">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <accidental>sharp</accidental>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="7">
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <accidental>sharp</accidental>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="8">
            <print new-system="yes"/>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="9">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="10">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="11">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">end</beam>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="12">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
                <repeat direction="backward"/>
            </barline>
        </measure>
        <measure number="X1" implicit="yes">
            <barline location="left">
                <bar-style>heavy-light</bar-style>
                <repeat direction="forward"/>
            </barline>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="13">
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="14">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
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
                <stem>up</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
        <measure number="15">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">begin</beam>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">continue</beam>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>down</stem>
                <beam number="1">end</beam>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="16">
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
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
                <stem>up</stem>
                <beam number="1">end</beam>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">begin</beam>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>eighth</type>
                <stem>up</stem>
                <beam number="1">end</beam>
            </note>
        </measure>
    </part>
    <part id="P3">
        <measure number="0" implicit="yes">
            <attributes>
                <divisions>8</divisions>
                <key>
                    <fifths>3</fifths>
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
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="1">
            <direction placement="below">
                <direction-type>
                    <dynamics>
                        <p/>
                    </dynamics>
                </direction-type>
                <offset>7</offset>
                <sound dynamics="54"/>
            </direction>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="2">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="3">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="4">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="5">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="6">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <accidental>natural</accidental>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="7">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>half</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <accidental>natural</accidental>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="8">
            <print new-system="yes"/>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>half</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="9">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="10">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="11">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>half</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <accidental>sharp</accidental>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="12">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
                <repeat direction="backward"/>
            </barline>
        </measure>
        <measure number="X1" implicit="yes">
            <barline location="left">
                <bar-style>heavy-light</bar-style>
                <repeat direction="forward"/>
            </barline>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="13">
            <direction placement="below">
                <direction-type>
                    <dynamics>
                        <p/>
                    </dynamics>
                </direction-type>
                <sound dynamics="54"/>
            </direction>
            <direction placement="above">
                <direction-type>
                    <words>pizz.</words>
                </direction-type>
                <sound pizzicato="yes">
                    <midi-instrument id="P3-I4">
                        <midi-program>46</midi-program>
                    </midi-instrument>
                </sound>
            </direction>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="14">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="15">
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
        </measure>
        <measure number="16">
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
    </part>
    <part id="P4">
        <measure number="0" implicit="yes">
            <attributes>
                <divisions>8</divisions>
                <key>
                    <fifths>3</fifths>
                    <mode>major</mode>
                </key>
                <time>
                    <beats>3</beats>
                    <beat-type>4</beat-type>
                </time>
                <clef>
                    <sign>C</sign>
                    <line>3</line>
                </clef>
            </attributes>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="1">
            <direction placement="below">
                <direction-type>
                    <dynamics>
                        <p/>
                    </dynamics>
                </direction-type>
                <offset>7</offset>
                <sound dynamics="54"/>
            </direction>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
        </measure>
        <measure number="2">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="3">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="4">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
        </measure>
        <measure number="5">
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
        </measure>
        <measure number="6">
            <note>
                <pitch>
                    <step>B</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
                <notations>
                    <slur type="start" number="1"/>
                </notations>
            </note>
        </measure>
        <measure number="7">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>half</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
        </measure>
        <measure number="8">
            <print new-system="yes"/>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>half</type>
                <stem>down</stem>
                <notations>
                    <slur type="stop" number="1"/>
                </notations>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="9">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="10">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="11">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>24</duration>
                <tie type="start"/>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem>up</stem>
                <notations>
                    <tied type="start"/>
                </notations>
            </note>
        </measure>
        <measure number="12">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <tie type="stop"/>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <tied type="stop"/>
                </notations>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
                <repeat direction="backward"/>
            </barline>
        </measure>
        <measure number="X1" implicit="yes">
            <barline location="left">
                <bar-style>heavy-light</bar-style>
                <repeat direction="forward"/>
            </barline>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="13">
            <direction placement="above">
                <direction-type>
                    <words>pizz.</words>
                </direction-type>
                <sound pizzicato="yes">
                    <midi-instrument id="P4-I5">
                        <midi-program>46</midi-program>
                    </midi-instrument>
                </sound>
            </direction>
            <direction placement="below">
                <direction-type>
                    <dynamics>
                        <p/>
                    </dynamics>
                </direction-type>
                <sound dynamics="54"/>
            </direction>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="14">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="15">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
        </measure>
        <measure number="16">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
    </part>
    <part id="P5">
        <measure number="0" implicit="yes">
            <attributes>
                <divisions>8</divisions>
                <key>
                    <fifths>3</fifths>
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
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="1">
            <direction placement="below">
                <direction-type>
                    <dynamics relative-y="8">
                        <p/>
                    </dynamics>
                </direction-type>
                <sound dynamics="54"/>
            </direction>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="2">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="3">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="4">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="5">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="6">
            <note>
                <pitch>
                    <step>D</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="7">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="8">
            <print new-system="yes"/>
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="9">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="10">
            <note>
                <rest/>
                <duration>24</duration>
                <voice>1</voice>
            </note>
        </measure>
        <measure number="11">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>2</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="start" number="1"/>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>2</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>2</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
                <notations>
                    <slur type="stop" number="1"/>
                    <articulations>
                        <staccato placement="below"/>
                    </articulations>
                </notations>
            </note>
        </measure>
        <measure number="12">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>2</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
                <repeat direction="backward"/>
            </barline>
        </measure>
        <measure number="X1" implicit="yes">
            <barline location="left">
                <bar-style>heavy-light</bar-style>
                <repeat direction="forward"/>
            </barline>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="13">
            <direction placement="below">
                <direction-type>
                    <dynamics>
                        <p/>
                    </dynamics>
                </direction-type>
                <sound dynamics="54"/>
            </direction>
            <direction placement="above">
                <direction-type>
                    <words>pizz.</words>
                </direction-type>
                <sound pizzicato="yes">
                    <midi-instrument id="P5-I6">
                        <midi-program>46</midi-program>
                    </midi-instrument>
                </sound>
            </direction>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="14">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
        <measure number="15">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
        </measure>
        <measure number="16">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>2</octave>
                </pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem>up</stem>
            </note>
            <note>
                <rest/>
                <duration>8</duration>
                <voice>1</voice>
                <type>quarter</type>
            </note>
        </measure>
    </part>
</score-partwise>

"""


binchoisMagnificat = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE score-partwise
  PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
  'http://www.musicxml.org/dtds/partwise.dtd'>
<score-partwise>
  <movement-title>Excerpt from Magnificat secundi toni</movement-title>
  <identification>
    <creator type="composer">Gilles Binchois</creator>
    <rights>Copyright 2003 Recordare LLC</rights>
    <encoding>
      <encoding-date>2003-12-02</encoding-date>
      <software>Finale 2003 for Windows</software>
      <software>Dolet for Finale 1.3</software>
    </encoding>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Cantus</part-name>
      <score-instrument id="P1-I5">
        <instrument-name>Cantus</instrument-name>
      </score-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Cantus 2 and Tenor</part-name>
      <score-instrument id="P2-I4">
        <instrument-name>Cantus 2</instrument-name>
      </score-instrument>
      <score-instrument id="P2-I3">
        <instrument-name>Tenor</instrument-name>
      </score-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>8</divisions>
        <key>
          <fifths>-1</fifths>
        </key>
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
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>Ma</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>gni</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <notations>
          <slur number="1" type="start"/>
        </notations>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>fi</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>none</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>cat</text>
        </lyric>
      </note>
    </measure>
    <measure number="2">
      <attributes>
        <key>
          <fifths>-1</fifths>
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
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>A</text>
        </lyric>
      </note>
    </measure>
    <measure number="3">
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>ni</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>ma</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem>down</stem>
        <beam number="1">begin</beam>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>me</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem>down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
    </measure>
    <measure number="4">
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>a</text>
        </lyric>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>do</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <measure number="5">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="6">
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>6</duration>
        <voice>1</voice>
        <type>eighth</type>
        <dot/>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem>down</stem>
        <beam number="1">end</beam>
        <beam number="2">backward hook</beam>
      </note>
    </measure>
    <measure number="7">
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>16th</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
        <beam number="2">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem>down</stem>
        <beam number="1">continue</beam>
        <beam number="2">end</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>mi</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <accidental>sharp</accidental>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <accidental>natural</accidental>
        <stem>down</stem>
        <beam number="1">continue</beam>
        <beam number="2">begin</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <alter>1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem>down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
    </measure>
    <measure number="8">
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>24</duration>
        <voice>1</voice>
        <type>half</type>
        <dot/>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>num.</text>
        </lyric>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <measure number="9">
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>Et</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
    </measure>
    <measure number="10">
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>ex</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>ul</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>ta</text>
        </lyric>
      </note>
    </measure>
    <measure number="11">
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>vit</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <notations>
          <fermata type="upright"/>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <measure number="12">
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>spi</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>ri</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
    </measure>
    <measure number="13">
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>16th</type>
        <stem>down</stem>
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
        <stem>down</stem>
        <beam number="1">end</beam>
        <beam number="2">end</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>tus</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="14">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>me</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="15">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
    </measure>
    <measure number="16">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <stem>down</stem>
        <notations>
          <fermata type="upright"/>
        </notations>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>us</text>
        </lyric>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
    <measure number="17">
      <note>
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>in</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
    </measure>
  </part>
  <part id="P2">
    <measure number="1">
      <attributes>
        <divisions>8</divisions>
        <key>
          <fifths>-1</fifths>
        </key>
        <clef>
          <sign>F</sign>
          <line>4</line>
        </clef>
      </attributes>
      <note>
        <rest/>
        <duration>40</duration>
        <voice>1</voice>
      </note>
    </measure>
    <measure number="2">
      <attributes>
        <key>
          <fifths>-1</fifths>
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
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>A</text>
        </lyric>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="3">
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">begin</beam>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>ni</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>ma</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>me</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
    </measure>
    <measure number="4">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>a</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>do</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="5">
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <rest/>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="6">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="7">
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">continue</beam>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>mi</text>
        </lyric>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">continue</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="8">
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>24</duration>
        <voice>1</voice>
        <type>half</type>
        <dot/>
        <stem>down</stem>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>num.</text>
        </lyric>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>24</duration>
        <voice>2</voice>
        <type>half</type>
        <dot/>
        <stem>down</stem>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <measure number="9">
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="10">
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="11">
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <notations>
          <fermata type="upright"/>
        </notations>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>2</voice>
        <type>half</type>
        <stem>down</stem>
        <notations>
          <fermata type="inverted"/>
        </notations>
      </note>
    </measure>
    <measure number="12">
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>2</voice>
        <type>quarter</type>
        <dot/>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="13">
      <note>
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>2</voice>
        <type>half</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="14">
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">begin</beam>
      </note>
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="start"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>2</voice>
        <type>half</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="start"/>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
        <notations>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
    <measure number="15">
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <tie type="stop"/>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">begin</beam>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
        <beam number="1">end</beam>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <tie type="stop"/>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
        <notations>
          <tied type="stop"/>
        </notations>
      </note>
      <note>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>16</duration>
        <voice>2</voice>
        <type>half</type>
        <stem>down</stem>
      </note>
    </measure>
    <measure number="16">
      <note>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>1</voice>
        <type>half</type>
        <stem>up</stem>
        <notations>
          <fermata type="upright"/>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>16</duration>
        <voice>2</voice>
        <type>half</type>
        <stem>down</stem>
        <notations>
          <fermata type="inverted"/>
        </notations>
      </note>
      <note>
        <rest/>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
      </note>
    </measure>
    <measure number="17">
      <note>
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>8</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>12</duration>
        <voice>1</voice>
        <type>quarter</type>
        <dot/>
        <stem>up</stem>
      </note>
      <note>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem>up</stem>
      </note>
      <backup>
        <duration>24</duration>
      </backup>
      <note>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>8</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem>down</stem>
      </note>
      <note>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>16</duration>
        <voice>2</voice>
        <type>half</type>
        <stem>down</stem>
      </note>
    </measure>
  </part>
</score-partwise>

"""


moussorgskyPromenade = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN"
                                "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">

  <part-list>
    <score-part id="P1">
      <part-name print-object="no">MusicXML Part</part-name>
      <score-instrument id="P1-I2">
        <instrument-name>MusicXML Default</instrument-name>
      </score-instrument>
      <midi-instrument id="P1-I2">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
  </part-list>
  <!--=========================================================-->
  <part id="P1">
    <measure number="1" width="328">
      <attributes>
        <divisions>2</divisions>
        <key>
          <fifths>-2</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>5</beats>
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
      <direction placement="below">
        <direction-type>
          <dynamics default-y="-75">
            <f/>
          </dynamics>
        </direction-type>
        <staff>1</staff>
      </direction>
      <note default-x="120">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="6">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="158">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0">up</stem>
        <staff>1</staff>
        <notations>
          <articulations>
            <tenuto default-x="1" default-y="-46" placement="below"/>
          </articulations>
        </notations>
      </note>
      <note default-x="197">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55">down</stem>
        <staff>1</staff>
        <notations>
          <articulations>
            <tenuto default-x="0" default-y="-5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="235">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-50">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
          <articulations>
            <tenuto default-x="1" default-y="-5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="260">
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-44.5">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="283">
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
          <slur number="1" type="stop"/>
          <articulations>
            <tenuto default-x="0" default-y="5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <backup>
        <duration>10</duration>
      </backup>
      <note>
        <rest/>
        <duration>10</duration>
        <voice>3</voice>
        <staff>2</staff>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="2" width="291">
      <attributes>
        <time>
          <beats>6</beats>
          <beat-type>4</beat-type>
        </time>
      </attributes>
      <note default-x="44">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-50">down</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <slur number="1" placement="above" type="start"/>
          <articulations>
            <tenuto default-x="0" default-y="-5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="68">
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>eighth</type>
        <stem default-y="-44.5">down</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="92">
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
          <slur number="1" type="stop"/>
          <articulations>
            <tenuto default-x="0" default-y="5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="131">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-55">down</stem>
        <staff>1</staff>
        <notations>
          <articulations>
            <tenuto default-x="0" default-y="-5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="169">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-50">down</stem>
        <staff>1</staff>
        <notations>
          <articulations>
            <tenuto default-x="0" default-y="-5" placement="above"/>
          </articulations>
        </notations>
      </note>
      <note default-x="207">
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="6">up</stem>
        <staff>1</staff>
        <notations>
          <articulations>
            <tenuto default-x="1" default-y="-45" placement="below"/>
          </articulations>
        </notations>
      </note>
      <note default-x="247">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0">up</stem>
        <staff>1</staff>
        <notations>
          <articulations>
            <tenuto default-x="0" default-y="-46" placement="below"/>
          </articulations>
        </notations>
      </note>
      <backup>
        <duration>12</duration>
      </backup>
      <note>
        <rest/>
        <duration>12</duration>
        <voice>3</voice>
        <staff>2</staff>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="3" width="263">
      <attributes>
        <time>
          <beats>5</beats>
          <beat-type>4</beat-type>
        </time>
      </attributes>
      <note default-x="47">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="6">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="47">
        <chord/>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="47">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="87">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="87">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="87">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="126">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="16">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="126">
        <chord/>
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="126">
        <chord/>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="165">
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-79">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="165">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>1</staff>
      </note>
      <note default-x="217">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-64">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="217">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>10</duration>
      </backup>
      <forward>
        <duration>6</duration>
        <voice>2</voice>
        <staff>1</staff>
      </forward>
      <note default-x="165">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="30">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <slur number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="193">
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="217">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="19">up</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>10</duration>
      </backup>
      <note default-x="47">
        <pitch>
          <step>G</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="24">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="47">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="87">
        <pitch>
          <step>A</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="18.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="87">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="126">
        <pitch>
          <step>G</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="24">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="126">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="165">
        <pitch>
          <step>F</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="18.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="165">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="217">
        <pitch>
          <step>D</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="15.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="217">
        <chord/>
        <pitch>
          <step>D</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>
    <!--=======================================================-->
    <measure number="4" width="332">
      <attributes>
        <time>
          <beats>6</beats>
          <beat-type>4</beat-type>
        </time>
      </attributes>
      <note default-x="47">
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-79">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="47">
        <chord/>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>1</staff>
      </note>
      <note default-x="99">
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="-64">down</stem>
        <staff>1</staff>
      </note>
      <note default-x="99">
        <chord/>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>1</staff>
      </note>
      <note default-x="138">
        <pitch>
          <step>D</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="16">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="138">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="138">
        <chord/>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="177">
        <pitch>
          <step>E</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <accidental>natural</accidental>
        <stem default-y="14">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="177">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="177">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="217">
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="6">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="217">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="217">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="256">
        <pitch>
          <step>A</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem default-y="0">up</stem>
        <staff>1</staff>
      </note>
      <note default-x="256">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <note default-x="256">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>4</octave>
        </pitch>
        <duration>2</duration>
        <voice>1</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>1</staff>
      </note>
      <backup>
        <duration>12</duration>
      </backup>
      <note default-x="47">
        <pitch>
          <step>C</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="30">up</stem>
        <staff>1</staff>
        <beam number="1">begin</beam>
        <notations>
          <slur number="1" placement="below" type="start"/>
        </notations>
      </note>
      <note default-x="75">
        <pitch>
          <step>F</step>
          <octave>5</octave>
        </pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>eighth</type>
        <stem default-y="35">up</stem>
        <staff>1</staff>
        <beam number="1">end</beam>
      </note>
      <note default-x="99">
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
        <duration>2</duration>
        <voice>2</voice>
        <type>quarter</type>
        <stem default-y="19">up</stem>
        <staff>1</staff>
        <notations>
          <slur number="1" type="stop"/>
        </notations>
      </note>
      <backup>
        <duration>4</duration>
      </backup>
      <note default-x="47">
        <pitch>
          <step>F</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="18.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="47">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="99">
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="-58.5">down</stem>
        <staff>2</staff>
      </note>
      <note default-x="99">
        <chord/>
        <pitch>
          <step>B</step>
          <alter>-1</alter>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>down</stem>
        <staff>2</staff>
      </note>
      <note default-x="138">
        <pitch>
          <step>G</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="24">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="138">
        <chord/>
        <pitch>
          <step>G</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="177">
        <pitch>
          <step>C</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="10.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="177">
        <chord/>
        <pitch>
          <step>C</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="217">
        <pitch>
          <step>E</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <accidental>natural</accidental>
        <stem default-y="13.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="217">
        <chord/>
        <pitch>
          <step>E</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <accidental>natural</accidental>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <note default-x="256">
        <pitch>
          <step>F</step>
          <octave>2</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem default-y="18.5">up</stem>
        <staff>2</staff>
      </note>
      <note default-x="256">
        <chord/>
        <pitch>
          <step>F</step>
          <octave>3</octave>
        </pitch>
        <duration>2</duration>
        <voice>3</voice>
        <type>quarter</type>
        <stem>up</stem>
        <staff>2</staff>
      </note>
      <barline location="right">
        <bar-style>light-light</bar-style>
      </barline>
    </measure>

  </part>
  <!--=========================================================-->
</score-partwise>
"""


edgefield82b = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise>
    <work>
        <work-title >EDGEFIELD, 82b</work-title>
    </work>
    <part-list>
        <score-part id="P1">
            <part-name font-family="Arial" font-size="10" font-weight="normal" font-style="normal">treble</part-name>
            <part-abbreviation font-family="Arial" font-size="10" font-weight="normal" font-style="normal"></part-abbreviation>
            <score-instrument id="P1-I1">
                <instrument-name>Instr 20</instrument-name>
            </score-instrument>
        </score-part>
        <score-part id="P2">
            <part-name font-family="Arial" font-size="10" font-weight="normal" font-style="normal">tenor</part-name>
            <part-abbreviation font-family="Arial" font-size="10" font-weight="normal" font-style="normal"></part-abbreviation>
            <score-instrument id="P2-I1">
                <instrument-name>Instr 22</instrument-name>
            </score-instrument>
        </score-part>
        <score-part id="P3">
            <part-name font-family="Arial" font-size="10" font-weight="normal" font-style="normal">bass</part-name>
            <part-abbreviation font-family="Arial" font-size="10" font-weight="normal" font-style="normal"></part-abbreviation>
            <score-instrument id="P3-I1">
                <instrument-name>Instr 21</instrument-name>
            </score-instrument>
        </score-part>
    </part-list>
    <part id="P1">
        <!--==========================[1,1]=============================-->
        <measure number="1" width="188">
            <attributes>
                <divisions>6720</divisions>
                <key>
                    <cancel>-4</cancel>
                    <fifths>3</fifths>
                    <mode>major</mode>
                </key>
                <time>
                    <beats>6</beats>
                    <beat-type>4</beat-type>
                </time>
                <clef number="1">
                    <sign>G</sign>
                    <line>2</line>
                </clef>
                <staff-details number="1" print-object="yes">
                    <staff-lines>5</staff-lines>
                    <staff-size>70.00</staff-size>
                </staff-details>
            </attributes>
            <note>
                <rest>
                </rest>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,2]=============================-->
        <measure number="2" width="173">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,3]=============================-->
        <measure number="3" width="93">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,4]=============================-->
        <measure number="4" width="178">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-25.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,5]=============================-->
        <measure number="5" width="90">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-35.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,6]=============================-->
        <measure number="6" width="176">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,7]=============================-->
        <measure number="7" width="96">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,8]=============================-->
        <measure number="8" width="181">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,9]=============================-->
        <measure number="9" width="86">
            <print new-system="yes">
                <system-layout>
                    <system-margins>
                        <left-margin>46.667</left-margin>
                        <right-margin>46.667</right-margin>
                    </system-margins>
                    <system-distance>203.000</system-distance>
                </system-layout>
            </print>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,10]=============================-->
        <measure number="10" width="173">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
        </measure>
        <!--==========================[1,11]=============================-->
        <measure number="11" width="80">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>40320</duration>
                <voice>1</voice>
                <type>whole</type>
                <dot/>
                <stem>none</stem>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
            </barline>
        </measure>
    </part>
    <part id="P2">
        <!--==========================[2,1]=============================-->
        <measure number="1" width="188">
            <print>
                <staff-layout number="1">
                    <staff-distance>64.167</staff-distance>
                </staff-layout>
            </print>
            <attributes>
                <divisions>6720</divisions>
                <key>
                    <cancel>-4</cancel>
                    <fifths>3</fifths>
                    <mode>major</mode>
                </key>
                <time>
                    <beats>6</beats>
                    <beat-type>4</beat-type>
                </time>
                <clef number="1">
                    <sign>G</sign>
                    <line>2</line>
                </clef>
                <staff-details number="1" print-object="yes">
                    <staff-lines>5</staff-lines>
                    <staff-size>70.00</staff-size>
                </staff-details>
            </attributes>
            <note>
                <rest>
                </rest>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="0.00">up</stem>
            </note>
        </measure>
        <!--==========================[2,2]=============================-->
        <measure number="2" width="173">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="5.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-5.00">up</stem>
            </note>
        </measure>
        <!--==========================[2,3]=============================-->
        <measure number="3" width="93">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="0.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="0.00">up</stem>
            </note>
        </measure>
        <!--==========================[2,4]=============================-->
        <measure number="4" width="178">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
        </measure>
        <!--==========================[2,5]=============================-->
        <measure number="5" width="90">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[2,6]=============================-->
        <measure number="6" width="176">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
        </measure>
        <!--==========================[2,7]=============================-->
        <measure number="7" width="96">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-35.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-35.00">down</stem>
            </note>
        </measure>
        <!--==========================[2,8]=============================-->
        <measure number="8" width="181">
            <note>
                <pitch>
                    <step>E</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>D</step>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
        </measure>
        <!--==========================[2,9]=============================-->
        <measure number="9" width="86">
            <print new-system="yes">
                <staff-layout number="1">
                    <staff-distance>64.167</staff-distance>
                </staff-layout>
            </print>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[2,10]=============================-->
        <measure number="10" width="173">
            <note>
                <pitch>
                    <step>A</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>5</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>B</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-55.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="5.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>4</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-5.00">up</stem>
            </note>
        </measure>
        <!--==========================[2,11]=============================-->
        <measure number="11" width="80">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>4</octave>
                </pitch>
                <duration>40320</duration>
                <voice>1</voice>
                <type>whole</type>
                <dot/>
                <stem>none</stem>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
            </barline>
        </measure>
    </part>
    <part id="P3">
        <!--==========================[3,1]=============================-->
        <measure number="1" width="188">
            <print>
                <staff-layout number="1">
                    <staff-distance>64.167</staff-distance>
                </staff-layout>
            </print>
            <attributes>
                <divisions>6720</divisions>
                <key>
                    <cancel>-4</cancel>
                    <fifths>3</fifths>
                    <mode>major</mode>
                </key>
                <time>
                    <beats>6</beats>
                    <beat-type>4</beat-type>
                </time>
                <clef number="1">
                    <sign>F</sign>
                    <line>4</line>
                </clef>
                <staff-details number="1" print-object="yes">
                    <staff-lines>5</staff-lines>
                    <staff-size>70.00</staff-size>
                </staff-details>
            </attributes>
            <note>
                <rest>
                </rest>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,2]=============================-->
        <measure number="2" width="173">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,3]=============================-->
        <measure number="3" width="93">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,4]=============================-->
        <measure number="4" width="178">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>A</step>
                    <octave>2</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="0.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,5]=============================-->
        <measure number="5" width="90">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,6]=============================-->
        <measure number="6" width="176">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,7]=============================-->
        <measure number="7" width="96">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-60.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-60.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,8]=============================-->
        <measure number="8" width="181">
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,9]=============================-->
        <measure number="9" width="86">
            <print new-system="yes">
                <staff-layout number="1">
                    <staff-distance>64.167</staff-distance>
                </staff-layout>
            </print>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <chord/>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>20160</duration>
                <voice>1</voice>
                <type>half</type>
                <dot/>
                <stem default-y="-60.00">down</stem>
            </note>
        </measure>
        <!--==========================[3,10]=============================-->
        <measure number="10" width="173">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-45.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>G</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-40.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>E</step>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="-50.00">down</stem>
            </note>
            <note>
                <pitch>
                    <step>C</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>6720</duration>
                <voice>1</voice>
                <type>quarter</type>
                <stem default-y="10.00">up</stem>
            </note>
        </measure>
        <!--==========================[3,11]=============================-->
        <measure number="11" width="80">
            <note>
                <pitch>
                    <step>F</step>
                    <alter>1</alter>
                    <octave>3</octave>
                </pitch>
                <duration>40320</duration>
                <voice>1</voice>
                <type>whole</type>
                <dot/>
                <stem>none</stem>
            </note>
            <barline location="right">
                <bar-style>light-heavy</bar-style>
            </barline>
        </measure>
    </part>
</score-partwise>
"""

tabTest = """<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE score-partwise PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN' 'http://www.musicxml.org/dtds/2.0/partwise.dtd'>
<score-partwise version="2.0">
 <movement-title>test</movement-title>
 <identification>
  <encoding>
   <encoding-date>2014-02-26</encoding-date>
   <software>Guitar Pro 6</software>
  </encoding>
 </identification>
 <part-list>
  <score-part id="P0">
   <part-name>Electric Guitar</part-name>
   <part-abbreviation>E-Gt</part-abbreviation>
   <midi-instrument id="P0">
    <midi-channel>1</midi-channel>
    <midi-bank>1</midi-bank>
    <midi-program>28</midi-program>
    <volume>80</volume>
    <pan>0</pan>
   </midi-instrument>
  </score-part>
 </part-list>
 <part id="P0">
  <measure number="0">
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
     <sign>TAB</sign>
     <line>5</line>
    </clef>
    <staff-details>
     <staff-lines>6</staff-lines>
     <staff-tuning line="1">
      <tuning-step>E</tuning-step>
      <tuning-octave>2</tuning-octave>
     </staff-tuning>
     <staff-tuning line="2">
      <tuning-step>A</tuning-step>
      <tuning-octave>2</tuning-octave>
     </staff-tuning>
     <staff-tuning line="3">
      <tuning-step>D</tuning-step>
      <tuning-octave>3</tuning-octave>
     </staff-tuning>
     <staff-tuning line="4">
      <tuning-step>G</tuning-step>
      <tuning-octave>3</tuning-octave>
     </staff-tuning>
     <staff-tuning line="5">
      <tuning-step>B</tuning-step>
      <tuning-octave>3</tuning-octave>
     </staff-tuning>
     <staff-tuning line="6">
      <tuning-step>E</tuning-step>
      <tuning-octave>4</tuning-octave>
     </staff-tuning>
    </staff-details>
    <transpose>
     <diatonic>0</diatonic>
     <chromatic>0</chromatic>
     <octave-change>0</octave-change>
    </transpose>
   </attributes>
   <direction directive="yes" placement="above">
    <direction-type>
     <metronome default-y="40" parentheses="yes">
      <beat-unit>quarter</beat-unit>
      <per-minute>120</per-minute>
     </metronome>
    </direction-type>
    <sound tempo="120"/>
   </direction>
   <note>
    <pitch>
     <step>F</step>
     <octave>2</octave>
    </pitch>
    <duration>2</duration>
    <voice>1</voice>
    <type>half</type>
    <stem>up</stem>
    <notations>
     <technical>
      <string>6</string>
      <fret>1</fret>
     </technical>
    </notations>
   </note>
   <note>
    <pitch>
     <step>F</step>
     <alter>1</alter>
     <octave>2</octave>
    </pitch>
    <duration>2</duration>
    <voice>1</voice>
    <type>half</type>
    <accidental>sharp</accidental>
    <stem>up</stem>
    <notations>
     <technical>
      <string>6</string>
      <fret>2</fret>
     </technical>
    </notations>
   </note>
  </measure>
 </part>
</score-partwise>
"""


# ------------------------------------------------------------------------------
# define all strings for access

#
# dictionary storing does not work

# CONTENTS = {'mozartTrioK581Excerpt': mozartTrioK581Excerpt,
#             'schumannOp48No1': schumannOp48No1,
#         'chantQuemQueritis': chantQuemQueritis,
#     'beethovenOp98': beethovenOp98,
#             }
#
# ALL1 = CONTENTS.items()


ALL = [chantQuemQueritis, mozartTrioK581Excerpt, schumannOp48No1,
                binchoisMagnificat, edgefield82b, tabTest]


def get(contentRequest):
    '''Get test material by type of content

    >>> from music21.musicxml.testFiles import get

    >>> a = get('lyrics')
    '''
    if contentRequest in ['lyrics']:
        return chantQuemQueritis


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testBasic(self):
        from music21 import converter
        for testMaterial in ALL[:1]:
            unused = converter.parse(testMaterial)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

