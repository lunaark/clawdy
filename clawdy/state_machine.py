"""动画状态机"""

import random

from .constants import STATE_DURATIONS, RANDOM_STATES


class StateMachine:
    MOOD_WEIGHTS = {
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
        self.mood = 0
        self.excluded_states = set()

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
