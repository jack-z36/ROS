# Octopus Local Deployment Worklog

Date: 2026-04-27

Workspace after migration: `/home/hit/ROS`

Project path after migration: `/home/hit/ROS/src/VTLA_octopus-master`

ROS package path: `/home/hit/ROS/src/VTLA_octopus-master/octopus`

Package name: `octopus`

## 1. Goal

Move and deploy the Octopus data acquisition GUI into the local ROS workspace so it can be built and run with ROS 2 Jazzy.

Target behavior for this round:

- Build the `octopus` ROS 2 package successfully.
- Run the Qt/ROS GUI in a no-hardware environment.
- Keep the network policy: use configured mirrors first, and use Clash proxy `127.0.0.1:7897` only as fallback.
- Preserve enough detail for future debugging of runtime, dependency, FFmpeg, Qt, and ROS topic issues.

## 2. Important Architecture Notes

Octopus is not only a desktop GUI. It initializes ROS 2 and creates ROS subscribers inside the Qt application.

Entry point:

```cpp
// octopus/src/main.cpp
rclcpp::init(argc, argv, options);
Scanner app(argc, argv);
const auto window = new MainWindow();
window->show();
return Scanner::exec();
```

Main ROS-facing behavior:

- Subscribes to RealSense image topics.
- Subscribes to Inspire tactile image topics.
- Subscribes to Inspire joint state topics.
- Records configured ROS topics into `.mcap` through `McapRecorder`.

So the runtime model is:

```text
RealSense ROS nodes ---> image topics ----\
Inspire ROS nodes   ---> tactile/joint ----> Octopus Qt GUI + ROS subscribers ---> display + MCAP recording
Other ROS nodes     ---> topics ----------/
```

## 3. Starting Environment

Observed system:

```text
Ubuntu 24.04 LTS
ROS 2 Jazzy
CMake 3.28.3
Qt available at: /home/hit/Qt/6.11.0/gcc_64
```

Already present:

- ROS 2 Jazzy: `/opt/ros/jazzy`
- `colcon`
- `build-essential`
- `cmake`
- `pkg-config`
- `python3-colcon-common-extensions`
- `libassimp-dev`
- Ubuntu FFmpeg 6.1 development packages

Missing or unsuitable at first:

- `ninja-build` was not installed.
- System Qt was only 6.4.2, but Qt 6.11.0 was already installed under `$HOME/Qt`.
- System FFmpeg development packages were 6.1, while `octopus/CMakeLists.txt` requires `find_package(FFmpeg 7.0 REQUIRED)`.
- RealSense packages were not installed.
- Original project directory was not a git worktree, and all `octopus/3rdparty/*` directories were empty.

## 4. Network Policy Used

No global proxy was active:

```bash
env | grep -Ei '^(http|https|all|no)_proxy='
git config --global --get-regexp 'proxy'
```

No proxy entries were found.

Configured mirrors/sources observed:

- ROS apt source: `https://mirrors.ustc.edu.cn/ros2/ubuntu/`
- Ubuntu packages were available from the USTC mirror in apt cache for many packages.
- FFmpeg 8 PPA was already configured:
  `https://ppa.launchpadcontent.net/ubuntuhandbook1/ffmpeg8/ubuntu/`

Actual downloads in this session:

- GitHub submodule clones succeeded directly, without Clash.
- FFmpeg 8 `.deb` downloads succeeded through existing apt sources/mirrors, without Clash.
- Clash `127.0.0.1:7897` was not needed.

Fallback proxy commands for future use:

```bash
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
export all_proxy=socks5://127.0.0.1:7897
```

For git only:

```bash
git -c http.proxy=http://127.0.0.1:7897 \
    -c https.proxy=http://127.0.0.1:7897 \
    clone <url> <dir>
```

## 5. Sudo Limitation

`sudo apt update` failed because the tool session could not provide an interactive password:

```text
sudo: a terminal is required to read the password
sudo: a password is required
```

Because of that, no system packages were installed or upgraded with sudo during this run.

Workaround used:

- Keep using existing system packages where possible.
- Download required FFmpeg 8 packages with `apt-get download`.
- Extract `.deb` files into a local project dependency directory:
  `/home/hit/ROS/src/VTLA_octopus-master/.deps/ffmpeg8`

## 6. Third-Party Source Dependencies

The source tree had these submodule directories, but they were empty:

```text
octopus/3rdparty/cmake-modules
octopus/3rdparty/glm
octopus/3rdparty/json
octopus/3rdparty/mcap
octopus/3rdparty/spdlog
octopus/3rdparty/zstd
```

