#!/usr/bin/python3
# -*- coding:utf-8 -*-
#
# Copyright (C) 2018 Joel Ong <joel.ong@yale.edu>
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

#for server
import sys
import os
import time
import shutil

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gio, Gtk, WebKit2
from os.path import abspath, basename, dirname, join

from notebook.notebookapp import NotebookApp
from multiprocessing import Process
import urllib.request

def get_home_dir():
    homedir = os.path.expanduser('~')
    homedir = os.path.realpath(homedir)
    return homedir

NEW = """{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.6.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 1
}"""

DEFAULT_THEME = 'theme-light'
#todo: add settings

WHERE_AM_I = abspath(dirname(__file__))

CALLBACK_PREFIX = "$$$$"
CALLBACK_SEPARATOR = "|"

class JupyterWindow(object):
    """
    Simple WebBrowser class.

    Uses WebKit introspected bindings for Python:
    http://webkitgtk.org/reference/webkit2gtk/stable/
    """

    def __init__(self, app, file):
        """
        Build GUI
        """

        # Build GUI from Glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(join(WHERE_AM_I, 'pyneapple.ui'))

        self.app = app
        self.file = file
        self.ready = False
        self.dialog_flags = flags=(Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT|Gtk.DialogFlags.USE_HEADER_BAR)

        # Get objects
        go = self.builder.get_object
        self.window = go('window')
        self.scrolled = go('scrolled')
        self.headerbar = go('headerbar')

        # Create WebView
        self.webview = WebKit2.WebView()
        self.scrolled.add_with_viewport(self.webview)

        # Connect signals
        self.builder.connect_signals(self)
        self.webview.connect('load-changed', self.load_changed_cb)
        self.webview.connect('notify::title', self.titlechanged)
        self.webview.connect('context-menu', lambda s, w, e, u: True)
        self.window.connect('delete-event', self.close)

        # Everything is ready
        # self.load_uri(local_uri + 'home')
        print(app.server.port, file)
        self.load_uri("http://localhost:{}/notebooks{}".format(app.server.port, file))
        self.window.set_application(app)
        self.window.show()
        self.window.show_all()

    def close(self, *args):
        if not self.ready:
            return False

            # This really should be part of a more general callback
            # handling scheme (much credit to N Whitehead)
            # but this is the only place it's actually needed

        ss = """{
                var success = function(evt) {
                  var old = document.title;
                  document.title = "$$$$-2|1"
                  document.title = old;
                };
                var failure = function(evt) {
                  var old = document.title;
                  document.title = "$$$$-2|0";
                  document.title = old;
                };
                require('base/js/events').on("notebook_saved.Notebook", success);
                }"""
        self.webview.run_javascript(ss)
        self.webview.run_javascript(self.jupyter_click_code('save_checkpoint'))
        return True

    def quit(self, *args):
        self.app.quit()

    def error(self, message, message2):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CANCEL, message, flags=self.dialog_flags)
        dialog.format_secondary_text(
            message2)
        dialog.run()
        print("ERROR dialog closed")

        dialog.destroy()

    def open(self, widget, *args):
        dialog = Gtk.FileChooserDialog("Please choose a file", self.window,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK), flags=self.dialog_flags)
        self.ipynb_filter(dialog)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.app.open_filename(dialog.get_filename())

        dialog.destroy()

    def save_as(self, widget, *args):
        self.webview.run_javascript(self.jupyter_click_code('save_checkpoint'))
        dialog = Gtk.FileChooserDialog("Please choose a location to save the file", self.window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK), flags=self.dialog_flags)
        self.ipynb_filter(dialog)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                shutil.copy(self.file, dialog.get_filename())
                self.ready = False
                self.load_uri("http://localhost:{}/notebooks{}".format(self.app.server.port, dialog.get_filename()))
            except e:
                self.error("Error Saving Notebook", e)

        self.app.windows[dialog.get_filename()] = self.app.windows[self.file]
        del self.app.windows[self.file]
        self.file = dialog.get_filename()
        dialog.destroy()

    def print(self, *args):
        self.webview.run_javascript("window.print()")

    def ipynb_filter(self, dialog):
        filter_ipynb = Gtk.FileFilter()
        filter_ipynb.set_name("Jupyter Notebooks")
        filter_ipynb.add_pattern("*.ipynb")
        filter_ipynb.add_mime_type("application/x-ipynb+json")
        dialog.add_filter(filter_ipynb)

    def export(self, widget, *args):
        format = Gtk.Buildable.get_name(widget)
        uri = "http://localhost:{}/nbconvert/{}{}".format(self.app.server.port, format, self.file)

        extension = {'python':'*.py', 'markdown':'*.md', 'html':'*.html'}
        name = widget.get_label()
        mime = {'python':'text/python', 'markdown':'text/markdown', 'html':'text/html'}

        self.webview.run_javascript(self.jupyter_click_code('save_checkpoint'))
        dialog = Gtk.FileChooserDialog("Please choose a location to export the file", self.window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK), flags=self.dialog_flags)
        filter = Gtk.FileFilter()
        filter.set_name(name + "({})".format(extension[format]))
        filter.add_pattern(extension[format])
        filter.add_mime_type(mime[format])
        dialog.add_filter(filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                urllib.request.urlretrieve(uri, dialog.get_filename())
            except e:
                self.error("Error Saving Notebook", e)
        dialog.destroy()


    def load_changed_cb(self, webview, event, user_data=None):
        """
        Callback for when the load operation in webview changes.
        """
        ev = str(event)
        if 'WEBKIT_LOAD_COMMITTED' in ev:
            self.headerbar.set_title("Pyneapple: "+ basename(self.file))
            self.headerbar.set_subtitle(self.webview.get_uri())
        elif 'WEBKIT_LOAD_FINISHED' in ev:
            self.set_theme(self.builder.get_object(DEFAULT_THEME))
            self.ready = True

    def load_uri(self, uri):
        """
        Load an URI on the browser.
        """
        self.webview.load_uri(uri)
        return

    def zoom(self, widget, *args):
        name = Gtk.Buildable.get_name(widget)
        #print("self.webview.{}()".format(name))
        if name == "zoom_in":
            self.webview.set_zoom_level(self.webview.get_zoom_level() * 1.1)
        elif name == "zoom_out":
            self.webview.set_zoom_level(self.webview.get_zoom_level() / 1.1)
        else:
            self.webview.set_zoom_level(1)

    def toggle_csd(self, *args):
        self.headerbar.set_visible(not self.headerbar.get_visible())


    def set_theme(self, widget, user_data=None):
        theme = "/custom/{}.css".format(Gtk.Buildable.get_name(widget))
        if theme[-8:-4] == "none":
            theme = "#"

        self.webview.run_javascript("""global_start_theme="{}";
            require('custom/custom').set_theme(global_start_theme);""".format(theme))


    def jupyter_click(self, widget, user_data=None):
        """
        Emulate a click on the Jupyter menu
        if suffix _toolbar is present, we strip it first
        """

        id = Gtk.Buildable.get_name(widget)
        if id[-len('_toolbar'):] == '_toolbar':
            id = id[:-len('_toolbar')]
        self.webview.run_javascript(self.jupyter_click_code(id))
        

    def jupyter_click_code(self, name):
        return "Jupyter.menubar.element.find('#%s').click(); true" % name

    def change_kernel(self, widget, *args):
        id = Gtk.Buildable.get_name(widget)
        self.webview.run_javascript("Jupyter.notebook.kernel_selector.set_kernel('%s');" % id)

    def new(self, *args):
        self.app.new()


    # def test_return(self, widget, user_data=None):
    #   print("test")
    #   self.webview.run_javascript("'asdf'", None, self.collect_result)

    # def collect_result(self, object, result, user_data=None):
    #   print(self.webview.run_javascript_finish(result).get_value())

    # Unfortunately, JScore objects are not introspectable and therefore
    # are unsupported with GIO in Python.
    # Here I port Nathan Whitehead's implementation of 
    # a callback scheme using the page title as a message-passing interface.

    def titlechanged(self, webview, *args):
        s = self.webview.get_title()
        if s.startswith(CALLBACK_PREFIX):
            num, contents = s[len(CALLBACK_PREFIX):].split(CALLBACK_SEPARATOR)
            num = int(num)
            if num == -3:
                # kernel list from page load
                spec = eval(contents)

                # We dynamically populate the menu of kernels
                kernellist = self.builder.get_object('change_kernel').get_submenu()
                for q in kernellist.get_children():
                    kernellist.remove(q)
                for q in spec:
                    a = Gtk.MenuItem(label=spec[q]['spec']['display_name'])
                    a.connect("activate", self.change_kernel)
                    Gtk.Buildable.set_name(a, q)
                    kernellist.append(a)
                kernellist.show_all()

            elif num == -2:
                # final save on window closure
                self.ready = False
                self.window.close()
                del self.app.windows[self.file]
                del self
                return

            elif num == -1:
                # kernel busy indicator: "true" if busy and "false" otherwise
                busy = True if contents == "true" else False
                self.builder.get_object('interrupt_kernel_toolbar').set_sensitive(busy)
                self.headerbar.set_title("Pyneapple: %s%s" %  (basename(self.file), " (busy)" if busy else ""))
            else:
                # Maybe Nathan coded other callbacks idk
                print(s)

    def clear_output(self, widget, user_data=None):
        """
        Clear output for selected cell
        """
        self.webview.run_javascript("require('base/js/namespace').notebook.clear_output();")


class PyneappleServer(object):
    """ 
    Adapted from N Whitehead
    """

    def __init__(self):
        self.port = int("4" + str(time.time()).split('.')[-1][:4])

    def run(self):
        """ 
        Need a way of getting config
        """

        def get_config_dir():
            homedir = get_home_dir()
            return os.path.join(homedir, '.pineapple', 'Jupyter')

        def get_data_dir():
            homedir = get_home_dir()
            return os.path.join(homedir, '.Pineapple', 'Jupyter')

        # Always serve from root
        sys.argv = [sys.executable, '--port={}'.format(self.port), '/']
        os.environ['JUPYTER_CONFIG_DIR'] = get_config_dir()
        os.environ['JUPYTER_DATA_DIR'] = get_data_dir()

        # Symlink custom resources
        customres = os.path.dirname(__file__) + '/custom'
        try:
            os.symlink(customres, os.environ['JUPYTER_CONFIG_DIR'] + '/custom')
        except:
            pass
        
        self.app = NotebookApp()
        self.app.open_browser = False
        self.app.token = ''

        """ Method that runs forever """
        self.app.initialize()
        self.app.start()

class Pyneapple(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.pyneapple",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.windows = {}
        self.highest_untitled = 0

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.argv = sys.argv
        self.server = PyneappleServer()
        self.serverprocess = Process(target=self.server.run)
        self.serverprocess.start()
        sys.argv = self.argv

        #hack
        time.sleep(1)

    def do_activate(self):
        Gtk.Application.do_activate(self)
        if len(self.windows) == 0:
            self.new()

    def new(self):
        while os.path.exists(os.path.join(get_home_dir(), "Untitled %d.ipynb" % self.highest_untitled)):
            self.highest_untitled += 1

        fn = os.path.join(get_home_dir(), "Untitled %d.ipynb" % self.highest_untitled)

        with open(fn, "w") as f:
            f.write(NEW)

        self.open_filename(fn)
        self.highest_untitled += 1

    def open_filename(self, filename):
        if filename not in self.windows:
            self.windows[filename] = JupyterWindow(self, filename)
        else:
            self.windows[filename].window.present()

    def do_open(self, files, *args):
        for file in files:
            p = file.get_path()
            if p[-6:] == ".ipynb":
                self.open_filename(p)

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)
        self.serverprocess.terminate()

if __name__ == '__main__':
    p = Pyneapple()
    p.run(sys.argv)
