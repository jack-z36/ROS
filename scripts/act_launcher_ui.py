#!/usr/bin/env python3
"""ACT Launcher 的目标风格界面构建器。

本模块只负责界面与只读配置展示。传感器、Octopus 的进程编排仍由
act_launcher.py 负责，避免视觉升级改变既有启动语义。
"""

from __future__ import annotations

import os
import subprocess
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox

import customtkinter as ctk
import yaml
from PIL import Image, ImageOps


WORKSPACE_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = WORKSPACE_DIR / "assets"
LAUNCHER_ASSET_DIR = ASSET_DIR / "launcher"
OCTOPUS_ICON_DIR = (
    WORKSPACE_DIR
    / "src/data_collection/VTLA_octopus-master/octopus/resources/icons"
)
CONFIG_PATH = WORKSPACE_DIR / "config/all_sensor_nodes.yaml"
IDENTITY_PATH = WORKSPACE_DIR / "config/hardware_identity_map.yaml"


class _FillHeightScrollableFrame(ctk.CTkScrollableFrame):
    """内容较短时填满视口，内容较长时仍可正常滚动。

    CTkScrollableFrame 的垂直模式默认只同步内部宽度，内部高度保持为所有
    子控件的自然高度。总览页在大屏上因此无法把剩余高度分配给日志区。
    """

    def _fit_frame_dimensions_to_canvas(self, event):
        super()._fit_frame_dimensions_to_canvas(event)
        if self._orientation != "vertical":
            return
        content_height = max(1, self.winfo_reqheight())
        self._parent_canvas.itemconfigure(
            self._create_window_id,
            height=max(event.height, content_height),
        )


def _detect_cjk_font(app) -> str:
    """选择本机实际存在的中文字体，杜绝 Tk 回退导致的缺字或糊字。"""
    installed = set(tkfont.families(app))
    for family in (
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "Microsoft YaHei",
        "DejaVu Sans",
    ):
        if family in installed:
            return family
    return "TkDefaultFont"


def _load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return yaml.safe_load(stream) or {}
    except (OSError, yaml.YAMLError):
        return {}


