#pragma once
#include <unordered_map>
#include <string>
#include <chrono>

#include <rtmidi/RtMidi.h>

namespace syna
{
    enum class NoteState : uint8_t
    {
        On = 1,
        Off = 0
    };

    class Note
    {
    public:
        Note(uint8_t note) : note_(note), timestamp_(std::chrono::steady_clock::now()) {}
        constexpr uint8_t note() const { return note_; }

        bool set(NoteState state)
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

    private:
        uint8_t note_;
        std::chrono::steady_clock::time_point timestamp_;
        NoteState state_ = NoteState::Off;
    };

    class Music
    {
    public:
        Music(std::shared_ptr<RtMidiOut> midi, uint8_t channel, uint8_t program)
            : midi_(midi), //
              notes_{
                  {60},
                  {62},
                  {64},
                  {65},
                  {67},
                  {69},
                  {72}},
              channel_(channel), program_(program)
        {
        }

        size_t get_len_notes()
        {
            return notes_.size();
        }

        void note_on(size_t index)
        {
            auto &note = notes_.at(index);
            if (note.set(NoteState::On))
            {
                std::vector<uint8_t> msg = {(uint8_t)0x90 + channel_, note.note(), 90};
                midi_->sendMessage(&msg);
            }
        }

        void note_off(size_t index)
        {
            auto &note = notes_.at(index);
            if (note.set(NoteState::Off))
            {
                std::vector<uint8_t> msg = {(uint8_t)0x80 + channel_, note.note(), 90};
                midi_->sendMessage(&msg);
            }
        }

    private:
        std::shared_ptr<RtMidiOut> midi_;
        std::vector<Note> notes_;
        uint8_t channel_;
        uint8_t program_;
    };

    class MusicBox
    {
    public:
        MusicBox(std::chrono::microseconds period, std::unordered_map<std::string, Music> musics) : musics_(std::move(musics)), period_(period)
        {
        }

        constexpr std::chrono::microseconds const period() { return period_; }
        inline Music &music(const std::string &key) { return musics_.at(key); }

    private:
        std::unordered_map<std::string, Music> musics_;
        std::chrono::microseconds period_;
    };
}