<form action="?" method="post">
    <input type="hidden" name="mod" value="groups"/>
    <input type="hidden" name="r" value="addgroup"/>
    <input type="hidden" name="sid" value="{SID}"/>
    <input type="hidden" name="addgroup[gid]" value="{GID}"/>
    <table>
        <tr>
            <td>Group name:</td>
            <td><input type="text" name="addgroup[name]"/></td>
        </tr>
        <tr>
            <td>Notes:</td>
            <td><input type="text" name="addgroup[notes]"/></td>
        </tr>
        <tr>
            <td><input type="submit" value="Add"/></td>
        </tr>
    </table>
</form>
