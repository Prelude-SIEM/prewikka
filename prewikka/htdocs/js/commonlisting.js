"use strict";

function CommonListing(elem, text, options, restored_parameters) {
    var dfd = $.Deferred();

    function genericFormatter(value, opts, rowObj) {
        if ( value )
            return value.toHTML ? value.toHTML() : _.escape(value);
        else
            return "";
    }

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

    $(elem).addClass("commonlisting table table-striped");

    for ( var i in options['colModel'] ) {
        if (! options['colModel'][i].formatter )
            options['colModel'][i].formatter = genericFormatter;
    }

    options = _mergedict({
        gridview: true,
        multiselect: true,
        multiSort: true,
        cellEdit: true,
        caption: text['title'],
        rowNum: -1,
        rowList: ['-1:all', 10, 20, 30],
        pager: true,
        hidegrid: false,
        viewrecords: true,
        globalSearch: false,
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
        resizeStop: function() {
            saveGridColumns($(this));
        },
        loadComplete: resizeGrid,
        loadError: null  // This prevents an error row to appear in the grid
    }, options);

    if ( restored_parameters )
        adaptColumns(options, restored_parameters);

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
        search: !options.globalSearch,
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
                        resizeGrid();
                        saveGridColumns($(elem));
                    }
                }
            });
        }
    });

    if ( options.globalSearch ) {
        $(".ui-jqgrid-titlebar").css("overflow", "auto")
        .append($("<label>", {for: "globalSearch", class: "pull-right"}).text(text["search"])
        .append($("<input>", {id: "globalSearch", type: "text"})));

        $("#globalSearch").on("keypress", function(e) {
            if ( e.which === $.ui.keyCode.ENTER ) {
                var query = $(this).val();
                var postData = grid.jqGrid("getGridParam", "postData");
                if ( options.datatype == "json" ) {
                    postData.query = query;
                }
                else {
                    var rules = $.map(grid.jqGrid("getGridParam", "colModel"), function(column) {
                        if ( column.search !== false )
                            return {field: column.name, op: "cn", data: query};
                    });
                    postData.filters = {groupOp: "OR", rules: rules};
                }
                grid.jqGrid("setGridParam", {search: true});
                grid.trigger("reloadGrid", [{page: 1, current: true}]);
                return false;
            }
        });
    }

    grid.delete_rows = function(rows) {
        // Iterate upwards because 'rows' gets modified
        for ( var i = rows.length - 1; i >= 0; i-- )
            grid.delRowData(rows[i]);

        grid.trigger("reloadGrid", [{current: true}]);
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

    prewikka_resource_register({
        destroy: function() {
            grid.jqGrid("clearGridData");
            grid.jqGrid("GridDestroy");
        }
    });

    resizeGrid();
    return grid;
}

$(window).on("resize", resizeGrid);

function resizeGrid() {
    $(".commonlisting").each(function(i, grid) {
        _resizeGrid(grid);
    });
}

function _resizeGrid(grid) {
    var titleHeight = $(".ui-jqgrid-titlebar:visible").outerHeight() || 0,
        headerHeight = $(".ui-jqgrid-hdiv:visible").outerHeight() || 0,
        pagerHeight = $(".ui-jqgrid-pager:visible").outerHeight() || 0,
        parent = $(grid).closest('.ui-jqgrid').parents('.modal-body, #main');

    var delta = titleHeight + headerHeight + pagerHeight + 10;

    if ( parent.attr('id') == 'main' ) {
        var height = $("#_main_viewport").height() - $(grid).closest('.ui-jqgrid').position().top - delta;

        if ( $('.footer-buttons').is(':visible') )
            height = $('.footer-buttons').offset().top - $(grid).closest('.ui-jqgrid').offset().top - delta;

        $(grid).jqGrid("setGridHeight", height, true);
    }

    var container = $(grid).closest(".container, .container-fluid");
    if ( container.length > 0 )
        parent = container;

    $(grid).jqGrid("setGridWidth", parent.width(), true);
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
    // Do not use jQuery selector because rowid may contain dots
    var row = document.getElementById(rowid);
    form.closest('div.ui-jqdialog').position({
        my: "right",
        at: "right",
        of: $(row)
    });
}

function disableButtons(elem, title) {
    $(elem).prop("disabled", true).prop("title", title);
}

function enableButtons(elem, title) {
    $(elem).prop("disabled", false).prop("title", "");
}

function saveGridColumns(grid) {
    var columns = [];
    var colModel = grid.jqGrid("getGridParam", "colModel");

    $.each(colModel, function(i, col) {
        // Ignore dynamically-added columns
        if ( ! col.hidedlg )
            columns.push({
                name: col.name,
                width: col.width,
                hidden: col.hidden
            });
    });

    prewikka_update_parameters({
        ["jqgrid_params_" + grid.attr("id")]: JSON.stringify(columns)
    });
}
