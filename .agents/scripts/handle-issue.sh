#!/bin/bash

# ==============================================================================
# handle-issue.sh
# ------------------------------------------------------------------------------
# Automatically finds the oldest confirmed, non-in-progress GitHub issue and
# triggers the /handle-issue workflow using the Gemini CLI.
#
# Designed for use with cron or other schedulers.
# ==============================================================================

set -ex

# --- Environment Setup ---
# Ensure common paths are included for cron environments
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

# Move to the project root directory (assuming script is in src/gadget/scripts/)
# Adjust if the script is called from elsewhere, but usually cron will be set to the project root.
SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if .env exists
if [ -f .env ]; then
  # Use a safer way to load .env that handles spaces and special characters
  set -o allexport
  source .env
  set +o allexport
fi

# --- Dependency Verification ---
command -v gh >/dev/null 2>&1 || { echo >&2 "Error: 'gh' CLI is required but not found in PATH."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo >&2 "Error: 'jq' is required but not found in PATH."; exit 1; }
command -v gemini >/dev/null 2>&1 || { echo >&2 "Error: 'gemini' CLI is required but not found in PATH."; exit 1; }

# --- Issue Discovery ---
# Fetch the oldest confirmed issue that is not yet in-progress
ISSUE_JSON=$(gh issue list --search 'label:"status: confirmed" -label:"status: in-progress" sort:created-asc' --limit 1 --json number)

# Extract issue number using jq. If empty, it returns an empty string.
ISSUE_NUMBER=$(echo "$ISSUE_JSON" | jq -r '.[0].number // empty')

# --- Execution ---
if [ -n "$ISSUE_NUMBER" ]; then
  echo "Found issue #$ISSUE_NUMBER. Starting automated resolution..."
  gemini -y -p "/handle-issue #$ISSUE_NUMBER"
else
  echo "No confirmed, non-in-progress issues found. Nothing to do."
fi
