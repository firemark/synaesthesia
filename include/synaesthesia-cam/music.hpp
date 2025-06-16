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

    struct MusicConfig
    {
        uint8_t channel;
        uint8_t program;
        float volume;
        float pitch;
        float polytouch;
        float sostain;
        float sostenuto;
    };

    class Music
    {
    public:
        Music(std::shared_ptr<RtMidiOut> midi, MusicConfig config)
            : midi_(midi), //
              notes_{
                  {60},
                  {62},
                  {64},
                  {65},
                  {67},
                  {69},
                  {72}},
              channel_(config.channel)
        {
            set_program(config.program);
            set_volume(config.volume);
            set_pitch(config.pitch);
            set_polytouch(config.polytouch);
            set_sostain(config.sostain);
            set_sostenuto(config.sostenuto);
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
                std::vector<uint8_t> msg = {id(0x90), note.note(), volume_};
                midi_->sendMessage(&msg);
            }
        }

        void note_off(size_t index)
        {
            auto &note = notes_.at(index);
            if (note.set(NoteState::Off))
            {
                std::vector<uint8_t> msg = {id(0x80), note.note(), volume_};
                midi_->sendMessage(&msg);
            }
        }

        void set_program(uint8_t program)
        {
            std::vector<uint8_t> msg = {id(0xC0), program};
            midi_->sendMessage(&msg);
        }

        void set_volume(float v)
        {
            volume_ = static_cast<float>(std::abs(v) * 0x7F);
        }

        void set_pitch(float v)
        {
            auto pitch = static_cast<uint16_t>(v * 0x1FFF);
            std::vector<uint8_t> msg = {id(0xE0), pitch >> 7, pitch & 0xFF};
            midi_->sendMessage(&msg);
        }

        void set_polytouch(float v)
        {
            auto vv = std::abs(static_cast<uint8_t>(v * 0xFF));
            std::vector<uint8_t> msg = {id(0xD0), vv};
            midi_->sendMessage(&msg);
        }

        void set_sostain(float v)
        {
            auto vv = std::abs(static_cast<uint8_t>(v * 0xFF));
            std::vector<uint8_t> msg = {id(0x64), vv};
            midi_->sendMessage(&msg);
        }

        void set_sostenuto(float v)
        {
            auto vv = std::abs(static_cast<uint8_t>(v * 0xFF));
            std::vector<uint8_t> msg = {0x66, vv};
            midi_->sendMessage(&msg);
        }

    private:
        constexpr uint8_t id(uint8_t first_id) { return first_id + channel_; }
        std::shared_ptr<RtMidiOut> midi_;
        std::vector<Note> notes_;
        uint8_t channel_;
        uint8_t volume_ = 0x40;
    };

    class MusicBox
    {
    public:
        MusicBox(std::chrono::microseconds period, std::unordered_map<std::string, Music> musics) : musics_(std::move(musics)), period_(period)
        {
        }

        constexpr std::chrono::microseconds const period() { return period_; }
        constexpr std::chrono::microseconds period(std::chrono::microseconds period) { return period_ = period; }
        inline Music &music(const std::string &key) { return musics_.at(key); }

    private:
        std::unordered_map<std::string, Music> musics_;
        std::chrono::microseconds period_;
    };
}