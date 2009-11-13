import music21
import cadencebook
from music21 import note
from music21.note import Accidental
from music21.interval import *
from music21 import twoStreams
from music21.twoStreams import TwoStreamComparer
from music21 import lily

debug = True

RULEONE   = 1
RULETWO   = 2
RULETHREE = 4
RULEFOURA = 8
RULEFOURB = 16

def capuaRuleOne(stream):
    '''Applies Capua's first rule to the given stream, i.e. if a line descends
    a major second then ascends back to the original note, the major second is
    made into a minor second. Also copies the relevant accidentals into
    note.editorial.misc under "saved-accidental" and changes note.editorial.color
    for rule 1 (blue green blue).'''
    for i in range(0, len(stream.notes)-2):
        n1 = stream.notes[i]
        n2 = stream.notes[i+1]
        n3 = stream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue
        
        i1 = generateInterval(n1,n2)
        i2 = generateInterval(n2,n3)

        if n1.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        ## e.g. G, F, G => G, F#, G
        if i1.directedName == "M-2" and \
           i2.directedName == "M2":
            if (n2.editorial.misc.has_key("capua")):
                n2.editorial.misc['capua'] += RULEONE
            else:
                n2.editorial.misc['capua'] = RULEONE
            if (n2.accidental is not None and n2.accidental.name == "flat"):
                n2.editorial.misc["saved-accidental"] = n2.accidental
                n2.accidental = None
                n2.editorial.ficta = Accidental("natural")
                n2.editorial.misc["capua-ficta"] = Accidental("natural")
                n1.editorial.color = "blue"
                n2.editorial.color = "green"
                n3.editorial.color = "blue"
            else:
                n2.editorial.ficta = Accidental("sharp")
                n2.editorial.misc["capua-ficta"] = Accidental("sharp")
                n1.editorial.color = "blue"
                n2.editorial.color = "green"
                n3.editorial.color = "blue"

def capuaRuleTwo(stream):
    '''Applies Capua's second rule to the given stream, i.e. if four notes are
    ascending with the pattern M2 m2 M2, the intervals shall be made M2 M2 m2.
    Also changes note.editorial.color for rule 2 (yellow yellow green yellow).'''
    for i in range(0, len(stream.notes)-3):
        n1 = stream.notes[i]
        n2 = stream.notes[i+1]
        n3 = stream.notes[i+2]
        n4 = stream.notes[i+3]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest or \
           n4.isRest:
            continue

        i1 = generateInterval(n1,n2)
        i2 = generateInterval(n2,n3)
        i3 = generateInterval(n3,n4)

        if n1.accidental is not None or \
           n2.accidental is not None or \
           n4.accidental is not None:
            continue

        ### never seems to improve things...
        if n3.step == "A" or n3.step == "D":
            continue

        # e.g., D E F G => D E F# G
        #    or F A Bb C => F A B C
        if i1.directedName == "M2" and \
           i2.directedName == "m2" and \
           i3.directedName == "M2":
            if (n3.editorial.misc.has_key("capua")):
                n3.editorial.misc['capua'] += RULETWO
            else:
                n3.editorial.misc['capua'] = RULETWO

            if (n3.accidental is not None and n3.accidental.name == "flat"):
                n3.editorial.misc["saved-accidental"] = n3.accidental
                n3.accidental = None
                n3.editorial.ficta = Accidental("natural")
                n3.editorial.misc["capua-ficta"] = Accidental("natural")
                n1.editorial.color = "yellow"
                n2.editorial.color = "yellow"
                n3.editorial.color = "green"
                n4.editorial.color = "yellow"
            else:
                n3.editorial.ficta = Accidental("sharp")
                n3.editorial.misc["capua-ficta"] = Accidental("sharp")
                n1.editorial.color = "yellow"
                n2.editorial.color = "yellow"
                n3.editorial.color = "green"
                n4.editorial.color = "yellow"

