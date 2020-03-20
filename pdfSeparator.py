# -*- coding: utf8 -*-
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# https://doc.qt.io/qt-5/qtwidgets-widgets-imageviewer-example.html

screen_size = (None,None)
developerMode = False

def preBuild(app):
    global screen_size
    screen_size = app.primaryScreen().size()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--dev':
            global developerMode
            developerMode = True
            print('Developer mode activated')

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        #(self.width, self.height) = (1000,800)

        self.initUI()

    def initUI(self):

        self.toolBar()
        self.initWorkSpace()
        self.initPaint()

        self.resize(1000,800)
        #self.showMaximized()
        self.center()
        self.setWindowTitle('pdfSeparator')

    def toolBar(self):
        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.setMovable(False)

        # Exit Icon to quit the App
        self.exitAction = QAction(QIcon('icon/exit.png'), '&Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.onExit)
        self.toolbar.addAction(self.exitAction)

        self.openAction = QAction(QIcon('icon/open.png'), '&Open file', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.triggered.connect(self.open)
        self.toolbar.addAction(self.openAction)

        #self.toolbar.addWidget(QIcon('icon/zoom.png'))

        self.zoomOutAction = QAction(QIcon('icon/minus.png'), '&Zoom Out', self)
        #zoomOutAction.setShortCut('Ctrl+Maj+-')
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.zoomOutAction.setEnabled(False)
        self.toolbar.addAction(self.zoomOutAction)

        self.zoomInAction = QAction(QIcon('icon/plus.png'), '&Zoom In', self)
        #zoomInAction.setShortCut('Ctrl+Maj+=')
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomInAction.setEnabled(False)
        self.toolbar.addAction(self.zoomInAction)

        self.fitWindowAction = QAction(QIcon('icon/fitOff.png'), '&Adjust', self)
        self.fitWindowAction.triggered.connect(self.fitToWindow)
        self.fitWindowAction.setEnabled(False)
        self.toolbar.addAction(self.fitWindowAction)

        self.penAction = QAction(QIcon('icon/penOff.png'), '&Pen', self)
        self.penAction.triggered.connect(self.onPenStatus)
        self.toolbar.addAction(self.penAction)
        self.penActivationStatus = False

        self.zoneAction = QAction(QIcon('icon/zoneRectangleOff.png'), '&Zone rectangle', self)
        self.zoneAction.triggered.connect(self.onZoneStatus)
        self.toolbar.addAction(self.zoneAction)
        self.zoneActivationStatus = False

        self.zoneLineAction = QAction(QIcon('icon/zoneLineOff.png'), '&Zone line', self)
        self.zoneLineAction.triggered.connect(self.onZoneLineStatus)
        self.toolbar.addAction(self.zoneLineAction)
        self.zoneLineActivationStatus = False

        self.zonePointAction = QAction(QIcon('icon/zonePointOff.png'), '&Zone point', self)
        self.zonePointAction.triggered.connect(self.onZonePointStatus)
        self.toolbar.addAction(self.zonePointAction)
        self.zonePointActivationStatus = False

        self.extractAction = QAction(QIcon('icon/zoom.png'), '&Extract area', self)
        self.extractAction.triggered.connect(self.onExtractActivationStatus)
        self.toolbar.addAction(self.extractAction)
        self.extractActivation = False

    def initWorkSpace(self):
        self.fitWindowBool = False

        self.label = QLabel()
        self.label.setBackgroundRole(QPalette.Base)
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.label)
        self.scrollArea.setVisible(False)

        self.setCentralWidget(self.scrollArea)

    def initPaint(self):
        self.sketch = False
        self.penWidth = 4
        self.penColor = QColor(0,0,255)
        self.pen = QPen(self.penColor, self.penWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.lastPoint = QPoint()
        self.image = None
        # The history parameter is to remove last element drawn
        self.history = []
        self.historyLength = 10
        self.historyShortCut = QShortcut(QKeySequence('Ctrl+Z'), self).activated.connect(self.goBack)
        self.inEvent = False
        self.zonePointList = []
        self.extractOriginPosition = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton) and self.sketch:
            self.lastPoint = self.cropEventPos(event)

            if not self.inEvent:
                self.addHistory()

            if self.zoneActivationStatus or self.zoneLineActivationStatus:
                self.topCorner = self.lastPoint

            if self.penActivationStatus or self.zonePointActivationStatus:
                painter = QPainter(self.image)
                painter.setPen(self.pen)
                painter.drawPoint(self.cropEventPos(event))

                if self.zonePointActivationStatus:
                    self.zonePointList.append(self.cropEventPos(event))

                    if len(self.zonePointList) == 2:
                        painter.drawLine(self.zonePointList[0].x(), self.zonePointList[0].y(),
                                         self.zonePointList[1].x(), self.zonePointList[1].y())
                        self.zonePointList.pop(0)

                # print(self.image.pixel(event.pos().x(), event.pos().y()))
                self.displayUpdate()

            if self.extractActivation:
                self.extractOriginPosition = self.cropEventPos(event)
                self.onExtract(self.extractOriginPosition)


    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.LeftButton) and self.sketch:
                painter = QPainter(self.image)
                painter.setPen(self.pen)

                if self.zoneActivationStatus:
                    painter.drawRect(self.topCorner.x(), self.topCorner.y(),
                                    self.cropEventPos(event).x() - self.topCorner.x(),
                                    self.cropEventPos(event).y() - self.topCorner.y())

                if self.zoneLineActivationStatus:
                    painter.drawLine(self.topCorner.x(), self.topCorner.y(),
                                    self.cropEventPos(event).x(), self.cropEventPos(event).y())

                self.displayUpdate()
                self.inEvent = False

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.sketch:
            if (self.penActivationStatus):
                painter = QPainter(self.image)
                painter.setPen(QPen(self.penColor, self.penWidth,
                                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(self.lastPoint, self.cropEventPos(event))
                self.lastPoint = self.cropEventPos(event)
                self.displayUpdate()

    def displayUpdate(self):
        self.update()
        self.label.setPixmap(self.image)

    def addHistory(self):
        if len(self.history) == self.historyLength:
            self.history.pop(0)
        self.history.append(self.image.copy())
        self.inEvent = True

    def goBack(self):
        if len(self.history) > 1:
            del self.history[-1]
        self.image = self.history[-1]

        self.displayUpdate()
            #self.update()

    def cropEventPos(self, event):
        """
        Because of the toolbar there is an offset on the y axis.
        To have the correct position based on the image we need to correct this offset
        Moreover we need to take in account the scrollbar positions.
        """
        return QPoint(event.pos().x() + self.scrollArea.horizontalScrollBar().value(),
                      event.pos().y() - 38 + self.scrollArea.verticalScrollBar().value())

    def open(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, 'Sélectionner une image','','Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        # Modifier pour prendre un pdf puis convertir
        if filename:
            image = QImage(filename)
            if image is None:
                QMessageBox.information(self, '', "Impossible de charger {}".format(filename))
                return
            self.imagePath = filename

            self.image = QPixmap.fromImage(image)
            self.label.setPixmap(self.image)
            # Insert the image in the history
            self.history.append(self.image.copy())
            self.factor = 1

            self.sketch = True

            self.scrollArea.setVisible(True)
            #self.printAct.setEnabled(True)
            self.fitWindowAction.setEnabled(True)
            self.zoomInAction.setEnabled(True)
            self.zoomOutAction.setEnabled(True)

            if not self.fitWindowAction.isChecked():
                self.label.adjustSize()

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.75)

    def normalSize(self):
        self.label.adjustSize()
        self.factor = 1.0

    def fitToWindow(self):
        self.scrollArea.setWidgetResizable(not self.fitWindowBool)
        print('Before: ',self.fitWindowBool)
        if self.fitWindowBool:
            self.fitWindowAction.setIcon(QIcon('icon/fitOff.png'))
            self.normalSize()
        else:
            self.fitWindowAction.setIcon(QIcon('icon/fitOn.png'))

        self.updateFit()
        self.fitWindowBool = not self.fitWindowBool

    def updateFit(self):
        self.zoomInAction.setEnabled(self.fitWindowBool)
        self.zoomOutAction.setEnabled(self.fitWindowBool)

    def scaleImage(self, factor):
        self.factor *= factor
        self.label.resize(self.factor * self.label.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        self.zoomInAction.setEnabled(self.factor < 3.0)
        self.zoomOutAction.setEnabled(self.factor > .333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1 ) * scrollBar.pageStep() / 2 )))


    def onExit(self, event):
        reply = QMessageBox.question(self, '', 'Are you sure you want to quit?', QMessageBox.Cancel | QMessageBox.Ok, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            app.quit()
        else:
            pass

    def onExtractActivationStatus(self):
        self.extractActivation = True
        self.disableAllElements(None)

    def onExtract(self, origin):

        img = self.image.toImage()
        img.save('tmp/extremeLocation.png')

        colorToDetect = list(self.penColor.getRgb()[:-1])[::-1]
        """
        We get only the R,G,B values without the alpha factor and we reverse the
        list because colorToDetect is RGB and the images are BGR.
        """

        opencvImg = cv2.imread('tmp/extremeLocation.png',1)

        pixelToDetect = cv2.imread('tmp/colorReference.png')
        if pixelToDetect is None or pixelToDetect[0][0] is not colorToDetect:
            pixelToDetect[0][0] = [colorToDetect[0], colorToDetect[1], colorToDetect[2]]
            cv2.imwrite('tmp/colorReference.png',pixelToDetect)

        pixel = cv2.imread('tmp/colorReference.png')
        pixel2 = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
        boundary = pixel2[0][0]

        opencvImg = cv2.cvtColor(opencvImg, cv2.COLOR_BGR2HSV)

        if developerMode:
            cv2.imwrite('tmp/inter.png',opencvImg)
        mask = cv2.inRange(opencvImg, boundary, boundary)

        _, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        extremePoints = []
        """
        The extremPOints list store the extreme points of each polygon and their centroid
        found in the image. This will be helpfull to crop the image later.
        """

        for c in cnts:
            M = cv2.moments(c)
            # calculate x,y coordinate of center
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            if developerMode:
                cv2.circle(opencvImg, (cX, cY), 5, (0, 0, 255), -1)
                cv2.putText(opencvImg, "centroid", (cX - 25, cY - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                mask = cv2.drawContours(mask,[c], -1,(255,255,255),-1)

            x, y, w, h = cv2.boundingRect(c)
            extremePoints.append([(cX,cY),(x,y,w,h)])

            # cv2.rectangle(opencvImg, (x, y), (x+w, y+h), (0, 255, 0), 2)

        if developerMode:
            cv2.imwrite('tmp/mask.png', mask)

        # The origin is the position clicked by the user which is inside the wanted area
        originX = origin.x()
        originY = origin.y()

        if developerMode:
            cv2.circle(opencvImg, (originX, originY), 5, (255, 255, 255), -1)
            cv2.imwrite('tmp/moments.png', opencvImg)

        """
        In the case of several areas, the user can only extract one where he clicked.
        So we need to find the closest area from the clicked position.
        """

        def closestArea(extremsPoints, originX, originY, closestDist, indexClosest, index):
            """
            The centroidX and centroidY parameters are the centroids argument of
            an element in the extremePoints list.
            indexCLosest is the index of the closest area in the extremePoints list.
            This function is recursive so index is the current position in
            """
            if index >= len(extremePoints) or len(extremePoints) == 0:
                return indexClosest

            (centroidX, centroidY) = extremePoints[index][0]
            dist = np.sqrt( (originX - centroidX)**2 + (originY - centroidY)**2 )
            if dist < closestDist:
                closestDist = dist
                indexClosest = index

            return closestArea(extremePoints, originX, originY, closestDist, indexClosest, index+1)

        areaToExtract = extremePoints[closestArea(extremePoints, originX, originY, opencvImg.shape[0], 0, 0)]
        (X, Y, W, H) = areaToExtract[1]

        if developerMode:
            cv2.rectangle(opencvImg, (X, Y), (X+W, Y+H), (0, 255, 0), 2)
            cv2.imwrite('tmp/areaToExtract.png', opencvImg)

        """
        Now we have the extreme points of the area, it's time to crop it.
        """

        fullImage = cv2.imread(self.imagePath)
        cropImage = np.zeros([H, W, 3], dtype=np.uint8)
        cropImage.fill(255)

        inside = False
        boundaryPixel = 255

        for pY in range(H):
            for pX in range(W):
                if mask[Y+pY][X+pX] == boundaryPixel:
                    cropImage[pY][pX] = fullImage[Y+pY][X+pX]

        cv2.imwrite('tmp/croppedImage.png', cropImage)

    def onPenStatus(self):
        self.disableAllElements(self.penAction)
        if self.penActivationStatus:
            self.penAction.setIcon(QIcon('icon/penOff.png'))
        else:
            self.penAction.setIcon(QIcon('icon/penOn.png'))
        self.penActivationStatus = not self.penActivationStatus

    def onZoneStatus(self):
        self.disableAllElements(self.zoneAction)
        if self.zoneActivationStatus:
            self.zoneAction.setIcon(QIcon('icon/zoneRectangleOff.png'))
        else:
            self.zoneAction.setIcon(QIcon('icon/zoneRectangleOn.png'))
        self.zoneActivationStatus = not self.zoneActivationStatus

    def onZoneLineStatus(self):
        self.disableAllElements(self.zoneLineAction)
        if self.zoneLineActivationStatus:
            self.zoneLineAction.setIcon(QIcon('icon/zoneLineOff.png'))
        else:
            self.zoneLineAction.setIcon(QIcon('icon/zoneLineOn.png'))
        self.zoneLineActivationStatus = not self.zoneLineActivationStatus

    def onZonePointStatus(self):
        self.disableAllElements(self.zonePointAction)
        if self.zonePointActivationStatus:
            self.zonePointAction.setIcon(QIcon('icon/zonePointOff.png'))
        else:
            self.zonePointAction.setIcon(QIcon('icon/zonePointOn.png'))
        self.zonePointActivationStatus = not self.zonePointActivationStatus
        self.zonePointList = []

    def disableAllElements(self, elementClicked):
        if elementClicked != self.penAction:
            self.penActivationStatus = False
            self.penAction.setIcon(QIcon('icon/penOff.png'))

        if elementClicked != self.zoneAction:
            self.zoneActivationStatus = False
            self.zoneAction.setIcon(QIcon('icon/zoneRectangleOff.png'))

        if elementClicked != self.zoneLineAction:
            self.zoneLineActivationStatus = False
            self.zoneLineAction.setIcon(QIcon('icon/zoneLineOff.png'))

        if elementClicked != self.zonePointAction:
            self.zonePointActivationStatus = False
            self.zonePointAction.setIcon(QIcon('icon/zonePointOff.png'))

        self.zonePointList = []


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    preBuild(app)
    window = App()
    window.show()
    sys.exit(app.exec_())
