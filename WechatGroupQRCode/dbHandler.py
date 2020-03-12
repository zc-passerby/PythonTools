#! /usr/bin/env python
# -*- coding=utf-8 -*-

import sqlite3
import traceback
import MySQLdb


class ObjSqliteConnector(object):
    """docstring for ObjSqliteConnector"""

    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.dbConn = None
        self.dbCursor = None
        self.conFlag = self._Connect()

    def _Connect(self):
        if not self.dbPath: return False
        try:
            self.dbConn = sqlite3.connect(self.dbPath)
            self.dbConn.text_factory = str
            self.dbCursor = self.dbConn.cursor()
            return True
        except:
            print traceback.format_exc()
            return False

    def _executeSql(self, sql):
        try:
            if not self.conFlag:
                self._Connect()
            # print sql
            self.dbCursor.execute(sql)
            self.dbConn.commit()
            return (True, 'successful')
        except:
            return (False, traceback.format_exc())

    def _executeSqlFormat(self, sql, params):
        try:
            if not self.conFlag:
                self._Connect()
            # print sql, params
            self.dbCursor.execute(sql, params)
            self.dbConn.commit()
            return (True, 'successful')
        except:
            return (False, traceback.format_exc())

    def _executeMany(self, sql, params):
        try:
            if not self.conFlag:
                self._Connect()
            # print sql, params
            self.dbCursor.executemany(sql, params)
            self.dbConn.commit()
            return (True, 'successful')
        except:
            return (False, traceback.format_exc())

    def _querySql(self, sql):
        try:
            if not self.conFlag:
                self._Connect()
            # print sql
            self.dbCursor.execute(sql)
            retList = self.dbCursor.fetchall()
            if len(retList) <= 0 and type(retList) != list:
                retList = None
            return (True, retList)
        except:
            return (False, traceback.format_exc())

    def _querySqlFormat(self, sql, params):
        try:
            if not self.conFlag:
                self._Connect()
            # print sql, params
            self.dbCursor.execute(sql, params)
            retList = self.dbCursor.fetchall()
            if len(retList) <= 0 and type(retList) != list:
                retList = None
            return (True, retList)
        except:
            return (False, traceback.format_exc())

    def createTable(self, tableName, tableColumns):
        self.dropTable(tableName)
        createSql = "CREATE TABLE {0} ({1});".format(tableName, ','.join(tableColumns))
        return self._executeSql(createSql)

    def dropTable(self, tableName):
        deleteSql = "DROP TABLE IF EXISTS {0};".format(tableName)
        return self._executeSql(deleteSql)

    def insert(self, tableName, values, columns=''):
        try:
            bRet, Result = False, 'System Error'
            if type(values) != list and type(values[0]) != tuple:
                bRet, Result = False, 'values is not fit for [(),]'
                return
            valuesLen = len(values)
            columnLen = len(values[0])
            if columnLen <= 0 or valuesLen <= 0:
                bRet, Result = False, 'there has not data to insert'
                return
            insertSqlFormat = 'INSERT INTO `{0}` {1} values (?' + ',?' * (columnLen - 1) + ');'
            insertSql = insertSqlFormat.format(tableName, columns)
            if valuesLen == 1:
                bRet, Result = self._executeSqlFormat(insertSql, values[0])
            else:
                bRet, Result = self._executeMany(insertSql, values)
        except:
            bRet, Result = False, traceback.format_exc()
        finally:
            return (bRet, Result)

    def select(self, tableName, columns='*', whereClause='', whereValue=''):
        try:
            bRet, Result = False, 'System Error'
            if columns == '': columns = '*'
            valueCount = 0
            if whereClause != '':
                valueCount = len(whereValue)
                clauseCount = whereClause.count('?');
                if valueCount != clauseCount or type(whereValue) != tuple:
                    bRet, Result = False, 'whereData not fit whereClause'
                    return
            selectSqlFormat = "select {0} from {1}"
            if valueCount != 0:
                selectSql = selectSqlFormat.format(columns, tableName) + ' where ' + whereClause + ';'
                bRet, Result = self._querySqlFormat(selectSql, whereValue)
            else:
                selectSql = selectSqlFormat.format(columns, tableName) + ';'
                bRet, Result = self._querySql(selectSql);
        except:
            bRet, Result = False, traceback.format_exc()
        finally:
            return (bRet, Result)

    def selectAndGetId(self, tableName, columns='*', whereClause='', whereValue=''):
        bRet, Result = self.select(tableName, columns, whereClause, whereValue)
        if bRet:
            if str(Result[0][0]).isdigit():
                Result = int(Result[0][0])
            else:
                bRet, Result = False, 'select result is not a integer'
        return bRet, Result

    def update(self, tableName, columns, values, whereClause='', whereValue=''):
        try:
            bRet, Result = False, 'System Error'
            if type(columns) != tuple or type(values) != tuple:
                bRet, Result = False, 'columns or values type is not tuple'
                return
            columnCount = len(columns)
            valuesCount = len(values)
            if columnCount != valuesCount:
                bRet, Result = False, 'columns not fit values'
                return
            whereValueCount = 0
            if whereClause != '':
                whereValueCount = len(whereValue)
                whereClauseCount = whereClause.count('?');
                if whereValueCount != whereClauseCount or type(whereValue) != tuple:
                    bRet, Result = False, 'whereData not fit whereClause'
                    return
            columnStr = ''
            for item in columns:
                target = '`' + str(item) + '`=?,'
                columnStr += target
            columnStr = columnStr[:-1]
            updateSqlFormat = "UPDATE {0} SET {1}"
            if whereValueCount != 0:
                updateSql = updateSqlFormat.format(tableName, columnStr) + ' where ' + whereClause + ';'
                bRet, Result = self._executeSqlFormat(updateSql, values + whereValue)
            else:
                updateSql = updateSqlFormat.format(tableName, columnStr) + ';'
                bRet, Result = self._executeSqlFormat(updateSql, values)
        except:
            bRet, Result = False, traceback.format_exc()
        finally:
            return (bRet, Result)

    def delete(self, tableName, whereClause='', whereValue=''):
        try:
            bRet, Result = False, 'System Error'
            valueCount = 0
            if whereClause != '':
                valueCount = len(whereValue)
                clauseCount = whereClause.count('?');
                if valueCount != clauseCount or type(whereValue) != tuple:
                    bRet, Result = False, 'whereData not fit whereClause'
                    return
            deleteSql = "DELETE FROM " + tableName
            if valueCount != 0:
                deleteSql = deleteSql + ' where ' + whereClause + ';'
                bRet, Result = self._executeSqlFormat(deleteSql, whereValue)
            else:
                deleteSql = deleteSql + ';'
                bRet, Result = self._executeSql(deleteSql);
        except:
            bRet, Result = False, traceback.format_exc()
        finally:
            return (bRet, Result)


