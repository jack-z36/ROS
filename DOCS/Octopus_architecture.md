# Octopus Architecture

This file is the first-read guide for this repository.

If you need to work on this project again, read this document before opening source files. It captures the high-level runtime structure, the main data flows, the module boundaries, and the recommended reading order so the codebase does not need to be rediscovered from scratch.

Interactive companion:

- `docs/octopus-architecture.html`

## 1. What This Program Is

Octopus is a ROS2 + Qt desktop application for multimodal data collection.

At a high level, it does three things:

1. Subscribes to live ROS2 topics and renders them in a desktop UI.
2. Records selected ROS2 topics into `.mcap` files.
3. Loads and saves local runtime settings such as theme, language, recording path, compression mode, and default topic list.

The application is not organized like a heavy layered backend. The real center of the runtime is `MainWindow`, which assembles the UI, owns the display subscriptions, and routes incoming ROS2 messages directly into page widgets.

## 2. System Boundary

Inputs:

- ROS2 topics from cameras, tactile sensors, and joint states
- User actions in the Qt UI
- Local config file `scanner.json`

Outputs:

- On-screen visualization in Qt panels
- `.mcap` recording files
- Updated `scanner.json`

External dependencies that define the shape of the app:

- Qt 6 for UI
- ROS2 `rclcpp` for topic subscription
- FFmpeg for frame conversion and media utilities
- Assimp for loading the 3D hand model
- MCAP C++ library for recording

## 3. Boot Sequence

The startup chain is:

1. `octopus/src/main.cpp`
2. `octopus/src/scanner.cpp`
3. `octopus/src/mainwindow.cpp`

What each step does:

- `main.cpp`
  Initializes logging, initializes ROS2, creates the Qt application object `Scanner`, creates `MainWindow`, and enters the Qt event loop.
- `scanner.cpp`
  Loads config, loads fonts, applies theme, installs translation files, and saves config on quit.
- `mainwindow.cpp`
  Creates the dock layout, creates the ROS2 display node and executor thread, creates topic subscriptions, and connects incoming messages to specific UI panels.

This means the runtime root is not a service container or domain model. The runtime root is the Qt application shell plus `MainWindow`.

## 4. Core Runtime Model

There are three main runtime flows:

1. Display flow
2. Recording flow
3. Config flow

These flows are related but not identical.

The most important architectural decision in this project is:

- Display and recording are decoupled.

The UI display path subscribes to topics and converts them into renderable frames for panels.

The recording path creates a separate recorder with its own ROS2 node and subscriptions, then writes serialized ROS2 messages into MCAP directly.

This is why the app can show transformed display data without making the recorder depend on display widgets or display frame conversions.

## 5. Display Flow

Macro path:

`ROS2 topics -> MainWindow subscriptions -> page widgets -> graphics/media helpers -> screen`

Detailed shape:

1. `MainWindow` creates a ROS2 node and a `SingleThreadedExecutor`.
2. `MainWindow::subscribeTopics()` subscribes to camera, tactile, and joint-state topics.
3. Each callback sends the message into the correct panel.
4. Panels use `media` and `graphics` helpers to convert or render data.

### 5.1 Camera display path

Path:

`sensor_msgs::msg::Image -> to_ffmpeg_frame() -> Resampler -> ImageDockWidget -> TextureWidget`

Main files:

- `octopus/src/mainwindow.cpp`
- `octopus/src/pages/image-widget.cpp`
- `octopus/src/graphics/texture-widget.h`
- `octopus/src/media/resampler.h`

Meaning:

- ROS2 image messages are converted to FFmpeg frames.
- Frames are resampled into a render-friendly pixel format.
- The image panel passes them to a texture widget backed by QRhi.

### 5.2 Tactile display path

Path:

`sensor_msgs::msg::Image -> grayscale normalization -> HandDockWidget -> ImageRenderItem attachments -> RhiWidget`

Main files:

- `octopus/src/mainwindow.cpp`
- `octopus/src/pages/hand-panel.cpp`
- `octopus/src/graphics/rhi-widget.h`
- `octopus/src/graphics/model.h`

Meaning:

- Tactile images are treated as grayscale sensor maps.
- Values are normalized into 8-bit intensity.
- Each tactile topic is attached to a fixed render item on a 3D hand model.

This is a display-specific representation. It is not a general tactile domain layer.

### 5.3 Joint-state display path

Path:

`sensor_msgs::msg::JointState -> JointStateDockWidget queue -> timer refresh -> Qt chart`

