<table cellpadding="3">
    <tr bgcolor="#E2EBF5">
        <td>Sensor ID</td>
        <td>Model</td>
        <td>Version</td>
        <td>OS Version</td>
        <td>Action</td>
    </tr>

    <!-- BEGIN alert -->
    <tr bgcolor="{COLOR}">
        <td>{ANALYZERID}</td>
        <td>{MODEL}</td>
        <td>{VERSION}</td>
        <td>{OSVERSION}</td>
        <td><a href="index.py?mod=sensors&amp;r=regsensor&amp;regsensor[analyzerid]={ANALYZERID}&amp;sid={SID}"><font color="#d2312a">Register this sensor</font></a></td>
    </tr>
    <!-- END alert -->
</table>
