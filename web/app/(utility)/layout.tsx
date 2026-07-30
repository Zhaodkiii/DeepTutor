import UtilitySidebar from "@/components/sidebar/UtilitySidebar";
import { MobileAppShell } from "@/components/mobile/MobileAppShell";
import { CapabilityAccessProvider } from "@/components/access/CapabilityAccessContext";
import CapabilityGate from "@/components/access/CapabilityGate";

export default function UtilityLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <CapabilityAccessProvider>
      <div className="flex h-dvh overflow-hidden md:h-screen">
        <div className="hidden md:block">
          <UtilitySidebar />
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
    </CapabilityAccessProvider>
  );
}
