




Object Design Sketch Pad
========================


This is a place where object design is discussed prior to implementation. For exisiting objects, attributes and methods may not match what is sketched here. 








GeneralNote
-----------
*attributes*
    + duration
    + notations
    + editorial
    + tie
*methods*
    + clone()
    + reinit()
    + splitNoteAtPoint()

Discussion
~~~~~~~~~~~

1. rename splitNoteAtPoint() to split() ?
2. Use ComplexDuration here





PitchedOrUnpitched(GeneralNote)
-------------------------------
*attributes*
    + 
*methods*
    + splitNoteAtPoint()



Discussion
~~~~~~~~~~~

1. Overridden method provides creation of a tie object to split
the only object that does not inheret form this is rest

2. Why not put full functionality of split() in GeneralNote; check if it is a rest or not by looking at attribute

3. It seems that this subclass is not necessary; functionality here can be put in GeneralNote, and then Rest, Unpitched, and Note can specialize.







SimpleNote(PitchedOrUnpitched)
-------------------------------
*attributes*
    + _overridden_freq440
    + _twelfth_root_of_two
    + accidental
    + octave
    + isNote
    + isUnpitched
    + isRest
*methods*
    + _getname() / .name
    + _setname() / .name
    + _getstep() / .step
    + _setstep() / .step
    + _preDurationLily()
    + _lilyName() / .lilyName
    + appendDuration()
    + addAccidentalObj()
    + addAccidentalStr()
    + diatonicNoteNum()
    + midiNote()
    + _getPitchClass  / .pitchClass


Discussion
~~~~~~~~~~~

ca:
appendDuration() might be better named setDuration()


how do we represent microtones?

why not:
_getPitchClass  / .pc
_midiNote  / .midi

and have setters that function as for name and step?





ComplexNote(SimpleNote)
-----------------------
*attributes*
    + componentDurations {*remove, access from duration*}
    + durationLinkages {*remove, access from duration*}
    + duration
*methods*
    + appendDuration()
    + clearDurations()
    + splitAtDurations()
    + _lilyName() / .lilyName

Discussion
~~~~~~~~~~~
1. componentDurations should always be accessed tyhrough the Duration object





Note(ComplexNote)
-----------------------
*attributes*
    + 
*methods*
    + 

Discussion
~~~~~~~~~~~
1. This is not an alias; this is a subclass.
why not make ComplexNote just Note?






Unpitched(PitchedOrUnpitched)
-----------------------------
*attributes*
    + displayStep = "C"
    + displayOctave = 4
    + isNote = False
    + isUnpitched = True
    + isRest = False
*methods*
    + 

Discussion
~~~~~~~~~~~
 
1. Rests may also need display values. Thus, perhaps Rest should inherit from Unpitched?

2. Perhaps Unpitched should simply inherit from GeneralNote?





Rest(GeneralNote)
----------------------------
*attributes*
    + isNote
    + isUnpitched
    + isRest
    + name
    + displayStep {*add*}
    + displayOctave {*add*}
*methods*
    + __lilyName() / .lillyName

Discussion
~~~~~~~~~~~

1. A rest does likely need to know how to split its duration. Thus, a rest should have a ComplexDuration, not just a simple Duration. 

2. A rest this might need a display pitch/octave ot something of the sort: somtimes rests are shifted in the staff (MusicXML supports this). Rest should inherit from 





Accidental
----------------------------
*attributes*
    + alter
    + displayType
    + displayEvaluated
    + displayStyle
    + displaySize
    + modifier
*methods*
    + __init__()
    + setAccidental()
    + __getLily() / .lillyName
    + __setLily() / .lillyName


Discussion
~~~~~~~~~~~

1. Why use of double underscore (__getLily); not used in SimpleNote?

2. Can we standardize Lily attributes as .lillyString or .lilly for all objects?





Tuplet {*modified*}
-----------------------
*attributes*
    + tupletId
    + nestedLevel
    + durationActual {*remove*}
    + durationNormal {*remove*}
    + tupletActual : [number, Duration]
    + tupletNormal : [number, Duration]
*methods*
    + tupletMultiplier()
    + totalTupletLength()
    + setRatio(number, number) {*new*}

Discussion
~~~~~~~~~~~

