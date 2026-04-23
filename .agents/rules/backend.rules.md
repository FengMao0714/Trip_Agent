---
trigger: always_on
---

# Python 后端编码规则

> **激活方式**：`glob: *.py`  
> **适用范围**：`backend/` 目录下所有 Python 文件  
> **前置依赖**：先阅读 `AGENTS.md` 中的通用规范

---

## 1. FastAPI 规范

### 1.1 路由定义

- 所有路由在 `app/api/` 目录下定义，由 `router.py` 统一注册
- 路由前缀统一为 `/api/v1/`
- 使用 `APIRouter` 分组，每个文件一个 Router

```python
# app/api/chat.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
) -> StreamingResponse:
    """对话接口，返回 SSE 流。"""
    ...
```

### 1.2 请求/响应模型

所有 API 的请求体和响应体必须使用 Pydantic V2 模型，定义在 `app/models/schemas.py`：

```python
# app/models/schemas.py
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """对话请求。"""
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: str = Field(..., description="会话 ID (UUID)")

class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str
    services: dict[str, str]
```

**规则**：
- 所有字段使用 `Field()` 添加 description 和校验
- 嵌套结构不要用 `dict`，定义独立模型类
- 模型类名以用途结尾：`XxxRequest`、`XxxResponse`

### 1.3 SSE 流式响应

```python
# app/api/chat.py
from fastapi.responses import StreamingResponse

async def sse_generator(session_id: str, message: str):
    """SSE 事件生成器。"""
    try:
        async for event in agent_graph.astream(state):
            event_type, data = format_sse_event(event)
            yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"
    except LLMServiceError as e:
        yield f"event: error\ndata: {json.dumps({'message': e.message})}\n\n"

@router.post("/chat")
async def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        sse_generator(request.session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

**SSE 事件格式**必须遵循 ARCHITECTURE.md §5.2：`thinking` / `tool_call` / `tool_result` / `content` / `itinerary` / `error` / `done`

### 1.4 依赖注入

- 数据库会话、Redis 连接、Settings 等通过 FastAPI `Depends()` 注入
- 禁止在路由函数中直接 import 全局连接对象

```python
# ✅ 正确
from app.config import Settings

async def get_settings() -> Settings:
    return Settings()

@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    ...

# ❌ 错误
from app.config import settings  # 直接导入全局单例
```

### 1.5 中间件与 CORS

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- 开发环境允许 `localhost:3000`
- 生产环境收紧为特定域名
- 在 `app/main.py` 中统一配置，不要分散到各 Router

---

## 2. LangGraph 规范

### 2.1 状态定义

`AgentState` 定义在 `app/agent/state.py`，必须使用 `TypedDict` + `Annotated`：

```python
# app/agent/state.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # 对话历史（自动追加）
    user_profile: dict | None               # 用户画像
    itinerary: dict | None                  # 当前行程 JSON
    iteration_count: int                    # ReAct 迭代计数
    should_end: bool                        # 是否终止循环
```

**规则**：
- 新增状态字段必须同时更新 `ARCHITECTURE.md §6.1`
- 使用 `Annotated[list, add_messages]` 自动管理消息历史
- `iteration_count` 上限为 10（`MAX_ITERATIONS`），超过触发 `fallback_node`

### 2.2 状态图构建

```python
# app/agent/graph.py
from langgraph.graph import StateGraph, END

async def build_graph() -> CompiledGraph:
    """构建并编译 Agent 状态图。"""
    graph = StateGraph(AgentState)

    # 注册节点
    graph.add_node("planner_node", run_planner)
    graph.add_node("tool_node", ToolNode(all_tools))
    graph.add_node("response_node", generate_response)
    graph.add_node("fallback_node", handle_fallback)

    # 设置入口
    graph.set_entry_point("planner_node")

    # 条件路由
    graph.add_conditional_edges("planner_node", route_decision)

    # 固定边
    graph.add_edge("tool_node", "planner_node")
    graph.add_edge("response_node", END)
    graph.add_edge("fallback_node", "response_node")

    return graph.compile()
```

**节点命名固定为**：`planner_node` / `tool_node` / `response_node` / `fallback_node`。不要随意更改。

### 2.3 条件路由逻辑

```python
# app/agent/nodes.py
def route_decision(state: AgentState) -> str:
    """根据 Agent 状态决定下一步路由。"""
    last_message = state["messages"][-1]

    if state["iteration_count"] >= MAX_ITERATIONS:
        return "fallback_node"

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node"

    return "response_node"
