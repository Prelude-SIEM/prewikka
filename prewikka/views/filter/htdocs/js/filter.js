function get_criterion(selector) {
    var selector = $(selector);

    if ( selector.hasClass("filter-group") )
        return _get_group_criterion(selector);
    else
        return _get_condition_criterion(selector);
}

function _get_group_criterion(selector) {
    var ret = null;
    var operator = selector.children("span.dropdown").children(":input.input-value").val();
    $.each(selector.children(".filter-list").children("li").children(), function() {
        if ( ret == null )
            ret = get_criterion(this);
        else
            ret = Criterion(ret, operator, get_criterion(this));
    });
    return ret;
}

function _get_condition_criterion(selector) {
    var values = $.map(selector.find(":input.input-value"), function(input) {
        return $(input).val();
    });

    return Criterion(values[0], values[1], values[2] || null);
}

function unindex_path(path) {
    return path.replace(/\([^)]+\)/g, "");
}

function FilterEdition(selector, default_paths, all_paths, operators, enums, tooltips) {

    var that = this;

    this.init = function() {
        $(selector).find(".data-paths").each(function() {
            that.init_condition($(this));
        });
    }

    this.init_condition = function(select) {
        var type = select.closest(".filter-edition").data("type");

        select.select2_container({
            width: "300px",
            tags: true,
            createTag: function(params) {
                if ( operators[type][unindex_path(params.term)] )
                    return {id: params.term, text: params.term};
                else
                    return null;
            }
        });

        that.init_operators(select);
        that.init_autocomplete(select);
    }

    this.init_operators = function(select) {
        var type = select.closest(".filter-edition").data("type");
        var ul = select.parent().siblings(".operator").children("ul").empty();
        var opdiv = $(ul).siblings("div[data-toggle=dropdown]");
        var oplist = operators[type][unindex_path(select.val())];

        $.each(oplist, function(index, operator) {
            $("<li>").append($("<a>", {
                "data-value": operator,
                "title": tooltips[operator]
            }).text(operator)).appendTo(ul);
        });

        if ( oplist.indexOf(opdiv.text()) == -1 ) {
            opdiv.children("span").first().text(oplist[0]);
        }
    }

    this.init_autocomplete = function(select) {
        var path = select.val();
        var type = select.closest(".filter-edition").data("type");
        var input = select.parent().siblings(".data-value");

        if ( enums[type][path] == null ) {
            if ( input.hasClass("ui-autocomplete-input") )
                input.autocomplete("destroy");
            return;
        }

        input.autocomplete({
            minLength: 0,
            source: enums[type][path]
        })
        .focus(function() {
            $(this).autocomplete("search");
        });
    }

    $(selector).on("click", ".newgroup", function() {
        var li = $("<li>").append($("div#example-group").clone().children());
        $(this).siblings("ul").append(li);
    });

    $(selector).on("click", ".newcond", function() {
        var li = $("<li>").append($("div#example-condition").clone().children());
        var select = li.find(".data-paths");
        var type = $(this).closest(".filter-edition").data("type");

        $.each(default_paths[type], function(label, path) {
            select.find("optgroup:first-child").append($("<option>", {value: path}).text(label));
        });
        $.each(all_paths[type], function(index, path) {
            select.find("optgroup:last-child").append($("<option>", {value: path}).text(path));
        });
        $(this).siblings("ul").append(li);
        that.init_condition(select);
    });

    $(selector).on("click", ".delgroup", function() {
        $(this).closest(".filter-group").remove();
    });

    $(selector).on("click", ".delcond", function() {
        $(this).closest(".form-group").remove();
    });

    $(selector).on("click", ".dropdown-menu a", function() {
        var menu = $(this).closest(".dropdown-menu")
        menu.siblings("[data-toggle=dropdown]").children("span").first().text($(this).text());
        menu.siblings(".input-value").val($(this).data("value"));
    });

    $(selector).on("change", ".data-paths", function() {
        that.init_operators($(this));
        that.init_autocomplete($(this));
    });

    $(selector).on("submit", function() {
        $(this).find(".filter-edition").each(function() {
            var value = null;
            if ( $(this).parent().siblings(".panel-heading").find(".type-checkbox").is(":checked") )
                value = get_criterion($(this).children(".filter-group"));

            $(this).children("input[name='filter_criteria[]']").val(JSON.stringify(value));
        });
    });

}
