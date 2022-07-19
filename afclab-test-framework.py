from stat import filemode
import sys
from tempfile import tempdir

from PyQt5.QtWidgets import QApplication, QGraphicsView, QWidget, QMainWindow,QVBoxLayout,QHBoxLayout,QLabel,QMenu,QAction,QGraphicsScene,QShortcut
from PyQt5.QtWidgets import QGraphicsItem,QGraphicsItemGroup,QStyle
from PyQt5.QtGui import QIcon,QColor,QKeySequence,QPen,QPainter,QStyleHints,QRadialGradient,QBrush
from PyQt5.QtCore import Qt,QLine,QObject,QRectF

import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QGridLayout, QGroupBox, QWidget,QPushButton,QListWidget,QStyleOptionGraphicsItem
from pyqtgraph.flowchart import Flowchart
import math

from TestGraphCanvas import *

pg.setConfigOptions(background='w')
pg.setConfigOptions(crashWarning=True)
pg.setConfigOptions(exitCleanup=True)

# 全局信号
class GlobalSignal(QObject):
    pass

class TestGraphModel(QObject):
    pass

# controller of MVC
class TestGraphController(QObject):
    def __init__(self,model):
        super(TestGraphController,self).__init__()
        self._model=model
        self._view=TestGraphicsView()
    
    def getView(self):
        return self._view

    def setNode(self):
        pass

class GraphPropsListWidget(QListWidget):
    def __init__(self):
        super(GraphPropsListWidget,self).__init__()
        self.setUI()
    
    def setUI(self):
        pass

class PropertyPanel(QWidget):
    def __init__(self):
        super(PropertyPanel,self).__init__()
        self.setUI()
    
    def setUI(self):
        self.layout=QVBoxLayout(self)
        self._controlLayout=QHBoxLayout(self)
        self._runPushButton=QPushButton(self)
        self._runPushButton.setText("执行测试")
        self._controlLayout.addWidget(self._runPushButton)
        self._globalLayout=QVBoxLayout(self)
        self._globalPropsList=GraphPropsListWidget()
        self._globalLayout.addWidget(self._globalPropsList)
        self._nodeLayout=QVBoxLayout(self)
        self._nodePropsList=GraphPropsListWidget()
        self._nodeLayout.addWidget(self._nodePropsList)
        self.layout.addLayout(self._controlLayout,10)
        self.layout.addLayout(self._globalLayout,50)
        self.layout.addLayout(self._nodeLayout,100)

class GridGraphScene(QGraphicsScene):
    def __init__(self,parent=None):
        super().__init__(parent)

        # 一些关于网格背景的设置
        self.grid_size = 20  # 一块网格的大小 （正方形的）
        self.grid_squares = 5  # 网格中正方形的区域个数
		
		# 一些颜色
        self._color_background = QColor('#ffffff')
        self._color_light = QColor('#eeeeee')
        self._color_dark = QColor('#aaaaaa')
		# 一些画笔
        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)
		
		# 设置画背景的画笔
        self.setBackgroundBrush(self._color_background)
        self.setSceneRect(0, 0, 500, 500)
	
	# override
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
		
		# 获取背景矩形的上下左右的长度，分别向上或向下取整数
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))
		
		# 从左边和上边开始
        first_left = left - (left % self.grid_size)  # 减去余数，保证可以被网格大小整除
        first_top = top - (top % self.grid_size)
		
		# 分别收集明、暗线
        lines_light, lines_dark = [], []
        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))
		
        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))
		
		# 最后把收集的明、暗线分别画出来
        painter.setPen(self._pen_light)
        if lines_light:
            painter.drawLines(*lines_light)

        painter.setPen(self._pen_dark)
        if lines_dark:
            painter.drawLines(*lines_dark)


class TestGraphRoundRect(QGraphicsItem):
    def __init__(self,x,y,width,height,round):
        super().__init__()
        self._x=x
        self._y=y
        self._width=width
        self._height=height
        self._round=round
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        

    def paint(self,painter,option,widget):
        # print(option.state&QStyle.State_Selected)
        print(int(QStyle.State_Selected))
        print(int(option.state))
        if(int(option.state) or QStyle.State_Selected):
            print("select")
            tmpRect=QRectF(self._x-5,self._y-5,self._width+10,self._height+10)
            radialGradient=QRadialGradient(tmpRect.center(),tmpRect.width()/2)
            radialGradient.setColorAt(0.0,QColor(0,0,0,1.0))
            radialGradient.setColorAt(1.0,QColor(255,255,255,1.0))
            brush = QBrush(radialGradient)
            save=painter.brush()
            painter.setBrush(brush)
            painter.drawRect(tmpRect)
            painter.setBrush(save)
        painter.drawRoundedRect(self._x,self._y,self._width,self._height,self._round,self._round)
        

    def boundingRect(self) -> QRectF:
        return QRectF(self._x,self._y,self._width,self._height)

class TestGraphNode(QGraphicsItemGroup):
    def __init__(self,x,y):
        super().__init__()
        self._x=x
        self._y=y
        self._border=TestGraphRoundRect(x,y,50,50,20)
        self.addToGroup(self._border)

class TestGraphicsView(QWidget):
    def __init__(self):
        super(TestGraphicsView, self).__init__()
        self._nodeMap=dict()
        self._nodeMap['start']=TestGraphNode(0,0)
        self._nodeMap['end']=TestGraphNode(100,100)
        self.setUI()
    
    def setUI(self):
        self.scene=GridGraphScene(self)
        # self.scene=QGraphicsScene(self)
        self.view=QGraphicsView(self)
        # 设置渲染属性
        self.view.setRenderHints(QPainter.Antialiasing |               # 抗锯齿
                            QPainter.HighQualityAntialiasing |         # 高品质抗锯齿
                            QPainter.TextAntialiasing |                # 文字抗锯齿
                            QPainter.SmoothPixmapTransform |           # 使图元变换更加平滑
                            QPainter.LosslessImageRendering)           # 不失真的图片渲染
        # 视窗更新模式
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # 设置水平和竖直方向的滚动条不显示
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setTransformationAnchor(self.view.AnchorUnderMouse)
        self.view.setScene(self.scene)
        self.view.setDragMode(self.view.RubberBandDrag)
        self.view.setAcceptDrops(True)
        # 垂直布局
        self.layout=QHBoxLayout(self)
        self.layout.addWidget(self.view,100)
        self._propsPanel=PropertyPanel()
        self.layout.addWidget(self._propsPanel,50)
        
        # 添加绘制内容
        for i in self._nodeMap.values():
            self.scene.addItem(i)
            


class DemoUI(QMainWindow):
    def __init__(self):
        super(DemoUI, self).__init__()
        self._currentGraph=None
        self._testGraphController=TestGraphController(self._currentGraph)
        self.setUI()

    def newFile(self,checked):
        self.setCentralWidget(self._testGraphController.getView())

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
    main = DemoUI()
    main.setWindowTitle("AFCLAB通用测试框架")
    main.show()
    main.setWindowState(Qt.WindowMaximized)
    app.exit(app.exec_())