def capuaRuleThree(stream):
    '''Applies Capua's third rule to the given stream, i.e. if there is a
    descending major third followed by an ascending major second, the second
    note will be made a half-step higher so that there is a descending minor
    third followed by an ascending minor second. Also changes
    note.editorial.color for rule 3 (green pink green).'''
    for i in range(0, len(stream.notes)-2):
        n1 = stream.notes[i]
        n2 = stream.notes[i+1]
        n3 = stream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue
        
        i1 = generateInterval(n1,n2)
        i2 = generateInterval(n2,n3)

        if n1.accidental is not None or \
           n2.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        # e.g., E C D => E C# D
        if i1.directedName  == "M-3" and \
           i2.directedName  == "M2":
            if (n2.editorial.misc.has_key("capua")):
                n2.editorial.misc['capua'] += RULETHREE
            else:
                n2.editorial.misc['capua'] = RULETHREE
            n2.editorial.ficta = Accidental("sharp")
            n2.editorial.misc["capua-ficta"] = Accidental("sharp")
            n1.editorial.color = "pink"
            n2.editorial.color = "green"
            n3.editorial.color = "pink"

def capuaRuleFourA(stream):
    '''Applies one interpretation of Capua's fourth rule to the given stream,
    i.e. if a descending minor third is followed by a descending major second,
    the intervals will be changed to a major third followed by a minor second.
    Also changes note.editorial.color for rule 4 (orange green orange).'''
    for i in range(0, len(stream.notes)-2):
        n1 = stream.notes[i]
        n2 = stream.notes[i+1]
        n3 = stream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue
        
        i1 = generateInterval(n1,n2)
        i2 = generateInterval(n2,n3)

        if n1.accidental is not None or \
           n2.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        # e.g., D B A => D Bb A
        if i1.directedName  == "m-3" and \
           i2.directedName  == "M2":
            if (n2.editorial.misc.has_key("capua")):
                n2.editorial.misc['capua'] += RULEFOURA
            else:
                n2.editorial.misc['capua'] = RULEFOURA
            n2.editorial.ficta = Accidental("flat")
            n2.editorial.misc["capua-ficta"] = Accidental("flat")
            n1.editorial.color = "orange"
            n2.editorial.color = "green"
            n3.editorial.color = "orange"

def capuaRuleFourB(stream):
    '''Applies more probable interpretation of Capua's fourth rule to the given
    stream, i.e. if a descending minor third is followed by a descending major
    second, the intervals will be changed to a major third followed by a minor
    second. Also copies any relevant accidental to note.editorial.misc under
    "saved-accidental" and changes note.editorial.color for rule 4 (orange
    green orange).'''
    for i in range(0, len(stream.notes)-2):
        n1 = stream.notes[i]
        n2 = stream.notes[i+1]
        n3 = stream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue

        i1 = generateInterval(n1,n2)
        i2 = generateInterval(n2,n3)

        if n1.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        # e.g., D F G => D F# G  or G Bb C => G B C
        if i1.directedName  == "m3" and \
           i2.directedName  == "M2":
            if (n2.editorial.misc.has_key("capua")):
                n2.editorial.misc['capua'] += RULEFOURB
            else:
                n2.editorial.misc['capua'] = RULEFOURB
            if (n2.accidental is not None and n2.accidental.name == "flat"):
                n2.editorial.misc["saved-accidental"] = n2.accidental
                n2.accidental = None
                n2.editorial.ficta = Accidental("natural")
                n2.editorial.misc["capua-ficta"] = Accidental("natural")
                n1.editorial.color = "orange"
                n2.editorial.color = "green"
                n3.editorial.color = "orange"
            else:
                n2.editorial.ficta = Accidental("sharp")
                n2.editorial.misc["capua-ficta"] = Accidental("sharp")
                n1.editorial.color = "orange"
                n2.editorial.color = "green"
                n3.editorial.color = "orange"

def clearFicta(stream1):
    '''In the given stream, moves anything under note.editorial.ficta into
    note.editorial.misc under "saved-ficta".'''

    for n2 in stream1:
        if  n2.editorial.ficta is not None:
            n2.editorial.misc["saved-ficta"] = n2.editorial.ficta
        n2.editorial.ficta = None   

