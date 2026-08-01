# 知识库与RAG需求

## 一、模块目标

本模块负责知识库创建、文件导入、索引构建、检索、版本管理和外部知识源接入。它是 DeepTutor 连接用户资料、文档和问答上下文的核心。

## 二、知识库与RAG模块结构

### 2.1 知识库管理

#### 需求说明

系统需要支持多个知识库并存，且每个知识库能独立维护文件、状态、索引版本和进度。

#### 基础要求与业务规则

- 知识库必须先落盘再进入索引。
- 版本信息要能反映索引是否可用、是否需要重建。
- 目录丢失和孤儿项要有清理规则。

#### 验收标准

- 能列出知识库。
- 能读取知识库状态。
- 能处理初始化中和陈旧孤儿项。

#### 技术细节与设计代码位置

| 职责 | 代码位置 |
| --- | --- |
| 知识库管理器 | `deeptutor/knowledge/manager.py` |
| 知识库命名 | `deeptutor/knowledge/naming.py` |
| 知识库类型 | `deeptutor/knowledge/kb_types.py` |

### 2.2 文档导入与解析

#### 需求说明

用户上传 PDF、Office、Markdown、文本或图片相关文件后，要能做校验、提取、路由和入库。

#### 基础要求与业务规则

- 文件格式必须先校验再处理。
- 文档提取失败要记录可读错误。
- linked KB 和外部 KB 不走本地持久化索引流程。

#### 验收标准

- 上传后可以看到导入进度。
- 文档被正确路由到对应处理器。

#### 技术细节与设计代码位置

| 职责 | 代码位置 |
| --- | --- |
| 文档添加 | `deeptutor/knowledge/add_documents.py` |
| 文档校验 | `deeptutor/utils/document_validator.py` |
| 文档提取 | `deeptutor/utils/document_extractor.py` |
| 文件路由 | `deeptutor/services/rag/file_routing.py` |

### 2.3 RAG 引擎与版本管理

#### 需求说明

每个知识库绑定一个检索引擎，支持本地向量检索和多种外部/替代引擎。

#### 基础要求与业务规则

- 当前知识库创建时绑定 provider。
- 选择 provider 后，增量添加和检索都必须沿同一条管线。
- embedding 变化和版本有效性要能判断。

#### 验收标准

- 能在 LlamaIndex、PageIndex、GraphRAG、LightRAG、外部服务之间切换。
- 版本状态和检索状态一致。

#### 技术细节与设计代码位置

| 职责 | 代码位置 |
| --- | --- |
| RAG factory | `deeptutor/services/rag/factory.py` |
| 版本探测 | `deeptutor/services/rag/index_probe.py` |
| 路由与签名 | `deeptutor/services/rag/embedding_signature.py`、`deeptutor/services/rag/index_versioning.py` |
| 具体 pipeline | `deeptutor/services/rag/pipelines/*` |

## 三、知识库与RAG模块功能

### 3.1 创建与维护知识库

#### 需求说明

需要支持创建、重命名、删除、状态更新、版本查看和孤儿清理。

#### 基础要求与业务规则

- 名称必须合法。
- 状态更新要能反映导入、重建和失败。

#### 验收标准

- 知识库列表能正确展示 ready / processing / error。

#### 技术细节与设计代码位置

- `deeptutor/api/routers/knowledge.py`
- `deeptutor/knowledge/manager.py`
- `deeptutor/knowledge/initializer.py`

### 3.2 导入文档并构建索引

#### 需求说明

用户上传文件后，系统需要异步导入并生成索引。

#### 基础要求与业务规则

- 上传和索引分开处理。
- 任务进度需要前端可感知。

#### 验收标准

- 可以查看导入状态和进度。

#### 技术细节与设计代码位置

- `deeptutor/api/routers/knowledge.py`
- `deeptutor/knowledge/add_documents.py`
- `deeptutor/services/rag/factory.py`

### 3.3 检索与引用

#### 需求说明

聊天和其它能力需要能检索知识库内容，并带回引用信息。

#### 基础要求与业务规则

- 检索结果要能返回来源。
- 检索失败不能破坏主对话。

#### 验收标准

- 开启 RAG 后，回答中能带回知识库来源。

#### 技术细节与设计代码位置

- `deeptutor/services/rag/*`
- `deeptutor/tools/rag_tool.py`
- `deeptutor/api/routers/chat.py`

## 整体业务流程

```text
创建或选择知识库
  ↓
上传文件 / 导入目录
  ↓
校验格式与内容
  ↓
解析文本并路由到对应 pipeline
  ↓
构建索引与版本记录
  ↓
查询时按 provider 检索并返回引用
```

## 状态模型

- 知识库状态：初始化、processing、ready、error、stale。
- 索引状态：未构建、构建中、可用、版本不匹配、需要重建。
- 文档状态：待导入、导入中、完成、失败、已删除。

## 数据与持久化

- 本地知识库目录存放文件与索引版本。
- 进度和状态由 manager / tracker / JSON 元数据维护。
- connected KB 只保存连接信息，不保存本地副本。

## 错误模型

- 名称非法。
- 文件不可读或不支持。
- 索引引擎不可用。
- embedding 版本不匹配。
- 外部知识源不可达。

## 与其他模块的接口边界

- 上游：Chat、Book、Knowledge UI、CLI。
- 下游：RAG pipelines、文件解析器、LLM、multi-user 权限。
- 不负责：对话生成逻辑本身。

## 关键代码对应关系

| 关键能力 | 代码位置 |
| --- | --- |
| 知识库管理 | `deeptutor/knowledge/manager.py` |
| 导入 API | `deeptutor/api/routers/knowledge.py` |
| RAG 工厂 | `deeptutor/services/rag/factory.py` |
| 文档解析 | `deeptutor/utils/document_extractor.py` |
| 文件路由 | `deeptutor/services/rag/file_routing.py` |

## 测试策略

- `tests/knowledge/*` 需要覆盖知识库 CRUD、导入和版本切换。
- 导入失败、孤儿清理和 embedding mismatch 需要回归测试。

## 当前实现、缺口与演进

当前已支持多引擎和版本化索引，但不同 provider 的状态模型还存在差异，后续建议继续统一对外状态字段。

## 整体验收标准

- [ ] 知识库能创建和列出。
- [ ] 导入任务可追踪。
- [ ] 多 RAG provider 能正常切换。
- [ ] 引用和版本状态可解释。

