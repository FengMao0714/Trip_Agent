# Step 3：RAG 知识库（Phase 3）

> **模型**：GPT-5.5 | **推理强度**：`medium` | **审批模式**：`auto-edit`
> **分支**：`Feature/RAG_Knowledge_Base`
> **预计工时**：3-4 天

---

## 3.1 旅游数据收集与格式化

```
目标：为北京、上海、成都 3 个城市准备 RAG 知识库数据。

上下文：
- 数据格式见 @.agents/rules/backend.rules.md §4.2
- 每城市至少 50 条（景点/餐厅/住宿），共 200+ 条
- 数据存放在 backend/data/{city}.json

操作：
1. 为每个城市生成 JSON 数据文件，每条记录包含：
   - city, category（景点/餐厅/住宿/交通规则）
   - title, content（详细描述，200-500字）
   - metadata: { address, lng, lat, rating, price_range, opening_hours, tags }

2. 数据来源策略：
   - 让 Codex 基于公开信息生成初始数据
   - 后续用高德 POI API 补充真实经纬度和评分

3. 确保数据多样性：
   - 景点：历史文化、自然风光、现代地标、公园等
   - 餐厅：各种菜系、不同价位
   - 住宿：经济型、中档、高端

约束：
- 经纬度必须大致准确（可后续用 API 校准）
- content 字段足够详细，能被 RAG 检索后提供有用信息

完成标准：
- beijing.json、shanghai.json、chengdu.json 各 50+ 条
- JSON 格式合法，可被 Python json.load() 解析
```

> [!TIP]
> 这个任务可以用 `full-auto` 模式让 Codex 批量生成数据。
> 生成后人工抽查几条确认质量即可。

---

## 3.2 Embedding 模型加载

```
目标：实现 bge-large-zh-v1.5 Embedding 模型的加载和使用。

上下文：
- 模型选型见 @Docs/TECH-STACK.md §1.5
- 规范见 @.agents/rules/backend.rules.md §4.1

操作：
1. 创建 backend/app/rag/embeddings.py：
   - 使用 sentence-transformers 加载 BAAI/bge-large-zh-v1.5
   - 模型加载函数（应用启动时调用一次，缓存模型实例）
   - encode() 函数：输入 text → 输出 1024 维向量
   - 支持批量 encode

2. 在 main.py 的 lifespan 中添加模型预加载

约束：
- 模型只加载一次，使用全局变量或单例
- 使用 CPU 模式（避免 CUDA 依赖）
- 向量维度必须是 1024

完成标准：
- 启动时模型加载成功（日志记录加载时间）
- encode("北京故宫") 返回 1024 维 float 列表
```

---

## 3.3 数据入库脚本

```
目标：实现 RAG 数据切片和向量化入库。

上下文：
- 入库规范见 @.agents/rules/backend.rules.md §4.2
- 表结构见 @Docs/ARCHITECTURE.md §4.2

操作：
1. 创建 backend/app/rag/ingest.py：
   - 读取 backend/data/*.json
   - 对每条记录：title + content 拼接后调用 embedding 模型
   - 批量插入 knowledge_chunks 表
   - 记录入库条数和耗时
   - 支持 --city 参数指定单个城市
   - 入库前检查是否已存在（避免重复）

2. 可通过命令行执行：
   cd backend && uv run python -m app.rag.ingest

约束：
- 使用 async 数据库操作
- 批量插入（batch size = 50）提高效率
- 有进度日志

完成标准：
- 执行后 knowledge_chunks 表有 200+ 条记录
- 每条记录的 embedding 维度正确（1024）
- 可重复执行不会重复插入
```

---

## 3.4 向量检索实现

```
目标：实现基于 pgvector 的语义检索。

上下文：
- 检索工具接口见 @.agents/rules/backend.rules.md §4.3

操作：
1. 创建 backend/app/rag/vectorstore.py：
   - search(query_embedding, city, category, top_k) → list[dict]
   - 使用 pgvector 的 cosine 距离
   - 支持按 city 和 category 过滤
   - 返回 title, content, metadata, similarity_score

2. 更新 backend/app/tools/rag_search.py（Step 2 中的占位）：
   - 接收 query, city, top_k
   - 调用 embeddings.encode(query) 获取向量
   - 调用 vectorstore.search() 检索
   - 返回格式化的知识片段列表

3. 在 Agent 的工具链中注册 rag_search

约束：
- 检索延迟 < 500ms
- Top-K 默认 5
- 结果包含相似度分数

完成标准：
- 查询 "北京历史景点" 能返回相关结果（故宫、天坛等）
- rag_search 工具能被 Agent 正确调用
- 有单元测试验证检索质量
```

---

## 本步骤检查清单

- [ ] 3 个城市各 50+ 条知识数据
- [ ] Embedding 模型加载正常
- [ ] 数据入库脚本执行成功
- [ ] knowledge_chunks 表有 200+ 条记录
- [ ] 语义检索返回相关结果
- [ ] rag_search 工具集成到 Agent
- [ ] Git commit: `feat(rag): RAG 知识库构建与检索实现`
