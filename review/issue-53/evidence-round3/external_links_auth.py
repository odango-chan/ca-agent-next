#!/usr/bin/env python3
"""Authenticated reachability check for every external URL in the 16 files.

GitHub URLs are resolved through the GitHub REST API with the `gh` CLI token so
that private repositories are distinguished from truly missing objects.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HEAD = "1f1234065be1f849dad2d17a91eaff986d384df5"
REPO = r"C:\Users\z00587616\Documents\ConnectionAgent\_rev3-wt"
OUT = Path(r"C:\Users\z00587616\Documents\ConnectionAgent\_rev3-evidence\external-links-auth.json")

CHANGED = [
    "docs/IR/IR 总登记册.md",
    "docs/SR/SR-016-工作台设计移交与条件编辑.md",
    "docs/SR/SR-025-MAS Owner Interface Package Publisher.md",
    "docs/参考与审计/跨仓依赖与可行性审计.md",
    "docs/参考与审计/跨仓设计资产迁移与一致性审计.md",
    "docs/架构设计/CA Agent Next 架构设计.md",
    "docs/架构设计/外部能力域架构总览.md",
    "docs/治理/SR 总索引.md",
    "docs/治理/功能树与需求追踪基线.md",
    "docs/治理/实施状态总览.md",
    "docs/治理/文档总目录与索引.md",
    "docs/治理/现有文档盘点与收敛计划.md",
    "docs/设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md",
    "docs/设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md",
    "docs/设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md",
    "docs/验收与实施/演示验收基线.md",
]

urls: dict[str, set[str]] = {}
for rel in CHANGED:
    text = subprocess.run(
        ["git", "-C", REPO, "show", f"{HEAD}:{rel}"], capture_output=True, check=True
    ).stdout.decode("utf-8")
    for raw in re.findall(r"\]\((https?://[^)\s]+)\)", text):
        urls.setdefault(raw, set()).add(rel)
    for raw in re.findall(r"(?<![(\[<])(https?://[^\s)\]>\"'`]+[^\s)\]>\"'`.,;：。])", text):
        urls.setdefault(raw, set()).add(rel)


def gh(path: str) -> tuple[int, str]:
    p = subprocess.run(["gh", "api", path], capture_output=True)
    if p.returncode == 0:
        return 200, ""
    err = p.stderr.decode("utf-8", "replace")
    m = re.search(r"HTTP (\d{3})", err)
    return (int(m.group(1)) if m else 0), err.strip().splitlines()[0] if err.strip() else ""


def probe(url: str) -> tuple[str, object]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.netloc == "github.com":
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            return url, "SKIP:not-repo"
        owner, repo = parts[0], parts[1]
        rest = parts[2:]
        if not rest:
            status, _ = gh(f"repos/{owner}/{repo}")
            return url, status
        kind = rest[0]
        if kind == "pull" and len(rest) >= 2:
            status, _ = gh(f"repos/{owner}/{repo}/pulls/{rest[1]}")
        elif kind == "issues" and len(rest) >= 2:
            status, _ = gh(f"repos/{owner}/{repo}/issues/{rest[1]}")
        elif kind == "commit" and len(rest) >= 2:
            status, _ = gh(f"repos/{owner}/{repo}/commits/{rest[1]}")
        elif kind == "tree" and len(rest) >= 2:
            ref = rest[1]
            sub = "/".join(rest[2:])
            if sub:
                status, _ = gh(
                    f"repos/{owner}/{repo}/contents/{urllib.parse.quote(sub)}?ref={ref}"
                )
            else:
                status, _ = gh(f"repos/{owner}/{repo}/git/trees/{ref}")
        elif kind == "blob" and len(rest) >= 3:
            ref = rest[1]
            sub = "/".join(rest[2:])
            status, _ = gh(f"repos/{owner}/{repo}/contents/{urllib.parse.quote(sub)}?ref={ref}")
        elif kind == "releases" and len(rest) >= 3 and rest[1] == "tag":
            status, _ = gh(f"repos/{owner}/{repo}/releases/tags/{rest[2]}")
        elif kind == "actions" and len(rest) >= 3 and rest[1] == "runs":
            status, _ = gh(f"repos/{owner}/{repo}/actions/runs/{rest[2]}")
        else:
            status, _ = gh(f"repos/{owner}/{repo}")
        return url, status
    req = urllib.request.Request(url, headers={"User-Agent": "dsh-review-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return url, resp.status
    except urllib.error.HTTPError as exc:
        return url, exc.code
    except Exception as exc:  # noqa: BLE001
        return url, f"ERR:{type(exc).__name__}"


results: dict[str, object] = {}
with ThreadPoolExecutor(max_workers=4) as pool:
    for url, status in pool.map(probe, sorted(urls)):
        results[url] = status

OUT.write_text(
    json.dumps(
        {"head": HEAD, "total": len(urls), "results": results,
         "sources": {u: sorted(s) for u, s in urls.items()}},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

ok = (200, 301, 302, 304, 307, 308)
bad = {u: s for u, s in results.items() if s not in ok}
print(f"unique URLs: {len(urls)}; resolved OK: {len(results) - len(bad)}; flagged: {len(bad)}")
for u, s in sorted(bad.items(), key=lambda kv: str(kv[1])):
    print(f"  [{s}] {u}")
    for src in sorted(urls[u]):
        print(f"        in {src}")
