import unittest

import music21
from music21.trecento import cadencebook
from music21 import note
from music21.note import Accidental
from music21.interval import notesToInterval
from music21 import lily

debug = True

RULE_ONE   = 1
RULE_TWO   = 2
RULE_THREE = 4
RULE_FOUR_A = 8
RULE_FOUR_B = 16

def applyCapua(thisWork):
    for thisSnippet in thisWork.snippets:
        applyCapuaSnippet(thisSnippet)

def applyCapuaSnippet(thisPolyphonicSnippet):
    for thisStream in thisPolyphonicSnippet.streams:
        applyCapuaStream(thisStream)

def applyCapuaStream(thisStream):
    clearFicta(thisStream)
    capuaRuleOne(thisStream)
    capuaRuleTwo(thisStream)
    capuaRuleThree(thisStream)
    capuaRuleFourB(thisStream)

## TODO: ruleTwoB


def capuaRuleOne(srcStream):
    '''Applies Nicolaus de Capua's first rule to the given srcStream, i.e. if a line descends
    a major second then ascends back to the original note, the major second is
    made into a minor second. Also copies the relevant accidentals into
    note.editorial.misc under "saved-accidental" and changes note.editorial.color
    for rule 1 (blue green blue).
    
    Returns the number of changes.    
    '''
    numChanged = 0
    
    for i in range(0, len(srcStream.notes)-2):
        n1 = srcStream.notes[i]
        n2 = srcStream.notes[i+1]
        n3 = srcStream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue
        
        i1 = notesToInterval(n1,n2)
        i2 = notesToInterval(n2,n3)

        if n1.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        ## e.g. G, F, G => G, F#, G
        if i1.directedName == "M-2" and \
           i2.directedName == "M2":
            numChanged += 1
            if ("capua" in n2.editorial.misc):
                n2.editorial.misc['capua_rule_number'] += RULE_ONE
            else:
                n2.editorial.misc['capua_rule_number'] = RULE_ONE
            if (n2.accidental is not None and n2.accidental.name == "flat"):
                n2.editorial.misc["saved-accidental"] = n2.accidental
                n2.accidental = None
                n2.editorial.ficta = Accidental("natural")
                n2.editorial.misc["capua-ficta"] = Accidental("natural")
                n1.editorial.color = "blue"
                n2.editorial.color = "forestGreen"
                n3.editorial.color = "blue"
            else:
                n2.editorial.ficta = Accidental("sharp")
                n2.editorial.misc["capua-ficta"] = Accidental("sharp")
                n1.editorial.color = "blue"
                n2.editorial.color = "ForestGreen"
                n3.editorial.color = "blue"

    return numChanged

def capuaRuleTwo(srcStream):
    '''Applies Capua's second rule to the given srcStream, i.e. if four notes are
    ascending with the pattern M2 m2 M2, the intervals shall be made M2 M2 m2.
    Also changes note.editorial.color for rule 2 (purple purple green purple).
    
    returns the number of times a note was changed
    '''
    numChanged = 0
    
    for i in range(0, len(srcStream.notes)-3):
        n1 = srcStream.notes[i]
        n2 = srcStream.notes[i+1]
        n3 = srcStream.notes[i+2]
        n4 = srcStream.notes[i+3]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest or \
           n4.isRest:
            continue

        i1 = notesToInterval(n1,n2)
        i2 = notesToInterval(n2,n3)
        i3 = notesToInterval(n3,n4)

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
            numChanged += 1
            if ("capua" in n3.editorial.misc):
                n3.editorial.misc['capua_rule_number'] += RULE_TWO
            else:
                n3.editorial.misc['capua_rule_number'] = RULE_TWO

            if (n3.accidental is not None and n3.accidental.name == "flat"):
                n3.editorial.misc["saved-accidental"] = n3.accidental
                n3.accidental = None
                n3.editorial.ficta = Accidental("natural")
                n3.editorial.misc["capua-ficta"] = Accidental("natural")
                n1.editorial.color = "purple"
                n2.editorial.color = "purple"
                n3.editorial.color = "ForestGreen"
                n4.editorial.color = "purple"
            else:
                n3.editorial.ficta = Accidental("sharp")
                n3.editorial.misc["capua-ficta"] = Accidental("sharp")
                n1.editorial.color = "purple"
                n2.editorial.color = "purple"
                n3.editorial.color = "ForestGreen"
                n4.editorial.color = "purple"

    return numChanged

