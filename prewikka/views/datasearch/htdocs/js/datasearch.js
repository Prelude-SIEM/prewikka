"use strict";

function DataSearchPage(backend, criterion_config, criterion_config_default, separators, timeline_url)
{
    var page = {};
    var escapeRegex = $.ui.autocomplete.escapeRegex;

    /* Check if a word needs quotes */
    function lucene_need_quotes(value)
    {
        /*
         * We add "/"" to the lucene escape characters as ELK interpret them as a regexp
         */
        return /[/\s+\-!(){}[\]^"~*?\:\\]|&&|\|\|/g.test(value);
    }

    function idmef_need_quotes(value)
    {
        return /[\s()&|]/g.test(value);
    }

    function need_quotes(value)
    {
        var ret;

        if ( criterion_config_default == "criterion" )
            ret = idmef_need_quotes(value);
        else
            ret = lucene_need_quotes(value);

        return ret;
    }

    function quote(value)
    {
        if ( need_quotes(value) )
            return '"' + value.replace(/"/g, '\\"') + '"';

        return value;
    }

    function _criterion(path, operator, value)
    {
        if ( value == undefined )
            value = "";

        operator = criterion_config[criterion_config_default].operators[operator];

        return eval(criterion_config[criterion_config_default].format);
    }

    function lucene_criterion(path, operator, value)
    {
        // We can't mix wildcards and quotes in Lucene
        return _criterion(path, operator, (operator == "substr" && ! need_quotes(value)) ? value + "*" : quote(value));
    }

    function idmef_criterion(path, operator, value)
    {
        return _criterion(path, operator, quote(value));
    }

    function criterion(path, operator, value)
    {
        var ret;

        if ( criterion_config_default == "criterion" )
            ret = idmef_criterion(path, operator, value);
        else
            ret = lucene_criterion(path, operator, value);

        return ret;
    }

    function lucene_criterion_regex(path, operator, value)
    {
        var ret;
        var opstr = criterion_config[criterion_config_default].operators[operator];

        if ( value == undefined )
            value = "";

        ret = escapeRegex(opstr + path + ":" + value);

        if ( operator == "equal" || operator == "substr" )
            ret = "[^-]" + ret;

        return ret;
    }

    function idmef_criterion_regex(path, operator, value)
    {
        if ( value == undefined )
            value = "";

        if ( operator )
            operator = criterion_config[criterion_config_default].operators[operator];
        else
            operator = "\\s*[=<>]+\\s*";

        return escapeRegex(path) + operator + escapeRegex(value.toString());
    }

    function criterion_regex(path, operator, value)
    {
        var ret;

        if ( criterion_config_default == "criterion" )
            ret = idmef_criterion_regex(path, operator, value);
        else
            ret = lucene_criterion_regex(path, operator, value);

        return ret.replace(/\s+/g, "\s*");
    }

    /* Remove value, or field from the search bar */
    function sub_from_search(field, operator, value, positive, search)
    {
        var regex, ffield, opregex;

        ffield = criterion_regex(field, operator, value);
        search = search === undefined? $("#input_search").val() : search;

        opregex = criterion_config[criterion_config_default].operators["AND"].concat(criterion_config[criterion_config_default].operators["OR"]);
        opregex = opregex.map(escapeRegex).join("|");
        opregex = "(" + opregex + "|\\s+|^)\\s*";

        regex = opregex + ffield;
        regex += ((value) ? /(\s+|$)/ : /(".+?"|\S+)/).source;

        search = search.replace(RegExp(regex, "ig"), "");

        /*
         * Remove any empty parenthesis, or leftover && / ||
         */
        search = search.replace(RegExp(/(^\s*&&\s*)|(\s*&&\s*$)|(\(\s*\))/, "ig"), "");
        return $.trim(search);
    }

    function _add_to_input(field, operator, value, positive)
    {
        value = String(value);

        var search;

        if ( positive ) {
            search = sub_from_search(field, operator, null, false);
            search = sub_from_search(field, "notequal", value, positive, search);
        } else {
            search = sub_from_search(field, operator, value, false);
        }

        if ( search ) {
            search += " " + criterion_config[criterion_config_default].operators["AND"][0] + " ";
            search = search.replace(/(\s\s+)$/g, " ");
        }

        $("#input_search").val(search + criterion(field, operator, value));
    }

    function render_timeline(force) {
        var shown = $("#timeline").hasClass("collapse in");

        if ( ! shown )
            return;

        if ( $("#timeline_results").children().length > 0 && !force )
            return;

        prewikka_resource_destroy($('#timeline_results'))

        $.ajax({
            url: timeline_url,
            data: $("#form_search").serializeArray()
        }).done(function(data, textStatus, xhr) {
            $("#timeline_results").html(data);
        });
    }

    /* Reset the search bar */
    function reset_search() {
        $("#input_search").val("");
    }

    function update_datasearch()
    {
        set_postdata();

        $("#datasearch_table").trigger("reloadGrid");
        render_timeline(true);
    }

    /* Create the "Informations" content */
    function _create_dom_infos(category, infos, is_first) {
        var li = $('<li>', {
            class: is_first ? "active" : ""
        });

        var pill = $('<a>', {
            text: infos.label,
            class: 'ajax-bypass',
            href: '.' + category,
            role: 'tab',
            'data-toggle': 'pill'
        });

        pill.appendTo(li);
        li.appendTo($(".oca-infos .nav"));

        var div_infos = $('<div>', {
            role: "tabpanel",
            class: "tab-pane fade in " + category + (is_first ? " active" : "")
        });

        div_infos.append(infos.info.toHTML ? infos.info.toHTML() : infos.info);
        div_infos.appendTo($(".oca-infos .tab-content"));
    }

    /* Delete the "Informations" content and show the spinner */
    function _clean_dom_infos() {
        $(".oca-infos .nav > li, .oca-infos .tab-content > div").remove();
        $(".oca-infos").find('.ajax-spinner, .processed-content').toggleClass("hidden");
    }

    function get_range_info(e) {
        var range;
        var textNode;
        var offset;
        var startNode;

        if ( document.caretPositionFromPoint ) {
            range = document.caretPositionFromPoint(e.clientX, e.clientY);
            textNode = range.offsetNode;
            offset = range.offset;
            range = document.createRange();
            range.setStart(textNode, offset);
            range.setEnd(textNode, offset);
        } else if ( document.caretRangeFromPoint ) {
            range = document.caretRangeFromPoint(e.clientX, e.clientY);
            textNode = range.startContainer;
            offset = range.startOffset;
        } else if ( document.body.createTextRange ) {
            range = document.body.createTextRange();
            range.moveToPoint(event.clientX, event.clientY);
            textNode = range.parentElement();
            startNode = document.body.createTextRange();
            startNode.moveToElementText(textNode);
            range.setEndPoint("StartToStart", startNode);
            offset = range.text.length;
            textNode = textNode.firstChild;
        }

        return [range, offset, textNode];
    }

    function update_selection(e) {
        var range;
        var textNode;
        var offset;
        var startNode;
        var startPos;
        var endNode;
        var endPos;
        var textLen;

        // Do not change the selection when the popover is shown
        var visible = $("#PopoverOption").is(':visible');
        if ( visible )
            return;

        [range, offset, textNode] = get_range_info(e);

        // If the current node is not a text node, do nothing
        if ( textNode === null || textNode.nodeType != 3 )
            return;

        // When the mouse is hovering over the start of a paragraph,
        // or when it's hovering over a word separator, do nothing.
        if ( offset === 0 || separators.word.indexOf(textNode[offset]) > -1 )
            return;

        textNode.parentNode.focus();

        startNode = textNode;
        startPos = offset;
        endNode = textNode;
        endPos = offset;

        // Find the word's starting position
        find_start:
        while ( true ) {
            for ( ; startPos > 0; startPos-- ) {
                if ( separators.word.indexOf(startNode.textContent[startPos - 1]) > -1 ) {
                    break find_start;
                }
            }
            if ( startNode.parentNode.previousSibling !== null ) {
                startNode = startNode.parentNode.previousSibling.firstChild;
                startPos = startNode.textContent.length;
            } else {
                break find_start;
            }
        }

        // Find the word's ending position
        find_end:
        while ( true ) {
            for ( textLen = endNode.length; endPos < textLen; endPos++ ) {
                if ( separators.word.indexOf(endNode.textContent[endPos]) > -1 || separators.term.indexOf(endNode.textContent[endPos]) > -1 ) {
                    break find_end;
                }
            }
            if ( endNode.parentNode.nextSibling !== null ) {
                endNode = endNode.parentNode.nextSibling.firstChild;
                endPos = 0;
            } else {
                break find_end;
            }
        }

        // Apply the new selection
        range = document.createRange();
        range.setStart(startNode, startPos);
        range.setEnd(endNode, endPos);
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }

    function remove_selection(e) {
        // Do not change the selection when the popover is shown
        var visible = $("#PopoverOption").is(':visible');
        if ( visible )
            return;

        var selection = window.getSelection();
        selection.removeAllRanges();
    }

    function hide_popover(e) {
        $("#PopoverOption").hide();
        $("span.selected").each(function() {
            var parent = $(this).parent();
            $(this).contents().unwrap();
            // Merge text nodes
            parent.html(function(i, html) {
                return html;
            });
        });
    }

    function prepare_popover(e) {
        if ( e.which != 1 ) return;

        var selection = window.getSelection();
        if ( selection === null || selection.anchorNode === null || !selection.rangeCount )
            return;

        var range = selection.getRangeAt(0);
        var range2 = get_range_info(e)[0];
        if ( range !== null && range2 !== null &&
             range.compareBoundaryPoints(Range.START_TO_START, range2) > 0 ||
             range.compareBoundaryPoints(Range.END_TO_END, range2) < 0 ) {
            hide_popover(e);
            return;
        }

        e.stopImmediatePropagation();
        e.preventDefault();

        var selected_value = selection.toString();
        var contents = range.extractContents();
        var div = $("<span>", {class: "selected"});
        div[0].appendChild(contents);
        range.insertNode(div[0]);
        div.closest(".selectable").find("span:empty").remove();

        if ( ! $("#PopoverOption").is(':visible') ) {
            display_popover(div, selected_value);
            selection.removeAllRanges();
        }
    }

    /* Popover on click on selection */
    function display_popover(node, selected_value) {
        var offset = node.offset();
        var rowid = node.closest("tr").attr("id");
        var td = node.closest("td").first();
        var selected_field = node.closest("[data-field]");
        var next_char = node[0].nextSibling.nodeValue[0];
        var selected_operator = separators.term.indexOf(next_char) === -1 ? "equal" : "substr";

        selected_value = node.closest("[data-value]").data("value") || selected_value;
        selected_field = selected_field.data("field");

        $("#PopoverOption a:not(.addon_search)")
            .data("field", selected_field)
            .data("operator", selected_operator)
            .data("value", selected_value).show();

        $("#PopoverOption .dropdown-submenu:not(.oca-infos)").each(function() {
            $(this).find('.addon_search').each(function() {
                var d = $(this).data();

                var href = d.link;
                if ( ! href ) {
                    href = $(this).attr("href");
                    $(this).data("link", href);
                }

                var value = selected_value;
                if ( d.field )
                    value = $('#datasearch_table').jqGrid('getCell', rowid, d.field);

                $(this).attr("href", href.replace(/%24value/g, encodeURIComponent(value)));
                if ( d.path )
                    $(this).toggleClass('hidden', d.path !== backend + "." + selected_field.replace(/\(\d+\)/g, ""));
            });

            $(this).toggleClass('disabled', $(this).find('li a:not(.hidden)').length == 0);
        });

        $("#PopoverOption a.groupby_search").attr("href", prewikka_location().href + "?groupby[]=" + selected_field);
        $("#PopoverOption .groupby_search span").text(selected_field);
        $("#PopoverOption").show();

        var oca_position = "bottom";
        var popover = $("#PopoverOption .popover");
        var top = offset.top + node.height();
        var left = offset.left - popover.width() / 2 + node.width() / 2;

        popover.find(".dropdown-submenu").removeClass("pull-left");

        if ( offset.left + node.width() / 2 + popover.width() > window.innerWidth ) {
            top -= popover.height() / 2 + node.height() / 2;
            left = offset.left - popover.width();
            oca_position = "left";
            popover.find(".dropdown-submenu").addClass("pull-left");
        } else if ( offset.left - node.width() / 2 - popover.width() / 2 < 0 ) {
            top -= popover.height() / 2 + node.height() / 2;
            left = offset.left + node.width();
            oca_position = "right";
        } else if ( offset.top + node.height() + popover.height() > window.innerHeight ) {
            top = offset.top - (node.height() / 2 + popover.height());
            oca_position = "top";
        }

        popover.removeClass("bottom top right left").addClass(oca_position);
        $("#PopoverOption").css({"top": top, "left": left});

        /* Modify the "informations" content if empty */
        var divinfos = $(".oca-infos");

        if ( divinfos.find('.panel-heading').text() === selected_value )
            return false;
        else
            _clean_dom_infos();

        var elem = {
            field: selected_field,
            value: selected_value,
            query: criterion(selected_field, selected_operator, selected_value),
            query_mode: criterion_config_default
        };

        var orig = $("#datasearch_table").jqGrid('getGridParam', 'userData')[rowid].cell;

        for ( var i in orig ) {
            elem[i] = (orig[i] && orig[i].toString) ? orig[i].toString() : orig[i];
        }

        if ( orig._criteria )
            elem["_criteria"] = JSON.stringify(orig._criteria);

        $.ajax({
            url: prewikka_location().pathname + "/ajax_infos",
            data: elem,
            prewikka: {spinner: false, error: false},
            success: function(data) {
                divinfos.find('.panel-heading').text(selected_value);
                var is_first = true;
                $.each(data.infos, function(k, v) {
                    _create_dom_infos(k, v, is_first);
                    is_first = false;
                });
            },
            error: function(xhr, status, error) {
                var m;

                if ( ! xhr.responseText )
                    m = {message: error};
                else
                    m = JSON.parse(xhr.responseText);

                divinfos.find(".tab-content").html(m.content);
            },
            complete: function() {
                divinfos.find('.ajax-spinner, .processed-content').toggleClass("hidden");
            }
        });
    }

    function set_postdata() {
        var pdata = $("#datasearch_table").getGridParam("postData") || {};

        $.each($("#form_search :input").serializeArray(), function(i, input) {
            pdata[input.name] = input.value;
        });

        return pdata;
    }

    page.listing = function(elem, columns, url, jqgrid_params) {
        CommonListing(elem, {}, {
            datatype: "json",
            url: url,
            postData: set_postdata(),
            colNames: columns.names,
            colModel: columns.model,
            rowattr: function(row, data, id) {
                if ( data._classes )
                    return { "class": data._classes };
            },
            subGrid: true,
            beforeProcessing: function(data) {
                _destroy_components(elem);
                data.userdata = data.rows;
                $("#datasearch input[name='datasearch_criteria']").val(JSON.stringify(data.criteria));
            },
            loadComplete: function() {
                _resizeGrid($(elem));
                _initialize_components(elem);
                $("span.selectable", elem).on("mousemove", "span", update_selection)
                                          .on("mouseleave", "span", remove_selection)
                                          .on("mousedown", "span", prepare_popover);
            },
            subGridRowExpanded: function(subgridDivId, rowId) {
                var subgrid = $("#" + $.jgrid.jqID(subgridDivId));

                /* Delete the first empty td when the checkboxes are not present */
                if (! $("#view-config-editable").prop("checked")) {
                    subgrid.parent().siblings().first().remove();
                }

                subgrid.html("<div class=\"loader\"></div>");

                var elem = {};
                var orig = $(this).jqGrid('getGridParam', 'userData')[rowId].cell;

                for ( var i in orig ) {
                    elem[i] = (orig[i] && orig[i].toString) ? orig[i].toString() : orig[i];
                }

                if ( orig._criteria )
                    elem["_criteria"] = JSON.stringify(orig._criteria);

                $.ajax({
                    url: prewikka_location().pathname + "/ajax_details",
                    data: elem,
                    prewikka: {spinner: false},
                    success: function(result) {
                        subgrid.html(result);
                        _initialize_components(subgrid);
                    },
                    error: function(result) {
                        subgrid.html(result.responseJSON.content);
                    }
                });
            }
        }, jqgrid_params);
    };

    /* Custom event to update datasearch */
    $("#main").on("datasearch:update", function() {
        prewikka_save_parameters($("#form_search").serializeArray());
        update_datasearch();
    });

    /* Event on link to add a complex filter in the searchbar */
    $("#main").on("click", "td a.add_search", function() {
        var criteria = $(this).data("criteria");
        criteria.forEach(function(criterion) {
            _add_to_input(criterion["field"], criterion["operator"], criterion["value"], true);
        });
        hide_popover();
        update_datasearch();
    });

    /* Event on popover link */
    $("#main").on("click", "#PopoverOption .new_search, #PopoverOption .add_search, .subgrid i.add_search", function() {
        if ( $(this).hasClass("new_search") )
            reset_search();

        _add_to_input($(this).data("field"), $(this).data("operator") || "equal", $(this).data("value"), true);
        hide_popover();
        update_datasearch();
    });

    $("#main").on("click", "#PopoverOption .del_search, .subgrid i.del_search", function() {
        var search = sub_from_search($(this).data("field"), null, quote($(this).data("value")), false);
        $("#input_search").val(search);

        _add_to_input($(this).data("field"), "not" + ($(this).data("operator") || "equal"), $(this).data("value"), false);
        hide_popover();
        update_datasearch();
    });

    $("#view-config-editable").change(function() {
        $("#datasearch_table").jqGrid($(this).prop("checked") ? 'showCol' : 'hideCol', 'cb');
        $("#main .footer-buttons").collapse($(this).prop("checked") ? 'show' : 'hide');
        $("#datasearch_table").find("td.sgexpanded").click();
        $("#form_search :input[name=editable]").val($(this).prop("checked") ? 1 : 0);
    }).change();

    $("#view-config-condensed").change(function() {
        $("#datasearch_table").toggleClass("table-nowrap", $(this).prop("checked"));
        $("#form_search :input[name=condensed]").val($(this).prop("checked") ? 1 : 0);
    }).change();

    $("#datasearch_table").parents(".row").change("change", function () {
        $("#main .footer-buttons .btn.needone").prop("disabled", $("#datasearch_table input.cbox:checked").length == 0);
    }).change();

    $("#prewikka-view-config-datasearch :input").on("change", function() {
        prewikka_update_parameters($("#form_search :input:not(.mainmenu)").serializeArray());
    });

    $("#form_search").on("submit", function(event) {
        if ( $("select[name='groupby[]'] :selected").length > 0 )
            return;

        event.preventDefault();
        update_datasearch();

        /*
         * Since we override the default form submit behavior,
         * we need to manually update the parameters so that the mainmenu is saved.
         */
        prewikka_save_parameters(
            $("#form_search").serializeArray(),
            prewikka_location().href,
            {
                "complete": function() {
                    $("#form_search").trigger("submit-complete");
                }
            }
        );
    });

    $("#timeline").on('show.bs.collapse', function() {
        $("#_main").css("overflow", "hidden");
    });

    $("#timeline").on('shown.bs.collapse hidden.bs.collapse', function() {
        var shown = $("#timeline").hasClass("collapse in");

        $("#timeline input").attr("value", (shown) ? "1" : "0");
        prewikka_update_parameters($("#form_search :input:not(.mainmenu)").serializeArray());

        render_timeline();
        resizeGrid();

        $("#_main").css("overflow", "auto");
    });

    $("#main .footer-buttons").on({'shown.bs.collapse': resizeGrid, 'hidden.bs.collapse': resizeGrid});

    $("#main").on("reload", function() {
        update_datasearch();
        return false;
    });

    $("#main").on("mousedown", function(event) {
        // Hide the popover if clicked outside
        var in_popover = $(event.target).parents("#PopoverOption", ".processed-content").length > 0;
        if ( ! in_popover )
            hide_popover();
    });

    $("#PopoverOption .dropdown-submenu").hover(function handlerIn() {
        if ( $(this).offset().top + 500 > window.innerHeight )
            $(this).find(".dropdown-menu").css({"top": "unset", "bottom": 0});
    }, function handlerOut() {
        $(this).find(".dropdown-menu").css({"top": "", "bottom": ""});
    });

    var window_width = $(window).width();
    $("#main").on("resize", function() {
        if ( $(window).width() != window_width ) {
            window_width = $(window).width();

            var chart = $("[class^=renderer-elem]");
            chart.find("div").first().css("width", "100%");
            chart.trigger("resize");
        }
    });

    $('#datasearch_table').on('mouseover mouseout', ".l", function(e) {
        $(this).toggleClass('hover', e.type == 'mouseover');
        e.stopPropagation();
    });

    $("#form_search .datasearch-mode").on("click", function() {
        criterion_config_default = (criterion_config_default == "lucene") ? "criterion" : "lucene";
        $(this).text(criterion_config_default.capitalize());
        $("#form_search input[name=query_mode]").val(criterion_config_default);
        prewikka_update_parameters($("#form_search").serializeArray());
        reset_search();
    });

    /* Refresh the search bar when click on refresh button */
    $("#form_search .datasearch-refresh").on("click", reset_search);

    $("#datasearch_grid_form").on("submit-prepare", function(event, form, data) {
        var idlist = [];
        var grid = $("#datasearch_table").getGridParam("userData");

        $.each($("#datasearch_table").getGridParam("selarrrow"), function(_, value) {
            data.push({name: "criteria[]", value: JSON.stringify(grid[value].cell._criteria)});
        });

        return data;
    });

    $("#datasearch_export_form").on("submit-prepare", function(event, form, data) {
        var grid = $("#datasearch_table").getRowData();
        var selected_rows = [];

        $.each($("#datasearch_table").getGridParam("selarrrow"), function(_, value) {
            selected_rows.push(grid[value]);
        });

        // Only get the text without the HTML tags
        data.push({"name": "datasearch_grid", "value": $("<div>").html(JSON.stringify(selected_rows)).text()});
    });

    if ( $("#main #timeline").hasClass("in") )
        render_timeline();

    return page;
}


function datasearch_autocomplete_init(availabledata, history, labels) {
    var escapeRegex = $.ui.autocomplete.escapeRegex;
    var data = {fields: [], history: []};

    function split(val) {
        return val.split( /(\s+-?)/ );
    }
    /* Extract the last term to autocomplete */
    function extractLast(term) {
        return split(term).pop();
    }

    /* Delete specific query in history */
    function delete_query(item) {
        prewikka_ajax({
            type: 'POST',
            url: $(item).data('url'),
            data: {query: $(item).data('query')},
            prewikka: {spinner: false}
        });
    }

    availabledata.forEach(function(item) {
        data.fields.push({'category': labels['Fields'], 'value': item});
    });

    if ( history.content !== null )
        history.content.forEach(function(item) {
            data.history.push({'category': labels['Query history'],
                               'value': item,
                               'url': history.url['delete']});
        });

    /* Redesign the select (without overwriting autocomplete) */
    $.widget("datasearch.myautocomplete", $.ui.autocomplete, {
        _create: function() {
            this._super();
            this.widget().menu( "option", "items", "> :not(.ui-autocomplete-category)" );
        },
        _renderMenu: function(ul, items) {
            var that = this,
                currentcategory = "";

            $.each(items, function(index, item) {
                if ( item.category != currentcategory ) {
                    ul.append($("<li>", {"class": "ui-autocomplete-category",
                                         "text": item.category}));
                    currentcategory = item.category;
                }

                that._renderItemData(ul, item);
            });
        },
        _renderItem: function(ul, item) {
            var li = $("<li>")
                .attr("class", "datasearch-field")
                .append(item.value);

            // The class ui-menu-item is mandatory
            // otherwise, the element is processed as a menu separator
            if ( item.url ) {
                li = $("<i>", {"class": "fa fa-trash history-query-delete ui-menu-item",
                               "data-url": item.url,
                               "data-query": item.value})
                    .add(li);
            }

            li.appendTo(ul);

            return li;
        },
        _close: function (event) {
            if ( event != undefined && event.keepOpen === true ) {
                this.search(null, event);
                return true;
            }

            return this._super(event);
        }
    });

    $("#form_search").on("submit", function() {
        var query = $("#input_search").val();
        if ( ! query || data.history.indexOf(query) === -1 ) return;

        data.history.unshift({'category': labels['Query history'],
                              'value': query,
                              'url': history.url['delete']});
    });

    /* Autocomplete on search bar */
    $("#input_search").on("keydown", function(event) {
        if ( event.which === $.ui.keyCode.TAB && $(this).myautocomplete("instance").menu.active ) {
            event.preventDefault();
        }
    }).myautocomplete({
        appendTo: "#datasearch",
        minLength: 0,
        delay: 700,
        source: function(request, response) {
            var matcher = new RegExp("^-?" + escapeRegex(extractLast(request.term)), "i");
            var entries = {};
            $.each(data, function(key, value) {
                entries[key] = $.grep(value, function(item) {
                    return matcher.test(item.value);
                });
            });
            // Display only 5 history entries
            response(entries.fields.concat(entries.history.slice(0, 5)));
        },
        focus: function() {
            return false;
        },
        select: function( event, ui ) {
            var target = event.originalEvent.originalEvent.target;
            if ( target.localName == "i" ) {
                // Delete the entry remotely
                delete_query(target);

                // Delete the entry locally
                data.history = $.grep(data.history, function(e) {
                    return e.value != ui.item.value;
                });

                $.extend(event.originalEvent, {keepOpen: true});
                return false;
            }

            // Replace the last term with the selection
            var terms = this.value.split(/\s+/);
            terms.pop();
            terms.push(ui.item.value);
            this.value = terms.join(" ");

            return false;
        }
    }).focus(function() {
        $(this).myautocomplete("search");
    });
}