def _open_path(path: Path) -> None:
    try:
        subprocess.Popen(
            ["xdg-open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        messagebox.showerror("打开失败", f"无法打开：\n{path}\n\n{exc}")


def _transparent_image(path: Path, size: tuple[int, int]) -> ctk.CTkImage | None:
    try:
        image = Image.open(path).convert("RGBA")
        return ctk.CTkImage(light_image=image, dark_image=image, size=size)
    except (OSError, ValueError):
        return None


def _button(
    parent,
    *,
    text,
    command,
    font,
    width=160,
    height=46,
    fg="#171C27",
    hover="#242B3A",
    border="#30384A",
    text_color="#F4F6FB",
    bold=False,
):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        corner_radius=8,
        fg_color=fg,
        hover_color=hover,
        border_width=1,
        border_color=border,
        text_color=text_color,
        font=font(14, "bold" if bold else "normal"),
    )


def _use_native_titlebar(environment=None) -> bool:
    """默认交给窗口管理器管理；仅显式请求时启用自绘标题栏。

    override-redirect 窗口不会进入 Ubuntu 的任务栏/分页器，最小化后也
    缺少可靠的系统恢复入口。原生标题栏因此是生产默认，自绘模式只保留
    给明确接受该限制的视觉演示。
    """
    environment = os.environ if environment is None else environment
    if environment.get("ACT_LAUNCHER_NATIVE_TITLEBAR") == "1":
        return True
    return environment.get("ACT_LAUNCHER_CUSTOM_TITLEBAR") != "1"


def _configure_window(app) -> int:
    """配置窗口并返回内容所在的起始行。"""
    app._native_titlebar = _use_native_titlebar()
    app.minsize(1180, 760)
    width, height = 1480, 1200
    screen_w = app.winfo_screenwidth()
    screen_h = app.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(28, (screen_h - height) // 2)
    app.geometry(f"{width}x{height}+{x}+{y}")

    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(1 if not app._native_titlebar else 0, weight=1)
    if app._native_titlebar:
        return 0

    app.overrideredirect(True)
    title = ctk.CTkFrame(
        app, height=46, corner_radius=0, fg_color="#10141C"
    )
    title.grid(row=0, column=0, sticky="ew")
    title.grid_propagate(False)
    title.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(
        title,
        text="HiT 华威科",
        font=app._font(16, "bold"),
        text_color="#F7F8FC",
    ).grid(row=0, column=0, padx=(18, 12), sticky="w")
    ctk.CTkLabel(
        title,
        text="UMI 无本体数据采集系统",
        font=app._font(12),
        text_color="#737C90",
    ).grid(row=0, column=1, sticky="w")

    app._restore_geometry = None
    app._drag_origin = None
    app._resize_origin = None

    def begin_drag(event):
        if app._restore_geometry is not None:
            return
        app._drag_origin = (
            event.x_root,
            event.y_root,
            app.winfo_x(),
            app.winfo_y(),
        )

    def drag(event):
        if not app._drag_origin:
            return
        start_x, start_y, win_x, win_y = app._drag_origin
        app.geometry(
            f"+{win_x + event.x_root - start_x}"
            f"+{win_y + event.y_root - start_y}"
        )

    def minimize():
        app.overrideredirect(False)
        app.iconify()

        def restore_override(_event=None):
            app.after(40, lambda: app.overrideredirect(True))
            app.unbind("<Map>", map_binding)

        map_binding = app.bind("<Map>", restore_override, add="+")

    def toggle_maximize(_event=None):
        if app._restore_geometry is None:
            app._restore_geometry = app.geometry()
            app.geometry(f"{screen_w}x{max(760, screen_h - 32)}+0+32")
            max_btn.configure(text="❐")
        else:
            app.geometry(app._restore_geometry)
            app._restore_geometry = None
            max_btn.configure(text="□")

    title.bind("<ButtonPress-1>", begin_drag)
    title.bind("<B1-Motion>", drag)
    title.bind("<Double-Button-1>", toggle_maximize)

    controls = ctk.CTkFrame(title, fg_color="transparent")
    controls.grid(row=0, column=2, sticky="e")
    for text, command, hover in (
        ("—", minimize, "#252B37"),
        ("□", toggle_maximize, "#252B37"),
        ("×", app._on_exit, "#C9364F"),
    ):
        control = ctk.CTkButton(
            controls,
            text=text,
            command=command,
            width=56,
            height=46,
            corner_radius=0,
            fg_color="transparent",
            hover_color=hover,
            font=app._font(21, "bold"),
            text_color="#D6DAE4",
            cursor="hand2",
        )
        control.pack(side="left")
        if text == "□":
            max_btn = control

    # 无边框窗口保留右下角缩放能力。
    grip = ctk.CTkLabel(
        app,
        text="◢",
        width=18,
        height=18,
        text_color="#596176",
        font=app._font(11),
        cursor="bottom_right_corner",
    )
    grip.place(relx=1.0, rely=1.0, anchor="se")
    grip.lift()

    def begin_resize(event):
        app._resize_origin = (
            event.x_root,
            event.y_root,
            app.winfo_width(),
            app.winfo_height(),
        )

    def resize(event):
        if not app._resize_origin or app._restore_geometry is not None:
            return
        start_x, start_y, start_w, start_h = app._resize_origin
        app.geometry(
            f"{max(1180, start_w + event.x_root - start_x)}x"
            f"{max(760, start_h + event.y_root - start_y)}"
        )

    grip.bind("<ButtonPress-1>", begin_resize)
    grip.bind("<B1-Motion>", resize)
    return 1


def _build_sidebar(app, parent, show_page) -> None:
    side = ctk.CTkFrame(parent, width=232, corner_radius=0, fg_color="#0D1119")
    side.grid(row=0, column=0, sticky="nsew")
    side.grid_propagate(False)
    side.grid_rowconfigure(4, weight=1)

    brand = ctk.CTkFrame(side, fg_color="transparent")
    brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 18))
    icon = _transparent_image(ASSET_DIR / "umi_launcher_icon_transparent.png", (72, 72))
    if icon:
        app._sidebar_icon = icon
        ctk.CTkLabel(brand, image=icon, text="").pack(pady=(0, 10))
    ctk.CTkLabel(
        brand,
        text="UMI 无本体",
        font=app._font(17, "bold"),
        text_color="#F5F6FA",
    ).pack()
    ctk.CTkLabel(
        brand,
        text="数据采集系统",
        font=app._font(17, "bold"),
        text_color="#F5F6FA",
    ).pack(pady=(2, 0))
    ctk.CTkLabel(
        brand,
        text="武汉华威科智能有限公司",
        font=app._font(10),
        text_color="#747C8E",
    ).pack(pady=(12, 0))

    nav = ctk.CTkFrame(side, fg_color="transparent")
    nav.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 8))
    app._nav_buttons = {}
    for page_id, icon_text, label in (
        ("overview", "✥", "系统总览"),
        ("sensors", "▦", "传感器"),
    ):
        button = ctk.CTkButton(
            nav,
            text=f"  {icon_text}   {label}",
            command=lambda p=page_id: show_page(p),
            height=46,
            anchor="w",
            corner_radius=8,
            fg_color="transparent",
            hover_color="#1C2230",
            text_color="#8F96A8",
            font=app._font(14, "bold"),
        )
        button.pack(fill="x", pady=3)
        app._nav_buttons[page_id] = button

    ctk.CTkLabel(
        side,
        text="系统状态",
        anchor="w",
        font=app._font(12, "bold"),
        text_color="#727A8D",
    ).grid(row=2, column=0, sticky="ew", padx=26, pady=(18, 8))

    state_card = ctk.CTkFrame(
        side,
        corner_radius=9,
        fg_color="#202634",
        border_width=1,
        border_color="#2B3342",
    )
    state_card.grid(row=3, column=0, sticky="ew", padx=20)
    state_card.grid_columnconfigure(1, weight=1)
    app._sys_dot = ctk.CTkLabel(
        state_card, text="●", font=app._font(14), text_color="#7B8498"
    )
    app._sys_dot.grid(row=0, column=0, padx=(14, 8), pady=(13, 3))
    app._sys_state_label = ctk.CTkLabel(
        state_card,
        text="就绪",
        anchor="w",
        font=app._font(15, "bold"),
        text_color="#F4F6FA",
    )
    app._sys_state_label.grid(row=0, column=1, sticky="w", pady=(13, 3))
    app._sys_state_desc = ctk.CTkLabel(
        state_card,
        text="等待启动",
        anchor="w",
        font=app._font(11),
        text_color="#8B93A6",
    )
    app._sys_state_desc.grid(row=1, column=0, columnspan=2, sticky="w", padx=14)
    app._clock_label = ctk.CTkLabel(
        state_card, text="", font=app._mono(11), text_color="#AEB4C2"
    )
    app._clock_label.grid(
        row=2, column=0, columnspan=2, sticky="e", padx=14, pady=(8, 13)
    )

    footer = ctk.CTkFrame(side, fg_color="transparent")
    footer.grid(row=5, column=0, sticky="sew", padx=14, pady=(8, 18))
    settings = ctk.CTkButton(
        footer,
        text="  ⚙   设置",
        command=lambda: show_page("settings"),
        height=44,
        anchor="w",
        corner_radius=8,
        fg_color="transparent",
        hover_color="#1C2230",
        text_color="#AAB0BE",
        font=app._font(13),
    )
    settings.pack(fill="x")
    app._nav_buttons["settings"] = settings
    ctk.CTkLabel(
        footer,
        text="ACT Launcher  ·  ROS 2 Jazzy",
        font=app._font(10),
        text_color="#646C7D",
    ).pack(anchor="w", padx=12, pady=(14, 0))


