#!/usr/bin/env python3
"""Clawdy Desktop Pet — macOS / Windows 跨平台桌面像素风小螃蟹"""

import tkinter as tk
import random
import math
import subprocess
import os
import sys
import glob
import threading
import json
import locale
import platform
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── 平台检测 ─────────────────────────────────────────────────
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'

# ─── 可选依赖（托盘 & 快捷键）────────────────────────────────
# macOS 上 pystray 会因线程问题导致崩溃，pynput 需要辅助功能权限
# 所以这两个库只在非 macOS 平台启用
_HAS_PYSTRAY = False
_HAS_PYNPUT = False

if not IS_MACOS:
    try:
        import pystray
        from PIL import Image, ImageDraw
        _HAS_PYSTRAY = True
    except ImportError:
        pass

    try:
        from pynput import keyboard as pynput_keyboard
        _HAS_PYNPUT = True
    except ImportError:
        pass

# Windows 音乐播放：优先用 pygame，否则用 winsound（仅 wav）
_HAS_PYGAME = False
if IS_WINDOWS:
    try:
        import pygame
        pygame.mixer.init()
        _HAS_PYGAME = True
    except (ImportError, Exception):
        pass

# ─── 国际化 ───────────────────────────────────────────────────
def _is_chinese():
    # macOS LaunchAgent 环境下 locale 可能是 'C'，改用系统语言检测
    if IS_MACOS:
        try:
            import subprocess as _sp
            out = _sp.check_output(
                ['defaults', 'read', '-g', 'AppleLanguages'],
                stderr=_sp.DEVNULL, timeout=2,
            ).decode()
            return 'zh' in out.split(')')[0]  # 只看第一优先语言
        except Exception:
            pass
    try:
        lang = locale.getlocale()[0] or ''
    except Exception:
        lang = ''
    return lang.startswith('zh')

_ZH = _is_chinese()

I18N = {
    'play_music':  '🎵 播放音乐' if _ZH else '🎵 Play Music',
    'stop_music':  '⏹ 停止音乐' if _ZH else '⏹ Stop Music',
    'next_track':  '⏭ 下一首'   if _ZH else '⏭ Next Track',
    'firework':    '🎆 放烟花'   if _ZH else '🎆 Fireworks',
    'show_hide':   '显示/隐藏'   if _ZH else 'Show/Hide',
    'quit':        '退出'        if _ZH else 'Quit',
    'drink_water': '喝水'        if _ZH else 'Water!',
    'checkin':      '✅ 打卡'       if _ZH else '✅ Check In',
    'progress':     '📊 查看进度'   if _ZH else '📊 Progress',
    'manage_plans': '📋 管理计划'   if _ZH else '📋 Plans',
    'go_beach':     '🏖 去沙滩'    if _ZH else '🏖 Beach',
    'go_home':      '🏠 回家'      if _ZH else '🏠 Home',
    'mode_settle':  '📍 定居'      if _ZH else '📍 Settle',
    'mode_wander':  '🚶 游走'      if _ZH else '🚶 Wander',
}

# ─── 常量 ─────────────────────────────────────────────────────
SCALE = 6          # 每个逻辑像素 = 6×6 屏幕像素
FPS = 15
INTERVAL = 1000 // FPS  # ms

# Windows 透明背景色（用一个不可能出现在像素画里的颜色做 transparent color key）
WIN_TRANSPARENT_COLOR = '#010101'

COLORS = {
    'body':    '#E07A5F',
    'eye':     '#000000',
    'white':   '#FFFFFF',
    'blush':   '#FAC8D8',
    'zzz':     '#888888',
    'heart':   '#F06090',
    'sweat':   '#88BBDD',
    'cookie':  '#C4883A',
    'cookie2': '#A06820',
    'crumb':   '#D4A050',
    'star':    '#FFD700',
    'star2':   '#FFA500',
    'screen':  '#5BC0AA',
    'screen2': '#3A9A7E',
    'happy_eye': '#333333',
    'note':    '#9B59B6',
    'note2':   '#E74C3C',
    # 烟花颜色
    'fw_red':    '#FF4444',
    'fw_gold':   '#FFD700',
    'fw_pink':   '#FF69B4',
    'fw_cyan':   '#00E5FF',
    'fw_green':  '#66FF66',
    'fw_orange': '#FFA500',
    'fw_fuse':   '#AA8855',
    'fw_spark':  '#FFEE88',
    # 沙滩背景
    'sand_base':  '#E8D5A3',
    'sand_dark':  '#D4BC7C',
    'sand_wet':   '#C4A86A',
    'sea_light':  '#5BA4CF',
    'sea_mid':    '#3A7CA5',
    'sea_deep':   '#2E5A7E',
    'sea_foam':   '#C8E6F0',
    'sky_gold':   '#FFB347',
    'sky_warm':   '#F0936E',
    'sky_pink':   '#D4637A',
    'sky_purple': '#6B4C9A',
    'sun_core':   '#FFD700',
    'sun_glow':   '#FFA500',
}

# ─── 像素风对话框样式 ────────────────────────────────────────
# 主色调：奶油米色底 + Clawd 橙 + 深棕边框，像老 GBA 菜单框
PX_BG          = '#F5E9D4'   # 奶油米色主背景
PX_BG_SOFT     = '#EADCC0'   # 分隔条/卡片底色
PX_BORDER      = '#5A3A2A'   # 深棕外边框
PX_BORDER_SOFT = '#A07050'   # 输入框边框（较浅）
PX_ACCENT      = '#E07A5F'   # Clawd 身体橙（标题/主按钮）
PX_ACCENT_DARK = '#C0604A'   # hover
PX_TEXT        = '#3A2418'   # 深棕文字
PX_TEXT_SOFT   = '#7A5A44'   # 次级文字
PX_INPUT_BG    = '#FFF8E7'   # 输入框底
PX_DANGER      = '#C94A3A'   # 删除红
PX_SUCCESS     = '#6BAE5F'   # 完成绿
PX_GOLD        = '#D4A94B'   # 奖励金
_PX_FAMILY = 'Menlo' if IS_MACOS else 'Consolas'
PX_FONT        = (_PX_FAMILY, 11)
PX_FONT_B      = (_PX_FAMILY, 11, 'bold')
PX_FONT_TITLE  = (_PX_FAMILY, 14, 'bold')
PX_FONT_BIG    = (_PX_FAMILY, 22, 'bold')


def _pixel_frame(parent, bg=PX_BG):
    """创建带像素风粗边框的容器：外层深棕 2px → 内层浅棕 2px → 内容区 bg"""
    outer = tk.Frame(parent, bg=PX_BORDER, bd=0)
    mid = tk.Frame(outer, bg=PX_BORDER_SOFT, bd=0)
    mid.pack(padx=2, pady=2, fill='both', expand=True)
    inner = tk.Frame(mid, bg=bg, bd=0)
    inner.pack(padx=2, pady=2, fill='both', expand=True)
    return outer, inner


def _pixel_entry(parent, var, width=None):
    """像素风输入框：浅底 + 深棕边"""
    wrap = tk.Frame(parent, bg=PX_BORDER_SOFT)
    entry = tk.Entry(
        wrap, textvariable=var, font=PX_FONT,
        bg=PX_INPUT_BG, fg=PX_TEXT,
        insertbackground=PX_TEXT,
        relief='flat', bd=0, highlightthickness=0,
    )
    if width:
        entry.config(width=width)
    entry.pack(padx=2, pady=2, fill='x', ipady=4)
    return wrap, entry


def _pixel_button(parent, text, command, primary=False, danger=False):
    """像素风按钮：方块 + 深色边框。用 Label 模拟以绕开 macOS tk.Button 主题限制。"""
    if danger:
        fg, bg, border, hover = '#FFFFFF', PX_DANGER, PX_BORDER, '#A63A2A'
    elif primary:
        fg, bg, border, hover = '#FFFFFF', PX_ACCENT, PX_BORDER, PX_ACCENT_DARK
    else:
        fg, bg, border, hover = PX_TEXT, PX_BG_SOFT, PX_BORDER_SOFT, PX_BG
    wrap = tk.Frame(parent, bg=border)
    btn = tk.Label(
        wrap, text=text, font=PX_FONT_B, fg=fg, bg=bg,
        padx=12, pady=4, cursor='hand2',
    )
    btn.pack(padx=2, pady=2)
    btn.bind('<ButtonRelease-1>',
             lambda e: command() if 0 <= e.x <= btn.winfo_width()
             and 0 <= e.y <= btn.winfo_height() else None)
    btn.bind('<Enter>', lambda e: btn.config(bg=hover))
    btn.bind('<Leave>', lambda e: btn.config(bg=bg))
    return wrap


def _bind_drag(dialog, handle):
    """让 handle 控件成为 dialog 的拖动把手"""
    drag = {'x': 0, 'y': 0}
    def on_press(e):
        drag['x'] = e.x_root - dialog.winfo_x()
        drag['y'] = e.y_root - dialog.winfo_y()
    def on_drag(e):
        dialog.geometry(f'+{e.x_root - drag["x"]}+{e.y_root - drag["y"]}')
    handle.bind('<ButtonPress-1>', on_press)
    handle.bind('<B1-Motion>', on_drag)


# 音乐文件夹
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music')


# Claude Code 联动 HTTP 端口
HOOK_PORT = 18900

# Claude Code 联动状态（优先级高于随机状态）
CLAUDE_STATE_MAP = {
    'prompt':    'thinking',    # 用户发 prompt → 思考
    'tool':      'working',     # 执行工具 → 打字工作
    'error':     'error',       # 出错 → 冒烟
    'done':      'celebrate',   # 完成 → 开心庆祝
    'idle':      None,          # 恢复随机状态
}

# Clawd 身体 14×8（1=身体像素, 0=透明）
BODY = [
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],  # row 0
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],  # row 1  ← 眼睛在这行
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0],  # row 2  ← 钳子
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0],  # row 3  ← 钳子
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],  # row 4
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],  # row 5
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],  # row 6  ← 腿
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],  # row 7  ← 腿
]

# 缩成一团的身体（睡觉用）
BODY_CURLED = [
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
]

EYE_L = (4, 1)
EYE_R = (9, 1)

LEGS_A = [
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],
]
LEGS_B = [
    [0,0,0,0,1,0,1,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,1,0,1,0,0,0,0],
]

CLAW_UP_RIGHT = {(13, 1): 1, (12, 0): 1}
CLAW_UP_LEFT  = {(0, 1): 1, (1, 0): 1}
CLAW_BOTH_UP  = {(13, 1): 1, (12, 0): 1, (0, 1): 1, (1, 0): 1}

COOKIE = [
    [0,1,1,0],
    [1,1,1,1],
    [1,1,1,1],
    [0,1,1,0],
]

