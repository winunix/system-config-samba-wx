## mainWindow.py - Contains the main UI for system-config-samba
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

import sambaBackend
import sambaParser
import sambaToken
import gtk
import gobject
import string
import os
import gtk.glade
import basicPreferencesWin
import sambaUserWin
import sambaUserData
import shareWindow

##
## I18N
##
from gettext import gettext as _
import gettext as translate
domain = 'system-config-samba'
translate.textdomain (domain)
gtk.glade.bindtextdomain(domain)

##
## Icon for windows
##

iconPixbuf = None      
try:
    iconPixbuf = gtk.gdk.pixbuf_new_from_file("/usr/share/system-config-samba/pixmaps/system-config-samba.png")
except:
    pass

class MainWindow:
    def __init__(self, debug_flag=None):
        self.debug_flag = debug_flag

        if os.access("system-config-samba.glade", os.F_OK):
            self.xml = gtk.glade.XML ("system-config-samba.glade", domain="system-config-samba")
        else:
            self.xml = gtk.glade.XML ("/usr/share/system-config-samba/system-config-samba.glade", domain="system-config-samba")

            
#        [0 dir, 1 hosts, 2 permissions, 3 visibility, 4 description, 5 sambaDataObject]
        self.share_store = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_PYOBJECT)

        self.main_window = gtk.Window()
        self.main_window.set_title(_("Samba Server Configuration"))
        self.main_window.connect("delete-event", self.destroy)
        self.main_window.set_position(gtk.WIN_POS_CENTER)
        self.main_window.set_icon(iconPixbuf)
        self.nameTag = _("Samba")
        self.commentTag = _("Create, modify, and delete samba shares")

        #Initialize Global Samba data store
        self.samba_data = sambaParser.SambaParser(self)
        self.processSambaData(self.samba_data)

        #Check if there are warnings
        if len (self.samba_data.warnings):
            warnings_dialog = self.xml.get_widget ('warnings_dialog')
            warnings_details_expander = self.xml.get_widget ('warnings_details_expander')
            warnings_details_expander_label = self.xml.get_widget ('warnings_details_expander_label')
            warnings_details_textview = self.xml.get_widget ('warnings_details_textview')

            def exp_activate (expander, data = None):
                if expander.get_expanded ():
                    warnings_details_expander_label.set_text (_('Hide _details'))
                else:
                    warnings_details_expander_label.set_text (_('Show _details'))

            warnings_details_expander.set_expanded (False)
            exp_activate (warnings_details_expander)
            warnings_details_expander.connect ('activate', exp_activate)

            warnings_details_text = "\n".join (map (lambda x: "%d: %s" % (x[0], x[1].getData ()), self.samba_data.warnings))

            warnings_details_textview.get_buffer ().set_text (warnings_details_text)
            warnings_dialog.set_position (gtk.WIN_POS_CENTER)
            warnings_dialog.set_modal (True)
            warnings_dialog.set_transient_for (self.main_window)
            warnings_dialog.set_icon (iconPixbuf)
            warnings_dialog.run ()
            warnings_dialog.hide ()

        #Initialize Samba Backend
        self.samba_backend = sambaBackend.SambaBackend()

        #Initialize Samba User Backend
        self.samba_user_data = sambaUserData.SambaUserData(self)

        #Initialize Samba User Window
        self.samba_user_win = sambaUserWin.SambaUserWin(self, self.xml, self.samba_user_data, self.main_window)

        self.basic_preferences_win = basicPreferencesWin.BasicPreferencesWin(self, self.xml, self.samba_data, self.samba_backend, self.main_window)
        self.share_win = shareWindow.ShareWindow(self, self.xml, self.samba_data, self.samba_user_data, self.samba_backend, self.main_window)
        
        self.toplevel_vbox = gtk.VBox(False)
        self.menu_bar = gtk.MenuBar()

        self.share_view = gtk.TreeView(self.share_store)
        self.share_view.set_rules_hint(True)
        self.share_view.columns_autosize()
        self.share_view_sw = gtk.ScrolledWindow()
        self.share_view_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.share_view_sw.set_shadow_type(gtk.SHADOW_IN)
        self.share_view_sw.add(self.share_view)

        col = gtk.TreeViewColumn(_("Directory"), gtk.CellRendererText(), text=0)
