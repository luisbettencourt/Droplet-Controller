import threading
import time
from tkinter import *


class Timer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

        self.previousElapsedTime = 0.0
        self.startTime = 0.0
        self.elapsedTime = 0.0
        self.timestr = ""
        self.stringVar = StringVar()

        self.stopEvent = threading.Event()
        self.pauseEvent = threading.Event()

        self.startTime = time.time()
        self.start()

    def resume(self):
        """ Start the stopwatch, ignore if running. """
        if self.pauseEvent.isSet():
            self.pauseEvent.clear()
            self.startTime = time.time()

    def run(self):
        """ Update the stopwatch """
        while not self.stopEvent.isSet():
            if(not self.pauseEvent.isSet()):
                self.elapsedTime = time.time() - self.startTime + self.previousElapsedTime
                self.setTime(self.elapsedTime)
            time.sleep(0.05)

    def setTime(self, elap):
        """ Set the time string to Minutes:Seconds:Hundreths """
        minutes = int(elap/60)
        seconds = int(elap - minutes*60.0)
        hseconds = int((elap - minutes*60.0 - seconds)*100)
        self.timestr = '%02d:%02d:%02d' % (minutes, seconds, hseconds)
        self.stringVar.set(self.timestr)

    def pause(self):
        """ Pause the stopwatch, ignore if stopped. """
        if not self.pauseEvent.isSet():
            self.elapsedTime = time.time() - self.startTime
            self.setTime(self.elapsedTime + self.previousElapsedTime)
            self.previousElapsedTime += self.elapsedTime
            self.pauseEvent.set()

    def stop(self):
        self.stopEvent.set()

    def reset(self):
        """ Reset the stopwatch. """
        self.startTime = time.time()
        self.elapsedTime = 0.0
        self.previousElapsedTime = 0.0
        self.setTime(self.elapsedTime)
