# -*- coding: utf-8 -*-
_DOC_IGNORE_MODULE_OR_PACKAGE = True

#import os
import unittest
#from music21 import analysis
#from music21 import common
#from music21 import *  # doing this because it will simplify the examples

# note: this are temporarily commented out until they work
# add optional show argument to mask output for automated testing

class Test(unittest.TestCase):

    def runTest(self):
        pass
            
#### thoughts on how to do this...
#    def xtest001(self):
#        '''Above G4 do higher pitches tend to be louder?
#        Is this asking if all pitches above G4 are louder, or if, above G4, 
#        as pitches get higher, are they louder?
#        '''
#        from music21 import analysis
#        from music21 import converter
#
#        partStream = converter.parse("dichterliebe1.xml")
#
#        ## make monophonic or make chords have a single pitch object...
#        notesAbove, notesBelow = analysis.partition(partStream, 'pitch', 'G4')
##        notesAbove, notesBelow = analysis.partition(partStream, this.pitch.midiNote > G4.midiNote)
#
#        # assuming we want to somehow graph two values, pitch space and 
#        # dynamics, by creating a table. this table could then be interpolated
#        # to determine trends
#        table = analysis.correlate(notesAbove, 'pitchSpace', 'dynamics')

### Thoughts on how to do this...
#    def xtest002(self):
#        '''Add explicit breath marks after each phrase.'''
#        from music21 import analysis
#        from music21 import converter
#
#        partStream = converter.parse("dichterliebe1.xml")
#        # we are frequently going to need a way to partition data into      
#        # phrases. this will be a very common operation that will
#        # need a number of different approaches
#
#        # a phrase stream is partitioned stream of phrases
#        # might provide a list of criteria that are used to partition 
#        # phrases
#        phraseStream = analysis.phraseExtract(partStream, 
#                               ['rest', 'slur', 'register'])
#        for phrase in phraseStream:
#            phraseNew = phrase.clone() 
#            phraseNew.append(articulations.BreathMark)
#            # how do we edit/update the old score? assuming that
#            # the objects are not linked, we need to find and replace
#            partStream.replace(phrase, phraseNew)


    def xtest003(self):
        '''Add key velocities to some MIDI data that reflect accent levels arising from the meter.

        Modify this to just adjust dynamics based on meter; this should be 
        reflected in musical output
        '''
        from music21 import articulations
        from music21 import converter

        partStream = converter.parse("dichterliebe1.xml")
        #for part in partStream.partData:
        # a part stream could have an iterator that partitions itself
        # into measure-length part streams
        for measure in partStream.getElementsByClass('Measure')():  # () ? 
            # measure is a partStream isolated for just the desired measure
            # assuming only one meter per measure
            meterObj = measure['meter']
            # get a list of pairs, specifying offset and accent
            for offset, accent in meterObj.accentPattern():
                if accent > 'mf': # assuming symbolic representation
                    # get all relevant elements
                    subStream = measure.getElementsByOffset(offset, 
                                    offset + meterObj.denominator)
                    # get a stream of just dynamics
                    dynamics = subStream.filterClass(articulations.DynamicArticulation)
                    for unused_obj in dynamics:
                        # can we increment dynamics by dynamics?
                        #obj += 'pppp'
                        pass
                    # will these changes be reflected in the source part stream?

    def xtest004(self):
        '''Align and display all of the bass lines for all of the variations concurrently.
'''
        pass

#    def xtest005(self):
#        '''Alphabetize a list of titles.'''
#        from music21 import analysis
#        from music21 import converter
#
#        corpusDir = 'path/to/files'
#        sort = []
#        for fn in os.listdir(corpusDir):
#            if not fn.endswith('.xml'): continue
#            # we may have more than one thing that looks like a title
#            titleCandidates = []
#            partStream = converter.parse(fn)
#            # pages might be represented as a stream of Page objects
#            # this could be contained w/n a part stream
#            pageStream = partStream['pages']
#            # assuming we have have classes for things on pages, such as 
#            # titles and other tex annotations
#            # here, we get these only from the first page
#            titleCandidates += pageStream[0].getElementsByClass(TextAnnotation)
#            # an additional slot might be used to store meta data, also
#            # as a stream
#            metaStream = partStream['meta'] 
#            titleCandidates += metaStream.getElementsByClass(TextAnnotation)
#            sort.append(titleCandidates)
#
#        sort.sort()



