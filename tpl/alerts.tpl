<!--
Year
<select>
    <!-- BEGIN filteryear -->
    <option value="{VALUEYEAR}">{DESCRYEAR}</option>
    <!-- END filteryear -->
</select>

Month
<select>
    <!-- BEGIN filtermonth -->
    <option value="{VALUEMONTH}">{DESCRMONTH}</option>
    <!-- END filtermonth -->
</select>

Date
<select>
    <!-- BEGIN filterdate -->
    <option value="{VALUEDATE}">{DESCRDATE}</option>
    <!-- END filterdate -->
</select>
<br/>
<br/>

Sensor
<select>
    <!-- BEGIN filtersensor -->
    <option value="{VALUESENSOR}">{DESCRSENSOR}</option>
    <!-- END filtersensor -->
</select>

Severity
<select>
    <!-- BEGIN filterseverity -->
    <option value="{VALUESEVERITY}">{DESCRSEVERITY}</option>
    <!-- END filterseverity -->
</select>
<br/>
<br/>

-->

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
        <td><a href="index.py?mod=alerts&amp;r=viewalert&amp;viewalert[alert_ident]={ALERT_IDENT}&amp;sid={SID}"><font color="#d2312a">{ALERT_IDENT}</font></a></td>
        <td>{TIME}</td>
        <td><a href="{URL}"><font color="#d2312a">{DESCRIPTION}</font></a></td>
        <td>{SIP}</td>
        <td>{DIP}</td>
        <td>{SENSORID}</td>
        <td>{SEVERITY}</td>
        <td>{TYPE}</td>
    </tr>
    <!-- END alert -->

