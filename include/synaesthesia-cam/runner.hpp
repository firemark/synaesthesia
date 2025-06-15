#pragma once
#include <unordered_map>
#include <opencv2/core.hpp>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-enum-enum-conversion"
#include <opencv2/videoio.hpp>
#include <opencv2/imgproc.hpp>
#pragma GCC diagnostic pop

#include <synaesthesia-cam/mask.hpp>
#include <synaesthesia-cam/music.hpp>

namespace syna
{

    class Runner
    {
    public:
        Runner(MusicBox musicbox, std::unordered_map<std::string, MaskConfig> colors, int source = 4);
        cv::Mat get_frame();
        std::chrono::microseconds loop(cv::Mat &frame, std::chrono::microseconds time);

    private:
        std::unordered_map<std::string, Mask> get_colors(cv::Mat &frame);
        Mask color_to_mask(const cv::Mat &h, const cv::Mat &s, const cv::Mat &v, const MaskConfig &config);
        void play(int x_progress, const cv::Mat &frame, const std::unordered_map<std::string, Mask> &colors);
        void draw(int x_progress, cv::Mat &frame, const std::unordered_map<std::string, Mask> &colors);

        MusicBox musicbox_;
        std::unordered_map<std::string, MaskConfig> colors_;
        cv::VideoCapture camera_;
        bool fail_ = false;
    };

}
