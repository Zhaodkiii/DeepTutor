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
