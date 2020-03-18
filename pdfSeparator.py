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
        self.toolBarHeight = 38

        self.initUI()

    def initUI(self):
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.toolBarLayout = QHBoxLayout()
        self.toolBarLayout.setObjectName("toolBarLayout")
        self.toolBarLayout.addWidget(self.toolBar())
        self.verticalLayout.addLayout(self.toolBarLayout)
        self.verticalLayout.addWidget(self.workSpace())

        print(screen_size)
        self.showMaximized()
        self.center()
        self.setWindowTitle('pdfSeparator')

    def toolBar(self):
        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.setMovable(False)

        # Exit Icon to quit the App
        exitAction = QAction(QIcon('icon/exit.png'), '&Quit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.onExit)
        self.toolbar.addAction(exitAction)

    def workSpace(self):
        self.workSpaceLayout = QVBoxLayout()

        self.pixMap = QPixmap('icon/pythonLogo.png')

        self.label = QLabel()

        self.label.setBackgroundRole(QPalette.Base)
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.label)
        self.scrollArea.setVisible(False)

        self.setCentralWidget(self.scrollArea)



    def openImage(self):
        options = QFileDialog.Options()
        filename = QFileDialog.getOpenFilename(self, 'Sélectionner une image','','Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        # Modifier pour prendre un pdf puis convertir

        if filename:
            image = QImage(filename)
            if image == null:
                QMessageBox.information(self, '', "Impossible de charger {}".format(filename))
                return

            self.label.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 1

            self.scrollArea.setVisible(True)
            self.printAct.setEnabled(True)


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
