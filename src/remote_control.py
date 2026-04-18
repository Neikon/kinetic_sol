# remote_control.py
#
# Copyright 2026 neikon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from urllib.parse import urlparse

from gi.repository import GLib

POWER_OFF_PATH = '/api/v1/poweroff'
STATUS_PATH = '/api/v1/status'
LEGACY_POWER_OFF_PATH = '/v1/poweroff'
LEGACY_STATUS_PATH = '/v1/status'


class _CommandHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        request_handler_class,
        token,
        on_poweroff_request,
        on_status_request,
        on_event,
    ):
        super().__init__(server_address, request_handler_class)
        self.token = token
        self.on_poweroff_request = on_poweroff_request
        self.on_status_request = on_status_request
        self.on_event = on_event


class _CommandHandler(BaseHTTPRequestHandler):
    server_version = 'KineticSOL/0.1'

    def do_GET(self):
        request_path = urlparse(self.path).path
        if request_path not in {STATUS_PATH, LEGACY_STATUS_PATH}:
            self._send_json(404, {'ok': False, 'message': 'Not found.'})
            return

        client_host = self.client_address[0]
        if not self._is_authorized():
            self.server.on_event(
                'request-rejected',
                f'Rejected remote status request from {client_host}: invalid token.',
            )
            self._send_json(401, {'ok': False, 'code': 'unauthorized', 'message': 'Invalid bearer token.'})
            return

        result = self.server.on_status_request(client_host)
        self._send_json(200, result)

    def do_POST(self):
        request_path = urlparse(self.path).path
        if request_path not in {POWER_OFF_PATH, LEGACY_POWER_OFF_PATH}:
            self._send_json(404, {'ok': False, 'message': 'Not found.'})
            return

        client_host = self.client_address[0]
        if not self._is_authorized():
            self.server.on_event(
                'request-rejected',
                f'Rejected remote request from {client_host}: invalid token.',
            )
            self._send_json(401, {'ok': False, 'code': 'unauthorized', 'message': 'Invalid bearer token.'})
            return

        self._discard_request_body()
        self.server.on_event(
            'request-received',
            f'Received remote power-off request from {client_host}.',
        )
        result = self.server.on_poweroff_request(client_host)
        status_code = 200 if result['ok'] else 503
        self._send_json(status_code, result)

    def log_message(self, format, *args):
        return

    def _is_authorized(self) -> bool:
        header = self.headers.get('Authorization', '')
        return header == f'Bearer {self.server.token}'

    def _discard_request_body(self):
        content_length = self.headers.get('Content-Length')
        if content_length is None:
            return

        try:
            length = int(content_length)
        except ValueError:
            return

        if length > 0:
            self.rfile.read(length)

    def _send_json(self, status_code: int, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            return


class RemoteCommandServer:
    def __init__(self, on_poweroff_request, on_status_request, on_event):
        self._on_poweroff_request = on_poweroff_request
        self._on_status_request = on_status_request
        self._on_event = on_event
        self._server = None
        self._thread = None
        self.port = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, port: int, token: str):
        self.stop()
        self._server = _CommandHTTPServer(
            ('0.0.0.0', port),
            _CommandHandler,
            token,
            self._dispatch_poweroff,
            self._dispatch_status,
            self._dispatch_event,
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name='kineticsol-http-listener',
            daemon=True,
        )
        self._thread.start()
        self.port = port
        self._dispatch_event('listener-started', f'Listening on port {port}.')

    def stop(self):
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)

        self._server = None
        self._thread = None
        self.port = None
        self._dispatch_event('listener-stopped', 'Listener stopped.')

    def _dispatch_event(self, event_code: str, message: str):
        GLib.idle_add(self._on_event, event_code, message)

    def _dispatch_poweroff(self, client_host: str):
        return self._dispatch_to_main_loop(lambda: self._on_poweroff_request(client_host))

    def _dispatch_status(self, client_host: str):
        return self._dispatch_to_main_loop(lambda: self._on_status_request(client_host))

    def _dispatch_to_main_loop(self, callback):
        result = {}
        completed = threading.Event()

        def invoke():
            result.update(callback())
            completed.set()
            return False

        GLib.idle_add(invoke)
        if not completed.wait(timeout=15):
            return {
                'ok': False,
                'code': 'timeout',
                'message': 'Timed out waiting for the UI thread to process the request.',
            }

        return result
