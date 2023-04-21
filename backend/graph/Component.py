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


# ================= 工具 =================
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
        else:
            return None
    
    @staticmethod
    def log(global_data,logData,loggerName='Default'):
        if isinstance(logData,bytes):
            logData = logData.hex(sep=' ',bytes_per_sep=1)
        print('logging {}'.format(logData))
        if '$$log' not in global_data:
            global_data['$$log'] = ''
        global_data['$$log'] = global_data['$$log'] + '{}({}): {}\n'.format(loggerName,time.time(),logData)

    @staticmethod
    def createTcpFile(addr,port):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((addr,port))
        return s
    
    @staticmethod
    async def createWebsocketFile(url):
        try:
            websocket = await websockets.connect(url)
        except ConnectionRefusedError as e:
            print('ws refuse {}'.format(e))
        return websocket

    @staticmethod
    async def recvWebsocket(websocket,timeout):
        try:
            return await asyncio.wait_for(websocket.recv(),timeout)
        except asyncio.TimeoutError as err:
            print('websocket recv timeout: {}'.format(err))

    @staticmethod
    async def sendWebsocket(websocket,dataBody,timeout):
        try:
            return await asyncio.wait_for(websocket.send(dataBody),timeout)
        except asyncio.TimeoutError as err:
            print('websocket send timeout: {}'.format(err))

    @staticmethod
    def createSeralFile(name,baudrate,parity='N',bytesize=8,stopbits=1):
        return serial.Serial(port=name,baudrate=baudrate,parity=parity,stopbits=stopbits,bytesize=bytesize)
    
    @staticmethod
    def strTobytes(string):
        # 将十六进制字符串转为bytes
        return bytes.fromhex(string)

# ================= IO参数 抽象 ================= 
class File:
    def __init__(self,file):
        self.file=file

class HttpFile(File):
    def __init__(self,url,method):
        super().__init__(None)
        self.url=url
        self.method=method

class TcpFile(File):
    pass

class WebsocketFile(File):
    pass

class SerialFile(File):
    pass


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
        return next

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
            print('constant setting: {} {}'.format(temp,type(temp)))
            data[self.name+'$'+str(i)] = runType(self.outputs[i]['paramValue'])

class VariableNode(ConstantNode):
    pass

class EndNode(BaseNode):
    def _post(self,data,testParam,prevNode):
        return []

class HttpNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        url = data[self.inputs[1]['paramRef'][0]]
        method = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1']=HttpFile(url,method)

class SendNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        file = data[self.inputs[1]['paramRef'][0]]
        rawData = data[self.inputs[2]['paramRef'][0]]
        timeout = data[self.inputs[3]['paramRef'][0]]
        result = ''
        dataBody = '{}'.format(rawData).encode()
        if isinstance(file,HttpFile):
            resp = requests.request(method=file.method,url=file.url,data=dataBody,timeout=timeout)
            if not resp.ok:
                raise TestRuntimeError(self.name,'http send failed: {}'.format(resp.content))
            result = resp.content
        elif isinstance(file,TcpFile):
            file.file.settimeout(timeout)
            result = file.file.send(dataBody)
        elif isinstance(file,WebsocketFile):
            result = asyncio.get_event_loop().run_until_complete(Tools.sendWebsocket(file.file,dataBody,timeout))
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
            logData += data[i] +' '
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

class TCPNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        addr = data[self.inputs[1]['paramRef'][0]]
        port = data[self.inputs[2]['paramRef'][0]]
        tcpFile = TcpFile(Tools.createTcpFile(addr,port))
        data[self.name+'$1'] = tcpFile

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
                print('timeout')
        elif isinstance(file,WebsocketFile):
            outputData = asyncio.get_event_loop().run_until_complete(Tools.recvWebsocket(file.file,timeout))
        elif isinstance(file,SerialFile):
            # TODO: 更好的串口数据读出方案（支持各种流式数据读取）
            # 等待数据准备完成
            t1 = time.time()
            print(file.file)
            while file.file.inWaiting() == 0:
                time.sleep(0.001)
                if time.time()-t1 > timeout:
                    print('timeout')
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
            print('serial {}'.format(outputData))
        else:
            raise TestRuntimeError(self.name,'unsupport RecvNode file: {}'.format(file))
        data[self.name+'$1'] = outputData

class WebSocketNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        url = data[self.inputs[1]['paramRef'][0]]
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        outputData = WebsocketFile(asyncio.get_event_loop().run_until_complete(Tools.createWebsocketFile(url)))
        data[self.name+'$1'] = outputData

class IfNode(BaseNode):
    def _post(self,data,testParam,prevNode):
        condition = data[self.inputs[1]['paramRef'][0]]
        print(condition)
        next = []
        if condition==True:
            for nextNode in self.outputs[0]['paramRef']:
                next.append(str(nextNode).partition('$')[0])
        elif condition==False:
            for nextNode in self.outputs[1]['paramRef']:
                next.append(str(nextNode).partition('$')[0])
        else:
            raise TestRuntimeError(self.name,'invalid condition: {}'.format(condition))
        return next

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
        print("?")
        inputCondition = data[self.inputs[1]['paramRef'][0]]
        print("?")
        data[self.name+'$1'] = (not inputCondition)
        print("?")

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
            return []

class SwitchNode(BaseNode):
    def __genNext(self,output):
        next = []
        for nextNode in output['paramRef']:
            next.append(str(nextNode).partition('$')[0])
        return next

    def _post(self,data,testParam,prevNode):
        testData = data[self.inputs[1]['paramRef'][0]]
        for i in range(2,len(self.inputs)):
            print('{} {}'.format(2,len(self.inputs)))
            if testData == data[self.inputs[i]['paramRef'][0]]:
                return self.__genNext(self.outputs[i-1])
        return self.__genNext(self.outputs[0])

class SerialNode(BaseNode):
    def _run(self,data,testParam,prevNode):
        baudrate = data[self.inputs[1]['paramRef'][0]]
        port = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = SerialFile(Tools.createSeralFile(port,baudrate))

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
        print(graph_node['internalGraph']['nameNodeMap'])
        self.internalGraph = TestGraphFactory.buildGraphFromNameNodeMap(graph_node['internalGraph']['nameNodeMap'])
        # startName beginName需要重新计算
        for i in self.internalGraph.nodes:
            if isinstance(i,ModuleBeginNode):
                self.internalGraph.startName=i.name
            elif isinstance(i,ModuleEndNode):
                self.internalGraph.endName=i.name
    
    def _run(self, data,testParam, prevNode):
        super()._run(data,testParam, prevNode)
        # 传递输入，直接将CommonModuleNode的依赖传递到ModuleBeginNode.outputs位置
        for inParam in range(1,len(self.inputs)):
            self.internalGraph.global_data[self.internalGraph.startName+'$'+str(inParam)]=data[self.inputs[inParam]['paramRef'][0]]
        print(self.internalGraph.global_data)
        # 执行子图
        internalResult = self.internalGraph.run(testParam,True)
        # 合并日志
        Tools.log(data,internalResult.log,self.name)
        if internalResult.exitState !=ExitStateEnum.SUCCESS.value:
            raise TestModuleError("module exit not success")
        # 传递输出，直接将ModuleEndNode.outputs传递到CommonModuleNode的输出位置
        for outParm in range(1,len(self.outputs)):
            data[self.name+'$'+str(outParm)]=self.internalGraph.global_data[self.internalGraph.endName+'$'+str(outParm)]
            

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
            print('unsupport node: {},pass'.format(graph_node['typeName']))
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

class TestParam:
    def __init__(self,testUUID=None,totalTimeout=30000) -> None:
        self.totalTimeout=totalTimeout
        # 标记测试是否可以继续
        self.toRun=True
        self.testUUID=testUUID or uuid.uuid4()

