<table>
<tr bgcolor="#ffffff">
<td>Time</td>
<td>{TIME}</td>
</tr>
<tr bgcolor="#eeeeee">
<td>Description</td>
<td>
<a href="{URL}"><font color="#d2312a">{DESCRIPTION}</font></a></td>
</tr>
<tr bgcolor="#ffffff">
<td>Source IP</td>
<td>{SIP}</td>
</tr>
<tr bgcolor="#eeeeee">
<td>Destination IP</td>
<td>{DIP}</td>
</tr>
<tr bgcolor="#ffffff">
<td>Sensor name</td>
<td>{SENSORID}</td>
</tr>
<tr bgcolor="#eeeeee">
<td>Severity</td>
<td>{SEVERITY}</td>
</tr>
<tr bgcolor="#ffffff">
<td>Type</td>
<td>{TYPE}</td>
</tr>
</table>
<table>
<tr bgcolor="#E2EBF5">
<td>Type</td>
<td>Data</td>
</tr>
<br/><br/>
<!-- BEGIN alert -->
<tr bgcolor="{COLOR}">
<td valign="top">{TYPE}</td>
<td valign="top"><pre style="margin:0px">{DATA}</pre></td>
</tr>
<!-- END alert -->
</table>
