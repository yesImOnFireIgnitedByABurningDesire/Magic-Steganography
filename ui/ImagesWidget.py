import PIL.Image
import PIL.ImageQt

import PyQt6.QtWidgets
import PyQt6.QtGui
import PyQt6.QtCore

from ui.LabelFixedAspect import LabelFixedAspect


class ImagesWidget(PyQt6.QtWidgets.QWidget):
    __UPPER_LAYOUT_HEIGHT = 300

    def __init__(self, parent: PyQt6.QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(300, self.__UPPER_LAYOUT_HEIGHT)
        self.populate()
        self.__images: list[PIL.Image.Image] = []

    def __remove_images(self):
        for index in reversed(range(self.__scrollable_layout.count())):
            item = self.__scrollable_layout.itemAt(index)
            if item is not None and item.widget() is not None:
                item.widget().setParent(None)

    @property
    def images(self) -> list[PIL.Image.Image]:
        return self.__images

    @images.setter
    def images(self, value: list[PIL.Image.Image]):
        self.__images = value
        self.__remove_images()
        self.__scrollable_layout.addStretch()

        for image in self.__images:
            label = LabelFixedAspect(self)
            label.setPixmap(PIL.ImageQt.toqpixmap(image))
            # label.setSizePolicy(
            #     PyQt6.QtWidgets.QSizePolicy.Policy.Minimum,
            #     PyQt6.QtWidgets.QSizePolicy.Policy.Minimum,
            # )

            self.__scrollable_layout.addWidget(label)

    def populate(self):
        self.__scrollable_layout = PyQt6.QtWidgets.QVBoxLayout(self)
        self.__scrollable_layout.setStretch

        self.__scroll_area_content = PyQt6.QtWidgets.QWidget(self)
        self.__scroll_area_content.setLayout(self.__scrollable_layout)
        self.__scroll_area_content.setSizePolicy(
            PyQt6.QtWidgets.QSizePolicy.Policy.Ignored,
            PyQt6.QtWidgets.QSizePolicy.Policy.Minimum,
        )

        self.__scroll_area = PyQt6.QtWidgets.QScrollArea(self)
        self.__scroll_area.setHorizontalScrollBarPolicy(
            PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__scroll_area.setVerticalScrollBarPolicy(
            PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setWidget(self.__scroll_area_content)

        self.__main_layout = PyQt6.QtWidgets.QVBoxLayout(self)
        self.setLayout(self.__main_layout)
        self.__main_layout.addWidget(self.__scroll_area)
