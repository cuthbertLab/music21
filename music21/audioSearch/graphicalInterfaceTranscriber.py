# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.graphicalInterfaceTranscriber.py
# Purpose:      Graphical interface for the score follower
#
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

_DOC_IGNORE_MODULE_OR_PACKAGE = True

from music21 import scale
import threading
import Queue as queue
from music21.audioSearch import transcriber
import Tkinter 
 
 
class SFApp():
   
    def __init__(self, master):
        self.master = master
        self.frame = Tkinter.Frame(master)
        #self.frame.pack()
        self.master.wm_title("Transcriber")        
          
        self.sizeButton = 11
        

        
        
        def callback():
            try:
                self.nameSong = '%s.wav' % boxName.get()          
                self.durationSong = int(boxDuration.get()) 
                
                self.textVar2 = Tkinter.StringVar()
                self.textVar2.set('%s - %d sec.' % (self.nameSong, self.durationSong)) 
                self.label2 = Tkinter.Label(self.master, textvariable=self.textVar2, width = 2*self.sizeButton)
                self.label2.grid(row=5,column=0,columnspan=2)
                
                
                self.buttonStart = Tkinter.Button(self.master, text="Start Recording", width=self.sizeButton,command=self.startRecording, bg='green')
                self.buttonStart.grid(row=6,column=0,columnspan=2)                
                
                self.textVarComments.set('Now, you can press recording')                      

            except:
                print('no he pogut')



        self.textVarName = Tkinter.StringVar()
        boxName = Tkinter.Entry(self.master,width=2*self.sizeButton,textvariable=self.textVarName)
        self.textVarName.set('exampleSong')
        boxName.grid(row=0,column=1)
        
        self.textDuration = Tkinter.StringVar()
        boxDuration = Tkinter.Entry(self.master,width=2*self.sizeButton,textvariable=self.textDuration)
        self.textDuration.set('20')
        boxDuration.grid(row=1,column=1)     

        self.var = Tkinter.IntVar()
        self.checkButton = Tkinter.Checkbutton(self.master, text="Show the file after recording" ,variable=self.var)
        self.var.set(1)
        self.checkButton.grid(row=3,column=0,columnspan=2)
        
        self.var2 = Tkinter.IntVar()
        self.checkButton = Tkinter.Checkbutton(self.master, text="Save the file after recording" ,variable=self.var2)
        self.var2.set(0)
        self.checkButton.grid(row=4,column=0,columnspan=2)
   
        self.buttonSubmit = Tkinter.Button(self.master, text="Submit", width=self.sizeButton, command=callback,bg='orange')
        self.buttonSubmit.grid(row=2,column=0,columnspan=2)
     
        self.textTitle = Tkinter.StringVar()
        self.textTitle.set('Title:') 
        self.labelTitle = Tkinter.Label(self.master,width=self.sizeButton,textvariable=self.textTitle)
        self.labelTitle.grid(row=0,column=0)
        
        self.textDuration = Tkinter.StringVar()
        self.textDuration.set('Duration:') 
        self.labelDuration = Tkinter.Label(self.master,width=self.sizeButton,textvariable=self.textDuration)
        self.labelDuration.grid(row=1,column=0)
                        
        self.textVarComments = Tkinter.StringVar()
        self.textVarComments.set('Type the name of the song') 
        self.labelComments = Tkinter.Label(self.master,width=3*self.sizeButton,textvariable=self.textVarComments)
        self.labelComments.grid(row=7,column=0,columnspan=2,rowspan=2)
        
        self.buttonStart = Tkinter.Button(self.master, text="Start Recording",state='disable', width=self.sizeButton,command=self.startRecording, bg='green')
        self.buttonStart.grid(row=6,column=0,columnspan=2)
        
        
        print('Initialized!')
        
    def startRecording (self):
        self.buttonStart = Tkinter.Button(self.master, text="Start Recording",state='disable', width=self.sizeButton,command=self.startRecording, bg='green')
        self.buttonStart.grid(row=6,column=0,columnspan=2)        
        
        self.show = self.var.get()
        if self.show == 1:
            self.show = True
        else:
            self.show = False
            
        storeSong = self.var2.get()
        if storeSong == 0:
            self.nameSong = None
            
        print('nom final', self.nameSong)   
        self.textVarComments.set('Recording...') 
        self.rt=RecordThread(self.show,self.nameSong,self.durationSong)            
        self.rt.daemon=True
        self.rt.start() # the 2nd thread starts here       
        
        self.master.after(self.durationSong, self.waitingRoutine)
    
          
    def waitingRoutine (self):
        self.rt.queue.get()
        self.buttonStart.destroy()
        self.buttonStart = Tkinter.Button(self.master, text="Start Recording", width=self.sizeButton,command=self.startRecording, bg='green')
        self.buttonStart.grid(row=6,column=0,columnspan=2)        
        self.textVarComments.set('Finished!') 
 

class RecordThread(threading.Thread):
    def __init__(self,show,saveFile,seconds):
        threading.Thread.__init__(self)
        self.show = show
        self.saveFile = saveFile
        self.seconds = seconds
        self.queue = queue.Queue()
        
    def run(self):
        self.myScore = transcriber.runTranscribe(show=self.show, plot=False, useMic=True, seconds=self.seconds, useScale=scale.ChromaticScale('C4'), saveFile=self.saveFile)
        self.queue.put(1)

if __name__ == "__main__":
    root = Tkinter.Tk()
    sfapp = SFApp(root)
    root.mainloop()