Because the project directory was not a git worktree, `git submodule update --init --recursive` could not be used from the root. Each dependency was cloned directly from `.gitmodules` URLs:

```bash
git clone --recursive https://github.com/foxglove/mcap.git octopus/3rdparty/mcap
git clone --recursive https://github.com/ffiirree/cmake-modules.git octopus/3rdparty/cmake-modules
git clone --recursive https://github.com/g-truc/glm.git octopus/3rdparty/glm
git clone --recursive https://github.com/gabime/spdlog.git octopus/3rdparty/spdlog
git clone --recursive https://github.com/nlohmann/json.git octopus/3rdparty/json
git clone --recursive https://github.com/facebook/zstd.git octopus/3rdparty/zstd
```

Resulting HEADs:

```text
octopus/3rdparty/cmake-modules: d38e688
octopus/3rdparty/glm: 6f14f479
octopus/3rdparty/json: 98386eb08
octopus/3rdparty/mcap: c3cab6bd3
octopus/3rdparty/spdlog: a2976707
octopus/3rdparty/zstd: 0cdce55f
```

## 7. Qt Resolution

Qt installer existed:

```text
/home/hit/下载/qt-online-installer-linux-x64-4.10.0.run
```

But a suitable Qt was already installed:

```text
/home/hit/Qt/6.11.0/gcc_64
```

Version check:

```bash
/home/hit/Qt/6.11.0/gcc_64/bin/qtpaths --qt-version
```

Output:

```text
6.11.0
```

Qt environment used:

```bash
export QT_ROOT=$HOME/Qt/6.11.0/gcc_64
export Qt6_DIR=$QT_ROOT/lib/cmake/Qt6
export CMAKE_PREFIX_PATH=$QT_ROOT:$CMAKE_PREFIX_PATH
export PATH=$QT_ROOT/bin:$PATH
export LD_LIBRARY_PATH=$QT_ROOT/lib:$LD_LIBRARY_PATH
```

## 8. FFmpeg 8 Local Dependency Workaround

Initial CMake error:

```text
CMake Error at 3rdparty/cmake-modules/FindFFmpeg.cmake:147 (message):
  Can not find the suitable version.
```

Reason:

- System FFmpeg development packages were version 6.1.
- Project requires FFmpeg 7.0 or newer.

FFmpeg 8.1 candidates were visible in apt:

```text
libavcodec-dev candidate: 10:8.1-0build3~ubuntu24.04
libavformat-dev candidate: 10:8.1-0build3~ubuntu24.04
libavutil-dev candidate: 10:8.1-0build3~ubuntu24.04
libswscale-dev candidate: 10:8.1-0build3~ubuntu24.04
libswresample-dev candidate: 10:8.1-0build3~ubuntu24.04
```

Downloaded and extracted FFmpeg 8 packages locally:

```bash
mkdir -p .deps/apt .deps/ffmpeg8
cd .deps/apt

apt-get download \
  libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libswresample-dev \
  libavdevice-dev libavfilter-dev \
  libavcodec62 libavformat62 libavutil60 libswscale9 libswresample6 \
  libavdevice62 libavfilter11

for deb in *.deb; do
  dpkg-deb -x "$deb" ../ffmpeg8
done
```

Verified local pkg-config versions:

```bash
PKG_CONFIG_PATH=$PWD/.deps/ffmpeg8/usr/lib/x86_64-linux-gnu/pkgconfig \
pkg-config --modversion \
  libavcodec libavformat libavutil libswscale libswresample libavdevice libavfilter
```

Observed:

```text
62.28.100
62.12.100
60.26.100
9.5.100
6.3.100
62.3.100
11.14.100
```

Important CMake detail:

The bundled `octopus/3rdparty/cmake-modules/FindFFmpeg.cmake` scans environment variables including:

```text
FFMPEG_PATH
FFMPEG_ROOT
```

So `CMAKE_PREFIX_PATH` alone was not enough. These were required:

```bash
export FFMPEG_ROOT=$PWD/.deps/ffmpeg8/usr
export FFMPEG_PATH=$FFMPEG_ROOT
```

## 9. FFmpeg Linker Dependency Fix

After local FFmpeg 8 was found, compilation progressed but linking failed with many missing FFmpeg downstream libraries.

Representative linker warnings/errors:

```text
libaribb24.so.0, needed by libavcodec.so, not found
libdavs2.so.16, needed by libavcodec.so, not found
libfdk-aac.so.2, needed by libavcodec.so, not found
libplacebo.so.360, needed by libavfilter.so, not found
libdvdnav.so.4, needed by libavformat.so, not found
undefined reference to ...
```

Missing libraries were detected with:

