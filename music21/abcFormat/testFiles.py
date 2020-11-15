# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testFiles.py
# Purpose:      ABC test files
#
# Authors:      Christopher Ariza
#
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest

# some lines must be this long, because of sources.
# pylint: disable=line-too-long


# abc standard
# http://abcnotation.com/abc2mtex/abc.txt

from music21 import environment
environLocal = environment.Environment('abcFormat.testFiles')

_DOC_IGNORE_MODULE_OR_PACKAGE = True


# http://abcnotation.com/tunePage?a=www.folkwiki.se/pub/cache/_Fyrareprisarn_0bf5b5/0001
# noinspection SpellCheckingInspection
fyrareprisarn = '''
%%abc-charset utf-8

X: 1
T: Fyrareprisarn
O: Jät, Småland
S: efter August Strömberg
D: Svensson, Gustafsson mfl - Bålgetingen
Z: Till abc av Jon Magnusson 100517
R: Hambo
M: 3/4
L: 1/8
K: F
c2 a>g f>e|d>c BA G>F|E>F GA B>c|d>c AB c>c|
c>a a>g f>e|d>c BA G>F|E>F Gd c>E|F2 f4::
{A}d>^c de f>g|e>f de =c>A|A>B AG FE|DE FG A>A|
d>^c de fg|e>f de =c>A|A>B AG FE|D2 d4::
c2 f2 c>c|B>d B4|G>c e2 c>e|f>>g a>f c2|
c2 f2 c>c|B>d g4|G2 e>g c>>>e|f2 f4::
f>f f4|e>e e3A|A>B AG FE|D>E FD E2|
f>f f4|e>e e3A|A>B AG FE|D2 d4:|
'''

# http://abcnotation.com/tunePage?a=www.fiddletech.com/music/abcproj/0253
# noinspection SpellCheckingInspection
mysteryReel = '''
X:254
T:Mystery Reel
R:reel
Z:transcribed by Dave Marshall
M:C|
K:G
|: egdB A3B | ~G3B A2Bd | e2dB A2BA |1 GEDE GABd :|2 GEDE GBdc |
|: B~G3 GEDG | BGAB GEDG | A2GB A2GA |1 Bdef gedc :|2 Bdef gedB |
|: ~G3E DEGB | dBGB A~E3 | GAGE DEGF | GBdB A2G2 :|
| gede g2ag | egde ge (3eee | gede g2ag | egde ~g3a |
gede g2ag | egde ge (3eee | ~g3e a2ba | ge (3eee b2ag |
'''

fullRiggedShip = '''X: 1
T:Full Rigged Ship
M:6/8
L:1/8
Q:100
C:Traditional
S:From The Boys of the Lough
R:Jig
O:Boys Of The Lough
A:Shetland
D:Boys of the Lough "Wish You Were Here"
K:G
|:e2a aea|aea b2a|e2f~g3|eag fed|
e2a aea|aea b2a|~g3 edB|A3A3:|!
|:efe edB|A2Bc3|BAG BAG|BcdE3|
efe edB|A2Bc2d|efe dBG|A3A3:|!
|:EFE EFE|EFE c3|EFE E2D|E2=F GEC|
EFE EFE|EFE c2d|efe dBG|A3A3:|
'''

