<%!
from prewikka import usergroup
%>

<%block name="messagelisting_scripts"></%block>

<link rel="stylesheet" type="text/css" href="messagelisting/css/messagelisting.css">

<script type="text/javascript">
$LAB.script("messagelisting/js/messagelisting.js").wait();

$(document).ready(function() {
  $(document).on("click", "#main form :input[name=pdfgen], #main form :input[name=csvgen]", function(event) {
        $("#main form").data("enable-download", true);
  });

  $("#allbox").click(function(){
    $('input[name=selection]').check($(this).prop('checked'));
  });

  if ( navigator.userAgent.indexOf("Konqueror") != -1 ) {
        $("th.filter_popup > div").css("display", "block");
        $("th.filter_popup > div").hide();
   }

  $(".filter_popup_link").click(function(){
        var div =  $(this).nextAll("div");
        $('.filter_popup_link + div').not(div).hide();
        div.toggle();
        return false;
  });

    $(".ajax-tooltip").tooltip({
        html: true,
        container: '#main',
        trigger: 'hover',
        delay: { "show": 200, "hide": 0 },
        title: function() {
            var title = $(this).data("title");
            if ( ! title && $(this).data("title-url") ) {
                $.ajax({
                    async: false,
                    type: "GET",
                    url: $(this).data("title-url"),
                    success: function(data) {
                        title = data.content;
                        if ( title instanceof Array ) {
                            title = title.map(function(v, i) {
                                return $("<div>").text(v).html();
                            }).join("<br>");
                        }
                    }
                });
                $(this).data("title-url", null);
                $(this).data("title", title);
            }
            return title;
        }
    });
});
</script>

<%block name="message_listing_header"></%block>

<form action="${ document.href }" id="messagelisting" name="messagelisting" method="post">

<div class="prewikka-view-config collapse">
  <div class="form-inline">
    <div class="form-group">
      <label for="message_listing_limit">${ _("Limit") }</label>
      <select id="message_listing_limit" class="form-control input-sm" name="limit" onchange="$('#main form').submit()">
        % for limit_available in [10, 30, 50, 100]:
        <option value="${ limit_available }" ${ selected(limit_available == int(limit)) }>${ limit_available }</option>
        % endfor
      </select>
    </div>
  </div>
</div>

<table id="message_list_result" class="table table-striped table-bordered table-rounded table-condensed">
  <%block name="message_fields_header"></%block>

  <tbody>
    %for message in messages:
        <tr>
          ${ self.message_fields(message) }
          %if env.request.user.has("IDMEF_ALTER"):
           <td><input class="checkbox" type="checkbox" name="selection" value="${ message['selection'] }" /></td>
          %endif
        </tr>
    %endfor
  </tbody>

   <tfoot>
%if messages:
     <tr><table id="message_list_nav" style="width:100%;">
         <tr>
            % if nav['prev']:
              <td class="message_list_nav_button"><a href="${ nav['first'] }">&lt;&lt;</a></td>
              <td class="message_list_nav_button"><a href="${ nav['prev'] }">&lt;</a></td>
            % else:
              <td class="message_list_nav_button_empty">&lt;&lt;</td>
              <td class="message_list_nav_button_empty">&lt;</td>
            % endif
            % if nav['next']:
              <td class="message_list_nav_button"><a href="${ nav['next'] }">&gt;</a></td>
              <td class="message_list_nav_button"><a href="${ nav['last'] }">&gt;&gt;</a></td>
            % else:
              <td class="message_list_nav_button_empty">&gt;</td>
              <td class="message_list_nav_button_empty">&gt;&gt;</td>
            % endif
          </tr>
          <tr>
            <td class="message_list_nav_infos" colspan="4">
              ${ nav['from'] } ... ${ nav['to'] } (${ _("total") }:${ total })
            </td>
          </tr>
        </table>
       </tr>
     <tr>
       <%block name="message_extra_footer"></%block>
     </tr>
% endif
    </tfoot>
</table>
</form>
