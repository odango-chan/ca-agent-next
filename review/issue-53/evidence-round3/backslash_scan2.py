#!/usr/bin/env python3
"""Definitive literal-backslash / hard-break audit on the fixed 16-file list."""
from __future__ import annotations

import json
import subprocess

from markdown_it import MarkdownIt

BASE = "34e99e0cc54cc82b6b40040286fc84673432ef76"
HEAD = "1f1234065be1f849dad2d17a91eaff986d384df5"
REPO = r"C:\Users\z00587616\Documents\ConnectionAgent\_rev3-wt"
MD = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")

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


def show(rev: str, path: str) -> str:
    p = subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"], capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"git show failed for {rev}:{path}\n{p.stderr.decode('utf-8', 'replace')}")
    return p.stdout.decode("utf-8")


report = {}
for rel in CHANGED:
    entry = {}
    for label, rev in (("base", BASE), ("head", HEAD)):
        text = show(rev, rel)
        html = MD.render(text)
        count = html.count("\\")
        entry[label] = {
            "literal_backslash": count,
            "trailing_double_space_lines": sum(
                1 for line in text.splitlines() if line.rstrip("\n").endswith("  ") and line.strip()
            ),
            "br_tags": html.count("<br />"),
        }
    report[rel] = entry

print(json.dumps(report, ensure_ascii=False, indent=2))
print()
for rel, e in report.items():
    b, h = e["base"], e["head"]
    flags = []
    if h["literal_backslash"] > b["literal_backslash"]:
        flags.append(f"literal-backslash {b['literal_backslash']}->{h['literal_backslash']}")
    if h["trailing_double_space_lines"] > b["trailing_double_space_lines"]:
        flags.append("trailing spaces reintroduced")
    if h["br_tags"] < b["br_tags"]:
        flags.append(f"br {b['br_tags']}->{h['br_tags']}")
    print(f"{'FLAG' if flags else 'ok  '} br {b['br_tags']:>3}->{h['br_tags']:<3} "
          f"bs {b['literal_backslash']}->{h['literal_backslash']} | {rel} {flags if flags else ''}")
