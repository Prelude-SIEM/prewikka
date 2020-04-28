function init_usersettings() {
    var length_permissions = $("form.usersettings input[name='permissions[]']:not([disabled])").length;
    var length_checked = $("form.usersettings input[name='permissions[]'][checked]:not([disabled])").length;

    if (length_permissions == length_checked && length_permissions > 0)
        $("form.usersettings input.allbox").prop('checked', true);
};