#    def xtest006(self):
#        '''Amalgamate arpeggios into chords and display as notation.
#
#        How are the arpeggios delineated? Is it a aprt with only arpeggios, or
#        are they intermingled?
#        '''
#        from music21 import analysis
#        from music21 import converter
#
#        partStream = converter.parse("dichterliebe1.xml")
#
#        # we might look at arpeggios as a type of extractable phrase, 
#        # looking fo open spacings, even rhythms, and chordal forms
#        phraseStream = analysis.phraseExtract(partStream, ['arpeggio'])
#        newStream = Stream()
#        newStream.append(partStream.notationStream)
#        for phrase in phraseStream:
#            chord = chord.Chord()
#            for note in Phrase:
#                chord.addPitch(note.pitch)
#            chord.duration = phrase.duration
#            chord.showJazzName = True ## something
#            chord.showFiguredBass = True ## 
#            newStream.appendNext(chord)
#
#        newStream.append(partStream)  # this puts them in parallel
#        newStream.show() 
        
#    def xtest007(self):
#        '''Annotate a score identifying possible cadential 6-4 chords.'''
#
#        chordSequenceMatch = chord.factory('V64'), chord.factory('I')
#
#        partStream = music21.converter.parse("dichterliebe1.xml")
#        ## when we have a passing-tone etc. removal program run here...
#        
#        chordStream = analysis.phraseExtract(partStream, ['simultaneities'])
#
#        # might have many different approaches to key analysls
#        # all return a stream of keys, with key objects at the appopriate 
#        # offsets
#        keyStream = analysis.key(partStream, 'chew.spiralArray')
#
#        for i in range(len(chordStream)-1):
#            chordThis = chordStream[i]
#            chordNext = chordStream[i+1]            
#            
#            # get key at this offset
#            # here, it is important that the offsets of the chords
#            # are the same scale as the offsets of the keyStream
#            # may need a method here that looks for elements that
#            # are active, not just present
#            # keys thus do not need a duration
#        
#            ### getElementsByOffsetRange....
#            key = keyStream.getElementsByOffset(chordThis.offset, 
#                            chordNext.offset, lastActive=True)
##            if (common.toRoman(chordThis.scaleDegree(key)) == "V" and chordThis.inversionName == "64" and
##                common.toRoman(chordThis.scaleDegree(key)) == "I" and chordThis.inversionName == "53"
##                )
## OR>:::           
#            if (chordThis.setKey(key) == chordSequenceMatch[0](key) and 
#                chordNext.setKey(key) == chordSequenceMatch[1](key)):
#                # here it is important that the offsets match that 
#                # of the source
#                # not sure where/how part stream places this
#                annotation = articulations.Annotation('big cadential moment')
#                partStream.insert(chordThis.offset, annotation)

#    def xtest008(self):
#        '''Are dynamic swells (crescendo-diminuendos) more common than dips (diminuendos-crescendos)?'''
#        partStream = music21.converter.parse("dichterliebe1.xml")
#        
#        # an analysis package can identify dynamic countours, movements from
#        # low to high or vice versa, and return these as a stream of
#        # DynamicMovement objects
#    
#        dynMovementStream = analysis.dynamicContour(partStream)
#        swells = dynMovementStream.getElementsByClass(DynamicCrescendo)
#        dips = dynMovementStream.getElementsByClass(DynamicDecrescendo)
#        if len(swells) > len(dips):
#            return 'swells win'
#        else:
#            return 'dips win'


    def xtest009(self):
        '''Are lower pitches likely to be shorter and higher pitches likely to be longer?'''

        partStream = music21.converter.parse("dichterliebe1.xml")
        unused_noteStream = partStream['notes']
        #unused_table = analysis.correlate(noteStream, 'pitchSpace', 'duration')

        # we must examine and interpoate the table in order to distinguish
        # trends

