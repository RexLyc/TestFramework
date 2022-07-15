from cgitb import reset
from msilib.schema import Error
from operator import ne, xor
from platform import node
from struct import unpack
import sys
import glob
from tokenize import Name
from numpy import isin
import serial
import time
import json
import idcard_sam_trans_model as model;

debug_mode=False

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

class RunToolFunc:
    def xorFunc(data):
        # calculate xor
        xorValue=0
        for i in data:
            xorValue^=i
        return xorValue

    def getFunc(name):
        # 将tpu命令打包（添加首尾、校验位、转义字符）
        def pack_tpu(data):
            # 添加异或校验字节
            data.append(RunToolFunc.xorFunc(data))
            # 添加转义字符0x10
            result = []
            for i in data:
                if i==0x10 or i==0x02 or i==0x03:
                    result.append(0x10)
                result.append(i)
            result.append(0x03)
            result.insert(0,0x02)
            return result

        # 将tpu报文解包（去掉首尾、校验位、转义字符）
        def unpack_tpu(data):
            find_10=False
            unpack_data=[]
            for i in data:
                if find_10:
                    unpack_data.append(i)
                    find_10=False
                    continue
                elif i == 0x10:
                    find_10=True
                else:
                    unpack_data.append(i)
            xorValue=unpack_data[-2]
            unpack_data=unpack_data[1:-2]
            checkValue=RunToolFunc.xorFunc(unpack_data)
            if checkValue!=xorValue:
                raise NameError("fatal error! xorValue invalid")
            return unpack_data

        # 打印数据（pre阶段打印输入，post阶段打印输出）
        def log(data):
            str = ''
            for i in data:
                str += '{:02X} '.format(i)
            # print("{:02X}".format(data))
            print('[',str,']')
            return data
        
        def sam_to_tpu(data):
            # 注意位移运算符优先级极低
            sam_length=(data[1]<<8)+data[2]
            if len(data) != sam_length +3:
                raise NameError("fatal error! receive wrong length packet from sam")
            result=[]
            sam_length-=1
            result.extend([0x32,0x54,0x00,0x20,0x22,0x07,0x07,0x14,0x11,0x00])
            # Moto 序
            result.append((sam_length&0xff00)>>8)
            result.append(sam_length&0x00ff)
            result.extend(data[4:])
            total_length=len(result)
            result.insert(0,(total_length&0xff00)>>8)
            result.insert(0,total_length&0x00ff)
            return result

        def tpu_to_sam(data):
            sam_length=(data[12]<<8)+data[13]
            if len(data) != int(sam_length+14):
                raise NameError("fatal error! receive wrong length packet from tpu")
            result=[]
            sam_length+=1
            result.append((sam_length&0xff00)>>8)
            result.append(sam_length&0x00ff)
            result.append(0x00)
            result.extend(data[14:])
            return result
        def bytes_to_list(data):
            if isinstance(data,bytes):
                temp = []
                temp.extend(data) 
                data=temp
            return data
        
        def incr(data):
            return data+1

        if name=='pack_tpu':
            return pack_tpu
        elif name=='unpack_tpu':
            return unpack_tpu
        elif name=='log':
            return log
        elif name=='sam_to_tpu':
            return sam_to_tpu
        elif name=='tpu_to_sam':
            return tpu_to_sam
        elif name=='bytes_to_list':
            return bytes_to_list
        elif name=='incr':
            return incr
        else:
            return None

class Node:
    def __init__(self,data_zone=None,node=None):
        self.data_zone=data_zone
        self.node=node

    def __str__(self):
        return 'Type: {}, Id: {}'.format(self.node['type'],self.node['id'])

    # pre仅支持对in数据预处理，其结果影响全局
    def _preRun(self):
        if self.node is not None and 'preRun' in self.node:
            for i in self.node['preRun']:
                # print('preRun: {}'.format(i))
                self.data_zone[self.node['in']]=RunToolFunc.getFunc(i)(self.data_zone[self.node['in']])

    def _run(self):
        pass

    # post仅支持对out数据后处理，其结果影响全局
    def _postRun(self):
        if self.node is not None and self.data_zone is not None:
            # 默认进行bytes到list的转换
            self.data_zone[self.node['out']]=RunToolFunc.getFunc("bytes_to_list")(self.data_zone[self.node['out']])
            if 'postRun' in self.node:
                for i in self.node['postRun']:
                    # print('postRun: {}'.format(i))
                    self.data_zone[self.node['out']]=RunToolFunc.getFunc(i)(self.data_zone[self.node['out']])

    def doRun(self):
        self._preRun()
        self._run()
        self._postRun()

