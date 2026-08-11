#!/usr/bin/env python3
"""HIT · UMI 无本体数据采集系统 — GUI 一键启动器。

界面设计遵循 Apple HIG / emil design-engineering 思路：
  - 材质与深度：深色画布 + 上浮卡片 + 细边高光（深度即层级）。
  - 排版尺度：统一字重/字号层级，大字紧凑负字距、正文近 0 字距。
  - 间距网格：8pt 基准的节奏化留白，区块化分组。
  - 反馈：按钮按下 scale(0.97)、状态点平滑变色、单一主操作强调。
  - 直白标签：状态用「正常/异常/启动中」而非含糊统称。

功能：一键启动全部传感器节点 (start_all_sensor.sh) 与 Octopus 录制器 (start_octopus.sh)。
"""

import os
import sys
import subprocess
import threading
import signal
import time

import customtkinter as ctk
from tkinter import messagebox


# ---------------------------------------------------------------------------
# 全局主题
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# 桌面图标与 GUI 内图标共用同一张透明底源图，避免两处视觉不一致。
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ICON_PATH = os.path.join(
    WORKSPACE_DIR, "assets", "umi_launcher_icon_transparent.png"
)


class ActLauncher(ctk.CTk):
    """HIT · UMI 无本体数据采集系统 GUI 启动器主窗口。"""

    STARTUP_MODE_ALL = "all"
    STARTUP_MODE_NO_TACTILE = "no_tactile"
    STARTUP_MODE_LABELS = {
        STARTUP_MODE_ALL: "全部节点",
        STARTUP_MODE_NO_TACTILE: "Baton Mini + GoPro（不含触觉）",
    }

    # --- 传感器定义：(id, 显示名称) ---
    SENSOR_DEFS = [
        ("baton_mini.left", "Baton Mini（左）"),
        ("baton_mini.right", "Baton Mini（右）"),
        ("gopro", "GoPro"),
        ("pressure", "压力传感器"),
        ("octopus", "Octopus 上位机"),
    ]

    # --- 设计令牌（Design Tokens）---
    # 双栏布局：左侧栏更深更"沉"，右侧主区上浮。更鲜艳的强调色。
    COLOR_CANVAS = "#0a0b12"          # 最底层画布
    COLOR_SIDEBAR = "#11121f"         # 左侧栏（最深的"沉底"面）
    COLOR_SURFACE = "#1a1d2e"         # 右侧主区卡片表面
    COLOR_SURFACE_RAISED = "#252a42"  # 卡片内次级面（传感器行、日志框）
    COLOR_HAIRLINE = "#2e3450"        # 描边 / 分隔线

    # 文本层级
    COLOR_TEXT = "#f4f5fb"
    COLOR_TEXT_SECONDARY = "#b8bce0"
    COLOR_TEXT_TERTIARY = "#757ba0"

    # 状态色 —— 更鲜艳、饱和（赛博/霓虹倾向），让状态一眼跳出
    COLOR_OK = "#00e676"              # 鲜亮绿
    COLOR_ERR = "#ff3b6b"             # 鲜亮红粉
    COLOR_WARN = "#ffb13d"            # 鲜亮橙
    COLOR_DIM = "#757ba0"
    STATUS_COLORS = {
        "unknown": COLOR_DIM,
        "ok": COLOR_OK,
        "error": COLOR_ERR,
        "starting": COLOR_WARN,
    }
    STATUS_TEXT = {
        "unknown": "未知",
        "ok": "正常",
        "error": "异常",
        "starting": "启动中",
        "skipped": "未启动",
    }

    # 强调色：更鲜艳的青蓝→紫渐变主调（单一 primary 用青蓝）
    COLOR_ACCENT = "#2d8cff"          # 鲜亮蓝（主操作）
    COLOR_ACCENT_2 = "#7c5cff"        # 紫（侧栏装饰渐变端）

    # 排版尺度：集中定义，层级 = 字重 × 字号 × 字距（Apple §15）
    FONT_FAMILY = "SF Pro Display", "Inter", "Segoe UI", "PingFang SC",
    "Noto Sans CJK SC", "Microsoft YaHei", "Helvetica Neue", "sans-serif"
    FONT_MONO = "SF Mono", "JetBrains Mono", "Menlo", "Consolas",
    "DejaVu Sans Mono", "monospace"

    def _font(self, size, weight="normal"):
        return ctk.CTkFont(family=self.FONT_FAMILY, size=size, weight=weight)

    def _mono(self, size):
        return ctk.CTkFont(family=self.FONT_MONO, size=size)

    def __init__(self):
        super().__init__()

        # --- 窗口基本属性 ---
        self.title("UMI 无本体数据采集系统")
        self.minsize(1020, 680)
        self.configure(fg_color=self.COLOR_CANVAS)

        # --- 窗口图标（任务栏 / 标题栏）---
        self._set_window_icon()

        # 工作区路径
        self._workspace_dir = WORKSPACE_DIR

        # 进程变量
        self._sensor_proc = None
        self._octopus_proc = None
        self._startup_mode = self.STARTUP_MODE_ALL
        self._active_startup_mode = self.STARTUP_MODE_ALL
        self._running = False
        self._closing = False
        self._polling_after_id = None
        self._cancel_start = threading.Event()
        self._stop_lock = threading.Lock()

        # 加载 ROS 环境
        self._load_ros_env()

        # 创建 UI
        self._create_widgets()

        # 窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    # ------------------------------------------------------------------
    # 窗口图标
    # ------------------------------------------------------------------

    def _set_window_icon(self):
        """设置窗口标题栏 / 任务栏图标为 UMI 图标。

        用 PIL.ImageTk.PhotoImage（customtkinter 未暴露 ImageTk），
        缺失文件时静默跳过，绝不阻断启动。
        """
        from PIL import Image, ImageTk
        try:
            self._tk_icon = ImageTk.PhotoImage(
                Image.open(APP_ICON_PATH).convert("RGBA")
            )
            self.iconphoto(True, self._tk_icon)
        except Exception:
            self._tk_icon = None

    # ------------------------------------------------------------------
    # 环境加载
    # ------------------------------------------------------------------

    def _load_ros_env(self):
        """调用 act_launcher_env.sh，解析输出并合并到 os.environ。"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_script = os.path.join(script_dir, "act_launcher_env.sh")
        try:
            result = subprocess.run(
                ["bash", env_script],
                capture_output=True,
                text=True,
                errors="surrogateescape",
                timeout=30,
                check=True,
            )
            for line in result.stdout.splitlines():
                if "=" in line:
                    key, _, value = line.partition("=")
                    if key and not key.startswith("BASH_FUNC"):
                        os.environ[key] = value
        except Exception as exc:
            messagebox.showerror(
                "环境加载失败",
                f"无法加载 ROS 环境：\n{exc}\n\n"
                f"请确保工作区已编译（colcon build）且 ROS2 Jazzy 已安装。",
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _create_widgets(self):
        """加载目标风格三页 GUI，进程编排仍保留在本类。"""
        try:
            from act_launcher_ui import build_launcher_ui
        except ImportError:
            from scripts.act_launcher_ui import build_launcher_ui
        build_launcher_ui(self)

    # ------------------------------------------------------------------
    # 左侧栏
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        """左侧固定栏：品牌头 + 系统总览状态 + 版权。

        全栏用最深的面（COLOR_SIDEBAR）压住，顶部品牌区用强调渐变条点亮身份。
        """
        side = ctk.CTkFrame(self, fg_color=self.COLOR_SIDEBAR, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        side.configure(width=230)
        side.grid_rowconfigure(2, weight=1)  # 状态总览区弹性

        self._build_sidebar_brand(side)
        self._build_sidebar_overview(side)
        self._build_sidebar_footer(side)

    def _build_sidebar_brand(self, parent):
        """左栏顶部：应用图标 + HIT 徽标 + 标题 + 渐变高亮条。"""
        brand = ctk.CTkFrame(parent, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=18, pady=(20, 14))

        # 图标 + 文字（横向）
        try:
            from PIL import Image
            icon_image = Image.open(APP_ICON_PATH).convert("RGBA")
            icon = ctk.CTkImage(
                light_image=icon_image,
                dark_image=icon_image,
                size=(46, 46),
            )
            ctk.CTkLabel(brand, image=icon, text="").grid(
                row=0, column=0, rowspan=2, padx=(0, 12))
            self._sidebar_icon = icon  # 防 GC
        except Exception:
            self._sidebar_icon = None

        # HIT 徽标（鲜艳强调色底 + 白字）
        hit_badge = ctk.CTkFrame(
            brand, fg_color=self.COLOR_ACCENT, corner_radius=6, width=44, height=22,
        )
        hit_badge.grid(row=0, column=1, sticky="w", pady=(2, 0))
        hit_badge.grid_propagate(False)
        hit_badge.grid_columnconfigure(0, weight=1)
        hit_badge.grid_rowconfigure(0, weight=1)
        ctk.CTkLabel(
            hit_badge, text="HIT", text_color="#ffffff",
            font=self._font(11, "bold"),
        ).grid(row=0, column=0)

        ctk.CTkLabel(
            brand, text="UMI 无本体", anchor="w",
            font=self._font(15, "bold"), text_color=self.COLOR_TEXT,
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ctk.CTkLabel(
            brand, text="数据采集系统", anchor="w",
            font=self._font(15, "bold"), text_color=self.COLOR_TEXT,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(1, 0))

        ctk.CTkLabel(
            brand, text="武汉华威科智能有限公司", anchor="w",
            font=self._font(10), text_color=self.COLOR_TEXT_TERTIARY,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # 渐变高亮条（青蓝→紫），强化"鲜艳"感与品牌色
        self._after_gradient_bar(parent, row=1, height=3)

    def _after_gradient_bar(self, parent, row, height=3):
        """绘制一条蓝→紫的渐变高亮条（PIL 现画，CTkImage 贴到 CTkLabel）。"""
        try:
            from PIL import Image
            w, h = 230, height
            # 用 RGBA，便于 CTkImage 缩放；高度取 2 倍以利 HiDPI 清晰。
            grad = Image.new("RGBA", (w, h * 2))
            px = grad.load()
            c1 = (45, 140, 255)   # COLOR_ACCENT
            c2 = (124, 92, 255)   # COLOR_ACCENT_2
            for x in range(w):
                t = x / (w - 1)
                col = (int(c1[0] + (c2[0] - c1[0]) * t),
                       int(c1[1] + (c2[1] - c1[1]) * t),
                       int(c1[2] + (c2[2] - c1[2]) * t), 255)
                for y in range(h * 2):
                    px[x, y] = col
            # CTkImage 支持 HiDPI 缩放，避免 ImageTk 直接贴图的 Warning。
            self._grad_icon = ctk.CTkImage(grad, size=(w, h))
            ctk.CTkLabel(parent, image=self._grad_icon, text="").grid(
                row=row, column=0, sticky="ew", padx=0, pady=0)
        except Exception:
            self._grad_icon = None

    def _build_sidebar_overview(self, parent):
        """左栏中部：系统总览（运行状态 + 各传感器迷你状态点列）。"""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=2, column=0, sticky="nsew", padx=18, pady=(6, 14))
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box, text="系统总览", anchor="w",
            font=self._font(10, "bold"), text_color=self.COLOR_TEXT_TERTIARY,
        ).pack(fill="x", pady=(0, 8))

        # 运行状态卡片（鲜艳绿=运行 / 灰=就绪）
        self._sys_state_card = ctk.CTkFrame(
            box, fg_color=self.COLOR_SURFACE_RAISED, corner_radius=10,
        )
        self._sys_state_card.pack(fill="x", pady=(0, 12))
        self._sys_dot = ctk.CTkLabel(
            self._sys_state_card, text="●", font=self._font(14),
            text_color=self.COLOR_DIM,
        )
        self._sys_dot.pack(side="left", padx=(12, 8), pady=10)
        self._sys_state_label = ctk.CTkLabel(
            self._sys_state_card, text="就绪", anchor="w",
            font=self._font(12, "bold"), text_color=self.COLOR_TEXT,
        )
        self._sys_state_label.pack(side="left", pady=10)
        # 右侧时钟（mono，次级明度）
        self._clock_label = ctk.CTkLabel(
            self._sys_state_card, text="", font=self._mono(11),
            text_color=self.COLOR_TEXT_SECONDARY,
        )
        self._clock_label.pack(side="right", padx=12)
        self._tick_clock()
        self.after(1000, self._tick_clock)

        # 各传感器迷你状态点列
        ctk.CTkLabel(
            box, text="传感器", anchor="w",
            font=self._font(10, "bold"), text_color=self.COLOR_TEXT_TERTIARY,
        ).pack(fill="x", pady=(2, 6))

    def _build_sidebar_footer(self, parent):
        """左栏底部：ACT Launcher 标识 + 版本感小字。"""
        foot = ctk.CTkFrame(parent, fg_color="transparent")
        foot.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 16))
        ctk.CTkLabel(
            foot, text="ACT Launcher", anchor="w",
            font=self._font(11, "bold"), text_color=self.COLOR_TEXT_SECONDARY,
        ).pack(fill="x")
        ctk.CTkLabel(
            foot, text="ROS 2 · Jazzy", anchor="w",
            font=self._font(9), text_color=self.COLOR_TEXT_TERTIARY,
        ).pack(fill="x", pady=(2, 0))

    def _tick_clock(self):
        """每秒刷新左侧栏运行状态卡的时钟。"""
        self._clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self._tick_clock)

    # ------------------------------------------------------------------
    # 右侧主区
    # ------------------------------------------------------------------

    def _build_main_area(self):
        """右侧主区：传感器状态网格 + 系统日志 + 主操作按钮条。"""
        main = ctk.CTkFrame(self, fg_color=self.COLOR_CANVAS, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)  # 日志区弹性拉伸

        self._build_status_grid(main)   # row 0
        self._build_log_panel(main)     # row 1
        self._build_button_bar(main)    # row 2

    def _build_status_grid(self, parent):
        """传感器状态网格：每个传感器一张卡片，2 列网格排布。

        每张卡片：左侧大状态点 + 名称（主）+ 副标题 + 右侧状态值。
        卡片化、留白足，靠分组+映射（Apple §16）让"哪个传感器、什么状态"一目了然。
        """
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=1)

        self._sensor_labels = {}
        for idx, (sensor_id, label_text) in enumerate(self.SENSOR_DEFS):
            r, c = divmod(idx, 2)
            card = ctk.CTkFrame(
                wrap, fg_color=self.COLOR_SURFACE, corner_radius=14,
                border_width=1, border_color=self.COLOR_HAIRLINE,
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            card.grid_columnconfigure(1, weight=1)

            # 左：大状态点（鲜艳色，未定=灰）
            status_label = ctk.CTkLabel(
                card, text="●", width=22, font=self._font(22),
                text_color=self.STATUS_COLORS["unknown"],
            )
            status_label.grid(row=0, column=0, padx=(16, 10), pady=16, rowspan=2)

            # 名称
            ctk.CTkLabel(
                card, text=label_text, anchor="w",
                font=self._font(14, "bold"), text_color=self.COLOR_TEXT,
            ).grid(row=0, column=1, sticky="sw", pady=(14, 0))

            # 状态值（右下，次级）
            desc_label = ctk.CTkLabel(
                card, text="未知", anchor="e",
                font=self._font(12), text_color=self.COLOR_TEXT_TERTIARY,
            )
            desc_label.grid(row=1, column=1, sticky="se", padx=(0, 16), pady=(0, 14))

            self._sensor_labels[sensor_id] = (status_label, desc_label)

    def _build_log_panel(self, parent):
        """系统日志面板：终端风深色文本框，占主区弹性空间。"""
        card = ctk.CTkFrame(
            parent, fg_color=self.COLOR_SURFACE, corner_radius=14,
            border_width=1, border_color=self.COLOR_HAIRLINE,
        )
        card.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="系统日志", anchor="w",
            font=self._font(11, "bold"), text_color=self.COLOR_TEXT_TERTIARY,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self._log_text = ctk.CTkTextbox(
            card, wrap="word", font=self._mono(12),
            fg_color=self.COLOR_SURFACE_RAISED, text_color=self.COLOR_TEXT,
            border_width=1, border_color=self.COLOR_HAIRLINE, corner_radius=10,
        )
        self._log_text.grid(row=1, column=0, padx=10, pady=(0, 14), sticky="nsew")
        self._log_text.configure(state="disabled")

    def _build_button_bar(self, parent):
        """底部主操作栏：单一主操作突出，次级操作克制，退出最弱靠右。

        层级（Apple §6/§16）：「启动」=鲜艳蓝填充主操作；「冒烟」=描边次级；
        「停止」=鲜艳红危险色但默认禁用；「退出」=最弱文本感。
        按下反馈 scale(0.97)（emil）由 CTkButton 内置。
        """
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 20))
        bar.grid_columnconfigure(99, weight=1)  # 退出推到右侧

        # 主操作：鲜艳蓝填充
        self._btn_start = ctk.CTkButton(
            bar, text="▶  启动系统", command=self._start_system, width=140, height=44,
            fg_color=self.COLOR_ACCENT, hover_color="#1a78f0", text_color="#ffffff",
            corner_radius=12, font=self._font(14, "bold"),
        )
        self._btn_start.grid(row=0, column=0, padx=(0, 8))

        # 次级：描边
        self._btn_smoke = ctk.CTkButton(
            bar, text="冒烟测试", command=self._start_smoke_test, width=118, height=44,
            fg_color="transparent", hover_color=self.COLOR_SURFACE_RAISED,
            border_width=1, border_color=self.COLOR_HAIRLINE,
            text_color=self.COLOR_TEXT, corner_radius=12, font=self._font(14),
        )
        self._btn_smoke.grid(row=0, column=1, padx=(0, 8))

        # 危险：默认禁用，鲜艳红
        self._btn_stop = ctk.CTkButton(
            bar, text="■  停止系统", command=self._stop_system, width=130, height=44,
            fg_color=self.COLOR_ERR, hover_color="#e02050", text_color="#ffffff",
            corner_radius=12, font=self._font(14, "bold"), state="disabled",
        )
        self._btn_stop.grid(row=0, column=2)

        # 最弱：退出靠右
        self._btn_exit = ctk.CTkButton(
            bar, text="退出", command=self._on_exit, width=88, height=44,
            fg_color="transparent", hover_color=self.COLOR_SURFACE_RAISED,
            text_color=self.COLOR_TEXT_SECONDARY, corner_radius=12,
            font=self._font(13),
        )
        self._btn_exit.grid(row=0, column=100, padx=(8, 0), sticky="e")

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------

    def _start_system(self):
        """启动系统（正常模式）。"""
        threading.Thread(
            target=self._run_start_sequence,
            args=(False, self._startup_mode),
            daemon=True,
        ).start()

    def _start_smoke_test(self):
        """启动系统（冒烟测试模式）。"""
        threading.Thread(
            target=self._run_start_sequence,
            args=(True, self._startup_mode),
            daemon=True,
        ).start()

    def _set_startup_mode(self, mode):
        """更新待启动模式；运行中由按钮状态阻止切换。"""
        if mode not in self.STARTUP_MODE_LABELS:
            return
        self._startup_mode = mode
        if self._running:
            return
        pressure_status = (
            "skipped"
            if mode == self.STARTUP_MODE_NO_TACTILE
            else "unknown"
        )
        pressure_desc = (
            "当前模式跳过"
            if pressure_status == "skipped"
            else "等待启动"
        )
        self._update_sensor_status("pressure", pressure_status, pressure_desc)

    def _run_start_sequence(self, smoke_test=False, startup_mode=None):
        """执行完整启动序列，在后台线程中运行。"""
        if self._running:
            return
        startup_mode = startup_mode or getattr(
            self, "_startup_mode", self.STARTUP_MODE_ALL
        )
        if startup_mode not in self.STARTUP_MODE_LABELS:
            startup_mode = self.STARTUP_MODE_ALL
        self._active_startup_mode = startup_mode
        no_tactile = startup_mode == self.STARTUP_MODE_NO_TACTILE
        self._running = True
        self._cancel_start.clear()

        # 切换按钮状态
        self.after(0, self._set_buttons_running, True)
        self.after(0, self._set_system_state, "starting")

        mode_text = "冒烟测试" if smoke_test else "启动系统"
        profile_text = self.STARTUP_MODE_LABELS[startup_mode]
        self.after(0, self._append_log, f"\n=== {mode_text} ===\n")
        self.after(0, self._append_log, f"启动模式：{profile_text}\n")

        # 正常模式下传感器与 Octopus 同时进入启动中状态。
        for sensor_id in self._sensor_labels:
            if sensor_id == "pressure" and no_tactile:
                self.after(
                    0,
                    self._update_sensor_status,
                    sensor_id,
                    "skipped",
                    "当前模式跳过",
                )
            elif sensor_id == "octopus":
                self.after(
                    0,
                    self._update_sensor_status,
                    sensor_id,
                    "starting" if not smoke_test else "unknown",
                    "同步启动中..." if not smoke_test else "冒烟测试不启动",
                )
            else:
                self.after(
                    0,
                    self._update_sensor_status,
                    sensor_id,
                    "starting",
                    "启动中...",
                )

        # Phase 1：启动传感器
        sensor_script_name = (
            "start_baton_gopro.sh" if no_tactile else "start_all_sensor.sh"
        )
        sensor_script = os.path.join(self._workspace_dir, sensor_script_name)
        cmd = [sensor_script]
        if smoke_test:
            cmd.append("--smoke-test")

        self.after(0, self._append_log, f"[Phase 1] 启动传感器: {' '.join(cmd)}\n")

        try:
            self._sensor_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=os.environ,
                start_new_session=True,
                cwd=self._workspace_dir,
            )
        except Exception as exc:
            self.after(0, self._append_log, f"错误：无法启动传感器进程: {exc}\n")
            self.after(0, self._reset_to_idle, smoke_test)
            return

        # 正常模式不等待传感器编译、身份校验或 postlaunch；传感器进程
        # 创建成功后立即创建 Octopus 进程，让节点与上位机并行启动。
        if not smoke_test:
            self._launch_octopus()

        # 逐行读取传感器输出
        sensor_success = False
        try:
            for line in self._sensor_proc.stdout:
                if self._cancel_start.is_set():
                    break
                self.after(0, self._append_log, line)
                # 检测启动成功标志
                if "postlaunch" in line.lower() or "全部通过" in line:
                    sensor_success = True
                if "冒烟测试通过" in line:
                    sensor_success = True
                # 正常模式下传感器进程会长期运行，不能等它关闭 stdout。
                # 一旦状态检查通过，剩余日志改由独立线程继续读取；
                # Octopus 已在传感器进程创建后并行启动。
                if sensor_success and not smoke_test:
                    break
        except Exception as exc:
            self.after(0, self._append_log, f"读取传感器输出异常: {exc}\n")

        # 等待进程结束（冒烟测试会自行退出；正常模式会持续运行）
        if smoke_test:
            self._sensor_proc.wait()
            if self._sensor_proc.returncode == 0:
                sensor_success = True
            else:
                sensor_success = False
                self.after(
                    0, self._append_log,
                    f"冒烟测试失败，退出码: {self._sensor_proc.returncode}\n",
                )

            self._sensor_proc = None
            self.after(0, self._append_log, "\n=== 冒烟测试完成 ===\n")
            self.after(0, self._reset_to_idle, True)
            return

        # 正常模式：检查进程是否仍在运行
        if self._sensor_proc and self._sensor_proc.poll() is None:
            sensor_success = True
            self.after(0, self._append_log, "[Phase 1] 传感器启动成功，进程运行中\n")
            threading.Thread(
                target=self._read_proc_output,
                args=(self._sensor_proc, "[Sensors]"),
                daemon=True,
            ).start()
        elif not sensor_success:
            self.after(0, self._append_log, "[Phase 1] 传感器启动失败\n")
            self._do_stop_system()
            return

        if self._cancel_start.is_set():
            return

        self.after(0, self._start_polling)

    def _launch_octopus(self):
        """立即启动 Octopus，不等待传感器健康检查完成。"""
        self.after(0, self._append_log, "\n[Phase 2] 启动 Octopus...\n")
        self.after(
            0,
            self._update_sensor_status,
            "octopus",
            "starting",
            "正在启动界面...",
        )
        octopus_script = os.path.join(self._workspace_dir, "start_octopus.sh")
        if not os.path.isfile(octopus_script):
            self.after(0, self._append_log, f"Octopus 启动脚本不存在: {octopus_script}\n")
            self.after(
                0,
                self._update_sensor_status,
                "octopus",
                "error",
                "启动脚本不存在",
            )
            self.after(0, self._set_system_state, "error", "Octopus 启动脚本不存在")
            return False

        try:
            self._octopus_proc = subprocess.Popen(
                ["bash", octopus_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=os.environ,
                start_new_session=True,
                cwd=self._workspace_dir,
            )
        except Exception as exc:
            self.after(0, self._append_log, f"无法启动 Octopus: {exc}\n")
            self._octopus_proc = None
            self.after(
                0,
                self._update_sensor_status,
                "octopus",
                "error",
                f"无法启动：{exc}",
            )
            self.after(0, self._set_system_state, "error", "Octopus 无法启动")
            return False

        # 启动 Octopus 日志与退出状态监视线程。
        octopus_proc = self._octopus_proc
        octo_thread = threading.Thread(
            target=self._watch_octopus,
            args=(octopus_proc,),
            daemon=True,
        )
        octo_thread.start()

        # 能持续存活一小段时间，才认为 GUI 启动成功；动态库、Qt 平台
        # 插件等错误通常会让进程立即退出。
        time.sleep(1.5)
        if octopus_proc.poll() is None:
            self.after(0, self._append_log, "[Phase 2] Octopus 界面已启动\n")
            self.after(
                0,
                self._update_sensor_status,
                "octopus",
                "ok",
                "界面运行中",
            )
        else:
            self.after(
                0,
                self._append_log,
                f"[Phase 2] Octopus 启动失败，退出码: {octopus_proc.returncode}\n",
            )
            return False
        return True

    def _read_proc_output(self, proc, prefix=""):
        """后台线程：逐行读取进程输出并写入日志面板。"""
        try:
            for line in proc.stdout:
                self.after(0, self._append_log, f"{prefix} {line}")
        except Exception as exc:
            self.after(0, self._append_log, f"{prefix} 日志读取异常: {exc}\n")

    def _watch_octopus(self, proc):
        """读取 Octopus 日志，并在意外退出时更新界面状态。"""
        self._read_proc_output(proc, "[Octopus]")
        returncode = proc.wait()
        if self._octopus_proc is proc:
            self._octopus_proc = None
        if self._running and not self._cancel_start.is_set():
            self.after(
                0,
                self._update_sensor_status,
                "octopus",
                "error",
                f"界面已退出（代码 {returncode}）",
            )
            self.after(
                0,
                self._append_log,
                f"[Octopus] 进程意外退出，代码: {returncode}\n",
            )
            self.after(0, self._set_system_state, "error", "Octopus 上位机已退出")

    def _reset_to_idle(self, smoke_test=False):
        """重置按钮和传感器状态到空闲。"""
        self._running = False
        self._cancel_start.clear()
        self._btn_start.configure(state="normal")
        self._btn_smoke.configure(state="normal")
        self._btn_stop.configure(state="disabled")
        for sensor_id in self._sensor_labels:
            if (
                sensor_id == "pressure"
                and self._startup_mode == self.STARTUP_MODE_NO_TACTILE
            ):
                self._update_sensor_status(sensor_id, "skipped", "当前模式跳过")
            else:
                self._update_sensor_status(sensor_id, "unknown", "已停止")
        self._set_system_state("ready")

    def _set_buttons_running(self, running):
        """切换按钮状态：运行中 / 空闲。"""
        if running:
            self._btn_start.configure(state="disabled")
            self._btn_smoke.configure(state="disabled")
            self._btn_stop.configure(state="normal")
            if hasattr(self, "_startup_mode_selector"):
                self._startup_mode_selector.configure(state="disabled")
        else:
            self._btn_start.configure(state="normal")
            self._btn_smoke.configure(state="normal")
            self._btn_stop.configure(state="disabled")
            if hasattr(self, "_startup_mode_selector"):
                self._startup_mode_selector.configure(state="normal")

    def _stop_system(self):
        """停止全部系统进程。"""
        if not self._running:
            return
        threading.Thread(target=self._do_stop_system, daemon=True).start()

    def _do_stop_system(self):
        """实际执行停止操作（在后台线程中运行）。"""
        with self._stop_lock:
            if not self._running:
                return

            self._cancel_start.set()
            self.after(0, self._append_log, "\n=== 停止系统 ===\n")
            self.after(0, self._set_system_state, "stopping")

            # 停止传感器状态轮询
            if self._polling_after_id is not None:
                self.after(0, lambda: self.after_cancel(self._polling_after_id))
                self._polling_after_id = None

            # 先停止 Octopus（使用进程组终止）
            if self._octopus_proc is not None:
                octopus_proc = self._octopus_proc
                self.after(0, self._append_log, "停止 Octopus...\n")
                try:
                    pgid = os.getpgid(octopus_proc.pid)
                    os.killpg(pgid, signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    pass
                try:
                    octopus_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(os.getpgid(octopus_proc.pid), signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        pass
                    try:
                        octopus_proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        pass
                if self._octopus_proc is octopus_proc:
                    self._octopus_proc = None

            # 再停止传感器（发送 SIGINT 给进程组）
            if self._sensor_proc is not None:
                self.after(0, self._append_log, "停止传感器...\n")
                try:
                    pgid = os.getpgid(self._sensor_proc.pid)
                    os.killpg(pgid, signal.SIGINT)
                except (ProcessLookupError, OSError):
                    pass
                try:
                    self._sensor_proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._sensor_proc.kill()
                    try:
                        self._sensor_proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                self._sensor_proc = None

            self.after(0, setattr, self, '_running', False)
            self.after(0, self._set_buttons_running, False)

            # 重置传感器状态
            for sensor_id in self._sensor_labels:
                if (
                    sensor_id == "pressure"
                    and self._startup_mode == self.STARTUP_MODE_NO_TACTILE
                ):
                    self.after(
                        0,
                        self._update_sensor_status,
                        sensor_id,
                        "skipped",
                        "当前模式跳过",
                    )
                else:
                    self.after(
                        0,
                        self._update_sensor_status,
                        sensor_id,
                        "unknown",
                        "已停止",
                    )

            self.after(0, self._append_log, "=== 系统已停止 ===\n")
            self.after(0, self._set_system_state, "ready", "系统已安全停止")


    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------

    def _append_log(self, text):
        """向日志面板追加带时间戳和等级颜色的 UTF-8 文本。"""
        self._log_text.configure(state="normal")
        lines = text.splitlines() or [text]
        for line in lines:
            stripped = line.strip()
            upper = stripped.upper()
            if any(token in upper for token in ("FAIL", "ERROR", "错误", "失败", "异常")):
                tag = "ERROR"
            elif any(token in upper for token in ("WARN", "警告")):
                tag = "WARN"
            elif any(token in upper for token in (" OK ", "OK ", "成功", "完成", "通过")):
                tag = "SUCCESS"
            else:
                tag = "INFO"
            if stripped:
                rendered = f"[{time.strftime('%H:%M:%S')}]  {line}\n"
            else:
                rendered = "\n"
            self._log_text._textbox.insert("end", rendered, (tag,))
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # 传感器状态
    # ------------------------------------------------------------------

    def _update_sensor_status(self, sensor_id, status, desc=""):
        """更新指定传感器的状态指示灯。

        颜色 + 文字双重编码（Apple §16 feedback）：状态点与描述同色，
        让「正常/异常」一眼可辨，不仅靠颜色（色盲友好）。
        """
        if sensor_id not in self._sensor_labels:
            return
        status_label, desc_label = self._sensor_labels[sensor_id]
        styles = {
            "unknown": ("#8992AA", "#202538"),
            "ok": ("#3AD99F", "#12362E"),
            "error": ("#FF647C", "#3A1822"),
            "starting": ("#F2B84B", "#3B3018"),
            "skipped": ("#8EA0B8", "#202A38"),
        }
        color, background = styles.get(status, styles["unknown"])
        status_label.configure(
            text=f"●  {self.STATUS_TEXT.get(status, '未知')}",
            text_color=color,
            fg_color=background,
        )
        desc_label.configure(
            text=desc or self.STATUS_TEXT.get(status, "未知"),
            text_color=color if status != "unknown" else "#747D90",
        )
        if not hasattr(self, "_card_status"):
            self._card_status = {}
        self._card_status[sensor_id] = status

    def _start_polling(self):
        """启动传感器状态轮询。"""
        self._set_system_state("running")
        self._poll_sensor_status()

    def _poll_sensor_status(self, force=False):
        """每 10 秒调用 all_sensor_status.py postlaunch 更新状态。"""
        if not self._running and not force:
            return
        if getattr(self, "_status_poll_inflight", False):
            return
        self._status_poll_inflight = True
        if hasattr(self, "_refresh_btn"):
            self._refresh_btn.configure(state="disabled", text="检测中…")

        status_script = os.path.join(
            self._workspace_dir, "scripts", "all_sensor_status.py"
        )
        config_file = os.path.join(
            self._workspace_dir, "config", "all_sensor_nodes.yaml"
        )
        status_mode_args = []
        if self._active_startup_mode == self.STARTUP_MODE_NO_TACTILE:
            status_mode_args = ["--no-pressure", "--skip-hardware-identity"]

        def _do_poll():
            try:
                result = subprocess.run(
                    [sys.executable, status_script, "postlaunch",
                     "--config", config_file, *status_mode_args],
                    capture_output=True, text=True, env=os.environ, timeout=30,
                )
                output = result.stdout
                self.after(0, self._parse_sensor_status, output)
                if result.stderr:
                    self.after(0, self._append_log, result.stderr)
            except Exception as exc:
                self.after(0, self._append_log, f"状态刷新失败: {exc}")
            finally:
                def finish_poll():
                    self._status_poll_inflight = False
                    if hasattr(self, "_refresh_btn"):
                        self._refresh_btn.configure(state="normal", text="↻  刷新")
                self.after(0, finish_poll)

        threading.Thread(target=_do_poll, daemon=True).start()

        # 运行中每 10 秒自动轮询；手动刷新不会创建重复定时器。
        if self._running and self._polling_after_id is None:
            def scheduled_poll():
                self._polling_after_id = None
                self._poll_sensor_status()
            self._polling_after_id = self.after(10000, scheduled_poll)

    def _parse_sensor_status(self, output):
        """解析 postlaunch 输出，更新传感器状态灯。"""
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("OK"):
                # OK   Baton Mini right: ...
                self._match_and_update(line, "ok")
            elif line.startswith("FAIL"):
                self._match_and_update(line, "error")
            elif line.startswith("WARN"):
                self._match_and_update(line, "starting")
        if self._running:
            values = [
                value
                for value in getattr(self, "_card_status", {}).values()
                if value != "skipped"
            ]
            if "error" in values:
                self._set_system_state("error", "检测到设备或节点异常")
            elif "starting" in values:
                self._set_system_state("warning", "部分设备状态不完整")
            elif values and all(value == "ok" for value in values):
                self._set_system_state("running")

    def _match_and_update(self, line, status):
        """根据日志行内容匹配传感器并更新状态。"""
        label_map = {
            "Baton Mini left": "baton_mini.left",
            "Baton Mini right": "baton_mini.right",
            "HWK pressure": "pressure",
        }
        for gopro_label in ("GoPro left", "GoPro right"):
            if gopro_label.lower() in line.lower():
                self._subdevice_status[gopro_label] = status
                left = self._subdevice_status.get("GoPro left", "unknown")
                right = self._subdevice_status.get("GoPro right", "unknown")
                states = (left, right)
                if "error" in states:
                    aggregate = "error"
                elif "starting" in states:
                    aggregate = "starting"
                elif states == ("ok", "ok"):
                    aggregate = "ok"
                else:
                    aggregate = "unknown"
                desc = {
                    "ok": "左右两路正常",
                    "error": "至少一路异常",
                    "starting": "至少一路不完整",
                    "unknown": "等待两路检测",
                }[aggregate]
                self.after(
                    0, self._update_sensor_status, "gopro", aggregate, desc
                )
                return
        for label_text, sensor_id in label_map.items():
            if label_text.lower() in line.lower():
                desc = line.split(":", 1)[-1].strip() if ":" in line else ""
                self.after(
                    0, self._update_sensor_status, sensor_id, status, desc,
                )
                break

    # ------------------------------------------------------------------
    # 退出
    # ------------------------------------------------------------------

    def _on_exit(self):
        """退出应用，如有进程运行则弹出确认。"""
        if self._closing:
            return
        if self._running:
            if not messagebox.askyesno("确认退出", "系统正在运行，确认停止并退出？"):
                return
            self._closing = True
            self._cancel_start.set()
            # 用户确认后立即移除窗口；进程清理继续在后台执行。避免 ROS/Qt
            # 退出等待让关闭按钮看起来像没有响应。
            self.withdraw()
            threading.Thread(target=self._do_stop_and_quit, daemon=True).start()
        else:
            self._closing = True
            self.destroy()

    def _do_stop_and_quit(self):
        """后台线程：停止系统后销毁窗口。"""
        try:
            self._do_stop_system()
        finally:
            self.after(0, self.destroy)


def main():
    app = ActLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