#        col.set_spacing(235)
        self.share_view.append_column(col)
        col = gtk.TreeViewColumn(_("Share name"), gtk.CellRendererText(), text=1)
        self.share_view.append_column(col)
        col = gtk.TreeViewColumn(_("Permissions"), gtk.CellRendererText(), text=2)
        self.share_view.append_column(col)
        col = gtk.TreeViewColumn(_("Visibility"), gtk.CellRendererText(), text=3)
        self.share_view.append_column(col)
        col = gtk.TreeViewColumn(_("Description"), gtk.CellRendererText(), text=4)   
        col.set_spacing(235)
        self.share_view.append_column(col)

        if not (gtk.__dict__.has_key ("ActionGroup") and gtk.__dict__.has_key ("UIManager")):
            accel_group = gtk.AccelGroup()
            item_fac = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)
            self.main_window.add_accel_group(accel_group)
            item_fac.create_items([
                ('/' + _('_File'),                                None,    None, 0, '<Branch>'),
                ('/' + _('_File') + '/' + _('_Add Share'),        None,    self.onNewButtonClicked, 6, '<StockItem>', gtk.STOCK_ADD),
                ('/' + _('_File') + '/' + _('_Properties'),       None,    self.onPropertiesButtonClicked, 6, '<StockItem>', gtk.STOCK_PROPERTIES),
                ('/' + _('_File') + '/' + _('_Delete'),           None,    self.onDeleteButtonClicked, 6, '<StockItem>', gtk.STOCK_DELETE),
                ('/' + _('_File') + '/separator',                 None,    None, 0, '<Separator>', ''),
                ('/' + _('_File') + '/' + _('_Quit'),             None,    self.destroy, 6, '<StockItem>', gtk.STOCK_QUIT),
                ('/' + _('_Preferences'),                         None,    None, 0, '<Branch>'),
                ('/' + _('_Preferences') + '/' + _('_Server Settings...'),
                                                                  None,    self.onBasicPreferencesClicked, 1, '<StockItem>', gtk.STOCK_PREFERENCES),
    #            ('/' + _(_Preferences) + '/' + _('_Advanced Preferences...'),  None,   self.onAdvancedPreferencesClicked, 2, ''),
                ('/' + _('_Preferences') + '/' + _('Samba _Users...'),
                                                                  None,    self.onModifyUsersClicked, 3, ''),
                ('/' + _('_Help'),                                None,    None, 0, '<Branch>'),
                ('/' + _('_Help') + '/' + _('_Contents'),         None,    self.onHelpClicked, 1, '<StockItem>', gtk.STOCK_HELP),
                ('/' + _('_Help') + '/' + _('_About'),            None,    self.onAboutClicked, 2, ''),
                ])
            self.menu_bar = item_fac.get_widget('<main>')

            self.actionMenu = self.menu_bar.get_children()[0].get_submenu()        
            self.propertiesMenu = self.actionMenu.get_children()[1]
            self.deleteMenu = self.actionMenu.get_children()[2]

            self.toolbar = gtk.Toolbar()

            button = self.toolbar.insert_stock('gtk-add', _("Add a Samba share"), None, self.onNewButtonClicked, None, 0)
            image, label = button.get_children()[0].get_children()
            label.set_text(_("_Add"))
            label.set_use_underline(True)

            self.properties_button = self.toolbar.insert_stock('gtk-properties', _("Edit the properties of the selected directory"), None, self.onPropertiesButtonClicked, None, 1)
            image, label = self.properties_button.get_children()[0].get_children()
            label.set_text(_("P_roperties"))
            label.set_use_underline(True)

            self.delete_button = self.toolbar.insert_stock('gtk-delete', _("Delete the selected directory"), None, self.onDeleteButtonClicked, None, 2)
            image, label = self.delete_button.get_children()[0].get_children()
            label.set_text(_("_Delete"))
            label.set_use_underline(True)
        
            self.toolbar.insert_stock('gtk-help', _("View help"), None, self.onHelpClicked, None, 3)

            self.toplevel_vbox.pack_start(self.menu_bar, False)        
            self.toplevel_vbox.pack_start(self.toolbar, False)
        else:
            ui_string = """<ui>
                <menubar name='Menubar'>
                    <menu action='FileMenu'>
                        <menuitem action='Add'/>
                        <menuitem action='Properties'/>
                        <menuitem action='Delete'/>
                        <separator />
                        <menuitem action='Quit'/>
                    </menu>
                    <menu action='Preferences'>
                        <menuitem action='Settings'/>
                        <menuitem action='Users'/>
                    </menu>
                    <menu action='Help'>
                        <menuitem action='Contents'/>
                        <menuitem action='About'/>
                    </menu>
                </menubar>
                <toolbar name='Toolbar'>
                    <toolitem action='Add'/>
                    <toolitem action='Properties'/>
                    <toolitem action='Delete'/>
                    <toolitem action='HelpB'/>
                </toolbar>
            </ui>"""

            ag = gtk.ActionGroup('WindowActions')
            actions = [
                ('FileMenu', None, _('_File')),
                ('Add',        gtk.STOCK_ADD, _('_Add Share'), None, _('Add a Samba share'), self.onNewButtonClicked),
                ('Properties',    gtk.STOCK_PROPERTIES, _('_Properties'), None, _('Edit the properties of the selected directory'), self.onPropertiesButtonClicked),
                ('Delete',    gtk.STOCK_DELETE, _('_Delete'), None, _('Delete the selected directory'), self.onDeleteButtonClicked),
                ('Quit',     gtk.STOCK_QUIT, _('_Quit'), None, _('Quit program'), self.destroy),
                ('Preferences', None, _('_Preferences')),
                ('Settings', gtk.STOCK_PREFERENCES, _('_Server Settings...'), None, _('Server Settings'), self.onBasicPreferencesClicked),
                ('Users', '', _('Samba _Users...'), None, _('Samba Users'), self.onModifyUsersClicked),
                ('Help', None, _('_Help')),
                ('HelpB', gtk.STOCK_HELP, _('_Help'), None, _('Help Contents'), self.onHelpClicked),
                ('Contents', gtk.STOCK_HELP, _('_Contents'), None, _('View Help'), self.onHelpClicked),
                ('About', '', _('_About'), None, _('About the program'), self.onAboutClicked)
                ]

            ag.add_actions(actions)
            self.main_window.ui = gtk.UIManager()
            self.main_window.ui.insert_action_group(ag, 0)
            self.main_window.ui.add_ui_from_string(ui_string)
            self.main_window.add_accel_group(self.main_window.ui.get_accel_group())

            self.properties_button = self.main_window.ui.get_widget('/Toolbar/Properties')
            self.delete_button = self.main_window.ui.get_widget('/Toolbar/Delete')
            self.propertiesMenu = self.main_window.ui.get_widget('/Menubar/FileMenu/Properties')
            self.deleteMenu = self.main_window.ui.get_widget('/Menubar/FileMenu/Delete')

            self.toplevel_vbox.pack_start(self.main_window.ui.get_widget('/Menubar'), expand=False)
            self.toplevel_vbox.pack_start(self.main_window.ui.get_widget('/Toolbar'), expand=False)

        self.properties_button.set_sensitive(False)
        self.delete_button.set_sensitive(False)
        self.propertiesMenu.set_sensitive(False)
        self.deleteMenu.set_sensitive(False)

        #-------------------Packing--------------------#
        self.toplevel_vbox.pack_start(self.share_view_sw, True)
        self.main_window.add(self.toplevel_vbox)
        self.main_window.set_default_size(600, 400)
        self.main_window.set_size_request(600, 200)

        self.selected_row = -1
        self.changed = False
        
        self.create_handler = None
        self.modify_handler = None

        self.main_window.show_all()

