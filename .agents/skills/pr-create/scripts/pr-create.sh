#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <issue-id>"
  exit 1
fi

ISSUE_ID=$1
BRANCH_NAME=$(git branch --show-current)

if [ -z "$BRANCH_NAME" ]; then
  echo "Error: Not currently on any branch. Are you in a detached HEAD state?"
  exit 1
fi

# Path verification: Ensure we are in a sub-directory of .worktrees/
REPO_ROOT=$(git rev-parse --show-toplevel)
if [[ ! "$REPO_ROOT" =~ /\.worktrees/[^/]+$ ]]; then
  echo "Error: High-risk execution detected. pr-create.sh must be run from a worktree directory (e.g., .worktrees/issue-id)."
  echo "Current root: $REPO_ROOT"
  exit 1
fi

echo "Fetching Issue details from GitHub..."
ISSUE_TITLE=$(gh issue view "${ISSUE_ID}" --json title --jq .title)
ISSUE_URL=$(gh issue view "${ISSUE_ID}" --json url --jq .url)

if [ -z "${ISSUE_TITLE}" ]; then
  echo "Error: Could not fetch title for Issue #${ISSUE_ID}. Is the issue ID correct?"
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  # Check for accidental artifacts in the current status (ignore deletions)
  REPORTS=$(git status --porcelain | grep -v "^ D" | grep -E "(_report\.md)$" || true)
  if [ -n "$REPORTS" ]; then
    echo "Error: Detected reports in the staging area or untracked files:"
    echo "$REPORTS"
    echo "Report files MUST NOT be committed to the repository. Please move them to the artifacts directory and remove them from the repository directory."
    exit 1
  fi

  echo "Committing uncommitted changes..."
  git add .
  git commit -m "${ISSUE_TITLE} (Fix #${ISSUE_ID})"
fi

echo "Pushing branch ${BRANCH_NAME}..."
git push -u origin HEAD

# Get the default branch name to ensure PR is created against the correct base
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)

echo "Creating PR for Issue #${ISSUE_ID} on branch ${BRANCH_NAME} against ${DEFAULT_BRANCH}..."
# Use retry logic for GitHub API indexing delay
MAX_RETRIES=3
RETRY_COUNT=0
PR_URL=""

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  # Temporarily disable set -e to handle errors in the loop
  set +e
  PR_OUTPUT=$(gh pr create --title "${ISSUE_TITLE}" --body "Resolves #${ISSUE_ID}" --base "${DEFAULT_BRANCH}" --head "${BRANCH_NAME}" 2>&1)
  EXIT_CODE=$?
  set -e
  
  if [ $EXIT_CODE -eq 0 ]; then
    PR_URL=$PR_OUTPUT
    break
  fi
  
  echo "PR creation failed, retrying in 5 seconds... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
  echo "Error message: $PR_OUTPUT"
  sleep 5
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Error: Failed to create PR after $MAX_RETRIES attempts."
  exit 1
fi

echo "Enabling auto-merge..."
gh pr merge "${PR_URL}" --squash --auto

echo "Changing directory to parent repository..."
MAIN_REPO_ROOT=$(dirname $(dirname "$REPO_ROOT"))
cd "${MAIN_REPO_ROOT}"

echo "Removing worktree and cleaning up branches..."
git worktree remove ".worktrees/${BRANCH_NAME}" --force
git branch -D "${BRANCH_NAME}" || true
git push origin --delete "${BRANCH_NAME}" || true

echo "PR created and cleanup completed successfully."
echo ""
echo "=================================================="
echo "Issue URL: ${ISSUE_URL}"
echo "PR URL:    ${PR_URL}"
echo "=================================================="
