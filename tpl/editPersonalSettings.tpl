<form action="?" method="post">
    <table>
        <input type="hidden" name="mod" value="groups"/>
        <input type="hidden" name="r" value="updatevalues"/>
        <input type="hidden" name="sid" value="{SID}"/>
        <tr>
            <td>Realname</td>
            <td><input type="text" name="updatevalues[realname]" value="{REALNAME}"/></td>
        </tr>
        <tr>
            <td>Email</td>
            <td><input type="text" name="updatevalues[email]" value="{EMAIL}" /></td>
        </tr>
        <tr>
            <td>
                <input type="submit" value="save"/>
            </td>
        </tr>
    </table>
</form>
