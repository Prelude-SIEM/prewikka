% if "embedded" in env.request.parameters:
<style>
.embedded-riskoverview {
    position: relative;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    margin: 0;  /* useful for <768px */
}

.embedded-riskoverview > li {
    float: left;  /* useful for <768px */
}
</style>

<ul class="nav navbar-nav embedded-riskoverview">
% endif

% for i in data:
<li class="top_view_header_riskoverview" >
    <div class="btn btn-default navbar-btn" role="button">
        <span class="hidden-sm hidden-md">${i.title}</span>
        % for j in i.data:
            ${j}
        % endfor
    </div>
</li>
% endfor


% if "embedded" in env.request.parameters:
</ul>
% endif
