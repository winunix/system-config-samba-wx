## sambaUserWin.py - contains the UI codee for the samba user window
## Copyright (C) 2002 - 2007 Red Hat, Inc.
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
import gobject
import string
import addUserWin
import mainWindow
import sambaToken

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)
gtk.glade.bindtextdomain(domain)

class SambaUserWin:

    def __init__(self, parent, xml, samba_user_data, main_window):
        self.ParentClass = parent
        self.samba_user_data = samba_user_data
        self.samba_sections = self.ParentClass.samba_data.sections
        self.samba_sections_dict = self.ParentClass.samba_data.sections_dict

        self.add_user_win = addUserWin.AddUserWin(self, self.samba_user_data, xml)

        self.samba_user_win = xml.get_widget("user_win")
        self.samba_user_win.set_modal(True)
        self.samba_user_win.set_transient_for(main_window)
        self.samba_user_win.connect("delete-event", self.onUsersCancelButtonClicked)
        self.samba_user_win.set_icon(mainWindow.iconPixbuf)
        self.samba_user_win.set_position(gtk.WIN_POS_CENTER)
        
        self.list_box = xml.get_widget("list_box")
        self.edit_button = xml.get_widget("edit_user_button")
        self.delete_button = xml.get_widget("delete_user_button")        

        self.user_store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        self.user_view = gtk.TreeView(self.user_store)
        self.user_view.get_selection().connect("changed", self.rowActivated)
        self.user_view.set_rules_hint(True)
        self.user_view_sw = gtk.ScrolledWindow()
        self.user_view_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.user_view_sw.set_shadow_type(gtk.SHADOW_IN)
        self.user_view_sw.add(self.user_view)

        col = gtk.TreeViewColumn(None, gtk.CellRendererText(), text=0)
        self.user_view.set_headers_visible(False)
        self.user_view.append_column(col)

        self.list_box.pack_start(self.user_view_sw)
        self.list_box.reorder_child(self.user_view_sw, 0)
        
        xml.signal_connect("on_users_ok_button_clicked", self.onUsersOkButtonClicked)
        xml.signal_connect("on_users_cancel_button_clicked", self.onUsersCancelButtonClicked)
        xml.signal_connect("on_add_user_button_clicked", self.onAddUserButtonClicked)
        xml.signal_connect("on_edit_user_button_clicked", self.onEditUserButtonClicked)
        xml.signal_connect("on_delete_user_button_clicked", self.onDeleteUserButtonClicked)

        self.fillUserList()

    def showWindow(self):
        self.reset()
        self.samba_user_win.show_all()

    def fillUserList(self):
        list = self.samba_user_data.getPasswdFile()

        self.user_store.clear()

        for line in list:
            tokens = string.split(line, ':')
            iter = self.user_store.append()
            self.user_store.set_value(iter, 0, tokens[0])
            self.user_store.set_value(iter, 1, line)

    def rowActivated(self, *args):
        object, data = self.user_view.get_selection().get_selected()
        if data:
            self.edit_button.set_sensitive(True)
            self.delete_button.set_sensitive(True)        
        else:
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)        

    def reset(self):
        self.user_view.get_selection().unselect_all()
        self.edit_button.set_sensitive(False)
        self.delete_button.set_sensitive(False)        
        
    def onUsersOkButtonClicked(self, *args):
        found = None

        section = self.samba_sections_dict['[global]']
        if not section:
            raise Error ("No [global] section found.")
        #This is a hack to correct the defaults in the stock smb.conf file.  If the security mode
        #is 'user', then turn on 'username map'
        security = section.getKey ("security")
        if not security or string.lower (security) == "user":
            section.setKey ("username map", "/etc/samba/smbusers")

        self.ParentClass.samba_data.writeFile()        
        self.samba_user_data.writeSmbUsersFile()
        self.samba_user_win.hide()

    def onUsersCancelButtonClicked(self, *args):
        self.samba_user_win.hide()
        return True

    def onAddUserButtonClicked(self, *args):
        self.add_user_win.showAddWindow()

    def onEditUserButtonClicked(self, *args):
        data, iter = self.user_view.get_selection().get_selected()
        unix_name = data.get_value(iter, 0)

        #Get a dict of the smbusers file
        user_dict = self.samba_user_data.getUserDict()
        user_keys = user_dict.keys()

        #If this user had an entry in smbusers, print the line
        if unix_name in user_keys:
            line = user_dict[unix_name]
            windows_name = self.samba_user_data.getWindowsName(line)
            self.add_user_win.showEditWindow(unix_name, windows_name)
        else:
            self.add_user_win.showEditWindow(unix_name, unix_name)

    def onDeleteUserButtonClicked(self, *args):
        #Remove user from the TreeView
        data, iter = self.user_view.get_selection().get_selected()
        name = self.user_store.get_value(iter, 0)
        line = self.user_store.get_value(iter, 1)

        #Remove user from the data store
        self.user_store.remove(iter)

        self.samba_user_data.deleteUser(name, line)
        
