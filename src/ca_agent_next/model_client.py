"""ModelClient 公共协议。

ModelClient 由应用组合入口创建并注入；Host/AgentLoop 不创建真实客户端，
不读取 Provider 配置，不拥有注入对象的资源生命周期。
"""

from __future__ import annotations

from typing import Protocol

from .contracts import ModelProposal, ModelRequest

__all__ = ["ModelClient"]


class ModelClient(Protocol):
    """同步模型客户端，接收 ModelRequest 并返回 ModelProposal。"""

    def propose(self, request: ModelRequest) -> ModelProposal:
        """对一次 ModelRequest 返回结构化提议；调用方保证只调用一次。"""
        ...