# this is two parts, the V:2 designating second art
# http://abcnotation.com/tunePage?a=www.scottishfiddlers.com/Sydney/Music/ABC/SSF_Dance/0182
aleIsDear = '''%  <A name="D1X180"></A>
X: 180
T:Ale is Dear, The
M: 4/4
L: 1/8
R:Reel
Q:1/4=211
% Last note suggests Locrian mode tune
K:D % 2 sharps
% (c) SSF January 2006
V:1
f2 ef B2 fe| \
fa ef cA ec| \
f2 ef B2 fe| \
fa ec B2 Bc|
f2 ef B2 fe| \
fa ef cA ec| \
f2 ef B2 fe| \
fa ec B2 Bc|
B3/2B<Bc/2 d2 cB| \
A3/2A<AB<AB/2 c<A| \
B3/2B<Bc/2 d2 cB| \
f<a e3/2c/2 B2 B2|
B3/2B<Bc/2 d2 cB| \
A3/2A<AB<AB/2 c<A| \
d2 f3/2d/2 c2 e3/2c/2| \
d<f e3/2c<BB<Bc/2|
V:2
% Chords
B,,z [FDB,]z B,,z [FDB,]z| \
B,,z [FDB,]z A,,z [ECA,]z| \
B,,z [FDB,]z B,,z [FDB,]z| \
B,,z [ECA,]z B,,z [FDB,]z|
B,,z [FDB,]z B,,z [FDB,]z| \
B,,z [FDB,]z A,,z [ECA,]z| \
B,,z [FDB,]z B,,z [FDB,]z| \
B,,z [ECA,]z B,,z [FDB,]z|
B,,z [FDB,]z B,,z [FDB,]z| \
A,,z [ECA,]z A,,z [ECA,]z| \
B,,z [FDB,]z B,,z [FDB,]z| \
B,,z [ECA,]z B,,z [FDB,]z|
B,,z [FDB,]z B,,z [FDB,]z| \
A,,z [ECA,]z A,,z [ECA,]z| \
B,,z [FDB,]z A,,z [ECA,]z| \
B,,z [ECA,]z B,,z [FDB,]

'''

# http://abcnotation.com/tunePage?a=abc.sourceforge.net/NMD/nmd/reelsh-l.txt/0056
# noinspection SpellCheckingInspection
kitchGirl = '''X: 57
T:Kitchen Girl
% Nottingham Music Database
S:via PR
M:4/4
L:1/4
K:D
'A"[c2 a2 ]"G"[B2g2]|"A"e/2f/2e/2d/2 cc/2d/2|"A"e/2c/2e/2f/2 "G"g/2a/2b/2a/2|\
"E"^ge ee/2=g/2|
"A"a/2b/2a/2f/2 "G"g/2a/2g/2f/2|"A"e/2f/2e/2d/2 c/2d/2e/2f/2|\
"G"gd "E"e/2f/2e/2d/2|"A"cA A2::
"Am"=cc/2A/2 "G"B/2A/2G/2B/2|"Am"A/2B/2A/2G/2 E/2D/2E/2G/2|\
"Am"A/2G/2A/2B/2 "C"=c/2B/2c/2d/2|"Em"ee/2g/2 e/2d/2B/2A/2|
"Am"=cc/2A/2 "G"B/2A/2G/2B/2|"Am"A/2B/2A/2G/2 E/2D/2E/2G/2|\
"Am"=c/2B/2A/2c/2 "G"B/2A/2G/2B/2|"Am"A3/2B/2 A2:|
'''


# http://abcnotation.com/tunePage?a=abc.sourceforge.net/NMD/nmd/morris.txt/0030
# noinspection SpellCheckingInspection
williamAndNancy = '''X: 31
T:William and Nancy
% Nottingham Music Database
P:A(AABBB)2(AACCC)2
S:Bledington
M:6/8
K:G
P:A
D|"G"G2G GBd|"C"e2e "G"dBG|"D7"A2d "G"BAG|"C"E2F "G"G2:|
P:B
d|"G"e2d B2d|"C"gfe "D7"d2d|"G"e2d B2d|"A7""C"gfe "D7""D"d2c|
"G""Em"B2B Bcd|"C"e2e "G"dBG|"D7"A2d "G"BAG|"C"E2F "G"G2:|
P:C
"G"d3 "C"e3|"G"d3 "Em"B3|"G"d3 "C"g3/2f3/2|"C"e3 "G"d3|"D7"d3 "G"e3|"G"d3 B2d|\
"A7""C"gfe "D7""D"d2c|
"G""Em"B2B Bcd|"C"e2e "G"dBG|"D7"A2d "G"BAG|"C"E2F "G"G2:|
'''

# note key of e dorian
# http://abcnotation.com/tunePage?a=www.banjolin.co.uk/banjolin12/music/tunes/abcs/morrisons/0000
# noinspection SpellCheckingInspection
morrisonsJig = '''X:297
T:Morrison's
O:Ireland
F:http://www.banjolin.co.uk/tunes/abcs/morrisons.abc
M:6/8
L:1/8
R:jig
K:Edor
|:E3 B3|E2B AFD|EBE B2c|dcB AFD|
|EDE B3|E2B AFD|GBG FGA|1 dAG FED:|2 dAG FGA|
|Bee fee|aee fed|Bee fee|fag fed|
|Bee fee|aee fed|gfe d2A|BAG FGA|
|Bee fee|aee fed|Bee fee|faf def|
|g3 gfe|def gfg|edc d2A|BAG FED||
'''