class StartNode(Node):
    def __init__(self,node):
        super().__init__(node=node)

class EndNode(Node):
    def _run(self):
        print("EndNode, Test Finish!")
class ErrorNode(Node):
    def __init__(self,data_zone):
        self.data_zone=data_zone
        self.node={
            'id':'-'
            ,'type':'error_node'
            ,'next':'end'
        }
    
    def __str__(self):
        return super().__str__() + ", global_data : {}".format(self.data_zone)

class ConditionNode(Node):
    pass
class ConstantContitionNode(ConditionNode):
    def __init__(self,data_zone,node):
        super().__init__(data_zone=data_zone,node=node)
    
    def _run(self):
        # 查看跳转条件
        for (key,value) in self.node['next'].items():
            if self.data_zone[self.node['in']]==key:
                self.data_zone[self.node['out']]=value
                return
        self.data_zone[self.node['out']]='error'

class TestError:
    def noSuchSTX():
        raise NameError("Unknown STX")

    def unfinishedFeature():
        raise NameError("Unfinished feature")

    def wrongBorder():
        raise NameError("wrong border")
    
    def timeoutLimitExceeded():
        raise NameError("timeout limit exceeded")

class ComReadTool:
    # 遵循[begin,end)
    def _readByLength(dev,timeout,begin,end,basic_len,escape):
        t1=time.time()
        result=[]
        dev.timeout=timeout
        # 获取包含长度的范围
        first = dev.read(end)
        if time.time()-t1>timeout:
            TestError.timeoutLimitExceeded()
        # 计算长度
        calculate_len=0
        temp=[]
        for i in first[begin:end]:
            if i !=escape:
                temp.append(i)
        if begin>end: # 反序
            temp.reverse()
        for i in temp:
            calculate_len=(calculate_len<<8)+i
        # 去掉已经读出来的
        remain_len=calculate_len+basic_len
        result.extend(first)
        remain=dev.read(remain_len)
        if time.time()-t1>timeout:
            TestError.timeoutLimitExceeded()
        result.extend(remain)
        return result

    # begin为起始字符，end为终止字符
    def _readByBorder(dev,timeout,begin,end,escape):
        t1=time.time()
        result = []
        dev.timeout=timeout
        first = dev.read(1)
        if time.time()-t1>timeout:
            TestError.timeoutLimitExceeded()
        if first[0] != begin:
            TestError.wrongBorder()
        escapeFlag=False
        result.extend(first)
        while True:
            temp = dev.read(1)
            a=temp[0]
            # print(a)
            if time.time()-t1>timeout:
                TestError.timeoutLimitExceeded()
            result.append(a)
            if escapeFlag !=True: # 未被转义
                if a==end: # 成功结束
                    break
                elif a==escape: # 遇到转义字符
                    escapeFlag=True
            else: # 被转义中
                # 解除转义
                escapeFlag=False
        return result

    # 根据首字节标志区分长度字段所在位置
    def _readSTXMultiLength(dev,timeout,length_map,escape=None):
        t1=time.time()
        result=[]
        dev.timeout=timeout
        first=dev.read(1)
        if time.time()-t1>timeout:
            TestError.timeoutLimitExceeded()
        if first[0] not in length_map:
            TestError.noSuchSTX()
        temp = ComReadTool._readByLength(dev,timeout,length_map[first[0]]['begin'],length_map[first[0]]['end'],length_map[first[0]]['basic_len'],escape)
        result.append(first[0])
        result.extend(temp)
        return result

    def _readDefault(dev,timeout):
        # 等待数据准备完成
        t1 = time.time()
        while dev.inWaiting() == 0:
            time.sleep(0.001)
            if time.time()-t1 > timeout:
                TestError.timeoutLimitExceeded()
        # 保证数据全部取出
        byte_number_1 = 0
        byte_number_2 = 1
        while byte_number_1 != byte_number_2:
            if time.time()-t1 > timeout:
                TestError.timeoutLimitExceeded()
            byte_number_1 = dev.inWaiting()
            time.sleep(0.01)
            byte_number_2 = dev.inWaiting()
        # 一次性读取
        return dev.read_all()

    def read(dev,policy):
        if policy is None:
            policy={'timeout':2.0}
        timeout=policy['timeout']
        if 'type' in policy and policy['type']=='border':
            return ComReadTool._readByBorder(dev,timeout,policy['begin'],policy['end'],policy['escape'])
        elif 'type' in policy and policy['type']=='length':
            return ComReadTool._readByLength(dev,timeout,policy['begin'],policy['end'],policy['basic_len'],policy['escape'])
        elif 'type' in policy and policy['type']=='stx_multi_length':
            return ComReadTool._readSTXMultiLength(dev,timeout,policy['length_map'],policy['escape'])
        else:
            return ComReadTool._readDefault(dev,timeout)


