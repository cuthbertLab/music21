# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.graphicalInterfaceSF.py
# Purpose:      Graphical interface for the score follower
#
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


from music21 import corpus
from music21 import converter
from music21 import environment
from music21 import scale, stream, note, pitch
import threading
import Queue as queue
import Tkinter
import time
import math

_missingImport = []
try:
    from PIL import Image as PILImage
    from PIL import ImageTk as PILImageTk
except ImportError:
    _missingImport.append('PIL')

 
from music21.audioSearch.base import *
from music21.audioSearch import recording
from music21.audioSearch import scoreFollower
 
 
 
 
 # TO DO
 # the same name for the score and the song!!!!
 
class SFApp():
   
    def __init__(self, master):
        if 'PIL' in _missingImport:
            raise music21.Music21Exception("Need PIL installed to run Score Follower")
        self.master = master
        self.frame = Tkinter.Frame(master)
        #self.frame.pack()
        self.master.wm_title("Score follower - music21")
        
        self.scoreNameSong = 'scores/d luca gloria_Page_' #'d:/desktop/Saint-Saens-Clarinet-Sonata/Saint-Saens-Clarinet-Sonata_Page_'  #'scores/test_pages_'         
        self.format='tiff'#'jpg'
        self.nameRecordedSong = 'luca/gloria' #'d:/desktop/Saint-Saens-Clarinet-Sonata/saint-saens.xml'#
        self.pageMeasureNumbers = [] # get directly from score - the last one is the last note of the score
        self.totalPagesScore = 1
        self.currentPage = 1
        self.pagesScore = []     
        self.phimage = []
        self.canvas = [] 
        self.listNamePages = []
        self.hits = 0
        self.isMoving = False
        self.firstTime = True
        
        self.sizeButton = 11
        self.x = 600#300#800
        self.y = 780#500#1200 
    
        self.filenameRequest()

    def filenameRequest(self):
        master = self.master
        self.textVarName = Tkinter.StringVar()
        self.box = Tkinter.Entry(master, width=2*self.sizeButton, textvariable=self.textVarName)
        self.textVarName.set(self.scoreNameSong)
        self.box.grid(row=0,column=3,columnspan=2)
        #box.pack()
                            
        self.buttonSubmit = Tkinter.Button(master, text="Submit score name", 
                                           width=2*self.sizeButton, command=self.startMainCanvas)
        self.buttonSubmit.grid(row=1,column=3,columnspan=2,padx=0)
                
                
        self.textVar3 = Tkinter.StringVar()
        self.textVar3.set('example: scores/d luca gloria_Page_') 
        self.label3 = Tkinter.Label(master, width=3*self.sizeButton, textvariable=self.textVar3)
        self.label3.grid(row=6,column=3,columnspan=2,rowspan=4)
    
    def startMainCanvas(self):
        self.scoreNameSong = self.box.get()
        self.initializeScore()
        try:
            self.initializeName()                
        except IOError:
            print 'no he pogut'
            print 'nom',self.scoreNameSong
        self.initializeGraphicInterface()
        print 'Initialized!'
        
        
        
    def initializeName(self):   
        self.newSize = [self.x, self.y]
        
        for i in range(self.totalPagesScore):
            numberLength = len(str(self.totalPagesScore))
            namePage = '%s%s.%s' % (str(self.scoreNameSong), str(i + 1).zfill(numberLength), self.format)
            
            self.listNamePages.append(namePage)
            pilPage = PILImage.open(namePage)
            if pilPage.mode != "RGB":
                pilPage = pilPage.convert("RGB")
            pilPage = self.cropBorder(pilPage)
            self.pagesScore.append(pilPage.resize(self.newSize, PILImage.ANTIALIAS))
            self.phimage.append(PILImageTk.PhotoImage(self.pagesScore[i]))                 
      
    def cropBorder(self, img, minColor=240, maxColor=256):
        colorRange = range(minColor, maxColor)
        data = img.getdata()

        resX = img.size[0]
        resY = img.size[1]
        leftCut = 0
        topCut = 0
        bottomCut = 0
        rightCut = 0

        #Find top
        for i in range(0, len(data), 4):
            if data[i][0] not in colorRange and data[i][1] not in colorRange and data[i][2] not in colorRange:
                topCut = int(i/resX)
                break     
        #Find bottom
        for i in range(len(data)-1, 0, -4):
            if data[i][0] not in colorRange and data[i][1] not in colorRange and data[i][2] not in colorRange:
                bottomCut = int((len(data) - i)/resX)
                break     
                  
        #Find left
        stop = False
        for xPos in range(0, resX, 4):  # check every 4th pixel
            for yPos in range(0, resY, 4): 
                pixelPosition = yPos * resX + xPos
                if data[pixelPosition][0] not in colorRange and \
                   data[pixelPosition][1] not in colorRange and \
                   data[pixelPosition][2] not in colorRange:
                    leftCut = xPos                 
                    stop = True
                    break                   
            if stop:
                break

        #Find right
        stop = False
        for xPos in range(resX-1, 0, -4):  # check every 4th pixel
            for yPos in range(0, resY, 4): 
                pixelPosition = yPos * resX + xPos
                if data[pixelPosition][0] not in colorRange and \
                   data[pixelPosition][1] not in colorRange and \
                   data[pixelPosition][2] not in colorRange:
                    rightCut = resX - xPos + 1                 
                    stop = True
                    break
            if stop:
                break

        margin = int(resX * 0.03) # leave border 3% of the size

        leftCut = leftCut - margin 
        topCut = topCut - margin
        bottomCut = bottomCut - margin
        rightCut = rightCut - margin
        if leftCut < 0: 
            leftCut = 0
        if topCut < 0: 
            topCut = 0
        if bottomCut < 0:
            bottomCut = 0
        if rightCut < 0:
            rightCut = 0
        #print (leftCut, topCut, rightCut, bottomCut)
        img = img.crop((leftCut, topCut, resX-rightCut, resY-bottomCut)) 
        return img
        
        
    def initializeScore(self):
        try:
            score = converter.parse(self.nameRecordedSong).parts[0]
        except converter.ConverterException:
            score = corpus.parse(self.nameRecordedSong).parts[0]
        self.scorePart = score
        self.pageMeasureNumbers = [0] # first measure is 0 in case of pickup
        for e in score.flat:
            if 'PageLayout' in e.classes:
                self.pageMeasureNumbers.append(e.measureNumber)
        lastMeasure = score.getElementsByClass('Measure')[-1].measureNumber
        self.pageMeasureNumbers.append(lastMeasure)
        self.totalPagesScore = len(self.pageMeasureNumbers)-1
        #print self.pageMeasureNumbers

        scNotes = score.flat.notesAndRests
        noteCounter=1
        pageCounter=0
        middlePagesCounter=0
        self.middlePages=[]
        self.beginningPages=[]
        doneThisPage = -1
        for i in scNotes:
            imn = i.measureNumber
            if imn >= self.pageMeasureNumbers[pageCounter]:
                self.beginningPages.append(noteCounter)
                pageCounter +=1
                doneThisPage = imn
                if pageCounter >= self.totalPagesScore:
                    pageCounter == self.totalPagesScore
            if middlePagesCounter<self.totalPagesScore and imn == math.floor((self.pageMeasureNumbers[middlePagesCounter+1]+self.pageMeasureNumbers[middlePagesCounter])/2):
                self.middlePages.append(noteCounter)
                middlePagesCounter +=1
            noteCounter +=1
        print "beginning of the pages",self.beginningPages
        print 'middles of the pages',self.middlePages
                                                                                  
    def initializeGraphicInterface(self):
        master = self.master

        self.separation = math.floor(self.x / 8)
        self.positionxLeft = math.floor(self.x / 2)
        self.positionyLeft = math.floor(self.y / 2)
        self.positionxRight = math.floor(1.5 * self.x + self.separation)
        self.positionyRight = math.floor(self.y / 2) 
        self.positionx3rd = math.floor(2.5 * self.x + 2 * self.separation)
        self.positiony3rd = math.floor(self.y / 2)
        self.sizeCanvasx = 2 * self.x + self.separation
        self.sizeCanvasy = self.y
    
        
        self.canvas1 = Tkinter.Canvas(master, borderwidth=1, width=self.sizeCanvasx, height=self.sizeCanvasy, bg="black")
        self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[0], tag='leftImage')
        
        if self.totalPagesScore >= 2:
            self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[1], tag='rightImage')
        self.canvas1.grid(row=1,column=0,columnspan=3,rowspan=7)
        #self.canvas1.pack()#(side='left')       
        self.textVarTitle = Tkinter.StringVar()
        self.textVarTitle.set('%s' %self.scoreNameSong) 
        self.labelTitle = Tkinter.Label(master, textvariable=self.textVarTitle)
        self.labelTitle.grid(row=0,column=1)
        
        self.textVar2 = Tkinter.StringVar()
        self.textVar2.set('Right page: %d/%d' % (self.currentPage + 1, self.totalPagesScore)) 
        self.label2 = Tkinter.Label(master, textvariable=self.textVar2)
        self.label2.grid(row=0,column=2,sticky=Tkinter.E)
        #self.label2.pack(side=Tkinter.RIGHT)
        
        self.textVar1 = Tkinter.StringVar()
        self.textVar1.set('Left page: %d/%d' % (self.currentPage, self.totalPagesScore))            
        self.label1 = Tkinter.Label(master, textvariable=self.textVar1)
        self.label1.grid(row=0,column=0,sticky=Tkinter.W)
        
        self.textVar3.set('That is a good song! :)')
        
        if self.firstTime == True:
            self.button2 = Tkinter.Button(master, text="Start SF", width=self.sizeButton,command=self.startScoreFollower, bg='green')
            self.button2.grid(row=5,column=3)
            
            self.button3 = Tkinter.Button(master, text="1st page", width=self.sizeButton,command=self.goTo1stPage)
            self.button3.grid(row=4,column=3)
            #self.button3.pack()#(side=Tkinter.BOTTOM)
            
            self.button3 = Tkinter.Button(master, text="Last page", width=self.sizeButton,command=self.goToLastPage)
            self.button3.grid(row=4,column=4)
            
            self.button4 = Tkinter.Button(master, text="Forward", width=self.sizeButton,command=self.pageForward)
            self.button4.grid(row=3,column=4)
            #self.button4.pack()
            
            self.button7 = Tkinter.Button(master, text="Backward", width=self.sizeButton,command=self.pageBackward)
            self.button7.grid(row=3,column=3)
            #self.button7.pack()
            
            self.button5 = Tkinter.Button(master, text="MOVE", width=self.sizeButton,command=self.moving, bg='beige')
            self.button5.grid(row=2,column=3)
            
            self.button6 = Tkinter.Button(master, text="STOP SF", width=self.sizeButton,command=self.stopScoreFollower, bg='red')
            self.button6.grid(row=5,column=4)
                                
            self.textVarComments = Tkinter.StringVar()
            self.textVarComments.set('Comments') 
            self.label2 = Tkinter.Label(master, textvariable=self.textVarComments)
            self.label2.grid(row=8,column=3,sticky=Tkinter.E)
            
            self.firstTime = False

        
    def moving(self):
        print "moving!"
        if self.currentPage + 1 < self.totalPagesScore:
            self.ntimes = 0
            self.newcoords = self.positionxRight, self.positionyLeft
            self.canvas1.create_image(self.positionx3rd, self.positiony3rd, image=self.phimage[self.currentPage + 1], tag='3rdImage')
            #self.canvas1.pack(side='left')
            self.speed = 3
            self.master.after(500, self.movingRoutine)
        
        
    def movingRoutine(self):
        if self.newcoords[0] > self.positionxLeft:
            self.newcoords = self.positionxRight - self.speed * self.ntimes, self.positionyRight
            self.canvas1.coords('rightImage', self.newcoords) 
            if self.currentPage + 2 <= self.totalPagesScore:
                self.newcoords3rd = self.positionx3rd - self.speed * self.ntimes, self.positiony3rd
                self.canvas1.coords('3rdImage', self.newcoords3rd) 
            self.ntimes += 1
            self.master.after(40, self.movingRoutine)
            
        else:
            if self.currentPage + 2 <= self.totalPagesScore:
                self.canvas1.delete('3rdImage')
            self.master.after(0, self.pageForward)
            self.isMoving = False
                        
        
                      
    def pageForward(self):   
        
        if self.currentPage + 1 <= self.totalPagesScore:
            self.canvas1.delete('leftImage')
            self.canvas1.delete('rightImage')  
            self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[self.currentPage], tag='leftImage')
            self.textVar1.set('Left page: %d/%d' % (self.currentPage + 1, self.totalPagesScore))
            
            if self.currentPage + 1 < self.totalPagesScore:
                self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[self.currentPage + 1], tag='rightImage')
                self.textVar2.set('Right page: %d/%d' % (self.currentPage + 2, self.totalPagesScore))               
            else:
                self.textVar2.set('Right page: --')   
                            
            self.canvas1.grid(row=1,column=0,columnspan=3,rowspan=7)
            #self.canvas1.pack(side=Tkinter.LEFT)              
            self.currentPage += 1        
        print "page Forward", self.currentPage, self.totalPagesScore 
        
    def pageBackward(self):           
        if self.currentPage > 1:
            self.canvas1.delete('leftImage')
            self.canvas1.delete('rightImage')  
            self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[self.currentPage - 2], tag='leftImage')

            self.textVar1.set('Left page: %d/%d' % (self.currentPage - 1, self.totalPagesScore))            
            self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[self.currentPage - 1], tag='rightImage')
            self.textVar2.set('Right page: %d/%d' % (self.currentPage, self.totalPagesScore))               
            #self.canvas1.pack(side=Tkinter.LEFT)    
            self.canvas1.grid(row=1,column=0,columnspan=3,rowspan=7)         
            self.currentPage -= 1    
        print "page Backward", self.currentPage, self.totalPagesScore    
            
    def goTo1stPage(self):
        self.currentPage = 1
        self.canvas1.delete('leftImage')
        self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[0], tag='leftImage')
        self.textVar1.set('Left page: %d/%d' % (1, self.totalPagesScore))
             
        if self.totalPagesScore > 1: #there is more than 1 page
            self.canvas1.delete('rightImage')             
            self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[1], tag='rightImage')
            self.textVar2.set('Right page: %d/%d' % (2, self.totalPagesScore)) 
                          
        self.canvas1.grid(row=1,column=0,columnspan=3,rowspan=7) 
        #self.canvas1.pack(side=Tkinter.LEFT)            
        
    def goToLastPage(self):
        self.currentPage = self.totalPagesScore
        self.canvas1.delete('leftImage')
        self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[self.totalPagesScore-1], tag='leftImage')
        self.textVar1.set('Left page: %d/%d' % (1, self.totalPagesScore))
             
        if self.totalPagesScore > 1: #there is more than 1 page
            self.canvas1.delete('rightImage')             
            self.textVar2.set('Right page: -/-') 
                          
        self.canvas1.grid(row=1,column=0,columnspan=3,rowspan=7)          
     
        
       
    def startScoreFollower(self):
        
        self.button2 = Tkinter.Button(self.master, text="Start SF", width=self.sizeButton,command=self.startScoreFollower,state='disable', bg='green')
        self.button2.grid(row=5,column=3)
        
        #scoreNotes = ["f'#4", "e'", "d'", "c'#", "b", "a", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "g", "e", "d8", "f#", "a", "g", "f#", "d", "f#", "e", "d", "B", "d", "a", "g", "b", "a", "g", "f#", "d", "e", "c'#", "d'", "f'#", "a'", "a", "b", "g", "a", "f#", "d", "d'16", "e'", "d'8", "c'#", "d'16", "c'#", "d'", "d", "c#", "a", "e", "f#", "d", "d'", "c'#", "b", "c'#", "f'#", "a'", "b'", "g'", "f'#", "e'", "g'", "f'#", "e'", "d'", "c'#", "b", "a", "g", "f#", "e", "g", "f#", "e", "d", "e", "f#", "g", "a", "e", "a", "g", "f#", "b", "a", "g", "a", "g", "f#", "e", "d", "B", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "e", "b", "a", "b", "a", "g", "f#8", "f'#", "e'4", "d'", "f'#", "b'4", "a'", "b'", "c'#'", "d''8", "d'", "c'#4", "b", "d'"]
        #scNotes = converter.parse(" ".join(scoreNotes), "4/4")
        scNotes = self.scorePart.flat.notes
        ScF = scoreFollower.ScoreFollower(scoreStream=scNotes)
        #ScF.runSFGraphic = self.runSFGraphic
        #ScF.runScoreFollower(show=True, plot=False, useMic=True, seconds=10.0)
        ScF.show = False
        ScF.plot = False
        ScF.useMic = True
        ScF.seconds_recording = 6.0
        ScF.useScale = scale.ChromaticScale('C4')
        ScF.begins = True
        ScF.countdown = 0
        self.firstTimeSF = True
        self.stop = False
        
        # decision lastNotePosition taking into account the beginning of the first page displayed
        ScF.lastNotePosition = self.pageMeasureNumbers[self.currentPage - 1]
        ScF.startSearchAtSlot = self.pageMeasureNumbers[self.currentPage - 1]
        ScF.result = False
        self.textVar3.set('recording in 1 sec!')
       
        self.scoreFollower = ScF     
        #parameters for the thread 2
        self.dummyQueue=queue.Queue()
        self.sampleQueue=queue.Queue()
        self.dummyQueue2=queue.Queue()
        self.sampleQueue2=queue.Queue()
        self.firstAnalysis = True
        self.continueScoreFollower()   
        #self.master.after(1000, self.continueScoreFollower)
        

 
    def continueScoreFollower(self):
        self.ScF = self.scoreFollower       
        if self.stop == False and (self.firstTimeSF == True or self.rt.resultInThread == False):
            self.firstTimeSF = False
            self.lastNoteString = 'at: %d, countdown:%d, page:%d' % (self.ScF.lastNotePosition,self.ScF.countdown,self.currentPage) 
            self.rt=RecordThread(self.dummyQueue,self.sampleQueue,self.ScF)            
            self.rt.daemon=True
            self.rt.start() # the 2nd thread starts here
            self.dummyQueue.put("Start")            
            self.master.after(6000,self.analyzeRecording)
        else:
            self.button2.destroy() 
            self.button2 = Tkinter.Button(self.master, text="Start SF", width=self.sizeButton,command=self.startScoreFollower,bg='green')
            self.button2.grid(row=5,column=3)
            self.textVarComments.set('END!! %s' %(self.rt.resultInThread))

            
    def analyzeRecording(self):
        self.rt.outQueue.get()
        self.textVar3.set(self.lastNoteString)         
        print "****",self.ScF.lastNotePosition,self.beginningPages[self.currentPage-1],self.currentPage,self.ScF.lastNotePosition < self.beginningPages[self.currentPage-1]
        if self.currentPage <= self.totalPagesScore:            
            if self.ScF.lastNotePosition < self.beginningPages[self.currentPage-1] or self.ScF.lastNotePosition >= self.beginningPages[self.currentPage+1]: # case in which the musician plays a note in a not displayed page
                pageNumber=0
                final=False
                while final==False:              
                    print "cas HOLA",pageNumber,self.ScF.lastNotePosition,self.beginningPages[pageNumber]
                    if pageNumber < self.totalPagesScore and self.ScF.lastNotePosition >= self.beginningPages[pageNumber]: 
                        pageNumber += 1
                    else:
                        final = True
                
                if self.ScF.lastNotePosition==0:
                    totalPagesToMove=0
                else:       
                    totalPagesToMove = pageNumber-self.currentPage
                print "TOTAL PAGES TO MOVE",totalPagesToMove,pageNumber,self.currentPage
                if totalPagesToMove > 0:                                  
                    for i in range(totalPagesToMove):
                        self.pageForward()
                    print "has played a note not shown in the score (forward)"
                elif totalPagesToMove <0:
                     for i in range(int(math.fabs(totalPagesToMove))):
                        self.pageBackward()                   
                     print "has played a note not shown in the score (backward)"

            
            elif self.ScF.lastNotePosition >= self.middlePages[self.currentPage] and self.isMoving==False:  #50% case
                self.isMoving = True
                self.moving()
                print "playing a note of the second half part of the right page"
                
            elif self.ScF.lastNotePosition >= self.beginningPages[self.currentPage] and self.ScF.lastNotePosition < self.middlePages[self.currentPage]+self.beginningPages[self.currentPage]: 
                self.hits +=1
                print "playing a note of the first half part of the right page: hits=%d" %self.hits
                if self.hits == 2:
                    self.hits=0
                    if self.isMoving == False:
                        self.isMoving = True
                        self.moving()
            else:
                self.hits=0
                print "playing a note of the left page"
       
        
        print '------------------last note position',self.ScF.lastNotePosition
        self.master.after(1000, self.continueScoreFollower)
 
    def stopScoreFollower(self):
        self.stop = True
        print "Stop button pressed!"  


class RecordThread(threading.Thread):
    def __init__(self,inQueue,outQueue,object):
        threading.Thread.__init__(self)
        self.inQueue=inQueue
        self.outQueue=outQueue
        self.l=[]
        self.object=object
        print 'valor dins el thread'
    def run(self):
        startCommand=self.inQueue.get()
        print "start command received: recording!"
        self.resultInThread = self.object.repeatTranscription()
        self.outQueue.put(1)
        self.outQueue.task_done()


               

if __name__ == "__main__":
    root = Tkinter.Tk()
    sfapp = SFApp(root)
    root.mainloop()
