cmake_minimum_required(VERSION 3.10)
project(SatTradeAlphaPrime)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(alpha_terminal 
    Terminal.cpp
)

# Include directories
target_include_directories(alpha_terminal PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Optimization flags for institutional speed
if(MSVC)
    target_compile_options(alpha_terminal PRIVATE /O2 /Oi /Ot /GL)
else()
    target_compile_options(alpha_terminal PRIVATE -O3 -march=native -flto)
endif()