```bash
LD_LIBRARY_PATH=$PWD/.deps/ffmpeg8/usr/lib/x86_64-linux-gnu \
ldd .deps/ffmpeg8/usr/lib/x86_64-linux-gnu/libavcodec.so \
    .deps/ffmpeg8/usr/lib/x86_64-linux-gnu/libavfilter.so \
    .deps/ffmpeg8/usr/lib/x86_64-linux-gnu/libavformat.so \
  | awk '/not found/ {print $1}' | sort -u
```

Downloaded and extracted the first missing dependency group:

```bash
cd .deps/apt

apt-get download \
  libaribb24-0t64 libdavs2-16 libfdk-aac2 libilbc3 \
  libopencore-amrnb0 libopencore-amrwb0 libvo-amrwbenc0 \
  libvvenc1.12 libxavs2-13 libopenh264-7 libkvazaar7 \
  libass9 libbs2b0 liblilv-0-0 librubberband2 libmysofa1 \
  libflite1 libplacebo360 libvmaf1 libvidstab1.1 libzimg2 \
  libdvdnav4 libdvdread8t64 libsrt1.5-openssl

for deb in *.deb; do
  dpkg-deb -x "$deb" ../ffmpeg8
done
```

Then downloaded and extracted the remaining missing dependency group:

```bash
cd .deps/apt

apt-get download \
  libfftw3-double3 libserd-0-0 libsord-0-0 libsratom-0-0 \
  libunibreak5 libzix-0-0

for deb in *.deb; do
  dpkg-deb -x "$deb" ../ffmpeg8
done
```

After that, FFmpeg shared library dependencies resolved when using:

```bash
LD_LIBRARY_PATH=$PWD/.deps/ffmpeg8/usr/lib/x86_64-linux-gnu
```

## 10. Build Attempts and Fixes

### Attempt 1: Ninja generator

Command shape:

```bash
colcon build --packages-select octopus \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -GNinja
```

Failure:

```text
CMake was unable to find a build program corresponding to "Ninja".
CMAKE_MAKE_PROGRAM is not set.
```

Reason:

- `ninja-build` was not installed.
- Installing it with sudo was not possible in this tool session.

Resolution:

- Build with default Unix Makefiles instead of Ninja.

### Attempt 2: Makefiles, system FFmpeg

Failure:

```text
Can not find the suitable version.
```

Resolution:

- Use locally extracted FFmpeg 8.1.
- Set `FFMPEG_ROOT` and `FFMPEG_PATH`.

### Attempt 3: Makefiles, local FFmpeg 8

Compilation succeeded but final link failed due to missing FFmpeg downstream shared libraries.

Resolution:

- Download and extract FFmpeg downstream runtime dependencies into `.deps/ffmpeg8`.
- Add linker runtime and rpath-link flags.

### Final Successful Build

From workspace root:

```bash
cd /home/hit/ROS

source /opt/ros/jazzy/setup.bash

export QT_ROOT=$HOME/Qt/6.11.0/gcc_64
export FFMPEG_ROOT=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr
export FFMPEG_PATH=$FFMPEG_ROOT
export Qt6_DIR=$QT_ROOT/lib/cmake/Qt6
export CMAKE_PREFIX_PATH=$QT_ROOT:$FFMPEG_ROOT:${CMAKE_PREFIX_PATH:-}
export PKG_CONFIG_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}
export PATH=$QT_ROOT/bin:$PATH
export LD_LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:$QT_ROOT/lib:${LD_LIBRARY_PATH:-}
export LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:${LIBRARY_PATH:-}

colcon build --packages-select octopus --cmake-args \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,$FFMPEG_ROOT/lib/x86_64-linux-gnu -Wl,-rpath,$FFMPEG_ROOT/lib/x86_64-linux-gnu -Wl,-rpath,$QT_ROOT/lib"
```

Result:

```text
Finished <<< octopus [49.0s]
Summary: 1 package finished
```

Warnings seen but not fatal:

```text
CMake Warning about zstd CMP0077
CMake Warning about CMP0144 and FFMPEG_ROOT
resources/shaders/*.frag -> *.qsb
media.h:283: Ignoring definition of undeclared qualified class
```

## 11. Migration to ROS Workspace

Original path:

```text
/home/hit/VTLA_octopus-master
```

Moved to:

```text
/home/hit/ROS/src/VTLA_octopus-master
```

Command used:

```bash
mv /home/hit/VTLA_octopus-master /home/hit/ROS/src/VTLA_octopus-master
```

Verified from `/home/hit/ROS`:

```bash
source /opt/ros/jazzy/setup.bash
colcon list | sort
```

Output included:

```text
octopus  src/VTLA_octopus-master/octopus  (ros.ament_cmake)
```

Other packages in the same workspace at the time:

```text
baton_mini
gopro_camera_launch
```

## 12. Build Artifacts

Workspace install artifact:

```text
/home/hit/ROS/install/octopus/lib/octopus/octopus
```

Installed runtime resources:

```text
/home/hit/ROS/install/octopus/lib/octopus/models/RH56E2-R.bin
/home/hit/ROS/install/octopus/lib/octopus/models/RH56E2-R.gltf
/home/hit/ROS/install/octopus/lib/octopus/models/loong_96.stl
/home/hit/ROS/install/octopus/lib/octopus/models/molding.stl
/home/hit/ROS/install/octopus/lib/octopus/translations/scanner_en_US.qm
/home/hit/ROS/install/octopus/lib/octopus/translations/scanner_zh_CN.qm
```

Size summary after deployment:

```text
175M  /home/hit/ROS/src/VTLA_octopus-master/.deps
54M   /home/hit/ROS/src/VTLA_octopus-master/build
27M   /home/hit/ROS/src/VTLA_octopus-master/install
```

Note: The authoritative workspace install after migration is `/home/hit/ROS/install`, not the old per-project `install` directory.

## 13. Runtime Command

Use this from the ROS workspace root:

```bash
cd /home/hit/ROS

source /opt/ros/jazzy/setup.bash
source install/setup.bash

export QT_ROOT=$HOME/Qt/6.11.0/gcc_64
export FFMPEG_ROOT=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr
export LD_LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:$QT_ROOT/lib:${LD_LIBRARY_PATH:-}

ros2 run octopus octopus
```

If CMake rebuild is needed, also export:

```bash
export FFMPEG_PATH=$FFMPEG_ROOT
export Qt6_DIR=$QT_ROOT/lib/cmake/Qt6
export CMAKE_PREFIX_PATH=$QT_ROOT:$FFMPEG_ROOT:${CMAKE_PREFIX_PATH:-}
export PKG_CONFIG_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}
export PATH=$QT_ROOT/bin:$PATH
export LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:${LIBRARY_PATH:-}
```

## 14. Runtime Verification

Dynamic library check:

```bash
cd /home/hit/ROS

LD_LIBRARY_PATH=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr/lib/x86_64-linux-gnu:$HOME/Qt/6.11.0/gcc_64/lib:${LD_LIBRARY_PATH:-} \
ldd /home/hit/ROS/install/octopus/lib/octopus/octopus | awk '/not found/ {print}'
```

Observed result:

```text
<no output>
```

Meaning: no unresolved dynamic libraries with the expected `LD_LIBRARY_PATH`.

No-hardware launch check:

```bash
cd /home/hit/ROS

source /opt/ros/jazzy/setup.bash
source install/setup.bash

export QT_ROOT=$HOME/Qt/6.11.0/gcc_64
export FFMPEG_ROOT=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr
export LD_LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:$QT_ROOT/lib:${LD_LIBRARY_PATH:-}

timeout 8s ros2 run octopus octopus
```

Observed:

```text
[INFO] [..] [rclcpp]: signal_handler(SIGINT/SIGTERM)
```

Interpretation:

- The application launched and stayed alive until `timeout` sent SIGTERM.
- No Qt platform, FFmpeg, ROS initialization, or shared library error appeared during the 8 second test.

