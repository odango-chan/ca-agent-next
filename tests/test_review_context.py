"""SR-001：PR 评审上下文生成器自动化验收测试。

覆盖 AC-REV-01～AC-REV-09（含 Base 严格 Schema 与规范化头部声明反例）：

* AC-REV-01 正常解析
* AC-REV-02 标记校验
* AC-REV-03 YAML/Schema 严格校验
* AC-REV-04 ID 冲突及语义冲突检测
* AC-REV-05 评审上下文生成
* AC-REV-06 完整统一评审提示词生成
* AC-REV-07 真实 PR SHA 和变更文件
* AC-REV-08 正式文档头部继承检查
* AC-REV-09 范围变更提示

测试使用临时 Git 仓库和临时提交构造 Fixture。Fixture 一律从本 checkout 的
根目录 ``Agent.md`` 派生，不在测试中维护第二份项目级 review_scope。

AC-REV-10（真实 PR Workflow Artifact 交付）只能由真实 GitHub Workflow Run
验收，不在本文件内模拟。
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "review_context.py"

_spec = importlib.util.spec_from_file_location("sr001_review_context", SCRIPT_PATH)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)  # type: ignore[union-attr]

AGENT_MD_TEXT = (REPO_ROOT / "Agent.md").read_text(encoding="utf-8")
BASELINE_BLOCK = rc.extract_scope_block(AGENT_MD_TEXT, "Agent.md")

AGENT_MD_PATH = "Agent.md"
IN_SCOPE_ANCHOR = "  always_required:"
ALWAYS_REQUIRED_ANCHOR = "  non_goals:"
NON_GOALS_ANCHOR = "  review_policy:"


# --------------------------------------------------------------------------
# Fixture 构造
# --------------------------------------------------------------------------


def agent_doc(block: str = BASELINE_BLOCK, before: str = "", after: str = "") -> str:
    """用给定 review_scope YAML 构造 Agent.md 文本。"""

    return (
        "# 仓库协作指引\n\n"
        "评审范围见下方机器可读区块。\n\n"
        f"{before}"
        f"{rc.BEGIN_MARKER}\n"
        "~~~yaml\n"
        f"{block}"
        "~~~\n"
        f"{rc.END_MARKER}\n"
        f"{after}"
    )


def scope_entry(entry_id: str, description: str) -> str:
    return f"    - id: {entry_id}\n      description: {description}\n"


def insert_in_scope(block: str, entry_id: str, description: str) -> str:
    return block.replace(
        IN_SCOPE_ANCHOR, scope_entry(entry_id, description) + IN_SCOPE_ANCHOR, 1
    )


def insert_always_required(block: str, entry_id: str, description: str) -> str:
    return block.replace(
        ALWAYS_REQUIRED_ANCHOR,
        scope_entry(entry_id, description) + ALWAYS_REQUIRED_ANCHOR,
        1,
    )


def insert_non_goals(block: str, entry_id: str, description: str) -> str:
    return block.replace(
        NON_GOALS_ANCHOR, scope_entry(entry_id, description) + NON_GOALS_ANCHOR, 1
    )


class TempRepo:
    """临时 Git 仓库，用于构造真实提交与变更文件。"""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="sr001-repo-")
        self.path = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "SR-001 Tests")
        self.git("config", "user.email", "sr001-tests@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    def close(self) -> None:
        self._tmp.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        command = [
            "git",
            "-c",
            "core.quotepath=false",
            "-C",
            str(self.path),
            *args,
        ]
        proc = subprocess.run(command, capture_output=True, check=False)
        if check and proc.returncode != 0:
            raise AssertionError(
                f"git {' '.join(args)} 失败："
                f"{proc.stderr.decode('utf-8', errors='replace')}"
            )
        return proc

    def write(self, relpath: str, text: str) -> None:
        target = self.path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    def remove(self, relpath: str) -> None:
        (self.path / relpath).unlink()

    def move(self, source: str, target: str) -> None:
        self.git("mv", source, target)

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.decode("utf-8").strip()

    def rev(self, ref: str) -> str:
        return self.git("rev-parse", ref).stdout.decode("utf-8").strip()


def invoke(
    repo: TempRepo,
    base: str,
    head: str,
    out: Path,
    *extra: str,
) -> tuple[int, str, str]:
    """在进程内调用 CLI，返回 (退出码, stdout, stderr)。"""

    argv = [
        "--repo",
        str(repo.path),
        "--base",
        base,
        "--head",
        head,
        "--out",
        str(out),
        *extra,
    ]
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = rc.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class RepoTestBase(unittest.TestCase):
    """提供临时仓库与两个提交的公共基线。"""

    def setUp(self) -> None:
        os.environ.pop("GITHUB_EVENT_PATH", None)
        self.repo = TempRepo()
        self.addCleanup(self.repo.close)
        self.repo.write(AGENT_MD_PATH, agent_doc())
        self.repo.write("README.md", "# test\n")
        self.base = self.repo.commit("base")
        self.out = self.repo.path / "out"

    def checkout_branch(self, name: str) -> None:
        self.repo.git("checkout", "-q", "-b", name)

    def read_artifact(self, name: str) -> str:
        return (self.out / name).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# AC-REV-01 正常解析
# --------------------------------------------------------------------------


class TestACREV01NormalParsing(RepoTestBase):
    def test_parse_baseline_agent_md(self) -> None:
        scope = rc.parse_agent_md(AGENT_MD_TEXT, "Agent.md")

        self.assertEqual(scope["schema_version"], 1)
        self.assertEqual(scope["profile"], "demo_prototype")
        self.assertIn("generic_agent_core", [item["id"] for item in scope["in_scope"]])
        self.assertIn("basic_validation", [item["id"] for item in scope["always_required"]])
        self.assertIn("production_ha_dr", [item["id"] for item in scope["non_goals"]])
        self.assertEqual(list(scope["finding_classes"]), list(rc.FINDING_CLASSES))

    def test_json_matches_parsed_yaml_values(self) -> None:
        raw = yaml.safe_load(BASELINE_BLOCK)["review_scope"]
        code, stdout, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        self.assertIn("校验通过", stdout)

        generated = json.loads(self.read_artifact(rc.SCOPE_JSON_NAME))
        self.assertEqual(generated, raw)
        self.assertEqual(generated["target"]["description"], raw["target"]["description"])

    def test_generates_exactly_three_artifacts(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        self.assertEqual(
            sorted(path.name for path in self.out.iterdir()),
            sorted([rc.SCOPE_JSON_NAME, rc.CONTEXT_NAME, rc.PROMPT_NAME]),
        )


# --------------------------------------------------------------------------
# AC-REV-02 标记校验
# --------------------------------------------------------------------------


class TestACREV02Markers(unittest.TestCase):
    def assert_invalid(self, text: str, fragment: str) -> None:
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(text, "Agent.md")
        self.assertIn(fragment, str(captured.exception))

    def test_missing_begin_marker(self) -> None:
        text = agent_doc().replace(rc.BEGIN_MARKER + "\n", "", 1)
        self.assert_invalid(text, "缺少 REVIEW_SCOPE:BEGIN 标记")

    def test_missing_end_marker(self) -> None:
        text = agent_doc().replace(rc.END_MARKER + "\n", "", 1)
        self.assert_invalid(text, "缺少 REVIEW_SCOPE:END 标记")

    def test_duplicate_begin_marker(self) -> None:
        text = agent_doc(before=rc.BEGIN_MARKER + "\n")
        self.assert_invalid(text, "REVIEW_SCOPE:BEGIN 标记重复出现")

    def test_duplicate_end_marker(self) -> None:
        text = agent_doc(after=rc.END_MARKER + "\n")
        self.assert_invalid(text, "REVIEW_SCOPE:END 标记重复出现")

    def test_reversed_markers(self) -> None:
        text = (
            "# 仓库协作指引\n\n"
            f"{rc.END_MARKER}\n"
            "~~~yaml\n"
            f"{BASELINE_BLOCK}"
            "~~~\n"
            f"{rc.BEGIN_MARKER}\n"
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(text, "Agent.md")
        self.assertIn("标记顺序错误", str(captured.exception))

    def test_missing_yaml_fence(self) -> None:
        text = (
            "# 仓库协作指引\n\n"
            f"{rc.BEGIN_MARKER}\n"
            f"{BASELINE_BLOCK}"
            f"{rc.END_MARKER}\n"
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(text, "Agent.md")
        self.assertIn("YAML 围栏", str(captured.exception))

    def test_two_fences(self) -> None:
        text = (
            "# 仓库协作指引\n\n"
            f"{rc.BEGIN_MARKER}\n"
            "~~~yaml\n"
            f"{BASELINE_BLOCK}"
            "~~~\n"
            "~~~yaml\n"
            "review_scope: {}\n"
            "~~~\n"
            f"{rc.END_MARKER}\n"
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(text, "Agent.md")
        self.assertIn("REVIEW_SCOPE 区块内只允许唯一 YAML 围栏", str(captured.exception))

    def test_free_text_before_fence(self) -> None:
        text = (
            "# 仓库协作指引\n\n"
            f"{rc.BEGIN_MARKER}\n"
            "评审范围见下文。\n"
            "~~~yaml\n"
            f"{BASELINE_BLOCK}"
            "~~~\n"
            f"{rc.END_MARKER}\n"
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(text, "Agent.md")
        self.assertIn("不得从自由文本推断评审范围", str(captured.exception))

    def test_content_after_fence(self) -> None:
        text = (
            "# 仓库协作指引\n\n"
            f"{rc.BEGIN_MARKER}\n"
            "~~~yaml\n"
            f"{BASELINE_BLOCK}"
            "~~~\n"
            "区块内围栏之后的自由文本\n"
            f"{rc.END_MARKER}\n"
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(text, "Agent.md")
        self.assertIn("REVIEW_SCOPE 区块内只允许唯一 YAML 围栏", str(captured.exception))

    def test_cli_rejects_missing_marker(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        repo.write(AGENT_MD_PATH, agent_doc().replace(rc.END_MARKER + "\n", "", 1))
        base = repo.commit("base")
        code, _, stderr = invoke(repo, base, base, repo.path / "out")
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("REVIEW_SCOPE:END", stderr)


# --------------------------------------------------------------------------
# AC-REV-03 YAML/Schema 严格校验
# --------------------------------------------------------------------------


class TestACREV03StrictSchema(RepoTestBase):
    def assert_rejected(self, block: str, fragment: str) -> None:
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn(fragment, str(captured.exception))

    def test_yaml_syntax_error(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  profile: demo_prototype\n",
            "  profile: demo_prototype\n   bad_indent: [unclosed\n",
            1,
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("YAML 解析失败", str(captured.exception))

    def test_duplicate_mapping_key(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  schema_version: 1\n",
            "  schema_version: 1\n  schema_version: 1\n",
            1,
        )
        self.assert_rejected(block, "重复的 mapping key")

    def test_non_text_mapping_key(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  schema_version: 1\n", "  1: schema_version\n", 1
        )
        self.assert_rejected(block, "mapping key 必须为文本")

    def test_merge_key_rejected(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  schema_version: 1\n", "  <<: {a: 1}\n  schema_version: 1\n", 1
        )
        self.assert_rejected(block, "不允许 YAML merge key")

    def test_unknown_top_level_field(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  schema_version: 1\n", "  schema_version: 1\n  extra_top: 1\n", 1
        )
        self.assert_rejected(block, "review_scope: 未知字段 'extra_top'")

    def test_unknown_target_field(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  target:\n", "  target:\n    note: 额外字段\n", 1
        )
        self.assert_rejected(block, "review_scope.target: 未知字段 'note'")

    def test_unknown_entry_field(self) -> None:
        block = insert_in_scope(BASELINE_BLOCK, "with_extra", "带额外字段的条目。").replace(
            "      description: 带额外字段的条目。\n",
            "      description: 带额外字段的条目。\n      note: 额外\n",
            1,
        )
        self.assert_rejected(block, "review_scope.in_scope[9]: 未知字段 'note'")

    def test_unknown_review_policy_field(self) -> None:
        block = BASELINE_BLOCK.replace(
            "    default_review_target:",
            "    extra_policy: true\n    default_review_target:",
            1,
        )
        self.assert_rejected(block, "review_scope.review_policy: 未知字段 'extra_policy'")

    def test_missing_required_field(self) -> None:
        block = BASELINE_BLOCK.replace("  profile: demo_prototype\n", "", 1)
        self.assert_rejected(block, "review_scope: 缺少必填字段 'profile'")

    def test_wrong_type_text(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  profile: demo_prototype\n", "  profile: [demo_prototype]\n", 1
        )
        self.assert_rejected(block, "review_scope.profile: 必须为文本")

    def test_wrong_type_entry_description(self) -> None:
        block = insert_in_scope(BASELINE_BLOCK, "bad_description", "123")
        block = block.replace(
            "      description: 123\n", "      description: 123\n", 1
        )
        # 去掉引号使 123 解析为整数
        self.assert_rejected(block, "review_scope.in_scope[9].description")

    def test_bool_as_integer(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  schema_version: 1\n", "  schema_version: true\n", 1
        )
        self.assert_rejected(block, "不得把 bool 当作整数")

    def test_unknown_schema_version(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  schema_version: 1\n", "  schema_version: 2\n", 1
        )
        self.assert_rejected(block, "不支持的 schema_version 2")

    def test_unknown_profile_enum(self) -> None:
        block = BASELINE_BLOCK.replace(
            "  profile: demo_prototype\n", "  profile: production\n", 1
        )
        self.assert_rejected(block, "未知 profile 'production'")

    def test_unknown_review_policy_enum(self) -> None:
        block = BASELINE_BLOCK.replace(
            "    default_review_target: changed_files_and_direct_dependencies",
            "    default_review_target: everything",
            1,
        )
        self.assert_rejected(block, "未知枚举 'everything'")

    def test_review_policy_bool_field_rejects_int(self) -> None:
        block = BASELINE_BLOCK.replace(
            "    blocker_requires_traceable_requirement: true",
            "    blocker_requires_traceable_requirement: 1",
            1,
        )
        self.assert_rejected(block, "必须为 bool")

    def test_unknown_finding_class(self) -> None:
        block = BASELINE_BLOCK.replace(
            "    - BLOCKER\n", "    - BLOCKER\n    - MAYBE\n", 1
        )
        self.assert_rejected(block, "未知分类 'MAYBE'")

    def test_duplicate_finding_class(self) -> None:
        block = BASELINE_BLOCK.replace(
            "    - BLOCKER\n", "    - BLOCKER\n    - BLOCKER\n", 1
        )
        self.assert_rejected(block, "重复的分类 'BLOCKER'")

    def test_missing_required_finding_class(self) -> None:
        block = BASELINE_BLOCK.replace("    - OUT_OF_SCOPE\n", "", 1)
        self.assert_rejected(block, "必须是治理规范 §11.3 的完整六种分类，缺少 OUT_OF_SCOPE")

    def test_missing_blocker_class(self) -> None:
        block = BASELINE_BLOCK.replace("    - BLOCKER\n", "", 1)
        self.assert_rejected(block, "缺少 BLOCKER")

    def test_missing_non_blocking_class(self) -> None:
        block = BASELINE_BLOCK.replace("    - NON_BLOCKING\n", "", 1)
        self.assert_rejected(block, "缺少 NON_BLOCKING")

    def test_empty_in_scope(self) -> None:
        start = BASELINE_BLOCK.index("  in_scope:\n")
        end = BASELINE_BLOCK.index("  always_required:\n")
        block = BASELINE_BLOCK[:start] + "  in_scope: []\n" + BASELINE_BLOCK[end:]
        self.assert_rejected(block, "空范围不得解释为没有限制")

    def test_empty_always_required(self) -> None:
        start = BASELINE_BLOCK.index("  always_required:\n")
        end = BASELINE_BLOCK.index("  non_goals:\n")
        block = BASELINE_BLOCK[:start] + "  always_required: []\n" + BASELINE_BLOCK[end:]
        self.assert_rejected(block, "空范围不得解释为没有限制")

    def test_extra_top_level_key_in_block(self) -> None:
        block = BASELINE_BLOCK + "\nother_root: 1\n"
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("只允许唯一的 review_scope 顶层键", str(captured.exception))

    def test_cli_reports_validation_failure(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        repo.write(
            AGENT_MD_PATH,
            agent_doc(BASELINE_BLOCK.replace("  profile: demo_prototype\n", "", 1)),
        )
        base = repo.commit("base")
        code, _, stderr = invoke(repo, base, base, repo.path / "out")
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("缺少必填字段 'profile'", stderr)


# --------------------------------------------------------------------------
# AC-REV-04 ID 冲突及语义冲突检测
# --------------------------------------------------------------------------


class TestACREV04Conflicts(RepoTestBase):
    def test_duplicate_id_within_group(self) -> None:
        block = insert_in_scope(BASELINE_BLOCK, "generic_agent_core", "重复 ID 的条目。")
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("重复的 ID 'generic_agent_core'", str(captured.exception))

    def test_id_between_in_scope_and_non_goals(self) -> None:
        block = insert_non_goals(BASELINE_BLOCK, "generic_agent_core", "同时出现在非目标。")
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("同时出现在 in_scope 与 non_goals", str(captured.exception))

    def test_id_between_in_scope_and_always_required(self) -> None:
        block = insert_always_required(
            BASELINE_BLOCK, "generic_agent_core", "跨列表重复 ID。"
        )
        with self.assertRaises(rc.ValidationError) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("跨列表重复出现", str(captured.exception))

    def test_semantic_conflict_identical_description(self) -> None:
        block = insert_in_scope(
            BASELINE_BLOCK,
            "ha_in_scope",
            "生产级 HA、跨区域容灾、自动故障转移和灾难恢复",
        )
        with self.assertRaises(rc.ScopeDecisionRequired) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("SCOPE_DECISION_REQUIRED", str(captured.exception))
        self.assertIn("ha_in_scope", str(captured.exception))
        self.assertIn("production_ha_dr", str(captured.exception))

    def test_semantic_conflict_contained_description(self) -> None:
        block = insert_in_scope(
            BASELINE_BLOCK, "ha_subset", "生产级 HA、跨区域容灾"
        )
        with self.assertRaises(rc.ScopeDecisionRequired) as captured:
            rc.parse_agent_md(agent_doc(block), "Agent.md")
        self.assertIn("互相包含", str(captured.exception))

    def test_cli_returns_scope_decision_exit_code(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        block = insert_in_scope(
            BASELINE_BLOCK,
            "ha_in_scope",
            "生产级 HA、跨区域容灾、自动故障转移和灾难恢复",
        )
        repo.write(AGENT_MD_PATH, agent_doc(block))
        base = repo.commit("base")
        code, _, stderr = invoke(repo, base, base, repo.path / "out")
        self.assertEqual(code, rc.EXIT_SCOPE_DECISION)
        self.assertIn("SCOPE_DECISION_REQUIRED", stderr)
        self.assertFalse((repo.path / "out" / rc.SCOPE_JSON_NAME).exists())

    def test_real_baseline_has_no_false_positive(self) -> None:
        scope = rc.parse_agent_md(AGENT_MD_TEXT, "Agent.md")
        self.assertEqual(rc.detect_semantic_conflicts(scope), [])


# --------------------------------------------------------------------------
# AC-REV-05 评审上下文生成
# --------------------------------------------------------------------------


class TestACREV05Context(RepoTestBase):
    def test_context_sections(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        context = self.read_artifact(rc.CONTEXT_NAME)

        for heading in (
            "## 项目目标",
            "## 必须范围（in_scope）",
            "## 始终必须满足的正确性要求（always_required）",
            "## 明确非目标（non_goals）",
            "## 评审策略（review_policy）",
            "## Finding 分类规则",
            "## 变更文件",
            "## 来源版本与 SHA",
        ):
            self.assertIn(heading, context)

    def test_context_contains_scope_values(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        context = self.read_artifact(rc.CONTEXT_NAME)
        scope_raw = yaml.safe_load(BASELINE_BLOCK)["review_scope"]

        self.assertIn(scope_raw["target"]["description"].strip(), context)
        for entry in scope_raw["in_scope"]:
            self.assertIn(entry["id"], context)
        for entry in scope_raw["always_required"]:
            self.assertIn(entry["id"], context)
        for entry in scope_raw["non_goals"]:
            self.assertIn(entry["id"], context)
        for finding_class in rc.FINDING_CLASSES:
            self.assertIn(finding_class, context)
        self.assertIn("scope_change_requires_user_approval", context)

    def test_context_states_source_sha(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        context = self.read_artifact(rc.CONTEXT_NAME)
        self.assertIn(f"`{self.base}`", context)
        self.assertIn("Agent.md blob SHA", context)
        self.assertIn("schema_version", context)


# --------------------------------------------------------------------------
# AC-REV-06 完整统一评审提示词生成
# --------------------------------------------------------------------------


class TestACREV06Prompt(RepoTestBase):
    def test_prompt_combines_principles_and_scope(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        prompt = self.read_artifact(rc.PROMPT_NAME)

        self.assertIn("## 1. 统一评审原则", prompt)
        self.assertIn("你是 CA Agent Next 的独立架构与实现评审 Agent", prompt)
        self.assertIn("## 2. 项目级评审范围", prompt)
        self.assertIn("## 3. 本次任务上下文", prompt)
        self.assertIn("## 4. 项目范围变更", prompt)
        self.assertIn("## 5. 输出要求", prompt)

        scope_raw = yaml.safe_load(BASELINE_BLOCK)["review_scope"]
        self.assertIn(scope_raw["target"]["description"].strip(), prompt)
        self.assertIn("generic_agent_core", prompt)
        self.assertIn("basic_validation", prompt)
        self.assertIn("production_ha_dr", prompt)

    def test_prompt_preserves_finding_class_semantics(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        prompt = self.read_artifact(rc.PROMPT_NAME)

        for finding_class in rc.FINDING_CLASSES:
            self.assertIn(finding_class, prompt)
        self.assertIn("`OUT_OF_SCOPE` 不阻塞当前实施", prompt)
        self.assertIn("`DEFERRED` 记录后续阶段", prompt)
        self.assertIn("`UNVERIFIED` 保持未知", prompt)
        self.assertIn("`SCOPE_DECISION_REQUIRED` 暂停范围判断", prompt)

    def test_prompt_does_not_claim_review_was_executed(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        prompt = self.read_artifact(rc.PROMPT_NAME)
        self.assertIn("生成提示词不等于 AI Review 已经执行", prompt)
        self.assertIn("不包含任何评审结论", prompt)

    def test_context_and_prompt_do_not_claim_external_injection(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.base, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        self.assertIn(
            "不等同于已经执行 AI Review", self.read_artifact(rc.CONTEXT_NAME)
        )
        self.assertIn(
            "不代表已注入任何外部评审 Harness", self.read_artifact(rc.CONTEXT_NAME)
        )
        self.assertIn(
            "生成提示词不等于 AI Review 已经执行", self.read_artifact(rc.PROMPT_NAME)
        )
        self.assertIn(
            "也不代表生成产物已被外部 Harness 消费",
            self.read_artifact(rc.PROMPT_NAME),
        )


# --------------------------------------------------------------------------
# AC-REV-07 真实 PR SHA 和变更文件
# --------------------------------------------------------------------------


class TestACREV07PRContext(RepoTestBase):
    def setUp(self) -> None:
        super().setUp()
        # base 版本额外包含一条只属于 base 的范围条目，用于证明读取 head。
        self.base_block = insert_in_scope(
            BASELINE_BLOCK, "base_only_scope_entry", "只应出现在 base 版本的范围条目。"
        )
        self.repo.write(AGENT_MD_PATH, agent_doc(self.base_block))
        self.repo.write("src/keep.py", "value = 1\n")
        self.repo.write(
            "docs/设计说明书/F01-示例.md",
            "# F01 示例设计\n\n"
            "> 全局评审范围：继承根目录 Agent.md 的 review_scope。\n"
            "> 本文局部非目标：无。\n\n"
            "## 1. 目标\n\n旧内容\n",
        )
        self.base = self.repo.commit("base with base-only scope entry")

        self.checkout_branch("feature/pr-context")
        self.head_block = insert_in_scope(
            BASELINE_BLOCK, "head_only_scope_entry", "只应出现在 head 版本的范围条目。"
        )
        self.repo.write(AGENT_MD_PATH, agent_doc(self.head_block))
        self.repo.write("src/added.py", "added = True\n")
        self.repo.write("src/keep.py", "value = 2\n")
        self.repo.write(
            "docs/设计说明书/F01-示例.md",
            "# F01 示例设计\n\n"
            "> 全局评审范围：继承根目录 Agent.md 的 review_scope。\n"
            "> 本文局部非目标：无。\n\n"
            "## 1. 目标\n\n新内容\n",
        )
        self.repo.write(
            "docs/设计说明书/F02-新设计.md",
            "# F02\n\n> 全局评审范围：继承根目录 Agent.md 的 review_scope。\n"
            "> 本文局部非目标：无。\n",
        )
        self.repo.move("README.md", "README-renamed.md")
        self.repo.remove("src/keep.py")
        self.head = self.repo.commit("feature changes")

    def test_uses_head_agent_md_and_head_sha(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.head, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        scope = json.loads(self.read_artifact(rc.SCOPE_JSON_NAME))
        ids = [entry["id"] for entry in scope["in_scope"]]

        self.assertIn("head_only_scope_entry", ids)
        self.assertNotIn("base_only_scope_entry", ids)

        context = self.read_artifact(rc.CONTEXT_NAME)
        self.assertIn(f"| Head SHA | `{self.head}` |", context)
        # 变更差异中允许出现 base 条目的删除记录，但范围正文只能来自 head。
        scope_section = context.split("## 变更文件", 1)[0]
        self.assertNotIn("base_only_scope_entry", scope_section)

    def test_changed_files_include_add_modify_rename_delete(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.head, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        context = self.read_artifact(rc.CONTEXT_NAME)

        self.assertIn("| M | `Agent.md` |", context)
        self.assertIn("| A | `src/added.py` |", context)
        self.assertIn("| M | `docs/设计说明书/F01-示例.md` |", context)
        self.assertIn("| A | `docs/设计说明书/F02-新设计.md` |", context)
        self.assertIn("| R100 | `README-renamed.md` | 重命名自 `README.md` |", context)
        self.assertIn("| D | `src/keep.py` | 删除", context)
        self.assertIn("合计 6 个文件", context)

    def test_pr_metadata_and_identifiers_from_event(self) -> None:
        event = {
            "pull_request": {
                "number": 4242,
                "title": "[SR-001] review context",
                "body": "关联 SR-001 与 AC-REV-07，依赖 IR-001。",
            }
        }
        event_path = self.repo.path / "event.json"
        event_path.write_text(json.dumps(event, ensure_ascii=False), encoding="utf-8")

        code, _, stderr = invoke(
            self.repo,
            self.base,
            self.head,
            self.out,
            "--event-path",
            str(event_path),
        )
        self.assertEqual(code, rc.EXIT_OK, stderr)
        context = self.read_artifact(rc.CONTEXT_NAME)
        self.assertIn("#4242", context)
        self.assertIn("SR-001", context)
        self.assertIn("AC-REV-07", context)
        self.assertIn("IR-001", context)

    def test_missing_identifiers_are_explicit(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, self.head, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)
        context = self.read_artifact(rc.CONTEXT_NAME)
        self.assertIn("PR 编号：未提供", context)
        self.assertIn("**未提供**", context)


# --------------------------------------------------------------------------
# AC-REV-08 正式文档头部继承检查
# --------------------------------------------------------------------------


HEADER_OK = (
    "# 示例设计\n\n"
    "> 全局评审范围：继承根目录 Agent.md 的 review_scope。\n"
    "> 本文局部非目标：无。\n\n"
    "## 1. 目标\n\n正文。\n"
)


class TestACREV08DocHeaders(RepoTestBase):
    def test_check_doc_header_accepts_repository_sr_doc(self) -> None:
        text = (REPO_ROOT / "docs/SR/SR-001-评审上下文自动生成.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(rc.check_doc_header(text, "docs/SR/SR-001.md"), [])

    def test_missing_header_fails_with_path(self) -> None:
        self.checkout_branch("feature/docs")
        self.repo.write("docs/架构设计/F01-无头部.md", "# 无头部\n\n## 1. 目标\n\n正文。\n")
        head = self.repo.commit("add doc without header")

        code, _, stderr = invoke(self.repo, self.base, head, self.out)
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("docs/架构设计/F01-无头部.md", stderr)
        self.assertIn("全局评审范围", stderr)
        self.assertIn("本文局部非目标", stderr)

    def test_modified_formal_doc_without_header_fails(self) -> None:
        self.checkout_branch("feature/docs")
        self.repo.write("docs/SR/SR-999-示例.md", HEADER_OK)
        self.base = self.repo.commit("base with formal doc")
        self.repo.write("docs/SR/SR-999-示例.md", "# 示例设计\n\n## 1. 目标\n\n修改。\n")
        head = self.repo.commit("modify doc removing header")

        code, _, stderr = invoke(self.repo, self.base, head, self.out)
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("docs/SR/SR-999-示例.md", stderr)

    def test_header_with_empty_local_non_goals_fails(self) -> None:
        self.checkout_branch("feature/docs")
        self.repo.write(
            "docs/决策记录/ADR-0001-示例.md",
            "# ADR\n\n> 全局评审范围：继承根目录 Agent.md 的 review_scope。\n"
            "> 本文局部非目标：\n",
        )
        head = self.repo.commit("add adr with empty non-goals")

        code, _, stderr = invoke(self.repo, self.base, head, self.out)
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("“本文局部非目标”声明为空", stderr)

    def test_valid_header_passes(self) -> None:
        self.checkout_branch("feature/docs")
        self.repo.write("docs/验收与实施/AC-REV-示例.md", HEADER_OK)
        head = self.repo.commit("add acceptance doc with header")

        code, _, stderr = invoke(self.repo, self.base, head, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)

    def test_deleted_formal_doc_is_not_checked(self) -> None:
        self.checkout_branch("feature/docs")
        self.repo.write("docs/SR/SR-998-待删除.md", "# 无头部旧文档\n\n正文。\n")
        self.base = self.repo.commit("base with legacy doc")
        self.repo.remove("docs/SR/SR-998-待删除.md")
        head = self.repo.commit("delete legacy doc")

        code, _, stderr = invoke(self.repo, self.base, head, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)

    def test_header_rejects_full_negated_inheritance_declarations(self) -> None:
        declarations = (
            "不继承根目录 Agent.md 的 review_scope",
            "无需继承根目录 Agent.md 的 review_scope",
            "不得继承根目录 Agent.md 的 review_scope",
            "禁止继承根目录 Agent.md 的 review_scope",
            "不需要继承根目录 Agent.md 的 review_scope",
            "继承根目录 Agent.md 的 review_scope（仅在适用时）",
        )
        for declaration in declarations:
            with self.subTest(declaration=declaration):
                problems = rc.check_doc_header(
                    "# 示例\n\n"
                    f"> 全局评审范围：{declaration}\n"
                    "> 本文局部非目标：无。\n",
                    "docs/架构设计/F01-否定继承.md",
                )
                self.assertTrue(problems)
                self.assertIn("全局评审范围", problems[0])

    def test_header_requires_single_uncommented_blockquote_declaration(self) -> None:
        invalid_headers = (
            (
                "bare declaration",
                "# 示例\n\n"
                "全局评审范围：继承根目录 Agent.md 的 review_scope\n"
                "> 本文局部非目标：无\n",
            ),
            (
                "fenced declaration",
                "# 示例\n\n"
                "~~~text\n"
                "> 全局评审范围：继承根目录 Agent.md 的 review_scope\n"
                "~~~\n"
                "> 本文局部非目标：无\n",
            ),
            (
                "commented declaration",
                "# 示例\n\n"
                "<!--\n"
                "> 全局评审范围：继承根目录 Agent.md 的 review_scope\n"
                "-->\n"
                "> 本文局部非目标：无\n",
            ),
        )
        for label, header in invalid_headers:
            with self.subTest(case=label):
                problems = rc.check_doc_header(
                    header, "docs/架构设计/F01-伪造继承.md"
                )
                self.assertTrue(problems)
                self.assertIn("全局评审范围", problems[0])

    def test_header_rejects_conflicting_duplicate_scope_declarations(self) -> None:
        problems = rc.check_doc_header(
            "# 示例\n\n"
            "> 全局评审范围：继承根目录 Agent.md 的 review_scope\n"
            "> 全局评审范围：不继承根目录 Agent.md 的 review_scope\n"
            "> 本文局部非目标：无\n",
            "docs/架构设计/F01-重复声明.md",
        )
        self.assertTrue(problems)
        self.assertIn("必须且只能使用一次", problems[0])

    def test_header_accepts_only_canonical_positive_declaration(self) -> None:
        problems = rc.check_doc_header(
            "# 示例\n\n"
            "> 全局评审范围: 继承根目录 Agent.md 的 review_scope。\n"
            "> 本文局部非目标：无。\n",
            "docs/架构设计/F01-正向继承.md",
        )
        self.assertEqual(problems, [])
    def test_non_formal_path_is_ignored(self) -> None:
        self.checkout_branch("feature/docs")
        self.repo.write("docs/规范/示例规范.md", "# 规范\n\n无头部说明。\n")
        head = self.repo.commit("add spec doc")

        code, _, stderr = invoke(self.repo, self.base, head, self.out)
        self.assertEqual(code, rc.EXIT_OK, stderr)


# --------------------------------------------------------------------------
# AC-REV-09 范围变更提示
# --------------------------------------------------------------------------


class TestACREV09ScopeChange(RepoTestBase):
    def test_scope_change_is_reported(self) -> None:
        self.checkout_branch("feature/scope-change")
        block = insert_in_scope(
            BASELINE_BLOCK, "new_scope_entry", "本次 PR 新增的项目范围条目。"
        )
        self.repo.write(AGENT_MD_PATH, agent_doc(block))
        head = self.repo.commit("change review scope")
        summary_path = self.repo.path / "summary.md"

        code, _, stderr = invoke(
            self.repo,
            self.base,
            head,
            self.out,
            "--summary",
            str(summary_path),
        )
        self.assertEqual(code, rc.EXIT_OK, stderr)

        summary = summary_path.read_text(encoding="utf-8")
        self.assertIn("CHANGED", summary)
        self.assertIn("新增：new_scope_entry：本次 PR 新增的项目范围条目。", summary)
        self.assertIn("项目负责人审查", summary)
        for required in (
            "| Base SHA |",
            "| Head SHA |",
            "| Agent.md Head SHA |",
            "| schema_version |",
            "| profile |",
            "| 校验结果 | PASS |",
            "| 变更文件 |",
        ):
            self.assertIn(required, summary)

        context = self.read_artifact(rc.CONTEXT_NAME)
        self.assertIn("范围变更：**CHANGED**", context)
        self.assertIn("new_scope_entry", context)
        self.assertIn("YAML 合法不代表范围变更已经获批", context)

        prompt = self.read_artifact(rc.PROMPT_NAME)
        self.assertIn("CHANGED", prompt)
        self.assertIn("不得把 YAML 合法解释为范围变更已经获批", prompt)

    def test_format_and_comment_changes_are_not_scope_changes(self) -> None:
        self.checkout_branch("feature/format-change")
        block = BASELINE_BLOCK.replace(
            "  profile: demo_prototype\n", '  profile: "demo_prototype"\n', 1
        )
        block = block.replace(
            "review_scope:\n", "review_scope:\n  # 仅注释变化，不影响解析结果\n", 1
        )
        block = block.replace(
            "  schema_version: 1\n", "  schema_version:   1\n", 1
        )
        self.repo.write(AGENT_MD_PATH, agent_doc(block))
        head = self.repo.commit("format only")
        summary_path = self.repo.path / "summary.md"

        code, _, stderr = invoke(
            self.repo, self.base, head, self.out, "--summary", str(summary_path)
        )
        self.assertEqual(code, rc.EXIT_OK, stderr)
        summary = summary_path.read_text(encoding="utf-8")
        self.assertIn("范围变更 | 未变化", summary)
        context = self.read_artifact(rc.CONTEXT_NAME)
        self.assertIn("本次 PR 未修改项目级 review_scope", context)

    def test_removed_entry_is_reported(self) -> None:
        self.checkout_branch("feature/scope-removal")
        block = BASELINE_BLOCK.replace(
            scope_entry(
                "generic_agent_core",
                "Python Agent Core/Host/Runtime 保持业务中立，新增业务不要求修改 Core 业务路由或状态机。",
            ),
            "",
            1,
        )
        self.repo.write(AGENT_MD_PATH, agent_doc(block))
        head = self.repo.commit("remove scope entry")
        summary_path = self.repo.path / "summary.md"

        code, _, stderr = invoke(
            self.repo, self.base, head, self.out, "--summary", str(summary_path)
        )
        self.assertEqual(code, rc.EXIT_OK, stderr)
        summary = summary_path.read_text(encoding="utf-8")
        self.assertIn("删除：generic_agent_core", summary)


# --------------------------------------------------------------------------
# Git 失败关闭
# --------------------------------------------------------------------------


class TestGitFailures(RepoTestBase):
    def test_unknown_base_commit(self) -> None:
        code, _, stderr = invoke(self.repo, "0" * 40, self.base, self.out)
        self.assertEqual(code, rc.EXIT_GIT)
        self.assertIn("base 提交对象不可读取", stderr)

    def test_unknown_head_commit(self) -> None:
        code, _, stderr = invoke(self.repo, self.base, "f" * 40, self.out)
        self.assertEqual(code, rc.EXIT_GIT)
        self.assertIn("head 提交对象不可读取", stderr)

    def test_no_merge_base(self) -> None:
        self.repo.git("checkout", "-q", "--orphan", "orphan")
        self.repo.write("other.txt", "unrelated\n")
        orphan = self.repo.commit("orphan root")

        code, _, stderr = invoke(self.repo, self.base, orphan, self.out)
        self.assertEqual(code, rc.EXIT_GIT)
        self.assertIn("不存在 merge-base", stderr)

    def test_missing_agent_md_fails_closed(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        repo.write("README.md", "# test\n")
        base = repo.commit("no agent md")

        code, _, stderr = invoke(repo, base, base, repo.path / "out")
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("Agent.md 缺失", stderr)

    def test_validation_failure_writes_no_artifact(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        repo.write(
            AGENT_MD_PATH,
            agent_doc(BASELINE_BLOCK.replace("  profile: demo_prototype\n", "", 1)),
        )
        base = repo.commit("invalid scope")
        out = repo.path / "out"

        code, _, stderr = invoke(repo, base, base, out)
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("缺少必填字段 'profile'", stderr)
        self.assertFalse(out.exists())

    def test_subprocess_returns_non_zero_with_location(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        repo.write(
            AGENT_MD_PATH,
            agent_doc(BASELINE_BLOCK.replace("    - OUT_OF_SCOPE\n", "", 1)),
        )
        base = repo.commit("invalid finding classes")
        env = {
            key: value
            for key, value in os.environ.items()
            if key != "GITHUB_EVENT_PATH"
        }
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--repo",
                str(repo.path),
                "--base",
                base,
                "--head",
                base,
                "--out",
                str(repo.path / "out"),
            ],
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("OUT_OF_SCOPE", proc.stderr.decode("utf-8"))
        self.assertFalse((repo.path / "out").exists())


# --------------------------------------------------------------------------
# base 版本范围比较的失败关闭（AC-REV-09 边界）
# --------------------------------------------------------------------------


class TestBaseScopeComparison(RepoTestBase):
    def test_base_rejects_unknown_fields_at_every_mapping_level(self) -> None:
        mutations = (
            (
                "outer document",
                lambda document: document.update({"unexpected_document_key": True}),
            ),
            (
                "review_scope mapping",
                lambda document: document["review_scope"].update(
                    {"unexpected_scope_key": True}
                ),
            ),
            (
                "target mapping",
                lambda document: document["review_scope"]["target"].update(
                    {"unexpected_target_key": True}
                ),
            ),
            (
                "in_scope entry",
                lambda document: document["review_scope"]["in_scope"][0].update(
                    {"unexpected_entry_key": True}
                ),
            ),
            (
                "always_required entry",
                lambda document: document["review_scope"]["always_required"][0].update(
                    {"unexpected_entry_key": True}
                ),
            ),
            (
                "non_goals entry",
                lambda document: document["review_scope"]["non_goals"][0].update(
                    {"unexpected_entry_key": True}
                ),
            ),
            (
                "review_policy mapping",
                lambda document: document["review_scope"]["review_policy"].update(
                    {"unexpected_policy_key": True}
                ),
            ),
        )

        for label, mutate in mutations:
            with self.subTest(mapping=label):
                repo = TempRepo()
                self.addCleanup(repo.close)
                document = yaml.safe_load(BASELINE_BLOCK)
                mutate(document)
                broken_block = yaml.safe_dump(
                    document, allow_unicode=True, sort_keys=False
                )
                repo.write(AGENT_MD_PATH, agent_doc(broken_block))
                base = repo.commit(f"base with unknown field in {label}")
                repo.write(AGENT_MD_PATH, agent_doc())
                head = repo.commit("head removes unknown base field")
                out = repo.path / "out"

                code, _, stderr = invoke(repo, base, head, out)
                self.assertEqual(code, rc.EXIT_VALIDATION, stderr)
                self.assertIn("无法判定范围变更", stderr)
                self.assertFalse(out.exists(), "Base Schema 失败不得写入任何 Artifact")

    def test_base_without_scope_block_is_added(self) -> None:
        repo = TempRepo()
        self.addCleanup(repo.close)
        repo.write(AGENT_MD_PATH, "# 仓库协作指引\n\n本版本暂无 review_scope 区块。\n")
        base = repo.commit("base without review scope")
        repo.write(AGENT_MD_PATH, agent_doc())
        head = repo.commit("add review scope block")
        summary_path = repo.path / "summary.md"

        code, _, stderr = invoke(
            repo, base, head, repo.path / "out", "--summary", str(summary_path)
        )
        self.assertEqual(code, rc.EXIT_OK, stderr)
        summary = summary_path.read_text(encoding="utf-8")
        self.assertIn("ADDED", summary)

    def test_base_with_partial_markers_fails_closed(self) -> None:
        self.repo.write(
            AGENT_MD_PATH,
            f"# 仓库协作指引\n\n{rc.BEGIN_MARKER}\n~~~yaml\n{BASELINE_BLOCK}~~~\n",
        )
        base = self.repo.commit("base with partial markers")
        self.repo.write(AGENT_MD_PATH, agent_doc())
        head = self.repo.commit("head with complete markers")

        code, _, stderr = invoke(self.repo, base, head, self.out)
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("REVIEW_SCOPE 标记不完整", stderr)

    def test_base_with_incomplete_structure_fails_closed(self) -> None:
        broken = BASELINE_BLOCK.replace(
            "  finding_classes:\n", "  finding_classes_removed:\n", 1
        )
        self.repo.write(AGENT_MD_PATH, agent_doc(broken))
        base = self.repo.commit("base with incomplete structure")
        self.repo.write(AGENT_MD_PATH, agent_doc())
        head = self.repo.commit("head with complete structure")

        code, _, stderr = invoke(self.repo, base, head, self.out)
        self.assertEqual(code, rc.EXIT_VALIDATION)
        self.assertIn("无法判定范围变更", stderr)
        self.assertNotIn("Traceback", stderr)


if __name__ == "__main__":
    unittest.main()
