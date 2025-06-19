#include "synaesthesia-cam/runner.hpp"

#include <opencv2/imgproc.hpp>

namespace syna
{
    Runner::Runner(MusicBox musicbox, std::unordered_map<std::string, MaskConfig> colors, CameraConfig camera_config) //
        : musicbox_(musicbox), colors_(colors), camera_(camera_config.source), camera_config_(camera_config)
    {
        camera_.set(cv::CAP_PROP_FRAME_WIDTH, camera_config.width);
        camera_.set(cv::CAP_PROP_FRAME_HEIGHT, camera_config.height);
        camera_.set(cv::CAP_PROP_BUFFERSIZE, 3);
        if (!camera_.isOpened())
        {
            std::cerr << "Could not open camera." << std::endl;
            fail_ = true;
            return;
        }
    }

    cv::Mat Runner::get_frame()
    {
        cv::Mat frame;
        camera_.read(frame);
        if (frame.empty())
        {
            return frame;
        }

        if (camera_config_.flip)
        {
            cv::flip(frame, frame, camera_config_.flip);
        }

        if (camera_config_.crop.has_value())
        {
            auto &[p0, p1] = camera_config_.crop.value();
            cv::Rect roi(p0.x, p0.y, p1.x - p0.x, p1.y - p0.y);
            frame = frame(roi);
        }

        return frame;
    }

    std::chrono::microseconds Runner::loop(cv::Mat &frame, std::chrono::microseconds time)
    {
        auto period = musicbox_.period();
        time = time % period;
        auto progress = static_cast<double>(time.count()) / static_cast<double>(period.count());
        auto x_progress = static_cast<int>((frame.size().width - 1) * progress);
        auto colors = get_colors(frame);
        play(x_progress, frame, colors);
        draw(x_progress, frame, colors);

        return time;
    }

    std::unordered_map<std::string, Mask> Runner::get_colors(cv::Mat &frame)
    {
        cv::Mat h, s, v;
        {
            cv::Mat hsv_int;
            cv::Mat hsv;
            cv::cvtColor(frame, hsv_int, cv::COLOR_BGR2HSV_FULL);
            hsv_int.convertTo(hsv, CV_64F);
            hsv /= 255.0;
            cv::extractChannel(hsv, h, 0);
            cv::extractChannel(hsv, s, 1);
            cv::extractChannel(hsv, v, 2);
        }

        std::unordered_map<std::string, Mask> colors;
        for (const auto &[name, config] : colors_)
        {
            colors[name] = color_to_mask(h, s, v, config);
        }
        return colors;
    }

    Mask Runner::color_to_mask(const cv::Mat &h, const cv::Mat &s, const cv::Mat &v, const MaskConfig &config)
    {
        auto next_h = config.h + 0.2;
        cv::Mat mask = cv::Mat::ones(h.size(), CV_8UC1);
        mask &= v > config.v;
        mask &= s > config.s;
        if (next_h > 1.0)
        {
            mask &= (h > config.h) | (h < next_h - 1.0);
        }
        else
        {
            mask &= (h > config.h) & (h < config.h);
        }

        static cv::Mat kernel = getStructuringElement(cv::MORPH_ELLIPSE,
                                                      cv::Size(2 * 2 + 1, 2 * 2 + 1),
                                                      cv::Point(2, 2));

        cv::Mat mask_e;
        cv::Mat mask_d;
        cv::Mat mask_c;
        cv::erode(mask, mask_e, kernel);
        cv::dilate(mask_e, mask_d, kernel);
        cv::morphologyEx(mask_d, mask_c, cv::MORPH_CLOSE, kernel);

        return {config, mask_c};
    }

    void Runner::play(int x_progress, const cv::Mat &frame, const std::unordered_map<std::string, Mask> &colors)
    {
        cv::Mat music_array = cv::Mat::zeros(frame.size(), CV_8U);
        for (const auto &[name, color] : colors)
        {
            auto &music = musicbox_.music(name);
            auto notes_total = music.get_len_notes();
            auto span = (frame.size().height - 1) / notes_total;
            size_t h = 0;
            for (size_t n = 0; n < notes_total; n++)
            {
                cv::Rect row_rect(x_progress, h, 1, span);
                cv::Mat row_mask = color.mask(row_rect);
                auto count = cv::sum(row_mask)[0];
                if (count > 0)
                {
                    music.note_on(n);
                }
                else
                {
                    music.note_off(n);
                }
                h += span;
            }
        }
    }

    void Runner::draw(int x_progress, cv::Mat &frame, const std::unordered_map<std::string, Mask> &colors)
    {
        {
            cv::Mat grayscale;
            cv::cvtColor(frame, grayscale, cv::COLOR_BGR2GRAY);
            cv::cvtColor(grayscale, frame, cv::COLOR_GRAY2BGR);
        }

        {
            cv::Mat color_mask;
            for (const auto &[name, color] : colors)
            {
                cv::addWeighted(frame, 0.5, color.config.color, 0.5, 0.0, color_mask);
                color_mask.copyTo(frame, color.mask);
            }
        }

        {
            static auto BLACK = cv::Scalar_<uint8_t>(0, 0, 0);
            cv::line(frame, {x_progress, 0}, {x_progress, frame.size().height - 1}, BLACK, 2);
        }
    }
}