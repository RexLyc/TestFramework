from stat import filemode
import sys

from PyQt5.QtWidgets import QApplication, QGraphicsView, QWidget, QMainWindow,QVBoxLayout,QLabel,QMenu,QAction
from PyQt5.QtGui import QIcon,QColor
from PyQt5.QtCore import Qt

import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QGridLayout, QGroupBox, QWidget
from pyqtgraph.flowchart import Flowchart

pg.setConfigOptions(background='w')
pg.setConfigOptions(crashWarning=True)
pg.setConfigOptions(exitCleanup=True)

class TestGraphicsView(QWidget):
    def __init__(self):
        super(TestGraphicsView, self).__init__()
        self.setUI()
    
    def setUI(self):
        # self.setCursor(Qt.CrossCursor)
        self.layout = QGridLayout(self)
        self.flowChartBox = QGroupBox(self)
        self.fc = Flowchart()
        self.flowChartWidget = self.fc.widget().chartWidget
        self.flowChartLayout = QGridLayout(self.flowChartBox)
        self.flowChartLayout.setContentsMargins(0, 0, 0, 0)
        self.flowChartLayout.addWidget(self.flowChartWidget)
        self.layout.addWidget(self.flowChartBox, 0, 0, 1, 1)

    
    def drawNode(self):
        pass
        

class DemoUI(QMainWindow):

    def __init__(self):
        super(DemoUI, self).__init__()
        self.setUI()

    def setUI(self):
        # Graphics View
        self.GraphicsView=TestGraphicsView()
        self.setCentralWidget(self.GraphicsView)
        
        # Property Panel
        
        # StatusBar
        self._statusLabel=QLabel()
        self._statusLabel.setText("hello world")
        self.statusBar().addWidget(self._statusLabel)
        
        # MenuBar
        self._fileMenu=self.menuBar().addMenu('文件')
        self._newFileAction=QAction('新建',self)
        self._newFileAction.triggered.connect(lambda checked:print("New File Triggered"))
        self._fileMenu.addAction(self._newFileAction)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = DemoUI()
    main.setWindowTitle("AFCLAB通用测试框架")
    main.show()
    main.setWindowState(Qt.WindowMaximized)
    app.setWindowIcon(QIcon("./afclab.png"))
    app.exit(app.exec_())