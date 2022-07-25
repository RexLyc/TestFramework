from pyqtgraph.flowchart import Node
from pyqtgraph import GraphicsObject
from PyQt5 import QtCore,QtGui,QtWidgets
from pyqtgraph import functions as fn
translate = QtCore.QCoreApplication.translate

class GraphBaseNode(GraphicsObject):
    def __init__(self, node):
        #QtWidgets.QGraphicsItem.__init__(self)
        GraphicsObject.__init__(self)
        #QObjectWorkaround.__init__(self)
        
        self.shadow = QtWidgets.QGraphicsDropShadowEffect()
        self.shadow.setOffset(0,0)
        self.shadow.setBlurRadius(20)
        self.setGraphicsEffect(self.shadow)
        
        self.pen = fn.mkPen(200,200,200)
        self.selectPen = fn.mkPen(200,200,200,width=2)
        self.brush = fn.mkBrush(200, 200, 200, 150)
        self.hoverBrush = fn.mkBrush(200, 200, 200, 200)
        self.selectBrush = fn.mkBrush(200, 200, 255, 200)
        self.hovered = False
        
        self.node = node
        flags = self.GraphicsItemFlag.ItemIsMovable | self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemIsFocusable | self.GraphicsItemFlag.ItemSendsGeometryChanges
        #flags =  self.ItemIsFocusable |self.ItemSendsGeometryChanges

        self.setFlags(flags)
        self.bounds = QtCore.QRectF(0, 0, 100, 100)
        self.nameItem = QtWidgets.QGraphicsTextItem(self.node.name(), self)
        self.nameItem.setDefaultTextColor(QtGui.QColor(50, 50, 50))
        self.nameItem.moveBy(self.bounds.width()/2. - self.nameItem.boundingRect().width()/2., 0)
        self.nameItem.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextEditorInteraction)
        self.updateTerminals()
        #self.setZValue(10)

        self.menu = None
        self.buildMenu()
        
        #self.node.sigTerminalRenamed.connect(self.updateActionMenu)
        
    #def setZValue(self, z):
        #for t, item in self.terminals.values():
            #item.setZValue(z+1)
        #GraphicsObject.setZValue(self, z)
        
    def labelChanged(self):
        newName = self.nameItem.toPlainText()
        if newName != self.node.name():
            self.node.rename(newName)
            
        ### re-center the label
        bounds = self.boundingRect()
        self.nameItem.setPos(bounds.width()/2. - self.nameItem.boundingRect().width()/2., 0)

    def setPen(self, *args, **kwargs):
        self.pen = fn.mkPen(*args, **kwargs)
        self.update()
        
    def setBrush(self, brush):
        self.brush = brush
        self.update()
        
        
    def updateTerminals(self):
        self.terminals = {}
        inp = self.node.inputs()
        out = self.node.outputs()
        
        maxNode = max(len(inp), len(out))
        titleOffset = 25
        nodeOffset = 12
        
        # calculate new height
        newHeight = titleOffset+maxNode*nodeOffset
        
        # if current height is not equal to new height, update
        if not self.bounds.height() == newHeight:
            self.bounds.setHeight(newHeight)
            self.update()

        # Populate inputs
        y = titleOffset
        for i, t in inp.items():
            item = t.graphicsItem()
            item.setParentItem(self)
            #item.setZValue(self.zValue()+1)
            item.setAnchor(0, y)
            self.terminals[i] = (t, item)
            y += nodeOffset
        
        # Populate inputs
        y = titleOffset
        for i, t in out.items():
            item = t.graphicsItem()
            item.setParentItem(self)
            item.setZValue(self.zValue())
            item.setAnchor(self.bounds.width(), y)
            self.terminals[i] = (t, item)
            y += nodeOffset
        
        #self.buildMenu()
        
        
    def boundingRect(self):
        return self.bounds.adjusted(-5, -5, 5, 5)
        
    def paint(self, p, *args):
        
        p.setPen(self.pen)
        if self.isSelected():
            p.setPen(self.selectPen)
            p.setBrush(self.selectBrush)
        else:
            p.setPen(self.pen)
            if self.hovered:
                p.setBrush(self.hoverBrush)
            else:
                p.setBrush(self.brush)
        
        # p.drawRect(self.bounds)
        p.drawRoundedRect(self.bounds,5,5)

        
    def mousePressEvent(self, ev):
        ev.ignore()


    def mouseClickEvent(self, ev):
        #print "Node.mouseClickEvent called."
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            #print "    ev.button: left"
            sel = self.isSelected()
            #ret = QtWidgets.QGraphicsItem.mousePressEvent(self, ev)
            self.setSelected(True)
            if not sel and self.isSelected():
                #self.setBrush(QtGui.QBrush(QtGui.QColor(200, 200, 255)))
                #self.emit(QtCore.SIGNAL('selected'))
                #self.scene().selectionChanged.emit() ## for some reason this doesn't seem to be happening automatically
                self.update()
            #return ret
        
        elif ev.button() == QtCore.Qt.MouseButton.RightButton:
            #print "    ev.button: right"
            ev.accept()
            #pos = ev.screenPos()
            self.raiseContextMenu(ev)
            #self.menu.popup(QtCore.QPoint(pos.x(), pos.y()))
            
    def mouseDragEvent(self, ev):
        #print "Node.mouseDrag"
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            self.setPos(self.pos()+self.mapToParent(ev.pos())-self.mapToParent(ev.lastPos()))
        
    def hoverEvent(self, ev):
        if not ev.isExit() and ev.acceptClicks(QtCore.Qt.MouseButton.LeftButton):
            ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton)
            self.hovered = True
        else:
            self.hovered = False
        self.update()
            
    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key.Key_Delete or ev.key() == QtCore.Qt.Key.Key_Backspace:
            ev.accept()
            if not self.node._allowRemove:
                return
            self.node.close()
        else:
            ev.ignore()

    def itemChange(self, change, val):
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            for k, t in self.terminals.items():
                t[1].nodeMoved()
        return GraphicsObject.itemChange(self, change, val)
            

    def getMenu(self):
        return self.menu
    
    def raiseContextMenu(self, ev):
        return
        
    def buildMenu(self):
        self.menu = QtWidgets.QMenu()
        self.menu.setTitle(translate("Context Menu", "Node"))
        a = self.menu.addAction(translate("Context Menu","Add input"), self.addInputFromMenu)
        if not self.node._allowAddInput:
            a.setEnabled(False)
        a = self.menu.addAction(translate("Context Menu", "Add output"), self.addOutputFromMenu)
        if not self.node._allowAddOutput:
            a.setEnabled(False)
        a = self.menu.addAction(translate("Context Menu", "Remove node"), self.node.close)
        if not self.node._allowRemove:
            a.setEnabled(False)
        
    def addInputFromMenu(self):  ## called when add input is clicked in context menu
        self.node.addInput(renamable=True, removable=True, multiable=True)
        
    def addOutputFromMenu(self):  ## called when add output is clicked in context menu
        self.node.addOutput(renamable=True, removable=True, multiable=False)


class BaseNode(Node):
    # 分类(用于右键菜单)
    def getClassify(self):
        return '通用/样例节点'

    def __init__(self,name):
        Node.__init__(self,name)
        Node.addInput(self,'input')
        Node.addOutput(self,'output')
    
    def graphicsItem(self):
        if self._graphicsItem is None:
            self._graphicsItem = BaseNode(self)
        return self._graphicsItem
    
