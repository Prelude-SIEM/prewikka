<form action='?' method='POST'>
	<!-- BEGIN hidden -->
	<input type='hidden' name='{NAME}' value='{VALUE}'/>
	<!-- END hidden -->
	<table class="properties_change_table">
		<!-- BEGIN entry -->
		<tr class='{TYPE}'>
			<td>{NAME}</td>
			<!-- BEGIN value -->
				<!-- BEGIN text -->
				<td><input type='text' name='{ARGUMENT}' {VALUE}/></td>
				<!-- END text -->
				
				<!-- BEGIN password -->
				<td><input type="password" name='{ARGUMENT}' {VALUE}/></td>
				<!-- END password -->
				
				<!-- BEGIN checkbox -->
				<td><input type='checkbox' name='{ARGUMENT}' {VALUE}/></td>
				<!-- END checkbox -->
			<!-- END value -->
		</tr>
		<!-- END entry -->
	</table>
	<br/>
	<input type='submit' value='{BUTTON_LABEL}'/>
</form>
