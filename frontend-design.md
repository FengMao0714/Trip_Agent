# 前端设计文档：智能 Agent 旅游助手

> **版本**：v1.0 | **日期**：2026-04-22 | **技术栈**：Next.js + shadcn/ui + Tailwind CSS + 高德地图 JS SDK

---

## 1. 页面路由表

本系统采用 Next.js App Router，共 3 个页面/视图：

| 路由路径 | 页面名称 | 优先级 | 说明 |
|----------|----------|--------|------|
| `/` | 落地页 / 欢迎页 | P0 | 产品介绍 + 快速开始入口，首次访问展示 |
| `/chat` | 对话规划页（**核心页**） | P0 | 左侧对话面板 + 右侧行程/地图面板，承载全部核心交互 |
| `/itinerary/[id]` | 行程详情页 | P2 | 独立查看/导出已生成行程（可选，MVP 阶段可省略） |

> [!NOTE]
> 系统核心交互集中在 `/chat` 一个页面完成，采用**分栏布局**而非多页面跳转，减少用户认知负担。

---

## 2. 各页面组件拆分

### 2.1 落地页 `/`

```
LandingPage
├── Navbar                        # 顶部导航栏（Logo + "开始规划"按钮）
├── HeroSection                   # 主视觉区：标题、副标题、CTA 按钮
│   └── QuickStartInput           # 内嵌的快捷输入框（"告诉我你想去哪"）
├── FeatureGrid                   # 产品特性展示（3-4 个卡片）
│   └── FeatureCard               #   单个特性卡片（图标 + 标题 + 描述）
└── Footer                        # 页脚（版权信息、技术栈说明）
```

**关键交互**：用户在 `QuickStartInput` 输入需求后，携带输入内容跳转到 `/chat`。

---

### 2.2 对话规划页 `/chat`（核心页）

```
ChatPage
├── ChatHeader                    # 顶部栏：Logo、新建会话按钮、设置
│
├── MainLayout                    # 主内容区（分栏布局）
│   ├── LeftPanel                 # ===== 左栏：对话面板 =====
│   │   ├── MessageList           # 消息列表（滚动区域）
│   │   │   ├── UserMessage       #   用户消息气泡
│   │   │   ├── AssistantMessage  #   AI 回复气泡（支持流式渲染）
│   │   │   │   └── StreamingText #     流式文本渲染器
│   │   │   └── ThinkingIndicator #   Agent 思考中状态（动画）
│   │   │
│   │   └── ChatInput             # 底部输入区
│   │       ├── TextArea          #   多行文本输入框（shadcn Textarea）
│   │       ├── SendButton        #   发送按钮
│   │       └── QuickPrompts      #   快捷提示词按钮组（可选）
│   │
│   └── RightPanel                # ===== 右栏：行程 + 地图面板 =====
│       ├── PanelTabs             # Tab 切换（行程视图 / 地图视图）
│       │
│       ├── ItineraryView         # Tab 1: 行程视图
│       │   ├── TripSummaryCard   #   行程概览卡片（目的地、天数、总预算）
│       │   ├── DayTabBar         #   日期切换 Tab（Day1 / Day2 / Day3）
│       │   ├── DayPlanCard       #   单日行程卡片
│       │   │   ├── WeatherBadge  #     天气徽章（晴/雨/温度）
│       │   │   └── ActivityItem  #     单个活动条目（时间线样式）
│       │   │       ├── TimeSlot  #       时间段标签
│       │   │       ├── PlaceInfo #       地点信息（名称、类型图标、描述）
│       │   │       ├── CostBadge #       费用标签
│       │   │       └── TransportSegment  # 交通段（方式、距离、耗时）
│       │   └── BudgetSummary     #   费用汇总栏
│       │
│       └── MapView               # Tab 2: 地图视图
│           ├── AMapContainer     #   高德地图容器
│           ├── POIMarker         #   景点标记（自定义图标，按类型区分）
│           ├── RouteLine         #   路线连线（Polyline）
│           ├── MarkerPopup       #   标记点击弹窗（景点详情）
│           └── DayFilterBar      #   按天筛选路线（Day1/Day2/全部）
│
└── ExportDialog                  # 导出弹窗（Markdown / 纯文本）
```

