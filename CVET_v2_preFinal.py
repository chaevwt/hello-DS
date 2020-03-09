

"""
Created on Tue Feb 18 03:07:58 2020

@author: Chaev-Tech
"""

#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys


from PyQt5.QtCore import Qt, QBuffer
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog, QApplication, QDockWidget, QGroupBox, QVBoxLayout
from win32api import GetCursorPos
from collections import namedtuple
import io
from PIL import Image
import colorsys
from sklearn.cluster import KMeans
from collections import Counter
import cv2 #for resizing image
import numpy as np

Point = namedtuple('Point', ('coords', 'n', 'ct'))
Cluster = namedtuple('Cluster', ('points', 'center', 'n'))


class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.left = 10
        self.top = 10
        self.title = 'Cvet v 0.2_ATest'
        self.resize(1280, 720)
        
        self.CONTRAST_FACTOR_MAX = 1.5
        self.CONTRAST_FACTOR_MIN = 0.5

        self.SHARPNESS_FACTOR_MAX = 3
        self.SHARPNESS_FACTOR_MIN = -1

        self.BRIGHTNESS_FACTOR_MAX = 1.5
        self.BRIGHTNESS_FACTOR_MIN = 0.5

        self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
      
        self.imageLabel.move(40,0)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(True)
        self.setCentralWidget(self.scrollArea)
    
        self.setMouseTracking(True)
        
        self.label = QLabel(self)
        self.label.resize(200, 40)
       
        self.label1 = QLabel(self)
        self.label1.setMinimumSize(100, 100)
        self.label2 = QLabel(self)
        self.label2.setMinimumSize(100, 100)
        
        self.label.setStyleSheet("QLabel {background-color: gray;}")
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)        
        
        self.label_RGB = QLabel(self)
        self.label_RGB.setText('')
        
        self.gr_RGB = QGroupBox('Colours')
        self.gr_RGB.setCheckable(False)
        self.gr_RGB.setMinimumSize(200,150)
        self.vbox_gr_RGB = QVBoxLayout()
        self.gr_RGB.setLayout(self.vbox_gr_RGB)
        self.vbox_gr_RGB.addWidget(self.label_RGB)
        
        self.dockwidget = QDockWidget('Cvet Dock',self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.setWidget(self.gr_RGB)
        
        self.gr_eff = QGroupBox('Paletter')
        self.gr_eff.setCheckable(False)
        self.vbox_eff = QVBoxLayout()
        self.gr_eff.setLayout(self.vbox_eff)
        self.vbox_eff.addWidget(self.label1,0)
        self.vbox_eff.addWidget(self.label2,1)
        
        self.dockwidget1 = QDockWidget('Cvet Dock',self)
        self.dockwidget1.setWidget(self.gr_eff)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget1)
        
        self.createActions()
        self.createMenus()
        self.move(300,150)
        
        
        
    def get_dominant_color(self,image, k=4, image_processing_size = (25,25)):
        """
        takes an image as input
        returns the dominant color of the image as a list
        """
        #resize image if new dims provided
        if image_processing_size is not None:
            image = np.array(image)
            image = cv2.resize(image, image_processing_size, 
                               interpolation = cv2.INTER_AREA)
    
        #reshape the image to be a list of pixels
        image = np.array(image)
        image = image.reshape((image.shape[0] * image.shape[1], 3))

        #cluster and assign labels to the pixels 
        clt = KMeans(n_clusters = k)
        labels = clt.fit_predict(image)

        #count labels to find most popular
        label_counts = Counter(labels)

        #subset out most popular centroid
        dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]
        dominant_color = np.around(dominant_color)
        dominant_color = dominant_color.astype(int)

        return list(dominant_color)    
        
        
        
        

    def open(self):
        options = QFileDialog.Options()
        # fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        fileName, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if fileName:
            self.image = QImage(fileName)
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            self.image.save(buffer, "PNG")
            pil_im = Image.open(io.BytesIO(buffer.data()))
            self.dominant_color = self.get_dominant_color(pil_im, 3, (25,25))
            print(self.dominant_color)
            self.label2.setStyleSheet("QLabel {background-color:rgb(%s , %s , %s)}" % (self.dominant_color[0],
                                                                                       self.dominant_color[1],
                                                                                       self.dominant_color[2]))
            
            #self.pil_im.show()
            if self.image.isNull():
                QMessageBox.information(self, "Image Viewer", "Cannot load %s." % fileName)
                return

            self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
            self.scaleFactor = 1.0

            self.scrollArea.setVisible(True)
            self.printAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.updateActions()
        
            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()
        
        


    def about(self):
        QMessageBox.about(self, "LOREM IPSUM HALELLUJAH")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False, checkable=True, shortcut="Ctrl+F",
                                      triggered=self.fitToWindow)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))
        
    def get_pixel_colour(self , i_x, i_y):
        import PIL.ImageGrab
        return PIL.ImageGrab.grab().load()[i_x, i_y]
 
    def mouseMoveEvent(self, event):
        x , y = GetCursorPos()
        
        self.label.setText(str(GetCursorPos()))
        RGB = self.get_pixel_colour(x,y)
        HSV = colorsys.rgb_to_hsv(RGB[0], RGB[1], RGB[2])
        
        def rgb_to_hex(rgb):
            return '%02x%02x%02x' % (rgb[0],rgb[1],rgb[2])
    
        self.color = '{:02x}{:02x}{:02x}'.format( RGB[0], RGB[1] , RGB[2] )
        print (self.color)
        self.label1.setStyleSheet("QLabel {background-color:rgb(%s , %s , %s)}" % RGB)
       
        self.label_RGB.setText(f"""
        Coordinates:
        ({x},{y})

        RGB COLOURS:
        RED: {RGB[0]}
        BLUE: {RGB[1]} 
        GREEN: {RGB[2]}
                               
        HSV COLOURS:
        HUE:{HSV[0]}
        SAT:{HSV[1]}
        VAL:{HSV[2]}
                               """)
      
        
if __name__ == '__main__':

    app = QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())