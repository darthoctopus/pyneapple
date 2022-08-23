#!/usr/bin/python3
# -*- coding:utf-8 -*-
#
# Copyright (C) 2022 Joel Ong <joel.ong@yale.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
import pathlib
import shutil
import asyncio

import urllib.request
import urllib.parse

import gi
from .config import config
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gio, Gtk, GLib, Notify
from .platform import WebView, platformat, SYSTEM,\
                      open_term, open_folder, open_uri

get_name = Gtk.Buildable.get_name
dialog_flags = (Gtk.DialogFlags.MODAL|
                Gtk.DialogFlags.DESTROY_WITH_PARENT|
                Gtk.DialogFlags.USE_HEADER_BAR)

def dialog_filter(dialog, name="Jupyter Notebook", ext="*.ipynb",
                  mime="application/x-ipynb+json"):
    filter_ipynb = Gtk.FileFilter()
    filter_ipynb.set_name(name)
    filter_ipynb.add_pattern(ext)
    filter_ipynb.add_mime_type(mime)
    dialog.add_filter(filter_ipynb)

# "string" operations because fuck you
# Why bother with GObject if you're going to
# totally disregard the python type system

STRING = GLib.VariantType.new('s')
def _(thing, reverse=False):
    if isinstance(thing, str):
        if reverse:
            return GLib.Variant.new_string(thing)
        return thing
    return thing.get_string()

WHERE_AM_I = os.path.abspath(os.path.dirname(__file__))

CALLBACK_PREFIX = "$$$$"
CALLBACK_SEPARATOR = "|"

Notify.init("Pyneapple")