# http://abcnotation.com/tunePage?a=www.alfwarnock.info/alfs/abc/alfwaltz/0048
# example of ties; note altered pitches are not specified
hectorTheHero = '''X: 48
T:Hector the Hero
M:3/4
L:1/8
C:Scott Skinner
K:A
A2B2|:"A"c3 BA2|"D"f4ec|"A"e4-ef|e4AB|\
"F#m"c4BA|"D"f4ec|"Bm"B4-Bc|"E"B4ce|
"F#m"c3 BA2|"D"f4ec|"A"e4A2|"D"a4f2|\
"A"e4Ac|"E"B4A2|"A"A6 -|[1 A2A2B2:|[2 A2c2e2||
:"D"f4df|a4gf|"A"e4-ef|e4ce|\
"F#m"f4ec|e4Ac|"Bm"B4-Bc|"E"B4ce|
"D"f4df|a4gf|"A"e4dc|"D"a4d2|\
"A"c4Ac|"E"B4A2|"A"A6 -|[1 A2c2e2:|[2 A2 z2|
'''

# http://abcnotation.com/tunePage?a=trillian.mit.edu/~jc/music/book/oneills/1001/F/09/0079
# removed problematic meta declarations:
# m: Tn2 = (3n/o/n/ m/n/
# m: Tn3 = n (3o/n/o/ (3n/m/n/

# noinspection SpellCheckingInspection
kingOfTheFairies = '''X: 979
T: King of the fairies
C: anon.
O: Ireland
B: Francis O'Neill: "The Dance Music of Ireland" (1907) no. 979
R: Long dance, set dance
Z: Transcribed by Frank Nordberg - http://www.musicaviva.com
F: http://www.musicaviva.com/abc/tunes/ireland/oneill-1001/oneill-1001-0979.abc
M: 2/4
L: 1/16
K: Edor
B,2|E^DE(F GF)GA|B2B2 TG3A|B2E2 E(FGE)|FGFE TD2B,2|E(^DEF) GFGA|B(AGB) d3
c|B2E2 (GF)E^D|"^1)"E4E2:|
d2|e2e2 Bde(f|ga)gf e2f2|e2B2 (BAB)c|d(edc) BcdB|e2B2 Bdef|g(agf) efed|Bd
e(g fe)df|"^2)"e6(ef)|
g3e f2d2|e(dBc) Td3e|dBA(F GA)B^c|dBA(F GF)ED|B,2E2 (EFG)A|B2e2 edef|e2B2
 BAG(F|TE4)E2|]
W:
W:
W: 1) org. dotted 4th note.
W: 2) org. not dotted.
W:
W:
W: From Musica Viva - http://www.musicaviva.com
W: the Internet center for free sheet music downloads.
'''

# http://abcnotation.com/tunePage?a=serpentpublications.org/music/bicinia/sicutrosa/allparts/0003
# noinspection SpellCheckingInspection
sicutRosa = '''X:1
T:9v. Sicut rosa
C:Orlando Lassusio
O: Bicinia, sive Cantionis
H: transcribed from the Musica Alamire facsimile of the original
H: printed in Antwerp by Petrum Phalesium, 1609
%%gchordfont Helvetica 12 box
%%MIDI nobarlines
M:C|
L:1/4
K:G mixolydian treble8
T:Tenor
%%MIDI transpose -12
%1
G3 A B c d B e4 d2 B4 e3 d c2 B2 d4 d2 G  A B c d3 c B4 G4 d3 c
w:Si- - - - - - - cut ro * -  - sa si- cut ro- - - - - - - sa in- -
%2
B A G4 F2 E4 "A"D2 A4 B2 c4 B2 d3 c B A G F E D C2 C2 G4 z2 G4 E2 G4 A2 c3 B A G
w:- - - ter spi- nas il - lis ad- dit spe- - - - - - - -  ci- em, sic ve- nu- stat su- - - -
%3
_B2 A2 A4 D2 F2 E2 F2 G4 G3 A B2 A2 F2 c2 B2 c2 d2 c3 B d4 c B c A c4 B2 "B"c4 z2 G2 A2 B4 F2 c4
w:- am vir- go Ma- ri- am pro- ge- - - ni- am Ma- ri- am pro- ge- - - - - - - - ni- am ger- mi- na- vit e-
%4
d2 e3 d/ c/ B c d A d3 c/ B/ c2 "C"d4-d4 z2 d2 e2 d3 B ^c2 d2 e2 c2 G A B c d2 G4 z2 G2
w:nim flo- - - - - - - - - - - rem, * qui vi- ta- - -  lem dat o- do- - - - - rem qui
%5
A2 G3 E ^F2 G2 A2 c4 B3 A/ G/ A4 HG4 |]
w:vi- ta- - - lem dat o- do- - - - rem.
'''

