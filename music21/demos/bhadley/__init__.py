#Disclaimer: this is very messy code and probably very inneficient....I know. 
#I will clean it up/make my coding practices much better as soon as I have time
#this weekend...but the analysis works. Just adjust the main section at bottom
#for the analysis you'd like to run
#TODO: lots of error handling...
#TODO: documentation


from music21 import *
from sets import Set
from decimal import *
import os, sys
import json

getcontext().prec = 6

def getPieceDataRootOnly(piece): 
    #TODO: this method should be combined with the method for analysis by Bass motion because
    #there are many similar components....
    '''
    input is a stream with chords, output is a list of the motion by percentage
    that occured between adjacent bass notes
    format of output: list of eleven decimals, the first six corresponding to
    motion by positive 1 through 6, the remaining five corresponding to motion
    by negative 1 through 5, respectively
    Example: [0, Decimal('17.3913'), 0, Decimal('4.34783'), Decimal('30.4348'), 0, Decimal('47.8261'), 0, 0, 0, 0]'''
    DICT = {}
    list = []
    totalintervals = 0
    PieceData = []
    
    oldpiece = harmony.getduration(piece)
    try:
        piece = oldpiece.expandRepeats()
    except:
        piece = oldpiece
    foo = piece.flat.getElementsByClass(harmony.ChordSymbol)
    cnt = -1
    for x in foo:
        if cnt == -1:
            last = x
            cnt = cnt + 1
            continue
        aNote = note.Note( str(x.root ) )
        bNote = note.Note( str(last.root))
        aInterval = interval.notesToChromatic(bNote, aNote)
        if aInterval.undirected != 0:
            if BYDURATION:
                boo = 0
                while boo < x.duration.quarterLength:
                    list.append( aInterval.undirected )
                    boo = boo + 1
            else:
                if aInterval.undirected != 0: 
                    list.append( aInterval.undirected)
        last = x
    #create a sorted set (really just the list above with all duplicates removed)
    uniqueSet = set(list)
    newlist = []
    for x in uniqueSet:
        newlist.append(x)
    newlist.sort()
    
    lastitem = 0
    totalintervals = len(list)
    
    for newitem in newlist:
        while (abs(lastitem + 1) != abs(newitem)):
            PieceData.append(0)
            lastitem = abs(lastitem + 1)
        PieceData.append( Decimal(100) * Decimal(list.count(newitem)) / Decimal(totalintervals) )
        lastitem = newitem

    #if the last item appended to PieceData is not 6, this means
    #that there is no motion above that lastitem, so we should stick
    #the value 0 in to PieceData
    if lastitem < 12:
        indexvalues = range(lastitem + 1, 12)
        for x in indexvalues:
            PieceData.append(0)
    return PieceData

def getPieceDataRootandBass(piece): #TODO: combine with method above
    
    lastbass = False
    list = []
    totalintervals = 0
    inversioncounter = 0
    PieceData = []
    oldpiece = harmony.getduration(piece)
    try:
        piece = oldpiece.expandRepeats()
    except:
        piece = oldpiece
    foo = piece.flat.getElementsByClass(harmony.Harmony)
    cnt = -1
    for x in foo:
        if cnt == -1:
            last = x
            cnt = cnt + 1
            continue
        if lastbass:
            bNote = note.Note( str(last.bass))
        else:
            bNote = note.Note( str(last.root))
            
        if x.bass != None: #bass exists
            aNote = note.Note(  str(x.bass ) )
            inversioncounter = inversioncounter + 1
            lastbass = True
        else:
            aNote = note.Note( str(x.root ) )
            lastbass = False
            
        aInterval = interval.notesToChromatic(bNote, aNote)

        if aInterval.undirected != 0:
            if BYDURATION:
                boo = 0
                while boo < x.duration.quarterLength:
                    list.append( aInterval.undirected )
                    boo = boo + 1
            else:
                if aInterval.undirected != 0: 
                    list.append( aInterval.undirected)
        last = x

       
        uniqueSet = set(list)
        newlist = []
        for x in uniqueSet:
            newlist.append(x)
        newlist.sort()
    
        lastitem = 0
        PieceData = []
        totalintervals = len(list)
        for newitem in newlist:
            while (abs(lastitem + 1) != abs(newitem)):
                PieceData.append(0)
                lastitem = abs(lastitem + 1)
            PieceData.append( Decimal(100) * Decimal(list.count(newitem)) / Decimal(totalintervals) )
            lastitem = newitem
        if lastitem < 12:
            indexvalues = range(lastitem + 1, 12)
            for x in indexvalues:
                PieceData.append(0)
    
    return PieceData

