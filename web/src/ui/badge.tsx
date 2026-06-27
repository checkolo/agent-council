import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center font-mono uppercase tracking-wider text-[10px] border whitespace-nowrap rounded-none",
  {
    variants: {
      variant: {
        default: "border-border bg-background text-foreground",
        muted: "border-border bg-muted text-muted-foreground",
        success: "border-success/30 bg-success/10 text-success",
        warning: "border-warning/30 bg-warning/10 text-warning",
        info: "border-info/30 bg-info/10 text-info",
        destructive: "border-destructive/30 bg-destructive/10 text-destructive",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export function severityVariant(severity: string): VariantProps<typeof badgeVariants>["variant"] {
  switch (severity) {
    case "blocker": return "destructive";
    case "major": return "warning";
    case "minor": return "muted";
    default: return "default";
  }
}
