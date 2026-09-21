cmake_minimum_required(VERSION 3.8)
project(ros2_counter)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/CounterStamped.msg"
  DEPENDENCIES builtin_interfaces
)

# Install these modules directly because ament_python_install_package and
# rosidl_generate_interfaces cannot safely own the same Python package target.
ament_get_python_install_dir(PYTHON_INSTALL_DIR)
install(DIRECTORY ros2_counter
  DESTINATION ${PYTHON_INSTALL_DIR}
  PATTERN "__pycache__" EXCLUDE
  PATTERN "*.pyc" EXCLUDE
)

install(PROGRAMS
  scripts/counter_publisher
  scripts/counter_subscriber_gui
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(counter_unit_tests test
    APPEND_ENV PYTHONPATH=${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_py
    TIMEOUT 120
  )
endif()

ament_export_dependencies(rosidl_default_runtime)
ament_package()
