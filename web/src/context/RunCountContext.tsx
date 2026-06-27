import { createContext, useContext, useState, type ReactNode } from "react";

interface RunCountContextValue {
  runCount: number;
  setRunCount: (count: number) => void;
  hasApiKey: boolean | null;
  setHasApiKey: (value: boolean) => void;
}

const RunCountContext = createContext<RunCountContextValue | null>(null);

export function RunCountProvider({ children }: { children: ReactNode }) {
  const [runCount, setRunCount] = useState(0);
  const [hasApiKey, setHasApiKey] = useState<boolean | null>(null);

  return (
    <RunCountContext.Provider
      value={{ runCount, setRunCount, hasApiKey, setHasApiKey }}
    >
      {children}
    </RunCountContext.Provider>
  );
}

export function useRunCount() {
  const ctx = useContext(RunCountContext);
  if (!ctx) throw new Error("useRunCount must be used within RunCountProvider");
  return ctx;
}