def restoreFicta(stream1):
    '''In the given stream, moves anything under note.editorial.misc["saved-ficta"]
    back to note.editorial.ficta.'''
    for n2 in stream1:
        if  n2.editorial.misc.has_key("saved-ficta"):
            n2.editorial.ficta = n2.editorial.misc["saved-ficta"]
            n2.editorial.misc["saved-ficta"] = None

def clearAccidental(note1):
    '''moves the accidental to \'saved-accidental\' and clears note.accidental'''
    if note1.accidental is not None:
        note1.editorial.misc["saved-accidental"] = note1.accidental
        note1.accidental = None

def restoreAccidental(note1):
    '''takes note.editorial.music[\'saved-accidental\'] and moves it back to the note'''
    if  note1.editorial.misc.has_key("saved-accidental"):
        note1.accidental = note1.editorial.misc["saved-accidental"]
        note1.editorial.misc["saved-accidental"] = None

def fictaToAccidental(note1):
    '''Moves the ficta (if any) to the accidental'''
    if note1.editorial.ficta is not None:
        if note1.accidental is not None:
            clearAccidental(note1)
        note1.accidental = note1.editorial.ficta

def pmfcFictaToAccidental(note1):
    '''Moves PMFC's ficta to the accidental'''
    if note1.editorial.misc.has_key("pmfc-ficta") and \
       note1.editorial.misc["pmfc-ficta"] is not None:
        if note1.accidental is not None:
            note1.editorial.misc["saved-accidental"] = note1.accidental
        note1.accidental = note1.editorial.misc["pmfc-ficta"]
        
def capuaFictaToAccidental(note1):
    '''Moves Capua's ficta to the accidental'''
    if note1.editorial.misc.has_key("capua-ficta") and \
       note1.editorial.misc["capua-ficta"] is not None:
        if note1.accidental is not None:
            note1.editorial.misc["saved-accidental"] = note1.accidental
        note1.accidental = note1.editorial.misc["capua-ficta"]

def runRulesOnStream(stream1):
    '''runs clearFicta and then each of the four Capua rules on the stream (4b not 4a)'''
    clearFicta(stream1)
    capuaRuleOne(stream1)
    capuaRuleTwo(stream1)
    capuaRuleThree(stream1)
#    capuaRuleFourA(stream1)
    capuaRuleFourB(stream1)

def evaluateCapuaRules(stream1, stream2):
    '''Runs evaluation method for capua on one stream only, and evaluating harmonies,
    for each stream; then runs method for applying capua rules to both and evaluating
    the resulting harmonies.''' #Returns SOMETHING USEFUL TO BE DETERMINED
    stream1Count = evaluateCapuaOneStream(stream1, stream2)
    stream2Count = evaluateCapuaOneStream(stream2, stream1)
    bothCount = evaluateCapuaTwoStreams(stream1, stream2)
    #do something with them...
    return bothCount

def evaluateCapuaOneStream(stream1, stream2):
    '''Runs Capua rules on one stream only and evaluates the harmonies; stores harmonies
    under "capua1FictaHarmony" in note.editorial.misc; returns a list of the number of
    [perfect cons, imperfect cons, dissonances].'''
    runRulesOnStream(stream1)
    for note1 in stream1:
        capuaFictaToAccidental(note1)
    stream1Count = compareOneStream(stream1, stream2, "capua1stream")
    for note1 in stream1:
        restoreAccidental(note1)
    return stream1Count

def evaluateCapuaTwoStreams(stream1, stream2):
    '''Runs Capua rules on both streams and evaluates the harmonies; stores harmonies
    under "capua2FictaHarmony" in note.editorial.misc; returns a dictionary that contains
    the number of [perfect cons, imperfect cons, dissonances] for each stream, which can
    be obtained with keys "stream1Count" and "stream2Count".'''
    runRulesOnStream(stream1)
    runRulesOnStream(stream2)
    for note1 in stream1:
        capuaFictaToAccidental(note1)
    for note2 in stream2:
        capuaFictaToAccidental(note2)
    stream1Count = compareOneStream(stream1, stream2, "capua2stream")
    stream2Count = compareOneStream(stream2, stream1, "capua2stream")
    for note1 in stream1:
        restoreAccidental(note1)
    for note2 in stream2:
        restoreAccidental(note2)
    bothCount = {}
    bothCount["stream1Count"] = stream1Count
    bothCount["stream2Count"] = stream2Count
    return bothCount

