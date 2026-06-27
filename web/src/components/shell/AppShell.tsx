import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/components/ThemeProvider";
import { CommandPalette } from "@/components/CommandPalette";
import { StatusStrip } from "@/components/shell/StatusStrip";
import { Header } from "@/components/shell/Header";
import { Footer } from "@/components/shell/Footer";
import { IdentityProvider } from "@/context/IdentityContext";
import { RunCountProvider, useRunCount } from "@/context/RunCountContext";
import { fetchHealth, fetchRuns } from "@/lib/api";

function AppShellInner() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { runCount, setRunCount, hasApiKey, setHasApiKey } = useRunCount();

  useEffect(() => {
    fetchHealth()
      .then((h) => setHasApiKey(h.has_api_key))
      .catch(() => setHasApiKey(false));

    fetchRuns({ limit: 100 })
      .then((data) => setRunCount(data.runs.length))
      .catch(() => {});
  }, [setRunCount, setHasApiKey]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <StatusStrip runCount={runCount} hasApiKey={hasApiKey} />
      <Header onOpenPalette={() => setPaletteOpen(true)} />
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <Outlet />
      </main>
      <Footer />
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
      <Toaster
        position="bottom-right"
        toastOptions={{
          classNames: {
            toast: "rounded-none shadow-none border border-border bg-background text-foreground",
          },
        }}
      />
    </div>
  );
}

export function AppShell() {
  return (
    <ThemeProvider>
      <IdentityProvider>
        <RunCountProvider>
          <AppShellInner />
        </RunCountProvider>
      </IdentityProvider>
    </ThemeProvider>
  );
}