def _build_hero(app, parent):
    hero = ctk.CTkFrame(
        parent,
        height=292,
        corner_radius=12,
        fg_color="#111722",
        border_width=1,
        border_color="#262E3D",
    )
    hero.pack(fill="x", padx=2, pady=(0, 14))
    hero.pack_propagate(False)
    try:
        source = Image.open(LAUNCHER_ASSET_DIR / "hero_humanoid.png").convert("RGB")
        source = ImageOps.fit(
            source,
            (1800, 420),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        app._hero_image = ctk.CTkImage(
            light_image=source, dark_image=source, size=(1080, 286)
        )
        app._hero_label = ctk.CTkLabel(hero, image=app._hero_image, text="")
        app._hero_label.place(x=0, y=0, relwidth=1, relheight=1)

        def resize_hero(event):
            width = max(760, event.width)
            app._hero_image.configure(size=(width, max(178, int(width / 4.28))))

        hero.bind("<Configure>", resize_hero)
    except OSError:
        app._hero_image = None

    brand_row = ctk.CTkFrame(hero, fg_color="transparent")
    brand_row.place(relx=0.34, rely=0.15, anchor="w")
    embosen = _transparent_image(OCTOPUS_ICON_DIR / "embosenx-light.png", (142, 24))
    if embosen:
        app._embosen_logo = embosen
        ctk.CTkLabel(brand_row, image=embosen, text="").pack(side="left")
    ctk.CTkLabel(
        brand_row,
        text="  |  具感时代",
        font=app._font(15, "bold"),
        text_color="#FFFFFF",
    ).pack(side="left")

    ctk.CTkLabel(
        hero,
        text="感知万物 · 同步采集",
        font=app._font(31, "bold"),
        text_color="#F5F2FF",
    ).place(relx=0.34, rely=0.40, anchor="w")
    ctk.CTkLabel(
        hero,
        text="多模态传感数据一站式采集",
        font=app._font(14),
        text_color="#D3D7E2",
    ).place(relx=0.34, rely=0.64, anchor="w")
    return hero


def _device_metadata(config: dict, identity: dict) -> dict[str, str]:
    baton = config.get("baton_mini") or {}
    gopro = config.get("gopro") or {}
    pressure = identity.get("pressure") or {}
    mapped = sum(
        1
        for entry in pressure.values()
        if (entry.get("match") or {}).get("HWK_CHIP_UID")
    )
    cameras = sum(
        1 for entry in gopro.values() if entry.get("enabled", True)
    )
    return {
        "baton_mini.left": f"IP  {baton.get('left', {}).get('server_ip', '未配置')}",
        "baton_mini.right": f"IP  {baton.get('right', {}).get('server_ip', '未配置')}",
        "gopro": f"{cameras} 路相机 · /gopro_left · /gopro_right",
        "pressure": f"{mapped}/4 UID 已映射",
        "octopus": "本机 GUI · 独立进程监控",
    }


def _build_device_grid(app, parent, metadata: dict[str, str]) -> None:
    section = ctk.CTkFrame(
        parent,
        corner_radius=11,
        fg_color="#0E131B",
        border_width=1,
        border_color="#252D3A",
    )
    section.pack(fill="x", padx=2, pady=(0, 14))

    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=18, pady=(13, 8))
    ctk.CTkLabel(
        header,
        text="设备状态",
        font=app._font(17, "bold"),
        text_color="#F4F6FA",
    ).pack(side="left")
    ctk.CTkLabel(
        header,
        text="实时监控各设备连接状态",
        font=app._font(10),
        text_color="#687184",
    ).pack(side="left", padx=10)
    app._refresh_btn = ctk.CTkButton(
        header,
        text="↻  刷新",
        command=lambda: app._poll_sensor_status(force=True),
        width=88,
        height=32,
        fg_color="transparent",
        hover_color="#202735",
        text_color="#DCE0E8",
        border_width=0,
        font=app._font(13, "bold"),
    )
    app._refresh_btn.pack(side="right")

    grid = ctk.CTkFrame(section, fg_color="transparent")
    grid.pack(fill="x", padx=14, pady=(0, 14))
    for column in (0, 1):
        grid.grid_columnconfigure(column, weight=1, uniform="device")
    app._sensor_labels = {}
    app._device_images = {}
    image_map = {
        "baton_mini.left": ("device_baton.png", (46, 82)),
        "baton_mini.right": ("device_baton.png", (46, 82)),
        "gopro": ("device_camera.png", (78, 64)),
        "pressure": ("device_pressure.png", (78, 62)),
        "octopus": ("device_octopus_controller.png", (72, 82)),
    }
    definitions = [
        ("baton_mini.left", "Baton Mini（左）"),
        ("baton_mini.right", "Baton Mini（右）"),
        ("gopro", "GoPro"),
        ("pressure", "压力传感器"),
        ("octopus", "Octopus 上位机"),
    ]
    for index, (sensor_id, title) in enumerate(definitions):
        row, column = divmod(index, 2)
        card = ctk.CTkFrame(
            grid,
            height=112,
            corner_radius=9,
            fg_color="#111720",
            border_width=1,
            border_color="#303847",
        )
        card.grid(row=row, column=column, padx=6, pady=6, sticky="nsew")
        card.grid_propagate(False)
        card.grid_columnconfigure(1, weight=1)

        filename, image_size = image_map[sensor_id]
        image = _transparent_image(LAUNCHER_ASSET_DIR / filename, image_size)
        if image:
            app._device_images[sensor_id] = image
            ctk.CTkLabel(card, image=image, text="", width=90).grid(
                row=0, column=0, rowspan=3, padx=(10, 4), pady=8
            )

        ctk.CTkLabel(
            card,
            text=title,
            anchor="w",
            font=app._font(15, "bold"),
            text_color="#F3F5F9",
        ).grid(row=0, column=1, sticky="sw", pady=(15, 0))
        ctk.CTkLabel(
            card,
            text=metadata.get(sensor_id, "未配置"),
            anchor="w",
            font=app._font(11),
            text_color="#939BAD",
        ).grid(row=1, column=1, sticky="w", pady=(2, 1))
        status_label = ctk.CTkLabel(
            card,
            text="●  未知",
            width=78,
            height=24,
            corner_radius=12,
            fg_color="#202538",
            font=app._font(11),
            text_color="#868FAA",
        )
        status_label.grid(row=2, column=1, sticky="nw", pady=(2, 12))
        desc_label = ctk.CTkLabel(
            card,
            text="等待检测",
            anchor="e",
            font=app._font(10),
            text_color="#747D90",
        )
        desc_label.grid(row=2, column=2, sticky="se", padx=14, pady=(2, 13))
        app._sensor_labels[sensor_id] = (status_label, desc_label)