```

### 2.4 节点函数模板

所有节点函数必须：
- 接收 `AgentState` 作为参数
- 返回 `dict`（状态更新 patch）
- 包含错误处理

```python
async def run_planner(state: AgentState) -> dict:
    """Planner 节点：调用 LLM 进行 ReAct 推理。"""
    try:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {
            "messages": [response],
            "iteration_count": state["iteration_count"] + 1,
        }
    except Exception as e:
        logger.error("Planner 节点执行失败", extra={"error": str(e)})
        return {
            "messages": [AIMessage(content="抱歉，规划过程中遇到了问题，请重试。")],
            "should_end": True,
        }
```

### 2.5 流式输出

使用 `graph.astream()` 或 `graph.astream_events()` 获取流式输出，不要使用 `graph.invoke()`：

```python
async for event in compiled_graph.astream(initial_state):
    # 处理每个节点的输出事件
    ...
```

---

## 3. Tool 类开发模板

### 3.1 工具分类

| 工具 | 文件 | 优先调用方式 | 降级方式 |
|------|------|-------------|----------|
| RAG 检索 | `tools/rag_search.py` | 直接调用 pgvector | 无降级 |
| POI 搜索 | `tools/poi_search.py` | MCP → 高德 API | 直接 HTTP 调用高德 |
| 路线规划 | `tools/route_plan.py` | MCP → 高德 API | 直接 HTTP 调用高德 |
| 天气查询 | `tools/weather.py` | MCP → 高德 API | 直接 HTTP 调用高德 |

### 3.2 LangChain Tool 定义模板

```python
# app/tools/poi_search.py
"""高德 POI 搜索工具（含 MCP 降级方案）。"""

import logging
from typing import Any

import httpx
from langchain_core.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ===== 降级方案：直接 HTTP 调用 =====

async def _fallback_poi_search(city: str, keyword: str, top_k: int = 5) -> list[dict]:
    """直接调用高德 REST API（MCP 不可用时的降级方案）。"""
    async with httpx.AsyncClient(timeout=3.0) as client:
        response = await client.get(
            "https://restapi.amap.com/v3/place/text",
            params={
                "key": settings.AMAP_API_KEY,
                "keywords": keyword,
                "city": city,
                "offset": top_k,
                "output": "json",
            },
        )
        response.raise_for_status()
        data = response.json()

    if data.get("status") != "1":
        raise ToolCallError("poi_search", f"高德 API 返回错误: {data.get('info')}")

    return [
        {
            "name": poi["name"],
            "address": poi.get("address", ""),
            "lng": float(poi["location"].split(",")[0]),
            "lat": float(poi["location"].split(",")[1]),
            "type": poi.get("type", ""),
            "rating": poi.get("biz_ext", {}).get("rating", ""),
        }
        for poi in data.get("pois", [])[:top_k]
    ]


# ===== 对外暴露的 LangChain Tool =====

@tool
async def poi_search(city: str, keyword: str, top_k: int = 5) -> list[dict]:
    """搜索指定城市的兴趣点（景点、餐厅、酒店等）。

    Args:
        city: 目标城市名称，如 "北京"、"上海"、"成都"。
        keyword: 搜索关键词，如 "历史文化景点"、"川菜餐厅"。
        top_k: 返回结果数量上限，默认 5。

    Returns:
        POI 列表，每项包含 name, address, lng, lat, type, rating。
    """
    logger.info("POI 搜索", extra={"city": city, "keyword": keyword})
    try:
        # 优先尝试 MCP 调用（由 MCP Client 管理）
        # 如果 MCP 可用，此工具会被 MCP 版本替代
        # 以下为降级方案
        return await _fallback_poi_search(city, keyword, top_k)
    except Exception as e:
        logger.error("POI 搜索失败", extra={"error": str(e)})
        return [{"error": f"POI 搜索暂不可用: {str(e)}"}]
```

### 3.3 Tool 开发检查清单

每个新 Tool 必须满足：

- [ ] 使用 `@tool` 装饰器，docstring 清晰描述功能和参数
- [ ] docstring 中的 Args 描述准确（LLM 依据此信息决定调用）
- [ ] 实现 `async` 异步版本
- [ ] 包含 try-except 错误处理，失败时返回错误信息而非抛异常
- [ ] 使用 `logging` 记录调用日志（包含参数和耗时）
- [ ] 外部 API 调用设置 `timeout`（上限 3 秒，参考 PRD §5.1）
- [ ] MCP 工具有对应的 HTTP 直接调用降级方案
- [ ] 在 `tests/test_tools.py` 中有对应的单元测试

### 3.4 MCP 客户端配置

```python
# app/tools/mcp_client.py
from langchain_mcp_adapters.client import MultiServerMCPClient