#    def xtest010(self):
#        '''Assemble individual parts into a full scores.'''
#        partStream = PartStream()
#        for part in PartsList:
#            partStream['id'].add(part)


    def xtest011(self):
        '''Assemble syllables into words for some vocal text.'''
        pass


    def xtest012(self):
        '''Calculate all the permuted harmonic intervals in a chord.'''
        pass

    def xtest013(self):
        '''Calculate changes of listeners' heart-rate from physiological data.
        
        We'll do something different from the Humdrum example which assumes you already
        have the data in spines.  Let's suppose you have the data in a Google Spreadsheet
        that has two columns: time and heart-rate.  We load the data in from the internet.
        We then convert the heart-rate data
        to a delta value (that is, the change since the last heart-rate measurement). 
        Next we add time data to each offset in our score; we then add an editorial attribute
        of "heart-rate" to the note just preceding the heart-rate measurement.
        We can then see if heart-rate is related to the dissonance level of the preceeding
        10 seconds.
        '''
        pass

    def xtest014(self):
        '''Calculate harmonic intervals between concurrent parts.'''
        pass


    
    def xtest015(self):
        '''Calculate harmonic intervals ignoring unisons.'''
        from collections import defaultdict
        score1 = music21.converter.parse("dichterliebe1.xml")
        monoScore = score1.chordsToNotes()    # returns a new Stream
        unused_notePairs = monoScore.getAllSimultaneousNotes()  # returns a list of Tuples intervals = interval.generateFromNotePairs(notePairs)
        intervals2 = defaultdict(lambda:0)
        for thisInt in intervals2:
            if thisInt.name != "P1":
                intervals2[thisInt.name] += 1

        for key in intervals2.sort(key = 'simpleName'):
            print(key, intervals2[key])



    def test016(self):
        '''Calculate harmonic intervals in semitones.'''
        pass

    def test017(self):
        '''Calculate melodic intervals not including intervals between the last note of one phrase and the first note of the next phrase.'''
        pass

    def test018(self):
        '''Calculate melodic intervals not including intervals between the last note of one phrase and the first note of the next phrase.'''
        pass

    def test019(self):
        '''Calculate pitch-class sets for melodic passages segmented by rests.'''
        pass

    def test020(self):
        '''Calculate pitch-class sets for melodic passages segmented by slurs/phrases.'''
        pass


    def test021(self):
        '''Calculate the difference in duration between the recapitulation and the exposition.'''
        pass

    def test022(self):
        '''Calculate the interval vector for some set.'''
        pass

    def test023(self):
        '''Calculate the normal form for some set.'''
        pass

    def test024(self):
        '''Calculate the prime form for some set.'''
        pass

    def test025(self):
        '''Calculate the proportion of sonorities where both the oboe and bassoon are active.'''
        pass

    def test026(self):
        '''Change all pizzicato marks to spiccato marks.'''
        pass

    def test027(self):
        '''Change all up-stems in measures 34 through 38 to down-stems.'''
        pass

    def test028(self):
        '''Classify cadences as either authentic, plagal or deceptive.'''
        pass

    def test029(self):
        '''Classify flute fingering transitions as either easy, moderate, or difficult.'''
        pass

    def test030(self):
        '''Classify phonemes in a vocal text as fricatives, nasals, plosives, etc.'''
        pass


    def test031(self):
        '''.'''
        pass

    def test032(self):
        '''.'''
        pass

    def test033(self):
        '''.'''
        pass

    def test034(self):
        '''.'''
        pass


    def test035(self):
        '''Compare the average overall dynamic level between the exposition and development sections.'''
        pass


    def test036(self):
        '''Compare the estimated keys for the 2nd theme in the exposition versus the 2nd theme in the recapitulation.'''
        pass

    def test037(self):
        '''Compare the first phrase of the Exposition with the first phrase of the Recapitulation.'''
        pass

    def test038(self):
        '''Compare the number of syllables in the first and second verses.'''
        pass

    def test039(self):
        '''Contrast the sonorities that occur on the first versus the third beats in a waltz repertory.'''
        pass

    def test040(self):
        '''Count how many measures contain at least one trill.'''
        pass


    def test041(self):
        '''Count the number of ascending major sixth intervals that occur in phrases that end on the dominant.'''
        pass

    def test042(self):
        '''Count the number of barlines in a work.'''
        pass

    def test043(self):
        '''Count the number of closed-position chords.'''
        pass

    def test044(self):
        '''Count the number of harmonic functions in each phrase.'''
        pass

    def test045(self):
        '''Count the number of notes in a work that belong to the same whole-tone set.'''
        pass

    def test046(self):
        '''Count the number of notes in measures 8 to 16.'''
        pass

    def test047(self):
        '''Count the number of notes in the exposition.'''
        pass

    def test048(self):
        '''Count the number of phrases in a score.'''
        pass

    def test049(self):
        '''Count the number of phrases that begin on the subdominant pitch.'''
        pass

    def test050(self):
        '''Count the number of phrases in the development.'''
        pass

 
