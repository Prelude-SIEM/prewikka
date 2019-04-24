<link rel="stylesheet" type="text/css" href="idmefnav/css/idmefnav.css" />
<div class="container">
    <h1>${ schema["name"] }</h1>

    <p>${ schema["description"] }</p>

    <div class="tab-content idmefnav-svg">${ schema['svg'] | n }</div>

    <hr>

% if schema.get("childs"):
    <h3>${ _("Children") }</h3>

    % for child in schema["childs"].keys():
    <h4><a href="${ url_for('.render', idmef_class=child) }">${ child }</a></h4>
    % endfor
% endif

% if schema.get("aggregates"):
    <h3>${ _("Aggregates") }</h3>

    % for name, aggregate in schema["aggregates"].items():
    <h4>
        % if name in full_schema:
        <a href="${ url_for('.render', idmef_class=name) }">${ name } (${ aggregate.get("multiplicity") })</a>
        % else:
        ${ name } (${ aggregate.get("multiplicity") })
        % endif
    </h4>

    <blockquote>${ aggregate["description"] }</blockquote>
    % endfor
% endif

% if schema.get("attributes"):
    <h3>${ _("Attributes") }</h3>

    % for name, attribute in schema["attributes"].items():
    <h4>
        % if name in full_schema:
        <a href="${ url_for('.render', idmef_class=name) }">${ name } (${ attribute.get("multiplicity") })</a>
        % else:
        ${ name } (${ attribute.get("multiplicity") })
        % endif
    </h4>

    <blockquote>
        ${ attribute["description"] }

        % if attribute.get("values"):
        <table class="table table-striped table-bordered">
            <thead>
                <tr>
                    <th>${ _("Rank") }</th>
                    <th>${ _("Keyword") }</th>
                    <th>${ _("Description") }</th>
                </tr>
            </thead>
            <tbody>
            % for value in attribute.get("values"):
            <tr>
                <td>${ value.get("rank") }</td>
                <td>${ value.get("keyword") }</td>
                <td>${ value.get("description") }</td>
            </tr>
            % endfor
            </tbody>
        </table>
        % endif
    </blockquote>
    % endfor
% endif

</div>
