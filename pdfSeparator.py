import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# https://doc.qt.io/qt-5/qtwidgets-widgets-imageviewer-example.html

screen_size = (None,None)

def preBuild(app):
    global screen_size
    screen_size = app.primaryScreen().size()

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        #(self.width, self.height) = (1000,800)

        self.initUI()

    def initUI(self):

        self.toolBar()
        self.initWorkSpace()
        self.initPaint()

        self.showMaximized()
        self.center()
        self.setWindowTitle('pdfSeparator')

    def toolBar(self):
        self.toolBarHeight = 38

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

        #self.addToolBar(QIcon('icon/zoom.png'))

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
        self.penAction.triggered.connect(self.penActivation)
        self.toolbar.addAction(self.penAction)
        self.penActivationStatus = False

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
        self.penWidth = 10
        self.sketch = False
        self.penColor = QColor(51,51,255)
        self.lastPoint = QPoint()
        self.image = None

    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.drawPixmap(self.rect(), self.image)

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton) and self.sketch:
            self.lastPoint = event.pos()

            if (self.penActivationStatus):
                painter = QPainter(self.image)
                painter.setPen(QPen(self.penColor, self.penWidth,
                                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawPoint(event.pos())
                self.displayUpdate()

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.LeftButton) and self.sketch:
            if (self.lastPoint == event.pos()):
                # painter = QPainter(self.image)
                # painter.setPen(QPen(self.penColor, self.penWidth,
                #                     Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                # paint.drawPoint(event.pos())
                pass


    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.sketch:
            if (self.penActivationStatus):
                painter = QPainter(self.image)
                painter.setPen(QPen(self.penColor, self.penWidth,
                                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(self.lastPoint, event.pos())
                self.lastPoint = event.pos()
                self.displayUpdate()

    def displayUpdate(self):
        self.update()
        self.label.setPixmap(self.image)

    def open(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, 'Sélectionner une image','','Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        # Modifier pour prendre un pdf puis convertir
        if filename:
            image = QImage(filename)
            if image is None:
                QMessageBox.information(self, '', "Impossible de charger {}".format(filename))
                return

            self.image = QPixmap.fromImage(image)
            self.label.setPixmap(self.image)
            self.factor = 1

            self.sketch = True # Allow to paint the image now

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

    def penActivation(self):

        if self.penActivationStatus:
            self.penAction.setIcon(QIcon('icon/penOff.png'))
        else:
            self.penAction.setIcon(QIcon('icon/penOn.png'))
        self.penActivationStatus = not self.penActivationStatus

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
