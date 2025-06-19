#include <iostream>
#include <thread>
#include <string>
#include <vector>
#include <fstream>

#include <opencv2/imgcodecs.hpp>

#include "synaesthesia-cam/factory.hpp"
#include "synaesthesia-cam/conn.hpp"

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
            cv::imwrite("/dev/shm/warsztat.png", frame);
            auto end = get_time();
            time += std::chrono::duration_cast<decltype(time)>(end - begin);
        }
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