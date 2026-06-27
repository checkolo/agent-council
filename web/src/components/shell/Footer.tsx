export function Footer() {
  return (
    <footer className="border-t border-border mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-3">Product</p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Multi-role code review</li>
              <li>Replayable cassettes</li>
              <li>MCP-native agents</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-3">Surfaces</p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Web — compose & view</li>
              <li>CLI — daily driver</li>
              <li>MCP — agent tools</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-3">License</p>
            <p className="text-sm text-muted-foreground">MIT · No telemetry · BYOK</p>
          </div>
        </div>
        <div className="border-t border-border pt-6 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          © {new Date().getFullYear()} Quorum · Inspectable AI reasoning
        </div>
      </div>
    </footer>
  );
}
