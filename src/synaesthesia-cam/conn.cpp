#include "synaesthesia-cam/conn.hpp"
#include <asio.hpp>

namespace syna::conn
{
    using asio::awaitable;
    using asio::co_spawn;
    using asio::detached;
    using asio::use_awaitable;
    using asio::ip::tcp;
    namespace this_coro = asio::this_coro;

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

    static awaitable<void> listener(std::shared_ptr<Runner> runner_ptr)
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
                std::cerr << without_newline << std::endl;
                std::cerr.flush();
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
                if (parts[0] == "camera")
                {
                    if (parts[1] == "flip")
                    {
                        auto val = std::stoi(parts[2]);
                        runner.camera_config().flip = val;
                    }
                    if (parts[1] == "crop")
                    {
                        if (parts.size() == 6)
                        {
                            Point p0{std::stoi(parts[2]), std::stoi(parts[3])};
                            Point p1{std::stoi(parts[4]), std::stoi(parts[5])};
                            runner.camera_config().crop = {{p0, p1}};
                        }
                        else
                        {
                            runner.camera_config().crop = {};
                        }
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
                    else if (parts[1] == "sustain")
                    {
                        music.set_sustain(val);
                    }
                    else if (parts[1] == "sostenuto")
                    {
                        music.set_sostenuto(val);
                    }
                    else if (parts[1] == "chorus")
                    {
                        music.set_chorus(val);
                    }
                    else if (parts[1] == "modwheel")
                    {
                        music.set_modwheel(val);
                    }
                    else if (parts[1] == "reverb")
                    {
                        music.set_reverb(val);
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