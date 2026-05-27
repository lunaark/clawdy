"""所有动画状态的绘制函数"""

import math
import random

from .constants import (
    COLORS, SCALE, FPS,
    LEGS_A, LEGS_B,
    CLAW_UP_RIGHT, CLAW_UP_LEFT, CLAW_BOTH_UP,
)
from .easing import ease_out, ease_in_out, lerp


def draw_idle(pet, f):
    ox, oy = pet.cx, pet.cy
    breath = round(math.sin(f * 0.15) * 0.5)
    oy += breath
    blink_cycle = f % 60
    if blink_cycle >= 56:
        eyes = 'blink'
    elif pet._is_looking_at_user:
        eyes = 'up'
    else:
        eyes = pet._get_mouse_eye_offset(ox, oy)

    lean = 0
    if pet._is_looking_at_user:
        lean = 1 if (f // 30) % 2 == 0 else -1
    elif isinstance(eyes, tuple) and eyes[0] != 0:
        lean = eyes[0]

    pet.renderer.draw_body(ox + lean, oy)
    pet.renderer.draw_eyes(ox + lean, oy, eyes)


def draw_walk(pet, f, direction):
    moving = not pet.sm.paused
    if moving and pet.renderer.scene == 'beach':
        nx = pet.cx + direction
        if nx < 0 or nx > 22:
            direction = -direction
            pet.sm.force_state('walk_right' if direction > 0 else 'walk_left')
            nx = pet.cx + direction
        pet.cx = nx
    ox, oy = pet.cx, pet.cy
    legs = LEGS_A if (f // 4) % 2 == 0 else LEGS_B
    eyes = 'forward'
    if f % 50 < 3:
        eyes = 'blink'
    pet.renderer.draw_body(ox, oy, legs=legs)
    pet.renderer.draw_eyes(ox, oy, eyes)
    if moving and pet.renderer.scene == 'home':
        pet._move_window(direction * 2, 0)


def draw_dance(pet, f):
    ox, oy = pet.cx, pet.cy
    t = (f % 30) / 30
    sway = round(math.sin(ease_in_out(t) * math.pi * 2) * 2)
    ox += sway
    bounce = round(abs(math.sin(f * 0.4)) * 2)
    oy -= bounce
    claw = CLAW_UP_RIGHT if math.sin(f * 0.3) > 0 else CLAW_UP_LEFT
    eyes = 'right' if sway > 0 else 'left'
    if f % 20 < 3:
        eyes = 'blink'
    pet.renderer.draw_body(ox, oy, claw_extra=claw)
    pet.renderer.draw_eyes(ox, oy, eyes)
    pet.renderer.draw_blush(ox, oy)
    if f % 6 == 0:
        pet.particles.emit(ox + 7, oy + 8, COLORS['star'], count=1,
                           speed=0.3, gravity=0.02, decay=0.04)


def draw_sleep(pet, f):
    ox, oy = pet.cx, pet.cy + 3
    breath = round(math.sin(f * 0.08) * 0.5)
    oy += breath
    pet.renderer.draw_body(ox, oy, curled=True)
    pet.renderer.draw_zzz(ox, oy, f)


def draw_wave(pet, f):
    ox, oy = pet.cx, pet.cy
    cycle = (f // 15) % 2
    claw = CLAW_UP_RIGHT if cycle == 0 else CLAW_UP_LEFT
    eyes = 'right' if cycle == 0 else 'left'
    sway = round(math.sin(f * 0.2) * 0.5)
    ox += sway
    pet.renderer.draw_body(ox, oy, claw_extra=claw)
    pet.renderer.draw_eyes(ox, oy, eyes)
    if f % 12 == 0:
        pet.particles.emit(ox + 14, oy - 1, COLORS['heart'], count=1,
                           speed=0.5, gravity=-0.01, decay=0.03)


def draw_jump(pet, f):
    ox, oy = pet.cx, pet.cy
    jump_f = f % 24
    if jump_f < 4:
        t = jump_f / 4
        squeeze = round(ease_in_out(t))
        oy += squeeze
        pet.renderer.draw_body(ox, oy, squash=True)
        pet.renderer.draw_eyes(ox, oy + 1, 'down')
    elif jump_f < 14:
        t = (jump_f - 4) / 10
        height = ease_out(math.sin(t * math.pi)) * 5
        oy -= round(height)
        pet.renderer.draw_body(ox, oy)
        pet.renderer.draw_eyes(ox, oy, 'forward')
        if 6 < jump_f < 10:
            pet.renderer.draw_sparkle(ox + 7, oy - 1)
            if jump_f == 8:
                pet.particles.emit(ox + 7, oy + 8, COLORS['white'], count=3,
                                   speed=0.4, gravity=0.06, decay=0.05)
    else:
        t = (jump_f - 14) / 10
        if t < 0.3:
            oy += 1
            pet.renderer.draw_body(ox, oy, squash=True)
            pet.renderer.draw_eyes(ox, oy + 1, 'blink')
            if jump_f == 15:
                pet.particles.emit(ox + 4, oy + 8, COLORS['zzz'], count=2,
                                   speed=0.3, spread=1.0, gravity=0.03, decay=0.04)
                pet.particles.emit(ox + 10, oy + 8, COLORS['zzz'], count=2,
                                   speed=0.3, spread=1.0, gravity=0.03, decay=0.04)
        else:
            pet.renderer.draw_body(ox, oy)
            pet.renderer.draw_eyes(ox, oy, 'forward')


def draw_working(pet, f):
    ox, oy = pet.cx, pet.cy
    pet.renderer.draw_screen(ox - 7, oy + 1, f)
    breath = round(math.sin(f * 0.12) * 0.3)
    pet.renderer.draw_body(ox, oy + breath)
    eyes = 'left'
    if f % 40 < 3:
        eyes = 'blink'
    pet.renderer.draw_eyes(ox, oy + breath, eyes)
    if f % 30 < 20:
        pet.renderer.draw_sweat(ox, oy + breath, f)


def draw_happy(pet, f):
    ox, oy = pet.cx, pet.cy
    t = (f % 20) / 20
    bounce = round(abs(math.sin(ease_in_out(t) * math.pi)) * 2)
    oy -= bounce
    pet.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
    pet.renderer.draw_eyes(ox, oy, 'happy')
    pet.renderer.draw_blush(ox, oy)
    if f % 8 == 0:
        hx = ox + random.randint(2, 12)
        pet.particles.emit(hx, oy - 1, COLORS['heart'], count=1,
                           speed=0.6, gravity=-0.02, decay=0.025)


def draw_eating(pet, f):
    ox, oy = pet.cx, pet.cy
    phase = f % 120
    if phase < 30:
        t = ease_out(phase / 30)
        cookie_x = round(lerp(ox - 6, ox - 3, t))
        pet.renderer.draw_cookie(cookie_x, oy + 3, bites=0)
        pet.renderer.draw_body(ox, oy)
        pet.renderer.draw_eyes(ox, oy, 'left')
    elif phase < 90:
        bites = (phase - 30) // 20
        pet.renderer.draw_cookie(ox + 1, oy + 2, bites=min(bites, 3))
        pet.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_LEFT)
        eyes = 'blink' if (phase // 8) % 3 == 0 else 'down'
        pet.renderer.draw_eyes(ox, oy, eyes)
        if bites > 0 and f % 5 == 0:
            pet.particles.emit(ox + 2, oy + 4, COLORS['crumb'], count=1,
                               speed=0.3, gravity=0.08, decay=0.04)
    else:
        pet.renderer.draw_body(ox, oy)
        pet.renderer.draw_eyes(ox, oy, 'happy')
        pet.renderer.draw_blush(ox, oy)
        if f % 10 == 0:
            pet.particles.emit(ox + 7, oy - 1, COLORS['heart'], count=1,
                               speed=0.4, gravity=-0.01, decay=0.03)


def draw_excited(pet, f):
    ox, oy = pet.cx, pet.cy
    t = (f % 15) / 15
    bounce = round(abs(math.sin(ease_out(t) * math.pi)) * 3)
    oy -= bounce
    sway = round(math.sin(f * 0.5) * 1)
    ox += sway
    claw = CLAW_BOTH_UP if math.sin(f * 0.4) > 0 else None
    pet.renderer.draw_body(ox, oy, claw_extra=claw)
    pet.renderer.draw_eyes(ox, oy, 'forward')
    if f % 4 == 0:
        pet.particles.emit(ox + random.randint(3, 11), oy - 1,
                           [COLORS['star'], COLORS['star2'], COLORS['white']],
                           count=1, speed=0.5, gravity=-0.02, decay=0.04)


def draw_thinking(pet, f):
    ox, oy = pet.cx, pet.cy
    breath = round(math.sin(f * 0.1) * 0.5)
    oy += breath
    pet.renderer.draw_body(ox, oy)
    eyes = 'up' if f % 40 > 5 else 'blink'
    pet.renderer.draw_eyes(ox, oy, eyes)
    dot_phase = (f // 8) % 4
    if dot_phase >= 1:
        pet.renderer.px(ox + 13, oy + 1, COLORS['zzz'])
    if dot_phase >= 2:
        pet.renderer.px(ox + 15, oy - 1, COLORS['zzz'])
    if dot_phase >= 3:
        bx, by = ox + 15, oy - 4
        pet.renderer.px(bx, by, COLORS['white'])
        pet.renderer.px(bx + 1, by, COLORS['white'])
        pet.renderer.px(bx + 2, by, COLORS['white'])
        pet.renderer.px(bx, by - 1, COLORS['white'])
        pet.renderer.px(bx + 1, by - 1, COLORS['white'])
        pet.renderer.px(bx + 2, by - 1, COLORS['white'])
        pet.renderer.px(bx + 3, by, COLORS['white'])
        pet.renderer.px(bx - 1, by, COLORS['white'])
        dot_i = (f // 4) % 3
        for i in range(3):
            dy = -1 if i == dot_i else 0
            pet.renderer.px(bx + i, by + dy, COLORS['eye'])


def draw_cc_working(pet, f):
    ox, oy = pet.cx, pet.cy
    breath = round(math.sin(f * 0.1) * 0.5)
    oy += breath
    pet.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
    eyes = 'forward' if f % 30 > 3 else 'blink'
    pet.renderer.draw_eyes(ox, oy, eyes)
    pet.renderer.draw_screen(ox - 7, oy + 1, f)
    if f % 4 == 0:
        pet.particles.emit(ox - 4, oy + 2,
                           [COLORS['screen'], COLORS['screen2'], COLORS['white']],
                           count=1, speed=0.4, gravity=0.02, decay=0.05)


def draw_error(pet, f):
    ox, oy = pet.cx, pet.cy
    shake = round(math.sin(f * 1.5) * 1)
    ox += shake
    pet.renderer.draw_body(ox, oy)
    pet.renderer.draw_eyes(ox, oy, 'forward')
    if f % 3 == 0:
        pet.particles.emit(ox + 5 + random.randint(0, 4), oy - 1,
                           [COLORS['zzz'], COLORS['happy_eye']],
                           count=2, speed=0.3, gravity=-0.03, decay=0.03)
    pet.renderer.px(ox + 7, oy - 2, COLORS['fw_red'])
    pet.renderer.px(ox + 7, oy - 3, COLORS['fw_red'])
    if f % 10 < 5:
        pet.renderer.px(ox + 7, oy - 1, COLORS['fw_red'])
    pet.renderer.draw_sweat(ox, oy, f)


def draw_celebrate(pet, f):
    ox, oy = pet.cx, pet.cy
    breath = round(math.sin(f * 0.1) * 0.5)
    oy += breath
    pet.renderer.draw_body(ox, oy)
    pet.renderer.draw_eyes(ox, oy, 'forward')
    pet.renderer.draw_blush(ox, oy)
    if f % 3 == 0:
        pet.particles.emit(ox + random.randint(2, 12), oy - 1,
                           [COLORS['fw_gold'], COLORS['fw_pink'],
                            COLORS['fw_cyan'], COLORS['heart'], COLORS['star']],
                           count=2, speed=0.8, gravity=0.03, decay=0.025)


def draw_firework(pet, f):
    ox, oy = pet.cx, pet.cy
    dur_frames = round(pet.sm.duration * FPS)
    t = f / max(dur_frames, 1)

    boom_x = ox + 7
    boom_y = 8

    if t < 0.12:
        pt = t / 0.12
        pet.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_RIGHT)
        pet.renderer.draw_eyes(ox, oy, 'forward')
        pet.renderer.draw_firework_stick(ox + 14, oy - 3)
        if pt > 0.4 and f % 2 == 0:
            pet.particles.emit(ox + 14, oy - 4, COLORS['fw_spark'], count=2,
                               speed=0.3, gravity=0.01, decay=0.06)

    elif t < 0.25:
        pt = (t - 0.12) / 0.13
        rocket_y = round(lerp(oy - 4, boom_y, ease_out(pt)))
        pet.renderer.draw_body(ox, oy, claw_extra=CLAW_UP_RIGHT)
        pet.renderer.draw_eyes(ox, oy, 'up')
        pet.renderer.px(boom_x, rocket_y, COLORS['fw_red'])
        pet.renderer.px(boom_x, rocket_y + 1, COLORS['fw_orange'])
        if f % 2 == 0:
            pet.particles.emit(boom_x, rocket_y + 2,
                               [COLORS['fw_spark'], COLORS['fw_orange']],
                               count=3, speed=0.4, gravity=0.06, decay=0.04)

    elif t < 0.50:
        pt = (t - 0.25) / 0.25
        pet.renderer.draw_body(ox, oy)
        pet.renderer.draw_eyes(ox, oy, 'up')
        pet.renderer.draw_blush(ox, oy)

        if f == round(0.25 * dur_frames):
            logo_colors = [COLORS['fw_gold'], COLORS['fw_orange'],
                           COLORS['body'], COLORS['star'], COLORS['white']]
            pet.particles.emit_claude_logo(
                boom_x, boom_y, logo_colors,
                speed=2.5, gravity=0.015, decay=0.012
            )

        if f == round(0.35 * dur_frames):
            pet.particles.emit_claude_logo(
                boom_x - 6, boom_y + 2,
                [COLORS['fw_pink'], COLORS['fw_red'], COLORS['fw_gold']],
                speed=1.5, gravity=0.02, decay=0.018
            )

        if f == round(0.42 * dur_frames):
            pet.particles.emit_claude_logo(
                boom_x + 8, boom_y + 3,
                [COLORS['fw_cyan'], COLORS['fw_green'], COLORS['white']],
                speed=1.2, gravity=0.02, decay=0.02
            )

    elif t < 0.75:
        pet.renderer.draw_body(ox, oy)
        pet.renderer.draw_eyes(ox, oy, 'up')
        pet.renderer.draw_blush(ox, oy)
        if f % 6 == 0:
            sx = boom_x + random.randint(-8, 8)
            sy = random.randint(2, 10)
            pet.particles.emit(sx, sy,
                               [COLORS['fw_spark'], COLORS['fw_gold'], COLORS['fw_orange']],
                               count=1, speed=0.15, gravity=0.03, decay=0.02)

    else:
        pt = (t - 0.75) / 0.25
        bounce = round(abs(math.sin(pt * math.pi * 4)) * 2)
        oy -= bounce
        pet.renderer.draw_body(ox, oy, claw_extra=CLAW_BOTH_UP)
        pet.renderer.draw_eyes(ox, oy, 'happy')
        pet.renderer.draw_blush(ox, oy)
        if f % 8 == 0:
            pet.particles.emit(ox + 7, oy - 1, COLORS['heart'], count=1,
                               speed=0.5, gravity=-0.02, decay=0.03)


DRAW_MAP = {
    'idle':       lambda pet, f: draw_idle(pet, f),
    'walk_left':  lambda pet, f: draw_walk(pet, f, -1),
    'walk_right': lambda pet, f: draw_walk(pet, f, 1),
    'dance':      lambda pet, f: draw_dance(pet, f),
    'sleep':      lambda pet, f: draw_sleep(pet, f),
    'wave':       lambda pet, f: draw_wave(pet, f),
    'jump':       lambda pet, f: draw_jump(pet, f),
    'working':    lambda pet, f: draw_working(pet, f),
    'happy':      lambda pet, f: draw_happy(pet, f),
    'eating':     lambda pet, f: draw_eating(pet, f),
    'excited':    lambda pet, f: draw_excited(pet, f),
    'firework':   lambda pet, f: draw_firework(pet, f),
    'thinking':   lambda pet, f: draw_thinking(pet, f),
    'cc_working': lambda pet, f: draw_cc_working(pet, f),
    'error':      lambda pet, f: draw_error(pet, f),
    'celebrate':  lambda pet, f: draw_celebrate(pet, f),
}
