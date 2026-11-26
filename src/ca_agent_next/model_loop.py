"""Agent Loop：一次请求，一次模型调用，无重试。

HostError 从 ``contracts`` 导入，不在本模块重新定义，避免与 ``host`` 形成
循环依赖或产生第二个异常类型。
"""

from __future__ import annotations

from collections.abc import Mapping

from .contracts import HostError, ModelProposal, ModelRequest, is_json_value
from .model_client import ModelClient

__all__ = ["AgentLoop"]


def _proposal_invalid() -> HostError:
    return HostError("MODEL_PROPOSAL_INVALID", "model proposal is invalid")


class AgentLoop:
    """最小 Model Loop：把一次 ModelRequest 投影为一次 ModelProposal。"""

    def __init__(self, model_client: ModelClient) -> None:
        self._model_client = model_client

    def run_once(self, request: ModelRequest) -> ModelProposal:
        """同步调用注入的 ModelClient 恰好一次，并校验其返回值。"""
        try:
            proposal = self._model_client.propose(request)
        except Exception:
            raise HostError("MODEL_CLIENT_FAILED", "model client failed") from None

        if not isinstance(proposal, ModelProposal):
            raise _proposal_invalid()
        if not isinstance(proposal.kind, str) or proposal.kind.strip() == "":
            raise _proposal_invalid()
        if not isinstance(proposal.payload, Mapping):
            raise _proposal_invalid()
        try:
            if not is_json_value(proposal.payload):
                raise _proposal_invalid()
        except HostError:
            raise
        except Exception:
            raise _proposal_invalid() from None
        return proposal
