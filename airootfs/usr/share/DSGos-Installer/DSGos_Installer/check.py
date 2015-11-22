#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  check.py
#
#  Copyright © 2013-2015 DSGos
#
#  This file is part of DSGos_Installer.
#
#  DSGos_Installer is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  DSGos_Installer is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The following additional terms are in effect as per Section 7 of the license:
#
#  The preservation of all legal notices and author attributions in
#  the material or in the Appropriate Legal Notices displayed
#  by works containing it is required.
#
#  You should have received a copy of the GNU General Public License
#  along with DSGos_Installer; If not, see <http://www.gnu.org/licenses/>.


""" Check screen (detects if DSGos prerequisites are meet) """


from gi.repository import GLib

import subprocess
import os
import logging

import info
import updater
import misc.misc as misc

from gtkbasebox import GtkBaseBox

# Constants
NM = 'org.freedesktop.NetworkManager'
NM_STATE_CONNECTED_GLOBAL = 70
UPOWER = 'org.freedesktop.UPower'
UPOWER_PATH = '/org/freedesktop/UPower'
MIN_ROOT_SIZE = 6000000000


class Check(GtkBaseBox):
    """ Check class """

    def __init__(self, params, prev_page="language", next_page="location"):
        """ Init class ui """
        super().__init__(self, params, "check", prev_page, next_page)

        self.remove_timer = False

        self.updater = None
        self.prepare_power_source = None
        self.prepare_network_connection = None
        self.prepare_enough_space = None
        self.timeout_id = None
        self.prepare_best_results = None
        self.updated = None

        self.label_space = self.ui.get_object("label_space")

        if 'checks_are_optional' in params:
            self.checks_are_optional = params['checks_are_optional']
        else:
            self.checks_are_optional = False

    def translate_ui(self):
        """ Translates all ui elements """
        txt = _("System Check")
        self.header.set_subtitle(txt)

        self.updated = self.ui.get_object("updated")
        txt = _("DSGos_Installer is up to date")
        self.updated.set_property("label", txt)

        self.prepare_enough_space = self.ui.get_object("prepare_enough_space")
        txt = _("has at least {0}GB available storage space. (*)").format(MIN_ROOT_SIZE / 1000000000)
        self.prepare_enough_space.set_property("label", txt)

        txt = _("This highly depends on which desktop environment you choose, so you might need more space.")
        txt = "(*) <i>{0}</i>".format(txt)
        self.label_space.set_markup(txt)
        self.label_space.set_hexpand(False)
        self.label_space.set_line_wrap(True)
        self.label_space.set_max_width_chars(80)

        self.prepare_power_source = self.ui.get_object("prepare_power_source")
        txt = _("is plugged in to a power source")
        self.prepare_power_source.set_property("label", txt)

        self.prepare_network_connection = self.ui.get_object("prepare_network_connection")
        txt = _("is connected to the Internet")
        self.prepare_network_connection.set_property("label", txt)

        self.prepare_best_results = self.ui.get_object("prepare_best_results")
        txt = _("For best results, please ensure that this computer:")
        txt = '<span weight="bold" size="large">{0}</span>'.format(txt)
        self.prepare_best_results.set_markup(txt)
        self.prepare_best_results.set_hexpand(False)
        self.prepare_best_results.set_line_wrap(True)
        self.prepare_best_results.set_max_width_chars(80)

    def check_all(self):
        """ Check that all requirements are meet """
        has_internet = misc.has_connection()
        self.prepare_network_connection.set_state(has_internet)

        on_power = not self.on_battery()
        self.prepare_power_source.set_state(on_power)

        space = self.has_enough_space()
        self.prepare_enough_space.set_state(space)

        if has_internet:
            updated = self.is_updated()
        else:
            updated = False

        self.updated.set_state(updated)

        if self.checks_are_optional:
            return True

        if has_internet and space:
            return True

        return False

    def on_battery(self):
        """ Checks if we are on battery power """
        import dbus

        if self.has_battery():
            bus = dbus.SystemBus()
            upower = bus.get_object(UPOWER, UPOWER_PATH)
            return misc.get_prop(upower, UPOWER_PATH, 'OnBattery')

        return False

    def has_battery(self):
        # UPower doesn't seem to have an interface for this.
        path = '/sys/class/power_supply'
        if not os.path.exists(path):
            return False
        for folder in os.listdir(path):
            type_path = os.path.join(path, folder, 'type')
            if os.path.exists(type_path):
                with open(type_path) as power_file:
                    if power_file.read().startswith('Battery'):
                        self.settings.set('laptop', 'True')
                        return True
        return False

    @staticmethod
    def has_enough_space():
        """ Check that we have a disk or partition with enough space """
        lsblk = subprocess.Popen(["lsblk", "-lnb"], stdout=subprocess.PIPE)
        output = lsblk.communicate()[0].decode("utf-8").split("\n")

        max_size = 0

        for item in output:
            col = item.split()
            if len(col) >= 5:
                if col[5] == "disk" or col[5] == "part":
                    size = int(col[3])
                    if size > max_size:
                        max_size = size

        if max_size >= MIN_ROOT_SIZE:
            return True

        return False

    def is_updated(self):
        """ Checks that DSGos_Installer version is, at least, latest stable """
        if not self.updater:
            # Only call updater once
            self.updater = updater.Updater(local_DSGos_Installer_version=info.DSGos_Installer_VERSION)
        return not self.updater.is_remote_version_newer()

    def on_timer(self):
        """ If all requirements are meet, enable forward button """
        if not self.remove_timer:
            self.forward_button.set_sensitive(self.check_all())
        return not self.remove_timer

    def store_values(self):
        """ Continue """
        # Remove timer
        self.remove_timer = True

        logging.info("We have Internet connection.")
        logging.info("We're connected to a power source.")
        logging.info("We have enough disk space.")

        # Enable forward button
        self.forward_button.set_sensitive(True)
        return True

    def prepare(self, direction):
        """ Load screen """
        self.translate_ui()
        self.show_all()

        self.forward_button.set_sensitive(self.check_all())

        # Set timer
        self.timeout_id = GLib.timeout_add(5000, self.on_timer)

# When testing, no _() is available
try:
    _("")
except NameError as err:
    def _(message):
        return message

if __name__ == '__main__':
    from test_screen import _, run

    run('Check')
