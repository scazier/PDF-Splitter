import cv2
import img2pdf
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

developerMode = False
dpi = 300.0

class PDF(QMainWindow):
    def __init__(self, start=None, width=None, height=None):
        super().__init__()
        self.start = start
        self.exportWidth = width
        self.exportHeight = height

        self.resize(600, 800)

        popupToolbar = self.addToolBar('toolbar')
        popupToolbar.setMovable(False)

        antiRotateAction = QAction(QIcon('icon/antiRotate.png'), '&Rotate -90°', self)
        antiRotateAction.triggered.connect(self.onAntiRotate)

        rotateAction = QAction(QIcon('icon/rotate.png'), '&Rotate 90°', self)
        rotateAction.triggered.connect(self.onRotate)

        printAction = QAction(QIcon('icon/print.png'), '&Print as PDF', self)
        printAction.triggered.connect(self.exportTOPDF) #self.exportTOPDF(pixmap.width(), pixmap.height())

        popupToolbar.addAction(antiRotateAction)
        popupToolbar.addAction(rotateAction)
        popupToolbar.addAction(printAction)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)
        self.image = QImage('tmp/croppedImage.png')
        self.pixmap = QPixmap.fromImage(self.image)
        self.reshape()
        self.label.setPixmap(self.pixmap)

        self.show()

    def reshape(self):
        if self.pixmap.height() > self.height():
            self.pixmap = self.pixmap.scaledToHeight(500)
        if self.pixmap.width() > self.width():
            self.pixmap = self.pixmap.scaledToWidth(500)

    def onAntiRotate(self):
        transform = QTransform()
        transform.rotate(90)
        self.image = self.image.transformed(transform)
        self.pixmap = QPixmap.fromImage(self.image)
        self.reshape()
        self.label.setPixmap(self.pixmap)

    def onRotate(self):
        transform = QTransform()
        transform.rotate(-90)
        self.image = self.image.transformed(transform)
        self.pixmap = QPixmap.fromImage(self.image)
        self.reshape()
        self.label.setPixmap(self.pixmap)


    def exportTOPDF(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Export to PDF', '', 'PDF files (*.pdf)')
        if developerMode:
            print('\tStart creation of pdf => ' + str(time.time() - self.start) + ' s')

        """
        The quality of the pdf is defined with the dpi so in order to have a proper
        output we need to set the width and the height of the pdf.
        You can easily check it on a linux system 'pdfimages':
            pdfimages -list <filename>.pdf
        """

        dim = (img2pdf.in_to_pt(self.exportWidth/dpi), img2pdf.in_to_pt(self.exportHeight/dpi))
        layout = img2pdf.get_layout_fun(dim)

        with open(filename,'wb') as file:
            file.write(img2pdf.convert('tmp/croppedImage.png', layout_fun = layout))

        if developerMode:
            print('\tPDF successfully created! => '+ str(time.time() - self.start) + ' s')
