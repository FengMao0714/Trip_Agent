# 技术栈锁定清单：智能 Agent 旅游助手

> **版本**：v1.1 | **日期**：2026-04-27 | **状态**：已锁定

---

## 1. 后端技术栈

### 1.1 核心框架

| 组件 | 选型 | 锁定版本 | Python 要求 | 说明 |
|------|------|----------|-------------|------|
| **Web 框架** | FastAPI | `0.136.0` | >= 3.9 | 异步框架，原生支持 SSE（StreamingResponse） |
| **ASGI 服务器** | Uvicorn | `0.34.x` | — | FastAPI 官方推荐，生产环境加 `--workers` |
| **数据校验** | Pydantic | `2.x`（FastAPI 内置） | — | V2 性能大幅提升，与 FastAPI 0.100+ 绑定 |

### 1.2 Agent 框架

| 组件 | 选型 | 锁定版本 | 说明 |
|------|------|----------|------|
| **Agent 编排** | LangGraph | `1.1.x` | 状态机管理，支持 ReAct 循环、条件分支、检查点 |
| **基础组件** | LangChain Core | `1.x` | 提供 ChatModel、Tool、PromptTemplate 等基础抽象 |
| **MCP 适配** | langchain-mcp-adapters | `0.2.2` | MCP 工具转 LangChain Tool 的轻量包装器（要求 langchain-core>=1.0.0） |
| **OpenAI 兼容** | langchain-openai | `1.x` | 通过 OpenAI 兼容接口调用 DeepSeek |

### 1.3 LLM 接入

| 项目 | 详情 |
|------|------|
| **模型** | DeepSeek-V3（模型名：`deepseek-chat`） |
| **API 端点** | `https://api.deepseek.com`（OpenAI 兼容格式） |
| **接入方式** | 通过 `langchain-openai` 的 `ChatOpenAI`，设置 `base_url` 指向 DeepSeek |
| **认证** | API Key，存储在环境变量 `DEEPSEEK_API_KEY` |
| **流式输出** | 支持，`stream=True` |
| **定价** | 输入 ~1 元/百万 token，输出 ~2 元/百万 token（毕设预算约 50-100 元） |

