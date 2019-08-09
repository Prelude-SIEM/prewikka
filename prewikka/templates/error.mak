<%!
from traceback import format_exception

from prewikka import utils
from prewikka.utils import html
from mako.exceptions import RichTraceback

try:
    from mako.exceptions import syntax_highlight, pygments_html_formatter
except:
    pygments_html_formatter = None

    def syntax_highlight(filename='', language=None):
        return html.escape

def inherit(context):
    if not context.get('is_ajax_error'):
        return "/prewikka/templates/baseview.mak"
    else:
        return None
%>


<%def name="tracebackf()">
<%
    tback = RichTraceback(error=traceback[1], traceback=traceback[2])
    src = tback.source
    line = tback.lineno
    if src:
        if isinstance(src, bytes):
            src = src.decode()

        lines = src.split("\n")
    else:
        lines = None
%>

<style>
    .context { margin-bottom: 40px; }
    .stacktrace { margin:5px 5px 5px 5px; }
    .highlight { padding:0px 10px 0px 10px; background-color:#9F9FDF; }
    .nonhighlight { padding:0px; background-color:#DFDFDF; }
    .sourceline { margin:5px 5px 10px 5px; font-family:monospace;}
    .location { font-size:60%; }
    .highlight { white-space:pre; }

% if pygments_html_formatter:
    ${pygments_html_formatter.get_style_defs()}
    .linenos { min-width: 2.5em; text-align: right; }
    pre { margin: 0; padding: 5px; }
    .syntax-highlighted { padding: 0 10px; }
    .syntax-highlightedtable { border-spacing: 1px; }
    .nonhighlight { border-top: 1px solid #DFDFDF;
                    border-bottom: 1px solid #DFDFDF; }
    .stacktrace .nonhighlight { margin: 5px 15px 10px; }
    .sourceline { margin: 0 0; font-family:monospace; }
    .code { background-color: #F8F8F8; width: 100%; }
    .error .code { background-color: #FFBDBD; }
    .error .syntax-highlighted { background-color: #FFBDBD; }
% endif
</style>

<textarea style="position: absolute; top: -999px" class="traceback-value">${"".join(format_exception(*traceback))}</textarea>

<div class="traceback">
  <h3>${ _("Detail") }
    <span class="traceback-copy pull-right" title="${_('Copy to clipboard')}"><i class="fa fa-clipboard"></i></span>
  </h3>
  <div>

    % if lines:
        <div class="context nonhighlight">
        % for index in range(max(0, line - 2), min(len(lines), line + 2)):
            <%
                if pygments_html_formatter:
                    pygments_html_formatter.linenostart = index + 1

                    if index + 1 == line:
                        old_cssclass = pygments_html_formatter.cssclass
                        pygments_html_formatter.cssclass = 'error ' + old_cssclass
            %>

            ${ lines[index] | syntax_highlight(), n }

            <%
                if index + 1 == line and pygments_html_formatter:
                    pygments_html_formatter.cssclass = old_cssclass
            %>
        % endfor
        </div>
    % endif

    <div class="stacktrace">
    % for (filename, lineno, function, line) in tback.reverse_traceback:
        <div class="location">${filename}, line ${lineno}:</div>
        <div class="nonhighlight">
            <%
                if pygments_html_formatter:
                    pygments_html_formatter.linenostart = lineno
            %>
            <div class="sourceline">${ line | syntax_highlight(filename),n }</div>
        </div>
    % endfor
    </div>

  </div>
</div>
</%def>



<%inherit file="${inherit(context)}" />
<%block name="content">

<div class="error-dialog" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="static" data-keyboard="true">

<script type="text/javascript">
  $(function() {
    $("div.traceback").accordion({collapsible: true, active: false, heightStyle: "content"});

    $(".traceback-copy").on("click", function() {
        var elem = $(this).closest(".traceback").siblings("textarea.traceback-value")[0];
        elem.select();
        elem.setSelectionRange(0, elem.value.length);
        document.execCommand("copy");
        return false;
    });
  });
</script>

    <div class="modal-dialog ${ 'modal-lg' if traceback or output else '' }">

      <div class="modal-content">
        <div class="modal-header ${ 'alert-warning' if code == 401 else 'alert-danger' }">
          <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
          % if errno:
          <span style="float:right; margin-right: 5px" title="${ _('Error: {0}').format(errno)}"><i class="fa fa-question-circle"></i></span>
          % endif
          <h5 class="modal-title" id="dialogLabel">${_(name) if name else _('An unexpected condition happened') }</h5>
        </div>

        <div class="modal-body">
             <p>${_(message)}</p>
             % if details:
                   <p><b>${_("Error: {0}").format(_(details))}</b></p>
             % endif

             % if output:
                   <br />
                   <pre><samp>${ output }</samp></pre>
             % endif

             % if code != 401 and code >= 400 and code < 500:
                   <br />
                   <p>${ _("This may be due to one or more of the following reasons:") }</p>
                   <ul>
                        <li>${ _("You don't have the required permissions.") }</li>
                        <li>${ _("Required apps are disabled. See the %s page for more details.") % ('<a href="settings/apps">Apps</a>') | n }</li>
                   </ul>
             % endif

            % if traceback:
                <br />
                ${ tracebackf() }
            % endif
        </div>

        <div class="modal-footer standard clearfix">
% if is_ajax_error:
 % if code != 401:
          <a class="btn btn-primary ok" aria-hidden="true" data-dismiss="modal">${ _('OK') }</a>
 % else:
        ## If the session expired, we proceed to reloading the whole page when the user validates the
        ## dialog. This will redirect the user to the Prewikka login page.

        <button class="btn btn-default cancel" data-dismiss="modal" aria-hidden="true">${ _('Cancel') }</button>
        <a class="btn btn-primary signin" onclick="window.location = window.location;"><span class="fa fa-sign-in"></span> ${ _('Sign in') }</a>
 % endif
% else:
        <div class="pull-left">
          <input class="btn btn-default" type="button" value="${ _("Back") }" onclick="history.back()" />
        </div>
        <div class="pull-right">
          <input class="btn btn-primary" type="submit" value="${ _("Retry") }" onclick="location.reload()"/>
          % if code >= 400 and code <= 500:
           <a class="btn btn-primary ajax-bypass" href="${ utils.iri2uri(env.request.web.get_baseurl()) }"><i class="fa fa-home"></i> ${ _("Redirect to main page") }</a>
          % endif
        </div>
% endif

        </div>
      </div>
    </div>

</div>

</%block>
