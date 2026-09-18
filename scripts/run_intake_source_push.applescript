-- Launchd cannot open iCloud Drive files (TCC). osascript `do shell script`
-- runs in the Aqua session so Snipd/WeRead rsync and git SSH can proceed.
try
  set homeDir to system attribute "HOME"
on error
  set homeDir to ""
end try
if homeDir is "" then set homeDir to "/Users/jake"

try
  set sock to system attribute "SSH_AUTH_SOCK"
on error
  set sock to ""
end try

set scriptPath to "/Users/jake/plugins/information-flow/scripts/push_intake_sources.sh"
set cmd to "HOME=" & quoted form of homeDir & " PATH=/opt/homebrew/bin:/usr/bin:/bin"
if sock is not "" then set cmd to cmd & " SSH_AUTH_SOCK=" & quoted form of sock
set cmd to cmd & " /bin/sh " & quoted form of scriptPath

with timeout of 600 seconds
  do shell script cmd
end timeout
