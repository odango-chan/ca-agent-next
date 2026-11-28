> 迁移来源：ai-gateway/docs/architecture.md  
> 固定源提交：a8fbf37f6614d5e8c4b4c7faed2fce6c98a34ac9  
> 源文档定位：G01 AI Gateway 架构原文  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# AI Gateway Architecture / 架构说明

AI Gateway is a lightweight Go HTTP gateway that runs on a user's own machine or on a trusted internal-network server. This document describes the architecture implemented by the current repository. The diagram is generated with Archify from the JSON source, not hand-drawn or exported as a one-off image.

AI Gateway 是一个轻量级 Go HTTP Gateway，运行在用户本机或可信内网服务器上。本文描述当前仓库实际实现的架构。架构图由 Archify 从 JSON 源码生成，不是手绘或一次性图片。

## Architecture diagram / 架构图

![AI Gateway architecture / AI Gateway 架构图](architecture/ai-gateway.svg)

- **Interactive HTML / 交互式成品**：[ai-gateway.html](architecture/ai-gateway.html) — download the file and open it in a local browser. GitHub's normal file preview can show the source but does not run the standalone page, and this repository does not use GitHub Pages.
- **Editable source / 可编辑源码**：[ai-gateway.architecture.json](architecture/ai-gateway.architecture.json) — the single Archify Architecture source used to regenerate the HTML and SVG.
- **HTML 使用方式**：下载 `docs/architecture/ai-gateway.html` 后用本地浏览器打开。GitHub 普通文件预览不会执行独立 HTML，本仓库也不依赖 GitHub Pages 或外部托管。

The diagram shows the main request journey and the two real deployment profiles. Components and source references are taken from `cmd/`, `internal/`, and `configs/`; features that exist only in prose are not drawn as implemented capabilities.

架构图展示真实请求链路和两种部署方式。组件与源码证据来自 `cmd/`、`internal/` 和 `configs/`；仅存在于文字描述、尚未实现的能力不会画成已实现组件。

## Deployment model / 部署模型

### Local use / 本机使用

Run the Gateway on the same machine as the client and keep the listener on the loopback address (the default is `127.0.0.1:8787`). No shared Gateway access token is required for this local-only mode.

Gateway 与客户端运行在同一台机器上，监听本机回环地址（默认 `127.0.0.1:8787`）。仅本机访问时，不需要配置共享 Gateway 访问令牌。

### Shared internal service / 内网共享服务

Run one Gateway process on an internal server and let multiple trusted clients use the same endpoint. To listen beyond loopback, explicitly set `server.allow_remote: true` and configure `server.access_token_env`. All clients use the same `X-Gateway-Token`; it is a shared network access secret, not user authentication.

在内网服务器上运行一个 Gateway 实例，供多个可信客户端共用。监听非回环地址时，必须显式设置 `server.allow_remote: true`，并配置 `server.access_token_env`。所有客户端共用同一个 `X-Gateway-Token`。它只是共享的网络访问密钥，不是用户身份认证。

Keep the service inside a trusted network boundary. Apply firewall rules and use a trusted TLS-terminating reverse proxy when HTTPS is required. Do not expose the Gateway directly to the public internet.

Gateway 应限制在可信内网中访问，配合防火墙控制网络边界；需要 HTTPS 时，在前面部署可信的 TLS 终止反向代理。不要将 Gateway 直接暴露到公网。

## Shared upstream credentials / 共享上游凭证

Provider credentials are configured on the Gateway host, normally through environment variables referenced by the YAML configuration. The Gateway injects the configured upstream headers when forwarding requests. Client applications do not need to store or receive the provider API key.

Provider 凭证保存在 Gateway 所在主机上，通常通过 YAML 配置引用环境变量。Gateway 转发请求时注入配置好的上游请求头。客户端应用不需要保存或接收 Provider API Key。

All clients use the configured shared provider account. Provider-side usage, quotas, and billing therefore belong to that shared account; the Gateway does not provide per-user attribution.

所有客户端共用配置的 Provider 账号，因此用量、配额和费用均归属于这个共享账号；Gateway 不提供按用户区分的用量归因。

## Access control / 访问控制

Two different credentials exist and must not be confused:

系统中有两种完全不同的凭证，不能混为一谈：

- **Provider API Key** — used by the Gateway to call an upstream model service. It is expanded from `${ENV_VAR}` placeholders at startup and exists only on the Gateway host.
- **Gateway Access Token** — a shared secret that remote clients send as `X-Gateway-Token` when the Gateway listens beyond loopback. It protects access to the Gateway itself.

- **Provider API Key**：Gateway 访问上游模型服务所需的凭证。启动时从 `${ENV_VAR}` 展开，只存在于 Gateway 所在主机。
- **Gateway Access Token**：监听非回环地址时，远程客户端通过 `X-Gateway-Token` 发送的共享访问令牌，用于保护 Gateway 本身。

The default listener is `127.0.0.1:8787`. A non-loopback listener is rejected unless both `allow_remote: true` and `access_token_env` are set. The token is compared in constant time and removed before the request is forwarded. This is simple shared access control for a trusted network, not a user account system.

默认监听 `127.0.0.1:8787`。监听非回环地址时，必须同时启用 `allow_remote: true` 并配置 `access_token_env`，否则启动失败。令牌使用常量时间比较，并在转发前移除。它只是可信内网中的简单共享访问控制，不是用户账户系统。

## Request flow / 请求流程

