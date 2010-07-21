


from music21 import midi as midiModule
from music21 import defaults
from music21 import pitch



#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass



#-------------------------------------------------------------------------------
# Notes

def fromMidiEventsToNote(eventList, ticksPerQuarter=None, input=None):
    '''Convert from a list of MIDI message to a music21 note

    The `input` parameter can be a Note or None; in the case of None, a Note object is created. 
    '''
    if input == None:
        from music21 import note
        n = note.Note()
    else:
        n = input

    if len(eventList) == 2:
        tOn, eOn = eventList[0]
        tOff, eOff = eventList[1]

        n.duration.midi = (tOff - tOn), ticksPerQuarter
        n.pitch.midi = eOn.pitch
    else:
        raise TranslateException('cannot handle MIDI event list in the form: %r', eventList)
    return n


def fromNoteToMidiEvents(input):

    n = input

    mt = None # use a midi track set to None
    eventList = []
    dt = midiModule.DeltaTime(mt)
    dt.time = 0 # set to zero; will be shifted later as necessary
    # add to track events
    eventList.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "NOTE_ON"
    me.channel = 1
    me.time = None # not required
    me.pitch = n.midi
    me.velocity = 90 # default, can change later
    eventList.append(me)

    # add note off / velocity zero message
    dt = midiModule.DeltaTime(mt)
    dt.time = n.duration.midi
    # add to track events
    eventList.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "NOTE_OFF"
    me.channel = 1
    me.time = None #d
    me.pitch = n.midi
    me.velocity = 0 # must be zero
    eventList.append(me)

    return eventList 



def fromNoteToMidiFile(input): 
    n = input

    mt = midiModule.MidiTrack(1)
    mt.events += midiModule.getStartEvents(mt)
    mt.events += fromNoteToMidiEvents(n)
    mt.events += midiModule.getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf




#-------------------------------------------------------------------------------
# Chords

def fromMidiEventsToChord(eventList, ticksPerQuarter=None, input=None):

    if input == None:
        from music21 import chord
        c = chord.Chord()
    else:
        c = input

    if isinstance(eventList, list) and isinstance(eventList[0], list):
        pitches = []
        # pairs of pairs
        for onPair, offPair in eventList:
            tOn, eOn = onPair
            tOff, eOff = offPair

            p = pitch.Pitch()
            p.midi = eOn.pitch
            pitches.append(p)
            
    c.pitches = pitches
    # can simply use last-assigned pair of tOff, tOn
    c.duration.midi = (tOff - tOn), ticksPerQuarter
    return c



def fromChordToMidiEvents(input):
    mt = None # midi track 
    eventList = []
    c = input

    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        dt = midiModule.DeltaTime(mt)
        # for a chord, only the first delta time should have the offset
        # here, all are zero
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

        me = midiModule.MidiEvent(mt)
        me.type = "NOTE_ON"
        me.channel = 1
        me.time = None # not required
        me.pitch = pitchObj.midi
        me.velocity = 90 # default, can change later
        eventList.append(me)

    # must create each note on in chord before each note on
    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        # add note off / velocity zero message
        dt = midiModule.DeltaTime(mt)
        # for a chord, only the first delta time should have the dur
        if i == 0:
            dt.time = c.duration.midi
        else:
            dt.time = 0
        eventList.append(dt)

        me = midiModule.MidiEvent(mt)
        me.type = "NOTE_OFF"
        me.channel = 1
        me.time = None #d
        me.pitch = pitchObj.midi
        me.velocity = 0 # must be zero
        eventList.append(me)
    return eventList 



def fromChordToMidiFile(input): 
    # this can be consolidated with fromNoteToMidiFile
    c = input

    mt = midiModule.MidiTrack(1)
    mt.events += midiModule.getStartEvents(mt)
    mt.events += fromChordToMidiEvents(c)
    mt.events += midiModule.getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf

