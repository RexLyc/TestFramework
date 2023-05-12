# client & server send messages to each other

from queue import Queue
import time
import uuid
from enum import Enum
from flask_socketio import SocketIO, emit
import logging

# 消息类型
class MessageType(Enum):
    #  测试图提交测试
    SUBMIT           = "submit"
    #  心跳
    PING             = "ping"
    #  测试执行结果
    TEST_RESULT      = "test_result"
    #  测试执行状态
    TEST_STATE       = "test_state"
    #  测试控制
    TEST_COMMAND     = "test_command"
    #  测试报告
    TEST_REPORT      = "test_report"

# 消息核心数据
class MessageBody(dict):
    def __init__(self,msgType:MessageType,msgData) -> None:
        # msgData类型和msgType相关
        self.msgType=msgType.value
        self.msgData=msgData
        self.msgTime=time.time()
        dict.__init__(self,msgType=self.msgType,msgData=msgData,msgTime=self.msgTime)

# 消息队列基本消息体
class Message:
    def __init__(self, testPlanUUID:uuid.UUID, messageBody :MessageBody) -> None:
        # 记录消息相关测试计划，消息体，消息时间戳
        self.testPlanUUID = testPlanUUID
        self.messageBody = messageBody

# 按测试计划，分类记录所有消息
class MessageContainer:
    listMap = dict()

    @staticmethod
    def append(message:Message):
        if message.testPlanUUID not in MessageContainer.listMap:
            MessageContainer.listMap[message.testPlanUUID]=[]
        MessageContainer.listMap[message.testPlanUUID].append(message)

    @staticmethod
    def getMessage(testPlanUUID :uuid.UUID, index):
        if testPlanUUID in MessageContainer.listMap:
            return MessageContainer.listMap[testPlanUUID][index]
    
    @staticmethod
    def getMessages(testPlanUUID: uuid.UUID, startIndex):
        if testPlanUUID in MessageContainer.listMap:
            return MessageContainer.listMap[testPlanUUID][startIndex:]
        else:
            return []


# 记录指定消费者的所有订阅测试计划
class GraphOfConsumer:
    def __init__(self, consumerId) -> None:
        # 消费者id
        self.consumerId=consumerId
        # 待消费测试计划名称-消费位置
        self.subTestPlan=dict()
        
    def subscribe(self,testPlanUUID):
        if testPlanUUID not in self.subTestPlan:
            self.subTestPlan[testPlanUUID]=0
    
    def desubscribe(self,testPlanUUID):
        if testPlanUUID in self.subTestPlan:
            self.subTestPlan.pop(testPlanUUID,0)
    
    def consumeAck(self,testPlanUUID):
        if testPlanUUID in self.subTestPlan:
            self.subTestPlan[testPlanUUID] += 1

    def getIndex(self,testPlanUUID):
        if testPlanUUID in self.subTestPlan:
            return self.subTestPlan[testPlanUUID]

# 记录指定测试计划的所有消费者
class ConsumerOfGraph:
    def __init__(self,testPlanUUID) -> None:
        # 测试计划名称
        self.testPlanUUID=testPlanUUID
        # 消费者id-消费位置
        self.consumers=dict()
    
    def subscribe(self,consumerId):
        if consumerId not in self.consumers:
            self.consumers[consumerId]=0
    
    def desubscribe(self,consumerId):
        if consumerId in self.consumers:
            self.consumers.pop(consumerId)
    
    def consumeAck(self,consumerId):
        if consumerId in self.consumers:
            self.consumers[consumerId] += 1

    def getIndex(self,consumerId):
        if consumerId in self.consumers:
            return self.consumers[consumerId]
    
    def getAllIndex(self):
        return self.consumers

# 提供测试消息收集、订阅、取消订阅、发送等功能
class MessageService:
    # 记录所有订阅者
    consumerMap = dict()
    # 记录所有测试计划
    testPlanMap = dict()
    # 网络接口
    socket      = None
    # 命名空间
    namespace   = None

    @staticmethod
    def initSocket(socketio:SocketIO,namespace):
        MessageService.socket=socketio
        MessageService.namespace=namespace

    @staticmethod
    def subscribe(consumerId,testPlanUUID):
        logging.info('consumerId: {} subscribe testPlan: {}'.format(consumerId,testPlanUUID))
        # 指定消费者订阅测试计划
        if consumerId not in MessageService.consumerMap:
            MessageService.consumerMap[consumerId]=GraphOfConsumer(consumerId)
        MessageService.consumerMap[consumerId].subscribe(testPlanUUID)
        if testPlanUUID not in MessageService.testPlanMap:
            MessageService.testPlanMap[testPlanUUID]=ConsumerOfGraph(testPlanUUID)
        MessageService.testPlanMap[testPlanUUID].subscribe(consumerId)
        MessageService.catchUp(testPlanUUID,consumerId)
    
    @staticmethod
    def desubscribe(consumerId,testPlanUUID):
        # 指定消费者取消订阅
        if consumerId in MessageService.consumerMap:
            MessageService.consumerMap[consumerId].desubscribe(testPlanUUID)
        if testPlanUUID in MessageService.testPlanMap:
            MessageService.testPlanMap[testPlanUUID].desubscribe(consumerId)

    @staticmethod
    def appendMessage(testPlanUUID:uuid.UUID,messageBody:MessageBody):
        # 追加消息
        MessageContainer.append(Message(testPlanUUID,messageBody))
        # 通知向所有testPlanUUID的订阅者发送数据
        MessageService.catchUp(testPlanUUID)
    
    @staticmethod
    def consumeAck(testPlanUUID,sid,consumeIndex):
        MessageService.testPlanMap[testPlanUUID].consumeAck(sid)
        MessageService.consumerMap[sid].consumeAck(testPlanUUID)
        logging.info('consumeAck {} {} {}'.format(testPlanUUID,sid,consumeIndex))

    @staticmethod
    def catchUp(testPlanUUID:uuid.UUID,consumerId=None):
        consumerIds = dict()
        if consumerId:
            consumerIds[consumerId]=MessageService.testPlanMap[testPlanUUID].getIndex(consumerId)
        else:
            consumerIds = MessageService.testPlanMap[testPlanUUID].getAllIndex()
        # 推送
        for id in consumerIds:
            logging.info('catch up for consumer: {} testPlan: {}'.format(id,testPlanUUID))
            for msg in MessageContainer.getMessages(testPlanUUID,consumerIds[id]):
                logging.info('send msg : {} {}'.format(msg.messageBody.msgType,msg.messageBody))
                MessageService.socket.emit(msg.messageBody.msgType,msg.messageBody
                                           ,namespace=MessageService.namespace
                                           ,to=id
                                           ,callback=MessageService.consumeAck(testPlanUUID,id,consumerIds[id]))