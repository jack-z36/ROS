
# 手把手教程：单相机节点发布

Info

这份文档面向“你自己一步一步执行”的场景来写。

当前目标不是双相机，而是：

**先在 Ubuntu 24.04 + ROS2 Jazzy 上跑通一台 RoboBaton MINI 的节点发布。**

## 一、你这次最终要做到什么

你这次执行完成后，应该做到：

1. 相机通过 USB 连到上位机
2. 上位机能识别出对应 USB 网卡
3. 官方 ROS 包能成功编译
4. launch 文件里的 IP 已改成真实值
5. 节点能成功启动
6. 你能通过：

   * `ros2 topic list`
   * `ros2 topic echo`

   看到目标 topic 正常发布

## 二、先准备好这些东西

### 1. 硬件

* 一台 RoboBaton MINI 相机
* 一根 USB-C → USB-A 数据线
* Ubuntu 上位机

### 2. 软件环境

* Ubuntu 24.04
* ROS2 Jazzy
* 可以打开终端
* 建议已经安装：
  * `git`
  * `colcon`
  * `cmake`
  * `g++`
  * OpenCV 开发环境

### 3. 你这次会参考的资料

* 旧版执行文档：[02-备份/FastUMI_Data-main 04-18/learn/学习笔记/深度相机话题发布.md](02-备份/FastUMI_Data-main 04-18/learn/学习笔记/深度相机话题发布.md)
* 当前执行文档：[深度相机话题发布](深度相机话题发布)
* 编译原理：[编译原理-系统化说明](编译原理-系统化说明)
* 运行原理：[运行原理-系统化说明](运行原理-系统化说明)
* 官方 SDK 文档剪报：[Clipping/USB_Demo — baton_doc 0.0 documentation](Clipping/USB_Demo — baton_doc 0.0 documentation)

## 三、步骤 1：物理连接相机

### 你要做什么

把相机用 USB 线连到上位机。

### 具体操作

1. 找到相机上的 USB-C 接口
2. 将 USB-C 端插到相机
3. 将 USB-A 端插到上位机
4. 等待几秒，让系统识别

### 你现在就执行

连接完成后，在 Ubuntu 终端输入：

```bash
ip link show
```

### 你应该看到什么

* 系统里多出一个新的网卡
* 常见名字可能是：
  * `usb0`
  * `enx...`
  * `enp...`

### 如果没看到

* 换一个 USB 口
* 重新插拔
* 再执行一次 `ip link show`

---

## 四、步骤 2：获取 USB 网卡的 IP 信息

### 你要做什么

确认：

* 哪个网卡是相机对应的网卡
* 这个网卡的本机 IP 是多少

### 具体操作

在 Ubuntu 终端输入：

```bash
ifconfig
```

如果系统里没有 `ifconfig`，先安装：

```bash
sudo apt update
sudo apt install net-tools
```

然后再次执行：

```bash
ifconfig
```

### 你应该重点找什么

重点看相机对应那张 USB 网卡，比如：

* `usb0`

然后记录它的 IP。

常见情况像这样：

* 设备 IP：`192.168.1.10`
* 本机 USB 网卡 IP：`192.168.1.11` 或 `192.168.1.18`

### 你现在要记下来

请把下面两个值记住：

* `server_ip` = 相机 IP
* `local_ip` = 你的 USB 网卡 IP

---

## 五、步骤 3：下载 ROS 包

### 你要做什么

把官方源码放进一个标准 ROS2 workspace，然后编译它。

### 先建立工作空间

建议你直接用这个目录：

```bash
mkdir -p /home/hit/ROS/src
cd /home/hit/ROS/src
```

### 下载官方源码

官方仓库地址：

```bash
https://github.com/Hessian-matrix/baton_mini_sdk_demo
```

在终端执行：

```bash
git clone https://github.com/Hessian-matrix/baton_mini_sdk_demo
```

下载完成后，目录应该像这样：