# 
# 
#     1.    Above G4 do higher pitches tend to be louder?
#     2.    Add explicit breath marks after each phrase.
#     3.    Add key velocities to some MIDI data that reflect accent levels arising from the meter.
#     4.    Align and display all of the bass lines for all of the variations concurrently.
#     5.    Alphabetize a list of titles.
#     6.    Amalgamate arpeggios into chords and display as notation.
#     7.    Annotate a score identifying possible cadential 6-4 chords.
#     8.    Are dynamic swells (crescendo-diminuendos) more common than dips (diminuendos-crescendos)?
#     9.    Are lower pitches likely to be shorter and higher pitches likely to be longer?
#     10.    Assemble individual parts into a full scores.
#     11.    Assemble syllables into words for some vocal text.
#     12.    Calculate all the permuted harmonic intervals in a chord.
#     13.    Calculate changes of listeners' heart-rate from physiological data.
#     14.    Calculate harmonic intervals between concurrent parts.
#     15.    Calculate harmonic intervals ignoring unisons.
#     16.    Calculate harmonic intervals in semitones.
#     17.    Calculate implied harmonic intervals between parts.
#     18.    Calculate melodic intervals not including intervals between the last note of one phrase and the first note of the next phrase.
#     19.    Calculate pitch-class sets for melodic passages segmented by rests.
#     20.    Calculate pitch-class sets for melodic passages segmented by slurs/phrases.
#     21.    Calculate the difference in duration between the recapitulation and the exposition.
#     22.    Calculate the interval vector for some set.
#     23.    Calculate the normal form for some set.
#     24.    Calculate the prime form for some set.
#     25.    Calculate the proportion of sonorities where both the oboe and bassoon are active.
#     26.    Change all pizzicato marks to spiccato marks.
#     27.    Change all up-stems in measures 34 through 38 to down-stems.
#     28.    Classify cadences as either authentic, plagal or deceptive.
#     29.    Classify flute fingering transitions as either easy, moderate, or difficult.
#     30.    Classify phonemes in a vocal text as fricatives, nasals, plosives, etc.
#     31.    Classify vocal vowels as front or back, higher or low.
#     32.    Compare Beethoven's use of dynamic marking with Brahms's.
#     33.    Compare orchestration patterns between the exposition and the development.
#     34.    Compare pitch-class sets used at the beginnings of slurs/phrases versus those used at the ends of slurs/phrases.
#     35.    Compare the average overall dynamic level between the exposition and development sections.
#     36.    Compare the estimated keys for the 2nd theme in the exposition versus the 2nd theme in the recapitulation.
#     37.    Compare the first phrase of the Exposition with the first phrase of the Recapitulation.
#     38.    Compare the number of syllables in the first and second verses.
#     39.    Contrast the sonorities that occur on the first versus the third beats in a waltz repertory.
#     40.    Count how many measures contain at least one trill.
#     41.    Count the number of ascending major sixth intervals that occur in phrases that end on the dominant.
#     42.    Count the number of barlines in a work.
#     43.    Count the number of closed-position chords.
#     44.    Count the number of harmonic functions in each phrase.
#     45.    Count the number of notes in a work that belong to the same whole-tone set.
#     46.    Count the number of notes in measures 8 to 16.
#     47.    Count the number of notes in the exposition.
#     48.    Count the number of phrases in a score.
#     49.    Count the number of phrases in each work containing `Liebe' in the title.
#     50.    Count the number of phrases in the development.
#     51.    Count the number of phrases that begin on the subdominant pitch.
#     52.    Count the number of phrases that end on the subdominant pitch.
#     53.    Count the number of sonorities where the oboe and bassoon sound concurrently.
#     54.    Count the number of subdominant pitches in the soprano voice that are approached by rising thirds or sixths and that coincide with a dominant seventh chord.
#     55.    Count the number of tonic pitches that are approached by a weak-to-strong context versus the number of tonic pitches approached by a strong-to-weak context.
#     56.    Count the number of works by various composers.
#     57.    Count the proportion of phrase endings in music by Alban Berg where the phrase ends on either a major or minor chord.
#     58.    Create an inventory of three-note long/short duration patterns.
#     59.    Determine fret-board patterns that are similar to some specified finger combination.
#     60.    Determine how frequently ascending melodic leaps are followed by descending steps.
#     61.    Determine how much longer a passage is when all the repeats are played.
#     62.    Determine how often a pitch is followed immediately by the same pitch.
#     63.    Determine how often both the oboe and bassoon are inactive.
#     64.    Determine the average semitone distance separating the cantus and altus voices in Lassus.
#     65.    Determine the complement for some pitch-class set.
#     66.    Determine the frequency of light-related words in the monastic offices for Thomas of Canterbury.
#     67.    Determine the highest note in the trumpet part in measure 29.
#     68.    Determine the longest duration of a note that is marked staccato.
#     69.    Determine the most common rhythmic pattern spanning a measure.
#     70.    Determine the most frequently used dynamic marking in Beethoven.
#     71.    Determine the predominant vowel height in a vocal text.
#     72.    Determine the rhyme scheme for some vocal text.
#     73.    Determine the total amount of time the trumpet plays.
#     74.    Determine the total duration of a work for a given metronome marking.
#     75.    Determine the total nominal duration of Gould's performance of a work.
#     76.    Determine what transposition of a clarinet melody minimizes the number of tones in the throat register.
#     77.    Determine whether 90 percent of the notes in a work by Bach use just two durations (such as eighths and sixteenths).
#     78.    Determine whether a composer uses B-A-C-H more often than would be expected by chance.
#     79.    Determine whether a work tends to begin quietly and end loudly, or vice versa.
#     80.    Determine whether any arpeggios form an augmented sixth chord.
#     81.    Determine whether Bach tends to avoid or prefer augmented eleventh harmonic intervals.
#     82.    Determine whether Bartok's articulation marks changed over his career.
#     83.    Determine whether Beethoven tends to link activity in the chalemeau register of the clarinet with low register activity in the strings.
#     84.    Determine whether descending melodic seconds are more common than ascending seconds.
#     85.    Determine whether descending minor seconds are more likely to be fah-mi or doh-ti.
#     86.    Determine whether flats are more common than sharps in Monteverdi.
#     87.    Determine whether German drinking songs are more likely to be in triple meter.
#     88.    Determine whether Haydn tends to avoid V-IV progressions.
#     89.    Determine whether high pitches tend to have longer durations than low pitches.
#     90.    Determine whether Liszt uses a greater variety of harmonies than does Chopin.
#     91.    Determine whether Monteverdi used roughly equivalent numbers of sharps and flats.
#     92.    Determine whether notes at the ends of phrases tend to be longer than notes at the beginnings of phrases.
#     93.    Determine whether Schoenberg tended to use simultaneities that have more semitone relations and fewer tritone relations.
#     94.    Determine whether secondary dominants are more likely to occur on the third beat of triple meter works.
#     95.    Determine whether semitone trills tend to be longer or shorter than whole-tone trills.
#     96.    Determine whether submediant chords are more likely to be approached in a strong-to-weak or weak-to-strong rhythmic context.
#     97.    Determine whether the first pitch in a phrase is lower than the last pitch in the phrase.
#     98.    Determine whether the initial phrase in a work tends to be shorter than the final phrase.
#     99.    Determine whether the subdominant pitch is used less often in pop melodies than in French chanson.
#     100.    Determine whether the words `high,' `hoch,' or `haut' tend to coincide with higher pitches in a vocal work.
#     101.    Determine whether there are any notes in the bassoon part.
#     102.    Determine whether tonic pitches tend to be followed by a greater variety of melodic intervals than precedes it.
#     103.    Determine whether two works have similar vocabularies for their vocal texts.
#     104.    Determine which English translation of a Schubert text best preserves the vowel coloration.
#                Use CMU Dict -- IPA dictionary.
#     105.    Determine which of two MIDI performances exhibits more dynamic range.
#     106.    Display lyrics with new lines indicated by punctuation.
#     107.    Display the MIDI data while performing.
#     108.    Do lower pitches tend to be quieter and higher pitches tend to be louder?
#     109.    Eliminate all data apart from beaming information.
#     110.    Eliminate all measure numbers.
#     111.    Estimate the amount of difference between two vocal texts.
#     112.    Estimate the degree of concrete/abstract language use for some vocal text.
#     113.    Estimate the degree of emotionality for some vocal text.
#     114.    Estimate the sensory dissonance evoked by some frequency spectrum.
#     115.    Expand all the verses for a strophic song.
#     116.    Expand repeats to a `through-composed' version of the score.
#     117.    Extract anacrusis material and the final measure from two scores.
#     118.    Extract and transpose the trumpet part to concert pitch.
#     119.    Extract any transposing instruments.
#     120.    Extract measure 27.
#     121.    Extract measures 10 to 20 in both of two scores.
#     122.    Extract measures 114 to 183 from a score.
#     123.    Extract the 'cello, oboe and flauto dolce parts.
#     124.    Extract the anacrusis material before the first barline.
#     125.    Extract the bass and soprano parts.
#     126.    Extract the bassoon part.
#     127.    Extract the coda section from a score.
#     128.    Extract the Erk edition.
#     129.    Extract the figured bass for the third recitative.
#     130.    Extract the first 20 sonorities of the last 30 sonorities.
#     131.    Extract the first and last notes of all phrases.
#     132.    Extract the first and third sonority following some marker.
#     133.    Extract the first four and last four phrases from a score.
#     134.    Extract the first four measures from the Trio section.
#     135.    Extract the first four phrases from a score.
#     136.    Extract the German text only from a score.
#     137.    Extract the lyrics for the third verse.
#     138.    Extract the material from Rehearsal Markings 5 to 7.
#     139.    Extract the MIDI data.
#     140.    Extract the recapitulation from a score.
#     141.    Extract the ripieno parts.
#     142.    Extract the second instance of the first theme.
#     143.    Extract the second theme from a score.
#     144.    Extract the second theme from the recapitulation.
#     145.    Extract the second-last phrase from a score.
#     146.    Extract the shamisen and shakuhachi parts.
#     147.    Extract the string parts and the oboe part.
#     148.    Extract the tenor part from a score.
#     149.    Extract the Trio section from a score.
#     150.    Extract the upper-most part.
#     151.    Extract the vocal parts.
#     152.    Extract the vocal text from a score.
#     153.    Extract the woodwind parts from a score.
#     154.    Find all 18th century works that include French horns and oboes.
#     155.    Find all Corelli works that contain a change of meter.
#     156.    Find all heterophonic works.
#     157.    Find all jazz works designated `bebop' in style.
#     158.    Find all Rondo movements.
#     159.    Find all scores composed by Cesar Franck.
#     160.    Find all scores containing one or more brass instruments.
#     161.    Find all scores containing passages in 7/8 meter.
#     162.    Find all scores containing passages in any minor key.
#     163.    Find all scores containing passages in C major.
#     164.    Find all scores containing pitch-class data.
#     165.    Find all scores written in compound meters.
#     166.    Find all woodwind quintets in compound meters that contain a change of key.
#     167.    Find all works composed between 1805 and 1809.
#     168.    Find all works that contain a change of key and a change of meter.
#     169.    Find all works that contain a change of key.
#     170.    Find other works that have the same instrumentation as a given work.
#     171.    For some flute work, compare fingering transitions for pre-Boehm and modern instruments.
#     172.    Generate a concordance of lyrics for some vocal corpus.
#     173.    Generate a list of all composers for some group of scores.
#     174.    Generate a list of instrumentations for some group of scores.
#     175.    Generate a list of titles for some group of scores.
#     176.    Generate a list of words used in some song.
#     177.    Generate a prime transposition for some tone-row.
#     178.    Generate a set matrix for a given tone row.
#     179.    Generate a standard MIDI file.
#     180.    Generate an inventory of pitch-class sets for melodic passages segmented into groups of three pitches.
#     181.    Generate an inventory of the patterns of stressed/unstressed syllables for some work.
#     182.    Generate an inversion for some tone-row.
#     183.    Group notes together by their beaming.
#     184.    Identify all D major triads in a work.
#     185.    Identify all encoded 17th century organ works in 6/8 meter.
#     186.    Identify all encoded 17th century organ works that do not contain passages in 6/8 meter.
#     187.    Identify all encoded works that were written in the 17th century, or were written for organ, or were written in 6/8 meter.
#     188.    Identify all meter signatures in a score.
#     189.    Identify all scores containing a tuba but not a trumpet.
#     190.    Identify all works not in the keys of C major, G major, B-flat major or D minor.
#     191.    Identify all works that are in compound meters, but not quadruple compound.
#     192.    Identify all works that end with a `tierce de picardie'.
#     193.    Identify alliterations in a vocal text.
#     194.    Identify any augmented sixth chords.
#     195.    Identify any augmented sixth intervals in Bach's two-part inventions.
#     196.    Identify any compound melodic intervals.
#     197.    Identify any cross-relations.
#     198.    Identify any differences between two vocal texts.
#     199.    Identify any diminished octave intervals in Beethoven's piano sonatas.
#     200.    Identify any eighth-notes that contain at least one flat and whose pitch lies within an octave of middle C.
#     201.    Identify any French sixth chords.
#     202.    Identify any German sixth chords.
#     203.    Identify any Italian sixth chords.
#     204.    Identify any Landini cadences.
#     205.    Identify any major or minor ninths melodic intervals.
#     206.    Identify any melody that contains both an ascending and descending major sixth interval.
#     207.    Identify any Neapolitan sixth chord that is missing the fifth of the chord.
#     208.    Identify any Neapolitan sixth chords spelled enharmonically on the raised tonic.
#     209.    Identify any Neapolitan sixth chords.
#     210.    Identify any subdominant chords between measures 80 and 86.
#     211.    Identify any tritone intervals that are not spelled as augmented fourths or diminished fifths.
#     212.    Identify any works that are classified as `Ballads'.
#     213.    Identify any works that are in irregular meters.
#     214.    Identify any works that are in simple triple meters.
#     215.    Identify any works that are not composed by Schumann.
#     216.    Identify any works that bear a dedication.
#     217.    Identify any works that contain passages in 9/8 meter.
#     218.    Identify any works that contain passages in either 3/8 or 9/8 meter.
#     219.    Identify any works that contain the word `Amour' in the title.
#     220.    Identify any works that contain the words `Drei' and `Koenige'.
#     221.    Identify any works that contain the words `Liebe' and `Tod' in the title.
#     222.    Identify any works that don't contain any double barlines.
#     223.    Identify any works whose instrumentation includes a cornet but not a trumpet.
#     224.    Identify any works whose instrumentation includes a trumpet and a cornet.
#     225.    Identify any works whose instrumentation includes a trumpet.
#     226.    Identify consecutive fifths or octaves.
#     227.    Identify doubled leading tones.
#     228.    Identify exposed octave.
#     229.    Identify crossing of parts.
#     230.    Identify overlapping of parts.
#     231.    Identify how frequently the dominant pitch occurs in the horn parts.
#     232.    Identify how often a high subdominant note in a long-short-long rhythm is followed by a low submediant in a long-long-short context.
#     233.    Identify how often the flute is resting when the trumpet is active.
#     234.    Identify how the melodic intervals in measures 8 to 32.
#     235.    Identify melodic intervals (avoiding intervals spanning rests).
#     236.    Identify overlapped parts.
#     237.    Identify parts that are out of range.
#     238.    Identify parts that are separated by more than an octave.
#     239.    Identify parts that move by augmented or diminished intervals.
#     240.    Identify possible recapitulation passages.
#     241.    Identify possible sonata-allegro movements.
#     242.    Identify progressions that are similar to II-IV-V-I.
#     243.    Identify similes using `like' or `as' in some vocal text.
#     244.    Identify the available versions of a score.
#     245.    Identify the average overall dynamic level for a work.
#     246.    Identify the crossing of parts.
#     247.    Identify the duration of the longest note marked staccato.
#     248.    Identify the highest note in a score.
#     249.    Identify the key signatures for all African works written in 3/4 meter.
#     250.    Identify the longest note in a score.
#     251.    Identify the longest run of ascending intervals in some melody.
#     252.    Identify the lowest note in a score.
#     253.    Identify the maximum number of voices in a score.
#     254.    Identify the most common harmonic interval arrangement in some score.
#     255.    Identify the most common harmonic progression apart from the V-I progression.
#     256.    Identify the most common sequence of five melodic intervals.
#     257.    Identify the most common word following `gloria' in Gregorian chants.
#     258.    Identify the number of notes per syllable for some score.
#     259.    Identify the number of notes per word for some score.
#     260.    Identify the number of syllables per phrase for some work.
#     261.    Identify the pitch-class sets used for vertical sonorities.
#     262.    Identify the proportion of intervals formed by the oboe and flute notes that are doubled.
#     263.    Identify the proportion of intervals formed by the oboe and flute notes that are doubled.
#     264.    Identify the shortest note in a score.
#     265.    Identify the stressed/unstressed pattern of syllables for some work.
#     266.    Identify those measures containing a ii-IV progression that were preceded by a iii-V progression in the previous measure.
#     267.    Identify those measures containing a iii-V progression.
#     268.    Identify those notes that begin a phrase, but are not rests.
#     269.    Identify two or more consecutive ascending major thirds in some melody.
#     270.    Identify unison doublings.
#     271.    Identify what harmonic intervals precede the interval of an octave.
#     272.    Identify what scale degree most commonly precedes the dominant pitch.
#     273.    Identify whether a score contains an `Andante' section.
#     274.    Identify whether a score contains any double sharps.
#     275.    Identify whether any score contains an `Andante' section.
#     276.    Identify whether drinking songs are more apt to be in triple meter.
#     277.    Identify whether dynamics are gradual or terraced.
#     278.    Identify whether large leaps involving chromatically-altered tones tend to have longer durations on the altered tone.
#     279.    Identify whether the dominant is more commonly approached from above or from below.
#     280.    Identify whether the subdominant occurs more frequently in one repertory than another.
#     281.    Identify whether there are any tritone melodic intervals in the vocal parts.
#     282.    Identify whether titles containing the word `death' or more likely to be in minor keys.
#     283.    Identify whether two songs have identical lyrics.
#     284.    Identify whether two works are identical apart from transposition.
#     285.    Identify whether two works have identical harmonies.
#     286.    Identify whether two works have identical rhythmic structures.
#     287.    Identify whether two works have the same instrumentation.
#     288.    Identify whether two works have the same key transitions.
#     289.    Identify which Bach chorale harmonizations have the same titles.
#     290.    Identify which composer has the most works.
#     291.    Identify which instrument is least likely to be playing when the woodwinds are active.
#     292.    Identify which works differ in instrumentation from other works.
#     293.    Identify which works have essentially the same vocal texts.
#     294.    Isolate all sonorities played on off-beats by the horns.
#     295.    Isolate all sonorities that occur on the fourth beat.
#     296.    Join three isolated measures into a single passage.
#     297.    Join three movements into a single score.
#     298.    Locate all instances of consecutive fifths.
#     299.    Locate all tritones in a score.
#     300.    Locate and identify all tone-row variants in a 12-tone work.
#     301.    Locate any beams that cross over phrase boundaries.
#     302.    Locate any double sharps in a score.
#     303.    Locate any doubled seventh scale degrees.
#     304.    Locate any parallel fifths between the bass and alto voices.
#     305.    Locate instances of the pitch sequence D-S-C-H in Shostakovich's music.
#     306.    Locate occurences of the word `Liebe' in some lyrics.
#     307.    Locate submediant pitches that are approached by an ascending major third followed by a descending major second.
#     308.    Locate the most emotionally charged words in some vocal text.
#     309.    Mark all instances of deceptive cadences.
#     310.    Measure the similarity of pitch motion between two parts.
#     311.    Modify a score so the durations are in diminution.
#     312.    Perform the first three measures from the second section of a binary form work.
#     313.    Play a melody but eliminate all tonic pitches.
#     314.    Play a melody but replace all tonic pitches by rests.
#     315.    Play just the rhythm of a work.
#     316.    Play some MIDI data from the `second theme'.
#     317.    Play some MIDI data.
#     318.    Play the clarinet part for the 4th and 8th phrases.
#     319.    Play the first and last measures from the Coda section at half tempo.
#     320.    Play the MIDI data at half tempo.
#     321.    Play the MIDI data from the next diminished octave.
#     322.    Play the MIDI data from the next G#.
#     323.    Play the MIDI data from the next pause.
#     324.    Play the thema and first variation at the same time.
#     325.    Play the `Trio' section.
#     326.    Print a transposed version of the accompaniment parts.
#     327.    Rearrange a score so the measures are in reverse order.
#     328.    Renumber all measures in a score.
#     329.    Scan a melody for passages that are similar in rhythm and pitch-contour to a given theme.
#     330.    Scan a melody for pitch motions that are similar to a given theme.
#     331.    Search for text phrases in the lyrics to some song.
#     332.    Select the Landowska version of a score.
#     333.    Shift the serial order of some series of dynamics, durations or articulation marks.
#     334.    Shift the serial order of some series of pitches.
#     335.    Transform a spectrum to take into account the effects of masking.
#     336.    Translate a Humdrum score to Csound for digital sound synthesis.
#     337.    Translate a pitch representation to standardized enharmonic pitch spelling.
#     338.    Translate a work to pitch-class representation.
#     339.    Translate to cents representation.
#     340.    Translate to French solfege representation.
#     341.    Translate to frequency representation.
#     342.    Translate to German pitch representation.
#     343.    Translate to International Standards Association pitch representation.
#     344.    Translate to MIDI representation.
#     345.    Translate to scale degree representation.
#     346.    Translate to semitone representation.
#     347.    Transpose down an augmented unison.
#     348.    Transpose enharmonically from F-sharp to G-flat.
#     349.    Transpose from one key to another.
#     350.    Transpose to Dorian mode.
#     351.    Transpose up a minor third.
#





#-------------------------------------------------------------------------------



if __name__ == "__main__":
    import music21
    music21.mainTest(Test)




#------------------------------------------------------------------------------
# eof