class JupyterWindow:
    """
    Simple WebBrowser class.

    Uses WebKit introspected bindings for Python:
    http://webkitgtk.org/reference/webkit2gtk/stable/
    """

    def __init__(self, app, server, file):
        """
        Initialisation of app window
        """

        builder = Gtk.Builder()
        self.go = builder.get_object

        # Build GUI from Glade file

        if not config.getboolean('csd'):
            builder.add_from_file(os.path.join(WHERE_AM_I, 'data', 'windows.ui'))

        else:
            builder.add_from_file(os.path.join(WHERE_AM_I, 'data', 'pyneapple.ui'))

        self.app = app
        self.server = server
        self.file = file
        self.ready = False
        self.busy = False

        # Get objects
        self.window = self.go('window')
        self.headerbar = self.go('headerbar')

        if not config.getboolean('csd'):
            self.headerbar.get_style_context().add_class(
                Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

        # Create WebView
        self.webview = WebView()
        self.go('scrolled').add(self.webview)
        props = self.go('scrolled').get_children()[0].props
        props.shadow_type = Gtk.ShadowType.NONE

        # Connect signals
        builder.connect_signals(self)

        if SYSTEM == "Windows":
            self.webview.connect('notify::load-status', self.load_status_cb)
        else:
            self.webview.connect('load_changed', self.load_changed_cb)
        self.webview.connect('notify::title', self.titlechanged)
        self.webview.connect('context-menu', lambda s, w, e, u: True)
        self.webview.connect('create', self.navigate)
        self.window.connect('delete-event', self.close)

        # Everything is ready
        # self.load_uri(local_uri + 'home')
        # print(app.server.port, file)

        self.reset()
        self.window.set_application(app)
        self.window.show()
        self.window.show_all()

        # Did I mention that Gio actions are horrible? let's introduce more
        # boilerplate for the sake of it woo

        for i in ["close", "quit", "open", "save_as", "print_dialog", "reset",
                  "clear_output", "toggle_csd", "new", "prefs",
                  "open_terminal", "open_folder"]:
            eval(f"self.action_hack('{i}', self.{i})")

        for i in ["jupyter_click_menu", "zoom", "export"]:
            eval(f"self.action_hack('{i}', self.{i}, True)")

        for i in ["change_kernel", "set_theme"]:
            eval(f"self.action_hack('{i}', self.{i}, True, True)")

        self.done_notification = Notify.Notification.new('Computation finished', '')

    def action_hack(self, name, method, param=False, stateful=False):
        """
        catch-all hack to create Gio actions for GtkApplicationMenu.
        One wonders why we can't just have activate signals,
        like with GtkMenu, or reserved function names, like with
        GtkApplication.
        """
        name = name.replace('_', '-')
        if param:
            if stateful:
                q = Gio.SimpleAction.new_stateful(name, STRING, _('', reverse=True))
            else:
                q = Gio.SimpleAction.new(name, STRING)
        else:
            q = Gio.SimpleAction.new(name, None)
        q.connect("activate", method)
        self.window.add_action(q)

    def navigate(self, webview, navigation, *args, **kwargs):
        '''
        Handle attempts to navigate to new URIs.

        Generally we delegate this to xdg-open for all URI schemes.
        '''

        open_uri(navigation.get_request().get_uri())

    def prefs(self, *_):
        self.app.prefs()

    def quit(self, *_):
        """
        Self-explanatory
        """
        self.app.quit()

    def close(self, *_):
        """
        I've implemented Nathan's autosave here
        """
        if not self.ready:
            return False

            # This really should be part of a more general callback
            # handling scheme (much credit to N Whitehead)
            # but this is the only place it's actually needed

        ss = """{
                var success = function(evt) {
                  require('custom/custom').flash("$$$$-2|1")
                };
                var failure = function(evt) {
                  require('custom/custom').flash("$$$$-2|0")
                };
                require('base/js/events').on("notebook_saved.Notebook", success);
                }"""
        self.webview.run_javascript(ss)
        self.jupyter_click_run('save_checkpoint')

        return True

    def error(self, message, message2):
        """
        Error message (if ever needed)
        """
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.CANCEL,
                                   str(message), flags=dialog_flags)
        dialog.format_secondary_text(
            str(message2))
        dialog.run()

        dialog.destroy()

    def open(self, *_):
        """
        Open a file with GTK FileChooserDialog
        """
        dialog = Gtk.FileChooserDialog("Please choose a file", self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
                                       flags=dialog_flags)
        dialog_filter(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.app.open_filename(dialog.get_filename())

        dialog.destroy()

    def open_terminal(self, *_):
        """
        Open a terminal window in the directory of the file
        """

        path = os.path.dirname(platformat(self.file))
        open_term(path)

    def open_folder(self, *_):
        """
        Open a file manager window in the directory of the file
        """

        path = os.path.dirname(platformat(self.file))
        open_folder(path)

    def reset(self, *_):
        """
        Refresh webview (in case of Bad Things happening,
        e.g. accidentally navigating with a hyperlink)
        """


        self.load_uri("http://{}:{}/notebooks{}?token={}".
                      format(self.server.servername, self.server.port, platformat(self.file), self.server.token))

    def save_as(self, *_):
        """
        Save As with file chooser
        """
        self.jupyter_click_run('save_checkpoint')
        dialog = Gtk.FileChooserDialog("Please choose a location to save the file", self.window,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK),
                                       flags=dialog_flags)
        dialog_filter(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                shutil.copy(self.file, dialog.get_filename())
                self.ready = False
                self.load_uri("http://{}:{}/notebooks{}?token={}"
                              .format(self.server.servername,
                                      self.server.port, platformat(dialog.get_filename()),
                                      self.server.token))
            except IOError as e:
                self.error("Error Saving Notebook", e)

        self.app.windows[dialog.get_filename()] = self.app.windows[self.file]
        del self.app.windows[self.file]
        self.file = dialog.get_filename()
        dialog.destroy()

    def print_dialog(self, *_):
        """
        Print with webview's built-in capabilities
        n.b. the resulting PDFs will be styled with the current theme
        """
        self.webview.run_javascript("window.print()")

    def export(self, __, f):
        """
        Exporting requires nbconvert (and by extension pandoc)
        """
        fmt = _(f)
        uri = "http://{}:{}/nbconvert/{}{}?token={}".\
            format(self.server.servername, self.server.port, fmt,
                   urllib.parse.quote(os.path.normpath(platformat(self.file))),
                   self.server.token)

        extension = {'python':'*.py', 'markdown':'*.md', 'html':'*.html'}
        name = {'python': 'Python', 'markdown': 'Markdown', 'html': 'HTML'}[fmt]
        mime = {'python':'text/python', 'markdown':'text/markdown', 'html':'text/html'}

        self.jupyter_click_run('save_checkpoint')
        dialog = Gtk.FileChooserDialog("Please choose a location to export the file", self.window,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK),
                                       flags=dialog_flags)
        dialog_filter(dialog, name=(name + " ({})".format(extension[fmt])),
                      ext=extension[fmt], mime=mime[fmt])

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                urllib.request.urlretrieve(uri, dialog.get_filename())
            except IOError as e:
                self.error("Error Exporting Notebook", e)
        dialog.destroy()


    def load_changed_cb(self, webview, event, user_data=None):
        # For WebKit2
        ev = str(event)
        self.load_event(ev)

    def load_status_cb(self, webview, *_):
        # For WebKit
        ev = str(webview.props.load_status)
        self.load_event(ev)

    def load_event(self, ev):
        """
        aka onLoad()
        """
        if 'WEBKIT_LOAD_COMMITTED' in ev:
            self.set_title("Pyneapple: "+ os.path.basename(self.file),
                           os.path.normpath(self.file))
        elif 'WEBKIT_LOAD_FINISHED' in ev:
            self.set_theme(config.get('theme'))
            Gtk.RecentManager.get_default().add_item(pathlib.Path(self.file).as_uri())
            self.ready = True

    def set_title(self, title, subtitle=None):
        if not config.getboolean('csd'):
            self.window.set_title(title)
        else:
            self.headerbar.set_title(title)
            if subtitle is not None:
                self.headerbar.set_subtitle(subtitle)

    def load_uri(self, uri):
        """
        Load an URI on the browser.
        """
        self.webview.load_uri(uri)
        return

    def zoom(self, __, level):
        """
        Set WebView zoomlevel
        per documentation, supply a scale factor (default 1)
        """
        name = _(level)
        #print("self.webview.{}()".format(name))
        if name == "zoom_in":
            self.webview.set_zoom_level(self.webview.get_zoom_level() * 1.1)
        elif name == "zoom_out":
            self.webview.set_zoom_level(self.webview.get_zoom_level() / 1.1)
        else:
            self.webview.set_zoom_level(1)

    def toggle_csd(self, *_):
        """
        n.b. this causes window to lose decorations if CSD is actually used
        """
        self.headerbar.set_visible(not self.headerbar.get_visible())

    def jupyter_click(self, widget, *_):
        """
        Emulate a click on the Jupyter menu
        if suffix _toolbar is present, we strip it first
        """
        widget_id = get_name(widget)
        if widget_id[-len('_toolbar'):] == '_toolbar':
            widget_id = widget_id[:-len('_toolbar')]
        self.jupyter_click_run(widget_id)

    def jupyter_click_menu(self, __, name):
        """
        Same deal but through a GtkAction rather than activate signal
        """
        widget_id = _(name)
        self.jupyter_click_run(widget_id)

    def jupyter_click_run(self, name):
        """
        Actual javascript invocation
        """
        self.webview.run_javascript("Jupyter.menubar.element.find('#%s').click(); true" % name)

    # Some of Nathan's utility functions are implemented here.

    def set_theme(self, *args):
        """
        Sets theme using themes nbextension
        """
        theme = "/custom/themes/{}.css".format(_(args[-1]))
        if theme[:-4] == "none":
            theme = "#"

        self.webview.run_javascript("""global_start_theme="{}";
            require('custom/custom').set_theme(global_start_theme);""".format(theme))

        try:
            args[0].set_state(args[1])
        except:
            pass

    def change_kernel(self, action, name):
        """
        Changes kernel
        """
        kernel = _(name)
        self.webview.run_javascript("Jupyter.notebook.kernel_selector.set_kernel('%s');" % kernel)
        action.set_state(name)

    def new(self, *_):
        self.app.new_ipynb()


    # def test_return(self, widget, user_data=None):
    #   print("test")
    #   self.webview.run_javascript("'asdf'", None, self.collect_result)

    # def collect_result(self, object, result, user_data=None):
    #   print(self.webview.run_javascript_finish(result).get_value())

    # Unfortunately, JScore objects are not introspectable and therefore
    # are unsupported with GIO in Python.
    # Here I port Nathan Whitehead's implementation of
    # a callback scheme using the page title as a message-passing interface.

    def titlechanged(self, *__):
        """
        Callback system using window title as MPI
        """
        s = self.webview.get_title()
        if s is not None and s.startswith(CALLBACK_PREFIX):
            num, contents = s[len(CALLBACK_PREFIX):].split(CALLBACK_SEPARATOR)
            num = int(num)
            if num == -3:
                # kernel list from page load
                spec = eval(contents)

                # We dynamically populate the menu of kernels
                kernellist = self.app.go('change_kernel')
                kernellist.remove_all()
                for q in spec:
                    a = Gio.MenuItem.new(label=spec[q]['spec']['display_name'])
                    a.set_action_and_target_value("win.change-kernel", _(q, reverse=True))
                    kernellist.append_item(a)

                # old routine

                # kernellist = self.go('change_kernel').get_submenu()
                # for q in kernellist.get_children():
                #     kernellist.remove(q)
                # for q in spec:
                #     a = Gtk.MenuItem(label=spec[q]['spec']['display_name'])
                #     a.connect("activate", self.change_kernel)
                #     Gtk.Buildable.set_name(a, q)
                #     kernellist.append(a)
                # kernellist.show_all()

            elif num == -2:
                # final save on window closure
                if int(contents):
                    self.ready = False
                    self.window.close()
                    del self.app.windows[self.file]
                    del self
                    return

            elif num == -1:
                # kernel busy indicator: "true" if busy and "false" otherwise
                self.busy = True if contents == "true" else False
                self.go('interrupt_kernel_toolbar').set_sensitive(self.busy)
                self.set_title("Pyneapple: %s%s"
                               %  (os.path.basename(self.file),
                                   " (busy)" if self.busy else ""))
                # # asyncio.run(self.notify()) in 3.7+, hopefully
                self.notify()
            else:
                # Maybe Nathan coded other callbacks idk
                print(s)

    def notify(self):
        time.sleep(1/60)
        # dirty hack to drop at most one frame at 60 fps
        if self.busy:
            # self.done_notification.close()
            pass
        else:
            if not self.window.is_active():
                self.done_notification.update("Computation Finished",
                                              "Evaluation of cell in %s complete"\
                                              % os.path.basename(self.file))
                self.done_notification.show()


    def clear_output(self, *_):
        """
        Clear output for selected cell
        """
        self.webview.run_javascript("require('base/js/namespace').notebook.clear_output();")

class ChromelessWindow:
    """
    general-purpose simple webview with no chrome or navigational controls.
    """

    def __init__(self, title, uri):
        """
        Build GUI
        """

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(WHERE_AM_I, 'data', 'prefs.ui'))
        go = builder.get_object
        window = go('window')
        scrolled = go('scrolled')

        # Create WebView
        webview = WebView()
        scrolled.add(webview)
        builder.connect_signals(self)
        window.connect('delete-event', self.cleanup)
        window.set_title (title)

        # Everything is ready
        webview.load_uri(uri)
        window.show_all()

    def cleanup(self, *_):
        del self
