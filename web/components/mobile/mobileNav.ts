import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  Bot,
  Brain,
  HeartHandshake,
  House,
  LayoutGrid,
  Library,
  PenLine,
  Settings,
} from "lucide-react";
import type { Capability } from "@/lib/capability-routes";

export interface MobileNavEntry {
  href: string;
  /** i18n key for the full label (matches sidebar keys). */
  labelKey: string;
  /** Optional shorter i18n key for bottom tab captions. */
  shortLabelKey?: string;
  icon: LucideIcon;
  match: string[];
  requires?: Capability;
  external?: boolean;
}

export const MOBILE_PRIMARY_NAV: MobileNavEntry[] = [
  {
    href: "/home",
    labelKey: "Home",
    icon: House,
    match: ["/home"],
    requires: "llm",
  },
  {
    href: "/partners",
    labelKey: "Partners",
    icon: HeartHandshake,
    match: ["/partners"],
    requires: "llm",
  },
  {
    href: "/agents",
    labelKey: "My Agents",
    shortLabelKey: "Mobile Agents",
    icon: Bot,
    match: ["/agents"],
  },
  {
    href: "/co-writer",
    labelKey: "Co-Writer",
    shortLabelKey: "Mobile Co-Writer",
    icon: PenLine,
    match: ["/co-writer"],
    requires: "llm",
  },
  {
    href: "/book",
    labelKey: "Book",
    icon: Library,
    match: ["/book"],
    requires: "llm",
  },
  {
    href: "/space",
    labelKey: "Learning Space",
    shortLabelKey: "Mobile Space",
    icon: LayoutGrid,
    match: ["/space"],
  },
];

export const MOBILE_CONTROL_NAV: MobileNavEntry[] = [
  {
    href: "/memory",
    labelKey: "Memory",
    icon: Brain,
    match: ["/memory"],
  },
  {
    href: "/knowledge",
    labelKey: "Knowledge Center",
    icon: BookOpen,
    match: ["/knowledge"],
  },
  {
    href: "/settings",
    labelKey: "Settings",
    icon: Settings,
    match: ["/settings"],
  },
];

export const RELEASES_URL = "https://github.com/HKUDS/DeepTutor/releases";

/** Returns true when pathname matches any prefix on a path-segment boundary. */
export function isRouteActive(pathname: string, prefixes: string[]): boolean {
  return prefixes.some(
    (prefix) =>
      pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}