1. `GET /healthz` returns `ok` without routing or token checks.
2. A client sends an HTTP request to `/{label}/{upstream-path}`, for example `/opencode-go/openai/v1/chat/completions`.
3. The Gateway resolves `label` against the static upstream configuration. An unknown label returns HTTP 404.
4. If a shared access token is configured, the request must carry the matching `X-Gateway-Token`; otherwise it returns HTTP 401.
5. The request body is limited to `limits.max_request_bytes` (16 MiB by default); oversized bodies return HTTP 413. At most `limits.max_concurrent` proxy requests run at once (16 by default); excess requests return HTTP 503 with `Retry-After: 1`.
6. The Gateway removes the label, joins the remaining path to the configured upstream base URL, removes `X-Gateway-Token` and `Proxy-Authorization`, and applies configured headers and server-side credentials.
7. The request body, query string, end-to-end headers, response status, and response body are forwarded transparently. SSE responses are streamed and flushed as they arrive rather than fully buffered.
8. `SIGTERM` triggers graceful shutdown with `limits.shutdown_timeout` (10 seconds by default).

1. `GET /healthz` 直接返回 `ok`，不经过路由和令牌校验。
2. 客户端向 `/{label}/{upstream-path}` 发送 HTTP 请求，例如 `/opencode-go/openai/v1/chat/completions`。
3. Gateway 根据静态上游配置解析 `label`；未知标签返回 HTTP 404。
4. 如果配置了共享访问令牌，请求必须携带匹配的 `X-Gateway-Token`，否则返回 HTTP 401。
5. 请求体受 `limits.max_request_bytes` 限制（默认 16 MiB），超限返回 HTTP 413；同时最多处理 `limits.max_concurrent` 个代理请求（默认 16），超出时返回 HTTP 503 和 `Retry-After: 1`。
6. Gateway 移除路由标签，将剩余路径拼接到上游 `base_url`，移除 `X-Gateway-Token` 与 `Proxy-Authorization`，再注入配置的请求头和服务端凭证。
7. 请求体、查询参数、端到端请求头、响应状态和响应体均透明转发；SSE 响应边到达边刷新，不会先缓存完整响应。
8. `SIGTERM` 触发优雅关闭，超时时间由 `limits.shutdown_timeout` 控制（默认 10 秒）。

For OpenCode Go, the client supplies a stable `X-Opencode-Session` value per conversation. The Gateway forwards it unchanged; it does not create or manage conversation sessions.

对于 OpenCode Go，客户端为每个会话提供稳定的 `X-Opencode-Session`，Gateway 原样转发，不负责创建或管理会话。

## Runtime boundaries / 运行边界

- One Go process (`cmd/ai-gateway`) owns configuration loading, the HTTP listener, routing, limits, forwarding, and shutdown.
- Upstreams are a static map built at startup. Requests cannot supply arbitrary target URLs.
- The gateway does not parse or modify JSON, prompts, model names, or provider-specific payloads.
- The gateway does not retry requests, balance traffic between replicas, or translate protocols.
- CORS is not enabled by default, and the built-in HTTP server does not terminate TLS.

- 单个 Go 进程（`cmd/ai-gateway`）负责配置加载、HTTP 监听、路由、限额、转发和关闭。
- 上游是启动时构建的静态映射，请求不能传入任意目标 URL。
- Gateway 不解析或修改 JSON、Prompt、模型名称或 Provider 专有请求内容。
- Gateway 不重试请求、不在多个实例间负载均衡，也不转换协议。
- 默认不启用 CORS，内置 HTTP 服务不负责 TLS 终止。

## Explicit non-goals / 明确不包含的内容

- No user accounts, OAuth, per-user API keys, roles, or multi-tenancy.
- No database, distributed session store, or user state.
- No Cloudflare Worker or public cloud deployment target in this architecture.
- No automatic retries, load balancing, or model protocol conversion.

- 不提供用户账户、OAuth、用户独立 API Key、角色或多租户。
- 不引入数据库、分布式会话或用户状态存储。
- 本架构不包含 Cloudflare Worker 或公网云端部署目标。
- 不提供自动重试、负载均衡或模型协议转换。

## Regenerating the diagram / 重新生成架构图

The Archify CLI is the installed Archify 3.2.0 skill (`node <archify-skill>/bin/archify.mjs`). From the repository root, run the complete delivery flow:

使用已安装的 Archify 3.2.0 Skill（`node <archify-skill>/bin/archify.mjs`），在仓库根目录执行完整交付流程：

```sh
node <archify-skill>/bin/archify.mjs finalize architecture \
  docs/architecture/ai-gateway.architecture.json \
  docs/architecture/ai-gateway.html \
  --repo-root . --quality showcase --json
```

`meta.output` in the JSON points to `docs/architecture/ai-gateway.html`. After the HTML passes finalize, regenerate the Markdown preview from the delivered page: open the HTML in a browser, choose **Export → SVG · auto**, and save it as `docs/architecture/ai-gateway.svg`. The SVG is the canonical Archify export with themes, styles, and fonts embedded.

JSON 中的 `meta.output` 指向 `docs/architecture/ai-gateway.html`。HTML 通过 finalize 后，从成品页面重新导出 Markdown 预览图：用浏览器打开 HTML，选择**导出 → SVG · 自动**，保存为 `docs/architecture/ai-gateway.svg`。该 SVG 是 Archify 的正式导出，已内嵌主题、样式和字体。

## Related documentation / 相关文档

- [Configuration / 配置说明](configuration.md)
- [Security policy / 安全策略](../SECURITY.md)
- [Release process / 发布流程](releasing.md)
