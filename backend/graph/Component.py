import json
import time
import requests

class RunResult(dict):
    def __init__(self,isSuccess,timeElapsed,log):
        self.isSuccess=isSuccess
        self.timeElapsed=timeElapsed
        self.log=log
        dict.__init__(self,isSuccess=isSuccess,timeElapsed=timeElapsed,log=log)

class TestRunError(RuntimeError):
    def __init__(self,msg):
        self.msg=msg

class BaseNode:
    def __init__(self, graph_node):
        self.name=graph_node['name']
        self.inputs=graph_node['inputs']
        self.outputs=graph_node['outputs']
        self.typeName=graph_node['typeName']
        self.data=graph_node['data']

    def __str__(self):
        return 'Type: {}, Id: {}'.format(self.__class__, self.name)

    def _run(self,data=None):
        return str(self.outputs['params'][0]['paramRef'][0]).partition('$')[0]

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
            raise TestRunError('unsupport paramRuntimeType')
    
    @staticmethod
    def log(global_data,loggerName,logData):
        print('logging {}'.format(logData))
        if '$$log' not in global_data:
            global_data['$$log'] = ''
        global_data['$$log'] = global_data['$$log'] + '{} - {}: {}\r\n'.format(time.time(),loggerName,logData)
        

class BeginNode(BaseNode):
    pass


class ConstantNode(BaseNode):
    def _run(self,data):
        for i in range(0,len(self.outputs['params'])):
            type = Tools.getParamType(self.outputs['params'][i]['paramType'])
            print('constant setting' + str(type(self.outputs['params'][i]['paramValue'])))
            data[self.name+'$'+str(i)] = type(self.outputs['params'][i]['paramValue'])

class EndNode(BaseNode):
    pass

class File:
    def __init__(self,file):
        self.file=file

class HttpFile(File):
    pass

class HttpNode(BaseNode):
    def _run(self,data):
        url = data[self.inputs['params'][1]['paramRef'][0]]
        data[self.name+'$1']=HttpFile(url)
        return super()._run()

class SendNode(BaseNode):
    def _run(self,data):
        file = data[self.inputs['params'][1]['paramRef'][0]]
        dataBody = data[self.inputs['params'][2]['paramRef'][0]]
        timeout = data[self.inputs['params'][3]['paramRef'][0]]
        result = ''
        if isinstance(file,HttpFile):
            result = requests.post(file.file,data=dataBody,timeout=timeout).content
        else:
            raise TestRunError('unsupport SendNode file')
        data[self.name+'$1']=result
        return super()._run()

class LogNode(BaseNode):
    def _run(self,data):
        logData = data[self.inputs['params'][1]['paramRef'][0]]
        Tools.log(data,self.name,logData)
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
            raise(RuntimeError('unsupport node: {},pass'.format(graph_node['typeName'])))

class TestGraph:
    def __init__(self,global_data,nodes,startName,endName):
        self.global_data=global_data
        self.nodes=nodes
        self.startName=startName
        self.endName=endName
    
    def run(self):
        # 传递变量区
        currentNode = self.nodes[self.startName]
        isSuccess=False
        a=time.time()
        try:
            Tools.log(self.global_data,'Default','begin running')
            while isinstance(currentNode,EndNode) != True:
                print(currentNode.name +' running')
                name = currentNode.doRun(self.global_data)
                print('next:{}'.format(name))
                currentNode = self.nodes[name]
            isSuccess=True
            Tools.log(self.global_data,'Default','end running')
        except RuntimeError as err:
            print(err)
        except Exception as err:
            print('fatal error: {}'.format(err))
        b=time.time()
        print('time elapsed :{}'.format(b-a))
        print(self.global_data)
        return RunResult(isSuccess,b-a,self.global_data['$$log'])

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