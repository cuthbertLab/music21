# -*- coding: utf-8 -*-
'''
Methods used to create the data in the NIPS2011 paper.
'''

import json
try:
    import orange, orngTree
except ImportError:
    if __name__ == '__main__':
        print("Orange must be installed to run this.")
        exit()
    orange = None
    orngTree = None

try:
    import BeautifulSoup
    from BeautifulSoup import *
except ImportError:
    pass

from music21 import common
from music21 import features
from music21 import converter

def nipsBuild(useOurExtractors = True, buildSet = 1, evaluationMethod = 'coarse'):
    '''
    Runs a collection of Feature Extractors, especially those related to Harmony (ChordSymbol) bass motion
    in order to classify pop songs from 
    the now-defunct website wikifonia as either early (pre-1960) or recent (post-1980)
    '''    
    leadsheetDir = 'd:/docs/research/music21/nips-2011/wikifonia/wikifonia-'
    
    
    # here are all the pieces by id and their year and billboard chart number (not used)
    # this data found by Beth Hadley
    entries = json.loads('''[{"1024":[2009,48]}, {"1028":[1961,56]}, {"1034":[1986,9]}, {"1054":[1971,12]}, {"1070":[1982,34]}, {"1081":[2006,55]}, {"1099":[1973,11]}, {"1105":[1952,13]}, {"1347":[2003,30]}, {"1384":[1993,27]}, {"1402":[2009,50]}, {"1459":[1969,2]}, {"1722":[1982,2]}, {"1742":[1959,3]}, {"1904":[1964,9]}, {"1905":[1967,18]}, {"1906":[1967,20]}, {"1907":[1964,8]}, {"1912":[1977,44]}, {"1922":[1954,94]}, {"1930":[1999,6]}, {"1934":[1985,10]}, {"1940":[1970,3]}, {"2045":[1961,7]}, {"2049":[1961,12]}, {"2125":[1959,19]}, {"2167":[1965,88]}, {"2170":[1957,68]}, {"2374":[1963,14]}, {"2387":[1950,4]}, {"2405":[1974,2]}, {"2431":[1985,15]}, {"2447":[1960,3]}, {"2448":[1982,28]}, {"2462":[1951,33]}, {"2519":[1965,7]}, {"2521":[1978,23]}, {"2523":[1955,16]}, {"2533":[1976,52]}, {"2546":[1952,50]}, {"2665":[2004,2]}, {"2688":[1973,45]}, {"2709":[2009,5]}, {"2729":[2004,2]}, {"2735":[2009,60]}, {"2742":[1970,98]}, {"2774":[1967,10]}, {"2776":[1952,46]}, {"2777":[1969,47]}, {"2833":[1957,34]}, {"2834":[1957,37]}, {"2838":[1956,8]}, {"2967":[1973,31]}, {"2984":[1987,14]}, {"2985":[1977,41]}, {"2994":[1967,76]}, {"3012":[1963,28]}, {"3153":[1963,5]}, {"3154":[1963,5]}, {"3155":[1965,9]}, {"3157":[1978,36]}, {"3195":[1975,65]}, {"3218":[1992,6]}, {"3226":[1963,58]}, {"3229":[1958,42]}, {"3232":[1979,10]}, {"3241":[1972,3]}, {"3242":[1977,12]}, {"3243":[1970,45]}, {"3275":[1965,8]}, {"3281":[1954,28]}, {"3282":[1991,15]}, {"3285":[1974,33]}, {"3299":[1956,57]}, {"3300":[1953,8]}, {"3301":[1957,47]}, {"3311":[1954,9]}, {"3323":[1954,28]}, {"3324":[1987,14]}, {"3379":[1962,25]}, {"3402":[1961,2]}, {"3409":[1972,12]}, {"3420":[1954,78]}, {"3452":[1971,85]}, {"3466":[1962,46]}, {"3477":[1960,13]}, {"3484":[1983,59]}, {"3532":[1961,15]}, {"3548":[1970,20]}, {"3554":[1981,53]}, {"3558":[1981,62]}, {"3668":[1953,73]}, {"3681":[1954,2]}, {"3687":[1957,11]}, {"3688":[1957,11]}, {"3689":[1962,15]}, {"3690":[1955,17]}, {"3717":[1955,5]}, {"3718":[1962,4]}, {"3719":[1958,48]}, {"3732":[1954,95]}, {"3749":[1953,3]}, {"3755":[1970,93]}, {"3764":[1958,44]}, {"3765":[1974,94]}, {"3772":[1973,71]}, {"3784":[1961,95]}, {"3785":[1950,17]}, {"3786":[1951,15]}, {"3821":[1954,66]}, {"3834":[1963,3]}, {"3845":[1985,65]}, {"3866":[1957,48]}, {"3871":[1950,82]}, {"3911":[1967,23]}, {"3928":[1959,52]}, {"3979":[1989,70]}, {"3980":[1963,10]}, {"4016":[1951,34]}, {"4022":[1956,98]}, {"4044":[1952,54]}, {"4051":[1984,56]}, {"4073":[1980,90]}, {"4117":[1976,1]}, {"4139":[1951,5]}, {"4252":[1950,14]}, {"4286":[1959,12]}, {"4288":[1965,43]}, {"4294":[1961,75]}, {"4318":[1960,10]}, {"4320":[1961,5]}, {"4335":[1966,62]}, {"4341":[1970,41]}, {"4343":[1964,2]}, {"4353":[1961,55]}, {"4354":[1962,21]}, {"4356":[1955,4]}, {"4357":[1966,23]}, {"4400":[1967,52]}, {"4438":[1965,71]}, {"4439":[1951,9]}, {"4462":[1968,42]}, {"4464":[1964,27]}, {"4470":[1987,38]}, {"4492":[1961,31]}, {"4494":[1952,65]}, {"4503":[1953,91]}, {"4504":[1953,35]}, {"4505":[1953,35]}, {"4514":[1970,51]}, {"4537":[1954,21]}, {"4538":[1956,4]}, {"4567":[1962,93]}, {"4575":[1960,19]}, {"4576":[1962,27]}, {"4618":[1998,13]}, {"4621":[1954,67]}, {"4643":[1970,2]}, {"4645":[1966,44]}, {"4649":[1953,40]}, {"4656":[1974,86]}, {"4657":[1984,25]}, {"4679":[1966,33]}, {"4728":[1974,56]}, {"4732":[2005,43]}, {"4740":[1964,33]}, {"4741":[1963,24]}, {"4742":[1970,18]}, {"4750":[1968,2]}, {"4773":[1971,98]}, {"4791":[1966,28]}, {"4795":[1983,96]}, {"4807":[1956,81]}, {"4837":[1950,5]}, {"4889":[1967,84]}, {"4897":[1957,67]}, {"4963":[1991,58]}, {"4978":[1959,51]}, {"4979":[1956,49]}, {"5002":[1956,3]}, {"5023":[1974,60]}, {"5025":[1977,22]}, {"5195":[1954,1]}, {"5228":[1963,65]}, {"5280":[1970,64]}, {"5296":[1955,62]}, {"5300":[1952,43]}, {"5346":[1955,52]}, {"5356":[1981,29]}, {"5367":[1964,54]}, {"5376":[1970,48]}, {"5391":[1982,31]}, {"5394":[1976,30]}, {"5431":[1974,8]}, {"5432":[1962,6]}, {"5480":[1971,49]}, {"5489":[1969,85]}, {"5506":[1960,98]}, {"5522":[1968,50]}, {"5541":[1972,90]}, {"5544":[2001,92]}, {"5547":[1975,70]}, {"5551":[1975,67]}, {"5556":[1999,29]}, {"5567":[1970,80]}, {"5579":[1981,8]}, {"5615":[1972,15]}, {"5631":[1954,81]}, {"5648":[1953,2]}, {"5652":[1950,63]}, {"5653":[1957,98]}, {"5702":[1959,81]}, {"5766":[1956,21]}, {"5768":[1959,47]}, {"5790":[1959,96]}, {"5794":[1957,3]}, {"5798":[1958,94]}, {"5805":[1979,63]}, {"5808":[1958,14]}, {"5810":[2001,5]}, {"5816":[1958,31]}, {"5825":[1959,61]}, {"5837":[1980,5]}, {"5838":[1995,34]}, {"5840":[1974,41]}, {"5841":[1973,35]}, {"5844":[1973,78]}, {"5882":[1954,90]}, {"5883":[1961,63]}, {"5893":[1981,31]}, {"5894":[1981,31]}, {"5936":[1981,30]}, {"5957":[1970,42]}, {"5976":[1992,41]}, {"5983":[1969,21]}, {"5987":[1970,90]}, {"5989":[1975,48]}, {"5990":[1978,37]}, {"6001":[1966,37]}, {"6002":[1969,92]}, {"6022":[1982,77]}, {"6023":[1988,39]}, {"6024":[1977,1]}, {"6042":[1981,2]}, {"6049":[1977,99]}, {"6050":[1956,10]}, {"6052":[1962,77]}, {"6053":[1964,29]}, {"6063":[1957,65]}, {"6065":[1956,15]}, {"6067":[1966,91]}, {"6069":[1987,69]}, {"6073":[1983,53]}, {"6091":[1950,95]}, {"6135":[1962,82]}, {"6151":[1978,18]}, {"6156":[1961,6]}, {"6164":[1954,60]}, {"6169":[1959,54]}, {"6185":[1958,25]}, {"6191":[2005,86]}, {"6239":[1970,24]}, {"6294":[1994,30]}, {"6301":[1952,17]}, {"6354":[2003,3]}, {"6370":[1987,55]}, {"6389":[1961,32]}, {"6398":[1965,15]}, {"6404":[1961,1]}, {"6426":[1992,100]}, {"6430":[1993,32]}, {"6444":[2010,32]}, {"6448":[1958,74]}, {"6476":[1955,12]}, {"6493":[1992,64]}, {"6523":[2007,76]}, {"6528":[1981,18]}, {"6563":[1960,12]}, {"6592":[1998,60]}, {"6689":[1960,20]}, {"6703":[1968,75]}, {"6722":[1955,12]}, {"6773":[1953,100]}, {"6903":[1958,24]}, {"6910":[1962,61]}, {"6961":[1981,35]}, {"6975":[1964,14]}, {"7030":[1958,34]}, {"7038":[1979,26]}, {"7083":[1970,91]}, {"7123":[1957,83]}, {"7228":[1971,2]}, {"7268":[1984,22]}, {"7409":[1994,96]}, {"7418":[1959,98]}, {"7660":[1950,80]}, {"7742":[1999,59]}, {"7790":[1956,14]}, {"7818":[1966,2]}, {"7837":[1972,42]}, {"7838":[1984,15]}, {"7914":[1960,29]}, {"7923":[1950,74]}, {"7925":[1993,87]}, {"7961":[1952,53]}, {"7965":[1959,87]}, {"8006":[1951,4]}, {"8016":[1997,75]}, {"8045":[1987,6]}, {"8103":[2010,74]}, {"8145":[1986,4]}, {"8192":[1970,67]}, {"8216":[1974,35]}, {"8243":[2008,98]}, {"8328":[1976,15]}, {"8364":[1970,65]}, {"8441":[1961,14]}, {"8448":[1962,90]}, {"8557":[1958,48]}, {"8678":[1967,74]}, {"8763":[1955,12]}, {"8855":[1962,74]}, {"8862":[1978,9]}, {"8884":[2009,2]}, {"8887":[2010,18]}, {"8915":[1974,74]}, {"8967":[1974,74]}, {"8999":[1963,3]}, {"9025":[1972,84]}, {"9026":[1971,78]}, {"9177":[1966,50]}, {"9192":[1961,2]}, {"9203":[1960,85]}, {"9224":[1970,69]}, {"9254":[1976,55]}, {"9264":[1973,95]}, {"9266":[1974,31]}, {"9294":[1994,2]}, {"9298":[1969,23]}, {"9322":[1952,81]}, {"9369":[1958,1]}, {"9618":[2007,25]}, {"9652":[2009,63]}, {"9673":[1965,64]}, {"9699":[1987,10]}, {"9883":[1973,67]}, {"9914":[1991,58]}, {"9918":[2010,6]}, {"9945":[1997,32]}, {"9954":[1959,80]}, {"9969":[1966,65]}, {"9983":[1987,14]}, {"9999":[1999,59]}, {"10052":[1969,64]}, {"10075":[1967,49]}, {"10118":[1961,18]}, {"10226":[2009,11]}, {"10234":[1979,14]}, {"10247":[1987,74]}, {"10260":[1970,82]}, {"10265":[1961,7]}, {"10269":[1989,39]}, {"10318":[1978,20]}, {"10320":[1970,35]}, {"10321":[1971,2]}, {"10395":[1968,33]}, {"10466":[1970,12]}, {"10571":[1985,84]}, {"10602":[1963,28]}, {"10604":[1965,25]}, {"10636":[1951,15]}, {"10656":[2010,42]}, {"10663":[1962,1]}, {"10703":[1969,25]}, {"10767":[1959,3]}, {"11007":[1994,31]}, {"11050":[1971,51]}, {"11103":[1986,39]}, {"11150":[1970,36]}, {"11158":[1961,14]}, {"11281":[2009,7]}, {"11284":[1967,41]}, {"11604":[2003,92]}, {"11665":[1992,64]}, {"11667":[1993,18]}, {"11733":[1964,41]}, {"11756":[1951,25]}, {"11767":[1973,66]}, {"11781":[1965,62]}, {"11785":[1979,20]}, {"11807":[1958,26]}, {"11857":[1958,22]}, {"12187":[2009,60]}, {"12275":[1959,98]}, {"12514":[2007,76]}, {"12899":[1958,2]}]''')
    
    entryDict = {}
    for d in entries: 
        sid = d.keys()[0];
        entryDict[int(sid)] = d[sid]
    
    
    ourExtractors = ['cs12', 'p22', 'k1', 'ql1', 'ql2', 'ql3', 'ql4', 'md1', ]
    jSymbolicExtrators = ['m1','m2','m3','m4','m5','m6','m7','m9','m10','m11','m12','m13','m14','m15','m17','m18','m19','r23','r32','r33','r35','p3','p4','p5','p6','p7','p10','p12','p15']

    if useOurExtractors is True:
        FEs = features.extractorsById(ourExtractors)
    else:
        FEs = features.extractorsById(jSymbolicExtrators)
    
    ds = features.DataSet(classLabel='year')
    ds.addFeatureExtractors(FEs)
    
    
    if buildSet == 1:
        halfOfData = entryDict.keys()[0:198]
    else:
        halfOfData = entryDict.keys()[198:]
    
    for wf in halfOfData:  # taking half the data here.... to get the other set do [198:]
        year = entryDict[wf][0]
        
        ## ignore 1960s and 1970s pieces...
        if year < 1961 or year >= 1981: 
            fn = leadsheetDir + str(wf) + '.mxl'
            print (fn, year, entryDict[wf][1])
            s = converter.parse(fn)
            title_id = s.metadata.title
            #cv = year  # if not using coarse but instead using the exact year as the class value
            
            if evaluationMethod == 'coarse':            
                #coarse evaluation (only "old" or "new")
                if year < 1961: 
                    cv = "old" 
                else: 
                    cv = "new"
            else: 
                # fine grained evaluations
                cv = year  # if not using coarse but instead using the exact year as the class value

            ds.addData(s, classValue=cv, id=title_id)
    
    ds.process()
    ds.write('d:/desktop/year7-ourextractors-only.tab')
    
