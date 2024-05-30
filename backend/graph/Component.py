import json
import time
import requests
from queue import Queue
from enum import Enum
import socket
import asyncio
import websockets
import sys
import glob
import serial
from concurrent.futures import ThreadPoolExecutor
# import threading
import uuid
import os
from threading import Event
import logging
import easyocr
import pyautogui
import numpy
import timeit
from Crypto.PublicKey import ECC
from Crypto.Hash import SHA256
from Crypto.Signature import DSS

def sm2_verify(public_key_pem, message, signature):
    """
    使用pycryptodome库进行SM2公钥验签
    :param public_key_pem: SM2公钥的PEM格式字符串
    :param message: 原始消息的字节串
    :param signature: 签名的字节串
    :return: 验签结果 (True/False)
    """
    # 加载公钥
    # public_key = ECC.import_key(public_key_pem)
    
    # 创建一个hash对象用于计算消息摘要
    hash_obj = SHA256.new(message)
    
    # 初始化签名验证器
    verifier = DSS.new(public_key_pem, 'fips-186-3')
    
    # 验证签名
    try:
        verifier.verify(hash_obj, signature)
        return True
    except ValueError:
        return False

class ExitStateEnum(Enum):
    # 正常结束
    SUCCESS     = 0
    # 整体超时
    TIMEOUT     = 1
    # 测试异常
    TESTERROR   = 2
    # 其他异常
    EXCEPTION   = 3
    # 被杀死
    KILLED      = 4
    # 断言未通过
    ASSERTERROR = 5
    # 无效
    INVALID     = 6

# ================= 运行结果、错误 ================= 
class RunResult(dict):
    # 总用时，全部日志，退出状态
    def __init__(self,timeElapsed,log,exitState:ExitStateEnum,testUUID:uuid.UUID):
        self.timeElapsed=timeElapsed
        self.log=log
        self.exitState=exitState.value
        self.testUUID=testUUID.hex
        dict.__init__(self,timeElapsed=timeElapsed,log=self.log,exitState=self.exitState,testUUID=self.testUUID)

class TestError(RuntimeError):
    def __init__(self,nodeName='global',msg='error'):
        self.nodeName=nodeName
        self.msg=msg
    
    def __format__(self, __format_spec: str) -> str:
        return '{}'.format(self.msg)

class TestRuntimeError(TestError):
    pass

class TestIncompatibleError(TestError):
    pass

class TestModuleError(TestRuntimeError):
    pass

class TestAssertError(TestRuntimeError):
    pass

class TestFlowAssertError(TestAssertError):
    pass

class TestStructureAssertError(TestAssertError):
    pass

class TestDataAssertError(TestAssertError):
    pass


# ================= 工具 =================
class PythonValue:
    def __init__(self,script) -> None:
        self.script = script
    
    def __call__(self, *args, **kwds):
        return compile(self.script,'','exec')

class HexValue:
    def __init__(self,hexStr) -> None:
        logging.info('save hexValue str: {}'.format(hexStr))
        self.hexStr = hexStr

    def __call__(self, *args, **kwds):
        return bytes.fromhex(self.hexStr)

