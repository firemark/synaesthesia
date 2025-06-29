#include "synaesthesia-cam/music.hpp"

namespace syna
{
    template <size_t I = 0x7F, typename T = uint8_t>
    static T val_to_int(double v)
    {
        return static_cast<T>(std::abs(v) * I);
    }

    bool Note::set(NoteState state)
    {
        if (state_ == state)
        {
            return false;
        }

        auto now = std::chrono::steady_clock::now();
        auto delay = now - timestamp_;
        if (delay < std::chrono::milliseconds(100))
        {
            return false;
        }

        state_ = state;
        timestamp_ = now;
        return true;
    }

    size_t Music::get_len_notes()
    {
        return notes_.size();
    }

    void Music::note_on(size_t index)
    {
        auto &note = notes_.at(index);
        if (note.set(NoteState::On))
        {
            std::vector<uint8_t> msg = {id(0x90), note.note(), volume_};
            midi_->sendMessage(&msg);
        }
    }

    void Music::note_off(size_t index)
    {
        auto &note = notes_.at(index);
        if (note.set(NoteState::Off))
        {
            std::vector<uint8_t> msg = {id(0x80), note.note(), volume_};
            midi_->sendMessage(&msg);
        }
    }

    void Music::set_bank(uint16_t bank)
    {
        std::vector<uint8_t> msg = {id(0xE0), 0, bank >> 7, bank & 0x7F};
        midi_->sendMessage(&msg);
    }

    void Music::set_program(uint8_t program)
    {
        std::vector<uint8_t> msg = {id(0xC0), program};
        midi_->sendMessage(&msg);
    }

    void Music::set_volume(float v)
    {
        volume_ = val_to_int(v);
    }

    void Music::set_pitch(float v)
    {
        auto pitch = val_to_int<0x3FFF, uint16_t>((v + 1.0) / 2.0);
        std::vector<uint8_t> msg = {id(0xE0), pitch >> 7, pitch & 0x7F};
        midi_->sendMessage(&msg);
    }

    void Music::set_modwheel(float v)
    {
        auto vv = val_to_int<0x3FFF, uint16_t>(v);
        std::vector<uint8_t> msg = {id(0xE0), 1, vv >> 7, vv & 0x7F};
        midi_->sendMessage(&msg);
    }

    void Music::set_polytouch(float v)
    {
        std::vector<uint8_t> msg = {id(0xD0), val_to_int(v)};
        midi_->sendMessage(&msg);
    }

    void Music::set_reverb(float v)
    {
        std::vector<uint8_t> msg = {id(0xB0), 91, val_to_int(v)};
        midi_->sendMessage(&msg);
    }

    void Music::set_chorus(float v)
    {
        std::vector<uint8_t> msg = {id(0xB0), 93, val_to_int(v)};
        midi_->sendMessage(&msg);
    }

    void Music::set_sustain(float v)
    {
        std::vector<uint8_t> msg = {id(0xB0), 64, val_to_int(v)};
        midi_->sendMessage(&msg);
    }

    void Music::set_sostenuto(float v)
    {
        std::vector<uint8_t> msg = {id(0xB0), 66, val_to_int(v)};
        midi_->sendMessage(&msg);
    }
}
