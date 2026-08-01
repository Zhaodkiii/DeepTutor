# 问题修复工单：移动端 Home 双实例渲染与布局适配回归

## 1. 工单信息

| 字段 | 内容 |
|---|---|
| 工单编号 | WEB-MOBILE-HOME-000002 |
| 创建日期 | 2026-07-30 |
| 模块 | Frontend/Web |
| 页面 | `/home`，同时覆盖 workspace / utility 移动端壳层 |
| 优先级 | P1 |
| 类型 | Bug / 移动端适配回归 |
| 状态 | 待修复 |

## 2. 问题标题

手机浏览器打开 `/home` 存在移动端适配异常风险：同一业务页面被桌面壳层和移动壳层同时挂载，导致 `/home` 双实例运行；桌面浏览器打开看起来正常。

## 3. 用户反馈

用户反馈：

```text
找出问题 创建问题工单 全新的 移动端 适配部分 有问题
电脑浏览器打开没有问题
```

随附控制台日志显示：

```text
GET /home 200
A tree hydrated but some attributes of the server rendered HTML didn't match the client properties.
...
- __gchrome_uniqueid="1"
- __gchrome_uniqueid="2"
```

## 4. 初步结论

本次日志中的 Hydration mismatch 不是最主要根因。日志展开后，服务端和客户端差异字段是：

```text
__gchrome_uniqueid
```

该属性通常由 Chrome / Chromium 插件或自动化环境注入，不是 DeepTutor 业务代码输出的属性。它可以作为干扰项记录，但不应把本次移动端问题优先归因到 React Hydration。

更高优先级的真实问题是：当前移动端响应式布局通过 CSS `hidden` 控制桌面/移动容器显示，但把同一个 `children` 同时渲染了两份。`/home` 是重状态页面，双实例会让隐藏的桌面页也执行 effect、读取 localStorage、加载会话、注册监听、维护 viewer panel 状态，并可能和移动端可见实例互相干扰。

## 5. 关键证据

### 5.1 workspace 布局双挂载 children

文件：

```text
web/app/(workspace)/layout.tsx
```

当前结构：

```tsx
<main className="hidden flex-1 overflow-hidden bg-[var(--background)] md:block">
  <CapabilityGate>{children}</CapabilityGate>
</main>

<div className="block min-w-0 flex-1 bg-[var(--background)] md:hidden">
  <MobileAppShell>
    <CapabilityGate>{children}</CapabilityGate>
  </MobileAppShell>
</div>
```

问题点：

- 桌面容器和移动容器只是 CSS 显隐。
- React 仍会同时挂载两份 `children`。
- `/home` 页面因此在一个浏览器页面里存在两个业务实例。

### 5.2 utility 布局存在同类问题

文件：

```text
web/app/(utility)/layout.tsx
```

同样把 `children` 渲染进桌面 main 和 `MobileAppShell` 两处。该问题会影响 `/settings`、`/memory`、`/knowledge`、`/agents`、`/profile`、`/notebook`、`/space` 等移动端页面。

### 5.3 `/home` 页面副作用密集，不能双实例运行

文件：

```text
web/app/(workspace)/home/[[...sessionId]]/page.tsx
web/context/UnifiedChatContext.tsx
```

风险包括：

- `loadSession` 被隐藏实例和可见实例同时触发。
- `router.replace("/home/<sessionId>")` 可能被重复执行。
- `localStorage` 中 viewer panel、capability config 等状态被两份实例读写。
- `SessionViewerPanel` 读写 `--viewer-width`、`dt:viewer-width`、`data-viewer-resizing`。
- `QuizFollowupBridge`、`GeogebraTabBridge`、`SubagentTabWatcher` 等桥接逻辑被重复挂载。
- 动态 preview / viewer / drawer 组件在隐藏树中仍会参与生命周期。

### 5.4 现有移动端测试覆盖不足

文件：

```text
web/tests/mobile-navigation.spec.ts
```

当前只验证：

- 手机宽度下底部 Tab 可见。
- 控制抽屉可打开。
- 桌面宽度下移动端控件隐藏。

缺少以下断言：

- `/home` 业务主区域只挂载一份。
- 手机宽度没有横向溢出。
- composer 不被底部 Tab 遮挡。
- 右上角控制按钮不遮挡标题/操作按钮。
- viewer panel / preview drawer 在手机宽度下不挤压聊天区。
- 控制台不出现项目自身导致的 hydration / duplicate effect 错误。

## 6. 可能表现

移动端可能出现以下一种或多种现象：

