# Step 1：项目初始化（Phase 1）

> **模型**：GPT-5.5 | **推理强度**：`low` | **审批模式**：`full-auto`
> **分支**：`Feature/Init_Project_Structure`
> **预计工时**：1-2 天

---

## 1.1 后端初始化

### 任务 1.1.1：uv 项目初始化 + 安装依赖

**与 Codex 的对话**：

```
目标：初始化后端 Python 项目并安装所有核心依赖。

上下文：
- 项目根目录在 e:\code\Trip_planner_FM
- 后端目录在 backend/，已有 pyproject.toml（仅含工具配置）
- 技术栈参考 @Docs/TECH-STACK.md §1

操作：
1. 在 backend/ 目录下用 uv 初始化项目（如果尚未初始化）
2. 在 pyproject.toml 中补充 [project] 段（name, version, python requires >= 3.11）
3. 安装以下依赖：
   - 核心：fastapi==0.136.0, uvicorn
   - Agent：langgraph>=0.4.0,<0.5, langchain-core>=0.3.0,<0.4, langchain-openai>=0.3.0,<0.4
   - MCP：langchain-mcp-adapters==0.2.2
   - 数据库：sqlalchemy>=2.0, asyncpg, pgvector>=0.3.0,<0.4, redis>=5.0
   - Embedding：sentence-transformers>=3.0
   - HTTP：httpx
   - 开发：pytest, pytest-asyncio, ruff, mypy
4. 生成 uv.lock 锁定版本

完成标准：
- pyproject.toml 包含完整的 [project] + [project.dependencies] 段
- uv.lock 文件已生成
- `uv run python -c "import fastapi; print(fastapi.__version__)"` 输出 0.136.0
```

### 任务 1.1.2：创建后端目录结构 + `__init__.py`

```
目标：创建 ARCHITECTURE.md §2 定义的完整后端目录结构。

操作：
创建以下目录和空 __init__.py 文件：
- backend/app/__init__.py
- backend/app/api/__init__.py
- backend/app/agent/__init__.py
- backend/app/tools/__init__.py
- backend/app/rag/__init__.py
- backend/app/models/__init__.py
- backend/app/services/__init__.py
- backend/app/db/__init__.py
- backend/tests/（已存在则跳过）
- backend/data/（已存在则跳过）

每个 __init__.py 文件内容为空或仅包含模块 docstring。

完成标准：目录结构与 @Docs/ARCHITECTURE.md §2 一致。
```

### 任务 1.1.3：config.py + main.py 骨架

```
目标：创建 FastAPI 应用入口和 Pydantic Settings 配置。

上下文：
- 参考 @.agents/rules/backend.rules.md §1.4 和 §1.5
- 环境变量清单见 @Docs/TECH-STACK.md §5

操作：
1. 创建 backend/app/config.py：
   - 使用 pydantic-settings 的 BaseSettings
   - 包含所有环境变量：DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
     POSTGRES_HOST/PORT/DB/USER/PASSWORD, REDIS_HOST/PORT, AMAP_API_KEY
   - 添加 model_config 设置 env_file=".env"

2. 创建 backend/app/main.py：
   - FastAPI 实例，带 lifespan 管理
   - CORS 中间件，允许 localhost:3000
   - 挂载路由（暂时只有 health）
   - 参考 backend.rules.md §1.5 和 §5.1 的 lifespan 模式

3. 创建 backend/app/api/health.py：
   - GET /api/v1/health 端点
   - 返回 HealthResponse（status + services dict）

4. 创建 backend/app/api/router.py：
   - 统一注册所有路由

约束：
- 遵循 backend.rules.md 的依赖注入模式
- 所有函数必须有类型注解和 docstring
- 禁止 print()，使用 logging

完成标准：
- `cd backend && uv run uvicorn app.main:app --port 8000` 能启动
- 访问 http://localhost:8000/api/v1/health 返回 JSON
- `uv run ruff check app/` 无错误
```

---

## 1.2 数据库初始化

### 任务 1.2.1：完善 init.sql 和 connection.py

