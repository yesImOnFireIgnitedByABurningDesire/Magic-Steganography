import PyQt6.QtWidgets
import PyQt6.QtGui
import PyQt6.QtCore


class ButtonsWidget(PyQt6.QtWidgets.QWidget):
    def __init__(self, parent: PyQt6.QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        # self.setMinimumSize(150, 0)
        self.populate()

    def populate(self):
        self.__main_layout = PyQt6.QtWidgets.QVBoxLayout(self)

        self.open_images_button = PyQt6.QtWidgets.QPushButton(
            text="Open Images", parent=self
        )

        self.__rs_spinbox_container = PyQt6.QtWidgets.QWidget(self)
        self.__rs_spinbox_layout = PyQt6.QtWidgets.QHBoxLayout(
            self.__rs_spinbox_container
        )
        self.rs_m_spinbox = PyQt6.QtWidgets.QSpinBox(self)
        self.rs_m_spinbox.setToolTip("RS m")
        self.rs_m_spinbox.setValue(2)
        self.__rs_spinbox_layout.addWidget(self.rs_m_spinbox)
        self.rs_n_spinbox = PyQt6.QtWidgets.QSpinBox(self)
        self.rs_n_spinbox.setToolTip("RS n")
        self.rs_n_spinbox.setValue(2)
        self.__rs_spinbox_layout.addWidget(self.rs_n_spinbox)

        self.__aump_spinbox_container = PyQt6.QtWidgets.QWidget(self)
        self.__aump_spinbox_layout = PyQt6.QtWidgets.QHBoxLayout(
            self.__aump_spinbox_container
        )
        self.aump_block_size_spinbox = PyQt6.QtWidgets.QSpinBox(self)
        self.aump_block_size_spinbox.setToolTip("AUMP block size")
        self.aump_block_size_spinbox.setValue(16)
        self.__aump_spinbox_layout.addWidget(self.aump_block_size_spinbox)
        self.aump_parameter_spinbox = PyQt6.QtWidgets.QSpinBox(self)
        self.aump_parameter_spinbox.setToolTip("AUMP parameters")
        self.aump_parameter_spinbox.setValue(5)
        self.__aump_spinbox_layout.addWidget(self.aump_parameter_spinbox)

        self.method_dropdown = PyQt6.QtWidgets.QComboBox(self)

        self.analyze_images_button = PyQt6.QtWidgets.QPushButton(
            text="Start analyze", parent=self
        )

        self.save_resuts_button = PyQt6.QtWidgets.QPushButton(
            text="Save Results", parent=self
        )

        self.__main_layout.addStretch()
        self.__main_layout.addWidget(self.open_images_button)
        self.__main_layout.addWidget(self.__rs_spinbox_container)
        self.__main_layout.addWidget(self.__aump_spinbox_container)
        self.__main_layout.addWidget(self.method_dropdown)
        self.__main_layout.addWidget(self.analyze_images_button)
        self.__main_layout.addWidget(self.save_resuts_button)
        self.__main_layout.addStretch()
