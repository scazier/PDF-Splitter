# -*- coding: utf8 -*-
import os
import sys
import cv2
import time
import numpy as np
from pdfPreview import PDF
from pdf2image import convert_from_path
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import (QIcon, QPalette, QColor, QPen,
                         QKeySequence, QPainter, QImage, QPixmap, qRgb)
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QFileDialog,
                             QMessageBox, QAction, QStatusBar, QLabel, QSizePolicy,
                             QScrollArea, QShortcut, QDesktopWidget, QProgressBar)


# https://doc.qt.io/qt-5/qtwidgets-widgets-imageviewer-example.html

screen_size = (None,None)
developerMode = False
dpi = 300.0
savepath = "tmp/"

def preBuild(app):
    global screen_size
    global dpi
    global savepath
    screen_size = app.primaryScreen().size()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--dev':
            global developerMode
            developerMode = True
            print('Developer mode activated')

    with open('config.txt') as config:
        content = config.readlines()
        content = [x.strip().split('=') for x in content if x[0] not in ['#','',' ','\n','\t']]
        for line in content:
            if line[0] == "dpi" and float(line[1]) != dpi:
                dpi = float(line[1])
            if line[0] == "savePath" and line[1] != savepath:
                savepath = line[1]
        print(dpi, savepath)

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('icon/pdf.png'))
        self.initUI()

    def initUI(self):
        self.toolBar()
        self.initWorkSpace()
        self.initPaint()
        self.initDev()

        self.resize(1000,800)
        #self.showMaximized()
        self.center()
        self.setWindowTitle('pdfSeparator')

    def initDev(self):
        self.start = None # Variable for time study of the program

    def toolBar(self):
        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.setMovable(False)

        # Exit Icon to quit the App
        self.exitAction = QAction(QIcon('icon/exit.png'), '&Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.onExit)

        self.openAction = QAction(QIcon('icon/open.png'), '&Open file', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.triggered.connect(self.open)

        #self.toolbar.addWidget(QIcon('icon/zoom.png'))

        self.zoomOutAction = QAction(QIcon('icon/minus.png'), '&Zoom Out', self)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.zoomOutAction.setEnabled(False)

        self.zoomInAction = QAction(QIcon('icon/plus.png'), '&Zoom In', self)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomInAction.setEnabled(False)

        self.fitWindowAction = QAction(QIcon('icon/fitOff.png'), '&Adjust', self)
        self.fitWindowAction.triggered.connect(self.fitToWindow)
        self.fitWindowAction.setEnabled(False)

        self.penAction = QAction(QIcon('icon/penOff.png'), '&Pen', self)
        self.penAction.triggered.connect(self.onPenStatus)
        self.penActivationStatus = False

        self.zoneAction = QAction(QIcon('icon/zoneRectangleOff.png'), '&Zone rectangle', self)
        self.zoneAction.triggered.connect(self.onZoneStatus)
        self.zoneActivationStatus = False

        self.zoneLineAction = QAction(QIcon('icon/zoneLineOff.png'), '&Zone line', self)
        self.zoneLineAction.triggered.connect(self.onZoneLineStatus)
        self.zoneLineActivationStatus = False

        self.zonePointAction = QAction(QIcon('icon/zonePointOff.png'), '&Zone point', self)
        self.zonePointAction.triggered.connect(self.onZonePointStatus)
        self.zonePointActivationStatus = False

        self.extractAction = QAction(QIcon('icon/exportOff.png'), '&Extract area', self)
        self.extractAction.triggered.connect(self.onExtractActivationStatus)
        self.extractActivation = False

        self.checkedAction = QAction(QIcon('icon/checkedOff.png'), '&Sign pdf as processed', self)
        self.checkedAction.triggered.connect(self.onCheckedActivationStatus)
        self.checkedActivation = False

        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addAction(self.fitWindowAction)
        self.toolbar.addAction(self.penAction)
        self.toolbar.addAction(self.zoneAction)
        self.toolbar.addAction(self.zoneLineAction)
        self.toolbar.addAction(self.zonePointAction)
        self.toolbar.addAction(self.extractAction)
        self.toolbar.addAction(self.checkedAction)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

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
        self.isDrawn = False

    def paintEvent(self, event):
        painter = QPainter(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.sketch:
                self.lastPoint = self.cropEventPos(event)

                if not self.inEvent and not self.extractActivation:
                    self.addHistory()

                if self.zoneActivationStatus or self.zoneLineActivationStatus:
                    self.topCorner = self.lastPoint

                if self.penActivationStatus or self.zonePointActivationStatus:
                    painter = QPainter(self.image)
                    painter.setPen(self.pen)
                    painter.drawPoint(self.cropEventPos(event))
                    self.isDrawn = True

                    if self.zonePointActivationStatus:
                        self.zonePointList.append(self.cropEventPos(event))

                        if len(self.zonePointList) == 2:
                            painter.drawLine(self.zonePointList[0].x(), self.zonePointList[0].y(),
                                             self.zonePointList[1].x(), self.zonePointList[1].y())
                            self.zonePointList.pop(0)

                    self.displayUpdate()

        if self.extractActivation:
            self.extractOriginPosition = self.cropEventPos(event)
            self.onExtract(self.extractOriginPosition)


    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.LeftButton) and self.sketch:
                painter = QPainter(self.image)
                painter.setPen(self.pen)

                if self.zoneActivationStatus:
                    position = self.cropEventPos(event)
                    (endCornerX, endCornerY) = (position.x(), position.y())

                    if endCornerX < 0:
                        endCornerX = 0
                    elif endCornerX > self.image.width():
                        endCornerX = self.image.width()

                    if endCornerY < 0:
                        endCornerY = 0
                    elif endCornerY > self.image.height():
                        endCornerY = self.image.height()

                    painter.drawRect(self.topCorner.x(), self.topCorner.y(),
                                    endCornerX - self.topCorner.x(),
                                    endCornerY - self.topCorner.y())
                    self.isDrawn = True

                if self.zoneLineActivationStatus:
                    painter.drawLine(self.topCorner.x(), self.topCorner.y(),
                                    self.cropEventPos(event).x(), self.cropEventPos(event).y())
                    self.isDrawn = True

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
                self.isDrawn = True

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
        return QPoint((event.pos().x() + self.scrollArea.horizontalScrollBar().value()) / self.factor,
                     (event.pos().y() - 38 + self.scrollArea.verticalScrollBar().value()) / self.factor)

    def open(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, 'Sélectionner un fichier','','Images (*.pdf *.png *.jpeg *.jpg *.bmp *.gif)', options=options)

        self.filename = filename

        if developerMode:
            self.start = time.time()
            print('Open and convert file:')
            print('\tGot filename: ' + filename + ' => ' + str(time.time() - self.start))

        if filename[-3:] == 'pdf':
            file = convert_from_path(filename, 300)
            filename = 'tmp/'+filename.split('/')[-1][:-3]+'png'
            print(filename)
            file[0].save(filename,'PNG')
            if developerMode:
                print('\tFile converted with success => ' + str(time.time() - self.start))

        if filename:
            image = QImage(filename)
            if image is None:
                QMessageBox.information(self, '', "Impossible de charger {}".format(filename))
                return
            self.imagePath = filename

            self.image = QPixmap.fromImage(image)
            self.label.resize(self.image.width(), self.image.height())
            self.label.setPixmap(self.image)

            # Insert the image in the history
            self.history.append(self.image.copy())

            self.factor = 1.0
            self.sketch = True

            self.scrollArea.setVisible(True)
            self.fitWindowAction.setEnabled(True)
            self.zoomInAction.setEnabled(True)
            self.zoomOutAction.setEnabled(True)


            if not self.fitWindowAction.isChecked():
                self.label.adjustSize()

            self.initAdjust()

            if developerMode:
                print('\tFile is now adjusted to the window => ' + str(time.time() - self.start))

        else:
            pass

        # Remove a previous processed image if exists
        pathProcessed = os.listdir('tmp/')
        if "processedImage.png" in pathProcessed:
            os.remove('tmp/processedImage.png')

    def initAdjust(self):
        while self.label.height() > self.height() and self.label.width() > self.width():
            self.scaleImage(0.8)

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
        self.zoomInAction.setEnabled(self.factor < 10.0)
        self.zoomOutAction.setEnabled(self.factor > .1)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1 ) * scrollBar.pageStep() / 2 )))


    def onExit(self, event):
        reply = QMessageBox.question(self, '', 'Are you sure you want to quit?', QMessageBox.Cancel | QMessageBox.Ok, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            app.quit()
        else:
            pass

    def onExtractActivationStatus(self):
        self.disableAllElements(None)
        if self.extractActivation:
            self.extractAction.setIcon(QIcon('icon/exportOff.png'))
        else:
            self.extractAction.setIcon(QIcon('icon/exportOn.png'))
        self.extractActivation = not self.extractActivation

    def pixmapToArray(self, img):
        channels_count = 4
        s = img.bits().asstring(img.width() * img.height() * channels_count)
        return np.frombuffer(s, dtype=np.uint8).reshape((img.height(), img.width(), channels_count))

    def arrayToPixmap(self, im):
        gray_color_table = [qRgb(i, i, i) for i in range(256)]
        if im is None:
            return QImage()
        if len(im.shape) == 2:  # 1 channel image
            qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
            return qim
        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888)
                return qim
            elif im.shape[2] == 4:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32)
                return qim

    def colorCheck(self, pixelToDetect, colorToDetect):
        if developerMode:
            print('\tCheck color to detect => ' + str(time.time() - self.start) + 's')

        if pixelToDetect is None or (pixelToDetect[0][0] != colorToDetect).all():
            pixelToDetect[0][0] = [colorToDetect[0], colorToDetect[1], colorToDetect[2]]
            cv2.imwrite('tmp/colorReference.png',pixelToDetect)

            if developerMode:
                print('\tAdd color to detect => ' + str(time.time() - self.start) + ' s')

    def contours(self, opencvImg):
        pixel = cv2.imread('tmp/colorReference.png')
        pixel2 = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
        boundary = pixel2[0][0]

        opencvImg = cv2.cvtColor(opencvImg, cv2.COLOR_BGR2HSV)

        if developerMode:
            cv2.imwrite('tmp/inter.png',opencvImg)
            print('\tConversion to HSV => ' + str(time.time() - self.start) + ' s')

        mask = cv2.inRange(opencvImg, boundary, boundary)
        _, cnts, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        return opencvImg, mask, cnts

    def centroids(self, opencvImg, mask, cnts):
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
            mask = cv2.drawContours(mask,[c], -1,(255,255,255),-1)

            if developerMode:
                cv2.circle(opencvImg, (cX, cY), 5, (0, 0, 255), -1)
                cv2.putText(opencvImg, "centroid", (cX - 25, cY - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            x, y, w, h = cv2.boundingRect(c)
            extremePoints.append([(cX,cY),(x,y,w,h)])

        return opencvImg, mask, extremePoints

        if developerMode:
            cv2.imwrite('tmp/mask.png', mask)
            print('\tMask and centroids created => ' + str(time.time() - start) + ' s')

    def closestArea(self, extremePoints, originX, originY, closestDist, indexClosest, index):
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

        return self.closestArea(extremePoints, originX, originY, closestDist, indexClosest, index+1)

    def onExtract(self, origin):

        colorToDetect = np.uint8(list(self.penColor.getRgb()[:-1])[::-1])
        """
        We get only the R,G,B values without the alpha factor and we reverse the
        list because colorToDetect is RGB and the images are BGR.
        """
        if not self.isDrawn:
            return None

        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setMaximum(100)
        self.statusBar.addWidget(self.progressBar)
        informationLabel = QLabel()
        informationLabel.setText('Extracting the area...')
        self.statusBar.addWidget(informationLabel)

        self.progressBar.setValue(0)

        if developerMode:
            self.start = time.time()
            print('Extraction of the area: ')
            print('\tBackup of the new image => ' + str(time.time() - self.start) + ' s')

        img = self.image.toImage()
        self.opencvImg = self.pixmapToArray(img)
        cv2.imwrite('tmp/extremeLocation.png', self.opencvImg)

        if developerMode:
            print('\tImage saved => ' + str(time.time() - self.start) + ' s')

        self.progressBar.setValue(20)

        pixelToDetect = cv2.imread('tmp/colorReference.png')

        self.colorCheck(pixelToDetect, colorToDetect)
        self.opencvImg, mask, cnts = self.contours(self.opencvImg)

        self.opencvImg, mask, extremePoints = self.centroids(self.opencvImg, mask, cnts)
        self.progressBar.setValue(40)

        # The origin is the position clicked by the user which is inside the wanted area
        originX = origin.x()
        originY = origin.y()

        if developerMode:
            cv2.circle(self.opencvImg, (originX, originY), 5, (255, 255, 255), -1)
            cv2.imwrite('tmp/moments.png', self.opencvImg)

        """
        In the case of several areas, the user can only extract one where he clicked.
        So we need to find the closest area from the clicked position.
        """

        indexExtremePoints = self.closestArea(extremePoints, originX, originY, self.opencvImg.shape[0], 0, 0)
        if indexExtremePoints < len(extremePoints):
            (X, Y, W, H) = extremePoints[indexExtremePoints][1]
        else:
            self.statusBar.removeWidget(self.progressBar)
            self.statusBar.removeWidget(informationLabel)
            return None
        self.progressBar.setValue(60)

        if developerMode:
            cv2.rectangle(self.opencvImg, (X, Y), (X+W, Y+H), (0, 255, 0), 2)
            cv2.imwrite('tmp/areaToExtract.png', self.opencvImg)
            print('\tFind area to extract => ' + str(time.time() - self.start) + ' s')

        """
        Now we have the extreme points of the area, it's time to crop it.
        """

        tmpList = os.listdir('tmp/')
        if "processedImage.png" in tmpList:
            fullImage = cv2.imread('tmp/processedImage.png')
        else:
            fullImage = cv2.imread(self.imagePath)

        cropImage = np.zeros([H, W, 3], dtype=np.uint8)
        cropImage.fill(255)

        res = cv2.bitwise_and(fullImage, fullImage, mask=mask)
        self.progressBar.setValue(80)
        res[mask==0] = (255,255,255)

        if developerMode:
            cv2.imwrite('tmp/bitwise.png', res)
            print('\tApplication of the mask: ' + str(time.time() - self.start) + 's')

        cropImage = res[Y:Y+H,X:X+W]
        cv2.imwrite('tmp/croppedImage.png', cropImage)
        self.progressBar.setValue(100)

        fullImage[mask==255] = (188, 185, 196)

        if developerMode:
            self.preview = PDF(self, fullImage, dpi, savepath, developerMode, self.start)
        else:
            self.preview = PDF(self, fullImage, dpi, savepath)
        self.preview.setWindowModality(Qt.WindowModal)
        self.statusBar.removeWidget(self.progressBar)
        self.statusBar.removeWidget(informationLabel)


        if len(cnts) == 1:
            self.isDrawn = False


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

    def onCheckedActivationStatus(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Voulez vous marquer le fichier comme traité")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            path = '/'.join(self.filename.split('/')[:-1])
            newFilename = "/PROCESSED-" + self.filename.split('/')[-1]
            os.rename(self.filename, path+newFilename)
            self.disableAllElements(None)
            self.checkedAction.setIcon(QIcon('icon/checkedOn.png'))

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

        if elementClicked != self.extractAction:
            self.extractActivation = False
            self.extractAction.setIcon(QIcon('icon/exportOff.png'))

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
