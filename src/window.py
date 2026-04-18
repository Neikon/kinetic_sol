# window.py
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

from datetime import datetime
from gettext import gettext as _
import ipaddress
from secrets import token_urlsafe
import shlex
import socket

from gi.repository import Adw, Gio, GLib, Gtk

from .power import Login1PowerController
from .remote_control import (
    LEGACY_POWER_OFF_PATH,
    LEGACY_STATUS_PATH,
    POWER_OFF_PATH,
    RemoteCommandServer,
    STATUS_PATH,
)
from .settings import AppSettings, SettingsSnapshot

@Gtk.Template(resource_path='/dev/neikon/kinetic_sol/window.ui')
class KineticsolWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KineticsolWindow'

    toast_overlay = Gtk.Template.Child()
    listen_switch = Gtk.Template.Child()
    autostart_switch = Gtk.Template.Child()
    port_spin = Gtk.Template.Child()
    token_entry = Gtk.Template.Child()
    copy_token_button = Gtk.Template.Child()
    base_url_row = Gtk.Template.Child()
    copy_base_url_button = Gtk.Template.Child()
    endpoint_row = Gtk.Template.Child()
    copy_curl_button = Gtk.Template.Child()
    diagnostics_group = Gtk.Template.Child()
    listener_state_row = Gtk.Template.Child()
    power_state_row = Gtk.Template.Child()
    last_request_row = Gtk.Template.Child()
    save_button = Gtk.Template.Child()
    rotate_token_button = Gtk.Template.Child()
    refresh_power_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._settings = AppSettings()
        self._power_controller = Login1PowerController()
        self._power_capability = None
        self._show_diagnostics = True
        self._listener = RemoteCommandServer(
            self._handle_remote_poweroff,
            self._handle_remote_status,
            self._handle_listener_event,
        )
        self._create_toggle_action(
            'show-diagnostics',
            self._on_show_diagnostics_changed,
            GLib.Variant.new_boolean(True),
        )

        self.save_button.connect('clicked', self._on_save_clicked)
        self.rotate_token_button.connect('clicked', self._on_rotate_token_clicked)
        self.copy_token_button.connect('clicked', self._on_copy_token_clicked)
        self.copy_base_url_button.connect('clicked', self._on_copy_base_url_clicked)
        self.copy_curl_button.connect('clicked', self._on_copy_curl_clicked)
        self.refresh_power_button.connect('clicked', self._on_refresh_power_clicked)
        self.connect('close-request', self._on_close_request)

        snapshot = self._settings.snapshot()
        self._show_diagnostics = snapshot.show_diagnostics
        self._apply_snapshot_to_form(snapshot)
        self._set_diagnostics_visible(snapshot.show_diagnostics)
        self._update_endpoint_row(snapshot.listen_port)
        self._update_listener_state(_('Configuration loaded. Apply to restart the listener.'))
        self._update_last_request(_('No remote commands received yet.'))
        self._refresh_power_state()

        if snapshot.listen_enabled and snapshot.start_listener_on_launch:
            self._apply_runtime_configuration(snapshot, show_toast=False)

    def _apply_snapshot_to_form(self, snapshot: SettingsSnapshot):
        self.listen_switch.set_active(snapshot.listen_enabled)
        self.autostart_switch.set_active(snapshot.start_listener_on_launch)
        self.port_spin.set_value(snapshot.listen_port)
        self.token_entry.set_text(snapshot.shared_token)

    def _read_form_snapshot(self) -> SettingsSnapshot:
        token = self.token_entry.get_text().strip() or self._settings.ensure_token()
        self.token_entry.set_text(token)
        return SettingsSnapshot(
            listen_enabled=self.listen_switch.get_active(),
            start_listener_on_launch=self.autostart_switch.get_active(),
            show_diagnostics=self._show_diagnostics,
            listen_port=int(self.port_spin.get_value()),
            shared_token=token,
        )

    def _on_save_clicked(self, _button):
        snapshot = self._settings.save(self._read_form_snapshot())
        self._apply_runtime_configuration(snapshot, show_toast=True)

    def _on_rotate_token_clicked(self, _button):
        token = token_urlsafe(24)
        self.token_entry.set_text(token)
        self._show_toast(_('Token rotated. Save to apply it to the listener.'))

    def _on_copy_token_clicked(self, _button):
        token = self.token_entry.get_text().strip()
        if not token:
            self._show_toast(_('There is no token to copy.'))
            return

        self._copy_to_clipboard(token)
        self._show_toast(_('Token copied to clipboard.'))

    def _on_copy_base_url_clicked(self, _button):
        base_url = self._get_primary_android_base_url(int(self.port_spin.get_value()))
        if base_url is None:
            self._show_toast(_('No base URL could be detected automatically.'))
            return

        self._copy_to_clipboard(base_url)
        self._show_toast(_('Base URL copied to clipboard.'))

    def _on_copy_curl_clicked(self, _button):
        curl_command = self._build_status_curl_command(int(self.port_spin.get_value()))
        if curl_command is None:
            self._show_toast(_('A base URL and token are required to build the curl command.'))
            return

        self._copy_to_clipboard(curl_command)
        self._show_toast(_('curl command copied to clipboard.'))

    def _on_refresh_power_clicked(self, _button):
        self._refresh_power_state()
        self._show_toast(_('Power capability refreshed.'))

    def _on_show_diagnostics_changed(self, action, value):
        visible = value.get_boolean()
        self._show_diagnostics = visible
        action.set_state(value)
        self._settings.set_show_diagnostics(visible)
        self._set_diagnostics_visible(visible)

    def _set_diagnostics_visible(self, visible: bool):
        self.diagnostics_group.set_visible(visible)
        action = self.lookup_action('show-diagnostics')
        if action is not None and action.get_state().get_boolean() != visible:
            action.set_state(GLib.Variant.new_boolean(visible))

    def _apply_runtime_configuration(self, snapshot: SettingsSnapshot, show_toast: bool):
        self._update_endpoint_row(snapshot.listen_port)
        if snapshot.listen_enabled:
            try:
                self._listener.start(snapshot.listen_port, snapshot.shared_token)
            except OSError as error:
                self._update_listener_state(f'Failed to start listener: {error.strerror or error}.')
                if show_toast:
                    self._show_toast(_('The listener could not be started.'))
                return
            if show_toast:
                self._show_toast(_('Configuration saved and listener restarted.'))
            return

        self._listener.stop()
        self._update_listener_state(_('Listener disabled in configuration.'))
        if show_toast:
            self._show_toast(_('Configuration saved and listener stopped.'))

    def _refresh_power_state(self):
        self._power_capability = self._power_controller.check_capability()
        self.power_state_row.set_subtitle(self._power_capability.message)

    def _update_endpoint_row(self, port: int):
        primary_base_url = self._get_primary_android_base_url(port)
        self.base_url_row.set_subtitle(self._build_android_base_url_subtitle(port, primary_base_url))
        self.copy_base_url_button.set_sensitive(primary_base_url is not None)
        self.copy_curl_button.set_sensitive(self._build_status_curl_command(port) is not None)
        self.endpoint_row.set_subtitle(
            f'GET {STATUS_PATH} and POST {POWER_OFF_PATH} on port {port}. '
            f'Legacy /v1 compatibility is enabled. Bearer token required.'
        )

    def _build_android_base_url_subtitle(self, port: int, primary_url: str | None) -> str:
        urls = [f'http://{address}:{port}' for address in self._get_candidate_ipv4_addresses()]
        if not urls:
            return _(
                'No LAN IPv4 address could be detected automatically. Use this PC network address with port %(port)s.'
            ) % {'port': port}

        if primary_url is None:
            primary_url = urls[0]

        if len(urls) == 1:
            return _('Use %(url)s. Android and this PC must be on the same local network.') % {
                'url': primary_url,
            }

        alternates = ', '.join(urls[1:])
        return _(
            'Use %(url)s. Android and this PC must be on the same local network. Other detected addresses: %(others)s'
        ) % {
            'url': primary_url,
            'others': alternates,
        }

    def _get_primary_android_base_url(self, port: int):
        addresses = self._get_candidate_ipv4_addresses()
        if not addresses:
            return None

        return f'http://{addresses[0]}:{port}'

    def _build_status_curl_command(self, port: int):
        base_url = self._get_primary_android_base_url(port)
        token = self.token_entry.get_text().strip()
        if base_url is None or not token:
            return None

        url = f'{base_url}{STATUS_PATH}'
        return (
            f'curl -i '
            f'-H {shlex.quote("Accept: application/json")} '
            f'-H {shlex.quote(f"Authorization: Bearer {token}")} '
            f'{shlex.quote(url)}'
        )

    def _get_candidate_ipv4_addresses(self):
        private_candidates = []
        other_candidates = []

        primary_address = self._detect_primary_ipv4_address()
        if primary_address is not None:
            self._append_candidate_ip(primary_address, private_candidates, other_candidates)

        hostname = socket.gethostname()
        try:
            infos = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        except OSError:
            infos = []

        for family, _socktype, _proto, _canonname, sockaddr in infos:
            if family != socket.AF_INET:
                continue

            address = sockaddr[0]
            self._append_candidate_ip(address, private_candidates, other_candidates)

        return private_candidates + other_candidates

    def _append_candidate_ip(self, address: str, private_candidates, other_candidates):
        if not self._is_candidate_lan_ipv4(address):
            return

        target = private_candidates if self._is_private_lan_ipv4(address) else other_candidates
        if address not in private_candidates and address not in other_candidates:
            target.append(address)

    def _detect_primary_ipv4_address(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # This does not send traffic, but lets the OS reveal the preferred outbound IP.
            sock.connect(('8.8.8.8', 80))
            address = sock.getsockname()[0]
            if self._is_candidate_lan_ipv4(address):
                return address
        except OSError:
            return None
        finally:
            sock.close()

        return None

    def _is_candidate_lan_ipv4(self, address: str) -> bool:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False

        return (
            isinstance(ip, ipaddress.IPv4Address)
            and not ip.is_loopback
            and not ip.is_link_local
            and not ip.is_unspecified
        )

    def _is_private_lan_ipv4(self, address: str) -> bool:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False

        return isinstance(ip, ipaddress.IPv4Address) and ip.is_private

    def _update_listener_state(self, message: str):
        self.listener_state_row.set_subtitle(message)

    def _update_last_request(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.last_request_row.set_subtitle(f'[{timestamp}] {message}')

    def _show_toast(self, message: str):
        self.toast_overlay.add_toast(Adw.Toast.new(message))

    def _copy_to_clipboard(self, value: str):
        self.get_display().get_clipboard().set(value)

    def _create_toggle_action(self, name: str, callback, initial_state):
        action = Gio.SimpleAction.new_stateful(name, None, initial_state)
        action.connect('change-state', callback)
        self.add_action(action)

    def _handle_remote_poweroff(self, client_host: str):
        result = self._power_controller.power_off()
        message = f'{client_host}: {result.message}'
        self._update_last_request(message)
        self._refresh_power_state()
        return {
            'ok': result.success,
            'code': result.code,
            'message': result.message,
        }

    def _handle_remote_status(self, client_host: str):
        self._refresh_power_state()
        snapshot = self._settings.snapshot()
        self._update_last_request(f'{client_host}: Status request served.')
        capability = self._power_capability
        return {
            'ok': True,
            'version': self.get_application().version,
            'listenerEnabled': snapshot.listen_enabled,
            'listenerRunning': self._listener.is_running,
            'powerBackend': 'login1',
            'canonicalStatusPath': STATUS_PATH,
            'canonicalPowerOffPath': POWER_OFF_PATH,
            'legacyStatusPath': LEGACY_STATUS_PATH,
            'legacyPowerOffPath': LEGACY_POWER_OFF_PATH,
            'canPowerOff': capability.raw_value,
            'message': capability.message,
        }

    def _handle_listener_event(self, event_code: str, message: str):
        if event_code.startswith('listener-'):
            self._update_listener_state(message)
        else:
            self._update_last_request(message)
        return False

    def _on_close_request(self, *_args):
        self._listener.stop()
        return False
