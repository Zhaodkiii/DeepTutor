# 问题修复工单：Next.js 16 移动端 Hydration 属性不一致

## 1. 问题标题

手机浏览器打开 DeepTutor Web 后出现 React Hydration 属性不一致警告，可能导致移动端交互异常。

## 2. 问题现象

手机浏览器打开当前 Web 页面后，控制台出现 Next.js / React 报错：

```text
A tree hydrated but some attributes of the server rendered HTML didn't match the client properties.
This won't be patched up.
```

页面上可能同时出现以下现象：

- 电脑端浏览器打开正常。
- 手机浏览器打开后，页面能显示，但部分按钮交互不稳定。
- 右上角设置按钮、侧边栏展开按钮、页面内抽屉/面板按钮可能点击后没有视觉变化。
- 控制台同时展示 `Next.js 16.2.3 (stale)` 与 `Turbopack` 提示。

说明：`stale` 是 Next.js 版本提示，不是本问题根因。真正需要处理的是 hydration mismatch。

## 3. 影响范围

| 影响项 | 说明 |
|---|---|
| 移动端 Web | 高风险，手机端首次访问更容易出现 |
| 桌面端 Web | 可能也有警告，但用户不一定感知 |
| 右上角移动端设置按钮 | Hydration 异常可能导致事件绑定或属性状态不一致 |
| 项目内侧边栏/抽屉 | 如果依赖 client state 展开，可能被同类问题影响 |
| 主题系统 | 高相关，当前主题初始化会在 hydration 前改写 `<html>` class |
| i18n / 本地偏好 | 中相关，localStorage 初值若参与首屏渲染，也可能造成不一致 |

## 4. 初步结论

本问题不是普通 CSS 适配问题，也不是单个按钮 `onClick` 逻辑问题。更可能是：

```text
服务端渲染出来的 HTML 属性
和客户端首次 hydration 时 React 期望的属性不一致。
```

当前项目中最可疑的点是：

```text
web/components/ThemeScript.tsx
web/app/layout.tsx
web/context/AppShellContext.tsx
```

其中 `ThemeScript` 会在 React hydration 前根据 `localStorage` 和 `matchMedia` 修改 `<html>` 的 class。

## 5. 关键代码位置

### 5.1 RootLayout

文件：

```text
web/app/layout.tsx
```

当前 `<html>` 服务端输出：

```tsx
<html
  lang="en"
  suppressHydrationWarning
  data-scroll-behavior="smooth"
  className={`${fontSans.variable} ${fontSerif.variable}`}
>
```

服务端只知道字体 class，不知道用户本地主题。

### 5.2 ThemeScript

文件：

```text
web/components/ThemeScript.tsx
```

当前逻辑会在 hydration 前执行：

```js
document.documentElement.classList.remove('dark', 'theme-glass', 'theme-snow');

if (stored === 'dark') {
  document.documentElement.classList.add('dark');
} else if (stored === 'glass') {
  document.documentElement.classList.add('dark', 'theme-glass');
} else if (stored === 'snow') {
  document.documentElement.classList.add('theme-snow');
}
```

这会让浏览器真实 DOM 变成：

```html
<html class="font-vars... theme-snow">
```

但服务端 HTML 可能是：

```html
<html class="font-vars...">
```

React hydration 时就可能提示属性不一致。

### 5.3 AppShellContext

文件：

```text
web/context/AppShellContext.tsx
```

当前 `theme` 初始值在客户端首次 render 时读取：

```tsx
const [theme, setThemeState] = useState<Theme>(() => {
  return getStoredTheme() ?? getSystemTheme();
});
```

虽然 `theme` 本身不一定直接渲染为 DOM 属性，但它和 `ThemeScript` 共同构成了 SSR/client 首屏状态不一致风险。

## 6. 根因假设

### 根因 1：ThemeScript 在 hydration 前修改 `<html>` class

这是最高优先级根因。

