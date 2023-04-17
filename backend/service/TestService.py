from graph.Component import TestPlanFactory,TestExecutor,TestIncompatibleError,TestRuntimeError,TestError,RunResult
from MessageService import *

class TestService:
    @staticmethod
    def getTestResult(jsonQuery):
        pass

    @staticmethod
    def getTestState(jsonQuery):
        pass

    @staticmethod
    def submit(jsonGraph):
        try:
            testPlan = TestPlanFactory.buildTestPlan(jsonData=jsonGraph)
            TestExecutor.submitTestTask(testPlan, )
            return CommonMessage(CommonMessageType.SUBMIT.value,msgData=)
        except TestIncompatibleError as err:
            return CommonResponse(CommonResponseEnum.INCOMPATIBLE.value,RunResult(0,'{}'.format(err)))
        except Exception as err:
            return CommonResponse(CommonResponseEnum.EXCEPTION.value,RunResult(0,'{}'.format(err)))