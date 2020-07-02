"use strict";

var Dashboard = function(options) {
    var charts = options.charts;
    var default_charts = options.default_charts;
    var editable = !!options.editable;
    var edit_mode = !!options.edit_mode;
    var labels = options.labels;
    var widget_html = options.widget_html;
    var ignore_change_event = false;
    var selector = options.selector || '.grid-stack';
    var current_url = options.current_url || prewikka_location().href;

    var grid = $(selector).gridstack({
        resizable: {handles: 'e, se, s, sw, w'},
        draggable: {handle: '.panel-heading'},
        animate: true,
        verticalMargin: '5px'
    }).data('gridstack');

    var window_width = $(window).width();

    function _on_resize() {
        if ( $(window).width() != window_width ) {
            window_width = $(window).width();

            $.map($('.grid-stack .grid-stack-item'), function(el) {
                resize_item($(el));
            });
        }
    }
    $("#main").on("resize", _on_resize);

    $('#edit-mode').on('change', function() {
        set_edit_mode(this.checked);
        _ajax({ data: { 'editable': this.checked ? 1 : 0 } });
    });

    $(selector).on('click', '.wbutton > button', function(event) {
        $(event.target).closest('.wmodal').remove();
    });

    // Catch modal and display them properly in the targeted widget
    $(selector).on('show.bs.modal', function(event) {
        _modal_on_widget($(event.target).parent());
        $(event.target).remove();

        return false;
    });

    $(selector).on('click', '.delete', function() {
        if ( $(this).attr('data-confirm') )
            return;

        var id = $(this).data("id");
        prewikka_resource_destroy($('#' + id));
        grid.removeWidget($('#' + id));
        _ajax({ data: {'destroy': id} });
    });

    $(selector).on('click', '.edit', function() {
        prewikka_ajax({
            url: "dashboard/" + $(this).data("id") + "/edit"
        });
    });

    $(selector).on('click', '.message_list_nav_button > a', function(e) {
        var wbody = $(e.target).parents('.panel-body');

        _ajax({
            type: 'GET',
            url: e.target.href,
            success: function(json) {
                wbody.html(json.content);
                wbody.find('.prewikka-view-config').remove();
            },
            error: _on_error(wbody)
        });

        return false;
    });

    $(selector).on('change', function(item) {
        if ( ! ignore_change_event )
            save_grid();
    });

    $('#confirm-init').on('click', function() {
        load_widgets(default_charts, true);
        set_edit_mode(editable);
    });

    $('#confirm-reset').on('click', function() {
        grid.removeAll();
        _ajax({ data: {'reset': true} });
    });

    $('.export-grid').on('click', function() {
        // Cannot use _ajax here because of the bypass option
        prewikka_ajax({ url: current_url, data: {'export': true} });
    });

    $('.import-grid').on('click', function() {
        if ( $(this).attr('data-confirm') )
            return;

        prewikka_import({
            extensions: ".json",
            callback: function(total, name, data) {
                try {
                    data = JSON.parse(data);
                    if ( ! $.isArray(data) || ! data.every($.isPlainObject) )
                        throw "Invalid value";
                }
                catch(e) {
                    prewikka_dialog({message: labels["Failed to import the dashboard."], classname: "danger"});
                    return;
                }

                grid.removeAll();
                _ajax({
                    data: {'reset': true},
                    success: function() {
                        load_widgets(data, true);
                    }
                });
            }
        });
    });

    $(selector).on('addWidget', function(event, data) {
        if ( data.id ) {
            prewikka_resource_destroy($('#' + data.id));
            data.reload = true;
        }
        else {
            _init_widget(data);
        }

        load_widget(data);
    });

    $(selector).on('resizestart', function(event, ui) {
        var render_dom = $(event.target).find('.renderer-elem');
        if (!render_dom.length) return;

        var widget_body = $(event.target).find('.panel-body');

        if (render_dom.attr('resizeable') == "false") {
            widget_body.html("");
        }
    });

    $(selector).on('resizestop', function(event, ui) {
        // We set a timeout because gridstack doesn't return the final
        // size of the resized widget
        setTimeout(function() {
            resize_item($(event.target));
        }, 250);
    });

    if ( charts.length == 0 ) {
        if ( editable && default_charts.length > 0 )
            $('#empty-dashboard-dialog').modal();
    }
    else
        load_widgets(charts, false);

    set_edit_mode(edit_mode);


    /*
     * DashboardCustom functions
     */
    function _ajax(settings)
    {
        $.ajax($.extend({ type: 'POST',
                          url: current_url,
                          prewikka: {error: false, spinner: false, bypass:true}}, settings || {}));
    }

    function _on_error(container)
    {
        return function(xhr, status, error) {
            var m;

            if ( ! xhr.responseText )
                m = {message: error || labels["Connection error"]};
            else
                m = JSON.parse(xhr.responseText);

            container.html(m.content);
        }
    }

    function resize_item(grid_item)
    {
        var render_dom = grid_item.find('.renderer-elem');
        // There is no renderer element when an unexpected error occurs
        if ( render_dom.length == 0 ) return;

        if ( render_dom.attr('resizeable') == "auto" ) return;

        var widget_body = grid_item.find('.panel-body');
        var css_update = render_dom.hasClass("renderer-elem-error") ? render_dom : render_dom.find('div');

        css_update.first().css({
            'width': widget_body.width(),
            'height': widget_body.height()
        });

        if ( render_dom.attr('resizeable') == "true" || render_dom.hasClass("renderer-elem-error") )
            render_dom.trigger('resize');
        else if ( grid_item.find('.wmodal').length == 0 )
            load_widget({id: grid_item.attr('id'), reload: true});
    }

    function load_widgets(wlist, save)
    {
        ignore_change_event = true;

        // Do not sort if the widgets' positions are undefined
        // See https://github.com/gridstack/gridstack.js/issues/1292
        if ( wlist.length != 0 && wlist[0].x !== undefined )
            wlist = GridStackUI.Utils.sort(wlist);

        $.each(wlist, function(idx, widget) {
            if ( save )
                widget.save = save;

            if ( wlist[idx - 1] && wlist[idx - 1].category === "text" )
                widget.new_line = true;

            _init_widget(widget);
            load_widget(widget);
        });

        ignore_change_event = false;
        save_grid();
    }

    function set_edit_mode(value)
    {
        editable = value;
        grid.movable('.grid-stack-item', value);
        grid.resizable('.grid-stack-item', value);
        $('.add-widget, .reset-grid, .import-grid').prop('disabled', ! value);
        $('.delete, .edit').toggle(value);
        $('.panel-heading').toggleClass('panel-movable', value);
    }

    function save_grid()
    {
        if ( ! edit_mode )
                return;

        var wlist = [];

        $.map($(selector).find('.grid-stack-item'), function(el) {
            el = $(el);
            var node = el.data('_gridstack_node');
            var widget = {};

            widget.id = el.attr('id');
            widget.x = node.x;
            widget.y = node.y;
            widget.width = node.width;
            widget.height = node.height;

            wlist.push(widget);
        });

        if ( wlist.length > 0 )
            _ajax({ data: { update: true, widgets: JSON.stringify(wlist) }});
    }

    function _init_widget(winfos)
    {
        if ( ! winfos.id )
            winfos.id = uuid.v1();

        if ( ! winfos.width )
            winfos.width = 4;

        if ( ! winfos.height )
            winfos.height = 5;
    }

    function load_widget(winfos)
    {
        var widget;

        if ( winfos.reload )
            widget = $("#" + winfos.id);
        else {
            widget = _build_widget(winfos);

            grid.addWidget(widget, {
                x: winfos.x,
                y: winfos.y,
                width: winfos.width,
                height: winfos.height,
                autoPosition: (typeof winfos.x == 'undefined')
            });
            _initialize_components(widget);

            if ( winfos.category === "text" || winfos.category === "blank" )
                return;
        }

        winfos.realwidth = $(widget).find('.panel-body').width();
        winfos.realheight = $(widget).find('.panel-body').height();
        winfos.x = $(widget).data('_gridstack_node').x;
        winfos.y = $(widget).data('_gridstack_node').y;

        if ( winfos.x !== 0 && winfos.new_line === true ) {
            grid.removeWidget( widget );
            load_widget({"x": winfos.x,
                         "y": winfos.y,
                         "width": winfos.width,
                         "height": winfos.height,
                         "category": "blank"});
            winfos.x = undefined;
            load_widget(winfos);
            return;
        }

        _ajax({
            type: 'GET',
            data: $.extend({ load: true, widget: JSON.stringify(winfos) }, $("#main form").serializeObject()),
            success: function(json) {
                if ( winfos.category == 'view' ) {
                    if ( ! json.url ) {
                        var div = $("<div>", {
                            class: "renderer-elem renderer-elem-error"
                        }).append($("<div>", {
                            class: "text-center-vh",
                            text: "Unknown view '" + winfos.view + "'"
                        }));
                        $('.pbody-' + winfos.id).html(div);
                        return;
                    }
                    _ajax({
                        type: 'GET',
                        url: json.url,
                        data: $("#main form").serializeObject(),
                        success: function(data) {
                            $('.pbody-' + winfos.id).html("<div class=\"scrollable\">" + data.content + "</div>");
                            $('.pbody-' + winfos.id + ' .prewikka-view-config').remove();
                            $('.title-' + winfos.id).text(winfos.title);
                        },
                        error: _on_error($('.pbody-' + winfos.id))
                    });
                } else if ( winfos.category == 'image' ) {
                    var div = $('<div/>', { class: 'widget-img' });
                    $('<img/>', { src: winfos.url }).appendTo(div);
                    $('.pbody-' + winfos.id).html(div);
                    $('.title-' + winfos.id).text(winfos.title);
                } else {
                    $('.pbody-' + winfos.id).html(json.html);
                    var pscript = $("<script>", {
                        'type': 'text/javascript',
                        'text': json.script
                    });
                    $('.pscript-' + winfos.id).html(pscript);
                    $('.title-' + winfos.id).text(json.title);

                    widget.find('.period-display').toggle("period_display" in json);
                    if ( "period_display" in json ) {
                        widget.find('.period-start').text(json.period_display.start);
                        widget.find('.period-end').text(json.period_display.end);
                    }

                    widget.find('.filter')
                        .toggle("filter" in json)
                        .data('bs.popover').options.content = json.filter;
                }
            },
            error: _on_error($('.pbody-' + winfos.id))
        });
    }

    /* 'options' object must have the properties 'id', 'title' and 'category' */
    function _build_widget(options)
    {
        if ( options.category == "text" )
            return $("<legend/>").html('<b>' + options.title + '</b>');

        if ( options.category === "blank" )
            return $('<div/>', { 'id': options.id });

        var widget = $($.parseHTML(widget_html)[0]);

        widget.attr('id', options.id);
        widget.find('.panel-title').addClass('title-' + options.id).text(options.title);
        widget.find('.edit, .delete').attr('data-id', options.id);
        widget.find('.panel-body').addClass('pbody-' + options.id);
        widget.find('.panel-script').addClass('pscript-' + options.id);

        return widget;
    }

    function _modal_on_widget(widget) {
        var wmodal = $('<div/>', { 'class': 'wmodal' });

        $('<p/>', { 'class': 'wtitle', text: widget.find('.modal-header').text() })
            .appendTo(wmodal);

        $('<p/>', { 'class': 'wtext', html: widget.find('.modal-body').contents() })
            .appendTo(wmodal);

        $('<div/>', { 'class': 'wbutton', html: widget.find('.modal-footer').contents() })
            .appendTo(wmodal);

        widget.append(wmodal);
    }

    function _destroy() {
        ignore_change_event = true;
        grid.destroy(false);
    }

    return {destroy: _destroy};
};
