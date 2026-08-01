# Book与内容编排需求

## 一、模块目标

本模块负责把一段教学或创作意图编排成可持续生成的 Book，包括提案、spine、章节页、块级内容和后续重编译。它是 DeepTutor 的长文生成与结构化内容引擎。

## 二、Book与内容编排模块结构

### 2.1 Book 规划与提案

#### 需求说明

系统先根据用户意图和上下文生成 Book proposal，再让用户确认。

#### 基础要求与业务规则

- 提案阶段必须可回退。
- 输入可以来自 chat、notebook、knowledge base 和 question bank。

#### 验收标准

- 能生成标题、描述和初始结构建议。

#### 技术细节与设计代码位置

| 职责 | 代码位置 |
| --- | --- |
| Book 引擎 | `deeptutor/book/engine.py` |
| 规划 agent | `deeptutor/book/agents/ideation_agent.py` |
| 输入构造 | `deeptutor/book/inputs.py` |

### 2.2 Spine 与页面编排

#### 需求说明

确认提案后，需要生成 spine 和 page shells，再进入页面级编译。

#### 基础要求与业务规则

- spine 是后续页面编排的骨架。
- 页面状态必须能区分 pending / processing / ready / error。

#### 验收标准

- spine 确认后，页面可逐个生成。

#### 技术细节与设计代码位置

| 职责 | 代码位置 |
| --- | --- |
| spine synthesizer | `deeptutor/book/agents/spine_synthesizer.py` |
| spine agent | `deeptutor/book/agents/spine_agent.py` |
| page planner | `deeptutor/book/agents/page_planner.py` |

### 2.3 页面编译与块系统

#### 需求说明

页面需要被编译成可渲染内容块，支持文本、代码、图、timeline、quiz、callout、deep dive、interactive 等块类型。

#### 基础要求与业务规则

- 块级生成要支持失败与重试。
- 用户注释和结构化输出都要可保留。

#### 验收标准

- 页面内容能逐块编译并回填。

#### 技术细节与设计代码位置

| 职责 | 代码位置 |
| --- | --- |
| book compiler | `deeptutor/book/compiler.py` |
| block 定义 | `deeptutor/book/blocks/*` |
| 内容模型 | `deeptutor/book/models.py` |

## 三、Book与内容编排模块功能

### 3.1 创建 Book

#### 需求说明

根据用户目标和上下文生成初始 Book 草案。

#### 基础要求与业务规则

- 需要捕获当前会话、笔记和知识库引用。
- 生成过程要可流式反馈。

#### 验收标准

- 可产生带标题和描述的 Book 草案。

#### 技术细节与设计代码位置

- `deeptutor/book/engine.py`
- `deeptutor/api/routers/book.py`

### 3.2 生成 spine 与页面

#### 需求说明

Book 确认后要变成可编译的章节结构。

#### 基础要求与业务规则

- spine 要稳定，不应随便变形。
- 页面缺失时可继续补编。

#### 验收标准

- 页面 shell 可列表、可加载。

#### 技术细节与设计代码位置

- `deeptutor/book/engine.py`
- `deeptutor/book/storage.py`

### 3.3 页面块编译

#### 需求说明

每一页内部由多个块组成，块可以是文本、图、互动组件或测验题。

#### 基础要求与业务规则

- 块类型要可扩展。
- 单块失败不能拖垮整页。

#### 验收标准

- 重新编译可以保留必要的用户自定义内容。

#### 技术细节与设计代码位置

- `deeptutor/book/blocks/*`
- `deeptutor/book/compiler.py`
- `deeptutor/book/streaming.py`

## 整体业务流程

```text
用户意图
  ↓
收集 chat / notebook / KB / question bank 上下文
  ↓
生成 proposal
  ↓
确认 proposal
  ↓
生成 spine
  ↓
创建 page shells
  ↓
按页编译 blocks
  ↓
流式展示进度与结果
```

## 状态模型

- Book：draft、ready、archived、deleted。
- Spine：pending、ready、needs_recompile。
- Page：pending、processing、ready、error。
- Block：pending、processing、ready、error。

## 数据与持久化

- Book、spine、page、progress 均由 BookStorage 管理。
- 页面与聊天 session 之间可以建立映射。

## 错误模型

- 提案失败。
- spine 生成失败。
- 页面编译失败。
- 单块内容生成失败。
- 强制重编译时必须保留用户笔记块。

## 与其他模块的接口边界

- 上游：Chat、Notebook、Knowledge、Learning、UI。
- 下游：LLM、RAG、blocks、storage。
- 不负责：用户授权和底层运行时。

## 关键代码对应关系

| 关键能力 | 代码位置 |
| --- | --- |
| Book 入口 | `deeptutor/book/engine.py` |
| 编译器 | `deeptutor/book/compiler.py` |
| 内容块 | `deeptutor/book/blocks/*` |
| API | `deeptutor/api/routers/book.py` |

## 测试策略

- Book 创建、spine 生成、页面编译和状态回退需要回归测试。
- 需要重点覆盖单页失败、重新编译和用户笔记保留。

## 当前实现、缺口与演进

Book 引擎已经是独立的并行入口，但内容块体系较多，后续需要继续收敛块级状态与错误模型。

## 整体验收标准

- [ ] Book 可从意图创建到页面编译完成。
- [ ] spine 与页面状态清晰。
- [ ] 单块失败可恢复。
- [ ] 用户自定义内容不会被重编译误删。