def evaluateEditorsFicta(stream1, stream2):
    '''Runs pmfcFictaToAccidental, then runs the evaluation method on the two streams.
    Returns editorProfile, a list of lists with the number of perfect cons, imperfect
    cons, and dissonances for each stream.'''
    for note1 in stream1:
        pmfcFictaToAccidental(note1)
    for note2 in stream2:
        pmfcFictaToAccidental(note2)
    editorProfile = evaluateHarmony(stream1, stream2, "editor")
    for note1 in stream1:
        restoreAccidental(note1)
    for note2 in stream2:
        restoreAccidental(note2)
    return editorProfile

def evaluateWithoutFicta(stream1, stream2):
    '''Clears all ficta, then evaluates the harmonies of the two streams. Returns
    a list of lists of the interval counts for each '''
    clearFicta(stream1) #probably not necessary to clear ficta, but just to be safe
    clearFicta(stream2)
    noneProfile1 = compareOneStream(stream1, stream2, None)
    noneProfile2 = compareOneStream(stream2, stream1, None)
    restoreFicta(stream1)
    restoreFicta(stream2)
    return noneProfile1



PerfectCons = ["P1", "P5", "P8"]
ImperfCons  = ["m3", "M3", "m6", "M6"]
Others      = ["m2", "M2", "A2", "d3", "A3", "d4", "P4", "A4", "d5", "A5", "d6",
               "A6", "d7", "m7", "M7", "A7"]

PERFCONS = 1
IMPERFCONS = 2
OTHERS = 3

def compareThreeFictas(stream1, stream2):
    noficta = {}
    pmfcficta = {}
    capuaficta = {}

    for i in (PerfectCons + ImperfCons + Others):
        noficta[i] = 0
        pmfcficta[i] = 0
        capuaficta[i] = 0

    ### populates the editorial.interval attribute on each note
    twoStream1 = TwoStreamComparer(stream1, stream2)
    twoStream1.intervalToOtherStreamWhenAttacked()

    for note1 in stream1.notes:
        if note1.editorial.misc.has_key("pmfc-ficta") or \
           note1.editorial.misc.has_key("capua-ficta"):
            normalInterval = note1.editorial.harmonicInterval.name
            if note1.editorial.misc.has_key("pmfc-ficta"):
                pmfcFictaToAccidental(note1)
                note1.editorial.harmonicInterval.reinit()
                pmfcInterval = note1.editorial.harmonicInterval.name
            else:
                pmfcInterval = ""
            if note1.editorial.misc.has_key("capua-ficta"):
                capuaFictaToAccidental(note1)
                note1.editorial.harmonicInterval.reinit()
                capuaInterval = note1.editorial.harmonicInterval.name
            else:
                capuaInterval = ""
            restoreAccidental(note1)
            print ("N: " + normalInterval, "P: " + pmfcInterval, "C: " +capuaInterval)

def compareStreamCapuaToEditor(stream1):
    totalDict = {
        'totalNotes': 0,
        'pmfcAlt': 0,
        'capuaAlt': 0,
        'pmfcNotCapua': 0,
        'capuaNotPmfc': 0,
        'pmfcAndCapua': 0,
        }
    for note1 in stream1.notes:
        thisDict = compareNoteCapuaToEditor(note1)
        for thisKey in thisDict.keys():
            totalDict[thisKey] += thisDict[thisKey]
    return totalDict

