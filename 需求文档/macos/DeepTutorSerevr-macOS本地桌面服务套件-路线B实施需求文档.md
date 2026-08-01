# DeepTutorSerevr macOS 本地桌面服务套件路线 B 实施需求文档

## 1. 文档目标

本文档描述如何把 `DeepTutorSerevr` 做成一个 `macOS` 安装包式应用，并采用“路线 B：把后端冻结成独立二进制，再由宿主 App 拉起”的方式落地。

这个方案的最终目标不是把项目拆成多个产品，而是把整个 DeepTutor 变成一个“安装后可直接打开、自动启动本地服务、自动进入主界面”的 macOS 桌面服务套件。

本文档的写法是按执行顺序拆分的。你可以直接照着做，不需要先理解全部实现细节。

---

## 2. 你最终要得到什么

安装完成后，用户只需要做以下动作：

1. 双击安装包。
2. 把 DeepTutor 安装到应用程序目录。
3. 第一次打开 App。
4. App 自动创建本地工作目录。
5. App 自动启动后端二进制。
6. App 自动启动前端服务。
7. App 通过健康检查确认服务已就绪。
8. App 自动打开本地页面。
9. 用户直接开始使用。

用户不需要：

- 手动安装 Python。
- 手动安装 Node.js。
- 手动执行 `pip install`。
- 手动执行 `deeptutor start`。
- 手动记住本地端口。

---

## 3. 当前仓库现状

当前仓库已经具备以下基础：

- 后端是 Python 服务，核心启动逻辑集中在 `deeptutor/api/main.py`。
- 开发态后端入口在 `deeptutor/api/run_server.py`。
- 前端是 Next.js，且已有独立的前端打包脚本 `scripts/prepare_web_package.py`。
- 项目本身已经有“workspace / data / settings”的运行概念。

当前最关键的事实是：

- `deeptutor/api/run_server.py` 仍然是开发态入口，里面启用了 `reload=True`，这不适合冻结成正式安装包的主入口。
- `deeptutor/api/main.py` 的 `lifespan` 已经承担了大量启动、迁移、初始化动作，这很适合作为冻结后端的核心逻辑。
- `scripts/prepare_web_package.py` 已经说明前端可以按 standalone 方式准备成可分发产物。

参考文件：

- [deeptutor/api/run_server.py](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/deeptutor/api/run_server.py)
- [deeptutor/api/main.py](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/deeptutor/api/main.py)
- [scripts/prepare_web_package.py](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/scripts/prepare_web_package.py)
- [README.md](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/README.md)

---

## 4. 总体架构

路线 B 的整体结构如下：

```text
macOS App
├── 启动器层
│   ├── 启动后端二进制
│   ├── 启动前端服务
│   ├── 监听健康检查
│   └── 管理退出与重启
├── 本地后端二进制
│   ├── FastAPI
│   ├── Uvicorn
│   ├── 会话 / 记忆 / 知识库 / 学习 / 伙伴
│   └── 本地数据目录
└── 本地前端服务
    ├── Next.js standalone
    ├── 静态资源
    └── 本地 Web UI
```

核心原则：

- 后端负责业务能力。
- 宿主 App 负责启动、守护和展示。
- 前端负责界面。
- 数据必须写到固定的本地工作目录。

---

## 5. 实施总原则

开始前先记住 5 条规则：

1. 先让开发环境能稳定启动，再做冻结。
2. 先做后端二进制，再做宿主 App。
3. 先让“本地启动成功”，再追求“安装包漂亮”。
4. 先跑通最小闭环，再做签名、公证和自动更新。
5. 每一步都要有明确产出，不要边做边散。

---

## 6. 分步骤实施

### Step 0：先定边界和产物

#### 你要先决定的事

在动代码之前，先把以下内容写死：

- 产品名称
- App Bundle ID
- 后端二进制名称
- 前端本地端口
- 后端本地端口
- 工作目录位置
- 安装包格式

#### 推荐默认值

```text
产品名称: DeepTutor
Bundle ID: com.yourcompany.deeptutor
后端端口: 8001
前端端口: 3782
工作目录: ~/Library/Application Support/DeepTutor/
安装包格式: .dmg
```

