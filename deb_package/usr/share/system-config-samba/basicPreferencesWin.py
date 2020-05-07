## basicPreferencesWin.py - contains the code for basic preferences window
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
import gtk.glade
import string
import sambaToken
import mainWindow
import libuser

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)
gtk.glade.bindtextdomain(domain)

class BasicPreferencesWin:

    def __init__(self, parent, xml, samba_data, samba_backend, main_window):
        self.ParentClass = parent
        self.samba_data = samba_data
        self.samba_backend = samba_backend
        self.samba_sections = samba_data.sections
        self.samba_sections_dict = samba_data.sections_dict

        self.basic_notebook = xml.get_widget("basic_notebook")
        self.basic_preferences_win = xml.get_widget("basic_preferences_win")
        self.basic_preferences_win.set_modal(True)
        self.basic_preferences_win.set_transient_for(main_window)
        self.basic_preferences_win.connect("delete-event", self.onBasicCancelButtonClicked)
        self.basic_preferences_win.set_icon(mainWindow.iconPixbuf)
        self.workgroup_entry = xml.get_widget("workgroup_entry")
        self.server_entry = xml.get_widget("server_entry")
        self.auth_server_entry = xml.get_widget("auth_server_entry")
        self.ads_realm_entry = xml.get_widget("ads_realm_entry")

        self.auth_option_menu = xml.get_widget("auth_option_menu")
        self.auth_menu = gtk.Menu()
        label = (_("ADS"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "ADS")
        self.auth_menu.append(item)
        label = (_("Domain"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "DOMAIN")
        self.auth_menu.append(item)
        label = (_("Server"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "SERVER")
        self.auth_menu.append(item)
        label = (_("Share"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "SHARE")
        self.auth_menu.append(item)
        label = (_("User"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "USER")
        self.auth_menu.append(item)
        self.auth_option_menu.set_menu(self.auth_menu)

        self.encrypt_option_menu = xml.get_widget("encrypt_option_menu")
        self.encrypt_menu = gtk.Menu()
        label = (_("Yes"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "yes")
        self.encrypt_menu.append(item)
        label = (_("No"))
        item = gtk.MenuItem(label)
        item.set_data("NAME", "no")
        self.encrypt_menu.append(item)
        self.encrypt_option_menu.set_menu(self.encrypt_menu)

        self.guest_option_menu = xml.get_widget("guest_option_menu")
        self.guest_menu = gtk.Menu()
        self.admin = libuser.admin()
        self.users = self.admin.enumerateUsers()
        self.users.sort()
        self.users.insert(0, _("No guest account"))
        for user in self.users:
            item = gtk.MenuItem(user)
            item.set_data("NAME", user)
            self.guest_menu.append(item)
        self.guest_option_menu.set_menu(self.guest_menu)

        xml.signal_connect("on_basic_cancel_button_clicked", self.onBasicCancelButtonClicked)
        xml.signal_connect("on_basic_ok_button_clicked", self.onBasicOkButtonClicked)
        self.auth_option_menu.connect("changed", self.authMenuChanged)

    def showWindow(self):
        self.reset()
        self.readFile()
        self.basic_preferences_win.show_all()

    def readFile(self):
        global_found = None
        guest_account = None
        guest_ok = None
        #Set auth_option_menu default to "User" since that is the default value for smb.conf
        self.auth_option_menu.set_history(4)
        #Set the encrypt_option_menu default to "Yes"
        self.encrypt_option_menu.set_history(0)

        section = self.samba_sections_dict["[global]"]

        keys_entries_functions = [
            [ "workgroup", self.workgroup_entry, string.lower ],
            [ "server string", self.server_entry ],
            [ "password server", self.auth_server_entry ]
        ]

        keys_optionmenus_xlate = [
            [ "security", self.auth_option_menu, [ "ads", "domain", "server", "share", "user" ] ],
            [ "encrypt passwords", self.encrypt_option_menu, [ "yes", "no" ] ]
        ]

        for kef in keys_entries_functions:
            val = section.getKey (kef[0])
            entry = kef[1]
            try:
                func = kef[2]
            except IndexError:
                func = None

            if val == None:
                val = ""
            if func:
                # we have (a) post processing function(s)
                if type (func) == list or type (func) == tuple:
                    # multiple functions are applied consecutively
                    for realfunc in kef[2]:
                        val = realfunc (val)
                else:
                    # function will be applied to value
                    val = func (val)

            entry.set_text (val)

        for kox in keys_optionmenus_xlate:
            val = section.getKey (kox[0])
            optionmenu = kox[1]
            xlate = kox[2]

            if val:
                val = string.lower (val)
                if val in xlate:
                    optionmenu.set_history (xlate.index (val))

        guest_ok = section.getKey ("guest ok")
        if guest_ok:
            guest_ok = string.lower (guest_ok)
            if guest_ok == "no":
                guest_account = None
                guest_ok = "no"
                self.guest_option_menu.set_history(0)
            else:
                guest_account = section.getKey ("guest account")
                if not guest_account:
                    #If guest accounts are enabled, let's assume the default is 'nobody'
                    guest_account = "nobody"

        #if guest accounts are enabled, lets set the menu to the guest user
        if guest_account:
            count = 0
            found = 0
            for user in self.users:
                if guest_account == user:
                    found = count
                count = count + 1
            self.guest_option_menu.set_history(found)            
                            
    def reset(self):
        self.basic_notebook.set_current_page(0)

    def onBasicOkButtonClicked(self, *args):
        #Check to see if workgroup is specified
        if not self.checkForWorkgroup(self.workgroup_entry.get_text()):
            return
        else:
            globalsection = self.samba_sections_dict["[global]"]
            globalsection.setKey ("workgroup", self.workgroup_entry.get_text ())
            globalsection.setKey ("server string", self.server_entry.get_text())

            auth_type = self.auth_menu.get_active().get_data("NAME")
            if auth_type == "USER":
                globalsection.setKey ("username map", "/etc/samba/smbusers")
                globalsection.delKey ("password server")
                globalsection.delKey ("realm")

            elif auth_type == "SHARE":
                globalsection.delKey ("username map")                
                globalsection.delKey ("password server")
                globalsection.delKey ("realm")

            else:
                globalsection.delKey ("username map")

                if auth_type == "SERVER" or auth_type == "DOMAIN" or auth_type == "ADS":
                    #If they've specified SERVER or DOMAIN, require a password server
                    auth_server = string.strip(self.auth_server_entry.get_text())
                    
                    if auth_server == "":
                        self.showMessageDialog(_("To auto-locate a password server, enter a \"*\" into the "
                                                 "Authentication Server entry field.  Otherwise, you must "
                                                 "specify a password server when using 'ADS', 'Domain' "
                                                 "or 'Server' authentication."))
                        self.auth_server_entry.grab_focus()
                        return 
                    else:
                        globalsection.setKey ("password server", auth_server)

                    #If they are using ADS, require a realm server
                    ads_realm_server = string.strip(self.ads_realm_entry.get_text())
                    if auth_type == "ADS":
                        if ads_realm_server == "":
                            #There's no realm server, so complain
                            self.showMessageDialog(_("Please enter a kerberos realm when using "
                                                     "ADS authentication."))
                            self.ads_realm_entry.grab_focus()
                            return
                        else:
                            #We've got a realm server
                            globalsection.setKey ("realm", self.ads_realm_entry.get_text (), "[global]")

            globalsection.setKey ("security", string.lower (self.auth_menu.get_active ().get_data("NAME")))
            globalsection.setKey ("encrypt passwords", self.encrypt_menu.get_active ().get_data ("NAME"))        

            if self.guest_option_menu.get_history() == 0:
                globalsection.setKey ("guest ok", "no")
                globalsection.setKey ("guest account", "nobody")
            else:
                globalsection.setKey ("guest ok", "yes")
                globalsection.setKey ("guest account", self.guest_menu.get_active ().get_data ("NAME"))

            self.basic_preferences_win.hide()
            
            #Let's go ahead and restart the service
            self.samba_data.writeFile()
            self.samba_backend.restartSamba()

    def onBasicCancelButtonClicked(self, *args):
        self.basic_preferences_win.hide()
        return True

    def checkForWorkgroup(self, workgroup):
        if string.strip(workgroup) == "":
            self.showMessageDialog(_("You must specify a workgroup."))
            return 0
        return 1

    def authMenuChanged(self, *args):
        type = self.auth_menu.get_active().get_data("NAME")

        #Let's enable/disable the auth_server_entry
        if type == "SERVER" or type == "DOMAIN":
            #allow password server if using 'server' or 'domain'
            self.auth_server_entry.set_sensitive(True)
            self.ads_realm_entry.set_sensitive(False)
        elif type == "ADS":
            #allow password server and realm server if using 'ads'
            self.auth_server_entry.set_sensitive(True)
            self.ads_realm_entry.set_sensitive(True)
        else:
            self.auth_server_entry.set_sensitive(False)            
            self.ads_realm_entry.set_sensitive(False)

        #Must force encrypted passwords with 'domain'
        if type == "DOMAIN":
            self.encrypt_option_menu.set_history(0)
            self.encrypt_option_menu.set_sensitive(False)
        else:
            self.encrypt_option_menu.set_sensitive(True)

    def showMessageDialog(self, text):
        dlg = gtk.MessageDialog(self.basic_preferences_win, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, text)
        dlg.set_position(gtk.WIN_POS_CENTER)
        dlg.set_modal(True)
        dlg.set_transient_for(self.basic_preferences_win)
        dlg.set_icon(mainWindow.iconPixbuf)            
        dlg.run()
        dlg.destroy()
        
