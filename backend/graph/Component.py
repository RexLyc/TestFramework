import json
import time
import requests
from queue import Queue
from enum import Enum
import socket
import asyncio
import websockets

# ================= 运行结果、错误 ================= 
class RunResult(dict):
    def __init__(self,timeElapsed,log):
        self.timeElapsed=timeElapsed
        self.log=log
        dict.__init__(self,timeElapsed=timeElapsed,log=log)

class TestError(RuntimeError):
    def __init__(self,nodeName='global',msg='error'):
        self.nodeName=nodeName
        self.msg=msg
    
    def __format__(self, __format_spec: str) -> str:
        return 'at {}, {}'.format(self.nodeName,self.msg)

class TestRuntimeError(TestError):
    pass

class TestIncompatibleError(TestError):
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
        print('logging {}'.format(logData))
        if '$$log' not in global_data:
            global_data['$$log'] = ''
        global_data['$$log'] = global_data['$$log'] + '{} - {}: {}\n'.format(time.time(),loggerName,logData)

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

    def _run(self,data,prevNode):
        pass
    
    def _writeBack(self,data):
        for (outputVar,param) in self.writeBackVar.items():
            data[outputVar]=data[param]

    def _post(self,data,prevNode):
        next = []
        for nextNode in self.outputs[0]['paramRef']:
            next.append(str(nextNode).partition('$')[0])
        return next

    # 执行运算，并返回下一个运行的节点
    def doRun(self,data,prevNode=None):
        try:
            self._run(data,prevNode)
            self._writeBack(data)
            return self._post(data,prevNode)
        except TestError as err:
            raise err
        except Exception as err:
            raise TestRuntimeError(self.name,'{}'.format(err))

class BeginNode(BaseNode):
    pass

class ConstantNode(BaseNode):
    def _run(self,data,prevNode):
        for i in range(0,len(self.outputs)):
            runType = Tools.getParamType(self.outputs[i]['paramType'])
            if runType == None:
                raise TestRuntimeError(self.name,'unsupported runType: {}'.format(self.outputs[i]['paramType']))
            elif runType == bool:
                # bool 类型比较特殊, bool("0")为false，需要先转一下
                self.outputs[i]['paramValue']=int(self.outputs[i]['paramValue'])
            print('constant setting: {} {} '.format(self.outputs[i]['paramValue'],runType(self.outputs[i]['paramValue'])))
            data[self.name+'$'+str(i)] = runType(self.outputs[i]['paramValue'])

class VariableNode(ConstantNode):
    pass

class EndNode(BaseNode):
    def _post(self,data,prevNode):
        return []

class HttpNode(BaseNode):
    def _run(self,data,prevNode):
        url = data[self.inputs[1]['paramRef'][0]]
        method = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1']=HttpFile(url,method)

class SendNode(BaseNode):
    def _run(self,data,prevNode):
        file = data[self.inputs[1]['paramRef'][0]]
        dataBody = data[self.inputs[2]['paramRef'][0]]
        timeout = data[self.inputs[3]['paramRef'][0]]
        result = ''
        dataBody = '{}'.format(dataBody).encode()
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
        else:
            raise TestRuntimeError(self.name,'unsupport SendNode file')
        data[self.name+'$1']=result

class LogNode(BaseNode):
    def _run(self,data,prevNode):
        logData = data[self.inputs[1]['paramRef'][0]]
        Tools.log(data,logData,self.name)

class ExtractNode(BaseNode):
    def _run(self,data,prevNode):
        inputData = data[self.inputs[1]['paramRef'][0]]
        outputData = outputData = inputData[data[self.inputs[2]['paramRef'][0]]:data[self.inputs[3]['paramRef'][0]]]
        data[self.name+'$1']=outputData

class MergeNode(BaseNode):
    def _run(self,data,prevNode):
        data_1 = data[self.inputs[1]['paramRef'][0]]
        data_2 = data[self.inputs[2]['paramRef'][0]]
        outputData = data_1 + data_2
        data[self.name+'$1']=outputData

