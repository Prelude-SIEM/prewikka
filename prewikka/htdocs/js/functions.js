String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};


$(document).ready(function(){
  var $cache = null;
  var $cachef = null;

  $.fn.popupUnique = function(animshow, animhide) {
        if ( $cache && this.is(':visible') ) {
                $cachef($cache);
                $cache = null;
        } else {
                animshow(this);
                if ( $cache )
                        $cachef($cache);
                $cachef = animhide;
                $cache = this;
        }

        return false;
  };

  $.fn.check = function(mode){
        return this.each(function() { this.checked = mode; } );
  };

  $(document).on("click", ".popup_menu_toggle", function(){
    $(this).next().popupUnique(function(data){data.show('fast'); data.css('display','block')}, function(data){data.hide('fast')});
  });



// IDMEF Browser

  var targetElem = null;

  $(document).on("click", ".idmef-browser-open", function(e) {
      targetElem = $(this).prev(".idmef-browser-target");
      var tree = $("#idmef-browser-dialog");
      if ( $(tree).dialog("isOpen") )
          $(tree).dialog("close");
      else {
          $(tree).dialog("option", "position", { my: "left top", at: "center", of: $(this) });
          $(tree).dialog("open");
      }
          e.preventDefault();
  });

  $("body").on("click", ".idmef-leaf", function(e) {
      var path = "";
      $('#idmef-prefix').children("#parenthesis, :visible").each(function() {
          path += $(this).val();
      });
      if ( path )
          path += ".";
      path += $(this).attr("id");

      var target = targetElem || $(".idmef-browser-target");
      if ($(target).is("input")) {
            $(target).val(path);
      }
      else {
            $(target).html(path);
      }
      $("#idmef-browser-dialog").dialog("close");
  });

  var to = false;

  $(document).on("keyup", "#idmef-browser-search", function() {
      if (to) { clearTimeout(to); }
      to = setTimeout(function() {
          var v = $('#idmef-browser-search').val();
          $('#idmef-browser-tree').jstree(true).search(v);
      }, 250);
  });

    $( "#help-button" ).button({
        icons: {
            primary: "ui-icon-help"
        },
        text: false
    }).hide();

    $( "#maximize-button" ).button({
        icons: {
            primary: "ui-icon-arrow-4-diag"
        },
        text: false
    });

    $( "#logout-button" ).button({
        icons: {
            primary: "ui-icon-closethick"
        },
        text: false
    });

  $("#prewikka-dialog").dialog({
      modal: true,
      appendTo: "#_main",
      autoOpen: false,
      draggable: false,
      width: 400,
      maxHeight: prewikka_dialog_getMaxHeight(),
      position: { my: "center bottom", at: "center", of: "#_main_viewport", within: "#_main_viewport" },
      show: {
          effect: "blind",
          duration: 500
      },
      hide: {
          effect: "blind",
          duration: 500
      },
      buttons: {
          Ok: function() {
              $( this ).dialog( "close" );
          }
      }
  });

  $("div.traceback").accordion({collapsible: true, active: false, heightStyle: "content"});

  $(document).on('click', '[data-confirm]', function() {
      var input = $(this);
      var confirm = input.data("confirm");

      function confirm_handler() {
          input.removeData("confirm").removeAttr('data-confirm');

          /*
           * Simulate a click using the DOM's native click() method
           * as jQuery's function does not work properly on "a" tags.
           * See http://stackoverflow.com/a/21762745 for more information.
           */
          input[0].click();
          input.attr("data-confirm", confirm).data("confirm", confirm);
          $('#dataConfirmModal').modal('hide');
          return false;
      }

      $('#dataConfirmModal').find('.modal-body').text(confirm);
      // Remove the handler in case it was already set. And set the correct handler
      $('#dataConfirmOK').off("click").on("click", confirm_handler);
      $('#dataConfirmModal').modal({show: true});
      return false;
  });

  $('ul.dropdown-menu [data-toggle=dropdown]').on('click', function() {
      $(this).closest(".dropdown-submenu").toggleClass("open");
      return false;
  });

  $(document).on('click', '.popup_menu_dynamic', function() {
      $(this).removeClass("popup_menu_dynamic");

      var popup_menu = $(this).next(".popup_menu");
      popup_menu.append($("<span>", {
        "class": "popup_menu_loading",
        "text": "Loading..."
      }));

      $.ajax({
          type: "GET",
          url: $(this).data("popup-url"),
          success: function(data) {
              var items = JSON.parse(data).content;
              popup_menu.find(".popup_menu_loading").remove();
              popup_menu.append(items.join(""));
          }
      });
  });


});