# http://abcnotation.com/tunePage?a=www.campin.me.uk/Embro/Webrelease/Embro/17riot/abc/AleWife/0000
# noinspection SpellCheckingInspection
theAleWifesDaughter = '''X:1
T:The Ale Wife's Daughter
Z:Jack Campin: "Embro, Embro", transcription (c) 2001
F:17riot/abc/AleWife.abc
S:John Hamilton: A Collection of Twenty-Four Scots Songs (Chiefly Pastoral.), 1796
B:NLS Glen.311
M:C
L:1/8
Q:1/4=80
N:Slow and Supplicative
K:G Mixolydian
(E/F/)|G<G GE  GA  c>B|A>A A>G Ac d3/ (c//d//)| e>g          d>e c>d e>d|cA A>G G3||
(c/d/)|e<e e>c e>f g>e|d>d d>c de f3/ (e//f//)|(g/f/) (e/f/) ed  c>d e>d|cA A>G G3|]
'''

# http://abcnotation.com/tunePage?a=trillian.mit.edu/~jc/music/book/playford/playford.abc.txt/0009
# noinspection SpellCheckingInspection
# a phrygian; one flat
theBeggerBoy = '''
X:5
T:The Begger Boy
R:Jig
H:The tune name may derive from the song "The Begger Boy of the North"
H:(c. 1630)
N:This tune is in the rare Phrygian mode--suggested chords are given
M:6/8
L:1/8
Q:90
K:APhry
AAAf2f|ec2d2c|AF2G2G|A2B cA2||
AAAf2f|ec2d2c|Ac2ede|fA2G3|
Acc e>dc|dfg/2f/2 efd|cAF G2G|A2B cA2||
W:From ancient pedigree, by due descent
W:I well can derive my generation
W:Throughout all Christendome, and also Kent
W:My calling is known both in terme and vacation
W:My parents old taught me to be bold
W:Ile never be daunted, whatever is spoken
W:Where e're I come, my custome I hold
W:And cry, Good your worship, bestow one token!
W:--Roxburghe Ballads
'''


# http://abcnotation.com/tunePage?a=www.campin.me.uk/Embro/Webrelease/Embro/17riot/abc/SnaBas/0000
# Eb lydian, written with two flats
# noinspection SpellCheckingInspection
theBattleOfTheSnaBas = '''X:1
T:The Battle of the Sna' Ba's
Z:Jack Campin: "Embro, Embro", transcription (c) 2001
F:17riot/abc/SnaBas.abc
S:NLS MH.v.549
N:identical format, typeface and engraving style to The Lyre, but anonymous
M:C|
L:1/8
Q:1/2=72
K:Eb Lydian
e|B>EE>E B>EG>e|B>EE>E B2G>B |A>FF>F A>FG>B|A>FF>F B2GF|
  E>ee>f e>cB>G|F>ff>g f>ed>c|B>ee>f e>cB>e|
  d>fc>e d>fc>e|d>fc>e d>ec>d|e>fg>f e2e  |]
'''

