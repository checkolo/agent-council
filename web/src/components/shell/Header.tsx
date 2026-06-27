import { Link } from "react-router-dom";
import { Moon, Sun, Search } from "lucide-react";
import { Button } from "@/ui/button";
import { useTheme } from "@/components/ThemeProvider";

interface HeaderProps {
  onOpenPalette: () => void;
}

export function Header({ onOpenPalette }: HeaderProps) {
  const { theme, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2">
            <span className="h-4 w-4 bg-foreground" />
            <span className="font-semibold tracking-tight">Quorum</span>
          </Link>
          <nav className="hidden sm:flex items-center gap-6 font-mono text-[11px] uppercase tracking-wider">
            <Link to="/" className="text-muted-foreground hover:text-foreground transition-colors">
              History
            </Link>
            <Link to="/new" className="text-muted-foreground hover:text-foreground transition-colors">
              New Run
            </Link>
            <Link to="/cassette" className="text-muted-foreground hover:text-foreground transition-colors">
              Cassette
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onOpenPalette} className="gap-2 font-mono text-[11px]">
            <Search className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Search</span>
            <kbd className="hidden sm:inline font-mono text-[10px] text-muted-foreground border border-border px-1">⌘K</kbd>
          </Button>
          <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
            {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </header>
  );
}
