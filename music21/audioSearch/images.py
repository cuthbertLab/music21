from music21 import corpus
from music21 import converter
from music21 import environment
from music21 import scale, stream, note, pitch
import threading
import Queue as queue
from music21.audioSearch.base import *
from music21.audioSearch import recording
from music21.audioSearch import scoreFollower
import Tkinter
from PIL import Image as PILImage
from PIL import ImageTk as PILImageTk
import time
import math
 
 
class SFApp():
   
    def __init__(self, master):
        self.master = master
        self.frame = Tkinter.Frame(master)
        self.frame.pack()
        self.master.wm_title("Score follower - music21")
        
        nameSong = 'scores/test_pages_'#'d luca gloria_Page_'        
        self.firstNotePage = [0, 46, 78, 88, 90, 111]
        self.totalPagesScore = len(self.firstNotePage)
        self.pageCounter = 1
        self.pagesScore = []     
        self.phimage = []
        self.canvas = [] 
        self.listNamePages = []
         
        self.x = 300
        self.y = 450 
        self.separation = math.floor(self.x / 4)
        self.newSize = [self.x, self.y]
        self.positionxLeft = math.floor(self.x / 2)
        self.positionyLeft = math.floor(self.y / 2)
        self.positionxRight = math.floor(1.5 * self.x + self.separation)
        self.positionyRight = math.floor(self.y / 2) 
        self.positionx3rd = math.floor(2.5 * self.x + 2 * self.separation)
        self.positiony3rd = math.floor(self.y / 2)
        self.sizeCanvasx = 2 * self.x + self.separation
        self.sizeCanvasy = self.y
        
        
        for i in range(self.totalPagesScore):
            
            namePage = '%s%d.jpg' % (nameSong, i + 1)
            self.listNamePages.append(namePage)
            self.pagesScore.append(PILImage.open(namePage))
            self.pagesScore[i] = self.pagesScore[i].resize(self.newSize)
            self.phimage.append(PILImageTk.PhotoImage(self.pagesScore[i])) 

                
        #now: canvas
        self.canvas1 = Tkinter.Canvas(master, borderwidth=1, width=self.sizeCanvasx, height=self.sizeCanvasy, bg="black")
        self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[0], tag='leftImage')
        
        if self.totalPagesScore >= 2:
            self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[1], tag='rightImage')
            
        self.canvas1.pack(side='left')    
        
        
        #        self.canvas2 = Tkinter.Canvas(master, width=self.sizeCanvasx, height=math.floor(self.sizeCanvasy / 6), bg="red")
        #        self.canvas2.pack(side='bottom')
        #        self.canvas2.text.insert('1.0', 'here is my text to insert')
        #        self.canvas2.
        self.button2 = Tkinter.Button(master, text="Start SF", command=self.startScoreFollower, bg='green')
        self.button2.pack(side=Tkinter.BOTTOM)
        
        self.button3 = Tkinter.Button(master, text="1st page", command=self.goTo1stPage)
        self.button3.pack(side=Tkinter.BOTTOM)
        
        self.button4 = Tkinter.Button(master, anchor='se', text="Forward", command=self.pageForward)
        self.button4.pack()
        
        self.button7 = Tkinter.Button(master, anchor='se', text="Backward", command=self.pageBackward)
        self.button7.pack()
        
        self.button5 = Tkinter.Button(master, text="MOVE", command=self.moving, bg='beige')
        self.button5.pack(side=Tkinter.BOTTOM)
        
        self.button6 = Tkinter.Button(master, text="STOP SF", command=self.stopScoreFollower, bg='red')
        self.button6.pack(side=Tkinter.BOTTOM)
        
        self.textVar2 = Tkinter.StringVar()
        self.textVar2.set('Right page: %d/%d' % (self.pageCounter + 1, self.totalPagesScore)) 
        self.label2 = Tkinter.Label(master, textvariable=self.textVar2)
        self.label2.pack(side=Tkinter.RIGHT)
        
        self.textVar1 = Tkinter.StringVar()
        self.textVar1.set('Left page: %d/%d' % (self.pageCounter, self.totalPagesScore))            
        self.label1 = Tkinter.Label(master, textvariable=self.textVar1)
        self.label1.pack(side=Tkinter.RIGHT)   
        
        self.textVar3 = Tkinter.StringVar()
        self.textVar3.set('Position') 
        self.label3 = Tkinter.Label(master, textvariable=self.textVar3)
        self.label3.pack(side=Tkinter.BOTTOM)          
        
    def moving(self):
        print "moving!"
        if self.pageCounter + 1 < self.totalPagesScore:
            self.ntimes = 0
            self.newcoords = self.positionxRight, self.positionyLeft
            self.canvas1.create_image(self.positionx3rd, self.positiony3rd, image=self.phimage[self.pageCounter + 1], tag='3rdImage')
            self.canvas1.pack(side='left')
            self.speed = 3
            self.master.after(500, self.movingRoutine)
        
        
    def movingRoutine(self):
        if self.newcoords[0] > self.positionxLeft:
            self.newcoords = self.positionxRight - self.speed * self.ntimes, self.positionyRight
            self.canvas1.coords('rightImage', self.newcoords) 
            if self.pageCounter + 2 <= self.totalPagesScore:
                self.newcoords3rd = self.positionx3rd - self.speed * self.ntimes, self.positiony3rd
                self.canvas1.coords('3rdImage', self.newcoords3rd) 
            self.ntimes += 1
            self.master.after(40, self.movingRoutine)
            
        else:
            if self.pageCounter + 2 <= self.totalPagesScore:
                self.canvas1.delete('3rdImage')
            self.master.after(0, self.pageForward)
                        
        
                      
    def pageForward(self):   
        print "page Forward", self.pageCounter, self.totalPagesScore
        if self.pageCounter + 1 <= self.totalPagesScore:
            self.canvas1.delete('leftImage')
            self.canvas1.delete('rightImage')  
            self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[self.pageCounter], tag='leftImage')
            self.textVar1.set('Left page: %d/%d' % (self.pageCounter + 1, self.totalPagesScore))
            
            if self.pageCounter + 1 < self.totalPagesScore:
                self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[self.pageCounter + 1], tag='rightImage')
                self.textVar2.set('Right page: %d/%d' % (self.pageCounter + 2, self.totalPagesScore))               
            else:
                print "only shows the last page (I should delete the page counter)"
                self.textVar2.set('Right page: --')               
           
            self.canvas1.pack(side=Tkinter.LEFT)              
            self.pageCounter += 1        
            
    def pageBackward(self):   
        print "page Backward", self.pageCounter, self.totalPagesScore
        if self.pageCounter > 1:
            self.canvas1.delete('leftImage')
            self.canvas1.delete('rightImage')  
            self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[self.pageCounter - 2], tag='leftImage')

            self.textVar1.set('Left page: %d/%d' % (self.pageCounter - 1, self.totalPagesScore))            
            self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[self.pageCounter - 1], tag='rightImage')
            self.textVar2.set('Right page: %d/%d' % (self.pageCounter, self.totalPagesScore))               
            self.canvas1.pack(side=Tkinter.LEFT)             
            self.pageCounter -= 1        
            
    def goTo1stPage(self):
        self.pageCounter = 1
        self.canvas1.delete('leftImage')
        self.canvas1.create_image(self.positionxLeft, self.positionyLeft, image=self.phimage[0], tag='leftImage')
        self.textVar1.set('Left page: %d/%d' % (1, self.totalPagesScore))
             
        if self.totalPagesScore > 1: #there is more than 1 page
            self.canvas1.delete('rightImage')             
            self.canvas1.create_image(self.positionxRight, self.positionyRight, image=self.phimage[1], tag='rightImage')
            self.textVar2.set('Right page: %d/%d' % (2, self.totalPagesScore))               
           
        self.canvas1.pack(side=Tkinter.LEFT)              
     
        
       
    def startScoreFollower(self):
        scoreNotes = ["f'#4", "e'", "d'", "c'#", "b", "a", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "g", "e", "d8", "f#", "a", "g", "f#", "d", "f#", "e", "d", "B", "d", "a", "g", "b", "a", "g", "f#", "d", "e", "c'#", "d'", "f'#", "a'", "a", "b", "g", "a", "f#", "d", "d'16", "e'", "d'8", "c'#", "d'16", "c'#", "d'", "d", "c#", "a", "e", "f#", "d", "d'", "c'#", "b", "c'#", "f'#", "a'", "b'", "g'", "f'#", "e'", "g'", "f'#", "e'", "d'", "c'#", "b", "a", "g", "f#", "e", "g", "f#", "e", "d", "e", "f#", "g", "a", "e", "a", "g", "f#", "b", "a", "g", "a", "g", "f#", "e", "d", "B", "b", "c'#", "d'", "c'#", "b", "a", "g", "f#", "e", "b", "a", "b", "a", "g", "f#8", "f'#", "e'4", "d'", "f'#", "b'4", "a'", "b'", "c'#'", "d''8", "d'", "c'#4", "b", "d'"]
        scNotes = converter.parse(" ".join(scoreNotes), "4/4")
        #scNotes = corpus.parse('luca/gloria').parts[0].flat.notes
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
        
        # decision lastNotePosition taking into account the beginning of the first page displayed
        ScF.lastNotePosition = self.firstNotePage[self.pageCounter - 1]
        ScF.startSearchAtSlot = self.firstNotePage[self.pageCounter - 1]
        self.result = False
        self.textVar3.set('recording in 1 sec!')
       
        self.scoreFollower = ScF        
        self.master.after(1000, self.continueScoreFollower)
        
        #parameters for the thread 2
        self.dummyQueue=queue.Queue()
        self.sampleQueue=queue.Queue()
        
 
    def continueScoreFollower(self):
        self.ScF = self.scoreFollower       
        if self.result is False:
            self.lastNoteString = 'at: ' + str(self.ScF.lastNotePosition) + ' countdown: ' + str(self.ScF.countdown) 
            #self.result = ScF.repeatTranscription()
            self.rt=RecordThread(self.dummyQueue,self.sampleQueue,self.ScF)
            self.rt.daemon=True
            self.variable=1
            print "Started at",time.time()
            self.rt.start() # the 2nd thread starts here
            print "ja ha engegat"
            self.dummyQueue.put("Start")
            print 'inteento',self.rt.variable
            self.master.after(12000,self.analyzeRecording)

            
    def analyzeRecording(self):
        self.rt.outQueue.get()
        print 'he passat la barrera'
        self.textVar3.set(self.lastNoteString)
        self.master.after(1000, self.continueScoreFollower)
        if self.ScF.lastNotePosition > 20:
            print "change page"
        else:
            self.textVar3.set("done!")
 
    def stopScoreFollower(self):
        self.result = "stopManually"
        print "Stop botton pressed!"  


class RecordThread(threading.Thread):
    def __init__(self,inQueue,outQueue,ScF):
        threading.Thread.__init__(self)
        self.inQueue=inQueue
        self.outQueue=outQueue
        self.l=[]
        self.ScF=ScF
        
    def run(self):
        print "recorder waiting for start command"
#        print 'variable' , self.variable
        self.variable=6
        startCommand=self.inQueue.get()
        print "start command received: recording!"
        self.result = self.ScF.repeatTranscription()
        self.outQueue.put(1)
        self.outQueue.task_done()


        


#class TestExternal(unittest.TestCase):
#    pass
#
#    def runTest(self):
#        pass
#
#    def testRunImage(self):
#        Im = SFApp()
#        Im.runImages()
        

if __name__ == "__main__":
    root = Tkinter.Tk()
    sfapp = SFApp(root)
    root.mainloop()

    
    
    
    
#    music21.mainTest(TestExternal)

#
#c=corpus.parse(nom).parts[0]
#for n in c.flat.notesAndREsts
#
#n.measureNumber
#
#n.storedMeasureNumer=n.measureNumber
