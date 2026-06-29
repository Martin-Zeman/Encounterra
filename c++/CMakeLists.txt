# How to use:
# 1) Navigate to the build directory
# 2) Run "cmake .."
# 3) Run "make build" or "cmake --build . --config Release"
# 4) Optional: Run "make runtests" to start the units tests

cmake_minimum_required(VERSION 3.22.1)

project ("encounterra")

set (ENCOUNTERRA_VERSION_MAJOR 1)
set (ENCOUNTERRA_VERSION_MINOR 0)

set (COMMON_INCLUDES ${PROJECT_SOURCE_DIR})
set (GOOGLE_TEST_DIR ${PROJECT_SOURCE_DIR}/googletest)

set(CMAKE_CXX_STANDARD 20)

# Set default build type to Debug if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

message ("PROJECT_SOURCE_DIR = ${PROJECT_SOURCE_DIR}")
message ("PROJECT_BINARY_DIR = ${PROJECT_BINARY_DIR}")
message ("CMAKE_BUILD_TYPE = ${CMAKE_BUILD_TYPE}")

# sudo apt-get install libssl-dev
find_package(OpenSSL REQUIRED)

# Try to find blaze - first attempt system paths, then fallback to local copy if system is inaccessible
find_package(blaze QUIET)

if(NOT blaze_FOUND)
    message(STATUS "System blaze not found, attempting local .blaze-cmake copy...")
    get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}" DIRECTORY)
    set(blaze_DIR "${REPO_ROOT}/.blaze-cmake" CACHE PATH "Path to blaze CMake config" FORCE)
    message(STATUS "Using local blaze configuration: ${blaze_DIR}")
    find_package(blaze REQUIRED)
else()
    message(STATUS "Found system blaze installation")
endif()

find_package(LAPACK REQUIRED)

# Required for std::thread (parallel, multi-core simulation runs in main.cpp).
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

#----GOOGLETEST BUILD----
add_subdirectory(${GOOGLE_TEST_DIR})

#----INCLUDE DIRECTORIES----
include_directories (${COMMON_INCLUDES} ${GTEST_INCLUDE_DIRS} ${OPENSSL_INCLUDE_DIR})

#----LIBRARY SOURCES----
# file (GLOB SOURCES "*.cpp")
file (GLOB SOURCES "core/*.cpp")
file (GLOB ABILITIES "abilities/*.cpp")
file (GLOB ACTIONS "actions/*.cpp")
file (GLOB COMBATANTS "combatants/*.cpp")
file (GLOB EFFECTS "effects/*.cpp")
file (GLOB SPELLS "spells/*.cpp")
file (GLOB UTILS "spells/*.cpp")
list (APPEND SOURCES ${ABILITIES} ${ACTIONS} ${COMBATANTS} ${EFFECTS} ${SPELLS} ${UTILS})

#----LIBRARY CREATION----
add_library (${PROJECT_NAME}_lib ${SOURCES})

add_library( blaze_target INTERFACE )
target_link_libraries( blaze_target INTERFACE blaze::blaze )

target_link_libraries(${PROJECT_NAME}_lib PUBLIC blaze_target OpenSSL::SSL OpenSSL::Crypto ${LAPACK_LIBRARIES} Threads::Threads)

#----BINARY CREATION----
add_executable(${PROJECT_NAME} "main.cpp")
target_link_libraries(${PROJECT_NAME} ${PROJECT_NAME}_lib)

# Set the output directory for the binary
set_target_properties(${PROJECT_NAME} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

#----STANDALONE RANDOM-MATCHUP TEST----
# Separate executable: two randomly built teams (each 2-4 random combatants) fight.
# NOT part of test_encounterra and NOT registered with ctest.
add_executable(random_matchup "random_matchup.cpp")
target_link_libraries(random_matchup ${PROJECT_NAME}_lib)
set_target_properties(random_matchup PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

#----TESTING----
# Test each module separately
add_subdirectory(test)

#----CUSTOM TARGET TO TRIGGER THE BUILD WITH A CMAKE COMMAND INSTEAD OF MAKE----
add_custom_target (build
    COMMAND ${CMAKE_COMMAND} --build ${PROJECT_BINARY_DIR} --config ${CMAKE_BUILD_TYPE}
	COMMENT "Running the build..."
	)

#----CUSTOM TARGET TO RUN THE UNIT TESTS----
add_custom_target (runtests
    COMMAND ${CMAKE_CTEST_COMMAND} --build-config ${CMAKE_BUILD_TYPE} --extra-verbose
    WORKING_DIRECTORY ${PROJECT_BINARY_DIR}/test
	COMMENT "Starting the unit tests..."
	)