def capuaRuleThree(srcStream):
    '''Applies Capua's third rule to the given srcStream, i.e. if there is a
    descending major third followed by an ascending major second, the second
    note will be made a half-step higher so that there is a descending minor
    third followed by an ascending minor second. Also changes
    note.editorial.color for rule 3 (pink green pink).
    
    returns the number of times a note was changed
    '''
    numChanged = 0
    
    for i in range(0, len(srcStream.notes)-2):
        n1 = srcStream.notes[i]
        n2 = srcStream.notes[i+1]
        n3 = srcStream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue
        
        i1 = notesToInterval(n1,n2)
        i2 = notesToInterval(n2,n3)

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
            numChanged += 1
            if ("capua" in n2.editorial.misc):
                n2.editorial.misc['capua_rule_number'] += RULE_THREE
            else:
                n2.editorial.misc['capua_rule_number'] = RULE_THREE
            n2.editorial.ficta = Accidental("sharp")
            n2.editorial.misc["capua-ficta"] = Accidental("sharp")
            n1.editorial.color = "DeepPink"
            n2.editorial.color = "ForestGreen"
            n3.editorial.color = "DeepPink"

    return numChanged

def capuaRuleFourA(srcStream):
    '''Applies one interpretation of Capua's fourth rule to the given srcStream,
    i.e. if a descending minor third is followed by a descending major second,
    the intervals will be changed to a major third followed by a minor second.
    Also changes note.editorial.color for rule 4 (orange green orange).
    
    returns the number of notes that were changed
    '''
    numChanged = 0
    
    for i in range(0, len(srcStream.notes)-2):
        n1 = srcStream.notes[i]
        n2 = srcStream.notes[i+1]
        n3 = srcStream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue
        
        i1 = notesToInterval(n1,n2)
        i2 = notesToInterval(n2,n3)

        if n1.accidental is not None or \
           n2.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        # e.g., D B A => D Bb A
        if i1.directedName  == "m-3" and \
           i2.directedName  == "M-2":
            numChanged += 1
            if ("capua" in n2.editorial.misc):
                n2.editorial.misc['capua_rule_number'] += RULE_FOUR_A
            else:
                n2.editorial.misc['capua_rule_number'] = RULE_FOUR_A
            n2.editorial.ficta = Accidental("flat")
            n2.editorial.misc["capua-ficta"] = Accidental("flat")
            n1.editorial.color = "orange"
            n2.editorial.color = "ForestGreen"
            n3.editorial.color = "orange"

    return numChanged

def capuaRuleFourB(srcStream):
    '''Applies more probable interpretation of Capua's fourth rule to the given
    srcStream, i.e. if a descending minor third is followed by a descending major
    second, the intervals will be changed to a major third followed by a minor
    second. Also copies any relevant accidental to note.editorial.misc under
    "saved-accidental" and changes note.editorial.color for rule 4 (orange
    green orange).
    
    returns the number of times a note was changed.
    '''
    numChanged = 0
    for i in range(0, len(srcStream.notes)-2):
        n1 = srcStream.notes[i]
        n2 = srcStream.notes[i+1]
        n3 = srcStream.notes[i+2]

        if n1.isRest or \
           n2.isRest or \
           n3.isRest:
            continue

        i1 = notesToInterval(n1,n2)
        i2 = notesToInterval(n2,n3)

        if n1.accidental is not None or \
           n3.accidental is not None:
            continue

        ### never seems to improve things...
        if n2.step == "A" or n2.step == "D":
            continue

        # e.g., D F G => D F# G  or G Bb C => G B C
        if i1.directedName  == "m3" and \
           i2.directedName  == "M2":
            numChanged += 1
            if ("capua" in n2.editorial.misc):
                n2.editorial.misc['capua_rule_number'] += RULE_FOUR_B
            else:
                n2.editorial.misc['capua_rule_number'] = RULE_FOUR_B
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

    return numChanged

