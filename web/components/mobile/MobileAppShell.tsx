"use client";

import { useEffect, useState } from "react";
import { Settings } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MobileBottomTabs } from "@/components/mobile/MobileBottomTabs";
import { MobileControlDrawer } from "@/components/mobile/MobileControlDrawer";
import { useLockBodyScroll } from "@/hooks/useLockBodyScroll";

export function MobileAppShell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useLockBodyScroll(drawerOpen);

  useEffect(() => {
    if (!drawerOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  return (
    <div className="relative h-dvh min-w-0 overflow-hidden bg-[var(--background)]">
      <button
        type="button"
        onClick={() => setDrawerOpen(true)}
        className="fixed right-3 top-[max(env(safe-area-inset-top),10px)] z-40 flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border)]/60 bg-[var(--background)]/95 text-[var(--foreground)] shadow-sm backdrop-blur transition-colors active:bg-[var(--accent)] md:hidden"
        aria-label={t("Open control panel")}
        aria-expanded={drawerOpen}
      >
        <Settings size={21} strokeWidth={1.8} />
      </button>

      <div className="h-full min-w-0 overflow-hidden pb-[calc(72px+env(safe-area-inset-bottom))]">
        {children}
      </div>

      <MobileBottomTabs />
      <MobileControlDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
