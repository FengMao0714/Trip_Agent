# Step 2：后端核心 — Agent + Tool + API（Phase 2）

> **模型**：GPT-5.5 | **推理强度**：`high` ~ `xhigh` | **审批模式**：`suggest`
> **分支**：`Feature/Agent_ReAct_Loop`、`Spike/MCP_Amap_Integration`
> **预计工时**：5-7 天

> [!WARNING]
> 这是全项目最关键的阶段！Task 2.1 和 2.2 是技术验证 Spike，失败需立即调整方案。
> 建议使用 **Suggest 模式**，每步都审查 Codex 的输出。

---

## 2.1 Spike：DeepSeek + LangGraph 最小 Agent

**分支**：`Spike/DeepSeek_LangGraph_Mini`

```
目标：验证 DeepSeek-V3 + LangGraph 能跑通最小 ReAct 循环。

上下文：
- LLM 接入方式见 @Docs/TECH-STACK.md §1.3
- Agent 状态机设计见 @Docs/ARCHITECTURE.md §6
- 节点函数模板见 @.agents/rules/backend.rules.md §2.4

操作：
1. 创建 backend/app/agent/state.py：
   - AgentState TypedDict，包含 messages, user_profile, itinerary,
     iteration_count, should_end
   - 使用 Annotated[list, add_messages]

2. 创建一个最小测试脚本 backend/tests/spike_agent.py：
   - 用 langchain-openai 的 ChatOpenAI 连接 DeepSeek
   - base_url = "https://api.deepseek.com"
   - model = "deepseek-chat"
   - 构建只有 planner_node → response_node → END 的最小图
   - 输入 "我想去北京玩3天"，验证能得到回复

约束：
- 使用 async/await
- streaming=True
- 不要硬编码 API Key，从环境变量读取

完成标准：
- 运行脚本能收到 DeepSeek 的流式回复
- 验证 LangGraph 状态图能正常编译和执行
- 记录延迟和 Token 消耗
```

---

## 2.2 Spike：MCP 协议调通高德地图

**分支**：`Spike/MCP_Amap_Integration`

```
目标：验证通过 MCP 协议能调用高德地图 API。

上下文：
- MCP 客户端配置见 @.agents/rules/backend.rules.md §3.4
- 工具注册见 @.agents/rules/backend.rules.md §3.5

操作：
1. 创建 backend/app/tools/mcp_client.py：
   - 使用 langchain-mcp-adapters 的 MultiServerMCPClient
   - 配置高德 MCP Server：
     command: "npx", args: ["-y", "@amap/amap-mcp-server"]
   - get_mcp_tools() 函数，失败时返回空列表

2. 创建测试脚本 backend/tests/spike_mcp.py：
   - 调用 get_mcp_tools() 获取工具列表
   - 打印所有可用工具的名称和描述
   - 尝试调用 POI 搜索：搜索 "北京" 的 "故宫"

约束：
- AMAP_API_KEY 从环境变量读取
- 设置 timeout，MCP 连接失败要有日志

完成标准：
- 能列出高德 MCP Server 提供的所有工具
- 能成功搜索到故宫的 POI 信息
- 如果 MCP 失败，记录错误并返回空列表（不崩溃）
```

> [!IMPORTANT]
> 如果 MCP 调不通，立即转入降级方案：直接 HTTP 调用高德 REST API。
> 降级方案的代码模板在 backend.rules.md §3.2。

---

## 2.3 AgentState + 状态图骨架

```
目标：实现完整的 LangGraph 状态图骨架（4 个节点 + 条件路由）。

上下文：
- 状态图设计见 @Docs/ARCHITECTURE.md §6.2 - §6.5
- 节点命名规范见 @.agents/rules/backend.rules.md §2.2

操作：
1. 完善 backend/app/agent/state.py（如果 Spike 中已创建则更新）

2. 创建 backend/app/agent/nodes.py：
   - run_planner(state) → 调用 LLM 推理，返回 messages + iteration_count
   - run_tools() → 使用 LangGraph 的 ToolNode
   - generate_response(state) → 整理最终回复
   - handle_fallback(state) → 迭代超限兜底
   - route_decision(state) → 条件路由函数
   - 每个节点都有 try-except 错误处理

3. 创建 backend/app/agent/graph.py：
   - build_graph() async 函数
   - 注册 4 个节点：planner_node, tool_node, response_node, fallback_node
   - 设置 entry_point 为 planner_node
   - 添加条件边：planner_node → route_decision
   - 添加固定边：tool_node → planner_node, response_node → END,
     fallback_node → response_node

约束：
- MAX_ITERATIONS = 10
- 节点名称固定，不可更改
- 使用 graph.astream() 获取流式输出
- 所有外部调用有 try-except

完成标准：
- build_graph() 能编译出 CompiledGraph
- 输入一条消息能走完 planner → response → END 的流程
- 迭代超过 10 次能正确路由到 fallback
- ruff check 无错误
```

---

## 2.4 工具实现（含降级方案）

