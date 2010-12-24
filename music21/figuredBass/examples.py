#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         examples.py
# Purpose:      music21 class which allows running of test cases
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

from music21.figuredBass import realizer
from music21 import note


def exampleA():
    '''
    This was one of my (Jose Cabal-Ugaz) 21M.302 assignments.
    The figured bass was composed by Charles Shadle.
    '''
    fb = realizer.FiguredBass('3/2', 'C')
    
    n1 = note.Note('C3')
    n2 = note.Note('D3')
    n3 = note.Note('E3')
    n4 = note.Note('F3')
    n5 = note.Note('C#3')
    n6 = note.Note('D3')
    n7 = note.Note('B2')
    n8 = note.Note('C3')
    n9 = note.Note('A#2')
    n10 = note.Note('B2')
    n11 = note.Note('B2')
    n12 = note.Note('E3')

    n1.quarterLength = 2.0
    n2.quarterLength = 2.0  
    n3.quarterLength = 2.0
    n4.quarterLength = 2.0
    n5.quarterLength = 2.0
    n6.quarterLength = 2.0
    n7.quarterLength = 2.0
    n8.quarterLength = 2.0  
    n9.quarterLength = 2.0
    n10.quarterLength = 4.0
    n11.quarterLength = 2.0
    n12.quarterLength = 6.0
    
    fb.addElement(n1)
    fb.addElement(n2, '6')
    fb.addElement(n3, '6')
    fb.addElement(n4, '6')
    fb.addElement(n5, '7-,5,3')
    fb.addElement(n6)
    fb.addElement(n7, '6#,5,3')
    fb.addElement(n8, '6')
    fb.addElement(n9, '7,5,3#')
    fb.addElement(n10, '6,4')
    fb.addElement(n11, '5#,3#')
    fb.addElement(n12)
    
    return fb

def exampleB():
    '''
    Retrieved from page 114 of 'The Music Theory Handbook' by Marjorie Merryman.
    '''
    fb = realizer.FiguredBass('4/4', 'D', 'minor')
    
    n1 = note.Note('D3')
    n2 = note.Note('A3')
    n3 = note.Note('B-3')
    n4 = note.Note('F3')
    n5 = note.Note('G3')
    n6 = note.Note('A3')
    n7 = note.Note('D3')
    
    n7.quarterLength = 2.0
    
    fb.addElement(n1)
    fb.addElement(n2, '7,5,3#')
    fb.addElement(n3)
    fb.addElement(n4, '6')
    fb.addElement(n5, '6')
    fb.addElement(n6, '7,5,3#')
    fb.addElement(n7)
    
    return fb
    
def exampleC():
    '''
    Retrieved from page 114 of 'The Music Theory Handbook' by Marjorie Merryman.
    '''
    fb = realizer.FiguredBass('4/4', 'F#', 'minor')
    
    n1 = note.Note('F#2')
    n2 = note.Note('G#2')
    n3 = note.Note('A2')
    n4 = note.Note('F#2')
    n5 = note.Note('B2')
    n6 = note.Note('C#3')
    n7 = note.Note('F#2')

    n7.quarterLength = 2.0
    
    fb.addElement(n1)
    fb.addElement(n2, '#6')
    fb.addElement(n3, '6')
    fb.addElement(n4)
    fb.addElement(n5, '6,5')
    fb.addElement(n6, '7,5,3#')
    fb.addElement(n7)
    
    return fb

def exampleD():
    '''
    Another one of my (Jose Cabal-Ugaz) assignments from 21M.302.
    This figured bass was composed by Charles Shadle.
    '''
    fb = realizer.FiguredBass('3/4', 'b', 'minor')
    
    #Measure 1
    n1 = note.Note('B2')
    n2 = note.Note('C#3')
    n3 = note.Note('D3')
    fb.addElement(n1)
    fb.addElement(n2, '#6')
    fb.addElement(n3, '6')
    
    #Measure2
    n4 = note.Note('E3')
    n4.quarterLength = 2.0
    n5 = note.Note('E#3')
    fb.addElement(n4)
    fb.addElement(n5, '6,5,#3')
    
    #Measure 3
    n6 = note.Note('F#3')
    n6.quarterLength = 2.0
    n7 = note.Note('F#3')
    fb.addElement(n6, '6,4')
    fb.addElement(n7, '5,#3')
    
    #Measure 4
    n8 = note.Note('G3')
    n8.quarterLength = 2.0
    n9 = note.Note('E3')
    fb.addElement(n8)
    fb.addElement(n9, '6')
    
    #Measure 5
    n10 = note.Note('F#3')
    n10.quarterLength = 2.0
    n11 = note.Note('E3')
    fb.addElement(n10, '6,4')
    fb.addElement(n11, '#4,2')
    
    #Measure 6
    n12 = note.Note('D3')
    n12.quarterLength = 2.0
    n13 = note.Note('E3')
    fb.addElement(n12, '6')
    fb.addElement(n13, '7,5,#3')
    
    #Measure 7
    n14 = note.Note('A2')
    n14.quarterLength = 3.0
    fb.addElement(n14)
    
    return fb


if __name__ == "__main__":
    #exampleA(), exampleB(), exampleC(), exampleD()
    fb = exampleA() #Set up the figured bass
    fb.solve()
    fb.showRandomSolutions(20)
