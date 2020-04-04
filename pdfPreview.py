import cv2
import img2pdf
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

developerMode = False
dpi = 300.0
statusWindow = 0

class PDF(QWidget):
    def __init__(self, start=None):
        QWidget.__init__(self)
        layout = QGridLayout()
        self.setLayout(layout)
        self.start = start

        self.resize(600, 800)

        popupToolbar = QToolBar()
        layout.addWidget(popupToolbar)

        antiRotateAction = QAction(QIcon('icon/antiRotate.png'), '&Rotate -90°', self)
        antiRotateAction.triggered.connect(self.onAntiRotate)

        rotateAction = QAction(QIcon('icon/rotate.png'), '&Rotate 90°', self)
        rotateAction.triggered.connect(self.onRotate)

        printAction = QAction(QIcon('icon/print.png'), '&Print as PDF', self)
        printAction.triggered.connect(self.exportTOPDF)

        self.colorCheckBox = QAction('Export in color', self, checkable=True)
        self.colorCheckBox.triggered.connect(self.colorCheck)

        popupToolbar.addAction(antiRotateAction)
        popupToolbar.addAction(rotateAction)
        popupToolbar.addAction(printAction)
        popupToolbar.addAction(self.colorCheckBox)

        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignCenter)

        self.image = QImage('tmp/croppedImage.png')
        self.pixmap = QPixmap.fromImage(self.image)
        self.reshape()
        self.label.setPixmap(self.pixmap)

        center = (self.width()/2, self.height()/2)
        self.label.move(center[0] - self.pixmap.width()/2, center[1] - self.pixmap.height()/2)

        self.setWindowModality(Qt.WindowModal)
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
        img = cv2.imread('tmp/croppedImage.png')
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite('tmp/croppedImage.png',img)

    def onRotate(self):
        transform = QTransform()
        transform.rotate(-90)
        self.image = self.image.transformed(transform)
        self.pixmap = QPixmap.fromImage(self.image)
        self.reshape()
        self.label.setPixmap(self.pixmap)
        img = cv2.imread('tmp/croppedImage.png')
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        cv2.imwrite('tmp/croppedImage.png',img)

    def colorCheck(self):
        if self.colorCheckBox.isChecked():
            img = cv2.imread('tmp/croppedImage.png', 1)
        else:
            img = cv2.imread('tmp/croppedImage.png', 0)
        cv2.imwrite('tmp/croppedImage.png', img)


    def exportTOPDF(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, 'Export to PDF', '', 'PDF files (*.pdf)', options=options)
        if developerMode:
            print('\tStart creation of pdf => ' + str(time.time() - self.start) + ' s')

        """
        The quality of the pdf is defined with the dpi so in order to have a proper
        output we need to set the width and the height of the pdf.
        You can easily check it on a linux system 'pdfimages':
            pdfimages -list <filename>.pdf
        """
        img = cv2.imread('tmp/croppedImage.png')

        dim = (img2pdf.in_to_pt(img.shape[1]/dpi), img2pdf.in_to_pt(img.shape[0]/dpi))
        layout = img2pdf.get_layout_fun(dim)

        if filename[-3:] != 'pdf':
            filename = filename + '.pdf'

        with open(filename,'wb') as file:
            file.write(img2pdf.convert('tmp/croppedImage.png', layout_fun = layout))

        if developerMode:
            print('\tPDF successfully created! => '+ str(time.time() - self.start) + ' s')

        self.close()