ROS topic state with no hardware:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | sort
```

Observed:

```text
/parameter_events
/rosout
```

This is expected before RealSense/Inspire drivers are launched.

## 15. RealSense and Hardware Work Remaining

RealSense packages were not installed during this session because sudo password input was unavailable.

Manual install command to run in a normal terminal:

```bash
sudo apt install ros-jazzy-realsense2-camera librealsense2-utils
```

Then enumerate cameras:

```bash
rs-enumerate-devices | grep Serial
```

Launch expected camera topic namespaces:

```bash
ros2 launch realsense2_camera rs_launch.py camera_namespace:=realsense camera_name:=left_hand serial_no:=_<SERIAL>
ros2 launch realsense2_camera rs_launch.py camera_namespace:=realsense camera_name:=right_hand serial_no:=_<SERIAL>
ros2 launch realsense2_camera rs_launch.py camera_namespace:=realsense camera_name:=top serial_no:=_<SERIAL>
```

Octopus expects these RealSense image topics:

```text
/realsense/right_hand/color/image_raw
/realsense/left_hand/color/image_raw
/realsense/top/color/image_raw
```

README and default recording config also mention depth topics:

```text
/realsense/right_hand/depth/image_rect_raw
/realsense/left_hand/depth/image_rect_raw
/realsense/top/depth/image_rect_raw
```

Octopus expects Inspire topics:

```text
/inspire/left_hand/tactile_12
/inspire/left_hand/tactile_13
/inspire/left_hand/tactile_22
/inspire/left_hand/tactile_23
/inspire/left_hand/tactile_32
/inspire/left_hand/tactile_33
/inspire/left_hand/tactile_42
/inspire/left_hand/tactile_43
/inspire/left_hand/tactile_52
/inspire/left_hand/tactile_54
/inspire/left_hand/tactile_61
/inspire/right_hand/tactile_12
/inspire/right_hand/tactile_13
/inspire/right_hand/tactile_22
/inspire/right_hand/tactile_23
/inspire/right_hand/tactile_32
/inspire/right_hand/tactile_33
/inspire/right_hand/tactile_42
/inspire/right_hand/tactile_43
/inspire/right_hand/tactile_52
/inspire/right_hand/tactile_54
/inspire/right_hand/tactile_61
/inspire/left_hand/joint_states
/inspire/right_hand/joint_states
```

Check hardware topics:

```bash
ros2 topic list | grep -E 'realsense|inspire'
```

## 16. Known Gotchas for Future Debug

### Run from `/home/hit/ROS`, not the old path

The old path was moved:

```text
/home/hit/VTLA_octopus-master
```

Use:

```text
/home/hit/ROS/src/VTLA_octopus-master
```

### Always set FFmpeg local library path

If this is missing:

```bash
export LD_LIBRARY_PATH=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr/lib/x86_64-linux-gnu:$HOME/Qt/6.11.0/gcc_64/lib:${LD_LIBRARY_PATH:-}
```

then runtime may fail to load FFmpeg 8 libraries or may accidentally use system FFmpeg 6.1.

### Rebuild needs `FFMPEG_ROOT`

The bundled CMake finder needs:

```bash
export FFMPEG_ROOT=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr
export FFMPEG_PATH=$FFMPEG_ROOT
```

Without these, CMake may report:

```text
Can not find the suitable version.
```

### Ninja is not installed

Do not use `-GNinja` unless `ninja-build` is installed.

Current working build uses default Makefiles.

### System sudo was not used

This deployment has a local `.deps/ffmpeg8` workaround. A cleaner future system-level setup would be:

```bash
sudo apt install ffmpeg \
  libavcodec-dev libavformat-dev libavutil-dev \
  libswscale-dev libswresample-dev libavdevice-dev libavfilter-dev
```

from the FFmpeg 8 PPA, if system-level package changes are acceptable.

### RealSense still needs manual install

Until this succeeds:

```bash
sudo apt install ros-jazzy-realsense2-camera librealsense2-utils
```

Octopus can launch, but camera topics will not appear unless another machine/process publishes them.

## 17. Quick Command Reference

Build only Octopus:

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash

export QT_ROOT=$HOME/Qt/6.11.0/gcc_64
export FFMPEG_ROOT=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr
export FFMPEG_PATH=$FFMPEG_ROOT
export Qt6_DIR=$QT_ROOT/lib/cmake/Qt6
export CMAKE_PREFIX_PATH=$QT_ROOT:$FFMPEG_ROOT:${CMAKE_PREFIX_PATH:-}
export PKG_CONFIG_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}
export PATH=$QT_ROOT/bin:$PATH
export LD_LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:$QT_ROOT/lib:${LD_LIBRARY_PATH:-}
export LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:${LIBRARY_PATH:-}

colcon build --packages-select octopus --cmake-args \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,$FFMPEG_ROOT/lib/x86_64-linux-gnu -Wl,-rpath,$FFMPEG_ROOT/lib/x86_64-linux-gnu -Wl,-rpath,$QT_ROOT/lib"
```

Run Octopus:

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash
source install/setup.bash

export QT_ROOT=$HOME/Qt/6.11.0/gcc_64
export FFMPEG_ROOT=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr
export LD_LIBRARY_PATH=$FFMPEG_ROOT/lib/x86_64-linux-gnu:$QT_ROOT/lib:${LD_LIBRARY_PATH:-}

ros2 run octopus octopus
```

Check package discovery:

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash
colcon list | grep octopus
```

Check library resolution:

```bash
cd /home/hit/ROS
LD_LIBRARY_PATH=$PWD/src/VTLA_octopus-master/.deps/ffmpeg8/usr/lib/x86_64-linux-gnu:$HOME/Qt/6.11.0/gcc_64/lib:${LD_LIBRARY_PATH:-} \
ldd install/octopus/lib/octopus/octopus | awk '/not found/ {print}'
```

Check ROS topics:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | sort
```