def clearFicta(srcStream1):
    '''In the given srcStream, moves anything under note.editorial.ficta into
    note.editorial.misc under "saved-ficta".'''

    for n2 in srcStream1.notes:
        if  n2.editorial.ficta is not None:
            n2.editorial.misc["saved-ficta"] = n2.editorial.ficta
        n2.editorial.ficta = None   

def restoreFicta(srcStream1):
    '''In the given srcStream, moves anything under note.editorial.misc["saved-ficta"]
    back to note.editorial.ficta.'''
    for n2 in srcStream1:
        if  "saved-ficta" in n2.editorial.misc:
            n2.editorial.ficta = n2.editorial.misc["saved-ficta"]
            n2.editorial.misc["saved-ficta"] = None

def clearAccidental(note1):
    '''moves the accidental to \'saved-accidental\' and clears note.accidental'''
    if note1.accidental is not None:
        note1.editorial.misc["saved-accidental"] = note1.accidental
        note1.accidental = None

def restoreAccidental(note1):
    '''takes note.editorial.music[\'saved-accidental\'] and moves it back to the note'''
    if  "saved-accidental" in note1.editorial.misc:
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
    if "pmfc-ficta" in note1.editorial.misc and \
       note1.editorial.misc["pmfc-ficta"] is not None:
        if note1.accidental is not None:
            note1.editorial.misc["saved-accidental"] = note1.accidental
        note1.accidental = note1.editorial.misc["pmfc-ficta"]
        
def capuaFictaToAccidental(note1):
    '''Moves Capua's ficta to the accidental'''
    if "capua-ficta" in note1.editorial.misc and \
       note1.editorial.misc["capua-ficta"] is not None:
        if note1.accidental is not None:
            note1.editorial.misc["saved-accidental"] = note1.accidental
        note1.accidental = note1.editorial.misc["capua-ficta"]

def capuaRulesOnsrcStream(srcStream1):
    '''runs clearFicta and then each of the four Capua rules on the srcStream (4b not 4a)'''
    clearFicta(srcStream1)
    capuaRuleOne(srcStream1)
    capuaRuleTwo(srcStream1)
    capuaRuleThree(srcStream1)
#    capuaRuleFourA(srcStream1)
    capuaRuleFourB(srcStream1)

def evaluateRules(srcStream1, srcStream2):
    '''Runs evaluation method for capua on one srcStream only, and evaluating harmonies,
    for each srcStream; then runs method for applying capua rules to both and evaluating
    the resulting harmonies.''' #Returns SOMETHING USEFUL TO BE DETERMINED
    srcStream1Count = evaluateCapuaOnesrcStream(srcStream1, srcStream2)
    srcStream2Count = evaluateCapuaOnesrcStream(srcStream2, srcStream1)
    bothCount = evaluateCapuatwoStreams(srcStream1, srcStream2)
    #do something with them...
    return bothCount

def evaluateCapuaOnesrcStream(srcStream1, srcStream2):
    '''Runs Capua rules on one srcStream only and evaluates the harmonies; stores harmonies
    under "capua1FictaHarmony" in note.editorial.misc; returns a list of the number of
    [perfect cons, imperfect cons, dissonances].'''
    capuaRulesOnsrcStream(srcStream1)
    for note1 in srcStream1:
        capuaFictaToAccidental(note1)
    srcStream1Count = compareOnesrcStream(srcStream1, srcStream2, "capua1srcStream")
    for note1 in srcStream1:
        restoreAccidental(note1)
    return srcStream1Count

