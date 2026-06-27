import { Button } from "@/ui/button";

interface IdentityToggleProps {
  hidden: boolean;
  onToggle: () => void;
}

export function IdentityToggle({ hidden, onToggle }: IdentityToggleProps) {
  return (
    <div className="flex items-center gap-2 mb-6">
      <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
        Member identity: {hidden ? "hidden" : "revealed"}
      </span>
      <Button variant="outline" size="sm" onClick={onToggle} className="font-mono text-[10px] uppercase">
        {hidden ? "Reveal" : "Hide"}
      </Button>
    </div>
  );
}
