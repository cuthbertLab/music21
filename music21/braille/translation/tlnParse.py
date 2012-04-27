# -*- coding: utf-8 -*-

import pprint
import re

from lxml import etree #need to install lxml
from music21.braille.translation import tlnTables
from music21.braille.translation import tlnLookup

#-------------------------------------------------------------------------------

def music():
    """
    http://www.music.vt.edu/musicdictionary/appendix/translations/Translations.html
    """
    f = open('websites/music.html')
    html = etree.HTML(f.read())
    
    englishToFrench = {}
    englishToGerman = {}
    englishToItalian = {}
    englishToSpanish = {}
    englishToAbbreviation = {}
    
    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        for col in allCols:
            items = [a.text.lower() for a in col.iter("a") if a.text is not None]
            items.extend([p.text.lower() for p in col.iter("p") if p.text is not None])
            if col.text is not None:
                items.append(col.text.lower())
            allSols.append(items)
        for cell in allSols[0]:
            cell = u" ".join(cell.split())
            englishToFrench[cell] = [u" ".join(s.split()) for s in allSols[1]]
            englishToGerman[cell] = [u" ".join(s.split()) for s in allSols[2]]
            englishToItalian[cell] = [u" ".join(s.split()) for s in allSols[3]]
            englishToSpanish[cell] = [u" ".join(s.split()) for s in allSols[4]]
            englishToAbbreviation[cell] = [u" ".join(s.split()) for s in allSols[5]]

    allDicts = [englishToFrench, englishToGerman, englishToItalian, englishToSpanish, englishToAbbreviation]
    for dict in allDicts:
        del dict[u'']
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    print "englishToFrench = ", 
    pprint.pprint(englishToFrench)
    print "\nenglishGerman = ", 
    pprint.pprint(englishToGerman)
    print "\nenglishItalian = ", 
    pprint.pprint(englishToItalian)
    print "\nenglishSpanish = ", 
    pprint.pprint(englishToSpanish)
    print "\nenglishAbbreviations = ", 
    pprint.pprint(englishToAbbreviation)

"""
Mapping of "best names" to instrument class name
Mapping of "abbreviations" to "best names"

Mapping of "best name" to synonyms

Words in Italian, French, German, Spanish, Russian map to "best name" or synomymys in English,
which map to instrument class name

italianToEnglish, frenchToEnglish, germanToEnglish,

english horn, french horn, alpine horn => horn

cor anglais  => english horn
cor francais => french horn

retrieves a dictionary from tlnLookup
adds a bunch of key, value pairs to it
rewrites ALL tables to it.
"""
#-------------------------------------------------------------------------------

def dolmetsch():
    """
    http://www.dolmetsch.com/musictheory29.htm#translatednames
    """
    f = open('websites/dolmetsch.html')
    html = etree.HTML(f.read())
    
    englishToFrench = {}
    englishToGerman = {}
    englishToItalian = {}
    englishToSpanish = {}
    
    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        for col in allCols:
            items = [td.text.lower() for td in col.iter("td") if td.text is not None]
            items.extend([br.tail.lower() for br in col.iter("br") if br.tail is not None])
            allSols.append([unicode(s.encode("utf-8")) for s in items])
        #for cell in allSols[0]:
        if len(allSols[0]) == 0:
            continue
        cell = allSols[0][0]
        cell = u" ".join(cell.split("(")[0].split())
        englishToItalian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
        englishToGerman[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]
        englishToFrench[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[3]]
        englishToSpanish[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[4]]

    allDicts = [englishToFrench, englishToGerman, englishToItalian, englishToSpanish]
    for dict in allDicts:
        try:
            del dict[u'']
        except KeyError:
            pass
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    #merge(tlnTables.englishToFrench, englishToFrench)
    #merge(tlnTables.englishToGerman, englishToGerman)
    #merge(tlnTables.englishToItalian, englishToItalian)
    #merge(tlnTables.englishToSpanish, englishToSpanish)
    
    print "englishToFrench = ", 
    pprint.pprint(englishToFrench)
    print "\nenglishGerman = ", 
    pprint.pprint(englishToGerman)
    print "\nenglishItalian = ", 
    pprint.pprint(englishToItalian)
    print "\nenglishSpanish = ", 
    pprint.pprint(englishToSpanish)

