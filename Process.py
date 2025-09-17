from threading import Lock, Thread
from time import sleep
from pyeventbus3.pyeventbus3 import *


class Process(Thread):

    def __init__(self, name, npProcess):
        Thread.__init__(self)

        self.npProcess = npProcess
        self.myId = Process.nbProcessCreated
        self.myProcessName = name
        self.setName("MainThread-" + name)
        PyBus.Instance().register(self, self)
        self.alive = True
        self.start()

    def run(self):
        loop = 0
        while self.alive:
            print(self.getName() + " Loop: " + str(loop))
            sleep(1)
            loop+=1
        print(self.getName() + " stopped")

    def stop(self):
        self.alive = False

    def waitStopped(self):
        self.join()
