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

import sys
import os
import time

import urllib.parse
from multiprocessing import Process

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk

from .config import config
from .windows import WHERE_AM_I, JupyterWindow, JupyterRemoteWindow, ChromelessWindow
from .servers import PyneappleLocalServer

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
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 1
}"""

class Pyneapple(Gtk.Application):
    """
    Main application
    """
    def __init__(self):
        super().__init__(application_id="org.pyneapple",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.windows = {}
        self.highest_untitled = 0
        self.server = PyneappleLocalServer()
        self.serverprocess = Process(target=self.server.run)

    def do_startup(self):
        """
        reserved method name for GtkApplication
        connected to startup signal
        """
        Gtk.Application.do_startup(self)

        # argv for the app will be different from that used for
        # starting the notebook server, in general

        argv = sys.argv
        self.serverprocess.start()
        sys.argv = argv

        # hack — give some time for the server to start before
        # opening the first webview. Otherwise we get
        # a refused connection (and confused users?)
        time.sleep(config.get('StartupDelay'))

        # Unfortunately, we now have one instance of
        # Builder and get_object per instance of ApplicationWindow
        # and ALSO for the parent Application, all in the name
        # of scoping the kernel-busy indicators to the respective
        # windows.
        builder = Gtk.Builder()
        self.go = builder.get_object
        builder.add_from_file(os.path.join(WHERE_AM_I, 'data', 'menu.ui'))
        self.set_menubar(builder.get_object("menubar"))

    def do_activate(self):
        """
        reserved method name for GtkApplication
        connected to activate signal (i.e. launching/raising)
        """
        Gtk.Application.do_activate(self)
        if not self.windows:
            # check to see if we have opened a file recently
            recents = [[q.get_modified(), q.get_uri()] for q in Gtk.RecentManager.get_default().\
                        get_items() if 'pyneapple' in q.get_applications()]
            if recents:
                # sort by last visited
                recents = sorted(recents)
                # parse file URI
                for _, f in recents[::-1]:
                    ff = urllib.parse.unquote(f)[7:]
                    if ff[-6:] == ".ipynb" and os.path.isfile(ff):
                        self.open_filename(ff)
                        return

                # if none of the recently opened files are valid, we make a new one as a last resort
                self.new_ipynb()
            else:
                self.new_ipynb()

    def new_ipynb(self):
        """
        Make a new ipynb, and then instantiate a window for it.
        """
        tmp = os.path.expanduser(config.get('TmpDir'))
        while os.path.exists(os.path.join(tmp,
                                          "Untitled %d.ipynb" % self.highest_untitled)):
            self.highest_untitled += 1

        fn = os.path.join(tmp, "Untitled %d.ipynb" % self.highest_untitled)

        with open(fn, "w") as f:
            f.write(NEW)

        self.open_filename(fn)
        self.highest_untitled += 1

    def prefs(self):
        w = ChromelessWindow("Notebook Extension Preferences", f"http://{self.server.servername}:{self.server.port}/nbextensions?token={self.server.token}")
        return w

    def open_filename(self, filename):
        """
        Instantiate window for existing ipynb
        """
        if filename not in self.windows:
            self.windows[filename] = JupyterWindow(self, self.server, filename)
        else:
            self.windows[filename].window.present()

    def open_uri(self, uri):
        if uri not in self.windows:
            if '/notebooks/' in uri:
                self.windows[uri] = JupyterRemoteWindow(self, uri)
            else:
                self.windows[uri] = ChromelessWindow(f'Notebook Server: {uri.split("?")[0]}', uri, app=self)
        else:
            self.windows[uri].window.present()

    def do_open(self, files, *_):
        """
        reserved method name for GtkApplication
        connected to file-open signal
        """

        for file in files:
            filepath = file.get_path()
            if filepath is None:
                uri = file.get_uri().replace("pyneapple://", "http://")
                self.open_uri(uri)
            elif filepath[-6:] == ".ipynb":
                self.open_filename(filepath)

    def do_shutdown(self):
        """
        reserved method name for GtkApplication
        connected to shutdown (i.e. app quit) signal
        """
        Gtk.Application.do_shutdown(self)
        self.serverprocess.terminate()
