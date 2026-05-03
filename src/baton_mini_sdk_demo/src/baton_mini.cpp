#include <cstdlib>
#include <cstring>
#include <iostream>
#include <memory>
#include <thread>

#include "baton_mini.h"

#ifdef BATON_USE_ROS
#include "io/ros_interface.h"
#endif

using namespace std;

system_status sys_status = ready;//define the status of system

vio_login_info_s login_info = {
    "192.168.1.10",
    8000,
    "",
    "",
    NULL,
    NULL,
    NULL
};

std::string server_ip = "192.168.1.10";//device ip address as server
std::string local_ip = "192.168.1.16";//local ip address as client

namespace {

#ifdef BATON_USE_ROS
std::unique_ptr<baton_mini_sdk_demo::ROS_IO> g_ros_io;
#endif

bool publish_imu_enabled() {
#ifdef BATON_USE_ROS
    return !g_ros_io || g_ros_io->publishImuEnabled();
#else
    return true;
#endif
}

bool publish_fast_odom_enabled() {
#ifdef BATON_USE_ROS
    return !g_ros_io || g_ros_io->publishFastOdomEnabled();
#else
    return true;
#endif
}

bool publish_image_left_enabled() {
#ifdef BATON_USE_ROS
    return !g_ros_io || g_ros_io->publishImageLeftEnabled();
#else
    return true;
#endif
}

bool publish_image_right_enabled() {
#ifdef BATON_USE_ROS
    return !g_ros_io || g_ros_io->publishImageRightEnabled();
#else
    return true;
#endif
}

image_get configured_image_mode() {
    const bool left_enabled = publish_image_left_enabled();
    const bool right_enabled = publish_image_right_enabled();
    if (left_enabled && right_enabled) {
        return stereo;
    }
    if (left_enabled) {
        return ::left;
    }
    if (right_enabled) {
        return ::right;
    }
    return none;
}

}  // namespace

//connect_callback get status for connect
void vio_call connect_callback(int state, void* userData){
    (void)userData;
    if (state == 1)
        printf("connect ok !\n");
    else if (state == 0)
        printf("disconnected !\n");
    else if(state == -1)
        printf("connect error !\n");
    else if (state == -2)
        printf("keepalive thread exit !\n");
    else
        printf("unknown !\n");
}

//receive device heartbeat signal
void vio_call event_callback(const char* data, int length, void* userData){
    (void)length;
    (void)userData;
    #ifdef BATON_USE_ROS
    baton_mini_sdk_demo::ROS_IO::info("event_callback:%s",data);
    #else
    printf("event_callback:%s\n",data);
    #endif
}

void odom_data_print(int length, const char* frameData) {
    (void)length;
	odom_t odom;
	memcpy(&odom.pose,frameData,sizeof(odom.pose));
	memcpy(&odom.speed,frameData + sizeof(odom.pose),sizeof(odom.speed));
    // printf("odom_data:\n");
	// std::cout << "\t Position:" << odom.pose.px << "," << odom.pose.py << "," << odom.pose.pz << "\n";
	// std::cout << "\t Quaternion:" << odom.pose.qx << "," << odom.pose.qy << "," << odom.pose.qz << "," << odom.pose.qw << "\n";
	// std::cout << "\t twist:" << odom.speed.lx << "," << odom.speed.ly << "," << odom.speed.lz 
	//           << "," << odom.speed.ax << "," << odom.speed.ay << "," << odom.speed.az << "\n";
	#ifdef BATON_USE_ROS
    if (g_ros_io) {
        g_ros_io->publishOdom(odom);
    }
    #endif
}

void vio_call stream_callback(int channel, const vio_frame_info_s* frameInfo, const char* frameData, void* userData){
    (void)channel;
    (void)userData;
    if (frameInfo->type == vio_frame_pose_and_twist) {//get the algo odometry
        odom_data_print(frameInfo->length,frameData);
    }
    else if (frameInfo->type == vio_frame_sys_state) {//get the status of system
        sys_status = static_cast<system_status>(frameData[frameInfo->length - 1]);
        // if(sys_status == ready){
        //     printf("system is ready!\n");
        // }else if(sys_status == stereo3_running){
        //     printf("stereo3 algorithm is running!\n");
        // }
        // printf("sys_status:%d\n", frameData[frameInfo->length - 1]);
    }
}

void vio_sdk_init(){
    printf("sdk version : 0x%08lx\n", net_vio_sdk_version());
    net_vio_sdk_init();
    std::strncpy(login_info.ipaddr, server_ip.c_str(), sizeof(login_info.ipaddr) - 1); //Set the IP address of the device you want to connect to
    login_info.ipaddr[sizeof(login_info.ipaddr) - 1] = '\0';
    login_info.event_cb = event_callback;//print heartbreat
    login_info.connect_cb = connect_callback;//get connect status
    std::cout << "server_ip: " << server_ip << std::endl;
    std::cout << "local_ip: " << local_ip << std::endl;
    loginHandle = net_vio_login(login_info);
    if (!loginHandle){
        cout << "login fail\n";
        net_vio_sdk_exit();
        cout << "ByeBye\n";
        exit(0);
    }
    std::cout << "login success\n";
    baton_client_ipaddress(local_ip.c_str());
}

