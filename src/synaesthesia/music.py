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
    DELTA = 300

    def __init__(self, portname="warsztat-0", program=5):
        self.notes = {i: Note(note) for i, note in enumerate(self.NOTES)}
        self.port = open_output(portname, autoreset=True)
        self.velocity = 127 
        self.note_period = 0.01

        self.change_program(program)

    def change_program(self, program: int):
        self.port.send(Message("program_change", program=program))

    def get_len_notes(self):
        return len(self.NOTES)

    def note_on(self, note_id: int):
        self._note_set(note_id, "on", velocity=self.velocity, time=self.DELTA)

    def note_off(self, note_id: int):
        self._note_set(note_id, "off")

    def _note_set(self, note_id: int, action: str, **kwargs):
        note = self.notes[note_id]
        if note.state == action:
            return

        now = monotonic()
        if now - note.timestamp < self.note_period:
            return

        note.state = action
        note.timestamp = now

        msg = Message(f"note_{action}", note=note.note, **kwargs)
        self.port.send(msg)