def compareNoteCapuaToEditor(note1):
    statsDict = {
        'totalNotes': 0,
        'pmfcAlt': 0,
        'capuaAlt': 0,
        'pmfcNotCapua': 0,
        'capuaNotPmfc': 0,
        'pmfcAndCapua': 0,
        }
    
    if note1.isRest:
        return {}
    statsDict['totalNotes'] += 1
    if note1.editorial.misc.has_key("pmfc-ficta") and \
           note1.editorial.misc.has_key("capua-ficta"):
        statsDict['pmfcAlt'] += 1
        statsDict['capuaAlt'] += 1
        statsDict['pmfcAndCapua'] += 1
    elif note1.editorial.misc.has_key("pmfc-ficta"):
        statsDict['pmfcAlt'] += 1
        statsDict['pmfcNotCapua'] += 1
        if note1.editorial.harmonicInterval:
            pass
            #print "In PMFC: " + note1.editorial.harmonicInterval.name
    elif note1.editorial.misc.has_key("capua-ficta"):
        statsDict['capuaAlt'] += 1
        statsDict['capuaNotPmfc'] += 1
        if note1.editorial.harmonicInterval:
            pass
            #print "In Capua: " + note1.editorial.harmonicInterval.name
    return statsDict

def compareOneStream(stream1, stream2, fictaType = "editor"):
    '''Helper function for evaluateHarmony that for each note in stream1 determines
    that notes starting interval in relation to stream2, and assigns identifiers to
    the fictaHarmony and fictaInterval in note.editorial if there is ficta, or to the
    noFictaHarmony if there is no ficta for that note. Returns a list of the number
    of perfect consonances, imperfect consonances, and other (dissonances) for stream1.
    For the fictaType variable, write "editor" or "capua", "capua1stream" or "capua2stream".'''
    twoStream1 = TwoStreamComparer(stream1, stream2)
    perfectConsCount = 0
    imperfConsCount = 0
    othersCount = 0

    ### populates the note.editorial.harmonicInterval object
    twoStream1.intervalToOtherStreamWhenAttacked()
    for note1 in stream1.notes:
        hasFicta = False
        interval1 = note1.editorial.harmonicInterval
        if interval1 is None:
            continue   # must have a rest in the other voice
        name1 = interval1.diatonic.name
        # read ficta as actual accidental
        if note1.editorial.ficta is not None:
            hasFicta = True

        iType = getIntervalType(interval1)
        if hasFicta and fictaType == "editor":
            if debug: print "found ficta of Editor type"
            note1.editorial.misc["editorFictaHarmony"] = iType
            note1.editorial.misc["editorFictaInterval"] = interval1 
        elif hasFicta and fictaType == "capua1stream":
            if debug: print "found ficta of capua1stream type"
            note1.editorial.misc["capua1FictaHarmony"] = iType
            note1.editorial.misc["capua1FictaInterval"] = interval1
        elif hasFicta and fictaType == "capua2stream":
            if debug: print "found ficta of capua2stream type"
            note1.editorial.misc["capua2FictaHarmony"] = iType
            note1.editorial.misc["capua2FictaInterval"] = interval1
        else:
            note1.editorial.misc["noFictaHarmony"] = iType

        if iType == "perfect cons":
            perfectConsCount += 1
        elif iType == "imperfect cons":
            imperfConsCount += 1
        elif iType == "dissonance":
            othersCount += 1
        else:
            raise("Hmmm.... I thought we already trapped this for errors...")
    return [perfectConsCount, imperfConsCount, othersCount]

def getIntervalType(interval1):
    '''returns either None (if interval is undef),  "perfect cons", "imperfect cons", "dissonance"
    or an error depending on how the interval fits into 14th century harmonic principles'''
    if interval1 is None:
        return None
    elif interval1.diatonic is None:
        return None
    elif interval1.diatonic.name in PerfectCons:
        return "perfect cons"
    elif interval1.diatonic.name in ImperfCons:
        return "imperfect cons"
    elif interval1.diatonic.name in Others:
        return "dissonance"
    else:
        raise("Wow!  The first " + interval1.niceName + " I have ever seen in 14th century music!  Go publish!  (or check for errors...)")
    
betterColor = "green"
worseColor = "red"
neutralColor = "blue"

##def compareAll(stream1, stream2):
##    # needs to evaluate fictaHarmony, noFictaHarmony to determine color of note,
##    # also evaluate counters for perfect, imperfect, and other intervals
##    pass