#### 这一步要完成什么

- 你要能明确说出“App 启动后到底起什么进程，监听什么端口，数据写到哪里”。
- 后面所有脚本、配置、签名都围绕这几个值展开。

#### 完成标准

- 端口不再依赖临时手填。
- 工作目录有统一约定。
- 你能画出完整启动链路。

---

### Step 1：把后端入口拆成开发态和生产态

#### 为什么要做

当前 `deeptutor/api/run_server.py` 是开发态启动脚本，里面有 `reload=True`。冻结后的正式安装包不能直接用这个入口。

#### 你要做什么

新增一个生产入口，比如：

```text
deeptutor/api/run_server_prod.py
```

这个文件负责：

- 读取运行目录。
- 读取后端端口。
- 配置日志。
- 设置运行模式。
- 启动 `uvicorn`。
- 不启用 `reload`。

#### 你要保留什么

保留 `deeptutor/api/main.py` 里的应用生命周期逻辑，因为它已经包含：

- 配置一致性校验
- LLM 初始化
- EventBus 启动
- Partner 自动启动
- Cron 启动
- PocketBase 检查
- 记忆迁移

#### 你要改什么

把 `run_server.py` 和生产入口分开：

- `run_server.py` 只给开发和调试用。
- `run_server_prod.py` 只给安装包和宿主 App 用。

#### 完成标准

- 你能独立启动开发态和生产态。
- 生产态没有自动重载。
- 生产态退出后不会反复拉起自己。

---

### Step 2：定义本地工作目录结构

#### 为什么要做

安装包模式下，用户不能自己决定项目目录结构。你必须给它一个统一的数据落点。

#### 推荐目录

```text
~/Library/Application Support/DeepTutor/
├── data/
├── logs/
├── cache/
├── runtime/
└── settings/
```

#### 每个目录的用途

| 目录 | 用途 |
|---|---|
| `data/` | 会话、知识库、记忆、笔记等业务数据 |
| `logs/` | 后端和宿主 App 日志 |
| `cache/` | 临时缓存、前端缓存、下载缓存 |
| `runtime/` | pid 文件、端口文件、启动状态文件 |
| `settings/` | 初始配置、模型设置、端口设置 |

#### 你要做什么

- 统一所有路径读取逻辑。
- 不要把运行数据写进安装目录。
- 不要让后端和前端各自定义一套目录。

#### 完成标准

- 后端启动时能自动找到工作目录。
- 所有数据都能在用户目录下找到。

---

### Step 3：整理后端可冻结依赖

#### 为什么要做

冻结前必须知道哪些依赖是运行时必须的，哪些只是开发时用的。

#### 你要做什么

把依赖分成 3 类：

1. **运行时必需**
   - `fastapi`
   - `uvicorn`
   - `pydantic`
   - `openai`
   - `aiohttp`
   - `httpx`
   - `pocketbase`
   - 以及业务相关运行依赖

2. **可选能力**
   - RAG 增强
   - 文档解析增强
   - Partner 渠道 SDK
   - 其他插件型能力

3. **开发依赖**
   - `pytest`
   - `bandit`
   - `pre-commit`
   - 其他测试或静态检查工具

#### 你要得到什么

最终冻结包只带真正需要的运行依赖，避免：

- 包体过大
- 冻结失败
- 运行时导入缺失
- 构建时间过长

#### 完成标准

- 你能说出“这个依赖为什么必须进安装包”。
- 开发依赖不会混进正式产物。

---

### Step 4：把后端冻结成独立二进制

#### 为什么要做

这是路线 B 的核心步骤。你要把 Python 后端变成 macOS 可执行程序，让宿主 App 能直接拉起。

#### 推荐工具

优先建议：

- `PyInstaller`

备选：

- `Nuitka`

#### 推荐冻结方式

建议先用：

- `onedir`

不要一开始就用：

- `onefile`

#### 这一步要做什么

1. 指定生产入口。
2. 收集 Python 运行时。
3. 收集依赖模块。
4. 收集资源文件。
5. 输出可执行后端目录。

