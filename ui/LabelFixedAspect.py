import PyQt6.QtWidgets
import PyQt6.QtGui
import PyQt6.QtCore


class LabelFixedAspect(PyQt6.QtWidgets.QLabel):
    def __init__(self, parent: PyQt6.QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(1, 1)

    def setPixmap(self, a0: PyQt6.QtGui.QPixmap) -> None:
        self.__pixmap = a0
        super().setPixmap(self.scaledPixmap())

    def pixmap(self) -> PyQt6.QtGui.QPixmap:
        return self.__pixmap

    def sizeHint(self) -> PyQt6.QtCore.QSize:
        return PyQt6.QtCore.QSize(self.width(), self.heightForWidth(self.width()))

    def heightForWidth(self, a0: int) -> int:
        if self.__pixmap is None:
            return self.height()
        return int(self.__pixmap.height() * a0 / self.__pixmap.width())

    def scaledPixmap(self) -> PyQt6.QtGui.QPixmap:
        return self.__pixmap.scaled(
            self.size(),
            PyQt6.QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            PyQt6.QtCore.Qt.TransformationMode.SmoothTransformation,
        )

    def resizeEvent(self, a0: PyQt6.QtGui.QResizeEvent | None) -> None:
        if self.__pixmap is not None:
            return super().setPixmap(self.scaledPixmap())
