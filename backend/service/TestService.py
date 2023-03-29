from graph.Component import TestGraphFactory,TestRunError,IncompatibleError,RunResult
from enum import Enum

class CommonResponse(dict):
    def __init__(self,code,data=None):
        self.code=code
        self.data=data
        dict.__init__(self,code=code,data=data)

class CommonResponseEnum(Enum):
    SUCCESS       = 0
    INCOMPATIBLE  = 1
    BUSY          = 2
    EXCEPTION     = 3
    FAILED        = 4

class TestService:
    @staticmethod
    def run(jsonGraph):
        try:
            graph = TestGraphFactory.buildGraph(jsonGraph)
            return CommonResponse(CommonResponseEnum.SUCCESS.value,graph.run())
        except IncompatibleError as err:
            return CommonResponse(CommonResponseEnum.INCOMPATIBLE.value,RunResult(0,'{}'.format(err)))
        except (TestRunError, Exception) as err:
            return CommonResponse(CommonResponseEnum.EXCEPTION.value,RunResult(0,'{}'.format(err)))

    @staticmethod
    def linkTest(jsonGraph):
        return CommonResponse(CommonResponseEnum.SUCCESS.value)