#! /usr/bin/env python
#-*- coding=utf-8 -*-
import sqlite3, traceback

class ObjSqliteConnector(object):
    """docstring for ObjSqliteConnector"""
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.dbConn = None
        self.dbCursor = None
        self.conFlag = self._Connect()

    def _Connect(self):
        if not self.dbPath : return False
        try:
            self.dbConn = sqlite3.connect(self.dbPath)
            self.dbCursor = self.dbConn.cursor()
            return True
        except:
            print traceback.format_exc()
            return False

    def _executeSql(self, sql):
        try:
            if not self.conFlag:
                self._Connect()
            self.dbCursor.execute(sql)
            self.dbConn.commit()
            return True
        except:
            print traceback.format_exc()
            return False

    def _executeSqlFormat(self, sql, params):
        try:
            if not self.conFlag:
                self._Connect()
            self.dbCursor.execute(sql, params)
            self.dbConn.commit()
            return (True, 'successful')
        except:
            return (False, traceback.format_exc())

    def _executeMany(self, sql, params):
        try:
            if not self.conFlag:
                self._Connect()
            self.dbCursor.executemany(sql, params)
            self.dbConn.commit()
            return (True, 'successful')
        except:
            return (False, traceback.format_exc())

    def _querySql(self, sql):
        try:
            if not self.conFlag:
                self._Connect()
            self.dbCursor.execute(sql)
            retList = self.dbCursor.fetchall()
            if len(retList) <= 0 and type(retList) != list:
                retList = None
            return retList
        except:
            print traceback.format_exc()
            return None


    def _querySqlFormat(self, sql, params):
        pass

    def createTable(self, tableName, tableColumns):
        self.dropTable(tableName)
        createSql = "CREATE TABLE {0} ({1});".format(tableName, ','.join(tableColumns))
        return self._executeSql(createSql)

    def dropTable(self, tableName):
        deleteSql = "DROP TABLE IF EXISTS {0};".format(tableName)
        return self._executeSql(deleteSql)

    def insert(self, tableName, values, columns = ''):
        try:
            bRet, Reason = False, 'System Error'
            if type(values) != list and type(values[0]) != tuple:
                return (False, 'values is not fit for [(),]')
            valuesLen = len(values)
            colunmLen = len(values[0])
            if colunmLen <= 0 or valuesLen <= 0:
                return (False, 'there has not data to insert')
            insertSqlFormat = 'INSERT INTO `{0}` {1} values (?' + ',?' * (colunmLen - 1) + ');'
            insertSql = insertSqlFormat.format(tableName, columns)
            print insertSql, valuesLen
            if valuesLen == 1:
                bRet, Reason = self._executeSqlFormat(insertSql, values[0])
            else:
                bRet, Reason = self._executeMany(insertSql, values)
            return bRet, Reason
        except:
            return (False, traceback.format_exc())

    def query(self, tableName, columns = None, whereClause = None):
        selectSql = 'SELECT {0} from {1} {2};'
        columnStr = '*'
        if columns != None and columns != "*":
            columnStr = "`" + "`,`".join(columns) + "`"
        whereClauseStr = ''
        if whereClause is not None:
            whereClauseStr = "where " + whereClause
        return self._querySql(selectSql.format(columnStr, tableName, whereClauseStr))

    def queryGetId(self, tableName, columns = None, whereClause = None):
        retInt = self.query(tableName, columns, whereClause)
        if retInt != None:
            if str(retInt[0][0]).isdigit():
                retInt = int(retInt[0][0])
            else:
                retInt = None
        return retInt



if __name__ == '__main__':
    sqliteConn = ObjSqliteConnector("./test.sqlite")
    print sqliteConn.createTable('abc', ['id integer primary key autoincrement', 'name varchar(128), info varchar(128)'])
    print sqliteConn.insert('abc', [(1, 'a', 'a'), (2, 'b', 'b'), (3, 'c', 'c')])
    print sqliteConn.insert('abc', [(4, 'd'), (5, 'e')], '(id, name)')
    print sqliteConn.insert('abc', [(4, 'd'), (5, 'e')], '(id, name)')
    print sqliteConn.insert('abc', [(6, 'f'), (7, 'g')], '(id, info)')
    print sqliteConn.insert('abc', [(8, 'h')], '(id, name)')
    print sqliteConn.insert('abc', [(9, 'i', 'i')])
    print sqliteConn.query('abc')
    print sqliteConn.query('abc', ['id'], 'id=5')
    print sqliteConn.queryGetId('abc', ['info'], 'id=5')
    #sqliteConn.dropTable('abc')