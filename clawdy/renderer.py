"""像素渲染器 + 沙滩背景绘制"""

import math

from .constants import (
    SCALE, COLORS, BODY, BODY_CURLED, EYE_L, EYE_R, COOKIE,
    SKY_ROWS, SAND_PATTERN,
)


class PixelRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.S = SCALE
        self._bg_drawn = False
        self.scene = 'home'

    def clear(self):
        self.canvas.delete('sprite')

    def set_scene(self, scene):
        if scene == self.scene:
            return
        self.scene = scene
        self.canvas.delete('bg')
        self.canvas.delete('sea')
        self._bg_drawn = False

    def draw_background(self, frame):
        if self.scene != 'beach':
            return
        if not self._bg_drawn:
            s = self.S
            for y, color in enumerate(SKY_ROWS):
                self.canvas.create_rectangle(
                    0, y * s, 36 * s, (y + 1) * s,
                    fill=color, outline='', tags='bg',
                )
            for dy, row_colors in enumerate(SAND_PATTERN):
                y = 22 + dy
                for x, color in enumerate(row_colors):
                    self.canvas.create_rectangle(
                        x * s, y * s, (x + 1) * s, (y + 1) * s,
                        fill=color, outline='', tags='bg',
                    )
            sun_cx, sun_cy = 8, 14
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    self.canvas.create_rectangle(
                        (sun_cx + dx) * s, (sun_cy + dy) * s,
                        (sun_cx + dx + 1) * s, (sun_cy + dy + 1) * s,
                        fill=COLORS['sun_core'], outline='', tags='bg',
                    )
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                self.canvas.create_rectangle(
                    (sun_cx + dx) * s, (sun_cy + dy) * s,
                    (sun_cx + dx + 1) * s, (sun_cy + dy + 1) * s,
                    fill=COLORS['sun_glow'], outline='', tags='bg',
                )
            self._bg_drawn = True

        self.canvas.delete('sea')
        s = self.S
        sea_colors = [COLORS['sea_foam'], COLORS['sea_light'], COLORS['sea_mid'], COLORS['sea_deep']]
        for dy in range(4):
            y = 18 + dy
            base_color = sea_colors[dy]
            for x in range(36):
                wave = math.sin(frame * 0.1 + x * 0.7)
                if dy == 0 and wave > 0.3:
                    color = COLORS['sea_foam']
                elif dy <= 1 and wave > 0.6:
                    color = COLORS['sea_foam']
                else:
                    color = base_color
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
        bar_w = 16
        bar_h = 2
        bg_color = '#4A3024'
        fill_color = '#E07A5F' if progress < 1.0 else '#D4A94B'
        border_color = '#2A160C'
        filled = round(bar_w * min(progress, 1.0))

        for x in range(bar_w + 2):
            self.px(sx + x, sy, border_color)
            self.px(sx + x, sy + bar_h + 1, border_color)
        for y in range(bar_h + 2):
            self.px(sx, sy + y, border_color)
            self.px(sx + bar_w + 1, sy + y, border_color)

        for y in range(bar_h):
            for x in range(bar_w):
                self.px(sx + 1 + x, sy + 1 + y, bg_color)

        for y in range(bar_h):
            for x in range(filled):
                self.px(sx + 1 + x, sy + 1 + y, fill_color)

        label = f'{done}/{total}'
        tx = (sx + 1 + bar_w / 2) * self.S
        ty = (sy + bar_h + 3) * self.S
        self.canvas.create_text(
            tx, ty, text=label,
            font=('Helvetica', 7, 'bold'), fill='#F5E9D4',
            anchor='center', tags='sprite'
        )

        if progress >= 1.0 and (frame // 10) % 2 == 0:
            self.px(sx + bar_w + 3, sy, COLORS['star'])
            self.px(sx + bar_w + 3, sy + 1, COLORS['star2'])