1. This seems like it could use some improvemens to avoid attributes getting out of sync with each other. For exampe, tupletActual might be changed while durationAcutal is not changed. 





Duration {*modified*}
-----------------------
*attributes*
    + _type {*changed*}
    + _qtrLength
    + _dots : []
    + _tuplets : []
    + timeInfo : []
*methods*
    + _updateQuarterLength()

    + _getType() / .type 
    + _setType() / .type {*permits validation*}

    + _getDots() / .dots 
    + _setDots() / .dots {*permits validation*}

    + _getQuarterLength() / .quarterLength
    + _setQuarterLength() / .quarterLength
    + clone()

    + _lilySimple / .lilySimple

    + convertTypeToQuarterLength()
    + convertQuarterLengthToType()
    + convertQuarterLengthToDuration()
    + convertNumberToType()
    + convertTypeToNumber()
    + convertTypeToOrdinal()

    + split() {*new*}
        given a duration in quarter notes, split and return two dur objects
    + splitHalf() {*new*}
        split evenly in half


Discussion
~~~~~~~~~~~

1. A ratio set method might provide an easy way to configure durations.

2. Seems that _lilySimple should be _lilyString or similar as used elsewhere

3. self.dot is combined with dotGroups. 

4. this will be SimpleDuration







ComplexDuration(Duration) {*new*} 
-----------------------------------------
*attributes*
    + _qtrLength
    + components
    + linkages
*methods*
    + _getQuarterLength() / .quarterLength
    + _setQuarterLength() / .quarterLength

    + _isComplex / .isComplex
        seems that the property should be just .complex        
    + _updateQuarterLength()

    + _lilySimple / .lilySimple

    + sliceComponentAtPosition()

Discussion
~~~~~~~~~~~ 

1. This should be renamed a DurationBundle or something similar, and should be the only duration object used for all Notes. 

3. This will be Duration





TempoMark
-----------------------
*attributes*
*methods*


Discussion
~~~~~~~~~~~

1. Why is this a base class: what other types of TempoMarks are we considering?







MetronomeMark(TempoMark)
------------------------
*attributes*
    + number
    + referent : Duration
*methods*


Discussion
~~~~~~~~~~~

1. I assume that referent is the unit of the metronome. Thus number might be mean quarters per minute, or halfs per minute, depending on the referent?

2. What about a bpm() method that returns the tempo in beats per minute?

3. What about a timeLapse() (or othe named) method that, given a number of beats (or Duration objects) determines how much time has passed?








Tuning {*new*} 
-----------------------
*attributes*
    + twelfth_root_of_2
*methods*
    + __call__()
        Given a pitch object or pc, return a frequency? or 12ET microtonal value?


Discussion
~~~~~~~~~~~

1. Should this be named Temperament?

2. Should this be in its own module?

3. How can various tuning and temperatments be encoded? I have done this in the past with dictionaries that are used for mapping pitch classes to tunings values. 







Sequence
---------

Basic operations for timed sequences.

Repeat operations





NoteStream {*modified*}
------------------------
*attributes*
    + noteSequence
        ordered collection of note objects
*methods*
    + next()
        all standard sequence opperations can be applied
    + isMonophonic()
        find out of this is monophonic or not

Discussion
~~~~~~~~~~~

1. This object represents a sequence of sequential notes or chords, where there is no overlapping of any event, and chords are always stemmed together.

2. Notes need to have the option to contain dyanmics, accents, and other note articulations; thus they will easily always stay with the note.





PolyStream {*new*}
------------------------
*attributes*
    + noteCloud
        collection of note objects specified as (Duration, Note, voiceId)  

        data representation::
        
            [(Duration, Note, voiceId), (Duration, Note, voiceId), ..]
 
        Duration is offset from beginning of of this stream
        permits any type of layering or multi-voice expression
        voiceId is an optional identifier that can be used to group by voice, staff, or other parameter.

*methods*
    + isMonophonic()
        find out of this is monophonic or not

Discussion
~~~~~~~~~~~

1. Overlapping is permitted.

2. Notes need to have the option to contain dyanmics, accents, and other note articulations; thus they will easily always stay with the note.





