# -*- coding: utf-8 -*-
"""
MyTreeView class is a subclass of QT QTreeView class.
Subclass is done in order to:
- implement a simple (ie not complex) drag & drop
- get selection events
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose: display tree structure of the .dxf file, select, enable and set export order of the shapes
@author: Xavier Izard
@since:  2012.10.01
@license: GPL
"""

from PyQt4 import QtCore, QtGui



class MyTreeView(QtGui.QTreeView):
    """
    Subclassed QTreeView in order to match our needs: implement a simple (ie not complex) drag & drop, get selection events
    """

    def __init__(self, parent = None):
        """
        Initialization of the MyTreeView class.
        """
        QtGui.QTreeView.__init__(self, parent)

        self.dragged_element = False #No item is currently dragged & dropped
        self.dragged_element_model_index = None
        self.selectionChangedcallback = None
        self.signals_blocked = False #Transmit events between classes

        QtCore.QObject.connect(self, QtCore.SIGNAL("pressed( const QModelIndex )"), self.elementPressed)



    def setSelectionCallback(self, callback):
        """
        Register a callback function called when the selection changes on the TreeView
        options
        @param callback: function with prototype functionName(parent, selected, deselected):
        """
        self.selectionChangedcallback = callback



    def dragEnterEvent(self, event):
        """
        Set flag dragged_element to True (we have started a drag).
        Note: we can't get the dragged index from this function because it is called really late in the drag chain. If the user is too fast in drag & drop, then the event.pos() will return a position that is sensibly different from the original position when the user has started to drag the item. So we only store a flag. We already got the item dragged through the elementPressed() function.
        options
        @param event: the dragEvent (contains position, ...)
        print("\033[32;1mdragEnterEvent {0} at pos({1}), index = {2}\033[m\n".format(event, event.pos(), self.indexAt(event.pos()).parent().internalId()))
        """
        self.dragged_element = True;
        QtGui.QTreeView.dragEnterEvent(self, event)



    def elementPressed(self, element_model_index):
        """
        This slot is called when an element (Shape, ...) is pressed with the mouse. It aims to store the index (QModelIndex) of the element pressed.
        options
        @param element_model_index: QModelIndex of the element pressed
        print("\033[32melementPressed row = {0}\033[m".format(element_model_index.model().itemFromIndex(element_model_index).row()))
        """
        self.dragged_element_model_index = element_model_index #save the index of the clicked element



    def dropEvent(self, event):
        """
        This function is called when the user has released the mouse button in order to drop an element at the mouse pointer place.
        Note: we have totally reimplemented this function because QT default implementation wants to Copy & Delete each dragged item, even when we only use internals move inside the treeView. This is totally unecessary and over-complicated for us because it would imply to implement a QMimeData import and export functions to export our Shapes / Layers / Entities. The code below tries to move the items at the right place when they are dropped ; it uses simple lists permutations (ie no duplicates & deletes).
        options
        @param event: the dropEvent (contains position, ...)
        print("\033[32mdropEvent {0} at pos({1}), index = {2}\033[m\n".format(event, event.pos(), self.indexAt(event.pos()).parent().internalId()))
        """

        if self.dragged_element:
            #print("action proposee = {0}".format(event.proposedAction()))
            event.setDropAction(QtCore.Qt.IgnoreAction)
            event.accept()

            drag_item = self.dragged_element_model_index.model().itemFromIndex(self.dragged_element_model_index)
            drop_model_index = self.indexAt(event.pos())

            if drop_model_index.isValid():
                drop_item = drop_model_index.model().itemFromIndex(drop_model_index)

                if drag_item.parent() == drop_item.parent():
                    items_parent = drag_item.parent()
                    if not items_parent:
                        items_parent = drag_item.model().invisibleRootItem() #parent is 0, so we need to get the root item of the tree as parent

                    drag_row = self.dragged_element_model_index.row() #original row
                    drop_row = drop_model_index.row() #destination row
                    #print("from row {0} to row {1}".format(drag_row, drop_row))

                    item_to_be_moved = items_parent.takeRow(drag_row)
                    if drop_row > drag_row:
                        drop_row -= 1 #we have one less item in the list, so if the item is dragged below it's original position, we must correct it's insert position
                    items_parent.insertRow(drop_row, item_to_be_moved)

                    #print("\033[32;1mACCEPTED!\033[m\n")

                elif drag_item.parent() == drop_item:
                    items_parent = drag_item.parent()
                    if not items_parent:
                        items_parent = drag_item.model().invisibleRootItem() #parent is 0, so we need to get the root item of the tree as parent

                    drag_row = self.dragged_element_model_index.row() #original row
                    drop_row = 0 #destination row is 0 because item is dropped on the parent
                    #print("from row {0} to row {1}".format(drag_row, drop_row))

                    item_to_be_moved = items_parent.takeRow(drag_row)
                    items_parent.insertRow(drop_row, item_to_be_moved)

                    #print("\033[32;1mACCEPTED ON PARENT!\033[m\n")

                elif self.dragged_element_model_index.parent().sibling(self.dragged_element_model_index.parent().row()+1, 0) == drop_model_index:
                    items_parent = drag_item.parent()
                    if not items_parent:
                        items_parent = drag_item.model().invisibleRootItem() #parent is 0, so we need to get the root item of the tree as parent

                    drag_row = self.dragged_element_model_index.row() #original row
                    #print("from row {0} to last row".format(drag_row))

                    item_to_be_moved = items_parent.takeRow(drag_row)
                    items_parent.appendRow(item_to_be_moved)

                    #print("\033[32;1mACCEPTED ON NEXT PARENT!\033[m\n")

                else:
                    None
                    #we are in the wrong branch of the tree ; item can't be pasted here
                    #print("\033[31;1mREFUSED!\033[m\n")

            else:
                #We are below any tree element => insert at end
                items_parent = drag_item.parent()
                if not items_parent:
                    items_parent = drag_item.model().invisibleRootItem() #parent is 0, so we need to get the root item of the tree as parent

                drag_row = self.dragged_element_model_index.row() #original row
                #print("from row {0} to last row".format(drag_row))

                item_to_be_moved = items_parent.takeRow(drag_row)
                items_parent.appendRow(item_to_be_moved)

                #print("\033[32;1mACCEPTED AT END!\033[m\n")


            self.dragged_element = False;
        else:
            event.ignore()



    def blockSignals(self, block):
        """
        Blocks the signals from this class. Subclassed in order to also block selectionChanged "signal" (callback)
        options
        @param block: whether to block signal (True) or not (False)
        """
        self.signals_blocked = block
        QtGui.QTreeView.blockSignals(self, block)



    def selectionChanged(self, selected, deselected):
        """
        Function called by QT when the selection has changed for this treeView. Subclassed in order to call a callback function
        options
        @param selected: list of selected items
        @param deselected: list of deselected items
        print("\033[32;1mselectionChanged selected count = {0} ; deselected count = {1}\033[m".format(selected.count(), deselected.count()))
        """
        QtGui.QTreeView.selectionChanged(self, selected, deselected)

        if self.selectionChangedcallback and not self.signals_blocked:
            self.selectionChangedcallback(self, selected, deselected)