```text
/home/hit/ROS/src/baton_mini_sdk_demo
```

### 这一步完成后的状态

你现在应该已经有：

* 一个标准 workspace：`/home/hit/ROS`
* 一份源码目录：`/home/hit/ROS/src/baton_mini_sdk_demo`

---

## 六、步骤 4：下载依赖

### 你要做什么

在正式执行 [colcon build](注释文件/colcon-build) 之前，先把后续编译和运行需要的 [注释文件/依赖](注释文件/依赖) 安装好。

这一步的目标不是“创建一个 Python 或 conda 环境”，而是：

* 在 **Ubuntu 系统环境** 里
* 先把 ROS2 构建和 C++ 编译要用到的系统依赖补齐

Important

对当前这个项目，不建议优先使用 conda，也不建议把依赖装进 conda `base` 环境。

更稳的做法是：

* ROS2 Jazzy 用系统安装
* CMake / 编译器 / OpenCV 用 `apt` 安装
* 后面再在 workspace 根目录执行 [colcon build](注释文件/colcon-build)

### 这一步为什么必须先做

如果这一步没做完，后面最常见的问题会是：

* `colcon build` 可以执行，但编译失败
* `find_package(OpenCV REQUIRED)` 找不到 OpenCV
* `ament_cmake` / `rclcpp` 找不到
* 终端里明明有源码，但 ROS2 构建系统识别不全

所以这一步的本质是：

> 先把“系统环境缺东西”这个变量排除掉，再进入正式编译。

### 你现在需要安装哪些依赖

对当前 `baton_mini_sdk_demo` 来说，建议先安装这些：

* `build-essential`
* `cmake`
* `python3-colcon-common-extensions`
* `python3-rosdep`
* `libopencv-dev`

如果你前面还没装过 `ifconfig`，也建议一起装上：

* `net-tools`

### 你现在就执行

先更新软件源：

```bash
sudo apt update
```

然后安装依赖：

```bash
sudo apt install -y \
  build-essential \
  cmake \
  python3-colcon-common-extensions \
  python3-rosdep \
  libopencv-dev \
  net-tools
```

### 如果你还没初始化 rosdep

第一次在这台机器上用 ROS2 时，建议补一次：

```bash
sudo rosdep init
rosdep update
```

Note

如果终端提示 `rosdep` 已经初始化过了，就不用重复做。

### 你应该看到什么

安装成功后，你至少应该具备：

* 可以执行 `colcon`
* 可以执行 `cmake`
* 系统里已经有 OpenCV 开发库
* 后面可以继续进入编译步骤

### 你现在可以简单验一下

在终端执行：

```bash
colcon --help
cmake --version
pkg-config --modversion opencv4
```

### 正常情况下会有什么表现

* `colcon --help` 能显示帮助信息
* `cmake --version` 能显示版本号
* `pkg-config --modversion opencv4` 能输出一个 OpenCV 版本号

。

---

## 七、步骤 5：修改 launch 文件里的 IP

### 你要做什么

把 launch 里的默认 IP 改成你真实的：

* 相机 IP
* 本机 USB 网卡 IP

### 打开 launch 文件

文件位置：

* `/home/hit/ROS/src/baton_mini_sdk_demo/launch/baton_mini.launch.py`

你可以用任意编辑器打开，比如：

```bash
nano /home/hit/ROS/src/baton_mini_sdk_demo/launch/baton_mini.launch.py
```

### 你会看到类似内容

```python
DeclareLaunchArgument("server_ip", default_value="192.168.1.10"),
DeclareLaunchArgument("local_ip", default_value="192.168.1.18"),
```

### 你要改什么

如果你的 `ifconfig` 看到本机 IP 不是 `192.168.1.18`，就把它改掉。

例如：

* 相机还是 `192.168.1.10`
* 你的 USB 网卡是 `192.168.1.11`

那就改成：

