<table cellpadding="3">
    <tr bgcolor="#E2EBF5">
        <td>Sensor ID</td>
        <td>Sensor name</td>
        <td>Notes</td>
        <td>Group</td>
        <td>Model</td>
        <td>Version</td>
        <td>OS Version</td>
        <td>Action</td>
    </tr>

    <!-- BEGIN alert -->
    <tr bgcolor="{COLOR}">
        <td>{ANALYZERID}</td>
        <td>{SENSORNAME}</td>
        <td>{NOTES}</td>
        <td>{GROUP}</td>
        <td>{MODEL}</td>
        <td>{VERSION}</td>
        <td>{OSVERSION}</td>
        <td><a href="index.py?mod=sensors&amp;r=delsensor&amp;sid={SID}&amp;delsensor[sensorid]={ANALYZERID}"><font color="#d2312a">Unregister</font></a></td>
    </tr>
    <!-- END alert -->

