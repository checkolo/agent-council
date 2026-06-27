interface ModelOverrideSelectProps {
  suggested: string[];
  value: string;
  onChange: (model: string) => void;
}

export function ModelOverrideSelect({
  suggested,
  value,
  onChange,
}: ModelOverrideSelectProps) {
  const options = [...new Set([...suggested, value])];

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="font-mono text-[11px] border border-border bg-background px-3 py-2 min-w-[220px] focus:outline-none focus:ring-1 focus:ring-foreground"
    >
      {options.map((model) => (
        <option key={model} value={model}>
          {model}
        </option>
      ))}
    </select>
  );
}
