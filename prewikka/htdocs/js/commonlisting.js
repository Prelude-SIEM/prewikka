"use strict";

function CommonListing(elem, text, options, restored_parameters) {
    var dfd = $.Deferred();

    function adaptColumns(options, saved_data) {
        var colModel = [];
        var columns = {};
        $.each(options.colModel, function(i, col) {
            columns[col.name] = col;
        });

        $.each(saved_data, function(i, col) {
            if ( col.name in columns ) {
                colModel.push($.extend(columns[col.name], col));
                delete columns[col.name];
            }
        });
        $.each(columns, function(name, col) {
            colModel.push(col);
        });

        options.colModel = colModel;
    }

    $(elem).addClass("commonlisting table table-striped").css("width", detectGridWidth($(elem)));

    /*
     * In jqGrid, the height attribute is specific to the height of the data, not including header and footer.
     * This is broken since it prevents a user from specifying the height on initialization, since header and
     * footer sizes are unknown at that time.
     *
     * As a result, we specify a height of 0, and call resizeGrid() in the loadComplete callback.
     */
    options = _mergedict({
        autowidth: false,
        width: detectGridWidth($(elem)),
        height: 0,
        gridview: true,
        multiselect: true,
        multiSort: true,
        cellEdit: true,
        caption: text['title'],
        rowNum: restored_parameters.limit || (options.datatype == "json" ? 20 : -1),
        rowList: options.datatype == "json" ? [10, 20, 30, 50, 100] : ['-1:all', 10, 20, 30, 50, 100],
        pager: true,
        hidegrid: false,
        viewrecords: true,
        globalSearch: false,
        useSearchbar: false,
        cmTemplate: $.jgrid.cmTemplate.html,
        onInitGrid: function() {
            if ( options.globalSearch ) {
                $(".ui-jqgrid-titlebar").css("overflow", "auto")
                .append($("<label>", {for: "globalSearch", class: "pull-right"}).text(text["search"])
                .append($("<input>", {id: "globalSearch", type: "text"})));

                $("#globalSearch").on("keypress", function(e) {
                    if ( e.which === $.ui.keyCode.ENTER ) {
                        return _searchGrid(elem, $(this).val(), options.datatype == "json");
                    }
                });
            }
        },
        gridComplete: function() {
            update_buttons_state($(this).jqGrid('getGridParam', 'selarrrow').length);
            dfd.resolve();
        },
        onSelectAll: function (rowsids, status) {
            if ( status )
                $(elem + " tr.nocheck > td > input.cbox").prop("checked", false);

            update_buttons_state($(this).jqGrid('getGridParam', 'selarrrow').length);
        },
        onSelectRow: function() {
            update_buttons_state($(this).jqGrid('getGridParam', 'selarrrow').length);
        },
        onPaging: function(pgButton) {
            if ( pgButton == "records" ) saveGrid($(this));
        },
        resizeStop: function() {
            saveGrid($(this));
        },
        beforeProcessing: function() {
            if ( options.datatype == "json" ) _destroy_components(elem);
        },
        loadComplete: function() {
            _resizeGrid($(elem));
            if ( options.datatype == "json" ) _initialize_components(elem);
        },
        loadError: null  // This prevents an error row to appear in the grid
    }, options);

    if ( restored_parameters.columns )
        adaptColumns(options, restored_parameters.columns);

    function update_buttons_state(rows_count) {
        if ( rows_count == 0 ) {
            disableButtons(".needone", "Please select at least one entry");
            disableButtons(".justone", "Please select exactly one entry");
        }
        else if ( rows_count > 1 ) {
            enableButtons(".needone");
            disableButtons(".justone", "Please select exactly one entry");
        }
        else {
            enableButtons(".needone, .justone");
        }
    }

    var grid = prewikka_grid(elem, options)
    .jqGrid('navGrid', {
        add: false,
        edit: false,
        del: false,
        search: !(options.useSearchbar || options.globalSearch),
        refresh: false
    })
    .jqGrid('navButtonAdd', {
        buttonicon: "fa-cog",
        caption: "",
        title: "Edit columns",
        onClickButton: function() {
            /*
             * This part of the code should not exist.
             * We need to call resizeGrid() after the columnChooser
             * validation and there is no way to do it outside the
             * done() method.
             *
             * The content of the done() method must be synchronized
             * with jQuery
             */
            $(elem).jqGrid('columnChooser', {
                done: function(perm) {
                    if (perm) {
                        $(elem).jqGrid("remapColumns", perm, true);
                        if ( $(elem).jqGrid("getGridParam", "forceFit") ) {
                            /* Work around an issue with resizable columns not being updated
                             * See https://github.com/free-jqgrid/jqGrid/issues/486 */
                            var last_visible;
                            var columns = {};
                            $.each(options.colModel, function(i, col) {
                                columns[col.name] = col;
                            });
                            var colModel = $(elem).jqGrid("getGridParam", "colModel");
                            $.each(colModel, function(i, col) {
                                if ( col.hidden == false && columns[col.name] ) {
                                    last_visible = col;
                                    col.resizable = columns[col.name].resizable;
                                    if ( col.resizable == undefined )
                                        col.resizable = true;
                                }
                            });
                            last_visible.resizable = false;

                            var headers = $(elem).closest(".ui-jqgrid").find("tr.ui-jqgrid-labels > th");
                            var resize_handle = headers.find("span.ui-jqgrid-resize").first();
                            headers.find("span.ui-jqgrid-resize").remove();
                            headers.each(function(i, item) {
                                if ( colModel[i].resizable )
                                    $(item).prepend(resize_handle.clone());
                            });
                        }
                        resizeGrid();
                        saveGrid($(elem));
                    }
                }
            });
        }
    })
    .jqGrid('navButtonAdd', {
        buttonicon: "fa-bolt",
        caption: "",
        title: "Reset preferences",
        onClickButton: function() {
            prewikka_dialog({message: "Reset the preferences for this grid?", type: "confirm"});

            $('#prewikka-dialog-confirm-OK').off("click").on("click", function() {
                var params = {};
                params["jqgrid_params_" + grid.attr("id")] = "{}";
                prewikka_update_parameters(params).done(function() {
                    prewikka_notification({
                        message: "Grid preferences have been reset to default. Reload the page for the changes to take effect.",
                        classname: "info",
                        duration: 5000
                    });
                });
            });
        }
    });

    grid.delete_rows = function(rows) {
        // Iterate upwards because 'rows' gets modified
        for ( var i = rows.length - 1; i >= 0; i-- )
            grid.delRowData(rows[i]);

        grid.reload([{current: true}]);
    };

    grid.ajax = function(data) {
        var rows = grid.getGridParam("selarrrow");
        if ( rows.length == 0 )
            return;

        data["data"] = _mergedict(data['data'], {id: rows});
        var s_cb = data['success'];
        if ( s_cb ) {
            data["success"] = function() { s_cb(rows); };
        }

        return prewikka_ajax(_mergedict(data, {type: "POST"}));
    };

    grid.done = function done(cb) {
        dfd.done(cb);
        return this;
    };

    grid.reload = function(options) {
        grid.trigger("reloadGrid", options);
    }

    grid.on("reload", function(event, options) {
        grid.reload($.isEmptyObject(options) ? [{current:true}] : options);
        return false;
    });

    /*
     * The following events are deprecated and should be removed !
     */
    $(".button-add").on("click", function() {
        /*
         * FIXME: OLD API, DO NOT USE, REMOVE ME.
         */
        prewikka_ajax({ url: options.editLink });
    });

    $(".button-duplicate").on("click", function() {
        /*
         * FIXME: OLD API, DO NOT USE, REMOVE ME.
         */
        var row = grid.getGridParam("selrow");
        if ( ! row ) return;
        prewikka_ajax({ url: options.editLink, data: {duplicate: row} });
    });

    $(".button-delete").on("click", function() {
        /*
         * FIXME: OLD API, DO NOT USE, REMOVE ME.
         */
        if ( $(this).data("confirm") )
            return;

        grid.ajax({ url: options.deleteLink, method: 'POST', success: grid.delete_rows });
    });

    var reloader;
    if ( options.reloadInterval ) {
        reloader = AjaxReloader(function() {
            grid.trigger("reload", {current: true});
        }, options.reloadInterval);
    }

    prewikka_resource_register({
        destroy: function() {
            grid.jqGrid("clearGridData", true);
            grid.jqGrid("GridDestroy");
            if ( reloader )
                reloader.destroy();
        },
        container: elem
    });

    return grid;
}

