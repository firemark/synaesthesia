#pragma once
#include <memory>

#include "synaesthesia-cam/runner.hpp"

namespace syna::conn
{
    void run(std::shared_ptr<Runner> runner);
}