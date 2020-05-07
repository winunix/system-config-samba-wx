## sambaToken.py - data structure for system-config-samba
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

from sambaDefaults import *
import string

def sambaTokenCanonicalNameValue (keyname, keyval):
    inverted = False
    # We need a sane way of handling samba keyname synonyms.
    # Otherwise we could have conflicting tags.
    for key in synonym_dict.keys ():
        if string.lower (keyname) in synonym_dict [key]:
            # We've found a synonym, so convert it to the real keyname
            keyname = key
            break

    # Now we need to check for the insane concept of inverted keynames.
    for key in inverted_synonym_dict.keys ():
        if string.lower (keyname) in inverted_synonym_dict[key]:
            # We've found a synonym, so convert it to the real keyname
            keyname = key

            # Now we need to invert the value.
            # AFAIK, the inverted case is only for yes/no values.
            if string.lower (keyval) == "no":
                keyval = "yes"
            elif string.lower (keyval) == "yes":
                keyval = "no"
            inverted = True
            break

    return (keyname, keyval, inverted)

class SambaToken:
    SAMBA_TOKEN_STRING = 1
    SAMBA_TOKEN_SECTION_HEADER = 2
    SAMBA_TOKEN_KEYVAL = 3
    SAMBA_TOKEN_BLANKLINE = 4
    
    def __init__(self, type, value, comment = None, accept_unknown = False):

        self.unknown = False
        if type == SambaToken.SAMBA_TOKEN_KEYVAL:
            if value[0] not in section_keys.keys() and value[0] not in global_keys.keys():
                if not accept_unknown:
                    raise AttributeError, value
                self.unknown = True

            self.keyname = value[0]
            self.keyval = value[1]

            if self.keyname.lower () in nomask_default_list:
                self.mask_default = False
            else:
                self.mask_default = True

        self.type = type
        self.value = value
        self.comment = comment

    def canonicalNameValue (self):
        return sambaTokenCanonicalNameValue (self.keyname, self.keyval)

    def getData(self):
        if self.type == SambaToken.SAMBA_TOKEN_STRING:
            return ("%s\n" % self.value)
        elif self.type == SambaToken.SAMBA_TOKEN_SECTION_HEADER:
            return ("%s\n" % self.value)
        elif self.type == SambaToken.SAMBA_TOKEN_KEYVAL:
            default_mask = False
            default = get_default (self.keyname)

            if default:
                default = string.lower(str(default))
            if default == None and self.keyval == None:
                return
            elif default == string.lower(str(self.keyval)):
                default_mask = True

            if default_mask and self.mask_default:
                default_mask_char = ';'
            else:
                default_mask_char = '';

            if self.comment:
                return ("%s\t%s = %s \t#%s\n" % (default_mask_char, self.keyname, self.keyval, self.comment))
            else:
                return ("%s\t%s = %s\n" % (default_mask_char, self.keyname, self.keyval))
            
        elif self.type == SambaToken.SAMBA_TOKEN_BLANKLINE:
            return "\n"

    def __repr__(self):
        d = self.getData ()
        if d:
            d = string.strip (d)
        else:
            d = ''
        return "<%s instance %d: '%s'>" % (self.__class__.__name__, self.type, d)