STATE_DURATIONS = {
    'idle':       (3, 6),
    'walk_left':  (3, 5),
    'walk_right': (3, 5),
    'dance':      (4, 7),
    'sleep':      (5, 8),
    'wave':       (3, 5),
    'jump':       (3, 4),
    'working':    (4, 7),
    'happy':      (4, 6),
    'eating':     (5, 8),
    'excited':    (3, 5),
    'firework':   (5, 7),
    'thinking':   (3, 10),   # Claude Code: 思考中
    'cc_working': (3, 10),   # Claude Code: 执行工具
    'error':      (3, 5),    # Claude Code: 出错
    'celebrate':  (3, 5),    # Claude Code: 完成
}

# 随机切换只用这些状态（不包含 Claude Code 联动状态）
RANDOM_STATES = [
    'idle', 'walk_left', 'walk_right', 'dance', 'sleep',
    'wave', 'jump', 'working', 'happy', 'eating', 'excited', 'firework',
]
STATES = list(STATE_DURATIONS.keys())

# 画布加大给烟花留空间
CANVAS_W = 36 * SCALE
CANVAS_H = 30 * SCALE


# ─── 缓动函数 ────────────────────────────────────────────────
def ease_out(t):
    """缓出：快→慢"""
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    """缓入缓出"""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2

def lerp(a, b, t):
    """线性插值"""
    return a + (b - a) * t


# ─── 粒子系统 ────────────────────────────────────────────────
class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'decay', 'color', 'gravity')

    def __init__(self, x, y, vx, vy, color, life=1.0, decay=0.02, gravity=0.04):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.decay = decay
        self.gravity = gravity


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def clear(self):
        self.particles.clear()

    def emit(self, x, y, color, count=1,
             speed=0.8, spread=1.0, gravity=0.04,
             life=1.0, decay=0.02, angle_range=None):
        for _ in range(count):
            if angle_range:
                angle = random.uniform(angle_range[0], angle_range[1])
                spd = random.uniform(speed * 0.5, speed)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
            else:
                vx = (random.random() - 0.5) * spread
                vy = -random.random() * speed - 0.2
            c = color if isinstance(color, str) else random.choice(color)
            self.particles.append(
                Particle(x, y, vx, vy, c, life, decay, gravity)
            )

    def emit_burst(self, x, y, colors, count=20, speed=1.5, gravity=0.05, decay=0.025):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            c = random.choice(colors)
            self.particles.append(
                Particle(x, y, vx, vy, c, life=1.0, decay=decay, gravity=gravity)
            )

    def emit_claude_logo(self, cx, cy, colors, speed=2.0, gravity=0.02, decay=0.015):
        angles = [
            -math.pi/2, math.pi/2, math.pi, 0,
            -math.pi/4, -3*math.pi/4, math.pi/4, 3*math.pi/4,
        ]
        for angle in angles:
            for i in range(6):
                spd = speed * (1.0 - i * 0.12) + random.uniform(-0.1, 0.1)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
                c = random.choice(colors)
                self.particles.append(
                    Particle(cx, cy, vx, vy, c, life=1.2, decay=decay, gravity=gravity)
                )
            for _ in range(2):
                a = angle + random.uniform(-0.2, 0.2)
                spd = speed * random.uniform(0.3, 0.7)
                vx = math.cos(a) * spd
                vy = math.sin(a) * spd
                c = random.choice(colors)
                self.particles.append(
                    Particle(cx, cy, vx, vy, c, life=0.8, decay=0.025, gravity=gravity)
                )

    def update(self):
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravity
            p.life -= p.decay
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, renderer):
        for p in self.particles:
            if p.life > 0.15:
                renderer.px(round(p.x), round(p.y), p.color)


# ─── 沙滩背景数据 ────────────────────────────────────────────
# 画布 36×30 逻辑像素，预计算每行颜色
# 行 0-17: 天空渐变  |  行 18-21: 海面  |  行 22-29: 沙滩
def _build_sky_gradient():
    """预计算天空渐变色（18 行）"""
    rows = []
    # 紫 → 粉 → 暖橙 → 金
    stops = [
        (0.00, (107, 76, 154)),   # 紫
        (0.30, (212, 99, 122)),   # 粉
        (0.60, (240, 147, 110)),  # 暖橙
        (1.00, (255, 179, 71)),   # 金
    ]
    for y in range(18):
        t = y / 17
        # 找到区间
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                m = (t - t0) / (t1 - t0)
                r = int(c0[0] + (c1[0] - c0[0]) * m)
                g = int(c0[1] + (c1[1] - c0[1]) * m)
                b = int(c0[2] + (c1[2] - c0[2]) * m)
                rows.append(f'#{r:02x}{g:02x}{b:02x}')
                break
    return rows

SKY_ROWS = _build_sky_gradient()

# 沙滩行颜色模式（预计算，避免每帧重算）
SAND_PATTERN = []
for _y in range(8):  # row 22-29
    row_colors = []
    for _x in range(36):
        pat = ((_x * 7 + _y * 13) % 11)
        if _y == 0:
            row_colors.append(COLORS['sand_wet'])
        elif pat < 1:
            row_colors.append(COLORS['sand_dark'])
        else:
            row_colors.append(COLORS['sand_base'])
    SAND_PATTERN.append(row_colors)


