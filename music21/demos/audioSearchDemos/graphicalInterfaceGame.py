# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.graphicalInterfaceTranscriber.py
# Purpose:      Graphical interface for the repetition game
#
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

_DOC_IGNORE_MODULE_OR_PACKAGE = True

import math
from music21.audioSearch import * #@UnusedWildImport
from music21.demos.audioSearchDemos import repetitionGame

from music21.ext import six
if six.PY3:
    import tkinter as Tkinter # @UnusedImport
else:
    import Tkinter #  @UnresolvedImport @Reimport
 
 
class SFApp():
   
    def __init__(self, master):
        self.master = master
        self.frame = Tkinter.Frame(master)
        #self.frame.pack()
        self.master.wm_title("Repetition game")        
          
        self.sizeButton = 11    
        self.startScreen()

                
    def startScreen(self):
        master = self.master        
        self.textRules = Tkinter.StringVar()
        self.boxRules = Tkinter.Label(master,textvariable=self.textRules)
        self.textRules.set("Welcome to the music21 game!\n Rules:\n Two players: the first one plays a note.\n The second one has to play the first note and a new one.\n Continue doing the same until one fails.")
        self.boxRules.grid(row=0,column=0,columnspan=4,rowspan=5,sticky=Tkinter.W)       
 
        self.buttonAccept = Tkinter.Button(master, text="Accept", width=self.sizeButton,command=self.callback, bg='white')
        self.buttonAccept.grid(row=8,column=1,columnspan=2)       
        
        print('Initialized!')
        
        
    def callback(self):
              
        master = self.master
        self.boxRules.destroy()
        self.buttonAccept.destroy()
        
        self.textP1 = Tkinter.StringVar()
        self.boxName1 = Tkinter.Label(self.master,textvariable=self.textP1)
        self.textP1.set('Player 1')
        self.boxName1.grid(row=0,column=0)
        
        self.textP1Result = Tkinter.StringVar()
        self.boxName2 = Tkinter.Label(master,textvariable=self.textP1Result)
        self.textP1Result.set('')
        self.boxName2.grid(row=2,column=0)

        self.textP2 = Tkinter.StringVar()
        self.boxName3 = Tkinter.Label(master,textvariable=self.textP2)
        self.textP2.set('Player 2')
        self.boxName3.grid(row=0,column=2)
        
        self.textP2Result = Tkinter.StringVar()
        self.boxName4 = Tkinter.Label(master,textvariable=self.textP2Result)
        self.textP2Result.set('')
        self.boxName4.grid(row=2,column=2)
        
        self.textRound = Tkinter.StringVar()
        self.boxName5 = Tkinter.Label(master,width=2*self.sizeButton,textvariable=self.textRound)
        self.textRound.set('Round')
        self.boxName5.grid(row=2,column=1)
        
        self.textFinal = Tkinter.StringVar()
        self.boxName6 = Tkinter.Label(master,textvariable=self.textFinal)
        self.textFinal.set('')
        self.boxName6.grid(row=4,column=0,columnspan=3)
        
        self.canvas1 = Tkinter.Canvas(master, width=40, height=40)
        self.canvas1.create_oval(1,1,40,40,fill='red')
        self.canvas1.grid(row=1,column=0)
        
        self.canvas2 = Tkinter.Canvas(master, width=40, height=40)
        self.canvas2.create_oval(1,1,40,40,fill='red')
        self.canvas2.grid(row=1,column=2)
               
        self.buttonStart = Tkinter.Button(master, text="Start Recording", width=self.sizeButton,command=self.startGame, bg='green')
        self.buttonStart.grid(row=3,column=0,columnspan=3)
    
    def startGame(self):
        #master = self.master
        self.good = True
        self.textFinal.set('WAIT...')
        #self.boxName6.grid(row=4,column=0,columnspan=3) 
        self.rG = repetitionGame.repetitionGame()
        self.good = True
        self.textFinal.set('GO!')
        self.master.after(0,self.mainLoop)
        
        
    def mainLoop(self):
        #master = self.master
        

        if self.good == True:
            print('rounddddddddddddasdasdadsadad',self.rG.round)
            self.textRound.set('Round %d' %(self.rG.round+1))
            self.counter = math.pow(-1, self.rG.round)
            if self.counter == 1: #player 1
                self.canvas1.create_oval(1,1,40,40,fill='green')
                self.canvas1.grid(row=1,column=0)

                self.canvas2.create_oval(1,1,40,40,fill='red')
                self.canvas2.grid(row=1,column=2)                

            else:
                self.canvas1.create_oval(1,1,40,40,fill='red')
                self.canvas1.grid(row=1,column=0)

                self.canvas2.create_oval(1,1,40,40,fill='green')
                self.canvas2.grid(row=1,column=2)       

                
            self.good = self.rG.game()
            self.master.after(10,self.mainLoop)   
        else:            
            if self.counter == -1:
                self.textP1Result.set('WINNER!')
                #boxName.grid(row=2,column=0)
                self.textP2Result.set('LOSER')
                #boxName.grid(row=2,column=2) 
                self.canvas1.create_oval(1,1,40,40,fill='yellow')
                self.canvas1.grid(row=1,column=0)                

                self.canvas2.create_oval(1,1,40,40,fill='grey')
                self.canvas2.grid(row=1,column=2) 
            else:     
                self.textP1Result.set('LOSER')
                self.textP2Result.set('WINNER!')

                self.canvas1.create_oval(1,1,40,40,fill='grey')
                self.canvas1.grid(row=1,column=0)                
                #self.canvas2.destroy()
                self.canvas2.create_oval(1,1,40,40,fill='yellow')
                self.canvas2.grid(row=1,column=2) 

            self.textFinal.set('Another game?')
            self.boxName6.grid(row=4,column=0,columnspan=3)
        
if __name__ == "__main__":
    root = Tkinter.Tk()
    sfapp = SFApp(root)
    root.mainloop()
