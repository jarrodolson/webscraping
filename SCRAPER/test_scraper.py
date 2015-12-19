import unittest
import csv
import os
import __init__ as x

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
        self.scraper = x.SCRAPER()
    
    def test_goOnline(self):
        '''if no website exists, should return none'''
        result = self.scraper.goOnline(self.destination)
        self.assertEqual(None, result)

    def test_parseRequestObj(self):
        '''if no website exists, there should be no self.term, or self.info'''
        pass

class WebsiteDoesExist(unittest.TestCase):
    def setUp(self):
        self.destination = 'http://www.python.org'
        self.scraper = x.SCRAPER()

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
        scraper = x.SCRAPER()
        destination = 'http://www.python.org'
        result = scraper.breakDownURL(destination)
        self.assertEqual('http', scraper.protocol)
        self.assertEqual('python.org', scraper.domain)

    def test_breakdownURL_valid_https(self):
        '''breakdownURL should still create self.protocol = https and self.domain = python.org'''
        scraper = x.SCRAPER()
        destination = 'https://www.python.org'
        scraper.breakDownURL(destination)
        self.assertEqual('https', scraper.protocol)
        self.assertEqual('python.org', scraper.domain)

    def test_breakdownURL_valid_https_with_children(self):
        '''breakdownURL should still create self.protocol = https and self.domain = python.org'''
        scraper = x.SCRAPER()
        destination = 'https://www.python.org/docs&something/go'
        scraper.breakDownURL(destination)
        self.assertEqual('https', scraper.protocol)
        self.assertEqual('python.org', scraper.domain)

    def test_breakdownURL_invalid_www(self):
        '''breakdownURL should not create self.protocol raise error and self.domain = python.org'''
        scraper = x.SCRAPER()
        destination = 'www.python.org'
        with self.assertRaises(ValueError):
            scraper.breakDownURL(destination)

class CheckUrls(unittest.TestCase):
    def test_checkFileType_pdf(self):
        '''Should return True if file ending is a file object (pdf)'''
        scraper = x.SCRAPER()
        destination = 'www.python.org/something.pdf'
        self.assertTrue(scraper.checkFileType(destination))

    def test_checkFileType_html(self):
        '''Should return False if file ending is not file object (html)'''
        scraper = x.SCRAPER()
        destination = 'www.python.org/something.htm'
        self.assertFalse(scraper.checkFileType(destination))
    
if __name__ == '__main__':
    unittest.main()