Main files:

- `octopus/src/mainwindow.cpp`
- `octopus/src/pages/joint-state-panel.cpp`
- `octopus/src/media/queue.h`

Meaning:

- Joint-state messages are queued first.
- A timer periodically drains the queue and updates chart series.
- This avoids repainting directly from each subscription callback.

## 6. Recording Flow

Macro path:

`OpDockWidget -> McapRecorder -> generic ROS2 subscriptions -> MCAP writer -> .mcap file`

Main files:

- `octopus/src/pages/op-panel.cpp`
- `octopus/src/mcap-recorder.h`
- `octopus/src/mcap-recorder.cpp`
- `octopus/src/utils/config.cpp`

Detailed shape:

1. The user clicks Start in `OpDockWidget`.
2. `OpDockWidget` creates `McapRecorder`.
3. The recorder reads the selected topics from `config::recording::mcap::topics`.
4. The recorder creates its own ROS2 node and executor thread.
5. The recorder uses `create_generic_subscription()` to subscribe by topic and type.
6. Incoming serialized messages are written to MCAP with schema/channel metadata.

Important boundary:

- The recorder does not reuse the display subscriptions.
- The recorder writes serialized ROS2 messages, not display-ready frames.

Current schema support in `McapRecorder::get_message_definition()` is limited to:

- `sensor_msgs/msg/Image`
- `sensor_msgs/msg/CompressedImage`
- `sensor_msgs/msg/JointState`

So the recorder is generic at the subscription layer, but schema definition support is still manually enumerated.

## 7. Config Flow

Macro path:

`scanner.json -> config namespace -> Scanner / SettingsDialog / OpDockWidget -> scanner.json`

Main files:

- `octopus/src/utils/config.h`
- `octopus/src/utils/config.cpp`
- `octopus/src/scanner.cpp`
- `octopus/src/pages/settings-dialog.cpp`

Detailed shape:

1. `Scanner` calls `config::load()` during app startup.
2. Global config values are stored in the `config` namespace.
3. UI components read and mutate those shared values directly.
4. `Scanner` saves config on quit.
5. `SettingsDialog` also saves config on close.

This is a simple shared-state model, not dependency injection.

Practical implication:

- Config is globally reachable and easy to use.
- Config changes can immediately affect runtime behavior, especially theme and recording settings.

## 8. Module Boundaries

The repository should be understood in these large modules.

### 8.1 Application shell and composition root

Responsibility:

- Start the app
- Load global runtime state
- Create the main window
- Own the display-side ROS2 executor and subscriptions
- Assemble all page widgets

Main files:

- `octopus/src/main.cpp`
- `octopus/src/scanner.h`
- `octopus/src/scanner.cpp`
- `octopus/src/mainwindow.h`
- `octopus/src/mainwindow.cpp`

### 8.2 Page-level business UI

Responsibility:

- Represent the user-facing business panels
- Hold business-oriented view logic
- Bridge incoming data into reusable rendering and widget primitives

Directory:

- `octopus/src/pages/`

Main files:

- `hand-panel.*`
- `image-widget.*`
- `joint-state-panel.*`
- `op-panel.*`
- `settings-dialog.*`
- `topics-widget.*`

### 8.3 Recording and persistence

Responsibility:

- Start and stop recording
- Discover topic types
- Build MCAP schema/channel state
- Subscribe to recorded topics
- Write `.mcap`

Main files:

- `octopus/src/mcap-recorder.h`
- `octopus/src/mcap-recorder.cpp`
- `octopus/src/pages/op-panel.cpp`

### 8.4 Graphics and 3D rendering

Responsibility:

- Texture upload and GPU-side rendering
- 3D model loading
- Render-item composition
- Camera and transform handling

Directory:

- `octopus/src/graphics/`

Important files:

- `texture-widget.*`
- `rhi-widget.*`
- `model.*`
- `render-item-*`

### 8.5 Media and frame utilities

Responsibility:

- FFmpeg wrappers
- Frame resampling and pixel-format conversion
- Media queue utilities
- General media support infrastructure

Directory:

- `octopus/src/media/`

Important files:

- `ffmpeg-wrapper.h`
- `resampler.*`
- `queue.h`

### 8.6 Shared UI infrastructure

Responsibility:

- Dock widget shell
- Menus and utility widgets
- Frameless window behavior
- Reusable controls used by pages and the main window

Directories:

- `octopus/src/widgets/`
- `octopus/src/frameless/`

### 8.7 Shared utilities

Responsibility:

- Config
- Logging
- Thread helpers
- Small utility primitives

Directory:

- `octopus/src/utils/`

Important files:

- `config.*`
- `logging.h`
- `thread.*`
- `defer.h`

### 8.8 Resources and build metadata

Responsibility:

- Static assets
- Translations
- Qt resource registration
- Build dependencies and install layout

Directories and files:

- `octopus/resources/`
- `octopus/languages/`
- `octopus/scanner.qrc`
- `octopus/CMakeLists.txt`
- `octopus/package.xml`

## 9. Threading and Execution Model

The app is not single-threaded in practice.

Relevant execution contexts:

1. Qt UI thread
2. MainWindow ROS2 executor thread
3. McapRecorder ROS2 executor thread when recording
4. Timer-driven refresh in widgets

Important implications:

- Display subscriptions run in the display executor thread.
- Recording subscriptions run in the recorder executor thread.
- Joint-state charting introduces an explicit queue to buffer data before UI refresh.
- Recording lifetime is tied to the recorder object lifetime.

## 10. Important Design Characteristics

These are the points worth remembering before touching code:

1. `MainWindow` is the operational hub of the live display path.
2. The UI layer is relatively direct; there is no deep domain abstraction between ROS2 callbacks and pages.
3. Display flow and recording flow are intentionally separate.
4. The project favors practical direct wiring over a heavily abstract architecture.
5. Config lives in a global namespace and is read or mutated directly by consumers.
6. Rendering depends on both `media` and `graphics`; `pages` are not self-sufficient.
7. Some runtime resources are expected next to the installed app, such as `models/RH56E2-R.gltf`.

## 11. Topic Families the App Cares About

The code and config strongly center around these topic families:

- Realsense camera images
  - `/realsense/right_hand/...`
  - `/realsense/left_hand/...`
  - `/realsense/top/...`
- Inspire hand tactile images
  - `/inspire/left_hand/tactile_*`
  - `/inspire/right_hand/tactile_*`
- Inspire hand joint states
  - `/inspire/left_hand/joint_states`
  - `/inspire/right_hand/joint_states`

If a future change is about a new sensor family, first check:

1. Does `MainWindow::subscribeTopics()` need a new display subscription path?
2. Does the settings/config default topic list need to be extended?
3. Does `McapRecorder::get_message_definition()` need new schema support?

## 12. Recommended Reading Order

If you need to re-enter this project quickly, read files in this order:

1. `ARCHITECTURE.md`
2. `octopus/src/main.cpp`
3. `octopus/src/scanner.cpp`
4. `octopus/src/mainwindow.cpp`
5. `octopus/src/pages/op-panel.cpp`
6. `octopus/src/mcap-recorder.cpp`
7. The specific page or rendering module you are about to change

This order gets you:

- boot sequence
- global runtime state
- live display wiring
- recording wiring
- then only the local module you need

## 13. Quick Map for Future Work

If the task is about one of these areas, start here:

- App startup / global runtime behavior
  - `octopus/src/main.cpp`
  - `octopus/src/scanner.cpp`
  - `octopus/src/mainwindow.cpp`
- Live image display
  - `octopus/src/mainwindow.cpp`
  - `octopus/src/pages/image-widget.cpp`
  - `octopus/src/graphics/texture-widget.h`
  - `octopus/src/media/resampler.h`
- Tactile hand visualization
  - `octopus/src/mainwindow.cpp`
  - `octopus/src/pages/hand-panel.cpp`
  - `octopus/src/graphics/rhi-widget.h`
  - `octopus/src/graphics/model.h`
- Joint-state charting
  - `octopus/src/pages/joint-state-panel.cpp`
  - `octopus/src/media/queue.h`
- Recording / MCAP
  - `octopus/src/pages/op-panel.cpp`
  - `octopus/src/mcap-recorder.cpp`
  - `octopus/src/utils/config.cpp`
- Theme / settings / persistence
  - `octopus/src/scanner.cpp`
  - `octopus/src/pages/settings-dialog.cpp`
  - `octopus/src/utils/config.cpp`

## 14. Summary

The shortest useful mental model is:

- `Scanner` is the Qt application shell.
- `MainWindow` is the live display composition root.
- `pages/` contains business-facing UI panels.
- `graphics/` and `media/` are the rendering support layers.
- `McapRecorder` is a separate recording pipeline with its own ROS2 node.
- `config` is shared global runtime state persisted to `scanner.json`.

If that model is loaded first, the rest of the project becomes much easier to navigate.
