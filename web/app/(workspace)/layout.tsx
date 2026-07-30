import WorkspaceSidebar from "@/components/sidebar/WorkspaceSidebar";
import { MobileAppShell } from "@/components/mobile/MobileAppShell";
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
        <div className="flex h-dvh overflow-hidden md:h-screen">
          <div className="hidden md:block">
            <WorkspaceSidebar />
          </div>

          <main className="hidden flex-1 overflow-hidden bg-[var(--background)] md:block">
            <CapabilityGate>{children}</CapabilityGate>
          </main>

          <div className="block min-w-0 flex-1 bg-[var(--background)] md:hidden">
            <MobileAppShell>
              <CapabilityGate>{children}</CapabilityGate>
            </MobileAppShell>
          </div>
        </div>
      </UnifiedChatProvider>
    </CapabilityAccessProvider>
  );
}