class ComTestNode(Node):
    def __init__(self,data_zone,node):
        super().__init__(data_zone=data_zone,node=node)
    
    def _run(self):
        # 写串口
        self.data_zone[self.node['dev']].write(self.data_zone[self.node['in']])
        # 根据自定义策略读串口
        out_policy=None
        if 'out_policy' in self.node:
            out_policy=self.node['out_policy']
        self.data_zone[self.node['out']]=ComReadTool.read(self.data_zone[self.node['dev']],out_policy)

class SendTpuNode(Node):
    pass

class ComInitNode(Node):
    def __init__(self,data_zone,node):
        super().__init__(data_zone=data_zone,node=node)
    
    def _run(self):
        self.data_zone[self.node['out']]=serial.Serial(port=self.node['in']['port'],parity=self.node['in']['parity'],baudrate=self.node['in']['baudrate'])

# 功能被ByteExtract代替
# class TpuStatusExtract(Node):
#     def __init__(self,data_zone,node):
#         self.data_zone=data_zone
#         self.node=node
    
#     def run(self):
#         # 状态在报文第8个字节(从0开始数)
#         self.data_zone[self.node['out']]='{:02X}'.format(self.data_zone[self.node['in']][8])

# 获取指定位置的字节
class ByteExtract(Node):
    def __init__(self,data_zone,node):
        super().__init__(data_zone=data_zone,node=node)
    
    def _run(self):
        self.data_zone[self.node['out']]='{:02X}'.format(self.data_zone[self.node['in']][self.node['offset']])

class InfoNode(Node):
    def __init__(self,data_zone,node):
        super().__init__(data_zone=data_zone,node=node)
    
    def _run(self):
        print("round : {}".format(self.data_zone[self.node['in']]))
        self.data_zone[self.node['out']]=self.data_zone[self.node['in']]

class NodeFactory:
    def createNode(graph_node,global_data):
        if graph_node['type']=='init_com':
            return ComInitNode(data_zone=global_data,node=graph_node)
        elif graph_node['type']=='com_node':
            return ComTestNode(data_zone=global_data,node=graph_node)
        elif graph_node['type']=='constant' or graph_node['type']=='variable':
            # 常量直接记录，不必建节点
            global_data[graph_node['id']]=graph_node['data']
        elif graph_node['type']=='start':
            return StartNode(node=graph_node)
        # elif graph_node['type']=='tpu_status_extract':
        #     return TpuStatusExtract(data_zone=global_data,node=graph_node)
        elif graph_node['type']=='info_node':
            return InfoNode(data_zone=global_data,node=graph_node)
        elif graph_node['type']=='end':
            return EndNode()
        elif graph_node['type']=='const_condition_node':
            return ConstantContitionNode(data_zone=global_data,node=graph_node)
        elif graph_node['type']=='byte_extract':
            return ByteExtract(data_zone=global_data,node=graph_node)
        else:
            print('unsupport node,pass',graph_node)

def run_test_graph(test_graph):
    # 全局数据存储
    global_data=dict()
    # 运行节点
    nodes=dict()
    # 建图
    for i in test_graph:
        node = NodeFactory.createNode(i,global_data)
        # 并非所有节点都需要运行
        if isinstance(node,Node):
            if debug_mode:
                print("node: ",i)
            nodes[i['id']]=node
            if i['prev']=='start':
                if 'start' in nodes:
                    assert("duplicate start node, exit!")
                nodes['start']=StartNode({
                    'id':'start'
                    ,'type':'start'
                    ,'next':i['id']
                })
    # 其他边界节点
    nodes['error']=ErrorNode(data_zone=global_data)
    nodes['end']=EndNode()
    currentNode = nodes['start']
    while isinstance(currentNode,EndNode) != True:
        if debug_mode:
            print('running node',currentNode)
        currentNode.doRun()
        if isinstance(currentNode,ConditionNode):
            currentNode=nodes[global_data[currentNode.node['out']]]
        else:
            currentNode=nodes[currentNode.node['next']]
    currentNode.doRun()
    print('finish global_data: {}'.format(global_data))

if __name__ == '__main__':
    # print(model.graph)
    a=time.time()
    run_test_graph(model.graph)
    b=time.time()
    print('time elapsed :{}'.format(b-a))
