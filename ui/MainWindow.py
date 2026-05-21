from ui.ImagesWidget import ImagesWidget
from ui.ButtonsWidget import ButtonsWidget

import control

import PIL.Image
import PIL.ImageQt

import PyQt6.QtWidgets
import PyQt6.QtGui
import PyQt6.QtCore

import multiprocessing
import pathlib
import json
import itertools
from bitarray import bitarray
import bitarray.util as bitutil

import enum


class AnalyseWorker(PyQt6.QtCore.QThread):
    __POOL_SIZE = 5
    __AUMP_KEY = "AUMP"
    __CHI2_KEY = "CHI2"
    __RS_KEY = "RS"
    __RS_FLIPPED_PIXELS_INDEX = 25

    finished = PyQt6.QtCore.pyqtSignal(dict)

    class Methods(enum.Enum):
        LSB_SEQ = 0
        LSB_RAND = 1
        LAB3 = 2
        LAB4 = 3

    def __init__(
        self,
        images: list[PIL.Image.Image],
        method: Methods,
        rs: tuple[int, int],
        aump: tuple[int, int],
    ):
        super().__init__()
        self.__images = images
        self.__processes = None
        self.__canceled = False
        self.__method = method
        self.__rs = rs
        self.__rs_a = control.RSAnalysis(*rs)
        self.__aump = aump

    @staticmethod
    def insert_message(
        image: PIL.Image.Image,
        message: bitarray,
        percent: int,
        method: Methods,
    ):
        if percent > 0:
            match method:
                case AnalyseWorker.Methods.LSB_SEQ:
                    cap = control.LSBSeq.get_max_capacity(image)
                    return control.LSBSeq.inject_message(
                        image, message[: cap * percent // 100]
                    )
                case AnalyseWorker.Methods.LSB_RAND:
                    pass
                case AnalyseWorker.Methods.LAB3:
                    cap = control.LSBMessage.get_max_capacity(image, message)
                    return control.LSBMessage.inject_message(
                        image, message[: cap * percent // 100]
                    )
                case AnalyseWorker.Methods.LAB4:
                    cap = control.LSBScaledMessage.get_max_capacity(image)
                    return control.LSBScaledMessage.inject_message(
                        control.LSBScaledMessage.scale_image(image),
                        message[: cap * percent // 100],
                    )
        if method == AnalyseWorker.Methods.LAB4:
            return control.LSBScaledMessage.scale_image(image)
        return image

    @staticmethod
    def analyze_image(image: PIL.Image.Image, rs_a, aump: tuple[int, int]):
        out = {}
        out[AnalyseWorker.__CHI2_KEY] = control.ChiSquaredAnalysis.analyze(image)
        out[AnalyseWorker.__AUMP_KEY] = control.AUMPAnalysis.analyze(image, *aump)
        # out[AnalyseWorker.__RS_KEY] = rs_a.analyze(image)
        return out

    def cancel(self):
        self.__canceled = True
        for proc in multiprocessing.active_children():
            proc.kill()

    def run(self):
        bits = bitutil.urandom(500000)

        out = {}
        for insert_rate in range(0, 101, 50):
            with multiprocessing.Pool(self.__POOL_SIZE) as pool:
                images = pool.starmap(
                    AnalyseWorker.insert_message,
                    zip(
                        self.__images,
                        itertools.repeat(bits),
                        itertools.repeat(insert_rate),
                        itertools.repeat(self.__method),
                    ),
                )

            with multiprocessing.Pool(self.__POOL_SIZE) as pool:
                out_cur = pool.starmap(
                    AnalyseWorker.analyze_image,
                    zip(
                        images,
                        itertools.repeat(self.__rs_a),
                        itertools.repeat(self.__aump),
                    ),
                )
                out[insert_rate] = {
                    k: sum([dic[k] for dic in out_cur]) for k in out_cur[0]
                }
                if insert_rate > 0:
                    for key in out[insert_rate].keys():
                        out[insert_rate][key] = (
                            (len(self.__images) - out[insert_rate][key])
                            * 100
                            / len(self.__images)
                        )
                else:
                    for key in out[insert_rate].keys():
                        out[insert_rate][key] = (
                            out[insert_rate][key] * 100 / len(self.__images)
                        )

            if self.__canceled:
                self.finished.emit({})
                return
        # out = {k: [dic[k] for dic in out] for k in out[0]}
        # out = {
        #     key: {index * 25: out[key][index] for index in range(len(out[key]))}
        #     for key in out.keys()
        # }
        self.finished.emit(out)


class MainWindow(PyQt6.QtWidgets.QMainWindow):
    __WINDOW_TITLE = "Stegonometry Task 6"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.__WINDOW_TITLE)
        self.populate()
        self.connect_buttons()

    def show_progress_indicator(self):
        self.__progress_indicator = PyQt6.QtWidgets.QProgressDialog(self)
        self.__progress_indicator.setWindowModality(
            PyQt6.QtCore.Qt.WindowModality.WindowModal
        )
        self.__progress_indicator.setRange(0, 0)
        self.__progress_indicator.setAttribute(
            PyQt6.QtCore.Qt.WidgetAttribute.WA_DeleteOnClose
        )
        # self.__buttons_widget.__main_layout.addWidget(self.__progress_indicator)
        self.__progress_indicator.show()

    def hide_progress_indicator(self):
        self.__progress_indicator.close()

    def connect_buttons(self):
        self.__worker_thread = None

        def open_images_event():
            paths = PyQt6.QtWidgets.QFileDialog.getOpenFileNames(
                parent=self, caption="Select images to open", filter="BMP (*.bmp)"
            )[0]
            if paths is not None:
                self.__images_before_widget.images = [PIL.Image.open(x) for x in paths]

        def analyze_images_event():
            def worker_finished(out: dict):
                self.hide_progress_indicator()
                self.__result_text_browser.setText(str(out))
                control.PlotBuilder.build_plot("Result", out)

            self.show_progress_indicator()
            self.__worker_thread = AnalyseWorker(
                self.__images_before_widget.images,
                self.__buttons_widget.method_dropdown.currentData(),
                (
                    self.__buttons_widget.rs_m_spinbox.value(),
                    self.__buttons_widget.rs_n_spinbox.value(),
                ),
                (
                    self.__buttons_widget.aump_block_size_spinbox.value(),
                    self.__buttons_widget.aump_parameter_spinbox.value(),
                ),
            )
            self.__worker_thread.finished.connect(worker_finished)
            self.__progress_indicator.canceled.connect(self.__worker_thread.quit)
            self.__worker_thread.start()

        def save_results_event():
            pathlib.Path("out.json").write_text(
                self.__result_text_browser.toPlainText()
            )

        self.__buttons_widget.open_images_button.clicked.connect(open_images_event)
        self.__buttons_widget.analyze_images_button.clicked.connect(
            analyze_images_event
        )
        self.__buttons_widget.save_resuts_button.clicked.connect(save_results_event)

    def populate(self):
        self.__central_widget = PyQt6.QtWidgets.QWidget(self)
        self.__main_layout = PyQt6.QtWidgets.QVBoxLayout(self.__central_widget)
        self.__central_widget.setLayout(self.__main_layout)
        self.setCentralWidget(self.__central_widget)

        self.__upper_layout_widget = PyQt6.QtWidgets.QWidget(self)
        self.__upper_layout = PyQt6.QtWidgets.QHBoxLayout(self.__upper_layout_widget)
        self.__upper_layout_widget.setLayout(self.__upper_layout)
        self.__main_layout.addWidget(self.__upper_layout_widget)

        self.__images_before_widget = ImagesWidget(self.__upper_layout_widget)
        self.__buttons_widget = ButtonsWidget(self.__upper_layout_widget)
        self.__upper_layout.addWidget(self.__images_before_widget)
        self.__upper_layout.addWidget(self.__buttons_widget)

        self.__result_text_browser = PyQt6.QtWidgets.QTextBrowser(self.__central_widget)
        self.__main_layout.addWidget(self.__result_text_browser)

        for method in AnalyseWorker.Methods:
            self.__buttons_widget.method_dropdown.addItem(str(method), method)
