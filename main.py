import ui

import sys
from PyQt6 import QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ui.MainWindow()
    window.show()
    app.exec()