#### 需要特别收集的资源

根据当前项目结构，至少要确认这些资源被带上：

- YAML prompts
- Markdown skills
- JSON 配置
- i18n 文本
- 默认设置文件
- 模板文件

#### 完成标准

- 冻结后的后端能在不依赖源码目录的情况下启动。
- 启动后能正常访问 API。
- 启动后能正常加载配置和资源。

---

### Step 5：把前端做成可分发产物

#### 为什么要做

后端二进制只负责 API，不负责 UI。你还需要一个可随包分发的前端服务。

#### 你要做什么

使用现有脚本：

- `scripts/prepare_web_package.py`

这个脚本的逻辑已经说明了一个关键事实：

- 先构建 Next.js
- 再把 `standalone`、静态资源和 `public` 打包出来

#### 这一步的目标

让前端产物可以在安装包中直接启动，而不是依赖用户本机的 Node 环境。

#### 完成标准

- 前端构建物独立存在。
- 宿主 App 能用本地端口访问前端。

---

### Step 6：创建 macOS 宿主 App

#### 为什么要做

宿主 App 是整个安装包的“门面”和“调度器”。

#### 宿主 App 负责什么

- 第一次启动时初始化目录。
- 启动后端二进制。
- 启动前端服务。
- 做健康检查。
- 打开主页面。
- 监听退出事件。
- 退出时关闭子进程。

#### 宿主 App 不负责什么

不要让宿主 App 直接承载业务逻辑。

它不应该：

- 直接实现知识库逻辑。
- 直接实现聊天逻辑。
- 直接实现 RAG 逻辑。
- 直接实现学习逻辑。

#### 推荐技术

```text
SwiftUI + AppKit 辅助
```

#### 完成标准

- 双击 App 后，宿主 App 能出现。
- 宿主 App 能启动后端和前端。

---

### Step 7：让宿主 App 拉起后端二进制

#### 为什么要做

这是“安装后自动启动”的关键动作。

#### 宿主 App 要做的动作

1. 找到后端可执行文件。
2. 设置环境变量。
3. 设置工作目录。
4. 启动子进程。
5. 记录 pid。
6. 轮询健康检查接口。
7. 确认服务 ready。

#### 推荐的健康检查方式

至少提供一个：

- `GET /health`
- `GET /ready`
- `GET /api/ping`

#### 不推荐的方式

不要只判断“进程还在不在”。

原因：

- 进程活着不代表服务已就绪。
- 进程刚启动时可能还在加载模型、配置、数据库。

#### 完成标准

- 宿主 App 能稳定判断服务是否启动完成。
- 启动失败时能给出可读错误。

---

### Step 8：让宿主 App 拉起前端服务

#### 为什么要做

完整桌面体验需要 UI 也能随包启动。

#### 你要做什么

1. 找到前端 standalone 产物。
2. 启动前端服务。
3. 等待前端端口 ready。
4. 打开主窗口或 WebView。

#### 推荐策略

先做最简单版本：

- 前端作为本地 Web 服务启动
- 宿主 App 用浏览器窗口或 WebView 打开 `http://127.0.0.1:3782`

后续再考虑：

- 直接内嵌 WebView
- 或者改成真正的原生壳层

#### 完成标准

- 用户不用手动打开浏览器。
- App 启动后自动进入界面。

---

### Step 9：做首次启动初始化

#### 为什么要做

用户第一次打开安装包时，什么都没有，所以必须自动初始化。

#### 初始化内容

1. 创建工作目录。
2. 创建 `settings` 文件。
3. 创建默认端口配置。
4. 创建日志目录。
5. 创建缓存目录。
6. 检查后端资源是否存在。
7. 检查前端资源是否存在。
8. 检查模型配置是否完整。

#### 建议做成一个向导页

第一次打开时可以按下面流程走：

1. 欢迎页。
2. 工作目录选择。
3. 模型配置。
4. 端口确认。
5. 初始化完成。
6. 自动启动。

#### 完成标准

- 第一次启动不会直接报错退出。
- 缺少配置时会引导用户补齐。

---

### Step 10：做进程管理与退出收尾