def nipsEvalFine():
    '''
    takes the data from nipsBuild() and runs it through a set of classifiers
    in order to see how well the FEs can classify a piece by year, giving
    an error value to misjudged years.
    
    Coarse evaluations worked much better
    '''
    data1 = orange.ExampleTable('d:/desktop/year1.tab')
    data2 = orange.ExampleTable('d:/desktop/year2.tab')
    
    learners = {}
    learners['maj'] = orange.MajorityLearner
    learners['bayes'] = orange.BayesLearner
    learners['tree'] = orngTree.TreeLearner
    learners['knn'] = orange.kNNLearner
    
    for cName in learners.keys():
        cType = learners[cName]
        for cData, cStr, matchData, matchStr in [
                                                 (data1, 'file1', data2, 'file2'),
                                                 (data2, 'file2', data1, 'file1'),
                                                 ]:
            # train with data1
            classifier = cType(cData)
            mismatch = []
            for i in range(len(matchData)):
                c = classifier(matchData[i])
                mismatch.append(c - int(matchData[i].getclass()))
            stdDev = common.standardDeviation(mismatch)
            print('%s %s: std. deviation %f on %s' % (cStr, cName, stdDev, matchStr))

def nipsEvalCoarse():
    '''
    takes the data from nipsBuild() and runs it through a set of classifiers
    in order to see how well the FEs can classify a piece as old or new.
    
    Worked rather well...
    '''
    data1 = orange.ExampleTable('d:/docs/research/music21/nips-2011/year5-ourExtractors-1.tab')
    data2 = orange.ExampleTable('d:/docs/research/music21/nips-2011/year6-ourExtractors-2.tab')

    #data1 = orange.ExampleTable('d:/docs/research/music21/nips-2011/year7-midi-only-1.tab')
    #data2 = orange.ExampleTable('d:/docs/research/music21/nips-2011/year8-midi-only-2.tab')

    
    learners = {}
    learners['maj'] = orange.MajorityLearner
    learners['bayes'] = orange.BayesLearner
    learners['tree'] = orngTree.TreeLearner
    learners['knn'] = orange.kNNLearner
    
    for cName in learners.keys():
        cType = learners[cName]
        for cData, cStr, matchData, matchStr in [
                                                 (data1, 'file1', data2, 'file2'),
                                                 (data2, 'file2', data1, 'file1'),
                                                 ]:
            # train with data1
            classifier = cType(cData)
            mismatch = 0
            for i in range(len(matchData)):
                c = classifier(matchData[i])
                if c != matchData[i].getclass():
                    mismatch += 1
            print('%s %s: misclassified %s/%s of %s' % (cStr, cName, mismatch, len(matchData), matchStr))

