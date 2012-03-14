# -*- coding: utf-8 -*-

import pprint
import re

#from lxml import etree #need to install lxml
from music21.braille.translation import tlnTables
from music21.braille.translation import tlnLookup

#-------------------------------------------------------------------------------

def music():
    """
    http://www.music.vt.edu/musicdictionary/appendix/translations/Translations.html
    """
    f = open('websites/music.html')
    html = etree.HTML(f.read())
    
    englishFrench = {}
    englishGerman = {}
    englishItalian = {}
    englishSpanish = {}
    englishAbbreviation = {}
    
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
            englishFrench[cell] = [u" ".join(s.split()) for s in allSols[1]]
            englishGerman[cell] = [u" ".join(s.split()) for s in allSols[2]]
            englishItalian[cell] = [u" ".join(s.split()) for s in allSols[3]]
            englishSpanish[cell] = [u" ".join(s.split()) for s in allSols[4]]
            englishAbbreviation[cell] = [u" ".join(s.split()) for s in allSols[5]]

    allDicts = [englishFrench, englishGerman, englishItalian, englishSpanish, englishAbbreviation]
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

    print "englishFrench = ", 
    pprint.pprint(englishFrench)
    print "\nenglishGerman = ", 
    pprint.pprint(englishGerman)
    print "\nenglishItalian = ", 
    pprint.pprint(englishItalian)
    print "\nenglishSpanish = ", 
    pprint.pprint(englishSpanish)
    print "\nenglishAbbreviations = ", 
    pprint.pprint(englishAbbreviation)

#-------------------------------------------------------------------------------

def dolmetsch():
    """
    http://www.dolmetsch.com/musictheory29.htm#translatednames
    """
    f = open('websites/dolmetsch.html')
    html = etree.HTML(f.read())
    
    englishFrench = {}
    englishGerman = {}
    englishItalian = {}
    englishSpanish = {}
    
    table = html.iter("tr")
    for row in table:
        allCols = list(row.iter("td"))
        allSols = []
        for col in allCols:
            items = [td.text.lower() for td in col.iter("td") if td.text is not None]
            items.extend([br.tail.lower() for br in col.iter("br") if br.tail is not None])
            allSols.append([unicode(s.encode("latin_1")) for s in items])
        for cell in allSols[0]:
            cell = u" ".join(cell.split("(")[0].split())
            englishItalian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishGerman[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]
            englishFrench[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[3]]
            englishSpanish[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[4]]

    allDicts = [englishFrench, englishGerman, englishItalian, englishSpanish]
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

    merge(tlnTables.englishFrench, englishFrench)
    merge(tlnTables.englishGerman, englishGerman)
    merge(tlnTables.englishItalian, englishItalian)
    merge(tlnTables.englishSpanish, englishSpanish)
    
    print "englishFrench = ", 
    pprint.pprint(englishFrench)
    print "\nenglishGerman = ", 
    pprint.pprint(englishGerman)
    print "\nenglishItalian = ", 
    pprint.pprint(englishItalian)
    print "\nenglishSpanish = ", 
    pprint.pprint(englishSpanish)

#-------------------------------------------------------------------------------

def dolmetsch2():
    """
    http://www.dolmetsch.com/musictheory29.htm#instrumentabbrev
    """
    f = open('websites/dolmetsch2.html')
    html = etree.HTML(f.read())
    
    englishAbbreviation = {}
    
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
            englishAbbreviation[cell] = items
    
    allDicts = [englishAbbreviation]
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

    merge(tlnTables.englishAbbreviation, englishAbbreviation)
    print "englishAbbreviation = ", 
    pprint.pprint(englishAbbreviation)

#-------------------------------------------------------------------------------

def yale():
    """
    http://www.library.yale.edu/cataloging/music/instname.htm#wind
    """
    f = open('websites/yale.html')
    html = etree.HTML(f.read())
    
    englishFrench = {}
    englishGerman = {}
    englishItalian = {}
    englishSpanish = {}
    englishRussian = {}
    
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
            englishFrench[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishGerman[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]
            englishItalian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[3]]
            englishRussian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[4]]
            englishSpanish[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[5]]

    allDicts = [englishFrench, englishGerman, englishItalian, englishSpanish, englishRussian]
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

    merge(tlnTables.englishFrench, englishFrench)
    merge(tlnTables.englishGerman, englishGerman)
    merge(tlnTables.englishItalian, englishItalian)
    merge(tlnTables.englishSpanish, englishSpanish)
    merge(tlnTables.englishRussian, englishRussian)
    
    print "englishFrench = ", 
    pprint.pprint(englishFrench)
    print "\nenglishGerman = ", 
    pprint.pprint(englishGerman)
    print "\nenglishItalian = ", 
    pprint.pprint(englishItalian)
    print "\nenglishSpanish = ", 
    pprint.pprint(englishSpanish)
    print "\nenglishRussian = ", 
    pprint.pprint(englishRussian)

#-------------------------------------------------------------------------------

def ukItalian():
    """
    http://www.musictheory.org.uk/res-musical-terms/italian-musical-terms.php
    """
    f = open('websites/ukItalian.html')
    html = etree.HTML(f.read())
    
    englishItalian = {}
    englishAbbreviation = {}

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
            englishAbbreviation[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishItalian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]

    allDicts = [englishItalian, englishAbbreviation]
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

    merge(tlnTables.englishItalian, englishItalian)
    merge(tlnTables.englishAbbreviation, englishAbbreviation)

    print "englishItalian = ", 
    pprint.pprint(englishItalian)
    print "\nenglishAbbreviations = ", 
    pprint.pprint(englishAbbreviation)

