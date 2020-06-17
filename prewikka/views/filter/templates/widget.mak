<%! from prewikka.dataprovider import CriterionOperator %>

<%def name="condition(field='', operator=CriterionOperator.EQUAL, value='', **kwargs)">
    <div class="form-group">
        <div class="input-group">
            <div class="form-control input-sm" style="border: none; padding: 0; position: static">
                <select class="data-paths input-value input-sm" data-placeholder="${_('Select a path...')}">
                    <% default_field = None %>
                    <optgroup label="${_('Default paths')}">
                        % for label, path in kwargs.get("default_paths", {}).items():
                        <% default_field = default_field or path %>
                        <option value="${path}" ${selected(path == field)}>${_(label)}</option>
                        % endfor
                    </optgroup>
                    <optgroup label="${_('All paths')}">
                        % for path in kwargs.get("all_paths", []):
                        <% default_field = default_field or path %>
                        <option value="${path}" ${selected(path == field)}>${path}</option>
                        % endfor
                    </optgroup>
                    % if field and field not in kwargs.get("all_paths", []) and field not in kwargs.get("default_paths", {}).values():
                    <option value="${field}" selected>${field}</option>
                    % endif
                </select>
            </div>
            <div class="input-group-addon dropdown dropdown-fixed operator">
                <input type="hidden" class="input-value" value="${operator.name}"/>
                <div data-toggle="dropdown" title="${_('Change operator')}"><span>${operator.name}</span></div>
                <ul class="dropdown-menu">
                % for op in (kwargs["operators"].get(field or default_field, []) if "operators" in kwargs else []):
                    <li><a data-value="${op}" title="${kwargs['tooltips'][op]}">${op}</a></li>
                % endfor
                </ul>
            </div>
            <input type="text" class="form-control input-sm data-value input-value" placeholder="${_('value')}" value="${value}" style="width: 300px"/>
            <span class="input-group-btn">
                <div class="btn btn-sm btn-danger delcond" title="${_('Delete condition')}"><i class="fa fa-trash"></i></div>
            </span>
        </div>
    </div>
</%def>


<%def name="group(operator=CriterionOperator.AND, operands=None, root=False, **kwargs)">
    <% OPERATORS = {"&&": _("AND"), "||": _("OR")} %>
    <div class="filter-group">
        <span class="dropdown dropdown-fixed">
            <input type="hidden" class="input-value" value="${operator.name}"/>
            <button type="button" class="btn btn-xs btn-primary" data-toggle="dropdown" title="${_('Change operator')}">
                <span>${OPERATORS[operator.name]}</span>
                <span class="caret"></span>
            </button>
            <ul class="dropdown-menu">
            % for op, label in OPERATORS.items():
                <li><a data-value="${op}">${label}</a></li>
            % endfor
            </ul>
        </span>
        <button type="button" class="btn btn-xs btn-success newcond" title="${_('Add condition')}"><i class="fa fa-plus"></i></button>
        <button type="button" class="btn btn-xs btn-success newgroup" title="${_('Add group')}"><b>&amp;</b></button>
        % if not root:
        <button type="button" class="btn btn-xs btn-danger delgroup" title="${_('Delete group')}"><i class="fa fa-trash"></i></button>
        % endif
        <ul class="filter-list">
        % if operands is not None:
            % for operand in operands:
                <li>${init(operand, **kwargs)}</li>
            % endfor
        % else:
            <li>${condition(**kwargs)}</li>
        % endif
        </ul>
    </div>
</%def>


<%def name="init(criterion, root=False, **kwargs)">
    % if not criterion:
        ${group(root=root, **kwargs)}
    % elif criterion.operator.is_boolean:
        ${group(criterion.operator, criterion.operands, root, **kwargs)}
    % else:
        ${condition(criterion.left, criterion.operator, criterion.right, **kwargs)}
    % endif
</%def>