def colorCapuaFicta(stream1, stream2, oneOrBoth = "both"):
    '''Given two streams, applies the capua rules and colors each note (in
    note.editorial.misc under "ficta-color") as compared to the streams with no ficta,
    using betterColor, worseColor, and neutralColor.'''
    twoStreams1 = TwoStreamComparer(stream1, stream2)
    twoStreams1.intervalToOtherStreamWhenAttacked()
    capuaCount = evaluateCapuaRules(stream1, stream2)
    print capuaCount
    noFictaCount = evaluateWithoutFicta(stream1, stream2)
    print noFictaCount
    for note1 in stream1:
        colorNote(note1, oneOrBoth)
    for note2 in stream2:
        colorNote(note2, oneOrBoth)

def colorNote(note1, oneOrBoth = "both"):
    '''Applies all rules to a note according to what harmonies are better/worse/neutral.'''
    if not note1.editorial.misc.has_key("capua2FictaHarmony"): return
    elif oneOrBoth == "one": capuaHarmony = note1.editorial.misc["capua1FictaHarmony"]
    elif oneOrBoth == "both": capuaHarmony = note1.editorial.misc["capua2FictaHarmony"]
    else: raise("Please specify \"one\" or \"both\" for the variable \"oneOrBoth\".")
    nonCapuaHarmony = note1.editorial.misc["noFictaHarmony"]
    #nonCapuaHarmony = getIntervalType(nonCapuaInterval)
    ruleOne(nonCapuaHarmony, capuaHarmony)
    #ruleTwo(....), ruleThree(...), and so on

def ruleOne(nonCapuaHarmony, capuaHarmony):
    '''Colors a note based on the rule dissonance -> perfect cons is better,
    perfect cons -> dissonance is worse.'''
    if nonCapuaHarmony == "dissonance" and capuaHarmony == "perfect cons":
        note.editorial.misc["ficta-color"] = betterColor
        #can put the color somewhere else; I didn't want to step on the color-coded
        #capua rules
    elif nonCapuaHarmony == "perfect cons" and capuaHarmony == "dissonance":
        note.editorial.misc["ficta-color"] = worseColor

def runPiece(pieceNum = 258):  # random default piece...
    ballataObj = cadencebook.BallataSheet()
    pieceObj   = ballataObj.makeWork(pieceNum)
    cadenceA   = pieceObj.cadenceAClass()
    stream1    = cadenceA.streams[0]
    stream2    = cadenceA.streams[1]  ## ignore 3rd voice for now...

    twoStreams1 = twoStreams.TwoStreamComparer(stream1, stream2)
    twoStreams1.intervalToOtherStreamWhenAttacked()
    for note in stream1:
        if note.editorial.harmonicInterval is not None:
            print note.editorial.harmonicInterval.niceName

debug = True

def testCompare1():
    ballataObj = cadencebook.BallataSheet()
    totalDict = {
        'totalNotes': 0,
        'pmfcAlt': 0,
        'capuaAlt': 0,
        'pmfcNotCapua': 0,
        'capuaNotPmfc': 0,
        'pmfcAndCapua': 0,
        }

    for i in range(232, 349):  # most of Landini PMFC
        pieceObj   = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipit_c == "":
            continue
        print pieceObj.title
        cadenceA   = pieceObj.cadenceAClass()
        if len(cadenceA.streams) >= 2:
            stream1    = cadenceA.streams[0]
            stream2    = cadenceA.streams[1]  ## ignore 3rd voice for now...
            twoStreams1 = twoStreams.TwoStreamComparer(stream1, stream2)
            twoStreams1.intervalToOtherStreamWhenAttacked()
            runRulesOnStream(stream1)
            thisDict = compareStreamCapuaToEditor(stream1)
            for thisKey in thisDict.keys():
                totalDict[thisKey] += thisDict[thisKey]

    print totalDict

