"""粒子系统"""

import math
import random


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
