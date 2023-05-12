from graph.Component import TestPlanFactory,TestExecutor,TestIncompatibleError,TestRuntimeError,TestError,RunResult,TestParam,TestPlan
from .MessageService import *
import logging

class SubmitResultType(Enum):
    SUCCESS      = 0
    INCOMPATIBLE = 1
    EXCEPTION    = 2

class SubmitResponse(dict):
    def __init__(self,submitResult:SubmitResultType,testUUID:uuid.UUID=None,message=None) -> None:
        self.result=submitResult
        if testUUID == None:
            self.testUUID=''
        else:
            self.testUUID=testUUID.hex
        self.message=message
        dict.__init__(self,result=self.result.value,testUUID=self.testUUID,message=self.message)

class TestReport(dict):
    def __init__(self,timeline,topology) -> None:
        self.timeline = timeline
        self.topology = topology
        dict.__init__(self,timeline=self.timeline,topology=self.topology)

class TestService:
    @staticmethod
    def _task_done(future,testPlan):
        MessageService.appendMessage(testPlan.testParam.testUUID,MessageBody(MessageType.TEST_RESULT,future.result()))
        MessageService.appendMessage(testPlan.testParam.testUUID,MessageBody(MessageType.TEST_REPORT,TestReport(testPlan.timeline,testPlan.topology)))

    @staticmethod
    def getTestResult(testUUID,sid):
        pass

    @staticmethod
    def getTestState(testUUID,sid):
        pass

    @staticmethod
    def setTestCommand(command,sid):
        logging.info('recv command from sid: {} testUUID: {} command: {}'.format(sid,command['testUUID'],command['command']))
        result = False
        message = ""
        try:
            (result,message) = TestExecutor.controlTestTask(sid,uuid.UUID(hex=command['testUUID']),command['command'])
        except Exception or RuntimeError as err:
            logging.info(err)
            message = "{}".format(err)
            logging.info('control failed: ',message)
        return MessageBody(msgType=MessageType.TEST_COMMAND,msgData={"result":result,"message":message})

    @staticmethod
    def submit(jsonGraph,sid):
        try:
            # 创建sid和testPlan的绑定
            testPlan = TestPlanFactory.buildTestPlan(jsonGraph)
            MessageService.subscribe(sid,testPlan.testParam.testUUID)
            TestExecutor.submitTestTask(testPlan, lambda future:TestService._task_done(future,testPlan))
            return MessageBody(msgType=MessageType.SUBMIT,msgData=SubmitResponse(SubmitResultType.SUCCESS,testPlan.testParam.testUUID,'test running...'))
        except TestIncompatibleError as err:
            logging.info('submit TestIncompatibleError {}'.format(err))
            return MessageBody(msgType=MessageType.SUBMIT,msgData=SubmitResponse(SubmitResultType.INCOMPATIBLE,message='{}'.format(err)))
        except Exception as err:
            logging.info('submit Exception {}'.format(err))
            return MessageBody(msgType=MessageType.SUBMIT,msgData=SubmitResponse(SubmitResultType.EXCEPTION,message='{}'.format(err)))