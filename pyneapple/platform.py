import platform
import gi
from pyneapple.config import config
import os

SYSTEM = platform.system()
del platform

if SYSTEM == "Windows":
    # Pylint doesn't like this.
    from gi.repository import WebKit
    platformat = lambda x: x[2:] if x[1] == ":" else x
    config['csd'] = "False"
    class WebView(WebKit.WebView):
        def run_javascript(self, script):
            return super().execute_script(script)
else:
    gi.require_version('WebKit2', '4.0')
    from gi.repository import WebKit2
    WebView = WebKit2.WebView
    platformat = lambda x: x


def open_term(path):
    if SYSTEM == "Windows":
        os.system("%s /K \"cd %s\"" % (config['term'], path))
    elif SYSTEM == "Linux":
        os.system("%s --working-directory=\"%s\"" % (config['term'], path))

def open_folder(path):
    if SYSTEM == "Windows":
        os.system("explorer.exe \"%s\"" % path)
    elif SYSTEM == "Linux":
        os.system("xdg-open \"%s\"" % path)