class TCPNode(BaseNode):
    def _run(self,data,prevNode):
        addr = data[self.inputs[1]['paramRef'][0]]
        port = data[self.inputs[2]['paramRef'][0]]
        tcpFile = TcpFile(Tools.createTcpFile(addr,port))
        data[self.name+'$1'] = tcpFile

class RecvNode(BaseNode):
    def _run(self,data,prevNode):
        file = data[self.inputs[1]['paramRef'][0]]
        timeout = data[self.inputs[2]['paramRef'][0]] / 1000.0
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
        else:
            raise TestRuntimeError(self.name,'unsupport RecvNode file: {}'.format(file))
        data[self.name+'$1'] = outputData

class WebSocketNode(BaseNode):
    def _run(self,data,prevNode):
        url = data[self.inputs[1]['paramRef'][0]]
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        outputData = WebsocketFile(asyncio.get_event_loop().run_until_complete(Tools.createWebsocketFile(url)))
        data[self.name+'$1'] = outputData

class IfNode(BaseNode):
    def _post(self,data,prevNode):
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
    def _run(self,data,prevNode):
        result = 0
        for plus in self.inputs[1]['paramRef']:
            result += data[plus]
        for minus in self.inputs[2]['paramRef']:
            result -= data[minus]
        data[self.name+'$1'] = result

class MultiDivNode(BaseNode):
    def _run(self,data,prevNode):
        result = 1
        for mul in self.inputs[1]['paramRef']:
            result *= data[mul]
        for div in self.inputs[2]['paramRef']:
            result /= data[div]
        data[self.name+'$1'] = result

class BiggerNode(BaseNode):
    def _run(self,data,prevNode):
        data_1 = data[self.inputs[1]['paramRef'][0]]
        data_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = data_1 > data_2

class EqualNode(BaseNode):
    def _run(self,data,prevNode):
        data_1 = data[self.inputs[1]['paramRef'][0]]
        data_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = (data_1 == data_2)

class AndNode(BaseNode):
    def _run(self,data,prevNode):
        condition_1 = data[self.inputs[1]['paramRef'][0]]
        condition_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = (condition_1 and condition_2)

class OrNode(BaseNode):
    def _run(self,data,prevNode):
        condition_1 = data[self.inputs[1]['paramRef'][0]]
        condition_2 = data[self.inputs[2]['paramRef'][0]]
        data[self.name+'$1'] = (condition_1 or condition_2)

class NotNode(BaseNode):
    def _run(self,data,prevNode):
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

    def _post(self,data,prevNode):
        if prevNode.name in self.prevNotDone:
            self.prevNotDone.remove(prevNode.name)
        if not self.prevNotDone:
            return super()._post(data,prevNode)
        else:
            return []

class SwitchNode(BaseNode):
    def __genNext(self,output):
        next = []
        for nextNode in output['paramRef']:
            next.append(str(nextNode).partition('$')[0])
        return next

    def _post(self,data,prevNode):
        testData = data[self.inputs[1]['paramRef'][0]]
        for i in range(2,len(self.inputs)):
            print('{} {}'.format(2,len(self.inputs)))
            if testData == data[self.inputs[i]['paramRef'][0]]:
                return self.__genNext(self.outputs[i-1])
        return self.__genNext(self.outputs[0])


