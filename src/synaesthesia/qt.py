import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QLabel,
    QComboBox,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
)

from synaesthesia.music import Music
from synaesthesia.instruments import INSTRUMENTS, INSTRUMENTS_LIST, INSTRUMENTS_REVERSE


class MainWindow(QMainWindow):

    def __init__(self, musicbox: dict[str, Music]):
        super().__init__()
        self.setWindowTitle("Synaesthesia")

        layout = QFormLayout()
        main_widget = QWidget()
        main_widget.setLayout(layout)

        for name, music in musicbox.items():
            widget = MusicWidget(music, parent=main_widget)
            layout.addRow(name, widget)

        self.setCentralWidget(main_widget)

        # w = QWidget()
        # b = QLabel(w)
        # b.setText("Hello World!")
        # w.setGeometry(100, 100, 200, 50)
        # b.move(50, 20)


class MusicWidget(QWidget):
    def __init__(self, music: Music, parent=None):
        super().__init__(parent)

        self._music = music

        self.select = QComboBox(self)
        for label in INSTRUMENTS_LIST:
            self.select.addItem(label)
        self.select.setCurrentText(INSTRUMENTS[music.get_program()])
        self.select.currentTextChanged.connect(self._set_program)

        self.volume_slider = QSlider(orientation=Qt.Orientation.Horizontal, parent=self)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(music.get_volume() * 100))
        self.volume_slider.valueChanged.connect(self._set_volume)

        self.polytouch_slider = QSlider(orientation=Qt.Orientation.Horizontal, parent=self)
        self.polytouch_slider.setMinimum(0)
        self.polytouch_slider.setMaximum(100)
        self.polytouch_slider.setValue(int(music.get_polytouch() * 100))
        self.polytouch_slider.valueChanged.connect(self._set_polytouch)

        layout = QHBoxLayout()
        layout.addWidget(self.select)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.polytouch_slider)
        self.setLayout(layout)

    def _set_program(self, text: str):
        id = INSTRUMENTS_REVERSE[text]
        self._music.change_program(id)

    def _set_volume(self, value: int):
        self._music.set_volume(value / 100)

    def _set_polytouch(self, value: int):
        self._music.set_polytouch(value / 100)


def window(musicbox: dict[str, Music]):
    app = QApplication(sys.argv)
    window = MainWindow(musicbox)
    window.show()
    app.exec()


if __name__ == "__main__":
    window()
