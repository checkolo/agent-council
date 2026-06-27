import ReactMarkdown from "react-markdown";
import type { StreamMember } from "@/hooks/useRunStream";
import type { MemberOutput } from "@/lib/api";
import { MemberTabs } from "@/components/MemberTabs";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/ui/tabs";

interface LiveMemberTabsProps {
  streamingMembers: Record<string, StreamMember>;
  reportMembers?: MemberOutput[];
  showIdentity: boolean;
}

export function LiveMemberTabs({
  streamingMembers,
  reportMembers,
  showIdentity,
}: LiveMemberTabsProps) {
  const members: MemberOutput[] =
    reportMembers && reportMembers.length > 0
      ? reportMembers
      : Object.values(streamingMembers).map((m) => ({
          role: m.role,
          model: m.model ?? "",
          content: m.content,
        }));

  if (members.length === 0) {
    return (
      <p className="text-sm text-muted-foreground font-mono text-[11px] uppercase tracking-wider">
        Waiting for panel members...
      </p>
    );
  }

  const hasPartial = Object.values(streamingMembers).some((m) => !m.done && m.content);

  if (hasPartial && (!reportMembers || reportMembers.length === 0)) {
    const keys = Object.keys(streamingMembers);
    return (
      <Tabs defaultValue={keys[0]}>
        <TabsList>
          {keys.map((key) => (
            <TabsTrigger key={key} value={key}>
              {key}
              {!streamingMembers[key].done && streamingMembers[key].content && " ·"}
            </TabsTrigger>
          ))}
        </TabsList>
        {keys.map((key) => {
          const m = streamingMembers[key];
          return (
            <TabsContent key={key} value={key}>
              {showIdentity && m.model && (
                <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-4">
                  Model: {m.model}
                </p>
              )}
              <div className="prose prose-sm max-w-none dark:prose-invert font-mono text-sm border border-border p-4">
                <ReactMarkdown>{m.content || "…"}</ReactMarkdown>
              </div>
            </TabsContent>
          );
        })}
      </Tabs>
    );
  }

  return <MemberTabs members={members} showIdentity={showIdentity} />;
}
