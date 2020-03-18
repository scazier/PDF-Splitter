import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# https://doc.qt.io/qt-5/qtwidgets-widgets-imageviewer-example.html

screen_size = (None,None)
fitWindowBool = False

def preBuild(app):
    global screen_size
    screen_size = app.primaryScreen().size()

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        #(self.width, self.height) = (1000,800)
        self.toolBarHeight = 38

        self.initUI()

    def initUI(self):

        self.toolBar()
        self.workSpace()

        self.showMaximized()
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

        #self.addToolBar(QIcon('icon/zoom.png'))

        self.zoomOutAction = QAction(QIcon('icon/minus.png'), '&Zoom Out', self)
        #zoomOutAction.setShortCut('Ctrl+Maj+-')
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.toolbar.addAction(self.zoomOutAction)

        self.zoomInAction = QAction(QIcon('icon/plus.png'), '&Zoom In', self)
        #zoomInAction.setShortCut('Ctrl+Maj+=')
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.toolbar.addAction(self.zoomInAction)

        self.fitWindowAction = QAction(QIcon('icon/fitOff.png'), '&Adjust', self)
        self.fitWindowAction.triggered.connect(self.fitToWindow)
        self.toolbar.addAction(self.fitWindowAction)

    def workSpace(self):
        self.workSpaceLayout = QVBoxLayout()

        self.pixMap = QPixmap('exampleImage/pythonLogo.png')

        self.label = QLabel()

        self.label.setBackgroundRole(QPalette.Base)
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.label)
        self.scrollArea.setVisible(False)

        self.setCentralWidget(self.scrollArea)



    def open(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, 'Sélectionner une image','','Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        # Modifier pour prendre un pdf puis convertir

        if filename:
            image = QImage(filename)
            if image is None:
                QMessageBox.information(self, '', "Impossible de charger {}".format(filename))
                return

            self.label.setPixmap(QPixmap.fromImage(image))
            self.factor = 1

            self.scrollArea.setVisible(True)
            #self.printAct.setEnabled(True)
            self.fitWindowAction.setEnabled(True)
            self.update()

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
        global fitWindowBool
        self.scrollArea.setWidgetResizable(fitWindowBool)

        if not fitWindowBool:
            self.normalSize()
            self.fitWindowAction.setIcon(QIcon('icon/fitOff.png'))
        else:
            self.fitWindowAction.setIcon(QIcon('icon/fitOn.png'))

        self.update()
        fitWindowBool = not fitWindowBool

    def update(self):
        global fitWindowBool
        self.zoomInAction.setEnabled(not fitWindowBool)
        self.zoomOutAction.setEnabled(not fitWindowBool)

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
