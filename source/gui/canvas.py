############################################################################
#
#   Copyright (C) 2015
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################


import math

from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QOpenGLVersionProfile
from PyQt5.QtWidgets import QOpenGLWidget


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)

        self.object = 0
        self.object2 = 0

        self.flipFlop = False

        self._isPanning = False
        self._isRotating = False
        self._lastPos = QPoint()
        self.setFocusPolicy(Qt.StrongFocus)

        self.posX = 0.0
        self.posY = 0.0
        self.posZ = -10.0
        self.rotX = 0.0
        self.rotY = 0.0
        self.rotZ = 0.0
        self.scale = 1.0

        self.camLeftX = -0.5
        self.camRightX = 0.5
        self.camBottomY = 0.5
        self.camTopY = -0.5
        self.camNearZ = 4.0
        self.camFarZ = 14.0

        self.colorBackground = QColor.fromHsl(160, 0, 240, 255)
        self.colorNormal = QColor.fromCmykF(0.4, 0.0, 1.0, 0.0, 1.0)
        self.colorSelect = QColor.fromCmykF(0.0, 1.0, 0.9, 0.0, 1.0)
        self.colorNormalDisabled = QColor.fromCmykF(0.4, 0.0, 1.0, 0.0, 0.3)
        self.colorSelectDisabled = QColor.fromCmykF(0.0, 1.0, 0.9, 0.0, 0.3)

    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(400, 400)

    def setXRotation(self, angle):
        self.rotX = self.normalizeAngle(angle)

    def setYRotation(self, angle):
        self.rotY = self.normalizeAngle(angle)

    def setZRotation(self, angle):
        self.rotZ = self.normalizeAngle(angle)

    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self._isPanning = True
            self.setCursor(Qt.OpenHandCursor)
        elif event.key() == Qt.Key_Alt:
            self._isRotating = True
            self.setCursor(Qt.PointingHandCursor)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self._isPanning = False
            self.unsetCursor()
        elif event.key() == Qt.Key_Alt:
            self._isRotating = False
            self.unsetCursor()

    def mousePressEvent(self, event):
        self._lastPos = event.pos()
        if self._isPanning or self._isRotating:
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            if self._isPanning:
                self.setCursor(Qt.OpenHandCursor)
            elif self._isRotating:
                self.setCursor(Qt.PointingHandCursor)

    def mouseMoveEvent(self, event):
        dx = event.x() - self._lastPos.x()
        dy = -event.y() + self._lastPos.y()

        if self._isRotating:
            if event.buttons() == Qt.LeftButton:
                self.setXRotation(self.rotX + 8 * dy)
                self.setYRotation(self.rotY + 8 * dx)
            elif event.buttons() == Qt.RightButton:
                self.setXRotation(self.rotX + 8 * dy)
                self.setZRotation(self.rotZ + 8 * dx)
        elif self._isPanning:
            if event.buttons() == Qt.LeftButton:
                min_side = min(self.frameSize().width(), self.frameSize().height())
                self.posX += dx / min_side
                self.posY -= dy / min_side

        self._lastPos = event.pos()
        self.update()

    def wheelEvent(self, event):
        min_side = min(self.frameSize().width(), self.frameSize().height())
        x = (event.pos().x() - self.frameSize().width() / 2) / min_side
        y = (event.pos().y() - self.frameSize().height() / 2) / min_side
        s = 1.001 ** event.angleDelta().y()

        self.posX = (self.posX - x) * s + x
        self.posY = (self.posY - y) * s + y
        self.scale *= s

        self.update()

    def initializeGL(self):
        version = QOpenGLVersionProfile()
        version.setVersion(2, 0)
        self.gl = self.context().versionFunctions(version)
        self.gl.initializeOpenGLFunctions()

        self.setClearColor(self.colorBackground)

        self.object = self.makeObject(0.1)
        self.object2 = self.makeObject(-0.1)

        self.gl.glShadeModel(self.gl.GL_SMOOTH)
        self.gl.glEnable(self.gl.GL_DEPTH_TEST)
        self.gl.glEnable(self.gl.GL_CULL_FACE)
        self.gl.glEnable(self.gl.GL_LIGHTING)
        self.gl.glEnable(self.gl.GL_LIGHT0)
        self.gl.glEnable(self.gl.GL_MULTISAMPLE)
        self.gl.glEnable(self.gl.GL_BLEND)
        self.gl.glBlendFunc(self.gl.GL_SRC_ALPHA, self.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.gl.glLightfv(self.gl.GL_LIGHT0, self.gl.GL_POSITION, (0.5, 5.0, 7.0, 1.0))

    def paintGL(self):
        # The last transformation you specify takes place first.
        print("flip") if self.flipFlop else print("flop")
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
        self.gl.glLoadIdentity()
        self.gl.glTranslated(self.posX, self.posY, self.posZ)
        self.gl.glScaled(self.scale, self.scale, self.scale)
        self.gl.glRotated(self.rotX / 16.0, 1.0, 0.0, 0.0)
        self.gl.glRotated(self.rotY / 16.0, 0.0, 1.0, 0.0)
        self.gl.glRotated(self.rotZ / 16.0, 0.0, 0.0, 1.0)
        self.setColor(self.colorSelect)
        self.gl.glCallList(self.object)
        self.setColor(self.colorNormal)
        self.gl.glCallList(self.object2)
        self.flipFlop = not self.flipFlop

    def resizeGL(self, width, height):
        side = min(width, height)
        self.gl.glViewport((width - side) // 2, (height - side) // 2, side, side)

        self.gl.glMatrixMode(self.gl.GL_PROJECTION)
        self.gl.glLoadIdentity()
        if width >= height:
            scale_x = width / height
            self.gl.glOrtho(self.camLeftX * scale_x, self.camRightX * scale_x, self.camBottomY, self.camTopY,
                            self.camNearZ, self.camFarZ)
        else:
            scale_y = height / width
            self.gl.glOrtho(self.camLeftX, self.camRightX, self.camBottomY * scale_y, self.camTopY * scale_y,
                            self.camNearZ, self.camFarZ)
        self.gl.glMatrixMode(self.gl.GL_MODELVIEW)

    def makeObject(self, z):
        genList = self.gl.glGenLists(1)
        self.gl.glNewList(genList, self.gl.GL_COMPILE)

        self.gl.glEnable(self.gl.GL_NORMALIZE)
        self.gl.glBegin(self.gl.GL_QUADS)

        x1 = +0.06
        y1 = -0.14
        x2 = +0.14
        y2 = -0.06
        x3 = +0.08
        y3 = +0.00
        x4 = +0.30
        y4 = +0.22

        self.quad(x1, y1, x2, y2, y2, x2, y1, x1, z)
        self.quad(x3, y3, x4, y4, y4, x4, y3, x3, z)

        self.extrude(x1, y1, x2, y2, z)
        self.extrude(x2, y2, y2, x2, z)
        self.extrude(y2, x2, y1, x1, z)
        self.extrude(y1, x1, x1, y1, z)
        self.extrude(x3, y3, x4, y4, z)
        self.extrude(x4, y4, y4, x4, z)
        self.extrude(y4, x4, y3, x3, z)

        NumSectors = 200

        for i in range(NumSectors):
            angle1 = (i * 2 * math.pi) / NumSectors
            x5 = 0.30 * math.sin(angle1)
            y5 = 0.30 * math.cos(angle1)
            x6 = 0.20 * math.sin(angle1)
            y6 = 0.20 * math.cos(angle1)

            angle2 = ((i + 1) * 2 * math.pi) / NumSectors
            x7 = 0.20 * math.sin(angle2)
            y7 = 0.20 * math.cos(angle2)
            x8 = 0.30 * math.sin(angle2)
            y8 = 0.30 * math.cos(angle2)

            self.quad(x5, y5, x6, y6, x7, y7, x8, y8, z)

            self.extrude(x6, y6, x7, y7, z)
            self.extrude(x8, y8, x5, y5, z)

        self.gl.glEnd()
        self.gl.glEndList()

        return genList

    def quad(self, x1, y1, x2, y2, x3, y3, x4, y4, z):
        self.gl.glNormal3d(0.0, 0.0, -1.0)
        self.gl.glVertex3d(x1, y1, -0.05 + z)
        self.gl.glVertex3d(x2, y2, -0.05 + z)
        self.gl.glVertex3d(x3, y3, -0.05 + z)
        self.gl.glVertex3d(x4, y4, -0.05 + z)

        self.gl.glNormal3d(0.0, 0.0, 1.0)
        self.gl.glVertex3d(x4, y4, +0.05 + z)
        self.gl.glVertex3d(x3, y3, +0.05 + z)
        self.gl.glVertex3d(x2, y2, +0.05 + z)
        self.gl.glVertex3d(x1, y1, +0.05 + z)

    def extrude(self, x1, y1, x2, y2, z):
        self.gl.glNormal3d((x1 + x2) / 2.0, (y1 + y2) / 2.0, 0.0)
        self.gl.glVertex3d(x1, y1, +0.05 + z)
        self.gl.glVertex3d(x2, y2, +0.05 + z)
        self.gl.glVertex3d(x2, y2, -0.05 + z)
        self.gl.glVertex3d(x1, y1, -0.05 + z)

    def setClearColor(self, c):
        self.gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        self.gl.glMaterialfv(self.gl.GL_FRONT, self.gl.GL_DIFFUSE,
                             (c.redF(), c.greenF(), c.blueF(), c.alphaF()))
