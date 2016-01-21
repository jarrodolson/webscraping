'''
webscraping tool - A basic Python script with postgres integration for scraping web pages
Copyright (C) 2016  Jarrod Olson - jarrod.olson@outlook.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

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
