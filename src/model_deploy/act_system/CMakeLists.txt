cmake_minimum_required(VERSION 3.8)
project(act_system)

find_package(ament_cmake REQUIRED)

# 纯资源包：只安装启动编排资源，无编译目标。
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/start_act_system.sh DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(
    test_act_camera_topic_contract
    test/test_act_camera_topic_contract.py
  )
endif()

ament_package()