$(window).on("resize", resizeGrid);

function resizeGrid() {
    $(".commonlisting").each(function(i, grid) {
        _resizeGrid($(grid));
    });
}

function detectGridHeight(grid) {
    var gridtbl = $(grid).closest(".ui-jqgrid"),
        parent = gridtbl.parents('.modal, #main');

    if ( parent.attr('id') != 'main' )
        return;

    var titleHeight = gridtbl.find(".ui-jqgrid-titlebar:visible").outerHeight() || 0,
        headerHeight = gridtbl.find(".ui-jqgrid-hdiv:visible").outerHeight() || 0,
        pagerHeight = gridtbl.find(".ui-jqgrid-pager:visible").outerHeight() || 0;

    var delta = titleHeight + headerHeight + pagerHeight + 10;
    var footer = $('.footer-buttons');
    var height = $(footer).is(':visible') ? $(footer).offset().top : $(window).height();

    return height - $(gridtbl).offset().top - delta;
}

function detectGridWidth(parent) {
    var container = parent.closest("#main, .modal, .container, .container-fluid, .row, [class*=col-]");
    return container.width();
}

function _resizeGrid(grid) {
    var height = detectGridHeight(grid);
    if ( height )
        $(grid).jqGrid("setGridHeight", height, true);

    $(grid).jqGrid("setGridWidth", detectGridWidth(grid), true);
}

