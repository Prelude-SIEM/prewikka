
<table>
    <form action="?" method="post">
        <input type="hidden" name="mod" value="groups" />
        <input type="hidden" name="r" value="updatepasswd" />
        <input type="hidden" name="sid" value="{SID}" />
        <tr>
            <td>Old password</td>
            <td><input type="passwd" name="updatepasswd[old]"> &nbsp; {OLD_ERROR}</td>
        </tr>
        <tr>
            <td>New password</td>
            <td><input type="passwd" name="updatepasswd[new]"></td>
        </tr>
        <tr>
            <td>New password again</td>
            <td><input type="passwd" name="updatepasswd[again]"> &nbsp; {AGAIN_ERROR}</td>
        </tr>
        <tr>
            <td>
                <input type="submit" value="Change"/>
            </td>
        </tr>
    </form>
</table>