def getPercentageInversions(piece): #returns #inversions in piece / total #inversions (not by duration)
    inversioncounter = 0
    try:
        piece = piece.expandRepeats()
    except:
        piece = piece
    foo = piece.flat.getElementsByClass(harmony.Harmony)
    for x in foo:         
        if x.bass != None: #bass exists
            inversioncounter = inversioncounter + 1
    return Decimal(100) * Decimal(inversioncounter) / Decimal(len(foo))


def getListOfFilesByNumber(lowerlimit, upperlimit): #returns list of numbers between certain range....really just
    #a re-written range function with my variable names
    rangeValues = range(lowerlimit, upperlimit)
    return getValidFiles(rangeValues)

def getListOfFilesByDate(lowerdate, upperdate):
    #returns list of files that fit provided date specifications
    entryDict = {}
    entries = json.loads('[{"1024":[2009,48]}, {"1028":[1961,56]}, {"1034":[1986,9]}, {"1054":[1971,12]}, {"1070":[1982,34]}, {"1081":[2006,55]}, {"1099":[1973,11]}, {"1105":[1952,13]}, {"1347":[2003,30]}, {"1384":[1993,27]}, {"1402":[2009,50]}, {"1459":[1969,2]}, {"1722":[1982,2]}, {"1742":[1959,3]}, {"1904":[1964,9]}, {"1905":[1967,18]}, {"1906":[1967,20]}, {"1907":[1964,8]}, {"1912":[1977,44]}, {"1922":[1954,94]}, {"1930":[1999,6]}, {"1934":[1985,10]}, {"1940":[1970,3]}, {"2045":[1961,7]}, {"2049":[1961,12]}, {"2125":[1959,19]}, {"2167":[1965,88]}, {"2170":[1957,68]}, {"2374":[1963,14]}, {"2387":[1950,4]}, {"2405":[1974,2]}, {"2431":[1985,15]}, {"2447":[1960,3]}, {"2448":[1982,28]}, {"2462":[1951,33]}, {"2519":[1965,7]}, {"2521":[1978,23]}, {"2523":[1955,16]}, {"2533":[1976,52]}, {"2546":[1952,50]}, {"2665":[2004,2]}, {"2688":[1973,45]}, {"2709":[2009,5]}, {"2729":[2004,2]}, {"2735":[2009,60]}, {"2742":[1970,98]}, {"2774":[1967,10]}, {"2776":[1952,46]}, {"2777":[1969,47]}, {"2833":[1957,34]}, {"2834":[1957,37]}, {"2838":[1956,8]}, {"2967":[1973,31]}, {"2984":[1987,14]}, {"2985":[1977,41]}, {"2994":[1967,76]}, {"3012":[1963,28]}, {"3153":[1963,5]}, {"3154":[1963,5]}, {"3155":[1965,9]}, {"3157":[1978,36]}, {"3195":[1975,65]}, {"3218":[1992,6]}, {"3226":[1963,58]}, {"3229":[1958,42]}, {"3232":[1979,10]}, {"3241":[1972,3]}, {"3242":[1977,12]}, {"3243":[1970,45]}, {"3275":[1965,8]}, {"3281":[1954,28]}, {"3282":[1991,15]}, {"3285":[1974,33]}, {"3299":[1956,57]}, {"3300":[1953,8]}, {"3301":[1957,47]}, {"3311":[1954,9]}, {"3323":[1954,28]}, {"3324":[1987,14]}, {"3379":[1962,25]}, {"3402":[1961,2]}, {"3409":[1972,12]}, {"3420":[1954,78]}, {"3452":[1971,85]}, {"3466":[1962,46]}, {"3477":[1960,13]}, {"3484":[1983,59]}, {"3532":[1961,15]}, {"3548":[1970,20]}, {"3554":[1981,53]}, {"3558":[1981,62]}, {"3668":[1953,73]}, {"3681":[1954,2]}, {"3687":[1957,11]}, {"3688":[1957,11]}, {"3689":[1962,15]}, {"3690":[1955,17]}, {"3717":[1955,5]}, {"3718":[1962,4]}, {"3719":[1958,48]}, {"3732":[1954,95]}, {"3749":[1953,3]}, {"3755":[1970,93]}, {"3764":[1958,44]}, {"3765":[1974,94]}, {"3772":[1973,71]}, {"3784":[1961,95]}, {"3785":[1950,17]}, {"3786":[1951,15]}, {"3821":[1954,66]}, {"3834":[1963,3]}, {"3845":[1985,65]}, {"3866":[1957,48]}, {"3871":[1950,82]}, {"3911":[1967,23]}, {"3928":[1959,52]}, {"3979":[1989,70]}, {"3980":[1963,10]}, {"4016":[1951,34]}, {"4022":[1956,98]}, {"4044":[1952,54]}, {"4051":[1984,56]}, {"4073":[1980,90]}, {"4117":[1976,1]}, {"4139":[1951,5]}, {"4252":[1950,14]}, {"4286":[1959,12]}, {"4288":[1965,43]}, {"4294":[1961,75]}, {"4318":[1960,10]}, {"4320":[1961,5]}, {"4335":[1966,62]}, {"4341":[1970,41]}, {"4343":[1964,2]}, {"4353":[1961,55]}, {"4354":[1962,21]}, {"4356":[1955,4]}, {"4357":[1966,23]}, {"4400":[1967,52]}, {"4438":[1965,71]}, {"4439":[1951,9]}, {"4462":[1968,42]}, {"4464":[1964,27]}, {"4470":[1987,38]}, {"4492":[1961,31]}, {"4494":[1952,65]}, {"4503":[1953,91]}, {"4504":[1953,35]}, {"4505":[1953,35]}, {"4514":[1970,51]}, {"4537":[1954,21]}, {"4538":[1956,4]}, {"4567":[1962,93]}, {"4575":[1960,19]}, {"4576":[1962,27]}, {"4618":[1998,13]}, {"4621":[1954,67]}, {"4643":[1970,2]}, {"4645":[1966,44]}, {"4649":[1953,40]}, {"4656":[1974,86]}, {"4657":[1984,25]}, {"4679":[1966,33]}, {"4728":[1974,56]}, {"4732":[2005,43]}, {"4740":[1964,33]}, {"4741":[1963,24]}, {"4742":[1970,18]}, {"4750":[1968,2]}, {"4773":[1971,98]}, {"4791":[1966,28]}, {"4795":[1983,96]}, {"4807":[1956,81]}, {"4837":[1950,5]}, {"4889":[1967,84]}, {"4897":[1957,67]}, {"4963":[1991,58]}, {"4978":[1959,51]}, {"4979":[1956,49]}, {"5002":[1956,3]}, {"5023":[1974,60]}, {"5025":[1977,22]}, {"5195":[1954,1]}, {"5228":[1963,65]}, {"5280":[1970,64]}, {"5296":[1955,62]}, {"5300":[1952,43]}, {"5346":[1955,52]}, {"5356":[1981,29]}, {"5367":[1964,54]}, {"5376":[1970,48]}, {"5391":[1982,31]}, {"5394":[1976,30]}, {"5431":[1974,8]}, {"5432":[1962,6]}, {"5480":[1971,49]}, {"5489":[1969,85]}, {"5506":[1960,98]}, {"5522":[1968,50]}, {"5541":[1972,90]}, {"5544":[2001,92]}, {"5547":[1975,70]}, {"5551":[1975,67]}, {"5556":[1999,29]}, {"5567":[1970,80]}, {"5579":[1981,8]}, {"5615":[1972,15]}, {"5631":[1954,81]}, {"5648":[1953,2]}, {"5652":[1950,63]}, {"5653":[1957,98]}, {"5702":[1959,81]}, {"5766":[1956,21]}, {"5768":[1959,47]}, {"5790":[1959,96]}, {"5794":[1957,3]}, {"5798":[1958,94]}, {"5805":[1979,63]}, {"5808":[1958,14]}, {"5810":[2001,5]}, {"5816":[1958,31]}, {"5825":[1959,61]}, {"5837":[1980,5]}, {"5838":[1995,34]}, {"5840":[1974,41]}, {"5841":[1973,35]}, {"5844":[1973,78]}, {"5882":[1954,90]}, {"5883":[1961,63]}, {"5893":[1981,31]}, {"5894":[1981,31]}, {"5936":[1981,30]}, {"5957":[1970,42]}, {"5976":[1992,41]}, {"5983":[1969,21]}, {"5987":[1970,90]}, {"5989":[1975,48]}, {"5990":[1978,37]}, {"6001":[1966,37]}, {"6002":[1969,92]}, {"6022":[1982,77]}, {"6023":[1988,39]}, {"6024":[1977,1]}, {"6042":[1981,2]}, {"6049":[1977,99]}, {"6050":[1956,10]}, {"6052":[1962,77]}, {"6053":[1964,29]}, {"6063":[1957,65]}, {"6065":[1956,15]}, {"6067":[1966,91]}, {"6069":[1987,69]}, {"6073":[1983,53]}, {"6091":[1950,95]}, {"6135":[1962,82]}, {"6151":[1978,18]}, {"6156":[1961,6]}, {"6164":[1954,60]}, {"6169":[1959,54]}, {"6185":[1958,25]}, {"6191":[2005,86]}, {"6239":[1970,24]}, {"6294":[1994,30]}, {"6301":[1952,17]}, {"6354":[2003,3]}, {"6370":[1987,55]}, {"6389":[1961,32]}, {"6398":[1965,15]}, {"6404":[1961,1]}, {"6426":[1992,100]}, {"6430":[1993,32]}, {"6444":[2010,32]}, {"6448":[1958,74]}, {"6476":[1955,12]}, {"6493":[1992,64]}, {"6523":[2007,76]}, {"6528":[1981,18]}, {"6563":[1960,12]}, {"6592":[1998,60]}, {"6689":[1960,20]}, {"6703":[1968,75]}, {"6722":[1955,12]}, {"6773":[1953,100]}, {"6903":[1958,24]}, {"6910":[1962,61]}, {"6961":[1981,35]}, {"6975":[1964,14]}, {"7030":[1958,34]}, {"7038":[1979,26]}, {"7083":[1970,91]}, {"7123":[1957,83]}, {"7228":[1971,2]}, {"7268":[1984,22]}, {"7409":[1994,96]}, {"7418":[1959,98]}, {"7660":[1950,80]}, {"7742":[1999,59]}, {"7790":[1956,14]}, {"7818":[1966,2]}, {"7837":[1972,42]}, {"7838":[1984,15]}, {"7914":[1960,29]}, {"7923":[1950,74]}, {"7925":[1993,87]}, {"7961":[1952,53]}, {"7965":[1959,87]}, {"8006":[1951,4]}, {"8016":[1997,75]}, {"8045":[1987,6]}, {"8103":[2010,74]}, {"8145":[1986,4]}, {"8192":[1970,67]}, {"8216":[1974,35]}, {"8243":[2008,98]}, {"8328":[1976,15]}, {"8364":[1970,65]}, {"8441":[1961,14]}, {"8448":[1962,90]}, {"8557":[1958,48]}, {"8678":[1967,74]}, {"8763":[1955,12]}, {"8855":[1962,74]}, {"8862":[1978,9]}, {"8884":[2009,2]}, {"8887":[2010,18]}, {"8915":[1974,74]}, {"8967":[1974,74]}, {"8999":[1963,3]}, {"9025":[1972,84]}, {"9026":[1971,78]}, {"9177":[1966,50]}, {"9192":[1961,2]}, {"9203":[1960,85]}, {"9224":[1970,69]}, {"9254":[1976,55]}, {"9264":[1973,95]}, {"9266":[1974,31]}, {"9294":[1994,2]}, {"9298":[1969,23]}, {"9322":[1952,81]}, {"9369":[1958,1]}, {"9618":[2007,25]}, {"9652":[2009,63]}, {"9673":[1965,64]}, {"9699":[1987,10]}, {"9883":[1973,67]}, {"9914":[1991,58]}, {"9918":[2010,6]}, {"9945":[1997,32]}, {"9954":[1959,80]}, {"9969":[1966,65]}, {"9983":[1987,14]}, {"9999":[1999,59]}, {"10052":[1969,64]}, {"10075":[1967,49]}, {"10118":[1961,18]}, {"10226":[2009,11]}, {"10234":[1979,14]}, {"10247":[1987,74]}, {"10260":[1970,82]}, {"10265":[1961,7]}, {"10269":[1989,39]}, {"10318":[1978,20]}, {"10320":[1970,35]}, {"10321":[1971,2]}, {"10395":[1968,33]}, {"10466":[1970,12]}, {"10571":[1985,84]}, {"10602":[1963,28]}, {"10604":[1965,25]}, {"10636":[1951,15]}, {"10656":[2010,42]}, {"10663":[1962,1]}, {"10703":[1969,25]}, {"10767":[1959,3]}, {"11007":[1994,31]}, {"11050":[1971,51]}, {"11103":[1986,39]}, {"11150":[1970,36]}, {"11158":[1961,14]}, {"11281":[2009,7]}, {"11284":[1967,41]}, {"11604":[2003,92]}, {"11665":[1992,64]}, {"11667":[1993,18]}, {"11733":[1964,41]}, {"11756":[1951,25]}, {"11767":[1973,66]}, {"11781":[1965,62]}, {"11785":[1979,20]}, {"11807":[1958,26]}, {"11857":[1958,22]}, {"12187":[2009,60]}, {"12275":[1959,98]}, {"12514":[2007,76]}, {"12899":[1958,2]}]')
    for d in entries: 
        iden = d.keys()[0]
        entryDict[int(iden)] = d[iden]
 
    rangeValues = []
    for piece in entryDict:
        try:
            x = entryDict[piece]
            if x[0] >= lowerdate and x[0] <= upperdate:
                rangeValues.append(piece)
        except:
            pass
    
    return getValidFiles(rangeValues)

