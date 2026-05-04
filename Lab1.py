import sys

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (
	QVBoxLayout,QLabel,QWidget,
    QApplication,QFileDialog,QHBoxLayout,
    QMainWindow,QPushButton,QSpinBox
)

class Buttons(QWidget):
    __minNum = 0
    __maxNum = 8 * 4 - 1

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.settle()

    def settle(self):
        layout = QVBoxLayout(self)

        self.attackImageButton = QPushButton(parent=self, text="Атака")
        self.selectImageButton = QPushButton(parent=self, text="Выбрать изображение")
        self.hideMessageButton = QPushButton(parent=self, text="Скрыть сообщение")
        self.saveImage = QPushButton(parent=self, text="Сохранить как")
        self.bitSpinbox = QSpinBox(self)
        self.bitSpinbox.setMinimum(self.__minNum)
        self.bitSpinbox.setMaximum(self.__maxNum)

        layout.addWidget(self.selectImageButton)
        layout.addWidget(self.bitSpinbox)
        layout.addWidget(self.attackImageButton)
        layout.addWidget(self.hideMessageButton)
        layout.addWidget(self.saveImage)
        layout.addStretch()


class ImageA(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(500, 500)
        self.settle()

    def setPixmap(self, pixmap: QPixmap):
        self.__label.setPixmap(pixmap)

    def getPixmap(self) -> QPixmap:
        return self.__label.pixmap()

    def settle(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.__label = QLabel(self)
        layout.addWidget(self.__label)

class ImageB(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(500, 500)
        self.settle()

    def setPixmap(self, pixmap: QPixmap):
        self.__label.setPixmap(pixmap)

    def getPixmap(self) -> QPixmap:
        return self.__label.pixmap()

    def settle(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.__label = QLabel(self)
        layout.addWidget(self.__label)

class MainWindow(QMainWindow):
    __Title: str = "Лабораторная №1"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.__Title)
        self.settle()

    def selectImage(self):
        self.__inputImagePath = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выбрать",
            filter="BMP (*.bmp);;PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)",
        )[0]
        if self.__inputImagePath is not None:
            self.__imageBefWidget.setPixmap(QPixmap(self.__inputImagePath))

    def hideMessage(self):
        message = "AlbertKuznetsovLinkoln" * 150 
        messageBits = "".join(format(i, "08b") for i in bytearray(message, encoding="utf-8"))
        messageBits = tuple(1 if i == "1" else 0 for i in messageBits)

        img = self.__imageBefWidget.getPixmap().toImage()
        index = 0
        for x in range(img.width()):
            for y in range(img.height()):
                if index >= len(messageBits):
                    break
                pixel = img.pixelColor(x, y)
                pixel.setRgba(img.pixelColor(x, y).rgba() & ~(1 << self.__buttonsWidget.bitSpinbox.value()) | (messageBits[index] << self.__buttonsWidget.bitSpinbox.value()))
                img.setPixelColor(x, y, pixel)
                index += 1
        self.__imageAfWidget.setPixmap(QPixmap.fromImage(img))

    def attackImage(self):
        img = self.__imageBefWidget.getPixmap().toImage()
        for x in range(img.width()):
            for y in range(img.height()):
                img.setPixelColor(x,y,0xFFFFFFFF * bool(img.pixelColor(x, y).rgba() & (1 << self.__buttonsWidget.bitSpinbox.value())))
        self.__imageAfWidget.setPixmap(QPixmap.fromImage(img))

    def saveImage(self):
        selection = QFileDialog.getSaveFileName(
            parent=self, caption="Сохранить как", filter="BMP (*.bmp);;PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)"
        )
        if selection[0] is not None:
            self.__imageAfWidget.getPixmap().save(selection[0], format="bmp")
 
    def settle(self):
        mainLayout = QHBoxLayout(self)
        mainLayoutContainer = QWidget(self)
        mainLayoutContainer.setLayout(mainLayout)

        self.__imageBefWidget = ImageB(self)
        self.__buttonsWidget = Buttons(self)
        self.__imageAfWidget = ImageA(self)

        self.__buttonsWidget.selectImageButton.clicked.connect(self.selectImage)
        self.__buttonsWidget.attackImageButton.clicked.connect(self.attackImage)
        self.__buttonsWidget.saveImage.clicked.connect(self.saveImage)
        self.__buttonsWidget.hideMessageButton.clicked.connect(self.hideMessage)

        mainLayout.addWidget(self.__imageBefWidget)
        mainLayout.addWidget(self.__buttonsWidget)
        mainLayout.addWidget(self.__imageAfWidget)

        self.setCentralWidget(mainLayoutContainer)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
