# 分支保护策略 — Trip Planner FM

> **适用于**：GitHub 仓库 Settings → Branches → Branch protection rules

---

## main 分支保护规则

在 GitHub 仓库的 Settings → Branches 中，对 `main` 分支配置以下保护规则：

### 必须启用

| 规则 | 设置 | 说明 |
|------|------|------|
| **Require a pull request before merging** | ✅ | 禁止直接 push 到 main |
| **Require status checks to pass** | ✅ | PR 必须通过 CI 才能合并 |
| Required checks | `Backend (Python)`, `Frontend (Next.js)` | CI 中的两个核心 Job |
| **Require conversation resolution** | ✅ | Review 中的讨论必须全部解决 |

### 建议启用

| 规则 | 设置 | 说明 |
|------|------|------|
| Require linear history | ✅ | 强制 rebase 或 squash merge，保持历史线性 |
| Do not allow bypassing | ✅ | 管理员也不能绕过保护规则 |

### 不启用（毕设阶段）

| 规则 | 说明 |
|------|------|
| Require approvals | 单人开发，无需 Code Review 审批 |
| Require signed commits | 开发便利性优先 |

---

## 分支工作流

```
main（受保护）
  │
  ├── Feature/Agent_ReAct_Loop      # 功能开发
  ├── Feature/Frontend_ChatInput
  ├── Fix/SSE_Stream_Disconnect     # Bug 修复
  ├── Docs/API_Design               # 文档更新
  └── Spike/MCP_Amap_Integration    # 技术验证
```

### 工作流程

1. 从 `main` 创建功能分支：`git checkout -b Feature/xxx`
2. 在功能分支上开发、提交（遵循 Conventional Commits）
3. 推送分支并创建 PR 到 `main`
4. CI 自动运行 lint + test
5. CI 通过后合并（推荐 Squash Merge）
6. 合并后删除功能分支

### 合并策略

推荐使用 **Squash and merge**：
- 将功能分支的多次提交压缩为一个
- 保持 main 分支历史简洁
- 合并时的 commit message 使用 Conventional Commits 格式
