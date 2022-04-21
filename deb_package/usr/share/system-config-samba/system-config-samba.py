#!/usr/bin/python2

## system-config-samba.py - Contains the startup script for system-config-samba
## Copyright (C) 2002 - 2004 Red Hat, Inc.
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
import sys
import signal

if __name__ == "__main__":
    signal.signal (signal.SIGINT, signal.SIG_DFL)

debug_flag = None
if '--debug' in sys.argv:
    debug_flag = 1

try:
    import gtk
except:
    print ("system-config-samba requires a currently running X server.")
    sys.exit(0)

os.umask (0022)

import mainWindow
mainWindow.MainWindow(debug_flag)
