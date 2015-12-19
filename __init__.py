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

import websites_to_ignore

##(DONE)Should read a config file (if none exists, walk user through creation, and save as json)
####(DONE)Config points to database, file save directory, initial seed list file, path to log file name,
##(DONE)If database table doesn't exist, create one
#### (DONE) Need to read in seed list and add to cache
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

        self.scraper = SCRAPER()

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
                self.createTableLinkTrack()
                seedLi = self.readSeedList()
                self.updateCacheNewUrls(seedLi)
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
            
    def createTableCache(self):
        with open("SQL_QUERIES/createCache.txt") as fi:
            query = fi.read().strip()
        self.db.cur.execute(query)

    def createTableLinkTrack(self):
        with open("SQL_QUERIES/createLinkTrack.txt") as fi:
            query = fi.read().strip()
        self.db.cur.execute(query)

    def updateCacheNewUrls(self, newLi, origin = None):
        count = 0
        notUrl = 0
        external = 0
        tempScraper = SCRAPER()##To access breakdownURL function
        for url in newLi:
            try:
                tempScraper.breakDownURL(url)
                try:
                    if tempScraper.domain not in self.scraper.term:
                        external += 1
                except AttributeError:
                    pass
                try:
                    self.db.cur.execute("INSERT INTO cache (url, protocol, domain, status) VALUES (%s, %s, %s, %s);",
                                         (url,
                                          tempScraper.protocol,
                                          tempScraper.domain,
                                          'todo',))
                    count+=1
                except psycopg2.IntegrityError:
                    pass
            except ValueError:
                notUrl+=1
        if origin is not None:
            with open("SQL_QUERIES/insertIntoLinkTrack.txt") as fi:
                query = fi.read().strip()
            self.db.cur.execute(query,
                                (origin, len(newLi), count, notUrl, external,))
        print("Saved {0} of {1} total viable links".format(count, len(newLi)-notUrl))

    def updateCacheDownload(self, ident):
        with open('SQL_QUERIES/updateCache_download.txt') as fi:
            query = fi.read().strip()
        self.db.cur.execute(query,
                            (datetime.datetime.now(),##Datetime of download
                             'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',##Should be dynamic
                             self.scraper.term,##url_returned
                             self.scraper.protocol,##protocol_returned
                             self.scraper.domain,##domain returned
                             self.scraper.info['Server'],##server returned
                             self.scraper.info['Date'], ##Date on server...in scraper.info dict
                             self.scraper.info['Content-Type'], ##contenttype
                             self.scraper.info['Connection'], ##connection
                             self.scraper.info_str,##Full response
                             ident,))

    def updateCacheDownload_Fail(self, record_id, reason = "Unknown"):
        if 'invalid record' in reason:
            self.db.cur.execute("UPDATE cache SET status = 'failed', status_msg = %s WHERE id = %s;",
                                (reason, record_id,))
        elif 'This item is a file object' in reason:
            self.db.cur.execute("UPDATE cache SET status = 'ignore', status_msg = %s WHERE id = %s;",
                                (reason, record_id))
        elif 'Ignored website' == reason:
            self.db.cur.execute("UPDATE cache SET status = 'ignore', status_msg = %s WHERE id = %s;",
                                (reason, record_id,))
        elif 'Failed to goOnline' == reason:
            self.db.cur.execute("UPDATE cache SET status = 'failed', status_msg = %s WHERE id = %s;",
                                (reason, record_id,))
        elif 'Could not access page' == reason:
            self.db.cur.execute("UPDATE cache SET status = 'failed', status_msg = %s WHERE id = %s;",
                                (self.scraper.ErrorMessage, record_id,))
        elif 'Parse error' == reason:
            with open('SQL_QUERIES/updateCache_download.txt') as fi:
                query = fi.read().strip()
            self.db.cur.execute(query,
                                (reason,##status_msg
                                 datetime.datetime.now(),##Datetime of download
                                 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',##Should be dynamic
                                 self.scraper.term,##url_returned
                                 self.scraper.protocol,##protocol_returned
                                 self.scraper.domain,##domain returned
                                 self.scraper.info['Server'],##server returned
                                 self.scraper.info['Date'], ##Date on server...in scraper.info dict
                                 self.scraper.info['Content-Type'], ##contenttype
                                 self.scraper.info['Connection'], ##connection
                                 self.scraper.info_str,##Full response
                                 record_id,))
        else:
            raise AttributeError("REASON FOR DOWNLOAD FAIL NOT VALID: {0}".format(reason))

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

    def makeToDoLi(self, low, high):
        self.db.cur.execute("SELECT id, url FROM cache WHERE status='todo' AND (id>%s AND id <%s);",
                            (low, high,))
        self.toDoLi = self.db.cur.fetchall()
        #print(self.toDoLi)

    def checkIgnore(self, url):
        for x in website_to_ignore.ignore:
            if x in url:
                return True
        return False

    def iterateThroughToDo(self):
        for urlRecord in self.toDoLi:
            try:
                ident = urlRecord[0]
                url = urlRecord[1]
                if self.checkIgnore(url)
                    try:
                        result = self.scraper.goOnline(url)
                        if result is not None:
                            try:
                                self.scraper.breakDownURL(url)
                                self.scraper.parseRequestObj(result)
                                self.updateCacheDownload(ident)
                                self.updateCacheNewUrls(self.scraper.newToDoLi,
                                                        origin = ident)
                            except:
                                updateCacheDownload_fail(ident, 'Parse Error')
                        elif 'This item is a file object' in self.scraper.ErrorMessage:
                            updateCacheDownload_fail(ident, self.scraper.ErrorMessage)
                        else:
                            updateCacheDownload_fail(ident, 'Could not access page')
                            ##todo: need to handle this error
                    except:
                        ##todo: need to handle this error
                        updateCacheDownload_fail(ident, 'Error making url request')
                else:
                    updateCacheDownload_fail(ident, 'Ignored website')
            except IndexError:
                updateCacheDownload_fail(ident, 'Invalid record in database {0}'.format(str(urlRecord))
            break

class EXECUTOR:
    def __init__(self, configFiName):
        ##todo: iteratively grab to do li, filtering as needed
        self.baseInstance = SCRAPING_INSTANCE(configFiName)
        self.maxId = self.baseInstance.db.getMaxId('id', 'cache')
        range_low = 0
        range_high = 100000
        range_change = 100000
        while range_low < self.maxId:
            self.baseInstance.makeToDoLi(range_low, range_high)
            self.baseInstance.iterateThroughToDo()
            self.maxId = self.baseInstance.db.getMaxId('id', 'cache')
            range_low = range_high
            range_high += range_change
            break

db = DBCONN('scraper', 'localhost', 'postgres', 'd11Rigent')
db.cur.execute("DROP TABLE cache CASCADE;")
db.cur.execute("DROP TABLE link_track;")
#si = SCRAPING_INSTANCE('test_config.json')
executor = EXECUTOR('test_config.json')
