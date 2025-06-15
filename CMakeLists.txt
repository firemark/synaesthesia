cmake_minimum_required(VERSION 3.15...4.0)

project(
  synaesthesia
  VERSION 1.0
  LANGUAGES CXX)

# find_package(ASIO REQUIRED)
find_package(OpenCV REQUIRED)

add_executable(synaesthesia
  src/synaesthesia-cam/runner.cpp
  src/synaesthesia-cam/main.cpp)
target_compile_options(synaesthesia PUBLIC -std=c++20 -Wall -Wfloat-conversion)
target_include_directories(synaesthesia PUBLIC include/ ${OpenCV_INCLUDE_DIRS})
target_link_libraries(synaesthesia PRIVATE ${OpenCV_LIBS} rtmidi )