- 页面看得到，但交互不稳定。
- 首屏正常，点击按钮或进入会话后状态错乱。
- 消息区滚动高度异常，底部输入框被底部 Tab 或安全区遮挡。
- Activity / 预览面板打开后聊天区被挤压或出现横向滚动。
- 会话加载、跳转、标题保存、附件预览出现重复请求或重复状态更新。
- 控制台出现 hydration mismatch，且日志中可看到重复的 `/home` 组件树片段。

## 7. 修复目标

修复后应满足：

- 手机端和桌面端都只挂载一份当前业务页面。
- 移动端继续显示 `MobileAppShell`、底部 Tab 和右侧控制抽屉。
- 桌面端继续显示原有 sidebar 和主工作区。
- `/home` 在 375px、390px、430px、768px 临界宽度下无横向溢出。
- composer、标题栏、右上角控制按钮、底部 Tab 互不遮挡。
- viewer panel / preview drawer 在 `<1024px` 下只覆盖，不挤压聊天主列。
- 不因修复引入 SSR / hydration 新问题。

## 8. 推荐修复方向

### 方案 A：新增客户端 ResponsiveShell，只渲染当前断点需要的 children

建议新增一个 client component，例如：

```text
web/components/layout/ResponsiveWorkspaceShell.tsx
web/components/layout/ResponsiveUtilityShell.tsx
```

核心要求：

- 用 `matchMedia("(min-width: 768px)")` 或现有 `useMediaQuery` 判断断点。
- mount 前提供稳定 fallback，避免 SSR 与首次客户端 render 输出互相打架。
- mount 后只渲染桌面或移动其中一支。
- 不要同时在两支里放 `{children}`。

注意：如果 mount 前返回 `null`，需要评估首屏空白是否可接受；更推荐 skeleton 或壳层级 fallback，但不要执行 `/home` 的业务副作用。

### 方案 B：把移动/桌面壳层合并为单一 children 挂载点

思路：

- 外层只渲染一次 `{children}`。
- 桌面 sidebar 和移动导航作为壳层装饰独立显示/隐藏。
- 主内容区域根据断点调整 padding / viewport，而不是把页面复制两份。

该方案长期更干净，但改动范围可能更大。

## 9. 落地方案技术细节

### 9.1 推荐采用单一 ResponsiveAppShell

新增一个通用客户端壳层组件，workspace 和 utility 两套路由共用。核心原则：

```text
断点判断可以在客户端做，但业务 children 只能渲染一份。
```

建议新增：

```text
web/components/layout/ResponsiveAppShell.tsx
```

关键代码示例：

```tsx
"use client";

import { useEffect, useState } from "react";
import { MobileAppShell } from "@/components/mobile/MobileAppShell";

interface ResponsiveAppShellProps {
  children: React.ReactNode;
  desktopSidebar: React.ReactNode;
}

export default function ResponsiveAppShell({
  children,
  desktopSidebar,
}: ResponsiveAppShellProps) {
  const [isDesktop, setIsDesktop] = useState<boolean | null>(null);

  useEffect(() => {
    const query = window.matchMedia("(min-width: 768px)");
    const sync = () => setIsDesktop(query.matches);

    sync();
    query.addEventListener("change", sync);

    return () => {
      query.removeEventListener("change", sync);
    };
  }, []);

  if (isDesktop === null) {
    return (
      <div
        aria-hidden="true"
        className="flex h-dvh overflow-hidden bg-[var(--background)] md:h-screen"
      />
    );
  }

  if (isDesktop) {
    return (
      <div className="flex h-screen overflow-hidden">
        <div className="block">{desktopSidebar}</div>
        <main className="flex-1 overflow-hidden bg-[var(--background)]">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="h-dvh min-w-0 overflow-hidden bg-[var(--background)]">
      <MobileAppShell>{children}</MobileAppShell>
    </div>
  );
}
```

说明：

- `isDesktop === null` 阶段只渲染空壳，不渲染 `{children}`，避免 `/home` 在断点确认前执行副作用。
- 断点确认后只进入桌面分支或移动分支，不会再出现隐藏树仍挂载的问题。
- 如果业务要求减少首屏空白，可把 fallback 换成轻量 loading shell，但仍然不能挂载 `{children}`。

### 9.2 workspace layout 改造

文件：

```text
web/app/(workspace)/layout.tsx
```

替换为：

