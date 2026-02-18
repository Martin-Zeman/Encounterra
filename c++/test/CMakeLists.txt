cmake_minimum_required(VERSION 3.22.1)
project(encounterra.test)
enable_testing()

file (GLOB TEST_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_executable(test_encounterra ${TEST_SOURCES})

# Link the main project library and include directories
target_link_libraries(test_encounterra gtest gtest_main encounterra_lib)
target_include_directories(test_encounterra PUBLIC ${COMMON_INCLUDES})

add_test(NAME test_encounterra COMMAND test_encounterra)
