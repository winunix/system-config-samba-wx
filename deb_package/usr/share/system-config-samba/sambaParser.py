## sambaParser.py - the smb.conf file parser for system-config-samba
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

import os
import errno
import gtk
import sambaToken
import mainWindow
from sambaDefaults import global_keys
from sambaDefaults import section_keys
import sambaDefaults

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)

class SambaSection:
    sections = []
    sections_dict = {}

    def __init__ (self, name = None, prototype = False):
        #print "SambaSection.__init__ (name = %s, prototype = %s)" % (name, prototype)
        self.name = None
        self.content = []
        if not prototype and not self.set_name (name):
            raise Error ("section %s already defined" % (name))
        #print "SambaSection.sections:", SambaSection.sections
        #print "SambaSection.sections_dict.keys ():", SambaSection.sections_dict.keys ()

    def __str__ (self):
        str = ""
        if self.name:
            str += "%s\n" % (self.name)
        for token in self.content:
            tokendata = token.getData ()
            if tokendata:
                # no default value
                if tokendata.strip () == "None":
                    raise Exception ("refusing to write illegal token %s which would yield %s" % (token, tokendata))
                else:
                    str += "%s" % (token.getData ())
        return str

    def __repr__ (self):
        contentstrings = []
        for token in self.content:
            contentstrings.append (repr (token))
        if self.name:
            name = self.name
        else:
            name = "preambel"
        return "<%s instance %s:\n%s\n>" % (self.__class__.__name__, name, "\n".join (contentstrings))

    def delete (self):
        #print "SambaSection.delete (%s)" % (self)
        #print "sections before:", SambaSection.sections
        #print "sections_dict before", SambaSection.sections
        name = self.name.lower ()
        if name and SambaSection.sections_dict.has_key (name):
            #print "  deleting from sections_dict"
            del SambaSection.sections_dict[name]
        if name in SambaSection.sections:
            #print "  deleting from sections"
            SambaSection.sections.remove (name)
        #print "sections after:", SambaSection.sections
        #print "sections_dict after", SambaSection.sections
        del (self)

    def set_name (self, newname):
        #print "SambaSection.set_name (%s)" % (newname)
        if type (newname) == str:
            if newname[0] != "[" and newname[-1] != "]":
                raise Exception ("section name must be enclosed in brackets")
            _newname = newname.lower ()
        else:
            _newname = newname
        if not newname in SambaSection.sections:
            if self.name:
                SambaSection.sections[SambaSection.sections.index (self.name.lower ())] = newname.lower ()
                del SambaSection.sections_dict[self.name.lower ()]
            else:
                SambaSection.sections.append (_newname)
            self.name = newname
            SambaSection.sections_dict[_newname] = self
            #print "--SambaSection.sections:", SambaSection.sections
            #print "--SambaSection.sections_dict.keys ():", SambaSection.sections_dict.keys ()
            return True
        return False

    def fetchKey (self, name):
        #print "SambaSection.fetchKey (%s)" % name
        canonicalName = sambaToken.sambaTokenCanonicalNameValue (name, "")[0]
        #print "\tcanonicalName", canonicalName
        for token in self.content:
            if token.type == sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL:
                if token.canonicalNameValue ()[0].lower () == canonicalName.lower ():
                    #print "\ttoken", token
                    return token

    def keyExists (self, name):
        if self.fetchKey (name):
            return True
        else:
            return False

    def getKey (self, name):
        # returns canonical names and values
        token = self.fetchKey (name)
        if token:
            (keyname, keyval, inverted) = token.canonicalNameValue ()
            if inverted:
                # revert to non inverted value
                if keyval.lower () == "no":
                    keyval = "yes"
                elif keyval.lower () == "yes":
                    keyval = "no"
            return keyval
        else:
            # no explicit token found, assume default
            return sambaDefaults.get_default (name)

    def setKey (self, name, value, comment = None):
        #print "SambaSection.setKey (name = '%s', value = '%s', comment = '%s')" % (name, value, comment)
        #print "content before", self.content
        token = self.fetchKey (name)
        (name, value, inverted) = sambaToken.sambaTokenCanonicalNameValue (name, value)
        if token:
            self.content[self.content.index (token)] = sambaToken.SambaToken (sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL, (name, value), token.comment)
        else:
            #print "\tcreating new token (%s/%s)" % (name, value)
            token = sambaToken.SambaToken (sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL, (name, value), comment)
            # insert before eventual blank lines or comments (which may as well
            # be for the next section)
            index = len (self.content) - 1
            while index >= 0 and (self.content[index].type == sambaToken.SambaToken.SAMBA_TOKEN_STRING or self.content[index].type == sambaToken.SambaToken.SAMBA_TOKEN_BLANKLINE):
                index -= 1
            self.content.insert (index + 1, token)
            if index == len (self.content) - 1:
                self.content.append (sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_BLANKLINE, (stripped_line)))
        #print "content after", self.content

    def delKey (self, name):
        #print "SambaSection.delKey (%s)" % name
        #print "content before", self.content
        token = self.fetchKey (name)
        if token:
            self.content.remove (token)
            del token
        #print "content after", self.content

def SambaSection_reset ():
    SambaSection.sections = []
    for name, section in SambaSection.sections_dict.iteritems ():
        del SambaSection.sections_dict[name]
        del section
    SambaSection.sections_dict = {}

