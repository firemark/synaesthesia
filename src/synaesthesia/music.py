from dataclasses import dataclass
from time import monotonic
from mido import Message, open_output
from mido.ports import BasePort


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

    def __init__(self, port: BasePort, channel: int, program=5):
        self.notes = {i: Note(note) for i, note in enumerate(self.NOTES)}
        self.port = port
        self._channel = channel
        self._note_period = 0.1
        self._effects: dict[int, int] = {}

        self.change_program(program)
        self.set_polytouch(0.0)
        self.set_pitch(0.0)
        self.set_volume(0.5)

    def get_program(self) -> int:
        return self._program

    def get_volume(self) -> float:
        return self._velocity / 127.0

    def get_pitch(self) -> float:
        return self._pitch / 8191.0

    def get_polytouch(self) -> float:
        return self._polytouch / 127.0

    def get_len_notes(self):
        return len(self.NOTES)

    def change_program(self, program: int):
        self._program = program
        self.port.send(
            Message("program_change", channel=self._channel, program=program)
        )

    def set_volume(self, volume: float):
        self._velocity = int(volume * 127)

    def set_pitch(self, value: float):
        self._pitch = int(value * 8191.0)
        self.port.send(Message("pitchwheel", channel=self._channel, pitch=self._pitch))

    def set_effect(self, id: int, value: float):
        v = int(value * 127)
        self._effects[id] = v
        self.port.send(
            Message("control_change", channel=self._channel, control=id, value=v)
        )

    def set_polytouch(self, value: float):
        self._polytouch = int(value * 127)
        self.port.send(
            Message("aftertouch", channel=self._channel, value=self._polytouch)
        )

    def note_on(self, note_id: int, add: float = 0.0):
        # pp = int(add * 1024.0)
        # self.port.send(Message("pitchwheel", channel=self._channel, pitch=pp))
        add_v = min(127, 63 + int(add * 64))
        self.port.send(
            Message("control_change", channel=self._channel, control=7, value=add_v)
        )
        self._note_set(note_id, "on", velocity=self._velocity)

    def note_off(self, note_id: int):
        self._note_set(note_id, "off", velocity=self._velocity)

    def _note_set(self, note_id: int, action: str, **kwargs):
        note = self.notes[note_id]
        if note.state == action:
            return

        now = monotonic()
        if now - note.timestamp < self._note_period:
            return

        note.state = action
        note.timestamp = now

        msg = Message(f"note_{action}", note=note.note, channel=self._channel, **kwargs)
        self.port.send(msg)


class MusicBox(dict[str, Music]):

    def __init__(self, obj: dict[str, Music]):
        super().__init__(obj)
        self.period = 10.0