# ─── 像素渲染器 ───────────────────────────────────────────────
class PixelRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.S = SCALE
        self._bg_drawn = False     # 静态背景是否已绘制
        self.scene = 'home'        # 'home'（透明）或 'beach'（沙滩）

    def clear(self):
        self.canvas.delete('sprite')

    def set_scene(self, scene):
        """切换场景。'home' 清空背景，'beach' 下次 draw_background 会重绘。"""
        if scene == self.scene:
            return
        self.scene = scene
        self.canvas.delete('bg')
        self.canvas.delete('sea')
        self._bg_drawn = False

    def draw_background(self, frame):
        """绘制沙滩日落背景。静态部分（天空+沙滩）只画一次，动态部分（海浪）每帧更新。"""
        # home 场景：透明桌面，不画任何背景
        if self.scene != 'beach':
            return
        # 静态背景只画一次（tag='bg' 不会被 clear 删除）
        if not self._bg_drawn:
            s = self.S
            # 天空（18 行）
            for y, color in enumerate(SKY_ROWS):
                self.canvas.create_rectangle(
                    0, y * s, 36 * s, (y + 1) * s,
                    fill=color, outline='', tags='bg',
                )
            # 沙滩（8 行，row 22-29）
            for dy, row_colors in enumerate(SAND_PATTERN):
                y = 22 + dy
                for x, color in enumerate(row_colors):
                    self.canvas.create_rectangle(
                        x * s, y * s, (x + 1) * s, (y + 1) * s,
                        fill=color, outline='', tags='bg',
                    )
            # 太阳（固定在天��中）
            sun_cx, sun_cy = 8, 14
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    self.canvas.create_rectangle(
                        (sun_cx + dx) * s, (sun_cy + dy) * s,
                        (sun_cx + dx + 1) * s, (sun_cy + dy + 1) * s,
                        fill=COLORS['sun_core'], outline='', tags='bg',
                    )
            # 太阳光晕
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                self.canvas.create_rectangle(
                    (sun_cx + dx) * s, (sun_cy + dy) * s,
                    (sun_cx + dx + 1) * s, (sun_cy + dy + 1) * s,
                    fill=COLORS['sun_glow'], outline='', tags='bg',
                )
            self._bg_drawn = True

        # 动态部分：海面（4 行，row 18-21）每帧重绘
        self.canvas.delete('sea')
        s = self.S
        sea_colors = [COLORS['sea_foam'], COLORS['sea_light'], COLORS['sea_mid'], COLORS['sea_deep']]
        for dy in range(4):
            y = 18 + dy
            base_color = sea_colors[dy]
            for x in range(36):
                # 海浪：用 sin 波纹制造泡沫效果
                wave = math.sin(frame * 0.1 + x * 0.7)
                if dy == 0 and wave > 0.3:
                    color = COLORS['sea_foam']
                elif dy <= 1 and wave > 0.6:
                    color = COLORS['sea_foam']
                else:
                    color = base_color
                # 太阳倒影
                if dy >= 1 and abs(x - 8) <= 1:
                    shimmer = math.sin(frame * 0.15 + y * 2)
                    if shimmer > 0.4:
                        color = COLORS['sky_gold']
                self.canvas.create_rectangle(
                    x * s, y * s, (x + 1) * s, (y + 1) * s,
                    fill=color, outline='', tags='sea',
                )

    def px(self, x, y, color, tag='sprite'):
        s = self.S
        self.canvas.create_rectangle(
            x * s, y * s, (x + 1) * s, (y + 1) * s,
            fill=color, outline='', tags=tag
        )

    def draw_body(self, ox, oy, legs=None, claw_extra=None, squash=False, curled=False):
        if curled:
            for r, row in enumerate(BODY_CURLED):
                for c, val in enumerate(row):
                    if val:
                        self.px(ox + c, oy + r, COLORS['body'])
            return
        rows = BODY[:6] if not squash else BODY[1:6]
        start_y = 0 if not squash else 1
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                if val:
                    self.px(ox + c, oy + r + start_y, COLORS['body'])
        leg_data = legs if legs else BODY[6:8]
        leg_offset = len(rows) + start_y
        for r, row in enumerate(leg_data):
            for c, val in enumerate(row):
                if val:
                    self.px(ox + c, oy + leg_offset + r, COLORS['body'])
        if claw_extra:
            for (cx, cy), val in claw_extra.items():
                if val:
                    self.px(ox + cx, oy + cy, COLORS['body'])

    def draw_eyes(self, ox, oy, variant='forward'):
        if variant == 'blink':
            return
        if variant == 'happy':
            self.px(ox + EYE_L[0], oy + EYE_L[1] + 1, COLORS['eye'])
            self.px(ox + EYE_R[0], oy + EYE_R[1] + 1, COLORS['eye'])
            return
        if isinstance(variant, tuple):
            dx, dy = variant
        else:
            offsets = {
                'forward':  (0, 0),
                'left':     (-1, 0),
                'right':    (1, 0),
                'down':     (0, 1),
                'up':       (0, -1),
            }
            dx, dy = offsets.get(variant, (0, 0))
        self.px(ox + EYE_L[0] + dx, oy + EYE_L[1] + dy, COLORS['eye'])
        self.px(ox + EYE_R[0] + dx, oy + EYE_R[1] + dy, COLORS['eye'])

    def draw_blush(self, ox, oy):
        self.px(ox + 3, oy + 2, COLORS['blush'])
        self.px(ox + 10, oy + 2, COLORS['blush'])

    def draw_zzz(self, ox, oy, frame):
        col = COLORS['zzz']
        z1_y = oy - 2 - (frame % 30) // 6
        z2_y = oy - 3 - ((frame + 15) % 30) // 6
        if z1_y > oy - 6:
            self.px(ox + 14, z1_y, col)
            self.px(ox + 15, z1_y - 1, col)
        if z2_y > oy - 7:
            self.px(ox + 16, z2_y, col)

    def draw_heart(self, hx, hy):
        heart = [[1,0,1],[1,1,1],[0,1,0]]
        for r, row in enumerate(heart):
            for c, val in enumerate(row):
                if val:
                    self.px(hx + c, hy + r, COLORS['heart'])

    def draw_sparkle(self, sx, sy, color=None):
        self.px(sx, sy, color or COLORS['white'])

    def draw_sweat(self, ox, oy, frame):
        drop_y = oy + (frame % 15) // 3
        if drop_y < oy + 4:
            self.px(ox + 13, drop_y, COLORS['sweat'])
            if drop_y > oy:
                self.px(ox + 13, drop_y - 1, COLORS['sweat'])

    def draw_cookie(self, cx, cy, bites=0):
        for r, row in enumerate(COOKIE):
            for c, val in enumerate(row):
                if val:
                    if bites >= 1 and r == 0 and c >= 2:
                        continue
                    if bites >= 2 and r == 1 and c >= 3:
                        continue
                    if bites >= 3 and r <= 1:
                        continue
                    col = COLORS['cookie'] if (r + c) % 3 != 0 else COLORS['cookie2']
                    self.px(cx + c, cy + r, col)

    def draw_crumbs(self, ox, oy, frame):
        col = COLORS['crumb']
        for i in range(3):
            cx = ox + 3 + i * 3 + round(math.sin(frame * 0.3 + i) * 1)
            cy = oy + 7 + (frame % 20) // 5 + i
            if cy < oy + 10:
                self.px(cx, cy, col)

    def draw_screen(self, sx, sy, frame):
        for x in range(6):
            self.px(sx + x, sy, COLORS['happy_eye'])
            self.px(sx + x, sy + 4, COLORS['happy_eye'])
        for y in range(5):
            self.px(sx, sy + y, COLORS['happy_eye'])
            self.px(sx + 5, sy + y, COLORS['happy_eye'])
        line_offset = (frame // 8) % 3
        for y in range(1, 4):
            width = 2 + ((y + line_offset) % 3)
            for x in range(1, 1 + width):
                self.px(sx + x, sy + y, COLORS['screen'] if (y + frame // 4) % 2 == 0 else COLORS['screen2'])

    def draw_music_notes(self, ox, oy, frame):
        notes = [
            (ox + 2,  COLORS['note']),
            (ox + 8,  COLORS['note2']),
            (ox + 14, COLORS['note']),
        ]
        for i, (nx, col) in enumerate(notes):
            phase = frame * 0.12 + i * 2.0
            ny = oy - 3 - round(math.sin(phase) * 2)
            self.px(nx, ny, col)
            self.px(nx, ny - 1, col)
            self.px(nx - 1, ny, col)

    def draw_float_hearts(self, ox, oy, frame, count=3):
        for i in range(count):
            phase = frame * 0.1 + i * 2.1
            hx = ox + 2 + round(math.sin(phase) * 3) + i * 4
            hy = oy - 3 - (frame % 30 + i * 5) // 6
            if hy > oy - 7:
                self.draw_heart(hx, hy)

    def draw_firework_stick(self, fx, fy):
        self.px(fx, fy, COLORS['fw_fuse'])
        self.px(fx, fy + 1, COLORS['fw_fuse'])
        self.px(fx, fy + 2, COLORS['fw_fuse'])
        self.px(fx, fy + 3, COLORS['fw_fuse'])

    def draw_sign(self, sx, sy, text):
        board = '#DEB887'
        pole = '#8B7355'
        char_w = len(text)
        bw = max(char_w * 2 + 2, 6)
        bh = 4
        for y in range(bh):
            for x in range(bw):
                self.px(sx + x, sy + y, board)
        for x in range(bw):
            self.px(sx + x, sy, pole)
            self.px(sx + x, sy + bh - 1, pole)
        self.px(sx + bw // 2, sy + bh, pole)
        self.px(sx + bw // 2, sy + bh + 1, pole)
        cx = (sx + bw / 2) * self.S
        cy = (sy + bh / 2) * self.S
        self.canvas.create_text(
            cx, cy, text=text,
            font=('Helvetica', 7, 'bold'), fill='#5D4037',
            anchor='center', tags='sprite'
        )

    def draw_progress_bar(self, sx, sy, progress, done, total, frame=0):
        """绘制像素风进度条 + 数字"""
        bar_w = 16           # 进度条宽度（像素格）
        bar_h = 2            # 进度条高度
        bg_color = '#4A3024'     # 深棕底槽，和 Clawd 边线同色系
        fill_color = '#E07A5F' if progress < 1.0 else '#D4A94B'  # Clawd 橙 → 金
        border_color = '#2A160C'  # 更深的边框
        filled = round(bar_w * min(progress, 1.0))

        # 边框
        for x in range(bar_w + 2):
            self.px(sx + x, sy, border_color)
            self.px(sx + x, sy + bar_h + 1, border_color)
        for y in range(bar_h + 2):
            self.px(sx, sy + y, border_color)
            self.px(sx + bar_w + 1, sy + y, border_color)

        # 背景
        for y in range(bar_h):
            for x in range(bar_w):
                self.px(sx + 1 + x, sy + 1 + y, bg_color)

        # 已完成部分
        for y in range(bar_h):
            for x in range(filled):
                self.px(sx + 1 + x, sy + 1 + y, fill_color)

        # 完成数字 "done/total"
        label = f'{done}/{total}'
        tx = (sx + 1 + bar_w / 2) * self.S
        ty = (sy + bar_h + 3) * self.S
        self.canvas.create_text(
            tx, ty, text=label,
            font=('Helvetica', 7, 'bold'), fill='#F5E9D4',
            anchor='center', tags='sprite'
        )

        # 全部完成：闪烁星星
        if progress >= 1.0 and (frame // 10) % 2 == 0:
            self.px(sx + bar_w + 3, sy, COLORS['star'])
            self.px(sx + bar_w + 3, sy + 1, COLORS['star2'])


# ─── 打卡系统 ────────────────────────────────────────────────
CHECKIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checkin.json')

class CheckInTracker:
    """多计划打卡进度追踪器

    数据结构 checkin.json:
    {
      "active": "plan_id",
      "plans": {
        "plan_id": {
          "name": "每周写公众号",
          "total": 32,
          "reward": "出国游一周",
          "start_date": "2026-04-20",
          "records": [{"date": "...", "note": "..."}, ...]
        },
        ...
      }
    }
    """

    def __init__(self):
        self.plans = {}
        self.active_id = None
        self._load()

    def _path(self):
        return CHECKIN_FILE

    def _load(self):
        try:
            with open(self._path(), 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 兼容旧格式（单计划）
            if 'plans' in data:
                self.plans = data['plans']
                self.active_id = data.get('active')
            elif 'total' in data:
                # 旧格式迁移
                pid = 'plan_1'
                self.plans = {pid: {
                    'name': '公众号写作计划' if _ZH else 'Writing Plan',
                    'total': data.get('total', 32),
                    'reward': data.get('reward', ''),
                    'start_date': data.get('start_date', date.today().isoformat()),
                    'records': data.get('records', []),
                }}
                self.active_id = pid
                self._save()  # 保存为新格式
        except (FileNotFoundError, json.JSONDecodeError):
            self.plans = {}
            self.active_id = None

    def _save(self):
        data = {
            'active': self.active_id,
            'plans': self.plans,
        }
        with open(self._path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @property
    def active(self):
        """当前激活的计划，没有则返回 None"""
        if self.active_id and self.active_id in self.plans:
            return self.plans[self.active_id]
        return None

    @property
    def total(self):
        p = self.active
        return p['total'] if p else 0

    @property
    def done(self):
        p = self.active
        return len(p['records']) if p else 0

    @property
    def progress(self):
        return self.done / max(self.total, 1)

    @property
    def completed(self):
        return self.total > 0 and self.done >= self.total

    def has_plan(self):
        return self.active is not None

    def plan_names(self):
        """返回 [(id, name, done, total), ...]"""
        result = []
        for pid, p in self.plans.items():
            result.append((pid, p['name'], len(p['records']), p['total']))
        return result

    def create_plan(self, name, total, reward='', start_date=None):
        """创建新计划并激活"""
        pid = f'plan_{len(self.plans) + 1}_{int(datetime.now().timestamp())}'
        self.plans[pid] = {
            'name': name,
            'total': total,
            'reward': reward,
            'start_date': start_date or date.today().isoformat(),
            'records': [],
        }
        self.active_id = pid
        self._save()
        return pid

    def switch_plan(self, pid):
        """切换激活计划"""
        if pid in self.plans:
            self.active_id = pid
            self._save()

    def delete_plan(self, pid):
        """删除计划"""
        if pid in self.plans:
            del self.plans[pid]
            if self.active_id == pid:
                self.active_id = next(iter(self.plans), None)
            self._save()

    def checkin(self, note=''):
        p = self.active
        if not p:
            return
        today = date.today().isoformat()
        p['records'].append({'date': today, 'note': note})
        self._save()

    def checkin_plan(self, pid, note=''):
        """对指定计划打卡（不切换 active）"""
        p = self.plans.get(pid)
        if not p:
            return
        today = date.today().isoformat()
        p['records'].append({'date': today, 'note': note})
        self._save()

    def checked_today(self, pid):
        """判断今日是否已对 pid 打卡"""
        p = self.plans.get(pid)
        if not p:
            return False
        today = date.today().isoformat()
        return any(r['date'] == today for r in p['records'])

    def undo(self):
        p = self.active
        if p and p['records']:
            p['records'].pop()
            self._save()

    @property
    def streak(self):
        """计算连续打卡天数（往回数连续有打卡记录的天数）"""
        p = self.active
        if not p or not p['records']:
            return 0
        dates = sorted(set(r['date'] for r in p['records']), reverse=True)
        today = date.today()
        # 最近一次打卡必须是今天或昨天，否则 streak 断了
        last = date.fromisoformat(dates[0])
        if (today - last).days > 1:
            return 0
        streak = 1
        for i in range(1, len(dates)):
            prev = date.fromisoformat(dates[i])
            curr = date.fromisoformat(dates[i - 1])
            if (curr - prev).days == 1:
                streak += 1
            elif (curr - prev).days == 0:
                continue  # 同一天多次打卡
            else:
                break
        return streak

    @property
    def days_since_last(self):
        """距离上次打卡的天数，没打过返回 -1"""
        p = self.active
        if not p or not p['records']:
            return -1
        last_date = max(r['date'] for r in p['records'])
        return (date.today() - date.fromisoformat(last_date)).days

    def summary(self):
        p = self.active
        if not p:
            return '暂无打卡计划' if _ZH else 'No active plan'

        name = p['name']
        done = len(p['records'])
        total = p['total']
        reward = p.get('reward', '')

        if _ZH:
            s = f'📋 {name}\n进度: {done}/{total}'
            if done >= total:
                s += f'\n🎉 全部完成！'
                if reward:
                    s += f'奖励: {reward}'
            else:
                s += f'\n剩余: {total - done}'
                try:
                    start = date.fromisoformat(p.get('start_date', ''))
                    today_d = date.today()
                    weeks_passed = max((today_d - start).days, 0) / 7
                    expected = min(int(weeks_passed * 2), total)
                    diff = done - expected
                    if diff >= 0:
                        s += ' ✅ 进度正常'
                    else:
                        s += f' ⚠️ 落后 {-diff}'
                except Exception:
                    pass
                if reward:
                    s += f'\n🎁 奖励: {reward}'
        else:
            s = f'📋 {name}\nProgress: {done}/{total}'
            if done >= total:
                s += f'\n🎉 Done!'
                if reward:
                    s += f' Reward: {reward}'
            else:
                s += f'\nRemaining: {total - done}'
                if reward:
                    s += f'\n🎁 Reward: {reward}'
        return s


# ─── 动画状态机 ───────────────────────────────────────────────
class StateMachine:
    # 心情权重：根据打卡状态调整各状态出现概率
    # mood > 0 开心，mood < 0 低落，mood == 0 正常
    MOOD_WEIGHTS = {
        # state:      (正常, 开心加成, 低落加成)
        'idle':       (1.0,  0.5,  1.5),
        'walk_left':  (1.0,  1.0,  1.0),
        'walk_right': (1.0,  1.0,  1.0),
        'dance':      (1.0,  2.5,  0.3),
        'sleep':      (1.0,  0.3,  2.5),
        'wave':       (1.0,  2.0,  0.5),
        'jump':       (1.0,  2.0,  0.5),
        'working':    (1.0,  1.0,  1.0),
        'happy':      (1.0,  3.0,  0.2),
        'eating':     (1.0,  1.5,  1.0),
        'excited':    (1.0,  2.5,  0.2),
        'firework':   (1.0,  1.5,  0.3),
    }

    def __init__(self):
        self.state = 'idle'
        self.frame = 0
        self.timer = 0.0
        self.duration = random.uniform(*STATE_DURATIONS['idle'])
        self.paused = False
        self.mood = 0  # -1.0 ~ 1.0
        self.excluded_states = set()  # 定居模式下屏蔽 walk_left/walk_right

    def update(self, dt):
        if self.paused:
            return
        self.timer += dt
        self.frame += 1
        if self.timer >= self.duration:
            self.transition()

    def transition(self):
        choices = [s for s in RANDOM_STATES if s != self.state and s not in self.excluded_states]
        if not choices:
            choices = ['idle']
        weights = []
        for s in choices:
            base, happy_w, sad_w = self.MOOD_WEIGHTS.get(s, (1.0, 1.0, 1.0))
            if self.mood > 0:
                w = base + (happy_w - base) * self.mood
            elif self.mood < 0:
                w = base + (sad_w - base) * (-self.mood)
            else:
                w = base
            weights.append(max(w, 0.05))
        self.state = random.choices(choices, weights=weights, k=1)[0]
        self.duration = random.uniform(*STATE_DURATIONS[self.state])
        self.timer = 0.0
        self.frame = 0

    def force_state(self, state, duration=None):
        if state in STATE_DURATIONS:
            self.state = state
            self.duration = duration or random.uniform(*STATE_DURATIONS[state])
            self.timer = 0.0
            self.frame = 0
            self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False


# ─── 托盘图标 ────────────────────────────────────────────────
def _create_tray_icon_image():
    """生成一个 16x16 的小螃蟹图标给托盘用"""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 简化的螃蟹轮廓
    body_color = (224, 122, 95, 255)  # #E07A5F
    eye_color = (0, 0, 0, 255)
    # 身体
    draw.rectangle([4, 3, 11, 10], fill=body_color)
    # 钳子
    draw.rectangle([2, 5, 3, 8], fill=body_color)
    draw.rectangle([12, 5, 13, 8], fill=body_color)
    # 腿
    for x in [5, 7, 9]:
        draw.rectangle([x, 11, x, 13], fill=body_color)
    # 眼睛
    draw.rectangle([6, 5, 6, 5], fill=eye_color)
    draw.rectangle([9, 5, 9, 5], fill=eye_color)
    return img


# ─── 主窗口 ───────────────────────────────────────────────────
class ClawdPet:
    def __init__(self):
        self.root = tk.Tk()
        # Dock 和菜单栏显示的应用名（macOS 上走 tk appname，不是 wm_title）
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
            # Windows: 用 transparentcolor 实现穿透
            self.root.config(bg=WIN_TRANSPARENT_COLOR)
            self.root.wm_attributes('-transparentcolor', WIN_TRANSPARENT_COLOR)
            canvas_bg = WIN_TRANSPARENT_COLOR
        else:
            # Linux fallback（不完美但能用）
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

        # 屏幕信息
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # 初始位置：屏幕右下角
        init_x = self.screen_w - CANVAS_W - 100
        init_y = self.screen_h - CANVAS_H - 80
        self.root.geometry(f'{CANVAS_W}x{CANVAS_H}+{init_x}+{init_y}')

        # 拖动
        self._drag_x = 0
        self._drag_y = 0
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        # 音乐播放
        self._music_proc = None
        self._music_playing = False
        self._music_files = []
        self._music_index = 0
        self._scan_music()

        # 右键菜单（macOS: Button-2, Windows/Linux: Button-3）
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=I18N['play_music'], command=self._toggle_music)
        self.menu.add_command(label=I18N['next_track'], command=self._next_music)
        self.menu.add_separator()
        self.menu.add_command(label=I18N['firework'], command=self._trigger_firework)
        self.menu.add_separator()
        # 场景切换
        self._scene_menu_index = self.menu.index('end') + 1
        self.menu.add_command(label=I18N['go_beach'], command=self._toggle_scene)
        # 游走/定居 模式
        self._mode_menu_index = self.menu.index('end') + 1
        self.menu.add_command(label=I18N['mode_settle'], command=self._toggle_wander)
        self.menu.add_separator()
        # 打卡菜单组（3 项）
        self.menu.add_command(label=I18N['checkin'], command=self._do_checkin)
        self.menu.add_command(label=I18N['progress'], command=self._show_progress)
        self.menu.add_command(label=I18N['manage_plans'], command=self._manage_plans_dialog)
        self.menu.add_separator()
        self.menu.add_command(label=I18N['show_hide'], command=self.toggle_visibility)
        self.menu.add_separator()
        self.menu.add_command(label=I18N['quit'], command=self._quit)

        if IS_MACOS:
            self.canvas.bind('<ButtonPress-2>', self._show_menu)
            self.canvas.bind('<Control-ButtonPress-1>', self._show_menu)
        else:
            self.canvas.bind('<ButtonPress-3>', self._show_menu)

        # Clawd 在画布中的锚点（偏下，给烟花留头部空间）
        self.cx = 11
        self.cy = 18

        # 游走 / 定居 模式（默认游走）
        self._wander_mode = True

        # 鼠标静止检测
        self._last_mouse_x = 0
        self._last_mouse_y = 0
        self._mouse_idle_frames = 0
        self._mouse_idle_threshold = FPS * 60 * 2   # 2 分钟没动鼠标 → 歪头看你
        self._is_looking_at_user = False

        # 久坐提醒
        self._work_frames = 0
        self._drink_reminder_interval = FPS * 60 * 45  # 每 45 分钟提醒一次
        self._showing_drink_sign = False
        self._drink_sign_frames = 0
        self._drink_sign_duration = FPS * 12  # 牌子显示 12 秒

        # 显示/隐藏状态
        self._visible = True

        # 打卡系统
        self.tracker = CheckInTracker()
        self._show_progress_bar = True           # 始终显示进度条
        self._checkin_celebrate_frames = 0       # 打卡庆祝动画剩余帧数

        # 心情更新计时
        self._mood_update_interval = FPS * 60  # 每分钟更新一次心情
        self._mood_update_counter = 0
        self._update_mood()  # 初始化心情

        # Claude Code 联动: 启动 HTTP server
        self._claude_linked = False
        self._boot_frame = 0
        self._start_hook_server()

        # 启动系统托盘
        self._tray_icon = None
        self._start_tray()

        # 启动全局快捷键监听
        self._hotkey_listener = None
        self._start_hotkey()

    # ─── 显示/隐藏切换 ────────────────────────────────────────

    def toggle_visibility(self):
        if self._visible:
            self._hide()
        else:
            self._show()

    def _hide(self):
        if self._visible:
            self.root.withdraw()
            self._visible = False

    def _show(self):
        if not self._visible:
            self.root.deiconify()
            self.root.wm_attributes('-topmost', True)
            self._visible = True

    # ─── 系统托盘 ─────────────────────────────────────────────

    def _start_tray(self):
        if not _HAS_PYSTRAY:
            return

        def on_show_hide(icon, item):
            self.root.after(0, self.toggle_visibility)

        def on_firework(icon, item):
            self.root.after(0, self._trigger_firework)

        def on_quit(icon, item):
            self.root.after(0, self._quit)

        tray_menu = pystray.Menu(
            pystray.MenuItem(I18N['show_hide'], on_show_hide, default=True),
            pystray.MenuItem(I18N['firework'], on_firework),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(I18N['quit'], on_quit),
        )

        icon_image = _create_tray_icon_image()
        self._tray_icon = pystray.Icon('clawdy', icon_image, 'Clawdy', tray_menu)

        t = threading.Thread(target=self._tray_icon.run, daemon=True)
        t.start()

    def _stop_tray(self):
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass

    # ─── 全局快捷键 ───────────────────────────────────────────

    def _start_hotkey(self):
        if not _HAS_PYNPUT:
            return

        try:
            def on_activate():
                self.root.after(0, self.toggle_visibility)

            # Ctrl+Shift+C
            hotkey = pynput_keyboard.HotKey(
                pynput_keyboard.HotKey.parse('<ctrl>+<shift>+c'),
                on_activate,
            )

            def for_canonical(f):
                return lambda k: f(self._hotkey_listener.canonical(k))

            self._hotkey_listener = pynput_keyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release),
            )
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
        except Exception:
            # 没有辅助功能权限时，静默跳过快捷键功能
            self._hotkey_listener = None

    def _stop_hotkey(self):
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass

    # ─── 打卡功能 ─────────────────────────────────────────────

    def _do_checkin(self):
        """打卡：弹出任务列表，每行一个打卡按钮"""
        if not self.tracker.has_plan():
            self._new_plan_dialog()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title('Clawdy')
        self._prep_dialog(dialog)

        outer, frame = _pixel_frame(dialog)
        outer.pack(fill='both', expand=True)
        frame.config(padx=18, pady=14)

        title_lbl = tk.Label(frame, text='🦀 ' + ('今日打卡' if _ZH else 'Today'),
                             font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
        title_lbl.pack(anchor='w', fill='x')

        list_frame = tk.Frame(frame, bg=PX_BG)
        list_frame.pack(fill='x', pady=(10, 0))

        def render_list():
            for w in list_frame.winfo_children():
                w.destroy()
            for pid, pname, pdone, ptotal in self.tracker.plan_names():
                done_today = self.tracker.checked_today(pid)
                completed = pdone >= ptotal
                card_border = tk.Frame(list_frame, bg=PX_BORDER_SOFT)
                card_border.pack(fill='x', pady=(0, 6))
                card = tk.Frame(card_border, bg=PX_BG_SOFT, padx=10, pady=8)
                card.pack(padx=2, pady=2, fill='x')

                info = tk.Frame(card, bg=PX_BG_SOFT)
                info.pack(side='left', fill='x', expand=True)
                pct = int(pdone / max(ptotal, 1) * 100)
                tk.Label(info, text=pname, font=PX_FONT_B,
                         fg=PX_TEXT, bg=PX_BG_SOFT, anchor='w').pack(anchor='w')
                tk.Label(info, text=f'{pdone}/{ptotal}  ({pct}%)',
                         font=PX_FONT, fg=PX_TEXT_SOFT,
                         bg=PX_BG_SOFT, anchor='w').pack(anchor='w')

                btn_box = tk.Frame(card, bg=PX_BG_SOFT)
                btn_box.pack(side='right')

                if completed:
                    tk.Label(btn_box, text='✓ ' + ('已完成' if _ZH else 'Done'),
                             font=PX_FONT_B, fg=PX_GOLD,
                             bg=PX_BG_SOFT, padx=10).pack()
                elif done_today:
                    tk.Label(btn_box, text='✓ ' + ('今日已打' if _ZH else 'Today ✓'),
                             font=PX_FONT_B, fg=PX_SUCCESS,
                             bg=PX_BG_SOFT, padx=10).pack()
                else:
                    _pixel_button(
                        btn_box, '打卡' if _ZH else 'Check',
                        lambda p=pid, n=pname: self._checkin_with_note(
                            p, n, on_done=render_list, parent=dialog),
                        primary=True,
                    ).pack()

        render_list()

        btn_frame = tk.Frame(frame, bg=PX_BG)
        btn_frame.pack(fill='x', pady=(12, 0))
        _pixel_button(btn_frame, '关闭' if _ZH else 'Close',
                      dialog.destroy).pack(side='right')

        dialog.bind('<Escape>', lambda e: dialog.destroy())

        dialog.update_idletasks()
        dw = max(dialog.winfo_reqwidth(), 340)
        dh = dialog.winfo_reqheight()
        x = (self.screen_w - dw) // 2
        y = (self.screen_h - dh) // 2
        dialog.geometry(f'{dw}x{dh}+{x}+{y}')
        _bind_drag(dialog, title_lbl)
        dialog.lift()

    def _checkin_with_note(self, pid, plan_name, on_done=None, parent=None):
        """对指定计划打卡，弹小输入框写一句 note（可跳过）"""
        dialog = tk.Toplevel(parent or self.root)
        dialog.title('Clawdy')
        self._prep_dialog(dialog)

        outer, frame = _pixel_frame(dialog)
        outer.pack(fill='both', expand=True)
        frame.config(padx=16, pady=12)

        p = self.tracker.plans.get(pid, {})
        count = len(p.get('records', [])) + 1
        title = f'🦀 {plan_name} · 第 {count} 次 ✅' if _ZH \
            else f'🦀 {plan_name} · #{count} ✅'
        title_lbl = tk.Label(frame, text=title, font=PX_FONT_TITLE,
                             fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
        title_lbl.pack(anchor='w', fill='x')

        tk.Label(frame, text='写一句话（可跳过）' if _ZH else 'Leave a note (optional)',
                 font=PX_FONT, fg=PX_TEXT_SOFT, bg=PX_BG).pack(anchor='w', pady=(10, 2))
        note_var = tk.StringVar()
        wrap, entry = _pixel_entry(frame, note_var)
        wrap.pack(fill='x')

        def do_submit():
            note = note_var.get().strip()
            total = p.get('total', 0)
            done_before = len(p.get('records', []))
            was_milestone = done_before in (
                round(total * 0.25),
                round(total * 0.50),
                round(total * 0.75),
            )
            self.tracker.checkin_plan(pid, note)
            self._update_mood()
            dialog.destroy()
            self._checkin_celebrate_frames = FPS * 3
            self.sm.force_state('celebrate', duration=3.0)
            done_after = done_before + 1
            if done_after >= total or was_milestone:
                self.root.after(2000, self._trigger_firework)
            if on_done:
                on_done()

        entry.bind('<Return>', lambda e: do_submit())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        btn_frame = tk.Frame(frame, bg=PX_BG)
        btn_frame.pack(fill='x', pady=(12, 0))
        _pixel_button(btn_frame, '打卡！' if _ZH else 'Check In!',
                      do_submit, primary=True).pack(side='right')
        _pixel_button(btn_frame, '取消' if _ZH else 'Cancel',
                      dialog.destroy).pack(side='right', padx=(0, 8))

        dialog.update_idletasks()
        dw = max(dialog.winfo_reqwidth(), 280)
        dh = dialog.winfo_reqheight()
        x = (self.screen_w - dw) // 2
        y = (self.screen_h - dh) // 2
        dialog.geometry(f'{dw}x{dh}+{x}+{y}')
        _bind_drag(dialog, title_lbl)
        dialog.lift()
        dialog.after(50, lambda: entry.focus_force())

    def _show_progress(self):
        """进度弹窗：列出全部计划的进度总览 + 每行撤销"""
        if not self.tracker.has_plan():
            self._manage_plans_dialog()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title('Clawdy')
        self._prep_dialog(dialog)

        outer, frame = _pixel_frame(dialog)
        outer.pack(fill='both', expand=True)
        frame.config(padx=18, pady=14)

        title_lbl = tk.Label(
            frame, text='🦀 ' + ('全部进度' if _ZH else 'All Progress'),
            font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
        title_lbl.pack(anchor='w', fill='x')

        streak = self.tracker.streak
        if streak > 0:
            streak_color = PX_DANGER if streak >= 7 else PX_ACCENT if streak >= 3 else PX_SUCCESS
            flame = '🔥' if streak >= 7 else '⚡' if streak >= 3 else '✨'
            streak_text = f'{flame} ' + (f'连续 {streak} 天' if _ZH else f'{streak} day streak')
            tk.Label(frame, text=streak_text, font=PX_FONT_B,
                     fg=streak_color, bg=PX_BG).pack(anchor='w', pady=(2, 0))

        list_frame = tk.Frame(frame, bg=PX_BG)
        list_frame.pack(fill='x', pady=(10, 0))

        def render_list():
            for w in list_frame.winfo_children():
                w.destroy()
            for pid, pname, pdone, ptotal in self.tracker.plan_names():
                p = self.tracker.plans.get(pid, {})
                progress = pdone / max(ptotal, 1)
                is_active = (pid == self.tracker.active_id)

                card_border = tk.Frame(list_frame, bg=PX_BORDER_SOFT)
                card_border.pack(fill='x', pady=(0, 6))
                card = tk.Frame(card_border, bg=PX_BG_SOFT, padx=10, pady=8)
                card.pack(padx=2, pady=2, fill='x')

                # 顶部一行：名字 + 计数
                top = tk.Frame(card, bg=PX_BG_SOFT)
                top.pack(fill='x')
                star = '★ ' if is_active else ''
                tk.Label(top, text=star + pname, font=PX_FONT_B,
                         fg=PX_ACCENT if is_active else PX_TEXT,
                         bg=PX_BG_SOFT, anchor='w').pack(side='left')
                tk.Label(top, text=f'{pdone}/{ptotal}  ({int(progress*100)}%)',
                         font=PX_FONT, fg=PX_TEXT_SOFT,
                         bg=PX_BG_SOFT).pack(side='right')

                # 迷你进度条
                bar_h = 10
                bar_border = tk.Frame(card, bg=PX_BORDER)
                bar_border.pack(fill='x', pady=(6, 0))
                bar_canvas = tk.Canvas(bar_border, height=bar_h, bg=PX_INPUT_BG,
                                       highlightthickness=0, bd=0)
                bar_canvas.pack(padx=2, pady=2, fill='x')

                def _paint_bar(cv=bar_canvas, prog=progress):
                    cv.delete('all')
                    bw = cv.winfo_width() or 240
                    fw = int(bw * min(prog, 1.0))
                    fc = PX_GOLD if prog >= 1.0 else PX_ACCENT
                    if fw > 0:
                        cv.create_rectangle(0, 0, fw, bar_h, fill=fc, outline='')
                    for i in range(1, 10):
                        gx = int(bw * i / 10)
                        cv.create_rectangle(gx, 0, gx + 1, bar_h,
                                            fill=PX_BORDER_SOFT, outline='')
                bar_canvas.bind('<Configure>', lambda e, fn=_paint_bar: fn())

                # 奖励（若有）
                reward = p.get('reward', '')
                if reward:
                    tk.Label(card, text='🎁 ' + reward, font=PX_FONT,
                             fg=PX_GOLD, bg=PX_BG_SOFT,
                             anchor='w').pack(anchor='w', pady=(6, 0))

                # 底部一行：最后一次打卡 + 撤销按钮
                if p.get('records'):
                    foot = tk.Frame(card, bg=PX_BG_SOFT)
                    foot.pack(fill='x', pady=(6, 0))
                    last = p['records'][-1]
                    last_txt = ('最近 ' if _ZH else 'Last ') + last['date']
                    if last.get('note'):
                        last_txt += f'  "{last["note"]}"'
                    tk.Label(foot, text=last_txt, font=PX_FONT,
                             fg=PX_TEXT_SOFT, bg=PX_BG_SOFT,
                             anchor='w', wraplength=260,
                             justify='left').pack(side='left', fill='x',
                                                  expand=True)
                    _pixel_button(
                        foot, '↩ ' + ('撤销' if _ZH else 'Undo'),
                        lambda p=pid: self._undo_plan(p, on_done=render_list,
                                                      parent=dialog),
                    ).pack(side='right')

        render_list()

        # 底部按钮栏
        tk.Frame(frame, bg=PX_BORDER_SOFT, height=1).pack(fill='x', pady=(12, 8))
        btn_frame = tk.Frame(frame, bg=PX_BG)
        btn_frame.pack(fill='x')
        _pixel_button(btn_frame, '关闭' if _ZH else 'Close',
                      dialog.destroy, primary=True).pack(side='right')
        _pixel_button(btn_frame, '打卡' if _ZH else 'Check In',
                      lambda: (dialog.destroy(),
                               self.root.after(80, self._do_checkin))).pack(
                                   side='right', padx=(0, 8))

        dialog.bind('<Escape>', lambda e: dialog.destroy())

        dialog.update_idletasks()
        dw = max(dialog.winfo_reqwidth(), 340)
        dh = dialog.winfo_reqheight()
        x = (self.screen_w - dw) // 2
        y = (self.screen_h - dh) // 2
        dialog.geometry(f'{dw}x{dh}+{x}+{y}')
        _bind_drag(dialog, title_lbl)
        dialog.lift()

    def _undo_plan(self, pid, on_done=None, parent=None):
        """撤销指定计划的最近一次打卡（带二次确认）"""
        p = self.tracker.plans.get(pid)
        if not p or not p.get('records'):
            return
        last = p['records'][-1]
        confirm = tk.Toplevel(parent or self.root)
        confirm.title('Clawdy')
        self._prep_dialog(confirm)
        c_outer, cf = _pixel_frame(confirm)
        c_outer.pack(fill='both', expand=True)
        cf.config(padx=16, pady=12)
        txt = f'撤销「{p["name"]}」{last["date"]} 的打卡？' if _ZH \
            else f'Undo "{p["name"]}" on {last["date"]}?'
        if last.get('note'):
            txt += f'\n"{last["note"]}"'
        tk.Label(cf, text=txt, font=PX_FONT, fg=PX_TEXT, bg=PX_BG,
                 wraplength=260, justify='center').pack(pady=(0, 10))
        cbf = tk.Frame(cf, bg=PX_BG)
        cbf.pack()

        def yes():
            p['records'].pop()
            self.tracker._save()
            self._update_mood()
            confirm.destroy()
            if on_done:
                on_done()

        _pixel_button(cbf, '撤销' if _ZH else 'Undo',
                      yes, danger=True).pack(side='left', padx=4)
        _pixel_button(cbf, '取消' if _ZH else 'Cancel',
                      confirm.destroy).pack(side='left', padx=4)
        confirm.update_idletasks()
        cw = confirm.winfo_reqwidth()
        ch = confirm.winfo_reqheight()
        cx = (self.screen_w - cw) // 2
        cy = (self.screen_h - ch) // 2
        confirm.geometry(f'{cw}x{ch}+{cx}+{cy}')
        confirm.lift()

    # ─── 管理计划弹窗 ────────────────────────────────────────

    def _manage_plans_dialog(self):
        """统一管理：新建 / 切换 / 删除计划"""
        plans = self.tracker.plan_names()

        # 没有任何计划 → 直接新建
        if not plans:
            self._new_plan_dialog()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title('Clawdy')
        self._prep_dialog(dialog)

        outer, frame = _pixel_frame(dialog)
        outer.pack(fill='both', expand=True)
        frame.config(padx=18, pady=14)

        tk.Label(frame, text='🦀 ' + ('管理计划' if _ZH else 'Manage Plans'),
                 font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG).pack(anchor='w')

        # 计划列表（每张卡片 = 浅棕边框 + 米白内底）
        for pid, pname, pdone, ptotal in plans:
            is_active = pid == self.tracker.active_id
            card_border = tk.Frame(frame, bg=PX_BORDER_SOFT)
            card_border.pack(fill='x', pady=(8, 0))
            card = tk.Frame(card_border, bg=PX_BG_SOFT, padx=10, pady=8)
            card.pack(padx=2, pady=2, fill='x')

            info = tk.Frame(card, bg=PX_BG_SOFT)
            info.pack(side='left', fill='x', expand=True)

            prefix = '▶ ' if is_active else '  '
            name_color = PX_ACCENT if is_active else PX_TEXT
            tk.Label(info, text=f'{prefix}{pname}',
                     font=PX_FONT_B, fg=name_color,
                     bg=PX_BG_SOFT, anchor='w').pack(anchor='w')
            pct = int(pdone / max(ptotal, 1) * 100)
            tk.Label(info, text=f'{pdone}/{ptotal}  ({pct}%)',
                     font=PX_FONT, fg=PX_TEXT_SOFT,
                     bg=PX_BG_SOFT, anchor='w').pack(anchor='w')

            btns = tk.Frame(card, bg=PX_BG_SOFT)
            btns.pack(side='right')

            if not is_active:
                _pixel_button(btns, '切换' if _ZH else 'Use',
                              lambda p=pid: (
                                  self.tracker.switch_plan(p),
                                  self._update_mood(),
                                  dialog.destroy(),
                                  self.root.after(100, self._manage_plans_dialog),
                              )).pack(side='left', padx=2)

            _pixel_button(btns, '删除' if _ZH else 'Del',
                          lambda p=pid, n=pname: self._confirm_delete_plan(
                              p, n, dialog,
                          ), danger=True).pack(side='left', padx=2)

        # 底部按钮
        tk.Frame(frame, bg=PX_BORDER_SOFT, height=1).pack(fill='x', pady=(12, 8))
        btn_frame = tk.Frame(frame, bg=PX_BG)
        btn_frame.pack(fill='x')

        _pixel_button(btn_frame, '关闭' if _ZH else 'Close',
                      dialog.destroy, primary=True).pack(side='right')

        _pixel_button(btn_frame, '+ ' + ('新建计划' if _ZH else 'New Plan'),
                      lambda: (dialog.destroy(), self._new_plan_dialog())
                      ).pack(side='left')

        dialog.bind('<Escape>', lambda e: dialog.destroy())

        # 居中
        dialog.update_idletasks()
        dw = max(dialog.winfo_reqwidth(), 320)
        dh = dialog.winfo_reqheight()
        x = (self.screen_w - dw) // 2
        y = (self.screen_h - dh) // 2
        dialog.geometry(f'{dw}x{dh}+{x}+{y}')
        dialog.lift()

    def _confirm_delete_plan(self, pid, name, parent_dialog):
        """删除计划确认弹窗（像素风）"""
        confirm = tk.Toplevel(parent_dialog)
        confirm.title('Clawdy')
        self._prep_dialog(confirm)

        c_outer, cf = _pixel_frame(confirm)
        c_outer.pack(fill='both', expand=True)
        cf.config(padx=16, pady=12)

        txt = f'确定删除「{name}」？\n所有打卡记录将丢失！' if _ZH else f'Delete "{name}"?\nAll records will be lost!'
        tk.Label(cf, text=txt, font=PX_FONT, fg=PX_TEXT, bg=PX_BG,
                 wraplength=240, justify='center').pack(pady=(0, 10))

        cbf = tk.Frame(cf, bg=PX_BG)
        cbf.pack()

        def yes():
            self.tracker.delete_plan(pid)
            self._update_mood()
            confirm.destroy()
            parent_dialog.destroy()
            if self.tracker.plan_names():
                self.root.after(100, self._manage_plans_dialog)

        _pixel_button(cbf, '删除' if _ZH else 'Delete',
                      yes, danger=True).pack(side='left', padx=4)
        _pixel_button(cbf, '取消' if _ZH else 'Cancel',
                      confirm.destroy).pack(side='left', padx=4)

        confirm.update_idletasks()
        cw = confirm.winfo_reqwidth()
        ch = confirm.winfo_reqheight()
        cx = (self.screen_w - cw) // 2
        cy = (self.screen_h - ch) // 2
        confirm.geometry(f'{cw}x{ch}+{cx}+{cy}')
        confirm.lift()

    def _new_plan_dialog(self):
        """弹窗创建新打卡计划（像素风）"""
        dialog = tk.Toplevel(self.root)
        dialog.title('Clawdy')
        self._prep_dialog(dialog)

        outer, frame = _pixel_frame(dialog)
        outer.pack(padx=0, pady=0, fill='both', expand=True)
        for w in (frame,):
            w.config(padx=18, pady=14)

        # 标题（作为拖动把手）
        title_lbl = tk.Label(frame, text='🦀 ' + ('新建打卡计划' if _ZH else 'New Plan'),
                             font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
        title_lbl.pack(anchor='w', fill='x')

        def add_field(label_text, var):
            tk.Label(frame, text=label_text, font=PX_FONT,
                     fg=PX_TEXT_SOFT, bg=PX_BG, anchor='w').pack(fill='x', pady=(10, 2))
            wrap, entry = _pixel_entry(frame, var)
            wrap.pack(fill='x')
            return entry

        name_var = tk.StringVar()
        name_entry = add_field('计划名称' if _ZH else 'Plan name', name_var)

        total_var = tk.StringVar(value='32')
        add_field('目标次数' if _ZH else 'Target count', total_var)

        reward_var = tk.StringVar()
        add_field(('完成奖励（选填）' if _ZH else 'Reward (optional)'), reward_var)

        date_var = tk.StringVar(value=date.today().isoformat())
        add_field('开始日期' if _ZH else 'Start date', date_var)

        def on_create():
            name = name_var.get().strip()
            if not name:
                return
            try:
                total = int(total_var.get().strip())
                if total <= 0:
                    return
            except ValueError:
                return
            reward = reward_var.get().strip()
            start = date_var.get().strip()
            self.tracker.create_plan(name, total, reward, start)
            self._update_mood()
            dialog.destroy()

        dialog.bind('<Return>', lambda e: on_create())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        btn_frame = tk.Frame(frame, bg=PX_BG)
        btn_frame.pack(fill='x', pady=(16, 0))
        _pixel_button(btn_frame, '创建' if _ZH else 'Create',
                      on_create, primary=True).pack(side='right')
        _pixel_button(btn_frame, '取消' if _ZH else 'Cancel',
                      dialog.destroy).pack(side='right', padx=(0, 8))

        # 居中
        dialog.update_idletasks()
        dw = max(dialog.winfo_reqwidth(), 300)
        dh = dialog.winfo_reqheight()
        x = (self.screen_w - dw) // 2
        y = (self.screen_h - dh) // 2
        dialog.geometry(f'{dw}x{dh}+{x}+{y}')

        # 拖动（只绑在标题 Label 上，不影响输入框）
        _bind_drag(dialog, title_lbl)

        dialog.lift()
        dialog.after(50, lambda: name_entry.focus_force())

    # ─── Hook Server ──────────────────────────────────────────

    def _start_hook_server(self):
        pet = self

        class HookHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                path = self.path.strip('/')
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else b''

                state_map = {
                    'prompt':    'thinking',
                    'tool':      'cc_working',
                    'error':     'error',
                    'done':      'celebrate',
                }

                # 显示/隐藏控制
                if path == 'toggle':
                    pet.root.after(0, pet.toggle_visibility)
                elif path == 'show':
                    pet.root.after(0, pet._show)
                elif path == 'hide':
                    pet.root.after(0, pet._hide)
                # Claude Code 联动
                elif path == 'idle':
                    pet._claude_linked = False
                    pet.root.after(0, lambda: pet.sm.transition())
                else:
                    new_state = state_map.get(path)
                    if new_state and pet._boot_frame >= FPS * 3:
                        pet._claude_linked = True
                        pet.sm.state = new_state
                        pet.sm.timer = 0.0
                        pet.sm.duration = 10.0
                        pet.sm.paused = False
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'ok')

            def log_message(self, format, *args):
                pass

        def run_server():
            try:
                server = HTTPServer(('127.0.0.1', HOOK_PORT), HookHandler)
                server.serve_forever()
            except OSError:
                pass

        t = threading.Thread(target=run_server, daemon=True)
        t.start()

    def _trigger_firework(self):
        self.sm.state = 'firework'
        self.sm.frame = 0
        self.sm.timer = 0.0
        self.sm.duration = random.uniform(*STATE_DURATIONS['firework'])
        self.particles.clear()

    # ─── 音乐（跨平台）───────────────────────────────────────

    def _scan_music(self):
        self._music_files = sorted(
            glob.glob(os.path.join(MUSIC_DIR, '*.mp3')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.m4a')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.wav')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.aac')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.flac'))
        )
        if self._music_files:
            random.shuffle(self._music_files)

    def _toggle_music(self):
        if self._music_playing:
            self._stop_music()
        else:
            self._play_music()

    def _play_music(self):
        if not self._music_files:
            self._scan_music()
        if not self._music_files:
            return
        self._stop_music()
        filepath = self._music_files[self._music_index % len(self._music_files)]

        if IS_MACOS:
            self._music_proc = subprocess.Popen(
                ['afplay', filepath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif IS_WINDOWS and _HAS_PYGAME:
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
            except Exception:
                return
        elif IS_WINDOWS:
            # fallback: 用 Windows Media Player CLI
            self._music_proc = subprocess.Popen(
                ['cmd', '/c', 'start', '/min', '', filepath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                shell=False,
            )
        else:
            # Linux: 尝试 mpv 或 aplay
            for player in ['mpv', 'aplay', 'paplay']:
                try:
                    self._music_proc = subprocess.Popen(
                        [player, filepath],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    break
                except FileNotFoundError:
                    continue

        self._music_playing = True
        self.menu.entryconfigure(0, label=I18N['stop_music'])
        self._check_music_end()

    def _stop_music(self):
        if IS_WINDOWS and _HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        if self._music_proc:
            self._music_proc.terminate()
            self._music_proc = None
        self._music_playing = False
        self.menu.entryconfigure(0, label=I18N['play_music'])

    def _next_music(self):
        if not self._music_files:
            return
        self._music_index = (self._music_index + 1) % len(self._music_files)
        if self._music_playing:
            self._play_music()

    def _check_music_end(self):
        if IS_WINDOWS and _HAS_PYGAME:
            if not pygame.mixer.music.get_busy():
                self._music_index = (self._music_index + 1) % len(self._music_files)
                self._play_music()
                return
        elif self._music_proc and self._music_proc.poll() is not None:
            self._music_index = (self._music_index + 1) % len(self._music_files)
            self._play_music()
            return
        if self._music_playing:
            self.root.after(1000, self._check_music_end)

    def _quit(self):
        self._stop_music()
        self._stop_tray()
        self._stop_hotkey()
        self.root.destroy()

    # ─── 拖动 ─────────────────────────────────────────────────

    def _on_press(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
        self.sm.pause()

    def _on_drag(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f'+{x}+{y}')

    def _on_release(self, event):
        self.sm.resume()

    def _show_menu(self, event):
        self.sm.pause()
        self.menu.tk_popup(event.x_root, event.y_root)
        # tk_popup 返回后菜单已关闭，恢复动画
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
        dx = 0
        if diff_x > threshold:
            dx = 1
        elif diff_x < -threshold:
            dx = -1

        dy = 0
        if diff_y > threshold:
            dy = 1
        elif diff_y < -threshold:
            dy = -1

        return (dx, dy)

    def _move_window(self, dx, dy):
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        x = max(0, min(x, self.screen_w - CANVAS_W))
        y = max(0, min(y, self.screen_h - CANVAS_H))
        self.root.geometry(f'+{x}+{y}')

    def _toggle_scene(self):
        if self.renderer.scene == 'home':
            self.renderer.set_scene('beach')
            self.menu.entryconfigure(self._scene_menu_index, label=I18N['go_home'])
            self.cx = 11
        else:
            self.renderer.set_scene('home')
            self.menu.entryconfigure(self._scene_menu_index, label=I18N['go_beach'])
            self.cx = 11

    def _prep_dialog(self, dialog):
        """让出主窗口 topmost，dialog 关闭时自动恢复。dialog 不用 overrideredirect 以保证键盘输入。"""
        self.root.wm_attributes('-topmost', False)
        dialog.wm_attributes('-topmost', True)
        dialog.config(bg=PX_BORDER)

        def _restore(e):
            if e.widget is dialog:
                try:
                    self.root.wm_attributes('-topmost', True)
                except Exception:
                    pass
        dialog.bind('<Destroy>', _restore, add='+')

    def _toggle_wander(self):
        self._wander_mode = not self._wander_mode
        if self._wander_mode:
            self.menu.entryconfigure(self._mode_menu_index, label=I18N['mode_settle'])
            self.sm.excluded_states.discard('walk_left')
            self.sm.excluded_states.discard('walk_right')
            # 立即开始走，避免等下次 transition
            self.sm.force_state(random.choice(['walk_left', 'walk_right']))
        else:
            self.menu.entryconfigure(self._mode_menu_index, label=I18N['mode_wander'])
            self.sm.excluded_states.update({'walk_left', 'walk_right'})
            # 如果当前在 walk，立即切成 idle
            if self.sm.state in ('walk_left', 'walk_right'):
                self.sm.force_state('idle')

    # ─── 各状态绘制 ───────────────────────────────────────────

    def _draw_idle(self, f):
        ox, oy = self.cx, self.cy
        breath = round(math.sin(f * 0.15) * 0.5)
        oy += breath
        blink_cycle = f % 60
        if blink_cycle >= 56:
            eyes = 'blink'
        elif self._is_looking_at_user:
            eyes = 'up'
        else:
            eyes = self._get_mouse_eye_offset(ox, oy)

        lean = 0
        if self._is_looking_at_user:
            lean = 1 if (f // 30) % 2 == 0 else -1
        elif isinstance(eyes, tuple) and eyes[0] != 0:
            lean = eyes[0]

        self.renderer.draw_body(ox + lean, oy)
        self.renderer.draw_eyes(ox + lean, oy, eyes)

    def _draw_walk(self, f, direction):
        moving = not self.sm.paused
        if moving and self.renderer.scene == 'beach':
            # 场景内移动：走到画布边就掉头
            nx = self.cx + direction
            if nx < 0 or nx > 22:
                direction = -direction
                self.sm.force_state('walk_right' if direction > 0 else 'walk_left')
                nx = self.cx + direction
            self.cx = nx
        ox, oy = self.cx, self.cy
        legs = LEGS_A if (f // 4) % 2 == 0 else LEGS_B
        eyes = 'forward'
        if f % 50 < 3:
            eyes = 'blink'
        self.renderer.draw_body(ox, oy, legs=legs)
        self.renderer.draw_eyes(ox, oy, eyes)
        if moving and self.renderer.scene == 'home':
            self._move_window(direction * 2, 0)

    def _draw_dance(self, f):
        ox, oy = self.cx, self.cy
        t = (f % 30) / 30
        sway = round(math.sin(ease_in_out(t) * math.pi * 2) * 2)
        ox += sway
        bounce = round(abs(math.sin(f * 0.4)) * 2)
        oy -= bounce
        claw = CLAW_UP_RIGHT if math.sin(f * 0.3) > 0 else CLAW_UP_LEFT
        eyes = 'right' if sway > 0 else 'left'
        if f % 20 < 3:
            eyes = 'blink'
        self.renderer.draw_body(ox, oy, claw_extra=claw)
        self.renderer.draw_eyes(ox, oy, eyes)
        self.renderer.draw_blush(ox, oy)
        if f % 6 == 0:
            self.particles.emit(ox + 7, oy + 8, COLORS['star'], count=1,
                                speed=0.3, gravity=0.02, decay=0.04)

    def _draw_sleep(self, f):
        ox, oy = self.cx, self.cy + 3
        breath = round(math.sin(f * 0.08) * 0.5)
        oy += breath
        self.renderer.draw_body(ox, oy, curled=True)
        self.renderer.draw_zzz(ox, oy, f)

    def _draw_wave(self, f):
        ox, oy = self.cx, self.cy
        cycle = (f // 15) % 2
        claw = CLAW_UP_RIGHT if cycle == 0 else CLAW_UP_LEFT
        eyes = 'right' if cycle == 0 else 'left'
        sway = round(math.sin(f * 0.2) * 0.5)
        ox += sway
        self.renderer.draw_body(ox, oy, claw_extra=claw)
        self.renderer.draw_eyes(ox, oy, eyes)
        if f % 12 == 0:
            self.particles.emit(ox + 14, oy - 1, COLORS['heart'], count=1,
                                speed=0.5, gravity=-0.01, decay=0.03)

    def _draw_jump(self, f):
        ox, oy = self.cx, self.cy
        jump_f = f % 24
        if jump_f < 4:
            t = jump_f / 4
            squeeze = round(ease_in_out(t))
            oy += squeeze
            self.renderer.draw_body(ox, oy, squash=True)
            self.renderer.draw_eyes(ox, oy + 1, 'down')
        elif jump_f < 14:
            t = (jump_f - 4) / 10
            height = ease_out(math.sin(t * math.pi)) * 5
            oy -= round(height)
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'forward')
            if 6 < jump_f < 10:
                self.renderer.draw_sparkle(ox + 7, oy - 1)
                if jump_f == 8:
                    self.particles.emit(ox + 7, oy + 8, COLORS['white'], count=3,
                                        speed=0.4, gravity=0.06, decay=0.05)
        else:
            t = (jump_f - 14) / 10
            if t < 0.3:
                oy += 1
                self.renderer.draw_body(ox, oy, squash=True)
                self.renderer.draw_eyes(ox, oy + 1, 'blink')
                if jump_f == 15:
                    self.particles.emit(ox + 4, oy + 8, COLORS['zzz'], count=2,
                                        speed=0.3, spread=1.0, gravity=0.03, decay=0.04)
                    self.particles.emit(ox + 10, oy + 8, COLORS['zzz'], count=2,
                                        speed=0.3, spread=1.0, gravity=0.03, decay=0.04)
            else:
                self.renderer.draw_body(ox, oy)
                self.renderer.draw_eyes(ox, oy, 'forward')

    def _draw_working(self, f):
        ox, oy = self.cx, self.cy
        self.renderer.draw_screen(ox - 7, oy + 1, f)
        breath = round(math.sin(f * 0.12) * 0.3)
        self.renderer.draw_body(ox, oy + breath)
        eyes = 'left'
        if f % 40 < 3:
            eyes = 'blink'
        self.renderer.draw_eyes(ox, oy + breath, eyes)
        if f % 30 < 20:
            self.renderer.draw_sweat(ox, oy + breath, f)

    def _draw_happy(self, f):
        ox, oy = self.cx, self.cy
        t = (f % 20) / 20
        bounce = round(abs(math.sin(ease_in_out(t) * math.pi)) * 2)
        oy -= bounce
        self.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
        self.renderer.draw_eyes(ox, oy, 'happy')
        self.renderer.draw_blush(ox, oy)
        if f % 8 == 0:
            hx = ox + random.randint(2, 12)
            self.particles.emit(hx, oy - 1, COLORS['heart'], count=1,
                                speed=0.6, gravity=-0.02, decay=0.025)

    def _draw_eating(self, f):
        ox, oy = self.cx, self.cy
        phase = f % 120
        if phase < 30:
            t = ease_out(phase / 30)
            cookie_x = round(lerp(ox - 6, ox - 3, t))
            self.renderer.draw_cookie(cookie_x, oy + 3, bites=0)
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'left')
        elif phase < 90:
            bites = (phase - 30) // 20
            self.renderer.draw_cookie(ox + 1, oy + 2, bites=min(bites, 3))
            self.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_LEFT)
            eyes = 'blink' if (phase // 8) % 3 == 0 else 'down'
            self.renderer.draw_eyes(ox, oy, eyes)
            if bites > 0 and f % 5 == 0:
                self.particles.emit(ox + 2, oy + 4, COLORS['crumb'], count=1,
                                    speed=0.3, gravity=0.08, decay=0.04)
        else:
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'happy')
            self.renderer.draw_blush(ox, oy)
            if f % 10 == 0:
                self.particles.emit(ox + 7, oy - 1, COLORS['heart'], count=1,
                                    speed=0.4, gravity=-0.01, decay=0.03)

    def _draw_excited(self, f):
        ox, oy = self.cx, self.cy
        t = (f % 15) / 15
        bounce = round(abs(math.sin(ease_out(t) * math.pi)) * 3)
        oy -= bounce
        sway = round(math.sin(f * 0.5) * 1)
        ox += sway
        claw = CLAW_BOTH_UP if math.sin(f * 0.4) > 0 else None
        self.renderer.draw_body(ox, oy, claw_extra=claw)
        self.renderer.draw_eyes(ox, oy, 'forward')
        if f % 4 == 0:
            self.particles.emit(ox + random.randint(3, 11), oy - 1,
                                [COLORS['star'], COLORS['star2'], COLORS['white']],
                                count=1, speed=0.5, gravity=-0.02, decay=0.04)

    def _draw_thinking(self, f):
        ox, oy = self.cx, self.cy
        breath = round(math.sin(f * 0.1) * 0.5)
        oy += breath
        self.renderer.draw_body(ox, oy)
        eyes = 'up' if f % 40 > 5 else 'blink'
        self.renderer.draw_eyes(ox, oy, eyes)
        dot_phase = (f // 8) % 4
        if dot_phase >= 1:
            self.renderer.px(ox + 13, oy + 1, COLORS['zzz'])
        if dot_phase >= 2:
            self.renderer.px(ox + 15, oy - 1, COLORS['zzz'])
        if dot_phase >= 3:
            bx, by = ox + 15, oy - 4
            self.renderer.px(bx, by, COLORS['white'])
            self.renderer.px(bx + 1, by, COLORS['white'])
            self.renderer.px(bx + 2, by, COLORS['white'])
            self.renderer.px(bx, by - 1, COLORS['white'])
            self.renderer.px(bx + 1, by - 1, COLORS['white'])
            self.renderer.px(bx + 2, by - 1, COLORS['white'])
            self.renderer.px(bx + 3, by, COLORS['white'])
            self.renderer.px(bx - 1, by, COLORS['white'])
            dot_i = (f // 4) % 3
            for i in range(3):
                dy = -1 if i == dot_i else 0
                self.renderer.px(bx + i, by + dy, COLORS['eye'])

    def _draw_cc_working(self, f):
        ox, oy = self.cx, self.cy
        breath = round(math.sin(f * 0.1) * 0.5)
        oy += breath
        self.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
        eyes = 'forward' if f % 30 > 3 else 'blink'
        self.renderer.draw_eyes(ox, oy, eyes)
        self.renderer.draw_screen(ox - 7, oy + 1, f)
        if f % 4 == 0:
            self.particles.emit(ox - 4, oy + 2,
                                [COLORS['screen'], COLORS['screen2'], COLORS['white']],
                                count=1, speed=0.4, gravity=0.02, decay=0.05)

    def _draw_error(self, f):
        ox, oy = self.cx, self.cy
        shake = round(math.sin(f * 1.5) * 1)
        ox += shake
        self.renderer.draw_body(ox, oy)
        self.renderer.draw_eyes(ox, oy, 'forward')
        if f % 3 == 0:
            self.particles.emit(ox + 5 + random.randint(0, 4), oy - 1,
                                [COLORS['zzz'], COLORS['happy_eye']],
                                count=2, speed=0.3, gravity=-0.03, decay=0.03)
        self.renderer.px(ox + 7, oy - 2, COLORS['fw_red'])
        self.renderer.px(ox + 7, oy - 3, COLORS['fw_red'])
        if f % 10 < 5:
            self.renderer.px(ox + 7, oy - 1, COLORS['fw_red'])
        self.renderer.draw_sweat(ox, oy, f)

    def _draw_celebrate(self, f):
        ox, oy = self.cx, self.cy
        breath = round(math.sin(f * 0.1) * 0.5)
        oy += breath
        self.renderer.draw_body(ox, oy)
        self.renderer.draw_eyes(ox, oy, 'forward')
        self.renderer.draw_blush(ox, oy)
        if f % 3 == 0:
            self.particles.emit(ox + random.randint(2, 12), oy - 1,
                                [COLORS['fw_gold'], COLORS['fw_pink'],
                                 COLORS['fw_cyan'], COLORS['heart'], COLORS['star']],
                                count=2, speed=0.8, gravity=0.03, decay=0.025)

    def _draw_firework(self, f):
        ox, oy = self.cx, self.cy
        dur_frames = round(self.sm.duration * FPS)
        t = f / max(dur_frames, 1)

        boom_x = ox + 7
        boom_y = 8

        if t < 0.12:
            pt = t / 0.12
            self.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_RIGHT)
            self.renderer.draw_eyes(ox, oy, 'forward')
            self.renderer.draw_firework_stick(ox + 14, oy - 3)
            if pt > 0.4 and f % 2 == 0:
                self.particles.emit(ox + 14, oy - 4, COLORS['fw_spark'], count=2,
                                    speed=0.3, gravity=0.01, decay=0.06)

        elif t < 0.25:
            pt = (t - 0.12) / 0.13
            rocket_y = round(lerp(oy - 4, boom_y, ease_out(pt)))
            self.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_RIGHT)
            self.renderer.draw_eyes(ox, oy, 'up')
            self.renderer.px(boom_x, rocket_y, COLORS['fw_red'])
            self.renderer.px(boom_x, rocket_y + 1, COLORS['fw_orange'])
            if f % 2 == 0:
                self.particles.emit(boom_x, rocket_y + 2,
                                    [COLORS['fw_spark'], COLORS['fw_orange']],
                                    count=3, speed=0.4, gravity=0.06, decay=0.04)

        elif t < 0.50:
            pt = (t - 0.25) / 0.25
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'up')
            self.renderer.draw_blush(ox, oy)

            if f == round(0.25 * dur_frames):
                logo_colors = [COLORS['fw_gold'], COLORS['fw_orange'],
                               COLORS['body'], COLORS['star'], COLORS['white']]
                self.particles.emit_claude_logo(
                    boom_x, boom_y, logo_colors,
                    speed=2.5, gravity=0.015, decay=0.012
                )

            if f == round(0.35 * dur_frames):
                self.particles.emit_claude_logo(
                    boom_x - 6, boom_y + 2,
                    [COLORS['fw_pink'], COLORS['fw_red'], COLORS['fw_gold']],
                    speed=1.5, gravity=0.02, decay=0.018
                )

            if f == round(0.42 * dur_frames):
                self.particles.emit_claude_logo(
                    boom_x + 8, boom_y + 3,
                    [COLORS['fw_cyan'], COLORS['fw_green'], COLORS['white']],
                    speed=1.2, gravity=0.02, decay=0.02
                )

        elif t < 0.75:
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'up')
            self.renderer.draw_blush(ox, oy)
            if f % 6 == 0:
                sx = boom_x + random.randint(-8, 8)
                sy = random.randint(2, 10)
                self.particles.emit(sx, sy,
                                    [COLORS['fw_spark'], COLORS['fw_gold'], COLORS['fw_orange']],
                                    count=1, speed=0.15, gravity=0.03, decay=0.02)

        else:
            pt = (t - 0.75) / 0.25
            bounce = round(abs(math.sin(pt * math.pi * 4)) * 2)
            oy -= bounce
            self.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
            self.renderer.draw_eyes(ox, oy, 'happy')
            self.renderer.draw_blush(ox, oy)
            if f % 8 == 0:
                self.particles.emit(ox + 7, oy - 1, COLORS['heart'], count=1,
                                    speed=0.5, gravity=-0.02, decay=0.03)

    # ─── 主循环 ───────────────────────────────────────────────

    def _update_mood(self):
        """根据打卡频率更新小螃蟹心情"""
        if not self.tracker.has_plan():
            self.sm.mood = 0.0
            return
        streak = self.tracker.streak
        days = self.tracker.days_since_last
        progress = self.tracker.progress

        mood = 0.0
        # streak 加成：连续打卡越多越开心
        if streak >= 7:
            mood += 0.6
        elif streak >= 3:
            mood += 0.3
        elif streak >= 1:
            mood += 0.1

        # 进度加成：接近完成时更兴奋
        if progress >= 0.75:
            mood += 0.3
        elif progress >= 0.5:
            mood += 0.15

        # 太久没打卡：心情下降
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

        # 定期更新心情
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

    def _game_loop(self):
        self.renderer.clear()
        self.renderer.draw_background(self.sm.frame)
        self.sm.update(1.0 / FPS)
        self._update_awareness()
        if self._boot_frame < FPS * 3:
            self._boot_frame += 1

        state = self.sm.state
        f = self.sm.frame

        draw_map = {
            'idle':       lambda: self._draw_idle(f),
            'walk_left':  lambda: self._draw_walk(f, -1),
            'walk_right': lambda: self._draw_walk(f, 1),
            'dance':      lambda: self._draw_dance(f),
            'sleep':      lambda: self._draw_sleep(f),
            'wave':       lambda: self._draw_wave(f),
            'jump':       lambda: self._draw_jump(f),
            'working':    lambda: self._draw_working(f),
            'happy':      lambda: self._draw_happy(f),
            'eating':     lambda: self._draw_eating(f),
            'excited':    lambda: self._draw_excited(f),
            'firework':   lambda: self._draw_firework(f),
            'thinking':   lambda: self._draw_thinking(f),
            'cc_working': lambda: self._draw_cc_working(f),
            'error':      lambda: self._draw_error(f),
            'celebrate':  lambda: self._draw_celebrate(f),
        }

        draw_fn = draw_map.get(state)
        if draw_fn:
            draw_fn()

        if self._is_looking_at_user and state == 'idle':
            ox, oy = self.cx, self.cy
            if (f // 20) % 3 != 0:
                self.renderer.px(ox + 15, oy - 1, COLORS['zzz'])

        if self._showing_drink_sign:
            ox, oy = self.cx, self.cy
            self.renderer.draw_sign(ox + 1, oy - 6, I18N['drink_water'])

        # 进度条（始终显示在小螃蟹下方）
        if self._show_progress_bar and self.tracker.total > 0:
            ox, oy = self.cx, self.cy
            self.renderer.draw_progress_bar(
                ox - 1, oy + 10,
                self.tracker.progress,
                self.tracker.done,
                self.tracker.total,
                frame=f,
            )

        # 打卡庆祝倒计时
        if self._checkin_celebrate_frames > 0:
            self._checkin_celebrate_frames -= 1

        self.particles.update()
        self.particles.draw(self.renderer)

        if self._music_playing:
            self.renderer.draw_music_notes(self.cx, self.cy, f)

        self.root.after(INTERVAL, self._game_loop)

    def run(self):
        self.root.after(100, self._game_loop)
        self.root.mainloop()


# ─── 入口 ─────────────────────────────────────────────────────
if __name__ == '__main__':
    pet = ClawdPet()
    pet.run()