def getLeadsheetDatesFromBillboard():    
    '''
    script to generate a json list matching leadsheet files to their dates. script compiles list of Billboard
    top 100 songs from jamrockentertainment.com, then uses this dictionary to match up titles from 
    leadsheet file. Last updated: 10/6/2011, Beth Hadley
    
    Both the dictionary generated by scraping the website and the json output has been copied into a text file
    and saved so this script shouldn't need to be re-run unless a change has been made. See text file.
    '''
    import os
    try:
        from urllib2 import urlopen
    except ImportError:
        from urllib.request import urlopen # python3
    import copy
    DIR = r'C:\leadsheets'

#     Code below scrapes this website: http://www.jamrockentertainment.com/billboard-music-top-100-songs-listed-by-year.html
#     for their listing of the Billboard 100 songs from 1950 to 2010.
#     
#     Generates an unordered dictionary with the corresponding data: each key in the dictionary is the year, each value is a list
#     of tuples, each tuple includes the song title at index 0 and group/artist at index 1. The list is ordered starting at
#     element 0 by rank, starting with number 1.
    DICT = {}
    tempList = []
    LOWERLIMIT = 1950
    UPPERLIMIT = 2011
    dates = range(LOWERLIMIT, UPPERLIMIT)
    for i in dates:
        if i !=2008 and i != 2009:
            address = 'http://www.jamrockentertainment.com/billboard-music-top-100-songs-listed-by-year/top-100-songs-%s.html' % i
            url = urlopen(address)
            html = url.read()
            soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
            trs = soup.findAll('td')
            song = True
            for td in trs:
                x = str(td.find(text=True))
                words = x.split()
                pretty = words[0]
                words.pop(0)
                for a in words:
                    a.strip()
                    pretty = pretty +" "+ a
                if song == True:
                    try:
                        j = float(x)
                        continue
                    except:
                        song = False
                        y = pretty
                        continue
                if song == False:
                    t = y, pretty
                    tempList.append( t )
                    song = True
        elif i == 2008:
            address = 'http://www.jamrockentertainment.com/billboard-music-top-100-songs-listed-by-year/top-100-songs-%s.html' % i
            url = urlopen(address)
            html = url.read()
            soup = BeautifulSoup(html)
            trs = soup.findAll('span')
            cnt = 0
            titles = []
            groups = []
            for strong in trs:
                x = strong.find(text=True)        
                if "&nbsp" in str(x):
                    x = x.strip('&nbsp;')
                x =  x.strip()
                if cnt < 100:
                    retstring = ""
                    loops = 1
                    for letter in x:
                        if loops > 3:
                            retstring = retstring + letter
                        loops = loops + 1
                    x = retstring
                final = x.strip().lower()
                if cnt < 100:
                    groups.append(final)
                else:
                    titles.append(final)
                cnt = cnt + 1
        
            for title, group in zip(titles, groups):
                title = title.encode('ascii', 'replace')
                title = title.replace('?', "'")
                group = group.encode('ascii', 'replace')
                group = group.replace('?', 'H')
                t = title, group 
                tempList.append( t )
        else: #i=2009
            address = 'http://www.jamrockentertainment.com/billboard-music-top-100-songs-lististed-by-year/top-100-songs-%s.html' % i
            url = urlopen(address)
            html = url.read()
            soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
            trs = soup.findAll('span')
            cnt = 0
            titles = []
            groups = []
            cnt = 0
            for strong in trs:
                x = strong.find(text=True)
                try:
                    j = float(x)
                    continue
                except:
                    if cnt < 100:
                        groups.append(str(x))
                    else:
                        titles.append(str(x))
                cnt = cnt + 1
                
            for title, group in zip(titles, groups):
                t = title, group 
                tempList.append( t )
        
        DICT[str(i)] = copy.deepcopy(tempList)
        tempList = []
        
    #print DICT  
    
    
    LOWERLIMIT = 1000
    UPPERLIMIT = 12938
    indexValues = range(LOWERLIMIT, UPPERLIMIT)
    matches = 0
    rank = 0
    
    outputjson = '\'['
    
    
    for i in indexValues:
        fn = 'wikifonia-%04s.mxl' % i
        fn = fn.replace(' ', '0')
        dst = os.path.join(DIR, fn)
        dates = []
        print (dst)
        if os.path.exists(dst):
            piece = converter.parse(dst)
            for year in DICT:
                    for title, group in DICT[year]:
                        if piece.metadata.movementName.lower() == str(title).lower()   : #or piece.metadata.composer == str(a):
                            #print "FOUND by title! Name", piece.metadata.movementName, "Composer", piece.metadata.composer, str(year)
                            #print dst   
                            dates.append(int(year))                    
                
            if len(dates) > 0:
                date = min(dates) #date of entry
                tempList = DICT[str(date)]
                for x in tempList:
                    for e in x:
                        if e.lower() == piece.metadata.movementName.lower():
                            rank =  (tempList.index(x) + 1 ) #position on Billboard 100
           
                #print "Title:", piece.metadata.movementName, "  Composer:", piece.metadata.composer, "  Date:", date, "  Position on Billboard:", rank
                #print "Title:", piece.metadata.movementName, "  Date:", date
                matches = matches + 1
                outputjson = outputjson + '{\"%s":[%s,%s]}, ' % (i, date, rank)
        if (i % 500) == 0:
            j = ((i-1000) / (11938.00)) * 100.00
            print ('%s %%' %round(j, 2))
            print (outputjson)
                
                    
                    
    foo = len(outputjson) - 2
    outputjson = outputjson[0:foo] + ']\''
    print (outputjson)
    print ("FINISHED! Found this many matches: ", matches)
    
