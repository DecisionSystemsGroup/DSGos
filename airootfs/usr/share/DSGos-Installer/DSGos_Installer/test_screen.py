#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_screen.py
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


""" Test screen (simulates main window to test a ui screen) """

from gi.repository import Gtk


def _(message):
    return message


def get_screen(screen_name, params):
    screen = None
    if screen_name == "DesktopAsk":
        import desktop
        screen = desktop.DesktopAsk(params)
    elif screen_name == "Check":
        import check
        screen = check.Check(params)
    elif screen_name == "Timezone":
        import timezone
        screen = timezone.Timezone(params)
        params['settings'].set('timezone_start', True)
    elif screen_name == "Wireless":
        import wireless
        screen = wireless.Wireless(params)
    elif screen_name == "Welcome":
        import welcome
        screen = welcome.Welcome(params)
    elif screen_name == "UserInfo":
        import user_info
        screen = user_info.UserInfo(params)
    elif screen_name == "Location":
        import location
        screen = location.Location(params)
    elif screen_name == "Language":
        import language
        screen = language.Language(params)
    elif screen_name == "Keymap":
        import keymap
        screen = keymap.Keymap(params)
    elif screen_name == "Features":
        import features
        screen = features.Features(params)
    elif screen_name == "Summary":
        import summary
        screen = summary.Summary(params)
    elif screen_name == "Slides":
        import slides
        screen = slides.Slides(params)
    elif screen_name == "InstallationAsk":
        import ask
        screen = ask.InstallationAsk(params)
    elif screen_name == "InstallationAdvanced":
        import advanced
        screen = advanced.InstallationAdvanced(params)
    elif screen_name == "InstallationAlongside":
        import alongside
        screen = alongside.InstallationAlongside(params)
    elif screen_name == "InstallationAutomatic":
        import automatic
        screen = automatic.InstallationAutomatic(params)
    return screen


def run(screen_name):
    window = Gtk.Window()
    window.connect('destroy', Gtk.main_quit)
    # window.set_size_request(600, 500)
    window.set_border_width(0)
    window.set_title("DSGos_Installer - Test of {0} screen".format(screen_name))

    import logging

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(module)s] %(levelname)s: %(message)s',
        "%Y-%m-%d %H:%M:%S")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    import config

    settings = config.Settings()
    settings.set('data', '/usr/share/DSGos_Installer/data')

    from desktop_info import DESKTOPS

    settings.set('desktops', DESKTOPS)
    settings.set('language_code', 'ca')

    params = {
        'title': "DSGos_Installer",
	'main_window': window,
        'ui_dir': "/usr/share/DSGos_Installer/ui",
        'disable_tryit': False,
        'settings': settings,
        'forward_button': Gtk.Button.new(),
        'backwards_button': Gtk.Button.new(),
        'main_progressbar': Gtk.ProgressBar.new(),
        'header': Gtk.HeaderBar.new(),
        'testing': True,
        'callback_queue': None,
        'alternate_package_list': "",
        'process_list': []}

    screen = get_screen(screen_name, params)

    if screen is not None:
        window.add(screen)
        window.show_all()
        screen.prepare('forward')
        Gtk.main()
    else:
        print("Unknown screen")
