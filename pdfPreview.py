#-*- coding:utf-8 -*-
import os
import sys
import cv2
import time
import img2pdf
import datetime
import numpy as np
from PyQt5.QtWidgets import (QAction, QLabel, QToolBar, QSizePolicy, QWidget,
                             QGridLayout)
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtCore import Qt


class PDF(QWidget):
    def __init__(self, mainInstance, fullImage, dpi, savepath, developerMode=False, start=None):
        QWidget.__init__(self)
        layout = QGridLayout()
        self.setLayout(layout)
        self.start = start
        self.dpi = dpi
        self.savepath = savepath
        self.mainInstance = mainInstance
        self.fullImage = fullImage
        self.developerMode = developerMode
        self.img = cv2.imread('tmp/croppedImage.png')

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
        self.img = cv2.rotate(self.img, cv2.ROTATE_90_CLOCKWISE)

    def onRotate(self):
        transform = QTransform()
        transform.rotate(-90)
        self.image = self.image.transformed(transform)
        self.pixmap = QPixmap.fromImage(self.image)
        self.reshape()
        self.label.setPixmap(self.pixmap)
        self.img = cv2.rotate(self.img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def colorCheck(self):
        if self.colorCheckBox.isChecked():
            self.img = cv2.imread('tmp/croppedImage.png', 1)
        else:
            self.img = cv2.imread('tmp/croppedImage.png', 0)


    def exportTOPDF(self):
        if self.developerMode:
            print('\tStart creation of pdf => ' + str(time.time() - self.start) + ' s')

        """
        The quality of the pdf is defined with the dpi so in order to have a proper
        output we need to set the width and the height of the pdf.
        You can easily check it on a linux system with 'pdfimages':
            pdfimages -list <filename>.pdf
        """
        cv2.imwrite('tmp/croppedImage.png', self.img)

        dim = (img2pdf.in_to_pt(self.img.shape[1]/self.dpi), img2pdf.in_to_pt(self.img.shape[0]/self.dpi))
        layout = img2pdf.get_layout_fun(dim)

        if self.savepath[-1] != '/':
            self.savepath += '/'

        filename = '-'.join(str(datetime.datetime.now()).split('.')[0].split(' '))+".pdf"
        filename = filename.replace(':','-')

        with open(self.savepath+filename,'wb') as file:
            file.write(img2pdf.convert('tmp/croppedImage.png', layout_fun = layout))

        if self.developerMode:
            print('\tPDF successfully created! => '+ str(time.time() - self.start) + ' s')

        # Update the main window label to hide the extracted zone
        cv2.imwrite('tmp/processedImage.png', self.fullImage)
        self.mainInstance.image = QPixmap.fromImage(self.mainInstance.arrayToPixmap(self.fullImage))
        self.mainInstance.displayUpdate()

        self.close()