def correctedMaj3():
    '''Find all cases where a Major 3rd moves inward to unison (within the next two or three notes, excluding rests)
    and see how often the PMFC editors correct it to Minor 3 and how often Capua gets it'''

    lilyAll = lily.LilyString()
    
    ballataObj = cadencebook.BallataSheet()
    totalDict = {
        'totalNotes': 0,
        'pmfcAlt': 0,
        'capuaAlt': 0,
        'pmfcNotCapua': 0,
        'capuaNotPmfc': 0,
        'pmfcAndCapua': 0,
        'alterAll': 0
        }

    notesToCheck = 1 # next note only
    for i in range(2, 459): # all ballate
#    for i in range(232, 372):  # all of Landini ballate
        pieceObj   = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipitClass() is None:
            continue
        cadenceA   = pieceObj.cadenceAClass()
        if cadenceA is not None and len(cadenceA.streams) >= 2:
            stream1    = cadenceA.streams[0]
            stream2    = cadenceA.streams[1]  ## ignore 3rd voice for now...
            twoStreams1 = twoStreams.TwoStreamComparer(stream2, stream1)
            twoStreams1.intervalToOtherStreamWhenAttacked()
            runRulesOnStream(stream2)

            for note1 in stream2:
                if note1.editorial.harmonicInterval is None or \
                   note1.editorial.harmonicInterval.simpleName != "M3":
                    continue

                nextFewNotes = stream2.notesFollowingNote(note1, notesToCheck, allowRests = False)
                foundP8 = False
                for thisNote in nextFewNotes:
                    if thisNote is None:
                        raise Exception("This was only supposed to return non-None, what is up???")
                    if thisNote.editorial.harmonicInterval is None:
                        continue  ## probably a rest
                    if thisNote.editorial.harmonicInterval.simpleName == "P1":
                        foundP8 = True
                if foundP8 is False:
                    continue
                newResults = compareNoteCapuaToEditor(note1)
                newResults['alterAll'] = 1
                for thisKey in newResults.keys():
                    if thisKey == 'capuaNotPmfc' and newResults[thisKey] == 1:
                        lilyAll += cadenceA.lily()
                    totalDict[thisKey] += newResults[thisKey]
                
    print totalDict
    lilyAll.showPDF()

def correctedMin6():
    '''Find all cases where a minor 6th moves outward to octave (within the next three notes, excluding rests)
    and see how often the PMFC editors correct it to Major 6 and how often Capua gets it'''
    
    ballataObj = cadencebook.BallataSheet()
    totalDict = {
        'totalNotes': 0,
        'pmfcAlt': 0,
        'capuaAlt': 0,
        'pmfcNotCapua': 0,
        'capuaNotPmfc': 0,
        'pmfcAndCapua': 0,
        'alterAll': 0
        }

    notesToCheck = 2 # allows Landini cadences, but note much more
    lilyAll = lily.LilyString()

    for i in range(2, 459):  # all ballate   
#    for i in range(232, 373):  # all of Landini ballate
        print i
        pieceObj   = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipitClass is None:
            continue
        cadenceA   = pieceObj.cadenceAClass()
        if cadenceA is not None and len(cadenceA.streams) >= 2:
            stream1    = cadenceA.streams[0]
            stream2    = cadenceA.streams[1]  ## ignore 3rd voice for now...
            twoStreams1 = twoStreams.TwoStreamComparer(stream1, stream2)
            twoStreams1.intervalToOtherStreamWhenAttacked()
            runRulesOnStream(stream1)

            for note1 in stream1:
                if note1.editorial.harmonicInterval is None or \
                   note1.editorial.harmonicInterval.simpleName != "m6":
                    continue
                
                nextFewNotes = stream1.notesFollowingNote(note1, notesToCheck, allowRests = False)
                foundP8 = False
                for thisNote in nextFewNotes:
                    if thisNote is None:
                        raise Exception("This was only supposed to return non-None, what is up???")
                    if thisNote.editorial.harmonicInterval is None:
                        continue  ## probably a rest
                    if thisNote.editorial.harmonicInterval.semiSimpleName == "P8":
                        foundP8 = True
                if foundP8 is False:
                    continue
                newResults = compareNoteCapuaToEditor(note1)
                newResults['alterAll'] = 1
                for thisKey in newResults.keys():
                    if thisKey == 'capuaNotPmfc' and newResults[thisKey] == 1:
                        lilyAll += cadenceA.lily()
                    totalDict[thisKey] += newResults[thisKey]
                
    print totalDict
    lilyAll.showPDF()

