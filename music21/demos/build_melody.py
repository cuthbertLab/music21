# -*- coding: utf-8 -*-
"""
Demo script showing how to work with MidiFile and MidiTrack directly.
Generates a completely random collection of 8th notes
First we create a MidiTrack, insert MidiEvent's into it. Then we add
that track to a MidiFile and write it to disc.
"""

import random
from music21 import midi, environment


def populate_midi_track_from_data(mt, data):
    t = 0
    tLast = 0
    for d, p, v in data:
        dt = midi.DeltaTime(mt)
        dt.time = t - tLast
        # add to track events
        mt.events.append(dt)

        me = midi.MidiEvent(mt)
        me.type = "NOTE_ON"
        me.channel = 1
        me.time = None  # d
        me.pitch = p
        me.velocity = v
        mt.events.append(me)

        # add note off / velocity zero message
        dt = midi.DeltaTime(mt)
        dt.time = d
        # add to track events
        mt.events.append(dt)

        me = midi.MidiEvent(mt)
        me.type = "NOTE_OFF"
        me.channel = 1
        me.time = None  # d
        me.pitch = p
        me.velocity = 0
        mt.events.append(me)

        tLast = t + d  # have delta to note off
        t += d  # next time

    # add end of track
    dt = midi.DeltaTime(mt)
    dt.time = 0
    mt.events.append(dt)

    me = midi.MidiEvent(mt)
    me.type = "END_OF_TRACK"
    me.channel = 1
    me.data = ''  # must set data to empty string
    mt.events.append(me)

    return mt

def main():
    mt = midi.MidiTrack(1)

    # duration, pitch, velocity
    data = [] # one start note

    beats_per_measure = 4
    measures = 16
    num_beats = measures * beats_per_measure

    # note array is ordered [duration, pitch, velocity]
    for i in range(1, num_beats):
        # pick random pitch and velocity for 8th note
        duration = 512
        pitch = random.randint(0, 128)
        velocity = random.randint(0, 128)

        data.append([duration, pitch, velocity])

    populate_midi_track_from_data(mt, data)

    mf = midi.MidiFile()
    mf.tracks.append(mt)

    env = environment.Environment()
    temp_filename = env.getTempFile('.mid')
    print("Saving file to: %s" % temp_filename)
    mf.open(temp_filename, 'wb')
    mf.write()
    mf.close()

if __name__ == '__main__':
    main()
