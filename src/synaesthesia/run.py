#!/usr/bin/env python3
from subprocess import Popen
from time import sleep


def main():
    processes = [
        Popen(["fluidsynth", "--portname", "warsztat-0"]),
        Popen(["fluidsynth", "--portname", "warsztat-1"]),
    ]
    try:
        while True:
            sleep(100000.0)
    finally:
        for p in processes:
            p.kill()