function prewikka_resizeTopMenu() {
    var mainmenu = $('#main_menu_navbar');
    var topmenu = $("#topmenu .topmenu_nav");
    var main = $("#main");
    var window_width = $(window).width();

    mainmenu.removeClass('collapsed'); // set standard view
    main.css("margin-top", "");
    mainmenu.css("margin-top", "");
    topmenu.css("height", "").css("width", "");

    if ( window_width > 768 ) {
        topmenu.css("width", window_width - mainmenu.innerWidth());

        if ( Math.max(mainmenu.innerHeight(), topmenu.innerHeight()) > 60 ) { // check if the topmenu or mainmenu is split across two lines
            mainmenu.addClass('collapsed');

            topmenu.css("width", window_width - mainmenu.innerWidth());

            var height = Math.max(mainmenu.innerHeight(), topmenu.innerHeight());

            if ( height > 60 ) { // check if we've still got 2 lines or more
                main.css("margin-top", height - 40);
                topmenu.css("height", height);
            }
        }
    }
    else {
        mainmenu.css("margin-top", topmenu.innerHeight());
        main.css("margin-top", mainmenu.innerHeight());
    }
}

function prewikka_dialog(data)
{
    $("#prewikka-dialog").dialog("option", "title", data.name || "Prelude Dialog");
    $("#prewikka-dialog .content").text(data.message);

    if ( data.traceback ) {
        $("#prewikka-dialog div.traceback").show();
        $("#prewikka-dialog div.traceback textarea").text(data.traceback);
    } else {
        $("#prewikka-dialog div.traceback").hide();
    }

    $("#prewikka-dialog").dialog('option', 'buttons', [{
        text: 'Ok',
        'class': 'btn btn-default',
        click: function() {
            $(this).dialog('close');
            /*
             * If the session expired, we proceed to reloading the whole page
             * when the user validates the dialog. This will redirect the user
             * to the Prewikka login page.
             */
            if ( data.code === 401 )
                location.reload();
        }
    }]);

    $("#prewikka-dialog").dialog("open");
}


function prewikka_dialog_getMaxHeight() {
    return $(window).height() - $("#topmenu").height() - 100;
}


function idmef_browser() {

    $("#idmef-browser-dialog").dialog({ autoOpen: false, title: "IDMEF Browser", zIndex: 99999 });
    $.jstree.defaults.search.show_only_matches = true;
    $("#idmef-browser-tree").jstree({
        "plugins": [ "search" ]
    })
    .bind('search.jstree before_open.jstree', function (e, data) {
        // Search Plugin: Allow to open found subnodes
        // See https://github.com/vakata/jstree/issues/668
        if (data.instance.settings.search.show_only_matches) {
            data.instance._data.search.dom.find('.jstree-node')
                .show().filter('.jstree-last').filter(function() {
                    return this.nextSibling;
                }).removeClass('jstree-last')
                .end().end().end().find(".jstree-children").each(function() {
                    $(this).children(".jstree-node:visible").eq(-1).addClass("jstree-last");
                });
        }
    });

}


function prewikka_getRenderSize(container, options)
{
        var parent;
        var size = [0, 0];
        var overflow_backup = document.body.style.overflow;

        /*
         * take into account potential scrollbar size.
         */
        document.body.style.overflow = "scroll";

        /*
         * Get the first parent block level element, so that we gather
         * the full usable width.
         */
        parent = $(container).parents().filter(function() {
            return $(this).css("display") == "block";
        }).first();

        size[0] = options.width;
        if ( ! size[0] )
            size[0] = $(parent).width();

        if ( typeof(options.width) == "string" && options.width.indexOf("%") != -1 ) {
            if ( ! options.spacing )
                options.spacing = 0;

            size[0] = ($(parent).width() - options.spacing) / 100 * parseInt(options.width) - options.spacing;
        }

        if ( typeof(options.height) == "string" && options.height.indexOf("%") != -1 )
            size[1] = ($(parent).width() - options.spacing) / 100 * parseInt(options.height) - options.spacing;
        else {
            size[1] = options.height;
            if ( ! size[1] )
                size[1] = $("#_main_viewport").height();
        }

        document.body.style.overflow = overflow_backup;

        return size;
}


function prewikka_grid(table, settings) {
    var conf = _mergedict({
        datatype: "local",
        cmTemplate: {title: false},
        autoencode: true,
        autowidth: true,
        forceFit: true,
        shrinkToFit: true,
        prmNames: {sort: "sort_index", order: "sort_order", search: null, nd: null}
    }, settings);

    return $(table).jqGrid(conf);
}
