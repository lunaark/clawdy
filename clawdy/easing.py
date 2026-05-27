"""缓动函数"""


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


def lerp(a, b, t):
    return a + (b - a) * t