```tsx
import WorkspaceSidebar from "@/components/sidebar/WorkspaceSidebar";
import ResponsiveAppShell from "@/components/layout/ResponsiveAppShell";
import { CapabilityAccessProvider } from "@/components/access/CapabilityAccessContext";
import CapabilityGate from "@/components/access/CapabilityGate";
import { UnifiedChatProvider } from "@/context/UnifiedChatContext";

export default function WorkspaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <CapabilityAccessProvider>
      <UnifiedChatProvider>
        <ResponsiveAppShell desktopSidebar={<WorkspaceSidebar />}>
          <CapabilityGate>{children}</CapabilityGate>
        </ResponsiveAppShell>
      </UnifiedChatProvider>
    </CapabilityAccessProvider>
  );
}
```

需要删除旧结构中的两处 `{children}`：

```tsx
<main className="hidden ... md:block">
  <CapabilityGate>{children}</CapabilityGate>
</main>

<div className="block ... md:hidden">
  <MobileAppShell>
    <CapabilityGate>{children}</CapabilityGate>
  </MobileAppShell>
</div>
```

### 9.3 utility layout 改造

文件：

```text
web/app/(utility)/layout.tsx
```

替换为：

```tsx
import UtilitySidebar from "@/components/sidebar/UtilitySidebar";
import ResponsiveAppShell from "@/components/layout/ResponsiveAppShell";
import { CapabilityAccessProvider } from "@/components/access/CapabilityAccessContext";
import CapabilityGate from "@/components/access/CapabilityGate";

export default function UtilityLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <CapabilityAccessProvider>
      <ResponsiveAppShell desktopSidebar={<UtilitySidebar />}>
        <CapabilityGate>{children}</CapabilityGate>
      </ResponsiveAppShell>
    </CapabilityAccessProvider>
  );
}
```

### 9.4 `/home` 移动端布局补强

文件：

```text
web/app/(workspace)/home/[[...sessionId]]/page.tsx
web/components/chat/home/ChatComposer.tsx
```

建议给 composer 根节点增加稳定测试标记：

```tsx
<div
  ref={composerRef}
  data-chat-composer="true"
  className={`relative z-20 mx-auto w-full shrink-0 px-4 pb-4 md:px-6 md:pb-5 ${
    hasMessages ? "pt-1 max-w-[960px]" : "max-w-[768px]"
  }`}
  style={{
    transition: "max-width 650ms cubic-bezier(0.16, 1, 0.3, 1)",
  }}
>
```

顶部栏建议明确给移动端右上角控制按钮留出空间：

```tsx
<div className="mx-auto flex w-full max-w-[960px] flex-wrap items-center justify-between gap-x-3 gap-y-1.5 px-4 pt-14 pr-16 pb-0 md:px-6 md:pt-3 md:pr-6">
```

空状态标题建议加移动端字号，避免英文 greeting 在 375px 下溢出：

```tsx
<h1 className="font-serif text-[30px] font-medium leading-[1.1] tracking-[-0.015em] text-[var(--foreground)] sm:text-[40px]">
  {t(welcomeGreeting)}
</h1>
```

### 9.5 SessionViewerPanel 移动端约束

文件：

```text
web/components/chat/home/SessionViewerPanel.tsx
```

当前 `SessionViewerPanel` 已经是 fixed overlay，并且主聊天 squeeze 只在 `@media (min-width: 1024px)` 生效。修复时需要确保不要把 squeeze 逻辑扩展到移动端。

移动端宽度建议保持：

```tsx
className={`fixed right-0 top-0 z-[30] flex h-full max-w-[92vw] flex-col ...`}
```

如果发现 375px 下 panel 仍过窄或遮挡关闭按钮，可追加移动端宽度策略：

```tsx
style={{
  width: `min(var(${VIEWER_WIDTH_VAR}, ${VIEWER_WIDTH_DEFAULT}px), 92vw)`,
  willChange: "transform",
  transitionDuration: `${ANIM_MS}ms`,
  pointerEvents: visible ? "auto" : "none",
}}
```

### 9.6 Playwright 回归测试关键代码

建议新增：

```text
web/tests/mobile-home-layout.spec.ts
```

测试 1：移动端不横向溢出。

```tsx
import { expect, test } from "@playwright/test";

test.describe("mobile home layout", () => {
  for (const viewport of [
    { width: 375, height: 812 },
    { width: 390, height: 844 },
    { width: 430, height: 932 },
    { width: 767, height: 900 },
  ]) {
    test(`does not overflow horizontally at ${viewport.width}px`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      await page.goto("/home");

      const hasOverflow = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth;
      });

      expect(hasOverflow).toBe(false);
    });
  }
});
```