class NodeFactory:
    @staticmethod
    def createNode(graph_node) -> BaseNode:
        if graph_node['typeName']==BeginNode.__name__:
            return BeginNode(graph_node=graph_node)
        elif graph_node['typeName']==EndNode.__name__:
            return EndNode(graph_node=graph_node)
        elif graph_node['typeName']==ConstantNode.__name__:
            return ConstantNode(graph_node=graph_node)
        elif graph_node['typeName']==HttpNode.__name__:
            return HttpNode(graph_node=graph_node)
        elif graph_node['typeName']==SendNode.__name__:
            return SendNode(graph_node=graph_node)
        elif graph_node['typeName']==LogNode.__name__:
            return LogNode(graph_node=graph_node)
        elif graph_node['typeName']==ExtractNode.__name__:
            return ExtractNode(graph_node=graph_node)
        elif graph_node['typeName']==MergeNode.__name__:
            return MergeNode(graph_node=graph_node)
        elif graph_node['typeName']==TCPNode.__name__:
            return TCPNode(graph_node=graph_node)
        elif graph_node['typeName']==RecvNode.__name__:
            return RecvNode(graph_node=graph_node)
        elif graph_node['typeName']==WebSocketNode.__name__:
            return WebSocketNode(graph_node=graph_node)
        elif graph_node['typeName']==IfNode.__name__:
            return IfNode(graph_node=graph_node)
        elif graph_node['typeName']==AddMinusNode.__name__:
            return AddMinusNode(graph_node=graph_node)
        elif graph_node['typeName']==MultiDivNode.__name__:
            return MultiDivNode(graph_node=graph_node)
        elif graph_node['typeName']==BiggerNode.__name__:
            return BiggerNode(graph_node=graph_node)
        elif graph_node['typeName']==EqualNode.__name__:
            return EqualNode(graph_node=graph_node)
        elif graph_node['typeName']==AndNode.__name__:
            return AndNode(graph_node=graph_node)
        elif graph_node['typeName']==OrNode.__name__:
            return OrNode(graph_node=graph_node)
        elif graph_node['typeName']==NotNode.__name__:
            return NotNode(graph_node=graph_node)
        elif graph_node['typeName']==BarrierNode.__name__:
            return BarrierNode(graph_node=graph_node)
        elif graph_node['typeName']==VariableNode.__name__:
            return VariableNode(graph_node=graph_node)
        elif graph_node['typeName']==SwitchNode.__name__:
            return SwitchNode(graph_node=graph_node)
        else:
            print('unsupport node: {},pass'.format(graph_node['typeName']))
            raise TestIncompatibleError(msg='unsupport node: {}'.format(graph_node['typeName']))

class TestGraph:
    def __init__(self,global_data,nodes,startName,endName):
        self.global_data=global_data
        self.nodes=nodes
        self.startName=startName
        self.endName=endName
        self.runQueue = Queue()
        # 上一个调度执行的节点
        self.lastRunNode = None
    
    def run(self):
        # 传递变量区
        # runQueue内容tuple，分别是节点前驱和后继
        self.runQueue.put((None,self.nodes[self.startName]))
        a=time.time()
        Tools.log(self.global_data,'begin running')
        while not self.runQueue.empty():
            (prevNode,currentNode) = self.runQueue.get()
            print('{} running'.format(currentNode.name))
            nextNodes = currentNode.doRun(self.global_data,prevNode)
            print('next: {}'.format(nextNodes))
            for node in nextNodes:
                self.runQueue.put((currentNode,self.nodes[node]))
            self.lastRunNode = currentNode
        Tools.log(self.global_data,'end running')
        b=time.time()
        Tools.log(self.global_data,'time elapsed :{}'.format(b-a))
        if not isinstance(self.lastRunNode,EndNode):
            Tools.log(self.global_data,'Test ended at Non-EndNode')
            raise TestRuntimeError(nodeName = self.lastRunNode.name,msg='Test ended at Non-EndNode')
        return RunResult(b-a,self.global_data['$$log'])

class TestGraphFactory:
    @staticmethod
    def buildGraph(jsonData):
        object = json.loads(jsonData)
        nodes = dict()
        global_data = dict()
        startName=''
        endName=''
        for jsonNode in object['graph']['nameNodeMap']:
            node = NodeFactory.createNode(graph_node=jsonNode[1])
            nodes[jsonNode[0]]=node
            if isinstance(node,BeginNode):
                startName = node.name
            elif isinstance(node,EndNode):
                endName = node.name
            elif isinstance(node,ConstantNode):
                node.doRun(global_data)
        return TestGraph(global_data=global_data,nodes=nodes,startName=startName,endName=endName)