# tray.py
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

from gettext import gettext as _

from gi.repository import Gio, GLib

ITEM_BUS_NAME = 'org.kde.StatusNotifierItem.dev.neikon.kinetic_sol'
ITEM_OBJECT_PATH = '/StatusNotifierItem'
ITEM_INTERFACE = 'org.kde.StatusNotifierItem'
WATCHER_BUS_NAME = 'org.kde.StatusNotifierWatcher'
WATCHER_OBJECT_PATH = '/StatusNotifierWatcher'
WATCHER_INTERFACE = 'org.kde.StatusNotifierWatcher'

ITEM_XML = f"""
<node>
  <interface name="{ITEM_INTERFACE}">
    <method name="Activate">
      <arg type="i" name="x" direction="in"/>
      <arg type="i" name="y" direction="in"/>
    </method>
    <method name="SecondaryActivate">
      <arg type="i" name="x" direction="in"/>
      <arg type="i" name="y" direction="in"/>
    </method>
    <method name="ContextMenu">
      <arg type="i" name="x" direction="in"/>
      <arg type="i" name="y" direction="in"/>
    </method>
    <method name="Scroll">
      <arg type="i" name="delta" direction="in"/>
      <arg type="s" name="orientation" direction="in"/>
    </method>
    <property type="s" name="Category" access="read"/>
    <property type="s" name="Id" access="read"/>
    <property type="s" name="Title" access="read"/>
    <property type="s" name="Status" access="read"/>
    <property type="u" name="WindowId" access="read"/>
    <property type="s" name="IconName" access="read"/>
    <property type="s" name="OverlayIconName" access="read"/>
    <property type="s" name="AttentionIconName" access="read"/>
    <property type="(sa(iiay)ss)" name="ToolTip" access="read"/>
    <property type="b" name="ItemIsMenu" access="read"/>
    <property type="o" name="Menu" access="read"/>
    <signal name="NewIcon"/>
    <signal name="NewToolTip"/>
    <signal name="NewStatus">
      <arg type="s" name="status"/>
    </signal>
  </interface>
</node>
"""


class PlasmaTrayIcon:
    def __init__(self, on_activate, on_state_changed):
        self._on_activate = on_activate
        self._on_state_changed = on_state_changed
        self._node_info = Gio.DBusNodeInfo.new_for_xml(ITEM_XML)
        self._interface_info = self._node_info.interfaces[0]
        self._owner_id = 0
        self._registration_id = 0
        self._connection = None
        self._status = 'Passive'
        self._title = 'KineticSOL'
        self._tooltip_text = _('KineticSOL is running in the background.')
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def show(self, tooltip_text: str):
        self._title = 'KineticSOL'
        self._tooltip_text = tooltip_text
        self._status = 'Active'
        if self._owner_id:
            self._emit_new_status()
            self._emit_new_tooltip()
            return

        self._owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            ITEM_BUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            self._on_bus_acquired,
            self._on_name_acquired,
            self._on_name_lost,
        )

    def hide(self):
        if self._owner_id:
            Gio.bus_unown_name(self._owner_id)
            self._owner_id = 0

        self._clear_registration()
        self._status = 'Passive'
        if self._active:
            self._active = False
            self._notify_state(_('Tray icon inactive. The app window is open.'))

    def _on_bus_acquired(self, connection, _name):
        self._connection = connection
        self._registration_id = connection.register_object(
            ITEM_OBJECT_PATH,
            self._interface_info,
            self._handle_method_call,
            self._handle_get_property,
            None,
        )

    def _on_name_acquired(self, connection, _name):
        try:
            connection.call_sync(
                WATCHER_BUS_NAME,
                WATCHER_OBJECT_PATH,
                WATCHER_INTERFACE,
                'RegisterStatusNotifierItem',
                GLib.Variant('(s)', (ITEM_BUS_NAME,)),
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error as error:
            self._active = False
            self._notify_state(_('Tray icon could not register with Plasma: %(error)s') % {'error': error.message})
            return

        self._active = True
        self._notify_state(_('Tray icon active in Plasma. Left click reopens the window.'))

    def _on_name_lost(self, _connection, _name):
        self._clear_registration()
        was_active = self._active
        self._active = False
        if self._owner_id:
            self._owner_id = 0

        if was_active:
            self._notify_state(_('Tray icon disconnected from Plasma.'))
        else:
            self._notify_state(_('Plasma tray watcher is not available or the sandbox is missing tray permissions.'))

    def _handle_method_call(
        self,
        _connection,
        _sender,
        _object_path,
        _interface_name,
        method_name,
        _parameters,
        invocation,
    ):
        if method_name in {'Activate', 'SecondaryActivate', 'ContextMenu'}:
            GLib.idle_add(self._on_activate)
        invocation.return_value(GLib.Variant('()', ()))

    def _handle_get_property(
        self,
        _connection,
        _sender,
        _object_path,
        _interface_name,
        property_name,
    ):
        values = {
            'Category': GLib.Variant('s', 'ApplicationStatus'),
            'Id': GLib.Variant('s', 'kineticsol'),
            'Title': GLib.Variant('s', self._title),
            'Status': GLib.Variant('s', self._status),
            'WindowId': GLib.Variant('u', 0),
            'IconName': GLib.Variant('s', 'dev.neikon.kinetic_sol'),
            'OverlayIconName': GLib.Variant('s', ''),
            'AttentionIconName': GLib.Variant('s', ''),
            'ToolTip': GLib.Variant(
                '(sa(iiay)ss)',
                ('dev.neikon.kinetic_sol', [], self._title, self._tooltip_text),
            ),
            'ItemIsMenu': GLib.Variant('b', False),
            'Menu': GLib.Variant('o', '/'),
        }
        return values.get(property_name)

    def _emit_signal(self, signal_name: str, parameters=None):
        if self._connection is None:
            return

        self._connection.emit_signal(
            None,
            ITEM_OBJECT_PATH,
            ITEM_INTERFACE,
            signal_name,
            parameters,
        )

    def _emit_new_status(self):
        self._emit_signal('NewStatus', GLib.Variant('(s)', (self._status,)))

    def _emit_new_tooltip(self):
        self._emit_signal('NewToolTip')

    def _clear_registration(self):
        if self._connection is not None and self._registration_id:
            self._connection.unregister_object(self._registration_id)
            self._registration_id = 0

        self._connection = None

    def _notify_state(self, message: str):
        GLib.idle_add(self._on_state_changed, message)
