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
import file_objects

##todo: add logging

class SCRAPING_INSTANCE:
    def __init__(self, configFiName, filterToSeed = False):
        self.configFiName = configFiName
        self.filterToSeed = filterToSeed##Limit queries to urls with domains in seed list
        self.readConfig()
        
        #self.log = LOG(self.createFiName(self.config['path_to_log'], 'log'))
        self.log = LOG('temp_log/test.csv')

        self.scraper = SCRAPER(file_objects)

        with open(self.config['path_to_db_pass']) as fi:
            dbPass = fi.read().strip()
    
        self.db = DBCONN(self.config['database'],
                         self.config['db_host'],
                         self.config['db_user'],
                         dbPass)
        self.seedLi = self.readSeedList()
        if self.db.conn is None:
            raise ValueError("The database does not exist: {0}".format(self.config['databae']))
        try:
            self.db.cur.execute("SELECT * FROM cache;")

        except psycopg2.ProgrammingError as err:
            if 'relation "cache" does not exist' in str(err):
                self.createTableCache()
                self.createTableLinkTrack()
                self.updateCacheNewUrls(self.seedLi)
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
        tempScraper = SCRAPER(file_objects)##To access breakdownURL function
        for url in newLi:
            if url[-1] == "/":
                url = url[0:(len(url)-1)]
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
        content_type = tryAndNone(self.scraper.info, 'Content-Type')
        if content_type == None:##Noticed an error with capitalization in some server responses
            content_type = tryAndNone(self.scraper.info, 'Content-type')
        try:
            self.db.cur.execute(
                query,
                (datetime.datetime.now(),##Datetime of download
                 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',##Should be dynamic
                 self.scraper.term,##url_returned
                 self.scraper.protocol,##protocol_returned
                 self.scraper.domain,##domain returned
                 tryAndNone(self.scraper.info, 'Server'),##server returned
                 tryAndNone(self.scraper.info, 'Date'), ##Date on server...in scraper.info dict
                 content_type, ##contenttype
                 tryAndNone(self.scraper.info, 'Connection'), ##connection
                 self.scraper.info_str,##Full response
                 str(self.scraper.soup),##Full string as text
                 str(self.scraper.soup),##Full string to md5 hash
                 str(self.scraper.body_clean),##body_clean
                 ident,))
        except psycopg2.IntegrityError:
            self.db.cur.execute(
                "UPDATE cache SET status = 'ignore', status_msg = 'DUPLICATE' WHERE id = %s;",
                (ident,)
                )

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
        elif 'Error making URL request' == reason:
            self.db.cur.execute("UPDATE cache SET status = 'failed', status_msg = %s WHERE id = %s;",
                                (reason, record_id,))
        elif 'Could not access page' == reason:
            self.db.cur.execute("UPDATE cache SET status = 'failed', status_msg = %s WHERE id = %s;",
                                (self.scraper.ErrorMessage, record_id,))
        elif 'Parse error' == reason:
            with open('SQL_QUERIES/updateCache_download.txt') as fi:
                query = fi.read().strip()
            content_type = tryAndNone(self.scraper.info, 'Content-Type')
            if content_type == None:##Noticed an error with capitalization in some server responses
                content_type = tryAndNone(self.scraper.info, 'Content-type')
            self.db.cur.execute(query,
                                (reason,##status_msg
                                 datetime.datetime.now(),##Datetime of download
                                 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',##Should be dynamic
                                 self.scraper.term,##url_returned
                                 self.scraper.protocol,##protocol_returned
                                 self.scraper.domain,##domain returned
                                 tryAndNone(self.scraper.info, 'Server'),##server returned
                                 tryAndNone(self.scraper.info, 'Date'), ##Date on server...in scraper.info dict
                                 content_type, ##contenttype
                                 tryAndNone(self.scraper.info, 'Connection'), ##connection
                                 self.scraper.info_str,##Full response
                                 record_id,))
        else:
            print(self.scraper.term)
            print(self.scraper.info)
            self.db.cur.execute("UPDATE cache SET status = 'failed', status_msg = 'UNKNOWN REASON' WHERE id = %s;",
                                (record_id,))
            #print(self.scraper.info)
            #raise AttributeError(
            #    "REASON FOR DOWNLOAD FAIL NOT VALID: {0}".format(reason))

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
        for x in websites_to_ignore.ignore:
            if x in url:
                return False
        return True

    def checkSeedList(self, url):
        for x in self.seedLi:
            if url.startswith(x):
                return True
        return False

    def iterateThroughToDo(self):
        for urlRecord in self.toDoLi:
            try:
                ident = urlRecord[0]
                url = urlRecord[1]
                goOn = False
                if self.filterToSeed == True:
                    if self.checkSeedList:
                        return True##In Seed List
                    else:
                        return False##Not in seed list
                else:
                    goOn = True##Seed list is irrelevant
                if goOn == True:
                    if self.checkIgnore(url):
                        try:
                            result = self.scraper.goOnline(url)
                            if result is not None:
                                try:
                                    self.scraper.breakDownURL(url)
                                    self.scraper.parseRequestObj(result)
                                    self.updateCacheDownload(ident)
                                    self.updateCacheNewUrls(
                                        self.scraper.newToDoLi,
                                        origin = ident
                                        )
                                except:
                                    self.updateCacheDownload_Fail(
                                        ident,
                                        'Parse error'
                                        )
                            elif 'This item is a file object' in self.scraper.ErrorMessage:
                                self.updateCacheDownload_Fail(
                                    ident,
                                    self.scraper.ErrorMessage
                                    )
                            else:
                                self.updateCacheDownload_Fail(
                                    ident,
                                    'Could not access page'
                                    )
                        except:
                            self.updateCacheDownload_Fail(
                                ident,
                                'Error making url request'
                                )
                    else:
                        self.updateCacheDownload_Fail(
                            ident,
                            'Ignored website'
                            )
            except IndexError:
                self.updateCacheDownload_Fail(
                    ident,
                    'Invalid record in database {0}'.format(str(urlRecord)))

class EXECUTOR:
    def __init__(self, configFiName, filterToSeed = False):
        self.baseInstance = SCRAPING_INSTANCE(configFiName, filterToSeed)
        self.maxId = self.baseInstance.db.getMaxId('id', 'cache')
        range_low = 0
        range_high = 100000
        if range_high > self.maxId:
            range_high = self.maxId+1
        range_change = 100000
        current = 0
        while range_low < self.maxId:
            self.baseInstance.makeToDoLi(range_low, range_high)
            self.baseInstance.iterateThroughToDo()
            self.maxId = self.baseInstance.db.getMaxId('id', 'cache')
            range_low = range_high - 1
            range_high += range_change
            self.maxId = self.baseInstance.db.getMaxId('id', 'cache')
            if range_high > self.maxId:
                range_high = self.maxId

def tryAndNone(dic, key):
    try:
        return dic[key]
    except KeyError:
        return None

db = DBCONN('scraper', 'localhost', 'postgres', 'd11Rigent')
db.cur.execute("DROP TABLE cache CASCADE;")
db.cur.execute("DROP TABLE link_track;")
#si = SCRAPING_INSTANCE('test_config.json')
executor = EXECUTOR('test_config.json')