**接入代码模式**：
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.environ["DEEPSEEK_API_KEY"],
    streaming=True,
)
```

### 1.4 数据存储

| 组件 | 选型 | 锁定版本 | 用途 |
|------|------|----------|------|
| **关系 + 向量数据库** | PostgreSQL + pgvector | PG `16` + pgvector `0.8.x` | 旅游知识向量存储 + Hybrid Search |
| **缓存** | Redis | `7.x` | 高频 POI/路线查询缓存，会话上下文暂存 |
| **Python ORM** | SQLAlchemy | `2.0.x` | 操作 PostgreSQL（可选，也可用原生 asyncpg） |
| **向量操作** | pgvector-python | `0.3.x` | SQLAlchemy 集成 pgvector 的 Python 库 |

**Redis 使用场景明细**：

| 场景 | Key 格式 | Value | TTL |
|------|----------|-------|-----|
| POI 搜索缓存 | `poi:{city}:{keyword}` | JSON 结果 | 24h |
| 路线规划缓存 | `route:{origin}:{dest}:{mode}` | JSON 结果 | 24h |
| 天气缓存 | `weather:{city}` | JSON 结果 | 6h |
| 会话上下文 | `session:{sessionId}` | 对话历史 JSON | 2h |

### 1.5 Embedding 模型

| 方案 | 模型 | 部署方式 | 成本 | 推荐度 |
|------|------|----------|------|--------|
| **方案 A（推荐）** | bge-large-zh-v1.5 | 本地（sentence-transformers） | 免费 | 首选，中文效果好 |
| 方案 B | DeepSeek Embedding | API 调用 | 按量付费 | 备选 |
| 方案 C | text-embedding-3-small | OpenAI API | 按量付费 | 备选 |

---

## 2. 前端技术栈

### 2.1 核心框架

| 组件 | 选型 | 锁定版本 | 说明 |
|------|------|----------|------|
| **框架** | Next.js | `15.x`（非 16，见下方说明） | App Router，React Server Components |
| **运行时** | React | `19.x` | Next.js 15 绑定 React 19 |
| **语言** | TypeScript | `5.x` | 全项目强类型 |
| **路由模式** | App Router | — | `app/` 目录结构，Server Components 默认 |

> [!WARNING]
> **为什么选 Next.js 15 而非最新的 16？**
> - Next.js 16 刚发布不久，shadcn/ui 和部分生态插件可能存在兼容性滞后
> - Next.js 15 是当前最稳定的 LTS 选择，社区资源和问题排查更丰富
> - 毕设项目优先求稳，不追最新版

### 2.2 UI 层

| 组件 | 选型 | 版本 | 说明 |
|------|------|------|------|
| **组件库** | shadcn/ui | `latest`（CLI 安装） | 基于 Radix UI，按需复制源码到项目 |
| **CSS 框架** | Tailwind CSS | `3.4.x` | utility-first，shadcn/ui 默认搭配 |
| **图标** | Lucide React | `0.470.x` | shadcn/ui 默认图标库 |
| **字体** | Inter + 系统中文 | — | 通过 `next/font/google` 加载 |
| **Markdown 渲染** | react-markdown | `9.x` | 渲染 Agent 回复中的 Markdown |
| **状态管理** | Zustand | `5.x` | 轻量级，管理会话/消息/行程状态 |

### 2.3 地图方案

| 项目 | 详情 |
|------|------|
| **选型** | 高德地图 JS API 2.0 |
| **加载方式** | `@amap/amap-jsapi-loader`（npm 包） |
| **SSR 处理** | 必须用 `next/dynamic` + `{ ssr: false }` 动态导入 |
| **客户端标记** | 地图组件文件顶部加 `'use client'` |
| **安全密钥** | `window._AMapSecurityConfig` 在 `useEffect` 中设置 |
| **环境变量** | `NEXT_PUBLIC_AMAP_KEY` + `NEXT_PUBLIC_AMAP_SECRET` |

### 2.4 流式渲染方案：SSE

| 维度 | SSE（Server-Sent Events） | WebSocket |
|------|--------------------------|-----------|
| 方向 | 服务端 → 客户端（单向） | 双向 |
| 复杂度 | 低（原生 EventSource 或 fetch） | 高（需连接管理） |
| 与 FastAPI 集成 | `StreamingResponse` 原生支持 | 需 `websockets` 库 |
| 断线重连 | EventSource 自带重连 | 需手动实现 |
| 适用场景 | 流式文本输出（正好匹配需求） | 实时双向通信 |
| **结论** | **选择 SSE** | 不选 |

**前端 SSE 接收方式**：使用 `fetch` + `ReadableStream`（而非 `EventSource`），原因是需要发送 POST 请求携带 JSON body。

```typescript
// 伪代码示意
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ message, sessionId }),
  headers: { 'Content-Type': 'application/json' },
});
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  // 解析 SSE 事件，更新 UI
}
```

---

## 3. 工具链

### 3.1 包管理

| 生态 | 工具 | 版本 | 说明 |
|------|------|------|------|
| **Python** | uv | `0.7.x` | 替代 pip + venv，速度快 10-100x |
| **Node.js** | pnpm | `9.x` | 替代 npm，磁盘空间优化、安装速度快 |

**Python 依赖管理**：
```bash
# 初始化项目
uv init backend
cd backend
uv add fastapi uvicorn langchain-core langchain-openai langgraph
uv add langchain-mcp-adapters pgvector sqlalchemy asyncpg redis
uv add sentence-transformers  # Embedding 模型
```

**Node.js 依赖管理**：
```bash
# 初始化项目
pnpm create next-app frontend --typescript --app --tailwind --eslint
cd frontend
pnpm dlx shadcn@latest init
pnpm add zustand react-markdown @amap/amap-jsapi-loader
```

### 3.2 代码质量

| 工具 | 生态 | 版本 | 用途 |
|------|------|------|------|
| **Ruff** | Python | `0.11.x` | Lint + Format（替代 flake8 + black + isort） |
| **ESLint** | Node.js | `9.x` | JS/TS 代码检查（Next.js 内置） |
| **Prettier** | Node.js | `3.x` | 代码格式化（可选，与 ESLint 配合） |
| **mypy** | Python | `1.x` | 类型检查（可选，建议至少对核心模块启用） |

### 3.3 测试

| 工具 | 生态 | 版本 | 用途 |
|------|------|------|------|
| **pytest** | Python | `8.x` | 后端单元测试 + Agent 集成测试 |
| **pytest-asyncio** | Python | `0.24.x` | 异步测试支持 |
| **httpx** | Python | `0.28.x` | FastAPI TestClient 异步测试 |
| **Jest** | Node.js | `29.x` | 前端组件测试（Next.js 内置支持） |
| **RAGAS** | Python | `0.2.x` | RAG 回答质量评估（忠实度/相关性） |

### 3.4 部署

| 组件 | 部署方式 | 端口 |
|------|----------|------|
| **Next.js 前端** | Docker / Vercel | 3000 |
| **FastAPI 后端** | Docker | 8000 |
| **PostgreSQL** | Docker | 5432 |
| **Redis** | Docker | 6379 |
| **MCP Server（高德）** | Docker / 本地进程 | stdio |
| **编排** | Docker Compose | — |

---

## 4. 版本兼容性矩阵

### 4.1 后端兼容性

```
Python 3.11+
  ├── FastAPI 0.136.0 ─── Pydantic 2.x ✅
  ├── LangGraph 1.1.x
  │     └── LangChain Core 1.x ✅
  │     └── langchain-openai 1.x ✅
  │     └── langchain-mcp-adapters 0.2.2 ✅
  ├── SQLAlchemy 2.0.x + asyncpg ✅
  ├── pgvector-python 0.3.x ── PostgreSQL 16 + pgvector 0.8.x ✅
  ├── redis-py 5.x ── Redis 7.x ✅
  └── sentence-transformers 3.x ── PyTorch 2.x ✅
