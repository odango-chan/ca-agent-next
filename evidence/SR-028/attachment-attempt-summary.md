# GitHub attachment upload attempts (SR-028 evidence, Issue #96)

Date: 2026-11-27 (Asia/Shanghai)
Tool: gh 2.101.0 / curl (PAT from gh auth token, scope repo+workflow)

| # | Method | HTTP | Result |
|---|---|---|---|
| 1 | POST /repos/odango-chan/ca-agent-next/issues/96/comments (multipart file) | 400 | Problems parsing JSON — REST comment API 不接受文件附件 |
| 2 | POST https://api.github.com/user-attachments (multipart) | 404 | Not Found — 无该 API |
| 3 | POST https://api.github.com/repos/odango-chan/ca-agent-next/attachments (multipart) | 404 | Not Found — 无该 API |
| 4 | POST https://github.com/upload/policies/assets (PAT, web upload policy) | 404 | GitHub Web 端点不接受 PAT（需要浏览器 session cookie + CSRF） |
| 5 | POST https://github.com/upload/assets/<uuid> (PAT) | 404 | 同上 |

结论：GitHub 官方 REST API 不提供 Issue 附件上传能力；浏览器附件上传需要已登录的 Web session，本自动化环境无浏览器会话，无法完成真实 Issue 附件上传。已改用仓库证据分支托管 ZIP 并提供 raw 下载链接（见 Issue 评论），不声称该 ZIP 为 Issue 附件。
