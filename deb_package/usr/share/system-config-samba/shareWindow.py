## shareWindow.py - the UI code for creating samba shares
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
import string
import mainWindow
import sambaToken
import sambaUserData
import sambaParser
import os
import gobject

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)
gtk.glade.bindtextdomain(domain)

class ShareWindow:
    def __init__(self, parent, xml, samba_data, samba_user_data, samba_backend, main_window):
        self.ParentClass = parent
        self.samba_data = samba_data
        self.samba_user_data = samba_user_data
        self.samba_backend = samba_backend
        self.samba_sections = samba_data.sections
        self.samba_sections_dict = samba_data.sections_dict
        
        self.share_window = xml.get_widget("share_win")
        self.share_window.set_modal(True)
        self.share_window.set_transient_for(main_window)
        self.share_window.connect("delete-event", self.onCancelButtonClicked)
        self.share_window.set_position(gtk.WIN_POS_CENTER)
        self.share_window.set_icon(mainWindow.iconPixbuf)
        self.share_notebook = xml.get_widget("share_notebook")
        self.dir_entry = xml.get_widget("share_dir_entry")
        self.description_entry = xml.get_widget("description_entry")
        self.sharename_entry = xml.get_widget("sharename_entry")
        self.writable_check = xml.get_widget("share_writable_check")
        self.visible_check = xml.get_widget("share_visible_check")

        self.user_access_radio = xml.get_widget("user_access_radio")
        self.guest_access_radio = xml.get_widget("guest_access_radio")
        self.user_access_radio.connect("toggled", self.userRadioToggled)
        
        xml.signal_connect("on_share_cancel_button_clicked", self.onCancelButtonClicked)
        xml.signal_connect("on_share_ok_button_clicked", self.onOkButtonClicked)
        xml.signal_connect("on_share_browse_button_clicked", self.onBrowseButtonClicked)
        xml.signal_connect("on_share_dir_entry_changed", self.onDirEntryChanged)
        xml.signal_connect("on_sharename_entry_changed", self.onShareNameEntryChanged)

        self.valid_users_treeview = xml.get_widget("valid_users_treeview")
        self.browsable_checkbutton = xml.get_widget("browsable_checkbutton")
        self.create_mode_label = xml.get_widget("create_mode_label")
        self.dir_mode_label = xml.get_widget("dir_mode_label")
        self.create_mode_button = xml.get_widget("create_mode_button")
        self.dir_mode_button = xml.get_widget("dir_mode_button")        

        self.valid_users_store = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING)
        self.valid_users_treeview.set_model(self.valid_users_store)

        self.checkbox = gtk.CellRendererToggle()
        col = gtk.TreeViewColumn('', self.checkbox, active = 0)
        col.set_fixed_width(20)
        col.set_clickable(True)
        self.checkbox.connect("toggled", self.userToggled)
        self.valid_users_treeview.append_column(col)

        col = gtk.TreeViewColumn("", gtk.CellRendererText(), text=1)
        self.valid_users_treeview.append_column(col)

    def populateUserStore(self):
        userList = self.samba_user_data.getPasswdFile()

        if userList == None:
            return

        userList.sort()
        for line in userList:
            iter = self.valid_users_store.append()
            tokens = string.split(line, ':')
            self.valid_users_store.set_value(iter, 0, False)
            self.valid_users_store.set_value(iter, 1, tokens[0])

    def populateUserStoreOnEdit(self, currentUserList, invalidUsers):
        userList = self.samba_user_data.getPasswdFile()

        if userList == None:
            return

        userList.sort()
        for line in userList:
            iter = self.valid_users_store.append()
            tokens = string.split(line, ':')

            if self.guest_access_radio.get_active() == True:
                self.valid_users_store.set_value(iter, 0, False)
                self.valid_users_store.set_value(iter, 1, tokens[0])
                continue
                
            if invalidUsers == "%S":
                #Make all users unselected
                self.valid_users_store.set_value(iter, 0, False)
                self.valid_users_store.set_value(iter, 1, tokens[0])
            else:
                #invalidUsers is not "%S"
                if currentUserList == ['None'] or currentUserList == []:
                    #If no users are specified, assume all are allowed
                    self.valid_users_store.set_value(iter, 0, True)
                    self.valid_users_store.set_value(iter, 1, tokens[0])
                else:
                    #Let's see which users are allowed
                    if tokens[0] in currentUserList:
                        self.valid_users_store.set_value(iter, 0, True)
                        self.valid_users_store.set_value(iter, 1, tokens[0])
                    else:
                        self.valid_users_store.set_value(iter, 0, False)
                        self.valid_users_store.set_value(iter, 1, tokens[0])

    def userToggled(self, data, row):
        iter = self.valid_users_store.get_iter((int(row),))
        val = self.valid_users_store.get_value(iter, 0)
        self.valid_users_store.set_value(iter, 0 , not val)

    def showNewWindow(self):
        self.section = None
        self.share_window.set_title(_("Create Samba Share"))
        self.edit_mode = 0
        self.reset ()
        self.dir_entry.grab_focus()
        self.populateUserStore()
        self.share_window.show_all()
        self.sharenamechanged = 0

    def showEditWindow(self, iter, section):
        self.section = section
        self.share_window.set_title(_("Edit Samba Share"))
        self.edit_mode = 1
        self.reset ()
        self.sharenamechanged = 1
        self.edit_iter = iter

        userList = []
        invalidUsers = None

        self.sharename_entry.set_text (string.strip (section.name, "[]"))

        path = section.getKey ("path")
        if path:
            self.dir_entry.set_text (path)

        comment = section.getKey ("comment")
        if comment and comment != "None":
            self.description_entry.set_text (comment)

        writeable = section.getKey ("writeable")
        if writeable and string.lower (writeable) == "yes":
            self.writable_check.set_active (True)
        else:
            self.writable_check.set_active (False)

        visible = section.getKey ("browseable")
        if visible and string.lower (visible) == "yes":
            self.visible_check.set_active (True)
        else:
            self.visible_check.set_active (False)

        guest_ok = section.getKey ("guest ok")
        if guest_ok and string.lower (guest_ok) == "yes":
            self.guest_access_radio.set_active(True)
        else:
            self.user_access_radio.set_active(True)

        valid_users = section.getKey ("valid users")
        if valid_users:
            list = string.split (valid_users, ",")
            for item in list:
                userList.append(string.strip(item))

        invalid_users = section.getKey ("invalid users")
        if invalid_users and invalid_users == "%S":
            invalidUsers = invalid_users

        self.sharenamechanged = 0
        self.populateUserStoreOnEdit(userList, invalidUsers)
        self.share_window.show_all()

    def reset (self):
        self.share_notebook.set_current_page (0)
        self.dir_entry.set_text ("")
        self.sharename_entry.set_text ("")
        self.description_entry.set_text ("")
        self.valid_users_store.clear ()
        self.writable_check.set_active (False)
        self.visible_check.set_active (False)
        self.user_access_radio.set_active (True)
        self.share_window.hide ()
        self.sharenamechanged = 0

    def checkDirectoryValidity(self, dir):
        if string.strip(dir) == "":
            dlg = gtk.MessageDialog(self.share_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("You must specify a directory to share.  \n\n"
                                       "Click \"OK\" to continue.")))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_modal(True)
            dlg.set_transient_for(self.share_window)
            dlg.set_icon(mainWindow.iconPixbuf)            
            dlg.run()
            dlg.destroy()
            return 0

        try:
            os.stat(dir)
        except:
            dlg = gtk.MessageDialog(self.share_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("The directory \"%s\" does not exist.  Please specify "
                                       "an existing directory. \n\n"
                                       "Click \"OK\" to continue." % dir)))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_modal(True)
            dlg.set_transient_for(self.share_window)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.run()
            dlg.destroy()
            self.share_notebook.set_current_page(0)
            return 0                  

        return 1

    def checkShareNameValidity(self, sharename, path, oldsharename = None):
        msg = None
        buttons = None
        header = "[" + sharename + "]"

        if sharename == "":
            msg = _("Please set a share name.\n\nClick \"OK\" to continue.")
        elif (not oldsharename or oldsharename != sharename) and header in self.samba_data.getHeaders ():
            if header in self.samba_data.getShareHeaders ():
                msg = _("The share name \"%s\" already exists.") % (sharename)
            else:
                msg = _("The share name \"%s\" is reserved.") % (sharename)
            msg += _("\nPlease use a different share name.\n\nClick \"Suggest Share Name\" or \"OK\" to continue.")
            buttons = [(_("_Suggest Share Name"), 2), (gtk.STOCK_OK, 1)]
            self.share_notebook.set_current_page(0)

        if msg:
            dlg = gtk.MessageDialog (self.share_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE, msg)
            if buttons:
                for button in buttons:
                    dlg.add_button (button[0], button[1])
            else:
                dlg.add_button (gtk.STOCK_OK, 1)
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_modal(True)
            dlg.set_transient_for(self.share_window)
            dlg.set_icon(mainWindow.iconPixbuf)
            result = dlg.run()
            dlg.destroy()
            if result == 2:
                self.sharename_entry.set_text (self.suggestShareName (path, sharename))
                
            return False
        return True

    def suggestShareName (self, path, sharename = None):
        if self.section:
            ownsharename = string.strip (self.section.name, "[]")
        else:
            ownsharename = ""
        if not sharename or sharename == "":
            if path == "/":
                #Sharing the root is a special case
                sharename = "root directory"

            else:
                #Check to see if the path ends in a "/"  If it does, strip it off
                if path[-1:] == "/":
                    path = path[:-1]

                #If there are any /'s or \'s in the path, split by them
                if '/' in path:
                    tokens = string.split(path, "/")
                    #The last item in the token list is the directory name that we want
                    sharename = tokens[len(tokens)-1]

                #sharename = string.replace (sharename, " ", "_")

        if sharename and sharename != "" and sharename != ownsharename:
            #If there's already a section header with this name, then start adding numbers to it
            #until it's a unique name
            if ("[" + sharename + "]") in self.samba_data.getHeaders():
                count = 1
                while ("[" + sharename + "]") in self.samba_data.getHeaders():
                    sharename = sharename + "-" + str(count)
                    count = count + 1
        else:
            sharename = ownsharename
 
        return sharename

    def getValidUsers (self):
        all_users = []
        selected_users = []

        user_iter = self.valid_users_store.get_iter_first()
        while user_iter:
            #Crawl through the list and see which users are selected
            all_users.append(self.valid_users_store.get_value(user_iter, 1))
            if self.valid_users_store.get_value(user_iter, 0) == True:
                selected_users.append(self.valid_users_store.get_value(user_iter, 1))
            user_iter = self.valid_users_store.iter_next(user_iter)

        return (all_users, selected_users)

    def checkValidUsers (self, all_users, selected_users, section = None):
        if self.user_access_radio.get_active() == True:
            if selected_users == []:
                #No users are selected.  Make the user choose at least one.
                dlg = gtk.MessageDialog(self.share_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                        (_("Please allow access to at least one user.")))
                dlg.set_position(gtk.WIN_POS_CENTER)
                dlg.set_modal(True)
                dlg.set_transient_for(self.share_window)
                dlg.set_icon(mainWindow.iconPixbuf)
                dlg.run()
                dlg.destroy()
                self.share_notebook.set_current_page(1)
                return False
            elif section:
                #They have selected at least one user.
                section.setKey ("guest ok", "no")

                #if all_users == selected_users:
                #    #They want to allow all users.  Remove "invalid_users" and "valid users"
                #    section.delKey ("valid users")
                #    section.delKey ("invalid users")
                #else:
                #    #They want to allow a subset of all samba users.
                #    users = string.join(selected_users, ", ")
                #    section.setKey ("valid users", users)
                #    section.delKey ("invalid users")

                users = string.join(selected_users, ", ")
                section.setKey ("valid users", users)
                section.delKey ("invalid users")

        elif section and self.guest_access_radio.get_active() == True:
            section.setKey ("guest ok", "yes")
            section.delKey ("valid users")
            section.delKey ("invalid users")

        return True
 
    #################Event Handlers######################
    def onShareNameEntryChanged (self, *args):
        if self.sharename_entry.is_focus ():
            self.sharenamechanged = 1
        dir_header = "[" + self.sharename_entry.get_text() + "]"

        if self.edit_mode == 1:
            section = self.ParentClass.share_store.get_value(self.edit_iter, 5)
        else:
            section = sambaParser.SambaSection (prototype = True)
        if section.name != dir_header and dir_header in self.samba_data.getShareHeaders():
            count = 1
            while dir_header in self.samba_data.getShareHeaders():
                dir_header = "[" + string.strip(dir_header, "[]") + "-" + str(count) + "]"
                count = count + 1
            self.sharename_entry.set_text (string.strip(dir_header, "[]"))

    def onDirEntryChanged(self, *args):
        if self.sharenamechanged != 1:
            path = string.strip(self.dir_entry.get_text())
            sharename = self.suggestShareName(path)

            self.sharename_entry.set_text(sharename)

    def onOkButtonClicked(self, *args):
        if self.edit_mode:
            oldsharename = self.ParentClass.share_store.get_value(self.edit_iter, 1)
        else:
            oldsharename = None
        # Get the path from the widget
        path = self.dir_entry.get_text()
        # Strip off any whitespace
        path = string.strip(path)

        # Get the sharename and strip off any whitespace
        sharename = string.strip(self.sharename_entry.get_text(), "\n[]")

        # Question: Are there other characters that are invalid for the sharename?
        # Is space invalid? Afaik not
        # sharename = string.replace (sharename, " ", "_")

        #Check to see if directory exists
        if not self.checkDirectoryValidity(path):
            return

        #Check to see whether the share name is valid, not duplicate, ...
        if not self.checkShareNameValidity(sharename, path, oldsharename):
            return
        dir_header = "[" + sharename + "]"

        #Check to see if any users are selected.  This will be useful to us later
        (all_users, selected_users) = self.getValidUsers ()
        if not self.checkValidUsers (all_users, selected_users):
            return

        if not self.edit_mode:
            #Ok, things are good now.  Start adding to the share_store
            iter = self.ParentClass.share_store.append()
            self.ParentClass.share_store.set_value(iter, 0, path)
            self.ParentClass.share_store.set_value(iter, 1, sharename)

            #create a blank line token
            last_section = self.samba_sections_dict[self.samba_sections[-1]]
            if last_section.content[-1].getData() != "\n":
                token = self.samba_data.createToken("", last_section)
                last_section.content.append(token)

            section = sambaParser.SambaSection (dir_header)
        else:
            iter = self.edit_iter
            section = self.ParentClass.share_store.get_value (iter, 5)

            # section contains [the old sharename] of course
            # If the new name differs from the old one, we will need to rename
            oldsharename = string.strip (section.name, "\n[]")
            if sharename != oldsharename:
                section.set_name (dir_header)

        #create token for the description if it exists
        description = string.strip(self.description_entry.get_text())

        if description != "":
            while description[-1] == "\\" or description[-1] == " ":
                #If description ends in a backslash, chop it off b/c it confuses Windows
                description = description[:-1]
            section.setKey ("comment", description)
            self.ParentClass.share_store.set_value(iter, 4, description)

        #set token for the path
        section.setKey ("path", path)
        #set path in main window
        self.ParentClass.share_store.set_value (iter, 0, path)

        #set sharename in main window
        self.ParentClass.share_store.set_value (iter, 1, sharename)

        #set token(s) for permissions        
        if self.writable_check.get_active() == False:
            self.ParentClass.share_store.set_value(iter, 2, (_("Read Only")))
            section.setKey ("read only", "yes")
        else:
            self.ParentClass.share_store.set_value(iter, 2, (_("Read/Write")))
            section.setKey ("read only", "no")

        #set token(s) for browsable
        if self.visible_check.get_active() == True:
            self.ParentClass.share_store.set_value(iter, 3, (_("Visible")))
            section.setKey ("browsable", "yes")
        else:
            self.ParentClass.share_store.set_value(iter, 3, (_("Hidden")))
            section.setKey ("browsable", "no")

        if self.guest_access_radio.get_active() == True:
            #set token for guest access
            section.setKey ("guest ok", "yes")
            section.delKey ("valid users")
            section.delKey ("invalid users")
        else:
            #if all_users != selected_users:
            #    #They have selected a subset of all samba users.
            #    users = string.join(selected_users, ", ")
            #    section.setKey ("valid users", users)
            users = string.join(selected_users, ", ")
            section.delKey ("guest ok")
            section.setKey ("valid users", users)

        self.ParentClass.share_store.set_value(iter, 5, section)            
        self.ParentClass.properties_button.set_sensitive(False)
        self.ParentClass.delete_button.set_sensitive(False)
        self.ParentClass.share_view.get_selection().unselect_all()
        self.reset()

        #Let's go ahead and restart the service.
        self.samba_data.writeFile()
        self.samba_backend.restartSamba()

    def FOOonOkEditButtonClicked(self, *args):
        section = self.ParentClass.share_store.get_value(self.edit_iter, 5)
        oldsharename = self.ParentClass.share_store.get_value(self.edit_iter, 1)

        dir = self.dir_entry.get_text()
        dir = string.strip(dir)

        # Get the sharename and strip off any whitespace
        sharename = string.strip(self.sharename_entry.get_text(), "\n[]")

        #Check to see if directory exists
        if not self.checkDirectoryValidity(dir):
            return

        #Check to see whether the share name is valid, not duplicate, ...
        if not self.checkShareNameValidity(sharename, dir, oldsharename):
            return
        dir_header = "[" + sharename + "]"

        #Check to see if any users are selected.  This will be useful to us later
        (all_users, selected_users) = self.getValidUsers ()
        if not self.checkValidUsers (all_users, selected_users, section):
            return

        # section contains [the old sharename] of course
        # If the new name differs from the old one, we will need to rename
        oldsharename = string.strip (section.name, "\n[]")
        if sharename != oldsharename:
            self.ParentClass.share_store.set_value(self.edit_iter, 1, sharename)
            section.set_name (dir_header)

        self.ParentClass.share_store.set_value(self.edit_iter, 0, dir)
        section.setKey ("path", dir)

        if self.writable_check.get_active() == False:
            self.ParentClass.share_store.set_value(self.edit_iter, 2, (_("Read Only")))
            section.setKey ("writeable", "no")
        else:
            self.ParentClass.share_store.set_value(self.edit_iter, 2, (_("Read/Write")))
            section.setKey ("writeable", "yes")

        if self.visible_check.get_active() == True:
            self.ParentClass.share_store.set_value(self.edit_iter, 3, (_("Visible")))
            section.setKey ("browsable", "yes")
        else:
            self.ParentClass.share_store.set_value(self.edit_iter, 3, (_("Hidden")))
            section.setKey ("browsable", "no")

        description = string.strip(self.description_entry.get_text())

        if description != "":
            while description[-1] == "\\" or description[-1] == " ":
                #If description ends in a backslash, chop it off b/c it confuses Windows
                description = description[:-1]

        if description == "":
            self.ParentClass.share_store.set_value(self.edit_iter, 4, description)
            section.delKey ("comment")
        else:
            self.ParentClass.share_store.set_value(self.edit_iter, 4, description)
            section.setKey ("comment", description)

        self.ParentClass.properties_button.set_sensitive(False)
        self.ParentClass.delete_button.set_sensitive(False)
        self.ParentClass.share_view.get_selection().unselect_all()
        self.reset()

        #Let's go ahead and restart the service.
        self.samba_data.writeFile()
        self.samba_backend.restartSamba()

    def onCancelButtonClicked(self, *args):
        self.reset()
        return True

    def onBrowseButtonClicked(self, *args):
        dlg = gtk.FileChooserDialog (_("Select Directory"), self.share_window,
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                (
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_OK, gtk.RESPONSE_OK
                )
            )
        filename = self.dir_entry.get_text ()
        if filename.strip () != "":
            dlg.set_filename (filename)
        
        result = dlg.run()
        
        if result == gtk.RESPONSE_OK:
            filename = dlg.get_filename()
            self.dir_entry.set_text(dlg.get_filename())

        dlg.destroy()

    def userRadioToggled(self, *args):
        self.valid_users_treeview.set_sensitive(self.user_access_radio.get_active())
