import { useEffect, useReducer, useRef } from "react";
import { subscribeRunEvents } from "@/lib/sse";

export type StreamPhase = "panel" | "review" | "judge" | "done";

export interface StreamMember {
  role: string;
  model?: string;
  content: string;
  done: boolean;
}

export interface StreamPeerReview {
  role: string;
  content: string;
  done: boolean;
}

export interface StreamingState {
  phase: StreamPhase;
  members: Record<string, StreamMember>;
  peerReviews: Record<string, StreamPeerReview>;
  judgeContent: string;
  judgeDone: boolean;
}

type StreamAction =
  | { type: "panel.token"; role: string; token: string }
  | { type: "panel.done"; role: string; content: string; model?: string }
  | { type: "review.token"; role: string; token: string }
  | { type: "review.done"; role: string; content: string }
  | { type: "judge.token"; token: string }
  | { type: "judge.done"; content: string }
  | { type: "run.done" }
  | { type: "reset"; phase: StreamPhase };

const initialState = (phase: StreamPhase): StreamingState => ({
  phase,
  members: {},
  peerReviews: {},
  judgeContent: "",
  judgeDone: false,
});

function streamReducer(state: StreamingState, action: StreamAction): StreamingState {
  switch (action.type) {
    case "panel.token": {
      const existing = state.members[action.role];
      return {
        ...state,
        members: {
          ...state.members,
          [action.role]: {
            role: action.role,
            model: existing?.model,
            content: (existing?.content ?? "") + action.token,
            done: false,
          },
        },
      };
    }
    case "panel.done":
      return {
        ...state,
        members: {
          ...state.members,
          [action.role]: {
            role: action.role,
            model: action.model,
            content: action.content,
            done: true,
          },
        },
      };
    case "review.token": {
      const existing = state.peerReviews[action.role];
      return {
        ...state,
        phase: "review",
        peerReviews: {
          ...state.peerReviews,
          [action.role]: {
            role: action.role,
            content: (existing?.content ?? "") + action.token,
            done: false,
          },
        },
      };
    }
    case "review.done":
      return {
        ...state,
        phase: "review",
        peerReviews: {
          ...state.peerReviews,
          [action.role]: {
            role: action.role,
            content: action.content,
            done: true,
          },
        },
      };
    case "judge.token":
      return {
        ...state,
        phase: "judge",
        judgeContent: state.judgeContent + action.token,
      };
    case "judge.done":
      return {
        ...state,
        phase: "judge",
        judgeContent: action.content,
        judgeDone: true,
      };
    case "run.done":
      return { ...state, phase: "done" };
    case "reset":
      return initialState(action.phase);
    default:
      return state;
  }
}

export function useRunStream(
  runId: string | undefined,
  runStatus?: string,
  onComplete?: () => void,
) {
  const initialPhase: StreamPhase = runStatus === "complete" ? "done" : "panel";
  const [state, dispatch] = useReducer(streamReducer, initialPhase, initialState);
  const lastEventIdRef = useRef(0);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (!runId) return;

    const phase: StreamPhase = runStatus === "complete" ? "done" : "panel";
    dispatch({ type: "reset", phase });
    lastEventIdRef.current = 0;

    const handleEvent = (event: string, data: Record<string, unknown>, eventId?: number) => {
      if (eventId !== undefined && eventId > lastEventIdRef.current) {
        lastEventIdRef.current = eventId;
      }

      const role = String(data.role ?? data.member ?? "");

      switch (event) {
        case "panel.token":
          dispatch({ type: "panel.token", role, token: String(data.token ?? "") });
          break;
        case "panel.done":
          dispatch({
            type: "panel.done",
            role,
            content: String(data.content ?? ""),
            model: data.model ? String(data.model) : undefined,
          });
          break;
        case "review.token":
          dispatch({ type: "review.token", role, token: String(data.token ?? "") });
          break;
        case "review.done":
          dispatch({
            type: "review.done",
            role,
            content: String(data.content ?? ""),
          });
          break;
        case "judge.token":
          dispatch({ type: "judge.token", token: String(data.token ?? "") });
          break;
        case "judge.done":
          dispatch({ type: "judge.done", content: String(data.content ?? "") });
          onCompleteRef.current?.();
          break;
        case "run.done":
          dispatch({ type: "run.done" });
          onCompleteRef.current?.();
          break;
      }
    };

    const unsub = subscribeRunEvents(runId, handleEvent, lastEventIdRef.current);
    return unsub;
  }, [runId]);

  return state;
}
