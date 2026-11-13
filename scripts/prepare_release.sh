#!/usr/bin/env bash
# Prepare clean open-source release branch (Scheme 1: zero-leak public tree)
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

echo "=== Verifying clean working tree and full gate ==="
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: working tree must be clean before preparing release" >&2
    exit 1
fi

./check.sh

RELEASE_BRANCH="release"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
TEMP_BRANCH="${RELEASE_BRANCH}-temp"
TEMP_COMMITTED=false

cleanup() {
    local rc=$?
    git checkout "$CURRENT_BRANCH" >/dev/null 2>&1 || true
    if [ "$TEMP_COMMITTED" = true ]; then
        git branch -D "$TEMP_BRANCH" >/dev/null 2>&1 || true
    fi
    exit "$rc"
}
trap cleanup ERR

echo "=== Creating/updating clean '$RELEASE_BRANCH' branch ==="
# Create orphan branch from current tree
git checkout --orphan "$TEMP_BRANCH"
git commit -m "feat: initial open-source release of bb10-gateway-core v1.0.0"
TEMP_COMMITTED=true

# Move temp orphan branch to target release branch
git branch -M "$TEMP_BRANCH" "$RELEASE_BRANCH"
TEMP_COMMITTED=false

# Return to development branch
git checkout "$CURRENT_BRANCH"
trap - ERR

echo ""
echo "=== Clean release branch '$RELEASE_BRANCH' prepared successfully ==="
echo "To publish to GitHub remote:"
echo "  git remote add origin https://github.com/ItsLaurelNotYanny/bb10-gateway-core.git"
echo "  git push -u origin ${RELEASE_BRANCH}:main"
echo "Your local '${CURRENT_BRANCH}' branch retains full development and review history."
