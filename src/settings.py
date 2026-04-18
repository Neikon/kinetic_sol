# settings.py
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

from dataclasses import dataclass
import secrets

from gi.repository import Gio

SCHEMA_ID = 'dev.neikon.kinetic_sol'
DEFAULT_PORT = 39721
MIN_PORT = 1024
MAX_PORT = 65535


@dataclass(slots=True)
class SettingsSnapshot:
    listen_enabled: bool
    start_listener_on_launch: bool
    listen_port: int
    shared_token: str


class AppSettings:
    def __init__(self):
        self._settings = Gio.Settings.new(SCHEMA_ID)

    def ensure_token(self) -> str:
        token = self._settings.get_string('shared-token').strip()
        if token:
            return token

        token = secrets.token_urlsafe(24)
        self._settings.set_string('shared-token', token)
        return token

    def snapshot(self) -> SettingsSnapshot:
        return SettingsSnapshot(
            listen_enabled=self._settings.get_boolean('listen-enabled'),
            start_listener_on_launch=self._settings.get_boolean('start-listener-on-launch'),
            listen_port=self._clamp_port(self._settings.get_int('listen-port')),
            shared_token=self.ensure_token(),
        )

    def save(self, snapshot: SettingsSnapshot) -> SettingsSnapshot:
        snapshot = SettingsSnapshot(
            listen_enabled=snapshot.listen_enabled,
            start_listener_on_launch=snapshot.start_listener_on_launch,
            listen_port=self._clamp_port(snapshot.listen_port),
            shared_token=snapshot.shared_token.strip() or self.ensure_token(),
        )
        self._settings.set_boolean('listen-enabled', snapshot.listen_enabled)
        self._settings.set_boolean('start-listener-on-launch', snapshot.start_listener_on_launch)
        self._settings.set_int('listen-port', snapshot.listen_port)
        self._settings.set_string('shared-token', snapshot.shared_token)
        return snapshot

    def _clamp_port(self, port: int) -> int:
        return max(MIN_PORT, min(MAX_PORT, port))
