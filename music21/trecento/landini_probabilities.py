'''Module to determine how often we would expect to have Francesco\'s cadences happen by chance
'''

import random

def getLetter(i):
    '''according to distribution of starting tenor notes of Landini cadences'''
    if i < 16: return "A"
    if i < 35: return "C"
    if i < 67: return "D"
    if i < 69: return "E"
    if i < 85: return "F"
    return "G"

def findsame(total = 1000):
    '''find out how often the first note and second note should be the same 
    according to chance, given Landini\'s distribution of pitches.
    '''
    same = 0
    for i in range(0,total):
        (n1, n2) = (random.randrange(138), random.randrange(138))
        if getLetter(n1) == getLetter(n2):
            same += 1
    return same

def multipleFindsame(total = 10000):
    '''find out how often findsame percentage meets or exceeds Landini\'s same count
    which is either 64 out of 138 (for A cadences) or 49 (for B cadences)
    '''
    mulFS = 0
    for i in range(0, total):
        same = findsame(138)
        if same >= 64: 
            mulFS += 1
    return mulFS