async def get_mcp_tools() -> list:
    """获取 MCP 工具列表。连接失败时返回空列表（触发降级）。"""
    try:
        client = MultiServerMCPClient({
            "amap": {
                "command": "npx",
                "args": ["-y", "@amap/amap-mcp-server"],
                "env": {"AMAP_API_KEY": settings.AMAP_API_KEY},
            }
        })
        return await client.get_tools()
    except Exception as e:
        logger.warning("MCP 连接失败，将使用降级方案", extra={"error": str(e)})
        return []
```

### 3.5 工具注册

```python
# app/agent/graph.py
async def build_graph():
    mcp_tools = await get_mcp_tools()

    # 如果 MCP 可用，使用 MCP 工具；否则使用降级工具
    if mcp_tools:
        all_tools = mcp_tools + [rag_search_tool]
    else:
        all_tools = [poi_search, route_plan, weather_query, rag_search_tool]

    llm_with_tools = llm.bind_tools(all_tools)
    ...
```

---

## 4. RAG 模块规范

### 4.1 Embedding

- 使用 `bge-large-zh-v1.5`，本地加载，1024 维向量
- 模型加载放在 `app/rag/embeddings.py`，应用启动时加载一次

### 4.2 知识库入库

- 入库脚本：`app/rag/ingest.py`
- 数据源格式：`backend/data/{city}.json`
- 切片策略：每个景点/餐厅/住宿为一个 chunk

```python
# 入库数据结构示例
{
    "city": "北京",
    "category": "景点",
    "title": "故宫博物院",
    "content": "故宫博物院位于北京市中心...",
    "metadata": {
        "address": "北京市东城区景山前街4号",
        "lng": 116.397,
        "lat": 39.918,
        "rating": 4.8,
        "price_range": "60元/人",
        "tags": ["历史", "世界遗产"]
    }
}
```

### 4.3 检索工具

```python
@tool
async def rag_search(query: str, city: str, top_k: int = 5) -> list[dict]:
    """从旅游知识库中检索相关信息。

    Args:
        query: 检索查询，如 "北京有哪些历史文化景点"。
        city: 限定城市范围。
        top_k: 返回结果数量。

    Returns:
        知识片段列表。
    """
```

---

## 5. 数据库规范

### 5.1 连接管理

- 使用 `asyncpg` + `SQLAlchemy 2.0` async 模式
- 连接池在 `app/db/connection.py` 中初始化
- 使用 FastAPI lifespan 管理连接池生命周期

```python
# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化连接池
    await init_db()
    await init_redis()
    yield
    # 关闭：释放连接
    await close_db()
    await close_redis()

app = FastAPI(lifespan=lifespan)
```

### 5.2 Redis 使用

Key 格式必须遵循 TECH-STACK.md §1.4 定义：

| 场景 | Key 格式 | TTL |
|------|----------|-----|
| POI 缓存 | `poi:{city}:{keyword}` | 24h |
| 路线缓存 | `route:{origin}:{dest}:{mode}` | 24h |
| 天气缓存 | `weather:{city}` | 6h |
| 会话上下文 | `session:{sessionId}` | 2h |

---

## 6. Prompt 管理

- 所有 System Prompt 定义在 `app/agent/prompts.py`
- 使用 Python 多行字符串，支持变量替换
- Prompt 修改必须在 commit message 中说明改动原因

```python
# app/agent/prompts.py
SYSTEM_PROMPT = """你是一个专业的旅行规划助手。你的任务是根据用户的需求，
生成详细的、按天排列的旅行行程方案。

## 你的能力
- 搜索真实的景点、餐厅、酒店信息（poi_search 工具）
- 计算景点间的真实距离和交通耗时（route_plan 工具）
- 查询目的地天气预报（weather_query 工具）
- 检索旅游知识库获取详细介绍（rag_search 工具）

## 输出要求
- 行程必须按天（Day 1, Day 2...）和时段（上午/下午/晚上）组织
- 每个活动包含：地点名称、活动描述、预计费用、交通方式
- 总费用不超过用户预算的 110%
- 景点间距离和交通耗时必须基于工具返回的真实数据

## 约束
- 用户画像: {user_profile}
- 已有行程: {current_itinerary}
"""
```

---

## 7. 启动与调试

```bash
# 开发模式启动后端
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 运行测试
cd backend && uv run pytest tests/ -v

# 运行 Ruff 检查
cd backend && uv run ruff check app/
cd backend && uv run ruff format app/

# 知识库入库
cd backend && uv run python -m app.rag.ingest
```
