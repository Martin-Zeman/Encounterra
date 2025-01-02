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

find_package(blaze REQUIRED)
find_package(LAPACK REQUIRED)

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
file (GLOB UTILS "utils/*.cpp")
list (APPEND SOURCES ${ABILITIES} ${ACTIONS} ${COMBATANTS} ${EFFECTS} ${SPELLS} ${UTILS})

#----LIBRARY CREATION----
add_library (${PROJECT_NAME}_lib ${SOURCES})

add_library( blaze_target INTERFACE )
target_link_libraries( blaze_target INTERFACE blaze::blaze )

target_link_libraries(${PROJECT_NAME}_lib PUBLIC blaze_target OpenSSL::SSL OpenSSL::Crypto ${LAPACK_LIBRARIES})

#----BINARY CREATION----
add_executable(${PROJECT_NAME} "main.cpp")
target_link_libraries(${PROJECT_NAME} ${PROJECT_NAME}_lib)

# Set the output directory for the binary
set_target_properties(${PROJECT_NAME} PROPERTIES
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