```
目标：完善数据库建表脚本和 Python 连接池。

上下文：
- backend/db/init.sql 已存在，参考 @Docs/ARCHITECTURE.md §4.2 的建表 SQL
- 连接管理参考 @.agents/rules/backend.rules.md §5.1

操作：
1. 确认 backend/db/init.sql 包含完整的 knowledge_chunks 表定义
   （含 pgvector 扩展启用、向量索引、城市+类别联合索引）

2. 创建 backend/app/db/connection.py：
   - 使用 SQLAlchemy 2.0 async 模式 + asyncpg
   - create_async_engine + async_sessionmaker
   - init_db() 和 close_db() 函数
   - 用于 FastAPI lifespan

3. 创建 backend/app/models/db_models.py：
   - knowledge_chunks 的 SQLAlchemy ORM 模型
   - 使用 pgvector 的 Vector 类型

完成标准：
- Docker 启动 PostgreSQL 后，init.sql 自动执行建表
- connection.py 能连接数据库
```

---

## 1.3 前端初始化

### 任务 1.3.1：创建 Next.js 项目

```
目标：在 frontend/ 目录初始化 Next.js 15 项目。

上下文：参考 @Docs/TECH-STACK.md §2 和 §3.1

操作：
1. 在项目根目录执行：
   pnpm create next-app frontend --typescript --app --tailwind --eslint --src-dir --use-pnpm

2. 安装额外依赖：
   cd frontend && pnpm add zustand react-markdown @amap/amap-jsapi-loader lucide-react

3. 初始化 shadcn/ui：
   pnpm dlx shadcn@latest init

4. 安装所需 shadcn 组件（参考 @Docs/frontend-design.md §4.2）：
   pnpm dlx shadcn@latest add button textarea card tabs badge dialog scroll-area skeleton tooltip avatar separator

5. 创建前端目录结构（参考 @Docs/frontend-design.md §7）：
   - src/components/chat/
   - src/components/itinerary/
   - src/components/map/
   - src/components/layout/
   - src/components/landing/
   - src/hooks/
   - src/store/
   - src/lib/
   - src/types/
   - src/mock/

6. 创建 .env.local 模板

完成标准：
- `cd frontend && pnpm dev` 能启动
- 访问 http://localhost:3000 显示默认页面
- shadcn/ui 组件可正常导入
```

### 任务 1.3.2：TypeScript 类型定义

```
目标：定义所有核心 TypeScript 类型。

上下文：
- 数据实体关系见 @Docs/PRD.md §4.2
- SSE 事件类型见 @Docs/ARCHITECTURE.md §5.2

操作：创建以下类型文件
1. src/types/message.ts — 消息类型（UserMessage, AssistantMessage, SSEEvent 等）
2. src/types/itinerary.ts — 行程数据结构（Itinerary, DayPlan, Activity, Transport 等）
3. src/types/map.ts — 地图相关类型（POIMarker, RoutePath 等）

约束：
- 禁止使用 any
- 所有类型使用 interface 或 type，不用 class
- SSE 事件类型必须与后端 ARCHITECTURE.md §5.2 完全对应

完成标准：类型定义完整，无 TypeScript 编译错误。
```

---

## 1.4 Docker Compose 验证

```
目标：验证 Docker Compose 能正常启动 PostgreSQL 和 Redis。

操作：
1. 确认 docker-compose.yml 中 postgres 和 redis 服务配置正确
2. 创建 .env 文件（从 .env.example 复制并填写密码）
3. 执行 docker-compose up -d postgres redis
4. 验证：
   - PostgreSQL: psql 连接成功，knowledge_chunks 表已创建
   - Redis: redis-cli ping 返回 PONG

完成标准：两个基础服务稳定运行。
```

---

## 本步骤检查清单

- [ ] backend/ 依赖安装完成，uv.lock 生成
- [ ] 后端目录结构与 ARCHITECTURE.md 一致
- [ ] FastAPI 启动正常，/api/v1/health 可访问
- [ ] PostgreSQL + Redis Docker 容器运行正常
- [ ] 前端 Next.js 启动正常
- [ ] TypeScript 类型定义完整
- [ ] `uv run ruff check app/` 无错误
- [ ] Git commit: `chore(init): 项目初始化，后端骨架+前端脚手架+基础服务`