void command_thread(){
    vio_sdk_init();
    HANDLE streamHandle1 = net_vio_stream_connect(loginHandle, 1, stream_callback);
    (void)streamHandle1;
    
    get_device_version();
    get_device_param();
    recv_switch imu_status = publish_imu_enabled() ? ON : OFF;
    recv_switch odom_status = publish_fast_odom_enabled() ? ON : OFF;
    image_get image_status = configured_image_mode();
    cout << "Auto command: start algorithm (1)" << std::endl;
    if (sys_status == ready) {
        alog_start();
    } else if (sys_status == stereo3_running) {
        cout << "Algorithm already running" << std::endl;
    } else {
        cout << "Algorithm state is not ready yet: " << sys_status << std::endl;
    }

    cout << "Auto command: " << (imu_status == ON ? "open" : "close") << " imu receive (3)" << std::endl;
    baton_open_imu_recv(imu_status);
    cout << "Auto command: " << (odom_status == ON ? "open" : "close") << " fast odom receive (5)" << std::endl;
    baton_open_fast_odom_recv(odom_status);
    cout << "Auto command: "
         << (image_status == none ? "close" : "open")
         << " image receive (4)" << std::endl;
    baton_open_image_recv(image_status);

    // set_network("192.168.1.10");
    cout << "Please input the operation[0-5] : ";   

    int v;
    while (cin >> v){
        if (v == 0) {//logout connect
            net_vio_logout(loginHandle);
            break;
        }
        else if (v == 1){//start or stop
            if (sys_status == ready) {//The system is currently in a ready state and can be started directly
                alog_start();
            }
            else if (sys_status == stereo3_running) {//The system is currently in a running state and can be stoped
                algo_stop();
            }
        }
        else if (v == 2) {//algo restart
            if (sys_status == stereo3_running) {//The stereo3 algorithm is currently in a running state and can be restart
                algo_restart();
            }
        }
		else if(v == 3){//open or close imu receive
            if(imu_status == ON){
                imu_status = OFF;
			    baton_open_imu_recv(imu_status);
            }
            else{
                imu_status = ON;
                baton_open_imu_recv(imu_status);
            }
		}
        else if(v == 4){//Select to receive image data 
            image_status = configured_image_mode();
            baton_open_image_recv(image_status);
        }
        else if(v == 5){//Select to receive fast odometry data
            if(odom_status == ON){
                odom_status = OFF;
			    baton_open_fast_odom_recv(odom_status);
            }
            else{
                odom_status = ON;
                baton_open_fast_odom_recv(odom_status);
            }
        }
    }
    net_vio_sdk_exit();
    cout << "ByeBye\n";
}

void imu_data_recv(imu_data& imu){
    #ifdef BATON_USE_ROS
    if (g_ros_io) {
        g_ros_io->publishImu(imu);
    }
    #else
    (void)imu;
    #endif
}

void fast_odom_data_recv(odom_pack& odom){
    #ifdef BATON_USE_ROS
    if (g_ros_io) {
        g_ros_io->publishFastOdom(odom);
    }
    #else
    (void)odom;
    #endif
}

void image_left_data(cv::Mat& image_){
    #ifdef BATON_USE_ROS
    if (g_ros_io) {
        g_ros_io->publishImageLeft(image_);
    }
    #else
    (void)image_;
    #endif
}

void image_right_data(cv::Mat& image_){
    #ifdef BATON_USE_ROS
    if (g_ros_io) {
        g_ros_io->publishImageRight(image_);
    }
    #else
    (void)image_;
    #endif
}

int main(int argc, char** argv){
#ifdef BATON_USE_ROS
	baton_mini_sdk_demo::ROS_IO::init(argc, argv, "baton_mini");
    g_ros_io.reset(new baton_mini_sdk_demo::ROS_IO());
    g_ros_io->initPublishers(server_ip, local_ip);
#endif

    std::thread http_command{command_thread};
    std::unique_ptr<IMU> imu_recv;
    std::unique_ptr<Fast_odom> odom_recv;
    std::unique_ptr<Image_tcp> image_left_recv;
    std::unique_ptr<Image_tcp> image_right_recv;
    if (publish_imu_enabled()) {
        imu_recv.reset(new IMU(&imu_data_recv));
    }
    if (publish_fast_odom_enabled()) {
        odom_recv.reset(new Fast_odom(&fast_odom_data_recv));
    }
    if (publish_image_left_enabled()) {
        image_left_recv.reset(new Image_tcp(&image_left_data));//left default
    }
    if (publish_image_right_enabled()) {
        image_right_recv.reset(new Image_tcp(&image_right_data,false));//right must set false
    }

#ifdef BATON_USE_ROS
    baton_mini_sdk_demo::ROS_IO::spin();
    baton_mini_sdk_demo::ROS_IO::shutdown();
    g_ros_io.reset();
#endif

    http_command.join();
    return 0;
}

