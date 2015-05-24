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

from math import pi, cos, sin, radians

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QOpenGLVersionProfile
from PyQt5.QtWidgets import QOpenGLWidget

from Core.Point import Point

import Global.Globals as g

class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)

        self.objects = []
        self.orientation = 0
        self.wpZero = 0

        self.isPanning = False
        self.isRotating = False
        self.isMultiSelect = False
        self._lastPos = QPoint()

        self.posX = 0.0
        self.posY = 0.0
        self.posZ = 0.0
        self.rotX = 0.0
        self.rotY = 0.0
        self.rotZ = 0.0
        self.scale = 1.0
        self.scaleCorr = 1.0

        self.camLeftX = -0.5
        self.camRightX = 0.5
        self.camBottomY = 0.5
        self.camTopY = -0.5
        self.camNearZ = -14.0
        self.camFarZ = 14.0

        self.colorBackground = QColor.fromHsl(160, 0, 255, 255)
        self.colorNormal = QColor.fromCmykF(1.0, 0.5, 0.0, 0.0, 1.0)
        self.colorSelect = QColor.fromCmykF(0.0, 1.0, 0.9, 0.0, 1.0)
        self.colorNormalDisabled = QColor.fromCmykF(1.0, 0.5, 0.0, 0.0, 0.25)
        self.colorSelectDisabled = QColor.fromCmykF(0.0, 1.0, 0.9, 0.0, 0.25)

        self.topLeft = Point()
        self.bottomRight = Point()

        self.tol = 0

    def resetAll(self):
        self.gl.glDeleteLists(1, self.orientation)  # the orientation arrows are currently generated last
        self.objects = []
        self.wpZero = 0
        self.orientation = 0

        self.posX = 0.0
        self.posY = 0.0
        self.posZ = 0.0
        self.rotX = 0.0
        self.rotY = 0.0
        self.rotZ = 0.0
        self.scale = 1.0

        self.topLeft = Point()
        self.bottomRight = Point()

        self.update()

    def setXRotation(self, angle):
        self.rotX = self.normalizeAngle(angle)

    def setYRotation(self, angle):
        self.rotY = self.normalizeAngle(angle)

    def setZRotation(self, angle):
        self.rotZ = self.normalizeAngle(angle)

    def normalizeAngle(self, angle):
        return (angle - 180) % -360 + 180

    def mousePressEvent(self, event):
        if self.isPanning or self.isRotating:
            self.setCursor(Qt.ClosedHandCursor)
        else:
            min_side = min(self.frameSize().width(), self.frameSize().height())
            clickedX = (event.pos().x() - self.frameSize().width() / 2) / min_side / self.scale
            clickedY = (event.pos().y() - self.frameSize().height() / 2) / min_side / self.scale
            offsetX, offsetY, offsetZ = -self.posX / self.scale, -self.posY / self.scale, -self.posZ / self.scale

            xyForZ = {}
            tol = 4 * self.scaleCorr / min_side / self.scale
            for shape in self.objects:
                hit = False
                z = shape.axis3_start_mill_depth
                if z not in xyForZ:
                    xyForZ[z] = self.determineSelectedPosition(clickedX, clickedY, z, offsetX, offsetY, offsetZ)
                hit |= shape.isHit(xyForZ[z], tol)

                if not hit:
                    z = shape.axis3_mill_depth
                    if z not in xyForZ:
                        xyForZ[z] = self.determineSelectedPosition(clickedX, clickedY, z, offsetX, offsetY, offsetZ)
                    hit |= shape.isHit(xyForZ[z], tol)

                if self.isMultiSelect and shape.selected:
                    hit = not hit

                if hit != shape.selected:
                    g.window.TreeHandler.updateShapeSelection(shape, hit)

                shape.selected = hit

            self.update()
        self._lastPos = event.pos()

    def determineSelectedPosition(self, clickedX, clickedY, forZ, offsetX, offsetY, offsetZ):
        angleX = -radians(self.rotX)
        angleY = -radians(self.rotY)

        zv = forZ - offsetZ
        clickedZ = ((zv + clickedX * sin(angleY)) / cos(angleY) - clickedY * sin(angleX)) / cos(angleX)
        sx, sy, sz = self.deRotate(clickedX, clickedY, clickedZ)
        return Point(sx + offsetX, - sy - offsetY)  #, sz + offsetZ

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            if self.isPanning:
                self.setCursor(Qt.OpenHandCursor)
            elif self.isRotating:
                self.setCursor(Qt.PointingHandCursor)

    def mouseMoveEvent(self, event):
        dx = event.pos().x() - self._lastPos.x()
        dy = event.pos().y() - self._lastPos.y()

        if self.isRotating:
            if event.buttons() == Qt.LeftButton:
                self.setXRotation(self.rotX - dy / 2)
                self.setYRotation(self.rotY + dx / 2)
            elif event.buttons() == Qt.RightButton:
                self.setXRotation(self.rotX - dy / 2)
                self.setZRotation(self.rotZ + dx / 2)
        elif self.isPanning:
            if event.buttons() == Qt.LeftButton:
                min_side = min(self.frameSize().width(), self.frameSize().height())
                dx, dy, dz = self.deRotate(dx, dy, 0)
                self.posX += dx / min_side
                self.posY += dy / min_side
                self.posZ += dz / min_side

        self._lastPos = event.pos()
        self.update()

    def wheelEvent(self, event):
        min_side = min(self.frameSize().width(), self.frameSize().height())
        x = (event.pos().x() - self.frameSize().width() / 2) / min_side
        y = (event.pos().y() - self.frameSize().height() / 2) / min_side
        s = 1.001 ** event.angleDelta().y()

        x, y, z = self.deRotate(x, y, 0)
        self.posX = (self.posX - x) * s + x
        self.posY = (self.posY - y) * s + y
        self.posZ = (self.posZ - z) * s + z
        self.scale *= s

        self.update()

    def rotate(self, x, y, z):
        angleZ = radians(self.rotZ)
        x, y, z = x*cos(angleZ) - y*sin(angleZ), x*sin(angleZ) + y*cos(angleZ), z
        angleY = radians(self.rotY)
        x, y, z = x*cos(angleY) + z*sin(angleY), y, -x*sin(angleY) + z*cos(angleY)
        angleX = radians(self.rotX)
        return x, y*cos(angleX) - z*sin(angleX), y*sin(angleX) + z*cos(angleX)

    def deRotate(self, x, y, z):
        angleX = -radians(self.rotX)
        x, y, z = x, y*cos(angleX) - z*sin(angleX), y*sin(angleX) + z*cos(angleX)
        angleY = -radians(self.rotY)
        x, y, z = x*cos(angleY) + z*sin(angleY), y, -x*sin(angleY) + z*cos(angleY)
        angleZ = -radians(self.rotZ)
        return x*cos(angleZ) - y*sin(angleZ), x*sin(angleZ) + y*cos(angleZ), z

    def initializeGL(self):
        version = QOpenGLVersionProfile()
        version.setVersion(2, 0)
        self.gl = self.context().versionFunctions(version)
        self.gl.initializeOpenGLFunctions()

        self.setClearColor(self.colorBackground)

        # self.gl.glPolygonMode(self.gl.GL_FRONT_AND_BACK, self.gl.GL_LINE )
        self.gl.glShadeModel(self.gl.GL_SMOOTH)
        self.gl.glEnable(self.gl.GL_DEPTH_TEST)
        self.gl.glEnable(self.gl.GL_CULL_FACE)
        # self.gl.glEnable(self.gl.GL_LIGHTING)
        # self.gl.glEnable(self.gl.GL_LIGHT0)
        self.gl.glEnable(self.gl.GL_MULTISAMPLE)
        self.gl.glEnable(self.gl.GL_BLEND)
        self.gl.glBlendFunc(self.gl.GL_SRC_ALPHA, self.gl.GL_ONE_MINUS_SRC_ALPHA)
        # self.gl.glLightfv(self.gl.GL_LIGHT0, self.gl.GL_POSITION, (0.5, 5.0, 7.0, 1.0))
        self.gl.glEnable(self.gl.GL_NORMALIZE)

    def paintGL(self):
        # The last transformation you specify takes place first.
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
        self.gl.glLoadIdentity()
        self.gl.glRotated(self.rotX, 1.0, 0.0, 0.0)
        self.gl.glRotated(self.rotY, 0.0, 1.0, 0.0)
        self.gl.glRotated(self.rotZ, 0.0, 0.0, 1.0)
        self.gl.glTranslated(self.posX, self.posY, self.posZ)
        self.gl.glScaled(self.scale, self.scale, self.scale)
        for shape in self.objects:
            if shape.disabled:
                if shape.selected:
                    self.setColor(self.colorSelectDisabled)
                else:
                    self.setColor(self.colorNormalDisabled)
            else:
                if shape.selected:
                    self.setColor(self.colorSelect)
                else:
                    self.setColor(self.colorNormal)
            self.gl.glCallList(shape.drawingObject)
        self.gl.glScaled(self.scaleCorr / self.scale, self.scaleCorr / self.scale, self.scaleCorr / self.scale)
        self.gl.glCallList(self.wpZero)
        self.gl.glTranslated(-self.posX / self.scaleCorr, -self.posY / self.scaleCorr, -self.posZ / self.scaleCorr)
        self.gl.glCallList(self.orientation)

    def resizeGL(self, width, height):
        self.gl.glViewport(0, 0, width, height)
        side = min(width, height)
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
        self.scaleCorr = 400 / side
        self.gl.glMatrixMode(self.gl.GL_MODELVIEW)

    def setClearColor(self, c):
        self.gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        self.setColorRGBA(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColorRGBA(self, r, g, b, a):
        # self.gl.glMaterialfv(self.gl.GL_FRONT, self.gl.GL_DIFFUSE, (r, g, b, a))
        self.gl.glColor4f(r, g, b, a)

    def addShape(self, shape):
        shape.drawingObject = self.makeShape(shape)
        self.objects.append(shape)

    def makeShape(self, shape):
        genList = self.gl.glGenLists(1)
        self.gl.glNewList(genList, self.gl.GL_COMPILE)

        self.gl.glBegin(self.gl.GL_LINES)
        shape.make_path(self.drawHorLine, self.drawVerLine)
        self.gl.glEnd()

        self.gl.glEndList()

        self.topLeft.detTopLeft(shape.topLeft)
        self.bottomRight.detBottomRight(shape.bottomRight)

        return genList

    def drawHorLine(self, Ps, Pe, z):
        self.gl.glVertex3d(Ps.x, -Ps.y, z)
        self.gl.glVertex3d(Pe.x, -Pe.y, z)

    def drawVerLine(self, Ps, zTop, zBottom):
        self.gl.glVertex3d(Ps.x, -Ps.y, zTop)
        self.gl.glVertex3d(Ps.x, -Ps.y, zBottom)

    def drawOrientationArrows(self):

        rCone = 0.01
        rCylinder = 0.004
        zTop = 0.05
        zMiddle = 0.02
        zBottom = -0.03
        segments = 20

        arrow = self.gl.glGenLists(1)
        self.gl.glNewList(arrow, self.gl.GL_COMPILE)

        self.drawCone(Point(), rCone, zTop, zMiddle, segments)
        self.drawSolidCircle(Point(), rCone, zMiddle, segments)
        self.drawCylinder(Point(), rCylinder, zMiddle, zBottom, segments)
        self.drawSolidCircle(Point(), rCylinder, zBottom, segments)

        self.gl.glEndList()

        self.orientation = self.gl.glGenLists(1)
        self.gl.glNewList(self.orientation, self.gl.GL_COMPILE)

        self.setColorRGBA(0.0, 0.0, 1.0, 0.5)
        self.gl.glCallList(arrow)

        self.gl.glRotated(90, 0, 1, 0)
        self.setColorRGBA(1.0, 0.0, 0.0, 0.5)
        self.gl.glCallList(arrow)

        self.gl.glRotated(90, 1, 0, 0)
        self.setColorRGBA(0.0, 1.0, 0.0, 0.5)
        self.gl.glCallList(arrow)

        self.gl.glEndList()

    def drawWpZero(self):

        r = 0.02
        segments = 20  # must be a multiple of 4

        self.wpZero = self.gl.glGenLists(1)
        self.gl.glNewList(self.wpZero, self.gl.GL_COMPILE)

        self.setColorRGBA(0.2, 0.2, 0.2, 0.7)
        self.drawSphere(r, segments, segments // 4, segments, segments // 4)

        self.gl.glBegin(self.gl.GL_TRIANGLE_FAN)
        self.gl.glVertex3d(0, 0, 0)
        for i in range(segments // 4 + 1):
            ang = -i * 2 * pi / segments
            xy2 = Point().get_arc_point(ang, r)
            # self.gl.glNormal3d(0, -1, 0)
            self.gl.glVertex3d(xy2.x, 0, xy2.y)
        for i in range(segments // 4 + 1):
            ang = -i * 2 * pi / segments
            xy2 = Point().get_arc_point(ang, r)
            # self.gl.glNormal3d(-1, 0, 0)
            self.gl.glVertex3d(0, -xy2.y, -xy2.x)
        for i in range(segments // 4 + 1):
            ang = -i * 2 * pi / segments
            xy2 = Point().get_arc_point(ang, r)
            # self.gl.glNormal3d(0, 0, 1)
            self.gl.glVertex3d(-xy2.y, xy2.x, 0)
        self.gl.glEnd()

        self.setColorRGBA(0.6, 0.6, 0.6, 0.5)
        self.drawSphere(r * 1.25, segments, segments, segments, segments)

        self.gl.glEndList()

    def drawSphere(self, r, lats, mlats, longs, mlongs):
        lats //= 2
        # based on http://www.cburch.com/cs/490/sched/feb8/index.html
        for i in range(mlats):
            lat0 = pi * (-0.5 + i / lats)
            z0 = r * sin(lat0)
            zr0 = r * cos(lat0)
            lat1 = pi * (-0.5 + (i + 1) / lats)
            z1 = r * sin(lat1)
            zr1 = r * cos(lat1)
            self.gl.glBegin(self.gl.GL_QUAD_STRIP)
            for j in range(mlongs + 1):
                lng = 2 * pi * j / longs
                x = cos(lng)
                y = sin(lng)

                self.gl.glNormal3f(x * zr0, y * zr0, z0)
                self.gl.glVertex3f(x * zr0, y * zr0, z0)
                self.gl.glNormal3f(x * zr1, y * zr1, z1)
                self.gl.glVertex3f(x * zr1, y * zr1, z1)
            self.gl.glEnd()

    def drawSolidCircle(self, origin, r, z, segments):
        self.gl.glBegin(self.gl.GL_TRIANGLE_FAN)
        # self.gl.glNormal3d(0, 0, -1)
        self.gl.glVertex3d(origin.x, -origin.y, z)
        for i in range(segments + 1):
            ang = -i * 2 * pi / segments
            xy2 = origin.get_arc_point(ang, r)
            self.gl.glVertex3d(xy2.x, -xy2.y, z)
        self.gl.glEnd()

    def drawCone(self, origin, r, zTop, zBottom, segments):
        self.gl.glBegin(self.gl.GL_TRIANGLE_FAN)
        xy1 = Point(origin.x, -origin.y, zTop)
        self.gl.glVertex3d(xy1.x, xy1.y, xy1.z)
        for i in range(segments + 1):
            ang = i * 2 * pi / segments
            xy2 = origin.get_arc_point(ang, r)

            # self.gl.glNormal3d(xy2.x, -xy2.y, zBottom)
            self.gl.glVertex3d(xy2.x, -xy2.y, zBottom)
        self.gl.glEnd()

    def drawCylinder(self, origin, r, zTop, zBottom, segments):
        self.gl.glBegin(self.gl.GL_QUAD_STRIP)
        for i in range(segments + 1):
            ang = i * 2 * pi / segments
            xy = origin.get_arc_point(ang, r)

            # self.gl.glNormal3d(xy.x, -xy.y, 0)
            self.gl.glVertex3d(xy.x, -xy.y, zTop)
            self.gl.glVertex3d(xy.x, -xy.y, zBottom)
        self.gl.glEnd()

    def autoScale(self):
        # TODO currently only works correctly when object is not rotated
        if self.frameSize().width() >= self.frameSize().height():
            aspect_scale_x = self.frameSize().width() / self.frameSize().height()
            aspect_scale_y = 1
        else:
            aspect_scale_x = 1
            aspect_scale_y = self.frameSize().height() / self.frameSize().width()
        scaleX = (self.camRightX - self.camLeftX) * aspect_scale_x / (self.bottomRight.x - self.topLeft.x)
        scaleY = (self.camBottomY - self.camTopY) * aspect_scale_y / (self.topLeft.y - self.bottomRight.y)
        self.scale = min(scaleX, scaleY) * 0.95
        self.posX = self.camLeftX * 0.95 * aspect_scale_x - self.topLeft.x * self.scale
        self.posY = -self.camTopY * 0.95 * aspect_scale_y + self.bottomRight.y * self.scale
        self.posZ = 0
        self.update()

    def topView(self):
        self.rotX = 0
        self.rotY = 0
        self.rotZ = 0
        self.update()

    def isometricView(self):
        self.rotX = -22
        self.rotY = -22
        self.rotZ = 0
        self.update()
