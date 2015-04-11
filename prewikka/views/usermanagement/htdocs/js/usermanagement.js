$(document).ready(function(){
  $("#_main").on("click", ":input.usersettings.cancel", function(event) {
        $(this).closest("div.ui-dialog").children(".ui-dialog-content").dialog('destroy').remove();
        return false;
  });

  $("#_main").on("change", "form.usersettings select[name=language], form.usersettings select[name=theme]", function() {
        $(this.form).data("need_reload", true);
  });

  $("#_main").on("submit", ".usersettings", function() {
        var form = $(this);

        /*
         * The following is done to prevent a double flicker in case localtion.reload() is going
         * to be called.
         */
        $.ajax({url: $(this).attr("action"), data: $(this).serialize(), type: $(this).attr("method"), dataType: "json"}).done(function(data) {
            if ( $(form).data("need_reload") )
                location.reload();
            else {
                $(form).parent().parent().find(".ui-dialog-content").dialog('destroy').remove();
                prewikka_drawTab(data);
            }
      });

      return false;
  });

});
