## addUserWin.py - UI code for adding a samba user
## Copyright (C) 2002 - 2005 Red Hat, Inc.
## Copyright (C) 2002, 2003 Brent Fox <bfox@redhat.com>

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

## Authors:
## Brent Fox <bfox@redhat.com>
## Nils Philippsen <nphilipp@redhat.com>

import gtk
import pwd
import mainWindow
import string

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)
gtk.glade.bindtextdomain(domain)

class AddUserWin:

    def __init__(self, samba_user_win, samba_user_data, xml):
        self.samba_user_win = samba_user_win
        self.samba_user_data = samba_user_data

        self.add_user_win = xml.get_widget("add_user_win")
        self.add_user_win.connect("delete-event", self.on_add_user_cancel_button_clicked)
        user_win = xml.get_widget("user_win")
        
        self.add_user_win.set_transient_for(user_win)
        self.add_user_win.set_icon(mainWindow.iconPixbuf)
        self.user_option_menu = xml.get_widget("user_option_menu")
        self.windows_user_entry = xml.get_widget("windows_user_entry")
        self.password_entry = xml.get_widget("password_entry")
        self.confirm_entry = xml.get_widget("confirm_entry")
        self.add_user_ok_button = xml.get_widget("add_user_ok_button")
        self.user_table = xml.get_widget("user_table")
        self.user_label = None

        self.user_menu = gtk.Menu()
        users = pwd.getpwall()
        self.users = []
        for user in users:
            self.users.append(user[0])
        self.users.sort()
        for user in self.users:
            item = gtk.MenuItem(user)
            item.set_data("NAME", user)
            self.user_menu.append(item)
        self.user_option_menu.set_menu(self.user_menu)
        
        self.changed_flag = 0

        self.handler = self.add_user_ok_button.connect("clicked", self.on_add_user_ok_button_clicked)
        xml.signal_connect("on_add_user_cancel_button_clicked", self.on_add_user_cancel_button_clicked)

    def showAddWindow(self):
        self.reset()
        self.handler = self.add_user_ok_button.connect("clicked", self.on_add_user_ok_button_clicked)
        self.user_option_menu.grab_focus()
        self.add_user_win.show_all()

    def showEditWindow(self, unix_name, windows_name):
        self.orig_unix_name = unix_name
        self.orig_windows_name = windows_name
        self.reset()
        self.user_table.remove(self.user_option_menu)
        self.user_label = gtk.Label(self.orig_unix_name)
        self.user_label.set_alignment(0.0, 0.5)
        self.user_table.attach(self.user_label, 1, 2, 0, 1, gtk.FILL|gtk.EXPAND)
        self.handler = self.add_user_ok_button.connect("clicked", self.on_edit_user_ok_button_clicked)

        count = 0
        found = 0
        for user in self.users:
            if unix_name == user:
                found = count
            count = count + 1
            self.user_option_menu.set_history(found)

        self.windows_user_entry.set_text(windows_name)
        self.password_entry.set_text("********")
        self.confirm_entry.set_text("********")
        self.windows_user_entry.grab_focus()
        
        self.add_user_win.show_all()
        
    def reset(self):
        if self.handler:
            self.add_user_ok_button.disconnect(self.handler)
            self.handler = None
        self.user_option_menu.set_sensitive(True)
        self.user_option_menu.set_history(0)
        self.windows_user_entry.set_text("")
        self.password_entry.set_text("")
        self.confirm_entry.set_text("")

    def on_edit_user_ok_button_clicked(self, *args):
        windows_name = self.windows_user_entry.get_text()
        password = self.password_entry.get_text()
        confirm = self.confirm_entry.get_text()

        if password != confirm:
            dlg = gtk.MessageDialog (None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                     _("The passwords do not match.  Please try again."))
            dlg.set_modal(True)
            dlg.set_transient_for(self.add_user_win) 
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.show_all()
            dlg.run()
            dlg.destroy()
            self.password_entry.set_text("")
            self.confirm_entry.set_text("")

        if self.orig_windows_name != windows_name:
            self.samba_user_data.changeWindowsUserName(self.orig_unix_name, windows_name)

        if password != "********":
            #The passwords match, so let's update the user's password
            result = self.samba_user_data.changePassword(self.orig_unix_name, password)

        self.user_label = None
        self.reset()
        self.add_user_win.hide()

    def on_add_user_ok_button_clicked(self, *args):
        unix_name = self.user_menu.get_active().get_data("NAME")
        windows_name = self.windows_user_entry.get_text()
        password = self.password_entry.get_text()
        confirm = self.confirm_entry.get_text()

        user_entity = None

        if string.strip(windows_name) == "":
            dlg = gtk.MessageDialog (None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                     (_("Please enter a Windows username.")))
            dlg.set_modal(True)
            dlg.set_transient_for(self.add_user_win)
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.show_all()
            dlg.run()
            dlg.destroy()
            self.windows_user_entry.grab_focus()

        elif password != confirm or password == "" or confirm == "":
            dlg = gtk.MessageDialog (None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                     (_("The passwords do not match.  Please try again.")))
            dlg.set_modal(True)
            dlg.set_transient_for(self.add_user_win)
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.show_all()
            dlg.run()
            dlg.destroy()
            self.password_entry.set_text("")
            self.confirm_entry.set_text("")
            self.password_entry.grab_focus()

        elif self.samba_user_data.userAlreadyExists(unix_name):
            dlg = gtk.MessageDialog (None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                     (_("An account for this user already exists.  Please try again.")))
            dlg.set_modal(True)
            dlg.set_transient_for(self.add_user_win)
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.show_all()
            dlg.run()
            dlg.destroy()
            self.user_option_menu.grab_focus()
            
        else:
            #The passwords match, so let's try to add the user    
            self.samba_user_data.addUser(unix_name, windows_name, password)
            self.samba_user_win.fillUserList()

            self.reset()
            self.add_user_win.hide()

    def on_add_user_cancel_button_clicked(self, *args):
        self.reset()

        if self.user_label:
            self.user_table.remove(self.user_label)
            self.user_table.attach(self.user_option_menu, 1, 2, 0, 1)
            self.user_label = None

        self.add_user_win.hide()
        return True