def PokeDexBuild(sqliteConn):
    print sqliteConn.dropTable('PokeDex')
    print sqliteConn.createTable('PokeDex', (
        '"Sn" TEXT NOT NULL ON CONFLICT IGNORE DEFAULT ""', '"NameZh" TEXT NOT NULL DEFAULT ""',
        '"NameJp" TEXT NOT NULL DEFAULT ""', '"NameEn" TEXT NOT NULL DEFAULT ""', 'PRIMARY KEY ("Sn")'))
    bRet, result = sqliteConn.select('PokemonBaseInfo', 'Sn, NameZh, NameJp, NameEn')
    for tInfo in result:
        Sn, NameZh, NameJp, NameEn = tInfo
        NameZh = NameZh.split('【')[0]
        print sqliteConn.insert('PokeDex', [(Sn, NameZh, NameJp, NameEn), ])


def PokemonMovementsGainBuild(sqliteConn):
    print sqliteConn.dropTable('PokemonMovementsGain')
    print sqliteConn.createTable('PokemonMovementsGain', (
        '"Sn" TEXT NOT NULL', '"Name" TEXT NOT NULL', '"MovementsJson" TEXT NOT NULL', '"Gen1Json" TEXT',
        '"Gen2Json" TEXT', '"Gen3Json" TEXT', '"Gen4Json" TEXT', '"Gen5Json" TEXT', '"Gen6Json" TEXT',
        '"Gen7Json" TEXT', '"Gen8Json" TEXT', 'PRIMARY KEY ("Sn")'))


def WechatQrcodeInfoBuild(sqliteConn):
    create_sql = 'CREATE TABLE wechat_qrcode_info ( "qrcode_url" TEXT NOT NULL, "qrcode_filename" TEXT NOT NULL, "website_name" TEXT NOT NULL, "create_time" TEXT NOT NULL );'
    unique_sql = 'CREATE UNIQUE INDEX "url" ON "wechat_qrcode_info" ( "qrcode_url" );'
    print sqliteConn._executeSql(create_sql)
    print sqliteConn._executeSql(unique_sql)


def InsertWechatQrcodeInfo(sqliteConn, qrcode_url, qrcode_filename, website_name, create_time):
    print sqliteConn.insert('wechat_qrcode_info', [(qrcode_url, qrcode_filename, website_name, create_time), ])


def insertIntoMysql(data):
    data_new = [str(x) for x in data]
    value_list = ','.join(data_new)
    insert_sql = "insert into `wechat_group_qrcode` (`qrcode_url`, `qrcode_filename`, `create_time`) values " + value_list + ";"
    # 打开数据库连接
    db = MySQLdb.connect("127.0.0.1", "root", "yt6533629@100", "u_crm_db_dev", charset='utf8')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    try:
        # 执行sql语句
        cursor.execute(insert_sql)
        # 提交到数据库执行
        db.commit()
    except:
        # Rollback in case there is any error
        db.rollback()
    # 关闭数据库连接
    db.close()


def SyncSqliteToMysql(sqliteConn):
    try:
        status, result = sqliteConn.select('wechat_qrcode_info', 'qrcode_url, qrcode_filename, create_time')
        if status:
            insertIntoMysql(result)
    except:
        print traceback.format_exc()


if __name__ == '__main__':
    pass
    # sqliteConn = ObjSqliteConnector("./52Poke.db3")
    # PokeDexBuild(sqliteConn)
    # PokemonMovementsGainBuild(sqliteConn)
    # sqliteConn._executeSql('VACUUM') # 释放空间
