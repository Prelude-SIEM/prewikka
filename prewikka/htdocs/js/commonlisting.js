function CommonListing(elem, text, options) {

    $(elem).addClass("commonlisting");

    options['colModel'][0].formatter = function(cellValue, opts, rowObj) {
        var link = $('<a>').prop("class", "widget-link")
                           .prop("title", rowObj.title)
                           .prop("href", rowObj.link)
                           .text(cellValue);
        return link.wrap("<div>").parent().html();
    };

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
        gridComplete: grid_buttons_state,
        onSelectAll: grid_buttons_state,
        onSelectRow: grid_buttons_state
    }, options);

    function grid_buttons_state() {
        update_buttons_state($(this).jqGrid('getGridParam', 'selarrrow').length);
   }

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
        buttonicon: "ui-icon-gear",
        caption: "",
        title: "Reorder Columns",
        onClickButton: function() {
            $(elem).jqGrid('columnChooser');
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

    $(".button-add").on("click", function() {
        prewikka_widget({
            url: prewikka_location().href + "/" + options.editLink,
            dialog: {
                title: text['new']
            }
        });
    });
    $(".button-duplicate").on("click", function() {
        var row = grid.getGridParam("selrow");
        if ( ! row ) return;
        prewikka_widget({
            url: prewikka_location().href + "/" + options.editLink,
            data: {id: row, duplicate: "true"},
            dialog: {
                title: text['new']
            }
        });
    });
    $(".button-delete").on("click", function() {
        var rows = grid.getGridParam("selarrrow");
        if ( ( rows.length == 0 ) || ( $(this).data("confirm") ) ) return;
        $.ajax({
            url: prewikka_location().href + "/" + options.deleteLink,
            data: {action: "delete", id: rows},
            success: function() {
                // Iterate upwards because 'rows' gets modified
                for ( var i = rows.length - 1; i >= 0; i-- )
                    grid.delRowData(rows[i]);

                update_buttons_state(0);
            }
        });
    });

    resizeGrid();
    return grid;
}


$(window).on("resize", function() {
    resizeGrid();
    resizeGrids();
});

function resizeGrid() {
    var grid = $(".commonlisting");
    if ( grid.length != 1 ) return;

    var titleHeight = $(".ui-jqgrid-titlebar").outerHeight() || 0;
    var headerHeight = $(".ui-jqgrid-hdiv").outerHeight() || 0;
    var pagerHeight = $(".ui-jqgrid-pager").outerHeight() || 0;
    var footerHeight = $(".footer-buttons").outerHeight() || 0;
    var margin = 5;

    var delta = titleHeight + headerHeight + pagerHeight + footerHeight + 3 * margin;

    var position = $("div#_main").position();
    var newHeight = window.innerHeight - position.top - delta;
    var newWidth = window.innerWidth - position.left - 2 * margin;
    $(grid).jqGrid("setGridHeight", newHeight, true);
    $(grid).jqGrid("setGridWidth", newWidth, true);
}

function resizeGrids() {
    $(".htmlgrid").each(function() {
        var newWidth = $(this).closest(".ui-jqgrid").parent().width();
        $(this).jqGrid("setGridWidth", newWidth, true);
    });
}

function getCellValue(cellvalue, options, cell) {
    return $(cell).text() || $(cell).find(":input").val();
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