def dolmetsch_b():
    """
    http://www.dolmetsch.com/musictheory29.htm#translatednames
    """
    f = open('websites/dolmetsch.html')
    html = etree.HTML(f.read())
    
    import collections
    synonyms = {}
    
    from music21.languageExcerpts import instrumentLookup
    
    
    
    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        for col in allCols:
            items = [td.text.lower() for td in col.iter("td") if td.text is not None]
            items.extend([br.tail.lower() for br in col.iter("br") if br.tail is not None])
            allSols.append([unicode(s.encode("utf_8")) for s in items])
        bestName = None
        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            if cell in instrumentLookup.bestNameToInstrumentClass:
                bestName = cell
        if bestName is not None:
            for cell in allSols[0]:
                cell = u" ".join(cell.split("(")[0].split())
                if cell != bestName:
                    synonyms[cell] = bestName

    return synonyms
#-------------------------------------------------------------------------------

def dolmetsch2():
    """
    http://www.dolmetsch.com/musictheory29.htm#instrumentabbrev
    """
    f = open('websites/dolmetsch2.html')
    html = etree.HTML(f.read())
    
    englishToAbbreviation = {}
    
    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        for col in allCols:
            items = [td.text.lower() for td in col.iter("td") if td.text is not None]
            allSols.append([unicode(s.encode("latin_1")) for s in items])
        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            items = []
            for a in allSols[1]:
                items.extend([x.strip() for x in a.split("(")[0].split(",")])
            englishToAbbreviation[cell] = items
    
    allDicts = [englishToAbbreviation]
    for dict in allDicts:
        try:
            del dict[u'']
        except KeyError:
            pass
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
            while(True):
                try:
                    dict[key].remove(u'-')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    merge(tlnTables.englishToAbbreviation, englishToAbbreviation)
    print "englishToAbbreviation = ", 
    pprint.pprint(englishToAbbreviation)

#-------------------------------------------------------------------------------

def yale():
    """
    http://www.library.yale.edu/cataloging/music/instname.htm#wind
    """
    f = open('websites/yale.html')
    html = etree.HTML(f.read())
    
    englishToFrench = {}
    englishToGerman = {}
    englishToItalian = {}
    englishToSpanish = {}
    englishToRussian = {}
    
    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        for col in allCols:
            items = []
            for f in col.iter("font"):
                if f.text is not None:
                    items.extend(re.split("[,;/]",f.text.lower()))
            for br in col.iter("br"):
                if br.tail is not None:
                    items.extend(re.split("[,;/]",br.tail.lower()))
            allSols.append(items)
        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            englishToFrench[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishToGerman[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]
            englishToItalian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[3]]
            englishToRussian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[4]]
            englishToSpanish[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[5]]

    allDicts = [englishToFrench, englishToGerman, englishToItalian, englishToSpanish, englishToRussian]
    for dict in allDicts:
        try:
            del dict[u'']
        except KeyError:
            pass
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    merge(tlnTables.englishToFrench, englishToFrench)
    merge(tlnTables.englishToGerman, englishToGerman)
    merge(tlnTables.englishToItalian, englishToItalian)
    merge(tlnTables.englishToSpanish, englishToSpanish)
    merge(tlnTables.englishToRussian, englishToRussian)
    
    print "englishToFrench = ", 
    pprint.pprint(englishToFrench)
    print "\nenglishGerman = ", 
    pprint.pprint(englishToGerman)
    print "\nenglishItalian = ", 
    pprint.pprint(englishToItalian)
    print "\nenglishSpanish = ", 
    pprint.pprint(englishToSpanish)
    print "\nenglishRussian = ", 
    pprint.pprint(englishToRussian)

#-------------------------------------------------------------------------------

