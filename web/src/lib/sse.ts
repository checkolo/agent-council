export type RunEventHandler = (
  event: string,
  data: Record<string, unknown>,
  eventId?: number,
) => void;

export function subscribeRunEvents(
  runId: string,
  onEvent: RunEventHandler,
  after = 0,
): () => void {
  const source = new EventSource(`/api/runs/${runId}/stream?after=${after}`);

  const handlers: Record<string, (e: MessageEvent) => void> = {};

  const eventTypes = [
    "panel.token",
    "panel.done",
    "review.token",
    "review.done",
    "judge.token",
    "judge.done",
    "run.done",
    "ping",
  ];

  for (const type of eventTypes) {
    handlers[type] = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        const eventId = e.lastEventId ? parseInt(e.lastEventId, 10) : undefined;
        onEvent(type, data, eventId);
      } catch {
        onEvent(type, {}, undefined);
      }
    };
    source.addEventListener(type, handlers[type]);
  };

  source.onerror = () => {
    source.close();
  };

  return () => {
    for (const type of eventTypes) {
      source.removeEventListener(type, handlers[type]);
    }
    source.close();
  };
}