服务端输出的 `<html class>` 与客户端 hydration 前被脚本修改后的 `<html class>` 不一致。React 19 / Next 16 对 hydration mismatch 的提示更敏感，因此开发环境会直接显示 console error。

### 根因 2：客户端首次 render 使用 localStorage / matchMedia 派生状态

以下状态如果在首次客户端 render 中直接参与 DOM 输出，也会导致 mismatch：

```text
theme
activeSessionId
codeBlockTheme
codeBlockShowLineNumbers
codeBlockWrapLongLines
```

当前 `language` 和 `sidebarCollapsed` 已经有 SSR-safe 注释与延后 hydrate，但其他本地状态仍需要逐项确认。

### 根因 3：浏览器插件或移动浏览器自动注入属性

React 报错文案中也会提到浏览器扩展可能修改 HTML。手机端如果使用带翻译、阅读模式、广告过滤、脚本注入能力的浏览器，也可能放大问题。

但本项目已有 `ThemeScript` 主动改 `<html>`，所以应先修项目内确定风险点。

## 7. 修复目标

修复后应满足：

- 手机端首次打开不再出现 hydration 属性不一致警告。
- 电脑端主题初始化不闪烁。
- 深色、浅色、Snow、Glass 主题继续生效。
- 移动端右上角设置按钮、侧边栏、Drawer、底部 Tab 交互稳定。
- 不破坏 Next.js App Router 的 SSR。

## 8. 推荐修复方案

### 方案 A：把主题 class 变成服务端可预测的默认值，然后客户端 mount 后再同步

这是推荐方案，稳定性最高。

思路：

1. 服务端 `<html>` 默认带上 `theme-snow`。
2. `ThemeScript` 仍可在 hydration 前切换主题，但服务端默认和大多数浅色设备一致。
3. `AppShellContext` 的 `theme` 初始值统一用 SSR-safe 默认值。
4. mount 后再读取 localStorage 并同步真实主题。

示例方向：

```tsx
<html
  lang="en"
  suppressHydrationWarning
  data-scroll-behavior="smooth"
  className={`${fontSans.variable} ${fontSerif.variable} theme-snow`}
>
```

同时调整 `AppShellContext`：

```tsx
const [theme, setThemeState] = useState<Theme>("snow");

useEffect(() => {
  const nextTheme = getStoredTheme() ?? getSystemTheme();
  setThemeState(nextTheme);
}, []);
```

注意：如果继续保留 `ThemeScript`，它会提前改 DOM；`suppressHydrationWarning` 仍应保留在 `<html>` 上。

### 方案 B：ThemeScript 不再修改 `<html class>`，只写 `data-theme` 或 CSS 变量

思路：

1. 避免直接改 React 管理的 `class` 属性。
2. 改为设置：

```js
document.documentElement.dataset.theme = storedTheme;
```

3. CSS 主题选择器从 `.theme-snow` / `.dark` 迁移到 `[data-theme="snow"]` / `[data-theme="dark"]`。

优点：

- 主题状态更明确。
- 减少 class 与 Next font class 混用导致的 mismatch。

缺点：

- CSS 改动范围较大。
- 需要迁移现有 `.dark` / `.theme-glass` / `.theme-snow` 选择器。

本期不建议优先使用。

### 方案 C：保留当前主题脚本，只降低报警

思路：

- 继续依赖 `suppressHydrationWarning`。
- 对所有可能 mismatch 的子节点也增加 suppress。

不推荐作为主方案。

原因：

- 只能遮住报错，不能解决属性来源不一致。
- 手机端交互异常如果来自 hydration 失败，遮警告没有意义。

## 9. 具体修复任务拆分

### 任务 1：确认 mismatch 的具体属性

在手机浏览器控制台展开完整错误，记录不一致属性。重点看：

```text
class
style
data-*
aria-expanded
```

如果错误指出 `<html class>`，直接执行任务 2。

### 任务 2：修复主题首屏一致性

修改范围：

```text
web/app/layout.tsx
web/context/AppShellContext.tsx
web/components/ThemeScript.tsx
```

要求：

