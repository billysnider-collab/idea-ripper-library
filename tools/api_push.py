#!/usr/bin/env python3
"""API push for idea-ripper-library with the same safety as `git push`.

Replaces `git push origin HEAD:main` on boxes where the git protocol can't
authenticate (the custom.github credential is API-only). Guarantees, per
Billy's 2026-09-30 deploy spec:
  - base_tree = origin/main's tree, only changed paths (never full-tree)
  - parent = origin/main HEAD
  - aborts if origin/main moved since we based (non-forcing semantics)
  - explicit author/committer "Chief" (traceable bot pushes)

Usage:
  python3 tools/api_push.py "<commit message>" [path ...]
  With no paths: pushes the diff between origin/main and local HEAD
  (the safe-deploy.sh flow, after its local `git commit`).
  With paths: pushes exactly those working-tree files (one-off surgical use).

Must run from the repo working copy. Exits nonzero on any failure.
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import http.client
import socket
import time
import urllib.error

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import dynamic_credential_entry  # noqa: E402

REPO = "billysnider-collab/idea-ripper-library"
API = "https://api.github.com"
AUTHOR_NAME = "Chief"
FALLBACK_EMAIL = "billysnider@gmail.com"


def sh(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        print("git failed: %s\n%s" % (" ".join(args), r.stderr), file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


def api(method, path, body=None):
    entry = dynamic_credential_entry("custom.github")
    surrogate = entry["surrogate"].strip()
    data = None
    headers = {"Authorization": "Bearer %s" % surrogate,
               "Accept": "application/vnd.github+json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=headers,
                                 method=method)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            print("API %s %s failed: %s\n%s" % (method, path, e,
                                                e.read().decode()[:500]),
                  file=sys.stderr)
            sys.exit(1)
        except (http.client.RemoteDisconnected, http.client.IncompleteRead,
                ConnectionResetError, TimeoutError, socket.timeout) as e:
            time.sleep(2 * (attempt + 1))
    print("API %s %s failed after retries" % (method, path), file=sys.stderr)
    sys.exit(1)


def resolve_email():
    try:
        emails = api("GET", "/user/emails")
        for e in emails:
            if e.get("primary") and e.get("verified"):
                return e["email"]
    except SystemExit:
        raise
    except Exception as e:
        print("email lookup failed (%s); using fallback" % e)
    return FALLBACK_EMAIL


def main():
    if len(sys.argv) < 2:
        print("usage: api_push.py \"<message>\" [path ...]", file=sys.stderr)
        sys.exit(2)
    message = sys.argv[1]
    os.chdir(sh("git", "rev-parse", "--show-toplevel"))

    base = sh("git", "rev-parse", "origin/main")
    base_tree = sh("git", "rev-parse", base + "^{tree}")

    if len(sys.argv) > 2:
        files = sys.argv[2:]
        deleted = []
    else:
        out = sh("git", "diff", "--name-status", base, "HEAD")
        files, deleted = [], []
        for line in out.splitlines():
            parts = line.split("\t")
            status = parts[0]
            if status.startswith("R"):
                # rename: old path deleted, new path added
                deleted.append(parts[1]); files.append(parts[2])
            else:
                (deleted if status.startswith("D") else files).append(parts[1])

    entries = []
    for path in files:
        with open(path, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        blob = api("POST", "/repos/%s/git/blobs" % REPO,
                   {"content": content, "encoding": "base64"})
        entries.append({"path": path, "mode": "100644",
                        "type": "blob", "sha": blob["sha"]})
    for path in deleted:
        entries.append({"path": path, "mode": "100644",
                        "type": "blob", "sha": None})
    if not entries:
        print("api_push: no changes vs origin/main; nothing to push")
        return

    tree = api("POST", "/repos/%s/git/trees" % REPO,
               {"base_tree": base_tree, "tree": entries})
    email = resolve_email()
    ident = {"name": AUTHOR_NAME, "email": email}
    commit = api("POST", "/repos/%s/git/commits" % REPO,
                 {"message": message, "tree": tree["sha"],
                  "parents": [base], "author": ident, "committer": ident})

    # non-forcing semantics: refuse if origin/main moved under us
    ref = api("GET", "/repos/%s/git/refs/heads/main" % REPO)
    if ref["object"]["sha"] != base:
        print("ABORT: origin/main moved (%s != %s); not forcing"
              % (ref["object"]["sha"][:8], base[:8]), file=sys.stderr)
        sys.exit(3)
    api("PATCH", "/repos/%s/git/refs/heads/main" % REPO,
        {"sha": commit["sha"]})
    print("PUSHED %s -> origin/main (%d files, %d deletions)"
          % (commit["sha"][:8], len(files), len(deleted)))
    print("SHA: %s" % commit["sha"])

    # Realign the local clone with the server-created commit object (it has a
    # different SHA than any local commit). Without this, the next
    # `git pull --ff-only` would fail on the diverged local commit.
    # Safe: only tracked files are reset, and only when the tracked tree is
    # clean (the deploy flow commits everything before pushing).
    sh("git", "fetch", "--quiet", "origin", "main")
    tracked_dirty = subprocess.run(
        ["git", "diff", "--quiet"], capture_output=True).returncode != 0
    staged_dirty = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], capture_output=True).returncode != 0
    if tracked_dirty or staged_dirty:
        print("warning: working tree has uncommitted tracked changes; "
              "leaving local HEAD as-is (run `git reset --hard origin/main` "
              "manually once they are safe)", file=sys.stderr)
    else:
        sh("git", "reset", "--hard", "--quiet", "origin/main")
        print("local HEAD realigned to origin/main")


if __name__ == "__main__":
    main()
