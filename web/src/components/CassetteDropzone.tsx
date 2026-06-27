import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/cn";

interface CassetteDropzoneProps {
  onLoad: (data: Record<string, unknown>) => void;
}

export function CassetteDropzone({ onLoad }: CassetteDropzoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      if (!file.name.endsWith(".cassette")) {
        setError("File must be a .cassette archive");
        return;
      }
      try {
        const form = new FormData();
        form.append("file", file);
        const res = await fetch("/api/cassettes/view", { method: "POST", body: form });
        if (!res.ok) throw new Error("Invalid cassette");
        const data = await res.json();
        onLoad(data);
      } catch {
        setError("Failed to parse cassette");
      }
    },
    [onLoad],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        "border border-dashed border-border p-12 text-center transition-colors",
        dragging && "bg-muted/40",
      )}
    >
      <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
      <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
        Drop a .cassette file here
      </p>
      <label className="cursor-pointer font-mono text-[11px] uppercase tracking-wider underline underline-offset-4">
        or browse
        <input
          type="file"
          accept=".cassette"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </label>
      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}
    </div>
  );
}