#        self.share_view.connect("cursor-changed", self.onShareListSelectRow)
        self.share_view.get_selection().connect("changed", self.onShareListSelectRow)
        self.share_view.connect ("row_activated", self.onShareListActivate)
        self.share_view.get_selection().unselect_all()
        
        if gtk.__dict__.has_key ("main"):
            gtk.main ()
        else:
            gtk.mainloop()

    def processSambaData(self, samba_data):
        sections = samba_data.sections
        sections_dict = samba_data.sections_dict

        #print "sections:", sections
        #print "sections_dict.keys ():", sections_dict.keys ()

        for section_name in sections:
            #print "-->", section_name, "<--"
            if not section_name in samba_data.getShareHeaders ():
                #print "FOO", section_name
                continue
            section = samba_data.sections_dict[section_name]
            #print "filling UI with section", repr (section)
 
            iter = self.share_store.append ()
            self.share_store.set_value (iter, 2, _("Read Only"))
            self.share_store.set_value (iter, 3, _("Visible"))

            sharename = string.strip (section.name ,"\n[]")
            self.share_store.set_value (iter, 1, sharename)
            self.share_store.set_value (iter, 5, section)

            for token in section.content:
                if token.type == sambaToken.SambaToken.SAMBA_TOKEN_KEYVAL:
                    
                    if token.keyname == "path":
                        self.share_store.set_value (iter, 0, token.keyval)
                    elif token.keyname == "read only":

                        if string.lower (token.keyval) == "no":
                            self.share_store.set_value (iter, 2, (_("Read/Write")))
                        else:
                            self.share_store.set_value (iter, 2, (_("Read Only")))

                    elif token.keyname == "writeable" or token.keyname == "writable":
                        if string.lower (token.keyval) == "no":
                            self.share_store.set_value(iter, 2, (_("Read Only")))
                        else:
                            self.share_store.set_value(iter, 2, (_("Read/Write")))

                    elif token.keyname == "browseable" or token.keyname == "browsable":
                        if string.lower (token.keyval) == "no":
                            self.share_store.set_value(iter, 3, (_("Hidden")))
                        else:
                            self.share_store.set_value(iter, 3, (_("Visible")))

                    elif token.keyname == "comment":
                        self.share_store.set_value (iter, 4, token.keyval)

    #--------Event handlers for main_window-----#
    def onShareListSelectRow(self, *args):
        store, iter = self.share_view.get_selection().get_selected()
        if iter:
            self.properties_button.set_sensitive(True)
            self.delete_button.set_sensitive(True)
            self.propertiesMenu.set_sensitive(True)
            self.deleteMenu.set_sensitive(True)
        else:
            self.properties_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            self.propertiesMenu.set_sensitive(False)
            self.deleteMenu.set_sensitive(False)

    def onNewButtonClicked(self, *args):
        self.changed = True
        self.share_win.showNewWindow()

    def onShareListActivate (self, *args):
        self.showPropertiesDialog ()

    def onPropertiesButtonClicked (self, *args):
        self.showPropertiesDialog ()

    def showPropertiesDialog (self):
        self.changed = True
        store, iter = self.share_view.get_selection ().get_selected ()
        if iter != None:
            section = self.share_store.get_value (iter, 5)
            self.share_win.showEditWindow (iter, section)
        
    def onDeleteButtonClicked(self, *args):
        self.changed = True

        
        store, iter = self.share_view.get_selection().get_selected()
        section = self.share_store.get_value(iter, 5)
        #print "deleting", section
        #print "before delete"
        section.delete ()
        #print "after delete"
        self.share_store.remove(iter)

        self.properties_button.set_sensitive(False)
        self.delete_button.set_sensitive(False)
        self.propertiesMenu.set_sensitive(False)
        self.deleteMenu.set_sensitive(False)

        #Let's go ahead and restart the service.
        self.samba_data.writeFile()
        self.samba_backend.restartSamba()

    def onApplyButtonClicked(self, *args):
        self.changed = True

        self.samba_data.writeFile()
        self.properties_button.set_sensitive(False)
        self.delete_button.set_sensitive(False)
        self.propertiesMenu.set_sensitive(False)
        self.deleteMenu.set_sensitive(False)
        self.share_view.get_selection().unselect_all()

        status = self.samba_backend.isSambaRunning()
        
        result = None
        if not status:
            #smb is not running, so ask the user if they want to start it
            dlg = gtk.MessageDialog(self.main_window, 0, gtk.MESSAGE_WARNING,
                                    gtk.BUTTONS_YES_NO, (_("The Samba service is not "
                                                           "currently running.  Do you "
                                                           "wish to start it?")))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.set_icon(iconPixbuf)
            dlg.set_modal(True)
            dlg.set_transient_for(self.main_window)
            result = dlg.run()
            dlg.destroy()
                                                           
            if result == gtk.RESPONSE_YES:
                #Start smb if the user says 'yes'
                if not self.debug_flag:
                    self.samba_backend.startSamba()
                else:
                    print "cannot start the service in debug mode"

        else:
            #smb is already running, so restart to allow changes to take effect
            if not self.debug_flag:
                self.samba_backend.restartSamba()
            else:
                print "cannot start the service in debug mode"

    def onBasicPreferencesClicked(self, *args):
        self.basic_preferences_win.showWindow()

    def onAdvancedPreferencesClicked(self, *args):
        advanced_preferences_win = self.xml.get_widget("advanced_preferences_win")
        advanced_preferences_win.show_all()

    def onRefreshButtonClicked(self, *args):
        pass

    def onModifyUsersClicked(self, *args):
        self.samba_user_win.showWindow()

    def destroy(self, *args):
