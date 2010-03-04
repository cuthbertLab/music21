#-------------------------------------------------------------------------------
# Name:         ratios.py
# Purpose:      interval ratios; possible to be moved
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import math
import doctest, unittest
from decimal import Decimal
import fractions

import music21
import music21.common




class IntervalRatio(object):
    
    def __init__(self, numerator = 1, denominator = 1):
        '''
        >>> a = IntervalRatio(4,3)
        '''
        self.unreduced_num = Decimal(numerator)
        self.unreduced_den = Decimal(denominator)
        GCD = fractions.gcd(numerator, denominator)
        
        self.numerator = Decimal(numerator/GCD)
        self.denominator = Decimal(denominator/GCD)
        self.decimal = self.numerator/self.denominator
        octaveless = denominator
        octaves = 0
        while ((octaveless * 2) < numerator):
            octaveless = octaveless * 2
            octaves += 1
        octaveless_GCD = fractions.gcd(numerator, octaveless)
        self.octaveless_num = numerator/octaveless_GCD
        self.octaveless_den = octaveless/octaveless_GCD
        self.octaves = octaves
        self.octaveless_decimal = self.octaveless_num/self.octaveless_den
        self.ratio = str(self.numerator) + ":" + str(self.denominator)
        self.ratio_unreduced = str(self.unreduced_num) + ":" + str(self.unreduced_den)
        self.ratio_octaveless = str(self.octaveless_num) + ":" + str(self.octaveless_den)

    def add(self, otherInt):
        return IntervalRatio(self.unreduced_num * otherInt.unreduced_num, self.unreduced_den * otherInt.unreduced_den)

    def sub(self, otherInt):
        return IntervalRatio(self.unreduced_num * otherInt.unreduced_den, self.unreduced_den * otherInt.unreduced_num)
     
    def show(self):
        print (str(self.numerator) + ":" + str(self.denominator))

    def show_unreduced(self):
        print (str(self.unreduced_num) + ":" + str(self.unreduced_den))

    def show_octaveless(self):
        print (str(self.octaveless_num) + ":" + str(self.octaveless_den))

    def times(self, repeat = 1):
        tempInt = self
        while repeat > 1:
            repeat = repeat - 1 
            tempInt = self.add(tempInt)
        return tempInt

    def reduce(self):
        return IntervalRatio(self.octaveless_num, self.octaveless_den)

#-------------------------------------------------------------------------------
class ETIntervalRatio(object):

    twelfthroot = 1.059463094359
    cent = 1.00577789507

    def __init__(self, halfsteps = 0):
        self.halfsteps = halfsteps
        self.decimal = 2 ** (halfsteps/12.0)
        
def centsCompare(obj1, obj2):
    centsdiff = math.log(float(obj1.decimal)/float(obj2.decimal), 2) * 1200
    return '%6.1f' % centsdiff



#-------------------------------------------------------------------------------
def testOld():

    P8 = IntervalRatio(2,1)
    P5 = IntervalRatio(3,2)
    P4 = IntervalRatio(4,3)
    WT = P5.sub(P4)
    print("Whole tone in ratio " + WT.ratio)
    print("Whole tone in decimal " + str(WT.decimal))
    
    P5_12times = P5.times(12)
    print("12 Perfect fifths exceeds an octave by " + P5_12times.ratio_octaveless)
    
    P8_7times = P8.times(7)
    print("your Wolf fifth will be too small by " + centsCompare(P5_12times, P8_7times) + " cents")
    
    #P11 = Interval(8,3)
    #P11.show()
    #P11.show_octaveless()
    #print P11.decimal
    #print P11.octaveless_decimal
    #print P11.octaves
    
    ET = ETIntervalRatio
    
    P5et = ET(7)
    print("A pythagorean Perfect 5 is  " + centsCompare(P5,P5et) + " cents above an ET P5")
    
    WTet = ET(2)
    print("A pythagorean Whole tone is " + centsCompare(WT,WTet) + " cents above an ET WT")
    
    ditone = WT.add(WT)
    M3et = ET(4)
    M3ji = IntervalRatio(5,4)
    print("")
    print("Ditone to M3 in ET        : " + centsCompare(ditone, M3et) + " cents higher;")
    print("M3 in ET to 5:4 major 3rd : " + centsCompare(M3et, M3ji) + " cents higher;")
    print("Ditone to 5:4 major 3rd   : " + centsCompare(ditone, M3ji) + " cents higher;")
    
    print("")
    
    Diminished4 = P4.times(8).reduce()
    print("A diminished fourth is " + str(Diminished4.octaveless_decimal))
    print("The difference in cents between a Just Major 3rd and a Pythagorean d4 is " + centsCompare(M3ji, Diminished4))
    
    majorST = IntervalRatio(17,16)
    minorST = IntervalRatio(18,17)
    
    collat7 = IntervalRatio(7,4)
    collat7sub = collat7.add(majorST)
    ET7th = ET(10)
    unison = ET(0)
    
    #print centsCompare(minorST.add(majorST), unison)
    
# if __name__ == "__main__":
#     test()

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        P8 = IntervalRatio(2,1)
        P5 = IntervalRatio(3,2)
        P4 = IntervalRatio(4,3)
        WT = P5.sub(P4)
        post = "Whole tone in ratio " + WT.ratio
        post = "Whole tone in decimal " + str(WT.decimal)
        
        P5_12times = P5.times(12)
        post = "12 Perfect fifths exceeds an octave by " + P5_12times.ratio_octaveless
        
        P8_7times = P8.times(7)
        post = "your Wolf fifth will be too small by " + centsCompare(P5_12times, P8_7times) + " cents"
        
        #P11 = Interval(8,3)
        #P11.show()
        #P11.show_octaveless()
        #print P11.decimal
        #print P11.octaveless_decimal
        #print P11.octaves
        
        ET = ETIntervalRatio
        
        P5et = ET(7)
        post = "A pythagorean Perfect 5 is  " + centsCompare(P5,P5et) + " cents above an ET P5"
        
        WTet = ET(2)
        post = "A pythagorean Whole tone is " + centsCompare(WT,WTet) + " cents above an ET WT"
        
        ditone = WT.add(WT)
        M3et = ET(4)
        M3ji = IntervalRatio(5,4)
        post = "Ditone to M3 in ET        : " + centsCompare(ditone, M3et) + " cents higher;"
        post = "M3 in ET to 5:4 major 3rd : " + centsCompare(M3et, M3ji) + " cents higher;"
        post = "Ditone to 5:4 major 3rd   : " + centsCompare(ditone, M3ji) + " cents higher;"
        
        
        Diminished4 = P4.times(8).reduce()
        post = "A diminished fourth is " + str(Diminished4.octaveless_decimal)
        post = "The difference in cents between a Just Major 3rd and a Pythagorean d4 is " + centsCompare(M3ji, Diminished4)
        
        majorST = IntervalRatio(17,16)
        minorST = IntervalRatio(18,17)
        
        collat7 = IntervalRatio(7,4)
        collat7sub = collat7.add(majorST)
        ET7th = ET(10)
        unison = ET(0)

if __name__ == "__main__":    
    music21.mainTest(Test)


