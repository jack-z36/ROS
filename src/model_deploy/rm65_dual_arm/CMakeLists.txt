cmake_minimum_required(VERSION 3.8)
project(rm65_dual_arm)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "GNU")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(act_interfaces REQUIRED)

# ---------------------------------------------------------------------------
# 睿尔曼 C/C++ SDK 以 vendor 方式集成：头文件在 include/rm65_dual_arm/，
# libRM_Service.so 在 lib/。官方 SDK 不提供 find_package / pkg-config，
# 只能手动 include_directories + link_directories + target_link_libraries。
# 运行前需先 `sudo bash lib/install_libs.sh` 把 .so 装到系统库路径。
# ---------------------------------------------------------------------------
# include/ 作为根，使代码可用 #include "rm65_dual_arm/xxx.hpp" 引用
include_directories(include)
link_directories(${CMAKE_CURRENT_SOURCE_DIR}/lib)

# 节点可执行文件依赖厂商 SDK 头文件（rm_service.h 等）与 libRM_Service.so。
# 这些文件不随仓库提交（按 lib/SDK_VENDOR_README.txt 由开发者从官方 SDK 拷入）。
# 当 SDK 头文件缺失时，跳过节点构建，但纯逻辑测试（pose_conversion /
# target_validator / delta_guard / permit_guard）仍可编译验证。
# 这样在真机 SDK 到位前即可完成纯逻辑层的离线验证。
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/include/rm65_dual_arm/rm_service.h")
  set(RM65_SDK_AVAILABLE TRUE)
else()
  set(RM65_SDK_AVAILABLE FALSE)
  message(STATUS
    "rm65_dual_arm: 厂商 SDK 头文件 include/rm65_dual_arm/rm_service.h 未找到。\n"
    "  按说明跳过节点可执行文件构建；纯逻辑测试照常编译。\n"
    "  真机部署前请按 lib/SDK_VENDOR_README.txt 从官方 SDK 拷入头文件与 .so。")
endif()

if(RM65_SDK_AVAILABLE)
  add_executable(rm65_dual_arm_node
    src/rm65_dual_arm_node.cpp
    src/pose_conversion.cpp
    src/target_validator.cpp
    src/delta_guard.cpp
    src/permit_guard.cpp
    src/rm65_arm.cpp
  )
  target_link_libraries(rm65_dual_arm_node RM_Service)
  ament_target_dependencies(rm65_dual_arm_node
    rclcpp
    geometry_msgs
    std_msgs
    std_srvs
    act_interfaces
  )

  install(TARGETS rm65_dual_arm_node DESTINATION lib/${PROJECT_NAME})
  # 安装 SDK 库随包可被运行时找到
  install(DIRECTORY lib/ DESTINATION lib/${PROJECT_NAME}
          FILES_MATCHING PATTERN "libRM_Service.so*")
endif()

# launch/config 无论 SDK 是否就绪都安装（便于离线检查与文档引用）
install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  # 纯逻辑测试：不依赖 rclcpp / SDK，直接编译对应 .cpp 源文件。
  # 注意依赖关系：target_validator 和 delta_guard 都调用 pose_conversion 的
  # 函数（is_valid_ros_quaternion / euler_to_ros_quaternion / rm_pose_to_ros_pose），
  # 必须把 src/pose_conversion.cpp 一并加入它们的源文件列表，否则链接失败。
  ament_add_gtest(test_pose_conversion
    tests/test_pose_conversion.cpp src/pose_conversion.cpp)
  target_include_directories(test_pose_conversion PRIVATE include)
  ament_target_dependencies(test_pose_conversion geometry_msgs)

  ament_add_gtest(test_target_validator
    tests/test_target_validator.cpp src/target_validator.cpp src/pose_conversion.cpp)
  target_include_directories(test_target_validator PRIVATE include)
  ament_target_dependencies(test_target_validator geometry_msgs)

  ament_add_gtest(test_delta_guard
    tests/test_delta_guard.cpp src/delta_guard.cpp src/pose_conversion.cpp)
  target_include_directories(test_delta_guard PRIVATE include)
  ament_target_dependencies(test_delta_guard geometry_msgs)

  ament_add_gtest(test_permit_guard
    tests/test_permit_guard.cpp src/permit_guard.cpp)
  target_include_directories(test_permit_guard PRIVATE include)
  ament_target_dependencies(test_permit_guard act_interfaces rclcpp)
endif()

ament_package()
