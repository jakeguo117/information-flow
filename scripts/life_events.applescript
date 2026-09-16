on run argv
	if (count of argv) < 1 then return ""
	set dayStr to item 1 of argv
	set AppleScript's text item delimiters to "-"
	set parts to text items of dayStr
	set AppleScript's text item delimiters to ""
	if (count of parts) < 3 then return ""
	set y to (item 1 of parts) as integer
	set m to (item 2 of parts) as integer
	set d to (item 3 of parts) as integer
	set targetDay to current date
	set year of targetDay to y
	set month of targetDay to m
	set day of targetDay to d
	set time of targetDay to 0
	set nextDay to targetDay + (1 * days)
	set out to ""

	try
		tell application "Calendar"
			repeat with c in calendars
				try
					set evs to (every event of c whose start date ≥ targetDay and start date < nextDay)
					repeat with e in evs
						set out to out & "cal|" & (my isoStamp(start date of e)) & "|" & (summary of e) & linefeed
					end repeat
				end try
			end repeat
		end tell
	end try

	tell application "Reminders"
		repeat with r in reminders
			try
				if (completed of r) is false then
					set due to missing value
					try
						set due to due date of r
					end try
					if due is not missing value then
						if due < nextDay then
							set out to out & "rem|" & (my isoDate(due)) & "|" & (name of r) & linefeed
						end if
					end if
				end if
			end try
		end repeat
	end tell
	return out
end run

on pad2(n)
	return text -2 thru -1 of ("0" & n)
end pad2

on isoDate(d)
	set y to year of d
	set m to my pad2(month of d as integer)
	set da to my pad2(day of d)
	return (y as text) & "-" & m & "-" & da
end isoDate

on isoStamp(d)
	return (my isoDate(d)) & "T" & (my pad2(hours of d)) & ":" & (my pad2(minutes of d))
end isoStamp
