# Step 4：前端骨架（Phase 4）

> **模型**：GPT-5.5 | **推理强度**：`medium` | **审批模式**：`auto-edit`
> **分支**：`Feature/Frontend_Skeleton`
> **预计工时**：5-6 天

> [!NOTE]
> 前端可以用 Mock 数据独立开发，不依赖后端。
> 建议先完成 Mock 数据，再逐个开发组件。

---

## 4.1 Mock 数据准备

```
目标：创建前端独立开发所需的 Mock 数据。

上下文：
- Mock 数据规范见 @Docs/PROJECT-SCOPE.md §2.2
- 行程数据结构见 @Docs/PRD.md §4.2

操作：在 frontend/src/mock/ 目录创建：
1. chat-response.json — 完整 Agent 回复（含行程 JSON）
2. itinerary-beijing-3d.json — 北京 3 天结构化行程
3. poi-search.json — 高德 POI 搜索结果样例
4. route-plan.json — 两点间路线规划结果
5. weather.json — 未来 7 天天气
6. sse-stream.txt — 模拟 SSE 事件序列

约束：
- 行程 JSON 必须与 types/itinerary.ts 类型完全匹配
- SSE 事件格式与 ARCHITECTURE.md §5.2 一致
- 数据要有足够的真实感（真实地名、合理价格）

完成标准：所有 Mock 数据文件创建完成，JSON 合法。
```

---

## 4.2 落地页

```
目标：实现落地页 (/) 的所有组件。

上下文：
- 组件树见 @Docs/frontend-design.md §2.1
- 用户流程见 frontend-design.md §3.1

操作：
1. src/components/layout/Navbar.tsx — Logo + "开始规划" 按钮
2. src/components/landing/HeroSection.tsx — 主视觉区 + CTA
3. src/components/landing/QuickStartInput.tsx — 快捷输入框
4. src/components/landing/FeatureGrid.tsx + FeatureCard.tsx — 特性展示
5. src/components/layout/Footer.tsx — 页脚
6. src/app/page.tsx — 组装落地页

关键交互：
- QuickStartInput 输入后携带内容跳转 /chat?q={input}
- CTA 按钮点击跳转 /chat

约束：
- 使用 shadcn/ui 组件 (Button, Card)
- 响应式：桌面双栏，移动单栏
- 使用 Lucide React 图标
- Inter 字体通过 next/font 加载
- 组件用命名导出，页面用默认导出

完成标准：
- 落地页视觉效果良好
- 点击 CTA 能跳转到 /chat
- 快捷输入能携带参数跳转
- 移动端布局正常
```

---

## 4.3 对话页布局 + 消息组件

```
目标：实现 /chat 页面的分栏布局和对话组件。

上下文：
- 布局规范见 @Docs/frontend-design.md §2.2 和 §5
- 桌面端 >= 1024px 双栏，移动端单栏 + 底部 Tab

操作：
1. src/components/layout/ChatHeader.tsx — 顶部栏
2. src/components/layout/MainLayout.tsx — 分栏容器
3. src/components/chat/MessageList.tsx — 消息列表（ScrollArea）
4. src/components/chat/UserMessage.tsx — 用户消息气泡
5. src/components/chat/AssistantMessage.tsx — AI 回复（支持 Markdown）
6. src/components/chat/StreamingText.tsx — 流式文本渲染 + 光标动画
7. src/components/chat/ThinkingIndicator.tsx — 思考状态动画
8. src/components/chat/ChatInput.tsx — 输入框 + 发送按钮
9. src/components/chat/QuickPrompts.tsx — 快捷提示词
10. src/app/chat/page.tsx — 组装对话页

约束：
- 所有组件标记 'use client'（涉及浏览器交互）
- 使用 react-markdown 渲染 AI 回复
- 消息列表自动滚动到底部
- 响应式参考 frontend-design.md §5

完成标准：
- 桌面端双栏布局正常
- 能输入消息并显示在列表中
- AI 回复支持 Markdown 渲染
- ThinkingIndicator 有动画效果
```

---

## 4.4 Zustand 状态管理 + SSE Hook

