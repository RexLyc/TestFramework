import json
import time
import requests
from queue import Queue
from enum import Enum

class RunResult(dict):
    def __init__(self,timeElapsed,log):
        self.timeElapsed=timeElapsed
        self.log=log
        dict.__init__(self,timeElapsed=timeElapsed,log=log)

class TestRunError(RuntimeError):
    def __init__(self,msg):
        self.msg=msg

class IncompatibleError(RuntimeError):
    def __init__(self,msg):
        self.msg=msg

class BaseNode:
    def __init__(self, graph_node):
        self.name=graph_node['name']
        self.inputs=graph_node['inputs']['params']
        self.outputs=graph_node['outputs']['params']
        self.typeName=graph_node['typeName']
        self.data=graph_node['data']

    def __str__(self):
        return 'Type: {}, Id: {}'.format(self.__class__, self.name)

    def _run(self,data=None):
        next = []
        for nextNode in self.outputs[0]['paramRef']:
            next.append(str(nextNode).partition('$')[0])
        return next

    # 执行运算，并返回下一个运行的节点
    def doRun(self,data):
        return self._run(data)

class Tools:
    @staticmethod
    def getParamType(typeName):
        if typeName == 'VarNameValue' or typeName == 'StringValue':
            return str
        elif typeName == 'IntegerValue':
            return int
        elif typeName == 'FloatValue':
            return float
        elif typeName == 'PythonValue':
            raise IncompatibleError('unsupport paramRuntimeType')
    
    @staticmethod
    def log(global_data,logData,loggerName='Default'):
        print('logging {}'.format(logData))
        if '$$log' not in global_data:
            global_data['$$log'] = ''
        global_data['$$log'] = global_data['$$log'] + '{} - {}: {}\n'.format(time.time(),loggerName,logData)
        

class BeginNode(BaseNode):
    pass


class ConstantNode(BaseNode):
    def _run(self,data):
        for i in range(0,len(self.outputs)):
            type = Tools.getParamType(self.outputs[i]['paramType'])
            print('constant setting' + str(type(self.outputs[i]['paramValue'])))
            data[self.name+'$'+str(i)] = type(self.outputs[i]['paramValue'])

class EndNode(BaseNode):
    def _run(self,data):
        return []

class File:
    def __init__(self,file):
        self.file=file

class HttpFile(File):
    pass

class HttpNode(BaseNode):
    def _run(self,data):
        url = data[self.inputs[1]['paramRef'][0]]
        data[self.name+'$1']=HttpFile(url)
        return super()._run()

class SendNode(BaseNode):
    def _run(self,data):
        file = data[self.inputs[1]['paramRef'][0]]
        dataBody = data[self.inputs[2]['paramRef'][0]]
        timeout = data[self.inputs[3]['paramRef'][0]]
        result = ''
        if isinstance(file,HttpFile):
            result = requests.post(file.file,data=dataBody,timeout=timeout).content
        else:
            raise TestRunError('unsupport SendNode file')
        data[self.name+'$1']=result
        return super()._run()

class LogNode(BaseNode):
    def _run(self,data):
        logData = data[self.inputs[1]['paramRef'][0]]
        Tools.log(data,logData,self.name)
        return super()._run()

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
        else:
            print('unsupport node: {},pass'.format(graph_node['typeName']))
            raise IncompatibleError('unsupport node: {},pass'.format(graph_node['typeName']))

class TestGraph:
    def __init__(self,global_data,nodes,startName,endName):
        self.global_data=global_data
        self.nodes=nodes
        self.startName=startName
        self.endName=endName
        self.runQueue = Queue()
        self.lastRunNode = None
    
    def run(self):
        # 传递变量区
        self.runQueue.put(self.nodes[self.startName])
        a=time.time()
        Tools.log(self.global_data,'begin running')
        while not self.runQueue.empty():
            currentNode = self.runQueue.get()
            print(currentNode.name +' running')
            nextNodes = currentNode.doRun(self.global_data)
            print('next: {}'.format(nextNodes))
            for node in nextNodes:
                self.runQueue.put(self.nodes[node])
            self.lastRunNode = currentNode
        Tools.log(self.global_data,'end running')
        b=time.time()
        Tools.log(self.global_data,'time elapsed :{}'.format(b-a))
        if not isinstance(self.lastRunNode,EndNode):
            Tools.log(self.global_data,'Test ended at Non-EndNode')
            raise TestRunError('Test ended at Non-EndNode')
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