class TestGraph:
    def __init__(self,global_data,nodes,startName,endName):
        self.global_data=global_data
        self.nodes=nodes
        self.startName=startName
        self.endName=endName
        self.runQueue = Queue()
        # 上一个调度执行的节点
        self.lastRunNode = None
    
    def run(self,testParam:TestParam,inModule=False):
        try:
            # 传递变量区
            # runQueue内容tuple，分别是节点前驱和后继
            self.runQueue.put((None,self.nodes[self.startName]))
            a=time.time()
            Tools.log(self.global_data,'begin running')
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
                (prevNode,currentNode) = self.runQueue.get()
                print('{} running'.format(currentNode.name))
                nextNodes = currentNode.doRun(self.global_data,testParam,prevNode)
                print('next: {}'.format(nextNodes))
                for node in nextNodes:
                    self.runQueue.put((currentNode,self.nodes[node]))
                self.lastRunNode = currentNode
            
            Tools.log(self.global_data,'end running')
            b=time.time()
            Tools.log(self.global_data,'time elapsed :{}'.format(b-a))
            if inModule == False and not isinstance(self.lastRunNode,EndNode):
                raise TestRuntimeError(nodeName = self.lastRunNode.name,msg='Test ended at Non-EndNode')
        except TestError as err:
            Tools.log(self.global_data,'{}'.format(err),err.nodeName)
            return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.TESTERROR,testParam.testUUID)
        except Exception as err:
            Tools.log(self.global_data,'{}'.format(err))
            return RunResult(time.time()-a,self.global_data['$$log'],ExitStateEnum.EXCEPTION,testParam.testUUID)
        return RunResult(b-a,self.global_data['$$log'],ExitStateEnum.SUCCESS,testParam.testUUID)



class TestGraphFactory:
    @staticmethod
    def buildGraph(jsonData):
        obj = json.loads(jsonData)
        return TestGraphFactory.buildGraphFromNameNodeMap(obj['graph']['nameNodeMap'])
    
    @staticmethod
    def buildGraphFromNameNodeMap(nameNodeMap):
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
        return TestGraph(global_data=global_data,nodes=nodes,startName=startName,endName=endName)

class TestPlan:
    def __init__(self,testGraph:TestGraph,testParam:TestParam=None):
        self.graph = testGraph
        # 默认测试参数
        self.testParam = testParam or TestParam()

class TestPlanFactory:
    @staticmethod
    def buildTestPlan(jsonData):
        return TestPlan(TestGraphFactory.buildGraph(jsonData))

class TestExecutor:
    testPool = ThreadPoolExecutor(max_workers=10)
    # uuid -> future
    testFutureMap = dict()
    # uuid -> testPlan
    testPlanMap = dict()

    @staticmethod
    def submitTestTask(testPlan:TestPlan,doneCallBack):
        print("submitTestTask")
        # 保存测试计划
        TestExecutor.testPlanMap[testPlan.testParam.testUUID]=testPlan
        # 保存Future
        future = TestExecutor.testPool.submit(testPlan.graph.run,testPlan.testParam)
        future.add_done_callback(doneCallBack)
        TestExecutor.testFutureMap[testPlan.testParam.testUUID] = future

    @staticmethod
    def killTestTask(testPlanUUID:uuid.UUID):
        TestExecutor.testFutureMap[testPlanUUID].cancel()
        TestExecutor.testPlanMap[testPlanUUID].testParam.toRun = False
    
    @staticmethod
    def controlTestTask(sid,testUUID,command):
        print("controlTestTask")
        if command=='kill':
            if testUUID not in TestExecutor.testFutureMap:
                raise RuntimeError("testUUID not exist")
            if TestExecutor.testFutureMap[testUUID].done():
                raise RuntimeError("task already killed")
            TestExecutor.killTestTask(testUUID)
        else:
            return False,'command not support'
        return True,'command ok'