class Tools:
    @staticmethod
    def getParamType(typeName):
        if typeName == 'VarNameValue' or typeName == 'StringValue':
            return str
        elif typeName == 'IntegerValue':
            return int
        elif typeName == 'FloatValue':
            return float
        elif typeName == 'BoolValue':
            return bool
        elif typeName == PythonValue.__name__:
            return PythonValue
        elif typeName == 'HexValue':
            return HexValue
        else:
            return None
    
    @staticmethod
    def log(global_data,logData,loggerName='Default'):
        if isinstance(logData,bytes):
            logData = logData.hex(sep=' ',bytes_per_sep=1)
        logging.info('logging {}'.format(logData))
        if '$$log' not in global_data:
            global_data['$$log'] = ''
        global_data['$$log'] = global_data['$$log'] + '{}({}): {}\n'.format(loggerName,time.time(),logData)

    @staticmethod
    def createTcpFile(addr,port):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setblocking(True)
        s.connect((addr,port))
        return s
    
    @staticmethod
    async def createWebsocketFile(url):
        try:
            websocket = await websockets.connect(url)
        except ConnectionRefusedError as e:
            logging.info('ws refuse {}'.format(e))
        return websocket

    @staticmethod
    async def recvWebsocket(websocket,timeout):
        try:
            return await asyncio.wait_for(websocket.recv(),timeout)
        except asyncio.TimeoutError as err:
            logging.info('websocket recv timeout: {}'.format(err))

    @staticmethod
    async def sendWebsocket(websocket,dataBody,timeout):
        try:
            return await asyncio.wait_for(websocket.send(dataBody),timeout)
        except asyncio.TimeoutError as err:
            logging.info('websocket send timeout: {}'.format(err))

    @staticmethod
    def createSeralFile(name,baudrate,parity='N',bytesize=8,stopbits=1):
        return serial.Serial(port=name,baudrate=baudrate,parity=parity,stopbits=stopbits,bytesize=bytesize)
    
    @staticmethod
    def strTobytes(string):
        # 将十六进制字符串转为bytes
        return bytes.fromhex(string)
    
    @staticmethod
    def jsonStructureCompare(src_data,dst_data):
        '''
        json结构递归对比\n
            1. 每一层类型需要相同：dict、list、其他\n
            2. 为dict时，要求key集合等价，对value递归\n
            3. 为list时\n
                1. 如果所有src_data类型相同，且所有dst_data类型相同，允许二者长度不匹配，取公共长度部分进行递归\n
                2. 否则长度必须匹配，进行递归\n
            4. 其他，恒为True\n
        '''
        if type(src_data) != type(dst_data):
            return False
        if isinstance(src_data, dict):
            # """若为dict格式"""
            for key in dst_data:
                if key not in src_data:
                    return False
            for key in src_data:
                if key not in dst_data:
                    return False
            # 对所有value递归
            for key in src_data:
                if Tools.jsonStructureCompare(src_data[key],dst_data[key]) == False:
                    return False
        elif isinstance(src_data, list):
            # """若为list格式"""
            # 当且仅当所有value同一类型，才允许有数量差异
            sameType = True
            for i in range(0,len(src_data)):
                if type(src_data[i]) != type(src_data[0]):
                    sameType = False
                    break
            if sameType == True:
                for i in range(0,len(dst_data)):
                    if type(dst_data[i]) != type(dst_data[0]):
                        sameType = False
                        break
            if sameType == False and len(src_data) != len(dst_data):
                return False
            # 同一类型，或者不同类型但是长度相等，继续递归判断
            for i in range(0,min(len(src_data),len(dst_data))):
                if Tools.jsonStructureCompare(src_data[i],dst_data[i]) == False:
                    return False
        else:
            # 其他情况不需要递归，直接判相同
            return True
    
    @staticmethod
    def jsonDataCompare(src_data,dst_data):
        '''
        json类型数据对比，每一层长度、类型都必须完全相同
        '''
        # 类型或长度任何一个不等都判负
        if type(src_data) != type(dst_data):
            return False
        if isinstance(src_data, dict):
            # """若为dict格式"""
            if len(src_data) != len(dst_data):
                return False
            for key in dst_data:
                if key not in src_data:
                    return False
            for key in src_data:
                if key not in dst_data:
                    return False
            # 对所有value递归
            for key in src_data:
                if Tools.jsonDataCompare(src_data[key],dst_data[key]) == False:
                    return False
        elif isinstance(src_data, list):
            # """若为list格式"""
            # 继续递归判断
            if len(src_data) != len(dst_data):
                return False
            for i in range(0,len(src_data)):
                if Tools.jsonDataCompare(src_data[i],dst_data[i]) == False:
                    return False
        else:
            # 其他情况不需要递归，直接判断
            return src_data == dst_data

# ================= IO参数 抽象 ================= 
class File:
    def __init__(self,file):
        self.file=file
    
    def close(self):
        self.file.close()

class HttpFile(File):
    def __init__(self,url,method):
        super().__init__(None)
        self.url=url
        self.method=method

    def close(self):
        # http file don't need to close
        pass

class TcpFile(File):
    pass

class WebsocketFile(File):
    pass

class SerialFile(File):
    pass

# ================= 测试报告 =================
class TimelineEntity(dict):
    def __init__(self, nodeName) -> None:
        self.nodeName = nodeName
        # self.totalTime = 0
        self.timelines = dict()
        dict.__init__(self,nodeName = self.nodeName, timelines = self.timelines)

    def markBegin(self,nodeFullName):
        self.timelines[nodeFullName] = [timeit.default_timer()]

    def markEnd(self,nodeFullName):
        self.timelines[nodeFullName].append(timeit.default_timer())
        # self.totalTime += round(self.timelines[nodeFullName][1]-self.timelines[nodeFullName][0],6)
        # self['totalTime']=self.totalTime

# 记录时间线
class TestTimeline(dict):
    def __init__(self) -> None:
        self.timelineMap = dict()
        dict.__init__(self,timelineMap = self.timelineMap)
    
    # 标记指定节点开启一个新的运行期
    def markNodeBegin(self,nodeType,nodeName,nodeFullName):
        if nodeType not in self.timelineMap:
            self.timelineMap[nodeType] = dict()
        if nodeFullName not in self.timelineMap[nodeType]:
            self.timelineMap[nodeType][nodeName] = TimelineEntity(nodeName)
        self.timelineMap[nodeType][nodeName].markBegin(nodeFullName)

    # 标记指定节点结束运行期
    def markNodeEnd(self,nodeType,nodeName,nodeFullName):
        self.timelineMap[nodeType][nodeName].markEnd(nodeFullName)

