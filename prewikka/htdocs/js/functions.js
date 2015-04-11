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


  if ( navigator.userAgent.indexOf("Konqueror") != -1 )
        $(".popup_menu").hide();


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
});


function prewikka_dialog(data)
{
    $("#prewikka-dialog").dialog("option", "title", data.name || "Prewikka Dialog");
    $("#prewikka-dialog .content").html(data.message);

    if ( data.traceback ) {
        $("#prewikka-dialog div.traceback").show();
        $("#prewikka-dialog div.traceback textarea").text(data.traceback);
    } else {
        $("#prewikka-dialog div.traceback").hide();
    }

    /*
     * If the session expired, we proceed to reload the whole page when
     * the user validate the dialog. This will redirect the user to the
     * Prewikka logging page.
     */
    if ( data.code == 401 ) {
        $("#prewikka-dialog").dialog('option', 'buttons', {
                'Ok': function() {
                        $(this).dialog('close');
                        location.reload();
                }
        });
    }

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
