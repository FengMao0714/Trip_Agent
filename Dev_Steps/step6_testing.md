# Step 6：测试与优化（Phase 6）

> **模型**：GPT-5.5 | **推理强度**：`medium` | **审批模式**：`auto-edit`
> **分支**：`Feature/Testing_Optimization`
> **预计工时**：3-4 天

---

## 6.1 后端单元测试

```
目标：为后端核心模块编写 pytest 测试。

上下文：
- 测试要求见 @.agents/AGENTS.md §6
- 测试工具见 @Docs/TECH-STACK.md §3.3

操作：
1. backend/tests/test_tools.py：
   - 测试每个 Tool 的降级方案（Mock 外部 API）
   - 测试 timeout 和错误处理
   - 测试返回格式正确性

2. backend/tests/test_api.py：
   - 使用 httpx AsyncClient + FastAPI TestClient
   - 测试 GET /api/v1/health
   - 测试 POST /api/v1/chat（Mock Agent）
   - 测试 400/429 错误场景

3. backend/tests/test_agent.py：
   - 测试 route_decision 条件路由
   - 测试 iteration_count 超限 → fallback
   - 测试状态图编译

约束：
- 使用 pytest-asyncio，asyncio_mode = "auto"
- 外部 API 调用用 Mock/Patch
- 测试命名：test_{功能}_{场景}

完成标准：
- `cd backend && uv run pytest tests/ -v` 全部通过
- 覆盖核心逻辑路径
```

---

## 6.2 RAGAS 评估

```
目标：用 RAGAS 框架评估 RAG 回答质量。

操作：
1. 创建 backend/tests/eval_ragas.py：
   - 准备 20-30 个测试问答对（query + expected_answer）
   - 分别在有 RAG 和无 RAG 条件下测试
   - 计算 faithfulness、answer_relevancy 指标
   - 输出对比结果表格

2. 实验设计：
   - 实验 A：Agent + RAG（正常模式）
   - 实验 B：Agent 无 RAG（仅 LLM 知识）
   - 对比两组的忠实度和相关性

约束：
- 使用 RAGAS 0.2.x API
- 测试数据覆盖 3 个城市
- 结果保存为 JSON 和 Markdown 表格

完成标准：
- 输出量化指标，证明 RAG 提升了回答质量
- 结果可用于论文
```

---

## 6.3 Prompt 调优

```
目标：优化 System Prompt，减少幻觉，提高输出质量。

操作：
1. 基于 Demo 测试结果，调整 prompts.py 中的 SYSTEM_PROMPT
2. 重点优化：
   - 强制使用工具返回的真实数据
   - 结构化输出格式约束
   - 预算约束表述
   - 行程微调时的上下文保持

约束：
- 修改 Prompt 后在 commit message 中说明改动原因
- 每次修改后跑一遍 3 个 Demo 场景验证

完成标准：3 个 Demo 场景的行程质量明显提升。
```

---

## 6.4 Redis 缓存接入

```
目标：为高频工具调用接入 Redis 缓存。

上下文：
- 缓存 Key 格式见 @Docs/TECH-STACK.md §1.4

操作：
1. 更新 services/cache.py，实现：
   - POI 缓存：poi:{city}:{keyword}，TTL 24h
   - 路线缓存：route:{origin}:{dest}:{mode}，TTL 24h
   - 天气缓存：weather:{city}，TTL 6h

2. 在各 Tool 中集成缓存：
   - 调用前检查缓存
   - 缓存命中直接返回
   - 缓存未命中调 API 后写入缓存

完成标准：
- 重复查询响应时间减少 50%+
- 缓存 TTL 正确
```

---

## 6.5 性能优化 + Bug 修复

```
目标：优化性能并修复发现的 Bug。

操作：
1. 前端 FCP/LCP 优化
2. SSE 首字符延迟优化（目标 < 2s）
3. 地图组件懒加载
4. 修复联调中发现的 Bug

完成标准：
- TTFT < 2s
- 完整行程 < 30s
- 首屏加载 < 3s
```

---

## 本步骤检查清单

- [ ] 后端 pytest 全部通过
- [ ] RAGAS 评估数据产出
- [ ] Prompt 调优完成
- [ ] Redis 缓存接入
- [ ] 性能指标达标
- [ ] 已知 Bug 修复
