import json
import re
import subprocess

repo = r"C:\Users\z00587616\Documents\ConnectionAgent\_rev3-wt"
HEAD = "1f1234065be1f849dad2d17a91eaff986d384df5"

files = subprocess.run(
    ["git", "-C", repo, "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", HEAD, "docs/SR"],
    capture_output=True,
).stdout.decode("utf-8").splitlines()

rows = []
for path in sorted(files):
    if not path.endswith(".md"):
        continue
    text = subprocess.run(
        ["git", "-C", repo, "show", f"{HEAD}:{path}"], capture_output=True
    ).stdout.decode("utf-8")
    head = text.splitlines()[:20]
    status = version = None
    for line in head:
        m = re.match(r">\s*状态[：:]\s*(\S+)", line)
        if m and status is None:
            status = m.group(1)
        m = re.match(r">\s*SR 版本[：:]\s*([0-9A-Za-z.\-]+)", line)
        if m and version is None:
            version = m.group(1).rstrip("\\")
    rows.append((path.split("/")[-1], version, status))

counts = {}
for _, _, s in rows:
    counts[s] = counts.get(s, 0) + 1
print(f"SR files: {len(rows)}")
print("status counts:", json.dumps(counts, ensure_ascii=False))
for name, ver, st in rows:
    print(f"  {st!s:12} {ver!s:10} {name}")