def getValidFiles(rangeValues):
    #checks wikifonia folder to see if input list files are actually present in folder
    #returns only index values of files that are present in folder
    indexValues = []
    for i in rangeValues:
        fn = 'wikifonia-%04s.mxl' % i
        fn = fn.replace(' ', '0')
        dst = os.path.join(DIR, fn)
        if os.path.exists(dst):
            indexValues.append(dst)
    return indexValues

def getPercentageMotion(DICT):
    #returns the average motion between all files in dictionary that are passed in
    #input parameter: Dictionary: {'C:\\wikifoniawithchords\\wikifonia-4139.mxl': [Decimal('3.10078'), Decimal('2.32558') ....
    #output - nicely formatted list of motion [{'+1': 3.6}, {'-1': '-'}, {'+2': 6.0}, {'-2': 0.7}, {'+3': 4.4}, {'-3': 1.4}, {'+4': 2.2}, {'-4': 2.4}, {'+5': 46.4}, {'-5': 31.3}, {'+6': 1.7}]
    sums = [0,0,0,0,0,0,0,0,0,0,0] #only indicate 1-6 (motion by 1-6)
    if len(DICT) > 0:
        for key in DICT:
            list = DICT[key]
            for x in range(0,11):
                sums[x] = Decimal(sums[x]) + Decimal(list[x])
        
        for x in range(0,11):
            sums[x] = Decimal(sums[x]) / Decimal(len(DICT))
    
        outputlist = []
        counter = 1
        for x in sums:
            if counter < 6:
                if x == 0:
                    outputlist.append({'+' + str(counter) : '-'})
                else:
                    outputlist.append({'+' + str(counter) : round(x,1)})
                if sums[11-counter] == 0:
                    outputlist.append({'-' + str(counter) : '-'})
                else:
                    outputlist.append({'-' + str(counter) : round(sums[11-counter],1)}) 
            if counter == 6:
                if x == 0:
                    outputlist.append({'+' + str(counter) : '-'})
                else:
                    outputlist.append({'+' + str(counter) : round(x,1)})
            counter = counter + 1
    return outputlist



