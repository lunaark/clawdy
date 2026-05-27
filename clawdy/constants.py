"""常量、颜色、像素数据、国际化"""

import locale
import math

from .platform import IS_MACOS

# ─── 国际化 ───────────────────────────────────────────────────
def _is_chinese():
    if IS_MACOS:
        try:
            import subprocess as _sp
            out = _sp.check_output(
                ['defaults', 'read', '-g', 'AppleLanguages'],
                stderr=_sp.DEVNULL, timeout=2,
            ).decode()
            return 'zh' in out.split(')')[0]
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

# ─── 渲染常量 ─────────────────────────────────────────────────
SCALE = 6
FPS = 15
INTERVAL = 1000 // FPS

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
    'fw_red':    '#FF4444',
    'fw_gold':   '#FFD700',
    'fw_pink':   '#FF69B4',
    'fw_cyan':   '#00E5FF',
    'fw_green':  '#66FF66',
    'fw_orange': '#FFA500',
    'fw_fuse':   '#AA8855',
    'fw_spark':  '#FFEE88',
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
PX_BG          = '#F5E9D4'
PX_BG_SOFT     = '#EADCC0'
PX_BORDER      = '#5A3A2A'
PX_BORDER_SOFT = '#A07050'
PX_ACCENT      = '#E07A5F'
PX_ACCENT_DARK = '#C0604A'
PX_TEXT        = '#3A2418'
PX_TEXT_SOFT   = '#7A5A44'
PX_INPUT_BG    = '#FFF8E7'
PX_DANGER      = '#C94A3A'
PX_SUCCESS     = '#6BAE5F'
PX_GOLD        = '#D4A94B'
_PX_FAMILY = 'Menlo' if IS_MACOS else 'Consolas'
PX_FONT        = (_PX_FAMILY, 11)
PX_FONT_B      = (_PX_FAMILY, 11, 'bold')
PX_FONT_TITLE  = (_PX_FAMILY, 14, 'bold')
PX_FONT_BIG    = (_PX_FAMILY, 22, 'bold')

# ─── 像素数据 ────────────────────────────────────────────────
BODY = [
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],
]

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

# ─── 动画状态 ────────────────────────────────────────────────
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
    'thinking':   (3, 10),
    'cc_working': (3, 10),
    'error':      (3, 5),
    'celebrate':  (3, 5),
}

RANDOM_STATES = [
    'idle', 'walk_left', 'walk_right', 'dance', 'sleep',
    'wave', 'jump', 'working', 'happy', 'eating', 'excited', 'firework',
]

STATES = list(STATE_DURATIONS.keys())

CANVAS_W = 36 * SCALE
CANVAS_H = 30 * SCALE

# ─── Claude Code 联动 ────────────────────────────────────────
HOOK_PORT = 18900

CLAUDE_STATE_MAP = {
    'prompt':    'thinking',
    'tool':      'working',
    'error':     'error',
    'done':      'celebrate',
    'idle':      None,
}

# ─── 沙滩背景预计算 ──────────────────────────────────────────
def _build_sky_gradient():
    rows = []
    stops = [
        (0.00, (107, 76, 154)),
        (0.30, (212, 99, 122)),
        (0.60, (240, 147, 110)),
        (1.00, (255, 179, 71)),
    ]
    for y in range(18):
        t = y / 17
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

SAND_PATTERN = []
for _y in range(8):
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
