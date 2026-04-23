# AGENTS.md — AI 编码助手通用规范

> **适用对象**：所有参与本项目的 AI 编码工具  
> **项目**：智能 Agent 旅游助手（Trip Planner FM）  
> **最后更新**：2026-04-23

---

## 1. 项目上下文

本项目是基于 **多智能体协作** 的 Web 端智能旅游助手。编写代码前**必须先阅读**：

| 文档 | 内容 |
|------|------|
| `PRD.md` | 用户故事、功能清单、非功能需求 |
| `ARCHITECTURE.md` | 系统架构、目录结构、API 接口、Agent 状态机 |
| `TECH-STACK.md` | 所有技术选型与版本锁定 |
| `frontend-design.md` | 页面路由、组件拆分、响应式策略 |
| `PROJECT-SCOPE.md` | 功能边界、Mock 策略、验收场景 |

核心技术栈：

- **后端**：Python 3.11+ / FastAPI 0.136 / LangGraph 0.4 / DeepSeek-V3
- **前端**：Next.js 15 / React 19 / TypeScript 5 / shadcn/ui / Tailwind CSS 3.4
- **数据**：PostgreSQL 16 + pgvector 0.8 / Redis 7
- **工具链**：uv（Python）/ pnpm（Node）/ Docker Compose

---

## 2. 目录结构约定

严格遵循 `ARCHITECTURE.md` 定义的结构。新文件必须放入对应模块目录。

- 后端每个 Python 包必须包含 `__init__.py`
- 前端组件按功能域分子目录（`chat/`、`itinerary/`、`map/`），不要堆在 `components/` 根目录
- **禁止**在项目根目录创建源代码文件

---

## 3. 代码风格

### 3.1 Python（后端）

| 项目 | 规范 |
|------|------|
| 格式化 | **Ruff**（替代 black + isort + flake8） |
| 行宽 | 88 字符 |
| 引号 | 双引号 `"` |
| 类型注解 | **必须**。所有函数签名必须有完整的参数和返回值类型注解 |
| docstring | Google 风格，所有公开函数和类必须有 |
| Python 语法 | 3.11+：用 `dict` 非 `Dict`，用 `X | None` 非 `Optional[X]` |
| 异步 | 全部使用 `async/await`，禁止同步阻塞调用 |

```python
# ✅ 正确
def search_poi(city: str, keyword: str, top_k: int = 5) -> list[dict]:
    """搜索指定城市的 POI 信息。

    Args:
        city: 城市名称，如 "北京"。
        keyword: 搜索关键词。
        top_k: 返回结果数量上限。

    Returns:
        POI 信息列表。
    """
```

### 3.2 TypeScript（前端）

| 项目 | 规范 |
|------|------|
| 格式化 | ESLint（Next.js 内置）+ Prettier |
| 缩进 | 2 空格 |
| 引号 | 单引号 `'` |
| 类型 | **必须**。禁止 `any`，必须定义所有 props 和 state 类型 |
| 组件 | 函数式 + Hooks，禁止 Class 组件 |
| 导出 | 组件用命名导出，页面用默认导出 |

---

## 4. 命名约定

### Python

| 类型 | 格式 | 示例 |
|------|------|------|
| 文件 | `snake_case.py` | `mcp_client.py`, `rag_search.py` |
| 类 | `PascalCase` | `AgentState`, `ChatRequest` |
| 函数 | `snake_case` | `run_planner()`, `search_poi()` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_ITERATIONS = 10` |
| LangGraph 节点 | `snake_case` | `planner_node`, `tool_node` |

### TypeScript

| 类型 | 格式 | 示例 |
|------|------|------|
| 组件文件 | `PascalCase.tsx` | `ChatInput.tsx`, `DayPlanCard.tsx` |
| 非组件文件 | `camelCase.ts` | `chatStore.ts`, `useChat.ts` |
| 组件名 | `PascalCase` | `MessageList`, `ActivityItem` |
| Hook | `useCamelCase` | `useChat`, `useAMap` |
| 接口/类型 | `PascalCase` | `Itinerary`, `DayPlan`, `Activity` |

### Git 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `Feature/{模块}_{描述}` | `Feature/Agent_ReAct_Loop` |
| 修复 | `Fix/{模块}_{描述}` | `Fix/SSE_Stream_Disconnect` |
| 文档 | `Docs/{描述}` | `Docs/Agent_Rules` |
| 实验 | `Spike/{描述}` | `Spike/MCP_Amap_Integration` |

### Commit 格式（Conventional Commits）

```
<type>(<scope>): <subject>
```

**type**：`feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `style`  
**scope**：`agent` / `api` / `tools` / `rag` / `frontend` / `chat` / `map` / `itinerary` / `docker` / `sse`