function _searchGrid(grid, query, is_remote) {
    var postData = $(grid).jqGrid("getGridParam", "postData");
    if ( is_remote ) {
        postData.query = query;
    }
    else {
        var rules = $.map($(grid).jqGrid("getGridParam", "colModel"), function(column) {
            if ( column.search !== false )
                return {field: column.name, op: "cn", data: query};
        });
        postData.filters = {groupOp: "OR", rules: rules};
    }
    $(grid).jqGrid("setGridParam", {search: true});
    $(grid).trigger("reloadGrid", [{page: 1, current: true}]);
    return false;
}

function getCellValue(cellvalue, options, cell) {
    return $(cell).text() || $(cell).find(":input").val();
}

function clearGridEdition(grid) {
    var param = grid.jqGrid("getGridParam");
    grid.jqGrid("saveCell", param.iRow, param.iCol);
    delete param.iRow;
}

function setConfirmDialogPosition(grid, form) {
    var rowid = grid.jqGrid('getGridParam', 'selrow');
    // Use escaping because rowid may contain dots
    var row = grid.find("#" + $.escapeSelector(rowid));
    form.closest('div.ui-jqdialog').position({
        my: "right",
        at: "right",
        of: row
    });
}

function disableButtons(elem, title) {
    $(elem).prop("disabled", true).prop("title", title);
}

function enableButtons(elem, title) {
    $(elem).prop("disabled", false).prop("title", "");
}

function saveGrid(grid) {
    var columns = [];
    var colModel = grid.jqGrid("getGridParam", "colModel");
    var params = {};

    $.each(colModel, function(i, col) {
        // Ignore dynamically-added columns
        if ( ! col.hidedlg )
            columns.push({
                name: col.name,
                width: col.width,
                hidden: col.hidden
            });
    });

    // The {[key]: value} syntax is not supported by IE11
    params["jqgrid_params_" + grid.attr("id")] = JSON.stringify({
        columns: columns,
        limit: parseInt($(".ui-pg-selbox", grid.jqGrid("getGridParam", "pager")).val())
    });
    prewikka_update_parameters(params);
}


var oldSortableRows = $.fn.jqGrid.sortableRows;

$.jgrid.extend({
    sortableRows: function(opts) {
        opts = $.extend({
            helper: function(e, item) {
                // Close any cell edition to avoid bugs
                $.fn.jqGrid.editCell.call($(this), 0, 0, false);

                // Clone the row (FIXME: #2746)
                var ret = item.clone();

                // Make sure cells have the correct width
                $("td", ret).each(function(i) {
                    this.style.width = $("td", item).eq(i).css("width");
                });

                return ret;
            }
        }, opts);
        return oldSortableRows.call($(this), opts);
    }
});

$.jgrid.cellattr = $.jgrid.cellattr || {};
$.extend($.jgrid.cellattr, {
    default_cellattr: function(rowId, value, rowObj) {
        if ( value && value.extra && value.extra["_classes"] )
            return ' class="' + value.extra["_classes"] + '"';
    }
});

$.jgrid.cmTemplate = $.jgrid.cmTemplate || {};
$.extend($.jgrid.cmTemplate, {
    html: {
        title: false,
        formatter: function(value, opts, rowObj) {
            if ( value )
                return value.toHTML ? value.toHTML() : _.escape(value);
            else
                return "";
        },
        unformat: function(value, opts) {
            return value;
        },
    }
});

$.jgrid.guiStyles.bootstrap.states.active = "";
$.jgrid.guiStyles.bootstrap.states.hover = "";
$.jgrid.guiStyles.bootstrap.states.select = "";
