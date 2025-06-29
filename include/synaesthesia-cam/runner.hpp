#pragma once
#include <mutex>
#include <tuple>
#include <optional>
#include <unordered_map>
#include <opencv2/core.hpp>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-enum-enum-conversion"
#include <opencv2/videoio.hpp>
#pragma GCC diagnostic pop

#include <synaesthesia-cam/mask.hpp>
#include <synaesthesia-cam/music.hpp>

namespace syna
{
    struct Point { int x, y; };
    struct CameraConfig
    {
        int source = 4;
        int width = 1280;
        int height = 720;
        int flip = 0;
        std::optional<std::tuple<Point, Point>> crop = {};
    };

    class Runner
    {
    public:
        Runner(MusicBox musicbox, std::unordered_map<std::string, MaskConfig> colors, CameraConfig camera_config);
        cv::Mat get_frame();
        std::chrono::microseconds loop(cv::Mat &frame, std::chrono::microseconds time);

        MusicBox &musicbox() { return musicbox_; }
        MaskConfig &colors(const std::string &key) { return colors_.at(key); }
        CameraConfig &camera_config() { return camera_config_; }
        std::mutex &mutex() { return mutex_; }

    private:
        std::unordered_map<std::string, Mask> get_colors(cv::Mat &frame);
        Mask color_to_mask(const cv::Mat &h, const cv::Mat &s, const cv::Mat &v, const MaskConfig &config);
        void play(int x_progress, const cv::Mat &frame, const std::unordered_map<std::string, Mask> &colors);
        void draw(int x_progress, cv::Mat &frame, const std::unordered_map<std::string, Mask> &colors);

        MusicBox musicbox_;
        std::unordered_map<std::string, MaskConfig> colors_;
        cv::VideoCapture camera_;
        CameraConfig camera_config_;
        std::mutex mutex_;
        bool fail_ = false;
    };

}
