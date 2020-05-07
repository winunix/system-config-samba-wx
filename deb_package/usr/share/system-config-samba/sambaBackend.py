## sambaBackend.py - contains the backend code for system-config-samba
## Copyright (C) 2002 - 2007 Red Hat, Inc.
## Copyright (C) 2002, 2003 Brent Fox <bfox@redhat.com>

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See then
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

## Authors:
## Brent Fox <bfox@redhat.com>
## Nils Philippsen <nphilipp@redhat.com>

import string
import os
import re

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)

class SambaBackend:

    def isSambaRunning (self):
		return os.path.exists('/var/run/samba/smbd.pid')

    def startSamba(self):
        os.system ('/usr/sbin/invoke-rc.d samba start > /dev/null')

    def restartSamba(self):
        os.system ('/usr/sbin/invoke-rc.d samba restart > /dev/null')
