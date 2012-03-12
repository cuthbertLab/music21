import inspect
import pprint

from lxml import etree #need to install lxml
from music21 import instrument
from music21.braille.translation import lookup

#-------------------------------------------------------------------------------

def music():
    f = open('music.html')
    html = etree.HTML(f.read())
    
    french = {}
    german = {}
    italian = {}
    spanish = {}
    abbr = {}
    
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
            french[cell] = [u" ".join(s.split()) for s in allSols[1]]
            german[cell] = [u" ".join(s.split()) for s in allSols[2]]
            italian[cell] = [u" ".join(s.split()) for s in allSols[3]]
            spanish[cell] = [u" ".join(s.split()) for s in allSols[4]]
            abbr[cell] = [u" ".join(s.split()) for s in allSols[5]]

    allClasses = [tup[1] for tup in inspect.getmembers(instrument, inspect.isclass) if issubclass(tup[1], instrument.Instrument)]
    num = 0
    for classDef in allClasses:
        i = classDef()
        try:
            val = german[i.bestName().lower()]
            #print i, val
            num+=1
        except:
            pass
        
    allDicts = {"French": french, "German": german, "Italian": italian, "Spanish": spanish, "Abbreviations": abbr}
    for dict in allDicts.values():
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

    print "french = ", 
    pprint.pprint(french)
    print "\ngerman = ", 
    pprint.pprint(german)
    print "\nitalian = ", 
    pprint.pprint(italian)
    print "\nspanish = ", 
    pprint.pprint(spanish)
    print "\nabbreviations = ", 
    pprint.pprint(abbr)

#-------------------------------------------------------------------------------

def dolmetsch():
    f = open('dolmetsch.html')
    html = etree.HTML(f.read())
    
    french = {}
    german = {}
    italian = {}
    spanish = {}
    
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
            italian[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[1]]
            german[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[2]]
            french[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[3]]
            spanish[cell] = [u" ".join(s.split("(")[0].split()) for s in allSols[4]]

    allClasses = [tup[1] for tup in inspect.getmembers(instrument, inspect.isclass) if issubclass(tup[1], instrument.Instrument)]
    num = 0
    for classDef in allClasses:
        i = classDef()
        try:
            val = german[i.bestName().lower()]
            #print i, val
            num+=1
        except:
            pass
        
    allDicts = {"French": french, "German": german, "Italian": italian, "Spanish": spanish}
    for dict in allDicts.values():
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

    merge(lookup.french, french)
    merge(lookup.german, german)
    merge(lookup.italian, italian)
    merge(lookup.spanish, spanish)
    
    print "french = ", 
    pprint.pprint(french)
    print "\ngerman = ", 
    pprint.pprint(german)
    print "\nitalian = ", 
    pprint.pprint(italian)
    print "\nspanish = ", 
    pprint.pprint(spanish)
        
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

if __name__ == "__main__":
    dolmetsch()

#------------------------------------------------------------------------------
# eof