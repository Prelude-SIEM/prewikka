<div id="alert_list_edition">
	<div id="timeline">
	<form action="?" method="post">
		<!-- BEGIN hidden -->
		<input type="hidden" name="{NAME}" value="{VALUE}"/>
		<!-- END hidden -->
			<div id="timeline_label">Step</div>
			<div id="timeline_value">
				<input name="timeline_value" type="text" size="8" value="{TIMELINE_VALUE}"/>
			</div>
			<div id="timeline_unit">
				<select name="timeline_unit">
					<option value="sec"{SEC_SELECTED}>Seconds
					<option value="min"{MIN_SELECTED}>Minutes
					<option value="hour"{HOUR_SELECTED}>Hours
					<option value="day"{DAY_SELECTED}>Days
					<option value="month"{MONTH_SELECTED}>Months
					<option value="year"{YEAR_SELECTED}>Years
				</select>
			</div>
			<div id="timeline_submit">
				<input type="submit"  value="apply">
			</div>
	</form>
	</div>
	<div id="timeline_range">
		<div id="timeline_start">From {TIMELINE_START}</div>
		<div id="timeline_end">To {TIMELINE_END}</div>
	</div>
	<div id="timeline_navigation">
		<div id="timeline_prev"><a href="index.py?{PREV_QUERY}">prev</a></div>
		<div id="timeline_current"><a href="index.py?{CURRENT_QUERY}">current</a></div>
		<div id="timeline_next"><a href="index.py?{NEXT_QUERY}">next</a></div>
	</div>
</div>

<div id="alert_list_result">
{ALERT_LIST}
</div>
