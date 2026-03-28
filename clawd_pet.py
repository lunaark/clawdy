#!/usr/bin/env python3
"""Clawd Desktop Pet — macOS 桌面像素风小螃蟹"""

import tkinter as tk
import random
import math
import subprocess
import os
import glob
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── 常量 ─────────────────────────────────────────────────────
SCALE = 6          # 每个逻辑像素 = 6×6 屏幕像素
FPS = 15
INTERVAL = 1000 // FPS  # ms

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
}

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
        """发射粒子"""
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
        """爆发式发射（烟花用）"""
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
        """Claude logo 米字形烟花：8个方向射出粒子线"""
        # 8 个方向：上、下、左、右、四个对角
        angles = [
            -math.pi/2,              # 上
            math.pi/2,               # 下
            math.pi,                 # 左
            0,                       # 右
            -math.pi/4,              # 右上
            -3*math.pi/4,            # 左上
            math.pi/4,               # 右下
            3*math.pi/4,             # 左下
        ]
        for angle in angles:
            # 每个方向射出多个粒子，速度递减，形成线条
            for i in range(6):
                spd = speed * (1.0 - i * 0.12) + random.uniform(-0.1, 0.1)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
                c = random.choice(colors)
                self.particles.append(
                    Particle(cx, cy, vx, vy, c, life=1.2, decay=decay, gravity=gravity)
                )
            # 方向之间加一些散射小粒子
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
        """更新所有粒子"""
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
        """绘制所有粒子"""
        for p in self.particles:
            if p.life > 0.15:
                renderer.px(round(p.x), round(p.y), p.color)


# ─── 像素渲染器 ───────────────────────────────────────────────
class PixelRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.S = SCALE

    def clear(self):
        self.canvas.delete('sprite')

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
            # 笑眼：只画下半格，表示眯眼
            self.px(ox + EYE_L[0], oy + EYE_L[1] + 1, COLORS['eye'])
            self.px(ox + EYE_R[0], oy + EYE_R[1] + 1, COLORS['eye'])
            return
        # 支持 tuple 传入自定义偏移（鼠标跟随用）
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
        """烟花棒"""
        self.px(fx, fy, COLORS['fw_fuse'])
        self.px(fx, fy + 1, COLORS['fw_fuse'])
        self.px(fx, fy + 2, COLORS['fw_fuse'])
        self.px(fx, fy + 3, COLORS['fw_fuse'])


# ─── 动画状态机 ───────────────────────────────────────────────
class StateMachine:
    def __init__(self):
        self.state = 'idle'
        self.frame = 0
        self.timer = 0.0
        self.duration = random.uniform(*STATE_DURATIONS['idle'])
        self.paused = False

    def update(self, dt):
        if self.paused:
            return
        self.timer += dt
        self.frame += 1
        if self.timer >= self.duration:
            self.transition()

    def transition(self):
        choices = [s for s in RANDOM_STATES if s != self.state]
        self.state = random.choice(choices)
        self.duration = random.uniform(*STATE_DURATIONS[self.state])
        self.timer = 0.0
        self.frame = 0

    def force_state(self, state, duration=None):
        """外部强制切换状态（Claude Code 联动用）"""
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


