from music21 import stream, note, chord, instrument, tempo, meter

# Create the score and parts
score = stream.Score()
melody = stream.Part()
harmony = stream.Part()
bass = stream.Part()

melody.insert(0, instrument.Flute())
harmony.insert(0, instrument.Violin())
bass.insert(0, instrument.Cello())

melody.append(tempo.MetronomeMark(number=100))
for part in [melody, harmony, bass]:
    part.append(meter.TimeSignature('4/4'))

# Add 40 measures of melody, harmony, and bass
for i in range(40):
    melody_notes = ['C5', 'D5', 'E5', 'F5'] if i % 2 == 0 else ['G5', 'A5', 'B4', 'C5']
    harmony_chord = ['C4', 'E4', 'G4'] if i % 2 == 0 else ['F4', 'A4', 'C5']
    bass_note = 'C3' if i % 2 == 0 else 'G2'

    m1 = stream.Measure()
    for pitch in melody_notes:
        m1.append(note.Note(pitch, quarterLength=1))
    melody.append(m1)

    m2 = stream.Measure()
    m2.append(chord.Chord(harmony_chord, quarterLength=4))
    harmony.append(m2)

    m3 = stream.Measure()
    m3.append(note.Note(bass_note, quarterLength=4))
    bass.append(m3)

# Combine parts and export
score.insert(0, melody)
score.insert(0, harmony)
score.insert(0, bass)

score.write('midi', fp='reflections_in_three_moods.mid')
print("MIDI file created: reflections_in_three_moods.mid")
