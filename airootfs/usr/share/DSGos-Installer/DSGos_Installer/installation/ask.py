#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ask.py
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


""" Asks which type of installation the user wants to perform """

import os
import sys
import queue

# When testing, no _() is available
try:
    _("")
except NameError as err:
    def _(message):
        return message

if __name__ == '__main__':
    # Insert the parent directory at the front of the path.
    # This is used only when we want to test this screen
    BASE_DIR = os.path.dirname(__file__) or '.'
    PARENT_DIR = os.path.join(BASE_DIR, '..')
    sys.path.insert(0, PARENT_DIR)

import bootinfo
import logging

from gtkbasebox import GtkBaseBox
import misc.misc as misc


def check_alongside_disk_layout():
    """ Alongside can only work if user has followed the recommended
        BIOS-Based Disk-Partition Configurations shown in
        http://technet.microsoft.com/en-us/library/dd744364(v=ws.10).aspx """

    # TODO: Add more scenarios where alongside could work

    partitions = misc.get_partitions()
    # logging.debug(partitions)
    extended = False
    for partition in partitions:
        if misc.is_partition_extended(partition):
            extended = True

    if extended:
        return False

    # We just seek for sda partitions
    partitions_sda = []
    for partition in partitions:
        if "sda" in partition:
            partitions_sda.append(partition)

    # There's no extended partition, so all partitions must be primary
    if len(partitions_sda) < 4:
        return True

    return False


