function CommonListing(elem, text, columns, data, editLink, deleteLink) {

    $(elem).addClass("commonlisting");

    columns['model'][0].formatter = function(cellValue, options) {
        var link = $('<a>').prop("class", "widget-link")
                           .prop("title", text['edit'] + ': ' + options.rowId)
                           .prop("href", editLink + '?id=' + options.rowId)
                           .text(cellValue);
        return link.wrap("<div>").parent().html();
    };

    var grid = prewikka_grid(elem, {
        colNames: columns['names'],
        colModel: columns['model'],
        data: data,
        gridview: true,
        multiselect: true,
        multiSort: true,
        cellEdit: true,
        caption: text['title'],
        rowNum: -1,
        rowList: ['-1:all', 10, 20, 30],
        pager: true,
        hidegrid: false,
        viewrecords: true
    })
    .jqGrid('navGrid', {
        add: false,
        edit: false,
        del: false,
        search: true,
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

    $(".button-add").on("click", function() {
        prewikka_widget({
            url: prewikka_location().href + "/" + editLink,
            dialog: {
                title: text['new']
            }
        });
    });
    $(".button-duplicate").on("click", function() {
        var row = grid.getGridParam("selrow");
        if ( ! row ) return;
        prewikka_widget({
            url: prewikka_location().href + "/" + editLink,
            data: {id: row, duplicate: "true"},
            dialog: {
                title: text['new']
            }
        });
    });
    $(".button-delete").on("click", function() {
        var rows = grid.getGridParam("selarrrow");
        if ( rows.length == 0 ) return;
        grid.delGridRow(rows, {
            onclickSubmit: function() {
                $.ajax({
                    url: prewikka_location().href + "/" + deleteLink,
                    data: {action: "delete", id: rows}
                });
            },
            afterShowForm: function(form) {
                // Center delete confirmation dialog
                form.closest('div.ui-jqdialog').position({
                    my: "center",
                    of: $("div#main")
                });
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
