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
-- do shell script does not inherit launchd EnvironmentVariables.
-- Copy only names that are set on this osascript process.
set forwardNames to {¬
  "INTAKE_VAULT", "INTAKE_SOURCE_REMOTE", "INTAKE_GIT_USER_NAME", "INTAKE_GIT_USER_EMAIL", ¬
  "INTAKE_SOURCE_WORKTREE", "INTAKE_SOURCE_ICLOUD_WAIT", "PLUGIN_ROOT", "PYTHON3", ¬
  "INFOFLOW_CONFIG", "INFOFLOW_VAULT_ROOT", "INFOFLOW_GIT_REMOTE", "INFOFLOW_GIT_BRANCH", ¬
  "INFOFLOW_STORAGE_MODE", "YOUTUBE_CLIENT_FILE", "YOUTUBE_TOKEN_FILE"}
repeat with varName in forwardNames
  set cmd to cmd & envAssign(varName as string)
end repeat
set cmd to cmd & " /bin/sh " & quoted form of scriptPath

with timeout of 600 seconds
  do shell script cmd
end timeout

on envAssign(varName)
  try
    set varValue to system attribute varName
  on error
    set varValue to ""
  end try
  if varValue is missing value or varValue is "" then return ""
  return " " & varName & "=" & quoted form of varValue
end envAssign