def probabilityOfChance():
    '''
    The experiment: 214 music xml leadsheets from wikifonia
    were categorized into two groups, dating from 1950-60 (120)
    or post 1980 (94). The probability that an algorithm could
    randomly determine the date correctly is about 0.507. This
    is above the standard 0.5 due to the slighlty different 
    quantity of old vs. new songs
    
    The program below runs the experiment to correctly
    guess a piece's date (old vs. new). The experiment is run 10,000
    times, then the average correct calculated and found to be 0.507
    The program then uses this experimentally-determined 'p' value
    to calculate the probability that the computer would have randomly
    found the answer correctly 69% of the time or more, which was the
    result found when using music21 feature extraction on the 214
    pieces to classify their dates.
    
    the typical result of this program is a probabilty of 3.5e-08 +/- 0.2
    which is far too unlikely to be the result of random chance, thus
    proving the validity of the music21 feature extraction.
    '''
    from math import factorial
    import random
    
    TOTAL_TRIALS = 214
    NUM_OLD_PIECES = 120
    NUM_NEW_PIECES = TOTAL_TRIALS - NUM_OLD_PIECES
    
    def getPFromExperiment():
        old = 0
        new = 1
        avg = 0.0
        for unused_trials in range(0, 10000):
            #generating the answerKey
            answerKey = []
            for i in range(0,NUM_OLD_PIECES):
                answerKey.append(old)
            for i in range(0,NUM_NEW_PIECES):
                answerKey.append(new)
            random.shuffle(answerKey)
            
            #generating the answers, then comparing them
            #to answerKey and calculating the percentage
            #guessed correctly
            numCorrect = 0.0
            guessesOld = []
            guessesNew = []
            for answer in answerKey:
                guess = random.randint(0,1)
                #the algorithm is smart - it knows
                #there is a maximum number of times it
                #can guess old vs. new, and if it
                #has reached that maximum,
                #it won't guess that value
                if guess == 0:
                    guessesOld.append(guess)
                else:
                    guessesNew.append(guess)
                if len(guessesOld) > NUM_OLD_PIECES:
                    guess = new
                elif len(guessesNew) > NUM_NEW_PIECES:
                    guess = old
                if answer == guess:
                    numCorrect +=1
            avg += numCorrect / TOTAL_TRIALS
    
        p = avg / 10000.0
        return p
    
    def BinomialCoefficient(n,k):
        if n > k:
            b = factorial(n) / (factorial(k)*factorial(n-k))
            return b
    
    def BinomialProbability(n,k,p,q):
        nchoosek = BinomialCoefficient(n,k)
        ptothek = pow(p,k)
        qtothenminusk = pow(q, (n-k) )
        return nchoosek * ptothek * qtothenminusk
    
    k = 148 #number of times music21 found correct date (successes)
    n = TOTAL_TRIALS #total number of trials
    p = getPFromExperiment()
    print ('The probability of a successful guess, as calculated by previous experiment', p)
    q = 1-p
    prob = 0.0
    #Probability of getting 148 or more correct (sum
    #the probabilty as k increses from 148 to 214)
    for k in range(k,TOTAL_TRIALS):
        prob = prob + BinomialProbability(n,k,p,q)
    
    print ('The probability that the computer would guess correctly 69% or more of the time', prob)

if __name__ == '__main__':
    #nipsBuild()
    nipsEvalCoarse()