---

### 2.3 行程详情页 `/itinerary/[id]`（P2，可选）

```
ItineraryPage
├── Navbar
├── ItineraryFullView             # 完整行程展示（复用 DayPlanCard）
│   ├── TripSummaryCard
│   ├── DayPlanCard [1..N]
│   └── BudgetSummary
├── MapView                       # 完整地图视图
└── ExportBar                     # 导出操作栏
```

---

## 3. 用户操作流程

### 3.1 主流程：从打开应用到获得行程

```
用户打开应用 (/)
    │
    ▼
看到落地页，点击"开始规划"或在 QuickStartInput 输入需求
    │
    ▼
跳转到对话页 (/chat)，输入内容自动填充到 ChatInput
    │
    ▼
用户发送消息（或补充发送）
    │
    ▼
左栏显示 ThinkingIndicator（Agent 思考中...）
    │
    ▼
Agent 回复以流式文本出现在 AssistantMessage 中
    │
    ├─ 如果 Agent 追问（缺少目的地/天数等）
    │   └─▶ 用户补充信息 → 再次发送 → 循环
    │
    ├─ 如果 Agent 生成了行程
    │   └─▶ 右栏自动切换到 ItineraryView，渲染行程卡片
    │       └─▶ 地图 Tab 同步标注景点位置和路线
    │
    ▼
用户查看行程
    │
    ├─ 满意 → 可选导出（ExportDialog）
    │
    └─ 不满意 → 在 ChatInput 输入修改意见
                  （如"第二天换成室内景点"）
                  └─▶ Agent 局部更新行程 → 右栏刷新
                       └─▶ 循环直到满意
```

### 3.2 关键状态流转

```
[空闲] ──用户发送消息──▶ [等待响应]
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        [流式输出中]                  [错误状态]
              │                           │
              ▼                           ▼
     [行程已生成] ◀──重试──         显示错误提示
              │
     ┌────────┴────────┐
     ▼                 ▼
  [查看行程]      [微调对话]
     │                 │
     ▼                 └──▶ [等待响应] ...
  [导出行程]
```

---

## 4. 技术选型确认

### 4.1 UI 组件库方案

| 类别 | 选型 | 说明 |
|------|------|------|
| **组件库** | shadcn/ui | 基于 Radix UI，可定制性强，按需复制组件源码到项目中 |
| **CSS 框架** | Tailwind CSS v3 | shadcn/ui 的默认搭配，utility-first |
| **地图组件** | 高德地图 JS API 2.0 | 国内访问稳定，与后端高德 MCP Server 数据一致 |
| **地图加载** | @amap/amap-jsapi-loader | 官方 React 加载器 |
| **图标** | Lucide React | shadcn/ui 默认图标库 |
| **字体** | Inter（英文）+ 系统中文字体 | 通过 `next/font` 加载 |
| **状态管理** | Zustand 或 React Context | 轻量，管理会话状态和行程数据 |
| **SSE 客户端** | 原生 EventSource 或 fetch + ReadableStream | 处理后端流式推送 |
| **Markdown 渲染** | react-markdown | 渲染 Agent 回复中的 Markdown 内容 |

### 4.2 需要安装的 shadcn/ui 组件

| 组件 | 用途 |
|------|------|
| `Button` | 发送、导出、CTA 等按钮 |
| `Textarea` | 对话输入框 |
| `Card` | 行程卡片、特性卡片 |
| `Tabs` | 行程/地图切换、日期切换 |
| `Badge` | 天气标签、费用标签、交通方式标签 |
| `Dialog` | 导出弹窗、设置弹窗 |
| `ScrollArea` | 消息列表滚动区域 |
| `Skeleton` | 加载骨架屏 |
| `Tooltip` | 地图标记点悬浮提示 |
| `Avatar` | 用户/AI 头像 |
| `Separator` | 分隔线 |

### 4.3 为什么选高德而非 Leaflet

