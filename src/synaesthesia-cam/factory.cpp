#include "synaesthesia-cam/factory.hpp"

namespace syna {
    static cv::Scalar _color(uint8_t r, uint8_t g, uint8_t b)
    {
        return cv::Scalar_<uint8_t>(b, g, r);
    }

    static std::shared_ptr<RtMidiOut> find_midi(const std::string &query)
    {
        std::shared_ptr<RtMidiOut> midi = std::make_shared<RtMidiOut>();

        unsigned int n = midi->getPortCount();
        for (unsigned int i = 0; i < n; i++)
        {
            auto name = midi->getPortName(i);
            auto name_first_part = name.substr(0, name.find(':'));
            if (name_first_part == query)
            {
                midi->openPort(i, name);
                return midi;
            }
        }

        throw std::runtime_error("midi not found.");
    }

    std::shared_ptr<Runner> create_runner(Json::Value &root)
    {
        auto midi = find_midi(root["midi"].asString());
        std::unordered_map<std::string, Music> musics;
        std::unordered_map<std::string, MaskConfig> color_configs;

        uint8_t channel = 0;
        uint8_t mask_index = 1;
        auto &root_music = root["music"];
        for (auto it = root_music.begin(); it != root_music.end(); it++)
        {
            auto key = it.key().asString();
            auto &music = *it;
            auto &color = music["color"];

            MusicConfig music_config{
                .bank = static_cast<uint16_t>(music["bank"].asInt()),
                .channel = channel++,
                .program = static_cast<uint8_t>(music["program"].asInt()),
                .volume = music["volume"].asFloat(),
                .pitch = music["pitch"].asFloat(),
                .polytouch = music["polytouch"].asFloat(),
                .modwheel = music["modwheel"].asFloat(),
                .reverb = music["reverb"].asFloat(),
                .chorus = music["chorus"].asFloat(),
                .sustain = music["sustain"].asFloat(),
                .sostenuto = music["sostenuto"].asFloat(),
            };
            MaskConfig mask_config{
                .index = mask_index++,
                .color = _color(color[0].asInt(), color[1].asInt(), color[2].asInt()),
                .h = music["h"].asFloat(),
                .v = music["v"].asFloat(),
                .s = music["s"].asFloat(),
            };
            musics.emplace(key, Music{midi, std::move(music_config)});
            color_configs.emplace(key, std::move(mask_config));
        }

        auto &camera_root = root["camera"];
        auto &crop_root = camera_root["crop"];
        std::optional<std::tuple<Point, Point>> crop = {};
        if (crop_root["on"].asBool())
        {
            auto &p0_json = crop_root["p0"];
            auto &p1_json = crop_root["p1"];
            Point p0{p0_json[0].asInt(), p0_json[1].asInt()};
            Point p1{p1_json[0].asInt(), p1_json[1].asInt()};
            crop = {{std::move(p0), std::move(p1)}};
        }
        CameraConfig camera_config{
            .source = camera_root.isMember("source") ? camera_root["source"].asInt() : 0,
            .width = camera_root.isMember("width") ? camera_root["width"].asInt() : 1280,
            .height = camera_root.isMember("height") ? camera_root["height"].asInt() : 720,
            .flip = camera_root.isMember("flip") ? camera_root["flip"].asInt() : 0,
            .crop = std::move(crop),
        };

        auto period = std::chrono::seconds(root["period"].asInt());
        return std::make_shared<Runner>(
            MusicBox{period, std::move(musics)},
            std::move(color_configs),
            std::move(camera_config));
    }
}
