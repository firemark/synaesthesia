#include <iostream>
#include <thread>
#include <vector>

#include <asio.hpp>
#include <opencv2/imgcodecs.hpp>

#include <synaesthesia-cam/runner.hpp>

static void print(const std::error_code & /*e*/)
{
    std::cout << "Hello, world!" << std::endl;
}

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

    Runner create_runner()
    {
        std::shared_ptr<RtMidiOut> midi = std::make_shared<RtMidiOut>();
        midi->openPort(1, "warsztat");

        unsigned int nPorts = midi->getPortCount();
        for (unsigned int i = 0; i < nPorts; i++)
        {
            auto portName = midi->getPortName(i);
            std::cerr << "  Input Port #" << i + 1 << ": " << portName << '\n';
        }

        std::cerr << "midi: " << nPorts << std::endl;
        return Runner{
            MusicBox{
                std::chrono::seconds(10),
                {
                    {"red", {midi, 0, 5}},
                    {"blue", {midi, 0, 12}},
                }},
            {
                {"red", {.index = 0, .color{color(255, 0, 0)}, .h = 0.9}},
                {"blue", {.index = 1, .color{color(0, 0, 255)}, .h = 0.5}},
            }};
    }
}

int main(int argc, char **argv)
{
    std::jthread camera_thread(syna::play_music, syna::create_runner());
    // asio::io_context io;

    // asio::steady_timer t(io, asio::chrono::seconds(5));
    // t.async_wait(&print);
    // io.run();
    camera_thread.join();

    return 0;
}