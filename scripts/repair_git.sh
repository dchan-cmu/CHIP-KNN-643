#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Repairing Git Object Database ==="

# 1. Clean zero-byte corrupt objects
find .git/objects/ -type f -empty -delete 2>/dev/null || true

# 2. Re-hash singlePE_design_exploration.py
if [ -f "scripts/singlePE_design_exploration.py" ]; then
    git hash-object -w scripts/singlePE_design_exploration.py >/dev/null
    echo "Restored blob for scripts/singlePE_design_exploration.py"
fi

# 3. Restore the 3 historical trees
echo -e "100644 blob 1be3f18e5327060c67375c05a74f07ffe0fadf1e\t.gitignore\n100644 blob de7ba011a049f7e91654561afd184bb7727e34ba\tLICENSE\n100644 blob a599259990d42f2ad4d29311b741e9cb85510353\tREADME.md\n040000 tree def017e008735cc0695130e680a8af88046f2b4a\tcommon\n040000 tree ae07a96815ad21f6de575c5b3ccf947587d65965\tscripts\n100644 blob 31d10198063735c2b527d11a381a18740c156a5d\tutils.mk" | git mktree >/dev/null

echo -e "100644 blob 1be3f18e5327060c67375c05a74f07ffe0fadf1e\t.gitignore\n100644 blob de7ba011a049f7e91654561afd184bb7727e34ba\tLICENSE\n100644 blob a599259990d42f2ad4d29311b741e9cb85510353\tREADME.md\n040000 tree def017e008735cc0695130e680a8af88046f2b4a\tcommon\n040000 tree 99527ab5b9e47bf9147fd229948103f54ed58655\tscripts\n100644 blob 31d10198063735c2b527d11a381a18740c156a5d\tutils.mk" | git mktree >/dev/null

echo -e "100644 blob 1be3f18e5327060c67375c05a74f07ffe0fadf1e\t.gitignore\n100644 blob de7ba011a049f7e91654561afd184bb7727e34ba\tLICENSE\n100644 blob a599259990d42f2ad4d29311b741e9cb85510353\tREADME.md\n040000 tree def017e008735cc0695130e680a8af88046f2b4a\tcommon\n040000 tree b7e0c57513a98dc8abfa60dc3a3196e4605835c9\tscripts\n100644 blob 31d10198063735c2b527d11a381a18740c156a5d\tutils.mk" | git mktree >/dev/null
echo "Restored historical commit trees"

# 4. Refresh index
git update-index --refresh 2>/dev/null || true

echo "=== Git database repaired successfully ==="
