# 使用pyqtgraph的flowchart进行流程图绘制、保存
import sys
from types import MethodType
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow,QVBoxLayout,QHBoxLayout,QLabel,QMenu,QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,QObject
import pyqtgraph as pg
from pyqtgraph.flowchart import Flowchart
from TestGraphCanvasNode import BaseMiddleGraphNode,BorderGraphNode

pg.setConfigOptions(background='w')
pg.setConfigOptions(crashWarning=True)
pg.setConfigOptions(exitCleanup=True)

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
    def __init__(self,parent):
        super().__init__(parent)
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
    
    def draw(self,graph):
        # 把默认的start/end画出来
        self._startNode=BorderGraphNode(name='start')
        self._endNode=BorderGraphNode(name='end')
        self._canvas.addNode(self._startNode,self._startNode.name(),[-150,0])
        self._canvas.addNode(self._endNode,self._endNode.name(),[0,0])
        # 画其他节点
        pass

# 测试图树结构封装类
class TestGraphPropertyPanel(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.setUI()
    
    def setUI(self):
        self.layout=QVBoxLayout(self)
        

# 测试图整体窗口封装类
class TestGraphicsView(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._graphData=TestGraph(self)
        self.setUI()
    
    def setUI(self):
        self.layout=QHBoxLayout(self)
        self._graphCanvas=TestGraphCanvas(self)
        self.layout.addWidget(self._graphCanvas)
        self.layout.addWidget(QLabel(self))
        self._graphCanvas.draw(self._graphCanvas)
    

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