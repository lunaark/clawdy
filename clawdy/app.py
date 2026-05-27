"""ClawdPet 主类"""

import tkinter as tk
import random

from .platform import IS_MACOS, IS_WINDOWS, setup_fullscreen_float
from .constants import (
    SCALE, FPS, INTERVAL, CANVAS_W, CANVAS_H,
    WIN_TRANSPARENT_COLOR, COLORS, I18N,
    STATE_DURATIONS, PX_BORDER,
)
from .renderer import PixelRenderer
from .particles import ParticleSystem
from .state_machine import StateMachine
from .checkin import CheckInTracker
from .animations import DRAW_MAP
from .music import MusicPlayer
from .hooks import start_hook_server
from .tray import TrayManager
from .dialogs import (
    show_checkin_dialog, show_progress_dialog,
    show_manage_plans_dialog,
)


class ClawdPet:
    def __init__(self):
        self.root = tk.Tk()
        try:
            self.root.tk.call('tk', 'appname', 'Clawdy')
        except Exception:
            pass
        self.root.title('Clawdy')
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', True)

        # ─── 跨平台透明窗口 ───
        if IS_MACOS:
            self.root.wm_attributes('-transparent', True)
            self.root.config(bg='systemTransparent')
            canvas_bg = 'systemTransparent'
        elif IS_WINDOWS:
            self.root.config(bg=WIN_TRANSPARENT_COLOR)
            self.root.wm_attributes('-transparentcolor', WIN_TRANSPARENT_COLOR)
            canvas_bg = WIN_TRANSPARENT_COLOR
        else:
            self.root.config(bg='black')
            canvas_bg = 'black'

        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_W, height=CANVAS_H,
            bg=canvas_bg,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.renderer = PixelRenderer(self.canvas)
        self.particles = ParticleSystem()
        self.sm = StateMachine()

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        init_x = self.screen_w - CANVAS_W - 100
        init_y = self.screen_h - CANVAS_H - 80
        self.root.geometry(f'{CANVAS_W}x{CANVAS_H}+{init_x}+{init_y}')

        # 全屏浮动修复（macOS NSPanel 方案）
        self._float_panel = None
        self.root.after(500, self._setup_float_panel)

        # 拖动
        self._drag_x = 0
        self._drag_y = 0
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self._music = MusicPlayer(self.root, self.menu)
        self.menu.add_command(label=I18N['play_music'], command=self._music.toggle)
        self.menu.add_command(label=I18N['next_track'], command=self._music.next_track)
        self.menu.add_separator()
        self.menu.add_command(label=I18N['firework'], command=self._trigger_firework)
        self.menu.add_separator()
        self._scene_menu_index = self.menu.index('end') + 1
        self.menu.add_command(label=I18N['go_beach'], command=self._toggle_scene)
        self._mode_menu_index = self.menu.index('end') + 1
        self.menu.add_command(label=I18N['mode_settle'], command=self._toggle_wander)
        self.menu.add_separator()
        self.menu.add_command(label=I18N['checkin'], command=lambda: show_checkin_dialog(self))
        self.menu.add_command(label=I18N['progress'], command=lambda: show_progress_dialog(self))
        self.menu.add_command(label=I18N['manage_plans'], command=lambda: show_manage_plans_dialog(self))
        self.menu.add_separator()
        self.menu.add_command(label=I18N['show_hide'], command=self.toggle_visibility)
        self.menu.add_separator()
        self.menu.add_command(label=I18N['quit'], command=self._quit)

        if IS_MACOS:
            self.canvas.bind('<ButtonPress-2>', self._show_menu)
            self.canvas.bind('<Control-ButtonPress-1>', self._show_menu)
        else:
            self.canvas.bind('<ButtonPress-3>', self._show_menu)

        self.cx = 11
        self.cy = 18

        self._wander_mode = True

        # 鼠标静止检测
        self._last_mouse_x = 0
        self._last_mouse_y = 0
        self._mouse_idle_frames = 0
        self._mouse_idle_threshold = FPS * 60 * 2
        self._is_looking_at_user = False

        # 久坐提醒
        self._work_frames = 0
        self._drink_reminder_interval = FPS * 60 * 45
        self._showing_drink_sign = False
        self._drink_sign_frames = 0
        self._drink_sign_duration = FPS * 12

        self._visible = True

        # 打卡系统
        self.tracker = CheckInTracker()
        self._show_progress_bar = True
        self._checkin_celebrate_frames = 0

        # 心情
        self._mood_update_interval = FPS * 60
        self._mood_update_counter = 0
        self._update_mood()

        # Claude Code 联动
        self._claude_linked = False
        self._boot_frame = 0
        start_hook_server(self)

        # 系统托盘 + 全局快捷键
        self._tray = TrayManager(self)
        self._tray.start_tray()
        self._tray.start_hotkey()

    # ─── 全屏浮动 ─────────────────────────────────────────────

    def _setup_float_panel(self):
        self._float_panel = setup_fullscreen_float(self.root, CANVAS_W, CANVAS_H)

    def _sync_panel(self):
        """同步 NSPanel 位置到 tkinter 窗口当前位置"""
        if not self._float_panel:
            return
        try:
            from AppKit import NSMakeRect
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            screen_h = self.root.winfo_screenheight()
            cocoa_y = screen_h - y - CANVAS_H
            self._float_panel.setFrame_display_(
                NSMakeRect(x, cocoa_y, CANVAS_W, CANVAS_H), False
            )
        except Exception:
            pass


    # ─── 显示/隐藏 ────────────────────────────────────────────

    def toggle_visibility(self):
        if self._visible:
            self._hide()
        else:
            self._show()

    def _hide(self):
        if self._visible:
            self.root.withdraw()
            if self._float_panel:
                self._float_panel.orderOut_(None)
            self._visible = False

    def _show(self):
        if not self._visible:
            self.root.deiconify()
            self.root.wm_attributes('-topmost', True)
            if self._float_panel:
                self._float_panel.orderFrontRegardless()
            self._visible = True

    # ─── 事件处理 ─────────────────────────────────────────────

    def _on_press(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
        self.sm.pause()

    def _on_drag(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        # 先移动 panel（父窗口），child 会自动跟随
        if self._float_panel:
            try:
                from AppKit import NSMakeRect
                screen_h = self.root.winfo_screenheight()
                cocoa_y = screen_h - y - CANVAS_H
                self._float_panel.setFrameOrigin_(
                    __import__('AppKit').NSMakePoint(x, cocoa_y)
                )
            except Exception:
                pass
        else:
            self.root.geometry(f'+{x}+{y}')

    def _on_release(self, event):
        self.sm.resume()

    def _show_menu(self, event):
        self.sm.pause()
        self.menu.tk_popup(event.x_root, event.y_root)
        self.sm.resume()

    def _get_mouse_eye_offset(self, ox, oy):
        win_x = self.root.winfo_x()
        win_y = self.root.winfo_y()
        eye_center_x = win_x + (ox + 7) * SCALE
        eye_center_y = win_y + (oy + 1) * SCALE
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        diff_x = mouse_x - eye_center_x
        diff_y = mouse_y - eye_center_y
        threshold = 40
        dx = 1 if diff_x > threshold else (-1 if diff_x < -threshold else 0)
        dy = 1 if diff_y > threshold else (-1 if diff_y < -threshold else 0)
        return (dx, dy)

    def _move_window(self, dx, dy):
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        x = max(0, min(x, self.screen_w - CANVAS_W))
        y = max(0, min(y, self.screen_h - CANVAS_H))
        if self._float_panel:
            try:
                screen_h = self.root.winfo_screenheight()
                cocoa_y = screen_h - y - CANVAS_H
                self._float_panel.setFrameOrigin_(
                    __import__('AppKit').NSMakePoint(x, cocoa_y)
                )
            except Exception:
                self.root.geometry(f'+{x}+{y}')
        else:
            self.root.geometry(f'+{x}+{y}')

    def _toggle_scene(self):
        if self.renderer.scene == 'home':
            self.renderer.set_scene('beach')
            self.menu.entryconfigure(self._scene_menu_index, label=I18N['go_home'])
        else:
            self.renderer.set_scene('home')
            self.menu.entryconfigure(self._scene_menu_index, label=I18N['go_beach'])
        self.cx = 11

    def _toggle_wander(self):
        self._wander_mode = not self._wander_mode
        if self._wander_mode:
            self.menu.entryconfigure(self._mode_menu_index, label=I18N['mode_settle'])
            self.sm.excluded_states.discard('walk_left')
            self.sm.excluded_states.discard('walk_right')
            self.sm.force_state(random.choice(['walk_left', 'walk_right']))
        else:
            self.menu.entryconfigure(self._mode_menu_index, label=I18N['mode_wander'])
            self.sm.excluded_states.update({'walk_left', 'walk_right'})
            if self.sm.state in ('walk_left', 'walk_right'):
                self.sm.force_state('idle')

    def _trigger_firework(self):
        self.sm.state = 'firework'
        self.sm.frame = 0
        self.sm.timer = 0.0
        self.sm.duration = random.uniform(*STATE_DURATIONS['firework'])
        self.particles.clear()

    def _quit(self):
        self._music.stop()
        self._tray.stop_tray()
        self._tray.stop_hotkey()
        self.root.destroy()

    # ─── 心情 & 感知 ─────────────────────────────────────────

    def _update_mood(self):
        if not self.tracker.has_plan():
            self.sm.mood = 0.0
            return
        streak = self.tracker.streak
        days = self.tracker.days_since_last
        progress = self.tracker.progress
        mood = 0.0
        if streak >= 7:
            mood += 0.6
        elif streak >= 3:
            mood += 0.3
        elif streak >= 1:
            mood += 0.1
        if progress >= 0.75:
            mood += 0.3
        elif progress >= 0.5:
            mood += 0.15
        if days > 7:
            mood -= 0.6
        elif days > 3:
            mood -= 0.3
        elif days > 1:
            mood -= 0.1
        self.sm.mood = max(-1.0, min(1.0, mood))

    def _update_awareness(self):
        try:
            mx = self.root.winfo_pointerx()
            my = self.root.winfo_pointery()
        except tk.TclError:
            return

        if mx != self._last_mouse_x or my != self._last_mouse_y:
            self._last_mouse_x = mx
            self._last_mouse_y = my
            self._mouse_idle_frames = 0
            self._is_looking_at_user = False
        else:
            self._mouse_idle_frames += 1
            if self._mouse_idle_frames >= self._mouse_idle_threshold:
                self._is_looking_at_user = True

        self._mood_update_counter += 1
        if self._mood_update_counter >= self._mood_update_interval:
            self._mood_update_counter = 0
            self._update_mood()

        self._work_frames += 1
        if self._showing_drink_sign:
            self._drink_sign_frames += 1
            if self._drink_sign_frames >= self._drink_sign_duration:
                self._showing_drink_sign = False
                self._drink_sign_frames = 0
        elif self._work_frames >= self._drink_reminder_interval:
            self._showing_drink_sign = True
            self._drink_sign_frames = 0
            self._work_frames = 0

    # ─── 主循环 ───────────────────────────────────────────────

    def _game_loop(self):
        self.renderer.clear()
        self.renderer.draw_background(self.sm.frame)
        self.sm.update(1.0 / FPS)
        self._update_awareness()
        if self._boot_frame < FPS * 3:
            self._boot_frame += 1

        state = self.sm.state
        f = self.sm.frame

        draw_fn = DRAW_MAP.get(state)
        if draw_fn:
            draw_fn(self, f)

        if self._is_looking_at_user and state == 'idle':
            ox, oy = self.cx, self.cy
            if (f // 20) % 3 != 0:
                self.renderer.px(ox + 15, oy - 1, COLORS['zzz'])

        if self._showing_drink_sign:
            ox, oy = self.cx, self.cy
            self.renderer.draw_sign(ox + 1, oy - 6, I18N['drink_water'])

        if self._show_progress_bar and self.tracker.total > 0:
            ox, oy = self.cx, self.cy
            self.renderer.draw_progress_bar(
                ox - 1, oy + 10,
                self.tracker.progress,
                self.tracker.done,
                self.tracker.total,
                frame=f,
            )

        if self._checkin_celebrate_frames > 0:
            self._checkin_celebrate_frames -= 1

        self.particles.update()
        self.particles.draw(self.renderer)

        if self._music.playing:
            self.renderer.draw_music_notes(self.cx, self.cy, f)

        self.root.after(INTERVAL, self._game_loop)

    def run(self):
        self.root.after(100, self._game_loop)
        self.root.mainloop()
