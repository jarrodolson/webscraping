import time
import datetime
import glob
import random
import json
import psycopg2
import csv

from SCRAPER import SCRAPER
from DB import DBCONN
from LOGGING import LOG

##(DONE)Should read a config file (if none exists, walk user through creation, and save as json)
####(DONE)Config points to database, file save directory, initial seed list file, path to log file name,
##(DONE)If database table doesn't exist, create one
####Need to read in seed list and add to cache
##If file directory doesn't exist, raise error
##(DONE - by default)If seed list file doesn't exist, raise error
##(DONE - but not explicit) If path to log file doesn't exist, raise error
##(DONE)Create new log with date and time of start to distinguish

class SCRAPING_INSTANCE:
    def __init__(self, configFiName):
        self.configFiName = configFiName
        self.readConfig()
        
        #self.log = LOG(self.createFiName(self.config['path_to_log'], 'log'))
        self.log = LOG('temp_log/test.csv')

        with open(self.config['path_to_db_pass']) as fi:
            dbPass = fi.read().strip()
    
        self.db = DBCONN(self.config['database'],
                         self.config['db_host'],
                         self.config['db_user'],
                         dbPass)
        if self.db.conn is None:
            raise ValueError("The database does not exist: {0}".format(self.config['databae']))
        try:
            self.db.cur.execute("SELECT * FROM cache;")
        except psycopg2.ProgrammingError as err:
            if 'relation "cache" does not exist' in str(err):
                self.createTableCache()
                self.readSeedList()
            else:
                raise ValueError("psycopg2 error: {0}".format(str(err)))
        
        
    def createFiName(self, path, prefix):
        timing = datetime.datetime.now()
        timing_formatted = timing.strftime("%Y%m%d-%H%M")
        finame = "{0}/{1}_{2}.csv".format(path,
                                         prefix,
                                         timing_formatted)
        return finame

    def checkPath(self, path):
        if path.endswith("/") or path.endswith("\\"):
            path = path[0:(len(path)-1)]
        return path

    def readConfig(self):
        try:
            with open(self.configFiName) as fi:
                self.config = json.load(fi)
        except FileNotFoundError:
            self.config = {}
            self.config['database'] = input("Name of database: ")
            self.config['path_to_db_pass'] = input("Path (w/ filename) to db password: ")
            self.config['db_user'] = input("DB User: ")
            self.config['db_host'] = input("DB host: ")
            self.config['path_to_file_save'] = self.checkPath(input("Path to save dump files: "))
            self.config['file_save_name'] = '0'
            self.config['seed_list'] = input('Seed list: ')
            self.config['path_to_log'] = self.checkPath(input("Path to log files: "))
            self.writeConfig()

    def writeConfig(self):
        with open(self.configFiName, 'w') as fi:
            fi.write(json.dumps(self.config))

    def readSeedList(self):
        pass
            
    def createTableCache(self):
        with open("SQL_QUERIES/createCache.txt") as fi:
            query = fi.read().strip()
        self.db.cur.execute(query)

    def updateCacheNewUrls(self, newLi):
        pass

    def readSeedList(self):
        seedList = []
        with open(self.config['seed_list']) as fi:
            reader = csv.reader(fi)
            for i, row in enumerate(reader):
                if i == 0:
                    foundUrlIndex = False
                    for k, col in enumerate(row):
                        if col == 'url':
                            foundUrlIndex = True
                            break
                    if foundUrlIndex == False:
                        raise ValueError("Your seed list file needs to have a column named 'url'.")
                else:
                    seedList.append(row[k])
        return seedList

db = DBCONN('scraper', 'localhost', 'postgres', 'd11Rigent')
db.cur.execute("DROP TABLE cache;")
##db.createTableCache()
si = SCRAPING_INSTANCE('test_config.json')
