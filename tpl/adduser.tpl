<form action="?" method="post">
    <input type="hidden" name="mod" value="groups"/>
    <input type="hidden" name="r" value="adduser"/>
    <input type="hidden" name="sid" value="{SID}"/>
    <table>
        <tr>
            <td>Username</td>
            <td><input type="text" name="adduser[uname]"/></td>
        </tr>
        <tr>
            <td>Password</td>
            <td><input type="text" name="adduser[passwd]"/></td>
        </tr>
        <tr>
            <td>Realname</td>
            <td><input type="text" name="adduser[realname]"/></td>
        </tr>
        <tr>
            <td>Email</td>
            <td><input type="text" name="adduser[email]"/></td>
        </tr>
        <tr>
            <td>Group</td>
            <td><select name="adduser[gid]">
                    <option value="0">None</option>
                    <!-- BEGIN group -->
                    <option value="{GROUPID}">{GROUPNAME}</option>
                    <!-- END group -->
                </select>
            </td>
        </tr>
        <tr>
            <td>
                <input type="submit" value="Register" />
            </td>
        </tr>
    </table>
</form>

