<form action="?" method="post">
    <input type="hidden" name="mod" value="sensors"/>
    <input type="hidden" name="r" value="addsensor"/>
    <input type="hidden" name="sid" value="{SID}"/>
    <input type="hidden" name="addsensor[sensorid]" value="{SENSORID}"/>
    <table>
        <tr>
            <td>Name</td>
            <td><input type="text" name="addsensor[name]"/></td>
        </tr>
        <tr>
            <td>Notes</td>
            <td><input type="text" name="addsensor[notes]"/></td>
        </tr>
        <tr>
            <td>Group</td>
            <td><select name="addsensor[group]">
                    <option value="0">None</option>
                    <!-- BEGIN groups -->
                    <option value="{GID}">{GNAME}</option>
                    <!-- END groups -->
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

