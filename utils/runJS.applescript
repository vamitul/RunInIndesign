on run params
	set myScript to item 1 of params
	set myPort to item 2 of params
	set paraNR to count params
	if paraNR > 2 then
		set myVer to item 3 of params
	else
		set myVer to false
	end if
	if myVer is not false then
		
		set appN to "Adobe Indesign " & replace_chars(myVer)
	else
		if exists application "Adobe InDesign CS6" then
			set appN to "Adobe Indesign CC 2014"
		else if exists application "Adobe InDesign CS6" then
			set appN to "Adobe Indesign CC"
		else if exists application "Adobe InDesign CS6" then
			set appN to "Adobe Indesign C6"
		end if
		
	end if
	set jsRunner to POSIX path of ((path to me as text) & "::" & "jsRunner.jsx") --get path to parent folder
	log jsRunner
	log appN
	using terms from application "Adobe InDesign CS6"
		tell application appN
			set myParams to {myScript, myPort}
			--your code
			--activate
			do script jsRunner language javascript with arguments myParams
		end tell
	end using terms from
end run

on replace_chars(this_text)
	if not (this_text starts with "CC.") then
		return this_text
	else
		set AppleScript's text item delimiters to "."
		set the item_list to every text item of this_text
		set AppleScript's text item delimiters to " "
		set this_text to the item_list as string
		set AppleScript's text item delimiters to ""
		return this_text
	end if
end replace_chars