#-------------------------------------------------------------------------------

def ukGerman():
    """
    http://www.musictheory.org.uk/res-musical-terms/german-musical-terms.php
    """
    f = open('websites/ukGerman.html')
    html = etree.HTML(f.read())
    
    englishGerman = {}
    englishAbbreviation = {}

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
            englishAbbreviation[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishGerman[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]

    allDicts = [englishGerman, englishAbbreviation]
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

    merge(tlnTables.englishGerman, englishGerman)
    merge(tlnTables.englishAbbreviation, englishAbbreviation)

    print "englishGerman = ", 
    pprint.pprint(englishGerman)
    print "\nenglishAbbreviations = ", 
    pprint.pprint(englishAbbreviation)

#-------------------------------------------------------------------------------

def ukFrench():
    """
    http://www.musictheory.org.uk/res-musical-terms/french-musical-terms.php
    """
    f = open('websites/ukFrench.html')
    html = etree.HTML(f.read())
    
    englishFrench = {}
    englishAbbreviation = {}

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
            englishAbbreviation[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            englishFrench[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]

    allDicts = [englishFrench, englishAbbreviation]
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

    merge(tlnTables.englishFrench, englishFrench)

    print "englishFrench = ", 
    pprint.pprint(englishFrench)

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

#-------------------------------------------------------------------------------

def rewriteLookup():
    from music21.braille import translation
    import os
    fn = translation.__path__[0] + os.path.sep + "tlnLookup.py"
    f = open(fn, "w")
    f.write("# -*- coding: utf-8 -*-\n")
    f.write("#-------------------------------------------------------------------------------\n")
    f.write("# Name:         {0}\n".format(fn))
    f.write("# Purpose:      Bidirectional musical translation\n")
    f.write("# Authors:      Jose Cabal-Ugaz\n")
    f.write("#\n")
    f.write("# Copyright:    (c) 2012 The music21 Project\n")
    f.write("# License:      LGPL\n")
    f.write("#-------------------------------------------------------------------------------\n")
    f.write("# WARNING: Do not update file. Generated automatically.\n# Add or subtract elements from tlnTables.py instead.\n\n")
    f.write("from music21.braille.translation import tlnTables\n\n")
    f.write("englishFrench = tlnTables.englishFrench\n")
    f.write("englishGerman = tlnTables.englishGerman\n")
    f.write("englishItalian = tlnTables.englishItalian\n")
    f.write("englishSpanish = tlnTables.englishSpanish\n")
    f.write("englishRussian = tlnTables.englishRussian\n")
    f.write("englishAbbreviation = tlnTables.englishAbbreviation\n\n")
    f.write("englishToAll = \\\n")
    f.write(englishToAll())
    f.write("\n\nallToEnglish = \\\n")
    f.write(allToEnglish())
    f.close()
    
def englishToAll():
    allDicts = [tlnTables.englishFrench,tlnTables.englishGerman,tlnTables.englishAbbreviation,
                tlnTables.englishItalian,tlnTables.englishSpanish, tlnTables.englishRussian]
    masterDict = {}
    
    for (key, value) in sorted(tlnTables.englishFrench.items()):
        if key not in masterDict:
            masterDict[key] = {}
        masterDict[key]["french"] = value
    for (key, value) in sorted(tlnTables.englishGerman.items()):
        if key not in masterDict:
            masterDict[key] = {}
        masterDict[key]["german"] = value
    for (key, value) in sorted(tlnTables.englishItalian.items()):
        if key not in masterDict:
            masterDict[key] = {}
        masterDict[key]["italian"] = value
    for (key, value) in sorted(tlnTables.englishSpanish.items()):
        if key not in masterDict:
            masterDict[key] = {}
        masterDict[key]["spanish"] = value
    for (key, value) in sorted(tlnTables.englishRussian.items()):
        if key not in masterDict:
            masterDict[key] = {}
        masterDict[key]["russian"] = value
    for (key, value) in sorted(tlnTables.englishAbbreviation.items()):
        if key not in masterDict:
            masterDict[key] = {}
        masterDict[key]["abbreviation"] = value
        
    return pprint.pformat(masterDict)

def allToEnglish():
    allDicts = [tlnTables.englishFrench,tlnTables.englishGerman,tlnTables.englishAbbreviation,
                tlnTables.englishItalian,tlnTables.englishSpanish, tlnTables.englishRussian]
    masterDict = {}
    
    for (key, value) in sorted(tlnTables.englishFrench.items()):
        for trans in value:
            masterDict[trans] = key
    for (key, value) in sorted(tlnTables.englishGerman.items()):
        for trans in value:
            masterDict[trans] = key
    for (key, value) in sorted(tlnTables.englishItalian.items()):
        for trans in value:
            masterDict[trans] = key
    for (key, value) in sorted(tlnTables.englishSpanish.items()):
        for trans in value:
            masterDict[trans] = key
    for (key, value) in sorted(tlnTables.englishRussian.items()):
        for trans in value:
            masterDict[trans] = key
    for (key, value) in sorted(tlnTables.englishAbbreviation.items()):
        for trans in value:
            masterDict[trans] = key
        
    return pprint.pformat(masterDict)

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

def getInstrumentFromString(name):
    pass

#------------------------------------------------------------------------------

if __name__ == "__main__":
    pass
    #rewriteLookup()
    #for each bestName instrument, go through englishToAll keys and look for 
    #bestName in each of them.
    #print translate("Sostenuto")

#------------------------------------------------------------------------------
# eof