| 维度 | 高德 JS API | Leaflet + 瓦片 |
|------|-------------|-----------------|
| 国内地图数据 | 原生支持，数据准确 | 需接第三方瓦片源，中文标注不稳定 |
| 与后端一致性 | 后端用高德 MCP，前后端 POI ID 一致 | 数据源不同，可能出现 ID 不匹配 |
| POI 搜索/路线 | 前端也可直接调用（备用） | 需额外集成 |
| 包体积 | 按需加载，约 200KB | 核心约 40KB，但加插件后差异不大 |
| 学习成本 | 中文文档完善 | 社区大但中文资源少 |

> [!TIP]
> **结论**：选择高德 JS API 2.0，前后端数据源统一，避免因坐标系/POI ID 不一致导致的 Bug。

---

## 5. 响应式策略

### 5.1 断点定义

| 断点名 | 宽度范围 | 目标设备 | 布局策略 |
|--------|----------|----------|----------|
| `sm` | < 640px | 手机竖屏 | 单栏，Tab 切换对话/行程/地图 |
| `md` | 640-1023px | 平板/手机横屏 | 单栏，行程面板可从底部滑出 |
| `lg` | 1024-1279px | 小屏笔记本 | 双栏，右栏收窄 |
| `xl` | >= 1280px | 桌面显示器 | 双栏，左右均衡（对话 45% / 行程 55%） |

### 5.2 各断点布局说明

**桌面端 (>= 1024px) — 双栏布局**

```
┌──────────────────────────────────────────────────┐
│  ChatHeader (Logo / 新建会话 / 设置)              │
├──────────────────┬───────────────────────────────┤
│                  │  [行程] [地图]  Tab 切换        │
│  对话消息列表     │                               │
│  (滚动)          │  行程卡片 或 地图展示           │
│                  │  (滚动)                        │
│                  │                               │
├──────────────────┤                               │
│  ChatInput       │  BudgetSummary                │
└──────────────────┴───────────────────────────────┘
```

- 左栏固定宽度 `w-[420px]` 或 `45%`，可拖拽调整
- 右栏自适应剩余空间
- 行程和地图通过 Tabs 切换

**移动端 (< 1024px) — 单栏 + 底部 Tab 布局**

```
┌────────────────────┐
│  ChatHeader        │
├────────────────────┤
│                    │
│  当前活跃视图       │
│  (对话 / 行程 / 地图)│
│                    │
│                    │
├────────────────────┤
│  ChatInput         │  ← 对话视图时显示
│  (或隐藏)          │  ← 其他视图时收起
├────────────────────┤
│ [对话] [行程] [地图] │  ← 底部 Tab 导航
└────────────────────┘
```

- 底部 Tab 栏在三个视图间切换
- 对话视图时 ChatInput 固定在底部
- 行程/地图视图时隐藏 ChatInput，显示"返回对话"浮动按钮
- 行程卡片改为全宽纵向排列

### 5.3 关键响应式规则

| 组件 | 桌面端 | 移动端 |
|------|--------|--------|
| 主布局 | `flex-row` 双栏 | `flex-col` 单栏 + 底部 Tab |
| 消息气泡 | 最大宽度 `max-w-[600px]` | 最大宽度 `max-w-[85vw]` |
| 行程卡片 | 紧凑卡片，横向信息排列 | 全宽卡片，信息纵向堆叠 |
| 地图容器 | 填充右栏高度 `h-full` | 固定高度 `h-[60vh]` |
| 日期 Tab | 横向 Tab 栏 | 可横向滚动的 Tab |
| 导出按钮 | Header 右侧 | 行程视图底部 FAB |
| 快捷提示词 | 输入框上方横排 | 输入框上方可横向滚动 |

---

## 6. 组件设计要点

### 6.1 流式消息渲染 (StreamingText)

- 使用 `fetch` + `ReadableStream` 接收 SSE
- 逐字/逐句追加到 AssistantMessage 中
- 输出过程中显示闪烁光标动画
- 输出完成后解析是否包含行程 JSON，若有则触发右栏渲染

### 6.2 行程卡片 (DayPlanCard)

