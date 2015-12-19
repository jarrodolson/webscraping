import os
import urllib.request, urllib.error, urllib.parse, urllib.parse, gzip
from xml.etree import ElementTree as et
from bs4 import BeautifulSoup
import time
import datetime
import glob
import random

import file_objects

class SCRAPER:
    def __init__(self):
        pass
    
    def goOnline(self, startTerm):
        opened = False
        file = self.checkFileType(startTerm)
        if file == True:
            self.obj = None
            self.ErrorMessage = 'This item is a file object: {0}'.format(startTerm)
            return self.obj
        while opened==False:
            try:
                ##User agent should be customizable
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
            self.info_str = str(obj.info())
            self.info['Date'] = datetime.datetime.strptime(self.info['Date'], '%a, %d %b %Y %H:%M:%S %Z')
            self.data = obj.read()
            self.status = obj.getcode()
            self.soup = BeautifulSoup(self.data)
            self.newToDoLi = self.getLinks()

    def getLinks(self):
        output = []
        linkLi = self.soup.findAll("a")
        for link in linkLi:
            path = link['href']
            if path.startswith("#")==False:
                output.append(urllib.parse.urljoin(self.term, path))
        return output

    def breakDownURL(self, string):
        stringLi = string.split("/")
        temp = stringLi[0]
        if temp.endswith(":"):
            self.protocol = stringLi[0].replace(":", "")
            domain = stringLi[2].split(".")
            self.domain = ".".join(domain[1:len(domain)])
        else:
            raise ValueError("Your URL is not valid... it has no protocol: {0}".format(string))

    def checkFileType(self, url):
        end = url.split(".")[-1]
        if end.lower() in file_objects.nonHtml:
            return True
        else:
            return False
#s = SCRAPER()
#obj = s.goOnline('https://www.python.org')
#s.parseRequestObj(obj)
