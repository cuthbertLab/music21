% "test_file.ly"
%
% Written as a test for the music21.mei module's ability to import MEI files.
% This file is a LilyPond score representing the intended musical content of
% "music21/converter/mei/test/test_file.mei" in an easier-to-verify format than
% Python objects.
%    Note that, if you want to visually check whether the file was successfully
% imported to music21, and you intend to do this by exporting the imported Score
% to MusicXML so you can visualize it, you introduce another series of possible
% errors. In particular, you'll find that nested tuplets, tuplets in grace notes,
% and nested slurs won't be exported properly to MusicXML, even though they are
% imported correctly from MEI.
%
% If you decide to perform "Test File: Movement title," please let me know,
% and if possible send a recording to me (Christopher Antila).

\version "2.18.2"

\header {
   subtitle = "Movement title"
   composer = "Christopher Antila"
   title = "Test File"
}


PartOne =  \relative e' {
   \clef "french"
   \key f \major
   \time 8/8

   % m.1
   e8 ^.[ e \acciaccatura { g16 f } e8^.] e <f as>2  |

   % m.2
   <<
      {
         \voiceOne
         \acciaccatura { as8 } g2
            \acciaccatura { bis\longa b <bes disis>\breve^^ beses1 }
            a4~ a
            \bar "|."  |
      } \\
      {
         \voiceTwo
         e4. f8 d4~ \times 2/3 { d8 cis d }
      }
   >>

   % m.3
   \key bes \major
   \time 3/4
   g16[ a bes c g a] bes8[ a16 a a a
      \bar "||"  |

   % m.4
   \times 2/3 { <c f>8] c \times 2/3 { d8 e d } c4 } bes
      \bar ":.|.:"  |

   % m.5
   \clef "treble"
   \times 1/7 {
      \times 4/5  { d8 f a g es }
      \clef "alto"
      c2 d c bes c d }
   \clef "treble"
   <g' beses,,>4  |

   % m.6
   R2. |

   % m.7
   \time 6/8
   \key g \major
   \acciaccatura { d,16 fis \times 2/3 { d16 fis d }} es2.  |

   % m.8
   R2. |

   % m.9
   d16 fis \times 2/3 { d16 fis d } es2  |
}


PartTwo =  \relative c {
   \clef "bass"
   \key f \major
   \time 8/8

   % m.1
   c4.( r8 d4) r  |

   % m.2
   e4\( r f( r \bar "|."  |

   % m.3
   \clef "tenor"
   \key bes \major
   \time 3/4
   g4)\) r f8 r \bar "||"  |

   % m.4
   R2.  |

   % m.5
   \clef "bass"
   \times 4/5 { es8 r32 r r16 r } r4 bes'  |

   % m.6
   R2.  |

   % m.7
   \key g \major
   R2.  |

   % mm.8--9
   R2.*2  |
}


% The score definition
\score {
   \new StaffGroup
   <<
      \new Staff
      <<
         \context Voice = "PartOne" { \PartOne }
      >>
      \new Staff
      <<
         \context Voice = "PartTwo" { \PartTwo }
      >>
   >>

   \layout {}
}
