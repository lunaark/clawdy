"""平台检测、可选依赖加载、全屏窗口修复"""

import platform as _platform

IS_MACOS = _platform.system() == 'Darwin'
IS_WINDOWS = _platform.system() == 'Windows'

# ─── 可选依赖（托盘 & 快捷键）────────────────────────────────
# macOS 上 pystray 会因线程问题导致崩溃，pynput 需要辅助功能权限
_HAS_PYSTRAY = False
_HAS_PYNPUT = False
pystray = None
pynput_keyboard = None
Image = None
ImageDraw = None

if not IS_MACOS:
    try:
        import pystray as _pystray
        from PIL import Image as _Image, ImageDraw as _ImageDraw
        pystray = _pystray
        Image = _Image
        ImageDraw = _ImageDraw
        _HAS_PYSTRAY = True
    except ImportError:
        pass

    try:
        from pynput import keyboard as _pynput_keyboard
        pynput_keyboard = _pynput_keyboard
        _HAS_PYNPUT = True
    except ImportError:
        pass

# Windows 音乐播放：优先用 pygame
_HAS_PYGAME = False
pygame = None
if IS_WINDOWS:
    try:
        import pygame as _pygame
        _pygame.mixer.init()
        pygame = _pygame
        _HAS_PYGAME = True
    except (ImportError, Exception):
        pass


def setup_fullscreen_float(root, canvas_w, canvas_h):
    """macOS: 创建透明 NSPanel 作为宿主，把 tkinter 窗口挂为 child，
    使小螃蟹能在全屏应用上方显示、跨所有 Space 浮动。
    非 macOS 平台无需处理。"""
    if not IS_MACOS:
        return None

    try:
        from AppKit import NSApplication, NSPanel, NSColor, NSMakeRect
        from Cocoa import (
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorIgnoresCycle,
            NSWindowStyleMaskBorderless,
            NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            NSWindowAbove,
        )

        ns_app = NSApplication.sharedApplication()

        # 找到 tkinter 主窗口（通过尺寸匹配）
        tk_nswin = None
        for win in ns_app.windows():
            frame = win.frame()
            if int(frame.size.width) == canvas_w and int(frame.size.height) == canvas_h:
                tk_nswin = win
                break

        if tk_nswin is None:
            return None

        behavior = (
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | NSWindowCollectionBehaviorIgnoresCycle
        )

        # 创建透明 NSPanel
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            tk_nswin.frame(),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        panel.setCollectionBehavior_(behavior)
        panel.setFloatingPanel_(True)
        panel.setLevel_(25)
        panel.setCanHide_(False)
        panel.setHidesOnDeactivate_(False)
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setIgnoresMouseEvents_(True)
        panel.orderFrontRegardless()

        # panel 为父，tkinter 窗口为子（跟随进入全屏 Space）
        panel.addChildWindow_ordered_(tk_nswin, NSWindowAbove)

        # tkinter 窗口也设置跨 Space 属性
        tk_nswin.setCollectionBehavior_(behavior)
        tk_nswin.setCanHide_(False)
        tk_nswin.setHidesOnDeactivate_(False)

        return panel

    except ImportError:
        pass
    except Exception:
        pass
    return None
