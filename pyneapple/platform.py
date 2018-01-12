import platform
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk, GLib

SYSTEM = platform.system()
del platform

if SYSTEM == "Windows":
    # Pylint doesn't like this.
    from gi.repository import WebKit
    platformat = lambda x: x[2:] if x[1] == ":" else x
    class WebView(WebKit.WebView):
        def run_javascript(self, script):
            return super().execute_script(script)
else:
    gi.require_version('WebKit2', '4.0')
    from gi.repository import WebKit2
    WebView = WebKit2.WebView
    platformat = lambda x: x
