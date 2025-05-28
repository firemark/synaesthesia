#!/usr/bin/env python3
from sys import stderr
import cv2 as cv
import numpy as np
from math import fmod
from time import monotonic

from synaesthesia.colors import get_colors
from synaesthesia.music import Music


PERIOD = 3.0


def play(row, music: Music, id: int):
    notes_total = music.get_len_notes()
    span = len(row) / notes_total
    for n in range(notes_total):
        start = int(span * n)
        stop = int(span * (n + 1))
        if np.any(row[start:stop] == id):
            music.note_on(n)
        else:
            music.note_off(n)


def loop(time, frame, musicbox):
    frame = cv.flip(frame, -1)
    progress = fmod(time, PERIOD) / PERIOD
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

    cv.line(frame, (x_progress, 0), (x_progress, height - 1), (0, 0, 0), 2)
    cv.imshow("Sound", frame)


def _main(musicbox, is_stopped):
    cv.namedWindow("Sound", cv.WINDOW_AUTOSIZE)
    cap = cv.VideoCapture(4)
    # cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("Cannot open camera", file=stderr)
        exit()

    time = 0.0
    try:
        while not is_stopped.is_set():
            start = monotonic()
            ret, frame = cap.read()
            if not ret:
                break

            loop(time, frame, musicbox)
            if cv.waitKey(1) == ord("q"):
                break
            time += monotonic() - start
    finally:
        # When everything done, release the capture
        cap.release()
        cv.destroyAllWindows()


def main():
    import threading
    from synaesthesia.qt import window

    musicbox = {
        "red": Music("warsztat-0", program=5),
        "green": Music("warsztat-1", program=12),
        "blue": Music("warsztat-2", program=97),
    }

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