def evaluateCapuatwoStreams(srcStream1, srcStream2):
    '''Runs Capua rules on both srcStreams and evaluates the harmonies; stores harmonies
    under "capua2FictaHarmony" in note.editorial.misc; returns a dictionary that contains
    the number of [perfect cons, imperfect cons, dissonances] for each srcStream, which can
    be obtained with keys "srcStream1Count" and "srcStream2Count".'''
    capuaRulesOnsrcStream(srcStream1)
    capuaRulesOnsrcStream(srcStream2)
    for note1 in srcStream1:
        capuaFictaToAccidental(note1)
    for note2 in srcStream2:
        capuaFictaToAccidental(note2)
    srcStream1Count = compareOnesrcStream(srcStream1, srcStream2, "capua2srcStream")
    srcStream2Count = compareOnesrcStream(srcStream2, srcStream1, "capua2srcStream")
    for note1 in srcStream1:
        restoreAccidental(note1)
    for note2 in srcStream2:
        restoreAccidental(note2)
    bothCount = {}
    bothCount["srcStream1Count"] = srcStream1Count
    bothCount["srcStream2Count"] = srcStream2Count
    return bothCount

def evaluateEditorsFicta(srcStream1, srcStream2):
    '''Runs pmfcFictaToAccidental, then runs the evaluation method on the two srcStreams.
    Returns editorProfile, a list of lists with the number of perfect cons, imperfect
    cons, and dissonances for each srcStream.'''
    for note1 in srcStream1:
        pmfcFictaToAccidental(note1)
    for note2 in srcStream2:
        pmfcFictaToAccidental(note2)
    editorProfile = evaluateHarmony(srcStream1, srcStream2, "editor")
    for note1 in srcStream1:
        restoreAccidental(note1)
    for note2 in srcStream2:
        restoreAccidental(note2)
    return editorProfile

def evaluateWithoutFicta(srcStream1, srcStream2):
    '''Clears all ficta, then evaluates the harmonies of the two srcStreams. Returns
    a list of lists of the interval counts for each '''
    clearFicta(srcStream1) #probably not necessary to clear ficta, but just to be safe
    clearFicta(srcStream2)
    noneProfile1 = compareOnesrcStream(srcStream1, srcStream2, None)
    noneProfile2 = compareOnesrcStream(srcStream2, srcStream1, None)
    restoreFicta(srcStream1)
    restoreFicta(srcStream2)
    return noneProfile1



PerfectCons = ["P1", "P5", "P8"]
ImperfCons  = ["m3", "M3", "m6", "M6"]
Others      = ["m2", "M2", "A2", "d3", "A3", "d4", "P4", "A4", "d5", "A5", "d6",
               "A6", "d7", "m7", "M7", "A7"]

PERFCONS = 1
IMPERFCONS = 2
OTHERS = 3

def compareThreeFictas(srcStream1, srcStream2):
    noficta = {}
    pmfcficta = {}
    capuaficta = {}

    for i in (PerfectCons + ImperfCons + Others):
        noficta[i] = 0
        pmfcficta[i] = 0
        capuaficta[i] = 0

    ### populates the editorial.interval attribute on each note
#    twosrcStream1 = TwoStreamComparer(srcStream1, srcStream2)
#    twosrcStream1.intervalToOtherStreamWhenAttacked()

    for note1 in srcStream1.notes:
        if "pmfc-ficta" in note1.editorial.misc or \
           "capua-ficta" in note1.editorial.misc:
            normalInterval = note1.editorial.harmonicInterval.name
            if "pmfc-ficta" in note1.editorial.misc:
                pmfcFictaToAccidental(note1)
                note1.editorial.harmonicInterval.reinit()
                pmfcInterval = note1.editorial.harmonicInterval.name
            else:
                pmfcInterval = ""
            if "capua-ficta" in note1.editorial.misc:
                capuaFictaToAccidental(note1)
                note1.editorial.harmonicInterval.reinit()
                capuaInterval = note1.editorial.harmonicInterval.name
            else:
                capuaInterval = ""
            restoreAccidental(note1)
            print ("N: " + normalInterval, "P: " + pmfcInterval, "C: " +capuaInterval)

