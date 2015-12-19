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
