<table cellpadding="3">
	<tr bgcolor="#E2EBF5">
		<td>Classification</td>
		<td>Source</td>
		<td>Target</td>
		<td>Sensor</td>
		<td>Time</td>
		<td></td>
	</tr>

	<!-- BEGIN alert -->
	<tr bgcolor="{COLOR}">
		<td><font color="{SEVERITY}">{CLASSIFICATION}</font></td>
		<td>{SOURCE}</td>
		<td>{TARGET}</td>
		<td>{SENSOR}</td>
		<td>{TIME}</td>
		<td>
		<div id="style7">
		    	<a href="index.py?mod=mod_alert&amp;section=Alert%20view&amp;Alert%20view.analyzerid={ANALYZERID}&amp;Alert%20view.alert_ident={ALERT_IDENT}">
				view
			</a>
		</div>
		</td>
	</tr>
	<!-- END alert -->
