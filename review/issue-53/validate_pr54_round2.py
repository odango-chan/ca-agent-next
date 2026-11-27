#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Independent static validation for PR #54 second-round review (Issue #53).

Reads fixed Git objects only; never reads the local working tree.
Default snapshot:
  base 34e99e0cc54cc82b6b40040286fc84673432ef76
  head 50a1c1496525c961b2ca6b1f9daaf2fb26ab3657

Checks: markdown-it parse (16 changed files), table column consistency,
document header/last-revision version matching, all Markdown links and
GitHub-style heading anchors, `git diff --check`, Git tree statistics, and
authoritative SR status distribution.

Definitions:
  local links      = repo-relative file links (excluding http/mailto/#frag)
  same-file anchors= hrefs starting with '#'
  fragment links   = any href carrying a non-empty '#' fragment

Usage:
  python validate_pr54_round2.py [--base SHA] [--head SHA] [--json OUT]
"""
import argparse
import json
import posixpath
import re
import subprocess
import sys
import unicodedata
import urllib.parse

import markdown_it

BASE = "34e99e0cc54cc82b6b40040286fc84673432ef76"
HEAD = "50a1c1496525c961b2ca6b1f9daaf2fb26ab3657"


def git(*args, binary=False):
    p = subprocess.run(["git", "-c", "core.quotepath=false", *args],
                       capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (args, p.stderr.decode("utf-8", "replace")))
    return p.stdout if binary else p.stdout.decode("utf-8")


def repo_paths(sha):
    out = git("ls-tree", "-r", "--name-only", sha)
    return [x for x in out.splitlines() if x]


def read_blob(sha, path):
    return git("show", "%s:%s" % (sha, path))


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip().lower()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in " -" or cat[0] in ("L", "N") or cat == "Mn" or cat == "Pc":
            out.append(ch)
    s = "".join(out)
    s = re.sub(r"\s", "-", s)
    return s


def anchors_for(text):
    md = markdown_it.MarkdownIt("commonmark").enable("table").enable("strikethrough")
    toks = md.parse(text)
    seen = {}
    result = set()
    for i, t in enumerate(toks):
        if t.type == "heading_open":
            inline = toks[i + 1]
            raw = "".join(c.content for c in inline.children if c.type in ("text", "code_inline"))
            base = slugify(raw)
            n = seen.get(base, 0)
            seen[base] = n + 1
            result.add(base if n == 0 else "%s-%d" % (base, n))
    return result


LINK_RE = None


def extract_links(tokens):
    links = []
    for t in tokens:
        if t.type == "inline":
            for c in t.children or []:
                if c.type == "link_open":
                    links.append((c.attrGet("href") or "", t.map[0] + 1 if t.map else 0))
                elif c.type == "image":
                    links.append((c.attrGet("src") or "", t.map[0] + 1 if t.map else 0))
    return links


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--head", default=HEAD)
    ap.add_argument("--json", default="validation-results-round2.json")
    args = ap.parse_args()
    base, head = args.base, args.head
    md = markdown_it.MarkdownIt("commonmark").enable("table").enable("strikethrough")

    changed = [x for x in git("diff", "--name-only", base, head).splitlines() if x]
    head_paths = repo_paths(head)
    head_set = set(head_paths)

    # ---------- tree stats ----------
    rec = [x for x in git("ls-tree", "-r", "-t", "--name-only", head).splitlines() if x]
    blobs = [p for p in head_paths]
    trees = [p for p in rec if p not in head_set]
    md_files = [p for p in blobs if p.lower().endswith(".md")]

    result = {
        "base_sha": base,
        "head_sha": head,
        "changed_files": len(changed),
        "markdown_it_version": getattr(markdown_it, "__version__", "unknown"),
        "git_version": git("--version").strip(),
        "tree": {
            "tracked_blobs": len(blobs),
            "markdown": len(md_files),
            "recursive_entries": len(rec),
            "directory_trees": len(trees),
        },
        "files": {},
        "markdown_parse_errors": [],
        "table_errors": [],
        "metadata": [],
        "metadata_mismatches": [],
        "links": {"total": 0, "local": 0, "same_file_anchors": 0,
                  "fragment_links": 0, "missing_paths": [], "missing_anchors": [],
                  "external_not_run": 0},
        "diff_check": {},
    }

    all_head_text = {}
    all_anchors = {}
    for p in head_paths:
        if p.lower().endswith(".md"):
            txt = read_blob(head, p)
            all_head_text[p] = txt
            all_anchors[p] = anchors_for(txt)

    for path in changed:
        txt = read_blob(head, path)
        entry = {"file": path, "lines": txt.count("\n") + 1}
        try:
            toks = md.parse(txt)
            entry["parse"] = "OK"
        except Exception as e:  # pragma: no cover
            entry["parse"] = "ERROR: %s" % e
            result["markdown_parse_errors"].append({"file": path, "error": str(e)})
            toks = []
        # unclosed fences: markdown-it tolerates; detect odd fence count
        fences = len([t for t in toks if t.type == "fence"])
        entry["fences"] = fences
        # tables
        tcount = 0
        for i, t in enumerate(toks):
            if t.type == "table_open":
                tcount += 1
                # find first tr header and body rows until table_close
                j = i + 1
                rows = []
                while j < len(toks) and toks[j].type != "table_close":
                    if toks[j].type == "tr_open":
                        k = j + 1
                        n = 0
                        while k < len(toks) and toks[k].type != "tr_close":
                            if toks[k].type in ("th_open", "td_open"):
                                n += 1
                            k += 1
                        rows.append((n, toks[j].map[0] + 1 if toks[j].map else 0))
                    j += 1
                counts = sorted(set(r[0] for r in rows))
                if len(counts) > 1:
                    result["table_errors"].append({
                        "file": path, "table_index": tcount,
                        "column_counts": counts,
                        "rows": [{"columns": r[0], "line": r[1]} for r in rows],
                    })
        entry["tables"] = tcount
        # metadata block
        hdr = {}
        for line in txt.splitlines()[:25]:
            m = re.match(r"^>\s*(文档版本|SR 版本|文档类型|修订日期|快照日期|状态)：\s*(.*?)\s*$", line)
            if m:
                hdr.setdefault(m.group(1), m.group(2))
        # last revision row version
        vers = []
        for line in txt.splitlines():
            m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([0-9][0-9A-Za-z.\-]*)\s*\|", line)
            if m:
                vers.append((m.group(1), m.group(2)))
        entry["header_version"] = hdr.get("文档版本") or hdr.get("SR 版本")
        entry["header_date"] = hdr.get("修订日期") or hdr.get("快照日期")
        entry["last_revision"] = vers[-1] if vers else None
        result["metadata"].append(entry)
        if entry["header_version"] and entry["last_revision"] and entry["header_version"] != entry["last_revision"][1]:
            result["metadata_mismatches"].append({
                "file": path, "header": entry["header_version"],
                "last_revision": entry["last_revision"][1]})
        # links
        links = extract_links(toks)
        entry["links"] = len(links)
        result["links"]["total"] += len(links)
        for href, ln in links:
            if not href:
                continue
            if re.match(r"^(https?:|mailto:|tel:)", href):
                result["links"]["external_not_run"] += 1
                continue
            if href.startswith("#"):
                result["links"]["same_file_anchors"] += 1
                result["links"]["fragment_links"] += 1
                frag = urllib.parse.unquote(href[1:])
                if frag and frag not in all_anchors.get(path, set()):
                    result["links"]["missing_anchors"].append({"file": path, "line": ln, "href": href})
                continue
            sp = href.split("#", 1)
            target, frag = sp[0], (sp[1] if len(sp) > 1 else "")
            if not target:
                continue
            if frag:
                result["links"]["fragment_links"] += 1
            tclean = urllib.parse.unquote(target).split("?", 1)[0]
            result["links"]["local"] += 1
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), tclean))
            resolved = resolved.lstrip("./")
            if resolved.startswith(".."):
                result["links"]["missing_paths"].append({"file": path, "line": ln, "href": href, "reason": "outside repo"})
                continue
            if resolved not in head_set:
                result["links"]["missing_paths"].append({"file": path, "line": ln, "href": href, "resolved": resolved, "reason": "not found"})
                continue
            if frag and resolved.lower().endswith(".md"):
                f = urllib.parse.unquote(frag)
                if f not in all_anchors.get(resolved, set()):
                    result["links"]["missing_anchors"].append({"file": path, "line": ln, "href": href, "resolved": resolved})
        result["files"][path] = entry

    # ---------- diff --check ----------
    p = subprocess.run(["git", "diff", "--check", base, head], capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    result["diff_check"] = {
        "exit": p.returncode,
        "warnings": [l for l in out.splitlines() if l.strip()],
        "count": len([l for l in out.splitlines() if l.strip()]),
    }

    # ---------- SR stats from authoritative files ----------
    sr_files = sorted([p for p in head_paths if re.match(r"docs/SR/SR-\d+.*\.md$", p)])
    sr = {}
    for p in sr_files:
        txt = read_blob(head, p)
        m = re.search(r"^>\s*(?:SR\s*版本|文档版本)：\s*(.+)$", txt, re.M)
        s = re.search(r"^>\s*状态：\s*(.*)$", txt, re.M)
        sid = re.search(r"SR-(\d+)", posixpath.basename(p))
        sr["SR-%s" % sid.group(1)] = {
            "file": p,
            "version": (m.group(1).strip() if m else None),
            "status_raw": (s.group(1).strip() if s else None),
        }
    def norm(raw):
        if not raw:
            return None
        for k in ("VERIFIED", "READY", "IMPLEMENTED", "IN_PROGRESS", "DRAFT", "BLOCKED"):
            if raw.startswith(k) or (" " + k) in raw[:40]:
                return k
        return raw.split()[0]
    dist = {}
    for sid, v in sr.items():
        st = norm(v["status_raw"])
        v["status"] = st
        dist[st] = dist.get(st, 0) + 1
    result["sr"] = {"count": len(sr), "distribution": dist, "files": sr}

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # console summary
    print("markdown-it-py", result["markdown_it_version"])
    print("changed files", len(changed), "| parsed", len(result["files"]))
    print("tree", result["tree"])
    print("tables errors", len(result["table_errors"]))
    print("links", result["links"]["total"], "local", result["links"]["local"],
          "same-file anchors", result["links"]["same_file_anchors"],
          "fragment links", result["links"]["fragment_links"],
          "missing_paths", len(result["links"]["missing_paths"]),
          "missing_anchors", len(result["links"]["missing_anchors"]))
    print("diff-check", result["diff_check"]["count"])
    print("SR", result["sr"]["count"], result["sr"]["distribution"])
    for e in result["metadata"]:
        print("META", e["header_version"], "last", e["last_revision"], "|", e["header_date"])


if __name__ == "__main__":
    main()