测试 2：composer 不被底部 Tab 遮挡。

```tsx
test("keeps composer above mobile bottom tabs", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/home");

  const nav = page.getByRole("navigation", {
    name: "Mobile primary navigation",
  });
  const composer = page.locator("[data-chat-composer='true']");

  await expect(nav).toBeVisible();
  await expect(composer).toBeVisible();

  const navBox = await nav.boundingBox();
  const composerBox = await composer.boundingBox();

  expect(navBox).not.toBeNull();
  expect(composerBox).not.toBeNull();
  expect(composerBox!.y + composerBox!.height).toBeLessThanOrEqual(navBox!.y);
});
```

测试 3：桌面/移动壳层不再双挂载。建议在页面根节点添加测试标记，例如 `/home` 根节点：

```tsx
<div
  data-home-page-root="true"
  data-preview-open={previewSource ? "true" : "false"}
  data-viewer-open={viewerPanelOpen ? "true" : "false"}
  className="chat-preview-shell flex h-full flex-col overflow-hidden bg-[var(--background)]"
>
```

对应断言：

```tsx
test("mounts only one home page instance on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/home");

  await expect(page.locator("[data-home-page-root='true']")).toHaveCount(1);
});
```

## 10. 具体修复任务

1. 修复 `web/app/(workspace)/layout.tsx`，禁止同时挂载两份 `children`。
2. 修复 `web/app/(utility)/layout.tsx`，保持同样策略。
3. 检查 `MobileAppShell` 的底部安全区，确保 `/home` composer 在 iPhone 13 / 14 / 15 宽度下不被底部 Tab 遮挡。
4. 检查 `/home` 顶部栏：
   - `pt-14 pr-14` 是否足够避开右上角移动端控制按钮。
   - 标题长文本、保存、下载、Activity 三个 icon 按钮在 375px 宽度下是否换行后仍可点。
5. 检查空状态：
   - `h1 text-[40px]` 在英文、中文、多语言长 greeting 下是否溢出。
6. 检查 `SessionViewerPanel`：
   - 手机端打开 Activity 时必须 overlay。
   - 不应通过 `--viewer-width` 把聊天区挤到不可用宽度。
7. 补充 Playwright 移动端回归测试。

## 11. 建议新增验收测试

在 `web/tests/mobile-navigation.spec.ts` 或新增 `web/tests/mobile-home-layout.spec.ts` 中增加：

```text
viewport: 375 x 812
viewport: 390 x 844
viewport: 430 x 932
viewport: 767 x 900
viewport: 768 x 900
```

断言：

- `/home` 页面没有横向滚动：`document.documentElement.scrollWidth <= window.innerWidth`。
- 移动端只存在一个可运行的聊天页面根节点。
- 底部导航可见，composer 底部高于底部导航顶部。
- 右上角控制按钮可见且可打开 drawer。
- drawer 打开时有 `aria-modal="true"`，关闭后从 DOM 移除或不可见。
- 点击 Activity 后，viewer panel 不导致主聊天区宽度小于 320px。
- console 中不出现项目代码导致的 hydration mismatch、duplicate key、act warning、uncaught error。

## 12. 验收标准

- 手机浏览器打开 `/home`，首屏、输入、发送、打开 Activity、打开右侧控制抽屉均正常。
- 桌面浏览器打开 `/home` 行为不回退。
- workspace 和 utility 两套路由在移动端都没有双实例挂载。
- Playwright 移动端测试通过。
- 浏览器控制台若仍出现 `__gchrome_uniqueid`，需在验收记录中标明为浏览器插件注入；项目自身不得输出新的 hydration mismatch。

## 13. 涉及文件

优先修改：

```text
web/app/(workspace)/layout.tsx
web/app/(utility)/layout.tsx
web/components/mobile/MobileAppShell.tsx
web/tests/mobile-navigation.spec.ts
```

可能涉及：

```text
web/app/(workspace)/home/[[...sessionId]]/page.tsx
web/components/chat/home/ChatComposer.tsx
web/components/chat/home/SessionViewerPanel.tsx
web/components/mobile/MobileBottomTabs.tsx
web/components/mobile/MobileControlDrawer.tsx
```

## 14. 备注

已有旧工单：

```text
需求文档/web/问题修复工单-Next16移动端Hydration属性不一致.md
```

该工单可以保留，但本次问题不要直接沿用旧工单结论。当前用户提供的日志里 mismatch 属性指向 `__gchrome_uniqueid`，优先应修复移动端响应式壳层双挂载和 `/home` 布局可用性。