def _build_log_panel(app, parent) -> None:
    card = ctk.CTkFrame(
        parent,
        corner_radius=11,
        fg_color="#0E131B",
        border_width=1,
        border_color="#30384A",
    )
    card.pack(fill="both", expand=True, padx=2, pady=(0, 14))
    header = ctk.CTkFrame(card, fg_color="transparent")
    header.pack(fill="x", padx=16, pady=(11, 7))
    ctk.CTkLabel(
        header,
        text="系统日志",
        font=app._font(16, "bold"),
        text_color="#F2F4F8",
    ).pack(side="left")

    def clear_log():
        app._log_text.configure(state="normal")
        app._log_text.delete("1.0", "end")
        app._log_text.configure(state="disabled")

    def export_log():
        default_name = time.strftime("umi-launcher-%Y%m%d-%H%M%S.log")
        path = filedialog.asksaveasfilename(
            title="导出系统日志",
            initialfile=default_name,
            defaultextension=".log",
            filetypes=(("日志文件", "*.log"), ("文本文件", "*.txt")),
        )
        if not path:
            return
        try:
            content = app._log_text.get("1.0", "end-1c")
            Path(path).write_text(content, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("导出失败", str(exc))

    for text, command in (("⇩  导出日志", export_log), ("♲  清空日志", clear_log)):
        ctk.CTkButton(
            header,
            text=text,
            command=command,
            width=100,
            height=28,
            fg_color="transparent",
            hover_color="#202735",
            text_color="#D5D9E2",
            font=app._font(11),
        ).pack(side="right", padx=(6, 0))

    app._log_text = ctk.CTkTextbox(
        card,
        height=170,
        wrap="word",
        fg_color="#090D13",
        text_color="#C8CEDA",
        border_width=1,
        border_color="#222A38",
        corner_radius=7,
        font=app._mono(11),
    )
    app._log_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    app._log_text._textbox.tag_configure("INFO", foreground="#58A6FF")
    app._log_text._textbox.tag_configure("WARN", foreground="#F2B84B")
    app._log_text._textbox.tag_configure("ERROR", foreground="#FF647C")
    app._log_text._textbox.tag_configure("SUCCESS", foreground="#3AD99F")
    app._log_text.configure(state="disabled")


def _build_button_bar(app, parent):
    bar = ctk.CTkFrame(
        parent,
        corner_radius=10,
        fg_color="#0E131B",
        border_width=1,
        border_color="#29313F",
    )
    bar.pack(fill="x", padx=2, pady=(0, 4))
    for column in range(4):
        bar.grid_columnconfigure(column, weight=1, uniform="actions")

    app._btn_start = _button(
        bar,
        text="▶  启动系统\nStart System",
        command=app._start_system,
        font=app._font,
        fg="#5636D9",
        hover="#6748EA",
        border="#735AF1",
        bold=True,
    )
    app._btn_smoke = _button(
        bar,
        text="〽  冒烟测试\nSmoke Test",
        command=app._start_smoke_test,
        font=app._font,
    )
    app._btn_stop = _button(
        bar,
        text="■  停止系统\nStop System",
        command=app._stop_system,
        font=app._font,
        fg="#A72C3D",
        hover="#C0384D",
        border="#CC4056",
        bold=True,
    )
    app._btn_stop.configure(state="disabled")
    app._btn_exit = _button(
        bar,
        text="⇥  退出\nExit",
        command=app._on_exit,
        font=app._font,
    )
    for column, button in enumerate(
        (app._btn_start, app._btn_smoke, app._btn_stop, app._btn_exit)
    ):
        button.grid(row=0, column=column, sticky="ew", padx=7, pady=9)
    return bar


def _build_overview_page(app, parent, config, identity) -> None:
    holder = ctk.CTkFrame(parent, fg_color="#090D13", corner_radius=0)
    holder.grid(row=0, column=0, sticky="nsew")
    page = _FillHeightScrollableFrame(
        holder,
        fg_color="#090D13",
        corner_radius=0,
        scrollbar_button_color="#252D3B",
        scrollbar_button_hover_color="#343E50",
    )
    page.pack(fill="both", expand=True)
    app._pages["overview"] = holder
    app._overview_page = page
    app._hero_frame = _build_hero(app, page)
    _build_device_grid(app, page, _device_metadata(config, identity))
    _build_log_panel(app, page)
    app._action_bar = _build_button_bar(app, page)


def _detail_row(app, parent, title: str, value: str, row: int) -> None:
    ctk.CTkLabel(
        parent,
        text=title,
        width=175,
        anchor="nw",
        font=app._font(12, "bold"),
        text_color="#8F98AA",
    ).grid(row=row, column=0, sticky="nw", padx=(18, 12), pady=7)
    ctk.CTkLabel(
        parent,
        text=value,
        anchor="nw",
        justify="left",
        wraplength=760,
        font=app._font(12),
        text_color="#E4E7EE",
    ).grid(row=row, column=1, sticky="nw", padx=(0, 18), pady=7)


def _detail_card(app, parent, title: str, rows: list[tuple[str, str]]) -> None:
    card = ctk.CTkFrame(
        parent,
        corner_radius=10,
        fg_color="#111720",
        border_width=1,
        border_color="#2B3443",
    )
    card.pack(fill="x", pady=7)
    card.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(
        card,
        text=title,
        anchor="w",
        font=app._font(17, "bold"),
        text_color="#F4F6FA",
    ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(15, 8))
    for index, (label, value) in enumerate(rows, start=1):
        _detail_row(app, card, label, value, index)


def _build_sensors_page(app, parent, config, identity) -> None:
    holder = ctk.CTkFrame(parent, fg_color="#090D13", corner_radius=0)
    holder.grid(row=0, column=0, sticky="nsew")
    page = ctk.CTkScrollableFrame(
        holder,
        fg_color="#090D13",
        corner_radius=0,
        scrollbar_button_color="#252D3B",
    )
    page.pack(fill="both", expand=True)
    app._pages["sensors"] = holder
    ctk.CTkLabel(
        page,
        text="传感器详情",
        anchor="w",
        font=app._font(23, "bold"),
        text_color="#F5F6FA",
    ).pack(fill="x", pady=(8, 2))
    ctk.CTkLabel(
        page,
        text="以下信息直接读取当前 YAML 配置，不使用虚构序列号。",
        anchor="w",
        font=app._font(12),
        text_color="#858EA0",
    ).pack(fill="x", pady=(0, 12))

    baton = config.get("baton_mini") or {}
    for side, label in (("left", "Baton Mini（左）"), ("right", "Baton Mini（右）")):
        entry = baton.get(side) or {}
        topics = [
            str(value.get("name"))
            for value in (entry.get("topics") or {}).values()
            if isinstance(value, dict) and value.get("enabled") and value.get("name")
        ]
        _detail_card(
            app,
            page,
            label,
            [
                ("设备 IP", str(entry.get("server_ip", "未配置"))),
                ("ROS 节点", str(entry.get("node_name", "未配置"))),
                ("启用 topic", "\n".join(topics) or "无"),
            ],
        )

    gopro = config.get("gopro") or {}
    rows = []
    for side, label in (("left", "左"), ("right", "右")):
        entry = gopro.get(side) or {}
        namespace = entry.get("namespace", f"gopro_{side}")
        rows.extend(
            [
                (f"{label}路设备", str(entry.get("video_device", "未配置"))),
                (f"{label}路 topic", f"/{namespace}/image_raw"),
            ]
        )
    _detail_card(app, page, "GoPro 双路相机", rows)

    pressure_rows = []
    for key, entry in (identity.get("pressure") or {}).items():
        match = entry.get("match") or {}
        target = entry.get("target") or {}
        pressure_rows.append(
            (
                key,
                f"UID: {match.get('HWK_CHIP_UID', '未配置')}\n"
                f"{target.get('stable_name', '无稳定设备名')}\n"
                f"{target.get('topic', '无 topic')}",
            )
        )
    _detail_card(app, page, "压力传感器（4 路）", pressure_rows)
    _detail_card(
        app,
        page,
        "Octopus 上位机",
        [
            ("运行位置", "本机 GUI"),
            ("启动脚本", str(WORKSPACE_DIR / "start_octopus.sh")),
            ("状态来源", "独立进程存活监控"),
        ],
    )


def _build_settings_page(app, parent) -> None:
    holder = ctk.CTkFrame(parent, fg_color="#090D13", corner_radius=0)
    holder.grid(row=0, column=0, sticky="nsew")
    page = ctk.CTkScrollableFrame(
        holder,
        fg_color="#090D13",
        corner_radius=0,
        scrollbar_button_color="#252D3B",
    )
    page.pack(fill="both", expand=True)
    app._pages["settings"] = holder
    ctk.CTkLabel(
        page,
        text="系统设置",
        anchor="w",
        font=app._font(23, "bold"),
        text_color="#F5F6FA",
    ).pack(fill="x", pady=(8, 2))
    ctk.CTkLabel(
        page,
        text="本页只读展示运行环境；硬件身份修改仍在 YAML 中完成。",
        anchor="w",
        font=app._font(12),
        text_color="#858EA0",
    ).pack(fill="x", pady=(0, 14))
    _detail_card(
        app,
        page,
        "运行环境",
        [
            ("中文字体", app.FONT_FAMILY),
            ("ROS 发行版", os.environ.get("ROS_DISTRO", "jazzy")),
            ("ROS Discovery", os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE", "LOCALHOST")),
            ("Python", os.path.realpath(os.sys.executable)),
            ("Qt Root", os.environ.get("QT_ROOT", "未设置")),
            ("工作区", str(WORKSPACE_DIR)),
        ],
    )

    actions = ctk.CTkFrame(page, fg_color="transparent")
    actions.pack(fill="x", pady=10)
    _button(
        actions,
        text="打开传感器配置",
        command=lambda: _open_path(CONFIG_PATH),
        font=app._font,
        width=190,
    ).pack(side="left", padx=(0, 10))
    _button(
        actions,
        text="打开硬件身份映射",
        command=lambda: _open_path(IDENTITY_PATH),
        font=app._font,
        width=210,
    ).pack(side="left")


def build_launcher_ui(app) -> None:
    """在已有 ActLauncher 实例上构建新版界面。"""
    app.FONT_FAMILY = _detect_cjk_font(app)
    app.FONT_MONO = "DejaVu Sans Mono"
    app.configure(fg_color="#090D13")
    content_row = _configure_window(app)

    root = ctk.CTkFrame(app, corner_radius=0, fg_color="#090D13")
    root.grid(row=content_row, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    page_host = ctk.CTkFrame(root, corner_radius=0, fg_color="#090D13")
    page_host.grid(row=0, column=1, sticky="nsew", padx=(20, 16), pady=16)
    page_host.grid_rowconfigure(0, weight=1)
    page_host.grid_columnconfigure(0, weight=1)

    app._pages = {}

    def show_page(page_id: str):
        for current_id, frame in app._pages.items():
            if current_id == page_id:
                frame.grid()
            else:
                frame.grid_remove()
        for current_id, button in app._nav_buttons.items():
            active = current_id == page_id
            button.configure(
                fg_color="#4B2DD0" if active else "transparent",
                hover_color="#5B3CDF" if active else "#1C2230",
                text_color="#FFFFFF" if active else "#9299AA",
            )

    _build_sidebar(app, root, show_page)
    config = _load_yaml(CONFIG_PATH)
    identity = _load_yaml(IDENTITY_PATH)
    _build_overview_page(app, page_host, config, identity)
    _build_sensors_page(app, page_host, config, identity)
    _build_settings_page(app, page_host)
    show_page("overview")

    state_styles = {
        "ready": ("#7B8498", "就绪", "等待启动"),
        "starting": ("#F0B64A", "启动中", "正在检查设备与节点"),
        "running": ("#39D99F", "运行正常", "系统与上位机正在运行"),
        "warning": ("#F0B64A", "需要注意", "部分设备状态不完整"),
        "error": ("#FF647C", "启动失败", "请查看系统日志"),
        "stopping": ("#A98BFF", "正在停止", "正在安全关闭进程"),
    }

    def set_system_state(state: str, detail: str = ""):
        color, title, default_detail = state_styles.get(
            state, state_styles["ready"]
        )
        app._sys_dot.configure(text_color=color)
        app._sys_state_label.configure(text=title)
        app._sys_state_desc.configure(text=detail or default_detail)

    app._set_system_state = set_system_state
    app._show_page = show_page
    app._status_poll_inflight = False
    app._subdevice_status = {}
    app._tick_clock()
    app._append_log("INFO  系统初始化完成")
    app._append_log("INFO  配置文件已加载")
    app._append_log("INFO  等待启动命令")
