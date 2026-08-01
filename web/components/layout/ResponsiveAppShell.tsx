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
