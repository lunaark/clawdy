"""音乐播放（跨平台）"""

import glob
import os
import random
import subprocess

from .platform import IS_MACOS, IS_WINDOWS, _HAS_PYGAME, pygame
from .constants import I18N

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'music')


class MusicPlayer:
    def __init__(self, root, menu):
        self._root = root
        self._menu = menu
        self._proc = None
        self._playing = False
        self._files = []
        self._index = 0
        self._scan()

    def _scan(self):
        self._files = sorted(
            glob.glob(os.path.join(MUSIC_DIR, '*.mp3')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.m4a')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.wav')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.aac')) +
            glob.glob(os.path.join(MUSIC_DIR, '*.flac'))
        )
        if self._files:
            random.shuffle(self._files)

    @property
    def playing(self):
        return self._playing

    def toggle(self):
        if self._playing:
            self.stop()
        else:
            self.play()

    def play(self):
        if not self._files:
            self._scan()
        if not self._files:
            return
        self.stop()
        filepath = self._files[self._index % len(self._files)]

        if IS_MACOS:
            self._proc = subprocess.Popen(
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
            self._proc = subprocess.Popen(
                ['cmd', '/c', 'start', '/min', '', filepath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                shell=False,
            )
        else:
            for player in ['mpv', 'aplay', 'paplay']:
                try:
                    self._proc = subprocess.Popen(
                        [player, filepath],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    break
                except FileNotFoundError:
                    continue

        self._playing = True
        self._menu.entryconfigure(0, label=I18N['stop_music'])
        self._check_end()

    def stop(self):
        if IS_WINDOWS and _HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        if self._proc:
            self._proc.terminate()
            self._proc = None
        self._playing = False
        self._menu.entryconfigure(0, label=I18N['play_music'])

    def next_track(self):
        if not self._files:
            return
        self._index = (self._index + 1) % len(self._files)
        if self._playing:
            self.play()

    def _check_end(self):
        if IS_WINDOWS and _HAS_PYGAME:
            if not pygame.mixer.music.get_busy():
                self._index = (self._index + 1) % len(self._files)
                self.play()
                return
        elif self._proc and self._proc.poll() is not None:
            self._index = (self._index + 1) % len(self._files)
            self.play()
            return
        if self._playing:
            self._root.after(1000, self._check_end)