# 记录拓扑关系（前驱后继，以及生成关系）
class TestTopology(dict):
    def __init__(self) -> None:
        self.runOrderList = []
        self.generateMap  = dict()
        self.nodeIndexMap = dict()
        dict.__init__(self,runOrderList= self.runOrderList, generateMap = self.generateMap)

    def nodeNew(self,prevNodeName,newNodeName):
        if prevNodeName not in self.generateMap:
            self.generateMap[prevNodeName] = []
        if newNodeName not in self.nodeIndexMap:
            self.nodeIndexMap[newNodeName] = 0
        newNodeFullName = newNodeName+' x'+str(self.nodeIndexMap[newNodeName])
        self.generateMap[prevNodeName].append(newNodeFullName)
        return newNodeFullName
    
    def nodeNewRound(self):
        '''
        标记一轮新增节点的结束，对所有nodeIndex进行自增
        '''
        for name in self.nodeIndexMap:
            self.nodeIndexMap[name] += 1
    
    def nodeRun(self,currentNodeName):
        self.runOrderList.append(currentNodeName)

# ================= 运行节点 =================
class BaseNode:
    def __init__(self, graph_node):
        self.name=graph_node['name']
        self.inputs=graph_node['inputs']['params']
        self.outputs=graph_node['outputs']['params']
        self.typeName=graph_node['typeName']
        self.data=graph_node['data']
        self.writeBackVar=dict()
        # 统计所有待回写变量
        for paramIndex in range(0,len(self.outputs)):
            for outputVar in self.outputs[paramIndex]['paramRef']:
                if str(outputVar).count(VariableNode.__name__)==1:
                    self.writeBackVar[outputVar]='{}${}'.format(self.name,paramIndex)


    def __str__(self):
        return 'Type: {}, Id: {}'.format(self.__class__, self.name)

    def _run(self,data,testParam,prevNode):
        pass
    
    def _writeBack(self,data):
        for (outputVar,param) in self.writeBackVar.items():
            data[outputVar]=data[param]

    def _post(self,data,testParam,prevNode):
        next = []
        for nextNode in self.outputs[0]['paramRef']:
            next.append(str(nextNode).partition('$')[0])
        return next, True

    # 执行运算，并返回下一个运行的节点
    def doRun(self,data,testParam=None,prevNode=None):
        try:
            self._run(data,testParam,prevNode)
            self._writeBack(data)
            return self._post(data,testParam,prevNode)
        except TestError as err:
            raise err
        except Exception as err:
            raise TestRuntimeError(self.name,'{}'.format(err))

# TODO: 更好的文件处理方案
class FileNode(BaseNode):
    def doRun(self, data, testParam=None, prevNode=None):
        try:
            data['$$file'] += self._run(data,testParam,prevNode)
            self._writeBack(data)
            return self._post(data,testParam,prevNode)
        except TestError as err:
            raise err
        except Exception as err:
            raise TestRuntimeError(self.name,'{}'.format(err))

class BeginNode(BaseNode):
    pass

class ConstantNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        for i in range(0,len(self.outputs)):
            runType = Tools.getParamType(self.outputs[i]['paramType'])
            if runType == None:
                raise TestRuntimeError(self.name,'unsupported runType: {}'.format(self.outputs[i]['paramType']))
            elif runType == bool:
                # bool 类型比较特殊, bool("0")为false，需要先转一下
                self.outputs[i]['paramValue']=int(self.outputs[i]['paramValue'])
            temp = runType(self.outputs[i]['paramValue'])
            logging.info('constant setting: {} {}'.format(temp,type(temp)))
            data[self.name+'$'+str(i)] = runType(self.outputs[i]['paramValue'])

class VariableNode(ConstantNode):
    pass

class EndNode(BaseNode):
    def _post(self,data,testParam,prevNode):
        return [], True

class HttpNode(FileNode):
    def _run(self,data,testParam,prevNode):
        url = data[self.inputs[1]['paramRef'][0]]
        method = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1']=HttpFile(url,method)
        return [data[self.name+'$1']]

class SendNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        file = data[self.inputs[1]['paramRef'][0]]
        rawData = data[self.inputs[2]['paramRef'][0]]
        timeout = data[self.inputs[3]['paramRef'][0]]
        result = ''
        dataBody = '{}'.format(rawData).encode()
        if isinstance(file,HttpFile):
            logging.info(dataBody)
            headers = {'Content-Type':'application/json'}
            resp = requests.request(method=file.method,headers=headers,url=file.url,data=dataBody,timeout=timeout)
            if not resp.ok:
                raise TestRuntimeError(self.name,'http send failed: {}'.format(resp.text))
            result = resp.text
        elif isinstance(file,TcpFile):
            file.file.settimeout(timeout)
            if isinstance(rawData,HexValue):
                result = file.file.sendall(rawData())
                
            else:
                result = file.file.sendall(dataBody)
        elif isinstance(file,WebsocketFile):
            logging.info("sendnode, send websocket")
            result = asyncio.get_event_loop().run_until_complete(Tools.sendWebsocket(file.file,rawData,timeout))
        elif isinstance(file,SerialFile):
            # 将str 转 bytes
            if isinstance(rawData,str):
                try:
                    rawData = Tools.strTobytes(rawData)
                except Exception as err:
                    raise TestRuntimeError(self.name,'bad hex string')
            elif isinstance(rawData,bytes):
                pass
            else:
                raise TestRuntimeError(self.name,'unsupport serial send data type: {}'.format(type(rawData)))

            result = file.file.write(rawData)
        else:
            raise TestRuntimeError(self.name,'unsupport SendNode file')
        data[self.name+'$1']=result

class LogNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        logData = ''
        for i in self.inputs[1]['paramRef']:
            if isinstance(data[i],bytes):
                logData += str(data[i].hex()) +' '
            else:
                logData += str(data[i]) +' '
        Tools.log(data,logData,self.name)

class ExtractNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        inputData = data[self.inputs[1]['paramRef'][0]]
        outputData = outputData = inputData[data[self.inputs[2]['paramRef'][0]]:data[self.inputs[3]['paramRef'][0]]]
        data[self.name+'$1']=outputData

class MergeNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        data_1 = data[self.inputs[1]['paramRef'][0]]
        data_2 = data[self.inputs[2]['paramRef'][0]]
        outputData = data_1 + data_2
        data[self.name+'$1']=outputData

class TCPNode(FileNode):
    def _run(self,data,testParam,prevNode):
        addr = data[self.inputs[1]['paramRef'][0]]
        port = data[self.inputs[2]['paramRef'][0]]
        tcpFile = TcpFile(Tools.createTcpFile(addr,port))
        data[self.name+'$1'] = tcpFile
        return [data[self.name+'$1']]

class RecvNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        file = data[self.inputs[1]['paramRef'][0]]
        timeout = data[self.inputs[2]['paramRef'][0]] / 1000
        outputData = None
        if isinstance(file,HttpFile):
            pass
        elif isinstance(file,TcpFile):
            file.file.settimeout(min(timeout,10))
            try:
                outputData = file.file.recv(4096)
            except socket.timeout as err:
                logging.info('timeout')
        elif isinstance(file,WebsocketFile):
            outputData = asyncio.get_event_loop().run_until_complete(Tools.recvWebsocket(file.file,timeout))
        elif isinstance(file,SerialFile):
            # TODO: 更好的串口数据读出方案（支持各种流式数据读取）
            # 等待数据准备完成
            t1 = time.time()
            logging.info(file.file)
            while file.file.inWaiting() == 0:
                time.sleep(0.001)
                if time.time()-t1 > timeout:
                    logging.info('timeout')
                    break
            # 保证数据全部取出
            if file.file.inWaiting() !=0:
                byte_number_1 = 0
                byte_number_2 = 1
                while byte_number_1 != byte_number_2:
                    if time.time()-t1 > timeout:
                        TestError.timeoutLimitExceeded()
                    byte_number_1 = file.file.inWaiting()
                    time.sleep(0.01)
                    byte_number_2 = file.file.inWaiting()
                # 一次性读取
                outputData = file.file.read_all()
            logging.info('serial {}'.format(outputData))
        else:
            raise TestRuntimeError(self.name,'unsupport RecvNode file: {}'.format(file))
        data[self.name+'$1'] = outputData

class WebSocketNode(FileNode):
    def _run(self,data,testParam,prevNode):
        url = data[self.inputs[1]['paramRef'][0]]
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        outputData = WebsocketFile(asyncio.get_event_loop().run_until_complete(Tools.createWebsocketFile(url)))
        data[self.name+'$1'] = outputData
        return [data[self.name+'$1']]

class IfNode(BaseNode):
    def _post(self,data,testParam,prevNode):
        condition = data[self.inputs[1]['paramRef'][0]]
        logging.info(condition)
        next = []
        if condition==True:
            for nextNode in self.outputs[0]['paramRef']:
                next.append(str(nextNode).partition('$')[0])
        elif condition==False:
            for nextNode in self.outputs[1]['paramRef']:
                next.append(str(nextNode).partition('$')[0])
        else:
            raise TestRuntimeError(self.name,'invalid condition: {}'.format(condition))
        return next, True

class AddMinusNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        result = 0
        for plus in self.inputs[1]['paramRef']:
            result += data[plus]
        for minus in self.inputs[2]['paramRef']:
            result -= data[minus]
        data[self.name+'$1'] = result

class MultiDivNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        result = 1
        for mul in self.inputs[1]['paramRef']:
            result *= data[mul]
        for div in self.inputs[2]['paramRef']:
            result /= data[div]
        data[self.name+'$1'] = result

class BiggerNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        data_1 = data[self.inputs[1]['paramRef'][0]]
        data_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = data_1 > data_2

class EqualNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        data_1 = data[self.inputs[1]['paramRef'][0]]
        data_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = (data_1 == data_2)

class AndNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        condition_1 = data[self.inputs[1]['paramRef'][0]]
        condition_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = (condition_1 and condition_2)

class OrNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        condition_1 = data[self.inputs[1]['paramRef'][0]]
        condition_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = (condition_1 or condition_2)

class NotNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        inputCondition = data[self.inputs[1]['paramRef'][0]]
        data[self.name+'$1'] = (not inputCondition)

class BarrierNode(BaseNode):
    def __init__(self, graph_node):
        super().__init__(graph_node)
        # 创建记录前驱用的set
        self.prevNotDone = set()
        for prev in self.inputs[0]['paramRef']:
            self.prevNotDone.add(str(prev).partition('$')[0])

    def _post(self,data,testParam,prevNode):
        if prevNode.name in self.prevNotDone:
            self.prevNotDone.remove(prevNode.name)
        if not self.prevNotDone:
            return super()._post(data,testParam,prevNode)
        else:
            return [], False

class SwitchNode(BaseNode):
    def __genNext(self,output):
        next = []
        for nextNode in output['paramRef']:
            next.append(str(nextNode).partition('$')[0])
        return next, True

    def _post(self,data,testParam,prevNode):
        testData = data[self.inputs[1]['paramRef'][0]]
        for i in range(2,len(self.inputs)):
            logging.info('{} {}'.format(2,len(self.inputs)))
            tempTestData = testData
            if type(tempTestData) != type(data[self.inputs[i]['paramRef'][0]]):
                # 类型不相等，需要进行处理
                if isinstance(tempTestData,bytes) and isinstance(data[self.inputs[i]['paramRef'][0]],str):
                    tempTestData = tempTestData.hex()
            if tempTestData == data[self.inputs[i]['paramRef'][0]]:
                return self.__genNext(self.outputs[i-1])
        return self.__genNext(self.outputs[0])

class SerialNode(FileNode):
    def _run(self,data,testParam,prevNode):
        baudrate = data[self.inputs[1]['paramRef'][0]]
        port = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = SerialFile(Tools.createSeralFile(port,baudrate))
        return [data[self.name+'$1']]

class SleepNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        sleepTime = data[self.inputs[1]['paramRef'][0]]
        time.sleep(sleepTime/1000)

class ModuleBeginNode(BeginNode):
    def _run(self,data,testParam,prevNode):
        # 只需要传递数据
        for i in range(1,len(self.inputs)):
            if len(self.inputs[i]['paramRef']) == 0:
                   continue
            data[self.name+'$'+str(i)] = data[self.inputs[i]['paramRef'][0]]

# 需要和Barrier一样，等待所有前驱完成
class ModuleEndNode(BarrierNode):
    def _post(self,data,testParam,prevNode):
        ret = BarrierNode._post(self,data,testParam,prevNode)
        if len(ret) != 0:
            # 传递数据
            for i in range(1,len(self.inputs)):
                data[self.name+'$'+str(i)] = data[self.inputs[i]['paramRef'][0]]
        return ret

# Module作为一个子图，在这里独立构造内部图，并独立执行
class CommonModuleNode(BaseNode):
    def __init__(self, graph_node):
        super().__init__(graph_node)
        logging.info(graph_node['internalGraph']['nameNodeMap'])
        self.internalGraph = TestGraphFactory.buildGraphFromNameNodeMap(graph_node['internalGraph']['nameNodeMap'],graph_node['internalGraph']['nameCountMap'],graph_node['internalGraph']['graphName'])
        # startName beginName需要重新计算
        for nodeName in self.internalGraph.nodes:
            i = self.internalGraph.nodes[nodeName]
            if isinstance(i,ModuleBeginNode):
                self.internalGraph.startName=i.name
            elif isinstance(i,ModuleEndNode):
                self.internalGraph.endName=i.name
    
    def _run(self, data,testParam, prevNode):
        super()._run(data,testParam, prevNode)
        # 传递输入，直接将CommonModuleNode的依赖传递到ModuleBeginNode.outputs位置
        for inParam in range(1,len(self.inputs)):
            self.internalGraph.global_data[self.internalGraph.startName+'$'+str(inParam)]=data[self.inputs[inParam]['paramRef'][0]]
        logging.info(self.internalGraph.global_data)
        # 执行子图
        internalResult = self.internalGraph.run(testParam,True)
        # 合并日志
        Tools.log(data,internalResult.log,self.name)
        if internalResult.exitState !=ExitStateEnum.SUCCESS.value:
            raise TestModuleError("module exit not success")
        # 传递输出，直接将ModuleEndNode.outputs传递到CommonModuleNode的输出位置
        for outParm in range(1,len(self.outputs)):
            data[self.name+'$'+str(outParm)]=self.internalGraph.global_data[self.internalGraph.endName+'$'+str(outParm)]

class FlowAssertNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        raise TestFlowAssertError(self.name,'Bad Flow Position')

class StructureAssertNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        # 对输入数据进行JSON反序列化并递归判断
        dataObject = json.loads(data[self.inputs[1]['paramRef'][0]])
        exampleObject = json.loads(data[self.inputs[2]['paramRef'][0]])
        if Tools.jsonStructureCompare(dataObject,exampleObject) == False:
            raise TestStructureAssertError(self.name,'json structure not match')

class DataAssertNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        # 对输入数据进行JSON反序列化并递归判断
        dataObject = json.loads(data[self.inputs[1]['paramRef'][0]])
        exampleObject = json.loads(data[self.inputs[2]['paramRef'][0]])
        logging.info('data obj {}'.format(dataObject))
        logging.info('example obj {}'.format(exampleObject))
        if Tools.jsonDataCompare(dataObject,exampleObject) == False:
            raise TestStructureAssertError(self.name,'json data not match')

class PythonNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        # 将输入数据作为python脚本，在新进程中启动
        script = data[self.inputs[1]['paramRef'][0]]
        args = data[self.inputs[2]['paramRef'][0]]
        execArgs = {'__builtins__':{'logging.info':logging.info
                                    ,'list':list
                                    ,'set':set
                                    ,'dict':dict
                                    ,'min':min
                                    ,'max':max
                                    ,'locals':locals
                                    ,'False':False
                                    ,'True':True
                                    ,'abs':abs
                                    ,'bool':bool
                                    ,'bytearray':bytearray
                                    ,'bytes':bytes
                                    ,'float':float
                                    ,'format':format
                                    ,'hash':hash
                                    ,'hex':hex
                                    ,'bin':bin
                                    ,'int':int
                                    ,'isinstance':isinstance
                                    ,'iter':iter
                                    ,'len':len
                                    ,'object':object
                                    ,'pow':pow
                                    ,'range':range
                                    ,'round':round
                                    ,'slice':slice
                                    ,'str':str
                                    ,'sum':sum
                                    ,'tuple':tuple
                                    ,'type':type}}
        exec(script.script, execArgs)
        data[self.name+'$1'] = execArgs['func'](args)

class OpenSSLNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        # 输入数据共两部分，
        algorithm = data[self.inputs[1]['paramRef'][0]]
        inputData = data[self.inputs[2]['paramRef'][0]]
        publicKey = data[self.inputs[3]['paramRef'][0]]
        privateKey = data[self.inputs[4]['paramRef'][0]]
        
        # 示例使用
        public_key_pem = publicKey
        message = bytes.fromhex(inputData)
        signature = bytes.fromhex(privateKey)
        nodeResult = sm2_verify(public_key_pem, message, signature)
        if nodeResult:
            logging.info("Signature is valid.")
        else:
            logging.info("Signature is invalid.")
        data[self.name+'$1'] = nodeResult

class ScreenCaptureNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        data[self.name+'$1'] = pyautogui.screenshot().convert('L')

class OCRNode(BaseNode):
    def __init__(self, graph_node):
        super().__init__(graph_node)    
        self.reader = easyocr.Reader(['ch_sim','en'])    

    def _run(self, data, testParam, prevNode):
        inputImage = numpy.asarray(data[self.inputs[1]['paramRef'][0]])
        data[self.name+'$1'] = self.reader.readtext(inputImage)

class MouseActionNode(BaseNode):
    def _run(self, data, testParam, prevNode):
        return super()._run(data, testParam, prevNode)
        

class NodeFactory:
    nodeLibaries = dict()
    @staticmethod
    def nodeRegister(nodeType:type):
        if not issubclass(nodeType,BaseNode):
            raise RuntimeError("invalid nodeType, must subclass of BaseNode")
        # 同名覆盖
        NodeFactory.nodeLibaries[nodeType.__name__]=nodeType

    @staticmethod
    def createNode(graph_node) -> BaseNode:
        if graph_node['typeName'] in NodeFactory.nodeLibaries:
            return NodeFactory.nodeLibaries[graph_node['typeName']](graph_node=graph_node)
        else:
            logging.info('unsupport node: {},pass'.format(graph_node['typeName']))
            raise TestIncompatibleError(msg='unsupport node: {}'.format(graph_node['typeName']))