def comparesrcStreamCapuaToEditor(srcStream1):
    totalDict = {
        'totalNotes': 0,
        'pmfcAlt': 0,
        'capuaAlt': 0,
        'pmfcNotCapua': 0,
        'capuaNotPmfc': 0,
        'pmfcAndCapua': 0,
        }
    for note1 in srcStream1.notes:
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
    if "pmfc-ficta" in note1.editorial.misc and \
           "capua-ficta" in note1.editorial.misc:
        statsDict['pmfcAlt'] += 1
        statsDict['capuaAlt'] += 1
        statsDict['pmfcAndCapua'] += 1
    elif "pmfc-ficta" in note1.editorial.misc:
        statsDict['pmfcAlt'] += 1
        statsDict['pmfcNotCapua'] += 1
        if note1.editorial.harmonicInterval:
            pass
            #print "In PMFC: " + note1.editorial.harmonicInterval.name
    elif "capua-ficta" in note1.editorial.misc:
        statsDict['capuaAlt'] += 1
        statsDict['capuaNotPmfc'] += 1
        if note1.editorial.harmonicInterval:
            pass
            #print "In Capua: " + note1.editorial.harmonicInterval.name
    return statsDict

def compareOnesrcStream(srcStream1, srcStream2, fictaType = "editor"):
    '''Helper function for evaluateHarmony that for each note in srcStream1 determines
    that notes starting interval in relation to srcStream2, and assigns identifiers to
    the fictaHarmony and fictaInterval in note.editorial if there is ficta, or to the
    noFictaHarmony if there is no ficta for that note. Returns a list of the number
    of perfect consonances, imperfect consonances, and other (dissonances) for srcStream1.
    For the fictaType variable, write "editor" or "capua", "capua1srcStream" or "capua2srcStream".'''
    twosrcStream1 = TwoStreamComparer(srcStream1, srcStream2)
    perfectConsCount = 0
    imperfConsCount = 0
    othersCount = 0

    ### populates the note.editorial.harmonicInterval object
    twosrcStream1.intervalToOtherStreamWhenAttacked()
    for note1 in srcStream1.notes:
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
            if debug: print ("found ficta of Editor type")
            note1.editorial.misc["editorFictaHarmony"] = iType
            note1.editorial.misc["editorFictaInterval"] = interval1 
        elif hasFicta and fictaType == "capua1srcStream":
            if debug: print ("found ficta of capua1srcStream type")
            note1.editorial.misc["capua1FictaHarmony"] = iType
            note1.editorial.misc["capua1FictaInterval"] = interval1
        elif hasFicta and fictaType == "capua2srcStream":
            if debug: print ("found ficta of capua2srcStream type")
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

##def compareAll(srcStream1, srcStream2):
##    # needs to evaluate fictaHarmony, noFictaHarmony to determine color of note,
##    # also evaluate counters for perfect, imperfect, and other intervals
##    pass

def colorCapuaFicta(srcStream1, srcStream2, oneOrBoth = "both"):
    '''Given two srcStreams, applies the capua rules and colors each note (in
    note.editorial.misc under "ficta-color") as compared to the srcStreams with no ficta,
    using betterColor, worseColor, and neutralColor.'''
    twoStreams1 = TwoStreamComparer(srcStream1, srcStream2)
    twoStreams1.intervalToOtherStreamWhenAttacked()
    capuaCount = evaluateRules(srcStream1, srcStream2)
    print(capuaCount)
    noFictaCount = evaluateWithoutFicta(srcStream1, srcStream2)
    print(noFictaCount)
    for note1 in srcStream1:
        colorNote(note1, oneOrBoth)
    for note2 in srcStream2:
        colorNote(note2, oneOrBoth)

