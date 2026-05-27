"""系统托盘图标（非 macOS 平台）"""

import threading

from .platform import _HAS_PYSTRAY, _HAS_PYNPUT, pystray, pynput_keyboard, Image, ImageDraw
from .constants import I18N


def _create_tray_icon_image():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    body_color = (224, 122, 95, 255)
    eye_color = (0, 0, 0, 255)
    draw.rectangle([4, 3, 11, 10], fill=body_color)
    draw.rectangle([2, 5, 3, 8], fill=body_color)
    draw.rectangle([12, 5, 13, 8], fill=body_color)
    for x in [5, 7, 9]:
        draw.rectangle([x, 11, x, 13], fill=body_color)
    draw.rectangle([6, 5, 6, 5], fill=eye_color)
    draw.rectangle([9, 5, 9, 5], fill=eye_color)
    return img


class TrayManager:
    def __init__(self, pet):
        self._pet = pet
        self._tray_icon = None
        self._hotkey_listener = None

    def start_tray(self):
        if not _HAS_PYSTRAY:
            return

        pet = self._pet

        def on_show_hide(icon, item):
            pet.root.after(0, pet.toggle_visibility)

        def on_firework(icon, item):
            pet.root.after(0, pet._trigger_firework)

        def on_quit(icon, item):
            pet.root.after(0, pet._quit)

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

    def stop_tray(self):
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass

    def start_hotkey(self):
        if not _HAS_PYNPUT:
            return

        pet = self._pet

        try:
            def on_activate():
                pet.root.after(0, pet.toggle_visibility)

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
            self._hotkey_listener = None

    def stop_hotkey(self):
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
