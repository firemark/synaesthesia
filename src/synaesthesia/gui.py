from typing import Any, Callable
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QComboBox,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QGraphicsView,
    QGraphicsScene,
)

from synaesthesia.music import Music, MusicBox
from synaesthesia.instruments import INSTRUMENTS, INSTRUMENTS_LIST, INSTRUMENTS_REVERSE


class ImageScene(QGraphicsScene):

    def mousePressEvent(self, event):
        x = event.scenePos().x()
        y = event.scenePos().y()
        print(x, y)


class MainWindow(QMainWindow):

    def __init__(self, musicbox: dict[str, Music]):
        super().__init__()
        self.setWindowTitle("Synaesthesia")

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        self.main_widget = QWidget(parent=self)
        self.main_widget.setLayout(main_layout)

        self.image_scene = ImageScene()
        self.image_widget = QGraphicsView(self.image_scene, parent=self.main_widget)
        self.image_widget.setMinimumWidth(320)
        self.image_widget.setMinimumHeight(320)
        self.image_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.image_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.image_widget.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.image_widget.setBackgroundBrush(QColor("black"))

        form_layout = QFormLayout()
        self.form_widget = QWidget(parent=self.main_widget)
        self.form_widget.setLayout(form_layout)

        form_layout.setLabelAlignment(Qt.AlignHCenter)
        form_layout.addRow("Synaesthesia", MusicBoxWidget(musicbox, parent=self.form_widget))
        for name, music in musicbox.items():
            widget = MusicWidget(music, parent=self.form_widget)
            form_layout.addRow(name, widget)

        main_layout.addWidget(self.image_widget)
        main_layout.addWidget(self.form_widget)
        self.setCentralWidget(self.main_widget)

    def resizeEvent(self, ev):
        self.image_widget.setFixedWidth(self.width() // 2)

    def show_image(self, frame):
        h, w, ch = frame.shape
        qt_image = QImage(frame.data, w, h, ch * w, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_image)
        self.image_scene.clear()
        self.image_scene.addPixmap(pixmap)
        self.image_widget.fitInView(0, 0, w, h, Qt.KeepAspectRatio)


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
        widget = QSlider(orientation=Qt.Orientation.Horizontal, parent=parent)
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

        value_cb = lambda v: f"{v:d}%"

        self.volume_slider = LabelWidget(
            "Volume",
            _make_dial(
                min=0,
                max=100,
                value=int(music.get_volume() * 100),
                cb=self._set_volume,
            ),
            value_cb=value_cb,
        )

        self.polytouch_slider = LabelWidget(
            "Polytone",
            _make_dial(
                min=0,
                max=100,
                value=int(music.get_polytouch() * 100),
                cb=self._set_polytouch,
            ),
            value_cb=value_cb,
        )

        self.pitch_slider = LabelWidget(
            "Pitch",
            _make_dial(
                min=-100,
                max=+100,
                value=int(music.get_pitch() * 100),
                cb=self._set_pitch,
            ),
            value_cb=value_cb,
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
                value_cb=value_cb,
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
