/*
 * Copyright (C) 2011 Red Hat, Inc; 2016 Joel Ong
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, see <http://www.gnu.org/licenses/>.
 *
 * The Sushi project hereby grant permission for non-gpl compatible GStreamer
 * plugins to be used and distributed together with GStreamer and Sushi. This
 * permission is above and beyond the permissions granted by the GPL license
 * Sushi is covered by.
 *
 * Authors: Cosimo Cecchi <cosimoc@redhat.com>
 *          Joel Ong <joel.ong@yale.edu>
 *
 */

const GtkClutter = imports.gi.GtkClutter;
const Gtk = imports.gi.Gtk;
const GLib = imports.gi.GLib;
const Lang = imports.lang;
const Sushi = imports.gi.Sushi;
const WebKit = imports.gi.WebKit2;

const MimeHandler = imports.ui.mimeHandler;
const Utils = imports.ui.utils;

const Gio = imports.gi.Gio;

const tmpdir="/tmp/sushipython"

GLib.spawn_command_line_sync("/usr/bin/mkdir -p " + tmpdir);
GLib.spawn_command_line_sync("/usr/bin/touch " + tmpdir + "/custom.css");

const JupyterRenderer = new Lang.Class({
    Name: 'JupyterRenderer',

    _init : function(args) {
        this.moveOnClick = false;
        this.canFullScreen = true;
    },

    prepare : function(file, mainWindow, callback) {
        this._mainWindow = mainWindow;
        this._file = file;
        this._callback = callback;

        this._webView = new WebKit.WebView();
        this._webView.show_all();

        /* disable the default context menu of the web view */
        this._webView.connect ("context-menu",
                               function() {return true;});
	
	/* Prepare HTML version of ipynb — requires nbconvert */

	this._path = file.get_path();
	this._hashstr = this._path + file.query_info(Gio.FILE_ATTRIBUTE_TIME_MODIFIED,0,null).get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED);
	this._hash = GLib.compute_checksum_for_string (GLib.ChecksumType.SHA512, this._hashstr, this._hashstr.length);	
	this._newname = tmpdir + "/" + this._hash + ".html"
	
	/* Gio file for new html file */
	this._file2 = Gio.file_new_for_path(this._newname);
	if (!(this._file2.query_exists(null))) GLib.spawn_command_line_sync("/usr/bin/jupyter nbconvert \"" + this._path + "\" --output=\"" + this._newname + "\"");
	
        this._webView.load_uri(this._file2.get_uri());

        this._actor = new GtkClutter.Actor({ contents: this._webView });
        this._actor.set_reactive(true);

        this._callback();
    },

    render : function() {
        return this._actor;
    },

    getSizeForAllocation : function(allocation) {
        return allocation;
    },

    createToolbar : function() {
        this._mainToolbar = new Gtk.Toolbar({ icon_size: Gtk.IconSize.MENU });
        this._mainToolbar.get_style_context().add_class('osd');
        this._mainToolbar.set_show_arrow(false);
        this._mainToolbar.show();

        this._toolbarActor = new GtkClutter.Actor({ contents: this._mainToolbar });

        this._toolbarZoom = Utils.createFullScreenButton(this._mainWindow);
        this._mainToolbar.insert(this._toolbarZoom, 0);

        let separator = new Gtk.SeparatorToolItem();
        separator.show();
        this._mainToolbar.insert(separator, 1);

        this._toolbarRun = Utils.createOpenButton(this._file, this._mainWindow);
        this._mainToolbar.insert(this._toolbarRun, 2);

        return this._toolbarActor;
    }
});

let handler = new MimeHandler.MimeHandler();
let renderer = new JupyterRenderer();

let mimeTypes = [
    'application/x-ipynb+json'
];

handler.registerMimeTypes(mimeTypes, renderer);