NodeFactory.nodeRegister(BeginNode)
NodeFactory.nodeRegister(EndNode)
NodeFactory.nodeRegister(ConstantNode)
NodeFactory.nodeRegister(HttpNode)
NodeFactory.nodeRegister(SendNode)
NodeFactory.nodeRegister(LogNode)
NodeFactory.nodeRegister(ExtractNode)
NodeFactory.nodeRegister(MergeNode)
NodeFactory.nodeRegister(TCPNode)
NodeFactory.nodeRegister(RecvNode)
NodeFactory.nodeRegister(WebSocketNode)
NodeFactory.nodeRegister(IfNode)
NodeFactory.nodeRegister(AddMinusNode)
NodeFactory.nodeRegister(MultiDivNode)
NodeFactory.nodeRegister(BiggerNode)
NodeFactory.nodeRegister(EqualNode)
NodeFactory.nodeRegister(AndNode)
NodeFactory.nodeRegister(OrNode)
NodeFactory.nodeRegister(NotNode)
NodeFactory.nodeRegister(BarrierNode)
NodeFactory.nodeRegister(VariableNode)
NodeFactory.nodeRegister(SwitchNode)
NodeFactory.nodeRegister(SerialNode)
NodeFactory.nodeRegister(SleepNode)
NodeFactory.nodeRegister(ModuleBeginNode)
NodeFactory.nodeRegister(ModuleEndNode)
NodeFactory.nodeRegister(CommonModuleNode)
NodeFactory.nodeRegister(FlowAssertNode)
NodeFactory.nodeRegister(StructureAssertNode)
NodeFactory.nodeRegister(DataAssertNode)
NodeFactory.nodeRegister(PythonNode)
NodeFactory.nodeRegister(OpenSSLNode)
NodeFactory.nodeRegister(OCRNode)
NodeFactory.nodeRegister(ScreenCaptureNode)

class TestParam:
    def __init__(self,testUUID=None,totalTimeout=30000) -> None:
        self.totalTimeout=totalTimeout
        # 标记测试是否可以继续
        self.toRun=True
        self.testUUID=testUUID or uuid.uuid4()

class TestGraph:
    def __init__(self,global_data,nodes,startName,endName,graphName,nameCountMap):
        self.global_data=global_data
        self.nodes=nodes
        self.startName=startName
        self.endName=endName
        self.runQueue = Queue()
        # 上一个调度执行的节点
        self.lastRunNode = None
        # 用于存储的内容
        self.graphName = graphName
        self.nameCountMap = nameCountMap
    
    def run(self,testParam:TestParam,inModule=False,topology:TestTopology=None,timeline:TestTimeline=None):
        try:
            # 传递变量区
            # runQueue内容tuple，分别是节点前驱和后继
            fullName = ''
            if not inModule:
                fullName = topology.nodeNew(None,self.nodes[self.startName].name)
            self.runQueue.put((None,self.nodes[self.startName],fullName))
            a=time.time()
            Tools.log(self.global_data,'begin running')
            self.global_data['$$file'] = []
            while not self.runQueue.empty():
                # TODO：更好的超时检查方案
                # 整体超时退出
                if time.time()-a > testParam.totalTimeout:
                    Tools.log(self.global_data,'graph test timeout')
                    return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.TIMEOUT,testParam.testUUID)
                # 被杀死
                if testParam.toRun == False:
                    Tools.log(self.global_data,'get killed')
                    return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.KILLED,testParam.testUUID)
                
                # 继续执行
                (prevNode, currentNode, currentNodeFullName) = self.runQueue.get()
                # 记录执行节点
                if not inModule:
                    topology.nodeRun(currentNodeName=currentNodeFullName)
                logging.info('{} running'.format(currentNode.name))
                # 调用节点运行
                if not inModule:
                    timeline.markNodeBegin(type(currentNode).__name__,currentNode.name,currentNodeFullName)
                nextNodes, isValid = currentNode.doRun(self.global_data,testParam,prevNode)
                if not inModule:
                    timeline.markNodeEnd(type(currentNode).__name__,currentNode.name,currentNodeFullName)
                logging.info('next: {}, isValid: {}'.format(nextNodes,isValid))
                if isValid:
                    for node in nextNodes:
                        if not inModule:
                            fullName = topology.nodeNew(currentNodeFullName,self.nodes[node].name)
                        self.runQueue.put((currentNode,self.nodes[node],fullName))
                self.lastRunNode = currentNode
                # 标记一轮结束
                if not inModule:
                    topology.nodeNewRound()
            Tools.log(self.global_data,'end running')
            b=time.time()
            Tools.log(self.global_data,'time elapsed :{}'.format(b-a))
            if inModule == False and not isinstance(self.lastRunNode,EndNode):
                raise TestRuntimeError(nodeName = self.lastRunNode.name,msg='Test ended at Non-EndNode')
        except TestAssertError as err:
            Tools.log(self.global_data,'{}'.format(err),err.nodeName)
            return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.ASSERTERROR,testParam.testUUID)
        except TestError as err:
            Tools.log(self.global_data,'{}'.format(err),err.nodeName)
            return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.TESTERROR,testParam.testUUID)
        except Exception as err:
            Tools.log(self.global_data,'{}'.format(err))
            return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.EXCEPTION,testParam.testUUID)
        finally:
            # 关闭所有file
            for file in self.global_data['$$file']:
                file.close()
        return RunResult(b-a,self.global_data['$$log'],ExitStateEnum.SUCCESS,testParam.testUUID)



