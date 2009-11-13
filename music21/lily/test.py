import music21
import music21.lily

def test():
	myString = '''VoiceIV = \\context Voice = VoiceIV {
	\\set Staff.midiInstrument = "acoustic grand"
	\\time 3/2
	\\key c \\major
	\\clef bass c2 f \\color "DeepPink" g4 f |
	e1 f2 |
	c \\ficta des4 \\ficta des \\ficta ees ees, |
	\\ficta a,2 des1 |
%5
	aes,1. \\bar "|."
}
\\score {
	<<

		
		\\VoiceIV
	>>
	\\layout {
	}

}'''
	myString2 = '''
{ \\tempo "Fast"
c'4 c' c' c'
c'4 c' c' c'
\\tempo "Andante" 4 = 120
c'4 c' c' c'
c'4 c' c' c'
\\tempo 4 = 100
c'4 c' c' c'
c'4 c' c' c'
\\tempo "" 4 = 30
c'4 c' c' c'
c'4 c' c' c'
}
'''

	music21.lily.LilyString(myString).showPNG()
	music21.lily.LilyString(myString2).showPNGandPlayMIDI()


def bracesTest():
	'''
	can we put braces around anything in lily?
	Apparently So
	'''
	lString = music21.lily.LilyString('{ \\time 6/4 {c\'4~} {c\'4} {d\'4} {ees\'4} r2 }')
	lString.showPNG()

if (__name__ == "__main__"):
	bracesTest()