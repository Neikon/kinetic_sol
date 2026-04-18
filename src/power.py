# power.py
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

from gi.repository import Gio, GLib

LOGIN1_BUS_NAME = 'org.freedesktop.login1'
LOGIN1_OBJECT_PATH = '/org/freedesktop/login1'
LOGIN1_MANAGER_IFACE = 'org.freedesktop.login1.Manager'


@dataclass(slots=True)
class PowerCapability:
    available: bool
    raw_value: str
    message: str


@dataclass(slots=True)
class PowerActionResult:
    success: bool
    code: str
    message: str


class Login1PowerController:
    def __init__(self):
        self._proxy = None

    def check_capability(self) -> PowerCapability:
        try:
            result = self._proxy_call('CanPowerOff')
        except GLib.Error as error:
            return PowerCapability(
                available=False,
                raw_value='error',
                message=f'Cannot query login1: {error.message}',
            )

        raw_value = result.unpack()[0]
        messages = {
            'yes': 'CanPowerOff() returned yes. Non-interactive shutdown may work.',
            'challenge': 'CanPowerOff() returned challenge. Polkit may require interaction.',
            'no': 'CanPowerOff() returned no. The host currently denies shutdown.',
            'na': 'CanPowerOff() returned n/a. The host does not expose this capability here.',
        }
        return PowerCapability(
            available=raw_value == 'yes',
            raw_value=raw_value,
            message=messages.get(raw_value, f'CanPowerOff() returned {raw_value}.'),
        )

    def power_off(self) -> PowerActionResult:
        capability = self.check_capability()
        try:
            self._proxy_call('PowerOff', GLib.Variant('(b)', (False,)))
        except GLib.Error as error:
            return PowerActionResult(
                success=False,
                code='login1-error',
                message=f'{capability.message} PowerOff(false) failed: {error.message}',
            )

        return PowerActionResult(
            success=True,
            code='ok',
            message='PowerOff(false) was accepted by login1.',
        )

    def _proxy_call(self, method_name: str, parameters=None):
        return self._get_proxy().call_sync(
            method_name,
            parameters,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _get_proxy(self):
        if self._proxy is None:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            self._proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                LOGIN1_BUS_NAME,
                LOGIN1_OBJECT_PATH,
                LOGIN1_MANAGER_IFACE,
                None,
            )
        return self._proxy
