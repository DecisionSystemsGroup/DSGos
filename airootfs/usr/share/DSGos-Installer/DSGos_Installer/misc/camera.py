#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  cheese.py
#
#  Based on code by Christian Schaller
#  Copyright © 2013-2015 DSGos
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


import sys
import logging

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GtkClutter', '1.0')
gi.require_version('Cheese', '3.0')

from gi.repository import GtkClutter
from gi.repository import Clutter, GObject, Gtk, Gst, GLib
from gi.repository import Cheese


def cheese_init():
    """ Initialize libcheese, by initializing Clutter and GStreamer. """
    Gst.init(None)
    GtkClutter.init([])

'''
camera.py:58: DeprecationWarning: Clutter.Container.add_actor is deprecated
  self.stage.add_actor(self.container)
camera.py:60: DeprecationWarning: Clutter.Texture.new is deprecated
  self.video_texture = Clutter.Texture.new()
camera.py:61: DeprecationWarning: Clutter.Texture.set_keep_aspect_ratio is deprecated
  self.video_texture.set_keep_aspect_ratio(True)
camera.py:70: DeprecationWarning: Clutter.BoxLayout.pack is deprecated
  y_align=Clutter.BoxAlignment.CENTER)
'''


class CameraBox(GtkClutter.Embed):
    __gtype_name__ = 'VideoBox'

    # __gsignals__ = {'location-changed': (GObject.SignalFlags.RUN_LAST, None, (object,))}

    def __init__(self, width=128, height=100):
        GtkClutter.Embed.__init__(self)

        self.set_size_request(width, height)

        self.stage = self.get_stage()
        self.stage.set_size(width, height)

        self.layout_manager = Clutter.BoxLayout()
        self.container = Clutter.Actor(layout_manager=self.layout_manager)
        self.stage.add_actor(self.container)

        self.video_texture = Clutter.Texture.new()
        self.video_texture.set_keep_aspect_ratio(True)
        self.video_texture.set_size(width, height)
        
        self.layout_manager.pack(
            self.video_texture,
            expand=False,
            x_fill=False,
            y_fill=False,
            x_align=Clutter.BoxAlignment.CENTER,
            y_align=Clutter.BoxAlignment.CENTER)

        self.camera = Cheese.Camera.new(
            video_texture=self.video_texture,
            camera_device_node=None,
            x_resolution=640,
            y_resolution=480)
        
        try:
            self.camera.setup()
            self.camera_found = True
        except GLib.GError as error:
            logging.warning(error)
            self.camera_found = False
            return

    def found(self):
        return self.camera_found

    def play(self):
        if self.camera_found:
            self.camera.play()

            def added(signal, data):
                uuid = data.get_uuid()
                node = data.get_device_node()
                logging.debug("Camera uuid is %s", str(uuid))
                logging.debug("Camera node is %s", str(node))
                self.camera.set_device_by_device_node(node)
                self.camera.switch_camera_device()

            device_monitor = Cheese.CameraDeviceMonitor.new()
            device_monitor.connect("added", added)
            device_monitor.coldplug()

            self.stage.show()
    
    def stop(self):
        if self.camera_found:
            self.camera.stop()

    def take_photo(self, filename):
        return self.camera.take_photo(filename)


if __name__ == "__main__":
    cheese_init()
    
    win = Gtk.Window()
    camera_box = CameraBox()
    win.add(camera_box)
    win.show_all()

    def exit_button(widget, data=None):
        camera_box.stop()
        sys.exit(0)

    win.connect('delete-event', exit_button)
    
    camera_box.play()

    import signal    # enable Ctrl-C since there is no menu to quit
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    Gtk.main()