# http://abcnotation.com/tunePage?a=www.oldmusicproject.com/AA2ABC/0701-1200/Abc-0901-1000/0912-Draught/0000
# has a secondary pickup bar mid-tune
# noinspection SpellCheckingInspection
draughtOfAle = '''X:0912
T:"A Draught of Ale"    (jig)     0912
C:after  Sg't. J. O'Neill
B:O'Neill's Music Of Ireland (The 1850) Lyon & Healy, Chicago, 1903 edition
Z:FROM O'NEILL'S TO NOTEWORTHY, FROM NOTEWORTHY TO ABC, MIDI AND .TXT BY VINCE BRENNAN June 2003 (HTTP://WWW.SOSYOURMOM.COM)
I:abc2nwc
M:6/8
L:1/8
K:G
D|GBA G2A|Bdg Bdg|GBA G2B|AFD AFD|
GBA G2A|Bdg Bdg|ecA dBG|cAF G2:|
|:d|egf g2f|ege dBG|GFG dBG|BAA A2d|
egf g2f|ege dBG|GFG dBG|cAF G2:|
'''

# has three tunes
# http://www.andyhornby.net/Music/slip%20jigs.abc
# noinspection SpellCheckingInspection
valentineJigg = '''
X:166
T:166  Valentine Jigg   (Pe)
M: 9/8
L: 1/8
S: original in 6/8 major reconstruction -AH
K:D
A3 F2A c2d | efe d2c BAG|A3 F2A c2d| A2a g>fg a3 :|
|: a2e c2e gag |e2c d2f efe |d3 G2B cdc |ABc dcB A3:|
%%vskip 1.5cm

X:167
T:167  The Dublin Jig     (HJ)
A:Wyresdale, Lancashire
B:H.S.J. Jackson, 1823
L:1/8
M:9/8
K:A
f|ecA ABA agf | ecA FBA GFE |ecA Ace agf | ecA FBG A2  :|
|:c|BGE EGB dcB | cAc ece aec |BGE EGB dcB | cde dcB A2  :|
%%vskip 1.5cm

X:168
T:168  The Castle Gate   (HJ)
A:Wyresdale, Lancashire
B:H.S.J. Jackson, 1823
L:1/8
S: original in E
M:9/8
K:A
E | Ace Ace Ace | Ace BcA GFE | Ace Ace Ace | cag fe^d e2 :|
|:e | fga def Bcd | FGA BcA GFE | FAd GBe Ace | fdB BAG A2 :|
%%vskip 1.5cm
'''


# ------------------------------------------------------------------------------
# raw data for direct translation tests

slurTest = '''
X: 979
T: Triplets in Slurs, Slurs in Triplets, Nested Slurs
M: 2/4
L: 1/16
K: Edor
B,2|E^DEE ((3GFG)BA)|E^DEF (3(GFG))BA|(E(^DE)F) (3(GF)G)BA|(E^DEF (3(GFG)))BA|G6
'''

