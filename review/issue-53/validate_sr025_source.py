#!/usr/bin/env python3
"""SR-025 Owner source 独立设计证据探针（Issue #53）。

只读取 ca-client-tools 固定 checkout，不构建 Publisher、不修改任何文件。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path("contracts/owner/openamsm-mas/v1alpha4")
EXPECTED_MAIN = "7bcb2614aa3615d8358df31eecefd0909e894e40"
EXPECTED_REVISION = "fc44c3a745c68443fcfb12054c7eadf0ed7cc3f7"
EXPECTED_MANIFEST_BLOB = "dff8136f7dc48b83bbc09d08ed0340f2c9a6ae72"
EXPECTED_BUILD_IDENTITY = "sha256:ac834080f31ff0fa91b9eb846fa47c889a94837fc1f37ec2034190e4e83085c0"


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    source = repo / ROOT
    errors = []
    metrics = {}

    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if head != EXPECTED_MAIN:
        errors.append(f"HEAD {head} != {EXPECTED_MAIN}")
    manifest_blob = subprocess.check_output(["git", "-C", str(repo), "rev-parse", f"HEAD:{ROOT.as_posix()}/manifest.json"], text=True).strip()
    if manifest_blob != EXPECTED_MANIFEST_BLOB:
        errors.append(f"manifest blob {manifest_blob} 不匹配")
    diff = subprocess.check_output(["git", "-C", str(repo), "diff", "--name-only", f"{EXPECTED_REVISION}..{EXPECTED_MAIN}", "--", ROOT.as_posix()], text=True).splitlines()
    if diff:
        errors.append(f"source Revision 与 main 有差异：{diff}")
    tracked = subprocess.check_output(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "HEAD", "--", ROOT.as_posix()], text=True).splitlines()
    if len(tracked) != 59:
        errors.append(f"source 文件数 {len(tracked)} != 59")
    metrics.update({"head": head, "source_revision": EXPECTED_REVISION, "source_files": len(tracked), "manifest_blob": manifest_blob, "source_revision_diff_files": len(diff)})

    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest["buildIdentity"] != EXPECTED_BUILD_IDENTITY:
        errors.append("buildIdentity 不匹配")
    artifacts = manifest["artifacts"]
    if len(artifacts) != 58:
        errors.append(f"artifact 数 {len(artifacts)} != 58")
    for path, expected in artifacts.items():
        actual = "sha256:" + hashlib.sha256((source / path).read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"artifact digest 不匹配：{path}")
    metrics["artifact_digests_verified"] = len(artifacts)

    operations = manifest["operations"]
    unpublished = manifest["notPublished"]
    operation_ids = {item["callable"] for item in operations}
    unpublished_ids = {item["callable"] for item in unpublished}
    if len(operations) != 25 or len(operation_ids) != 25:
        errors.append("published operation 数不是 25 或存在重复")
    if len(unpublished) != 7 or len(unpublished_ids) != 7:
        errors.append("notPublished 数不是 7 或存在重复")
    if operation_ids & unpublished_ids:
        errors.append("published 与 notPublished 有交集")
    metrics.update({"published_operations": len(operation_ids), "not_published": len(unpublished_ids)})

    catalog = yaml.safe_load((source / "tool-catalog.yaml").read_text(encoding="utf-8"))
    contracts = catalog["spec"]["contracts"]
    contract_ids = {item["id"] for item in contracts}
    if len(contracts) != 25 or contract_ids != operation_ids:
        errors.append("ToolCatalog contract ID 与 manifest.operations 不一致")

    capabilities = yaml.safe_load((source / "capability-contracts.yaml").read_text(encoding="utf-8"))["spec"]["capabilities"]
    capability_ids = {item["id"] for item in capabilities}
    members = [member["id"] for item in capabilities for member in item["callables"]]
    if len(capabilities) != 24 or len(capability_ids) != 24:
        errors.append("Capability ID 数不是 24 或存在重复")
    if len(members) != 25 or set(members) != operation_ids:
        errors.append("Capability 25 members 未精确覆盖公开 operations")
    metrics.update({"capability_ids": len(capability_ids), "capability_members": len(members)})

    evidence = yaml.safe_load((source / "evidence-guarantees.yaml").read_text(encoding="utf-8"))
    producer_ids = [producer["id"] for descriptor in evidence.values() for producer in descriptor["producers"]]
    if len(evidence) != 25 or set(producer_ids) != operation_ids:
        errors.append("EvidenceDescriptor/Producer 未精确覆盖 25 个公开 operations")
    if any(descriptor["authority"] != "openamsm.smf.mas" for descriptor in evidence.values()):
        errors.append("Evidence authority 不匹配")
    metrics["evidence_descriptors"] = len(evidence)

    schema_documents = {}
    for path in source.rglob("*.schema.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        schema_documents[document["$id"]] = (path, document)
    metrics["schema_files"] = len(schema_documents)
    if len(schema_documents) != 54:
        errors.append(f"Schema 文件数 {len(schema_documents)} != 54")

    roots = set()
    for key, value in walk(catalog):
        if key in {"$ref", "inputSchema", "outputSchema", "receiptSchema", "schema"} and isinstance(value, str) and value.startswith("urn:"):
            roots.add(value)
    closure = set()
    pending = list(roots)
    while pending:
        schema_id = pending.pop()
        if schema_id in closure:
            continue
        if schema_id not in schema_documents:
            errors.append(f"缺少 Schema $id：{schema_id}")
            continue
        closure.add(schema_id)
        _, document = schema_documents[schema_id]
        for key, value in walk(document):
            if key == "$ref" and isinstance(value, str) and value.startswith("urn:"):
                pending.append(value)
    if len(closure) != 53:
        errors.append(f"公开 Schema 闭包 {len(closure)} != 53")
    excluded = set(schema_documents) - closure
    if len(excluded) != 1 or not any("deployment-binding" in schema_documents[item][0].name for item in excluded):
        errors.append(f"闭包排除项异常：{sorted(excluded)}")
    metrics["public_schema_closure"] = len(closure)
    metrics["excluded_schema_ids"] = sorted(excluded)

    original_payload_paths = [source / "tool-catalog.yaml", source / "evidence-guarantees.yaml"]
    original_payload_paths += [path for schema_id in closure for path, _ in [schema_documents[schema_id]]]
    unique_payload_paths = set(original_payload_paths)
    if len(unique_payload_paths) != 55:
        errors.append(f"原始 payload 文件数 {len(unique_payload_paths)} != 55")
    payload_bytes = sum(path.stat().st_size for path in unique_payload_paths)
    if payload_bytes != 80479:
        errors.append(f"原始 payload bytes {payload_bytes} != 80479")
    metrics.update({"original_payload_files": len(unique_payload_paths), "original_payload_bytes": payload_bytes, "exports_total": 25 + 24 + 25 + len(closure), "payload_files_with_generated_capability_catalog": 56, "zip_files_with_package_json": 57})

    result = {"overall": "PASS" if not errors else "FAIL", "metrics": metrics, "errors": errors, "not_run": ["Publisher generate/verify", "Compiler BuildDevelopment/VerifyDevelopment", "ca-client-tools go test", "Studio 双根消费"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
