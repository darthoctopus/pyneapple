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

const {GLib, GObject, Gio} = imports.gi;

const Renderer = imports.ui.renderer;
const HTML = imports.viewers.html
const tmpdir="/tmp/sushipython"
const jupyter = "/home/joel/.local/bin/jupyter"

var Klass = GObject.registerClass({
    Implements: [Renderer.Renderer],
    Properties: {
        fullscreen: GObject.ParamSpec.boolean('fullscreen', '', '',
                                              GObject.ParamFlags.READABLE,
                                              false),
        ready: GObject.ParamSpec.boolean('ready', '', '',
                                         GObject.ParamFlags.READABLE,
                                         false)
    },
}, class JupyterRenderer extends HTML.Klass {
    get ready() {
        return !!this._ready;
    }

    get fullscreen() {
        return !!this._fullscreen;
    }

    _init(file) {
        GLib.spawn_command_line_sync("/usr/bin/mkdir -p " + tmpdir);
        GLib.spawn_command_line_sync("/usr/bin/touch " + tmpdir + "/custom.css");

        let _path = file.get_path();
        let _hashstr = _path + file.query_info(Gio.FILE_ATTRIBUTE_TIME_MODIFIED,0,null).get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED);
        let _hash = GLib.compute_checksum_for_string (GLib.ChecksumType.SHA512, _hashstr, _hashstr.length);  
        let _newname = tmpdir + "/" + _hash + ".html"
        let _file2 = Gio.file_new_for_path(_newname);
        if (!(_file2.query_exists(null))) GLib.spawn_command_line_sync(jupyter + " nbconvert \"" + _path + "\" --to html --output \"" + _newname + "\"");
        super._init(_file2);
    }
});

var mimeTypes = [
    'application/x-ipynb+json'
];