# ─── 主窗口 ───────────────────────────────────────────────────
class ClawdPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Clawd')
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', True)
        self.root.wm_attributes('-transparent', True)
        self.root.config(bg='systemTransparent')

        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_W, height=CANVAS_H,
            bg='systemTransparent',
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

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='🦀 Clawd Desktop Pet', state='disabled')
        self.menu.add_separator()
        self.menu.add_command(label='🎵 播放音乐', command=self._toggle_music)
        self.menu.add_command(label='⏭ 下一首', command=self._next_music)
        self.menu.add_separator()
        self.menu.add_command(label='🎆 放烟花', command=self._trigger_firework)
        self.menu.add_separator()
        self.menu.add_command(label='退出', command=self._quit)
        self.canvas.bind('<ButtonPress-2>', self._show_menu)
        self.canvas.bind('<Control-ButtonPress-1>', self._show_menu)

        # Clawd 在画布中的锚点（偏下，给烟花留头部空间）
        self.cx = 11
        self.cy = 18

        # Claude Code 联动: 启动 HTTP server
        self._claude_linked = False
        self._start_hook_server()

    def _start_hook_server(self):
        """启动 HTTP server 接收 Claude Code hooks"""
        pet = self

        class HookHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                path = self.path.strip('/')
                # 读取 body
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else b''

                # 根据路径切换状态
                state_map = {
                    'prompt':    'thinking',
                    'tool':      'cc_working',
                    'error':     'error',
                    'done':      'celebrate',
                }

                new_state = state_map.get(path)
                if new_state:
                    pet._claude_linked = True
                    pet.root.after(0, lambda: pet.sm.force_state(new_state))
                elif path == 'idle':
                    # 恢复随机状态
                    pet._claude_linked = False
                    pet.root.after(0, lambda: pet.sm.transition())
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'ok')

            def log_message(self, format, *args):
                pass  # 静默日志

        def run_server():
            try:
                server = HTTPServer(('127.0.0.1', HOOK_PORT), HookHandler)
                server.serve_forever()
            except OSError:
                pass  # 端口被占用就跳过

        t = threading.Thread(target=run_server, daemon=True)
        t.start()

    def _trigger_firework(self):
        """手动触发烟花"""
        self.sm.state = 'firework'
        self.sm.frame = 0
        self.sm.timer = 0.0
        self.sm.duration = random.uniform(*STATE_DURATIONS['firework'])
        self.particles.clear()

    # ─── 音乐 ─────────────────────────────────────────────────

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
        self._music_proc = subprocess.Popen(
            ['afplay', filepath],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self._music_playing = True
        self.menu.entryconfigure(2, label='⏹ 停止音乐')
        self._check_music_end()

    def _stop_music(self):
        if self._music_proc:
            self._music_proc.terminate()
            self._music_proc = None
        self._music_playing = False
        self.menu.entryconfigure(2, label='🎵 播放音乐')

    def _next_music(self):
        if not self._music_files:
            return
        self._music_index = (self._music_index + 1) % len(self._music_files)
        if self._music_playing:
            self._play_music()

    def _check_music_end(self):
        if self._music_proc and self._music_proc.poll() is not None:
            self._music_index = (self._music_index + 1) % len(self._music_files)
            self._play_music()
            return
        if self._music_playing:
            self.root.after(1000, self._check_music_end)

    def _quit(self):
        self._stop_music()
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
        self.menu.post(event.x_root, event.y_root)

    def _get_mouse_eye_offset(self, ox, oy):
        """根据鼠标位置计算眼睛偏移方向"""
        # Clawd 眼睛中心在屏幕上的绝对位置
        win_x = self.root.winfo_x()
        win_y = self.root.winfo_y()
        eye_center_x = win_x + (ox + 7) * SCALE  # 两眼中间
        eye_center_y = win_y + (oy + 1) * SCALE   # 眼睛行

        # 获取鼠标绝对位置
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()

        # 计算方向差
        diff_x = mouse_x - eye_center_x
        diff_y = mouse_y - eye_center_y

        # 转换成 -1/0/1 的偏移量，加一个死区避免抖动
        threshold = 40  # 像素
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

    # ─── 各状态绘制 ───────────────────────────────────────────

    def _draw_idle(self, f):
        ox, oy = self.cx, self.cy
        breath = round(math.sin(f * 0.15) * 0.5)
        oy += breath
        blink_cycle = f % 60
        if blink_cycle >= 56:
            eyes = 'blink'
        else:
            # 眼睛跟随鼠标
            eyes = self._get_mouse_eye_offset(ox, oy)

        # 身体微微倾斜（根据鼠标水平方向）
        lean = 0
        if isinstance(eyes, tuple) and eyes[0] != 0:
            lean = eyes[0]  # -1 或 1

        self.renderer.draw_body(ox + lean, oy)
        self.renderer.draw_eyes(ox + lean, oy, eyes)

    def _draw_walk(self, f, direction):
        ox, oy = self.cx, self.cy
        legs = LEGS_A if (f // 4) % 2 == 0 else LEGS_B
        eyes = 'forward'
        if f % 50 < 3:
            eyes = 'blink'
        self.renderer.draw_body(ox, oy, legs=legs)
        self.renderer.draw_eyes(ox, oy, eyes)
        self._move_window(direction * 2, 0)

    def _draw_dance(self, f):
        ox, oy = self.cx, self.cy
        # 缓动摇摆
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
        # 跳舞时脚底偶尔冒小粒子
        if f % 6 == 0:
            self.particles.emit(ox + 7, oy + 8, COLORS['star'], count=1,
                                speed=0.3, gravity=0.02, decay=0.04)

    def _draw_sleep(self, f):
        ox, oy = self.cx, self.cy + 3
        breath = round(math.sin(f * 0.08) * 0.5)
        oy += breath
        self.renderer.draw_body(ox, oy, curled=True)
        # 闭眼：不画眼睛，靠 Zzz 表达睡觉
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
        # 粒子爱心代替静态爱心
        if f % 12 == 0:
            self.particles.emit(ox + 14, oy - 1, COLORS['heart'], count=1,
                                speed=0.5, gravity=-0.01, decay=0.03)

    def _draw_jump(self, f):
        ox, oy = self.cx, self.cy
        jump_f = f % 24  # 拉长周期更平滑
        if jump_f < 4:
            # 蓄力压扁 (缓动)
            t = jump_f / 4
            squeeze = round(ease_in_out(t))
            oy += squeeze
            self.renderer.draw_body(ox, oy, squash=True)
            self.renderer.draw_eyes(ox, oy + 1, 'down')
        elif jump_f < 14:
            # 起跳 (缓出)
            t = (jump_f - 4) / 10
            height = ease_out(math.sin(t * math.pi)) * 5
            oy -= round(height)
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'forward')
            # 最高点闪光 + 粒子
            if 6 < jump_f < 10:
                self.renderer.draw_sparkle(ox + 7, oy - 1)
                if jump_f == 8:
                    self.particles.emit(ox + 7, oy + 8, COLORS['white'], count=3,
                                        speed=0.4, gravity=0.06, decay=0.05)
        else:
            # 落地 (缓入)
            t = (jump_f - 14) / 10
            if t < 0.3:
                oy += 1
                self.renderer.draw_body(ox, oy, squash=True)
                self.renderer.draw_eyes(ox, oy + 1, 'blink')
                # 落地粒子
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
        # 平滑弹跳
        t = (f % 20) / 20
        bounce = round(abs(math.sin(ease_in_out(t) * math.pi)) * 2)
        oy -= bounce
        self.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
        self.renderer.draw_eyes(ox, oy, 'happy')
        self.renderer.draw_blush(ox, oy)
        # 粒子爱心飘上去
        if f % 8 == 0:
            hx = ox + random.randint(2, 12)
            self.particles.emit(hx, oy - 1, COLORS['heart'], count=1,
                                speed=0.6, gravity=-0.02, decay=0.025)

    def _draw_eating(self, f):
        ox, oy = self.cx, self.cy
        phase = f % 120
        if phase < 30:
            # 发现饼干：缓动走过去
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
            # 碎屑粒子
            if bites > 0 and f % 5 == 0:
                self.particles.emit(ox + 2, oy + 4, COLORS['crumb'], count=1,
                                    speed=0.3, gravity=0.08, decay=0.04)
        else:
            # 吃完满足
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'happy')
            self.renderer.draw_blush(ox, oy)
            if f % 10 == 0:
                self.particles.emit(ox + 7, oy - 1, COLORS['heart'], count=1,
                                    speed=0.4, gravity=-0.01, decay=0.03)

    def _draw_excited(self, f):
        ox, oy = self.cx, self.cy
        # 缓动快跳
        t = (f % 15) / 15
        bounce = round(abs(math.sin(ease_out(t) * math.pi)) * 3)
        oy -= bounce
        sway = round(math.sin(f * 0.5) * 1)
        ox += sway
        claw = CLAW_BOTH_UP if math.sin(f * 0.4) > 0 else None
        self.renderer.draw_body(ox, oy, claw_extra=claw)
        self.renderer.draw_eyes(ox, oy, 'forward')
        # 闪光粒子
        if f % 4 == 0:
            self.particles.emit(ox + random.randint(3, 11), oy - 1,
                                [COLORS['star'], COLORS['star2'], COLORS['white']],
                                count=1, speed=0.5, gravity=-0.02, decay=0.04)

    def _draw_thinking(self, f):
        """Claude Code: 思考中 — 头顶思考气泡"""
        ox, oy = self.cx, self.cy
        breath = round(math.sin(f * 0.1) * 0.5)
        oy += breath
        self.renderer.draw_body(ox, oy)
        # 眼睛朝上看，在想事情
        eyes = 'up' if f % 40 > 5 else 'blink'
        self.renderer.draw_eyes(ox, oy, eyes)
        # 思考气泡：三个渐大的圆点 + 大气泡
        dot_phase = (f // 8) % 4
        if dot_phase >= 1:
            self.renderer.px(ox + 13, oy + 1, COLORS['zzz'])
        if dot_phase >= 2:
            self.renderer.px(ox + 15, oy - 1, COLORS['zzz'])
        if dot_phase >= 3:
            # 大气泡里三个跳动的点
            bx, by = ox + 15, oy - 4
            self.renderer.px(bx, by, COLORS['white'])
            self.renderer.px(bx + 1, by, COLORS['white'])
            self.renderer.px(bx + 2, by, COLORS['white'])
            self.renderer.px(bx, by - 1, COLORS['white'])
            self.renderer.px(bx + 1, by - 1, COLORS['white'])
            self.renderer.px(bx + 2, by - 1, COLORS['white'])
            self.renderer.px(bx + 3, by, COLORS['white'])
            self.renderer.px(bx - 1, by, COLORS['white'])
            # 跳动的三个黑点
            dot_i = (f // 4) % 3
            for i in range(3):
                dy = -1 if i == dot_i else 0
                self.renderer.px(bx + i, by + dy, COLORS['eye'])

    def _draw_cc_working(self, f):
        """Claude Code: 执行工具 — 快速打字"""
        ox, oy = self.cx, self.cy
        # 小幅快速点头
        nod = round(abs(math.sin(f * 0.5)) * 0.8)
        oy += nod
        self.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
        eyes = 'forward' if f % 30 > 3 else 'blink'
        self.renderer.draw_eyes(ox, oy, eyes)
        # 屏幕在前方
        self.renderer.draw_screen(ox - 7, oy + 1, f)
        # 飞溅的代码粒子
        if f % 4 == 0:
            self.particles.emit(ox - 4, oy + 2,
                                [COLORS['screen'], COLORS['screen2'], COLORS['white']],
                                count=1, speed=0.4, gravity=0.02, decay=0.05)

    def _draw_error(self, f):
        """Claude Code: 出错 — 冒烟 + 惊慌"""
        ox, oy = self.cx, self.cy
        # 身体微微颤抖
        shake = round(math.sin(f * 1.5) * 1)
        ox += shake
        self.renderer.draw_body(ox, oy)
        self.renderer.draw_eyes(ox, oy, 'forward')
        # 头顶冒烟粒子
        if f % 3 == 0:
            self.particles.emit(ox + 5 + random.randint(0, 4), oy - 1,
                                [COLORS['zzz'], COLORS['happy_eye']],
                                count=2, speed=0.3, gravity=-0.03, decay=0.03)
        # 头顶 ERROR 感叹号
        self.renderer.px(ox + 7, oy - 2, COLORS['fw_red'])
        self.renderer.px(ox + 7, oy - 3, COLORS['fw_red'])
        if f % 10 < 5:
            self.renderer.px(ox + 7, oy - 1, COLORS['fw_red'])
        # 汗滴
        self.renderer.draw_sweat(ox, oy, f)

    def _draw_celebrate(self, f):
        """Claude Code: 完成 — 开心弹跳 + 粒子庆祝"""
        ox, oy = self.cx, self.cy
        bounce = round(abs(math.sin(f * 0.4)) * 3)
        oy -= bounce
        self.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
        self.renderer.draw_eyes(ox, oy, 'happy')
        self.renderer.draw_blush(ox, oy)
        # 五彩粒子庆祝
        if f % 3 == 0:
            self.particles.emit(ox + random.randint(2, 12), oy - 1,
                                [COLORS['fw_gold'], COLORS['fw_pink'],
                                 COLORS['fw_cyan'], COLORS['heart'], COLORS['star']],
                                count=2, speed=0.8, gravity=0.03, decay=0.025)

    def _draw_firework(self, f):
        """烟花状态：点燃→上升→Claude logo 绽放→余韵→欢呼"""
        ox, oy = self.cx, self.cy
        dur_frames = round(self.sm.duration * FPS)
        t = f / max(dur_frames, 1)

        # 烟花爆心位置（画布上方中央）
        boom_x = ox + 7
        boom_y = 8

        if t < 0.12:
            # 阶段1：举烟花棒，引线冒火花
            pt = t / 0.12
            self.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_RIGHT)
            self.renderer.draw_eyes(ox, oy, 'forward')
            self.renderer.draw_firework_stick(ox + 14, oy - 3)
            if pt > 0.4 and f % 2 == 0:
                self.particles.emit(ox + 14, oy - 4, COLORS['fw_spark'], count=2,
                                    speed=0.3, gravity=0.01, decay=0.06)

        elif t < 0.25:
            # 阶段2：烟花弹上升
            pt = (t - 0.12) / 0.13
            rocket_y = round(lerp(oy - 4, boom_y, ease_out(pt)))
            self.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_RIGHT)
            self.renderer.draw_eyes(ox, oy, 'up')
            # 上升的弹体
            self.renderer.px(boom_x, rocket_y, COLORS['fw_red'])
            self.renderer.px(boom_x, rocket_y + 1, COLORS['fw_orange'])
            # 尾迹粒子
            if f % 2 == 0:
                self.particles.emit(boom_x, rocket_y + 2,
                                    [COLORS['fw_spark'], COLORS['fw_orange']],
                                    count=3, speed=0.4, gravity=0.06, decay=0.04)

        elif t < 0.50:
            # 阶段3：Claude logo 米字形绽放！
            pt = (t - 0.25) / 0.25
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'up')
            self.renderer.draw_blush(ox, oy)

            # 第一波：主爆炸，Claude logo 米字形
            if f == round(0.25 * dur_frames):
                # 橙色系 Claude logo 颜色
                logo_colors = [COLORS['fw_gold'], COLORS['fw_orange'],
                               COLORS['body'], COLORS['star'], COLORS['white']]
                self.particles.emit_claude_logo(
                    boom_x, boom_y, logo_colors,
                    speed=2.5, gravity=0.015, decay=0.012
                )

            # 第二波：延迟小爆炸，偏移位置
            if f == round(0.35 * dur_frames):
                self.particles.emit_claude_logo(
                    boom_x - 6, boom_y + 2,
                    [COLORS['fw_pink'], COLORS['fw_red'], COLORS['fw_gold']],
                    speed=1.5, gravity=0.02, decay=0.018
                )

            # 第三波
            if f == round(0.42 * dur_frames):
                self.particles.emit_claude_logo(
                    boom_x + 8, boom_y + 3,
                    [COLORS['fw_cyan'], COLORS['fw_green'], COLORS['white']],
                    speed=1.2, gravity=0.02, decay=0.02
                )

        elif t < 0.75:
            # 阶段4：余韵，粒子慢慢消散，零星闪光
            self.renderer.draw_body(ox, oy)
            self.renderer.draw_eyes(ox, oy, 'up')
            self.renderer.draw_blush(ox, oy)
            # 零星小火花缓缓下落
            if f % 6 == 0:
                sx = boom_x + random.randint(-8, 8)
                sy = random.randint(2, 10)
                self.particles.emit(sx, sy,
                                    [COLORS['fw_spark'], COLORS['fw_gold'], COLORS['fw_orange']],
                                    count=1, speed=0.15, gravity=0.03, decay=0.02)

        else:
            # 阶段5：欢呼，蹦跳 + 笑眼 + 爱心
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

    def _game_loop(self):
        self.renderer.clear()
        self.sm.update(1.0 / FPS)

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

        # 更新和绘制粒子
        self.particles.update()
        self.particles.draw(self.renderer)

        # 播放音乐时显示音符
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