class TestGraphFactory:
    @staticmethod
    def buildGraph(jsonData):
        obj = json.loads(jsonData)
        return TestGraphFactory.buildGraphFromNameNodeMap(obj['graph']['nameNodeMap'],obj['graph']['nameCountMap'],obj['graph']['graphName'])
    
    @staticmethod
    def buildGraphFromNameNodeMap(nameNodeMap, nameCountMap, graphName):
        nodes = dict()
        global_data = dict()
        startName=''
        endName=''
        for jsonNode in nameNodeMap:
            node = NodeFactory.createNode(graph_node=jsonNode[1])
            nodes[jsonNode[0]]=node
            if isinstance(node,BeginNode):
                startName = node.name
            elif isinstance(node,EndNode):
                endName = node.name
            elif isinstance(node,ConstantNode):
                node.doRun(global_data)
        return TestGraph(global_data=global_data,nodes=nodes,startName=startName,endName=endName,graphName=graphName,nameCountMap=nameCountMap)

class TestPlan:
    def __init__(self,testGraph:TestGraph,testParam:TestParam=None):
        self.graph = testGraph
        # 默认测试参数
        self.testParam = testParam or TestParam()
        # 测试结果
        self.runResult = None
        # 测试报告
        self.timeline = TestTimeline()
        self.topology = TestTopology()
    
    def beginTest(self):
        self.runResult = self.graph.run(self.testParam,topology=self.topology,timeline=self.timeline)
        return self.runResult

class TestPlanFactory:
    @staticmethod
    def buildTestPlan(jsonData):
        return TestPlan(TestGraphFactory.buildGraph(jsonData))
    
    @staticmethod
    def exportTestPlan(testPlan:TestPlan):
        '''
        将testPlan导出为json
        {
            "meta": {
                "version": 1,
                "type": "report"
            },
            "testPlan" : {
                "graph": {
                    "graphName": "",
                    "nameCountMap": [],
                    "nameNodeMap": []
                },
                "testParam":{}
                "runResult":{}
                "timeline":{}
                "topology":{}
            }
        }
        '''
        exportDict = dict(graph=testPlan.graph
                          , testParam=testPlan.testParam
                          , runResult = testPlan.runResult.exitState
                          , timeline =testPlan.timeline
                          , topology = testPlan.topology)
        return json.dumps(exportDict)

class TestExecutor:
    testPool = ThreadPoolExecutor(max_workers=10)
    # uuid -> future
    testFutureMap = dict()
    # uuid -> testPlan
    testPlanMap = dict()

    @staticmethod
    def submitTestTask(testPlan:TestPlan,doneCallBack):
        logging.info("submitTestTask")
        # 保存测试计划
        TestExecutor.testPlanMap[testPlan.testParam.testUUID]=testPlan
        # 保存Future
        # future = TestExecutor.testPool.submit(testPlan.graph.run,testPlan.testParam)
        future = TestExecutor.testPool.submit(testPlan.beginTest)
        future.add_done_callback(doneCallBack)
        TestExecutor.testFutureMap[testPlan.testParam.testUUID] = future

    @staticmethod
    def killTestTask(testPlanUUID:uuid.UUID):
        TestExecutor.testFutureMap[testPlanUUID].cancel()
        TestExecutor.testPlanMap[testPlanUUID].testParam.toRun = False
    
    @staticmethod
    def controlTestTask(sid,testUUID,command):
        logging.info("controlTestTask")
        if command=='kill':
            if testUUID not in TestExecutor.testFutureMap:
                raise RuntimeError("testUUID not exist")
            if TestExecutor.testFutureMap[testUUID].done():
                raise RuntimeError("task already killed")
            TestExecutor.killTestTask(testUUID)
        else:
            return False,'command not support'
        return True,'command ok'