import control

from PyQt6 import QtCore, QtGui, QtWidgets

from PIL import Image
from PIL import ImageQt

import datetime
import re
import pathlib
import itertools
import multiprocessing
import typing

UPPER_LAYOUT_HEIGHT = 300
POOL_SIZE = 4


class LabelFixedAspect(QtWidgets.QLabel):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(1, 1)

    def setPixmap(self, a0: QtGui.QPixmap) -> None:
        self.__pixmap = a0
        super().setPixmap(self.scaledPixmap())

    def pixmap(self) -> QtGui.QPixmap:
        return self.__pixmap

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(self.width(), self.heightForWidth(self.width()))

    def heightForWidth(self, a0: int) -> int:
        if self.__pixmap is None:
            return self.height()
        return int(self.__pixmap.height() * a0 / self.__pixmap.width())

    def scaledPixmap(self) -> QtGui.QPixmap:
        return self.__pixmap.scaled(
            self.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

    def resizeEvent(self, a0: QtGui.QResizeEvent | None) -> None:
        if self.__pixmap is not None:
            return super().setPixmap(self.scaledPixmap())


class ImagesWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(300, UPPER_LAYOUT_HEIGHT)
        self.populate()
        self.__images: list[Image.Image] = []

    def __remove_images(self):
        for index in reversed(range(self.__scrollable_layout.count())):
            item = self.__scrollable_layout.itemAt(index)
            if item is not None and item.widget() is not None:
                item.widget().setParent(None)

    @property
    def images(self) -> list[Image.Image]:
        return self.__images

    @images.setter
    def images(self, value: list[Image.Image]):
        self.__images = value
        self.__remove_images()
        self.__scrollable_layout.addStretch()

        for image in self.__images:
            label = LabelFixedAspect(self)
            # ImageQt.toqpixmap(image)
            label.setPixmap(ImageQt.toqpixmap(image))
            # label.setSizePolicy(
            #     QtWidgets.QSizePolicy.Policy.Minimum,
            #     QtWidgets.QSizePolicy.Policy.Minimum,
            # )

            self.__scrollable_layout.addWidget(label)

    def get_images(self) -> list[Image.Image]:
        return []

    def populate(self):
        self.__scrollable_layout = QtWidgets.QVBoxLayout(self)
        self.__scrollable_layout.setStretch

        self.__scroll_area_content = QtWidgets.QWidget(self)
        self.__scroll_area_content.setLayout(self.__scrollable_layout)
        self.__scroll_area_content.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )

        self.__scroll_area = QtWidgets.QScrollArea(self)
        self.__scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setWidget(self.__scroll_area_content)

        self.__main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.__main_layout)
        self.__main_layout.addWidget(self.__scroll_area)


class ButtonsWidget(QtWidgets.QWidget):
    __MIN_BIT_INDEX = 0
    __MAX_BIT_INDEX = 7

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumSize(150, UPPER_LAYOUT_HEIGHT)
        self.populate()

    def populate(self):
        self.__main_layout = QtWidgets.QVBoxLayout(self)

        self.open_images_button = QtWidgets.QPushButton(text="Выбрать изображение", parent=self)

        self.save_results_button = QtWidgets.QPushButton(
            text="Сохранить результат", parent=self
        )

        self.bit_spinbox = QtWidgets.QSpinBox(self)
        self.bit_spinbox.setMinimum(self.__MIN_BIT_INDEX)
        self.bit_spinbox.setMaximum(self.__MAX_BIT_INDEX)
        self.bit_spinbox.setToolTip("Bit index for attack")

        self.__aump_spinbox_container = QtWidgets.QWidget(self)
        self.__aump_spinbox_layout = QtWidgets.QHBoxLayout(
            self.__aump_spinbox_container
        )
        self.aump_block_size_spinbox = QtWidgets.QSpinBox(self)
        self.aump_block_size_spinbox.setToolTip("AUMP block size")
        self.aump_block_size_spinbox.setValue(16)
        self.__aump_spinbox_layout.addWidget(self.aump_block_size_spinbox)
        self.aump_parameter_spinbox = QtWidgets.QSpinBox(self)
        self.aump_parameter_spinbox.setToolTip("AUMP parameters")
        self.aump_parameter_spinbox.setValue(5)
        self.__aump_spinbox_layout.addWidget(self.aump_parameter_spinbox)

        self.attack_images_button = QtWidgets.QPushButton(
            text="Атака", parent=self
        )

        self.rs_analyze_image_button = QtWidgets.QPushButton(
            text="RS анализ", parent=self
        )

        self.aump_analyze_image_button = QtWidgets.QPushButton(
            text="AUMP анализ", parent=self
        )

        self.chi2_analyze_image_button = QtWidgets.QPushButton(
            text="Chi2 анализ", parent=self
        )

        self.__main_layout.addStretch()
        self.__main_layout.addWidget(self.open_images_button)
        self.__main_layout.addWidget(self.save_results_button)
        self.__main_layout.addWidget(self.bit_spinbox)
        self.__main_layout.addWidget(self.attack_images_button)
        self.__main_layout.addWidget(self.rs_analyze_image_button)
        self.__main_layout.addWidget(self.__aump_spinbox_container)
        self.__main_layout.addWidget(self.aump_analyze_image_button)
        self.__main_layout.addWidget(self.chi2_analyze_image_button)

        self.__main_layout.addStretch()


