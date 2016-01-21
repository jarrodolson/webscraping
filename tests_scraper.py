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

import unittest
import csv
import os
import SCRAPER as x

import file_objects

def readCsv(finame):
    data = []
    with open(finame) as fi:
        reader = csv.reader(fi)
        for i, row in enumerate(reader):
            data.append(row)
    return data

class WebsiteDoesNotExist(unittest.TestCase):
    def setUp(self):
        self.destination = 'http://www.aasdfasdfa.com'
        self.scraper = x.SCRAPER(file_objects)
    
    def test_goOnline(self):
        '''if no website exists, should return none'''
        result = self.scraper.goOnline(self.destination)
        self.assertEqual(None, result)

class WebsiteDoesExist(unittest.TestCase):
    def setUp(self):
        self.destination = 'http://www.python.org'
        self.scraper = x.SCRAPER(file_objects)

    def test_goOnline(self):
        '''if website exists, should return a response object'''
        result = self.scraper.goOnline(self.destination)
        self.assertTrue(str(result).startswith('<http.client.HTTPResponse'))

    def test_parseRequestObj(self):
        '''if website exists, should return a parseable object'''
        result = self.scraper.goOnline(self.destination)
        self.scraper.parseRequestObj(result)
        self.assertIs(dict, type(self.scraper.info))

class BreakingUrlsDown(unittest.TestCase):

    def test_breakdownURL_valid_http(self):
        '''breakdownURL should still create self.protocol = http and self.domain = python.org'''
        scraper = x.SCRAPER(file_objects)
        destination = 'http://www.python.org'
        result = scraper.breakDownURL(destination)
        self.assertEqual('http', scraper.protocol)
        self.assertEqual('python.org', scraper.domain)

    def test_breakdownURL_valid_https(self):
        '''breakdownURL should still create self.protocol = https and self.domain = python.org'''
        scraper = x.SCRAPER(file_objects)
        destination = 'https://www.python.org'
        scraper.breakDownURL(destination)
        self.assertEqual('https', scraper.protocol)
        self.assertEqual('python.org', scraper.domain)

    def test_breakdownURL_valid_https_with_children(self):
        '''breakdownURL should still create self.protocol = https and self.domain = python.org'''
        scraper = x.SCRAPER(file_objects)
        destination = 'https://www.python.org/docs&something/go'
        scraper.breakDownURL(destination)
        self.assertEqual('https', scraper.protocol)
        self.assertEqual('python.org', scraper.domain)

    def test_breakdownURL_invalid_www(self):
        '''breakdownURL should not create self.protocol raise error and self.domain = python.org'''
        scraper = x.SCRAPER(file_objects)
        destination = 'www.python.org'
        with self.assertRaises(ValueError):
            scraper.breakDownURL(destination)

class CheckUrls(unittest.TestCase):
    def test_checkFileType_pdf(self):
        '''Should return True if file ending is a file object (pdf)'''
        scraper = x.SCRAPER(file_objects)
        destination = 'www.python.org/something.pdf'
        self.assertTrue(scraper.checkFileType(destination))

    def test_checkFileType_html(self):
        '''Should return False if file ending is not file object (html)'''
        scraper = x.SCRAPER(file_objects)
        destination = 'www.python.org/something.htm'
        self.assertFalse(scraper.checkFileType(destination))
    
if __name__ == '__main__':
    unittest.main()
