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

    void play_music(std::stop_token stoken, Runner runner)
    {
        std::chrono::microseconds time(0);
        while (!stoken.stop_requested())
        {
            auto begin = get_time();
            auto frame = runner.get_frame();
            if (frame.empty())
            {
                return;
            }
            time = runner.loop(frame, time);
            static uint8_t i = 0;
            if ((i++ % 128) == 0)
            {
                cv::imwrite("/tmp/test.jpg", frame);
            }
            auto end = get_time();
            time += std::chrono::duration_cast<decltype(time)>(end - begin);
        }
    }

    static cv::Scalar color(uint8_t r, uint8_t g, uint8_t b)
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

    static Runner create_runner(Json::Value &root)
    {
        auto midi = find_midi(root["midi"].asString());
        int source = 0;
        return Runner{
            MusicBox{
                std::chrono::seconds(root["period"].asInt()),
                {
                    {"red", {midi, 0, 5}},
                    {"blue", {midi, 0, 12}},
                }},
            {
                {"red", {.index = 0, .color{color(255, 0, 0)}, .h = 0.9}},
                {"blue", {.index = 1, .color{color(0, 0, 255)}, .h = 0.5}},
            },
            root["camera_source"].asInt()};
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

    awaitable<void> listener()
    {
        auto listen = [](tcp::socket socket) -> awaitable<void>
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

                std::cerr << read_msg << std::endl;
                read_msg.erase(0, n);
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
    run()
    {
        asio::io_context io_context;
        asio::signal_set signals(io_context, SIGINT, SIGTERM);
        signals.async_wait([&](auto, auto)
                           { io_context.stop(); });

        co_spawn(io_context, listener(), detached);

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

    syna::conn::run();

    camera_thread.request_stop();
    camera_thread.join();

    return 0;
}