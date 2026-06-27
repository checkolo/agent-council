import { useCallback, useState } from "react";
import { Upload, X } from "lucide-react";
import { cn } from "@/lib/cn";
import { Textarea } from "@/ui/input";

const ACCEPTED = [".patch", ".diff", ".txt"];

interface InputDropzoneProps {
  value: string;
  onChange: (value: string) => void;
  filename: string | null;
  onFilenameChange: (name: string | null) => void;
}

export function InputDropzone({
  value,
  onChange,
  filename,
  onFilenameChange,
}: InputDropzoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      const ext = file.name.includes(".")
        ? `.${file.name.split(".").pop()?.toLowerCase()}`
        : "";
      if (!ACCEPTED.includes(ext)) {
        setError("Accepted: .patch, .diff, .txt");
        return;
      }
      try {
        const text = await file.text();
        onChange(text);
        onFilenameChange(file.name);
      } catch {
        setError("Failed to read file");
      }
    },
    [onChange, onFilenameChange],
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
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "border border-dashed border-border p-6 text-center transition-colors",
          dragging && "bg-muted/40",
        )}
      >
        <Upload className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
        <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
          Drop .patch, .diff, or .txt
        </p>
        <label className="cursor-pointer font-mono text-[11px] uppercase tracking-wider underline underline-offset-4">
          or browse
          <input
            type="file"
            accept=".patch,.diff,.txt"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </label>
        {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      </div>

      {filename && (
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-wider border border-border px-2 py-1">
            {filename}
          </span>
          <button
            type="button"
            onClick={() => {
              onFilenameChange(null);
              onChange("");
            }}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Clear file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <Textarea
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          if (!e.target.value.trim()) onFilenameChange(null);
        }}
        placeholder="Paste a diff, code snippet, or review question..."
        rows={12}
      />
    </div>
  );
}
