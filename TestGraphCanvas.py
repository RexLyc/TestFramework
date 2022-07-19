# 使用pyqtgraph的flowchart进行流程图绘制、保存

import sys
from types import MethodType

from PyQt5.QtWidgets import QApplication, QGraphicsView, QWidget, QMainWindow,QVBoxLayout,QHBoxLayout,QLabel,QMenu,QAction,QGraphicsScene,QShortcut
from PyQt5.QtWidgets import QGraphicsItem,QGraphicsItemGroup,QStyle
from PyQt5.QtGui import QIcon,QColor,QKeySequence,QPen,QPainter,QStyleHints,QRadialGradient,QBrush
from PyQt5.QtCore import Qt,QLine,QObject,QRectF

import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QGridLayout, QGroupBox, QWidget,QPushButton,QListWidget,QStyleOptionGraphicsItem
from pyqtgraph.flowchart import Flowchart,FlowchartGraphicsView,Node
import math
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
    

# 测试图绘制封装类
class TestGraphCanvas(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.setUI()

    def closeEvent(self, a0) -> None:
        self._canvas.clear() 
        self._canvas.viewBox.close()
        return super().closeEvent(a0)
    
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
        print(self._canvas.viewBox.getContextMenus)
        # 动态覆盖pyqtgraph提供的上下文菜单
        # 成员函数的覆盖需要用MethodType进行绑定
        self._canvas.viewBox.getMenu=MethodType(lambda self,ev:QMenu(),self._canvas.viewBox)
    
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
        self._newFileShortcut=QShortcut
        self._newFileAction.triggered.connect(self.newFile)
        self._newFileAction.setShortcut("Ctrl+N")
        self._fileMenu.addAction(self._newFileAction)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./afclab.png"))
    main = GraphMainWindow()
    main.setWindowTitle("AFCLAB通用测试框架")
    main.show()
    main.setWindowState(Qt.WindowMaximized)
    app.exit(app.exec_())