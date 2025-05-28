from dataclasses import dataclass
from time import monotonic
from mido import Message, open_output


@dataclass
class Note:
    note: int
    timestamp: float = 0.0
    state: str = "off"


class Music:
    NOTES = [60, 62, 64, 67, 69, 72]
    NOTES_A = [60, 62, 64, 65, 67, 69, 71]
    NOTES_B = [60, 62, 64, 65, 67, 69, 71]
    NOTES_C = [60, 62, 64, 65, 67, 69, 71]
    DELTA = 300

    def __init__(self, portname="warsztat-0", program=5):
        self.notes = {i: Note(note) for i, note in enumerate(self.NOTES)}
        self.port = open_output(portname, autoreset=True)
        self._note_period = 0.01

        self.change_program(program)
        self.set_polytouch(0.0)
        self.set_volume(0.5)

    def get_program(self) -> int:
        return self._program

    def get_volume(self) -> float:
        return self._velocity / 127.0

    def get_polytouch(self) -> float:
        return self._polytouch / 127.0

    def get_len_notes(self):
        return len(self.NOTES)

    def change_program(self, program: int):
        self._program = program
        self.port.send(Message("program_change", program=program))

    def set_volume(self, volume: float):
        self._velocity = int(volume * 127)

    def set_polytouch(self, value: float):
        self._polytouch = int(value * 127)
        self.port.send(Message("aftertouch", value=self._polytouch))

    def note_on(self, note_id: int):
        self._note_set(note_id, "on", velocity=self._velocity, time=self.DELTA)

    def note_off(self, note_id: int):
        self._note_set(note_id, "off")

    def _note_set(self, note_id: int, action: str, **kwargs):
        note = self.notes[note_id]
        if note.state == action:
            return

        now = monotonic()
        if now - note.timestamp < self._note_period:
            return

        note.state = action
        note.timestamp = now

        msg = Message(f"note_{action}", note=note.note, **kwargs)
        self.port.send(msg)
