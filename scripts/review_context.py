#!/usr/bin/env python3
"""SR-001：PR 评审上下文生成器。

从本次 PR 的 head 提交读取根目录 ``Agent.md``，只解析其中唯一的
``REVIEW_SCOPE`` 区块，严格校验后生成三份评审上下文产物：

* ``review-scope.json``：通过校验的标准化项目范围对象。
* ``评审上下文.md``：项目目标、必须范围、正确性要求、非目标、分类规则、
  本次 PR 变更文件和来源版本。
* ``统一评审提示词.md``：统一评审原则、项目级评审范围与本次任务上下文的组合。

设计依据：``docs/SR/SR-001-评审上下文自动生成.md`` v0.3.6 与
``docs/规范/文档编写与治理规范.md`` §11。

用法::

    python scripts/review_context.py --base <base-sha> --head <head-sha> --out <dir>

退出码：

===  ==================================================================
0    成功生成三份产物
1    校验失败（标记、YAML、Schema、ID 冲突、文档头部缺失等）
2    需要范围决策（输出 SCOPE_DECISION_REQUIRED，不得自动裁决）
3    Git 对象、merge-base 或运行环境不可用
4    产物写入失败
64   命令行用法错误
===  ==================================================================

本脚本不调用任何大模型、外部 Harness 或自动 Review 服务；生成产物不等同于
已经执行 AI Review。
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_SCOPE_DECISION = 2
EXIT_GIT = 3
EXIT_OUTPUT = 4
EXIT_USAGE = 64

AGENT_MD_PATH = "Agent.md"
BEGIN_MARKER = "<!-- REVIEW_SCOPE:BEGIN -->"
END_MARKER = "<!-- REVIEW_SCOPE:END -->"
SCOPE_JSON_NAME = "review-scope.json"
CONTEXT_NAME = "评审上下文.md"
PROMPT_NAME = "统一评审提示词.md"

SCHEMA_VERSION = 1
PROFILE = "demo_prototype"
DEFAULT_REVIEW_TARGET = "changed_files_and_direct_dependencies"
UNRESOLVED_SCOPE_CONFLICT = "SCOPE_DECISION_REQUIRED"

TOP_KEYS = (
    "schema_version",
    "profile",
    "target",
    "in_scope",
    "always_required",
    "non_goals",
    "review_policy",
    "finding_classes",
)
TARGET_KEYS = ("description", "sequence")
ENTRY_KEYS = ("id", "description")
SCOPE_LISTS = ("in_scope", "always_required", "non_goals")
POLICY_ENUM_KEYS = ("default_review_target", "unresolved_scope_conflict")
POLICY_BOOL_KEYS = (
    "blocker_requires_traceable_requirement",
    "blocker_requires_verifiable_evidence",
    "missing_non_goal_capability_is_blocking",
    "production_best_practice_alone_is_defect",
    "scope_change_requires_user_approval",
    "findings_must_include_requirement_location_evidence_and_current_goal_impact",
)
POLICY_KEYS = (
    "default_review_target",
    "blocker_requires_traceable_requirement",
    "blocker_requires_verifiable_evidence",
    "missing_non_goal_capability_is_blocking",
    "production_best_practice_alone_is_defect",
    "scope_change_requires_user_approval",
    "unresolved_scope_conflict",
    "findings_must_include_requirement_location_evidence_and_current_goal_impact",
)

FINDING_CLASSES = (
    "BLOCKER",
    "NON_BLOCKING",
    "OUT_OF_SCOPE",
    "DEFERRED",
    "UNVERIFIED",
    "SCOPE_DECISION_REQUIRED",
)
# SR-001 §9：finding_classes 必须是治理规范 §11.3 的六种分类，且无重复。

# 正式架构、设计说明书、SR、验收和决策文档目录（治理规范 §11.7）。
FORMAL_DOC_PREFIXES = (
    "docs/架构设计/",
    "docs/设计说明书/",
    "docs/SR/",
    "docs/验收与实施/",
    "docs/决策记录/",
)

# 明确属于参考资料而非 Next 当前权威架构/设计的目录，不执行正式文档头部门禁。
REFERENCE_ONLY_DOC_PREFIXES = (
    "docs/架构设计/参考实现/",
    "docs/架构设计/目标参考/",
    "docs/设计说明书/参考实现/",
)

# #120 / AC-REV-08: only these existing, reviewed immutable historical source
# paths are eligible for the original-source header exception. Provenance must
# ALSO pass the strict metadata check. A matching header alone is insufficient.
# Adding another imported source requires an explicit reviewed code change.
ARCHIVED_SOURCE_COPY_PATHS = frozenset((
    "docs/决策记录/EC06-ADR-0001-Source-first-Visual.md",
    "docs/决策记录/EC06-ADR-0002-IDE Host Spike.md",
    "docs/决策记录/EC06-ADR-0003-Theia原生工作台与Markdown.md",
    "docs/决策记录/EC06-ADR-0004-Package优先工作区.md",
    "docs/决策记录/EC06-ADR-0005-固定源码与预览工作台.md",
    "docs/架构设计/G01-AI Gateway架构原文.md",
    "docs/架构设计/G01-DeepSeek Harness架构原文.md",
    "docs/架构设计/外部能力域/EC02-Compiler工具链架构原文.md",
    "docs/架构设计/外部能力域/EC03-Tool与Provider架构原文.md",
    "docs/架构设计/外部能力域/EC04-OpenAMSM Go Event Plugin架构提案原文.md",
    "docs/架构设计/外部能力域/EC06-Skill Studio所有权与源码边界原文.md",
    "docs/架构设计/外部能力域/EC06-Theia工作台架构与迁移原文.md",
    "docs/架构设计/外部能力域/EC07-5GC参考领域模型原文.md",
    "docs/架构设计/外部能力域/EC07-5GC模拟器架构原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL Authoring Syntax 原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL Create Skill 工作流原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL Package Layout 原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL Schema Ownership 原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL Skill Granularity 原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL作者指南原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL作者指南英文原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/CA-SL作者模型原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/Ingress Operation契约设计原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/MAS Lifecycle Acceptance Matrix原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/MAS Lifecycle Owner Contract原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/MAS Lifecycle Source Mapping原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/MAS v1alpha5 Compiler Gate原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/MAS v1alpha5 Source Contract Closure原文.md",
    "docs/设计说明书/外部能力域/EC01-CA-SL/Schema闭包摘要设计原文.md",
    "docs/设计说明书/外部能力域/EC02-Compiler/Checked CEL when与运行时Artifact发布设计原文.md",
    "docs/设计说明书/外部能力域/EC02-Compiler/Compiler Core与公共API原文.md",
    "docs/设计说明书/外部能力域/EC02-Compiler/Compiler v1alpha5 Artifact契约原文.md",
    "docs/设计说明书/外部能力域/EC02-Compiler/Development Build Harness交接原文.md",
    "docs/设计说明书/外部能力域/EC02-Compiler/Development Build试点设计原文.md",
    "docs/设计说明书/外部能力域/EC02-Compiler/Evidence与Assurance职责审计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Generic SBI Executor设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Host集成边界设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/MAS Scheme C Typed Callables设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/NAS 5GSM Codec设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Provider Backend Binding Catalog v2设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Provider Protocol v2契约原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Runtime Bindings设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/SBI客户端与Payload Engine设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Tool Provider发布包设计原文.md",
    "docs/设计说明书/外部能力域/EC03-Tool Provider/Typed MAS Provider v2设计原文.md",
    "docs/设计说明书/外部能力域/EC04-OpenAMSM Plugin验收设计提案原文.md",
    "docs/设计说明书/外部能力域/EC05-OpenAMSM Owner/MAS Owner契约与Receipt设计原文.md",
    "docs/设计说明书/外部能力域/EC05-OpenAMSM Owner/PFCP UNKNOWN Reconcile与重启恢复设计原文.md",
    "docs/设计说明书/外部能力域/EC05-OpenAMSM Owner/Scheme C Modify与Release Owner设计原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/AI Procedure Authoring Workbench设计原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/Authoring Workbench设计原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/C4 Package Overview原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/LSP诊断设计原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/LSP语言导航与补全设计原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/Plugin-managed Configuration & Tool Integration v0.1原文.md",
    "docs/设计说明书/外部能力域/EC06-Skill Studio/SKILL Project布局与Compiler集成原文.md",
    "docs/设计说明书/外部能力域/EC07-5GC仿真与Mock AMF/5GC状态机设计原文.md",
    "docs/设计说明书/外部能力域/EC07-5GC仿真与Mock AMF/Mock AMF SBI Test Peer完整设计原文.md",
    "docs/设计说明书/外部能力域/EC07-5GC仿真与Mock AMF/Owner Local Core设计原文.md",
    "docs/设计说明书/外部能力域/EC07-5GC仿真与Mock AMF/Simulator进程与Bindings设计原文.md",
    "docs/设计说明书/外部能力域/EC07-5GC仿真与Mock AMF/模拟协议与Service Fabric边界设计原文.md",
    "docs/设计说明书/目标参考/TARGET01-Go Agent Task Machine契约原文.md",
    "docs/设计说明书/目标参考/TARGET01-Go Host Artifact Store契约原文.md",
))

# A fixed Issue snapshot that lacks the repo in "固定来源" derives it ONLY
# from this reviewed source identity; no new Issue/repo identity is inferred
# from user-authored header text.
ARCHIVED_ISSUE_SOURCE_IDENTITIES = {
    "docs/设计说明书/外部能力域/EC02-Compiler/Checked CEL when与运行时Artifact发布设计原文.md": (
        "ca-skill-compiler", "61"
    ),
}

# 治理规范 §11.3；上下文与提示词只陈述分类语义，不构成另一份项目范围配置。
CLASS_DEFINITIONS = {
    "BLOCKER": (
        "有可复核证据证明违反当前必须要求、破坏核心架构边界或导致必需 Acceptance 无法通过",
        "阻塞当前交付",
    ),
    "NON_BLOCKING": (
        "属于当前范围，但不阻止本次目标或验收闭合",
        "记录并安排处理",
    ),
    "OUT_OF_SCOPE": (
        "属于 Agent.md 明确排除的能力，且没有证据证明其缺失阻断当前目标",
        "不阻塞，不要求当前实施",
    ),
    "DEFERRED": (
        "已明确留待后续阶段处理",
        "记录后续阶段",
    ),
    "UNVERIFIED": (
        "证据不足，暂时无法判断",
        "保持未知，不得写 PASS 或确定缺陷",
    ),
    "SCOPE_DECISION_REQUIRED": (
        "非目标与当前目标可能存在真实冲突，需要用户决定是否改变范围",
        "暂停范围判断，不擅自升级为 BLOCKER",
    ),
}

# 治理规范 §11.5 公共评审提示词原文；CI 在此基础上叠加项目范围与任务上下文。
PUBLIC_REVIEW_PROMPT = """你是 CA Agent Next 的独立架构与实现评审 Agent。

