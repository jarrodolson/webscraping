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

import psycopg2
import psycopg2.extras

class DBCONN:
    def __init__(self, dbname, host, user, pw):
        try:
            self.conn = psycopg2.connect("dbname='{0}'"
                                         "user='{1}'"
                                         "host='{2}'"
                                         "password='{3}'".format(dbname,
                                                                 user,
                                                                 host,
                                                                 pw))
            ##DictCursor allows us to reference column by name, rather than row
            self.cur = self.conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
            self.conn.autocommit = True
        except pscyopg2.ProgrammingError:
            self.conn = None
            self.cur = None
        
    def getMaxId(self, idColName, tableName):
        self.cur.execute("SELECT MAX({0}) FROM {1};".format(idColName, tableName))
        maxId = self.cur.fetchone()[0]
        return maxId