```python
DeclareLaunchArgument("server_ip", default_value="192.168.1.10"),
DeclareLaunchArgument("local_ip", default_value="192.168.1.11"),
```

### 改完后保存退出

如果你用的是 nano：

* `Ctrl + O` 保存
* 回车确认
* `Ctrl + X` 退出

---

## 八、步骤 6：编译 ROS 包

### 你要做什么

在 IP 已经明确、源码已经下载好的前提下，正式编译这个 ROS 包。

### 加载 Jazzy 环境

在终端执行：

```bash
source /opt/ros/jazzy/setup.bash
```

Note

官方文档里常写的是 Humble。

你这里是 Jazzy，所以要换成 `jazzy`。

### 开始编译

先进入工作空间根目录：

```bash
cd /home/hit/ROS
```

然后编译：

```bash
colcon build --cmake-args -DUSE_ROS=ON
```

### 编译成功后你应该看到什么

工作空间下出现：

* `build/`
* `install/`
* `log/`

并且不应该出现最后的致命报错。

### 编译失败时先看什么

先不要慌，按这个顺序检查：

1. 你是不是在 `/home/hit/ROS` 根目录
2. 源码是不是在 `/home/hit/ROS/src/baton_mini_sdk_demo`
3. 你有没有先执行：
   ```bash
   source /opt/ros/jazzy/setup.bash
   ```
4. 依赖是否缺失

如果你卡在这里，优先回看：

* [编译原理-系统化说明](编译原理-系统化说明)

---

## 九、步骤 7：运行节点并检查 topic

### 先加载环境

先打开一个新终端，执行：

```bash
source /opt/ros/jazzy/setup.bash
source /home/hit/ROS/install/setup.bash
```

### 启动节点

执行：

```bash
ros2 launch baton_mini baton_mini.launch.py
```

### 这里有一个非常重要的点

这个项目不是“启动后自动把你想要的所有 topic 都打开”。

根据项目 README，启动后终端还会等待你输入命令。

你通常至少要做：

1. 输入：

```text
1
```

按回车

含义：启动算法

2. 如果你想看 `fast_odom`，再输入：

```text
5
```

按回车

含义：打开 fast odom 接收

### 然后检查 topic

重新开第二个终端，执行：

```bash
source /opt/ros/jazzy/setup.bash
source /home/hit/ROS/install/setup.bash
ros2 topic list
```

### 你应该找哪些 topic

先重点关注这些：

* `/baton_mini/imu`
* `/baton_mini/odometry`
* `/baton_mini/fast_odom`
* `/baton_mini/image_left`
* `/baton_mini/image_right`

### 再看具体数据

如果你想看 fast odom：

```bash
ros2 topic echo /baton_mini/fast_odom
```

如果你想看普通 odometry：

```bash
ros2 topic echo /baton_mini/odometry
```

### 你应该看到什么

如果成功，你应该能看到不断刷新的消息，里面有：

* `position`
* `orientation`

### 如果看不到数据

按这个顺序查：

1. 节点有没有成功启动
2. IP 有没有改对
3. 相机 USB 网卡是不是还在
4. 你有没有在节点终端输入：
   * `1`
   * `5`
5. 你查看的 topic 名字是不是对的

如果你卡在这里，优先回看：

* [运行原理-系统化说明](运行原理-系统化说明)

---

## 十、这一步做完后，算真正成功的标准

你可以把“单相机跑通”定义成：

1. 相机已连接
2. `ifconfig` 能看到正确 USB 网卡 IP
3. ROS 包已成功编译
4. launch IP 已改对
5. 节点已启动
6. 你能用 `ros2 topic list` 看到目标 topic
7. 你能用 `ros2 topic echo` 看到持续数据

---

## 十一、如果你下一步要继续做什么

如果这一步已经跑通，后面再进入：

* 第二个相机如何接入
* 双相机如何避免 IP 冲突
* 双相机如何避免 topic 冲突

也就是从“单相机教程”进入“双相机封装”。
