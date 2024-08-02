cmake_minimum_required(VERSION 3.22.1)
project(encounterra.test)
enable_testing()

file (GLOB TEST_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_executable(test_encounterra ${TEST_SOURCES})
target_link_libraries(test_encounterra gtest gtest_main)
add_test( test_encounterra test_encounterra )