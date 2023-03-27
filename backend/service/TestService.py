from graph import Component

class TestService:
    @staticmethod
    def run(jsonGraph):
        graph = Component.TestGraphFactory.buildGraph(jsonGraph)
        return graph.run()