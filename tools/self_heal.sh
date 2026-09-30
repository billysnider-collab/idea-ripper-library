#!/usr/bin/env bash
# Self-heal for idearipper.com (added 2026-09-30). Run by .github/workflows/site-guard.yml
# only when tools/site_guard.py fails on an automated "rip deploy" push.
# Keeps the deploy's content (cards.json, fullbooks.json, books/*.md, shelf.yaml),
# restores the guarded template files from the newest passing ancestor, rebuilds, pushes.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
BAD=$(git rev-parse HEAD)
GOOD=$(python3 tools/site_guard.py last-good) || { echo "::error::no passing ancestor to restore from"; exit 1; }
echo "restoring guarded template from $GOOD (bad push $BAD)"
GUARDED="build_site.py 404.html _config.yml"
for f in $GUARDED; do
  if git cat-file -e "$GOOD:$f" 2>/dev/null; then git show "$GOOD:$f" > "$f"; fi
done
python3 build_site.py
python3 tools/site_guard.py check
git config user.name "site-guard[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
for f in $GUARDED index.html sitemap.xml robots.txt assets data; do if [ -e "$f" ]; then git add -A -- "$f"; fi; done
if git diff --cached --quiet; then echo "nothing to heal"; echo "healed=false" >> "${GITHUB_OUTPUT:-/dev/null}"; exit 0; fi
git commit -q -m "ci: self-heal: restore guarded build_site.py from ${GOOD:0:7}" \
  -m "rip deploy ${BAD:0:7} pushed a stale build_site.py (site_guard failed). Content from the deploy is kept; only the template was restored and index.html rebuilt."
if git push origin HEAD:main; then
  echo "healed=true" >> "${GITHUB_OUTPUT:-/dev/null}"
  # pushes made with GITHUB_TOKEN may not trigger a Pages build: request one
  gh api -X POST "repos/${GITHUB_REPOSITORY}/pages/builds" >/dev/null 2>&1 || echo "::warning::could not request a Pages build"
else
  echo "::warning::heal push rejected (main moved on); the next site-guard run re-checks the new head"
fi