开始前必须阅读 Agent.md、文档编写与治理规范、CI 生成的评审上下文（如存在）、本次任务的 SR/PR/Acceptance、对应架构和设计说明书，以及本次变更涉及的实现和测试。

严格遵守 Agent.md 的项目目标、必须范围、非目标和架构约束。本次任务范围可以更窄，不得自行扩大。默认只评审本次变更及其直接依赖。

必须检查当前目标路径、架构责任边界、接口和 Schema、状态转换、调用链、基本输入/路径校验、fail-closed、Runtime Action Boundary、Owner Receipt/Commit Proof、UNKNOWN、Continuation、二进制载荷保真，以及必需 Example/Acceptance。

对明确排除的生产级能力，不得因其缺失认定为当前缺陷、P0/P1 或阻塞。基本正确性要求仍必须严格检查。如果认为某项非目标阻断当前目标，标记 SCOPE_DECISION_REQUIRED，提供证据并等待用户确认。

每条发现必须引用具体要求，给出位置、可复核证据、实际影响、处理建议和阻塞判断。推测和最佳实践建议不能直接认定为缺陷。未运行测试不得标记 PASS。

分类：BLOCKER、NON_BLOCKING、OUT_OF_SCOPE、DEFERRED、UNVERIFIED、SCOPE_DECISION_REQUIRED。分类与 P0/P1/P2 优先级分开判断。

