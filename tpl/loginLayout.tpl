<html>
    <head>
        <link rel="stylesheet" href="lib/style.css" type="text/css"/>
        <title>LOGIN</title>
    </head>
    <body>
        <table width="100%"  border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td bgcolor="#D2312A"><img src="img/n.gif" alt="." width="1" height="4" /></td>
            </tr>
        </table>
        <table width="100%"  border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td width="160" valign="top">
                    <br/>
                    <form action="?" method="post">
                        <input type="hidden" name="mod" value="login"/>
                        <input type="hidden" name="r" value="login"/>
                        <table cellspacing="0" cellpadding="1">
                            <tr>
                                <td>Username:</td>
                                <td><input type="text" name="login[username]" size="8" class="login"/></td>
                            </tr>
                            <tr>
                                <td>Password:</td>
                                <td><input type="password" name="login[password]" size="8" class="login"/></td>
                            </tr>
                            <tr>
                                <td colspan="2" align="right"><input type="submit" value="login" class="login"/></td>
                            </tr>
                        </table>
                    </form>
                </td>
                <td valign="top">
                    <table width="100%"  border="0" cellspacing="0" cellpadding="12">
                        <tr>
                            <td background="img/bg_content.gif" height="400px" valign="top">
                                {MESSAGE}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
</html>
