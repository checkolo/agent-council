interface PageHeaderProps {
  eyebrow: string;
  title: React.ReactNode;
  description?: string;
}

export function PageHeader({ eyebrow, title, description }: PageHeaderProps) {
  return (
    <header className="border-b border-border pb-8 mb-8">
      <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground mb-4">
        {eyebrow}
      </p>
      <h1 className="text-4xl md:text-5xl font-semibold leading-[1.05] tracking-tight text-balance">
        {title}
      </h1>
      {description && (
        <p className="mt-4 text-muted-foreground max-w-2xl">{description}</p>
      )}
    </header>
  );
}
