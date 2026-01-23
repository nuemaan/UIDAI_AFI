import { cn } from "@/lib/utils";

interface FrictionBadgeProps {
  score: number;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
}

export function FrictionBadge({ score, showLabel = true, size = "md" }: FrictionBadgeProps) {
  const level = score < 50 ? "low" : score < 100 ? "medium" : "high";
  const label = level === "low" ? "Low" : level === "medium" ? "Medium" : "High";
  
  const sizeStyles = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
    lg: "text-base px-3 py-1.5",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium border",
        sizeStyles[size],
        level === "low" && "friction-low",
        level === "medium" && "friction-medium",
        level === "high" && "friction-high"
      )}
    >
      <span className="font-semibold">{score.toFixed(1)}</span>
      {showLabel && <span className="opacity-80">• {label}</span>}
    </span>
  );
}
