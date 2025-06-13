#pragma once
#include <opencv2/core/mat.hpp>

namespace syna
{
    struct MaskConfig
    {
        size_t index;
        cv::Scalar color;
        double h;
        double v = 0.3;
        double s = 0.3;
    };

    struct Mask
    {
        MaskConfig config;
        cv::Mat mask;
    };
}