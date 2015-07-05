from PyQt5.QtCore import (
   QAbstractItemModel,
   QModelIndex,
   Qt,
   QVariant
)

from PyQt5.QtWidgets import QApplication, QTreeView

class TreeItem(object):
    def __init__(self, content, parentItem):
        self.content = content
        self.parentItem = parentItem
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return 1

    def data(self, column):
        if self.content != None and column == 0:
           return QVariant(self.content)

        return QVariant()

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

class NodeTree(QAbstractItemModel):
   def __init__(self,parent,data) :
      super(NodeTree,self).__init__(parent)
      self.rootItem = TreeItem(None, None)
      self.parents = {0 : self.rootItem}
      self.setupModelData(self.rootItem, data)

   def setupModelData(self, root, data):
      for el in data:
         if isinstance(el, list):
            item = TreeItem("Node", root)
            self.setupModelData(item, el)
         else:
            item = TreeItem(el, root)
         root.appendChild(item)

   def rowCount(self, parent = QModelIndex()):
      if parent.column() > 0:
         return 0
      if not parent.isValid():
         p_Item = self.rootItem
      else:
         p_Item = parent.internalPointer()
      return p_Item.childCount()

   def columnCount(self, parent = QModelIndex()):
      return 1

   def data(self, index, role):
       if not index.isValid():
           return QVariant()

       item = index.internalPointer()
       if role == Qt.DisplayRole:
           return item.data(index.column())
       if role == Qt.UserRole:
           if item:
               return item.content

       return QVariant()

   def headerData(self, column, orientation, role):
       if (orientation == Qt.Horizontal and
                role == Qt.DisplayRole):
           return QVariant("Content")

       return QVariant()

   def index(self, row, column, parent):
       if not self.hasIndex(row, column, parent):
          return QModelIndex()

       if not parent.isValid():
          parentItem = self.rootItem
       else:
          parentItem = parent.internalPointer()

       childItem = parentItem.child(row)
       if childItem:
          return self.createIndex(row, column, childItem)
       else:
          return QModelIndex()

   def parent(self, index):
       if not index.isValid():
          return QModelIndex()

       childItem = index.internalPointer()
       if not childItem:
          return QModelIndex()

       parentItem = childItem.parent()

       if parentItem == self.rootItem:
          return QModelIndex()

       return self.createIndex(parentItem.row(), 0, parentItem)

if __name__ == "__main__" :
   # http://blog.mathieu-leplatre.info/filesystem-watch-with-pyqt4.html
   import sys

   app = QApplication(sys.argv)
   TreeView  = QTreeView()
   TreeModel = NodeTree(TreeView, [['A',['a',1]],['C','D'],['E','F']])
   TreeView.setModel(TreeModel)
   TreeView.show()
   app.exec_()