def improvedHarmony():
    '''find how often an augmented or diminished interval was corrected to a perfect interval'''
    
    ballataObj = cadencebook.BallataSheet()

    checkDict = {
                 "perfIgnored": 0,
                 "perfCapua": 0, 
                 "imperfIgnored": 0, 
                 "imperfCapua": 0
                 }

    for i in range(2, 459):  # all ballate   
#    for i in range(232, 373):  # all of Landini ballate
        print i
        pieceObj   = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipitClass is None:
            continue
        
        for thisCadence in pieceObj.snippetBlocks:
            if thisCadence is not None and len(thisCadence.streams) >= 2:
                stream1    = thisCadence.streams[0]
                stream2    = thisCadence.streams[1]  ## ignore 3rd voice for now...
                twoStreams1 = twoStreams.TwoStreamComparer(stream1, stream2)
                try:
                    twoStreams1.intervalToOtherStreamWhenAttacked()
                except:
                    print "UGGGH ERROR!"
                    continue
                runRulesOnStream(stream1)
    
                for note1 in stream1:
                    hI = note1.editorial.harmonicInterval
                    if hI is None or \
                       hI.generic.perfectable is False or \
                       hI.generic.simpleUndirected == 4:
                        continue
    
                    #### KEEP PROGRAMMING FROM HERE
                    if hI.diatonic.specificName == "Perfect":
                        if note1.editorial.misc.has_key("capua-ficta"):
                            checkDict["perfCapua"] += 1  ## ugh Capua changed a P1, P5, or P8
                        else:
                            checkDict["perfIgnored"] +=1 ## yay Capua left it alone
                    else:
                        if note1.editorial.misc.has_key("capua-ficta"):
                            checkDict["imperfCapua"] += 1  ## yay Capua changed a A1 or d1, A5 or d5, or A8 or d8
                        else:
                            checkDict["imperfIgnored"] +=1 ## hrumph, Capua left it alone                                
                for note2 in stream2:
                    hI = note1.editorial.harmonicInterval
                    if hI is None or \
                       hI.generic.perfectable is False or \
                       hI.generic.simpleUndirected == 4:
                        continue
    
                    #### KEEP PROGRAMMING FROM HERE
                    if hI.diatonic.specificName == "Perfect":
                        if note1.editorial.misc.has_key("capua-ficta"):
                            checkDict["perfCapua"] += 1  ## ugh Capua changed a P1, P5, or P8
                        else:
                            checkDict["perfIgnored"] +=1 ## yay Capua left it alone
                    else:
                        if note1.editorial.misc.has_key("capua-ficta"):
                            checkDict["imperfCapua"] += 1  ## yay Capua changed a A1 or d1, A5 or d5, or A8 or d8
                        else:
                            checkDict["imperfIgnored"] +=1 ## hrumph, Capua left it alone                                

    print checkDict

def test():
    ballataObj = cadencebook.BallataSheet()
    pieceObj   = ballataObj.makeWork(20)  ## N.B. -- we now use Excel column numbers
    if pieceObj.incipitClass() is None:
        return None
    cadenceA   = pieceObj.cadenceAClass()
    if len(cadenceA.streams) >= 2:
        stream1    = cadenceA.streams[0]
        stream2    = cadenceA.streams[1]  ## ignore 3rd voice for now...
        twoStreams1 = twoStreams.TwoStreamComparer(stream1, stream2)
#    raise("hi?")
#    clearFicta(stream1)
#    compareThreeFictas(stream1, stream2)
#    scoreList = compareOneStream(stream1, stream2)
#    if debug == True:
#        for note in stream1:
#            print note.name
#            print note.editorial.ficta
#            print note.editorial.harmonicInterval.diatonic.name
#    restoreFicta(stream1)
#    print scoreList
    
if (__name__ == "__main__"):
#    test()
#    correctedMin6()
#    correctedMaj3()
    runPiece()
#    improvedHarmony()