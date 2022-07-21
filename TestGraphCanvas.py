# 使用pyqtgraph的flowchart进行流程图绘制、保存
import sys
from tkinter.messagebox import showinfo
from types import MethodType
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow,QVBoxLayout,QHBoxLayout,QLabel,QMenu,QAction,QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,QObject,pyqtSignal
import pyqtgraph as pg
from pyqtgraph.flowchart import Flowchart
from pyqtgraph import DataTreeWidget
from TestGraphCanvasNode import BaseMiddleGraphNode, BorderGraphItem,BorderGraphNode
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree


pg.setConfigOptions(background='w')
pg.setConfigOptions(crashWarning=True)
pg.setConfigOptions(exitCleanup=True)



## test subclassing parameters
## This parameter automatically generates two child parameters which are always reciprocals of each other
class ComplexParameter(pTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type'] = 'bool'
        opts['value'] = True
        pTypes.GroupParameter.__init__(self, **opts)
        
        self.addChild({'name': 'A = 1/B', 'type': 'float', 'value': 7, 'suffix': 'Hz', 'siPrefix': True})
        self.addChild({'name': 'B = 1/A', 'type': 'float', 'value': 1/7., 'suffix': 's', 'siPrefix': True})
        self.a = self.param('A = 1/B')
        self.b = self.param('B = 1/A')
        self.a.sigValueChanged.connect(self.aChanged)
        self.b.sigValueChanged.connect(self.bChanged)
        
    def aChanged(self):
        self.b.setValue(1.0 / self.a.value(), blockSignal=self.bChanged)

    def bChanged(self):
        self.a.setValue(1.0 / self.b.value(), blockSignal=self.aChanged)


## test add/remove
## this group includes a menu allowing the user to add new parameters into its child list
class ScalableGroup(pTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type'] = 'group'
        opts['addText'] = "Add"
        opts['addList'] = ['str', 'float', 'int']
        pTypes.GroupParameter.__init__(self, **opts)
    
    def addNew(self, typ):
        val = {
            'str': '',
            'float': 0.0,
            'int': 0
        }[typ]
        self.addChild(dict(name="ScalableParam %d" % (len(self.childs)+1), type=typ, value=val, removable=True, renamable=True))

# 测试图数据封装类
class TestGraph(QObject):
    def __init__(self,parent):
        super().__init__(parent)
        self.clear()
    
    def clear(self):
        self._graph=[]
    
    def addNode(self,node):
        self._graph.append(node)
    
    def flowConnect(self,prevNodeId,nextNodeId):
        # 单后继节点
        # 多后继
        pass

    def flowDisconnect(self,prevNodeId,nextNodeId):
        pass

    def dataConnect(self,prevNodeId,prevDataId,nextNodeId,nextDataId):
        pass

    def dataDisconnect(self,prevNodeId,prevDataId,nextNodeId,nextDataId):
        pass

# 测试图绘制封装类
class TestGraphCanvas(QWidget):
    def __init__(self,parent,graph):
        super().__init__(parent)
        self._graph=graph
        self.setUI()

    def closeEvent(self, a0) -> None:
        self._canvas.clear()
        self._canvas.viewBox.close()
        return super().closeEvent(a0)
    
    def newNode(self,action :QAction):
        print(action.text())

    def setUI(self):
        self.layout=QHBoxLayout(self)
        self._canvas=Flowchart()
        # hide default hover selection widget
        self._canvas.widget().chartWidget.hoverDock.setVisible(False)
        self._canvas.widget().chartWidget.selDock.setVisible(False)
        self.layout.addWidget(self._canvas.widget().chartWidget)
        # remove default input output nodes
        self._canvas.removeNode(self._canvas.inputNode)
        self._canvas.removeNode(self._canvas.outputNode)
        # 动态覆盖pyqtgraph提供的上下文菜单
        # 成员函数的覆盖需要用MethodType进行绑定
        self._contextMenu=QMenu('菜单',self)
        self._contextCOMMenu=QMenu('串口',self._contextMenu)
        self._contextCommonMenu=QMenu('通用',self._contextMenu)
        self._contextCOMActions=[QAction(i,self) for i in ['串口初始化节点','串口测试节点']]
        for i in self._contextCOMActions:
            self._contextCOMMenu.addAction(i)
        self._contextCommonActions=[QAction(i,self) for i in ['单字节提取节点','多字节提取节点','条件跳转节点']]
        for i in self._contextCommonActions:
            self._contextCommonMenu.addAction(i)
        self._contextMenu.addMenu(self._contextCOMMenu)
        self._contextMenu.addMenu(self._contextCommonMenu)
        self._contextMenu.triggered.connect(self.newNode)
        tempContext=self._contextMenu
        self._canvas.viewBox.raiseContextMenu=MethodType(lambda self,ev:tempContext.popup(ev.screenPos().toPoint()),self._canvas.viewBox)
        # 点击节点的信号处理

        self._canvas.widget().chartWidget.scene().selectionChanged.connect(self.selectionChanged)
    
    def draw(self,graph):
        # 把默认的start/end画出来
        self._startNode=BorderGraphNode(name='start')
        self._endNode=BorderGraphNode(name='end')
        self._canvas.addNode(self._startNode,self._startNode.name(),[-150,0])
        self._canvas.addNode(self._endNode,self._endNode.name(),[0,0])
        # 画其他节点
        pass

    def selectionChanged(self):
        items = self._canvas.widget().chartWidget.scene().selectedItems()
        self.canvasSelectionChanged.emit(items)
    
    canvasSelectionChanged = pyqtSignal(object)


# 测试图树结构封装类
class TestGraphPropertyPanel(QWidget):
    def __init__(self,parent,graph):
        super().__init__(parent)
        self._graph=graph
        self.setUI()
    
    def setUI(self):
        self.layout=QVBoxLayout(self)
        # 不能设置parent为self，会被视为意图替换layout而被禁止
        self._toolButtonLayout=QVBoxLayout()
        self._parameterTreeLayout=QHBoxLayout()
        self._runGraphButton=QPushButton("运行测试",self)
        self._debugGraphButton=QPushButton("调试测试",self)
        self._toolButtonLayout.addWidget(self._runGraphButton)
        self._toolButtonLayout.addWidget(self._debugGraphButton)
        self._parameterTree=ParameterTree(self)
        self._parameterTreeLayout.addWidget(self._parameterTree)
        self.layout.addItem(self._parameterTreeLayout)
        self.layout.addItem(self._toolButtonLayout)
    
    def onSelectionChanged(self,items):
        if len(items)>1:
            print('should only select one item,use items[0]')
        elif len(items)==0:
            self.clear()
            return
        item=items[0]
        self.showNode(item)

    def clear(self):
        self._parameterTree.clear()
    
    def showNode(self,item):
        # from grphicItem to node
        nodeName=item.node.name()
        
        params = [
            {'name': 'Save/Restore functionality', 'type': 'group', 'children': [
                {'name': 'Save State', 'type': 'action'},
                {'name': 'Restore State', 'type': 'action', 'children': [
                    {'name': 'Add missing items', 'type': 'bool', 'value': True},
                    {'name': 'Remove extra items', 'type': 'bool', 'value': True},
                ]},
            ]},
            {'name': 'Custom context menu', 'type': 'group', 'children': [
                {'name': 'List contextMenu', 'type': 'float', 'value': 0, 'context': [
                    'menu1',
                    'menu2'
                ]},
                {'name': 'Dict contextMenu', 'type': 'float', 'value': 0, 'context': {
                    'changeName': 'Title',
                    'internal': 'What the user sees',
                }},
            ]},
            ComplexParameter(name='Custom parameter group (reciprocal values)'),
            ScalableGroup(name="Expandable Parameter Group", tip='Click to add children', children=[
                {'name': 'ScalableParam 1', 'type': 'str', 'value': "default param 1"},
                {'name': 'ScalableParam 2', 'type': 'str', 'value': "default param 2"},
            ]),
        ]

        ## Create tree of Parameter objects
        p = Parameter.create(name='params', type='group', children=params)
        self._parameterTree.setParameters(p,showTop=False)
        

# 测试图整体窗口封装类
class TestGraphicsView(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._graphData=TestGraph(self)
        self.setUI()
    
    def setUI(self):
        self.layout=QHBoxLayout(self)
        self._graphCanvas=TestGraphCanvas(self,self._graphData)
        self._propertyPanel=TestGraphPropertyPanel(self,self._graphData)
        self.layout.addWidget(self._graphCanvas,120)
        self.layout.addWidget(self._propertyPanel,40)
        self._graphCanvas.draw(self._graphCanvas)
        # 连接图和属性列表
        self._graphCanvas.canvasSelectionChanged.connect(self._propertyPanel.onSelectionChanged)
    

class GraphMainWindow(QMainWindow):
    def __init__(self):
        super(GraphMainWindow, self).__init__()
        self._testGraphView=TestGraphicsView(self)
        self.setUI()

    def newFile(self,checked):
        self.setCentralWidget(self._testGraphView)

    def openFile(self,checked):
        pass

    def setUI(self):                
        # StatusBar
        self._statusLabel=QLabel()
        self._statusLabel.setText("欢迎使用AFCLAB通用测试框架")
        self.statusBar().addWidget(self._statusLabel)
        
        # MenuBar
        self._fileMenu=self.menuBar().addMenu('文件')
        self._newFileAction=QAction('新建',self)
        self._newFileAction.triggered.connect(self.newFile)
        self._newFileAction.setShortcut("Ctrl+N")
        self._fileMenu.addAction(self._newFileAction)
        self.newFile(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./afclab.png"))
    main = GraphMainWindow()
    main.setWindowTitle("AFCLAB通用测试框架")
    main.show()
    main.setWindowState(Qt.WindowMaximized)
    app.exit(app.exec_())