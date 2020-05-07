## sambaUserData.py - contains code to handle samba users
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

import string
import os
import gtk
import mainWindow

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)
gtk.glade.bindtextdomain(domain)

pdbeditcmd = '/usr/bin/pdbedit'

class SambaUserData:
    def __init__(self, parent):
        self.ParentClass = parent

        self.samba_passwd_file = []
        self.samba_users_file = []

        self.readSmbPasswords()
        self.readSmbUsersFile()      

    def readSmbPasswords (self):
        # Try to read the Samba passwords
        list = []

        fd = os.popen ('%s -L -w 2>/dev/null' % (pdbeditcmd), 'r')

        for line in fd.readlines ():
            if string.strip(line)[0] != "#":
                list.append(line)
        status = fd.close()

        if not status or os.WEXITSTATUS (status) == 0:
            self.samba_passwd_file = list
        else:
            raise RuntimeError, (_("You do not have permission to execute %s." % pdbeditcmd))


    def readSmbUsersFile(self):
        path = '/etc/samba/smbusers'

        if os.access(path, os.F_OK) == 1:
            #The file exists.  Now check to see if we can read it or not

            if os.access(path, os.R_OK) == 1:
                fd = open('/etc/samba/smbusers', 'r')
                lines = fd.readlines()
                fd.close()
                self.samba_users_file = lines
            else:
                raise RuntimeError, (_("Cannot read %s.  Program will now exit." % path))

    def getPasswdFile(self):
        return self.samba_passwd_file

    def getUsersFile(self):
        return self.samba_users_file

    def getUserDict(self):
        user_dict = {}
        for line in self.samba_users_file:
            tmp_line = string.strip(line)
            if tmp_line and tmp_line[0] != '#':
                tokens = string.split(tmp_line, '=')
                user_dict[string.strip(tokens[0])] = line
        return user_dict

    def writeSmbUsersFile(self):
        path = '/etc/samba/smbusers'
        if os.access(path, os.W_OK) == 1:
            fd = open(path, 'w')
        elif os.access(path, os.F_OK) == 0:
            fd = open(path, 'w')
        else:
            dlg = gtk.MessageDialog(self.ParentClass.main_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("Cannot write to %s.  Program will now exit." % path)))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_modal(True)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.run()
            dlg.destroy()
            if gtk.__dict__.has_key ("main_quit"):
                gtk.main_quit ()
            else:
                gtk.mainquit()
            raise RuntimeError, (_("You do not have permission to write to %s.  Program will now exit." % path))
            
        for line in self.samba_users_file:
            fd.write(line)

        fd.close()
            
    def addUser(self, unix_name, windows_name, password):
        line = unix_name + " = " + windows_name + '\n'
        self.samba_users_file.append(line)
        self.writeSmbUsersFile()

        pipe = os.popen ('/usr/bin/smbpasswd -a -s "%s"' % (unix_name), "w")
        for i in (1, 2):
            pipe.write ("%s\n" % (password))
        pipe.close ()
        
        self.readSmbPasswords()
        self.readSmbUsersFile()

    def changePassword(self, unix_name, password):
        pipe = os.popen('/usr/bin/smbpasswd -s "%s"' % (unix_name), "w")
        for i in (1, 2):
            pipe.write ("%s\n" % (password))
        pipe.close ()

    def changeWindowsUserName(self, unix_name, windows_name):
        userDict = self.getUserDict()

        found = 0
        for line in self.samba_users_file:
            try:
                if line == userDict[unix_name]:
                    new_line = unix_name + " = " + windows_name + '\n'
                    self.samba_users_file[self.samba_users_file.index(line)] = new_line
                    found = 1
            except:
                pass

        if not found:
            #There's no current entry in smbusers
            line = unix_name + " = " + windows_name + '\n'
            if unix_name != windows_name:
                self.samba_users_file.append(line)
                self.writeSmbUsersFile()
                self.readSmbPasswords()
                self.readSmbUsersFile()

        self.writeSmbUsersFile()
        self.readSmbUsersFile()

    def deleteUser (self, name, line):
        # Remove the user from the smbpasswd file/tdb/ldap
        os.system ('%s -x -u "%s" >/dev/null' % (pdbeditcmd, name))

        # Get a dict of the smbusers file
        user_dict = self.getUserDict ()
        user_keys = user_dict.keys ()

        # If this user had an entry in smbusers, remove that line
        if name in user_keys:
            self.samba_users_file.remove (user_dict[name])

        self.writeSmbUsersFile ()
        self.readSmbUsersFile ()
        self.readSmbPasswords ()

    def getWindowsName(self, line):
        tokens = string.split(line, '=')
        windows_name = string.strip(tokens[1])
        return windows_name

    def userAlreadyExists (self, user):
        # Check to see if the user is already in the smbusers file
        self.readSmbUsersFile ()
        for line in self.samba_users_file:
            tokens = string.split (line)
            if tokens and user == tokens[0]:
                return 1

        # Check to see if the user is already in the smbpasswd file/tdb/ldap
        self.readSmbPasswords ()
        for line in self.samba_users_file:
            tokens = string.split (line)
            if tokens and user == tokens[0]:
                return 1

        return None
