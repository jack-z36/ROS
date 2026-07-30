cmake_minimum_required(VERSION 3.22)
project(octopus VERSION 1.0.1129 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/3rdparty/cmake-modules)

set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

add_subdirectory(3rdparty/glm EXCLUDE_FROM_ALL)
add_subdirectory(3rdparty/json EXCLUDE_FROM_ALL)
add_subdirectory(3rdparty/spdlog EXCLUDE_FROM_ALL)

# zstd: only use the bundled CMake project when it is complete and is not a
# symlink.  This repository snapshot can omit build/cmake because its parent
# .gitignore matches "*build*"; a self-referential replacement would otherwise
# make add_subdirectory() recurse through build/cmake indefinitely.
set(ZSTD_CMAKE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/3rdparty/zstd/build/cmake")
if(EXISTS "${ZSTD_CMAKE_DIR}/CMakeLists.txt"
   AND EXISTS "${ZSTD_CMAKE_DIR}/lib/CMakeLists.txt"
   AND NOT IS_SYMLINK "${ZSTD_CMAKE_DIR}")
  message(STATUS "Using bundled zstd from ${ZSTD_CMAKE_DIR}")
  set(ZSTD_BUILD_STATIC ON)
  set(ZSTD_BUILD_SHARED OFF)
  add_subdirectory("${ZSTD_CMAKE_DIR}" 3rdparty/zstd EXCLUDE_FROM_ALL)
else()
  find_package(zstd CONFIG REQUIRED)
  add_library(libzstd ALIAS zstd::libzstd_static)
  message(STATUS "Using system zstd: zstd::libzstd_static")
endif()

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)
set(QT_NO_PRIVATE_MODULE_WARNING ON)

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(hwk_pressure_interfaces REQUIRED)
find_package(FFmpeg REQUIRED)
find_package(assimp 5.2 REQUIRED)
find_package(Qt6 6.8 COMPONENTS Core Gui GuiPrivate Widgets Charts LinguistTools ShaderTools REQUIRED)

configure_file(src/version.h.in ${PROJECT_BINARY_DIR}/version.h @ONLY)

file(GLOB_RECURSE SOURCES src/*.cpp)

set(TS_FILES languages/scanner_en_US.ts languages/scanner_zh_CN.ts)
qt6_create_translation(QM_FILES ${SOURCES} ${TS_FILES} OPTIONS -locations none -no-obsolete)

add_executable(${PROJECT_NAME} ${SOURCES} scanner.qrc ${QM_FILES})
target_compile_definitions(${PROJECT_NAME} PUBLIC MCAP_COMPRESSION_NO_LZ4)
target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)

qt_add_shaders(${PROJECT_NAME} "qrhi_shaders"
        PREFIX
        "/"
        FILES
        "resources/shaders/vertex.vert"
        "resources/shaders/instancing.vert"
        "resources/shaders/fragment.frag"
        "resources/shaders/gray.frag"
        "resources/shaders/yuv.frag"
        "resources/shaders/yuva.frag"
        "resources/shaders/yuv_p10.frag"
        "resources/shaders/yuv_p10_bt2020_pq.frag"
        "resources/shaders/yuyv.frag"
        "resources/shaders/uyvy.frag"
        "resources/shaders/nv12.frag"
        "resources/shaders/nv21.frag"
        "resources/shaders/nv12_bt2020_pq.frag"
        "resources/shaders/rgba.frag"
        "resources/shaders/bgra.frag"
        "resources/shaders/argb.frag"
        "resources/shaders/abgr.frag"
        "resources/shaders/gbrp.frag"
        "resources/shaders/pal8.frag"
        "resources/shaders/lut.frag"
        "resources/shaders/video.vert"
)

target_link_libraries(${PROJECT_NAME}
        PRIVATE
        rclcpp::rclcpp
        ffmpeg::ffmpeg
        glm::glm
        nlohmann_json::nlohmann_json
        assimp::assimp
        spdlog::spdlog
        libzstd
        Qt6::Core Qt6::Gui Qt6::Widgets Qt6::GuiPrivate Qt6::Charts
        ${sensor_msgs_TARGETS}
        ${nav_msgs_TARGETS}
        ${hwk_pressure_interfaces_TARGETS}
)

target_include_directories(${PROJECT_NAME}
        PRIVATE
        src
        3rdparty/mcap/cpp/mcap/include
        ${PROJECT_BINARY_DIR}
)

install(TARGETS
        ${PROJECT_NAME}
        DESTINATION lib/${PROJECT_NAME}
)

install(FILES
        ${QM_FILES}
        DESTINATION lib/${PROJECT_NAME}/translations
)

install(DIRECTORY
        resources/models
        DESTINATION lib/${PROJECT_NAME}
)

ament_package()
