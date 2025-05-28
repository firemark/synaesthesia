#!/usr/bin/env python3
from sys import stderr
import cv2 as cv
import numpy as np
from math import fmod
from time import monotonic
from mido import Message, open_output
import skimage as ski
from dataclasses import dataclass, replace


PERIOD = 3.0


class Music:
    NOTES = [60, 62, 64, 67, 69, 72]
    DELTA = 300

    def __init__(self, portname="warsztat-0", program=5):
        self.port = open_output(portname, autoreset=True)
        self.port.send(Message("program_change", program=program))

    def note_on(self, note):
        self.port.send(Message("note_on", note=note, velocity=127, time=self.DELTA))

    def note_off(self, note):
        self.port.send(Message("note_off", note=note))


def play(row, music, id):
    notes_total = len(music.NOTES)
    span = len(row) / notes_total
    for n, note in enumerate(music.NOTES):
        start = int(span * n)
        stop = int(span * (n + 1))
        if np.any(row[start:stop] == id):
            music.note_on(note)
        else:
            music.note_off(note)


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

    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame = cv.cvtColor(frame, cv.COLOR_GRAY2BGR)
    for mask in colors.values():
        frame[mask.mask] = frame[mask.mask] / 2 + mask.color / 2
    # frame[:, :, 0] = h * 255

    cv.line(frame, (x_progress, 0), (x_progress, height - 1), (0, 0, 0), 2)
    cv.imshow("Sound", frame)


@dataclass
class Mask:
    index: int
    color: np.ndarray
    mask: np.ndarray


def get_colors(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV) / 255.0

    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    colors = {
        "red": Mask(1, np.array((0, 0, 255)), (s > 0.3) & ((h < 0.2) | (h > 0.9))),
        "blue": Mask(2, np.array((255, 0, 0)), (s > 0.3) & ((h > 0.3) & (h < 0.6))),
    }

    return {
        color: replace(mask, mask=morphology(mask.mask))
        for color, mask in colors.items()
    }


def morphology(mask):
    mask = ski.morphology.erosion(mask, ski.morphology.disk(1))
    mask = ski.morphology.dilation(mask, ski.morphology.disk(3))
    mask = ski.morphology.closing(mask, ski.morphology.disk(2))
    return mask


def main():
    cv.namedWindow("Sound", cv.WINDOW_AUTOSIZE)
    cap = cv.VideoCapture(4)
    # cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("Cannot open camera", file=stderr)
        exit()

    musicbox = {
        "red": Music("warsztat-0", program=12),
        "blue": Music("warsztat-1", program=97),
    }
    time = 0.0
    while True:
        start = monotonic()
        ret, frame = cap.read()
        if not ret:
            break

        loop(time, frame, musicbox)
        if cv.waitKey(1) == ord("q"):
            break
        time += monotonic() - start

    # When everything done, release the capture
    cap.release()
    cv.destroyAllWindows()
