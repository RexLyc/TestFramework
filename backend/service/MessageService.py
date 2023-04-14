# client & server send messages to each other

from queue import Queue
import time

class MessageBody:
    def __init__(self,messageType,messageContent,) -> None:
        pass

# 记录测试消息
class Message:
    def __init__(self, graphName, messageBody :MessageBody, timeStamp=None) -> None:
        self.graphName = graphName
        self.messageBody = messageBody
        self.timeStamp = timeStamp or time.time()

# 记录某个测试图的消息
class MessageList:
    def __init__(self,graphName) -> None:
        self.graphName=graphName
        self.messages=list()
    
    def append(self,message,timeStamp=None):
        self.messages.append(Message(self.graphName,message))
    
    def getMessage(self,index):
        return self.messages[index]

# 静态，记录所有测试图消息
class MessageListContainer:
    listMap = map()

    @staticmethod
    def append(graphName,message,timeStamp=None):
        if graphName not in MessageListContainer.listMap:
            MessageListContainer.listMap[graphName]=MessageList(graphName)
        MessageListContainer.listMap[graphName].append(message,timeStamp)

    @staticmethod
    def getMessage(graphName,index):
        return MessageListContainer.listMap[graphName].getMessage(index)

# 记录指定消费者的所有订阅测试图
class GraphOfConsumer:
    def __init__(self, consumerId) -> None:
        # 消费者id
        self.consumerId=consumerId
        # 待消费测试图名称-消费位置
        self.subGraphs=map()
        
    def subscribe(self,graphName):
        if graphName not in self.subGraphs:
            self.subGraphs.add(graphName,0)

# 记录指定测试图的所有消费者
class ConsumerOfGraph:
    def __init__(self,graphName) -> None:
        # 测试图名称
        self.graphName=graphName
        # 消费者id-消费位置
        self.consumers=map()
    
    def subscribe(self,consumerId):
        if consumerId not in self.consumers:
            self.consumers.add(consumerId,0)

# 提供测试消息收集、订阅、取消订阅、发送等功能
class MessageService:
    consumerMap = map()
    graphMap = map()

    @staticmethod
    def subscribe(consumerId,graphName):
        if consumerId not in MessageService.consumerMap:
            MessageService.consumerMap[consumerId]=GraphOfConsumer(consumerId)
        MessageService.consumerMap[consumerId].subscribe(graphName)
        if graphName not in MessageService.graphMap:
            MessageService.consumerMap[graphName]=ConsumerOfGraph(graphName)
        MessageService.consumerMap[graphName].subscribe(consumerId)
    
    @staticmethod
    def appendMessage(self,graphName,message:MessageBody,timeStamp=None):
        MessageListContainer.append(graphName,message,timeStamp)
        # 向所有订阅者发送数据
        