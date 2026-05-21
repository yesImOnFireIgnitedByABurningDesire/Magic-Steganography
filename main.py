from control.PlotBuilder import PlotBuilder
import numpy as np
import ui

import sys
import PyQt6.QtWidgets

# PlotBuilder.build_plot(
#     "test",
#     {
#         0: {"CHI2": np.int64(8), "AUMP": np.int64(3)},
#         50: {"CHI2": np.int64(6), "AUMP": np.int64(8)},
#         100: {"CHI2": np.int64(6), "AUMP": np.int64(10)},
#     },
# )


if __name__ == "__main__":
    # sys.settrace(None)
    app = PyQt6.QtWidgets.QApplication(sys.argv)
    window = ui.MainWindow()
    window.show()
    app.exec()
