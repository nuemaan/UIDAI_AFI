import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  caption?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}

export function ChartCard({
  title,
  subtitle,
  caption,
  children,
  className,
  actions,
}: ChartCardProps) {
  return (
    <div className={cn("chart-container animate-fade-in", className)}>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <div className="min-h-[300px]">{children}</div>
      {caption && (
        <p className="text-xs text-muted-foreground mt-4 italic border-t border-border pt-4">
          {caption}
        </p>
      )}
    </div>
  );
}
