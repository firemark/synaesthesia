#pragma once
#include <memory>
#include <jsoncpp/json/json.h>

#include "synaesthesia-cam/runner.hpp"

namespace syna
{
    std::shared_ptr<Runner> create_runner(Json::Value &root);
}