- 服务端默认主题 class 固定。
- 客户端首 render 不直接依赖 localStorage / matchMedia 输出不一致 DOM。
- mount 后同步真实主题。
- 保留 `suppressHydrationWarning`，但不能只靠它掩盖问题。

### 任务 3：审计 Client Component 首屏不稳定值

搜索：

```bash
rg "Date\\(|new Date|Math.random|randomUUID|localStorage|getItem|matchMedia|window\\.inner|navigator|typeof window" web/app web/components web/context web/i18n -n
```

重点检查这些值是否直接参与首屏 JSX：

```text
className
style
aria-*
id
key
文本内容
```

如果参与首屏 JSX，需要改为：

```text
服务端固定默认值 -> useEffect mount 后更新
```

### 任务 4：移动端交互回归测试

重点页面：

```text
/home
/partners
/agents
/co-writer
/book
/space
/memory
/knowledge
/settings
```

重点动作：

```text
右上角设置按钮
右侧控制面板展开/关闭
底部 Tab 切换
项目内侧边栏展开/收起
Chat 输入框点击与发送
```

## 10. 验证方式

### 10.1 本地启动

```bash
cd /Users/hua/Documents/project/DeepTutor/DeepTutorSerevr/web
npm run dev -- --hostname 0.0.0.0 --port 9896
```

手机访问：

```text
http://192.168.1.152:9896
```

### 10.2 清理手机端缓存验证

为避免旧 localStorage 干扰，需要测试两轮：

```text
1. 普通模式，保留已有 localStorage
2. 无痕模式，空 localStorage
```

如果普通模式报错、无痕模式不报错，说明本地持久化状态是关键触发条件。

### 10.3 控制台验收

手机端控制台不应再出现：

```text
A tree hydrated but some attributes of the server rendered HTML didn't match the client properties.
```

可以忽略：

```text
Next.js 16.2.3 (stale)
```

该提示是版本提醒，不是 hydration 修复验收项。

## 11. 验收标准

### 11.1 功能验收

- 手机端打开 `/home` 后无 hydration mismatch console error。
- 右上角设置按钮点击后能展开右侧控制面板。
- 点击遮罩能关闭控制面板。
- 点击“记忆 / 知识中心 / 设置”能跳转。
- 底部 Tab 能切换 6 个主入口。
- 项目内其他侧边栏展开/收起按钮可用。

### 11.2 主题验收

- Snow 默认主题正常。
- Dark 主题刷新后仍保持。
- Glass 主题刷新后仍保持。
- 首屏不出现明显白屏/黑屏闪烁。

### 11.3 桌面端回归

- 桌面端左侧 Sidebar 正常显示。
- Sidebar 折叠/展开正常。
- Recents 状态正常恢复。
- 设置页主题切换正常。
- `npm run lint` 无新增 error。
- `npm run build` 无新增 error。

## 12. 风险说明

| 风险 | 说明 | 处理方式 |
|---|---|---|
| 主题闪烁 | 如果移除 ThemeScript，首次打开可能闪白/闪黑 | 优先保留脚本，但让服务端默认 class 更接近客户端 |
| suppress 掩盖问题 | 只加 suppress 会让真实 mismatch 保留 | 必须修正首屏状态来源 |
| 本地缓存差异 | 手机端 localStorage 和电脑端不同 | 必须用普通模式 + 无痕模式分别验证 |
| 误判为 Next stale | stale 是版本提示，不是交互失效根因 | 工单验收只看 hydration error 是否消失 |

## 13. 优先级

```text
优先级：P1
类型：Bug / Hydration
影响端：移动端 Web 优先，桌面端回归
建议负责人：前端
```

## 14. 修复建议结论

优先修复 `ThemeScript` 与 `<html class>` 的 SSR/client 不一致问题。当前项目在 hydration 前主动根据 localStorage 修改 `<html>` class，这是最明确、最靠近报错的风险点。修复时不要只隐藏 warning，而是让服务端默认 HTML、客户端首次 render、hydration 前脚本三者的主题属性策略保持一致。
