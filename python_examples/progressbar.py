
from PyQt4 import QtCore, QtGui
import time
from PyQt4.QtGui import QApplication
import sys


# http://stackoverflow.com/questions/19442443/busy-indication-with-pyqt-progress-bar
class MyCustomWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MyCustomWidget, self).__init__(parent)
        layout = QtGui.QVBoxLayout(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setRange(0,100)
        button = QtGui.QPushButton("Start", self)
        layout.addWidget(self.progressBar)
        layout.addWidget(button)

        button.clicked.connect(self.onStart)

        self.myLongTask = TaskThread()
        print(self.myLongTask.result)
        self.myLongTask.notifyProgress.connect(self.onProgress)
        self.myLongTask.done.connect(self.finPBar)

    def finPBar(self, object):
        print(object.result)

    def onStart(self):
        self.myLongTask.start()

    def onProgress(self, i):
        self.progressBar.setValue(i)


class TaskThread(QtCore.QThread):
    notifyProgress = QtCore.pyqtSignal(int)
    done = QtCore.pyqtSignal(object)

    def __init__(self):
        super(TaskThread, self).__init__()
        self.result = "No"

    def run(self):
        for i in range(101):
            self.notifyProgress.emit(i)
            time.sleep(0.1)
        self.result = "success"
        self.done.emit(self)


if __name__ == "__main__" :
    app = QApplication(sys.argv)
    tester = MyCustomWidget()
    tester.show()
    sys.exit(app.exec_())
