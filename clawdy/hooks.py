"""Claude Code HTTP hook server"""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from .constants import HOOK_PORT, FPS


def start_hook_server(pet):
    class HookHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            path = self.path.strip('/')
            length = int(self.headers.get('Content-Length', 0))
            if length:
                self.rfile.read(length)

            state_map = {
                'prompt':    'thinking',
                'tool':      'cc_working',
                'error':     'error',
                'done':      'celebrate',
            }

            if path == 'toggle':
                pet.root.after(0, pet.toggle_visibility)
            elif path == 'show':
                pet.root.after(0, pet._show)
            elif path == 'hide':
                pet.root.after(0, pet._hide)
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