def colorNote(note1, oneOrBoth = "both"):
    '''Applies all rules to a note according to what harmonies are better/worse/neutral.'''
    if "capua2FictaHarmony" not in note1.editorial.misc: return
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
        print(pieceObj.title)
        cadenceA   = pieceObj.cadenceAClass()
        if len(cadenceA.srcStreams) >= 2:
            srcStream1    = cadenceA.srcStreams[0]
            srcStream2    = cadenceA.srcStreams[1]  ## ignore 3rd voice for now...
            twoStreams1 = twoStreams.TwoStreamComparer(srcStream1, srcStream2)
            twoStreams1.intervalToOtherStreamWhenAttacked()
            capuaRulesOnsrcStream(srcStream1)
            thisDict = comparesrcStreamCapuaToEditor(srcStream1)
            for thisKey in thisDict.keys():
                totalDict[thisKey] += thisDict[thisKey]

    print(totalDict)

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
        if cadenceA is not None and len(cadenceA.srcStreams) >= 2:
            srcStream1    = cadenceA.srcStreams[0]
            srcStream2    = cadenceA.srcStreams[1]  ## ignore 3rd voice for now...
            twoStreams1 = twoStreams.TwoStreamComparer(srcStream2, srcStream1)
            twoStreams1.intervalToOtherStreamWhenAttacked()
            capuaRulesOnsrcStream(srcStream2)

            for note1 in srcStream2:
                if note1.editorial.harmonicInterval is None or \
                   note1.editorial.harmonicInterval.simpleName != "M3":
                    continue

                nextFewNotes = srcStream2.notesFollowingNote(note1, notesToCheck, allowRests = False)
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
                
    print(totalDict)
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
        print(i)
        pieceObj   = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipitClass is None:
            continue
        cadenceA   = pieceObj.cadenceAClass()
        if cadenceA is not None and len(cadenceA.srcStreams) >= 2:
            srcStream1    = cadenceA.srcStreams[0]
            srcStream2    = cadenceA.srcStreams[1]  ## ignore 3rd voice for now...
            twoStreams1 = twoStreams.TwoStreamComparer(srcStream1, srcStream2)
            twoStreams1.intervalToOtherStreamWhenAttacked()
            capuaRulesOnsrcStream(srcStream1)

            for note1 in srcStream1:
                if note1.editorial.harmonicInterval is None or \
                   note1.editorial.harmonicInterval.simpleName != "m6":
                    continue
                
                nextFewNotes = srcStream1.notesFollowingNote(note1, notesToCheck, allowRests = False)
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
                
    print(totalDict)
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
        print(i)
        pieceObj   = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipitClass is None:
            continue
        
        for thisCadence in pieceObj.snippetBlocks:
            if thisCadence is not None and len(thisCadence.srcStreams) >= 2:
                srcStream1    = thisCadence.srcStreams[0]
                srcStream2    = thisCadence.srcStreams[1]  ## ignore 3rd voice for now...
                twoStreams1 = twoStreams.TwoStreamComparer(srcStream1, srcStream2)
                try:
                    twoStreams1.intervalToOtherStreamWhenAttacked()
                except:
                    print("UGGGH ERROR!")
                    continue
                capuaRulesOnsrcStream(srcStream1)
    
                for note1 in srcStream1:
                    hI = note1.editorial.harmonicInterval
                    if hI is None or \
                       hI.generic.perfectable is False or \
                       hI.generic.simpleUndirected == 4:
                        continue
    
                    #### KEEP PROGRAMMING FROM HERE
                    if hI.diatonic.specificName == "Perfect":
                        if "capua-ficta" in note1.editorial.misc:
                            checkDict["perfCapua"] += 1  ## ugh Capua changed a P1, P5, or P8
                        else:
                            checkDict["perfIgnored"] +=1 ## yay Capua left it alone
                    else:
                        if "capua-ficta" in note1.editorial.misc:
                            checkDict["imperfCapua"] += 1  ## yay Capua changed a A1 or d1, A5 or d5, or A8 or d8
                        else:
                            checkDict["imperfIgnored"] +=1 ## hrumph, Capua left it alone                                
                for note2 in srcStream2:
                    hI = note1.editorial.harmonicInterval
                    if hI is None or \
                       hI.generic.perfectable is False or \
                       hI.generic.simpleUndirected == 4:
                        continue
    
                    #### KEEP PROGRAMMING FROM HERE
                    if hI.diatonic.specificName == "Perfect":
                        if "capua-ficta" in note1.editorial.misc:
                            checkDict["perfCapua"] += 1  ## ugh Capua changed a P1, P5, or P8
                        else:
                            checkDict["perfIgnored"] +=1 ## yay Capua left it alone
                    else:
                        if "capua-ficta" in note1.editorial.misc:
                            checkDict["imperfCapua"] += 1  ## yay Capua changed a A1 or d1, A5 or d5, or A8 or d8
                        else:
                            checkDict["imperfIgnored"] +=1 ## hrumph, Capua left it alone                                

    print(checkDict)