#        #Maybe we don't need to restart the service now, so let's comment this line out
#        self.onApplyButtonClicked()
        if gtk.__dict__.has_key ("main_quit"):
            gtk.main_quit ()
        else:
            gtk.mainquit()

    def onAboutClicked(self, *args):
        copyrights = (('2002 - 2005', 'Red Hat, Inc.', None),
                ('2002 - 2004', 'Brent Fox', 'bfox@redhat.com'),
                ('2002 - 2004', 'Tammy Fox', 'tfox@redhat.com'),
                ('2004 - 2005', 'Nils Philippsen', 'nphilipp@redhat.com'))
        copyrighttext = ''
        for year, holder, email in copyrights:
            if email:
                email = '<%s>' % (email)
            else:
                email = ''
            copyrighttext += _("Copyright %s (c) %s %s\n") % (year, holder, email)
        copyrighttext += '\n'

        dlg = gtk.MessageDialog (None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                 # first placeholder is the version, second is
                                 # a (newline-terminated) list of copyright
                                 # holders
                                 _("Samba Server Configuration Tool %s\n%sA graphical interface for configuring SMB shares") % ("1.2.63", copyrighttext))
        label = dlg.vbox.get_children ()[0].get_children ()[1].get_children ()[0]
        label.set_line_wrap (False)
        dlg.set_title(_("About"))
        dlg.set_default_size(100, 100)
        dlg.set_position (gtk.WIN_POS_CENTER)
        dlg.set_border_width(2)
        dlg.set_modal(True)
        dlg.set_transient_for(self.main_window)
        dlg.set_icon(iconPixbuf)
        rc = dlg.run()
        dlg.destroy()

    def onHelpClicked(self, *args):
        help_page = "ghelp:system-config-samba"
        paths = ["/usr/bin/yelp", None]

        for path in paths:
            if path and os.access (path, os.X_OK):
                break
        
        if path == None:
            dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                    (_("The help viewer could not be found. To be able to view help you need to install the 'yelp' package.")))
            dlg.set_position(gtk.WIN_POS_CENTER)
            dlg.run()
            dlg.destroy()
            return

        pid = os.fork()
        if not pid:
            os.execv(path, [path, help_page])
