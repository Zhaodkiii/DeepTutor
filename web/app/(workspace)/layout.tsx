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
