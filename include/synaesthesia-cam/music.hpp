#pragma once
#include <unordered_map>
#include <string>
#include <chrono>
#include <memory>

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
        bool set(NoteState state);

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
        float modwheel;
        float reverb;
        float chorus;
        float sustain;
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
                  {72},
                  {74},
                  {76},
                  {77},
                  {79},
                  {81},
                  {83},
                  {87},
              },
              channel_(config.channel)
        {
            set_program(config.program);
            set_volume(config.volume);
            set_pitch(config.pitch);
            set_polytouch(config.polytouch);
            set_modwheel(config.modwheel);
            set_reverb(config.reverb);
            set_chorus(config.chorus);
            set_sustain(config.sustain);
            set_sostenuto(config.sostenuto);
        }

        size_t get_len_notes();
        void note_on(size_t index);
        void note_off(size_t index);
        void set_program(uint8_t program);
        void set_volume(float v);
        void set_pitch(float v);
        void set_modwheel(float v);
        void set_polytouch(float v);
        void set_reverb(float v);
        void set_chorus(float v);
        void set_sustain(float v);
        void set_sostenuto(float v);

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