NotationStream {*new*}
------------------------
*attributes*
    + tempoSequence 
        a sequenct list of (Duration, Tempo) objects
    + meterSequence
        a sequential list of (Duration, TimeSignature) objects, in order
    + keySequence
        a sequential list of (Duration, Key) objects, in order      
    + clefSequence 
        a sequenct list of (Duration, Clef) objects

    + expressionsSequence
        a sequential list of (Duration, Expression/Notation/Editorial) objects, in order  

*methods*
    + 

Discussion
~~~~~~~~~~~

1. This is a sequence of notation elements that are used to create Measures and scores. These are independent of any specific notes.

2. Contains one or more sequence objects; idea that we can add many sequences; we might have a sequence for comments, notes, editorial comments, original clefs.

3. instrument stream; where instruments change



Fragment
-----------------------
*attributes*
    + streams : {}
        data representation::
        
            {'streamName': 
                {'stream':Stream, 
                'offset':Duration
                'scale':Float
                }
            }

        one or more streams can be stored in a Fragment in a dictionar; dictionary also provides methods to shift in time (relative to this fragment and to scale in time the fragment.
        
    + notationStream : NotationStream
        all sequential notation information allplied to all streams

*methods*
    + 


Discussion
~~~~~~~~~~~

1. A fragment provides a way to group and contain one or more streams as well as a single notationSequence.







Measure(NotationStream?) {*modified*}
-----------------------
*attributes*
    + timeSignature
        changes to time signature may cause keySequence or barlineSequence
        to longer have reasonable values. 
    + barlineBoundary
        a two element list of (Bar, Bar) that stores Bar objects
    + barlineSequence
        a sequential list of (Duration, Bar) objects, in order
    + clefSequence 
        a sequenct list of (Duration, Clef) objects
    + tempoSequence 
        a sequenct list of (Duration, Tempo) objects
    + meterSequence
        a sequential list of (Duration, TimeSignature) objects, in order
    + keySequence
        a sequential list of (Duration, Key) objects, in order
    + expressionsSequence
        a sequential list of (Duration, Expression/Notation/Editorial) objects, in order        
    + noteCloud : []
        a list of (Duration, Note) pairs
*methods*
    + split()
        split into two measure given a quarter note length
        divide barlineSequence, keySequence as necessary
    + musicXML()
        return the MusicXML reprsentation
    + deriveNotationStream()
        return a notation stream representatio of this measure


Discussion
~~~~~~~~~~~

1. Using Duration objects to mark the position of elements may be very useful.

2. Measure is like a NotationStream though it has notes and is bound only within the time of its time signature. Measure may be a sub-class of NotationStream






Part {*new*}
-----------------------
*attributes*
    + staves : {}
        a dictionary of Measure sequences; more than one staff may be employed

        data representation::
        
            {'staffId': 
                {'measureSequence': [Measure, Measure, ...], 
                }
            }

    + fragment : Fragment

*methods*
    + _updateFragment():
        based on Measure, update fragment
    + _updateMeasures():
        based on Fragment, update measures

    + loadFragment(Fragment)
        given one or more Fragments, create and fill the necessary Measures
    + loadMeasures([Measure, Measure, ...])
        can load measures directly; can then be used to derive a fragment this is useful importing MusicXML

    + deriveFragment()
        return a Fragment
    + deriveNoteStream()
        return a note straem of this part
    + deriveNotationStream()
        return a notation straem of this part

    + musicXML()
    + lily()


Discussion
~~~~~~~~~~~

1. A part represents one ore more staves that are used as a musical unit. This could be a solo line or a two or three staff guitar/piano part. 

2. A part can only have one time signature / key at a time. 

3. When realized as Measures, the offsets and scaling factors of Fragmetns are taken into account







Score {*new*}
-----------------------
*attributes*
    + parts : {}
        store Part instances as well as metadata

        data representation::
        
            {'partId': 
                {'partName': String, 
                'partObj': Part
                'partAbbreviation': String, 
                'instrument': String, 
                'transposition': String, 
                'midiData': String, 
                }
            }

*methods*
    + musicXML()
    + lily()


Discussion
~~~~~~~~~~~

1. Parts, based on their Fragments, may have different time signatures, measure boundaries, and key signatures. If these are not supported in the desired output format, then the Part must re-reprsent itself using a different (a common) NotationStream.