def runPiece(pieceNum = 331, snipNum = 0):  # random default piece...
    ballataObj = cadencebook.BallataSheet()
    pieceObj   = ballataObj.makeWork(pieceNum)
#    pieceObj.snippets[0].lily.showPNG()
    applyCapua(pieceObj)
    pieceObj.snippets[snipNum].lily.showPNG()
    srcStream    = pieceObj.snippets[snipNum].streams[0]
    cmpStream    = pieceObj.snippets[snipNum].streams[1]  ## ignore 3rd voice for now...
    srcStream.attachIntervalsBetweenStreams(cmpStream)

    for note in srcStream.notes:
        if note.editorial.harmonicInterval is not None:
            print(note.name)
            print(note.editorial.harmonicInterval.simpleName)
            if "capua-ficta" in note.editorial.misc:
                print note.editorial.misc['capua-ficta']

def ruleFrequency():
    ballataObj = cadencebook.BallataSheet()
    num1 = 0
    num2 = 0
    num3 = 0
    num4a = 0
    num4b = 0
    for i in range(2, 100): #459): # all ballate
        pieceObj = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers
        theseStreams = pieceObj.getAllStreams()
        for thisStream in theseStreams:
            num1 += 0#capuaRuleOne(thisStream)
            num2 += 0#capuaRuleTwo(thisStream)
            num3 += 0#capuaRuleThree(thisStream)
            num4a += 0#capuaRuleFourA(thisStream)
            num4b += capuaRuleFourB(thisStream)
            
    return (num1, num2, num3, num4a, num4b)

def showFourA():
    ballataObj = cadencebook.BallataSheet()
    showStream = music21.stream.Stream()
    for i in range(2, 45): #459): # all ballate
        pieceObj = ballataObj.makeWork(i)  ## N.B. -- we now use Excel column numbers

        theseStreams = pieceObj.getAllStreams()
        for thisStream in theseStreams:
            if capuaRuleFourA(thisStream) > 0:
                showStream.append(thisStream)

    showStream.lily.showPNG()


class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testRunPiece(self):
        pieceNum = 331 # Francesco, PMFC 4 6-7: Non creder, donna
        ballataObj = cadencebook.BallataSheet()
        pieceObj   = ballataObj.makeWork(pieceNum)
        applyCapua(pieceObj)
        srcStream    = pieceObj.snippets[0].streams[0]
        cmpStream    = pieceObj.snippets[0].streams[1]  ## ignore 3rd voice for now...
        srcStream.attachIntervalsBetweenStreams(cmpStream)

        outList = []
        for note in srcStream.notes:
            if note.editorial.harmonicInterval is not None:
                note.lyric = note.editorial.harmonicInterval.simpleName
        
        pieceObj.snippets[0].lily.showPNG()

    def testShowFourA(self):
        showFourA()