class InstallationAsk(GtkBaseBox):
    def __init__(self, params, prev_page="features", next_page=None):
        super().__init__(self, params, "ask", prev_page, next_page)

        data_dir = self.settings.get("data")

        partitioner_dir = os.path.join(data_dir, "images", "partitioner", "small")

        image = self.ui.get_object("automatic_image")
        path = os.path.join(partitioner_dir, "automatic.png")
        image.set_from_file(path)

        # image = self.ui.get_object("alongside_image")
        # path = os.path.join(partitioner_dir, "alongside.png")
        # image.set_from_file(path)

        image = self.ui.get_object("advanced_image")
        path = os.path.join(partitioner_dir, "advanced.png")
        image.set_from_file(path)

        self.other_oses = []

        # DISABLE ALONGSIDE INSTALLATION. IT'S NOT READY YET
        # enable_alongside = self.check_alongside()
        enable_alongside = False
        self.settings.set('enable_alongside', enable_alongside)
        '''
        if enable_alongside:
            msg = "DSGos_Installer will enable the 'alongside' installation mode."
        else:
            msg = "DSGos_Installer will NOT enable the 'alongside' installation mode."
        logging.debug(msg)
        '''

        # By default, select automatic installation
        self.next_page = "installation_automatic"

    def check_alongside(self):
        """ Check if alongside installation type must be enabled.
        Alongside only works when Windows is installed on sda  """

        enable_alongside = False

        # FIXME: Alongside does not work in UEFI systems
        if os.path.exists("/sys/firmware/efi"):
            msg = "The 'alongside' installation mode does not work in UEFI systems"
            logging.debug(msg)
            enable_alongside = False
        else:
            oses = bootinfo.get_os_dict()
            self.other_oses = []
            for key in oses:
                # We only check the first hard disk
                if "sda" in key and oses[key] not in ["unknown", "Swap", "Data or Swap"] and oses[key] not in self.other_oses:
                    self.other_oses.append(oses[key])

            if len(self.other_oses) > 0:
                for detected_os in self.other_oses:
                    if "windows" in detected_os.lower():
                        logging.debug("Windows(tm) OS detected.")
                        enable_alongside = True
                if not enable_alongside:
                    logging.debug("Windows(tm) OS not detected.")
                    enable_alongside = False
            else:
                logging.debug("Can't detect any OS in device sda.")
                enable_alongside = False

            if not check_alongside_disk_layout():
                logging.debug("Unsuported disk layout for the 'alongside' installation mode")
                enable_alongside = False

        return enable_alongside

    def enable_automatic_options(self, status):
        """ Enables or disables automatic installation options """
        names = [
            "encrypt_checkbutton",
            "encrypt_label",
            "lvm_checkbutton",
            "lvm_label",
            "home_checkbutton",
            "home_label"]

        for name in names:
            obj = self.ui.get_object(name)
            obj.set_sensitive(status)

    def prepare(self, direction):
        """ Prepares screen """
        self.translate_ui()
        self.show_all()

        if not self.settings.get('enable_alongside'):
            self.hide_alongside_option()

    def hide_alongside_option(self):
        """ Hides alongisde widgets """
        widgets = [
            "alongside_radiobutton",
            "alongside_description",
            "alongside_image"]

        for name in widgets:
            widget = self.ui.get_object(name)
            if widget is not None:
                widget.hide()

    def get_os_list_str(self):
        os_str = ""
        len_other_oses = len(self.other_oses)
        if len_other_oses > 0:
            if len_other_oses > 1:
                if len_other_oses == 2:
                    os_str = _(" and ").join(self.other_oses)
                else:
                    os_str = ", ".join(self.other_oses)
            else:
                os_str = self.other_oses[0]

        # Truncate string if it's too large
        if len(os_str) > 40:
            os_str = os_str[:40] + "..."

        return os_str

    def translate_ui(self):
        """ Translates screen before showing it """
        self.header.set_subtitle(_("Installation Type"))

        self.forward_button.set_always_show_image(True)
        self.forward_button.set_sensitive(True)

        description_style = '<span style="italic">{0}</span>'
        bold_style = '<span weight="bold">{0}</span>'

        oses_str = self.get_os_list_str()

        max_width_chars = 80

        # Automatic Install
        radio = self.ui.get_object("automatic_radiobutton")
        if len(oses_str) > 0:
            txt = _("Replace {0} with DSGos").format(oses_str)
        else:
            txt = _("Erase disk and install DSGos")
        radio.set_label(txt)
        radio.set_name('auto_radio_btn')

        label = self.ui.get_object("automatic_description")
        txt = _("Warning: This will erase ALL data on your disk.")
        # txt = description_style.format(txt)
        label.set_text(txt)
        label.set_name("automatic_desc")
        label.set_hexpand(False)
        label.set_line_wrap(True)
        label.set_max_width_chars(max_width_chars)

        button = self.ui.get_object("encrypt_checkbutton")
        txt = _("Encrypt this installation for increased security.")
        button.set_label(txt)
        button.set_name("enc_btn")
        button.set_hexpand(False)
        # button.set_line_wrap(True)
        # button.set_max_width_chars(max_width_chars)

        label = self.ui.get_object("encrypt_label")
        txt = _("You will be asked to create an encryption password in the next step.")
        # txt = description_style.format(txt)
        label.set_text(txt)
        label.set_name("enc_label")
        label.set_hexpand(False)
        label.set_line_wrap(True)
        label.set_max_width_chars(max_width_chars)

        button = self.ui.get_object("lvm_checkbutton")
        txt = _("Use LVM with this installation.")
        button.set_label(txt)
        button.set_name("lvm_btn")
        button.set_hexpand(False)
        # button.set_line_wrap(True)
        # button.set_max_width_chars(max_width_chars)

        label = self.ui.get_object("lvm_label")
        txt = _("This will setup LVM and allow you to easily manage partitions and create snapshots.")
        # txt = description_style.format(txt)
        label.set_text(txt)
        label.set_name("lvm_label")
        label.set_hexpand(False)
        label.set_line_wrap(True)
        label.set_max_width_chars(max_width_chars)

        button = self.ui.get_object("home_checkbutton")
        txt = _("Set your Home in a different partition/volume")
        button.set_label(txt)
        button.set_name("home_btn")
        button.set_hexpand(False)
        # button.set_line_wrap(True)
        # button.set_max_width_chars(max_width_chars)

        label = self.ui.get_object("home_label")
        txt = _("This will setup you /home directory in a different partition or volume.")
        # txt = description_style.format(txt)
        label.set_text(txt)
        label.set_name("home_label")
        label.set_hexpand(False)
        label.set_line_wrap(True)
        label.set_max_width_chars(max_width_chars)

        # Alongside Install (For now, only works with Windows)
        # if len(oses_str) > 0:
        #     txt = _("Install DSGos alongside {0}").format(oses_str)
        #     radio = self.ui.get_object("alongside_radiobutton")
        #     radio.set_label(txt)
        #
        #     label = self.ui.get_object("alongside_description")
        #     txt = _("Installs DSGos without removing {0}").format(oses_str)
        #     txt = description_style.format(txt)
        #     label.set_markup(txt)
        #     label.set_line_wrap(True)
        #
        #     intro_txt = _("This computer has {0} installed.").format(oses_str)
        #     intro_txt = intro_txt + "\n" + _("What do you want to do?")
        # else:
        intro_txt = _("How would you like to proceed?")

        intro_label = self.ui.get_object("introduction")
        # intro_txt = bold_style.format(intro_txt)
        intro_label.set_text(intro_txt)
        intro_label.set_name("intro_label")
        intro_label.set_hexpand(False)
        intro_label.set_line_wrap(True)
        intro_label.set_max_width_chars(max_width_chars)

        # Advanced Install
        radio = self.ui.get_object("advanced_radiobutton")
        radio.set_label(_("Choose exactly where DSGos should be installed."))
        radio.set_name("advanced_radio_btn")

        label = self.ui.get_object("advanced_description")
        txt = _("Edit partition table and choose mount points.")
        # txt = description_style.format(txt)
        label.set_text(txt)
        label.set_name("adv_desc_label")
        label.set_hexpand(False)
        label.set_line_wrap(True)
        label.set_max_width_chars(max_width_chars)

    def store_values(self):
        """ Store selected values """
        check = self.ui.get_object("encrypt_checkbutton")
        use_luks = check.get_active()

        check = self.ui.get_object("lvm_checkbutton")
        use_lvm = check.get_active()

        check = self.ui.get_object("home_checkbutton")
        use_home = check.get_active()

        if self.next_page == "installation_automatic":
            self.settings.set('use_lvm', use_lvm)
            self.settings.set('use_luks', use_luks)
            self.settings.set('use_luks_in_root', True)
            self.settings.set('luks_root_volume', "cryptDSGos")
            self.settings.set('use_home', use_home)
        else:
            # Set defaults. We don't know these yet.
            self.settings.set('use_lvm', False)
            self.settings.set('use_luks', False)
            self.settings.set('use_luks_in_root', False)
            self.settings.set('luks_root_volume', "")
            self.settings.set('use_home', False)

        if self.settings.get('use_luks'):
            logging.info("DSGos installation will be encrypted using LUKS")

        if self.settings.get('use_lvm'):
            logging.info("DSGos will be installed using LVM volumes")
            if self.settings.get('use_home'):
                logging.info("DSGos will be installed using a separate /home volume.")
        elif self.settings.get('use_home'):
            logging.info("DSGos will be installed using a separate /home partition.")

        if self.next_page == "installation_alongside":
            self.settings.set('partition_mode', 'alongside')
        elif self.next_page == "installation_advanced":
            self.settings.set('partition_mode', 'advanced')
        elif self.next_page == "installation_automatic":
            self.settings.set('partition_mode', 'automatic')

        # Check if there are still processes running...
        must_wait = False
        for proc in self.process_list:
            if proc.is_alive():
                must_wait = True
                break

        if must_wait:
            from gi.repository import Gtk
            txt1 = _("Ranking mirrors")
            txt2 = _("DSGos_Installer is still updating and optimizing your mirror lists.")
            txt2 += "\n\n"
            txt2 += _("Please be patient...")
            txt1 = "<big>{0}</big>".format(txt1)
            txt2 = "<i>{0}</i>".format(txt2)
            wait_ui = Gtk.Builder()
            ui_file = os.path.join(self.ui_dir, "wait.ui")
            wait_ui.add_from_file(ui_file)
            lbl1 = wait_ui.get_object("label1")
            lbl1.set_markup(txt1)
            lbl2 = wait_ui.get_object("label2")
            lbl2.set_markup(txt2)
            progress_bar = wait_ui.get_object("progressbar")
            wait_window = wait_ui.get_object("wait_window")
            wait_window.set_modal(True)
            wait_window.set_transient_for(self.get_toplevel())
            wait_window.set_default_size(320, 240)
            wait_window.set_position(Gtk.WindowPosition.CENTER)
            wait_window.show_all()

            ask_box = self.ui.get_object("ask")
            if ask_box:
                ask_box.set_sensitive(False)

            import time
            logging.debug("Waiting for all external processes to finish...")
            while must_wait:
                must_wait = False
                for proc in self.process_list:
                    # This waits until process finishes, no matter the time.
                    if proc.is_alive():
                        must_wait = True
                # Just wait...
                time.sleep(0.1)
                # Update our progressbar dialog
                progress_bar.pulse()
                while Gtk.events_pending():
                    Gtk.main_iteration()
            logging.debug("All external processes are finished. Installation can go on")
            wait_window.hide()

            if ask_box:
                ask_box.set_sensitive(True)

        return True

    def get_next_page(self):
        return self.next_page

    def on_automatic_radiobutton_toggled(self, widget):
        """ Automatic selected, enable all options """
        if widget.get_active():
            self.next_page = "installation_automatic"
            self.enable_automatic_options(True)

    def on_alongside_radiobutton_toggled(self, widget):
        """ Alongside selected, disable all automatic options """
        if widget.get_active():
            self.next_page = "installation_alongside"
            self.enable_automatic_options(False)

    def on_advanced_radiobutton_toggled(self, widget):
        """ Advanced selected, disable all automatic options """
        if widget.get_active():
            self.next_page = "installation_advanced"
            self.enable_automatic_options(False)


if __name__ == '__main__':
    from test_screen import _, run

    run('InstallationAsk')
