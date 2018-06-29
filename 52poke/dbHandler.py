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

    def _executeSqlFormat(self, sql, param):
        try:
            if not self.conFlag:
                self._Connect()
            self.dbCursor.execute(sql, param)
            self.dbConn.commit()
            return True
        except:
            print traceback.format_exc()
            return False

    def executeSql(self, sqlStr):
        if not self.conFlag:
            self._Connect()
        return self._executeSql(sqlStr)

    def createTable(self, tableName, tableColumns):
        self.dropTable(tableName)
        createSql = "CREATE TABLE {0} ({1});".format(tableName, ','.join(tableColumns))
        return self._executeSql(createSql)

    def dropTable(self, tableName):
        deleteSql = "DROP TABLE IF EXISTS {0};".format(tableName)
        return self._executeSql(deleteSql)

    def insert(self, tableName, values, columns = None):
        insertSql = 'INSERT INTO {0} {1} values {2};'.format(tableName)
        columnStr = ''
        if columns is not None:
            columnStr = "(`" + "`,`".join(columns) + "`)"
        valueStr = "('" + "','".join(values) + "')"
        print columnStr, valueStr
        self.dbCursor.execute('insert into abc (id, name) values (?,?)', (1, 'abc'))
        self.dbConn.commit()
        return self._executeSqlFormat(insertSql, (columnStr, valueStr))


if __name__ == '__main__':
    sqliteConn = ObjSqliteConnector("./test.sqlite")
    sqliteConn.createTable('abc', ['id integer primary key autoincrement', 'name varchar(128), info varchar(128)'])
    sqliteConn.insert('abc', ['1', '2', '3'])
    #sqliteConn.dropTable('abc')