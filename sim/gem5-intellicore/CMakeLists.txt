cmake_minimum_required(VERSION 3.22)

project(gem5_intellicore LANGUAGES CXX)

add_library(gem5_intellicore
    src/cache_agent.cpp
)

target_include_directories(gem5_intellicore
    PUBLIC
        include
)

target_compile_features(gem5_intellicore PUBLIC cxx_std_20)

add_executable(gem5_intellicore_smoke tests/cache_agent_smoke.cpp)
target_link_libraries(gem5_intellicore_smoke PRIVATE gem5_intellicore)
