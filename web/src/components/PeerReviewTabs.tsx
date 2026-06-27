import ReactMarkdown from "react-markdown";
import type { StreamPeerReview } from "@/hooks/useRunStream";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/ui/tabs";

interface PeerReviewTabsProps {
  peerReviews: Record<string, StreamPeerReview>;
  reportReviews?: { reviewer_role: string; content: string }[];
}

export function PeerReviewTabs({ peerReviews, reportReviews }: PeerReviewTabsProps) {
  const reviews =
    reportReviews && reportReviews.length > 0
      ? reportReviews
      : Object.values(peerReviews).map((r) => ({
          reviewer_role: r.role,
          content: r.content,
        }));

  if (reviews.length === 0) return null;

  return (
    <div className="mt-10">
      <h3 className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-4">
        Peer reviews
      </h3>
      <Tabs defaultValue={reviews[0].reviewer_role}>
        <TabsList>
          {reviews.map((r) => (
            <TabsTrigger key={r.reviewer_role} value={r.reviewer_role}>
              {r.reviewer_role}
            </TabsTrigger>
          ))}
        </TabsList>
        {reviews.map((r) => (
          <TabsContent key={r.reviewer_role} value={r.reviewer_role}>
            <div className="prose prose-sm max-w-none dark:prose-invert font-mono text-sm border border-border p-4">
              <ReactMarkdown>{r.content || "…"}</ReactMarkdown>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
