# 提供对于测试图存档、共享功能
from enum import Enum
import sqlite3 as sql

FRAMEWORK_DATABASE_PATH = './test_framework.db'

sql_map = {
'save_info': '''
                create table save_info(
                    save_name   varchar(128) not null,
                    save_time   datetime     not null default (datetime('now','localtime')),
                    description varchar(256) ,
                    type        varchar(2)   not null default '1', -- module 0 , graph 1
                    category    varchar(64)  not null default 'uncategorized', -- category name
                    PRIMARY KEY (save_name)
                );
            '''           
}

class SaveResponseType(Enum):
    # 存储成功
    SUCCESS     = 0
    # 存储重名
    DUPLICATE   = 1
    # 存储异常
    EXCEPTION   = 2

class SaveResponse(dict):
    def __init__(self,code:SaveResponseType,data) -> None:
        self.code=code
        self.data=data
        dict.__init__(self,code=code.value,data=data)

class DBUtils:
    @staticmethod
    def queryOrCreate(conn,table):
        cursor = []
        try:
            cursor = conn.execute('select * from {}'.format(table))
        except Exception as err:
            conn.execute(sql_map[table])
        # conn.
        return cursor

class SaveService:
    @staticmethod
    def getAllSaveInfo():
        print('get all save info')
        with sql.connect(FRAMEWORK_DATABASE_PATH) as conn:
            cursor = DBUtils.queryOrCreate(conn,'save_info')
            result = []
            for row in cursor:
                print(row)
                result.append({'save_name':row[0],'save_time':row[1],'description':row[2],'type':row[3],'category':row[4]})
        return result

    @staticmethod
    def getSave(saveName):
        print('get save: {}'.format(saveName))
        pass

    @staticmethod
    def addSave(saveName,saveType,saveCatogery,jsonGraph):
        print('add save: {} {} {} {}'.format(saveName,saveType,saveCatogery,jsonGraph))
        pass

    @staticmethod
    def delSave(saveName):
        print('delete save: {} {} {} {}'.format(saveName))
        pass
