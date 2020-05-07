## sambaDefaults.py - default values for smb.conf data structure
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
import re

__all__ = ['global_keys', 'section_keys', 'synonym_dict', 'inverted_synonym_dict', 'nomask_default_list', 'get_default']

nomask_default_list = [
    'security',
    'workgroup'
]

section_keys_list = [
    '-valid',
    'acl compatibility',
    'acl check permissions',
    'admin users',
    'afs share',
    'allow hosts',
    'available',
    'blocking locks',
    'block size',
    'browsable',
    'browseable',
    'case sensitive',
    'casesignames',
    'comment',
    'copy',
    'create mask',
    'create mode',
    'csc policy',
    'cups options',
    'default case',
    'default devmode',
    'delete readonly',
    'delete veto files',
    'deny hosts',
    'directory mask',
    'directory mode',
    'directory',
    'directory security mask',
    'dont descend',
    'dos filemode',
    'dos filetime resolution',
    'dos filetimes',
    'ea support',
    'exec',
    'fake directory create times',
    'fake oplocks',
    'follow symlinks',
    'force create mode',
    'force directory mode',
    'force directory security mode',
    'force group',
    'force security mode',
    'force unknown acl user',
    'force user',
    'fstype',
    'group',
    'guest ok',
    'guest only',
    'hide dot files',
    'hide files',
    'hide special files',
    'hide unreadable',
    'hide unwriteable files',
    'hosts allow',
    'hosts deny',
    'inherit acls',
    'inherit permissions',
    'invalid users',
    'level2 oplocks',
    'locking',
    'lppause command',
    'lpq command',
    'lpresume command',
    'lprm command',
    'magic output',
    'magic script',
    'mangle case',
    'mangled map',
    'mangled names',
    'mangling char',
    'map acl inherit',
    'map archive',
    'map hidden',
    'map system',
    'max connections',
    'max print jobs',
    'max reported print jobs',
    'min print space',
    'msdfs proxy',
    'msdfs root',
    'nt acl support',
    'only user',
    'only guest',
    'oplock contention limit',
    'oplocks',
    'path',
    'posix locking',
    'postexec',
    'postscript',
    'preexec',
    'preexec close',
    'preserve case',
    'print command',
    'printable',
    'printcap name',
    'printer admin',
    'printer driver',
    'printer driver location',
    'printer name',
    'printer',
    'printing',
    'print ok',
    'profile acls',
    'public',
    'queuepause command',
    'queueresume command',
    'read list',
    'read only',
    'root postexec',
    'root preexec',
    'root preexec close',
    'security mask',
    'set directory',
    'share modes',
    'short preserve case',
    'status',
    'store dos attributes',
    'strict allocate',
    'strict locking',
    'strict sync',
    'sync always',
    'use client driver',
    'username',
    'user',
    'users',
    'use sendfile',
    'valid users',
    'veto files',
    'veto oplock files',
    'vfs object',
    'vfs objects',
    'vfs options',
    'volume',
    'wide links',
    'writeable',
    'writable',
    'write cache size',
    'write list',
    'write ok'
    ]

synonym_dict = {
    'browseable' : ['browsable'],
    'case sensitive' : ['casesignames'],
    'create mask' : ['create mode'],
    'debug timestamp' : ['timestamp logs'],
    'default service' : ['default'],
    'directory mask' : ['directory mode'],
    'force group' : ['group'],
    'guest ok' : ['public'],
    'guest only' : ['only guest'],
    'hosts allow' : ['allow hosts'],
    'hosts deny' : ['deny hosts'],
    'idmap gid' : ['winbind gid'],
    'idmap uid' : ['winbind uid'],
    'lock directory' : ['lock dir'],
    'log level' : ['debuglevel'],
    'max protocol' : ['protocol'],
    'min password length' : ['min passwd length'],
    'path' : ['directory'],
    'preexec' : ['exec'],
    'preferred master' : ['prefered master'],
    'preload' : ['auto services'],
    'printable' : ['print ok'],
    'printcap name' : ['printcap'],
    'printer name' : ['printer'],
    'root directory' : ['root', 'root dir'],
    'username' : ['user', 'users'],
    'vfs objects' : ['vfs object'],
    'writeable' : ['writable'],
    }

inverted_synonym_dict = {
    'writeable' : ['read only'],
    'write ok' : ['read only']
    }

# overrides, presets (e.g. keys not mentioned by testparm)
global_keys = {
        'client ntlmv2 auth' : "no",
        'iprint server' : None,
        'nis homedir' : "no"
        }
section_keys = {
        '-valid' : "yes",
        'read only': "yes"
        }

kv_re = re.compile (r'^\s*(?P<key>[^=]*[^=\s])\s*=\s*(?P<value>.*\S)?\s*$')

p = os.popen ('/usr/bin/testparm -s -v /dev/null 2>/dev/null')

while True:
    line = p.readline ()
    if len(line) == 0:
        break
    m = kv_re.match (line)
    if m:
        key = m.group ('key').lower ()
        value = m.group ('value')
        if value:
            value = value.lower ()
        if key in section_keys_list:
            if key not in section_keys.keys ():
                section_keys[key] = value
        else:
            if key not in global_keys.keys ():
                global_keys[key] = value

p.close ()

for isynkey in inverted_synonym_dict.keys ():
    isynvalue = inverted_synonym_dict[isynkey][0]
    if isynvalue in global_keys.keys ():
        list = global_keys
    elif isynvalue in section_keys.keys ():
        list = section_keys
    else:
        raise LookupError, "isynkey %s value %s not in global_keys or section_keys" % (isynkey, inverted_synonym_dict[isynkey][0])

    ivdict = {
            'yes': 'No',
            '1': '0',
            'true': 'False',
            'no': 'Yes',
            '0': '1',
            'false': 'True'
            }

    value = list[isynvalue].lower()
    try:
        ivalue = ivdict[value]
    except KeyError:
        raise ValueError, "no inversion possible for '%s'" % (value)

    list[isynkey] = ivalue

for synkey in synonym_dict.keys ():
    if synkey in global_keys.keys ():
        list = global_keys
    elif synkey in section_keys.keys ():
        list = section_keys
    else:
        # allow unknown synonyms to handle different samba versions
        continue

    for synonym in synonym_dict[synkey]:
        list[synonym] = list[synkey]

def get_default (keyname):
    if keyname in global_keys.keys ():
        default = global_keys[keyname]
    elif keyname in section_keys.keys ():
        default = section_keys[keyname]
    else:
        default = None
    return default
