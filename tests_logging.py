import unittest
import csv
import os
import LOGGING as x

def readCsv(finame):
    data = []
    with open(finame) as fi:
        reader = csv.reader(fi)
        for i, row in enumerate(reader):
            data.append(row)
    return data

class NoLogExists(unittest.TestCase):
    def test_create_log(self):
        '''if no log exists, should create one'''
        finame = 'test_log.csv'
        if os.path.isfile(finame):
            raise ValueError("There is already a file in place, but it should not be for NoLogExists tests.")
        log = x.LOG(finame, console = False)
        data = readCsv(finame)
        self.assertEqual(['datetime', 'message', 'message_type'],
                         data[0])
        self.assertEqual('Initializing log', data[1][1])
        self.assertEqual(3, len(data[0]))
        os.remove(finame)

class LogExists(unittest.TestCase):
    def setUp(self):
        self.finame = 'test_log.csv'
        log = x.LOG(self.finame, console = False)

    def tearDown(self):
        os.remove(self.finame)
        
    def test_write_default_msg(self):
        '''if a log exists, should append it'''
        if os.path.isfile(self.finame) == False:
            raise ValueError("There is no file in place, but it should be for LogExists class of tests")
        log = x.LOG(self.finame)
        msg = 'test message'
        log.writeMsg(msg)
        data = readCsv(self.finame)
        self.assertEqual(msg, data[2][1])
        self.assertEqual('MESSAGE', data[2][2])

    def test_write_custom_msg_type(self):
        '''if a log exists, should append it'''
        if os.path.isfile(self.finame) == False:
            raise ValueError("There is no file in place, but it should be for LogExists class of tests")
        log = x.LOG(self.finame)
        msg = 'test message'
        msg_type = 'TESTING'
        log.writeMsg(msg, msg_type)
        data = readCsv(self.finame)
        self.assertEqual(msg, data[2][1])
        self.assertEqual(msg_type, data[2][2])

if __name__ == '__main__':
    unittest.main()