#### 为什么要做

如果没有这一步，App 会出现“窗口关了，后台进程还在”的问题。

#### 你要做什么

宿主 App 需要管理以下状态：

- 后端 pid
- 前端 pid
- 当前端口占用
- 当前服务状态
- 崩溃重启策略

#### 退出时要做什么

1. 停前端。
2. 停后端。
3. 写退出日志。
4. 清理临时文件。

#### 崩溃时要做什么

如果后端异常退出：

- 弹出错误提示
- 给出日志位置
- 允许用户重试

#### 完成标准

- App 退出后不会残留进程。
- 崩溃后用户知道怎么处理。

---

### Step 11：做签名、公证和安装包

#### 为什么要做

macOS 正式分发必须做代码签名和公证，否则用户装完也可能打不开。

#### 你要做什么

1. 签名宿主 App。
2. 签名后端二进制。
3. 签名前端嵌入产物。
4. 生成 `.app`。
5. 打包成 `.dmg` 或 `.pkg`。
6. 提交 Apple notarization。
7. staple 回安装包。

#### 推荐顺序

先：

- 本地签名测试

再：

- 公证测试

最后：

- 正式发布

#### 完成标准

- 用户双击安装包后能正常安装。
- 用户首次打开不会被系统阻拦。

---

## 7. 推荐的文件改造清单

### 必改

- [deeptutor/api/run_server.py](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/deeptutor/api/run_server.py)
- [deeptutor/api/main.py](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/deeptutor/api/main.py)
- [scripts/prepare_web_package.py](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/scripts/prepare_web_package.py)
- [pyproject.toml](/Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/pyproject.toml)

### 建议新增

- `deeptutor/api/run_server_prod.py`
- `packaging/macos/`
- `packaging/macos/launcher/`
- `packaging/macos/scripts/`
- `packaging/macos/assets/`

### 可能需要补充

- 健康检查接口
- 生产启动脚本
- 后端产物复制脚本
- 宿主 App 启动器代码

---

## 8. 你可以照着做的最小可行顺序

如果你不想一次改太多，先按这个顺序来：

1. 新增后端生产入口。
2. 本地把后端冻结成二进制。
3. 本地把前端构建成 standalone 产物。
4. 写一个最小 macOS 宿主 App。
5. 让宿主 App 拉起后端。
6. 让宿主 App 拉起前端。
7. 加健康检查。
8. 加首次启动配置。
9. 加退出管理。
10. 做签名和公证。

这 10 步的顺序不要打乱。

---

## 9. 每一步的验收问题

你做完每一步，都问自己这 3 个问题：

1. 这一步结束后，能不能独立运行？
2. 这一步失败时，能不能看出哪里坏了？
3. 这一步会不会影响下一步继续做？

如果有一个问题答不上来，就不要急着往下走。

---

## 10. 风险提示

### 风险 1：后端冻结后依赖找不到

表现：

- App 启动报错
- 模块导入失败
- 资源文件找不到

应对：

- 提前整理资源收集清单
- 先在本机验证二进制

### 风险 2：启动顺序乱了

表现：

- 前端先起，后端还没 ready
- 页面空白
- API 请求失败

应对：

- 宿主 App 必须按“后端 ready -> 前端 ready -> 打开界面”的顺序执行

### 风险 3：数据目录不统一

表现：

- 配置丢失
- 升级后找不到旧数据
- 多次启动状态混乱

应对：

- 所有路径统一到一个 workspace 根目录

### 风险 4：安装包能装但打不开

表现：

- 被 macOS 拦截
- 提示未签名
- 提示无法验证开发者

应对：

- 签名、公证、staple 必须纳入正式流程

---

## 11. 结论

路线 B 的本质是把 DeepTutor 做成一个 macOS 本地桌面服务套件。

它不是单纯的“打包一下 Python 程序”，而是要把下面四层一起封装：

1. 后端二进制。
2. 前端服务产物。
3. 宿主 App。
4. 本地工作目录与进程管理。

如果你按本文档的顺序一步一步做，最终就能得到一个“安装后可直接启动”的 macOS 应用。