def ukItalian():
    """
    http://www.musictheory.org.uk/res-musical-terms/italian-musical-terms.php
    """
    f = open('websites/ukItalian.html')
    html = etree.HTML(f.read())
    
    englishToItalian = {}
    englishToAbbreviation = {}

    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        if len(allCols) == 0:
            continue
        for td in allCols[3].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower())
                allSols.append([unicode(s.encode("latin_1")) for s in items])
        for td in allCols[2].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower()[1:-1])
                allSols.append([unicode(s.encode("latin_1")) for s in items])
        for td in allCols[0].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower())
                allSols.append([unicode(s.encode("latin_1")) for s in items])

        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            englishToAbbreviation[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishToItalian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]

    allDicts = [englishToItalian, englishToAbbreviation]
    for dict in allDicts:
        try:
            del dict[u'']
        except KeyError:
            pass
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    merge(tlnTables.englishToItalian, englishToItalian)
    merge(tlnTables.englishToAbbreviation, englishToAbbreviation)

    print "englishToItalian = ", 
    pprint.pprint(englishToItalian)
    print "\nenglishAbbreviations = ", 
    pprint.pprint(englishToAbbreviation)

#-------------------------------------------------------------------------------

def ukGerman():
    """
    http://www.musictheory.org.uk/res-musical-terms/german-musical-terms.php
    """
    f = open('websites/ukGerman.html')
    html = etree.HTML(f.read())
    
    englishToGerman = {}
    englishToAbbreviation = {}

    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        if len(allCols) == 0:
            continue
        for td in allCols[3].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower())
                allSols.append([unicode(s.encode("latin_1")) for s in items])
        for td in allCols[2].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower()[1:-1])
                allSols.append([unicode(s.encode("latin_1")) for s in items])
        for td in allCols[0].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower())
                allSols.append([unicode(s.encode("latin_1")) for s in items])

        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            englishToAbbreviation[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishToGerman[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]

    allDicts = [englishToGerman, englishToAbbreviation]
    for dict in allDicts:
        try:
            del dict[u'']
        except KeyError:
            pass
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    merge(tlnTables.englishToGerman, englishToGerman)
    merge(tlnTables.englishToAbbreviation, englishToAbbreviation)

    print "englishToGerman = ", 
    pprint.pprint(englishToGerman)
    print "\nenglishAbbreviations = ", 
    pprint.pprint(englishToAbbreviation)

#-------------------------------------------------------------------------------

def ukFrench():
    """
    http://www.musictheory.org.uk/res-musical-terms/french-musical-terms.php
    """
    f = open('websites/ukFrench.html')
    html = etree.HTML(f.read())
    
    englishToFrench = {}
    englishToAbbreviation = {}

    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        if len(allCols) == 0:
            continue
        for td in allCols[3].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower())
                allSols.append([unicode(s.encode("latin_1")) for s in items])
        for td in allCols[2].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower()[1:-1])
                allSols.append([unicode(s.encode("latin_1")) for s in items])
        for td in allCols[0].iter("td"):
            if td.text is not None:
                items = re.split("/;", td.text.lower())
                allSols.append([unicode(s.encode("latin_1")) for s in items])

        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            englishToAbbreviation[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishToFrench[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]

    allDicts = [englishToFrench, englishToAbbreviation]
    for dict in allDicts:
        try:
            del dict[u'']
        except KeyError:
            pass
        for key in dict:
            while(True):
                try:
                    dict[key].remove(u'')
                except ValueError:
                    break
        for key in dict.keys():
            if len(dict[key]) == 0:
                del dict[key]

    merge(tlnTables.englishToFrench, englishToFrench)

    print "englishToFrench = ", 
    pprint.pprint(englishToFrench)

def charlesl():
    """
    http://utminers.utep.edu/charlesl/transpose.html
    """
    f = open("websites/charlesl.html")
    html = etree.HTML(f.read())

    allTables = list(html.iter("table"))
    for table in allTables[0:1]:
        allRows = list(table.iter("tr"))
        print list(allRows[0].iter("font"))[0].text
        for row in table.iter("tr"):
            pass

#-------------------------------------------------------------------------------

def merge(source, target):
    """
    Merge source dictionary with target dictionary.
    """
    for srcKey in source.keys():
        if not target.has_key(srcKey):
            target[srcKey] = source[srcKey]
        else:
            for item in source[srcKey]:
                if not item in target[srcKey]:
                    target[srcKey].append(item)
    
#------------------------------------------------------------------------------

def translate(term, language="English"):
    if language.lower() == "english":
        return toEnglish(term.lower())
    
    try:
        return fromEnglish(term.lower(), language)
    except Exception:
        pass

    eng = toEnglish(term.lower())
    try:
        return fromEnglish(eng, language)
    except Exception:
        raise Exception("{0} could not be translated to {1}.".format(term, language))

def fromEnglish(term, language="Italian"):
    try:
        info = tlnLookup.englishToAll[unicode(term.lower())]
    except KeyError:
        raise Exception("{0} not found in dictionary.".format(term))
    try:
        return u" OR ".join(info[language.lower()])
    except KeyError:
        raise Exception("{0} could not be translated to {1}.".format(term, language))
        
def toEnglish(term):
    try:
        return tlnLookup.allToEnglish[unicode(term.lower())]
    except KeyError:
        raise Exception("{0} not found in dictionary.".format(term))

def combinations(instrumentString):
    sampleList = instrumentString.split()
    allComb = []
    for size in range(1,len(sampleList)+1):
        for i in range(len(sampleList)-size+1):
            allComb.append(u" ".join(sampleList[i:i+size]))
    return allComb

def getInstrumentFromString(instrumentString):
    from music21.languageExcerpts import instrumentLookup
    allCombinations = combinations(instrumentString)
    from music21 import instrument
    # First task: Find the best instrument.
    bestInstClass = None
    bestInstrument = None
    bestName = None
    for substring in allCombinations:
        try:
            englishName = instrumentLookup.allToEnglish[unicode(substring.lower())]
            className = instrumentLookup.bestNameToInstrumentClass[englishName]
            thisInstClass = eval("instrument.{0}".format(className))
            thisInstrument = thisInstClass()
            thisBestName = thisInstrument.bestName().lower()
            if bestInstClass is None or len(thisBestName.split())\
             >= len(bestName.split()) and not issubclass(bestInstClass, thisInstClass):
                 # priority is also given to same length instruments which fall later
                 # on in the string (i.e. Bb Piccolo Trumpet)
                 bestInstClass = thisInstClass
                 bestInstrument = thisInstrument
                 bestName = thisBestName
        except KeyError:
            pass
    if bestInstClass is None:
        raise Exception("No matching instrument for string.")
    if bestName not in instrumentLookup.transposition:
        return bestInstrument

    # A transposition table is defined for the instrument.
    for substring in allCombinations:
        try:
            bestPitch = instrumentLookup.pitchFullNameToName[unicode(substring.lower())]
            bestInterval = instrumentLookup.transposition[bestName][bestPitch]
            from music21 import interval
            bestInstrument.transposition = interval.Interval(bestInterval)
            break
        except KeyError:
            pass
    return bestInstrument
        
#------------------------------------------------------------------------------

if __name__ == "__main__":
    pprint.pprint(dolmetsch_b())
    '''
    from music21 import interval
    t1 = getInstrumentFromString("Bb Piccolo Trumpet")
    t2 = getInstrumentFromString("Corno in A")
    # bug: intervals can be equal and not equal at the same time.
    print t2.transposition == interval.Interval('m-3')
    
    t3 = getInstrumentFromString("B-Flat Clarinet")
    print t3.transposition == interval.Interval("M-2")
    t4 = getInstrumentFromString("Bb Clarinet")
    print t4.transposition == interval.Interval("M-2")
    t5 = getInstrumentFromString("Eb Clarinet")
    print t5.transposition == interval.Interval("m3")
    '''
    
    
#------------------------------------------------------------------------------
# eof