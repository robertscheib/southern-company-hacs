#!/usr/bin/env bash
# Sync changes from nicor-gas-support to hacs-nicor-standalone,
# rewriting custom_components/southern_company/ -> custom_components/nicor_gas/.
#
# Usage:
#   ./sync-standalone.sh          # sync last commit
#   ./sync-standalone.sh 3        # sync last N commits
#   ./sync-standalone.sh abc123   # sync from <commit> to HEAD

set -euo pipefail

SUPPORT_BRANCH="nicor-gas-support"
STANDALONE_BRANCH="hacs-nicor-standalone"
STANDALONE_REMOTE="nicor-gas-hacs"
PATCH=$(mktemp /tmp/nicor-sync-XXXXXX.patch)

# Determine the diff range
ARG="${1:-1}"
if [[ "$ARG" =~ ^[0-9]+$ ]]; then
  RANGE="HEAD~${ARG}..HEAD"
else
  RANGE="${ARG}..HEAD"
fi

# Must be on the support branch
CURRENT=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT" != "$SUPPORT_BRANCH" ]]; then
  echo "error: run this from $SUPPORT_BRANCH (currently on $CURRENT)" >&2
  exit 1
fi

# Generate patch for just the integration files
git diff "$RANGE" -- custom_components/southern_company/ > "$PATCH"

if [[ ! -s "$PATCH" ]]; then
  echo "Nothing to sync (no changes to custom_components/southern_company/ in $RANGE)."
  rm "$PATCH"
  exit 0
fi

# Rewrite paths
sed -i 's|custom_components/southern_company/|custom_components/nicor_gas/|g' "$PATCH"

# Build a commit message from the synced commits
MSG=$(git log --oneline "$RANGE" | sed 's/^/  /')

git checkout "$STANDALONE_BRANCH"

if ! git apply "$PATCH"; then
  echo "error: patch did not apply cleanly — resolve conflicts manually." >&2
  git checkout "$SUPPORT_BRANCH"
  rm "$PATCH"
  exit 1
fi

rm "$PATCH"

git add -u
git commit -m "sync: apply changes from $SUPPORT_BRANCH

Synced range: $RANGE

$MSG

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push "$STANDALONE_REMOTE" "${STANDALONE_BRANCH}:main"

git checkout "$SUPPORT_BRANCH"

echo ""
echo "Synced and pushed to $STANDALONE_REMOTE/main."
