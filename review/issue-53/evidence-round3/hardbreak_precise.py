#!/usr/bin/env python3
"""Precise hard-break audit for the leading metadata blockquote (BASE vs HEAD)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from markdown_it import MarkdownIt

BASE = "34e99e0cc54cc82b6b40040286fc84673432ef76"
HEAD = "1f1234065be1f849dad2d17a91eaff986d384df5"
REPO = Path(r"C:\Users\z00587616\Documents\ConnectionAgent\_rev3-wt")

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

MD = MarkdownIt("commonmark", {"html": True})

LABEL_RE = re.compile(
    r"(文档类型|文档版本|SR 版本|状态|修订日期|创建日期|快照日期|审计日期|"
    r"功能归属|关联 SR|适用范围|全局评审范围|本文局部非目标|权威来源|权威规则|"
    r"权威范围|目标|关联|局部非目标|设计依据|上游需求|功能|所属阶段|维护规则|"
    r"范围|非目标)[：:]"
)


def show(rev: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), "show", f"{rev}:{path}"], capture_output=True, check=True
    ).stdout.decode("utf-8")


def blockquote_lines(text: str) -> list[str]:
    lines, started = [], False
    for line in text.splitlines():
        if line.startswith(">"):
            started = True
            lines.append(line)
        elif not started and line.strip() == "":
            continue
        elif started:
            break
    return lines


def analyse(lines: list[str]) -> dict:
    """Return field grouping + literal-backslash diagnostics for the block."""
    # mark every line with the break it carries
    br_after: list[bool] = []
    for idx, line in enumerate(lines):
        body = line[1:]
        if body.strip().startswith("<br"):
            br_after.append(True)
            continue
        trailing_bs = body.rstrip("\n").endswith("\\")
        trailing_sp = body.endswith("  ")
        br_after.append(trailing_bs or trailing_sp)
    # groups of labels per rendered line
    groups: list[list[str]] = []
    current: list[str] = []
    for idx, line in enumerate(lines):
        if line[1:].strip().startswith("<br"):
            groups.append(current)
            current = []
            continue
        labels = LABEL_RE.findall(line)
        current.extend(labels)
        if br_after[idx]:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    # literal trailing backslash at the very end of the block
    last = lines[-1][1:].rstrip()
    literal_trailing_bs = last.endswith("\\")
    html = MD.render("\n".join(lines))
    return {
        "groups": [g for g in groups if g],
        "literal_trailing_backslash": literal_trailing_bs,
        "html_tail": html[-160:],
        "lines": lines,
    }


def flatten(groups: list[list[str]]) -> dict[str, int]:
    """Map each label to the index of the rendered group that holds it."""
    return {label: i for i, group in enumerate(groups) for label in group}


print("=== per-file metadata hard-break audit ===")
issues = 0
for rel in CHANGED:
    base = analyse(blockquote_lines(show(BASE, rel)))
    head = analyse(blockquote_lines(show(HEAD, rel)))
    b_flat = flatten(base["groups"])
    h_flat = flatten(head["groups"])
    merged = []
    for label, h_idx in h_flat.items():
        if label not in b_flat:
            continue
        # labels sharing the head group
        same_head = [x for x, i in h_flat.items() if i == h_idx and x != label]
        b_sep = all(b_flat.get(x) != b_flat[label] for x in same_head)
        if same_head and b_sep:
            merged.append((label, same_head, h_idx))
    status = []
    if merged:
        status.append(f"REGRESSION merged={merged}")
        issues += 1
    if head["literal_trailing_backslash"]:
        status.append("LITERAL_TRAILING_BACKSLASH")
        issues += 1
    print(f"\n{rel}")
    print(f"  base groups={base['groups']}")
    print(f"  head groups={head['groups']}")
    if status:
        for s in status:
            print(f"  -> {s}")
    else:
        print("  -> structure preserved")

print(f"\ntotal flagged conditions: {issues}")
