import threading
from mido import open_output
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
import numpy as np

from synaesthesia.music import MusicBox, Music
from synaesthesia.camera import run_thread
from synaesthesia.gui import MainWindow


class CameraWorker(QObject):
    signal_progress = pyqtSignal(np.ndarray)
    signal_finished = pyqtSignal()
    _signal_stop = pyqtSignal()

    def __init__(self, musicbox: MusicBox):
        super().__init__()
        self.progress = pyqtSignal(np.ndarray)
        self._musicbox = musicbox
        self._is_stopped = threading.Event()
        self._signal_stop.connect(self._stop_cb)

    def run(self):
        run_thread(self._musicbox, self._is_stopped, self.signal_progress.emit)

    def stop(self):
        self._signal_stop.emit()

    def _stop_cb(self):
        self._is_stopped.set()
        self.signal_finished.emit()


def main():
    port = open_output("warsztat", autoreset=True)
    musicbox = MusicBox(
        {
            "red": Music(port, channel=0, program=5),
            "green": Music(port, channel=1, program=12),
            "blue": Music(port, channel=2, program=97),
        }
    )

    app = QApplication([])
    window = MainWindow(musicbox)
    thread = QThread()
    camera_worker = CameraWorker(musicbox)
    camera_worker.moveToThread(thread)

    camera_worker.signal_finished.connect(thread.quit)
    camera_worker.signal_progress.connect(window.show_image)
    thread.started.connect(camera_worker.run)
    # window.destroyed.connect(camera_worker.stop)

    try:
        thread.start()
        window.show()
        app.exec()
    except KeyboardInterrupt:
        pass
    finally:
        camera_worker.stop()
        thread.quit()