# Codex 开发总览：智能 Agent 旅游助手

> **工具**：OpenAI Codex **桌面版** + GPT-5.5
> **目的**：指导你使用 Codex Desktop 按模块高效完成项目代码编写

---

## 1. 环境准备

### 1.1 Codex Desktop 安装

1. 从 [OpenAI 官网](https://openai.com) 下载 Codex Desktop（Windows 版）
2. 登录你的 OpenAI 账户（需开通 GPT-5.5 访问权限）
3. 打开 Codex Desktop，导入项目：`e:\code\Trip_planner_FM`

### 1.2 项目级配置（可选）

在项目根目录创建 `.codex/config.toml`，Codex Desktop 会自动读取：

```toml
# .codex/config.toml
model = "gpt-5.5"
approval_policy = "on-request"
```

---

## 2. AGENTS.md 已就绪

你的项目已有完善的 AGENTS.md 体系，**Codex Desktop 打开项目后会自动读取**：

| 文件 | 作用 |
|------|------|
| `.agents/AGENTS.md` | 通用编码规范（命名、风格、错误处理） |
| `.agents/rules/backend.rules.md` | Python 后端详细规则（FastAPI/LangGraph/Tool） |
| `.agents/rules/frontend.rules.md` | Next.js 前端详细规则 |

> Codex Desktop 支持 AGENTS.md 的层级加载，会从项目根目录开始向下搜索，自动应用最匹配的规则文件。你无需每次重复提供上下文。

---

## 3. GPT-5.5 模型选择

在 Codex Desktop 的 **Composer 界面**顶部有模型选择器，选择 `GPT-5.5`。

| 任务类型 | 推荐做法 | 说明 |
|----------|---------|------|
| 架构设计 / 复杂逻辑 | GPT-5.5，让它充分思考再输出 | Agent 状态机、SSE 流式、条件路由 |
| 常规模块代码 | GPT-5.5，正常对话即可 | CRUD、工具函数、组件 |
| 批量生成 / 数据 | GPT-5.5，一次给清晰模板 | Mock 数据、测试用例 |

> **技巧**：对于复杂任务，在 Prompt 中加上 "请先分析需求并输出实现计划，确认后再写代码"，让 GPT-5.5 先思考再执行。

---

## 4. Codex Desktop 工作模式

Codex Desktop 提供可视化的审批界面：

| 操作 | 说明 |
|------|------|
| **Review Diffs** | 查看 Agent 生成的代码变更差异，逐个审查后 Apply |
| **多 Agent 并行** | 可同时开多个 Agent 线程处理不同模块 |
| **项目记忆** | Desktop 版会跨会话保持项目上下文 |
| **文件树浏览** | GUI 中可直接浏览和选择项目文件作为上下文 |

### 推荐使用策略

| 模块类型 | 策略 |
|----------|------|
| 核心模块（Agent/API/SSE） | 逐步审查每个 Diff，手动 Apply |
| 日常组件（UI/工具函数） | 快速审查后批量 Apply |
| 初始化/数据生成 | 信任 Agent 输出，快速 Apply |

---

## 5. 开发阶段总览

按 STATUS.md 的 Phase 划分，共 7 个开发步骤：

| Step | 对应 Phase | 内容 | 文件 |
|------|-----------|------|------|
| Step 1 | Phase 1 | 项目初始化 | `step1_init.md` |
| Step 2 | Phase 2 | 后端核心（Agent + Tool + API） | `step2_backend_core.md` |
| Step 3 | Phase 3 | RAG 知识库 | `step3_rag.md` |
| Step 4 | Phase 4 | 前端骨架 | `step4_frontend.md` |
| Step 5 | Phase 5 | 前后端联调 | `step5_integration.md` |
| Step 6 | Phase 6 | 测试与优化 | `step6_testing.md` |
| Step 7 | Phase 7 | 论文与 Demo | `step7_final.md` |

---

## 6. 与 Codex Desktop 沟通的黄金模板

在 Composer 中输入任务时，使用 **四段式结构**：

```
1.【目标】明确要做什么
2.【上下文】用 @ 引用相关文件（Desktop 支持 @ 文件引用）
3.【约束】技术限制、规范要求
4.【完成标准】怎样算做完
```

**示例（直接粘贴到 Composer）**：

```
目标：实现 POST /api/v1/chat SSE 端点

上下文：
- 参考 @Docs/ARCHITECTURE.md 第 5.2 节的 SSE 事件格式
- 遵循 @.agents/rules/backend.rules.md 的路由规范

约束：
- 使用 FastAPI StreamingResponse
- 事件类型严格为 thinking/tool_call/tool_result/content/itinerary/error/done
- headers 包含 Cache-Control: no-cache, X-Accel-Buffering: no

完成标准：
- 能接收 ChatRequest 并返回 SSE 流
- 有错误处理，错误通过 error 事件发送
- 通过 ruff check
```

---

## 7. Desktop 版专属技巧

### 7.1 多 Agent 并行开发

Codex Desktop 支持同时运行多个 Agent 线程，推荐方案：

| Agent 线程 1 | Agent 线程 2 | Agent 线程 3 |
|-------------|-------------|-------------|
| 写后端 Tool 代码 | 写对应的单元测试 | 更新文档 |

### 7.2 使用 @ 引用提供上下文

在 Composer 中用 `@` 符号直接引用项目文件：
- `@Docs/ARCHITECTURE.md` — 让 Agent 参考架构设计
- `@.agents/rules/backend.rules.md` — 让 Agent 遵循编码规范
- `@backend/app/agent/state.py` — 让 Agent 基于已有代码继续开发

### 7.3 Interview Mode（复杂任务前）

对于复杂模块，先让 Agent 提问：

```
我需要你实现 LangGraph Agent 状态图。
在动手写代码之前，请先阅读 @Docs/ARCHITECTURE.md 第 6 节和
@.agents/rules/backend.rules.md 第 2 节，
然后列出你需要确认的问题。
```

### 7.4 Review 界面审查要点

审查 Agent 生成的代码时重点检查：
- ✅ 类型注解是否完整
- ✅ 错误处理是否覆盖
- ✅ 是否遵循 AGENTS.md 规范
- ✅ 是否有硬编码的 API Key
- ✅ 命名是否符合约定

---

## 8. 关键提示

1. **先 Plan 后 Code**：复杂任务先让 Agent 输出计划，Review 确认后再让它写代码
2. **单模块单线程**：每个模块在一个 Agent 线程中完成，避免上下文混乱
3. **验证优先**：每完成一个模块，让 Agent 运行测试或启动服务验证
4. **Git 分支**：每个 Step 在独立分支上开发，遵循 BRANCH-STRATEGY.md
5. **善用项目记忆**：Desktop 版会记住之前的会话，后续任务可引用之前的决策
