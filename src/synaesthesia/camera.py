#!/usr/bin/env python3
from sys import stderr
import cv2 as cv
import numpy as np
from math import fmod
from time import monotonic
from typing import Callable

from synaesthesia.colors import get_colors
from synaesthesia.music import Music, MusicBox


class Crop:
    def __init__(self):
        self.step = 0
        self.flip = 0
        self.p0 = (0, 0)
        self.p1 = (0, 0)


def get_camera():
    cap = cv.VideoCapture(4)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 424)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv.CAP_PROP_BUFFERSIZE, 3)
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


def loop(time, frame, musicbox: MusicBox, show_image):
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

    draw(frame, width, height, x_progress, colors, show_image)


def draw(frame, width, height, x_progress, colors, show_image):
    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame = cv.cvtColor(frame, cv.COLOR_GRAY2BGR)
    for mask in colors.values():
        frame[mask.mask] = frame[mask.mask] / 2 + mask.color / 2
    # frame[:, :, 0] = h * 255

    # frame = cv.cvtColor(frame, cv.COLOR_BGR2HSV_FULL)[:, :, 1]
    # frame[frame > 128] = 255
    # frame[frame <= 128] = 0

    cv.line(frame, (x_progress, 0), (x_progress, height - 1), (0, 0, 0), 2)
    show_image(frame)


def run_thread(musicbox, crop: Crop, is_stopped: "threading.Event", show_image: Callable[[np.ndarray], None]):
    # cv.namedWindow("Sound", cv.WINDOW_NORMAL)
    # cv.setMouseCallback("Sound", on_click)
    cap = get_camera()

    time = 0.0
    try:
        while not is_stopped.is_set():
            start = monotonic()
            ret, frame = cap.read()

            if not ret:
                break

            frame = cv.flip(frame, crop.flip)

            if crop.step == 2:
                x0, y0 = crop.p0
                x1, y1 = crop.p1
                if x0 > x1:
                    x0, x1 = x1, x0
                if y0 > y1:
                    y0, y1 = y1, y0
                frame = frame[y0:y1, x0:x1]

            loop(time, frame, musicbox, show_image)
            # if cv.waitKey(1) == ord("q"):
            #    break
            time += monotonic() - start
    finally:
        # When everything done, release the capture
        cap.release()
        cv.destroyAllWindows()

