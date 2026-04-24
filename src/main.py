# main.py
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

import sys
import gi

from gettext import gettext as _

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .settings import AppSettings
from .window import KineticsolWindow

CURRENT_RELEASE_NOTES = """
<p>Startup and background-mode refinements for long-running KineticSOL sessions.</p>
<ul>
  <li>A new preference can start KineticSOL directly hidden in the system tray while the listener starts normally.</li>
  <li>Reopening the app from the launcher or tray now reuses the existing window and listener state.</li>
  <li>The startup mode is stored in GSettings alongside the existing background and remote-access preferences.</li>
</ul>
""".strip()


class KineticsolApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version: str):
        super().__init__(application_id='dev.neikon.kinetic_sol',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/dev/neikon/kinetic_sol')
        self.version = version
        self._settings = AppSettings()
        self._window = None
        self._initial_activation_done = False
        self.create_action('quit', self.on_quit_action, ['<control>q'])
        self.create_action('show', self.on_show_action)
        self.create_action('about', self.on_about_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        if not self._initial_activation_done:
            self._initial_activation_done = True
            if self._settings.snapshot().start_hidden:
                win = self._ensure_window()
                win.start_hidden_on_launch()
                return

        self._present_window()

    def _ensure_window(self):
        if self._window is None:
            self._window = KineticsolWindow(application=self)
            self._window.connect('destroy', self._on_window_destroyed)
        return self._window

    def _on_window_destroyed(self, *_args):
        self._window = None

    def _present_window(self):
        win = self._ensure_window()
        win.present()
        win.on_window_presented()
        return win

    def _prepare_shutdown(self):
        if self._window is not None:
            self._window.prepare_for_shutdown()

    def on_show_action(self, *_args):
        self._present_window()

    def on_quit_action(self, *_args):
        self._prepare_shutdown()
        self.quit()

    def do_shutdown(self):
        self._prepare_shutdown()
        Adw.Application.do_shutdown(self)

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='KineticSOL',
                                application_icon='dev.neikon.kinetic_sol',
                                developer_name='neikon',
                                version=self.version,
                                comments=_('Linux companion app for Kinetic WOL on Android.'),
                                # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
                                translator_credits = _('translator-credits'),
                                developers=['neikon'],
                                copyright='© 2026 neikon')
        about.set_website('https://github.com/Neikon/kinetic_sol')
        about.set_issue_url('https://github.com/Neikon/kinetic_sol/issues')
        about.set_support_url('https://github.com/Neikon/kinetic_wol')
        about.set_release_notes_version(self.version)
        about.set_release_notes(CURRENT_RELEASE_NOTES)
        about.add_link(_('KineticSOL Repository'), 'https://github.com/Neikon/kinetic_sol')
        about.add_link(_('Kinetic WOL Android Repository'), 'https://github.com/Neikon/kinetic_wol.git')
        about.present(self._window or self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = KineticsolApplication(version)
    return app.run(sys.argv)
