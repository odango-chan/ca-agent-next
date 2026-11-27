#!/usr/bin/env python3
"""Third-round independent static validation for PR #54 (read-only).

Reads files exclusively from the fixed git objects BASE and HEAD via
``git show`` so the working tree cannot influence the result.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

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


def git_show(rev: str, path: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{rev}:{path}"],
        capture_output=True,
        check=True,
    )
    return out.stdout.decode("utf-8")


def git_ls(rev: str) -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", rev],
        capture_output=True,
        check=True,
    )
    return {line for line in out.stdout.decode("utf-8").splitlines() if line}


def make_md() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")


# ---------------------------------------------------------------- slug helper
def github_slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\- ]", "", text)
    text = text.replace(" ", "-")
    return text


def heading_slugs(text: str) -> list[str]:
    md = make_md()
    tokens = md.parse(text)
    slugs: list[str] = []
    seen: dict[str, int] = {}
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            inline = tokens[i + 1]
            base = github_slug(inline.content)
            n = seen.get(base, 0)
            slugs.append(base if n == 0 else f"{base}-{n}")
            seen[base] = n + 1
    return slugs


# ---------------------------------------------------------------- header block
def leading_blockquote(text: str) -> list[str]:
    lines = text.splitlines()
    block: list[str] = []
    started = False
    for line in lines:
        if line.startswith(">"):
            started = True
            block.append(line)
        elif line.strip() == "" and not started:
            continue
        elif started:
            break
    return block


def render_block(lines: list[str]) -> str:
    md = make_md()
    return md.render("\n".join(lines))


def hard_break_profile(html: str) -> dict:
    return {
        "br_tags": len(re.findall(r"<br\s*/?>", html)),
        "soft_newlines": html.count("\n") - 1 if html else 0,
        "html": html,
    }


# ---------------------------------------------------------------- main checks
def main() -> int:
    md = make_md()
    head_files = git_ls(HEAD)
    results: dict = {"base": BASE, "head": HEAD, "files": {}}
    totals = {
        "parse_errors": 0,
        "table_errors": 0,
        "links_total": 0,
        "links_local": 0,
        "links_anchor": 0,
        "missing_paths": [],
        "missing_anchors": [],
        "hard_break_regressions": [],
        "metadata_mismatches": [],
        "trailing_space_lines": 0,
    }

    slug_cache: dict[str, set[str]] = {}

    def slugs_for(path: str) -> set[str]:
        if path not in slug_cache:
            try:
                text = git_show(HEAD, path)
            except subprocess.CalledProcessError:
                slug_cache[path] = set()
            else:
                slug_cache[path] = set(heading_slugs(text))
        return slug_cache[path]

    for rel in CHANGED:
        head_text = git_show(HEAD, rel)
        base_text = git_show(BASE, rel)
        info: dict = {}

        # 1. markdown-it parse
        try:
            tokens = md.parse(head_text)
            info["parse_ok"] = True
            info["tokens"] = len(tokens)
        except Exception as exc:  # noqa: BLE001
            info["parse_ok"] = False
            info["parse_error"] = str(exc)
            totals["parse_errors"] += 1

        # fence balance
        info["fence_markers"] = sum(1 for line in head_text.splitlines() if line.strip().startswith("```"))
        info["fence_balanced"] = info["fence_markers"] % 2 == 0

        # 2. table column consistency
        table_errors = []
        table_count = 0
        i = 0
        while i < len(tokens):
            if tokens[i].type == "table_open":
                table_count += 1
                expected = None
                j = i + 1
                row_idx = 0
                while j < len(tokens) and tokens[j].type != "table_close":
                    if tokens[j].type in {"tr_open"}:
                        pass
                    if tokens[j].type == "inline":
                        pass
                    j += 1
                # structural check via line scan of the raw block is easier below
            i += 1
        # raw line scan: header row pipes vs separator pipes
        lines = head_text.splitlines()
        for idx, line in enumerate(lines):
            if re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$", line):
                sep_cols = len([c for c in line.strip().strip("|").split("|")])
                head_row = lines[idx - 1]
                if not head_row.lstrip().startswith("|"):
                    continue
                hdr_cols = len(head_row.strip().strip("|").split("|"))
                if hdr_cols != sep_cols:
                    table_errors.append({"line": idx, "header": hdr_cols, "separator": sep_cols})
        info["tables"] = table_count
        info["table_errors"] = table_errors
        totals["table_errors"] += len(table_errors)

        # 3. metadata: version + last revision
        version = None
        mdv = re.search(r"^> (?:文档版本|SR 版本)[：:]\s*([0-9A-Za-z.\-]+)", head_text, re.M)
        if mdv:
            version = mdv.group(1).rstrip("\\").strip()
        rev_date = re.search(r"^> 修订日期[：:]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", head_text, re.M)
        last_rev = None
        rev_rows = re.findall(r"^\| (\d{4}-\d{2}-\d{2}) \| ([0-9A-Za-z.\-]+) \|", head_text, re.M)
        if rev_rows:
            last_rev = rev_rows[-1]
        info["header_version"] = version
        info["header_rev_date"] = rev_date.group(1) if rev_date else None
        info["last_revision"] = last_rev
        if rev_rows and version and last_rev and last_rev[1] != version:
            totals["metadata_mismatches"].append(
                {"file": rel, "header": version, "last_revision": last_rev[1], "row": last_rev}
            )

        # 4. hard-break semantics between base and head metadata block
        base_html = render_block(leading_blockquote(base_text))
        head_html = render_block(leading_blockquote(head_text))
        base_br = len(re.findall(r"<br\s*/?>", base_html))
        head_br = len(re.findall(r"<br\s*/?>", head_html))
        info["base_meta_br"] = base_br
        info["head_meta_br"] = head_br
        if head_br < base_br:
            totals["hard_break_regressions"].append({"file": rel, "base_br": base_br, "head_br": head_br})

        # 5. links
        links = re.findall(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", head_text)
        local, anchors, missing_path, missing_anchor = 0, 0, [], []
        for raw in links:
            totals["links_total"] += 1
            if raw.startswith(("http://", "https://", "mailto:")):
                continue
            if raw.startswith("#"):
                anchors += 1
                totals["links_anchor"] += 1
                frag = unquote(raw[1:])
                if frag and frag not in slugs_for(rel):
                    missing_anchor.append({"link": raw, "target": rel})
                continue
            local += 1
            totals["links_local"] += 1
            parts = urlsplit(raw)
            target = unquote(parts.path)
            base_dir = (Path(rel).parent).as_posix()
            resolved = (Path(base_dir) / target).as_posix()
            # normalise
            norm = []
            for seg in resolved.split("/"):
                if seg == "..":
                    if norm:
                        norm.pop()
                elif seg in (".", ""):
                    continue
                else:
                    norm.append(seg)
            resolved = "/".join(norm)
            if resolved not in head_files:
                missing_path.append({"link": raw, "resolved": resolved})
                continue
            if parts.fragment:
                frag = unquote(parts.fragment)
                if frag not in slugs_for(resolved):
                    missing_anchor.append({"link": raw, "resolved": resolved, "fragment": frag})
        info["links"] = len(links)
        info["links_local"] = local
        info["links_anchor"] = anchors
        info["missing_paths"] = missing_path
        info["missing_anchors"] = missing_anchor
        totals["missing_paths"].extend(missing_path)
        totals["missing_anchors"].extend(missing_anchor)

        # 6. trailing double-space hard breaks
        info["trailing_double_spaces"] = sum(
            1 for line in head_text.splitlines() if line.endswith("  ") and line.strip()
        )
        info["backslash_breaks"] = sum(
            1 for line in head_text.splitlines() if line.rstrip().endswith("\\")
        )
        info["br_tag_lines"] = sum(1 for line in head_text.splitlines() if line.strip() == "> <br />")
        totals["trailing_space_lines"] += info["trailing_double_spaces"]

        info["lines"] = len(lines)
        results["files"][rel] = info

    results["totals"] = totals
    out = Path(r"C:\Users\z00587616\Documents\ConnectionAgent\_rev3-evidence\validation-round3.json")
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"files parsed: {len(results['files'])}/{len(CHANGED)}")
    print("parse_errors:", totals["parse_errors"])
    print("table_errors:", totals["table_errors"])
    print("fence_unbalanced:", [f for f, i in results["files"].items() if not i["fence_balanced"]])
    print("links_total:", totals["links_total"], "local:", totals["links_local"], "anchor:", totals["links_anchor"])
    print("missing_paths:", len(totals["missing_paths"]))
    for m in totals["missing_paths"]:
        print("   MISSING PATH", m)
    print("missing_anchors:", len(totals["missing_anchors"]))
    for m in totals["missing_anchors"]:
        print("   MISSING ANCHOR", m)
    print("metadata_mismatches:", totals["metadata_mismatches"])
    print("hard_break_regressions:", totals["hard_break_regressions"])
    print("trailing_double_space_lines:", totals["trailing_space_lines"])
    print("\nper-file:")
    for f, i in results["files"].items():
        print(
            f"  {i['header_version']:>8} rev={i['header_rev_date']} last={i['last_revision']} "
            f"metaBR {i['base_meta_br']}->{i['head_meta_br']} links={i['links']} "
            f"bs={i['backslash_breaks']} brlines={i['br_tag_lines']} tables={i['tables']} | {f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
