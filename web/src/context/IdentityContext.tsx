import { createContext, useContext, useState, type ReactNode } from "react";

interface IdentityContextValue {
  showIdentity: boolean;
  toggleIdentity: () => void;
  setShowIdentity: (value: boolean) => void;
}

const IdentityContext = createContext<IdentityContextValue | null>(null);

export function IdentityProvider({ children }: { children: ReactNode }) {
  const [showIdentity, setShowIdentity] = useState(false);

  return (
    <IdentityContext.Provider
      value={{
        showIdentity,
        toggleIdentity: () => setShowIdentity((v) => !v),
        setShowIdentity,
      }}
    >
      {children}
    </IdentityContext.Provider>
  );
}

export function useIdentity() {
  const ctx = useContext(IdentityContext);
  if (!ctx) throw new Error("useIdentity must be used within IdentityProvider");
  return ctx;
}
