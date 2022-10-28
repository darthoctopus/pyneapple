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
import hashlib
import shutil

from notebook.notebookapp import NotebookApp

from .config import config

def md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

class PyneappleLocalServer(object):
    """
    Adapted from N Whitehead
    """

    def __init__(self):
        self.port = int("4" + str(time.time()).split('.')[-1][:4])
        self.token = md5(str(time.time()))
        self.servername = 'localhost'
        print(f"http://{self.servername}:{self.port}/?token={self.token}")

    def run(self):
        """
        Run the Jupyter server with configuration options
        """

        # Always serve from root
        sys.argv = [sys.executable, '--port={}'.format(self.port), '/']
        # note: omitting this line and specifying the port and notebook_dir
        # using properties of NotebookApp leads to open_browser = False
        # not being respected. I have no idea why this is the case, and no
        # time or patience to debug this.

        os.environ['JUPYTER_CONFIG_DIR'] = os.path.expanduser(config.get('ConfigDir'))
        os.environ['JUPYTER_DATA_DIR'] = os.path.expanduser(config.get('DataDir'))

        # copy custom resources
        # I used to symlink but this breaks when doing pip upgrades
        customres = os.path.dirname(__file__) + '/custom'
        try:
            # really only important for first run
            os.makedirs(os.environ['JUPYTER_CONFIG_DIR'])
        except Exception:
            print("Config directory Exists")

        try:
            shutil.copytree(customres, os.environ['JUPYTER_CONFIG_DIR'] + '/custom')
        except Exception:
            print("Custom Resources Exist")
        try:
            os.makedirs(os.path.expanduser(config.get('TmpDir')))
        except Exception:
            print("Temp directory Exists")

        app = NotebookApp()
        app.open_browser = False
        app.token = self.token

        app.initialize()
        app.contents_manager.allow_hidden = True
        app.start()
