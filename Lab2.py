import sys
import numpy as np

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (   
    QPushButton,QVBoxLayout,QApplication,
    QFileDialog,QHBoxLayout,QMainWindow,
    QLabel,QWidget
)

CDB_COEFF = 0.572  # 0.572
CDB_RANGE = 3

BIT_SIZE = 1024
SEED = 0xAAAA

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

class Buttons(QWidget):
    __minNum = 0
    __maxNum = 8 * 4 - 1

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.settle()

    def settle(self):
        layout = QVBoxLayout(self)

        self.getMessageButton = QPushButton(parent=self, text="Получить сообщение")
        self.selectImageButton = QPushButton(parent=self, text="Выбрать изображение")
        self.hideMessageButton = QPushButton(parent=self, text="Скрыть сообщение")
        self.saveImageButton = QPushButton(parent=self, text="Сохранить как")
        self.testCDBButton = QPushButton(parent=self, text="Тест CDB") # what is it?

        layout.addWidget(self.selectImageButton)
        layout.addWidget(self.hideMessageButton)        
        layout.addWidget(self.getMessageButton)
        layout.addWidget(self.testCDBButton)
        layout.addWidget(self.saveImageButton)        
        layout.addStretch()

class MainWindow(QMainWindow):
    __TITLE: str = "Лабораторная №2"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.__TITLE)
        self.settle()

    def selectImage(self):
        self.__inputImagePath = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выбрать",
            filter="BMP (*.bmp);; PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)",
        )[0]
        if self.__inputImagePath is not None:
            self.__imageBefWidget.setPixmap(QPixmap(self.__inputImagePath))

    def CDBInject(self, messageBits: list, img: QImage) -> QImage:
        gen = np.random.RandomState(SEED)
        for bit in messageBits:
            x = gen.randint(0, img.width())
            y = gen.randint(0, img.height())

            pixelColor = img.pixelColor(x, y)
            red = pixelColor.redF()
            green = pixelColor.greenF()
            blue = pixelColor.blueF()
            brightness = 0.299 * red + 0.587 * green + 0.114 * blue
            newBlue = blue + (2 * bit - 1) * brightness * CDB_COEFF
            pixelColor.setBlueF(newBlue)
            img.setPixelColor(x, y, pixelColor)
        return img

    def hideMessage(self):
        messageBits = [np.random.randint(0, 2) for i in range(BIT_SIZE)]
        print(messageBits)
        img = self.__imageBefWidget.getPixmap().toImage()
        img = self.CDBInject(messageBits, img)
        self.__imageAfWidget.setPixmap(QPixmap.fromImage(img))

    def CDBExtract(self, img: QImage) -> list:
        messageBits = []
        gen = np.random.RandomState(SEED)
        for bit_index in range(BIT_SIZE):
            x = gen.randint(0, img.width())
            y = gen.randint(0, img.height())
            xSum = sum(
                img.pixelColor(i, y).blueF()
                for i in range(max(x, 0), min(x + CDB_RANGE, img.width() - 1) + 1))
            ySum = sum(
                img.pixelColor(x, i).blueF()
                for i in range(max(y, 0), min(y + CDB_RANGE, img.height() - 1) + 1))
            predictedBlue = (xSum + ySum - 2 * img.pixelColor(x, y).blueF()) / (
                4 * CDB_RANGE)
            messageBits.append(int(img.pixelColor(x, y).blueF() > predictedBlue))
        return messageBits

    def getMessage(self):
        img = self.__imageBefWidget.getPixmap().toImage()
        messageBits = self.CDBExtract(img)
        print(messageBits)
        self.__imageAfWidget.setPixmap(QPixmap.fromImage(img))

    def saveImage(self):
        selection = QFileDialog.getSaveFileName(
            parent=self, caption="Сохранить как", filter="BMP (*.bmp);;PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)")
        if selection[0] is not None:
            self.__imageAfWidget.getPixmap().save(selection[0], format="bmp")

    def testCDB(self):
        messageBits = [np.random.randint(0, 2) for i in range(BIT_SIZE)]
        img = self.__imageBefWidget.getPixmap().toImage()
        imgAfter = self.CDBInject(messageBits, img)
        self.__imageAfWidget.setPixmap(QPixmap.fromImage(imgAfter))
        messageBitsAfter = self.CDBExtract(imgAfter)
        print("Биты по дефолту:")
        print(f"    {''.join(str(i) for i in messageBits)}")
        print("После изменений:")
        print(f"    {''.join(str(i) for i in messageBitsAfter)}")
        print(f"Относительная погрешность: {sum(not (messageBits[i] == messageBitsAfter[i]) for i in range(BIT_SIZE)) / BIT_SIZE * 100}%")

    def settle(self):
        mainLayout = QHBoxLayout(self)
        mainLayoutContainer = QWidget(self)
        mainLayoutContainer.setLayout(mainLayout)

        self.__imageBefWidget = ImageB(self)
        self.__buttonsWidget = Buttons(self)
        self.__imageAfWidget = ImageA(self)

        self.__buttonsWidget.selectImageButton.clicked.connect(self.selectImage)
        self.__buttonsWidget.getMessageButton.clicked.connect(self.getMessage)
        self.__buttonsWidget.saveImageButton.clicked.connect(self.saveImage)
        self.__buttonsWidget.hideMessageButton.clicked.connect(self.hideMessage)
        self.__buttonsWidget.testCDBButton.clicked.connect(self.testCDB)

        mainLayout.addWidget(self.__imageBefWidget)
        mainLayout.addWidget(self.__buttonsWidget)
        mainLayout.addWidget(self.__imageAfWidget)

        self.setCentralWidget(mainLayoutContainer)


app = QApplication(sys.argv)

window = MainWindow()
window.show()


app.exec()