class Analyser(QtCore.QThread):
    finished = QtCore.pyqtSignal(typing.Any)

    def __init__(self, func, data, *args, **kwargs):
        super().__init__()
        self.__func = func
        self.__data = data
        self.__args = args
        self.__kwargs = kwargs

    def run(self):
        out = []
        for x in self.__data:
            out.append(self.__func(*self.__args, **self.__kwargs))
        self.finished.emit(out)


class MainWindow(QtWidgets.QMainWindow):
    __WINDOW_TITLE = "Лабораторная №5"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.__WINDOW_TITLE)
        self.populate()
        self.connect_buttons()

    def show_progress_indicator(self):
        self.progress_indicator = QtWidgets.QProgressDialog(self)
        self.progress_indicator.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.progress_indicator.setRange(0, 0)
        self.progress_indicator.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.progress_indicator.show()

    def hide_progress_indicator(self):
        self.progress_indicator.close()

    def connect_buttons(self):
        def open_images_event():
            paths = QtWidgets.QFileDialog.getOpenFileNames(
                parent=self, caption="Выбрать", filter="BMP (*.bmp)"
            )[0]
            if paths is not None:
                self.__images_before_widget.images = [Image.open(x) for x in paths]

        def save_results_event():
            folder_path = pathlib.Path(
                f"./out/{
                    re.sub(
                        ' ', '_', re.sub('[:\\.]', '-', str(datetime.datetime.now()))
                    )
                }"
            )
            folder_path.mkdir(parents=True, exist_ok=True)
            if self.__save_source_images_action.isChecked():
                for index, image in enumerate(self.__images_before_widget.images):
                    image.save(folder_path / f"source_{index}.bmp")
            if self.__save_result_images_action.isChecked():
                for index, image in enumerate(self.__images_after_widget.images):
                    image.save(folder_path / f"result_{index}.bmp")
            if self.__save_log_action.isChecked():
                (folder_path / "log.txt").write_text(
                    self.__result_text_browser.toPlainText()
                )
            QtWidgets.QToolTip.showText(
                QtGui.QCursor.pos(),
                f"Saved at {folder_path.absolute().as_posix()}",
            )

        def attack_images_event():
            with multiprocessing.Pool(POOL_SIZE) as pool:
                self.__images_after_widget.images = pool.starmap(
                    control.Attacker.attack_image,
                    zip(
                        self.__images_before_widget.images,
                        itertools.repeat(self.__buttons_widget.bit_spinbox.value()),
                    ),
                )

        def rs_analyze_image_event():
            rs = control.RSAnalysis(2, 2)
            result_text = f"{datetime.datetime.now()}: Starting RS analysis.\n"

            with multiprocessing.Pool(POOL_SIZE) as pool:
                results = pool.map(rs.analyze, self.__images_before_widget.images)

            for index, result in enumerate(results):
                result_text += (
                    f"\tImage {index}: {'contains' if result else "doesn't contain"}\n"
                )

            self.__result_text_browser.append(result_text)

        def aump_analyze_image_event():
            result_text = f"{datetime.datetime.now()}: Starting AUMP analysis.\n"

            with multiprocessing.Pool(POOL_SIZE) as pool:
                results = pool.starmap(
                    control.AUMP.analyze,
                    zip(
                        self.__images_before_widget.images,
                        itertools.repeat(
                            self.__buttons_widget.aump_block_size_spinbox.value()
                        ),
                        itertools.repeat(
                            self.__buttons_widget.aump_parameter_spinbox.value()
                        ),
                    ),
                )

            for index, result in enumerate(results):
                result_text += (
                    f"\tImage {index}: {'contains' if result else "doesn't contain"}\n"
                )

            self.__result_text_browser.append(result_text)

        def chi2_analyze_image_event():
            result_text = f"{datetime.datetime.now()}: Starting chi2 analysis.\n"

            with multiprocessing.Pool(POOL_SIZE) as pool:
                results = pool.map(
                    control.Chi2.analyze, self.__images_before_widget.images
                )

            for index, result in enumerate(results):
                result_text += (
                    # f"\tImage {index}: {result}\n"
                    f"\tImage {index}: {'contains' if result else "doesn't contain"}\n"
                )

            self.__result_text_browser.append(result_text)

        self.__buttons_widget.open_images_button.clicked.connect(open_images_event)
        self.__buttons_widget.save_results_button.clicked.connect(save_results_event)
        self.__buttons_widget.attack_images_button.clicked.connect(attack_images_event)
        self.__buttons_widget.rs_analyze_image_button.clicked.connect(
            rs_analyze_image_event
        )
        self.__buttons_widget.aump_analyze_image_button.clicked.connect(
            aump_analyze_image_event
        )
        self.__buttons_widget.chi2_analyze_image_button.clicked.connect(
            chi2_analyze_image_event
        )

    def populate(self):
        self.__central_widget = QtWidgets.QWidget(self)
        self.__main_layout = QtWidgets.QVBoxLayout(self.__central_widget)
        self.__central_widget.setLayout(self.__main_layout)
        self.setCentralWidget(self.__central_widget)

        self.__upper_layout_widget = QtWidgets.QWidget(self)
        self.__upper_layout = QtWidgets.QHBoxLayout(self.__upper_layout_widget)
        self.__upper_layout_widget.setLayout(self.__upper_layout)
        self.__main_layout.addWidget(self.__upper_layout_widget)

        self.__images_before_widget = ImagesWidget(self.__upper_layout_widget)
        self.__buttons_widget = ButtonsWidget(self.__upper_layout_widget)
        self.__images_after_widget = ImagesWidget(self.__upper_layout_widget)
        self.__upper_layout.addWidget(self.__images_before_widget)
        self.__upper_layout.addWidget(self.__buttons_widget)
        self.__upper_layout.addWidget(self.__images_after_widget)

        self.__result_text_browser = QtWidgets.QTextBrowser(self.__central_widget)
        self.__main_layout.addWidget(self.__result_text_browser)

        self.__menu_bar = QtWidgets.QMenuBar(self)
        self.__settings_menu = QtWidgets.QMenu("Настройки", self.__menu_bar)
        self.__menu_bar.addMenu(self.__settings_menu)

        self.__save_source_images_action = QtWidgets.QWidgetAction(self)
        self.__save_source_images_action.setCheckable(True)
        self.__save_source_images_action.setChecked(True)
        self.__save_source_images_action.setText("Сохранить исходные изображения")
        self.__settings_menu.addAction(self.__save_source_images_action)

        self.__save_result_images_action = QtWidgets.QWidgetAction(self)
        self.__save_result_images_action.setCheckable(True)
        self.__save_result_images_action.setChecked(True)
        self.__save_result_images_action.setText("Сохранить изображения результатов")
        self.__settings_menu.addAction(self.__save_result_images_action)

        self.__save_log_action = QtWidgets.QWidgetAction(self)
        self.__save_log_action.setCheckable(True)
        self.__save_log_action.setChecked(True)
        self.__save_log_action.setText("Сохранить log")
        self.__settings_menu.addAction(self.__save_log_action)

        self.setMenuBar(self.__menu_bar)
