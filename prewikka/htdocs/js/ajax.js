"use strict";

var PrewikkaAjaxTarget = Object.freeze({"AUTO": 1, "TAB": 2, "LAYOUT": 3});

$(function() {
    $.xhrPool = function() {
        var that = {};

        that.pool = [];
        that.active = 0;

        that.push = function(xhr, settings) {
            if ( settings.prewikka.target == PrewikkaAjaxTarget.LAYOUT )
                return;

            that.active++;
            xhr._pool_index = that.pool.push(xhr) - 1;
        };

        that.done = function(xhr) {
            if ( xhr._pool_index == undefined || xhr._aborted ) /* LAYOUT target */
                return;

            that.pool[xhr._pool_index] = null;
            if ( --that.active == 0 )
                that.pool = [];
        };

        that.abortAll = function() {
            $(that.pool).each(function(idx, xhr) {
                if ( xhr ) {
                    xhr._aborted = true;
                    xhr.abort();
                    xhr.onreadystatechange = null;
                }
            });

            that.active = 0;
            that.pool = [];
        };

        return that;
    }();

    $.eventSourcePool = function() {
        var that = {};

        that.pool = [];
        that.active = 0;

        that.push = function(stream) {
            that.active++;
            stream._pool_index = that.pool.push(stream) - 1;
        };

        that.done = function(stream) {
            if ( stream._pool_index == undefined )
                return;

            that.pool[stream._pool_index] = null;
            if ( --that.active == 0 )
                that.pool = [];
        };

        that.abortAll = function() {
            $(that.pool).each(function(idx, stream) {
                if ( stream ) {
                    stream.close();
                }
            });

            that.active = 0;
            that.pool = [];
        };

        return that;
    }();

    $.ajaxSetup({
        prewikka: { spinner: true,
                    error: true,
                    target: PrewikkaAjaxTarget.AUTO,
                    history: true,
                    bypass: false
        }
    });

    $(document).ajaxSend(function(event, xhr, settings) {
        if ( ! _csrf_safe_method(settings.type) && check_same_origin(settings.url) );
            xhr.setRequestHeader("X-CSRFToken", get_cookie("CSRF_COOKIE"));

        if ( settings.prewikka.spinner )
            $("#ajax-spinner").show();

        $.xhrPool.push(xhr, settings);
    });

    $(document).ajaxSuccess(function(event, xhr, settings, data) {
        $.xhrPool.done(xhr);
        if ( ! settings.prewikka.bypass )
            prewikka_process_ajax_response(settings, data, xhr);
    });

    $(document).ajaxComplete(function(event, xhr, settings) {
        if ( settings.prewikka.spinner )
            $("#ajax-spinner").hide();
    });

    $(document).ajaxError(function(event, xhr, settings) {
        $.xhrPool.done(xhr);

        /*
         * User aborted the request or no error handling required
         */
        if ( xhr._aborted || ! settings.prewikka.error )
            return;

        if ( ! xhr.responseText )
            $("#prewikka-dialog-connection-error").modal();

        else if ( xhr.getResponseHeader("content-type") == "application/json" )
            prewikka_json_dialog(JSON.parse(xhr.responseText));

        else
            prewikka_json_dialog({content: xhr.responseText, error: true});
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
    $(container).find('[data-title-url]').ajaxTooltip();
    $(container).find('[autofocus]').focus();
    $(container).find('.form-control-select2').select2_container();
}


function _destroy_components(container) {
    $(container).find('[data-toggle="tooltip"]').tooltip("destroy");
    $(container).find('[data-toggle="popover"]').popover("destroy");
    $(container).find('[data-title-url]').tooltip("destroy");
    $(container).find('.form-control-select2').select2("destroy");
}


function _csrf_safe_method(method)
{
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}


function get_cookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}


function prewikka_drawTab(data)
{
    var form;
    var content = $(data.content);

    if ( ! data.content )
        return;

    $.eventSourcePool.abortAll();
    $.xhrPool.abortAll();

    /*
     * Check self and descendant
     */
    form = $(content).find("form").addBack("form").first();
    if ( ! form.length )
        form = content = content.wrapAll('<form method="POST" action="' + prewikka_location().pathname + '"></form>').parent();

    if ( ! _csrf_safe_method(form.attr("method")) )
        form.prepend('<input type="hidden" name="_csrftoken" value="' + get_cookie("CSRF_COOKIE") + '" />');

    form.prepend(data._extensions.menu);

    prewikka_resource_destroy($("#main"));
    $("#main").off().html(content);

    $("#topmenu_right .prewikka-help-button").data("href", data._extensions.help).prop("disabled", data._extensions.help ? false : true);
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

function _split_url(url) {
    var idx = url.indexOf('#');
    var frag = '';

    if ( idx != -1 ) {
        frag = url.substr(idx);
        url = url.substr(0, idx);
    }

    return [url, frag];
}

/* Update the tab's menu according to the url */
function _url_update(xhr, settings)
{
        var redirect = false;
        var url = _split_url(settings.url);
        var fragment = url[1];
        url = url[0];
        var newurl = xhr.getResponseHeader("X-responseURL");

        if ( newurl && newurl != url ) {
            url = newurl;
            redirect = true;
        }

        var tab = $("#topmenu .topmenu_item a[href='" + url.split("?")[0] + fragment + "']");

        if ( redirect || (settings.prewikka.history && (settings.type || "").toUpperCase() != "POST") ) {
            var params = settings['data'];

            if ( params && ! redirect ) {
                if ( typeof(params) != 'string' )
                        params = $.param(params);

                url += "?" + params;
            }

            url += fragment;
            history.pushState(url, document.title, url);
        }

        if ( tab.length > 0 ) {
                $("#topmenu ul.topmenu_section").hide();
                $(tab).parent().parent().show();
                $("#topmenu .active").toggleClass("active", false);
                $(tab).parent().toggleClass("active", true);
                _update_browser_title($("#topmenu .active").closest("ul").data("section-title"));
        }
}


function _process_widget(data, widget)
{
        widget.attr("tabindex", -1);
        $(widget).wrapInner('<div class="modal-dialog ' + $(widget).attr("data-widget-options") + '"><div class="modal-content"></div></div>');

        if ( data._extensions.help ) {
            var help = $("<button>", { "type": "button", "class": "close prewikka-help-button", "data-href": data._extensions.help, "html": '?&nbsp;' });
            $(widget).find(".modal-header button").after(help);
        }

        $(widget).addClass("prewikka-resources-container");
        return prewikka_json_dialog({"content": widget });
}


function _process_ajax_response(settings, data, xhr)
{
    var result;
    var default_target = "#main";
    var event = jQuery.Event("prewikka-ajax-response");

    $("#main").trigger(event, data);
    if ( event.isDefaultPrevented() )
        return;

    if ( data._extensions ) {
        $.each(data._extensions.notifications, function(_, value) {
            prewikka_notification(value);
        });
    }

    if ( data.type == "reload" ) {
        if ( data.target == "window" )
            $("#prewikka-notifications-container > div").promise().done(function() { location.reload(); });

        else if ( data.target == "view" )
            data.target = default_target;

        if ( $(data.target).length )
            $(data.target).trigger("reload", data.options || {});
    }

    else if ( data.type == "download" ) {
        window.location.href = data.href;
        result = false;
    }

    else if ( data.type == "content" ) {
        if ( data.target ) {
            $(data.target).replaceWith(data.content);
            _initialize_components(data.target);
        }

        else {
            var widget = $(data.content).find(".widget").addBack(".widget");

            if ( settings.prewikka.target == PrewikkaAjaxTarget.AUTO && widget.length > 0 ) {
                result = _process_widget(data, widget);
            } else {
                _url_update(xhr, settings);
                result = prewikka_drawTab(data);
            }
        }
    }

    if ( data._extensions ) {
        $.each(data._extensions.html_content, function(_, value) {
            $(value.target || default_target).append(value.html);
        });
    }

    return result;
}


function prewikka_process_ajax_response(settings, data, xhr)
{
    if ( ! data )
        return;

    if ( data.constructor == Object )
        return _process_ajax_response(settings, data, xhr);

    else if ( data.constructor == Array ) {
        for ( var i in data )
            _process_ajax_response(settings, data[i], xhr);
    }
}


function prewikka_ajax(settings)
{
    return $.ajax(settings);
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
            $.eventSourcePool.done(jsonStream);
        };
    }

    jsonStream.addEventListener('close', function(e) {
        if ( config['close'] != undefined )
            config["close"](e);

        jsonStream.close();
        $.eventSourcePool.done(jsonStream);
    });

    var decode_json = function(e) { return JSON.parse(e.data); };
    if ( config['type'] != undefined && config['type'] != 'json' ) {
        decode_json = function(e) { return e; };
    }

    for ( var ev in config['events'] ) {
        (function(_ev) {
            jsonStream.addEventListener(_ev, function(e) { config['events'][_ev](decode_json(e)); });
        })(ev);
    }

    jsonStream.onmessage = function(e) { config['message'](decode_json(e)); };
    jsonStream.onerror = function(e) { config['error'](e); };

    $.eventSourcePool.push(jsonStream);
    return jsonStream;
}



function _update_parameters(data, location, method, options)
{
    if ( ! location )
        location = prewikka_location().href;


    var ajax_opts = {
        method: method,
        url: location + "/ajax_parameters_update",
        prewikka: { spinner: false },
        data: data
    };

    return prewikka_ajax(_mergedict(ajax_opts, options));
}


function prewikka_update_parameters(data, location, options)
{
    return _update_parameters(data, location, "PATCH", options);
}


function prewikka_save_parameters(data, location, options)
{
    return _update_parameters(data, location, "PUT", options);
}