- 采用**时间线（Timeline）样式**纵向排列活动
- 每个 ActivityItem 之间用 TransportSegment 连接（显示交通方式图标 + 耗时）
- 类型图标区分：景点(地标图标)、餐厅(餐具图标)、住宿(床铺图标)
- 费用标签右对齐，用 Badge 展示

### 6.3 地图交互 (MapView)

- 初始视角：自动 `fitBounds` 包含所有景点
- Marker 按活动类型使用不同颜色（景点蓝色、餐厅橙色、住宿紫色）
- 点击 Marker 弹出 InfoWindow，显示名称、时间、费用
- 路线用不同颜色区分天数（Day1 蓝 / Day2 绿 / Day3 橙）
- DayFilterBar 可切换显示某一天或全部路线

### 6.4 思考状态 (ThinkingIndicator)

- 显示 Agent 当前步骤（"正在搜索景点..."、"正在计算路线..."、"正在生成行程..."）
- 使用脉冲圆点动画 + 文字提示
- 步骤信息从后端 SSE 事件中获取（event type 区分 `thinking` / `tool_call` / `content`）

---

## 7. 目录结构建议

```
src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # 根布局（字体、全局样式）
│   ├── page.tsx                  # 落地页 (/)
│   ├── chat/
│   │   └── page.tsx              # 对话规划页 (/chat)
│   └── itinerary/
│       └── [id]/
│           └── page.tsx          # 行程详情页 (P2)
│
├── components/
│   ├── ui/                       # shadcn/ui 组件（自动生成）
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── tabs.tsx
│   │   └── ...
│   │
│   ├── layout/                   # 布局组件
│   │   ├── Navbar.tsx
│   │   ├── ChatHeader.tsx
│   │   ├── MainLayout.tsx        # 分栏布局容器
│   │   └── Footer.tsx
│   │
│   ├── chat/                     # 对话相关组件
│   │   ├── MessageList.tsx
│   │   ├── UserMessage.tsx
│   │   ├── AssistantMessage.tsx
│   │   ├── StreamingText.tsx
│   │   ├── ThinkingIndicator.tsx
│   │   ├── ChatInput.tsx
│   │   └── QuickPrompts.tsx
│   │
│   ├── itinerary/                # 行程相关组件
│   │   ├── TripSummaryCard.tsx
│   │   ├── DayTabBar.tsx
│   │   ├── DayPlanCard.tsx
│   │   ├── ActivityItem.tsx
│   │   ├── TransportSegment.tsx
│   │   ├── WeatherBadge.tsx
│   │   ├── CostBadge.tsx
│   │   └── BudgetSummary.tsx
│   │
│   ├── map/                      # 地图相关组件
│   │   ├── MapView.tsx
│   │   ├── AMapContainer.tsx
│   │   ├── POIMarker.tsx
│   │   ├── RouteLine.tsx
│   │   ├── MarkerPopup.tsx
│   │   └── DayFilterBar.tsx
│   │
│   └── landing/                  # 落地页组件
│       ├── HeroSection.tsx
│       ├── FeatureGrid.tsx
│       └── FeatureCard.tsx
│
├── hooks/                        # 自定义 Hooks
│   ├── useChat.ts                # 对话状态管理 + SSE 连接
│   ├── useItinerary.ts           # 行程数据解析与管理
│   └── useAMap.ts                # 高德地图初始化与操作
│
├── lib/                          # 工具函数
│   ├── api.ts                    # 后端 API 调用封装
│   ├── sse.ts                    # SSE 流式连接工具
│   ├── parseItinerary.ts         # 行程 JSON 解析器
│   └── utils.ts                  # 通用工具
│
├── store/                        # 状态管理
│   └── chatStore.ts              # Zustand store（会话、消息、行程）
│
├── types/                        # TypeScript 类型定义
│   ├── message.ts                # 消息类型
│   ├── itinerary.ts              # 行程数据结构
│   └── map.ts                    # 地图相关类型
│
└── styles/
    └── globals.css               # Tailwind 全局样式 + 自定义变量
```