输出总体结论、评审范围、逐条发现、未验证项和明确非目标。评审目标是验证当前阶段承诺的目标是否正确实现，而不是把 Demo 改造成生产级平台。未经用户确认，不得修改项目范围。"""


class GeneratorError(Exception):
    """带退出码的生成器错误。"""

    exit_code = EXIT_VALIDATION

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(GeneratorError):
    """Agent.md 或生成物校验失败（退出码 1）。"""

    exit_code = EXIT_VALIDATION


class ScopeDecisionRequired(GeneratorError):
    """不同 ID 的语义冲突，必须由用户决定（退出码 2）。"""

    exit_code = EXIT_SCOPE_DECISION

    def __init__(self, conflicts: Sequence[str], source: str) -> None:
        detail = "\n".join(f"- {item}" for item in conflicts)
        super().__init__(
            f"SCOPE_DECISION_REQUIRED: {source} 中不同 ID 的范围描述存在语义冲突，"
            "不得自动裁决，必须由项目负责人确认范围：\n" + detail
        )
        self.conflicts = list(conflicts)


class GitError(GeneratorError):
    """Git 对象或 merge-base 不可用（退出码 3）。"""

    exit_code = EXIT_GIT


class OutputError(GeneratorError):
    """产物写入失败（退出码 4）。"""

    exit_code = EXIT_OUTPUT


# --------------------------------------------------------------------------
# Git 访问
# --------------------------------------------------------------------------


class GitRepository:
    """只读 Git 访问封装。"""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        command = ["git", "-c", "core.quotepath=false", "-C", str(self.root), *args]
        try:
            return subprocess.run(command, capture_output=True, check=False)
        except FileNotFoundError as exc:  # pragma: no cover - 环境缺少 git
            raise GitError(f"无法执行 git：{exc}") from exc

    def _stderr(self, proc: subprocess.CompletedProcess) -> str:
        return proc.stderr.decode("utf-8", errors="replace").strip()

    def resolve_toplevel(self) -> Path:
        proc = self._run("rev-parse", "--show-toplevel")
        if proc.returncode != 0:
            raise GitError(f"无法确定 Git 仓库根目录：{self._stderr(proc)}")
        return Path(proc.stdout.decode("utf-8").strip())

    def require_commit(self, revision: str, label: str) -> str:
        proc = self._run("cat-file", "-e", f"{revision}^{{commit}}")
        if proc.returncode != 0:
            raise GitError(f"{label} 提交对象不可读取：{revision}（{self._stderr(proc)}）")
        resolved = self._run("rev-parse", "--verify", f"{revision}^{{commit}}")
        if resolved.returncode != 0:
            raise GitError(f"{label} 提交对象不可解析：{revision}")
        return resolved.stdout.decode("utf-8").strip()

    def merge_base(self, base: str, head: str) -> str:
        proc = self._run("merge-base", base, head)
        if proc.returncode != 0:
            raise GitError(
                f"不存在 merge-base：{base} 与 {head}（{self._stderr(proc)}）"
            )
        value = proc.stdout.decode("utf-8").strip()
        if not value:
            raise GitError(f"不存在 merge-base：{base} 与 {head}")
        return value

    def read_path(self, revision: str, path: str, label: str) -> bytes | None:
        proc = self._run("cat-file", "blob", f"{revision}:{path}")
        if proc.returncode != 0:
            return None
        return proc.stdout

    def blob_sha(self, revision: str, path: str) -> str | None:
        proc = self._run("rev-parse", "--verify", f"{revision}:{path}")
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8").strip() or None

    def changed_files(self, merge_base: str, head: str) -> list[dict[str, str]]:
        proc = self._run(
            "diff",
            "--name-status",
            "--find-renames",
            "-z",
            merge_base,
            head,
        )
        if proc.returncode != 0:
            raise GitError(f"无法枚举变更文件：{self._stderr(proc)}")
        fields = [item for item in proc.stdout.decode("utf-8").split("\0") if item]
        entries: list[dict[str, str]] = []
        index = 0
        while index < len(fields):
            status = fields[index]
            index += 1
            code = status[:1]
            if code in ("R", "C"):
                if index + 1 >= len(fields):
                    raise GitError("变更文件列表格式异常：重命名/复制缺少路径")
                old_path = fields[index]
                new_path = fields[index + 1]
                index += 2
                entries.append(
                    {
                        "status": status,
                        "code": code,
                        "path": new_path,
                        "old_path": old_path,
                    }
                )
            else:
                if index >= len(fields):
                    raise GitError("变更文件列表格式异常：缺少路径")
                path = fields[index]
                index += 1
                entries.append(
                    {"status": status, "code": code, "path": path, "old_path": ""}
                )
        return entries


# --------------------------------------------------------------------------
# Agent.md review_scope 区块提取与 YAML 解析
# --------------------------------------------------------------------------

_FENCE_OPEN_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})\s*ya?ml\s*$", re.IGNORECASE)
_FENCE_ANY_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})\s*$")


def _marker_lines(lines: Sequence[str], marker: str, source: str) -> list[int]:
    return [index for index, line in enumerate(lines) if line.strip() == marker]


def extract_scope_block(text: str, source: str) -> str:
    """提取 BEGIN/END 标记之间唯一的 YAML 围栏内容。

    只接受单独成行的 HTML 注释标记，以及其间唯一的 YAML 围栏。标记缺失、
    重复、反序或围栏数量不为 1 时失败关闭。
    """

    lines = text.splitlines()
    begins = _marker_lines(lines, BEGIN_MARKER, source)
    ends = _marker_lines(lines, END_MARKER, source)

    if not begins:
        raise ValidationError(f"{source}: 缺少 REVIEW_SCOPE:BEGIN 标记")
    if len(begins) > 1:
        raise ValidationError(
            f"{source}: REVIEW_SCOPE:BEGIN 标记重复出现 {len(begins)} 次，"
            f"首次出现在第 {begins[0] + 1} 行"
        )
    if not ends:
        raise ValidationError(f"{source}: 缺少 REVIEW_SCOPE:END 标记")
    if len(ends) > 1:
        raise ValidationError(
            f"{source}: REVIEW_SCOPE:END 标记重复出现 {len(ends)} 次，"
            f"首次出现在第 {ends[0] + 1} 行"
        )

    begin_index = begins[0]
    end_index = ends[0]
    if begin_index > end_index:
        raise ValidationError(
            f"{source}: REVIEW_SCOPE:END（第 {end_index + 1} 行）出现在 "
            f"REVIEW_SCOPE:BEGIN（第 {begin_index + 1} 行）之前，标记顺序错误"
        )

    body = lines[begin_index + 1 : end_index]
    first_content = next(
        (offset for offset, line in enumerate(body) if line.strip()), None
    )
    if first_content is None:
        raise ValidationError(f"{source}: REVIEW_SCOPE 区块为空，缺少 YAML 围栏")

    open_line_no = begin_index + 2 + first_content
    open_match = _FENCE_OPEN_RE.match(body[first_content].strip())
    if open_match is None:
        raise ValidationError(
            f"{source}: 第 {open_line_no} 行应为 YAML 围栏起始行（如 ~~~yaml），"
            "不得从自由文本推断评审范围"
        )

    fence = open_match.group("fence")
    content: list[str] = []
    closed_at: int | None = None
    for offset in range(first_content + 1, len(body)):
        line = body[offset]
        close_match = _FENCE_ANY_RE.match(line.strip())
        if close_match is not None:
            closing = close_match.group("fence")
            if closing[0] != fence[0] or len(closing) < len(fence):
                raise ValidationError(
                    f"{source}: 第 {begin_index + 2 + offset} 行的围栏与起始围栏 "
                    f"{fence} 不匹配"
                )
            closed_at = offset
            break
        content.append(line)

    if closed_at is None:
        raise ValidationError(f"{source}: YAML 围栏缺少结束行（起始于第 {open_line_no} 行）")

    close_line_no = begin_index + 2 + closed_at
    trailing = body[closed_at + 1 :]
    for offset, line in enumerate(trailing):
        if line.strip():
            raise ValidationError(
                f"{source}: 第 {begin_index + 3 + closed_at + offset} 行位于 YAML 围栏之后，"
                "REVIEW_SCOPE 区块内只允许唯一 YAML 围栏"
            )

    for offset, line in enumerate(content):
        stripped = line.strip()
        if _FENCE_OPEN_RE.match(stripped) or _FENCE_ANY_RE.match(stripped):
            raise ValidationError(
                f"{source}: 第 {begin_index + 3 + offset} 行出现第二个 YAML 围栏，"
                "REVIEW_SCOPE 区块内只允许唯一围栏"
            )

    if not any(line.strip() for line in content):
        raise ValidationError(f"{source}: 第 {open_line_no}～{close_line_no} 行 YAML 围栏为空")

    return "\n".join(content) + "\n"


# --------------------------------------------------------------------------
# 严格 YAML 加载（安全 Loader、拒绝重复 mapping key）
# --------------------------------------------------------------------------


def _yaml_module():
    try:
        import yaml  # noqa: PLC0415 - 延迟导入以便给出明确环境错误
    except ImportError as exc:  # pragma: no cover - 环境缺少 PyYAML
        raise GitError(
            "缺少 PyYAML，无法解析 review_scope；请安装 PyYAML>=6,<7"
        ) from exc
    return yaml


def _strict_loader() -> type:
    yaml = _yaml_module()

    class StrictScopeLoader(yaml.SafeLoader):
        """SafeLoader：拒绝重复 key、非文本 key 与 merge key。"""

        def construct_mapping(self, node, deep=False):  # noqa: ANN001, ANN201
            if not isinstance(node, yaml.MappingNode):
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"期望 mapping，实际为 {node.id}",
                    node.start_mark,
                )
            mapping: dict[str, Any] = {}
            for key_node, value_node in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    raise yaml.constructor.ConstructorError(
                        None,
                        None,
                        "不允许 YAML merge key（<<）",
                        key_node.start_mark,
                    )
                key = self.construct_object(key_node, deep=True)
                if type(key) is not str:
                    raise yaml.constructor.ConstructorError(
                        None,
                        None,
                        f"mapping key 必须为文本，实际为 {_type_name(key)}",
                        key_node.start_mark,
                    )
                if key == "<<":
                    raise yaml.constructor.ConstructorError(
                        None,
                        None,
                        "不允许 YAML merge key（<<）",
                        key_node.start_mark,
                    )
                if key in mapping:
                    raise yaml.constructor.ConstructorError(
                        None,
                        None,
                        f"重复的 mapping key：{key!r}",
                        key_node.start_mark,
                    )
                mapping[key] = self.construct_object(value_node, deep=deep)
            return mapping

    return StrictScopeLoader


def _format_yaml_error(exc: Exception) -> str:
    problem = getattr(exc, "problem", None)
    mark = getattr(exc, "problem_mark", None) or getattr(exc, "context_mark", None)
    location = f"第 {mark.line + 1} 行" if mark is not None else "未知位置"
    detail = problem or str(exc).splitlines()[0]
    return f"{location} YAML 解析失败：{detail}"


def load_scope_yaml(yaml_text: str, source: str) -> dict[str, Any]:
    """解析 review_scope YAML 并返回顶层 mapping。"""

    yaml = _yaml_module()
    loader = _strict_loader()
    try:
        document = yaml.load(yaml_text, Loader=loader)
    except yaml.YAMLError as exc:
        raise ValidationError(f"{source}: {_format_yaml_error(exc)}") from exc
    if type(document) is not dict:
        raise ValidationError(
            f"{source}: review_scope 区块顶层必须为 mapping，实际为 {_type_name(document)}"
        )
    return document


# --------------------------------------------------------------------------
# Schema 校验
# --------------------------------------------------------------------------


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "bool"
    if type(value) is int:
        return "int"
    if type(value) is float:
        return "float"
    if type(value) is str:
        return "str"
    if type(value) is list:
        return "list"
    if type(value) is dict:
        return "mapping"
    return type(value).__name__


def _fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def _expect_mapping(value: Any, path: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(path, f"必须为 mapping，实际为 {_type_name(value)}")
    return value


def _expect_text(value: Any, path: str) -> str:
    if type(value) is not str:
        _fail(path, f"必须为非空文本，实际为 {_type_name(value)}")
    if not value.strip():
        _fail(path, "必须为非空文本，实际为空文本")
    return value


def _expect_sequence(value: Any, path: str) -> list[Any]:
    if type(value) is not list:
        _fail(path, f"必须为 list，实际为 {_type_name(value)}")
    return value


def _check_keys(mapping: dict[str, Any], allowed: Sequence[str], path: str) -> None:
    unknown = [key for key in mapping if key not in allowed]
    if unknown:
        rendered = "、".join(repr(key) for key in unknown)
        _fail(path, f"未知字段 {rendered}；允许字段为 " + "、".join(allowed))
    missing = [key for key in allowed if key not in mapping]
    if missing:
        rendered = "、".join(repr(key) for key in missing)
        _fail(path, f"缺少必填字段 {rendered}")


def _expect_bool(value: Any, path: str) -> bool:
    if type(value) is not bool:
        _fail(path, f"必须为 bool，实际为 {_type_name(value)}（bool 与整数不得互换）")
    return value


def validate_scope(raw: Any, source: str) -> dict[str, Any]:
    """按 SR-001 §3/§6 与治理规范 §11 校验 review_scope 并返回标准化对象。"""

    scope = _expect_mapping(raw, "review_scope")
    _check_keys(scope, TOP_KEYS, "review_scope")

    schema_version = scope["schema_version"]
    if type(schema_version) is not int:
        _fail(
            "review_scope.schema_version",
            f"必须为整数 {SCHEMA_VERSION}，实际为 {_type_name(schema_version)}"
            "（不得把 bool 当作整数）",
        )
    if schema_version != SCHEMA_VERSION:
        _fail(
            "review_scope.schema_version",
            f"不支持的 schema_version {schema_version}；仅支持 {SCHEMA_VERSION}",
        )

    profile = scope["profile"]
    if type(profile) is not str:
        _fail("review_scope.profile", f"必须为文本，实际为 {_type_name(profile)}")
    if profile != PROFILE:
        _fail(
            "review_scope.profile",
            f"未知 profile {profile!r}；仅支持 {PROFILE!r}",
        )

    target = _expect_mapping(scope["target"], "review_scope.target")
    _check_keys(target, TARGET_KEYS, "review_scope.target")
    target_description = _expect_text(
        target["description"], "review_scope.target.description"
    )
    sequence_raw = _expect_sequence(target["sequence"], "review_scope.target.sequence")
    if not sequence_raw:
        _fail("review_scope.target.sequence", "必须为非空 list")
    sequence: list[str] = []
    for index, item in enumerate(sequence_raw):
        text = _expect_text(item, f"review_scope.target.sequence[{index}]")
        if text in sequence:
            _fail(
                f"review_scope.target.sequence[{index}]",
                f"重复的 sequence 项 {text!r}",
            )
        sequence.append(text)

    lists: dict[str, list[dict[str, str]]] = {}
    id_origin: dict[str, list[str]] = {}
    for group in SCOPE_LISTS:
        items_raw = _expect_sequence(scope[group], f"review_scope.{group}")
        if group != "non_goals" and not items_raw:
            _fail(f"review_scope.{group}", "必须为非空 list，空范围不得解释为没有限制")
        entries: list[dict[str, str]] = []
        seen: set[str] = set()
        for index, entry_raw in enumerate(items_raw):
            path = f"review_scope.{group}[{index}]"
            entry = _expect_mapping(entry_raw, path)
            _check_keys(entry, ENTRY_KEYS, path)
            entry_id = _expect_text(entry["id"], f"{path}.id")
            description = _expect_text(entry["description"], f"{path}.description")
            if entry_id in seen:
                _fail(f"{path}.id", f"重复的 ID {entry_id!r}")
            seen.add(entry_id)
            id_origin.setdefault(entry_id, []).append(group)
            entries.append({"id": entry_id, "description": description})
        lists[group] = entries

    for entry_id, groups in id_origin.items():
        if len(groups) > 1:
            if "in_scope" in groups and "non_goals" in groups:
                _fail(
                    f"review_scope.{groups[-1]}",
                    f"ID {entry_id!r} 同时出现在 in_scope 与 non_goals",
                )
            _fail(
                "review_scope",
                f"ID {entry_id!r} 跨列表重复出现（{'、'.join(groups)}）"
                "；三组范围列表的 ID 必须跨组唯一",
            )

    policy = _expect_mapping(scope["review_policy"], "review_scope.review_policy")
    _check_keys(policy, POLICY_KEYS, "review_scope.review_policy")
    default_target = policy["default_review_target"]
    if type(default_target) is not str:
        _fail(
            "review_scope.review_policy.default_review_target",
            f"必须为文本，实际为 {_type_name(default_target)}",
        )
    if default_target != DEFAULT_REVIEW_TARGET:
        _fail(
            "review_scope.review_policy.default_review_target",
            f"未知枚举 {default_target!r}；仅支持 {DEFAULT_REVIEW_TARGET!r}",
        )
    unresolved = policy["unresolved_scope_conflict"]
    if type(unresolved) is not str:
        _fail(
            "review_scope.review_policy.unresolved_scope_conflict",
            f"必须为文本，实际为 {_type_name(unresolved)}",
        )
    if unresolved != UNRESOLVED_SCOPE_CONFLICT:
        _fail(
            "review_scope.review_policy.unresolved_scope_conflict",
            f"未知枚举 {unresolved!r}；仅支持 {UNRESOLVED_SCOPE_CONFLICT!r}",
        )
    normalized_policy: dict[str, Any] = {
        "default_review_target": default_target,
        "blocker_requires_traceable_requirement": _expect_bool(
            policy["blocker_requires_traceable_requirement"],
            "review_scope.review_policy.blocker_requires_traceable_requirement",
        ),
        "blocker_requires_verifiable_evidence": _expect_bool(
            policy["blocker_requires_verifiable_evidence"],
            "review_scope.review_policy.blocker_requires_verifiable_evidence",
        ),
        "missing_non_goal_capability_is_blocking": _expect_bool(
            policy["missing_non_goal_capability_is_blocking"],
            "review_scope.review_policy.missing_non_goal_capability_is_blocking",
        ),
        "production_best_practice_alone_is_defect": _expect_bool(
            policy["production_best_practice_alone_is_defect"],
            "review_scope.review_policy.production_best_practice_alone_is_defect",
        ),
        "scope_change_requires_user_approval": _expect_bool(
            policy["scope_change_requires_user_approval"],
            "review_scope.review_policy.scope_change_requires_user_approval",
        ),
        "unresolved_scope_conflict": unresolved,
        "findings_must_include_requirement_location_evidence_and_current_goal_impact": _expect_bool(
            policy[
                "findings_must_include_requirement_location_evidence_and_current_goal_impact"
            ],
            "review_scope.review_policy."
            "findings_must_include_requirement_location_evidence_and_current_goal_impact",
        ),
    }

    classes_raw = _expect_sequence(scope["finding_classes"], "review_scope.finding_classes")
    if not classes_raw:
        _fail("review_scope.finding_classes", "必须为非空 list")
    classes: list[str] = []
    for index, item in enumerate(classes_raw):
        path = f"review_scope.finding_classes[{index}]"
        text = _expect_text(item, path)
        if text not in FINDING_CLASSES:
            _fail(path, f"未知分类 {text!r}；仅支持 {'、'.join(FINDING_CLASSES)}")
        if text in classes:
            _fail(path, f"重复的分类 {text!r}")
        classes.append(text)
    missing_classes = [name for name in FINDING_CLASSES if name not in classes]
    if missing_classes:
        _fail(
            "review_scope.finding_classes",
            "必须是治理规范 §11.3 的完整六种分类，缺少 "
            + "、".join(missing_classes),
        )

    normalized = {
        "schema_version": schema_version,
        "profile": profile,
        "target": {"description": target_description, "sequence": sequence},
        "in_scope": lists["in_scope"],
        "always_required": lists["always_required"],
        "non_goals": lists["non_goals"],
        "review_policy": normalized_policy,
        "finding_classes": classes,
    }
    conflicts = detect_semantic_conflicts(normalized)
    if conflicts:
        raise ScopeDecisionRequired(conflicts, source)
    return normalized


# --------------------------------------------------------------------------
# 不同 ID 的语义冲突检测（只报告，不自动裁决）
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_PUNCT_RE = re.compile(r"[\s\u3000，。；：、,.!?;:！？（）()【】\[\]{}<>《》\"'“”‘’`~!@#$%^&*+=|\\/…—-]+")


def _normalize_text(text: str) -> str:
    return _PUNCT_RE.sub("", text.lower())


def _token_set(text: str) -> set[str]:
    lowered = text.lower()
    tokens = set(_TOKEN_RE.findall(lowered))
    cjk = "".join(_CJK_RE.findall(lowered))
    tokens.update(cjk[index : index + 2] for index in range(len(cjk) - 1))
    return {token for token in tokens if token}


def detect_semantic_conflicts(scope: dict[str, Any]) -> list[str]:
    """检测不同 ID 之间的范围语义冲突。

    只使用确定性文本规则，不做语义推断，也不自动裁决：

    1. 不同 ID 的规范化描述完全相同；
    2. 跨 in_scope/always_required 与 non_goals 的描述互相包含（较短文本
       不少于 8 个字符）；
    3. 跨上述两类时，描述 token 集合的 Jaccard 相似度不低于 0.85 且两侧
       token 数均不少于 8。

    命中任一条即要求用户决定范围，不自动扩大或缩小范围。
    """

    entries: list[dict[str, str]] = []
    for group in SCOPE_LISTS:
        for entry in scope[group]:
            entries.append(
                {
                    "id": entry["id"],
                    "description": entry["description"],
                    "group": group,
                }
            )

    conflicts: list[str] = []
    for index, left in enumerate(entries):
        for right in entries[index + 1 :]:
            if left["id"] == right["id"]:
                continue
            left_norm = _normalize_text(left["description"])
            right_norm = _normalize_text(right["description"])
            if not left_norm or not right_norm:
                continue
            if left_norm == right_norm:
                conflicts.append(
                    f"ID {left['id']!r}（{left['group']}）与 ID {right['id']!r}"
                    f"（{right['group']}）的描述完全相同：{left['description']}"
                )
                continue
            cross_group = (left["group"] == "non_goals") != (
                right["group"] == "non_goals"
            )
            if not cross_group:
                continue
            shorter, longer = sorted((left_norm, right_norm), key=len)
            if len(shorter) >= 8 and shorter in longer:
                conflicts.append(
                    f"ID {left['id']!r}（{left['group']}）与 ID {right['id']!r}"
                    f"（{right['group']}）的范围描述互相包含，可能存在范围冲突："
                    f"{left['description']} / {right['description']}"
                )
                continue
            left_tokens = _token_set(left["description"])
            right_tokens = _token_set(right["description"])
            if len(left_tokens) < 8 or len(right_tokens) < 8:
                continue
            union = left_tokens | right_tokens
            similarity = len(left_tokens & right_tokens) / len(union)
            if similarity >= 0.85:
                conflicts.append(
                    f"ID {left['id']!r}（{left['group']}）与 ID {right['id']!r}"
                    f"（{right['group']}）的描述高度相似（Jaccard={similarity:.2f}），"
                    "可能存在范围冲突"
                )
    return conflicts


# --------------------------------------------------------------------------
# 范围变更比较
# --------------------------------------------------------------------------


def compare_scopes(
    base_scope: dict[str, Any] | None, head_scope: dict[str, Any]
) -> dict[str, Any]:
    """比较 base/head 解析后的范围对象。

    注释、缩进或引号等格式变化不影响解析结果，因此不会误报范围变更。
    """

    if base_scope is None:
        return {
            "status": "ADDED",
            "sections": [
                {
                    "title": "review_scope",
                    "before": "（base 版本不存在 review_scope 区块）",
                    "after": "已定义",
                }
            ],
        }

    sections: list[dict[str, Any]] = []
    for key in ("schema_version", "profile"):
        if base_scope[key] != head_scope[key]:
            sections.append(
                {
                    "title": key,
                    "before": str(base_scope[key]),
                    "after": str(head_scope[key]),
                }
            )

    if base_scope["target"]["description"] != head_scope["target"]["description"]:
        sections.append(
            {
                "title": "target.description",
                "before": base_scope["target"]["description"],
                "after": head_scope["target"]["description"],
            }
        )

    base_sequence = list(base_scope["target"]["sequence"])
    head_sequence = list(head_scope["target"]["sequence"])
    added = [item for item in head_sequence if item not in base_sequence]
    removed = [item for item in base_sequence if item not in head_sequence]
    if added or removed:
        sections.append(
            {"title": "target.sequence", "added": added, "removed": removed}
        )
    elif base_sequence != head_sequence:
        sections.append(
            {
                "title": "target.sequence（顺序变化）",
                "before": " → ".join(base_sequence),
                "after": " → ".join(head_sequence),
            }
        )

    for group in SCOPE_LISTS:
        base_entries = {entry["id"]: entry["description"] for entry in base_scope[group]}
        head_entries = {entry["id"]: entry["description"] for entry in head_scope[group]}
        added_ids = [key for key in head_entries if key not in base_entries]
        removed_ids = [key for key in base_entries if key not in head_entries]
        changed = [
            {
                "id": key,
                "before": base_entries[key],
                "after": head_entries[key],
            }
            for key in head_entries
            if key in base_entries and base_entries[key] != head_entries[key]
        ]
        if added_ids or removed_ids or changed:
            sections.append(
                {
                    "title": group,
                    "added": [f"{key}：{head_entries[key]}" for key in added_ids],
                    "removed": [f"{key}：{base_entries[key]}" for key in removed_ids],
                    "changed": changed,
                }
            )

    for key in POLICY_KEYS:
        if base_scope["review_policy"][key] != head_scope["review_policy"][key]:
            sections.append(
                {
                    "title": f"review_policy.{key}",
                    "before": str(base_scope["review_policy"][key]),
                    "after": str(head_scope["review_policy"][key]),
                }
            )

    base_classes = list(base_scope["finding_classes"])
    head_classes = list(head_scope["finding_classes"])
    added_classes = [item for item in head_classes if item not in base_classes]
    removed_classes = [item for item in base_classes if item not in head_classes]
    if added_classes or removed_classes:
        sections.append(
            {
                "title": "finding_classes",
                "added": added_classes,
                "removed": removed_classes,
            }
        )

    return {"status": "CHANGED" if sections else "UNCHANGED", "sections": sections}


def render_scope_diff(comparison: dict[str, Any]) -> list[str]:
    """把范围比较结果渲染成 Markdown 行。"""

    status = comparison["status"]
    if status == "UNCHANGED":
        return [
            "范围变更：**未变化**（base 与 head 解析后的 review_scope 对象一致；"
            "注释和格式差异不计为范围变更）。"
        ]

    lines: list[str] = []
    if status == "ADDED":
        lines.append("范围变更：**ADDED**（base 版本不存在 review_scope 区块）。")
    else:
        lines.append("范围变更：**CHANGED**。以下为变更前后差异。")
    lines.append("")
    for section in comparison["sections"]:
        lines.append(f"#### {section['title']}")
        lines.append("")
        if "before" in section:
            lines.append(f"- 变更前：{section['before']}")
            lines.append(f"- 变更后：{section['after']}")
        for item in section.get("added", []):
            lines.append(f"- 新增：{item}")
        for item in section.get("removed", []):
            lines.append(f"- 删除：{item}")
        for item in section.get("changed", []):
            lines.append(f"- 修改 {item['id']}：{item['before']} → {item['after']}")
        lines.append("")
    lines.append(
        "> YAML 合法不代表范围变更已经获批。`review_policy.scope_change_requires_user_approval` "
        "要求项目负责人审查上述差异并显式确认。"
    )
    return lines


# --------------------------------------------------------------------------
# 正式文档头部检查（AC-REV-08）
# --------------------------------------------------------------------------


def _is_formal_doc(path: str) -> bool:
    if not path.endswith(".md"):
        return False
    if any(path.startswith(prefix) for prefix in REFERENCE_ONLY_DOC_PREFIXES):
        return False
    return any(path.startswith(prefix) for prefix in FORMAL_DOC_PREFIXES)


def _is_archived_source_copy(text: str, path: str) -> bool:
    """识别带完整来源链的只读历史原文副本，不把它误作当前正式设计文档。"""

    if path not in ARCHIVED_SOURCE_COPY_PATHS:
        return False

    lines = text.splitlines()
    separator = next(
        (index for index, line in enumerate(lines[:24]) if line.strip() == "---"),
        None,
    )
    if separator is None:
        return False

    metadata = lines[:separator]
    has_origin = any(
        re.match(r"^>\s*(?:迁移来源|源仓)\s*[：:]\s*\S", line)
        for line in metadata
    )
    has_source_path = any(
        re.match(r"^>\s*源路径\s*[：:]\s*\S", line)
        for line in metadata
    )
    has_fixed_commit = any(
        re.fullmatch(
            r">\s*(?:固定源提交|固定候选提交)[：:]\s*\x60?[0-9a-fA-F]{40}\x60?\s*",
            line,
        )
        for line in metadata
    )
    # Existing source copies have one Issue snapshot with a source repo+Issue.
    # Verify the identity against the reviewed path manifest and reject
    # mismatched Issue IDs, arbitrary timestamps, and malformed calendar dates.
    issue_sources = [
        re.fullmatch(
            r">\s*迁移来源[：:]\s*([A-Za-z0-9_.-]+)\s+Issue\s+#(\d+)\s*",
            line,
        )
        for line in metadata
        if re.match(r"^>\s*迁移来源[：:].*\bIssue\b", line)
    ]
    issue_sources = [x for x in issue_sources if x is not None]
    fixed_issue_lines = [
        line for line in metadata if re.match(r"^>\s*固定来源[：:]", line)
    ]
    has_fixed_issue_snapshot = False
    if len(fixed_issue_lines) == 1 and len(issue_sources) == 1:
        fixed = re.fullmatch(
            r">\s*固定来源[：:]\s*Issue\s+#(\d+)[，,]\s*"
            r"最后更新时间\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\s*",
            fixed_issue_lines[0],
        )
        source_repo, source_issue = issue_sources[0].groups()
        if fixed is not None:
            issue_id, when = fixed.groups()
            try:
                valid_calendar = datetime.strptime(
                    when, "%Y-%m-%d %H:%M"
                ).strftime("%Y-%m-%d %H:%M") == when
            except ValueError:
                valid_calendar = False
            has_fixed_issue_snapshot = (
                valid_calendar
                and issue_id == source_issue
                and ARCHIVED_ISSUE_SOURCE_IDENTITIES.get(path)
                == (source_repo, source_issue)
            )
    # A malformed fixed Issue record cannot be laundered through a second
    # 40-hex commit token in the same archived-document header.
    if fixed_issue_lines and not has_fixed_issue_snapshot:
        return False

    has_source_state = any(
        re.match(r"^>\s*(?:原始状态|源文档定位)\s*[：:]\s*\S", line)
        for line in metadata
    )
    has_migration_trace = any(
        re.match(r"^>\s*(?:迁移追踪|迁移记录)\s*[：:]\s*\S", line)
        for line in metadata
    )
    # 两种已存在的迁移头格式：迁移来源（自带源路径），或源仓 + 源路径。
    origin_is_complete = has_origin or (
        any(re.match(r"^>\s*源仓\s*[：:]\s*\S", line) for line in metadata)
        and has_source_path
    )
    return (
        origin_is_complete
        and (has_fixed_commit or has_fixed_issue_snapshot)
        and has_source_state
        and has_migration_trace
    )


def _normalize_header_declaration(line: str) -> str:
    """规范化 Markdown blockquote、空白和冒号，不改变声明语义。"""

    value = line.strip()
    while value.startswith(">"):
        value = value[1:].lstrip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*[：:]\s*", "：", value)
    return value.rstrip("。.")


def _header_metadata_lines(header_lines: list[str]) -> list[str]:
    """仅提取真实 Markdown blockquote 元数据行，忽略代码围栏和 HTML 注释。"""

    declarations: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    in_html_comment = False

    for line in header_lines:
        stripped = line.lstrip()
        fence_probe = stripped
        while fence_probe.startswith(">"):
            fence_probe = fence_probe[1:].lstrip()
        fence = re.match(r"^(\x60{3,}|~{3,})", fence_probe)
        if fence:
            marker = fence.group(1)
            if fence_char is None:
                fence_char = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = None
                fence_length = 0
            continue
        if fence_char is not None:
            continue

        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            continue
        if "<!--" in line:
            if "-->" not in line.split("<!--", 1)[1]:
                in_html_comment = True
            continue

        if line.startswith(">"):
            declarations.append(_normalize_header_declaration(line))

    return declarations


def check_doc_header(text: str, path: str) -> list[str]:
    """检查正式文档头部是否声明继承全局范围和本文局部非目标。"""

    header_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## ") or line.startswith("# "):
            if header_lines:
                break
        header_lines.append(line)
        if line.startswith("## "):
            break

    problems: list[str] = []
    metadata_lines = _header_metadata_lines(header_lines)
    canonical_scope = "全局评审范围：继承根目录 Agent.md 的 review_scope"
    scope_declarations = [
        line for line in metadata_lines if line.startswith("全局评审范围")
    ]
    if scope_declarations != [canonical_scope]:
        problems.append(
            f"{path}: 文档头部必须且只能使用一次正向规范声明“{canonical_scope}”"
        )

    local_declarations = [
        line for line in metadata_lines if line.startswith("本文局部非目标")
    ]
    if len(local_declarations) != 1:
        problems.append(
            f"{path}: 文档头部必须且只能包含一条“本文局部非目标”声明（没有时写“无”）"
        )
    else:
        declaration = re.fullmatch(
            r"本文局部非目标[：:]\s*(.*)", local_declarations[0]
        )
        if declaration is None or not declaration.group(1).strip():
            problems.append(
                f"{path}: 文档头部的“本文局部非目标”声明为空或格式错误（没有时写“无”）"
            )
    return problems


def check_changed_doc_headers(
    repo: GitRepository, head: str, changes: Sequence[dict[str, str]]
) -> list[str]:
    """对本次新增或修改的正式文档执行头部检查；删除文件只列入摘要。"""

    problems: list[str] = []
    for change in changes:
        if change["code"] == "D":
            continue
        path = change["path"]
        if not _is_formal_doc(path):
            continue
        blob = repo.read_path(head, path, f"head:{path}")
        if blob is None:
            problems.append(f"{path}: 无法从 head 版本读取该文档内容")
            continue
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError as exc:
            problems.append(f"{path}: 文档不是合法 UTF-8（{exc}）")
            continue
        # 原始来源副本保留原文，不强制注入 Next 当前设计头；只有完整来源链才可豁免。
        if _is_archived_source_copy(text, path):
            continue
        problems.extend(check_doc_header(text, path))
    return problems


# --------------------------------------------------------------------------
# 本次任务上下文
# --------------------------------------------------------------------------


def load_pr_metadata(
    event_path: str | None, pr_number: str | None
) -> dict[str, Any]:
    """从 GITHUB_EVENT_PATH 读取 PR number/title/body，并提取已有标识。"""

    number = pr_number
    title = ""
    body = ""
    source = "未提供"
    if event_path:
        path = Path(event_path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ValidationError(f"GITHUB_EVENT_PATH 不存在：{event_path}")
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"无法解析 GitHub 事件 JSON（{event_path}）：{exc}")
        pull_request = data.get("pull_request") or {}
        if not isinstance(pull_request, dict):
            raise ValidationError(f"{event_path}: pull_request 字段不是对象")
        if pull_request.get("number") is not None:
            number = str(pull_request["number"])
        title = pull_request.get("title") or ""
        body = pull_request.get("body") or ""
        source = event_path
        if not isinstance(title, str) or not isinstance(body, str):
            raise ValidationError(f"{event_path}: PR title/body 必须是文本")

    text = f"{title}\n{body}"
    identifiers = {
        "SR": sorted(set(re.findall(r"SR-\d{3}", text))),
        "IR": sorted(set(re.findall(r"IR-\d{3}", text))),
        "AC": sorted(set(re.findall(r"AC-[A-Z0-9]+-\d{1,3}", text))),
    }
    return {
        "number": number or "",
        "title": title,
        "body": body,
        "source": source,
        "identifiers": identifiers,
    }


def _render_identifiers(metadata: dict[str, Any]) -> list[str]:
    identifiers = metadata["identifiers"]
    lines: list[str] = []
    if not any(identifiers.values()):
        lines.append("- SR/Acceptance 标识：**未提供**（PR 标题与正文中未声明）。")
        return lines
    for key, label in (("SR", "SR"), ("IR", "IR"), ("AC", "Acceptance")):
        values = identifiers[key]
        rendered = "、".join(values) if values else "未提供"
        lines.append(f"- {label} 标识：{rendered}")
    return lines


# --------------------------------------------------------------------------
# 产物渲染
# --------------------------------------------------------------------------


def _render_scope_body(scope: dict[str, Any], level: int) -> list[str]:
    marker = "#" * level
    lines: list[str] = []
    lines.append(f"{marker} 项目目标")
    lines.append("")
    lines.append(scope["target"]["description"].strip())
    lines.append("")
    lines.append("目标顺序：")
    lines.append("")
    for index, item in enumerate(scope["target"]["sequence"], start=1):
        lines.append(f"{index}. `{item}`")
    lines.append("")

    titles = {
        "in_scope": "必须范围（in_scope）",
        "always_required": "始终必须满足的正确性要求（always_required）",
        "non_goals": "明确非目标（non_goals）",
    }
    for group in SCOPE_LISTS:
        lines.append(f"{marker} {titles[group]}")
        lines.append("")
        entries = scope[group]
        if not entries:
            lines.append("- 无")
            lines.append("")
            continue
        for entry in entries:
            lines.append(f"- `{entry['id']}`：{entry['description']}")
        lines.append("")

    lines.append(f"{marker} 评审策略（review_policy）")
    lines.append("")
    lines.append("| 策略项 | 值 |")
    lines.append("|---|---|")
    for key in POLICY_KEYS:
        value = scope["review_policy"][key]
        rendered = "true" if value is True else "false" if value is False else str(value)
        lines.append(f"| `{key}` | `{rendered}` |")
    lines.append("")

    lines.append(f"{marker} Finding 分类规则")
    lines.append("")
    lines.append("| 分类 | 定义 | 默认处理 |")
    lines.append("|---|---|---|")
    for name in scope["finding_classes"]:
        definition, handling = CLASS_DEFINITIONS[name]
        lines.append(f"| {name} | {definition} | {handling} |")
    lines.append("")
    return lines


def _render_changed_files(changes: Sequence[dict[str, str]], level: int) -> list[str]:
    marker = "#" * level
    lines = [f"{marker} 变更文件", ""]
    if not changes:
        lines.append("本次 PR 没有变更文件（merge-base 与 head 之间无差异）。")
        lines.append("")
        return lines
    lines.append("| 状态 | 路径 | 说明 |")
    lines.append("|---|---|---|")
    for change in changes:
        status = change["status"]
        if change["code"] == "R":
            note = f"重命名自 `{change['old_path']}`"
        elif change["code"] == "D":
            note = "删除；只列入摘要，不读取 head 内容"
        else:
            note = ""
        lines.append(f"| {status} | `{change['path']}` | {note} |")
    lines.append("")
    counts: dict[str, int] = {}
    for change in changes:
        counts[change["code"]] = counts.get(change["code"], 0) + 1
    summary = "、".join(f"{key} {counts[key]} 个" for key in sorted(counts))
    lines.append(f"合计 {len(changes)} 个文件（{summary}）。")
    lines.append("")
    return lines


def _render_source(
    info: dict[str, Any], metadata: dict[str, Any], level: int
) -> list[str]:
    marker = "#" * level
    lines = [f"{marker} 来源版本与 SHA", ""]
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| Base SHA | `{info['base']}` |")
    lines.append(f"| Head SHA | `{info['head']}` |")
    lines.append(f"| Merge base | `{info['merge_base']}` |")
    lines.append(f"| Agent.md 来源 | head `{info['head']}` 的 `Agent.md` |")
    lines.append(f"| Agent.md blob SHA | `{info['agent_md_blob']}` |")
    lines.append(f"| schema_version | {info['scope']['schema_version']} |")
    lines.append(f"| profile | `{info['scope']['profile']}` |")
    lines.append(f"| PR | {('#' + metadata['number']) if metadata['number'] else '未提供'} |")
    lines.append("| 生成器 | SR-001 `scripts/review_context.py` v1 |")
    lines.append("")
    return lines


def render_context(
    info: dict[str, Any], metadata: dict[str, Any], changes: Sequence[dict[str, str]]
) -> str:
    scope = info["scope"]
    lines: list[str] = [
        "# 评审上下文（SR-001 自动生成）",
        "",
        "> 本文件由 CI 从根目录 `Agent.md` 的唯一 `review_scope` 区块生成，"
        "不是评审结论。",
        "> 生成产物不等同于已经执行 AI Review，也不代表已注入任何外部评审 Harness。",
        "",
    ]
    lines.extend(_render_scope_body(scope, level=2))
    lines.extend(_render_changed_files(changes, level=2))

    lines.append("## 本次任务上下文")
    lines.append("")
    lines.append(f"- PR 编号：{('#' + metadata['number']) if metadata['number'] else '未提供'}")
    lines.append(f"- PR 标题：{metadata['title'].strip() or '未提供'}")
    lines.append(f"- 元数据来源：{metadata['source']}")
    lines.extend(_render_identifiers(metadata))
    lines.append("")

    lines.append("## 项目范围变更")
    lines.append("")
    if info["comparison"]["status"] == "UNCHANGED":
        lines.append("本次 PR 未修改项目级 review_scope。")
    else:
        lines.extend(render_scope_diff(info["comparison"]))
    lines.append("")
    lines.extend(_render_source(info, metadata, level=2))
    return "\n".join(lines).rstrip() + "\n"


def render_prompt(
    info: dict[str, Any], metadata: dict[str, Any], changes: Sequence[dict[str, str]]
) -> str:
    scope = info["scope"]
    lines: list[str] = [
        "# 统一评审提示词（SR-001 自动生成）",
        "",
        "> 本提示词由 CI 组合统一评审原则、项目级评审范围和本次任务上下文。",
        "> **生成提示词不等于 AI Review 已经执行**；本文件不包含任何评审结论，",
        "> 也不代表生成产物已被外部 Harness 消费。",
        "",
        "## 1. 统一评审原则",
        "",
        PUBLIC_REVIEW_PROMPT,
        "",
        "## 2. 项目级评审范围",
        "",
        "以下内容来自根目录 `Agent.md` 的 `review_scope` 区块（head "
        f"`{info['head']}`，blob `{info['agent_md_blob']}`）。任务级范围可以缩小，"
        "不得扩大。",
        "",
    ]
    lines.extend(_render_scope_body(scope, level=3))

    lines.append("## 3. 本次任务上下文")
    lines.append("")
    lines.append(f"- PR 编号：{('#' + metadata['number']) if metadata['number'] else '未提供'}")
    lines.append(f"- PR 标题：{metadata['title'].strip() or '未提供'}")
    lines.append(f"- Base SHA：`{info['base']}`")
    lines.append(f"- Head SHA：`{info['head']}`")
    lines.append(f"- Merge base：`{info['merge_base']}`")
    lines.extend(_render_identifiers(metadata))
    lines.append("")
    lines.extend(_render_changed_files(changes, level=3))

    lines.append("## 4. 项目范围变更")
    lines.append("")
    if info["comparison"]["status"] == "UNCHANGED":
        lines.append("本次 PR 未修改项目级 review_scope。评审仍须以本提示词的项目范围为准。")
    else:
        lines.extend(render_scope_diff(info["comparison"]))
        lines.append("")
        lines.append(
            "评审必须要求项目负责人审查上述范围变更并显式确认；"
            "不得把 YAML 合法解释为范围变更已经获批。"
        )
    lines.append("")

    lines.append("## 5. 输出要求")
    lines.append("")
    lines.append(
        "每条发现必须包含：分类（必要时附优先级）、对应架构/设计/SR/Acceptance 要求、"
        "具体文件/符号/行号、预期与实际行为、可复核证据、对当前目标的影响、"
        "处理建议和阻塞理由。"
    )
    lines.append("")
    lines.append(
        "分类必须使用上述 `finding_classes` 的原始语义：`OUT_OF_SCOPE` 不阻塞当前实施；"
        "`DEFERRED` 记录后续阶段；`UNVERIFIED` 保持未知，不得写成 PASS 或确定缺陷；"
        "`SCOPE_DECISION_REQUIRED` 暂停范围判断并等待用户确认，不得擅自升级为 BLOCKER。"
    )
    lines.append("")
    lines.append("未运行的测试必须标记 NOT_RUN 或 BLOCKED，不得推断 PASS。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_summary(info: dict[str, Any], metadata: dict[str, Any]) -> str:
    scope = info["scope"]
    changes = info["changes"]
    counts: dict[str, int] = {}
    for change in changes:
        counts[change["code"]] = counts.get(change["code"], 0) + 1
    counts_text = " / ".join(f"{key} {counts[key]}" for key in sorted(counts)) or "无"
    status_text = {
        "UNCHANGED": "未变化",
        "CHANGED": "CHANGED（需项目负责人审查）",
        "ADDED": "ADDED（base 无范围区块）",
    }[info["comparison"]["status"]]

    lines: list[str] = [
        "## Review Context（SR-001）",
        "",
        "| 项 | 值 |",
        "|---|---|",
        f"| PR | {('#' + metadata['number']) if metadata['number'] else '未提供'} |",
        f"| PR 标题 | {metadata['title'].strip() or '未提供'} |",
        f"| Base SHA | `{info['base']}` |",
        f"| Head SHA | `{info['head']}` |",
        f"| Merge base | `{info['merge_base']}` |",
        f"| Agent.md Head SHA | `{info['head']}` |",
        f"| Agent.md blob SHA | `{info['agent_md_blob']}` |",
        f"| schema_version | {scope['schema_version']} |",
        f"| profile | `{scope['profile']}` |",
        f"| 变更文件 | {len(changes)} 个（{counts_text}） |",
        f"| 范围变更 | {status_text} |",
        f"| 校验结果 | {info['validation_result']} |",
        "",
        "### 生成物",
        "",
        f"- `{SCOPE_JSON_NAME}`",
        f"- `{CONTEXT_NAME}`",
        f"- `{PROMPT_NAME}`",
        "",
        "> 生成物不等同于 AI Review 已执行，也不代表已自动注入外部评审 Harness。",
        "",
    ]
    if changes:
        lines.append("### 变更文件摘要")
        lines.append("")
        lines.append("| 状态 | 路径 |")
        lines.append("|---|---|")
        for change in changes[:50]:
            path = change["path"]
            if change["code"] == "R":
                path = f"{change['old_path']} → {change['path']}"
            lines.append(f"| {change['status']} | `{path}` |")
        if len(changes) > 50:
            lines.append(f"| … | 其余 {len(changes) - 50} 个文件省略 |")
        lines.append("")
    lines.append("### 范围变更")
    lines.append("")
    lines.extend(render_scope_diff(info["comparison"]))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------


def _read_agent_md(repo: GitRepository, revision: str, label: str) -> str:
    blob = repo.read_path(revision, AGENT_MD_PATH, label)
    if blob is None:
        raise ValidationError(f"{label}: {AGENT_MD_PATH} 缺失（{revision}）")
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{label}: {AGENT_MD_PATH} 不是合法 UTF-8（{exc}）") from exc


def parse_agent_md(text: str, source: str) -> dict[str, Any]:
    """提取、解析并严格校验 Agent.md 中的 review_scope。"""

    block = extract_scope_block(text, source)
    document = load_scope_yaml(block, source)
    if "review_scope" not in document:
        raise ValidationError(f"{source}: review_scope 区块缺少顶层 review_scope 键")
    unknown = [key for key in document if key != "review_scope"]
    if unknown:
        rendered = "、".join(repr(key) for key in unknown)
        raise ValidationError(
            f"{source}: review_scope 区块只允许唯一的 review_scope 顶层键，"
            f"发现额外顶层键 {rendered}"
        )
    return validate_scope(document["review_scope"], source)


def _require_comparable_scope(raw: Any, source: str) -> dict[str, Any]:
    """Base 必须通过与 Head 完全相同的当前严格 Schema，不做兼容降级。"""

    try:
        # 统一校验顶层/嵌套 mapping 的未知字段、必填字段、类型、枚举、
        # ID 唯一性和六类 finding_classes；返回标准化对象供差异比较。
        return validate_scope(raw, source)
    except ValidationError as exc:
        raise ValidationError(
            f"{source}: Base review_scope 不符合当前严格 Schema，"
            f"无法判定范围变更：{exc.message}"
        ) from None


def build_result(
    repo: GitRepository,
    base: str,
    head: str,
    event_path: str | None,
    pr_number: str | None,
) -> dict[str, Any]:
    """执行完整生成流程并返回结果信息（不写产物）。"""

    base_commit = repo.require_commit(base, "base")
    head_commit = repo.require_commit(head, "head")
    merge_base = repo.merge_base(base_commit, head_commit)

    head_text = _read_agent_md(repo, head_commit, f"head({head_commit})")
    head_scope = parse_agent_md(head_text, f"Agent.md（head {head_commit}）")

    base_scope: dict[str, Any] | None = None
    base_blob = repo.read_path(base_commit, AGENT_MD_PATH, "base")
    base_source = f"Agent.md（base {base_commit}）"
    if base_blob is None:
        base_scope = None
    else:
        try:
            base_text = base_blob.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError(
                f"{base_source} 不是合法 UTF-8，无法判定范围变更（{exc}）"
            ) from exc
        base_lines = base_text.splitlines()
        base_begin = _marker_lines(base_lines, BEGIN_MARKER, "base")
        base_end = _marker_lines(base_lines, END_MARKER, "base")
        if not base_begin and not base_end:
            # base 版本没有 review_scope 区块：范围由无到有，必须显式展示。
            base_scope = None
        elif not base_begin or not base_end:
            raise ValidationError(
                f"{base_source} 的 REVIEW_SCOPE 标记不完整，无法判定范围变更"
            )
        else:
            block = extract_scope_block(base_text, base_source)
            document = load_scope_yaml(block, base_source)
            if "review_scope" not in document:
                raise ValidationError(
                    f"{base_source} 的 review_scope 区块缺少顶层 review_scope 键，"
                    "无法判定范围变更"
                )
            unknown_document_keys = [
                key for key in document if key != "review_scope"
            ]
            if unknown_document_keys:
                rendered = "、".join(repr(key) for key in unknown_document_keys)
                raise ValidationError(
                    f"{base_source}: review_scope 区块只允许唯一的 "
                    f"review_scope 顶层键，发现额外顶层键 {rendered}；"
                    "无法判定范围变更"
                )
            base_scope = _require_comparable_scope(document["review_scope"], base_source)

    comparison = compare_scopes(base_scope, head_scope)
    changes = repo.changed_files(merge_base, head_commit)

    header_problems = check_changed_doc_headers(repo, head_commit, changes)
    if header_problems:
        raise ValidationError(
            "正式文档头部检查失败（治理规范 §11.7）：\n"
            + "\n".join(f"- {item}" for item in header_problems)
        )

    metadata = load_pr_metadata(event_path, pr_number)
    info = {
        "base": base_commit,
        "head": head_commit,
        "merge_base": merge_base,
        "agent_md_blob": repo.blob_sha(head_commit, AGENT_MD_PATH) or "",
        "scope": head_scope,
        "comparison": comparison,
        "changes": changes,
        "validation_result": "PASS",
    }
    info["metadata"] = metadata
    info["artifacts"] = {
        SCOPE_JSON_NAME: json.dumps(head_scope, ensure_ascii=False, indent=2) + "\n",
        CONTEXT_NAME: render_context(info, metadata, changes),
        PROMPT_NAME: render_prompt(info, metadata, changes),
    }
    info["summary"] = render_summary(info, metadata)
    return info


def write_artifacts(out_dir: Path, artifacts: dict[str, str]) -> list[Path]:
    written: list[Path] = []
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OutputError(f"无法创建输出目录 {out_dir}：{exc}") from exc
    for name, content in artifacts.items():
        target = out_dir / name
        try:
            target.write_text(content, encoding="utf-8", newline="\n")
        except OSError as exc:
            raise OutputError(f"无法写入生成物 {target}：{exc}") from exc
        written.append(target)
    return written


class _UsageArgumentParser(argparse.ArgumentParser):
    """命令行用法错误使用独立退出码，避免与 SCOPE_DECISION_REQUIRED 混淆。"""

    def error(self, message: str) -> None:  # pragma: no cover - 用法错误分支
        self.print_usage(sys.stderr)
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = _UsageArgumentParser(
        prog="review_context.py",
        description="SR-001 PR 评审上下文生成器：从 head 版 Agent.md 生成评审上下文。",
    )
    parser.add_argument("--base", required=True, help="PR base 提交 SHA")
    parser.add_argument("--head", required=True, help="PR head 提交 SHA")
    parser.add_argument("--out", required=True, help="生成物输出目录（临时目录）")
    parser.add_argument("--repo", default=None, help="Git 仓库路径，默认当前目录")
    parser.add_argument(
        "--event-path",
        default=None,
        help="GitHub 事件 JSON 路径，默认读取 GITHUB_EVENT_PATH",
    )
    parser.add_argument("--pr-number", default=None, help="PR 编号补充来源")
    parser.add_argument("--summary", default=None, help="Workflow Summary Markdown 输出路径")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):  # pragma: no cover - 非标准流
            pass

    args = parse_args(argv)
    try:
        repo = GitRepository(Path(args.repo) if args.repo else Path.cwd())
        if args.repo is None:
            repo = GitRepository(repo.resolve_toplevel())
        event_path = args.event_path
        if event_path is None:
            import os  # noqa: PLC0415 - 仅在需要时读取环境

            event_path = os.environ.get("GITHUB_EVENT_PATH")
        info = build_result(repo, args.base, args.head, event_path, args.pr_number)
        written = write_artifacts(Path(args.out), info["artifacts"])
        if args.summary:
            summary_path = Path(args.summary)
            try:
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(info["summary"], encoding="utf-8", newline="\n")
            except OSError as exc:
                raise OutputError(f"无法写入 Summary {summary_path}：{exc}") from exc
        print(
            f"review_scope 校验通过：head={info['head']} "
            f"schema_version={info['scope']['schema_version']} "
            f"profile={info['scope']['profile']} "
            f"变更文件={len(info['changes'])} "
            f"范围变更={info['comparison']['status']}"
        )
        for path in written:
            print(f"生成：{path}")
        return EXIT_OK
    except GeneratorError as exc:
        print(f"ERROR: {exc.message}" if exc.exit_code != EXIT_SCOPE_DECISION else exc.message,
              file=sys.stderr)
        return exc.exit_code
    except BrokenPipeError:  # pragma: no cover - 管道提前关闭
        return EXIT_OUTPUT


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
