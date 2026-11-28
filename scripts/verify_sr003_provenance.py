#!/usr/bin/env python3
"""#120 trusted GitHub PR HEAD provenance: read-only, default-branch execution."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen


def reject(reason: str) -> None:
    raise ValueError(reason)


def sha(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        reject("INVALID_SHA")
    return value


def attest(event_name: str, event: dict, repository: str, fetch) -> dict:
    """Fail closed on fork, merge queue, event drift and Git object mismatch."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        reject("INVALID_REPOSITORY")
    if (event.get("repository") or {}).get("full_name") != repository:
        reject("EVENT_REPOSITORY_MISMATCH")
    if event_name == "merge_group":
        reject("MERGE_GROUP_NOT_QUALIFIED")
    if event_name != "pull_request_target":
        reject("UNTRUSTED_EVENT")
    pr = event.get("pull_request") or {}
    number = pr.get("number")
    if type(number) is not int or number < 1:
        reject("INVALID_PR_NUMBER")
    head, base = pr.get("head") or {}, pr.get("base") or {}
    if (head.get("repo") or {}).get("full_name") != repository:
        reject("FORK_NOT_QUALIFIED")
    if (base.get("repo") or {}).get("full_name") != repository:
        reject("BASE_REPOSITORY_MISMATCH")
    expected, expected_base = sha(head.get("sha")), sha(base.get("sha"))
    current = fetch(f"/repos/{repository}/pulls/{number}")
    if (current.get("head") or {}).get("sha") != expected:
        reject("PR_HEAD_DRIFT")
    if (current.get("base") or {}).get("sha") != expected_base:
        reject("PR_BASE_DRIFT")
    if ((current.get("head") or {}).get("repo") or {}).get("full_name") != repository:
        reject("LIVE_FORK")
    commit = fetch(f"/repos/{repository}/git/commits/{expected}")
    if commit.get("sha") != expected:
        reject("COMMIT_MISMATCH")
    tree_sha = sha((commit.get("tree") or {}).get("sha"))
    tree = fetch(f"/repos/{repository}/git/trees/{tree_sha}")
    if tree.get("sha") != tree_sha:
        reject("TREE_MISMATCH")
    return {
        "status": "PASS", "head_sha": expected, "base_sha": expected_base,
        "tree_sha": tree_sha, "pr_number": number, "fork": False
    }


def read_github(path: str) -> dict:
    token = os.environ.get("GH_TOKEN")
    if not token:
        reject("GITHUB_TOKEN_MISSING")
    request = Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json"},
    )
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        reject("INVALID_API_RESULT")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    info = {
        "status": "FAIL_CLOSED", "event": os.environ.get("GITHUB_EVENT_NAME"),
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "trusted_run_id": os.environ.get("GITHUB_RUN_ID"),
        "trusted_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "trusted_workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF"),
    }
    result = 1
    try:
        data = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            reject("INVALID_EVENT")
        info.update(attest(info["event"], data, info["repository"], read_github))
        result = 0
    except Exception as exc:
        # Evidence must survive a malformed event, API failure, or fork.
        info["reason"] = f"{type(exc).__name__}: {exc}"
        print("TRUSTED_SHA_FAIL_CLOSED: " + info["reason"], file=sys.stderr)
    finally:
        output.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
