import os
import sys
import hashlib
import numpy as np

from PyQt6 import QtCore
from PyQt6.QtGui import QColor, QImage, QPixmap, qGray, qPixelFormatGrayscale, qRgba64
from PyQt6.QtCore import QByteArray, QSize
from PyQt6.QtWidgets import (
    QApplication,QFileDialog,QHBoxLayout,QMainWindow,
    QPushButton,QSpinBox,QVBoxLayout,QLabel,QWidget,
)
from PIL import Image
from PIL import ImageQt

import logic


class ButtonsWidget(QWidget):
    __minNum = 0
    __maxNum = 8 * 4 - 1

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.settle()

    def settle(self):
        layout = QVBoxLayout(self)

        self.attackImageButton = QPushButton(parent=self, text="Атака")
        self.selectImageButton = QPushButton(parent=self, text="Выбрать изображение")
        self.scaleImageButton = QPushButton(parent=self, text="Масштабирование изображения")
        self.hideMessageButton = QPushButton(parent=self, text="Скрыть сообщение")
        self.extractMessageButton = QPushButton(parent=self, text="Извлечь сообщение")
        self.testAlgorithmButton = QPushButton(parent=self, text="Тест алгоритма")

        self.bitSpinbox = QSpinBox(self)
        self.bitSpinbox.setMinimum(self.__minNum)
        self.bitSpinbox.setMaximum(self.__maxNum)

        self.benchmarkButton = QPushButton(parent=self, text="Бенчмарк")
        self.saveImageButton = QPushButton(parent=self, text="Сохранить изображение")

        layout.addWidget(self.selectImageButton)
        layout.addWidget(self.bitSpinbox)
        layout.addWidget(self.scaleImageButton)
        layout.addWidget(self.attackImageButton)
        layout.addWidget(self.hideMessageButton)
        layout.addWidget(self.extractMessageButton)
        layout.addWidget(self.testAlgorithmButton)
        layout.addWidget(self.benchmarkButton)
        layout.addWidget(self.saveImageButton)
        layout.addStretch()


class ImageWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(500, 500)
        self.settle()

    def setImage(self, image: Image.Image):
        self.__image = image
        self.__label.setPixmap(ImageQt.toqpixmap(image))

    def getImage(self) -> Image.Image:
        return self.__image

    def settle(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.__label = QLabel(self)
        layout.addWidget(self.__label)


class MainWindow(QMainWindow):
    __TITLE: str = "Лабораторная №4"

    def __init__(self):
        super().__init__()
        self.prepareWindow()
        self.settle()

    def prepareWindow(self):
        self.setWindowTitle(self.__TITLE)


    def selectImage(self):
        self.__inputImagePath = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выбрать",
            filter="BMP (*.bmp);; PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)",
        )[0]
        if len(self.__inputImagePath) > 0:
            self.__imageBefWidget.setImage(Image.open(self.__inputImagePath))

    def scaleImage(self):
        self.__imageAfWidget.setImage(logic.scaleImage(self.__imageBefWidget.getImage()))

    def injectMessage(self, image: Image.Image, messageBits: tuple) -> Image.Image:
        return logic.injectMessage(image, messageBits)[0]

    def hideMessage(self):
        message = "world.execute(me)" * 2
        messageBits = "".join(format(i, "08b") for i in bytearray(message, encoding="utf-8"))
        messageBits = tuple(1 if i == "1" else 0 for i in messageBits)
        self.messageSize = len(messageBits)

        img = self.__imageBefWidget.getImage()

        img = self.injectMessage(img, messageBits)
        print(f"Внедрён {messageBits}")
        # print(f"Injected {messageBits}")

        self.__imageAfWidget.setImage(img)

    def extractMessage(self, image: Image.Image, messageLen: int) -> tuple:
        return logic.extractMessage(image, messageLen)

    def extractMessageInImage(self):
        messageBits = self.extractMessage(self.__imageBefWidget.getImage(), self.messageSize)
        messageHash = hashlib.md5("".join(map(str, messageBits)).encode()).hexdigest()
        print(f"Извлечён {messageBits}")
        # print(f"Extracted {messageBits}")

    def attackImage(self):
        self.__imageAfWidget.setImage(
            logic.attackImage(
                self.__imageBefWidget.getImage(),
                self.__buttonsWidget.bitSpinbox.value(),))

    def testAlgorithm(self):
        messageBits = tuple(np.random.randint(0, 2) for _ in range(np.random.randint(0, 256)))
        messageHash = hashlib.md5("".join(map(str, messageBits)).encode()).hexdigest()
        imgOut = self.injectMessage(self.__imageBefWidget.getImage(), messageBits)
        self.__imageAfWidget.setImage(imgOut)

        messageOutBits = self.extractMessage(self.__imageAfWidget.getImage(), len(messageBits))
        messageOutHash = hashlib.md5("".join(map(str, messageOutBits)).encode()).hexdigest()

        print(
            f"""
Хеш сообщение до внедрения: {messageHash}
Хеш сообщение после внедрения: {messageOutHash}
Сообщения одинаковы? {"Да" if messageBits == messageOutBits else "Нет"}
"""
        )

    def benchmark(self):
        kbs = [2**x for x in range(9)]
        dataCapacity = []
        dataPSNR = []
        capacity = logic.getCapacity(self.__imageBefWidget.getImage())
        print(f"Емкость={capacity[0]}; Среднее={capacity[1]}")
        for kb in kbs:
            messageBits = tuple(np.random.randint(0, 2) for _ in range(1024 * 8 * kb))
            imgAfter = self.injectMessage(self.__imageBefWidget.getImage(), messageBits)
            # capacity = (
            #     len(self.extractMessage(logic.TEMP_IMAGE_PATH, len(messageBits)))
            #     / len(messageBits)
            #     * 100
            # )
            psnr = logic.getPSNR(self.__imageBefWidget.getImage(), imgAfter)
            # dataCapacity.append(capacity)
            dataPSNR.append(psnr)
            print(f"{kb}KB:")
            print(f"    PSNR={psnr}\n")
        # logic.drawPlot(kbs, dataCapacity, "KB", "Capacity, %")
        logic.drawPlot(kbs, dataPSNR, "KB", "PSNR")

    def saveImage(self):
        selection = QFileDialog.getSaveFileName(parent=self, caption="Сохранить как", filter="BMP (*.bmp);;PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)")
        if selection[0] is not None:
            self.__imageAfWidget.getImage().save(selection[0], format="bmp")

    def settle(self):
        mainLayout = QHBoxLayout(self)
        mainLayoutContainer = QWidget(self)
        mainLayoutContainer.setLayout(mainLayout)

        self.__imageBefWidget = ImageWidget(self)
        self.__buttonsWidget = ButtonsWidget(self)
        self.__imageAfWidget = ImageWidget(self)

        self.__buttonsWidget.selectImageButton.clicked.connect(self.selectImage)
        self.__buttonsWidget.scaleImageButton.clicked.connect(self.scaleImage)
        self.__buttonsWidget.attackImageButton.clicked.connect(self.attackImage)
        self.__buttonsWidget.saveImageButton.clicked.connect(self.saveImage)
        self.__buttonsWidget.hideMessageButton.clicked.connect(self.hideMessage)
        self.__buttonsWidget.extractMessageButton.clicked.connect(self.extractMessageInImage)
        self.__buttonsWidget.testAlgorithmButton.clicked.connect(self.testAlgorithm)
        self.__buttonsWidget.benchmarkButton.clicked.connect(self.benchmark)

        mainLayout.addWidget(self.__imageBefWidget)
        mainLayout.addWidget(self.__buttonsWidget)
        mainLayout.addWidget(self.__imageAfWidget)

        self.setCentralWidget(mainLayoutContainer)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