tieTest = '''
X: 979
T: Slur test, plus tie tokens
M: 2/4
L: 1/16
K: Edor
B,2|E^DE-E ((3GFG)BA)|E^DEF (3(G-GG))BA|(E(^DE)F) (3(GF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

crescTest = '''
X: 979
T: Tie test, plus crescendo tokens
M: 2/4
L: 1/16
K: Edor
B,2|!crescendo(!E^DE-E!crescendo)! ((3GFG)BA)|E^DEF (3(G-GG))BA|(E(^DE)F) (3(GF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

dimTest = '''
X: 979
T: Tie test, plus diminuendo tokens
M: 2/4
L: 1/16
K: Edor
B,2|!diminuendo(!E^DE-E!diminuendo)! ((3GFG)BA)|E^DEF (3(G-GG))BA|(E(^DE)F) (3(GF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

staccTest = '''
X: 979
T: Diminuendo test, plus staccato tokens
M: 2/4
L: 1/16
K: Edor
B,2|!diminuendo(!.E^D.E-E!diminuendo)! ((3.G.F.G)BA)|E^DEF (3(G-GG))BA|(E(^DE)F) (3(GF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

bowTest = '''
X: 979
T: Staccato test, plus bowing articulations
M: 2/4
L: 1/16
K: Edor
B,2|!diminuendo(!.E^D.E-E!diminuendo)! ((3.G.F.G)BvA)|E^DEF (3(G-GG))BuA|(E(^DuE)F) (3(GF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

# noinspection SpellCheckingInspection
accTest = '''
X: 979
T: Staccato test, plus accents and tenuto marks
M: 2/4
L: 1/16
K: Edor
B,2|!diminuendo(!.E^D.E-E!diminuendo)! ((3.G.F.KG)BA)|E^DMEF (3(G-GG))BkMA|(E(^DE)F) (3(kGKF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

# noinspection SpellCheckingInspection
graceTest = '''
X: 979
T: Slur test, plus grace notes
M: 2/4
L: 1/16
K: Edor
B,2|{E^DEE} E^DEE ((3GFG)BA)|E^DEF {CDEFGAB}(3(GFG))BA|(E(^DE)F) (3(GF)G)BA|(E^DEF (3(GFG)))BA|G6
'''

# noinspection SpellCheckingInspection
guineapigTest = '''
X: 979
T: Guinea Pig
M: 2/4
L: 1/16
K: Edor
B,2|!diminuendo(!KE^DkK.uvME-E!diminuendo)! !GARBAGE! {CDEFGAB} ((3.G.FG){BA}BA)|{E^DMEF} E^DMEF(3(G-GG))BA|(E(^DE)F) (3(GF)G)A-A|(E^DEF (3(GFG)))BA|G6
'''

# noinspection SpellCheckingInspection
testPrimitive = '''
M:4/4
ed|cecA B2ed|cAcA E2ed|cecA B2ed|c2A2 A2:|
K:G

AB|cdec BcdB|ABAF GFE2|cdec BcdB|c2A2 A2:|

% comment line

E2E EFE|E2E EFG|\
M:9/8
A2G F2E D2|]

"C"[CEGc] "Gm7"[.=G,^c']

(3.a.b.c  % stacato
vAuBvA  % up down bow
'''

testPrimitivePolyphonic = '''M:6/8
L:1/8
K:G
V:1 name="Whistle" snm="wh"
B3 A3 | G6 | B3 A3 | G6 ||
V:2 name="violin" snm="v"
BdB AcA | GAG D3 | BdB AcA | D6 ||
V:3 name="Bass" snm="b" clef=bass
D3 D3 | D6 | D3 D3 | D6 ||
'''

# noinspection SpellCheckingInspection
testPrimitiveTuplet = '''M:4/4
K:E
T:Test Tuplet Primitive
(3.c=c^c (5ccc=cc (6ccccc=f (7Bcc^^c=cc^f

(3.c2=c2^c2 (3.c2=c2^c2

(6c/c/c/c/c/=f/ (6B/c/c/^^c/c/^f/ z4

'''
# (9Bc^C ^c=cc =Cc=f


# abc-2.1 code + allowing shared header information.
# noinspection SpellCheckingInspection
reelsABC21 = '''%abc-2.1
M:4/4
O:Irish
R:Reel

X:1
T:Untitled Reel
C:Trad.
K:D
eg|a2ab ageg|agbg agef|g2g2 fgag|f2d2 d2:|\
ed|cecA B2ed|cAcA E2ed|cecA B2ed|c2A2 A2:|
K:G
AB|cdec BcdB|ABAF GFE2|cdec BcdB|c2A2 A2:|

X:2
T:Kitchen Girl
C:Trad.
K:D
[c4a4] [B4g4]|efed c2cd|e2f2 gaba|g2e2 e2fg|
a4 g4|efed cdef|g2d2 efed|c2A2 A4:|
K:G
ABcA BAGB|ABAG EDEG|A2AB c2d2|e3f edcB|ABcA BAGB|
ABAG EGAB|cBAc BAG2|A4 A4:|
'''

sponge1613 = '''
X:1
T:Example 16-13
L:1/4
M:3/4
K:F
V:1
fz((6:4F,//A,//C//F//A//c// e/d/)dz
'''

# noinspection SpellCheckingInspection
czernyCsharp = '''
X:4
T:D Fragment
C:Czerny
M:C
K:C#
L:1/16
CEDF EGFA GBAc Bdce|]
'''

carryThrough = '''
X:213
T:Through Measure
L:1/16
Q:1/4=104
M:4/4
K:G
V:1 treble
V:1
(=fe^d^c _BcdB) fB=BB c=cc^c|c4d2f2 ^G2=f2B2^A2-|A4F4 A2B2  c2f2|]
'''

tieOver = '''
X:213
T:Tie Through Measure
L:1/8
M:4/4
K:G
V:1 treble
V:1
z8 ^G=fB^A-|A2F2 AB cf|]
'''

directiveCarryOctave = '''
%abc-2.1
%%propagate-accidentals octave
X:213
T:Directive Octave
L:1/8
M:4/4
K:G
V:1 treble
V:1
g^G_ag a=ffF|=F2^c2 FB =ca|]
'''

directiveCarryPitch = '''
%abc-2.1
%%propagate-accidentals pitch
X:213
T:Directive Pitch
L:1/8
M:4/4
K:G
V:1 treble
V:1
g^G_ag a=ffF|=F2^c2 FB =ca|]
'''

directiveCarryNot = '''
%abc-2.1
%%propagate-accidentals not
X:213
T:Directive Not
L:1/8
M:4/4
K:G
V:1 treble
V:1
g^G_ag a=ffF|=F2^c2 FB =ca|]

'''


# ------------------------------------------------------------------------------

ALL = [fyrareprisarn, mysteryReel, fullRiggedShip, aleIsDear, kitchGirl,
        williamAndNancy, morrisonsJig, hectorTheHero, kingOfTheFairies,
        sicutRosa, theAleWifesDaughter, theBeggerBoy, theBattleOfTheSnaBas,
        draughtOfAle,
        valentineJigg,
        testPrimitive, testPrimitivePolyphonic, testPrimitiveTuplet
       ]


def get(contentRequest):
    '''
    Get test material by type of content
    '''
    pass


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testBasic(self):
        from music21 import abcFormat
        from music21.abcFormat import translate
        from music21.musicxml import m21ToXml

        af = abcFormat.ABCFile()
        GEX = m21ToXml.GeneralObjectExporter()

        for i, tf in enumerate(ALL):
            ah = af.readstr(tf)
            title = ah.getTitle()
            environLocal.printDebug([title])
            s = translate.abcToStreamScore(ah)
            # run musicxml processing to look for internal errors
            # print(repr(s.metadata._workIds['localeOfComposition']._data))
            # print(s.metadata.all())
            try:
                unused_out = GEX.parse(s)
            except UnicodeDecodeError as ude:
                environLocal.warn('About to fail on ABC file #{}'.format(i))
                raise ude

    def testKeySignatures(self):
        from music21 import abcFormat
        from music21.abcFormat import translate
        af = abcFormat.ABCFile()
        ah = af.readstr(czernyCsharp)
        s = translate.abcToStreamScore(ah)
        sharps = s.parts[0].keySignature.sharps
        self.assertEqual(sharps, 7, 'C# key signature should be parsed as 7 sharps')

    def testAbc21(self):
        from music21 import abcFormat, note
        from music21.abcFormat import translate

        af = abcFormat.ABCFile(abcVersion=(2, 1, 0))
        ah = af.readstr(carryThrough)
        title = ah.getTitle()
        environLocal.printDebug([title])
        s = translate.abcToStreamScore(ah)
        notes = s.flat.getElementsByClass(note.Note)
        cSharp = notes[3]
        cThrough = notes[5]
        self.assertEqual(cSharp.pitch.midi, cThrough.pitch.midi,
                         'Sharp does not carry through measure')
        bFlat = notes[4]
        bLast = notes[7]
        self.assertEqual(bFlat.pitch.midi, bLast.pitch.midi, 'Flat does not carry through measure')
        bNat = notes[10]
        bNatNext = notes[11]
        self.assertEqual(bNat.pitch.midi, bNatNext.pitch.midi,
                         'Natural does not carry through measure')
        self.assertEqual(notes[12].pitch.midi, 73, 'Sharp does not carry through measure')
        self.assertEqual(notes[13].pitch.midi, 72, 'Natural is ignored')
        self.assertEqual(notes[14].pitch.midi, 72, 'Natural does not carry through measure')
        self.assertEqual(notes[16].pitch.midi, 72, 'Sharp carries over measure incorrectly')
        self.assertEqual(notes[17].pitch.midi, 74, 'Sharp (D5) carries over measure incorrectly')
        self.assertEqual(notes[18].pitch.midi, 78, 'Natural (F5) carries over measure incorrectly')
        # TODO: Carrying an accidental into the next measure with a tie does not work.
        # notes = s.flat.getElementsByClass(note.Note)
        # self.assertEqual(notes[4].pitch.midi, 70, 'Tied note loses it sharp')
        # self.assertEqual(notes[6].pitch.midi, 69, 'Tied-over sharp persists past the tie')

    def testAbc21DirectiveCarryPitch(self):
        from music21 import abcFormat, note
        from music21.abcFormat import translate

        af = abcFormat.ABCFile()
        ah = af.readstr(directiveCarryPitch)
        s = translate.abcToStreamScore(ah)
        notes = s.flat.getElementsByClass(note.Note)
        gSharp = notes[1]
        g8va = notes[3]
        self.assertEqual(gSharp.pitch.midi % 12,
                         g8va.pitch.midi % 12,
                         'Sharp does not carry through measure')
        aFlat = notes[2]
        a = notes[4]
        self.assertEqual(aFlat.pitch.midi,
                         a.pitch.midi,
                         'Flat does not carry through measure')
        fNat = notes[5]
        f = notes[6]
        f8ba = notes[7]
        self.assertEqual(fNat.pitch.midi,
                         f.pitch.midi,
                         'Natural does not carry through measure')
        self.assertEqual(fNat.pitch.midi % 12,
                         f8ba.pitch.midi % 12,
                         'Natural does not carry through measure')
        self.assertEqual(notes[8].pitch.midi, 65, 'Natural is ignored')
        self.assertEqual(notes[12].pitch.midi, 72, 'Natural is ignored')

    def testAbc21DirectiveCarryOctave(self):
        from music21 import abcFormat, note
        from music21.abcFormat import translate

        af = abcFormat.ABCFile()
        ah = af.readstr(directiveCarryOctave)
        s = translate.abcToStreamScore(ah)
        notes = s.flat.getElementsByClass(note.Note)
        gSharp = notes[1]
        g8va = notes[3]
        self.assertGreater(gSharp.pitch.midi % 12,
                           g8va.pitch.midi % 12,
                           'Sharp carries beyond its octave')
        aFlat = notes[2]
        a = notes[4]
        self.assertEqual(aFlat.pitch.midi,
                         a.pitch.midi,
                         'Flat does not carry through measure')
        fNat = notes[5]
        f = notes[6]
        f8ba = notes[7]
        self.assertEqual(fNat.pitch.midi,
                         f.pitch.midi,
                         'Natural does not carry through measure')
        self.assertLess(fNat.pitch.midi % 12,
                        f8ba.pitch.midi % 12,
                        'Natural carries beyond its octave')
        self.assertEqual(notes[8].pitch.midi, 65, 'Natural is ignored')
        self.assertEqual(notes[12].pitch.midi, 72, 'Natural is ignored')

    def testAbc21DirectiveCarryNot(self):
        from music21 import abcFormat, note
        from music21.abcFormat import translate

        af = abcFormat.ABCFile()
        ah = af.readstr(directiveCarryNot)
        s = translate.abcToStreamScore(ah)
        notes = s.flat.getElementsByClass(note.Note)
        gSharp = notes[1]
        g8va = notes[3]
        self.assertGreater(gSharp.pitch.midi % 12,
                           g8va.pitch.midi % 12,
                           'Sharp carries beyond its octave')
        aFlat = notes[2]
        a = notes[4]
        self.assertLess(aFlat.pitch.midi,
                        a.pitch.midi,
                        'Flat carries through measure')
        fNat = notes[5]
        f = notes[6]
        f8ba = notes[7]
        self.assertLess(fNat.pitch.midi,
                        f.pitch.midi,
                        'Natural carries through measure')
        self.assertLess(fNat.pitch.midi % 12,
                        f8ba.pitch.midi % 12,
                        'Natural carries beyond its octave')
        self.assertEqual(notes[8].pitch.midi, 65, 'Natural is ignored')
        self.assertEqual(notes[12].pitch.midi, 72, 'Natural is ignored')


if __name__ == '__main__':
    import music21
    # music21.converter.parse(reelsABC21, format='abc').scores[1].show()
    music21.mainTest(Test)


