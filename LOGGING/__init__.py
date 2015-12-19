import time
import datetime
import csv

##Should take a filename, and either create a new, or set open and append a csv log
##Log should contain date, msg_type (default = "MESSAGE"), msg
class LOG:
    def __init__(self, fiName, console = True):
        self.fiName = fiName
        self.createOrAppend(console)

    def createOrAppend(self, console):
        try:
            obj = open(self.fiName, 'r')
            obj.close()
        except FileNotFoundError:
            with open(self.fiName, 'w', newline = '') as fi:
                writer = csv.writer(fi)
                writer.writerow(['datetime', 'message', 'message_type'])
            self.writeMsg('Initializing log', console = console)

    def writeMsg(self, msg, msgType = 'MESSAGE', console = False):
        with open(self.fiName, 'a', newline = '') as fi:
            writer = csv.writer(fi)
            timing = datetime.datetime.now()
            if console == True:
                print("LOGGING: {0}, {1}, {2}".format(timing, msg, msgType))
            writer.writerow([timing, msg, msgType])
