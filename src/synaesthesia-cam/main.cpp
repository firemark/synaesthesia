#include <iostream>
#include <thread>
#include <string>
#include <vector>
#include <fstream>

#include <opencv2/imgcodecs.hpp>
#include <asio.hpp>
#include <jsoncpp/json/json.h>

#include <synaesthesia-cam/runner.hpp>

namespace syna
{
    static std::chrono::steady_clock::time_point get_time()
    {
        return std::chrono::steady_clock::now();
    }

    void play_music(std::stop_token stoken, std::shared_ptr<Runner> runner)
    {
        std::chrono::microseconds time(0);
        while (!stoken.stop_requested())
        {
            auto begin = get_time();
            auto frame = runner->get_frame();
            if (frame.empty())
            {
                return;
            }
            {
                std::lock_guard lock(runner->mutex());
                time = runner->loop(frame, time);
            }
            static uint8_t i = 0;
            if ((i++ % 128) == 0)
            {
                cv::imwrite("/tmp/test.jpg", frame);
            }
            auto end = get_time();
            time += std::chrono::duration_cast<decltype(time)>(end - begin);
        }
    }

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

    static std::vector<std::string> string_split(std::string s, const char delimiter)
    {
        size_t start = 0;
        size_t end = s.find_first_of(delimiter);

        std::vector<std::string> output;

        while (end <= std::string::npos)
        {
            output.emplace_back(s.substr(start, end - start));

            if (end == std::string::npos)
                break;

            start = end + 1;
            end = s.find_first_of(delimiter, start);
        }

        return output;
    }

    static std::shared_ptr<Runner> create_runner(Json::Value &root)
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
                .channel = channel++,
                .program = music["program"].asInt(),
                .volume = music["volume"].asFloat(),
                .pitch = music["pitch"].asFloat(),
                .polytouch = music["polytouch"].asFloat(),
                .sostain = music["sostain"].asFloat(),
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

        auto period = std::chrono::seconds(root["period"].asInt());
        return std::make_shared<Runner>(
            MusicBox{period, std::move(musics)},
            std::move(color_configs),
            root["camera_source"].asInt());
    }
}

namespace syna::conn
{

    using asio::awaitable;
    using asio::co_spawn;
    using asio::detached;
    using asio::use_awaitable;
    using asio::ip::tcp;
    namespace this_coro = asio::this_coro;

    awaitable<void> listener(std::shared_ptr<Runner> runner_ptr)
    {
        auto listen = [runner_ptr](tcp::socket socket) -> awaitable<void>
        {
            for (;;)
            {
                std::string read_msg;
                size_t n = co_await asio::async_read_until( //
                    socket,
                    asio::dynamic_buffer(read_msg, 1024), "\n", use_awaitable);

                if (n == 0)
                {
                    co_return;
                }

                if (read_msg == "\n")
                {
                    co_return;
                }

                auto without_newline = read_msg.substr(0, read_msg.find("\n"));
                read_msg.erase(0, n);
                auto parts = string_split(without_newline, ' ');
                if (parts.size() < 3)
                {
                    continue;
                }

                auto &runner = *runner_ptr;
                std::lock_guard lock(runner.mutex());
                if (parts[0] == "music")
                {
                    if (parts[1] == "period")
                    {
                        auto count = static_cast<int>(std::stof(parts[2]) * 1e6);
                        runner.musicbox().period(std::chrono::microseconds(count));
                    }
                }
                if (parts[0] == "screen")
                {
                    if (parts[1] == "flip")
                    {
                        // TODO
                    }
                }

                if (parts[0].substr(0, 6) == "music_")
                {
                    auto key = parts[0].substr(6);
                    auto &music = runner.musicbox().music(key);
                    auto &color = runner.colors(key);
                    auto val = std::stof(parts[2]);
                    if (parts[1] == "program")
                    {
                        music.set_program(static_cast<uint8_t>(val));
                    }
                    else if (parts[1] == "volume")
                    {
                        music.set_volume(val);
                    }
                    else if (parts[1] == "pitch")
                    {
                        music.set_pitch(val);
                    }
                    else if (parts[1] == "polytouch")
                    {
                        music.set_polytouch(val);
                    }
                    else if (parts[1] == "sostain")
                    {
                        music.set_sostain(val);
                    }
                    else if (parts[1] == "sostenuto")
                    {
                        music.set_sostenuto(val);
                    }
                    else if (parts[1] == "h")
                    {
                        color.h = val;
                    }
                    else if (parts[1] == "v")
                    {
                        color.v = val;
                    }
                    else if (parts[1] == "s")
                    {
                        color.s = val;
                    }
                }
            }
        };

        auto executor = co_await this_coro::executor;
        tcp::acceptor acceptor(executor, {tcp::v4(), 2137});
        for (;;)
        {
            tcp::socket socket = co_await acceptor.async_accept(use_awaitable);
            co_spawn(executor, listen(std::move(socket)), detached);
        }
    }

    void
    run(std::shared_ptr<Runner> runner)
    {
        asio::io_context io_context;
        asio::signal_set signals(io_context, SIGINT, SIGTERM);
        signals.async_wait([&](auto, auto)
                           { io_context.stop(); });

        co_spawn(io_context, listener(runner), detached);

        io_context.run();
    }

}

int main(int argc, char **argv)
{
    if (argc < 2)
    {
        return -1;
    }

    Json::Value root;
    std::ifstream ifs;
    ifs.open(argv[1]);

    Json::CharReaderBuilder builder;
    JSONCPP_STRING errs;
    if (!parseFromStream(builder, ifs, &root, &errs))
    {
        std::cout << errs << std::endl;
        return -1;
    }

    auto runner = syna::create_runner(root);
    std::jthread camera_thread(syna::play_music, runner);
    syna::conn::run(runner);

    camera_thread.request_stop();
    camera_thread.join();

    return 0;
}