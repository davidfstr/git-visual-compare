#!/bin/bash
input=$(cat)
session_id=$(echo "$input" | jq -r '.session_id')
command=$(echo "$input" | jq -r '.tool_input.command')
Q="'"
escaped="${command//$Q/${Q}\\${Q}${Q}}"
prefixed="./sandbox bash -c ${Q}${escaped}${Q}"

sentinel_dir="/tmp/gvc-sandbox-notified"
sentinel="${sentinel_dir}/${session_id}"

mkdir -p "$sentinel_dir"
find "$sentinel_dir" -maxdepth 1 -type f -mtime +7 -delete 2>/dev/null

first_use=false
[ ! -f "$sentinel" ] && first_use=true
touch "$sentinel"

if $first_use; then
  jq -n --arg cmd "$prefixed" '{
    systemMessage: "Note: Bash commands in this session are being run inside a gvc-custom sandbox located at: ./sandbox",
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      updatedInput: { command: $cmd },
      additionalContext: "Note: Your Bash commands in this session are being run inside a gvc-custom sandbox located at: ./sandbox. Permission denied errors may be caused by the sandbox rather than the underlying command — if it matters to distinguish, ask the user to rerun the command themselves. For simple cases, consult ./sandbox directly to see what actions are allowed. There is no way to disable the sandbox."
    }
  }'
else
  jq -n --arg cmd "$prefixed" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      updatedInput: { command: $cmd }
    }
  }'
fi
