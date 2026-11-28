"""#120: trusted SR-003 provenance checks use fake GitHub objects, never network."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sr003_trusted", ROOT / "scripts/verify_sr003_provenance.py")
assert spec and spec.loader
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
REPO = "odango-chan/ca-agent-next"
HEAD, BASE, TREE = "a"*40, "b"*40, "c"*40


def event(fork=False):
    return {"repository":{"full_name":REPO}, "pull_request":{
        "number":42,
        "head":{"sha":HEAD,"repo":{"full_name":"someone/fork" if fork else REPO}},
        "base":{"sha":BASE,"repo":{"full_name":REPO}}}}


def fake(path):
    if path.endswith("/pulls/42"):
        return {"head":{"sha":HEAD,"repo":{"full_name":REPO}},"base":{"sha":BASE}}
    if path.endswith("/git/commits/"+HEAD):
        return {"sha":HEAD, "tree":{"sha":TREE}}
    if path.endswith("/git/trees/"+TREE):
        return {"sha":TREE}
    raise AssertionError(path)


class TrustedSR003ProvenanceTests(unittest.TestCase):
    def test_valid_immutable_head_and_tree(self):
        self.assertEqual(v.attest("pull_request_target", event(), REPO, fake)["tree_sha"], TREE)

    def test_fork_rejected_without_reading_code(self):
        with self.assertRaisesRegex(ValueError, "FORK_NOT_QUALIFIED"):
            v.attest("pull_request_target", event(True), REPO, lambda _: self.fail("unsafe call"))

    def test_merge_queue_fails_closed_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"event.json"
            p.write_text(json.dumps({"repository":{"full_name":REPO},"merge_group":{"head_sha":HEAD}}))
            out=Path(d)/"diag.json"
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME":"merge_group","GITHUB_REPOSITORY":REPO}):
                code=v.main(["--event-path",str(p),"--out",str(out)])
            self.assertEqual(code,1)
            obj=json.loads(out.read_text())
            self.assertEqual(obj["status"],"FAIL_CLOSED")
            self.assertIn("MERGE_GROUP_NOT_QUALIFIED",obj["reason"])

    def test_untrusted_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_EVENT"):
            v.attest("pull_request", event(), REPO, fake)

    def test_changed_pr_head_rejected(self):
        def changed(path):
            val=fake(path)
            if path.endswith("/pulls/42"):
                val["head"]["sha"]="d"*40
            return val
        with self.assertRaisesRegex(ValueError, "PR_HEAD_DRIFT"):
            v.attest("pull_request_target",event(),REPO,changed)

    def test_changed_pr_base_rejected(self):
        def changed(path):
            val=fake(path)
            if path.endswith("/pulls/42"):
                val["base"]["sha"]="d"*40
            return val
        with self.assertRaisesRegex(ValueError, "PR_BASE_DRIFT"):
            v.attest("pull_request_target",event(),REPO,changed)

    def test_wrong_git_tree_rejected(self):
        def changed(path):
            val=fake(path)
            if path.endswith("/git/trees/"+TREE):
                val["sha"]="d"*40
            return val
        with self.assertRaisesRegex(ValueError, "TREE_MISMATCH"):
            v.attest("pull_request_target",event(),REPO,changed)

    def test_repository_injection_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_REPOSITORY"):
            v.attest("pull_request_target",event(),"repo/example;rm -rf",fake)
