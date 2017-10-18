"use strict";

$(function() {
    $(document).ajaxSend(function(event, xhr, settings) {
        if ( settings['spinner'] == undefined || settings['spinner'] )
            $("#ajax-spinner").show();
    });

    $(document).ajaxComplete(function(event, xhr, settings) {
        if ( settings['spinner'] == undefined || settings['spinner'] )
            $("#ajax-spinner").hide();
    });

    $(document).ajaxError(function( event, xhr, settings, error ) {
       /*
        * If the user aborded the request, this is not an error.
        */
       if ( error == "abort" )
           return;

       if ( xhr.responseText )
           prewikka_json_dialog(JSON.parse(xhr.responseText));
       else
           $("#prewikka-dialog-connection-error").modal();
    });

    $(window).on('resize', prewikka_resizeTopMenu);
});


function prewikka_location() {
    return window.history.location || window.location;
}


function _mergedict(obj1, obj2) {
        var obj3 = {};

        for ( var attrname in obj1 ) {
                obj3[attrname] = obj1[attrname];
        }

        for ( var attrname in obj2 ) {
                obj3[attrname] = obj2[attrname];
        }

        return obj3;
}


function _initialize_components(container) {
    $(container).find('[data-toggle="tooltip"]').tooltip();
    $(container).find('[data-toggle="popover"]').popover();
}

function handle_notifications(data)
{
    if ( data.notifications ) {
        $.each(data.notifications, function(_, value) {
            prewikka_notification(value);
        });
    }
}

function prewikka_drawTab(data)
{
    var form;
    var content = $(data.content);

    handle_notifications(data);

    if ( ! data.content )
        return;

    /*
     * Check self and descendant
     */
    form = $(content).find("form").addBack("form").first();
    if ( ! form.length )
        form = content = content.wrapAll('<form method="POST" action="' + prewikka_location().pathname + '"></form>').parent();

    $(form).prepend(data.menu);

    prewikka_resource_destroy($("#main"));
    $("#main").off().html(content);

    $("#topmenu_right .prewikka-help-button").data("href", data.help).prop("disabled", data.help ? false : true);
    $("#topmenu_right .prewikka-config-button").prop("disabled", $("#main .prewikka-view-config").length == 0);

    prewikka_resizeTopMenu();

    _initialize_components("#main");
    window.scrollTo(0, 0);
}


function _update_browser_title(title)
{
    /* Update the document's title according to the names of the section*/
    if ( ! document.orig_title )
       document.orig_title = document.title;

    document.title = document.orig_title + " - " + title;
}


/* Update the tab's menu according to the url */
function _url_update(settings)
{
        var url = settings['url'].split("?")[0];
        var tab = $("#topmenu .topmenu_item a[href='" + url + "']");

        if ( settings['history'] && (settings['type'] || "").toUpperCase() != "POST" ) {
                var url = settings['url'];
                var params = settings['data'];

                if ( params ) {
                        if ( typeof(params) != 'string' )
                                params = $.param(params);

                        url += "?" + params;
                }

                history.pushState(url, '', url);
        }

        if ( tab.length > 0 ) {
                $("#topmenu ul.topmenu_section").hide();
                $(tab).parent().parent().show();
                $("#topmenu .active").toggleClass("active", false);
                $(tab).parent().toggleClass("active", true);
                _update_browser_title($("#topmenu .active").closest("ul").data("section-title"));
        }
}


function _process_ajax_response(settings, data, xhr)
{
    if ( data.type == "reload" )
        location.reload();

    else if ( data.type == "ajax-reload" )
        return prewikka_ajax({ url: prewikka_location().href });

    else if ( data.type == "download" ) {
        window.location.href = data.href;
        return false;
    }

    else if ( data.type == "html" ) {
        var widget = $(data.content).find(".widget").addBack(".widget");

        if ( settings['context'] != "tab" && widget.length > 0 ) {
            widget.attr("tabindex", -1);
            $(widget).wrapInner('<div class="modal-dialog ' + $(widget).attr("data-widget-options") + '"><div class="modal-content"></div></div>');

            if ( data.help ) {
                var help = $("<button>", { "class": "close prewikka-help-button", "data-href": data.help, "html": '?&nbsp;' });
                $(widget).find(".modal-header button").after(help);
            }

            $(widget).addClass("prewikka-resources-container");
            return prewikka_json_dialog({"content": widget });
        }

        if ( settings['history'] == undefined ) {
                settings['history'] = true;
                $("#top_view_navbar .dropdown").removeClass("open"); /* FIXME this should be automated through event */
        }

        var newurl = xhr.getResponseHeader("X-responseURL");
        if ( newurl && settings.url != newurl )
            settings.url = newurl;

        _url_update(settings);

        return prewikka_drawTab(data);
    }
}


function prewikka_process_ajax_response(settings, data, xhr)
{
    if ( ! data )
        return;

    if ( data.constructor == Object )
        return _process_ajax_response(settings, data, xhr);

    for ( var i in data )
        _process_ajax_response(settings, data[i], xhr);
}


function prewikka_ajax(settings)
{
        if ( settings['dataType'] == undefined )
                settings['dataType'] = "json";

        settings['beforeSend'] = function(xhr) {
                if ( window._prewikka_current_xhr != null)
                        window._prewikka_current_xhr.abort();

                window._prewikka_current_xhr = xhr;
        };

        settings['complete'] = $.makeArray(settings['complete']);
        settings['complete'].push(function(xhr) {
                window._prewikka_current_xhr = null;
        });

        return $.ajax(settings).done(function(data, status, xhr) {
                prewikka_process_ajax_response(settings, data, xhr);
        });
}



function prewikka_EventSource(config)
{
    var jsonStream = new EventSource(config['url']);

    if ( config['error'] == undefined ) {
        config['error'] = function(e) {
            if ( e.data )
                prewikka_json_dialog(JSON.parse(e.data));
            else
                $("#prewikka-dialog-connection-error").modal();

            jsonStream.close();
        };
    }

    if ( config['close'] == undefined ) {
        config['close'] = function(e) {
            jsonStream.close();
        };
    }

    jsonStream.addEventListener('close', function(e) {
        config["close"](e)
        jsonStream.close();
    });

    var decode_json = function(e) { return JSON.parse(e.data) };
    if ( config['type'] != undefined && config['type'] != 'json' ) {
        decode_json = function(e) { return e };
    }

    for ( var ev in config['events'] ) {
        (function(_ev) {
            jsonStream.addEventListener(_ev, function(e) { config['events'][_ev](decode_json(e)) });
        })(ev);
    }

    jsonStream.onmessage = function(e) { config['message'](decode_json(e)) };
    jsonStream.onerror = function(e) { config['error'](e) };

    return jsonStream;
}



function _update_parameters(data, location, method)
{
    if ( ! location )
        location = prewikka_location().href;

    return prewikka_ajax({ method: method,
             url: location + "/ajax_parameters_update",
             spinner: false,
             data: data
    });
}


function prewikka_update_parameters(data, location)
{
    return _update_parameters(data, location, "PATCH");
}


function prewikka_save_parameters(data, location)
{
    return _update_parameters(data, location, "PUT");
}
