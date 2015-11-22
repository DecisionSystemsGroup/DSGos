#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  firewall.py
#
#  Copyright © 2013-2015 DSGos
#  Based on parts of ufw code © 2012 Canonical
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


""" Manage ufw setup """

import logging
from installation import chroot

try:
    import ufw
    _UFW = True
except ImportError:
    _UFW = False


def run(params, dest_dir="/install"):
    cmd = ["ufw"]
    cmd.extend(params)

    if not _UFW:
        # Could not import ufw module (missing?)
        # Will call ufw command directly
        try:
            chroot.run(cmd, dest_dir)
        except OSError as os_error:
            logging.warning(os_error)
        finally:
            return

    app_action = False

    # Remember, will have to take --force into account if we use it with 'app'
    idx = 1
    if len(cmd) > 1 and cmd[1].lower() == "--dry-run":
        idx += 1

    if len(cmd) > idx and cmd[idx].lower() == "app":
        app_action = True

    res = ""
    try:
        cmd_line = ufw.frontend.parse_command(cmd)
        ui = ufw.frontend.UFWFrontend(cmd_line.dryrun)
        if app_action and 'type' in cmd_line.data and cmd_line.data['type'] == 'app':
            res = ui.do_application_action(cmd_line.action, cmd_line.data['name'])
        else:
            bailout = False
            if cmd_line.action == "enable" and not cmd_line.force and \
               not ui.continue_under_ssh():
                res = _("Aborted")
                bailout = True

            if not bailout:
                if 'rule' in cmd_line.data:
                    res = ui.do_action(
                        cmd_line.action,
                        cmd_line.data['rule'],
                        cmd_line.data['iptype'],
                        cmd_line.force)
                else:
                    res = ui.do_action(
                        cmd_line.action,
                        "",
                        "",
                        cmd_line.force)
    except (ValueError, ufw.UFWError) as ufw_error:
        logging.error(ufw_error)
        # Error using ufw module
        # Will call ufw command directly
        try:
            chroot.run(cmd, dest_dir)
        except OSError as os_error:
            logging.warning(os_error)
        finally:
            return

    logging.debug(res)
