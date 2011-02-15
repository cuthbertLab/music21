import os
import re
import time
import sys
import threading 


# possible look at:
# http://code.activestate.com/recipes/576780/
# http://www.garyrobinson.net/2009/10/non-blocking-raw_input-for-python.html



class Prompt(threading.Thread):
    def __init__ (self, prompt, timeOutTime):
        threading.Thread.__init__(self)
        self.status = None
        self.timeLeft = timeOutTime
        self.prompt = prompt

    def removeTime(self, value):
        self.timeLeft -= value

    def printPrompt(self):
        sys.stdout.write('%s: ' % self.prompt)

    def run(self):
        self.printPrompt() # print on first call
        self.status = raw_input()


def getResponseOrTimeout(prompt='provide a value', timeOutTime=16):

    current = Prompt(prompt=prompt, timeOutTime=timeOutTime)
    current.start()
    reportInterval = 4
    updateInterval = 1
    intervalCount = 0

    post = None
    while True:
    #for host in range(60,70):
        if not current.isAlive() or current.status is not None:
            break
        if current.timeLeft <= 0:
            break
        time.sleep(updateInterval)
        current.removeTime(updateInterval)

        if intervalCount % reportInterval == reportInterval - 1:
            sys.stdout.write('\ntime out in %s seconds\n' % current.timeLeft)
            current.printPrompt()

        intervalCount += 1
    #for o in objList:
        # can have timeout argument, otherwise blocks
        #o.join() # wait until the thread terminates

    post = current.status
    # pass timeout of 0 to kill
    #current.join(timeout=0)

    if post == None:
        print('got no value')
    else:
        print ('got: %s' % post)

if __name__ == '__main__':
    getResponseOrTimeout()

