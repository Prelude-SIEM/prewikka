<table cellpadding="3">
    <tr bgcolor="#E2EBF5">
        <td>Alert Ident</td>
        <td>Time</td>
        <td>Description</td>
        <td>Source IP</td>
        <td>Dest IP</td>
        <td>Sensor Name</td>
        <td>Severity</td>
        <td>Type</td>
    </tr>

    <!-- BEGIN alert -->
    <tr bgcolor="{COLOR}">
        <td><a href="index.py?mod=alert&amp;section=Alert%20view&amp;Alert%20view.alert_ident={ALERT_IDENT}"><font color="#d2312a">{ALERT_IDENT}</font></a></td>
        <td>{TIME}</td>
        <td><a href="{URL}"><font color="#d2312a">{DESCRIPTION}</font></a></td>
        <td>{SIP}</td>
        <td>{DIP}</td>
        <td>{SENSORID}</td>
        <td>{SEVERITY}</td>
        <td>{TYPE}</td>
    </tr>
    <!-- END alert -->
