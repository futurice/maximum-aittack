# Records gameplay into an image and event series so that it can later be reused without
# opening the game.

import cv2
import numpy as np
import datetime
import os
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.widgets.RawImageWidget import RawImageWidget

from windowcapture import WindowCapture

from gamelibs import telemetry as tel

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

text = QtWidgets.QLabel()

viewer_layout.addWidget(text)

viewer_window.show()

tel_idx = 0
tel.reset()

timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(':', '-')
rec_dir_name = os.path.join(os.getcwd(), 'recordings', timestamp)
os.mkdir(rec_dir_name)

telemetry_file_name = os.path.join(rec_dir_name, 'telemetry.txt')

image_dir_name = os.path.join(rec_dir_name, 'images')
os.mkdir(image_dir_name)


def update(telemetry_file):
    global tel_idx

    # get an updated image of the game
    screenshot = win_cap.get_screenshot()
    # Original 1280 x 1024, half 640 x 512, half 320 x 256
    screenshot = cv2.resize(screenshot, dsize=(320, 256), interpolation=cv2.INTER_CUBIC)

    draw_image = np.swapaxes(screenshot, 0, 1)
    draw_image = np.flip(draw_image, 2)
    draw_frame.setImage(draw_image)

    QApplication.processEvents()

    did_update = tel.update()

    lap_time = tel.get_telemetry_value('m_lapTime')

    text.setText(
        ";".join([
            str(tel_idx),
            "{:.2f}".format(tel.get_telemetry_value('m_totalDistance')),
            "{:.2f}".format(tel.get_telemetry_value('m_lapTime')),
            "{:.2f}".format(tel.get_telemetry_value('m_speed')),
            "{:.2f}".format(tel.get_telemetry_value('m_steer')),
            "{:.2f}".format(tel.get_telemetry_value('m_throttle')),
            "{:.2f}".format(tel.get_telemetry_value('m_brake')),
            "{:.2f}".format(tel.get_telemetry_value('m_gear')),
            "{:.2f}".format(tel.get_telemetry_value('m_engineRate'))
        ])
    )

    if did_update and lap_time > 0:
        np.save(os.path.join(image_dir_name, str(tel_idx)), draw_image)
        telemetry_file.write(tel.pack_data_to_json() + '\n')

        tel_idx += 1


with open(telemetry_file_name, 'w') as telemetry_file:
    while True:
        update(telemetry_file)

sys.exit(pg.exec())
