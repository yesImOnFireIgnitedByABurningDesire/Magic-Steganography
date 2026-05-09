import os
import sys

from PyQt6 import QtCore
from PyQt6.QtGui import QColor, QImage, QPixmap, qGray, qPixelFormatGrayscale, qRgba64
from PyQt6.QtCore import QByteArray, QSize
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QLabel,
    QWidget,
)

import numpy as np

import logic


class ButtonsWidget(QWidget):
    __minNum = 0
    __maxNum = 8 * 4 - 1

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.settle()

    def settle(self):
        layout = QVBoxLayout(self)

        self.attackImage_button = QPushButton(parent=self, text="Атака")
        self.selectImageButton = QPushButton(parent=self, text="Выбрать изображение")
        self.hideMessageButton = QPushButton(parent=self, text="Скрыть сообщение")
        self.extractMessageButton = QPushButton(parent=self, text="Извлечь сообщение")
        self.testAlgorithmButton = QPushButton(parent=self, text="Тест алгоритма")

        self.bitSpinbox = QSpinBox(self)
        self.bitSpinbox.setMinimum(self.__minNum)
        self.bitSpinbox.setMaximum(self.__maxNum)

        self.benchmarkButton = QPushButton(parent=self, text="Бенчмарк")
        self.saveImageButton = QPushButton(parent=self, text="Сохранить как")

        layout.addWidget(self.selectImageButton)
        layout.addWidget(self.bitSpinbox)
        layout.addWidget(self.attackImage_button)
        layout.addWidget(self.hideMessageButton)
        layout.addWidget(self.extractMessageButton)
        layout.addWidget(self.testAlgorithmButton)
        layout.addWidget(self.benchmarkButton)
        layout.addWidget(self.saveImageButton)
        layout.addStretch()


class ImageW(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(500, 500)
        self.settle()

    def setImage(self, image: QImage):
        self.__label.setPixmap(QPixmap.fromImage(image.convertToFormat(QImage.Format.Format_Grayscale8)))

    def getImage(self) -> QImage:
        return (
            self.__label.pixmap()
            .toImage()
            .convertToFormat(QImage.Format.Format_Grayscale8)
        )

    def settle(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.__label = QLabel(self)
        layout.addWidget(self.__label)


class MainWindow(QMainWindow):
    __TITLE: str = "Лабораторная №3"

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
        if self.__inputImagePath is not None:
            self.__imageBefWidget.setImage(QImage(self.__inputImagePath))

    def injectMessage(self, imagePath: str, messageBits: tuple) -> QImage:
        logic.injectMessage(imagePath, messageBits)
        return QImage(logic.TEMP_IMAGE_PATH )

    def hideMessage(self):
        message = "IGotThatSummertimeSummertimeSadness" * 25
        messageBits = "".join(
            format(i, "08b") for i in bytearray(message, encoding="utf-8")
        )
        messageBits = tuple(1 if i == "1" else 0 for i in messageBits)
        self.messageSize = len(messageBits)

        img = self.__imageBefWidget.getImage()

        img = self.injectMessage(self.__inputImagePath, messageBits)
        print(f"Внедрён {hex(hash(messageBits))}")

        self.__imageАfWidget.setImage(img)

    def extractMessage(self, imagePath: str, messageLen: int) -> tuple:
        return logic.extractMessage(imagePath, messageLen)

    def extractMessageInImage(self):
        messageBits = self.extractMessage(self.__inputImagePath, self.messageSize)
        print(f"Извлечён {hex(hash(messageBits))}")

    def attackImage(self):
        logic.attackImage(self.__inputImagePath, self.__buttonsWidget.bitSpinbox.value())
        self.__imageАfWidget.setImage(QImage(logic.TEMP_IMAGE_PATH ))

    def testAlgorithm(self):
        messageBits = tuple(np.random.randint(0, 2) for _ in range(256))
        message_hash = hex(hash(messageBits))

        img_out = self.injectMessage(self.__inputImagePath, messageBits)
        self.__imageАfWidget.setImage(img_out)

        messageOutBits = self.extractMessage(
            logic.TEMP_IMAGE_PATH , len(messageBits))
        messageOutHash = hex(hash(messageOutBits))

        print(
            f"""
Хеш сообщение до внедрения: {message_hash}
Хеш сообщение после внедрения: {messageOutHash}
Сообщения одинаковы? {"Да" if messageBits == messageOutBits else "Нет"}
"""
        )

    def benchmark(self):
        kbs = [2**x for x in range(10)]
        dataCapacity = []
        dataPSNR = []
        for kb in kbs:
            messageBits = tuple(np.random.randint(0, 2) for _ in range(1024 * 8 * kb))
            self.injectMessage(self.__inputImagePath, messageBits)
            capacity = (len(self.extractMessage(logic.TEMP_IMAGE_PATH , len(messageBits))) / len(messageBits) * 100)
            psnr = logic.getPSNR(self.__inputImagePath, logic.TEMP_IMAGE_PATH )
            dataCapacity.append(capacity)
            dataPSNR.append(psnr)
            print(f"{kb}KB:")
            print(f"    Емкость={capacity}%")
            print(f"    PSNR={psnr}\n")
        logic.drawPlot(kbs, dataCapacity, "KB", "Емкость, %")
        logic.drawPlot(kbs, dataPSNR, "KB", "PSNR")

    def saveImage(self):
        selection = QFileDialog.getSaveFileName(parent=self, caption="Сохранить как", filter="BMP (*.bmp);;PGM (*.pgm);; PNG (*.png);; JPEG (*.jpg)")
        if selection[0] is not None:
            logic.copyImage(logic.TEMP_IMAGE_PATH , selection[0], format="bmp")

    def settle(self):
        mainLayout = QHBoxLayout(self)
        mainLayoutContainer = QWidget(self)
        mainLayoutContainer.setLayout(mainLayout)

        self.__imageBefWidget = ImageW(self)
        self.__buttonsWidget = ButtonsWidget(self)
        self.__imageАfWidget = ImageW(self)

        self.__buttonsWidget.selectImageButton.clicked.connect(self.selectImage)
        self.__buttonsWidget.attackImage_button.clicked.connect(self.attackImage)
        self.__buttonsWidget.saveImageButton.clicked.connect(self.saveImage)
        self.__buttonsWidget.hideMessageButton.clicked.connect(self.hideMessage)
        self.__buttonsWidget.extractMessageButton.clicked.connect(self.extractMessageInImage)
        self.__buttonsWidget.testAlgorithmButton.clicked.connect(self.testAlgorithm)
        self.__buttonsWidget.benchmarkButton.clicked.connect(self.benchmark)

        mainLayout.addWidget(self.__imageBefWidget)
        mainLayout.addWidget(self.__buttonsWidget)
        mainLayout.addWidget(self.__imageАfWidget)

        self.setCentralWidget(mainLayoutContainer)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

