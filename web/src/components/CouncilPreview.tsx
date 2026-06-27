import type { RoleDetail } from "@/lib/api";
import { ModelOverrideSelect } from "@/components/ModelOverrideSelect";
import { cn } from "@/lib/cn";
import { X } from "lucide-react";

interface CouncilPreviewProps {
  roleDetails: RoleDetail[];
  defaultRoleKeys: string[];
  activeRoles: string[];
  judgeModel: string;
  judgeModels: string[];
  modelOverrides: Record<string, string>;
  onOverrideChange: (key: string, model: string) => void;
  onToggleRole: (key: string) => void;
  onResetRoles: () => void;
}

export function CouncilPreview({
  roleDetails,
  defaultRoleKeys,
  activeRoles,
  judgeModel,
  judgeModels,
  modelOverrides,
  onOverrideChange,
  onToggleRole,
  onResetRoles,
}: CouncilPreviewProps) {
  const isCustomized =
    activeRoles.length !== defaultRoleKeys.length ||
    activeRoles.some((r, i) => r !== defaultRoleKeys[i]);

  return (
    <div className="border border-border">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          Council preview · {activeRoles.length} of {defaultRoleKeys.length} roles
        </span>
        {isCustomized && (
          <button
            type="button"
            onClick={onResetRoles}
            className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground underline underline-offset-4"
          >
            Reset to template
          </button>
        )}
      </div>
      <div className="divide-y divide-border">
        {roleDetails.map((role) => {
          const active = activeRoles.includes(role.key);
          return (
            <div
              key={role.key}
              className={cn(
                "flex flex-wrap items-center justify-between gap-4 px-4 py-3 transition-colors",
                !active && "bg-muted/30 opacity-60",
              )}
            >
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => onToggleRole(role.key)}
                  disabled={active && activeRoles.length <= 1}
                  className={cn(
                    "font-mono text-[10px] uppercase tracking-wider border px-2 py-1 transition-colors",
                    active
                      ? "border-foreground bg-foreground text-background"
                      : "border-border hover:bg-muted/40",
                    active && activeRoles.length <= 1 && "opacity-50 cursor-not-allowed",
                  )}
                  title={active ? "Remove from council" : "Add to council"}
                >
                  {active ? "On council" : "Excluded"}
                </button>
                <div>
                  <p className="text-sm font-medium">{role.display_name}</p>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    {role.key}
                  </p>
                </div>
              </div>
              {active ? (
                <ModelOverrideSelect
                  suggested={role.suggested_models}
                  value={modelOverrides[role.key] ?? role.suggested_models[0]}
                  onChange={(model) => onOverrideChange(role.key, model)}
                />
              ) : (
                <button
                  type="button"
                  onClick={() => onToggleRole(role.key)}
                  className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground flex items-center gap-1"
                >
                  <X className="h-3 w-3" />
                  Add back
                </button>
              )}
            </div>
          );
        })}
        <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-3">
          <div>
            <p className="text-sm font-medium">Judge</p>
            <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              synthesizes decision report
            </p>
          </div>
          <ModelOverrideSelect
            suggested={[judgeModel, ...judgeModels]}
            value={modelOverrides.judge ?? judgeModel}
            onChange={(model) => onOverrideChange("judge", model)}
          />
        </div>
      </div>
    </div>
  );
}
