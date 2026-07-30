"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  isRouteActive,
  MOBILE_CONTROL_NAV,
  RELEASES_URL,
  type MobileNavEntry,
} from "@/components/mobile/mobileNav";
import { normalizeVersionTag } from "@/lib/version";

interface MobileControlDrawerProps {
  open: boolean;
  onClose: () => void;
}

function DrawerNavItem({
  item,
  onNavigate,
}: {
  item: MobileNavEntry;
  onNavigate: () => void;
}) {
  const pathname = usePathname();
  const { t } = useTranslation();
  const active = isRouteActive(pathname, item.match);

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={`flex h-14 items-center gap-3 rounded-xl px-3 text-[22px] font-medium transition-colors ${
        active
          ? "bg-[var(--accent)] text-[var(--foreground)]"
          : "text-[var(--foreground)]/90 hover:bg-[var(--background)]/60"
      }`}
    >
      <item.icon size={24} strokeWidth={active ? 2 : 1.7} />
      <span>{t(item.labelKey)}</span>
    </Link>
  );
}

export function MobileControlDrawer({ open, onClose }: MobileControlDrawerProps) {
  const { t } = useTranslation();
  const tag = normalizeVersionTag(process.env.NEXT_PUBLIC_APP_VERSION || "");
  const displayTag = tag ?? "v—";

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-50 md:hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.16 }}
        >
          <button
            type="button"
            className="absolute inset-0 bg-[var(--overlay)]"
            aria-label={t("Close control panel")}
            onClick={onClose}
          />
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label={t("Mobile control panel")}
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            className="absolute right-0 top-0 flex h-dvh w-[min(76vw,280px)] flex-col border-l bg-[var(--secondary)] shadow-2xl"
          >
            <div className="flex items-center justify-end px-3 pb-2 pt-[max(env(safe-area-inset-top),12px)]">
              <button
                type="button"
                onClick={onClose}
                aria-label={t("Close control panel")}
                className="flex h-10 w-10 items-center justify-center rounded-full text-[var(--muted-foreground)] transition-colors hover:bg-[var(--background)]/60 hover:text-[var(--foreground)]"
              >
                <X size={20} strokeWidth={1.8} />
              </button>
            </div>

            <nav className="flex flex-col gap-1 px-2">
              {MOBILE_CONTROL_NAV.map((item) => (
                <DrawerNavItem key={item.href} item={item} onNavigate={onClose} />
              ))}
            </nav>

            <div className="mt-auto border-t border-[var(--border)]/40 px-4 py-4 pb-[max(env(safe-area-inset-bottom),16px)]">
              <a
                href={RELEASES_URL}
                target="_blank"
                rel="noreferrer noopener"
                onClick={onClose}
                className="inline-flex items-center rounded-lg px-2 py-1.5 font-mono text-[13px] tabular-nums tracking-tight text-[var(--muted-foreground)] transition-colors hover:bg-[var(--background)]/50 hover:text-[var(--foreground)]"
              >
                {displayTag}
              </a>
            </div>
          </motion.aside>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