class SambaParser:
    def __init__(self, parent):
        self.ParentClass = parent
        self.warnings = []
        self.parseFile ()

    def parseFile(self):
        path = "/etc/samba/smb.conf"
        lines = []
        # reset SambaSection lists of sections
        SambaSection_reset ()
        self.sections = SambaSection.sections
        self.sections_dict = SambaSection.sections_dict

        if os.access(path, os.F_OK) == 0:
            #If path doesn't exist, read template
            path = "/usr/share/system-config-samba/smb.conf.template"
        
        if os.access(path, os.R_OK) == 1:
            #Check to see if we can read from the file
            fd = open(path, 'r')
            lines = fd.readlines()
            fd.close()
        else:
            #The file exists, but we can't read it.  Not much we can do now but quit.
            dlg = gtk.MessageDialog(self.ParentClass.main_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("Cannot read %s.  Program will now exit." % path)))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_modal(True)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.run()
            dlg.destroy()
            if gtk.__dict__.has_key ("main_quit"):
                gtk.main_quit ()
            else:
                gtk.mainquit()
            raise RuntimeError, (_("Cannot read %s.  Program will now exit." % path))
        
        if lines:
            section = SambaSection (None)

            lineno = 0
            for line in lines:
                lineno += 1
                token = self.createToken (line, section) 
                if token:
                    if token.type == sambaToken.SambaToken.SAMBA_TOKEN_SECTION_HEADER:
                        section = SambaSection (token.value)
                    else:
                        #If the token is valid, then add it
                        section.content.append (token)
                        if token.unknown:
                            self.warnings.append ([lineno, token])

    def createToken(self, line, section):
        # eat trailing newline
        if len (line) > 0 and line[-1] == '\n':
            line = line[:-1]

        stripped_line = line.strip ()
        if stripped_line != "":
            tmp = tuple(stripped_line)
        else:
            token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_BLANKLINE, (line))
            return token

        if tmp:
            if tmp[0] == "#" or tmp[0] == ";":
                try:
                    commented_section = stripped_line[1:].strip ()
                    if commented_section[0] == '[' and commented_section[-1] == ']':
                        # we found a commented out section, treat commented out
                        # key value pairs as comments from now on until next
                        # section, e.g. for example sections
                        self.honour_default_value_comments = False
                except IndexError:
                    pass

            if tmp[0] == "#":
                #The line begins with a "#"
                token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_STRING, (line))
                return token

            elif tmp[0] == ";":
                # possibly a commented out default key value
                name = None
                try:
                    name, value = line.split ("=", 1)
                    name = name[1:].strip ()
                    value = value.strip ()
                except ValueError:
                    pass

                if name and self.honour_default_value_comments:
                    if not self.isDuplicateKey(name, section):
                        default_value = sambaDefaults.get_default (name)
                        try:
                            if value.lower () == default_value.lower ():
                                token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL, (name, default_value))
                                return token
                        except AttributeError:
                            pass
                    else:
                        return None

                # possibly just a comment
                token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_STRING, (line))
                return token

            elif tmp[0] == "[" and tmp[-1] == "]":
                #The line contains a section header
                token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_SECTION_HEADER, (line), None)
                # honour commented out key value pairs from now on
                self.honour_default_value_comments = True
                return token

            else:
                #The line isn't a section header and is probably a key/value line
                comment_token = None

                #See if there are any comments at the end of the line
                if "#" in line:
                    data, comment = line.split ("#", 1)
                    comment_token = comment
                    line = data
                else:
                    #There are no comments in the line
                    data = line

                name, value = line.split ("=", 1)
                name = name.strip ()
                value = value.strip ()

                if comment_token:
                    token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL, (name, value), comment_token)
                    return token
                else:
                    if not self.isDuplicateKey(name, section):
                        try:
                            token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL, (name, value))
                            return token
                        except AttributeError:
                            token = sambaToken.SambaToken(sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL, (name, value), accept_unknown = True)
                            return token
                    else:
                        #We've found a duplicate key, so return none.  This keeps duplicates from being
                        #added to the list
                        return None

    def writeFile(self):
        path = "/etc/samba/smb.conf"
        try:
            oldmode = os.stat ("path")[0] & 07777
        except OSError:
            oldmode = 0644
        if os.access (path, os.W_OK) == 1 and os.access (os.path.dirname (path), os.W_OK) == 1:
            try:
                os.unlink (path + ".new")
            except OSError, e:
                if e.errno != errno.ENOENT:
                    raise e
            fd = open(path + ".new", 'w', oldmode)
        else:
            dlg = gtk.MessageDialog(self.ParentClass.main_window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("Cannot write to %s.  Program will now exit." % path)))
            dlg.set_modal(True)
            dlg.set_icon(mainWindow.iconPixbuf)
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.run()
            dlg.destroy()
            if gtk.__dict__.has_key ("main_quit"):
                gtk.main_quit ()
            else:
                gtk.mainquit()
            raise RuntimeError, (_("Cannot write to %s.  Program will now exit." % path))
        

        if fd:
            for name in SambaSection.sections:
                lines = str (self.getSection (name))
                if lines:
                    fd.write(lines)
            fd.close()

        os.rename (path + ".new", path)

    def printSections (self):
        for name in self.getSections ():
            print str (self.getSection (name))
        
    def getSections (self):
        return self.sections

    def getSection (self, name):
        #print "getSection (%s)" % name
        return self.sections_dict[name]

    def getShareHeaders(self):
        header_list = self.getHeaders ()
        share_header_list = []
        for header in header_list:
            if header != "[global]" and header != "[printers]" and header != "[homes]":
                share_header_list.append (header)
        return share_header_list

    def getHeaders(self):
        header_list = []
        for name in self.sections:
            if name:
                header_list.append (name)
        return header_list

    def isDuplicateKey (self, name, section):
        return section.keyExists (name)
