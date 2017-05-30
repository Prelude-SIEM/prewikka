function CommonListing(elem, text, options) {
    var dfd = $.Deferred();

    function genericFormatter(value, opts, rowObj) {
        return (value) ? prewikka_html_node(value) : "";
    }

    function _backwardCompatibleFormatter(cellValue, opts, rowObj) {
        if ( rowObj._class || rowObj._title || rowObj._link ) {
            /*
             * FIXME: OLD API, DO NOT USE, REMOVE ME.
             */
            var link = $('<a>', {
                class: rowObj._class || "widget-link",
                title: rowObj._title,
                href: rowObj._link
            }).text(cellValue);

            return link.wrap("<div>").parent().html();
        }

        return genericFormatter(cellValue, opts, rowObj);
    }

    $(elem).addClass("commonlisting table table-striped");

    for ( i in options['colModel'] ) {
        if (! options['colModel'][i].formatter )
            options['colModel'][i].formatter = (i == 0) ? _backwardCompatibleFormatter : genericFormatter;
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
        loadComplete: resizeGrid,
        loadError: null  // This prevents an error row to appear in the grid
    }, options);

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

        prewikka_ajax(_mergedict(data, {type: "POST"}));
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
    var titleHeight = $(".ui-jqgrid-titlebar").outerHeight() || 0,
        headerHeight = $(".ui-jqgrid-hdiv").outerHeight() || 0,
        pagerHeight = $(".ui-jqgrid-pager").outerHeight() || 0,
        margin = 5,
        height = 0,
        parent = $(grid).closest('.ui-jqgrid').parents('.modal-body, #_main');

    var delta = titleHeight + headerHeight + pagerHeight + margin;

    if ( parent.attr('id') == '_main' ) {
        parent = parent.siblings('#_main_viewport');
        height = parent.height() - $(grid).closest('.ui-jqgrid').offset().top;

        if ( $('.footer-buttons').is(':visible') )
            height = $('.footer-buttons').offset().top - $(grid).closest('.ui-jqgrid').offset().top - delta;
    }

    if ( height ) {
        $(grid).jqGrid("setGridHeight", height, true);
    }

    var newWidth = parent.width() - 2 * margin;
    $(grid).jqGrid("setGridWidth", newWidth, true);
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
