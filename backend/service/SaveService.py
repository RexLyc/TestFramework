# 提供对于测试图存档、共享功能
from enum import Enum
import sqlite3 as sql
import os
import logging

FRAMEWORK_DATABASE_PATH = './test_framework.db'
FRAMEWORK_DATA_DIR      = './data'
FRAMEWORK_SAVE_DIR      = FRAMEWORK_DATA_DIR + '/save/'
FRAMEWORK_REPORT_DIR    = FRAMEWORK_DATA_DIR + '/report/'

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
    # 存储异常
    EXCEPTION   = 1

class SaveResponse(dict):
    def __init__(self,code:SaveResponseType,data=None) -> None:
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
    
    @staticmethod
    def insert(conn,table,**kwargs):
        names = ''
        values = ''
        for key,value in kwargs.items():
            names+='`'+key+'`,'
            values+="'"+value+"',"
            logging.info(key,values)
        sqlStatement= 'insert into {} ({}) values({})'.format(table,names[:-1],values[:-1])
        logging.info(sqlStatement)
        return conn.execute(sqlStatement)
    
    @staticmethod
    def delete(conn,table,where):
        sqlStatement = 'delete from {} {}'.format(table,where)
        logging.info(sqlStatement)
        conn.execute(sqlStatement)


class SaveService:
    @staticmethod
    def init():
        # 初始化环境，建立表格、文件夹
        SaveService.getAllSaveInfo()
        if not os.path.isdir(FRAMEWORK_SAVE_DIR):
            os.makedirs(FRAMEWORK_SAVE_DIR)
        if not os.path.isdir(FRAMEWORK_REPORT_DIR):
            os.makedirs(FRAMEWORK_REPORT_DIR)

    @staticmethod
    def getAllSaveInfo():
        logging.info('get all save info')
        with sql.connect(FRAMEWORK_DATABASE_PATH) as conn:
            cursor = DBUtils.queryOrCreate(conn,'save_info')
            result = []
            for row in cursor:
                result.append({'save_name':row[0],'save_time':row[1],'description':row[2],'type':row[3],'category':row[4]})
        return SaveResponse(SaveResponseType.SUCCESS,result)

    @staticmethod
    def getSave(saveNames):
        logging.info('get save: {}'.format(saveNames))
        nameTypeMap = {}
        with sql.connect(FRAMEWORK_DATABASE_PATH) as conn:
            cursor = DBUtils.queryOrCreate(conn,'save_info')
            for row in cursor:
                nameTypeMap[row[0]]=row[3]
        # 找到其中的graph、module
        ret = {'graph':None,'modules':[]}
        for i in saveNames:
            if i not in nameTypeMap:
                continue
            fi = open(FRAMEWORK_SAVE_DIR+'/'+i+'.json','r')
            data = fi.read()
            fi.close()
            if nameTypeMap[i]=='0':
                # 加载模块
                ret['modules'].append(data)
            else:
                # 加载测试图
                ret['graph'] = data
        return SaveResponse(SaveResponseType.SUCCESS,ret)

    @staticmethod
    def addSave(save_name,type,category,description,jsonGraph):
        logging.info('add save: {} {} {} {} {}'.format(save_name,type,category,description,jsonGraph))
        with sql.connect(FRAMEWORK_DATABASE_PATH) as conn:
            cursor = DBUtils.insert(conn,'save_info',save_name=save_name,type=type,category=category,description=description)
            fo = open(FRAMEWORK_SAVE_DIR+'/'+save_name+'.json', "w")
            fo.write(jsonGraph)
            fo.close()
        return SaveResponse(SaveResponseType.SUCCESS)

    @staticmethod
    def deleteSave(deleteNames):
        logging.info('delete save: {}'.format(deleteNames))
        with sql.connect(FRAMEWORK_DATABASE_PATH) as conn:
            names = ''
            for i in deleteNames:
                names+="'{}',".format(i)
            where = 'where save_name in ({})'.format(names[:-1])
            cursor = DBUtils.delete(conn,'save_info',where=where)
        # 尽力删除，不删也没关系
        try:
            for i in deleteNames:
                os.remove(FRAMEWORK_SAVE_DIR+'/'+i+'.json')
        except Exception as err:
            logging.info(err)
        logging.info(cursor)
        pass

    @staticmethod
    def getCategory():
        with sql.connect(FRAMEWORK_DATABASE_PATH) as conn:
            cursor = DBUtils.queryOrCreate(conn,'save_info')
            categoryName = set()
            for row in cursor:
                categoryName.add(row[4])
            result={'categoryName':list(categoryName)}
        return result
