import json
from typing import Any, Callable
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtNetwork import QTcpSocket, QHostAddress
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QComboBox,
    QPushButton,
    QSlider,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGridLayout,
)

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

QCheckBox::indicator {
    border: 1px solid #8CCDEB;
    color: #8CCDEB;
}
QCheckBox::indicator::checked {
    background-color: #8CCDEB;
}
"""


class Crop:
    def __init__(self):
        self.step = 0
        self.flip = 0
        self.p0 = (0, 0)
        self.p1 = (0, 0)


class ImageScene(QGraphicsScene):

    def __init__(self, signal, crop):
        super().__init__()
        self.signal = signal
        self.crop = crop

    def mousePressEvent(self, event):
        x = event.scenePos().x()
        y = event.scenePos().y()

        if self.crop.step == 0:
            self.crop.p0 = (int(x), int(y))
            self.crop.step = 1
        elif self.crop.step == 1:
            self.crop.p1 = (int(x), int(y))
            self.crop.step = 2
            self.signal.emit(*self.crop.p0, *self.crop.p1)
        else:
            self.crop.step = 0
            self.signal.emit(0, 0, 0, 0)



class MainWindow(QMainWindow):
    signal_image_clicked = pyqtSignal(int, int, int, int)

    def __init__(self, filepath, config):
        super().__init__()
        self.setWindowTitle("Synaesthesia")

        self.socket = QTcpSocket(self)
        self.socket.connectToHost(QHostAddress.LocalHost, 2137)
        self.config = config

        def sck(*args):
            self.socket.write(" ".join(args).encode() + b"\n")
            self.socket.flush()

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        self.main_widget = QWidget(parent=self)
        self.main_widget.setLayout(main_layout)
        self._crop = Crop()
        self._crop.step = 2 if self.config["camera"]["crop"]["on"] else 0

        self.image_scene = ImageScene(self.signal_image_clicked, self._crop)
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

        musicbox_widget = MusicBoxWidget(filepath, config, sck, parent=self.form_widget)
        form_layout.addWidget(musicbox_widget, 0, 0, 1, -1)

        for index, (name, music) in enumerate(config["music"].items(), start=1):
            label = QLabel()
            label.setText(name)
            label.setStyleSheet("QLabel { background-color: %s; color: black; }" % name)
            label.setAlignment(Qt.AlignCenter)
            widget = MusicWidget(music, sck, name, parent=self.form_widget)
            form_layout.addWidget(label, index, 0)
            form_layout.addWidget(widget, index, 1)

        main_layout.addWidget(self.image_widget)
        main_layout.addWidget(self.form_widget)
        self.setCentralWidget(self.main_widget)
        self.setStyleSheet(STYLE)

        self.signal_image_clicked.connect(self.crop)

        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.timer.start(config["window_speed"])

    def timeout(self):
        self.show_image("/dev/shm/warsztat.jpg")

    def resizeEvent(self, ev):
        self.image_widget.setFixedWidth(self.width() // 3)

    def crop(self, x0, y0, x1, y1):
        if x0 == y0 == x1 == y1 == 0:
            self.config["camera"]["crop"] = {
                "on": False,
            }
            self.socket.write(b"camera crop - -\n")
        else:
            self.config["camera"]["crop"] = {
                "on": True,
                "p0": [x0, y0],
                "p1": [x1, y1],
            }
            self.socket.write(f"camera crop {x0} {y0} {x1} {y1}\n".encode())

    def show_image(self, url):
        pixmap = QPixmap(url)
        if pixmap.isNull():
            return
        self.image_scene.clear()
        self.image_scene.addPixmap(pixmap)
        self.image_widget.fitInView(0, 0, pixmap.width(), pixmap.height(), Qt.KeepAspectRatio)


class LabelWidget(QWidget):
    def __init__(
        self,
        label: str,
        widget_factory: Callable[[QWidget], QWidget],
        value_cb: Callable[[Any], str],
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
    def __init__(self, filepath, config, socket, parent=None):
        super().__init__(parent)

        self.filepath = filepath
        self.config = config
        self.socket = socket
        self.period_slider = LabelWidget(
            "Period",
            _make_dial(
                min=30,
                max=300,
                value=int(config["period"] * 10),
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
            return lambda: self._flip(val)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.addWidget(make_btn("No Flip", flip_emit(0)), 0, 0)
        grid_layout.addWidget(make_btn("Flip", flip_emit(1)), 0, 1)
        grid_layout.addWidget(make_btn("Mirror", flip_emit(-1)), 1, 0)
        grid_layout.addWidget(make_btn("Save", self._save), 1, 1)
        grid_layout.addWidget(self.period_slider, 0, 3, -1, 1)

        self.setLayout(grid_layout)

    def _set_period(self, value: int):
        v = value / 10
        self.socket("music", "period", str(v))
        self.config["period"] = v

    def _save(self):
        with open(self.filepath, "w") as file:
            json.dump(self.config, file, indent=4)

    def _flip(self, val):
        self.socket("camera", "crop", "-", "-")
        self.socket("camera", "flip", str(val))
        self.config["camera"]["flip"] = val


class MusicWidget(QWidget):
    def __init__(self, config, socket, name, parent=None):
        super().__init__(parent)

        self._config = config
        self._socket = socket
        self._name = name

        self.select = QComboBox(self)
        for label in INSTRUMENTS_LIST:
            self.select.addItem(label)
        self.select.setCurrentText(INSTRUMENTS[config["program"]])
        self.select.currentTextChanged.connect(self._set_program)

        def make_callback(key):
            def f(v):
                vv = v / 100
                self._socket("music_" + self._name, key, str(vv))
                config[key] = vv

            return f

        def make_dial_color(key):
            factory = _make_dial(
                min=0,
                max=100,
                value=int(config[key] * 100),
                cb=make_callback(key),
            )
            return factory(parent=self)

        def make_dial_music(name, key, min=0, max=100):
            return LabelWidget(
                name,
                _make_dial(
                    min=min,
                    max=max,
                    value=int(config[key] * 100),
                    cb=make_callback(key),
                ),
                value_cb=lambda v: f"{v:d}%",
            )

        def make_checkbox_music(name, key, min=0, max=100):
            def f(v):
                vv = 1.0 if v == Qt.Checked else 0.0
                self._socket("music_" + self._name, key, str(vv))
                config[key] = vv

            widget = QCheckBox(name, parent=self)
            widget.setTristate(False)
            widget.setCheckState(Qt.Checked if config[key] > 0.5 else Qt.Unchecked)
            widget.stateChanged.connect(f)
            return widget

        color_layout = QVBoxLayout()
        color_layout.addWidget(make_dial_color("h"))
        color_layout.addWidget(make_dial_color("v"))
        color_layout.addWidget(make_dial_color("s"))
        color_layout.addWidget(self.select)

        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(make_checkbox_music("Sustain", "sustain"))
        checkbox_layout.addWidget(make_checkbox_music("Sostenuto", "sostenuto"))

        layout = QHBoxLayout()
        layout.addLayout(color_layout)
        layout.addLayout(checkbox_layout)
        layout.addWidget(make_dial_music("Volume", "volume"))
        layout.addWidget(make_dial_music("Polytouch", "polytouch"))
        layout.addWidget(make_dial_music("Pitch", "pitch", min=-100))
        layout.addWidget(make_dial_music("Modwheel", "modwheel"))
        layout.addWidget(make_dial_music("Reverb", "reverb"))
        layout.addWidget(make_dial_music("Chorus", "chorus"))
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

    def _set_program(self, text: str):
        id = INSTRUMENTS_REVERSE[text]
        self._socket("music_" + self._name, "program", str(id))
        self._config["program"] = id
