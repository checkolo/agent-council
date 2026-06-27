import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Command } from "cmdk";
import { useTheme } from "@/components/ThemeProvider";
import { useIdentity } from "@/context/IdentityContext";
import { fetchRuns, type Run } from "@/lib/api";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const { toggle } = useTheme();
  const { toggleIdentity } = useIdentity();
  const [recentRuns, setRecentRuns] = useState<Run[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (open) {
      fetchRuns({ limit: 20 })
        .then((data) => setRecentRuns(data.runs))
        .catch(() => {});
    } else {
      setSearch("");
    }
  }, [open]);

  const run = (fn: () => void) => {
    fn();
    onOpenChange(false);
  };

  const query = search.toLowerCase();
  const filteredRuns = recentRuns.filter(
    (r) =>
      !query ||
      r.id.toLowerCase().includes(query) ||
      r.template.toLowerCase().includes(query) ||
      r.input_text.toLowerCase().includes(query),
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <div className="fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2 border border-border bg-background shadow-none">
        <Command className="rounded-none" shouldFilter={false}>
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder="Search commands or runs..."
            className="w-full border-0 border-b border-border bg-transparent px-4 py-3 font-mono text-sm outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>
            <Command.Group
              heading="Navigate"
              className="[&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              <CommandItem onSelect={() => run(() => navigate("/"))} label="Dashboard" />
              <CommandItem onSelect={() => run(() => navigate("/new"))} label="New Run" />
              <CommandItem
                onSelect={() => run(() => navigate("/cassette"))}
                label="Cassette Viewer"
              />
            </Command.Group>
            {filteredRuns.length > 0 && (
              <Command.Group
                heading="Recent Runs"
                className="[&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
              >
                {filteredRuns.map((r) => (
                  <CommandItem
                    key={r.id}
                    onSelect={() => run(() => navigate(`/runs/${r.id}`))}
                    label={`${r.id} · ${r.template}`}
                  />
                ))}
              </Command.Group>
            )}
            <Command.Group
              heading="Actions"
              className="[&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              <CommandItem onSelect={() => run(toggleIdentity)} label="Toggle member identities" />
              <CommandItem onSelect={() => run(toggle)} label="Toggle theme" />
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

function CommandItem({ onSelect, label }: { onSelect: () => void; label: string }) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex cursor-pointer items-center px-2 py-2 text-sm aria-selected:bg-muted data-[selected=true]:bg-muted"
    >
      {label}
    </Command.Item>
  );
}
