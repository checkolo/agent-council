import { MarkdownContent } from "@/components/MarkdownContent";
import type { MemberOutput } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/ui/tabs";

interface MemberTabsProps {
  members: MemberOutput[];
  showIdentity: boolean;
}

export function MemberTabs({ members, showIdentity }: MemberTabsProps) {
  if (members.length === 0) {
    return (
      <p className="text-sm text-muted-foreground font-mono text-[11px] uppercase tracking-wider">
        No member outputs yet.
      </p>
    );
  }

  return (
    <Tabs defaultValue={members[0].role}>
      <TabsList>
        {members.map((m) => (
          <TabsTrigger key={m.role} value={m.role}>
            {m.role}
          </TabsTrigger>
        ))}
      </TabsList>
      {members.map((m) => (
        <TabsContent key={m.role} value={m.role}>
          {showIdentity && (
            <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-4">
              Model: {m.model}
            </p>
          )}
          <div className="border border-border p-4">
            <MarkdownContent>{m.content}</MarkdownContent>
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
