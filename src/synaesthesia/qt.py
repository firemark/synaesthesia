from functools import partial
import json
from pathlib import Path
from sys import argv
import threading
from mido import open_output
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
import numpy as np

from synaesthesia.colors import MaskConfig
from synaesthesia.music import MusicBox, Music
from synaesthesia.camera import Crop
from synaesthesia.gui import MainWindow


def on_click(crop, x: float, y: float):
    if crop.step == 0:
        crop.p0 = (int(x), int(y))
        crop.step = 1
    elif crop.step == 1:
        crop.p1 = (int(x), int(y))
        crop.step = 2
    else:
        crop.step = 0


def on_flip(crop: Crop, flip: int):
    crop.flip = flip
    crop.step = 0


def main():
    path = Path(argv[1])
    with open(argv[1]) as file:
        config = json.load(file)

    crop = Crop()
    app = QApplication([])
    window = MainWindow(path, config)

    try:
        window.show()
        app.exec()
    except KeyboardInterrupt:
        pass
    finally:
        pass
        # camera_worker.stop()
        # thread.quit()