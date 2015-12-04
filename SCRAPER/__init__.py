import os
import urllib.request, urllib.error, urllib.parse, urllib.parse, gzip
from xml.etree import ElementTree as et
from bs4 import BeautifulSoup
import time
import datetime
import glob
import random

class SCRAPER:
    def __init__(self):
        pass
    
    def goOnline(self, startTerm):
        opened = False
        while opened==False:
            try:
                self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
                self.req = urllib.request.Request(url=startTerm)
                self.req.add_header('User-Agent', self.user_agent)
                self.obj = urllib.request.urlopen(self.req)
                opened = True
            except urllib.error.URLError as xxx_todo_changeme:
                self.ErrorMessage = xxx_todo_changeme
                opened = True
                self.obj = None
        return self.obj

    def parseRequestObj(self, obj):
        if obj is not None:
            self.term = obj.geturl()
            self.breakDownURL(self.term)
            self.info = dict(obj.info())

    def breakDownURL(self, string):
        stringLi = string.split("/")
        self.protocol = stringLi[0].replace(":", "")
        domain = stringLi[2].split(".")
        self.domain = ".".join(domain[1:len(domain)])

##s = SCRAPER()
##obj = s.goOnline('https://www.wine-db.com')
##s.parseRequestObj(obj)
