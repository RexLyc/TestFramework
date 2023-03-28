from graph import Component

class TestService:
    @staticmethod
    def run(jsonGraph):
        graph = Component.TestGraphFactory.buildGraph(jsonGraph)
        return graph.run()

    @staticmethod
    def linkTest(jsonGraph):
        resp = Component.CommonResponse("",Component.CommonResponseEnum.value)
        try:
            Component.TestGraphFactory.buildGraph(jsonGraph)
        except Component.IncompatibleError as err:
            resp.code=Component.CommonResponseEnum.INCOMPATIBLE.value
            print('found incompatible problems {}'.format(resp.code))
        except Exception as err:
            print('found exception')
            resp.code=Component.CommonResponseEnum.EXCEPTION.value
        finally:
            return resp