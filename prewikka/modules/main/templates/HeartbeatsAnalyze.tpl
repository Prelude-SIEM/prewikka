<table>
	<thead>
		<tr>
			<td>Analyzerid</td>
			<td>Type</td>
			<td>OS</td>
			<td>Name</td>
			<td>Location</td>
			<td>Address</td>
			<td>Last Heartbeat</td>
		</td>
	</thead>
	<tbody>
		<!-- BEGIN analyzer -->
		<tr class="table_row_even heartbeats_analyze_analyzer">
			<td>{ANALYZERID}</td>
			<td>{TYPE}</td>
			<td>{OS}</td>
			<td>{NAME}</td>
			<td>{LOCATION}</td>
			<td>{ADDRESS}</td>
			<td>{LAST_HEARTBEAT}</td>
			<!-- BEGIN heartbeat_message -->
			<tr class="heartbeats_analyze_message">
				<td colspan="7">{CONTENT}</td>
			</tr>
			<!-- END heartbeat_message -->
		<!-- END analyzer -->
	</tbody>
</table>
