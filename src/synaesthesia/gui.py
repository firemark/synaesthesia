from typing import Any, Callable
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtNetwork import QTcpSocket, QHostAddress
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QComboBox,
    QPushButton,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGridLayout,
)

from synaesthesia.colors import MaskConfig
from synaesthesia.music import Music, MusicBox
from synaesthesia.instruments import INSTRUMENTS, INSTRUMENTS_LIST, INSTRUMENTS_REVERSE

STYLE = """
QWidget {
    background-color: #222831;
    color: #6EACDA;
    font-size: 12pt;
}

QPushButton:pressed {
    background-color: #8CCDEB;
    color: #222831;
}

QPushButton:hover, QComboBox:hover, QSlider:hover {
    background-color: #648DB3;
    color: #222831;
}

*:focus {
    background-color: #333446;
}

QComboBox:selected {
    background-color: #27548A;
    color: #222831;
}

QSlider::groove {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #222831, stop:1 #333446);
    height: 8px;
}

QSlider::handle {
    background: #8CCDEB;
    width: 18px;
}

QSlider::sub-page {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8CCDEB, stop:1 #648DB3);
}
"""


class ImageScene(QGraphicsScene):

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def mousePressEvent(self, event):
        x = event.scenePos().x()
        y = event.scenePos().y()
        self.signal.emit(x, y)


class MainWindow(QMainWindow):
    signal_image_clicked = pyqtSignal(float, float)
    signal_image_flipped = pyqtSignal(int)

    def __init__(self, musicbox: dict[str, Music], colors: dict[str, MaskConfig]):
        super().__init__()
        self.setWindowTitle("Synaesthesia")

        self.socket = QTcpSocket(self)
        self.socket.connectToHost(QHostAddress.LocalHost, 2137)

        def sck(*args):
            self.socket.write(" ".join(args).encode() + b"\n")

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        self.main_widget = QWidget(parent=self)
        self.main_widget.setLayout(main_layout)

        self.image_scene = ImageScene(self.signal_image_clicked)
        self.image_widget = QGraphicsView(self.image_scene, parent=self.main_widget)
        self.image_widget.setMinimumWidth(320)
        self.image_widget.setMinimumHeight(320)
        self.image_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.image_widget.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.image_widget.setAlignment(Qt.AlignCenter)
        self.image_widget.setBackgroundBrush(QColor("#222831"))
        self.image_widget.setStyleSheet("* {border: 0;}")

        form_layout = QGridLayout()
        self.form_widget = QWidget(parent=self.main_widget)
        self.form_widget.setLayout(form_layout)

        musicbox_widget = MusicBoxWidget(musicbox, sck, parent=self.form_widget)
        form_layout.addWidget(musicbox_widget, 0, 0, 1, -1)

        for index, (name, music) in enumerate(musicbox.items(), start=1):
            label = QLabel()
            label.setText(name)
            label.setStyleSheet("QLabel { background-color: %s; color: black; }" % name)
            label.setAlignment(Qt.AlignCenter)
            widget = MusicWidget(
                music, sck, name, colors[name], parent=self.form_widget
            )
            form_layout.addWidget(label, index, 0)
            form_layout.addWidget(widget, index, 1)

        main_layout.addWidget(self.image_widget)
        main_layout.addWidget(self.form_widget)
        self.setCentralWidget(self.main_widget)
        self.setStyleSheet(STYLE)

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
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        layout.addWidget(self.widget)
        layout.addWidget(self.value)
        self.setLayout(layout)


def _make_dial(min: int, max: int, value: int, cb: Callable[[int], None]):
    def factory(parent: QWidget) -> QWidget:
        widget = QSlider(orientation=Qt.Orientation.Horizontal, parent=parent)
        widget.setMinimum(min)
        widget.setMaximum(max)
        widget.setValue(value)
        widget.setMinimumWidth(100)
        widget.valueChanged.connect(cb)
        return widget

    return factory


class MusicBoxWidget(QWidget):
    def __init__(self, musicbox: MusicBox, socket, parent=None):
        super().__init__(parent)

        self._musicbox = musicbox
        self.socket = socket
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

        def make_btn(text, cb):
            button = QPushButton()
            button.setText(text)
            button.clicked.connect(cb)
            return button

        def flip_emit(val):
            return lambda: self.socket("screen", "flip", str(val))

        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.addWidget(make_btn("No Flip", flip_emit(0)), 0, 0)
        grid_layout.addWidget(make_btn("Flip", flip_emit(1)), 0, 1)
        grid_layout.addWidget(make_btn("Mirror", flip_emit(-1)), 1, 0)
        grid_layout.addWidget(make_btn("Save", flip_emit(0)), 1, 1)
        grid_layout.addWidget(self.period_slider, 0, 3, -1, 1)

        self.setLayout(grid_layout)

    def _set_period(self, value: int):
        v = value / 10
        self.socket("music", "period", str(v))
        self._musicbox.period = v


class MusicWidget(QWidget):
    def __init__(
        self, music: Music, socket, name, color_config: MaskConfig, parent=None
    ):
        super().__init__(parent)

        self._music = music
        self._socket = socket
        self._name = name

        self.select = QComboBox(self)
        for label in INSTRUMENTS_LIST:
            self.select.addItem(label)
        self.select.setCurrentText(INSTRUMENTS[music.get_program()])
        self.select.currentTextChanged.connect(self._set_program)

        def make_dial_color(key):
            def f(v):
                vv = v / 100
                self._socket("music_" + self._name, key, str(vv))
                setattr(color_config, key, str(vv))

            factory = _make_dial(
                min=0,
                max=100,
                value=int(getattr(color_config, key) * 100),
                cb=f,
            )
            return factory(parent=self)

        color_layout = QVBoxLayout()
        color_layout.addWidget(make_dial_color("h"))
        color_layout.addWidget(make_dial_color("v"))
        color_layout.addWidget(make_dial_color("s"))
        color_layout.addWidget(self.select)

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
        layout.addLayout(color_layout)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.polytouch_slider)
        layout.addWidget(self.pitch_slider)
        layout.addWidget(create_effect_widget("Sustain", 64))
        layout.addWidget(create_effect_widget("Sostenuto", 66))
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

    def _set_program(self, text: str):
        id = INSTRUMENTS_REVERSE[text]
        self._socket("music_" + self._name, "program", str(id))
        self._music.change_program(id)

    def _set_volume(self, value: int):
        v = value / 100
        self._socket("music_" + self._name, "volume", str(v))
        self._music.set_volume(v)

    def _set_polytouch(self, value: int):
        v = value / 100
        self._socket("music_" + self._name, "polytouch", str(v))
        self._music.set_polytouch(v)

    def _set_pitch(self, value: int):
        v = value / 100
        self._socket("music_" + self._name, "pitch", str(v))
        self._music.set_pitch(v)
