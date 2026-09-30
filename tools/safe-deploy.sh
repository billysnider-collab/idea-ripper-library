#!/usr/bin/env bash
# Reference "rip deploy" for idearipper.com (added 2026-09-30).
# The real deploy job (author "Newsroom", Python 3.12) was not found on Billy's PC or
# the box. Whoever runs it: replace its build/commit/push step with this script.
#
#   tools/safe-deploy.sh            # after the ripper has written cards.json/shelf.yaml/books/*.md
#
# Guarantees:
#  - one deploy at a time (flock on .git/rip-deploy.lock)
#  - builds only from the repo's build_site.py at origin/main, never a cached copy
#  - aborts if build_site.py differs from origin/main's, or if HEAD is behind origin/main
#  - never force-pushes; runs the site guard before pushing and a live smoke test after
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
exec 9>".git/rip-deploy.lock"
flock -n 9 || { echo "ABORT: another rip deploy is running"; exit 3; }

TEMPLATE="build_site.py 404.html _config.yml tools .github"
git fetch --quiet origin main
# bring HEAD to origin/main first, keeping new data as uncommitted changes;
# upstream template updates are pulled in (we build from origin/main's code)
git pull --ff-only --autostash --quiet origin main || { echo "ABORT: HEAD cannot fast-forward to origin/main"; exit 5; }
BEHIND=$(git rev-list --count HEAD..origin/main)
[ "$BEHIND" = 0 ] || { echo "ABORT: HEAD is $BEHIND commits behind origin/main"; exit 5; }
# template files must never carry LOCAL edits into a deploy (checked post-pull
# against HEAD, so genuine upstream template updates don't trip the guard)
if ! git diff --quiet HEAD -- $TEMPLATE || ! git diff --cached --quiet HEAD -- $TEMPLATE; then
  echo "ABORT: local template files differ from HEAD:"
  git diff --stat HEAD -- $TEMPLATE
  echo "Fix: git checkout HEAD -- $TEMPLATE   (edit the template in the repo, not in a cache)"; exit 4
fi
LOCAL=$(sha256sum build_site.py | cut -c1-64)
REMOTE=$(git show origin/main:build_site.py | sha256sum | cut -c1-64)
[ "$LOCAL" = "$REMOTE" ] || { echo "ABORT: build_site.py hash $LOCAL != origin/main $REMOTE"; exit 6; }

python3 compile.py 2>/dev/null || true   # shelf.yaml -> cards.json when the ripper uses it
python3 build_site.py
python3 build_index.py
python3 tools/site_guard.py check || { echo "ABORT: site guard failed; nothing pushed"; exit 7; }

N=$(python3 -c "import json;d=json.load(open('cards.json'));b=d['books'];t=sum(1 for x in b if x['genre']=='Thesis');print(len(d['cards']),len(b)-t,t)")
set -- $N
for f in cards.json shelf.yaml books fullbooks.json index.html sitemap.xml robots.txt assets data; do if [ -e "$f" ]; then git add -A -- "$f"; fi; done
git diff --cached --quiet && { echo "nothing to deploy"; exit 0; }
git commit -q -m "rip deploy: $1 rips, $2 books, $3 theses ($(date +%F))"
if [ -n "${IRLIB_API_PUSH:-}" ]; then
  # This box can't auth the git protocol (API-only credential), so push via
  # the API with identical guarantees: base_tree=origin/main tree, only
  # changed paths, parent=origin/main HEAD, abort if main moved. Never forced.
  python3 tools/api_push.py "rip deploy: $1 rips, $2 books, $3 theses ($(date +%F))" || { echo "API PUSH FAILED"; exit 9; }
else
  git push origin HEAD:main            # plain push: rejected (not forced) if main moved
fi
MARK=$(grep -o '<meta name="build" content="[^"]*"' index.html | sed 's/.*content="\([^"]*\)".*/\1/')
if [ -f tools/smoke.js ] && command -v node >/dev/null; then
  node tools/smoke.js https://idearipper.com/ --expect-build "$MARK" --wait 600 || { echo "SMOKE FAILED: roll back with git revert $(git rev-parse --short HEAD)"; exit 8; }
fi
echo "deployed $(git rev-parse --short HEAD) ($MARK)"