示例：`feat(agent): 实现 ReAct 状态机循环`

---

## 5. 错误处理模式

### 后端降级策略（必须遵循，来自 PRD §5.4）

| 故障场景 | 处理方式 |
|----------|----------|
| DeepSeek API 不可用 | 返回友好提示，SSE 发送 `error` 事件 |
| MCP Server 连接失败 | **降级为直接 HTTP API 调用** |
| 高德 API 调用失败 | 跳过路线信息，标注"路线信息暂不可用" |
| RAG 检索无结果 | 基于 LLM 知识生成，标注"未经知识库验证" |
| Agent 迭代超限（>10） | 强制终止，返回当前已有结果 |

### 后端异常层次

```python
class TripPlannerError(Exception):
    """项目基础异常。"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class LLMServiceError(TripPlannerError):     # 503
class ToolCallError(TripPlannerError):       # 502
class RateLimitError(TripPlannerError):      # 429
```

### 日志规范

- 后端使用 `logging` 模块，**禁止 `print()`**
- 前端仅使用 `console.error`（错误场景）
- 日志必须包含上下文（tool 名、city、duration 等）

### 前端错误处理

- 所有 `fetch` 调用必须有 `try-catch`
- 按 HTTP 状态码分别处理：429（限流）、503（服务不可用）、其他
- 网络错误显示友好 Toast 提示

---

## 6. 测试要求

### 后端（pytest）

| 类型 | 要求 | 工具 |
|------|------|------|
| 工具单元测试 | 每个 Tool 必须有测试 | `pytest` |
| API 端点测试 | 所有 `/api/v1/*` 端点 | `pytest` + `httpx` |
| Agent 集成测试 | 覆盖 3 个 Demo 场景 | `pytest-asyncio` |
| RAG 质量评估 | 忠实度和相关性 | `ragas` |

测试命令：`cd backend && uv run pytest tests/ -v`  
文件命名：`test_{模块名}.py`

### 前端（Jest）

- 核心工具函数（`parseItinerary`、`sse.ts`）建议写单元测试
- 测试文件命名：`{文件名}.test.ts`，与源文件同目录

---

## 7. 禁止事项

### 绝对禁止

| # | 禁止事项 |
|---|----------|
| 1 | **硬编码 API Key**（必须从环境变量读取） |
| 2 | **提交 `.env` 文件**（只提交 `.env.example`） |
| 3 | **使用 `print()` 调试**（用 `logging`） |
| 4 | **使用 `any` 类型**（TypeScript 必须显式定义类型） |
| 5 | **跳过错误处理**（所有外部调用必须有 try-except/catch） |
| 6 | **前端直接调用后端模块**（仅通过 `/api/v1/*` 通信） |
| 7 | **Server Component 中使用浏览器 API**（地图/SSE/localStorage 需 `'use client'`） |
| 8 | **使用 `pip install` 或 `npm install`**（统一用 `uv` 和 `pnpm`） |
| 9 | **升级已锁定的核心依赖版本**（除非更新 `TECH-STACK.md`） |

### 避免

- 过长函数（>50 行）→ 拆分
- 深层嵌套（>3 层）→ 早返回
- Agent 节点直接操作数据库 → 通过 `services/` 或 `tools/` 层

---

## 8. 环境变量管理

后端通过 `app/config.py` 的 Pydantic Settings 加载，前端通过 `NEXT_PUBLIC_` 前缀暴露：

```bash
# 后端 (.env)
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
POSTGRES_HOST=localhost
REDIS_HOST=localhost
AMAP_API_KEY=xxx

# 前端 (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AMAP_KEY=xxx
NEXT_PUBLIC_AMAP_SECRET=xxx
```

---

## 9. SSE 流式协议约定

遵循 `ARCHITECTURE.md §5.2` 定义的事件类型：

| event | data 结构 | 说明 |
|-------|----------|------|
| `thinking` | `{"step": string}` | Agent 推理状态 |
| `tool_call` | `{"tool": string, "args": object}` | 工具调用开始 |
| `tool_result` | `{"tool": string, "result": object}` | 工具调用结果 |
| `content` | `{"text": string}` | 流式文本片段 |
| `itinerary` | `{"itinerary": Itinerary}` | 结构化行程 JSON |
| `error` | `{"message": string}` | 错误信息 |
| `done` | `{}` | 流结束 |

新增事件类型必须同时更新此文档和 `ARCHITECTURE.md`。