class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testRunPiece(self):
        pieceNum = 331 # Francesco, PMFC 4 6-7: Non creder, donna
        ballataObj = cadencebook.BallataSheet()
        pieceObj   = ballataObj.makeWork(pieceNum)
        applyCapua(pieceObj)
        srcStream    = pieceObj.snippets[0].streams[0]
        cmpStream    = pieceObj.snippets[0].streams[1]  ## ignore 3rd voice for now...
        srcStream.attachIntervalsBetweenStreams(cmpStream)

        outList = []
        for note in srcStream.notes:
            if note.editorial.harmonicInterval is not None:
                outList.append(note.name)
                outList.append(note.editorial.harmonicInterval.simpleName)
                if "capua-ficta" in note.editorial.misc:
                    outList.append(repr(note.editorial.misc['capua-ficta']))
                    
        self.assertEqual(outList, [u'A', 'P5', u'A', 'M6', u'G', 'P5', u'G', 'm6', u'A', 'm7', u'F', 'd5', '<accidental sharp>', u'G', 'm6', u'A', 'P1', u'B', 'M6', u'A', 'P5', u'G', 'm7', u'G', 'm6', u'F', 'd5', u'E', 'M3', u'D', 'P1'])


    def run1test(self):
        ballataSht = cadencebook.BallataSheet()
        pieceObj   = ballataSht.makeWork(20)  ## N.B. -- we now use Excel column numbers
        if pieceObj.incipitClass() is None:
            return None
        cadenceA   = pieceObj.cadenceAClass()
        if len(cadenceA.srcStreams) >= 2:
            srcStream1    = cadenceA.srcStreams[0]
            srcStream2    = cadenceA.srcStreams[1]  ## ignore 3rd voice for now...
    #        twoStreams1 = twoStreams.TwoStreamComparer(srcStream1, srcStream2)
    #    raise("hi?")
    #    clearFicta(srcStream1)
    #    compareThreeFictas(srcStream1, srcStream2)
    #    scoreList = compareOnesrcStream(srcStream1, srcStream2)
    #    if debug == True:
    #        for note in srcStream1:
    #            print note.name
    #            print note.editorial.ficta
    #            print note.editorial.harmonicInterval.diatonic.name
    #    restoreFicta(srcStream1)
    #    print scoreList

    def xtestColorCapuaFicta(self):
        from music21.note import Note
        from music21.stream import Stream
        (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
        (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
        n11.duration.type = "quarter"
        n11.name = "D"
        n12.duration.type = "quarter"
        n12.name = "E"
        n13.duration.type = "quarter"
        n13.name = "F"
        n14.duration.type = "quarter"
        n14.name = "G"
    
        n21.name = "C"
        n21.duration.type = "quarter"
        n22.name = "C"
        n22.duration.type = "quarter"
        n23.name = "B"
        n23.octave = 3
        n23.duration.type = "quarter"
        n24.name = "C"
        n24.duration.type = "quarter"
    
        stream1 = Stream()
        stream1.append([n11, n12, n13, n14])
        stream2 = Stream()
        stream2.append([n21, n22, n23, n24])
    
    
        ### Need twoStreamComparer to Work
        evaluateWithoutFicta(stream1, stream2)
        assert n13.editorial.harmonicInterval.name == "d5", n13.editorial.harmonicInterval.name
#        evaluateCapuaTwoStreams(stream1, stream2)
#    
#        colorCapuaFicta(stream1, stream2, "both")
#        assert n13.editorial.harmonicInterval.name == "P5", n13.editorial.harmonicInterval.name
#    
#        assert n11.editorial.color == "yellow"
#        assert n12.editorial.color == "yellow"
#        assert n13.editorial.color == "green"
#        assert n14.editorial.color == "yellow"
#    
#        assert n11.editorial.harmonicInterval.name == "M2"
#        assert n21.editorial.harmonicInterval.name == "M2"
#    
#        assert n13.editorial.harmonicInterval.name == "P5"
#        assert n13.editorial.misc["noFictaHarmony"] == "perfect cons"
#        assert n13.editorial.misc["capua2FictaHarmony"] == "perfect cons"
#        assert n13.editorial.misc["capua2FictaInterval"].name == "P5"
#        assert n13.editorial.color == "green"
#        assert stream1.lily.strip() == r'''\clef "treble" \color "yellow" d'4 \color "yellow" e'4 \ficta \color "green" fis'!4 \color "yellow" g'4'''

    def testRuleFrequency(self):        
        import time
        #print time.ctime()
        (num1, num2, num3, num4a, num4b) = ruleFrequency()
        #print time.ctime()
        #print num1
        #print num2
        #print num3
        #print num4a
        #print num4b
#        self.assertEqual(num4a,  57)
#        self.assertEqual(num4b, 104)
    

if (__name__ == "__main__"):
    runPiece(267)
    #music21.mainTest(Test) #, TestExternal)
    
#    test()
#    correctedMin6()
#    correctedMaj3()
#    improvedHarmony()