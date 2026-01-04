#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="${STATE_FILE:-last_seen.json}"
BRANCH="${STATE_BRANCH:-state}"

if [ ! -f "$STATE_FILE" ]; then
  echo "No state file ($STATE_FILE) found; nothing to push."
  exit 0
fi

# Prepare a clean temporary dir to stage only the state file
TMPDIR="$(mktemp -d)"
cp "$STATE_FILE" "$TMPDIR/$STATE_FILE"

# Configure git user
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

# Create or switch to orphan branch
if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  git checkout "$BRANCH"
  # remove all tracked files to ensure branch contains only state file
  git rm -rf . >/dev/null 2>&1 || true
else
  git checkout --orphan "$BRANCH"
  git rm -rf . >/dev/null 2>&1 || true
fi

# Restore state file and commit
mv "$TMPDIR/$STATE_FILE" "$STATE_FILE"
# Ensure .gitignore does not accidentally ignore the state file in branch commit
if grep -q "^$STATE_FILE\b" .gitignore >/dev/null 2>&1; then
  sed -i.bak "/^$STATE_FILE\b/d" .gitignore || true
fi

git add "$STATE_FILE"
git commit -m "Update state file" || true
git push origin "$BRANCH" --force

echo "Pushed $STATE_FILE to branch '$BRANCH'."