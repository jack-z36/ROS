cmake_minimum_required(VERSION 3.8)
project(baton_mini)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(USE_ROS "Enable ROS support" ON)

find_package(OpenCV REQUIRED)

set(SOURCE_FILES
  src/sdk/Base64.cpp
  src/sdk/CHttpRequest.cpp
  src/sdk/cJSON.cpp
  src/sdk/CommonSocket.cpp
  src/sdk/syslib.cpp
  src/sdk/vio_msg.cpp
  src/sdk/vio_sdk.cpp
  src/baton_cmd.cpp
  src/baton_mini.cpp
)

set(COMMON_INCLUDE_DIRS
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${OpenCV_INCLUDE_DIRS}
)

if(USE_ROS)
  set(X_ROS_VERSION $ENV{ROS_VERSION})
  if(NOT X_ROS_VERSION)
    set(X_ROS_VERSION 1)
  endif()

  if("${X_ROS_VERSION}" STREQUAL "2")
    if(CMAKE_VERSION VERSION_LESS 3.8)
      message(FATAL_ERROR "ROS2 build requires CMake >= 3.8")
    endif()

    add_definitions(-DBATON_USE_ROS -DROS2)
    find_package(ament_cmake REQUIRED)
    find_package(rclcpp REQUIRED)
    find_package(nav_msgs REQUIRED)
    find_package(sensor_msgs REQUIRED)

    list(APPEND SOURCE_FILES src/io/ros_interface.cpp)

    add_executable(baton_mini ${SOURCE_FILES})
    target_include_directories(baton_mini PRIVATE ${COMMON_INCLUDE_DIRS})
    target_link_libraries(baton_mini ${OpenCV_LIBS} pthread)
    ament_target_dependencies(
      baton_mini
      rclcpp
      nav_msgs
      sensor_msgs
    )

    install(TARGETS baton_mini DESTINATION lib/${PROJECT_NAME})
    install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

    ament_package()
  else()
    add_definitions(-DBATON_USE_ROS)
    find_package(catkin REQUIRED COMPONENTS
      roscpp
      nav_msgs
      sensor_msgs
    )

    catkin_package(
      INCLUDE_DIRS include
    )

    list(APPEND SOURCE_FILES src/io/ros_interface.cpp)

    add_executable(baton_mini ${SOURCE_FILES})
    target_include_directories(
      baton_mini
      PRIVATE
        ${catkin_INCLUDE_DIRS}
        ${COMMON_INCLUDE_DIRS}
    )
    target_link_libraries(baton_mini
      ${catkin_LIBRARIES}
      ${OpenCV_LIBS}
      pthread
    )
  endif()
else()
  message(STATUS "Building without ROS support")
  add_executable(baton_mini ${SOURCE_FILES})
  target_include_directories(baton_mini PRIVATE ${COMMON_INCLUDE_DIRS})
  target_link_libraries(baton_mini ${OpenCV_LIBS} pthread)
endif()
