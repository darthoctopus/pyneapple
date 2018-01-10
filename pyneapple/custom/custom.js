/**
 * Pineapple custom js
 *
 * This code runs once on document load
 */
define([
    'base/js/namespace',
    'base/js/events',
    'base/js/promises',
    'notebook/js/notebook',
    'notebook/js/cell',
    'custom/nbextensions/theme',
    'custom/nbextensions/readonly',
    'custom/nbextensions/button',
    'custom/nbextensions/tabs',
], function(Jupyter, events, promises, notebook, cell, theme, readOnly, button, tabs) {

    /// Register permanent events
    var flash = function(txt) {
        var old = document.title;
        document.title = txt;
        document.title = old;
    };


    var truncate = function(json) {
	pool = {}
	for (var key in json){
	    pool[key] = {
		    "name": json[key]["name"],
		    "spec": {
			    "display_name": json[key]["spec"]["display_name"]
		    }
	    }
	}
	return pool;
    }
    events.on('kernel_busy.Kernel', function (evt) {
        flash('$$$$-1|true');
    });
    events.on('kernel_idle.Kernel', function (evt) {
        flash('$$$$-1|false');
    });

    // When notebook is loaded and kernel_selector filled, respond
    // requires at least Jupyter notebook 5.1 (promise not implemented in 5.0)
    promises.notebook_loaded.then(function(appname) {
        var selector = Jupyter.notebook.kernel_selector;
        var response = function() {
            flash('$$$$-3|' + JSON.stringify(truncate(selector.kernelspecs)));
        };
        if (selector._loaded) {
            response();
        } else {
            selector.loaded.then(response);
        }
    });


    return {
        set_theme: theme.set_theme,
        toggleReadOnly: readOnly.toggleReadOnly,
        setSelectionButton: button.setSelectionButton,
        toggleSheetNew: tabs.toggleSheetNew
    };
});
