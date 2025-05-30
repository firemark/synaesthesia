#!/usr/bin/env python3
from sys import stderr
import cv2 as cv
import numpy as np
from math import fmod
from time import monotonic

from synaesthesia.colors import get_colors
from synaesthesia.music import Music, MusicBox


class Crop:
    def __init__(self):
        self.step = 0
        self.p0 = (0, 0)
        self.p1 = (0, 0)



def get_camera():
    cap = cv.VideoCapture(4)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 424)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
    if not cap.isOpened():
        print("Cannot open camera", file=stderr)
        exit()
    return cap


def play(row, music: Music, id: int):
    notes_total = music.get_len_notes()
    span = len(row) / notes_total
    count = (row == id).sum()
    for n in range(notes_total):
        start = int(span * n)
        stop = int(span * (n + 1))
        if np.any(row[start:stop] == id) > 0:
            val = count / len(row)
            music.note_on(n, add=val)
        else:
            music.note_off(n)


def loop(time, frame, musicbox: MusicBox):
    # frame = cv.flip(frame, -1)
    period = musicbox.period
    progress = fmod(time, period) / period
    height, width = frame.shape[0:2]

    x_progress = int((width - 1) * progress)

    colors = get_colors(frame)
    music_array = np.zeros(frame.shape[0:2])
    for mask in colors.values():
        music_array[mask.mask] = mask.index

    for name, mask in colors.items():
        music = musicbox[name]
        row = music_array[:, x_progress]
        play(row, music, mask.index)

    draw(frame, width, height, x_progress, colors)


def draw(frame, width, height, x_progress, colors):
    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame = cv.cvtColor(frame, cv.COLOR_GRAY2BGR)
    for mask in colors.values():
        frame[mask.mask] = frame[mask.mask] / 2 + mask.color / 2
    # frame[:, :, 0] = h * 255

    # frame = cv.cvtColor(frame, cv.COLOR_BGR2HSV_FULL)[:, :, 1]
    # frame[frame > 128] = 255
    # frame[frame <= 128] = 0

    cv.line(frame, (x_progress, 0), (x_progress, height - 1), (0, 0, 0), 2)
    cv.imshow("Sound", frame)




def _main(musicbox, is_stopped):
    crop = Crop()
    def on_click(event, x, y, flags, params):
        if event == cv.EVENT_LBUTTONDOWN:
            if crop.step == 0:
                crop.p0 = (x, y)
                crop.step = 1
            elif crop.step == 1:
                crop.p1 = (x, y)
                crop.step = 2

    cv.namedWindow("Sound", cv.WINDOW_NORMAL)
    cv.setMouseCallback("Sound", on_click)
    cap = get_camera()

    time = 0.0
    try:
        while not is_stopped.is_set():
            start = monotonic()
            ret, frame = cap.read()

            if not ret:
                break

            if crop.step == 2:
                x0, y0 = crop.p0
                x1, y1 = crop.p1
                if x0 > x1:
                    x0, x1 = x1, x0
                if y0 > y1:
                    y0, y1 = y1, y0
                frame = frame[y0:y1, x0:x1]

            loop(time, frame, musicbox)
            # if cv.waitKey(1) == ord("q"):
            #    break
            time += monotonic() - start
    finally:
        # When everything done, release the capture
        cap.release()
        cv.destroyAllWindows()


def main():
    import threading
    from synaesthesia.qt import window
    from mido import open_output

    port = open_output("warsztat", autoreset=True)
    musicbox = MusicBox(
        {
            "red": Music(port, channel=0, program=5),
            "green": Music(port, channel=1, program=12),
            "blue": Music(port, channel=2, program=97),
        }
    )

    is_stopped = threading.Event()
    thread_cv = threading.Thread(target=_main, args=(musicbox, is_stopped))
    thread_cv.start()

    try:
        window(musicbox)
    except KeyboardInterrupt:
        pass
    finally:
        is_stopped.set()
        thread_cv.join()
