from functools import partial
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
    port = open_output("warsztat", autoreset=True)
    musicbox = MusicBox(
        {
            "red": Music(port, channel=0, program=5),
            "green": Music(port, channel=1, program=12),
            "blue": Music(port, channel=2, program=97),
        }
    )

    colors = {
        "red": MaskConfig(1, np.array((0, 0, 255)), h=0.9),
        "green": MaskConfig(2, np.array((0, 255, 0)), h=0.2),
        "blue": MaskConfig(3, np.array((255, 0, 0)), h=0.5),
        # "yellow": MaskConfig(4, np.array((255, 255, 0)), h=0.1),
    }

    crop = Crop()
    app = QApplication([])
    window = MainWindow(musicbox, colors)
    # thread = QThread()
    # camera_worker = CameraWorker(musicbox, crop, colors)
    # camera_worker.moveToThread(thread)

    # window.signal_image_clicked.connect(partial(on_click, crop))
    # window.signal_image_flipped.connect(partial(on_flip, crop))
    # camera_worker.signal_finished.connect(thread.quit)
    # camera_worker.signal_progress.connect(window.show_image)
    # thread.started.connect(camera_worker.run)
    # window.destroyed.connect(camera_worker.stop)

    try:
        # thread.start()
        window.show()
        app.exec()
    except KeyboardInterrupt:
        pass
    finally:
        pass
        # camera_worker.stop()
        # thread.quit()