```
目标：实现 4 个 LangChain Tool：poi_search, route_plan, weather, rag_search。

上下文：
- 工具模板见 @.agents/rules/backend.rules.md §3.2
- 工具分类表见 backend.rules.md §3.1
- 开发检查清单见 backend.rules.md §3.3

操作：分 4 个子任务，每个工具一个 Codex 会话：

### 2.4.1 poi_search.py
创建 backend/app/tools/poi_search.py：
- @tool 装饰器 + async
- 参数：city, keyword, top_k=5
- 优先 MCP，降级为直接调用高德 REST API /v3/place/text
- 返回 list[dict]（name, address, lng, lat, type, rating）
- timeout=3s，错误时返回 [{"error": "..."}]

### 2.4.2 route_plan.py
创建 backend/app/tools/route_plan.py：
- @tool 装饰器 + async
- 参数：origin(经纬度), destination(经纬度), mode("driving"/"transit"/"walking")
- 降级调用高德 /v3/direction/{mode}
- 返回 dict（distance_km, duration_min, steps）

### 2.4.3 weather.py
创建 backend/app/tools/weather.py：
- @tool 装饰器 + async
- 参数：city
- 降级调用高德 /v3/weather/weatherInfo?extensions=all
- 返回未来天气列表

### 2.4.4 rag_search.py（占位）
创建 backend/app/tools/rag_search.py：
- @tool 装饰器 + async
- 参数：query, city, top_k=5
- 暂时返回空列表（RAG 在 Step 3 实现）
- 留好接口

约束（全部工具通用）：
- 遵循 backend.rules.md §3.3 的检查清单
- 使用 logging 记录调用日志
- httpx timeout=3s
- docstring 中 Args 描述准确（LLM 依据此信息决定调用）

完成标准：
- 每个工具有对应的单元测试 backend/tests/test_tools.py
- 降级方案能独立工作（不依赖 MCP）
```

---

## 2.5 SSE 流式端点

```
目标：实现 POST /api/v1/chat SSE 端点。

上下文：
- SSE 规范见 @Docs/ARCHITECTURE.md §5.2
- 路由规范见 @.agents/rules/backend.rules.md §1.1 和 §1.3
- 请求/响应模型见 backend.rules.md §1.2

操作：
1. 创建 backend/app/models/schemas.py：
   - ChatRequest：message(str, min_length=1), session_id(str)
   - HealthResponse：status(str), services(dict[str, str])
   - 所有字段用 Field() 添加 description

2. 创建 backend/app/api/chat.py：
   - POST /api/v1/chat
   - sse_generator() 异步生成器
   - 从 graph.astream() 获取事件
   - 格式化为 SSE 事件：thinking/tool_call/tool_result/content/itinerary/error/done
   - StreamingResponse + 正确的 headers

3. 在 router.py 中注册 chat 路由

约束：
- SSE 事件格式必须严格遵循 ARCHITECTURE.md §5.2
- 错误时发送 error 事件，不要直接抛异常
- 流结束必须发送 done 事件
- headers 包含 Cache-Control: no-cache, X-Accel-Buffering: no

完成标准：
- curl 测试能收到 SSE 流
- 事件类型和 data 格式与文档一致
- 错误场景有正确的 error 事件
```

---

## 2.6 System Prompt + 会话管理

```
目标：编写 System Prompt 并实现 Redis 会话管理。

上下文：
- Prompt 管理规范见 @.agents/rules/backend.rules.md §6
- Redis 使用见 backend.rules.md §5.2
- 会话 Key 格式：session:{sessionId}，TTL 2h

操作：
1. 创建 backend/app/agent/prompts.py：
   - SYSTEM_PROMPT 多行字符串，支持 {user_profile} 和 {current_itinerary} 变量
   - 包含角色定义、能力描述、输出要求、约束条件
   - 参考 backend.rules.md §6 的模板

2. 创建 backend/app/services/session.py：
   - get_session(session_id) → 从 Redis 读取会话
   - save_session(session_id, data) → 写入 Redis，TTL 2h
   - clear_session(session_id) → 删除会话

3. 创建 backend/app/services/cache.py：
   - get_cache(key) / set_cache(key, value, ttl)
   - Key 格式遵循 TECH-STACK.md §1.4

完成标准：
- Prompt 包含完整的角色定义和输出约束
- 会话数据能正确读写 Redis
- 缓存有正确的 TTL
```

---

## 本步骤检查清单

- [ ] Spike 验证通过：DeepSeek + LangGraph 能生成回复
- [ ] Spike 验证通过：MCP / 降级方案能调用高德 API
- [ ] 4 个节点函数实现完成
- [ ] 状态图能正确编译和执行
- [ ] 4 个 Tool 实现完成（含降级方案）
- [ ] SSE 端点能正确返回流式事件
- [ ] System Prompt 编写完成
- [ ] Redis 会话管理可用
- [ ] 所有代码通过 ruff check
- [ ] Git commits 遵循 Conventional Commits
