"""Standard ROS2 message definitions used by the MCAP cleaning pipeline."""

from __future__ import annotations

STD_MSGS_FLOAT32 = """float32 data
"""

STD_MSGS_HEADER = """builtin_interfaces/Time stamp
string frame_id
================================================================================
MSG: builtin_interfaces/msg/Time
int32 sec
uint32 nanosec
"""

GEOMETRY_MSGS_POINT = """float64 x
float64 y
float64 z
"""

GEOMETRY_MSGS_QUATERNION = """float64 x
float64 y
float64 z
float64 w
"""

GEOMETRY_MSGS_POSE = """geometry_msgs/Point position
geometry_msgs/Quaternion orientation
================================================================================
MSG: geometry_msgs/msg/Point
float64 x
float64 y
float64 z
================================================================================
MSG: geometry_msgs/msg/Quaternion
float64 x
float64 y
float64 z
float64 w
"""

GEOMETRY_MSGS_VECTOR3 = """float64 x
float64 y
float64 z
"""

GEOMETRY_MSGS_TWIST = """geometry_msgs/Vector3 linear
geometry_msgs/Vector3 angular
================================================================================
MSG: geometry_msgs/msg/Vector3
float64 x
float64 y
float64 z
"""

GEOMETRY_MSGS_POSE_WITH_COVARIANCE = """geometry_msgs/Pose pose
float64[36] covariance
================================================================================
MSG: geometry_msgs/msg/Pose
geometry_msgs/Point position
geometry_msgs/Quaternion orientation
================================================================================
MSG: geometry_msgs/msg/Point
float64 x
float64 y
float64 z
================================================================================
MSG: geometry_msgs/msg/Quaternion
float64 x
float64 y
float64 z
float64 w
"""

GEOMETRY_MSGS_TWIST_WITH_COVARIANCE = """geometry_msgs/Twist twist
float64[36] covariance
================================================================================
MSG: geometry_msgs/msg/Twist
geometry_msgs/Vector3 linear
geometry_msgs/Vector3 angular
================================================================================
MSG: geometry_msgs/msg/Vector3
float64 x
float64 y
float64 z
"""

GEOMETRY_MSGS_POSE_STAMPED = """std_msgs/Header header
geometry_msgs/Pose pose
================================================================================
MSG: std_msgs/msg/Header
builtin_interfaces/Time stamp
string frame_id
================================================================================
MSG: builtin_interfaces/msg/Time
int32 sec
uint32 nanosec
================================================================================
MSG: geometry_msgs/msg/Pose
geometry_msgs/Point position
geometry_msgs/Quaternion orientation
================================================================================
MSG: geometry_msgs/msg/Point
float64 x
float64 y
float64 z
================================================================================
MSG: geometry_msgs/msg/Quaternion
float64 x
float64 y
float64 z
float64 w
"""

NAV_MSGS_ODOMETRY = """std_msgs/Header header
string child_frame_id
geometry_msgs/PoseWithCovariance pose
geometry_msgs/TwistWithCovariance twist
================================================================================
MSG: std_msgs/msg/Header
builtin_interfaces/Time stamp
string frame_id
================================================================================
MSG: builtin_interfaces/msg/Time
int32 sec
uint32 nanosec
================================================================================
MSG: geometry_msgs/msg/PoseWithCovariance
geometry_msgs/Pose pose
float64[36] covariance
================================================================================
MSG: geometry_msgs/msg/Pose
geometry_msgs/Point position
geometry_msgs/Quaternion orientation
================================================================================
MSG: geometry_msgs/msg/Point
float64 x
float64 y
float64 z
================================================================================
MSG: geometry_msgs/msg/Quaternion
float64 x
float64 y
float64 z
float64 w
================================================================================
MSG: geometry_msgs/msg/TwistWithCovariance
geometry_msgs/Twist twist
float64[36] covariance
================================================================================
MSG: geometry_msgs/msg/Twist
geometry_msgs/Vector3 linear
geometry_msgs/Vector3 angular
================================================================================
MSG: geometry_msgs/msg/Vector3
float64 x
float64 y
float64 z
"""

SENSOR_MSGS_IMAGE = """std_msgs/Header header
uint32 height
uint32 width
string encoding
uint8 is_bigendian
uint32 step
uint8[] data
================================================================================
MSG: std_msgs/msg/Header
builtin_interfaces/Time stamp
string frame_id
================================================================================
MSG: builtin_interfaces/msg/Time
int32 sec
uint32 nanosec
"""

STANDARD_SCHEMA_TEXTS = {
    "std_msgs/msg/Float32": STD_MSGS_FLOAT32,
    "std_msgs/msg/Header": STD_MSGS_HEADER,
    "geometry_msgs/msg/PoseStamped": GEOMETRY_MSGS_POSE_STAMPED,
    "nav_msgs/msg/Odometry": NAV_MSGS_ODOMETRY,
    "sensor_msgs/msg/Image": SENSOR_MSGS_IMAGE,
}

