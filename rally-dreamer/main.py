import numpy as np
import os
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
from pyqtgraph.Qt import QtWidgets, QtGui
from pyqtgraph.widgets.RawImageWidget import RawImageWidget

from windowcapture import WindowCapture

WIN_WIDTH = 500
WIN_HEIGHT = 500

# Change the working directory to the folder this script is in.
# Doing this because I'll be putting the files from each video in their own folder on GitHub
os.chdir(os.path.dirname(os.path.abspath(__file__)))

win_cap = WindowCapture('DiRT Rally')

pg.mkQApp("Test")

viewer_window = QtWidgets.QWidget()
viewer_window.setWindowTitle("Rally Dreamer")
viewer_window.setFixedSize(WIN_WIDTH, WIN_HEIGHT)
viewer_layout = QtWidgets.QGridLayout()
viewer_window.setLayout(viewer_layout)

draw_frame = RawImageWidget(scaled=True)
viewer_layout.addWidget(draw_frame)

viewer_window.show()


def update():
    # get an updated image of the game
    screenshot = win_cap.get_screenshot()

    draw_image = np.swapaxes(screenshot, 0, 1)
    draw_image = np.flip(draw_image, 2)
    draw_frame.setImage(draw_image)

    QApplication.processEvents()


while True:
    update()

sys.exit(pg.exec())
