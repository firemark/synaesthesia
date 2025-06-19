import json
from pathlib import Path
from sys import argv
from PyQt5.QtWidgets import QApplication
from synaesthesia.gui import MainWindow


def main():
    path = Path(argv[1])
    with open(argv[1]) as file:
        config = json.load(file)

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
