# Some useful constants for binary translation
# =================

# midi instruments name from general midi patch
MidiInstruments = [
    'Acoustic Grand Piano',     # 0
    'Bright Acoustic Piano',    # 1
    'Electric Grand Piano',     # 2
    'Honky-tonk Piano',         # 3
    'Electric Piano 1',         # 4
    'Electric Piano 2',         # 5
    'Harpsichord',              # 6
    'Clavi',                    # 7
    'Celesta',                  # 8
    'Glockenspiel',             # 9
    'Music Box',                # 10
    'Vibraphone',               # 11
    'Marimba',                  # 12
    'Xylophone',                # 13
    'Tubular Bells',            # 14
    'Dulcimer',                 # 15
    'Drawbar Organ',            # 16
    'Percussive Organ',         # 17
    'Rock Organ',               # 18
    'Church Organ',             # 19
    'Reed Organ',               # 20
    'Accordion',                # 21
    'Harmonica',                # 22
    'Tango Accordion',          # 23
    'Acoustic Guitar (nylon)',  # 24
    'Acoustic Guitar (steel)',  # 25
    'Electric Guitar (jazz)',   # 26
    'Electric Guitar (clean)',  # 27
    'Electric Guitar (muted)',  # 28
    'Overdriven Guitar',        # 29
    'Distortion Guitar',        # 30
    'Guitar harmonics',         # 31
    'Acoustic Bass',            # 32
    'Electric Bass (finger)',   # 33
    'Electric Bass (pick)',     # 34
    'Fretless Bass',            # 35
    'Slap Bass 1',              # 36
    'Slap Bass 2',              # 37
    'Synth Bass 1',             # 38
    'Synth Bass 2',             # 39
    'Violin',                   # 40
    'Viola',                    # 41
    'Cello',                    # 42
    'Contrabass',               # 43
    'Tremolo Strings',          # 44
    'Pizzicato Strings',        # 45
    'Orchestral Harp',          # 46
    'Timpani',                  # 47
    'String Ensemble 1',        # 48
    'String Ensemble 2',        # 49
    'SynthStrings 1',           # 50
    'SynthStrings 2',           # 51
    'Choir Aahs',               # 52
    'Voice Oohs',               # 53
    'Synth Voice',              # 54
    'Orchestra Hit',            # 55
    'Trumpet',                  # 56
    'Trombone',                 # 57
    'Tuba',                     # 58
    'Muted Trumpet',            # 59
    'French Horn',              # 60
    'Brass Section',            # 61
    'SynthBrass 1',             # 62
    'SynthBrass 2',             # 63
    'Soprano Sax',              # 64
    'Alto Sax',                 # 65
    'Tenor Sax',                # 66
    'Baritone Sax',             # 67
    'Oboe',                     # 68
    'English Horn',             # 69
    'Bassoon',                  # 70
    'Clarinet',                 # 71
    'Piccolo',                  # 72
    'Flute',                    # 73
    'Recorder',                 # 74
    'Pan Flute',                # 75
    'Blown Bottle',             # 76
    'Shakuhachi',               # 77
    'Whistle',                  # 78
    'Ocarina',                  # 79
    'Lead 1 (square)',          # 80
    'Lead 2 (sawtooth)',        # 81
    'Lead 3 (calliope)',        # 82
    'Lead 4 (chiff)',           # 83
    'Lead 5 (charang)',         # 84
    'Lead 6 (voice)',           # 85
    'Lead 7 (fifths)',          # 86
    'Lead 8 (bass + lead)',     # 87
    'Pad 1 (new age)',          # 88
    'Pad 2 (warm)',             # 89
    'Pad 3 (polysynth)',        # 90
    'Pad 4 (choir)',            # 91
    'Pad 5 (bowed)',            # 92
    'Pad 6 (metallic)',         # 93
    'Pad 7 (halo)',             # 94
    'Pad 8 (sweep)',            # 95
    'FX 1 (rain)',              # 96
    'FX 2 (soundtrack)',        # 97
    'FX 3 (crystal)',           # 98
    'FX 4 (atmosphere)',        # 99
    'FX 5 (brightness)',        # 100
    'FX 6 (goblins)',           # 101
    'FX 7 (echoes)',            # 102
    'FX 8 (sci-fi)',            # 103
    'Sitar',                    # 104
    'Banjo',                    # 105
    'Shamisen',                 # 106
    'Koto',                     # 107
    'Kalimba',                  # 108
    'Bag pipe',                 # 109
    'Fiddle',                   # 110
    'Shanai',                   # 111
    'Tinkle Bell',              # 112
    'Agogo',                    # 113
    'Steel Drums',              # 114
    'Woodblock',                # 115
    'Taiko Drum',               # 116
    'Melodic Tom',              # 117
    'Synth Drum',               # 118
    'Reverse Cymbal',           # 119
    'Guitar Fret Noise',        # 120
    'Breath Noise',             # 121
    'Seashore',                 # 122
    'Bird Tweet',               # 123
    'Telephone Ring',           # 124
    'Helicopter',               # 125
    'Applause',                 # 126
    'Gunshot']                  # 127

# Clef objects
# =================
# Clef Names
ClefNames = [
    'Treble',
    'Bass',
    'Alto',
    'Tenor'
    'Percussion']

# octave shift indicators
OctaveShiftNames = [
    None,
    'Octave Up',
    'Octave Down']


# Key signatures
# =================
# Flat mask
FlatMask = {
    0x00: '',
    0x02: 'Bb',
    0x12: 'Bb,Eb',
    0x13: 'Bb,Eb,Ab',
    0x1B: 'Bb,Eb,Ab,Db',
    0x5B: 'Bb,Eb,Ab,Db,Gb',
    0x5F: 'Bb,Eb,Ab,Db,Gb,Cb',
    0x7F: 'Bb,Eb,Ab,Db,Gb,Cb,Fb'}

# sharp mask
SharpMask = {
    0x00: '',
    0x20: 'F#',
    0x24: 'F#,C#',
    0x64: 'F#,C#,G#',
    0x6C: 'F#,C#,G#,D#',
    0x6D: 'F#,C#,G#,D#,A#',
    0x7D: 'F#,C#,G#,D#,A#,E#',
    0x7F: 'F#,C#,G#,D#,A#,E#,B#'}

# Text for alteration. x is double #, v double b.
AlterationTexts = [
    '#',
    'b',
    'n',
    'x',
    'v',
    '']

# Bar line styles
# =================
BarStyles = [
    'Single',
    'Double',
    'SectionOpen',
    'SectionClose',
    'LocalRepeatOpen',
    'LocalRepeatClose',
    'MasterRepeatOpen',
    'MasterRepeatClose']

# Duration name
# =================
DurationValues = [
    'Whole',
    'Half',
    '4th',
    '8th',
    '16th',
    '32nd',
    '64th']