```
目标：实现全局状态管理和 SSE 流式连接。

上下文：
- 状态管理见 @Docs/frontend-design.md §3.2
- SSE 方案见 @Docs/TECH-STACK.md §2.4

操作：
1. src/store/chatStore.ts — Zustand store
   - messages: Message[]
   - itinerary: Itinerary | null
   - isLoading, error
   - sessionId (UUID)
   - addMessage, setItinerary, setLoading 等 actions

2. src/lib/sse.ts — SSE 流式连接工具
   - 使用 fetch + ReadableStream（不用 EventSource，因为需要 POST）
   - 解析 SSE 事件：event 行 + data 行
   - 返回异步迭代器

3. src/hooks/useChat.ts — 对话 Hook
   - sendMessage(text) → 调用 /api/v1/chat
   - 处理 SSE 流：thinking → 更新状态, content → 追加文本,
     itinerary → 解析行程, error → 显示错误, done → 结束
   - 管理 loading 状态

4. src/lib/api.ts — API 封装
   - BASE_URL 从 NEXT_PUBLIC_API_URL 读取
   - fetchChat(message, sessionId) → SSE 流

5. src/lib/parseItinerary.ts — 行程 JSON 解析器

约束：
- fetch 必须有 try-catch
- 按状态码分别处理：429/503/其他
- 网络错误显示友好提示

完成标准：
- 使用 Mock 数据能走通完整流程
- 消息发送 → 显示思考 → 流式输出 → 行程解析
```

---

## 4.5 行程卡片组件

```
目标：实现行程展示相关组件。

上下文：
- 组件设计见 @Docs/frontend-design.md §6.2
- 数据结构见 @Docs/PRD.md §4.2

操作：
1. src/components/itinerary/TripSummaryCard.tsx — 行程概览
2. src/components/itinerary/DayTabBar.tsx — 日期切换
3. src/components/itinerary/DayPlanCard.tsx — 单日行程（时间线样式）
4. src/components/itinerary/ActivityItem.tsx — 单个活动条目
5. src/components/itinerary/TransportSegment.tsx — 交通段连接
6. src/components/itinerary/WeatherBadge.tsx — 天气徽章
7. src/components/itinerary/CostBadge.tsx — 费用标签
8. src/components/itinerary/BudgetSummary.tsx — 费用汇总
9. src/hooks/useItinerary.ts — 行程数据管理 Hook

约束：
- 时间线纵向排列，活动间用 TransportSegment 连接
- 类型图标区分：景点（地标）、餐厅（餐具）、住宿（床铺）
- 使用 shadcn Card, Badge, Tabs

完成标准：
- 用 Mock 数据渲染出完整的 3 天行程卡片
- 日期 Tab 切换正常
- 费用汇总正确
```

---

## 4.6 高德地图集成

```
目标：集成高德地图 JS API 2.0。

上下文：
- 地图方案见 @Docs/TECH-STACK.md §2.3
- 交互设计见 @Docs/frontend-design.md §6.3

操作：
1. src/components/map/AMapContainer.tsx — 地图容器
2. src/components/map/MapView.tsx — 地图主组件
3. src/components/map/POIMarker.tsx — 景点标记
4. src/components/map/RouteLine.tsx — 路线连线
5. src/components/map/MarkerPopup.tsx — 标记弹窗
6. src/components/map/DayFilterBar.tsx — 按天筛选
7. src/hooks/useAMap.ts — 地图初始化 Hook

约束：
- 必须用 next/dynamic + { ssr: false } 导入
- 组件文件顶部加 'use client'
- window._AMapSecurityConfig 在 useEffect 中设置
- 环境变量：NEXT_PUBLIC_AMAP_KEY + NEXT_PUBLIC_AMAP_SECRET
- Marker 颜色：景点蓝/餐厅橙/住宿紫
- 路线颜色按天区分

完成标准：
- 地图能正常加载显示
- Mock 数据的景点能标注到地图上
- 路线连线可见
- 点击 Marker 弹出详情
```

---

## 本步骤检查清单

- [ ] Mock 数据完整
- [ ] 落地页视觉效果良好
- [ ] /chat 分栏布局正常
- [ ] 消息发送和流式渲染正常
- [ ] Zustand 状态管理正常
- [ ] 行程卡片渲染完整
- [ ] 高德地图加载和标注正常
- [ ] 移动端布局可用
- [ ] ESLint 无错误
- [ ] Git commit: `feat(frontend): 前端骨架完成`
