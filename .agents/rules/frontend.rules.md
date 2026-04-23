# Next.js 前端编码规则

> **激活方式**：`glob: *.{ts,tsx,css}`  
> **适用范围**：`frontend/` 目录下所有文件  
> **前置依赖**：先阅读 `AGENTS.md` 通用规范

---

## 1. App Router 规范

### 页面路由

| 路由 | 文件 | 优先级 |
|------|------|--------|
| `/` | `src/app/page.tsx` | P0 落地页 |
| `/chat` | `src/app/chat/page.tsx` | P0 核心对话页 |
| `/itinerary/[id]` | `src/app/itinerary/[id]/page.tsx` | P2 可选 |

- 页面用**默认导出**，组件用**命名导出**
- 新增路由必须同步更新 `frontend-design.md`

### Server / Client Component 边界

默认 Server Component，以下场景**必须** `'use client'`：

| 场景 | 组件 |
|------|------|
| 高德地图（依赖 `window`） | `MapView`, `AMapContainer`, `POIMarker` |
| SSE 流式连接 | `MessageList`, `StreamingText` |
| 用户交互状态 | `ChatInput`, `DayTabBar`, `PanelTabs` |
| Zustand Store | 所有消费 store 的组件 |
| localStorage | 会话管理组件 |

### 地图动态导入（必须）

```tsx
import dynamic from 'next/dynamic';
const AMapContainer = dynamic(() => import('./AMapContainer'), { ssr: false });
```

### 根布局

必须包含：`next/font/google` 加载 Inter、`metadata` 导出、`globals.css` 导入、`<html lang="zh-CN">`。

---

## 2. 组件规范

### 目录结构

按功能域分目录，**禁止**堆在 `components/` 根目录：

```
src/components/
├── ui/           # shadcn/ui（不修改核心逻辑）
├── chat/         # MessageList, ChatInput, StreamingText, ThinkingIndicator...
├── itinerary/    # DayPlanCard, ActivityItem, TransportSegment, WeatherBadge...
├── map/          # MapView, AMapContainer, POIMarker, RouteLine...
├── layout/       # Navbar, ChatHeader, MainLayout, Footer
└── landing/      # HeroSection, FeatureGrid, FeatureCard
```

### 组件模板

```tsx
'use client';
import { MapPin } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { Activity } from '@/types/itinerary';

interface ActivityItemProps {
  activity: Activity;
  isLast: boolean;
}

export function ActivityItem({ activity, isLast }: ActivityItemProps) {
  return (/* ... */);
}
```

**检查清单**：Props 用 `interface` 定义（禁止 `any`） · 命名导出 · 需要浏览器 API 时加 `'use client'` · 使用 `@/` 路径别名 · 图标用 Lucide React

### shadcn/ui

- 安装后源码在 `src/components/ui/`，不修改核心逻辑，需定制时外部包装
- 用 `cn()` 合并 className：`<Card className={cn('p-4', isActive && 'border-primary')} />`

---

## 3. 类型定义

统一放 `src/types/`，与后端 Pydantic 模型对齐：

```typescript
// types/itinerary.ts
export interface Activity {
  timeSlot: string; placeName: string;
  placeType: 'attraction' | 'restaurant' | 'hotel';
  lng: number; lat: number; description: string;
  cost: number; transport: Transport | null;
}
export interface Transport {
  mode: 'walking' | 'driving' | 'transit';
  distanceKm: number; durationMin: number;
}
export interface DayPlan {
  date: string; dayIndex: number;
  weather: string | null; activities: Activity[];
}
export interface Itinerary {
  destination: string; days: DayPlan[]; totalCost: number;
}

// types/message.ts
export type MessageRole = 'user' | 'assistant';
export interface ChatMessage {
  id: string; role: MessageRole; content: string;
  timestamp: number; isStreaming?: boolean;
}
export type SSEEventType =
  | 'thinking' | 'tool_call' | 'tool_result'
  | 'content' | 'itinerary' | 'error' | 'done';

// types/map.ts
export interface MapMarker {
  id: string; lng: number; lat: number; title: string;
  type: 'attraction' | 'restaurant' | 'hotel'; dayIndex: number;
}
```

