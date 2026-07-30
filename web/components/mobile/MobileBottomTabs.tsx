"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Lock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useCapabilityAccess } from "@/components/access/CapabilityAccessContext";
import {
  isRouteActive,
  MOBILE_PRIMARY_NAV,
  type MobileNavEntry,
} from "@/components/mobile/mobileNav";

function MobileTabItem({ item }: { item: MobileNavEntry }) {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { has } = useCapabilityAccess();
  const active = isRouteActive(pathname, item.match);
  const locked = item.requires ? !has(item.requires) : false;
  const caption = t(item.shortLabelKey ?? item.labelKey);

  if (locked) {
    return (
      <button
        key={item.href}
        type="button"
        aria-disabled="true"
        aria-label={`${t(item.labelKey)} — ${t("Locked — contact your administrator to get access.")}`}
        className="relative flex min-w-0 flex-col items-center justify-center gap-0.5 rounded-[10px] text-[10.5px] leading-none text-[var(--muted-foreground)]/40"
        onClick={() => {
          // No global toast API yet; aria-label conveys the locked state.
        }}
      >
        <item.icon size={20} strokeWidth={1.7} />
        <Lock size={10} className="absolute right-3 top-2" strokeWidth={2} />
        <span className="max-w-full truncate">{caption}</span>
      </button>
    );
  }

  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      className={`flex min-w-0 flex-col items-center justify-center gap-0.5 rounded-[10px] text-[10.5px] leading-none transition-colors ${
        active
          ? "bg-[var(--accent)] font-medium text-[var(--foreground)]"
          : "text-[var(--foreground)]/75 hover:bg-[var(--accent)]/50 hover:text-[var(--foreground)]"
      }`}
    >
      <item.icon size={20} strokeWidth={active ? 2 : 1.7} />
      <span className="max-w-full truncate">{caption}</span>
    </Link>
  );
}

export function MobileBottomTabs() {
  const { t } = useTranslation();

  return (
    <nav
      aria-label={t("Mobile primary navigation")}
      className="fixed inset-x-0 bottom-0 z-40 border-t bg-[var(--background)]/95 px-1.5 pb-[max(env(safe-area-inset-bottom),6px)] pt-1.5 backdrop-blur md:hidden"
    >
      <div className="grid h-14 grid-cols-6 gap-1">
        {MOBILE_PRIMARY_NAV.map((item) => (
          <MobileTabItem key={item.href} item={item} />
        ))}
      </div>
    </nav>
  );
}