if __name__ == '__main__':

    DIR = 'C:\wikifoniawithchords' #directory that contains all wikifonia files with chords; you will have to
    #run analysis with new wikifonia folder I sent you (includes only wikifonia files with chords defined)
    BYDURATION = False #do you want to run analysis by duration or not?
    allpiecesdict = {}
    try:
        #iteratelist = getListOfFilesByNumber(1000,1010) #for analysis by file number
        #iteratelist = getListOfFilesByDate(1980,2012) #for analysis by dates
    
        for i in iteratelist:
            print i
            piece = converter.parse(i)
            
            #allpiecesdict[str(i)] = getPieceDataRootOnly(converter.parse(i)) #analysis by root only

            #allpiecesdict[str(i)] = getPieceDataRootandBass(converter.parse(i)) #analysis by bass only (including no inversions)
            
            #if getPercentageInversions(piece) > 10: #analysis by inversions (indicate %inversions here)
            #    allpiecesdict[str(i)] = getPieceDataRootandBass(converter.parse(i)) 
        print "Analysis of %s pieces \n" %len(allpiecesdict)
        print "Motion  Percentage"
        for dict in getPercentageMotion(allpiecesdict):
            for key, value in dict.items():
                print " %1s %9s" % (key, value)
    except:
        print "ERROR during analysis: Uncomment some lines in code to run analysis or change DIR name to valid path"