---

## 4. 状态管理（Zustand）

Store 放 `src/store/`，不在 Store 中做 API 调用（放 Hooks 里）：

```typescript
// store/chatStore.ts
interface ChatState {
  sessionId: string;
  messages: ChatMessage[];
  itinerary: Itinerary | null;
  isLoading: boolean;
  thinkingStep: string | null;
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (content: string) => void;
  setItinerary: (it: Itinerary) => void;
  setLoading: (v: boolean) => void;
  setThinkingStep: (step: string | null) => void;
  resetSession: () => void;
}
```

---

## 5. SSE 流式处理

使用 `fetch` + `ReadableStream`（非 `EventSource`，因需 POST + JSON body）。

必须处理全部 7 种事件：`thinking` / `tool_call` / `tool_result` / `content` / `itinerary` / `error` / `done`。

```typescript
// lib/sse.ts 核心签名
interface SSECallbacks {
  onThinking: (step: string) => void;
  onContent: (text: string) => void;
  onToolCall?: (tool: string, args: Record<string, unknown>) => void;
  onToolResult?: (tool: string, result: unknown) => void;
  onItinerary: (itinerary: Itinerary) => void;
  onError: (message: string) => void;
  onDone: () => void;
}
export async function parseSSEStream(
  body: ReadableStream<Uint8Array>, callbacks: SSECallbacks
): Promise<void>;
```

`JSON.parse` 必须 `try-catch` 包裹。

---

## 6. Hooks

命名：`use` + camelCase，文件名与 Hook 同名。

### useChat

- 通过 `useChatStore` 管理状态
- `sendMessage` 中：按 429/503/其他状态码分别处理错误
- 网络错误显示"网络连接失败"Toast

### useAMap

- 在 `useEffect` 中设置 `window._AMapSecurityConfig`（必须在 load 前）
- 使用 `@amap/amap-jsapi-loader` 加载 v2.0
- plugins: `['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow']`
- cleanup 时调用 `map.destroy()`

---

## 7. 响应式布局

断点（对齐 `frontend-design.md §5.1`）：

| 断点 | 宽度 | 布局 |
|------|------|------|
| `< lg` | < 1024px | 单栏 + 底部 Tab 切换 |
| `lg` | 1024-1279px | 双栏，右栏收窄 |
| `xl` | ≥ 1280px | 双栏，左 45% / 右 55% |

关键规则：

| 组件 | 桌面端 | 移动端 |
|------|--------|--------|
| 消息气泡 | `max-w-[600px]` | `max-w-[85vw]` |
| 地图容器 | `h-full` | `h-[60vh]` |
| 行程卡片 | 紧凑横向 | 全宽纵向堆叠 |

---

## 8. 样式规范

- Tailwind CSS **v3.4**（非 v4），与 shadcn/ui 一致
- 颜色用 shadcn/ui CSS 变量（`text-muted-foreground`），**避免硬编码**（`text-gray-500`）
- 地图 Marker 颜色：景点蓝 / 餐厅橙 / 住宿紫
- 路线颜色按天区分：Day1 蓝 / Day2 绿 / Day3 橙

---

## 9. API 调用

- 所有调用通过 `src/lib/api.ts`（REST）或 `src/lib/sse.ts`（流式）
- **禁止**组件中直接拼 URL
- **禁止**前端 import 后端模块（仅 HTTP 通信）
- 所有 `fetch` 必须 `try-catch`

---

## 10. 开发命令

```bash
pnpm dev                          # 启动开发服务器
pnpm dlx shadcn@latest add <c>    # 安装 shadcn/ui 组件
pnpm tsc --noEmit                 # 类型检查
pnpm lint                         # Lint
pnpm build                        # 生产构建（仅部署时）
```

Mock 数据放 `src/mock/`，通过 `NEXT_PUBLIC_USE_MOCK=true` 切换。
