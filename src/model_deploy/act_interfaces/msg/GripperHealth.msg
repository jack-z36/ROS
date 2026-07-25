std_msgs/Header header
uint8 OK=0
uint8 DEGRADED=1
uint8 FAULT=2
string hardware_id          # "elephant_gripper"
uint8 status                # overall = worse of left/right
bool left_connected
bool right_connected
uint8 left_status
uint8 right_status
bool estop_active
string detail               # human-readable summary of the most recent error / timeout
