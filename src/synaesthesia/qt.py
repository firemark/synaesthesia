import sys
from typing import Any, Callable
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QLabel,
    QComboBox,
    QSlider,
    QDial,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
)

from synaesthesia.music import Music, MusicBox
from synaesthesia.instruments import INSTRUMENTS, INSTRUMENTS_LIST, INSTRUMENTS_REVERSE


class MainWindow(QMainWindow):

    def __init__(self, musicbox: dict[str, Music]):
        super().__init__()
        self.setWindowTitle("Synaesthesia")

        layout = QFormLayout()
        main_widget = QWidget()
        main_widget.setLayout(layout)

        layout.setLabelAlignment(Qt.AlignHCenter)
        layout.addRow("Synaesthesia", MusicBoxWidget(musicbox, parent=main_widget))
        for name, music in musicbox.items():
            widget = MusicWidget(music, parent=main_widget)
            layout.addRow(name, widget)

        self.setCentralWidget(main_widget)


class LabelWidget(QWidget):
    def __init__(
        self,
        label: str,
        widget_factory: Callable[[QWidget], QWidget],
        value_cb: Callable[[Any], None],
        parent=None,
    ):
        super().__init__(parent)

        self.label = QLabel(self)
        self.label.setText(label)
        self.label.setAlignment(Qt.AlignHCenter)

        self.value = QLabel(self)
        self.value.setText("-")
        self.value.setAlignment(Qt.AlignHCenter)

        self.widget = widget_factory(self)
        self.value.setText(value_cb(self.widget.value()))
        self.widget.valueChanged.connect(lambda v: self.value.setText(value_cb(v)))

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.widget)
        layout.addWidget(self.value)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)


def _make_dial(min: int, max: int, value: int, cb: Callable[[int], None]):
    def factory(parent: QWidget) -> QWidget:
        widget = QDial(parent=parent)
        widget.setMinimum(min)
        widget.setMaximum(max)
        widget.setValue(value)
        widget.valueChanged.connect(cb)
        return widget

    return factory


class MusicBoxWidget(QWidget):
    def __init__(self, musicbox: MusicBox, parent=None):
        super().__init__(parent)

        self._musicbox = musicbox
        self.period_slider = LabelWidget(
            "Period",
            _make_dial(
                min=30,
                max=300,
                value=int(self._musicbox.period * 10),
                cb=self._set_period,
            ),
            value_cb=lambda v: f"{v / 10:0.1f}s",
        )

        layout = QHBoxLayout()
        layout.addWidget(self.period_slider)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

    def _set_period(self, value: int):
        self._musicbox.period = value / 10


class MusicWidget(QWidget):
    def __init__(self, music: Music, parent=None):
        super().__init__(parent)

        self._music = music

        self.select = QComboBox(self)
        for label in INSTRUMENTS_LIST:
            self.select.addItem(label)
        self.select.setCurrentText(INSTRUMENTS[music.get_program()])
        self.select.currentTextChanged.connect(self._set_program)

        self.volume_slider = LabelWidget(
            "Volume",
            _make_dial(
                min=0,
                max=100,
                value=int(music.get_volume() * 100),
                cb=self._set_volume,
            ),
            value_cb=str,
        )

        self.polytouch_slider = LabelWidget(
            "Polytone",
            _make_dial(
                min=0,
                max=100,
                value=int(music.get_polytouch() * 100),
                cb=self._set_polytouch,
            ),
            value_cb=str,
        )

        self.pitch_slider = LabelWidget(
            "Pitch",
            _make_dial(
                min=-100,
                max=+100,
                value=int(music.get_pitch() * 100),
                cb=self._set_pitch,
            ),
            value_cb=str,
        )

        def create_effect_widget(name, id):
            return LabelWidget(
                name,
                _make_dial(
                    min=0,
                    max=100,
                    value=0,
                    cb=lambda v: self._music.set_effect(id, v / 100),
                ),
                value_cb=str,
            )

        layout = QHBoxLayout()
        layout.addWidget(self.select)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.polytouch_slider)
        layout.addWidget(self.pitch_slider)
        layout.addWidget(create_effect_widget("Sustain", 64))
        layout.addWidget(create_effect_widget("Sostenuto", 66))
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

    def _set_program(self, text: str):
        id = INSTRUMENTS_REVERSE[text]
        self._music.change_program(id)

    def _set_volume(self, value: int):
        self._music.set_volume(value / 100)

    def _set_polytouch(self, value: int):
        self._music.set_polytouch(value / 100)

    def _set_pitch(self, value: int):
        self._music.set_pitch(value / 100)


def window(musicbox: dict[str, Music]):
    app = QApplication(sys.argv)
    window = MainWindow(musicbox)
    window.show()
    app.exec()


if __name__ == "__main__":
    window()