```

### 4.2 前端兼容性

```
Node.js 20 LTS
  ├── Next.js 15.x ── React 19.x ✅
  ├── Tailwind CSS 3.4.x ✅
  ├── shadcn/ui (latest CLI) ── Radix UI ✅
  ├── Zustand 5.x ── React 19.x ✅
  ├── react-markdown 9.x ── React 19.x ✅
  └── @amap/amap-jsapi-loader ── 需 dynamic import + ssr:false ✅
```

### 4.3 已知风险与注意事项

| 风险项 | 严重程度 | 描述 | 缓解措施 |
|--------|----------|------|----------|
| **LangGraph 版本迭代快** | 中 | API 可能在小版本间变化 | 锁定 `1.1.x`，用 `uv.lock` 固定精确版本 |
| **langchain-mcp-adapters 较新** | 中 | 社区案例少，遇到 Bug 难排查 | 准备直接 API 调用的降级方案 |
| **sentence-transformers 依赖 PyTorch** | 低 | PyTorch 体积大（~2GB），Docker 镜像体积膨胀 | 使用 `torch` CPU-only 版本减小体积 |
| **高德地图 SSR 不兼容** | 低 | 高德 JS SDK 依赖 `window` 对象 | 已确认用 `dynamic + ssr:false` 解决 |
| **Tailwind CSS 3 vs 4** | 低 | Tailwind v4 已发布但 shadcn/ui 默认仍是 v3 | 保持 v3，等 shadcn/ui 官方适配 v4 后再升级 |
| **React 19 Server Components** | 低 | 地图/对话等需 `'use client'` 标记 | 明确区分 Server/Client 组件边界 |

---

## 5. 环境变量汇总

```bash
# ===== 后端 (.env) =====

# LLM
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 数据库
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trip_planner
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 高德地图
AMAP_API_KEY=xxxxxxxxxxxxxxxx

# ===== 前端 (.env.local) =====

# 后端地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# 高德地图（前端用 NEXT_PUBLIC_ 前缀才能暴露给浏览器）
NEXT_PUBLIC_AMAP_KEY=xxxxxxxxxxxxxxxx
NEXT_PUBLIC_AMAP_SECRET=xxxxxxxxxxxxxxxx
```

---

## 6. Docker Compose 服务编排

```yaml
# docker-compose.yml（结构预览）
services:
  frontend:       # Next.js，端口 3000
  backend:        # FastAPI，端口 8000
  postgres:       # PostgreSQL 16 + pgvector，端口 5432
  redis:          # Redis 7，端口 6379
```

| 服务 | 基础镜像 | 说明 |
|------|----------|------|
| `frontend` | `node:20-alpine` | 构建 Next.js 生产包 |
| `backend` | `python:3.11-slim` | 安装 uv 依赖 + 启动 uvicorn |
| `postgres` | `pgvector/pgvector:pg16` | 官方镜像，已包含 pgvector 扩展 |
| `redis` | `redis:7-alpine` | 轻量 Alpine 镜像 |

---

## 7. 最终技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                     前端 (Next.js 15)                │
│  React 19 + shadcn/ui + Tailwind CSS 3.4            │
│  Zustand (状态) + 高德 JS API 2.0 (地图)             │
│  fetch + ReadableStream (SSE 流式接收)               │
├─────────────────────────────────────────────────────┤
│                        SSE                           │
├─────────────────────────────────────────────────────┤
│                   后端 (FastAPI 0.136)                │
│  LangGraph 1.1 (Agent 编排)                          │
│  LangChain Core 1.x (基础组件)                       │
│  langchain-mcp-adapters 0.2 (MCP 工具适配)           │
│  DeepSeek-V3 (LLM，OpenAI 兼容接口)                  │
├──────────────┬──────────────┬────────────────────────┤
│  PostgreSQL  │    Redis     │    MCP Server          │
│  16 +        │    7.x       │    (高德地图/天气)      │
│  pgvector    │    (缓存)    │    (stdio 通信)        │
│  0.8 (RAG)   │              │                        │
├──────────────┴──────────────┴────────────────────────┤
│                    工具链                             │
│  uv (Python) + pnpm (Node) + Ruff + ESLint           │
│  pytest + Jest + RAGAS + Docker Compose              │
└─────────────────────────────────────────────────────┘
```
